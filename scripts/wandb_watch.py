"""Send a training job's progress to Weights & Biases while it runs.

kev.train prints a line every 10 optimizer steps:

    ep0 step 40/100 loss 0.412 kl 0.087 anchor 0.000 0.311s/rec

This script follows the job's log, sends the loss and the speed to W&B, and stops when training saves or stops. Run on the
GPU node, W&B also records the node's GPU utilization and memory on its System tab. The Advanced training jobs start
it through slurm/marlowe/advanced/wandb.sh whenever they find the room's key; the older train_*.slurm templates start
it when WANDB=1:

    WANDB=1 sbatch slurm/yens/01_train_1gpu.slurm

It needs `wandb login` once (your API key goes to ~/.netrc, never into this repo). Where compute nodes cannot reach
the internet, set WANDB_MODE=offline and run `wandb sync` on the run directory afterward from an interactive Yen node or the Marlowe login node.
"""
import argparse
import json
import os
import re
import signal
import statistics
import subprocess
import sys
import time

import wandb

STEP = re.compile(r"ep(\d+) step (\d+)/(\d+) loss ([\d.]+) kl ([\d.]+) anchor ([\d.]+) ([\d.]+)s/rec")
DONE = ("saved ", "stopped after step", "Traceback")
RECORDS = re.compile(r"^(\d+) training requests")   # kev.train: the records one epoch trains on
STAMP = re.compile(r"^\[\s*\d+:\d{2}\] ")   # the [mm:ss] that slurm/train_args.sh's stamp() adds


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


def gpus_now():
    """The busiest GPU's memory in GB and the GPUs' average use in %, on this node, from nvidia-smi."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout
        rows = [[float(x) for x in line.split(",")] for line in out.strip().splitlines()]
        return max(r[0] for r in rows) / 1024, statistics.mean(r[1] for r in rows)
    except Exception:
        return None


def final_numbers(run_dir, records, per_step):
    """What scripts/step_times.py prints, from the run's training_metrics.json, for the run's summary."""
    m = json.load(open(os.path.join(run_dir, "training_metrics.json")))
    times = m["step_seconds"][3:] or m["step_seconds"]
    sec = statistics.median(times)
    out = {"median_seconds_per_step": sec, "peak_gpu_gb": m["peak_device_bytes"] / 1e9, "world_size": m["world_size"]}
    if records:
        out["epoch_hours"] = records / per_step * sec / 3600
        out["epoch_gpu_hours"] = out["epoch_hours"] * m["world_size"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True, help="the job's Slurm log")
    ap.add_argument("--name", required=True, help="the run's name in W&B, e.g. cp1-1gpu")
    ap.add_argument("--gpus", type=int, default=1)
    ap.add_argument("--run-dir", help="the run's --out directory: its settings go into the config, and when training saves, "
                                      "its training_metrics.json gives the summary the median time per step and the epoch cost")
    ap.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "marlowe-hackathon"))
    a = ap.parse_args()
    run = wandb.init(project=a.project, name=f"{a.name}-{os.environ.get('SLURM_JOB_ID', 'local')}",
                     config={"user": os.environ.get("USER"), "gpus": a.gpus, "job": os.environ.get("SLURM_JOB_ID"), "node": os.uname().nodename})
    signal.signal(signal.SIGTERM, lambda *_: (run.finish(exit_code=1), sys.exit(0)))   # the job ended first
    last, records, peak = None, None, 0.0
    per_step, cfg = 16, a.run_dir and os.path.join(a.run_dir, "training_config.json")
    print(f"W&B run: {run.url}", flush=True)
    for line in follow(a.log):
        line = STAMP.sub("", line)
        if cfg and os.path.exists(cfg):   # kev.train writes it before the first step
            c = json.load(open(cfg)).get("args", {})
            per_step = (c.get("batch") or 1) * (c.get("accum") or 1) * a.gpus
            run.config.update({k: c.get(k) for k in ("base", "full_ft", "lora", "lr", "batch", "accum", "max_steps",
                                                     "max_state", "weights_dtype", "checkpointing")} | {"records_per_step": per_step})
            cfg = None
        if r := RECORDS.match(line):
            records = int(r.group(1))
            run.config.update({"records_per_epoch": records})
        if m := STEP.search(line):
            ep, step, steps, loss, _, _, sec_rec = m.groups()   # kl and anchor are unused terms (always 0 here)
            now, step = time.time(), int(step)
            row = {"loss": float(loss), "seconds_per_item": float(sec_rec), "epoch": int(ep),
                   "progress": step / int(steps)}
            if last:   # seconds per optimizer step over the last 10 steps, by this script's clock
                row["seconds_per_step"] = (now - last[0]) / (step - last[1])
                if records:   # what one epoch would take at this speed, as step_times.py works it out
                    row["epoch_hours_so_far"] = records / per_step * row["seconds_per_step"] / 3600
                    row["epoch_gpu_hours_so_far"] = row["epoch_hours_so_far"] * a.gpus
            if g := gpus_now():
                row["gpu_memory_gb"], row["gpu_use_percent"] = g
                peak = max(peak, g[0])
                run.summary["gpu_memory_peak_gb"] = peak
            last = (now, step)
            run.log(row, step=step)
        elif line.startswith(DONE):
            run.summary["result"] = line.strip()
            if line.startswith("saved ") and a.run_dir:
                try:
                    run.summary.update(final_numbers(a.run_dir, records, per_step))
                except (OSError, KeyError, ValueError) as e:
                    print(f"W&B: no training_metrics.json summary ({e})", flush=True)
            run.finish(exit_code=0 if line.startswith("saved ") else 1)
            return


if __name__ == "__main__":
    main()
