"""Send filings to a running Kev server and save its answers.

Kev serves Jev's API (POST /v1/systemone), so the request is the same one Jev answered: the filing as the state and the
three questions. Labels in the input file are never sent.

    $PY scripts/label.py --url http://127.0.0.1:8009 --data $WORK/data/test1000.jsonl --out $WORK/results/kev-4b.jsonl
    $PY scripts/label.py --url ... --data $DATA/item502_v1.parquet --limit 10000 --out $WORK/results/all.jsonl

--data is a JSONL from make_kev_data.py, or Jev's parquet itself (every filing with text, in filing order).

Writes one line per filing: {"id", "ok", "seconds", "answers"} (or "error"), then <out>_summary.json with the
throughput. A rerun skips filings already answered.
"""
import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import requests

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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--data", required=True, help="JSONL from make_kev_data.py (labels are ignored) or Jev's parquet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="kev-latest")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--limit", type=int, default=0, help="label only the first N filings")
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
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(line)["id"] for line in open(a.out) if json.loads(line).get("ok")}
    todo = [r for r in recs if r["_meta"]["id"] not in done]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    print(f"{len(recs):,} filings, {len(done):,} already answered, {len(todo):,} to send at concurrency {a.concurrency}", flush=True)
    start, rows = time.perf_counter(), []
    with open(a.out, "a") as f, ThreadPoolExecutor(a.concurrency) as ex:
        for i, row in enumerate(ex.map(lambda r: ask(a.url, a.model, r, a.timeout), todo), 1):
            f.write(json.dumps(row) + "\n")
            rows.append(row)
            if i % 100 == 0 or i == len(todo):
                bad = sum(not x["ok"] for x in rows)
                print(f"  {i:,}/{len(todo):,}  {i / (time.perf_counter() - start):.1f} filings/s  failed {bad}", flush=True)
            if i == 20 and all(not x["ok"] for x in rows):
                raise SystemExit(f"stopping: the first 20 requests all failed ({rows[-1]['error']})")
    ok = [x["seconds"] for x in rows if x["ok"]]
    wall = time.perf_counter() - start
    summary = {"filings": len(todo), "succeeded": len(ok), "wall_seconds": round(wall, 1),
               "filings_per_second": round(len(ok) / wall, 2) if wall else None,
               "latency_p50": round(statistics.median(ok), 3) if ok else None,
               "latency_p95": round(sorted(ok)[int(0.95 * (len(ok) - 1))], 3) if ok else None,
               "concurrency": a.concurrency}
    json.dump(summary, open(a.out.replace(".jsonl", "_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
