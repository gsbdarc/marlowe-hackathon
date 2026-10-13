"""Stage 4: keyword prefilter over one shard of paragraphs.

For every paragraph in data/interim/paragraphs/part-<shard>.parquet:
  kw_terms          core and trap terms found (config/keywords.yaml)
  kw_core           any core term
  incident_cue      any incident cue (used by Stage 6 enrichment)
  in_random_sample  no core or trap term, and selected by a seeded hash of para_id
                    (share 1%; a fixed hash gives about 1% in every fiscal year and is
                    the same on every rerun)

Writes, per shard:
  data/interim/prefilter/flags-<shard>.parquet  para_id and the four columns, every paragraph
  data/interim/pool/part-<shard>.parquet        full rows for the candidate pool: keyword hits,
                                                the random sample, and incident-cue matches
Run as a Slurm array (slurm/04_prefilter.slurm), one task per shard.
"""

import argparse
import hashlib
import os
import re
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
CONFIG = yaml.safe_load((ROOT / "config" / "keywords.yaml").read_text())


# Words that start with a prefix term but are not about it (place names, surnames).
PREFIX_EXCLUDE = {"hack": r"(?!ensack|ney|ett|berry)"}


def term_pattern(term, prefix):
    """Whole-word pattern; where terms overlap ("data breach" and "breach"), the first listed wins."""
    words = [re.escape(w) for w in term.split()]
    body = r"[\s\-]+".join(words)
    tail = PREFIX_EXCLUDE.get(term, "") + r"\w*" if prefix else r"(?:e?s)?"
    return rf"\b{body}{tail}\b"


def compile_terms(terms, prefix=()):
    """One alternation with a named group per term, so a single pass finds every term."""
    groups = {f"t{i}": t for i, t in enumerate(terms)}
    rx = re.compile("|".join(f"(?P<{g}>{term_pattern(t, t in prefix)})" for g, t in groups.items()), re.I)
    return rx, groups


KW_RX, KW_GROUPS = compile_terms(CONFIG["core"] + CONFIG["traps"], set(CONFIG["prefix"]))
CORE = set(CONFIG["core"])
CUE_RX, _ = compile_terms(CONFIG["incident_cues"])
SHARE = CONFIG["random_sample"]["share"]
SEED = str(CONFIG["random_sample"]["seed"])


def in_sample(para_id):
    h = int(hashlib.sha256(f"{SEED}:{para_id}".encode()).hexdigest()[:12], 16)
    return h / 16 ** 12 < SHARE


def flag(rows):
    out = []
    for para_id, text in rows:
        found = sorted({KW_GROUPS[m.lastgroup] for m in KW_RX.finditer(text)})
        out.append((para_id, found, any(t in CORE for t in found),
                    bool(CUE_RX.search(text)), (not found) and in_sample(para_id)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shard", type=int, default=None, help="defaults to SLURM_ARRAY_TASK_ID")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    args = ap.parse_args()
    shard = args.shard if args.shard is not None else int(os.environ["SLURM_ARRAY_TASK_ID"])
    src = INTERIM / "paragraphs" / f"part-{shard:03d}.parquet"

    t0 = time.time()
    para = pq.read_table(src).to_pandas()
    pairs = list(zip(para.para_id, para.text))
    step = 20000
    with Pool(args.workers) as pool:
        parts = pool.map(flag, [pairs[i:i + step] for i in range(0, len(pairs), step)])
    flags = pd.DataFrame([r for part in parts for r in part],
                         columns=["para_id", "kw_terms", "kw_core", "incident_cue", "in_random_sample"])
    assert len(flags) == len(para) and (flags.para_id.values == para.para_id.values).all()

    for sub in ("prefilter", "pool"):
        (INTERIM / sub).mkdir(parents=True, exist_ok=True)
    flags.to_parquet(INTERIM / "prefilter" / f"flags-{shard:03d}.parquet", index=False)
    keep = flags.kw_terms.map(len).gt(0) | flags.in_random_sample | flags.incident_cue
    pool_rows = pd.concat([para[keep.values].reset_index(drop=True),
                           flags[keep.values].drop(columns="para_id").reset_index(drop=True)], axis=1)
    pool_rows.to_parquet(INTERIM / "pool" / f"part-{shard:03d}.parquet", index=False, compression="zstd")
    print(f"shard {shard:03d}: {len(para):,} paragraphs, {int(flags.kw_terms.map(len).gt(0).sum()):,} keyword hits "
          f"({int(flags.kw_core.sum()):,} core), {int(flags.in_random_sample.sum()):,} random, "
          f"{int(flags.incident_cue.sum()):,} cue; pool {len(pool_rows):,}; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
