---
layout: default
title: "4. One Full Node"
nav_order: 8
permalink: /checkpoint-4/
---

# Checkpoint 4: One Full Node

**Goal:** run the same job on all 8 H100s of one Marlowe node, and see how far the scaling table goes.

---

## Step 1: Run on 8 GPUs

```bash
sbatch slurm/marlowe/04_train_8gpu.slurm
```
{: .marlowe }

Compared with Checkpoint 3: `--gpus-per-node=8` and `--exclusive` take the whole node, whose 8 H100s are linked by
NVLink; `GPUS=8` makes each step 2 records per GPU (still 16 in all); and `torchrun --nproc_per_node 8` starts eight
training processes. Look for
`world=8` in the log:

```bash
tail -f logs/ceo-cp4-<jobid>.out
```
{: .marlowe }

Check that all eight GPUs are working:

```bash
tail -8 logs/gpu-<jobid>.csv
```
{: .marlowe }

## Step 2: Extend the table

```bash
$PY scripts/step_times.py $WORK/runs/cp3-1gpu $WORK/runs/cp4-8gpu
```
{: .marlowe }

Add your Yens H200 rows from [Checkpoints 1 and 2]({{ '/checkpoint-2/' | relative_url }}) and answer:

1. What is the speedup from 1 to 8 H100s? How close is it to 8?
2. Which scale has the lowest **epoch GPU-hours**? That is the cheapest way to train, and it is usually not the
   fastest.
3. With your 3-epoch estimate, how long would the full run take on one node, and would it fit in `preempt`'s 4-hour
   limit?

{: .tip }
> With only 16 records per step, each of the 8 GPUs gets 2 records and spends much of the step waiting for the others.
> Real runs on many GPUs use larger steps. Try `ACCUM=8 sbatch slurm/marlowe/04_train_8gpu.slurm` (64 records per
> step) and compare seconds per record (`step_times.py --per-step 64`), not seconds per step.

{: .checkpoint }
> **Checkpoint 4 (50 GPU-hours).** Post your table with the 8-GPU row, and your answers to the three questions, in
> Slack. Then put up a 🟩 green sticky. 🟥 if you are stuck.
