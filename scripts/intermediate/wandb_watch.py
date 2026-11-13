"""Send a training job's progress to Weights & Biases while it runs.

The intermediate track's copy of scripts/wandb_watch.py, with --run-dir added; the other tracks use
scripts/wandb_watch.py.

kev.train prints a line every 10 optimizer steps:

    ep0 step 40/100 loss 0.412 kl 0.087 anchor 0.000 0.311s/rec

This script follows the job's log, sends the loss and the speed to W&B, and stops when training saves or stops.
With --evals valid test it keeps the run open after training, waits for score.py's scores of each set and adds
them to the same run, so one W&B run holds the training curve and the validation and test scores. Without --log
it follows no training, for a job that only scores a released model (--model). Run on the
GPU node, W&B also records the node's GPU utilization and memory on its System tab. slurm/yens/intermediate/finetune_kev.slurm
starts it when it finds the hackathon's shared W&B key ($HACKATHON/wandb.env, or a .env of your own):

    sbatch slurm/yens/intermediate/finetune_kev.slurm

It needs `wandb login` once (your API key goes to ~/.netrc, never into this repo). Where compute nodes cannot reach
the internet, set WANDB_MODE=offline and run `wandb sync` on the run directory afterward from a login node.
"""
import argparse
import json
import os
import pwd
import re
import signal
import subprocess
import sys
import time

import wandb

STEP = re.compile(r"ep(\d+) step (\d+)/(\d+) loss ([\d.]+) kl ([\d.]+) anchor ([\d.]+) ([\d.]+)s/rec")
DONE = ("saved ", "stopped after step", "Traceback")


def follow(path):
    while not os.path.exists(path):
        time.sleep(5)
    with open(path) as f:
        while True:
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(5)


def train(run, a):
    """Follow the training log into the run. True once training saves; False (and the run finished as failed) if it
    stops or fails first."""
    last, cfg = None, a.run_dir and os.path.join(a.run_dir, "training_config.json")
    for line in follow(a.log):
        if cfg and os.path.exists(cfg):   # kev.train writes it before the first step
            c = json.load(open(cfg)).get("args", {})
            run.config.update({k: c.get(k) for k in ("init_from", "lr", "batch", "accum", "lora", "weights_dtype",
                                                     "max_steps", "max_state", "seed")})
            cfg = None
        if m := STEP.search(line):
            ep, step, steps, loss, _, _, sec_rec = m.groups()   # kl and anchor are unused terms (always 0 here)
            now, step = time.time(), int(step)
            row = {"loss": float(loss), "seconds_per_item": float(sec_rec), "epoch": int(ep),
                   "progress": step / int(steps)}
            if last:   # seconds per optimizer step over the last 10 steps, by this script's clock
                row["seconds_per_step"] = (now - last[0]) / (step - last[1])
            last = (now, step)
            run.log(row, step=step)
        elif line.startswith(DONE):
            run.summary["result"] = line.strip()
            if line.startswith("saved "):
                return True
            run.finish(exit_code=1)
            return False


def scores(path, since):
    """The scores score.py wrote to path, once it has written them in this job (not a file from an earlier attempt)."""
    while True:
        if os.path.exists(path) and os.path.getmtime(path) >= since:
            try:
                return json.load(open(path))
            except ValueError:   # still being written
                pass
        time.sleep(5)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", help="the job's Slurm log, to follow training; leave it out when the job trains nothing")
    ap.add_argument("--name", required=True, help="the run's name in W&B, e.g. cp1-1gpu")
    ap.add_argument("--gpus", type=int, default=1)
    ap.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "marlowe-hackathon"))
    ap.add_argument("--run-dir", help="the run's --out directory: its training_config.json settings go into the W&B config")
    ap.add_argument("--evals", nargs="*", default=[], help="after training, wait for these sets' scores (valid, test) and "
                    "add them to the run's summary as valid/..., test/...")
    ap.add_argument("--results", help="with --evals, the scores' path up to -<set>_scores.json, e.g. $WORK/results/i2/<jobid>")
    ap.add_argument("--model", help="when the job trains nothing, the released model it scores, for the run's config")
    a = ap.parse_args()
    start = time.time()
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader", "-i", "0"],
                         capture_output=True, text=True, check=True).stdout.strip()
    config = {"user": pwd.getpwuid(os.getuid()).pw_name,   # what whoami prints; everyone shares one W&B key
              "gpu": gpu, "gpus": a.gpus, "job": os.environ.get("SLURM_JOB_ID"), "node": os.uname().nodename}
    if a.model:
        config["init_from"] = a.model
    run = wandb.init(project=a.project, name=f"{a.name}-{os.environ.get('SLURM_JOB_ID', 'local')}", config=config)
    print(f"W&B run: {run.url}", flush=True)
    signal.signal(signal.SIGTERM, lambda *_: (run.finish(exit_code=1), sys.exit(0)))   # the job ended first
    if a.log and not train(run, a):
        return
    for e in a.evals:   # one run holds the training curve and every set's scores: nothing reopens it later
        run.summary.update({f"{e}/{k}": v for k, v in scores(f"{a.results}-{e}_scores.json", start).items() if k != "run"})
    run.finish(exit_code=0)


if __name__ == "__main__":
    main()
