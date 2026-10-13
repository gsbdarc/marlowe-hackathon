"""Stage 7 report: combine teacher shards and run the Stage 7 checks.

Reads data/teacher/<run_id>/*-shard-*.parquet and run.json. Writes
data/teacher/<run_id>/report.json and, for a full run, data/final/teacher_labels.parquet.

Checks (runbook Stage 7, Stop and ask): among keyword-hit items, no label under 1% or over
90%; mean confidence at least 0.8; invalid outputs at most 0.5%.
Throughput and GPU-hours come from the per-shard timings, times the GPUs used.

  python scripts/07_report.py --run-id pilot --gpus 8
  python scripts/07_report.py --run-id full --gpus 8 --write-final
"""

import argparse
import os
import glob
import json
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("CYBER_ROOT", Path(__file__).resolve().parent.parent))
FINAL = ROOT / "data" / "final"
TEACHER = ROOT / "data" / "teacher"
SAMPLE_FILES = {"train": "train_400k.parquet", "val": "val.parquet", "test": "test.parquet",
                "test_incident_slice": "test_incident_slice.parquet"}
OUT_COLS = ["para_id", "label", "confidence", "p_A", "p_B", "p_C", "p_D", "p_E", "use_for_training", "invalid",
            "teacher_model", "teacher_revision", "prompt_version", "run_id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--gpus", type=int, default=8, help="GPUs the run used, for GPU-hours")
    ap.add_argument("--write-final", action="store_true", help="write data/final/teacher_labels.parquet")
    args = ap.parse_args()
    d = TEACHER / args.run_id
    lab = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(d / "*-shard-*.parquet")))], ignore_index=True)
    run = json.loads((d / "run.json").read_text())

    meta = pd.concat([pd.read_parquet(FINAL / SAMPLE_FILES[s], columns=["para_id", "kw_terms", "kw_core", "in_random_sample", "section", "fiscal_year"])
                      for s in lab["sample"].unique()]).drop_duplicates("para_id")
    x = lab.merge(meta, on="para_id", how="left")
    x["kw_hit"] = x.kw_terms.map(lambda t: t is not None and len(t) > 0)
    valid = x[~x.invalid]
    kw = valid[valid.kw_hit]
    dist_kw = kw.label.value_counts(normalize=True).reindex(["NONE", "RISK", "GOVERNANCE", "INCIDENT", "PRODUCT"]).fillna(0)

    secs = sum(s["seconds"] for s in run["shards"])
    items = sum(s["items"] for s in run["shards"])
    flags = {
        "label_under_1pct_of_keyword_hits": [k for k, v in dist_kw.items() if v < 0.01],
        "label_over_90pct_of_keyword_hits": [k for k, v in dist_kw.items() if v > 0.90],
        "mean_confidence_under_0.8": bool(valid.confidence.mean() < 0.8),
        "invalid_over_0.5pct": bool(x.invalid.mean() > 0.005),
    }
    report = {
        "run_id": args.run_id, "model": run.get("model"), "revision": run.get("revision"),
        "vllm_version": run.get("vllm_version"), "tensor_parallel": run.get("tensor_parallel"),
        "expert_parallel": run.get("expert_parallel"),
        "items": len(x), "items_per_second": round(items / secs, 2) if secs else None,
        "gpu_hours": round(secs * args.gpus / 3600, 2),
        "gpu_hours_per_100k_items": round(secs * args.gpus / 3600 / items * 1e5, 2) if items else None,
        "invalid_share": round(float(x.invalid.mean()), 5),
        "mean_confidence": round(float(valid.confidence.mean()), 4),
        "share_confidence_below_0.7": round(float((valid.confidence < 0.7).mean()), 4),
        "mean_letter_mass": round(float(valid.letter_mass.mean()), 4),
        "labels_all": {k: int(v) for k, v in valid.label.value_counts().items()},
        "labels_keyword_hits_share": {k: round(float(v), 4) for k, v in dist_kw.items()},
        "labels_random_sample": {k: int(v) for k, v in valid[valid.in_random_sample == True].label.value_counts().items()},
        "random_sample_not_none_share": round(float((valid[valid.in_random_sample == True].label != "NONE").mean()), 4)
        if (valid.in_random_sample == True).any() else None,
        "invalid_top_tokens": {str(k): int(v) for k, v in x[x.invalid].top_token.value_counts().head(10).items()},
        "stop_and_ask": flags,
    }
    (d / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if args.write_final:
        lab[OUT_COLS].to_parquet(FINAL / "teacher_labels.parquet", index=False)
        print(f"wrote {FINAL / 'teacher_labels.parquet'} ({len(lab):,} rows)")


if __name__ == "__main__":
    main()
