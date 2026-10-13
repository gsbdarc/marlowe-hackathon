"""Stage 1b: select the filings the pipeline uses, from the headers read in Stage 1a.

1. Annual reports: 10-K family originals (10-K, 10-K405, 10KSB, 10KSB40, 10-KT, 10KT405).
   Fiscal year = calendar year of CONFORMED PERIOD OF REPORT; keep 1996-2025.
   One per CIK and fiscal year: the earliest-filed original.
2. 8-Ks filed on or after 2023-12-18 whose header lists Item 1.05 or Item 8.01.
3. Follow-ups: for each Item 1.05 8-K, the same company's first 10-Q or 10-K filed after it.

Writes data/final/filings.parquet, data/interim/select_stats.json, and the Filings
section of reports/data_report.md. Runs in a minute on a login node.
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

headers = import_module("01_headers")

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
REPORT = ROOT / "reports" / "data_report.md"

ANNUAL = ["10-K", "10-K405", "10KSB", "10KSB40", "10-KT", "10KT405"]
QUARTERLY = ["10-Q", "10QSB", "10-QT"]
FY_MIN, FY_MAX = 1996, 2025
# The header names most items ("Other Events" is 8.01), but Item 1.05 appears only as
# "<ITEMS>1.05" with no name; match either form.
ITEM_105 = ("material cybersecurity incidents", "<items>1.05")
ITEM_801 = ("other events", "<items>8.01")

COLUMNS = ["accession", "cik", "company_name", "form_type", "filing_date", "period_of_report",
           "fiscal_year", "sic", "sic_from_header", "state_of_inc", "doc_count", "file_bytes", "filepath",
           "is_annual", "is_8k", "is_followup", "has_item_105", "has_item_801", "followup_of",
           "parse_status"]


def load_headers():
    files = sorted((INTERIM / "headers").glob("headers_*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["filing_date"] = pd.to_datetime(df["date_filed"])
    df["company_name"] = df["hdr_company_name"].fillna(df["company_name"])
    return df, [f.stem.split("_")[1] for f in files]


def fill_sic(h, stats):
    """Fill a missing SIC from the same CIK's most common SIC in other filings.

    Many fiscal-2000 headers lack the SIC line (about 25% of that year's filings).
    """
    h["sic_from_header"] = h.sic.notna()
    modal = h[h.sic.notna()].groupby("cik").sic.agg(lambda s: s.mode().iloc[0])
    before = int(h.sic.isna().sum())
    h["sic"] = h.sic.fillna(h.cik.map(modal)).astype("Int64")
    stats["sic_filled_from_other_filings"] = before - int(h.sic.isna().sum())
    return h


def select_annual(h, stats):
    a = h[h.form_type.isin(ANNUAL)].copy()
    stats["annual_read"] = len(a)
    stats["annual_header_errors"] = int((a.status != "ok").sum())
    a = a[a.status == "ok"]
    stats["annual_no_period"] = int(a.period_of_report.isna().sum())
    a = a[a.period_of_report.notna()]
    a["fiscal_year"] = a.period_of_report.dt.year.astype(int)
    out_of_range = ~a.fiscal_year.between(FY_MIN, FY_MAX)
    stats["annual_fy_out_of_range"] = int(out_of_range.sum())
    stats["annual_fy_out_of_range_by_fy"] = {int(k): int(v) for k, v in a[out_of_range].fiscal_year.value_counts().sort_index().items()}
    a = a[~out_of_range]
    stats["annual_in_range_before_dedup"] = len(a)

    a = a.sort_values(["cik", "fiscal_year", "filing_date", "accession"])
    dup = a.duplicated(["cik", "fiscal_year"], keep="first")
    stats["annual_dropped_second_filing"] = int(dup.sum())
    dropped_by_fy = a[dup].fiscal_year.value_counts()
    a = a[~dup]

    # Co-registrants: one accession listed under several CIKs. Keep the CIK with the
    # most selected annual reports (usually the parent), then the lowest CIK.
    n_by_cik = a.cik.map(a.cik.value_counts())
    a = a.assign(_n=n_by_cik).sort_values(["accession", "_n", "cik"], ascending=[True, False, True])
    co = a.duplicated("accession", keep="first")
    stats["annual_dropped_coregistrant"] = int(co.sum())
    a = a[~co].drop(columns="_n")
    a["is_annual"] = True
    return a, dropped_by_fy


def select_8k(h, stats):
    e = h[h.form_type == "8-K"].copy()
    stats["8k_read"] = len(e)
    stats["8k_header_errors"] = int((e.status != "ok").sum())
    items = e.item_info.map(lambda x: list(x) if x is not None else [])
    e["has_item_105"] = items.map(lambda xs: any(x.strip().lower() in ITEM_105 for x in xs))
    e["has_item_801"] = items.map(lambda xs: any(x.strip().lower() in ITEM_801 for x in xs))
    e = e[e.has_item_105 | e.has_item_801].drop_duplicates("accession")
    e["fiscal_year"] = pd.NA
    e["is_8k"] = True
    stats["8k_item_105"] = int(e.has_item_105.sum())
    stats["8k_item_801"] = int(e.has_item_801.sum())
    stats["8k_item_105_companies"] = int(e[e.has_item_105].cik.nunique())
    return e


def select_followups(e8, stats):
    """First 10-Q or 10-K (original) filed after each Item 1.05 8-K, by the same CIK."""
    q = pd.read_parquet(INTERIM / "edgar_index_10q.parquet")
    k = pd.read_parquet(INTERIM / "edgar_index_10k.parquet")
    periodic = pd.concat([q[q.form_type.isin(QUARTERLY)], k[k.form_type.isin(ANNUAL)]], ignore_index=True)
    periodic["filing_date"] = pd.to_datetime(periodic.date_filed)
    inc = e8[e8.has_item_105][["accession", "cik", "filing_date"]].rename(
        columns={"accession": "followup_of", "filing_date": "date_8k"})
    m = inc.merge(periodic, on="cik")
    m = m[m.filing_date > m.date_8k].sort_values(["followup_of", "filing_date", "accession"])
    f = m.drop_duplicates("followup_of", keep="first")
    stats["followup_8k_without_later_filing"] = int(len(inc) - len(f))
    # One row per follow-up filing; several 8-Ks can share one.
    f = f.groupby("accession", as_index=False).agg(
        followup_of=("followup_of", list), cik=("cik", "first"), company_name=("company_name", "first"),
        form_type=("form_type", "first"), filing_date=("filing_date", "first"), filepath=("filepath", "first"))
    stats["followup_filings"] = len(f)
    stats["followup_by_form"] = {k: int(v) for k, v in f.form_type.value_counts().items()}
    return f


def main():
    h, years = load_headers()
    stats = {"filing_years_read": years}

    h = fill_sic(h, stats)
    annual, dropped_by_fy = select_annual(h, stats)
    e8 = select_8k(h, stats)
    fu = select_followups(e8, stats)

    # 10-Q follow-ups were not in Stage 1a; read their headers here (a few hundred files).
    need = fu[~fu.accession.isin(h.accession)]
    recs = pd.DataFrame([headers.process(r) for r in need.itertuples(index=False)]) if len(need) else pd.DataFrame()
    if len(recs):
        for c in ("period_of_report", "filed_as_of"):
            recs[c] = pd.to_datetime(recs[c], format="%Y%m%d", errors="coerce")
    hdr_cols = ["accession", "cik", "period_of_report", "sic", "state_of_inc", "doc_count", "file_bytes", "status"]
    fu_hdr = pd.concat([h[hdr_cols], recs.reindex(columns=hdr_cols)], ignore_index=True).drop_duplicates(["accession", "cik"])
    fu = fu.merge(fu_hdr, on=["accession", "cik"], how="left")
    fu["period_of_report"] = pd.to_datetime(fu.period_of_report)
    fu["fiscal_year"] = fu.period_of_report.dt.year.astype("Int64")
    fu["is_followup"] = True

    # Merge the three roles into one row per accession.
    allf = pd.concat([annual, e8, fu], ignore_index=True)
    flags = allf.groupby("accession").agg(
        is_annual=("is_annual", lambda s: bool(s.fillna(False).any())),
        is_8k=("is_8k", lambda s: bool(s.fillna(False).any())),
        is_followup=("is_followup", lambda s: bool(s.fillna(False).any())),
        followup_of=("followup_of", lambda s: next((x for x in s if isinstance(x, list)), [])),
    ).reset_index()
    base = allf.sort_values("is_annual", na_position="last").drop_duplicates("accession")
    out = base.drop(columns=["is_annual", "is_8k", "is_followup", "followup_of"]).merge(flags, on="accession")
    out["has_item_105"] = out.has_item_105.fillna(False).astype(bool)
    out["has_item_801"] = out.has_item_801.fillna(False).astype(bool)
    out["fiscal_year"] = pd.to_numeric(out.fiscal_year).astype("Int64")
    out["sic"] = pd.to_numeric(out.sic).astype("Int64")
    out["sic_from_header"] = out.sic_from_header.astype("boolean")
    out["doc_count"] = pd.to_numeric(out.doc_count).astype("Int64")
    out["parse_status"] = pd.NA  # filled by Stage 2
    out = out[COLUMNS].sort_values(["filing_date", "accession"]).reset_index(drop=True)
    assert out.accession.is_unique

    FINAL.mkdir(parents=True, exist_ok=True)
    out.to_parquet(FINAL / "filings.parquet", index=False)

    sel = out[out.is_annual]
    stats.update({
        "selected_annual": len(sel),
        "selected_annual_companies": int(sel.cik.nunique()),
        "selected_annual_by_form": {k: int(v) for k, v in sel.form_type.value_counts().items()},
        "selected_annual_no_sic": int(sel.sic.isna().sum()),
        "rows_in_filings_parquet": len(out),
    })
    by_fy = sel.groupby("fiscal_year").agg(selected=("accession", "size"), companies=("cik", "nunique"))
    by_fy["dropped_second_filing"] = dropped_by_fy.reindex(by_fy.index, fill_value=0)
    by_fy["no_sic"] = sel.groupby("fiscal_year").sic.apply(lambda s: s.isna().sum())
    form_fy = sel.pivot_table(index="fiscal_year", columns="form_type", values="accession", aggfunc="size", fill_value=0)
    by_fy = by_fy.join(form_fy)
    stats["fy_fewest"] = {"fiscal_year": int(by_fy.selected.idxmin()), "n": int(by_fy.selected.min())}
    stats["fy_most"] = {"fiscal_year": int(by_fy.selected.idxmax()), "n": int(by_fy.selected.max())}
    (INTERIM / "select_stats.json").write_text(json.dumps(stats, indent=2, default=str))

    to_md = import_module("00_query_redivis").to_markdown
    section = ["## Filings selected (Stage 1)", "",
               "Annual reports by fiscal year (calendar year of the period of report), one per CIK and year.", "",
               to_md(by_fy), "",
               "Counts and drops: `data/interim/select_stats.json`.", ""]
    text = REPORT.read_text() if REPORT.exists() else "# Data report\n"
    text = text.split("## Filings selected (Stage 1)")[0].rstrip() + "\n\n" + "\n".join(section)
    REPORT.write_text(text)
    print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    main()
