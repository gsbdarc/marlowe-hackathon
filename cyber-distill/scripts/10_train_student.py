"""Stage 10: train the student (Qwen3-1.7B + LoRA) on teacher labels. One script for every
hackathon checkpoint: 1 GPU, several GPUs, one node or two nodes (launch with torchrun).

The student sees the teacher's prompt (config/prompt_v1.txt) through the chat template with
enable_thinking=False, and is trained on the answer letter only: cross-entropy over the five
letter logits at the answer position (--soft trains on the teacher's five probabilities
instead). Only rows with use_for_training = true are used.

Outputs in runs/<name>/ (relative to CYBER_ROOT):
  best_adapter/      LoRA adapter with the best validation macro F1 (vs the teacher)
  checkpoint-last/   adapter, optimizer, scheduler and step, for --resume
  metrics.jsonl      one line per evaluation; timing.json: seconds per step, samples per second

  torchrun --nproc_per_node 1 scripts/10_train_student.py --size 25k  --name ckpt1
  torchrun --nproc_per_node 8 scripts/10_train_student.py --size 200k --name ckpt4
  (two nodes: see slurm/marlowe/10_student_2node.slurm; add --resume to continue a run)
"""

import argparse
import json
import math
import os
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.distributed as dist
import torch.nn.functional as F
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, Dataset, DistributedSampler

ROOT = Path(os.environ.get("CYBER_ROOT", Path(__file__).resolve().parent.parent))
FINAL = ROOT / "data" / "final"
LETTERS = ["A", "B", "C", "D", "E"]
LABELS = ["NONE", "RISK", "GOVERNANCE", "INCIDENT", "PRODUCT"]
SUBSET_COL = {"25k": "in_25k", "200k": "in_200k", "400k": None}


def ddp_setup():
    if "RANK" in os.environ:
        dist.init_process_group("nccl")
        rank, world, local = dist.get_rank(), dist.get_world_size(), int(os.environ["LOCAL_RANK"])
    else:
        rank, world, local = 0, 1, 0
    torch.cuda.set_device(local)
    return rank, world, local


def load_split(name, labels_path, size=None):
    files = {"train": "train_400k.parquet", "val": "val.parquet", "test": "test.parquet"}
    df = pd.read_parquet(FINAL / files[name])
    if size and SUBSET_COL[size]:
        df = df[df[SUBSET_COL[size]]]
    lab = pd.read_parquet(labels_path)
    df = df.merge(lab[["para_id", "label", "p_A", "p_B", "p_C", "p_D", "p_E", "use_for_training", "invalid"]],
                  on="para_id", how="inner")
    if name == "train":
        df = df[df.use_for_training]
    else:
        df = df[~df.invalid]
    return df.reset_index(drop=True)


class Items(Dataset):
    def __init__(self, df, template, tok, max_len):
        self.df, self.template, self.tok, self.max_len = df, template, tok, max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        r = self.df.iloc[i]
        content = self.template.format(heading=r.heading or "(none)", prev_text=r.prev_text or "(none)", text=r.text)
        prompt = self.tok.apply_chat_template([{"role": "user", "content": content}], tokenize=False,
                                              add_generation_prompt=True, enable_thinking=False)
        ids = self.tok(prompt, add_special_tokens=False, truncation=True, max_length=self.max_len)["input_ids"]
        target = LABELS.index(r.label)
        soft = torch.tensor([r.p_A, r.p_B, r.p_C, r.p_D, r.p_E], dtype=torch.float32)
        return ids, target, soft


def collate(batch, pad_id):
    """Left padding, so the last position is the answer position for every row."""
    n = max(len(b[0]) for b in batch)
    ids = torch.full((len(batch), n), pad_id, dtype=torch.long)
    mask = torch.zeros((len(batch), n), dtype=torch.long)
    for i, (x, _, _) in enumerate(batch):
        ids[i, n - len(x):] = torch.tensor(x)
        mask[i, n - len(x):] = 1
    return ids, mask, torch.tensor([b[1] for b in batch]), torch.stack([b[2] for b in batch])


def letter_logits(model, ids, mask, letter_ids):
    out = model(input_ids=ids, attention_mask=mask, logits_to_keep=1)
    return out.logits[:, -1, :][:, letter_ids].float()


