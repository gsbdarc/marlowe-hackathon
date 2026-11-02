"""Send filings to a running Kev server, or an OpenAI-compatible chat server such as vLLM, and save its answers.

Kev serves Jev's API (POST /v1/systemone), so the request is the same one Jev answered: the filing as the state and the
three questions. With --api chat, the same filing and questions go to POST /v1/chat/completions as one prompt with
numbered options, and the server is asked for JSON limited to those options (structured outputs); the answers are
saved in the same form, so score.py scores either. Labels in the input file are never sent.

    $PY scripts/label.py --url http://127.0.0.1:8009 --data $WORK/data/test1000.jsonl --out $WORK/results/kev-4b.jsonl
    $PY scripts/label.py --url ... --data $DATA/item502_v1.parquet --limit 10000 --out $WORK/results/all.jsonl
    $PY scripts/label.py --api chat --model qwen-235b --url http://n05:8123 --data ... --out $WORK/results/qwen-235b.jsonl

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

from questions import (FUTURE_INSTRUCTIONS, REASON, STATUS, STATUS_INSTRUCTIONS, WHY_INSTRUCTIONS, questions,
                       state)


def ask(url, model, rec, timeout):
    body = {"model": model, "state": rec["state"], "questions": questions(with_why=True)}
    t = time.perf_counter()
    try:
        r = requests.post(f"{url}/v1/systemone", json=body, timeout=timeout)
        r.raise_for_status()
        return {"id": rec["_meta"]["id"], "ok": True, "seconds": time.perf_counter() - t, "answers": r.json()["answers"]}
    except (requests.RequestException, KeyError, ValueError) as e:
        return {"id": rec["_meta"]["id"], "ok": False, "seconds": time.perf_counter() - t, "error": f"{type(e).__name__}: {e}"}


# --api chat: the questions as one prompt, and a JSON schema that holds the answer to the options
ANSWER_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["status", "why", "future"],
                 "properties": {"status": {"type": "integer", "enum": list(STATUS)},
                                "why": {"type": "integer", "enum": list(REASON)},
                                "future": {"type": "boolean"}}}


def chat_prompt(state_text):
    options = lambda d: "\n".join(f"{k}. {v}" for k, v in d.items())
    return (f"{state_text}\n\n---\n\nAnswer three questions about the filing above.\n\n"
            f"1. {STATUS_INSTRUCTIONS}\n{options(STATUS)}\n\n"
            f"2. {WHY_INSTRUCTIONS}\n{options(REASON)}\n\n"
            f"3. {FUTURE_INSTRUCTIONS}\n\n"
            'Reply with JSON only: {"status": <option number for 1>, "why": <option number for 2>, "future": <true or false for 3>}')


def ask_chat(url, model, rec, timeout):
    body = {"model": model, "messages": [{"role": "user", "content": chat_prompt(rec["state"])}],
            "temperature": 0, "max_tokens": 64,
            "response_format": {"type": "json_schema", "json_schema": {"name": "answers", "schema": ANSWER_SCHEMA}}}
    t = time.perf_counter()
    try:
        r = requests.post(f"{url}/v1/chat/completions", json=body, timeout=timeout)
        r.raise_for_status()
        a = json.loads(r.json()["choices"][0]["message"]["content"])
        answers = {"status": {"choice": STATUS[a["status"]]}, "why": {"choice": REASON[a["why"]]},
                   "future": {"noul": 1.0 if a["future"] else 0.0}}
        return {"id": rec["_meta"]["id"], "ok": True, "seconds": time.perf_counter() - t, "answers": answers}
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as e:
        return {"id": rec["_meta"]["id"], "ok": False, "seconds": time.perf_counter() - t, "error": f"{type(e).__name__}: {e}"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--api", choices=["systemone", "chat"], default="systemone", help="systemone: a Kev server; chat: an OpenAI-compatible server (vLLM)")
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
    ex = ThreadPoolExecutor(a.concurrency)
    with open(a.out, "a") as f:
        send = ask_chat if a.api == "chat" else ask
        for i, row in enumerate(ex.map(lambda r: send(a.url, a.model, r, a.timeout), todo), 1):
            f.write(json.dumps(row) + "\n")
            rows.append(row)
            if i % 100 == 0 or i == len(todo):
                bad = sum(not x["ok"] for x in rows)
                print(f"  {i:,}/{len(todo):,}  {i / (time.perf_counter() - start):.1f} filings/s  failed {bad}", flush=True)
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
               "concurrency": a.concurrency}
    json.dump(summary, open(a.out.replace(".jsonl", "_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
