"""Fine-tune a released Kev checkpoint on the cyber records, calibrate it, and score it against the untouched checkpoint.

The Yens port of the kev-finetune skill's Modal `train` (skills/kev-finetune/scripts/kev_modal.py::run_train at
KEV_REF), same steps and defaults:
  1. kev.train --init_from <checkpoint>: warm-start its LoRA and pointer head, one epoch on train.jsonl mixed with 2,000
     replay records from Kev's own recipe (evals/v7/decision-v7) so it keeps what it knew. Batch, accumulation and
     gradient checkpointing come from the checkpoint's own training args; lr too, capped at 5e-5.
  2. Fit one temperature on calibration.jsonl (min NLL) and write it into the checkpoint.
  3. Score development.jsonl at that temperature, and the init checkpoint the same way (its own fit), with a paired
     bootstrap of the difference; then a forgetting check on 300 public decision-v7 development groups.
Two changes for this task: --max_state 1280 (Kev's default 384 would drop 14% of training paragraphs, the long ones),
and the project's own metrics (macro F1, per-label F1, confusion) on development and the incident slice.

Writes kev/runs/<name>/: checkpoint/ (adapter, head.pt with the temperature), train.log, result.json, errors.jsonl
(wrong development answers, most confident first), and the prediction dumps. Names are never reused.

  $KEV_VENV/bin/python kev/scripts/k03_train.py --data kev/data/hard-25k --name kev4b-hard-25k --init-from $KEV_4B
"""

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from kev.benchmark import evaluate_records
from kev.checkpoint import Checkpoint, LoadOptions, read_meta, write_meta
from kev.data import load_records
from kev.metrics import fit_temperature, grouped_metrics, metrics, paired_bootstrap, probabilities_at_temperature
from kev.model import training_context
from kev.predictors import LocalPredictor
from kev.suite import load_split, write_json, write_jsonl

KEV_HOME = Path(os.environ["KEV_HOME"])
SUITE = KEV_HOME / "evals" / "v7" / "decision-v7"
RUNS = Path(__file__).resolve().parent.parent / "runs"
MAX_DELTA_LR = 5e-5
OPTIONS = ["not_cyber", "risk", "governance", "incident", "product"]


def train(cmd, log_path):
    with log_path.open("w", encoding="utf-8") as log, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                                       text=True, cwd=KEV_HOME) as proc:
        for line in proc.stdout:
            log.write(line); log.flush()
            if line.startswith(("ep", "saved", "device", "delta", "replay", "dropped")) or "Error" in line or "Traceback" in line:
                print(line.rstrip(), flush=True)
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd, f"kev.train failed; see {log_path}")


def score(run, records, out, context, calibration=None):
    """Raw-logit predictor; temperature fitted on `calibration` when given, then `records` scored at it."""
    predictor = LocalPredictor(run, "cuda", LoadOptions(temperature=1.0), context=context)
    try:
        T = 1.0
        if calibration:
            _, cal_rows = evaluate_records(calibration, predictor, out / "calibration")
            T = fit_temperature(cal_rows, aggregation="micro")
        report, rows = evaluate_records(records, predictor, out / "scored", T)
        return report, rows, T
    finally:
        del predictor; gc.collect(); torch.cuda.empty_cache()


def tempered(rows, T):
    return [{**r, "p": probabilities_at_temperature(r, T).tolist()} for r in rows]


