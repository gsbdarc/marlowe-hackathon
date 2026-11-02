"""Score a model's answers against Jev's on the test sample.

Agreement with Jev measures how well the student copies the teacher. "Weighted" uses the sample weights, so it
estimates agreement over the whole 2022-2026 test split rather than over the oversampled rare statuses.

    $PY scripts/score.py $WORK/results/kev-4b-zeroshot.jsonl $WORK/results/kev-4b-step500.jsonl

Prints one row per run and writes <run>_scores.json next to each run.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from questions import REASON, STATUS, STATUS_SHORT

STATUS_CODE = {v: k for k, v in STATUS.items()}
REASON_CODE = {v: k for k, v in REASON.items()}


def load(path):
    rows = {}
    for line in open(path):
        r = json.loads(line)
        if r.get("ok"):
            a = r["answers"]
            rows[r["id"]] = {"status": STATUS_CODE[a["status"]["choice"]], "why": REASON_CODE[a["why"]["choice"]],
                             "future": a["future"]["noul"] > 0.5}
    return rows


def score(sample, path):
    got = load(path)
    s = sample[sample.accession.isin(got)].copy()
    s["m_status"] = s.accession.map(lambda x: got[x]["status"])
    s["m_why"] = s.accession.map(lambda x: got[x]["why"])
    s["m_future"] = s.accession.map(lambda x: got[x]["future"])
    same = s.m_status == s.status
    jev_ceo, m_ceo = s.status != 1, s.m_status != 1
    tp, fp, fn = int((jev_ceo & m_ceo).sum()), int((~jev_ceo & m_ceo).sum()), int((jev_ceo & ~m_ceo).sum())
    out = {"run": os.path.basename(path), "answered": len(s), "of": len(sample),
           "status_agree_weighted": round(float(np.average(same, weights=s.weight)), 3),
           "status_agree_on_ceo_changes": round(float(same[jev_ceo].mean()), 3),
           "ceo_change_f1": round(2 * tp / (2 * tp + fp + fn), 3) if tp else 0.0,
           "ceo_change_precision": round(tp / (tp + fp), 3) if tp + fp else None,
           "ceo_change_recall": round(tp / (tp + fn), 3) if tp + fn else None,
           "reason_agree_on_ceo_changes": round(float((s.m_why == s.why)[jev_ceo].mean()), 3),
           "future_agree_on_ceo_changes": round(float((s.m_future == (s.p_future > 0.5))[jev_ceo].mean()), 3),
           "status_agree_by_jev_status": {STATUS_SHORT[k]: round(float(g.mean()), 3) for k, g in same.groupby(s.status)}}
    summary = path.replace(".jsonl", "_summary.json")
    if os.path.exists(summary):
        out["filings_per_second"] = json.load(open(summary)).get("filings_per_second")
    json.dump(out, open(path.replace(".jsonl", "_scores.json"), "w"), indent=2)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--sample", default=os.path.join(os.environ.get("WORK", "."), "data", "test1000.parquet"))
    a = ap.parse_args()
    sample = pd.read_parquet(a.sample)
    sample["status"], sample["why"] = sample.status.astype(int), sample.why.astype(int)
    res = [score(sample, p) for p in a.runs]
    cols = ["run", "answered", "status_agree_weighted", "status_agree_on_ceo_changes", "ceo_change_f1",
            "reason_agree_on_ceo_changes", "filings_per_second"]
    print(pd.DataFrame(res).reindex(columns=cols).to_string(index=False))
    for r in res:
        print(f"\n{r['run']}: status agreement by Jev's status")
        for k, v in r["status_agree_by_jev_status"].items():
            print(f"  {k:<24} {v:.1%}")


if __name__ == "__main__":
    main()
