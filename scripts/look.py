"""Look at the data before training on it: how many filings, what Jev said, and a few examples.

    $PY scripts/look.py                      # counts by split, status and reason
    $PY scripts/look.py --examples 3         # also print 3 filings Jev calls a CEO change

Reads $DATA/item502_v1.parquet (source env/yens.sh or env/marlowe.sh first).
"""
import argparse
import os
import textwrap

import pandas as pd

from questions import REASON_SHORT, STATUS_SHORT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", type=int, default=0)
    a = ap.parse_args()
    d = pd.read_parquet(os.path.join(os.environ["DATA"], "item502_v1.parquet"))
    d = d[d.labeled]
    print(f"{len(d):,} labeled filings, {int(d.ceo_change.sum()):,} CEO changes, filed {d.date_filed.min()} to {d.date_filed.max()}\n")
    print(pd.crosstab(d.split, d.ceo_change, margins=True).rename(columns={False: "not a CEO change", True: "CEO change"}), "\n")
    print("What Jev says happens to the CEO (status):")
    print(d.status.map(STATUS_SHORT).value_counts().to_string(), "\n")
    ceo = d[d.ceo_change]
    print("Why the CEO leaves, according to the filing (CEO changes only):")
    print(ceo.why.map(REASON_SHORT).value_counts().to_string(), "\n")
    print(f"Median length: {int(d.words.median())} words; 99th percentile {int(d.words.quantile(.99))} words")
    for r in ceo.sample(a.examples, random_state=1).itertuples() if a.examples else []:
        print(f"\n--- {r.company_name}, filed {r.date_filed} | Jev: {STATUS_SHORT[r.status]} "
              f"({r.status_conf:.2f}), why: {REASON_SHORT[r.why]}")
        print(textwrap.fill(r.text_502[:1200], 110))


if __name__ == "__main__":
    main()
