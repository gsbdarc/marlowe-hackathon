"""B5: turn Kev's labels into a finding. Reads the answers from one or more B4 jobs and the filings they label.

    $PY scripts/beginner/findings.py trend   $WORK/results/b4/<jobid>             # CEO changes per year
    $PY scripts/beginner/findings.py reasons $WORK/results/b4/<jobid>             # why CEOs left, by period
    $PY scripts/beginner/findings.py read    $WORK/results/b4/<jobid> --year 2009 --reason retired
    $PY scripts/beginner/findings.py read    $WORK/results/b4/<jobid> --year 2005 --disagree
    $PY scripts/beginner/findings.py read    $WORK/results/b4/<jobid> --cik 883943    # one company's CEO changes

Give it several job folders and it uses every pile (shard) found in them; a filing labeled twice counts once. Reads
$DATA/item502_v1.parquet for each filing's year, company and text (source env/marlowe.sh first).
"""
import argparse
import glob
import json
import os
import sys
import textwrap

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from questions import REASON, REASON_SHORT, STATUS, STATUS_SHORT  # noqa: E402

STATUS_NUM = {v: k for k, v in STATUS.items()}
REASON_NUM = {v: k for k, v in REASON.items()}
PARQUET = lambda: os.path.join(os.environ["DATA"], "item502_v1.parquet")   # noqa: E731
FORCED = {3, 4}            # pushed out over performance; dismissed over legal or policy violations
PERIODS = [(2004, 2007, "2004-07"), (2008, 2009, "2008-09 crisis"), (2010, 2019, "2010-19"),
           (2020, 2021, "2020-21 pandemic"), (2022, 2026, "2022-26")]


def load(folders):
    files = sorted({f for d in folders for f in glob.glob(os.path.join(d, "shard-*.jsonl"))})
    if not files:
        sys.exit(f"no shard-*.jsonl files in {' '.join(folders)}: is the job ID right, and has the job finished?")
    rows = []
    for f in files:
        with open(f) as fh:
            for line in fh:
                r = json.loads(line)
                if not r.get("ok"):
                    continue
                a = r["answers"]
                rows.append((r["id"], STATUS_NUM[a["status"]["choice"]], a["status"]["confidence"],
                             REASON_NUM[a["why"]["choice"]], a["why"]["confidence"], a["future"]["noul"]))
    kev = pd.DataFrame(rows, columns=["accession", "kev_status", "kev_status_conf", "kev_why", "kev_why_conf",
                                      "kev_future"])
    kev = kev.drop_duplicates("accession")
    cols = ["accession", "cik", "company_name", "date_filed", "year", "words", "edgar_url", "labeled", "status", "why",
            "p_future"]               # not the text: `read` fetches it for the few filings it shows
    d = pd.read_parquet(PARQUET(), columns=cols)
    d = d.merge(kev, on="accession", how="inner")
    d["month"] = pd.to_datetime(d.date_filed).dt.month
    d["kev_change"] = d.kev_status != 1
    d["kev_forced"] = d.kev_change & d.kev_why.isin(FORCED)
    piles = sorted({os.path.basename(f) for f in files})   # the 1-GPU job and a bigger one both have shard-0
    print(f"{len(d):,} filings labeled by Kev, from {len(piles)} of the 8 piles: {', '.join(piles)}")
    if len(piles) < 8:
        print(f"That is about {len(piles)} in 8 of all filings, dealt evenly across the years, so the shares below are"
              " estimates from a sample; the counts are for your sample only.")
    print()
    return d


def bar(x, scale):
    return "#" * int(round(x * scale))


def trend(d):
    d = d.assign(jev_change=d.status != 1)
    y = d.groupby("year").agg(filings=("accession", "size"), kev=("kev_change", "sum"), jev=("jev_change", "sum"))
    scale = 40 / (100 * y.kev / y.filings).max()
    print("CEO changes per year: how many of each year's Item 5.02 filings report the CEO leaving the job.")
    print("Jev labeled every filing too, so its column is the check on Kev's.\n")
    print(f"{'year':>4} {'filings':>8} {'Kev: changes':>12} {'per 100':>7} {'Jev: per 100':>12}  Kev per 100")
    for r in y.itertuples():
        k, j = 100 * r.kev / r.filings, 100 * r.jev / r.filings
        print(f"{r.Index:>4} {r.filings:>8,} {r.kev:>12,} {k:>7.1f} {j:>12.1f}  {bar(k, scale)}")


