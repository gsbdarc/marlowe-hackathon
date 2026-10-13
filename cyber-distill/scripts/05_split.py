"""Stage 5: company split. Frozen once written.

split = int(sha256(str(cik)), 16) % 10: 0-7 train, 8 validation, 9 test, for every CIK in
data/final/filings.parquet. Writes data/final/company_split.parquet. If the file exists,
the script recomputes the split and stops with an error if anything differs; it never
overwrites the file. Paragraph files are not rewritten; later stages join on cik.
"""

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "final" / "company_split.parquet"


def split_of(cik):
    v = int(hashlib.sha256(str(cik).encode()).hexdigest(), 16) % 10
    return "train" if v <= 7 else ("val" if v == 8 else "test")


def main():
    ciks = sorted(pd.read_parquet(ROOT / "data" / "final" / "filings.parquet", columns=["cik"]).cik.unique())
    df = pd.DataFrame({"cik": ciks})
    df["split"] = df.cik.map(split_of)
    if OUT.exists():
        old = pd.read_parquet(OUT)
        merged = old.merge(df, on="cik", how="outer", suffixes=("_old", "_new"), indicator=True)
        changed = merged[(merged._merge != "both") | (merged.split_old != merged.split_new)]
        if len(changed):
            raise SystemExit(f"company_split.parquet exists and {len(changed)} CIKs differ; it is frozen, not overwriting")
        print(f"company_split.parquet exists and matches ({len(old):,} CIKs); unchanged")
        return
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT}: {df.split.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
