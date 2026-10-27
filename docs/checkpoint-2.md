---
layout: default
title: "2. Plan the GPU-hours"
nav_order: 6
permalink: /checkpoint-2/
---

# Checkpoint 2: Plan the GPU-hours

**Goal:** tune the one-GPU job, then estimate the GPU-hours a full training run would need. That estimate is what a
Marlowe application asks for.

---

## Why one GPU on the Yens

A Yen GPU node has two or more GPUs, but they have no **NVLink**, the fast direct link between GPUs. They exchange
data over the PCIe bus instead. When a job is split across GPUs, every step the GPUs swap the model's weights and
gradients, so the speed of that link decides whether a second GPU helps.

DARC tested it: the Checkpoint 1 job on one A40 and on two A40s, 30 steps each:

```
run              GPUs steps  s/step peak GPU GB epoch hours epoch GPU-hours
cp1-1gpu            1    30   14.02        19.4        12.8            12.8
cp2-2gpu            2    30   14.19        38.1        13.0            26.0
```
{: .output }

The second GPU made no difference to the time per step, so the same training cost twice the GPU-hours. Marlowe's
H100s are linked by NVLink within a node, so the multi-GPU part of the day happens there, in
[Checkpoints 3 to 5]({{ '/checkpoint-3/' | relative_url }}). On the Yens, use one GPU.

---

## Step 1: Larger micro-batches

Each step trains on 16 records. In Checkpoint 1 the GPU took them one at a time (`BATCH=1`) and added up the results
16 times (`ACCUM=16`). Taking 4 at a time does the same training in 4 passes instead of 16. Whether that is faster
depends on the GPU and the data, so measure it:

```bash
BATCH=4 RUN=cp2-batch4 sbatch slurm/yens/01_train_1gpu.slurm
```
{: .yens }

If the H200s are busy, add `-C GPU_MODEL:A40` as in Checkpoint 1, and compare with an A40 run of Checkpoint 1.

`slurm/train_args.sh` sets `ACCUM` to keep 16 records per step, so this run is comparable with Checkpoint 1. It writes
to `$WORK/runs/cp2-batch4`.

## Step 2: Compare

```bash
$PY scripts/step_times.py $WORK/runs/cp1-1gpu $WORK/runs/cp2-batch4
```
{: .yens }

- **s/step**: median seconds per optimizer step (the first three steps are left out as warm-up).
- **peak GPU GB**: the most GPU memory the job used. Larger micro-batches use more.
- **epoch hours**: how long one pass over all 52,757 training records would take.
- **epoch GPU-hours**: epoch hours times the number of GPUs, which is what an allocation is charged.

Did the larger micro-batch make each step faster? DARC's test on an A40 says it may not:

```
run              GPUs steps  s/step peak GPU GB epoch hours epoch GPU-hours
cp1-1gpu            1    30   14.02        19.4        12.8            12.8
cp2-batch4          1    30   49.92        21.3        45.7            45.7
```
{: .output }

`BATCH=4` was 3.6 times slower per step. Filings vary in length, and every micro-batch is padded to its longest
filing, so a batch of 4 does much more work than 4 batches of 1. Use the faster setting for your estimate, whichever
it is on your GPU. On a 141 GB H200 you can also try `BATCH=2`.

## Step 3: Estimate a full run

Suppose a real study trains for 3 epochs. With your faster setting:

```
GPU-hours = 3 epochs x epoch GPU-hours, plus about 25% for test runs and reruns
```

Write down the estimate and how long it would take on one H200. You will set it next to the Marlowe numbers in
Checkpoints 3 to 5.

{: .checkpoint }
> **Checkpoint 2.** Post your two rows of the table and your GPU-hour estimate in Slack, then put up a 🟩 green
> sticky. 🟥 if you are stuck.

---

## If you have time

- Compare the GPU logs of the two runs (`logs/gpu-<jobid>.csv`). Is utilization higher with larger micro-batches?
- With W&B (`WANDB=1`), put both runs on one chart of `seconds_per_step`.
