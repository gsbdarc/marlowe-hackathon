---
layout: default
title: "1. One GPU on the Yens"
nav_order: 5
permalink: /checkpoint-1/
---

# Checkpoint 1: One GPU on the Yens

**Goal:** measure where Kev-4B starts, then fine-tune it on Jev's labels on one H200 and read the job's speed and
memory use.

You need the [setup]({{ '/setup/' | relative_url }}) done: Kev installed and the training files built. Every command
below runs from your clone of the repository on the Yens.

```bash
cd /scratch/users/$USER/marlowe-hackathon
source env/yens.sh
```
{: .yens }

---

## Step 1: Make Kev-4B trainable

Kev-4B is released as a small add-on (an adapter) on top of Qwen3.5-4B. A full fine-tune trains every weight, so it
needs the two folded together into one set of weights. That is a CPU job of about 6 minutes, and you do it once:

```bash
sbatch slurm/yens/00_merge_kev.slurm
```
{: .yens }

It ends with the size of the merged model:

```
7.9G	/scratch/users/<sunet>/ceo-turnover/kev-4b-full/checkpoint
```
{: .output }

## Step 2: The starting point

While it merges, measure how well Kev-4B matches Jev before any training. This job starts a Kev server on one GPU,
sends it the 1,000 test filings, and scores its answers against Jev's:

```bash
sbatch slurm/yens/serve_and_label.slurm
```
{: .yens }

The scores are in `logs/ceo-label-<jobid>.out` and in `$WORK/results/kev-4b-zeroshot_scores.json`:

```
                  run  answered  status_agree_weighted  status_agree_on_ceo_changes  ceo_change_f1  reason_agree_on_ceo_changes  filings_per_second
kev-4b-zeroshot.jsonl      1000                  0.883                        0.584          0.839                        0.826                 6.1

kev-4b-zeroshot.jsonl: status agreement by Jev's status
  not a CEO change         93.7%
  temporary leave          70.0%
  becomes exec chair       74.4%
  becomes non-exec chair   58.3%
  director only            79.7%
  other role at company    71.8%
  leaves entirely          19.9%
  interim steps aside      83.8%
```
{: .output }

- **status_agree_weighted**: how often Kev-4B picks Jev's status, weighted to stand for all 56,334 test filings.
  Most filings are not CEO changes, and those are easy, so this number is high.
- **status_agree_on_ceo_changes**: the same, only on the 700 CEO changes. This is the number to move.
- **ceo_change_f1**: how well it answers the yes-or-no question "is this a CEO change?"
- **reason_agree_on_ceo_changes**: agreement on why the CEO left.

Kev-4B nearly always knows whether a filing is about the CEO, but on CEO changes it picks the same status as Jev only
58% of the time, and when the CEO leaves the company entirely, it agrees only one time in five. Write these numbers down: you will compare against them after training.

## Step 3: Train on one GPU

```bash
sbatch slurm/yens/01_train_1gpu.slurm
```
{: .yens }

Open `slurm/yens/01_train_1gpu.slurm` while it waits in the queue. It asks for one H200, 24 CPUs and 92 GB of memory,
and runs `kev.train` with the arguments in `slurm/train_args.sh`: a full fine-tune of Kev-4B on `train.jsonl` for 100
optimizer steps of 16 records each.

{: .note }
> Why 92 GB of host memory for one GPU? With a single GPU, Kev keeps the full-precision copy of the weights and the
> optimizer's state in the node's memory instead of on the GPU. That lets a 4B model train on one GPU, at the cost of
> some speed. With more GPUs (on Marlowe, [Checkpoint 4]({{ '/checkpoint-4/' | relative_url }})) that state is split across them.

{: .tip }
> The Yens have only two H200s, shared by the whole room. If your job is still pending (`PD` in `squeue --me`) after
> a few minutes, cancel it and run on an A40 instead: `sbatch -C GPU_MODEL:A40 slurm/yens/01_train_1gpu.slurm`. An A40
> takes about 14 seconds per step for this job, so 100 steps take about 25 minutes.

Add `WANDB=1` in front of `sbatch` to also watch it in Weights & Biases; see
[Monitoring Training]({{ '/monitoring/' | relative_url }}).

## Step 4: Watch it

```bash
squeue --me
tail -f logs/ceo-train-1gpu-<jobid>.out
```
{: .yens }

Loading takes a few minutes. Then a line every 10 steps:

```
device=cuda world=1 trainable params=4207.1M
dropped 1669 of 54426 records that exceed the training context (2048 state / 2688 branch / 3712 packed tokens)
52757 training requests (holdout=[]), questions by type {'choice': 78747, 'noul': 25990}
ep0 step 10/100 loss 0.914 kl 0.000 anchor 0.000 1.510s/rec
ep0 step 20/100 loss 0.497 kl 0.000 anchor 0.000 1.192s/rec
ep0 step 30/100 loss 0.340 kl 0.000 anchor 0.000 1.095s/rec
```
{: .output }

`loss` should fall. (`kl` and `anchor` are optional extra terms we do not use, so they stay at 0.) [Monitoring Training]({{ '/monitoring/' | relative_url }}) explains every field.

In a second terminal, check the GPU log:

```bash
tail -3 logs/gpu-<jobid>.csv
```
{: .yens }

## Step 5: Read the result

When the log ends with `saved .../runs/cp1-1gpu`, that directory is your fine-tuned model (`config.json`, the
`model-*.safetensors` weights and Kev's answer head `head.pt`), plus the job's timings in `training_metrics.json`:

```bash
$PY scripts/step_times.py $WORK/runs/cp1-1gpu
```
{: .yens }

This prints the median seconds per step, the peak GPU memory, and what one full epoch (about 3,300 steps) would take.

{: .checkpoint }
> **Checkpoint 1.** Post in the Slack channel your job ID, your seconds per step and your peak GPU memory, then put up
> a 🟩 green sticky. Stuck? Put up a 🟥 red sticky and a helper will come over.

---

## If you have time

- Look at `$WORK/results/kev-4b-zeroshot_scores.json`: which statuses does Kev-4B get wrong most often?
- Re-run Step 3 with `STEPS=200 sbatch ...`. Does the time per step change? Does the loss keep falling?
