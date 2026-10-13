"""Stage 6: teacher samples from the candidate pool (keyword hits plus the 1% random sample).

Outputs in data/final/ (the files that go to Marlowe):
  train_400k.parquet           400,000 paragraphs from train-split companies, with nested
                               in_25k and in_200k subsets and sample_weight
  val.parquet                  2,000 paragraphs from validation-split companies (simple random)
  test.parquet                 5,000 annual-report paragraphs from test-split companies,
                               1,250 per era: FY1996-2010, 2011-2017, 2018-2022, 2023-2025
  test_incident_slice.parquet  500 incident-enriched paragraphs from test-split companies

Training sample:
  - Candidates: train-split pool rows, one per exact text (text_sha1), and none whose text is
    also in the validation or test pools.
  - Enrichment (INCIDENT is rare), capped at ENRICH_CAP: (a) every keyword-hit paragraph from
    8-Ks and Item 1.05 follow-up filings; (b) annual-report paragraphs with an incident cue and a
    keyword, drawn at random to fill the cap.
  - The rest is annual-report paragraphs stratified by fiscal year: an equal share per year,
    with a year's unused share passed to the others.
  - Subsets of N = 25,000 and 200,000 take the first rows of each stratum in a fixed random
    order, so 25k is inside 200k inside 400k; each has the same enrichment share.
  - sample_weight = candidates in the row's stratum / rows drawn from it (400k sample), so
    weighted counts estimate the train-split candidate pool.

Validation and test are frozen: if a file exists, the script stops unless its para_ids match
what it would write. Seed: SEED below. Run as one Slurm job (slurm/06_samples.slurm).
"""

import argparse
import glob
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
REPORT = ROOT / "reports" / "data_report.md"
SECTION = "## Samples (Stages 5-6)"

SEED = 20261106
TRAIN_N, SUBSETS = 400_000, (25_000, 200_000)
ENRICH_CAP = 40_000
VAL_N, TEST_PER_ERA, INCIDENT_N = 2_000, 1_250, 500
ERAS = [(1996, 2010), (2011, 2017), (2018, 2022), (2023, 2025)]
ANNUAL = {"10-K", "10-K405", "10KSB", "10KSB40", "10-KT", "10KT405"}
KEEP = ["para_id", "accession", "cik", "form_type", "fiscal_year", "section", "heading", "prev_text", "text",
        "n_words", "text_sha1", "kw_terms", "kw_core", "incident_cue", "in_random_sample"]


def rkey(ids, salt):
    """Fixed pseudo-random order: hash of seed, salt and para_id."""
    return np.array([int(hashlib.sha256(f"{SEED}:{salt}:{i}".encode()).hexdigest()[:15], 16) for i in ids])


def waterfill(avail, total):
    """Equal share per stratum; unused share from small strata goes to the rest."""
    alloc = pd.Series(0, index=avail.index)
    left, open_ = total, list(avail.index)
    while left > 0 and open_:
        share = left // len(open_) or 1
        nxt = []
        for k in open_:
            take = min(share, avail[k] - alloc[k], left)
            alloc[k] += take
            left -= take
            if alloc[k] < avail[k]:
                nxt.append(k)
            if left == 0:
                break
        if nxt == open_ and share * len(open_) > left and left > 0:
            for k in nxt[:left]:  # remainder smaller than the number of strata
                alloc[k] += 1
            left = 0
        open_ = nxt
    return alloc


def take_ranked(df, by, alloc):
    """Rows with rank (in random-key order within stratum) below the stratum's allocation."""
    rank = df.sort_values("_key").groupby(by).cumcount()
    return rank.reindex(df.index) < df[by].map(alloc).fillna(0)


def frozen_write(df, name, check_only_ids=True):
    path = FINAL / name
    if path.exists():
        old = pd.read_parquet(path, columns=["para_id"])
        if sorted(old.para_id) != sorted(df.para_id):
            raise SystemExit(f"{name} is frozen and would change; not overwriting")
        print(f"{name}: frozen, unchanged ({len(old):,} rows)")
        return
    df.to_parquet(path, index=False, compression="zstd")
    print(f"{name}: wrote {len(df):,} rows")


