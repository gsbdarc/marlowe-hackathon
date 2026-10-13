"""Stage 4 report: keyword hits per term and fiscal year, from the candidate pool.

Writes the "Prefilter (Stage 4)" section of reports/data_report.md and
data/interim/prefilter_stats.json. Paragraph totals per year come from the Stage 2-3
status files. Run after every task of slurm/04_prefilter.slurm has finished (login node, ~1 min).
"""

import glob
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
REPORT = ROOT / "reports" / "data_report.md"
SECTION = "## Prefilter (Stage 4)"
CONFIG = yaml.safe_load((ROOT / "config" / "keywords.yaml").read_text())


def md(df):
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [f"{v:,}" if isinstance(v, int) else str(v) for v in r]
            for i, r in zip(df.index, df.astype(object).itertuples(index=False))]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(r) + " |" for r in rows])


def main():
    cols = ["para_id", "fiscal_year", "form_type", "kw_terms", "kw_core", "incident_cue", "in_random_sample"]
    pool = pd.concat([pd.read_parquet(f, columns=cols) for f in sorted(glob.glob(str(INTERIM / "pool" / "part-*.parquet")))],
                     ignore_index=True)
    st = pd.concat([pd.read_parquet(f, columns=["accession", "n_paras"]) for f in glob.glob(str(INTERIM / "extract" / "status-[0-9]*.parquet"))])
    f = pd.read_parquet(ROOT / "data" / "final" / "filings.parquet", columns=["accession", "fiscal_year", "is_annual"])
    total_by_fy = st.merge(f[f.is_annual], on="accession").groupby("fiscal_year").n_paras.sum()
    total = int(st.n_paras.sum())

    hits = pool[pool.kw_terms.map(len) > 0]
    ann = hits[hits.fiscal_year.notna()].explode("kw_terms")
    terms = CONFIG["core"] + CONFIG["traps"]
    by_term = ann.pivot_table(index="fiscal_year", columns="kw_terms", values="para_id", aggfunc="size", fill_value=0)
    by_term = by_term.reindex(columns=[t for t in terms if t in by_term.columns]).astype(int)
    hits_ann = hits[hits.fiscal_year.notna()]
    summary = pd.DataFrame({
        "paragraphs": total_by_fy.astype(int),
        "keyword_hits": hits_ann.groupby("fiscal_year").size(),
        "core_hits": hits_ann[hits_ann.kw_core].groupby("fiscal_year").size(),
        "random_sample": pool[pool.in_random_sample & pool.fiscal_year.notna()].groupby("fiscal_year").size(),
    }).fillna(0).astype(int)
    summary.index = summary.index.astype(int)
    summary["hit_share"] = (100 * summary.keyword_hits / summary.paragraphs).round(2).map(lambda x: f"{x}%")
    by_term.index = by_term.index.astype(int)

    top5 = ann.kw_terms.value_counts().head(5)
    stats = {
        "paragraphs_total": total,
        "keyword_hits": len(hits), "keyword_hit_share": round(len(hits) / total, 5),
        "core_hits": int(hits.kw_core.sum()),
        "random_sample": int(pool.in_random_sample.sum()),
        "incident_cue": int(pool.incident_cue.sum()),
        "incident_cue_and_keyword": int((pool.incident_cue & (pool.kw_terms.map(len) > 0)).sum()),
        "pool_rows": len(pool),
        "top5_terms": {k: int(v) for k, v in top5.items()},
    }
    (INTERIM / "prefilter_stats.json").write_text(json.dumps(stats, indent=2))
    lines = [SECTION, "", "Annual-report paragraphs by fiscal year. A paragraph counts once in `keyword_hits` "
             "however many terms it has; `random_sample` is 1% of paragraphs with no term.", "", md(summary), "",
             "Paragraphs per term (a paragraph with two terms counts under both):", "", md(by_term), "",
             "Totals: `data/interim/prefilter_stats.json`.", ""]
    text = REPORT.read_text()
    REPORT.write_text(text.split(SECTION)[0].rstrip() + "\n\n" + "\n".join(lines))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
