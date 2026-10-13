"""Stage 0: list 10-K, 10-Q and 8-K filings in the Yens EDGAR mirror from Redivis.

Writes data/interim/edgar_index_{10k,10q,8k}.parquet, a JSON query record next to
each, and the per-year filing counts to reports/data_report.md. Amendments are
listed too (Stage 1 drops them) so the report can count them.

Small-business forms are coded without a hyphen in this table (10KSB, 10KSB40,
10KT405, 10QSB), unlike the SEC form names.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import redivis
from dotenv import load_dotenv

TABLE = "stanfordgsblibrary.edgar_filings:dq12:v3_206.edgar_filings:kc0j"
TABLE_VERSION = "v3_206"

FAMILIES = {
    "10k": ["10-K", "10-K405", "10KSB", "10KSB40", "10-KT", "10KT405",
            "10-K/A", "10-K405/A", "10KSB/A", "10KSB40/A", "10-KT/A", "10KT405/A"],
    "10q": ["10-Q", "10QSB", "10-QT", "10-Q/A", "10QSB/A", "10-QT/A"],
    "8k": ["8-K"],
}
# 8-Ks are only needed from the Item 1.05 effective date on.
MIN_DATE = {"10k": "1996-01-01", "10q": "1996-01-01", "8k": "2023-12-18"}

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "interim"
REPORT = ROOT / "reports" / "data_report.md"


def query_family(name):
    forms = ", ".join(f"'{f}'" for f in FAMILIES[name])
    sql = f"""
SELECT cik, company_name, form_type, date_filed, year, quarter, accession, filepath
FROM `{TABLE}`
WHERE form_type IN ({forms}) AND date_filed >= '{MIN_DATE[name]}'
ORDER BY date_filed, cik, accession
""".strip()
    df = redivis.query(sql).to_pandas_dataframe(progress=False)
    out = OUT_DIR / f"edgar_index_{name}.parquet"
    df.to_parquet(out, index=False)
    counts = df.groupby(["year", "form_type"]).size().unstack(fill_value=0)
    record = {
        "table": TABLE,
        "table_version": TABLE_VERSION,
        "queried_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sql": sql,
        "rows": len(df),
        "latest_date_filed": str(df.date_filed.max()),
        "counts_by_year_form": {str(y): {k: int(v) for k, v in r.items() if v} for y, r in counts.iterrows()},
    }
    (OUT_DIR / f"edgar_index_{name}.json").write_text(json.dumps(record, indent=2))
    print(f"{name}: {len(df):,} rows -> {out}")
    return counts


def to_markdown(df):
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [f"{v:,}" for v in r] for i, r in zip(df.index, df.values)]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                     + ["| " + " | ".join(r) + " |" for r in rows])


def year_flags(series):
    """Years missing or more than 30% below the mean of their neighbors (Stage 0 check)."""
    flags = []
    years = list(series.index)
    for i, y in enumerate(years):
        nbrs = [series.iloc[j] for j in (i - 1, i + 1) if 0 <= j < len(years)]
        if nbrs and series.iloc[i] < 0.7 * sum(nbrs) / len(nbrs):
            flags.append(int(y))
    full = set(range(min(years), max(years) + 1))
    return flags, sorted(full - set(years))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--families", nargs="+", default=list(FAMILIES), choices=list(FAMILIES))
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Data report", "", "## Filings (Stage 0)", "",
             f"Source: Redivis `{TABLE}`. `year` is the filing year, not the fiscal year.", ""]
    for name in args.families:
        counts = query_family(name)
        originals = [c for c in counts.columns if not c.endswith("/A")]
        counts["originals"] = counts[originals].sum(axis=1)
        flags, missing = year_flags(counts.loc[counts.index < counts.index.max(), "originals"])
        lines += [f"### {name}", "", to_markdown(counts), "",
                  f"Years more than 30% below neighbors (originals, excluding the partial last year): {flags or 'none'}. "
                  f"Missing years: {missing or 'none'}.", ""]
    REPORT.write_text("\n".join(lines))
    print(f"report -> {REPORT}")


if __name__ == "__main__":
    main()
