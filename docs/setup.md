---
layout: default
title: "Before You Arrive"
nav_order: 1
permalink: /setup/
---

# Before You Arrive

Do these steps before November 13, so the day goes to training rather than setup.

---

## Accounts

1. **Yens.** You need a Yens account with access to the GPU partition. Check that you can log in:

   ```bash
   ssh <sunet>@yen.stanford.edu
   ```
   {: .laptop }

2. **Marlowe.** The Marlowe team creates accounts from the SUNet IDs on the registration form. Log in once before
   the day:

   ```bash
   ssh <sunet>@login.marlowe.stanford.edu
   ```
   {: .laptop }

   Jobs run under the hackathon's project, account `marlowe-m000106`, on the `preempt` partition.

{: .warning }
> Never put code, environments or model weights in your Marlowe home directory: it holds 32 GB. Everything in this
> hackathon lives in the project scratch space, `/scratch/m000106/gsb_hackathon/`.

---

## Clone this repository

On the Yens, in your scratch space:

```bash
cd /scratch/users/$USER
git clone https://github.com/gsbdarc/marlowe-hackathon.git
cd marlowe-hackathon
```
{: .yens }

On Marlowe, in the hackathon's project space:

```bash
mkdir -p /scratch/m000106/gsb_hackathon/$USER && cd /scratch/m000106/gsb_hackathon/$USER
git clone https://github.com/gsbdarc/marlowe-hackathon.git
cd marlowe-hackathon
```
{: .marlowe }

Instead of cloning on Marlowe, you can copy your Yens clone over with Globus. Cloning keeps both copies in step with
`git pull`.

---

## Set up Kev

Kev is an open family of small models that answer the same kind of questions Jev does, through the same API. Its
code includes the trainer and the server you will use all day. `scripts/setup_kev.sh` installs Kev at the version
DARC tested, builds its Python environment and downloads the Kev-4B weights. Run it on a **login node** of each
cluster, so no GPU time is spent downloading.

```bash
source env/yens.sh
bash scripts/setup_kev.sh
```
{: .yens }

```bash
source env/marlowe.sh
bash scripts/setup_kev.sh
```
{: .marlowe }

It takes about 10 minutes and about 25 GB of scratch on each cluster, and it is safe to rerun.

`env/yens.sh` and `env/marlowe.sh` set every path the scripts use. Every job sources one of them:

| Variable | What it is | Yens | Marlowe |
|---|---|---|---|
| `DATA` | Jev's labeled filings (read only) | `/yen/projects/darc/marlowe_hackathon/ceo-turnover/data/jev` | `/scratch/m000106/gsb_hackathon/ceo-turnover/data/jev` |
| `WORK` | your training files, runs and results | `/scratch/users/$USER/ceo-turnover` | `/scratch/m000106/gsb_hackathon/$USER/ceo-turnover` |
| `KEV_HOME` | Kev's code and Python environment | `/scratch/users/$USER/kev` | `/scratch/m000106/gsb_hackathon/$USER/kev` |
| `HF_HOME` | model weights | `/scratch/users/$USER/hf` | `/scratch/m000106/gsb_hackathon/hf_cache` (shared) |

---

## Build the training data

On the Yens, build the training, validation and test files from Jev's labels (a CPU job, a few minutes):

```bash
mkdir -p logs
sbatch slurm/yens/00_data.slurm
```
{: .yens }

When it finishes, `logs/ceo-data-<jobid>.out` ends with:

```
.../ceo-turnover/data/train.jsonl: 54,426 records, 27,213 CEO changes
.../ceo-turnover/data/valid.jsonl: 2,000 records, 1,019 CEO changes
.../ceo-turnover/data/test1000.jsonl: 1,000 records, 700 CEO changes
```
{: .output }

Copy `$WORK/data/` to the same place on Marlowe with Globus, or run the same script there with `source env/marlowe.sh`.
[The task and the data]({{ '/task/' | relative_url }}) explains what is in each file.
