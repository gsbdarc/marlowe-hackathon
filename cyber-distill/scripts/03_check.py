"""Stage 2-3 checks: combine the per-shard outputs of 02_extract.py.

- data/interim/parse_failures.csv: accession and reason for every failed or empty filing
- data/final/filings.parquet: fills parse_status and adds abs_issuer
  (Regulation AB cited in the main document, or SIC 6189)
- reports/data_report.md: section "Text and paragraphs (Stages 2-3)" with, by fiscal year,
  the parse failure rate and the Item 1A, 1C and 7 detection rates
- data/interim/extract_stats.json: the numbers for the README data card

Item 1A is counted among filings expected to have it: not asset-backed and not saying
Item 1A is not applicable. Item 1C is counted the same way, without the 1A exemption.
Run as a small Slurm job: sbatch slurm/03_check.slurm
"""

import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
REPORT = ROOT / "reports" / "data_report.md"
SECTION = "## Text and paragraphs (Stages 2-3)"
STOP_FAIL_RATE, STOP_DETECT = 0.05, 0.80


def main():
    files = sorted((INTERIM / "extract").glob("status-[0-9]*.parquet"))
    st = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    f = pd.read_parquet(FINAL / "filings.parquet").drop(columns=["parse_status", "abs_issuer"], errors="ignore")
    assert st.accession.is_unique and set(st.accession) == set(f.accession), "status files do not cover filings.parquet"

    f = f.merge(st[["accession", "status", "reg_ab"]].rename(columns={"status": "parse_status"}), on="accession", how="left")
    f["abs_issuer"] = f.reg_ab.fillna(False).astype(bool) | (f.sic == 6189)
    f = f.drop(columns="reg_ab")
    f.to_parquet(FINAL / "filings.parquet", index=False)

    bad = st[st.status != "ok"].merge(f[["accession", "fiscal_year", "form_type"]], on="accession")
    bad[["accession", "fiscal_year", "form_type", "status", "error", "format"]].to_csv(INTERIM / "parse_failures.csv", index=False)

    a = st.merge(f[f.is_annual][["accession", "fiscal_year", "form_type", "abs_issuer"]], on="accession")
    a["not_ok"] = a.status != "ok"
    exp_1a = ~a.abs_issuer & ~a.item_1a_na.fillna(False).astype(bool)
    by = a.groupby("fiscal_year").agg(filings=("accession", "size"), failed=("status", lambda s: (s == "failed").sum()),
                                      empty=("status", lambda s: (s == "empty").sum()), abs_issuer=("abs_issuer", "sum"),
                                      text=("format", lambda s: (s == "text").sum()), html=("format", lambda s: (s == "html").sum()),
                                      ixbrl=("format", lambda s: (s == "ixbrl").sum()))
    by["fail_rate"] = (by.failed + by.empty) / by.filings
    by["item_1a"] = a[exp_1a].groupby("fiscal_year").has_1a.mean()
    by["item_1c"] = a[~a.abs_issuer].groupby("fiscal_year").has_1c.mean()
    by["item_7"] = a.groupby("fiscal_year").has_7.mean()
    by["paragraphs"] = a.groupby("fiscal_year").n_paras.sum()
    pct = ["fail_rate", "item_1a", "item_1c", "item_7"]
    shown = by.copy()
    for c in pct:
        shown[c] = (100 * shown[c]).round(1).map(lambda x: f"{x}%")

    flags = {
        "fail_rate_above_5pct": [int(y) for y in by.index[by.fail_rate > STOP_FAIL_RATE]],
        "item_1a_below_80pct_from_2006": [int(y) for y in by.index[(by.index >= 2006) & (by.item_1a < STOP_DETECT)]],
        "item_1c_below_80pct_from_2024": [int(y) for y in by.index[(by.index >= 2024) & (by.item_1c < STOP_DETECT)]],
    }

    cols = ["n_words", "chunk", "fiscal_year", "section", "form_type"]
    p = ds.dataset(INTERIM / "paragraphs", format="parquet").to_table(columns=cols).to_pandas()
    size_gb = sum(x.stat().st_size for x in (INTERIM / "paragraphs").glob("part-[0-9]*.parquet")) / 1e9
    stats = {
        "parser": f"lxml {import_module('lxml.etree').__version__} (HTML, inline XBRL); regex rules for plain text",
        "filings": len(st), "annual_filings": len(a),
        "status": {k: int(v) for k, v in st.status.value_counts().items()},
        "annual_fail_rate": round(float(a.not_ok.mean()), 5),
        "worst_fail_year": {"fiscal_year": int(by.fail_rate.idxmax()), "rate": round(float(by.fail_rate.max()), 4)},
        "paragraphs_total": len(p),
        "paragraphs_annual": int(p.fiscal_year.notna().sum()),
        "words_median": float(p.n_words.median()), "words_p95": float(p.n_words.quantile(0.95)),
        "paragraphs_from_split": int((p.chunk >= 0).sum()),
        "item_1a_share_fy2006_on": round(float(a[exp_1a & (a.fiscal_year >= 2006)].has_1a.mean()), 4),
        "item_1c_share_fy2024_on": round(float(a[~a.abs_issuer & (a.fiscal_year >= 2024)].has_1c.mean()), 4),
        "item_7_share_all": round(float(a.has_7.mean()), 4),
        "abs_issuer_annual": int(a.abs_issuer.sum()),
        "paragraphs_size_gb": round(size_gb, 2),
        "stop_and_ask": flags,
    }
    (INTERIM / "extract_stats.json").write_text(json.dumps(stats, indent=2))

    lines = [SECTION, "",
             "Annual reports by fiscal year. `fail_rate` counts failed and empty filings. `item_1a` is the share of "
             "filings expected to have Item 1A (not asset-backed, not \"not applicable\") where it was found; "
             "`item_1c` excludes asset-backed issuers. Item 1A is required from fiscal 2005-06 and Item 1C from fiscal 2023-24, "
             "so earlier values count voluntary sections only.", "",
             md_table(shown), "",
             f"Stop-and-ask flags: {flags}. Failures: `data/interim/parse_failures.csv`. Totals: `data/interim/extract_stats.json`.", ""]
    text = REPORT.read_text()
    text = text.split(SECTION)[0].rstrip() + "\n\n" + "\n".join(lines)
    REPORT.write_text(text)
    print(json.dumps(stats, indent=2))


def md_table(df):
    """Markdown table; integers get thousands separators, everything else prints as is."""
    def fmt(v):
        return f"{v:,}" if isinstance(v, int) or (hasattr(v, "is_integer") and float(v).is_integer() and not isinstance(v, float)) else str(v)
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [fmt(v) for v in r] for i, r in zip(df.index, df.astype(object).itertuples(index=False))]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(r) + " |" for r in rows])


if __name__ == "__main__":
    main()
