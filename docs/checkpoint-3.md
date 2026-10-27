---
layout: default
title: "3. First Marlowe Job"
nav_order: 7
permalink: /checkpoint-3/
---

# Checkpoint 3: First Marlowe Job

**Goal:** run the Checkpoint 1 job on one H100 on Marlowe and compare it with the Yens.

---

## Step 1: Log in and get the code

```bash
ssh <sunet>@login.marlowe.stanford.edu
```
{: .laptop }

If you did not clone the repository during setup:

```bash
mkdir -p /scratch/m000106/gsb_hackathon/$USER && cd /scratch/m000106/gsb_hackathon/$USER
git clone https://github.com/gsbdarc/marlowe-hackathon.git
cd marlowe-hackathon
source env/marlowe.sh
```
{: .marlowe }

{: .warning }
> Work only under `/scratch/m000106/gsb_hackathon/`. Your Marlowe home directory holds 32 GB, and a model download
> there fills it.

## Step 2: Data and weights on Marlowe

The training files and the merged Kev-4B have to be on Marlowe too. Either copy your `$WORK` from the Yens with
Globus (from `/scratch/users/<sunet>/ceo-turnover` on the Yens to `/scratch/m000106/gsb_hackathon/<sunet>/ceo-turnover`
on Marlowe), or rebuild them there in one short job:

```bash
mkdir -p logs
sbatch slurm/marlowe/00_prepare.slurm
```
{: .marlowe }

## Step 3: What is different on Marlowe

Open `slurm/marlowe/03_train_1gpu.slurm` and compare it with the Yens version:

| | Yens | Marlowe |
|---|---|---|
| Account and partition | `-p gpu` | `--account=marlowe-m000106 --partition=preempt` |
| GPUs | `-G 1 -C GPU_MODEL:H200` | `--gpus-per-node=1` (every Marlowe GPU is an H100) |
| Before the job | | `module load slurm mps` |
| Paths | `env/yens.sh` | `env/marlowe.sh` |

The training itself, `slurm/train_args.sh`, is the same file.

{: .note }
> `preempt` is the partition for basic Marlowe access. Jobs there can run up to 4 hours, and a job can be stopped to
> make room for others. A stopped job goes back in the queue and starts again. [Checkpoint 5]({{ '/checkpoint-5/' | relative_url }})
> shows how to make a long job carry on from where it stopped.

## Step 4: Run it

```bash
sbatch slurm/marlowe/03_train_1gpu.slurm
squeue --me
tail -f logs/ceo-cp3-<jobid>.out
```
{: .marlowe }

When it ends with `saved`, add it to your table:

```bash
$PY scripts/step_times.py $WORK/runs/cp3-1gpu
```
{: .marlowe }

How does one H100 compare with one H200 per step? The H200 has more memory (141 GB against 80 GB) and faster memory;
the H100s on Marlowe sit eight to a node with fast links between them, which is what the next checkpoint uses.

{: .checkpoint }
> **Checkpoint 3 (10 GPU-hours).** Post your Marlowe job ID and seconds per step in Slack, then put up a 🟩 green
> sticky. 🟥 if you are stuck.
