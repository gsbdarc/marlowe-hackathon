"""Stage 7: teacher labeling, as a client of a vLLM server running in a container.

The server is started separately with gsbdarc/vllm_helper (`source $VLLM_HELPER/vllm.sh;
vllm serve &`, see slurm/marlowe/07_teacher.slurm), which serves an OpenAI-compatible API and
writes its host and port to $SCRATCH_BASE/vllm/{host,port}.txt. This script needs only pandas,
pyarrow and requests.

For each paragraph: fill config/prompt_v<N>.txt with its heading, previous paragraph and text,
send it as a chat message (the server applies the model's chat template; thinking off), and ask
for one token at temperature 0 with the top 20 log probabilities. The probabilities of the five
answer letters A-E are renormalized to sum to 1. The item is invalid if the top token is not a
letter. Requests run concurrently so vLLM can batch them.

Writes data/teacher/<run_id>/<sample>-shard-<NNNN>.parquet, 10,000 items per shard, and skips
shards that already exist, so a restarted job picks up where it stopped. run.json records the
server's model and vLLM version, the settings and per-shard timing. scripts/07_report.py
combines the shards and runs the Stage 7 checks.

  python scripts/07_teacher.py --run-id pilot --samples train --limit 10000
  python scripts/07_teacher.py --run-id full --samples train val test test_incident_slice
"""

import argparse
import json
import math
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import local

import pandas as pd
import requests

ROOT = Path(os.environ.get("CYBER_ROOT", Path(__file__).resolve().parent.parent))
FINAL = ROOT / "data" / "final"
TEACHER = ROOT / "data" / "teacher"
LETTERS = ["A", "B", "C", "D", "E"]
LABELS = dict(zip(LETTERS, ["NONE", "RISK", "GOVERNANCE", "INCIDENT", "PRODUCT"]))
SAMPLE_FILES = {"train": "train_400k.parquet", "val": "val.parquet", "test": "test.parquet",
                "test_incident_slice": "test_incident_slice.parquet"}
SHARD = 10_000
MIN_CONFIDENCE = 0.7
SEED = 20261106
_tls = local()


def server_url(arg):
    if arg:
        return arg.rstrip("/")
    s = Path(os.environ["SCRATCH_BASE"]) / "vllm"
    return f"http://{(s / 'host.txt').read_text().strip()}:{(s / 'port.txt').read_text().strip()}"


def session():
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
    return _tls.s


def ask(url, model, content, top_logprobs, retries=4):
    body = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 1,
            "temperature": 0.0, "logprobs": True, "top_logprobs": top_logprobs, "seed": SEED,
            "chat_template_kwargs": {"enable_thinking": False}}
    for attempt in range(retries):
        try:
            r = session().post(f"{url}/v1/chat/completions", json=body, timeout=600)
            r.raise_for_status()
            return r.json()["choices"][0], None
        except Exception as e:  # retried with backoff; the last error is recorded on the row
            err = f"{type(e).__name__}: {e}"[:300]
            time.sleep(2 ** attempt)
    return None, err


def score(choice, err):
    if choice is None:
        return {"label": None, "letter": None, "confidence": 0.0, **{f"p_{L}": 0.0 for L in LETTERS},
                "letter_mass": 0.0, "invalid": True, "top_token": None, "error": err}
    first = choice["logprobs"]["content"][0]
    p = {L: 0.0 for L in LETTERS}
    for alt in first["top_logprobs"]:
        t = alt["token"].strip()
        if t in p:
            p[t] += math.exp(alt["logprob"])
    total = sum(p.values())
    probs = {L: (p[L] / total if total > 0 else 0.0) for L in LETTERS}
    top = first["token"].strip()
    invalid = top not in LETTERS
    return {"label": None if invalid else LABELS[top], "letter": None if invalid else top,
            "confidence": 0.0 if invalid else probs[top], **{f"p_{L}": probs[L] for L in LETTERS},
            "letter_mass": total,  # probability on A-E before renormalizing
            "invalid": invalid, "top_token": first["token"], "error": None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--samples", nargs="+", default=["train"], choices=list(SAMPLE_FILES))
    ap.add_argument("--limit", type=int, default=None, help="items per sample, in a fixed random order (pilot)")
    ap.add_argument("--url", default=None, help="server URL; default: $SCRATCH_BASE/vllm/{host,port}.txt")
    ap.add_argument("--revision", default=os.environ.get("TEACHER_REVISION"), help="model revision served, recorded only")
    ap.add_argument("--prompt-version", default="v1")
    ap.add_argument("--concurrency", type=int, default=128)
    ap.add_argument("--top-logprobs", type=int, default=20)
    args = ap.parse_args()

    url = server_url(args.url)
    model = requests.get(f"{url}/v1/models", timeout=60).json()["data"][0]["id"]
    try:
        vllm_version = requests.get(f"{url}/version", timeout=60).json().get("version")
    except Exception:
        vllm_version = None
    template = (ROOT / "config" / f"prompt_{args.prompt_version}.txt").read_text()
    out_dir = TEACHER / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    run_path = out_dir / "run.json"
    run = json.loads(run_path.read_text()) if run_path.exists() else {"shards": []}
    run.update({"run_id": args.run_id, "model": model, "revision": args.revision, "prompt_version": args.prompt_version,
                "vllm_version": vllm_version, "server": url, "client_host": socket.gethostname(),
                "tensor_parallel": os.environ.get("VLLM_TP"), "image": os.environ.get("VLLM_SIF"),
                "concurrency": args.concurrency, "top_logprobs": args.top_logprobs})
    print(f"server {url}: model {model}, vLLM {vllm_version}")

    for sample in args.samples:
        df = pd.read_parquet(FINAL / SAMPLE_FILES[sample])
        if args.limit:
            df = df.sample(n=min(args.limit, len(df)), random_state=SEED)
        df = df.reset_index(drop=True)
        for k in range(math.ceil(len(df) / SHARD)):
            path = out_dir / f"{sample}-shard-{k:04d}.parquet"
            if path.exists():
                print(f"{path.name}: exists, skipped")
                continue
            part = df.iloc[k * SHARD:(k + 1) * SHARD]
            contents = [template.format(heading=r.heading or "(none)", prev_text=r.prev_text or "(none)", text=r.text)
                        for r in part.itertuples(index=False)]
            t0 = time.time()
            with ThreadPoolExecutor(args.concurrency) as pool:
                results = list(pool.map(lambda c: ask(url, model, c, args.top_logprobs), contents))
            dt = time.time() - t0
            res = pd.DataFrame([score(c, e) for c, e in results])
            res.insert(0, "para_id", part.para_id.values)
            res["use_for_training"] = ~res.invalid & (res.confidence >= MIN_CONFIDENCE)
            res["teacher_model"], res["teacher_revision"] = model, args.revision
            res["prompt_version"], res["run_id"], res["sample"] = args.prompt_version, args.run_id, sample
            tmp = path.with_suffix(".tmp")
            res.to_parquet(tmp, index=False)
            tmp.rename(path)  # a shard file exists only once it is complete
            run["shards"].append({"file": path.name, "items": len(part), "seconds": round(dt, 1),
                                  "items_per_second": round(len(part) / dt, 1), "errors": int(res.error.notna().sum()),
                                  "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            run_path.write_text(json.dumps(run, indent=2))
            print(f"{path.name}: {len(part):,} items in {dt:.0f}s ({len(part) / dt:.1f}/s); errors {res.error.notna().sum()}; "
                  f"invalid {res.invalid.mean():.2%}; labels {res.label.value_counts().to_dict()}", flush=True)
    run_path.write_text(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