@torch.no_grad()
def evaluate(model, loader, letter_ids, device, world):
    model.eval()
    preds, gold = [], []
    for ids, mask, y, _ in loader:
        lg = letter_logits(model, ids.to(device), mask.to(device), letter_ids)
        preds.append(lg.argmax(-1).cpu())
        gold.append(y)
    p, g = torch.cat(preds).to(device), torch.cat(gold).to(device)
    if world > 1:  # gather predictions from every rank (padded to the same length)
        sizes = [torch.zeros(1, device=device, dtype=torch.long) for _ in range(world)]
        dist.all_gather(sizes, torch.tensor([len(p)], device=device))
        m = int(max(s.item() for s in sizes))
        pp = F.pad(p, (0, m - len(p)), value=-1)
        gg = F.pad(g, (0, m - len(g)), value=-1)
        ps, gs = [torch.zeros_like(pp) for _ in range(world)], [torch.zeros_like(gg) for _ in range(world)]
        dist.all_gather(ps, pp)
        dist.all_gather(gs, gg)
        p, g = torch.cat(ps), torch.cat(gs)
        keep = g >= 0
        p, g = p[keep], g[keep]
    p, g = p.cpu().numpy(), g.cpu().numpy()
    f1s = {}
    for k, name in enumerate(LABELS):
        tp, fp, fn = ((p == k) & (g == k)).sum(), ((p == k) & (g != k)).sum(), ((p != k) & (g == k)).sum()
        f1s[name] = float(2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else float("nan")
    present = [v for v in f1s.values() if not math.isnan(v)]
    model.train()
    return {"macro_f1": float(np.mean(present)) if present else 0.0, "accuracy": float((p == g).mean()),
            "f1": f1s, "n": int(len(g))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", choices=list(SUBSET_COL), required=True)
    ap.add_argument("--name", required=True, help="run name; outputs in runs/<name>/")
    ap.add_argument("--labels", default=str(FINAL / "teacher_labels.parquet"))
    ap.add_argument("--model", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--prompt-version", default="v1")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--batch-per-gpu", type=int, default=16)
    ap.add_argument("--global-batch", type=int, default=128, help="kept fixed across GPU counts via accumulation")
    ap.add_argument("--max-len", type=int, default=1536)
    ap.add_argument("--eval-every", type=int, default=500, help="optimizer steps")
    ap.add_argument("--save-every", type=int, default=500)
    ap.add_argument("--max-steps", type=int, default=None, help="stop early (timing runs, smoke tests)")
    ap.add_argument("--soft", action="store_true", help="train on the teacher's five probabilities (optional variant)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--gradient-checkpointing", action="store_true")
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args()

    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup

    rank, world, local = ddp_setup()
    device = torch.device("cuda", local)
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    out = ROOT / "runs" / args.name
    if rank == 0:
        out.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.padding_side = "left"
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    letter_ids = [tok.encode(L, add_special_tokens=False)[0] for L in LETTERS]
    template = (ROOT / "config" / f"prompt_{args.prompt_version}.txt").read_text()

    train_df = load_split("train", args.labels, args.size)
    val_df = load_split("val", args.labels)
    train_ds, val_ds = Items(train_df, template, tok, args.max_len), Items(val_df, template, tok, args.max_len)
    sampler = DistributedSampler(train_ds, num_replicas=world, rank=rank, shuffle=True, seed=args.seed, drop_last=True)
    vsampler = DistributedSampler(val_ds, num_replicas=world, rank=rank, shuffle=False)
    col = lambda b: collate(b, pad_id)
    train_dl = DataLoader(train_ds, batch_size=args.batch_per_gpu, sampler=sampler, collate_fn=col, num_workers=4, drop_last=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch_per_gpu * 2, sampler=vsampler, collate_fn=col, num_workers=4)

    accum = max(1, args.global_batch // (args.batch_per_gpu * world))
    steps_per_epoch = len(train_dl) // accum
    total_steps = args.max_steps or max(1, int(steps_per_epoch * args.epochs))

    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(device)
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    ckpt = out / "checkpoint-last"
    if args.resume and ckpt.exists():
        model = PeftModel.from_pretrained(model, ckpt / "adapter", is_trainable=True)
    else:
        model = get_peft_model(model, LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0.05,
                                                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                                 "gate_proj", "up_proj", "down_proj"]))
    if rank == 0:
        model.print_trainable_parameters()
    ddp = DDP(model, device_ids=[local]) if world > 1 else model
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
    sched = get_cosine_schedule_with_warmup(opt, int(0.03 * total_steps), total_steps)
    step, best = 0, -1.0
    if args.resume and ckpt.exists():
        state = torch.load(ckpt / "state.pt", map_location="cpu", weights_only=False)
        opt.load_state_dict(state["optimizer"]); sched.load_state_dict(state["scheduler"])
        step, best = state["step"], state["best_macro_f1"]
        if rank == 0:
            print(f"resumed at step {step}")

    if rank == 0:
        print(f"train {len(train_df):,} rows, val {len(val_df):,}; world {world}, batch/gpu {args.batch_per_gpu}, "
              f"accum {accum}, global batch {args.batch_per_gpu * world * accum}; {total_steps} steps")
    timing = {"world_size": world, "batch_per_gpu": args.batch_per_gpu, "accum": accum, "step_seconds": []}

    def save(tag):
        if rank != 0:
            return
        d = out / tag
        (d / "adapter").mkdir(parents=True, exist_ok=True)
        model.save_pretrained(d / "adapter")
        if tag == "checkpoint-last":
            torch.save({"optimizer": opt.state_dict(), "scheduler": sched.state_dict(), "step": step,
                        "best_macro_f1": best}, d / "state.pt")

    ddp.train()
    epoch = step // max(steps_per_epoch, 1)
    done = step >= total_steps
    while not done:
        sampler.set_epoch(epoch)
        skip = (step % max(steps_per_epoch, 1)) * accum if epoch == step // max(steps_per_epoch, 1) else 0
        t_step, micro = time.time(), 0
        for b_i, (ids, mask, y, soft) in enumerate(train_dl):
            if b_i < skip:
                continue  # resume mid-epoch: same order, skip batches already used
            ids, mask, y, soft = ids.to(device), mask.to(device), y.to(device), soft.to(device)
            sync = (micro + 1) % accum == 0
            ctx = ddp.no_sync() if (world > 1 and not sync) else torch.enable_grad()
            with ctx:
                lg = letter_logits(ddp, ids, mask, letter_ids)
                loss = (F.kl_div(F.log_softmax(lg, -1), soft / soft.sum(-1, keepdim=True), reduction="batchmean")
                        if args.soft else F.cross_entropy(lg, y)) / accum
                loss.backward()
            micro += 1
            if not sync:
                continue
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
            step += 1
            torch.cuda.synchronize()
            timing["step_seconds"].append(round(time.time() - t_step, 4))
            t_step = time.time()
            if rank == 0 and step % 20 == 0:
                print(f"step {step}/{total_steps} loss {loss.item() * accum:.4f} lr {sched.get_last_lr()[0]:.2e} "
                      f"{timing['step_seconds'][-1]:.2f}s/step", flush=True)
            if step % args.eval_every == 0 or step == total_steps:
                m = evaluate(model, val_dl, letter_ids, device, world)
                if rank == 0:
                    m.update(step=step, time=time.time())
                    with open(out / "metrics.jsonl", "a") as fh:
                        fh.write(json.dumps(m) + "\n")
                    print(f"eval step {step}: macro F1 {m['macro_f1']:.4f} acc {m['accuracy']:.4f}", flush=True)
                    if m["macro_f1"] > best:
                        best = m["macro_f1"]
                        save("best_adapter")
            if step % args.save_every == 0 or step == total_steps:
                save("checkpoint-last")
            if step >= total_steps:
                done = True
                break
        epoch += 1

    if rank == 0:
        s = timing["step_seconds"][5:] or timing["step_seconds"]  # skip warm-up steps
        timing.update(steps=len(timing["step_seconds"]), median_step_seconds=float(np.median(s)) if s else None,
                      samples_per_second=(args.batch_per_gpu * world * accum / float(np.median(s))) if s else None,
                      best_val_macro_f1=best, train_rows=len(train_df), args=vars(args))
        (out / "timing.json").write_text(json.dumps(timing, indent=2))
        print(f"done: best val macro F1 {best:.4f}; median {timing['median_step_seconds']}s/step")
    if world > 1:
        dist.barrier()
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
