"""Put B5's results on the room's W&B board: my_analysis.py calls analysis() every time it runs. W&B is optional here:
without a key, or if W&B fails, this prints one line and the script carries on. (B4's jobs log themselves, through the
I5 job's shards.py.)

The key is found the same way as scripts/beginner/wandb_key.sh: WANDB_API_KEY if it is set, else the line
WANDB_API_KEY=... in the hackathon's shared wandb.env ($SHARE on Marlowe), else in .env at the top of the repo.
WANDB_PROJECT, if set, sends the run to another project (instructors test with WANDB_PROJECT=beginner-smoke-test).
"""
import os
import re

ENTITY = os.environ.get("WANDB_ENTITY", "Marlowe-Hackathon")


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


def analysis(done, kev_fit, jev_fit, charts):
    """B5: one run per person, updated each time my_analysis.py runs. done maps each exercise to True once it is
    filled in; kev_fit and jev_fit are Exercise 5's regressions (or None); charts are PNGs to show if they exist."""
    user = os.environ.get("USER", "me")
    n = sum(done.values())
    run = start("Beginner Exercise 5", user, run_id=re.sub(r"[^A-Za-z0-9_-]", "-", f"b5-{user}"), config={"user": user})
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

