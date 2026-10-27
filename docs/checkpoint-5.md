---
layout: default
title: "5. Two Nodes and Resume"
nav_order: 9
permalink: /checkpoint-5/
---

# Checkpoint 5: Two Nodes and Resume

**Goal:** run across two Marlowe nodes (16 H100s), stop the job partway, and continue it from its last resume point.
This is the advanced checkpoint.

---

## Why resume points

A real training run can take longer than a job is allowed to run (4 hours on `preempt`), and on `preempt` a job can
be stopped to make room for others. A **resume point** is a snapshot of the job partway through: the weights, the
optimizer's state and the position in the training data. A job started with `--resume 1` looks for one and continues
from it instead of starting over.

## Step 1: Start, and stop at step 100

```bash
STOP_AFTER=100 sbatch slurm/marlowe/05_train_2node.slurm
```
{: .marlowe }

The script asks for two whole nodes and uses `srun` to start one `torchrun` on each. The two connect to each other
through the first node (`--rdzv_endpoint`), giving one job of 16 processes (`world=16` in the log). It runs 300 steps
in all, writes a resume point every 50 steps (`SAVE_STEPS`), and `STOP_AFTER=100` makes it exit after step 100, as if
it had been preempted:

```
stopped after step 100; continue with --resume 1
```
{: .output }

The resume point is in `$WORK/runs/cp5-2node/resume/`:

```bash
ls $WORK/runs/cp5-2node/resume/
```
{: .marlowe }

## Step 2: Resume

Submit the same script again, without `STOP_AFTER`:

```bash
sbatch slurm/marlowe/05_train_2node.slurm
```
{: .marlowe }

The new job's log should say where it picked up, then carry on from step 110:

```
resumed from .../cp5-2node/resume/step-100: step 100, epoch 0, micro-batch ...
```
{: .output }

When it ends with `saved`, the resume points are deleted: the finished checkpoint replaces them.

{: .warning }
> A resumed job must run the same training: the same `STEPS`, data and settings. Only the save and stop settings may
> change. Kev refuses to resume a run whose arguments differ.

## Step 3: Add the last row

```bash
$PY scripts/step_times.py $WORK/runs/cp3-1gpu $WORK/runs/cp4-8gpu $WORK/runs/cp5-2node
```
{: .marlowe }

Going from 8 to 16 GPUs means crossing the network between nodes, which is slower than the links inside a node. Does
the time per step still fall?

{: .checkpoint }
> **Checkpoint 5 (500 GPU-hours).** Post both job IDs, the `resumed from` line and your full scaling table in Slack.
> Then put up a 🟩 green sticky. 🟥 if you are stuck.
