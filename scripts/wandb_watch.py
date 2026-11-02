"""Send a training job's progress to Weights & Biases while it runs.

kev.train prints a line every 10 optimizer steps:

    ep0 step 40/100 loss 0.412 kl 0.087 anchor 0.000 0.311s/rec

This script follows the job's log, sends the loss and the speed to W&B, and stops when training saves or stops. Run on the
GPU node, W&B also records the node's GPU utilization and memory on its System tab. The train_*.slurm scripts start
it when WANDB=1:

    WANDB=1 sbatch slurm/yens/01_train_1gpu.slurm

It needs `wandb login` once (your API key goes to ~/.netrc, never into this repo). Where compute nodes cannot reach
the internet, set WANDB_MODE=offline and run `wandb sync` on the run directory afterward from a login node.
"""
import argparse
import os
import re
import signal
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True, help="the job's Slurm log")
    ap.add_argument("--name", required=True, help="the run's name in W&B, e.g. cp1-1gpu")
    ap.add_argument("--gpus", type=int, default=1)
    ap.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "marlowe-hackathon"))
    a = ap.parse_args()
    run = wandb.init(project=a.project, name=f"{a.name}-{os.environ.get('SLURM_JOB_ID', 'local')}",
                     config={"gpus": a.gpus, "job": os.environ.get("SLURM_JOB_ID"), "node": os.uname().nodename})
    signal.signal(signal.SIGTERM, lambda *_: (run.finish(exit_code=1), sys.exit(0)))   # the job ended first
    last = None
    for line in follow(a.log):
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
            run.finish(exit_code=0 if line.startswith("saved ") else 1)
            return


if __name__ == "__main__":
    main()
