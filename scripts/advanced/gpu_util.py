"""How busy the GPUs were and how much memory they used, from a job's GPU log.

Every training job writes logs/gpu-<jobid>.csv (a two-node job, one file per node): nvidia-smi's utilization and
memory for each GPU every 15 seconds. With no arguments this reads the newest job's logs; or name the files.

    $PY scripts/advanced/gpu_util.py                          # the newest job
    $PY scripts/advanced/gpu_util.py logs/gpu-540493.csv      # one job
    $PY scripts/advanced/gpu_util.py logs/gpu-540493.csv logs/gpu-540584-*.csv

The average includes the minutes the job spends loading the model and saving it, when the GPUs wait.
"""
import argparse
import csv
import glob
import os
import re


def job_of(path):
    m = re.search(r"gpu-(\d+)", os.path.basename(path))
    return m.group(1) if m else path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*", help="GPU logs (default: the newest job's logs/gpu-*.csv)")
    a = ap.parse_args()
    files = a.logs
    if not files:
        found = glob.glob("logs/gpu-*.csv")
        if not found:
            raise SystemExit("no logs/gpu-*.csv here: run this from your clone of the repository")
        newest = job_of(max(found, key=os.path.getmtime))
        files = sorted(f for f in found if job_of(f) == newest)
    jobs = {}
    for f in files:
        jobs.setdefault(job_of(f), []).append(f)
    print(f"{'job':<10} {'GPUs':>4} {'average use':>11} {'peak use':>8} {'peak memory GB':>14}")
    for job, paths in jobs.items():
        util, mem, gpus = [], [], set()
        for p in paths:
            for row in csv.DictReader(open(p), skipinitialspace=True):
                gpus.add((p, row["index"]))
                util.append(float(row["utilization.gpu [%]"].split()[0]))
                mem.append(float(row["memory.used [MiB]"].split()[0]) / 1024)
        if not util:
            print(f"{job:<10} no samples yet")
            continue
        print(f"{job:<10} {len(gpus):>4} {sum(util) / len(util):>10.0f}% {max(util):>7.0f}% {max(mem):>14.1f}")


if __name__ == "__main__":
    main()
