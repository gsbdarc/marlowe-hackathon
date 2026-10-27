---
layout: default
title: "Take It Home"
nav_order: 11
permalink: /take-home/
---

# Take It Home

Everything in this repository is a template. The CEO-turnover task is one example of a common research pattern: a
large model answers questions about many documents, and you want a small model you run yourself to answer them the
same way, at scale, on your own GPU. To reuse it for your own project, change three things.

## 1. Your documents

`scripts/make_kev_data.py` reads Jev's parquet and builds a **state** for each document with `questions.state()`: the
text the model reads. Point it at your own table and build the state from your own columns. Keep states short: Kev-4B
was trained on states of up to 7,552 tokens and is validated to 8,192.

## 2. Your questions

`scripts/questions.py` defines the questions in the System One request shape that Jev and Kev share:

- `choice`: pick one of several options. The option text is the label, so write each option as a full description.
- `noul`: yes or no.
- `score`: an ordered scale.

Change the instructions and options to your own. The wording is the task: version it, and do not edit it after you
have labels.

## 3. Your labels

Each training record needs a `label` on every question. You can also give a `target`, a probability for each option,
when your labels come from a model that reports them (as Jev's do) or from several human coders who disagree. Kev
trains on the target when there is one.

Labels can come from Jev or another teacher model, from hand coding, or from an existing dataset. Keep a test set the
model never trains on, chosen before you look at results, and split it so the same company or document never appears
on both sides.

## The Slurm templates

| Template | Use it for |
|---|---|
| `slurm/yens/serve_and_label.slurm` | serving any Kev checkpoint on one Yen GPU and labeling a file of documents |
| `slurm/yens/01_train_1gpu.slurm` | a fine-tune on one GPU |
| `slurm/yens/02_train_2gpu.slurm` | the same job sharded across the GPUs of one node with `torchrun` |
| `slurm/marlowe/04_train_8gpu.slurm` | one full Marlowe node |
| `slurm/marlowe/05_train_2node.slurm` | several nodes, with resume points for preemptible or time-limited jobs |

The training arguments live in one place, `slurm/train_args.sh`, so every scale runs the same job. Change the model,
learning rate or number of steps there.

## Applying for Marlowe

A Marlowe project application asks how many GPU-hours your project needs. The scaling table you build in
[Checkpoint 2]({{ '/checkpoint-2/' | relative_url }}) is that estimate: measure time per step at two or three scales
on a short run, multiply by the steps a full run needs, and add a margin for reruns.
