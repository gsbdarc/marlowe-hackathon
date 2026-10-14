"""A first look at Kev, zero-shot: load a released checkpoint on one GPU and ask it the codebook question about a few
training paragraphs picked by kind (Item 1C, risk factors, Item 1.05 8-Ks, trap terms, no keyword). No labels and
nothing scored: the point is to see that the model loads and answers, and whether the answers look sensible.

It calls the model the way kev.serve does inside (kev/serve.py, `answer`), without the HTTP server:
  request (state + question)  --kev.api.to_record-->  record  --model.encode-->  token ids
  --model.probs-->  one probability per option, with the checkpoint's own temperature applied
in bf16, kev.serve's default on CUDA. Paragraphs come from train_400k (train-split companies), never from val or test.

  $KEV_VENV/bin/python kev/scripts/k01_look.py --run $KEV_4B --out kev/runs/look/kev-4b.jsonl
"""

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
import torch
from kev.api import SystemOneRequest, to_record
from kev.checkpoint import Checkpoint, LoadOptions
from kev.model import SERVE_MAX_BRANCH, SERVE_MAX_STATE

from k02_to_jsonl import DATA, QUESTION, state

SEED = 20261106
PER_KIND = 2
SELLS = re.compile(r"\b(?:we|our)\b.{0,60}\b(?:security|cybersecurity) (?:products|solutions|software|services)\b", re.I)
KINDS = {  # why a paragraph was picked -> rows of train_400k
    "Item 1C, core term": lambda d: (d.section == "1C") & d.kw_core,
    "Item 1A, core term, fiscal 2012+": lambda d: (d.section == "1A") & d.kw_core & (d.fiscal_year >= 2012),
    "8-K Item 1.05": lambda d: d.section == "1.05",
    "incident cue + keyword": lambda d: d.source == "enrich_cue",
    "sells security products?": lambda d: (d.section == "OTHER") & d.kw_core & d.text.str.contains(SELLS),
    "trap: only 'breach'": lambda d: d.terms == ("breach",),
    "trap: only 'virus', fiscal 2020-21": lambda d: (d.terms == ("virus",)) & d.fiscal_year.isin([2020, 2021]),
    "trap: only 'year 2000'": lambda d: d.terms == ("year 2000",),
    "no keyword (random sample)": lambda d: d.source == "random",
}


def pick():
    d = pd.read_parquet(DATA / "train_400k.parquet", columns=["para_id", "fiscal_year", "form_type", "section", "heading",
                                                              "prev_text", "text", "kw_terms", "kw_core", "source"])
    d["terms"] = d.kw_terms.map(tuple)
    for kind, rule in KINDS.items():
        rows = d[rule(d).fillna(False).astype(bool)]
        for r in rows.sample(n=min(PER_KIND, len(rows)), random_state=SEED).itertuples(index=False):
            yield kind, r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="checkpoint: Hub id[@revision] or a local run directory")
    ap.add_argument("--out", required=True, help="JSONL of the answers")
    args = ap.parse_args()

    t0 = time.time()
    ck = Checkpoint(args.run)
    tok, model = ck.load("cuda", LoadOptions(dtype=torch.bfloat16))
    print(f"{args.run}: base {ck.meta.base}, weights {ck.meta.weights}, temperature {model.head.temperature:.2f}; "
          f"loaded in {time.time() - t0:.0f} s, {torch.cuda.memory_allocated() / 1e9:.1f} GB on {torch.cuda.get_device_name(0)}\n",
          flush=True)
    question = {k: QUESTION[k] for k in ("type", "instructions", "criteria")}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad(), out.open("w", encoding="utf-8") as f:
        for n, (kind, r) in enumerate(pick()):
            rec, meta = to_record(SystemOneRequest.model_validate({"state": state(r), "questions": {"cyber": question}}))
            enc = model.encode(tok, rec, max_state=SERVE_MAX_STATE, max_branch=SERVE_MAX_BRANCH, strict=True)
            if n == 0:
                model.probs(enc)  # warm-up: the first call compiles the DeltaNet kernels
            torch.cuda.synchronize(); t = time.perf_counter()
            p = model.probs(enc)[0]
            torch.cuda.synchronize(); ms = 1000 * (time.perf_counter() - t)
            probs = sorted(zip(meta[0]["keys"], p.tolist()), key=lambda kv: -kv[1])
            text = " ".join(r.text.split())
            print(f"[{kind}] fiscal {r.fiscal_year}, {r.form_type}, section {r.section}, keywords: {', '.join(r.terms) or '-'}\n"
                  f"  {text[:400]}{' ...' if len(text) > 400 else ''}\n"
                  f"  -> " + " | ".join(f"{k} {v:.2f}" for k, v in probs) + f"   ({ms:.0f} ms, {len(enc['ids'])} tokens)\n",
                  flush=True)
            f.write(json.dumps({"para_id": r.para_id, "kind": kind, "answer": probs[0][0], "probabilities": dict(probs),
                                "ms": round(ms, 1), "tokens": len(enc["ids"]), "run": args.run}) + "\n")


if __name__ == "__main__":
    main()
