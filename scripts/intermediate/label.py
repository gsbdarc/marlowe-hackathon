"""Send filings to a running Kev server and save its answers.

The intermediate track's copy of scripts/label.py, with --wandb added; the other tracks use scripts/label.py.

Kev serves Jev's API (POST /v1/systemone), so the request is the same one Jev answered: the filing as the state and the
three questions. Labels in the input file are never sent.

    $PY scripts/intermediate/label.py --url http://127.0.0.1:8009 --data $WORK/data/test1000.jsonl --out $WORK/results/kev-4b.jsonl
    $PY scripts/intermediate/label.py --url ... --data $DATA/item502_v1.parquet --limit 10000 --out $WORK/results/all.jsonl
    $PY scripts/intermediate/label.py --url ... --data ... --shard 3 --shards 8 --out $WORK/results/i5/<jobid>/shard-3.jsonl

With --shard I --shards N, it sends only every Nth filing, starting from the Ith (0 to N-1): N copies, one per GPU,
label the filings between them with no overlap (slurm/marlowe/intermediate/label.sh, I5).

--data is a JSONL from make_kev_data.py, or Jev's parquet itself (every filing with text, in filing order).

Writes one line per filing: {"id", "ok", "seconds", "answers"} (or "error"), then <out>_summary.json with the
throughput. A rerun skips filings already answered.

With --wandb NAME (slurm/yens/intermediate/score_kev.slurm), the run also goes to Weights & Biases: the server's settings, the speed
and GPU memory every 100 filings, and at the end the peak memory and the mean batch the server ran. Run it on the GPU
node, as the job does: it reads the GPU with nvidia-smi, and W&B's System tab charts that GPU.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # questions.py is in scripts/
from questions import questions, state


def ask(url, model, rec, timeout):
    body = {"model": model, "state": rec["state"], "questions": questions(with_why=True)}
    t = time.perf_counter()
    try:
        r = requests.post(f"{url}/v1/systemone", json=body, timeout=timeout)
        r.raise_for_status()
        return {"id": rec["_meta"]["id"], "ok": True, "seconds": time.perf_counter() - t, "answers": r.json()["answers"]}
    except (requests.RequestException, KeyError, ValueError) as e:
        return {"id": rec["_meta"]["id"], "ok": False, "seconds": time.perf_counter() - t, "error": f"{type(e).__name__}: {e}"}


def gpu():
    """(name, GB in use, GB in all) of the job's GPU, from nvidia-smi."""
    index = os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]   # nvidia-smi ignores CUDA_VISIBLE_DEVICES: ask for it
    out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits", "-i", index],
                         capture_output=True, text=True, check=True).stdout
    name, used, total = (x.strip() for x in out.split(","))
    return name, int(used) / 1024, int(total) / 1024


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--data", required=True, help="JSONL from make_kev_data.py (labels are ignored) or Jev's parquet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="kev-latest")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--limit", type=int, default=0, help="label only the first N filings")
    ap.add_argument("--shard", type=int, default=0, help="which share of the filings to send, 0 to --shards - 1")
    ap.add_argument("--shards", type=int, default=1, help="split the filings into this many shares, one per GPU")
    ap.add_argument("--wandb", metavar="NAME", help="also log the run to Weights & Biases under this name")
    a = ap.parse_args()
    if a.data.endswith(".parquet"):
        import pandas as pd
        d = pd.read_parquet(a.data, columns=["accession", "company_name", "date_filed", "text_502", "extract_status"])
        d = d[d.extract_status == "ok"].sort_values("date_filed")
        recs = [{"state": state(r.company_name, str(r.date_filed), r.text_502), "_meta": {"id": r.accession}} for r in d.itertuples()]
    else:
        recs = [json.loads(line) for line in open(a.data)]
    if a.limit:
        recs = recs[:a.limit]
    recs = recs[a.shard::a.shards]
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(line)["id"] for line in open(a.out) if json.loads(line).get("ok")}
    todo = [r for r in recs if r["_meta"]["id"] not in done]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    print(f"{len(recs):,} filings, {len(done):,} already answered, {len(todo):,} to send at concurrency {a.concurrency}", flush=True)
    if not todo:   # e.g. a job requeued after it had finished: keep the summary of the run that did the work
        print("nothing to send: every filing is already answered", flush=True)
        return
    run, peak = None, 0.0
    if a.wandb:
        import wandb
        card = requests.get(f"{a.url}/v1/models", timeout=30).json()["models"][0]
        name, _, total = gpu()
        run = wandb.init(name=a.wandb, config={
            "user": os.environ.get("USER"), "job": os.environ.get("SLURM_JOB_ID"), "gpu": name,
            "gpu_memory_gb": round(total, 1), "model": card["run"], "dtype": card["dtype"],
            "fused": os.environ.get("KEV_FUSED") != "0", "concurrency": a.concurrency, "filings": len(todo)})
        print(f"W&B run: {run.url}", flush=True)
    start, rows = time.perf_counter(), []
    ex = ThreadPoolExecutor(a.concurrency)
    with open(a.out, "a") as f:
        for i, row in enumerate(ex.map(lambda r: ask(a.url, a.model, r, a.timeout), todo), 1):
            f.write(json.dumps(row) + "\n")
            rows.append(row)
            if i % 100 == 0 or i == len(todo):
                bad = sum(not x["ok"] for x in rows)
                rate = i / (time.perf_counter() - start)
                print(f"  {i:,}/{len(todo):,}  {rate:.1f} filings/s  failed {bad}", flush=True)
                if run:
                    used = gpu()[1]
                    peak = max(peak, used)
                    run.log({"filings_per_second_so_far": rate, "failed": bad, "gpu_memory_used_gb": used}, step=i)
            if i == 20 and all(not x["ok"] for x in rows):
                ex.shutdown(wait=False, cancel_futures=True)   # do not wait for the requests still queued
                raise SystemExit(f"stopping: the first 20 requests all failed ({rows[-1]['error']})")
    ex.shutdown()
    ok = [x["seconds"] for x in rows if x["ok"]]
    wall = time.perf_counter() - start
    summary = {"filings": len(todo), "succeeded": len(ok), "wall_seconds": round(wall, 1),
               "filings_per_second": round(len(ok) / wall, 2) if wall else None,
               "latency_p50": round(statistics.median(ok), 3) if ok else None,
               "latency_p95": round(sorted(ok)[int(0.95 * (len(ok) - 1))], 3) if ok else None,
               "concurrency": a.concurrency, "shard": a.shard, "shards": a.shards}
    if run:
        b = requests.get(f"{a.url}/v1/models", timeout=30).json()["models"][0]["batches"]
        summary.update(gpu_memory_peak_gb=round(peak, 1), mean_batch=round(b["requests"] / b["count"], 1) if b["count"] else None)
        run.summary.update(summary)
        summary["wandb_run_id"] = run.id
        run.finish()
    json.dump(summary, open(a.out.replace(".jsonl", "_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
