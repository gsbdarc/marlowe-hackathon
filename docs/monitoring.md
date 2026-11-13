---
layout: default
title: "Monitoring Training"
nav_order: 2
parent: "Reference"
permalink: /monitoring/
---

# Monitoring Training

A training job runs on a GPU node, not in your terminal. Watch it in the job's log, in the GPU log the job writes next
to it, or, for charts, in Weights & Biases.

---

## Is it running?

```bash
squeue --me
```
{: .yens }

`ST` is `PD` while the job waits for GPUs and `R` once it runs; `NODELIST(REASON)` shows the node, or why it is
waiting. `scontrol show job <jobid>` shows the job's full details.

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
| `s/rec` | a running average since the job started, per item Kev builds from the records (a record can yield more than one), not per filing; it reads lower at `BATCH=4` even when each step is slower, so compare runs with `step_times.py` instead. W&B charts it as `seconds_per_item` |
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

## Weights & Biases

[Weights & Biases](https://wandb.ai) (W&B) is a website that records every training run: its settings, its loss and
speed as it trains, and its GPUs' utilization and memory, drawn as charts. It puts runs side by side, which makes a
scaling comparison easy to see.

The track jobs report to the hackathon's W&B team, [Marlowe-Hackathon on W&B](https://forge.coreweave.com/wandb/Marlowe-Hackathon), with one shared key that the
organizers keep in `wandb.env` in the hackathon's shared folder on each cluster. Each job reads that file before it
starts, so there is nothing to set up. A line `WANDB_API_KEY=<key>` in a `.env` file at the top of your clone, which
git ignores, overrides it. If the job cannot find a key, its log says `W&B off` and the job runs without W&B.

Kev's trainer does not talk to W&B itself. `scripts/wandb_watch.py` runs alongside the training on the same node,
reads the log lines above as they appear, and sends the loss and the speed to W&B every 10 optimizer steps. Because it
runs on the GPU node, W&B also records that node's GPUs on the run's **System** tab. The job's log shows a `W&B run:`
line with a link to the run.

After the hackathon, use a key of your own: create a free account at [wandb.ai](https://wandb.ai), copy your key from
[wandb.ai/authorize](https://wandb.ai/authorize), and put it in `.env` in your clone or run
`$KEV_HOME/kev/.venv/bin/wandb login` once on each cluster. Never commit a key to a repository. The older templates in
`slurm/yens/` and `slurm/marlowe/` send a run to W&B only when you submit with `WANDB=1 sbatch ...`.

{: .note }
> If compute nodes cannot reach wandb.ai, submit with `WANDB_MODE=offline sbatch ...`: the run is written to a `wandb/`
> folder (under `$WORK` for the track jobs), and `$KEV_HOME/kev/.venv/bin/wandb sync <that folder>/offline-run-*` from an interactive Yen node or the
> Marlowe login node uploads it afterward.
