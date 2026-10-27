---
layout: default
title: "2. Scaling on the Yens"
nav_order: 6
permalink: /checkpoint-2/
---

# Checkpoint 2: Scaling on the Yens

**Goal:** run the same training on two H200s, build a scaling table, and estimate the GPU-hours a full run would need.

---

## Step 1: Two GPUs

```bash
sbatch slurm/yens/02_train_2gpu.slurm
```
{: .yens }

Compare it with the one-GPU script:

```bash
diff slurm/yens/01_train_1gpu.slurm slurm/yens/02_train_2gpu.slurm
```
{: .yens }

Three things change: `-G 2` asks for two GPUs, `GPUS=2` halves the gradient accumulation so each step still sees
16 records, and `torchrun --nproc_per_node 2` starts one training process per GPU. Kev notices it is running under
`torchrun` and shards the model and optimizer state across the GPUs with FSDP. The log now shows `world=2`.

{: .note }
> Both scripts take the same 100 steps of 16 records, so they do the same training. Any difference in time per step is
> the effect of the second GPU.

## Step 2: The scaling table

When both runs have finished:

```bash
$PY scripts/step_times.py $WORK/runs/cp1-1gpu $WORK/runs/cp2-2gpu
```
{: .yens }

Here is what DARC's 30-step test runs printed on A40s (the H200s were busy that day):

```
run              GPUs steps  s/step peak GPU GB epoch hours epoch GPU-hours
cp1-1gpu            1    30   14.02        19.4        12.8            12.8
cp2-2gpu            2    30   14.19        38.1        13.0            26.0
```
{: .output }

Yours will differ on H200s; the shape of the table is what matters.

- **s/step**: median seconds per optimizer step (the first three steps are left out as warm-up).
- **epoch hours**: how long one pass over all 52,757 training records would take at this scale.
- **epoch GPU-hours**: epoch hours times the number of GPUs, which is what an allocation is charged.

**Speedup** is the one-GPU time per step divided by the two-GPU time. With perfect scaling it would be 2. It is less,
because the two GPUs exchange their results at every step.

On the A40s the speedup was about 1: the second GPU made no difference to the time per step, so the 2-GPU run cost
twice the GPU-hours for the same training. Two things changed between the runs, and both show in the table:

- **Peak GPU memory doubled** (19 GB to 38 GB per GPU). On one GPU, Kev keeps the full-precision weights and the
  optimizer's state in the node's memory; with FSDP that state moves onto the GPUs.
- **Each GPU waited on the other.** Each step is 8 micro-batches of one record per GPU, and before every one FSDP
  gathers the model's weights from both GPUs. The A40s talk over the PCIe bus, so that traffic takes about as long
  as the computing it saves.

More GPUs pay off when each one has more work between exchanges (larger micro-batches, longer documents, a bigger
model) and when the GPUs have fast links between them, as Marlowe's H100s do. Checkpoints 3 and 4 test that.

## Step 3: Estimate a full run

Suppose a real study trains for 3 epochs. From your table:

```
GPU-hours = 3 epochs x epoch GPU-hours, plus about 25% for test runs and reruns
```

Write down your estimate for one GPU and for two, and which you would ask for. This is the number a Marlowe
application asks for.

{: .checkpoint }
> **Checkpoint 2.** Post your scaling table, speedup and GPU-hour estimate in Slack, then put up a 🟩 green sticky.
> 🟥 if you are stuck.

---

## If you have time

- Look at both GPU logs (`logs/gpu-<jobid>.csv`). Is utilization higher with one GPU or two? Why might that be?
- Give each GPU more work per exchange: `BATCH=4 ACCUM=2 sbatch slurm/yens/02_train_2gpu.slurm` still takes 16
  records per step, in 2 micro-batches of 4. Does the time per step fall? Watch peak GPU memory.
- With W&B (`WANDB=1`), put both runs on one chart of `seconds_per_step`.
