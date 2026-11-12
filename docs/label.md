---
layout: default
title: "Use Your Trained Model"
parent: "Reference"
nav_order: 4
permalink: /label/
---

# Use Your Trained Model

A model you train is a folder under `$WORK/runs/`, and the training job's log names it. This page serves that model,
scores it against Jev on the 1,000 test filings, and labels more filings with it. The same jobs also serve a Kev
model as released, by its Hugging Face name.

---

## Step 1: Score it on the test filings

`serve_and_label.slurm` starts a Kev server on one GPU, sends it the 1,000 test filings, and scores its answers
against Jev's. The first argument is the model, the second a name for its answers, which it saves as
`$WORK/results/<name>.jsonl`.

On Marlowe, for a model you trained there:

```bash
sbatch slurm/marlowe/serve_and_label.slurm $WORK/runs/<run> my-model
```
{: .marlowe }

On the Yens:

```bash
sbatch -C GPU_MODEL:H200 slurm/yens/serve_and_label.slurm $WORK/runs/<run> my-model
```
{: .yens }

A model you trained on Marlowe has to be copied to the Yens first, with [Globus]({{ '/globus/' | relative_url }}).
A 27B model needs the Marlowe job, which asks for enough memory to load it.

## Step 2: Compare it with where you started

With no arguments, the same job scores Kev-4B as released and saves `$WORK/results/kev-4b-zeroshot.jsonl`. Put the
two side by side:

```bash
$PY scripts/score.py $WORK/results/kev-4b-zeroshot.jsonl $WORK/results/my-model.jsonl
```

`score.py` prints one row per model. Did agreement on CEO changes go up? Did "leaves the company entirely" improve?
The runs in the tracks are short, about 3% of an epoch for 100 steps, so expect a change, not the whole gap closed.

{: .note }
> The test filings are from 2022 to 2026 and the training filings from 2004 to 2018, so a gain here is a gain on
> filings the model has never seen, from years it was not trained on.

## Step 3: Label more filings

A third argument labels any other file: one in the format of `test1000.jsonl`, or Jev's whole release,
`$DATA/item502_v1.parquet`. Only the test filings are scored.

```bash
sbatch slurm/marlowe/serve_and_label.slurm $WORK/runs/<run> my-model-all $DATA/item502_v1.parquet
```
{: .marlowe }

One GPU labels about 6 filings per second, so all 296,477 take about 14 hours. The job stops at its time limit; submit
the same command again and it carries on, because `label.py` skips filings it has already answered. Or ask for more
time, for example `sbatch --time=16:00:00 ...`.

To label them in under an hour, use all 8 GPUs of a Marlowe node, one Kev server per GPU, as in
[I5]({{ '/intermediate/i5/' | relative_url }}):

```bash
RUN=$WORK/runs/<run> sbatch slurm/marlowe/intermediate/label_8gpu.slurm
```
{: .marlowe }

To label your own documents rather than filings, see [Take It Home]({{ '/take-home/' | relative_url }}).

{: .warning }
> On the Yens, run one `serve_and_label` job at a time. Every job loads the model onto its own GPU, and the Yens' H200s
> are shared by everyone in the room.
