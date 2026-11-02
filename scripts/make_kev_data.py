"""Turn Jev's labels into Kev training records, and draw the evaluation sample.

Each record is one filing in Kev's training format (a System One request plus a label on every question). The label is
Jev's answer and the target is Jev's full probability distribution, so the student learns from the teacher's soft labels.
Filings Jev calls "not a CEO change" get only the status question: Jev answers why and future for every filing, but
they mean nothing when the CEO is not leaving.

    $PY scripts/make_kev_data.py                    # train.jsonl, valid.jsonl, test1000.jsonl in $WORK/data
    $PY scripts/make_kev_data.py --neg-ratio 1 --max-train 20000

Splits are Jev's, by filing year: train 2004-2018, valid 2019-2021, test 2022-2026.
  --neg-ratio   in train, keep this many "not a CEO change" filings per CEO change (87% of filings are not)
  --max-train   cap the training file (records are shuffled first)
The test sample is 1,000 test-split filings stratified by Jev's status (300 not a CEO change, 700 across the others,
proportional to the square root of each status's size, at least 40 each), with weights back to the whole test split,
the same design as Alex Storer's eval1000. Its parquet keeps Jev's answers for scoring.
"""
import argparse
import json
import math
import os

import pandas as pd

from questions import REASON, STATUS, questions, state

SEED = 502


def record(r):
    q = questions(with_why=r.status != 1)
    q["status"]["label"] = STATUS[r.status]
    q["status"]["target"] = {STATUS[k]: float(getattr(r, f"p_status_{k}")) for k in STATUS}
    if r.status != 1:
        q["why"]["label"] = REASON[r.why]
        q["why"]["target"] = {REASON[k]: float(getattr(r, f"p_why_{k}")) for k in REASON}
        q["future"]["label"] = bool(r.p_future > 0.5)
        q["future"]["target"] = {"false": 1 - float(r.p_future), "true": float(r.p_future)}
    return {"state": state(r.company_name, str(r.date_filed), r.text_502), "questions": q, "_meta": {"id": r.accession}}


def write(df, path):
    with open(path, "w") as f:
        for r in df.itertuples():
            f.write(json.dumps(record(r)) + "\n")
    print(f"{path}: {len(df):,} records, {int(df.ceo_change.sum()):,} CEO changes")


def stratified_test(test, n=1000, n_not_ceo=300, floor=40):
    counts = test.status.value_counts().sort_index()
    ceo = counts.drop(1)
    rest = n - n_not_ceo
    alloc = {s: max(floor, rest * math.sqrt(c) / sum(math.sqrt(x) for x in ceo)) for s, c in ceo.items()}
    big = [s for s, v in alloc.items() if v > floor]
    scale = (rest - floor * (len(alloc) - len(big))) / sum(alloc[s] for s in big)
    alloc = {s: int(round(v * scale)) if s in big else floor for s, v in alloc.items()}
    alloc[max(alloc, key=alloc.get)] += rest - sum(alloc.values())
    alloc = {1: n_not_ceo, **alloc}
    parts = [test[test.status == s].sample(k, random_state=SEED + int(s)).assign(weight=counts[s] / k) for s, k in alloc.items()]
    return pd.concat(parts).sort_values("accession")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--neg-ratio", type=float, default=1.0)
    ap.add_argument("--max-train", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(os.environ.get("WORK", "."), "data"))
    a = ap.parse_args()
    d = pd.read_parquet(os.path.join(os.environ["DATA"], "item502_v1.parquet"))
    d = d[d.labeled]
    d["status"], d["why"] = d.status.astype(int), d.why.astype(int)
    os.makedirs(a.out, exist_ok=True)

    tr = d[d.split == "train"]
    pos, neg = tr[tr.ceo_change], tr[~tr.ceo_change]
    neg = neg.sample(min(len(neg), int(len(pos) * a.neg_ratio)), random_state=SEED)
    tr = pd.concat([pos, neg]).sample(frac=1, random_state=SEED)
    if a.max_train:
        tr = tr.head(a.max_train)
    write(tr, os.path.join(a.out, "train.jsonl"))

    va = d[d.split == "valid"]
    va = pd.concat([va[va.ceo_change], va[~va.ceo_change].sample(int(va.ceo_change.sum()), random_state=SEED)]).sample(n=2000, random_state=SEED)
    write(va, os.path.join(a.out, "valid.jsonl"))

    te = stratified_test(d[d.split == "test"])
    te.drop(columns=["text_502"]).to_parquet(os.path.join(a.out, "test1000.parquet"), index=False)
    write(te, os.path.join(a.out, "test1000.jsonl"))


if __name__ == "__main__":
    main()
