"""The scaling table: time per step at each scale, and what one epoch of training would cost.

Reads training_metrics.json from each finished run (kev.train writes it next to the checkpoint).

    $PY scripts/step_times.py $WORK/runs/cp1-1gpu $WORK/runs/cp2-batch4

The first steps of a run are slower (compilation, warm caches), so the median step time skips the first 3.
GPU-hours for one epoch = steps per epoch x seconds per step x GPUs / 3600. Steps per epoch is the number of training
records divided by the records per step (--batch x --accum x GPUs: 16 at every scale in slurm/train_args.sh).
"""
import argparse
import json
import os
import statistics


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run directories (each with training_metrics.json)")
    ap.add_argument("--records", type=int, default=52_757, help="records trained per epoch: the 'N training requests' line of the training log (52,757 for the default train.jsonl)")
    ap.add_argument("--per-step", type=int, default=16, help="records per optimizer step (slurm/train_args.sh)")
    a = ap.parse_args()
    print(f"{'run':<16} {'GPUs':>4} {'steps':>5} {'s/step':>7} {'peak GPU GB':>11} {'epoch hours':>11} {'epoch GPU-hours':>15}")
    for run in a.runs:
        m = json.load(open(os.path.join(run, "training_metrics.json")))
        times = m["step_seconds"][3:] or m["step_seconds"]
        sec = statistics.median(times)
        hours = a.records / a.per_step * sec / 3600
        print(f"{os.path.basename(run.rstrip('/')):<16} {m['world_size']:>4} {m['optimizer_steps']:>5} {sec:>7.2f} "
              f"{m['peak_device_bytes'] / 1e9:>11.1f} {hours:>11.1f} {hours * m['world_size']:>15.1f}")


if __name__ == "__main__":
    main()
