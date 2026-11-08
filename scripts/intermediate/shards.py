"""Add up a I5 labeling job: the shards one per GPU, how fast they went together, and what labeling every filing would
take and cost, against Jev.

    $PY scripts/intermediate/shards.py $WORK/results/i5/<jobid>
    $PY scripts/intermediate/shards.py $WORK/results/i5/<1-GPU jobid> $WORK/results/i5/<8-GPU jobid>     # side by side

Reads <dir>/shard-*_summary.json (label.py) and <dir>/job-*.json (label.sh: GPUs and load time, one per node of a
job array). Run it again once every task of an array is done: each task prints only what had finished when it did.
The token counts come from Jev's own record of each filing, jev_input_tokens in $DATA/item502_v1.parquet.
"""
import argparse
import glob
import json
import os

JEV_PER_BILLION = 42.0        # dollars per billion input tokens (I1)


def load(d):
    shards = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "shard-*_summary.json")))]
    jobs = [json.load(open(p)) for p in glob.glob(os.path.join(d, "job-*.json"))]
    job = {"gpus": sum(j["gpus"] for j in jobs), "load_seconds": max(j["load_seconds"] for j in jobs)}
    ids = {json.loads(line)["id"] for p in glob.glob(os.path.join(d, "shard-*.jsonl")) for line in open(p)
           if json.loads(line).get("ok")}
    return shards, job, ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--gpu-hour", type=float, default=float(os.environ.get("GPU_HOUR", "3.0")),
                    help="dollars per H100-hour to price the GPUs at (default 3, or GPU_HOUR)")
    a = ap.parse_args()
    import pandas as pd
    d = pd.read_parquet(os.path.join(os.environ["DATA"], "item502_v1.parquet"),
                        columns=["accession", "extract_status", "jev_input_tokens"])
    d = d[d.extract_status == "ok"]
    corpus, corpus_tokens = len(d), d.jev_input_tokens.sum()
    tokens = dict(zip(d.accession, d.jev_input_tokens))

    print(f"{'job':<10}{'GPUs':>5}{'filings':>9}{'failed':>7}{'filings/s':>10}{'load s':>7}"
          f"{'all hours':>10}{'GPU-hours':>10}{'GPUs $':>8}{'Jev $':>7}")
    for p in a.dirs:
        shards, job, ids = load(p)
        n = sum(s["succeeded"] for s in shards)
        failed = sum(s["filings"] - s["succeeded"] for s in shards)
        wall = max((s["wall_seconds"] for s in shards), default=0)   # the job waits for its slowest shard
        if not wall:
            print(f"{os.path.basename(p.rstrip('/')):<10}no labeling time in its summaries (still running, or nothing was sent)")
            continue
        rate = n / wall
        hours = corpus / rate / 3600                             # every filing, at this rate
        gpu_hours = hours * job["gpus"]
        jev = corpus_tokens / 1e9 * JEV_PER_BILLION
        print(f"{os.path.basename(p.rstrip('/')):<10}{job['gpus']:>5}{n:>9,}{failed:>7}{rate:>10.1f}{job['load_seconds']:>7}"
              f"{hours:>10.2f}{gpu_hours:>10.2f}{gpu_hours * a.gpu_hour:>8.2f}{jev:>7.2f}")
        mine = sum(tokens.get(i, 0) for i in ids)
        print(f"{'':<10}{len(ids):,} answers saved: {mine / 1e6:.1f}M tokens, ${mine / 1e9 * JEV_PER_BILLION:.2f} from Jev;"
              f" the last run labeled {n:,} in {wall / 60:.1f} min on {job['gpus']} GPU(s),"
              f" ${wall / 3600 * job['gpus'] * a.gpu_hour:.2f} at ${a.gpu_hour:.2f}/GPU-hour")
    print(f"\nall hours, GPU-hours, GPUs $: labeling all {corpus:,} filings at the job's rate ({corpus_tokens / 1e6:.0f}M tokens);"
          f" Jev $: the same filings from Jev at ${JEV_PER_BILLION:.0f} per billion input tokens")


if __name__ == "__main__":
    main()