def reasons(d):
    d = d.assign(period=None, jev_change=d.status != 1)
    for lo, hi, name in PERIODS:
        d.loc[d.year.between(lo, hi), "period"] = name
    order = [p[2] for p in PERIODS]
    for who, change, why in [("Kev", "kev_change", "kev_why"), ("Jev", "jev_change", "why")]:
        c = d[d[change]]
        t = pd.crosstab(c.period, c[why].astype(int).map(REASON_SHORT), normalize="index").mul(100).reindex(order)
        t = t[[v for k, v in sorted(REASON_SHORT.items()) if v in t.columns]]
        t.index.name, t.columns.name = None, None
        t["CEO changes"] = c.groupby("period").size().reindex(order)
        print(f"Why CEOs left, by {who}: the share of each period's CEO changes given each reason (%; rows add to 100)\n")
        print(t.round(1).to_string(), "\n")
    print("Forced out (performance, or legal or policy violations), as a share of each year's CEO changes:\n")
    print(f"{'year':>4} {'Kev':>6} {'Jev':>6}  Jev")
    k = d[d.kev_change].groupby("year").kev_why.apply(lambda s: 100 * s.isin(FORCED).mean())
    j = d[d.jev_change].groupby("year").why.apply(lambda s: 100 * s.astype(int).isin(FORCED).mean())
    scale = 40 / max(j.max(), 1)
    for yr in j.index:
        print(f"{yr:>4} {k.get(yr, 0):>5.1f}% {j[yr]:>5.1f}%  {bar(j[yr], scale)}")


def read(d, year, reason, n, seed, disagree, cik):
    if disagree:                     # Kev and Jev disagree on whether the CEO is leaving the job, either way round
        c = d[d.kev_change != (d.status != 1)]
        if reason:
            sys.exit("--reason and --disagree do not go together: half these filings have no CEO change by Kev")
    else:
        c = d[d.kev_change]
    if year:
        c = c[c.year == year]
    if cik:
        c = c[c.cik == cik]
    if reason:
        num = {v: k for k, v in REASON_SHORT.items()}.get(reason)
        if num is None:
            sys.exit(f"--reason is one of: {', '.join(REASON_SHORT.values())}")
        c = c[c.kev_why == num]
    if c.empty:
        sys.exit("no filings match; try another --year or --reason")
    what = "filings where Kev and Jev disagree" if disagree else "CEO changes"
    print(f"{len(c):,} {what} match; here are {min(n, len(c))} at random (--seed {seed}; change it for others).\n")
    show = c.sample(min(n, len(c)), random_state=seed)
    texts = pd.read_parquet(PARQUET(), columns=["accession", "text_502"],
                           filters=[("accession", "in", list(show.accession))]).set_index("accession").text_502
    for _, r in show.iterrows():
        print("=" * 100)
        print(f"{r.company_name}, filed {r.date_filed}   {r.edgar_url}")
        kev_why = f", because: {REASON_SHORT[r.kev_why]} ({r.kev_why_conf:.0%} sure)" if r.kev_change else ""
        print(f"Kev: {STATUS_SHORT[r.kev_status]} ({r.kev_status_conf:.0%} sure){kev_why}")
        if r.labeled:
            jev_why = f", because: {REASON_SHORT[int(r.why)]}" if r.status != 1 else ""
            print(f"Jev: {STATUS_SHORT[int(r.status)]}{jev_why}")
        print()
        text = " ".join(str(texts.get(r.accession, "")).split())
        print(textwrap.fill(text[:1500] + (" ..." if len(text) > 1500 else ""), 100))
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", choices=["trend", "reasons", "read"])
    ap.add_argument("folders", nargs="+", help="one or more B4 result folders, $WORK/results/b4/<jobid>")
    ap.add_argument("--year", type=int, help="read: only this year")
    ap.add_argument("--reason", help=f"read: only this reason ({', '.join(REASON_SHORT.values())})")
    ap.add_argument("--examples", type=int, default=3, help="read: how many filings to show")
    ap.add_argument("--seed", type=int, default=0, help="read: which random filings")
    ap.add_argument("--disagree", action="store_true", help="read: filings where Kev and Jev disagree on a CEO change")
    ap.add_argument("--cik", type=int, help="read: only this company (its SEC number, the cik column)")
    a = ap.parse_args()
    d = load(a.folders)
    if a.question == "trend":
        trend(d)
    elif a.question == "reasons":
        reasons(d)
    else:
        read(d, a.year, a.reason, a.examples, a.seed, a.disagree, a.cik)


if __name__ == "__main__":
    main()
