"""Put the Beginner track's B4 and B5 results on the room's W&B board. W&B is optional here: without a key, or if W&B
fails, this prints one line and whatever called it carries on.

    $PY scripts/beginner/wandb_log.py label $WORK/results/b4/<jobid>     # B4: label.slurm runs this when it finishes

my_analysis.py (B5) calls analysis() itself, every time it runs.

The key is found the same way as scripts/beginner/wandb_key.sh: WANDB_API_KEY if it is set, else the line
WANDB_API_KEY=... in the hackathon's shared wandb.env ($SHARE on Marlowe), else in .env at the top of the repo.
WANDB_PROJECT, if set, sends the run to another project (instructors test with WANDB_PROJECT=beginner-smoke-test).
"""
import glob
import json
import os
import re
import sys

ENTITY = os.environ.get("WANDB_ENTITY", "Marlowe-Hackathon")
ALL_FILINGS = 296_477


def key():
    """The room's W&B key, or None. Each file is read for its WANDB_API_KEY line, not run."""
    if os.environ.get("WANDB_API_KEY"):
        return os.environ["WANDB_API_KEY"]
    shared = os.environ.get("HACKATHON") or os.environ.get("SHARE") or "/nonexistent"
    found = None
    for f in (os.path.join(shared, "wandb.env"), ".env"):
        try:
            lines = open(f).read().splitlines()
        except OSError:
            continue
        for line in lines:
            m = re.match(r"\s*(?:export\s+)?WANDB_API_KEY=(.*)", line)
            k = m.group(1).strip().strip("\"'").strip() if m else ""
            if k and "<" not in k and ">" not in k:       # skip the placeholder <the room's key>
                found = k                                 # .env, read last, wins
    return found


def start(project, name, run_id=None, config=None):
    """A W&B run, or None (with one line saying why) if there is no key or W&B fails."""
    k = key()
    if not k:
        print("W&B off: no key in the shared wandb.env or in .env")
        return None
    os.environ["WANDB_API_KEY"] = k
    os.environ.setdefault("WANDB_SILENT", "true")
    cache = os.environ.get("XDG_CACHE_HOME")              # keep W&B's files out of home, as the jobs do
    if cache:
        os.environ.setdefault("WANDB_CACHE_DIR", os.path.join(cache, "wandb"))
        os.environ.setdefault("WANDB_CONFIG_DIR", os.path.join(cache, "wandb-config"))
    try:
        import wandb
        return wandb.init(entity=ENTITY, project=os.environ.get("WANDB_PROJECT", project), name=name, id=run_id,
                          resume="allow" if run_id else None, config=config or {},
                          dir=os.environ.get("WORK"), settings=wandb.Settings(console="off"))
    except Exception as e:                                # a W&B problem must never stop the job or the script
        print(f"W&B off: {type(e).__name__}: {e}")
        return None


def finish(run, what):
    try:
        print(f"W&B: {what} is on the board: {run.url}")
        run.finish()
    except Exception as e:
        print(f"W&B: could not finish the run: {type(e).__name__}: {e}")


def label(d):
    """B4: one run per labeling job, with the numbers shards.py prints for it."""
    jobs = [json.load(open(p)) for p in glob.glob(os.path.join(d, "job-*.json"))]
    shards = [json.load(open(p)) for p in glob.glob(os.path.join(d, "shard-*_summary.json"))]
    wall = max((s["wall_seconds"] for s in shards), default=0)
    if not jobs or not wall:
        print(f"W&B: nothing to log in {d} (no job-*.json, or no labeling time)")
        return
    gpus = sum(j["gpus"] for j in jobs)
    n = sum(s["succeeded"] for s in shards)
    rate = n / wall
    jobid = os.path.basename(d.rstrip("/"))
    user = os.environ.get("USER", "me")
    run = start("beginner-4-label", f"{user}-{gpus}gpu-{jobid}",
                config={"gpus": gpus, "job": jobid, "model": jobs[0].get("run"), "user": user})
    if run is None:
        return
    try:
        run.summary.update({
            "gpus": gpus,
            "filings": n,
            "failed": sum(s["filings"] - s["succeeded"] for s in shards),
            "filings_per_s": round(rate, 1),
            "filings_per_s_per_gpu": round(rate / gpus, 1),
            "load_seconds": max(j["load_seconds"] for j in jobs),
            "minutes": round(wall / 60, 1),
            "all_filings_hours": round(ALL_FILINGS / rate / 3600, 2),
            "all_filings_gpu_hours": round(ALL_FILINGS / rate / 3600 * gpus, 2),
        })
    except Exception as e:
        print(f"W&B: could not log the numbers: {type(e).__name__}: {e}")
    finish(run, "this job")


def analysis(done, kev_fit, jev_fit, charts):
    """B5: one run per person, updated each time my_analysis.py runs. done maps each exercise to True once it is
    filled in; kev_fit and jev_fit are Exercise 5's regressions (or None); charts are PNGs to show if they exist."""
    user = os.environ.get("USER", "me")
    n = sum(done.values())
    run = start("beginner-5-analysis", user, run_id=re.sub(r"[^A-Za-z0-9_-]", "-", f"b5-{user}"), config={"user": user})
    if run is None:
        return
    try:
        import wandb
        summary = {"exercises_done": n, **{f"{name}_done": bool(v) for name, v in done.items()}}
        for name, fit in (("kev", kev_fit), ("jev", jev_fit)):  # None clears a slope an earlier run left behind
            summary[f"e5_{name}_slope"] = None if fit is None else round(float(fit.slope), 3)
            summary[f"e5_{name}_t"] = None if fit is None else round(float(fit.slope / fit.stderr), 1)
        run.summary.update(summary)
        images = {os.path.splitext(os.path.basename(p))[0].replace("-", "_"): wandb.Image(p)
                  for p in charts if os.path.exists(p)}
        if images:
            run.log(images)
    except Exception as e:
        print(f"W&B: could not log the results: {type(e).__name__}: {e}")
    finish(run, f"your progress ({n} of {len(done)} exercises)")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "label":
        label(sys.argv[2])
    else:
        sys.exit(__doc__)
