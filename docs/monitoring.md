---
layout: default
title: "Monitoring Training"
nav_order: 4
permalink: /monitoring/
---

# Monitoring Training

A training job runs on a GPU node, not in your terminal. There are three ways to watch it: the job's log, a GPU log the
job writes next to it, and, if you want charts, Weights & Biases.

---

## Is it running?

```bash
squeue --me
```
{: .yens }

`ST` is `PD` while the job waits for GPUs and `R` once it runs; `NODELIST(REASON)` shows the node, or why it is
waiting. `scontrol show job <jobid>` gives the full picture.

## The job's log

Every job writes `logs/<job name>-<jobid>.out` in the repository. Follow it as it grows:

```bash
tail -f logs/ceo-train-1gpu-<jobid>.out
```
{: .yens }

Press `Ctrl-C` to stop following; the job keeps running. After a minute or two of loading, Kev prints how it set up the
run, then a line every 10 optimizer steps:

```
device=cuda world=1 trainable params=4207.1M
52757 training requests (holdout=[]), questions by type {'choice': 78747, 'noul': 25990}
ep0 step 10/100 loss 0.914 kl 0.000 anchor 0.000 1.510s/rec
ep0 step 20/100 loss 0.497 kl 0.000 anchor 0.000 1.192s/rec
...
saved /scratch/users/<sunet>/ceo-turnover/runs/cp1-1gpu
```
{: .output }

| Field | Meaning |
|---|---|
| `world` | how many GPUs share the job |
| `step 20/100` | optimizer steps done, of the steps this job runs |
| `loss` | cross-entropy between Kev's probabilities and Jev's, averaged over the last 10 steps; should fall |
| `kl`, `anchor` | optional extra loss terms, not used today; they stay at 0 |
| `s/rec` | seconds per record on one GPU since the job started, loading included; it falls as the run settles |
| `saved ...` | training finished and wrote the model checkpoint |

When the job finishes, the run directory holds `training_metrics.json` with the time of every step and the peak GPU
memory. `scripts/step_times.py` turns it into a row of the scaling table.

## GPU memory and utilization

Every training job also writes `logs/gpu-<jobid>.csv`, a sample of `nvidia-smi` every 15 seconds:

```bash
tail -5 logs/gpu-<jobid>.csv
```
{: .yens }

```
timestamp, index, name, utilization.gpu [%], memory.used [MiB], memory.total [MiB]
2026/10/27 08:16:30.423, 0, NVIDIA A40, 100 %, 19855 MiB, 46068 MiB
```
{: .output }

Utilization near 100% means the GPU is busy computing. Utilization that keeps dropping to 0 means it is waiting on
something: data, host memory (one-GPU full fine-tuning keeps the optimizer state there), or other GPUs. Memory used
tells you how close you are to the GPU's limit before you try a bigger batch or a bigger model.

For a live look, open a shell on the job's node and run `nvidia-smi`:

```bash
srun --jobid <jobid> --overlap --pty nvidia-smi
```
{: .yens }

## Weights & Biases (optional)

[Weights & Biases](https://wandb.ai) (W&B) draws the loss, the speed and the GPUs' utilization and memory as charts in
your browser, and puts runs side by side, which makes the scaling comparison easy to see.

Kev's trainer does not talk to W&B itself. `scripts/wandb_watch.py` runs alongside the training on the same node,
reads the log lines above as they appear, and sends the loss and the speed to W&B. Because it runs on the GPU node, W&B also records that
node's GPUs on the run's **System** tab.

**Once:** create a free account at [wandb.ai](https://wandb.ai) with your Stanford email, copy your API key from
[wandb.ai/authorize](https://wandb.ai/authorize), and log in on each cluster:

```bash
source env/yens.sh
$KEV_HOME/kev/.venv/bin/wandb login
```
{: .yens }

```bash
source env/marlowe.sh
$KEV_HOME/kev/.venv/bin/wandb login
```
{: .marlowe }

The key is saved in `~/.netrc` in your home directory. Never put it in this repository or in a script.

**Then** add `WANDB=1` in front of any training job:

```bash
WANDB=1 sbatch slurm/yens/01_train_1gpu.slurm
```
{: .yens }

The run appears in your W&B project `marlowe-hackathon`, named after the checkpoint and job ID (for example
`cp1-1gpu-873242`). Charts update every 10 steps.

{: .note }
> If compute nodes cannot reach wandb.ai, the run will fail to connect. Submit with
> `WANDB=1 WANDB_MODE=offline sbatch ...`: the run is written to `wandb/` in the repository, and
> `$KEV_HOME/kev/.venv/bin/wandb sync wandb/offline-run-*` from a login node uploads it afterward.