def era_of(fy):
    for i, (a, b) in enumerate(ERAS):
        if a <= fy <= b:
            return f"{a}-{b}"
    return None


def md(df):
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = [[str(i)] + [f"{v:,}" if isinstance(v, (int, np.integer)) else str(v) for v in r]
            for i, r in zip(df.index, df.astype(object).itertuples(index=False))]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(r) + " |" for r in rows])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite-train", action="store_true",
                    help="rewrite train_400k.parquet (only before the teacher has labeled it)")
    args = ap.parse_args()

    pool = pd.concat([pd.read_parquet(f, columns=KEEP) for f in sorted(glob.glob(str(INTERIM / "pool" / "part-*.parquet")))],
                     ignore_index=True)
    split = pd.read_parquet(FINAL / "company_split.parquet")
    filings = pd.read_parquet(FINAL / "filings.parquet", columns=["accession", "is_followup", "is_8k", "abs_issuer"])
    pool = pool.merge(split, on="cik", how="left").merge(filings, on="accession", how="left")
    assert pool.split.notna().all()
    pool["hit"] = pool.kw_terms.map(len) > 0
    pool = pool[pool.hit | pool.in_random_sample].reset_index(drop=True)  # cue-only rows are not in the pool
    pool["annual"] = pool.form_type.isin(ANNUAL)
    pool["event"] = pool.is_8k.fillna(False) | pool.is_followup.fillna(False)
    stats = {"pool_rows": len(pool), "pool_by_split": {k: int(v) for k, v in pool.split.value_counts().items()}}

    # ---------------- validation and test (frozen)
    val_pool = pool[pool.split == "val"].copy()
    val_pool["_key"] = rkey(val_pool.para_id, "val")
    val = val_pool.nsmallest(VAL_N, "_key").copy()
    val["sample_weight"] = len(val_pool) / VAL_N

    test_pool = pool[(pool.split == "test") & pool.annual].copy()
    test_pool["era"] = test_pool.fiscal_year.map(lambda y: era_of(int(y)))
    test_pool["_key"] = rkey(test_pool.para_id, "test")
    test = test_pool[take_ranked(test_pool, "era", {e: TEST_PER_ERA for e in test_pool.era.unique()})].copy()
    era_n = test_pool.era.value_counts()
    test["sample_weight"] = test.era.map(era_n) / test.era.map(test.era.value_counts())

    tst = pool[pool.split == "test"].copy()
    inc_cand = tst[(tst.event & tst.hit) | (tst.annual & tst.incident_cue & tst.hit)].copy()
    inc_cand["_key"] = rkey(inc_cand.para_id, "incident")
    inc = inc_cand.nsmallest(min(INCIDENT_N, len(inc_cand)), "_key").copy()
    inc["sample_weight"] = len(inc_cand) / len(inc)
    stats.update(val=len(val), test=len(test), test_per_era={k: int(v) for k, v in test.era.value_counts().sort_index().items()},
                 incident_slice=len(inc), incident_candidates_test=len(inc_cand))

    # ---------------- training candidates
    tr = pool[pool.split == "train"].copy()
    heldout = set(pool.loc[pool.split != "train", "text_sha1"])
    n0 = len(tr)
    tr = tr[~tr.text_sha1.isin(heldout)]
    stats["train_dropped_text_in_val_test"] = n0 - len(tr)
    tr["_key"] = rkey(tr.para_id, "train")
    n1 = len(tr)
    tr = tr.sort_values("_key").drop_duplicates("text_sha1", keep="first")
    stats["train_dropped_exact_duplicates"] = n1 - len(tr)
    stats["train_candidates"] = len(tr)

    enrich_a = tr[tr.event & tr.hit].copy()
    enrich_a["source"] = "enrich_event"
    cue_pool = tr[tr.annual & tr.incident_cue & tr.hit & ~tr.para_id.isin(enrich_a.para_id)].copy()
    n_b = max(0, min(len(cue_pool), ENRICH_CAP - len(enrich_a)))
    enrich_b = cue_pool.nsmallest(n_b, "_key").copy()
    enrich_b["source"] = "enrich_cue"
    enrich_a["sample_weight"] = 1.0
    enrich_b["sample_weight"] = len(cue_pool) / max(n_b, 1)
    enrich = pd.concat([enrich_a, enrich_b])
    stats.update(enrich_event=len(enrich_a), enrich_cue=len(enrich_b), enrich_cue_candidates=len(cue_pool))

    strat_pool = tr[tr.annual & ~tr.para_id.isin(enrich.para_id)].copy()
    strat_pool["fiscal_year"] = strat_pool.fiscal_year.astype(int)
    avail = strat_pool.fiscal_year.value_counts().sort_index()
    alloc = {N: waterfill(avail, N - round(len(enrich) * N / TRAIN_N)) for N in (*SUBSETS, TRAIN_N)}
    strat = strat_pool[take_ranked(strat_pool, "fiscal_year", alloc[TRAIN_N])].copy()
    strat["source"] = strat.in_random_sample.map({True: "random", False: "keyword"})
    strat["sample_weight"] = strat.fiscal_year.map(avail) / strat.fiscal_year.map(alloc[TRAIN_N])
    rank = strat.sort_values("_key").groupby("fiscal_year").cumcount().reindex(strat.index)
    erank = enrich.sort_values("_key").reset_index(drop=False)
    for N in SUBSETS:
        col = f"in_{N // 1000}k"
        strat[col] = rank < strat.fiscal_year.map(alloc[N])
        k = round(len(enrich) * N / TRAIN_N)
        enrich[col] = enrich.para_id.isin(set(erank.para_id.head(k)))
    train = pd.concat([strat, enrich], ignore_index=True)
    assert len(train) == TRAIN_N, len(train)
    for N in SUBSETS:
        assert train[f"in_{N // 1000}k"].sum() == N, (N, train[f"in_{N // 1000}k"].sum())
    assert (train.in_200k | ~train.in_25k).all()
    stats["train_per_year_cap"] = int(alloc[TRAIN_N].max())
    stats["train_by_source"] = {k: int(v) for k, v in train.source.value_counts().items()}
    stats["train_random_share"] = round(float((train.source == "random").mean()), 4)
    stats["train_enrichment_share"] = round(float(train.source.str.startswith("enrich").mean()), 4)

    # ---------------- write
    out_cols = KEEP + ["split", "abs_issuer"]
    frozen_write(val[out_cols + ["sample_weight"]], "val.parquet")
    frozen_write(test[out_cols + ["era", "sample_weight"]], "test.parquet")
    frozen_write(inc[out_cols + ["sample_weight"]], "test_incident_slice.parquet")
    tcols = out_cols + ["source", "in_25k", "in_200k", "sample_weight"]
    tpath = FINAL / "train_400k.parquet"
    if tpath.exists() and not args.overwrite_train:
        frozen_write(train[tcols], "train_400k.parquet")
    else:
        train[tcols].to_parquet(tpath, index=False, compression="zstd")
        print(f"train_400k.parquet: wrote {len(train):,} rows")
    stats["teacher_items_total"] = len(train) + len(val) + len(test) + len(inc)
    (INTERIM / "samples_stats.json").write_text(json.dumps(stats, indent=2))

    by_year = pd.DataFrame({
        "candidates": avail, "allocated_400k": alloc[TRAIN_N], "in_200k": alloc[200_000], "in_25k": alloc[25_000],
        "random_share": strat.groupby("fiscal_year").source.apply(lambda s: f"{100 * (s == 'random').mean():.0f}%"),
    })
    by_year.index.name = "fiscal_year"
    lines = [SECTION, "", f"Company split: {split.split.value_counts().to_dict()} CIKs. Training sample by fiscal year "
             f"(stratified part; enrichment adds {len(enrich):,} more):", "", md(by_year), "",
             "Totals: `data/interim/samples_stats.json`.", ""]
    text = REPORT.read_text()
    REPORT.write_text(text.split(SECTION)[0].rstrip() + "\n\n" + "\n".join(lines))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