def label_scores(rows, T):
    """Macro F1, per-option F1 and the confusion matrix (rows = label, columns = prediction), as in Stage 10/12."""
    gold = np.array([OPTIONS.index(r["keys"][r["label"]]) for r in rows])
    pred = np.array([OPTIONS.index(r["keys"][int(probabilities_at_temperature(r, T).argmax())]) for r in rows])
    f1 = {}
    for k, name in enumerate(OPTIONS):
        tp, fp, fn = ((pred == k) & (gold == k)).sum(), ((pred == k) & (gold != k)).sum(), ((pred != k) & (gold == k)).sum()
        f1[name] = float(2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else None
    present = [v for v in f1.values() if v is not None]
    confusion = {g: {p: int(((gold == i) & (pred == j)).sum()) for j, p in enumerate(OPTIONS)} for i, g in enumerate(OPTIONS)}
    return {"macro_f1": float(np.mean(present)), "f1": f1, "accuracy": float((pred == gold).mean()), "n": len(rows),
            "confusion": confusion}


def summary(rows, T):
    clean = [r for r in rows if r["variant"] == "clean"]
    return {"temperature": T, "raw": metrics(clean), "calibrated": metrics(clean, T),
            "labels": label_scores(clean, T), "per_question": grouped_metrics(clean, "question", T)}


def errors(rows, records, T, limit=200):
    by_id = {r["_meta"]["id"]: r for r in records}
    out = []
    for r in rows:
        p = probabilities_at_temperature(r, T); i = int(p.argmax())
        if i != r["label"]:
            out.append({"id": r["id"], "confidence": round(float(p[i]), 3), "predicted": r["keys"][i], "label": r["keys"][r["label"]],
                        "probabilities": {k: round(float(v), 3) for k, v in zip(r["keys"], p)}, "state": by_id[r["id"]]["state"]})
    return sorted(out, key=lambda e: -e["confidence"])[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="directory from k02_to_jsonl.py")
    ap.add_argument("--name", required=True, help="run name; outputs in kev/runs/<name>/, never reused")
    ap.add_argument("--init-from", default=os.environ.get("KEV_4B", "jaredpalmer/kev-4b@v1.0"))
    ap.add_argument("--max-state", type=int, default=1280)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--lr", type=float, default=0.0, help="0 = the checkpoint's own delta lr, capped at 5e-5")
    ap.add_argument("--batch", type=int, default=0, help="0 = the checkpoint's own")
    ap.add_argument("--accum", type=int, default=0, help="0 = the checkpoint's own")
    ap.add_argument("--replay", type=int, default=2000)
    ap.add_argument("--p-none-pair", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--regression", type=int, default=300, help="public decision-v7 development groups; 0 skips the check")
    ap.add_argument("--no-baseline", action="store_true", help="skip scoring the init checkpoint")
    ap.add_argument("--max-steps", type=int, default=0, help="smoke tests: stop training after this many optimizer steps")
    ap.add_argument("--eval-limit", type=int, default=0, help="smoke tests: score only the first N records of each file")
    args = ap.parse_args()

    started = time.time()
    out = RUNS / args.name
    if out.exists():
        raise SystemExit(f"{out} exists; run names are never reused")
    out.mkdir(parents=True)
    data = Path(args.data).resolve()
    init = Checkpoint(args.init_from)
    meta, a = init.meta, init.meta.extra["args"]
    cfg = {"lr": args.lr or min(a["lr"], MAX_DELTA_LR), "batch": args.batch or a["batch"], "accum": args.accum or a["accum"],
           "checkpointing": a["checkpointing"], "epochs": args.epochs, "seed": args.seed, "replay": args.replay,
           "p_none_pair": args.p_none_pair, "max_state": args.max_state, "max_steps": args.max_steps}
    write_json(out / "config.json", {"name": args.name, "init_from": args.init_from, "init_resolved": str(init.path), "base": meta.base,
                                     "base_revision": meta.base_revision, "data": str(data), "config": cfg,
                                     "kev_ref": subprocess.run(["git", "-C", str(KEV_HOME), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
                                     "gpu": torch.cuda.get_device_name(0), "slurm_job": os.environ.get("SLURM_JOB_ID")})

    run = out / "checkpoint"
    cmd = [sys.executable, "-m", "kev.train", "--data", data / "train.jsonl", "--init_from", args.init_from, "--out", run,
           "--device", "cuda", "--dtype", "bf16", "--base", meta.base, "--lora", meta.lora, "--head_dim", meta.head_dim,
           "--lora_targets", a["lora_targets"], "--option_isolation", int(meta.option_isolation),
           "--special_embeddings", int(meta.special_embeddings), "--weights_dtype", meta.weights_dtype,
           "--epochs", cfg["epochs"], "--lr", cfg["lr"], "--batch", cfg["batch"], "--accum", cfg["accum"],
           "--checkpointing", cfg["checkpointing"], "--seed", cfg["seed"], "--p_none_pair", cfg["p_none_pair"],
           "--max_state", cfg["max_state"]]
    if meta.base_revision: cmd += ["--base_revision", meta.base_revision]
    if cfg["replay"]: cmd += ["--suite", SUITE, "--replay", cfg["replay"]]
    if cfg["max_steps"]: cmd += ["--max_steps", cfg["max_steps"]]
    cmd = [str(c) for c in cmd]
    print("training: " + " ".join(cmd[2:]), flush=True)
    t0 = time.time()
    train(cmd, out / "train.log")
    train_seconds = round(time.time() - t0)

    context = {**training_context(args.max_state), "truncate": False}
    load = lambda part: load_records(data / f"{part}.jsonl")[:args.eval_limit or None]
    calibration, development, incident = load("calibration"), load("development"), load("incident")
    print(f"scoring {args.name}: {len(calibration)} calibration, {len(development)} development, {len(incident)} incident records", flush=True)
    report, rows, T = score(str(run), development, out / "finetuned", context, calibration)
    _, inc_rows, _ = score(str(run), incident, out / "finetuned-incident", context)
    m = read_meta(run); m.temperature = T
    m.extra["temperature_fit"] = {"rows": "calibration.jsonl", "n": len(calibration), "method": "min NLL, micro, kev.metrics.fit_temperature", "value": T}
    write_meta(run, m)   # the checkpoint now serves calibrated probabilities by default
    result = {"name": args.name, "init_from": args.init_from, "config": cfg, "train_seconds": train_seconds,
              "development": summary(rows, T), "incident_slice": summary(inc_rows, T)}
    write_jsonl(out / "errors.jsonl", errors(rows, development, T))

    if not args.no_baseline:
        print(f"scoring the baseline {args.init_from} on the same records", flush=True)
        _, b_rows, b_T = score(args.init_from, development, out / "baseline", context, calibration)
        _, b_inc, _ = score(args.init_from, incident, out / "baseline-incident", context)
        result["baseline"] = {"run": args.init_from, "development": summary(b_rows, b_T), "incident_slice": summary(b_inc, b_T)}
        result["bootstrap"] = {k: paired_bootstrap(tempered(rows, T), tempered(b_rows, b_T), metric=k, aggregation="micro")
                               for k in ("acc", "brier", "ece")}
    if args.regression:
        groups = {}
        for r in load_split(str(SUITE), "development"):
            groups.setdefault(r["_meta"]["group_id"], []).append(r)
        chosen = np.random.default_rng(args.seed).choice(sorted(groups), min(args.regression, len(groups)), replace=False)
        sample = [r for g in chosen for r in groups[g]]
        print(f"regression check: {len(sample)} public decision-v7 development records", flush=True)
        _, r_rows, _ = score(str(run), sample, out / "regression-finetuned", context)
        result["regression"] = {"n": len(sample), "finetuned": metrics([r for r in r_rows if r["variant"] == "clean"])}
        if not args.no_baseline:
            _, rb_rows, _ = score(args.init_from, sample, out / "regression-baseline", context)
            result["regression"]["baseline"] = metrics([r for r in rb_rows if r["variant"] == "clean"])
    result["wall_seconds"] = round(time.time() - started)
    write_json(out / "result.json", result)

    for title, block in [("finetuned", result["development"])] + ([("baseline", result["baseline"]["development"])] if "baseline" in result else []):
        c, lab = block["calibrated"], block["labels"]
        print(f"{title:9s} T={block['temperature']:.2f}  acc {c['acc']:.3f}  macro F1 {lab['macro_f1']:.3f}  "
              f"incident F1 {lab['f1']['incident'] or 0:.3f}  brier {c['brier']:.3f}  ece {c['ece']:.3f}  "
              f"coverage@5% {c.get('coverage_at_5pct_error', float('nan')):.2f}", flush=True)
    print(f"done in {result['wall_seconds']}s; {out}/result.json", flush=True)


if __name__ == "__main__":
    main()
