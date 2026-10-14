"""Kev records from the frozen samples and the teacher labels: one System One request per paragraph.

The state is what the teacher saw (section heading, previous paragraph, paragraph) as named fields; the one question
is codebook v1 as a `choice` with five named options. The label is the teacher's top letter; with --soft each record
also carries the teacher's five probabilities as `target`, so kev.train fits them instead (distillation).

  train.jsonl        train_400k rows in the --size subset with use_for_training (teacher confidence >= 0.7)
  calibration.jsonl  val (2,000): fits the temperature, never scored
  development.jsonl  test (5,000): the scores
  incident.jsonl     test_incident_slice (500): reported on its own
Validation and test drop only invalid teacher outputs, as Stage 10 does.

  $KEV_VENV/bin/python kev/scripts/k02_to_jsonl.py --size 25k --out kev/data/hard-25k
  $KEV_VENV/bin/python kev/scripts/k02_to_jsonl.py --size 25k --soft --out kev/data/soft-25k
"""

import argparse
import json
import os
from pathlib import Path

import pandas as pd

DATA = Path(os.environ.get("CYBER_DATA", "/zfs/projects/darc/marlowe_hackathon/cyber-distill/data/final"))
SUBSET_COL = {"25k": "in_25k", "200k": "in_200k", "400k": None}
FILES = {"train": "train_400k.parquet", "calibration": "val.parquet", "development": "test.parquet",
         "incident": "test_incident_slice.parquet"}
# Teacher letter -> Kev option name. NONE is `not_cyber`, so it is never confused with the "none of these" options
# kev.train inserts at random (kev.data.NONE_OPTIONS).
OPTION = {"A": "not_cyber", "B": "risk", "C": "governance", "D": "incident", "E": "product"}
LABEL_TO_OPTION = dict(zip(["NONE", "RISK", "GOVERNANCE", "INCIDENT", "PRODUCT"], OPTION.values()))
# Codebook v1 (config/prompt_v1.txt), worded as Kev option descriptions.
QUESTION = {
    "type": "choice",
    "instructions": "What cybersecurity content does this paragraph from an SEC filing contain? "
                    "If more than one fits, choose in this order: incident, governance, risk, product, not_cyber.",
    "criteria": {
        "not_cyber": "Not about cybersecurity. Includes breach of contract or covenants, disease viruses, Year 2000 date "
                     "problems, IT outages with no attacker, and privacy-law compliance with no security content.",
        "risk": "Cyber threats described as possible future harm, including general statements that the company has faced "
                "attacks before.",
        "governance": "How the company manages cyber risk, such as security leadership, board oversight, frameworks, "
                      "audits, training, insurance or response plans.",
        "incident": "A specific incident that happened to the company, or to a vendor in a way that affected the company, "
                    "with at least one concrete detail (when, what system or data, a consequence, or the response).",
        "product": "Cybersecurity products or services the company sells, or their market.",
    },
}


def state(r):
    """What the teacher saw, as named fields (Kev renders them as `key: value` lines)."""
    return {"section": r.heading or "(none)", "previous paragraph": r.prev_text or "(none)", "paragraph": r.text}


def record(r, soft):
    q = {**QUESTION, "label": LABEL_TO_OPTION[r.label]}
    if soft:
        q["target"] = {OPTION[L]: float(getattr(r, f"p_{L}")) for L in OPTION}
    return {"state": state(r), "questions": {"cyber": q}, "_meta": {"id": r.para_id, "group_id": r.para_id}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", choices=list(SUBSET_COL), required=True)
    ap.add_argument("--out", required=True, help="directory for the four JSONL files")
    ap.add_argument("--labels", default=str(DATA / "teacher_labels.parquet"))
    ap.add_argument("--soft", action="store_true", help="add the teacher's five probabilities as each question's target")
    args = ap.parse_args()

    labels = pd.read_parquet(args.labels, columns=["para_id", "label", "p_A", "p_B", "p_C", "p_D", "p_E",
                                                    "use_for_training", "invalid"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {"labels": args.labels, "size": args.size, "soft": args.soft, "partitions": {}}
    for part, name in FILES.items():
        df = pd.read_parquet(DATA / name).merge(labels, on="para_id", how="inner")
        if part == "train":
            if SUBSET_COL[args.size]:
                df = df[df[SUBSET_COL[args.size]]]
            df = df[df.use_for_training]
        else:
            df = df[~df.invalid]
        with (out / f"{part}.jsonl").open("w", encoding="utf-8") as f:
            for r in df.itertuples(index=False):
                f.write(json.dumps(record(r, args.soft), ensure_ascii=False) + "\n")
        mix = df.label.map(LABEL_TO_OPTION).value_counts(normalize=True).round(4).to_dict()
        summary["partitions"][part] = {"records": len(df), "label_share": mix}
        print(f"{part}: {len(df):,} records; labels {mix}")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
