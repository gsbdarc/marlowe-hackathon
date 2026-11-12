---
layout: default
title: "Key Ideas"
nav_order: 2
parent: "Start Here"
permalink: /concepts/
---

# Key Ideas

What Jev and Kev are, how fine-tuning works, and what changes when a job runs on more GPUs. The task pages link
here when they rely on one of these.

---

## Jev: the teacher

**Jev** is a hosted model from TypeSafe that makes decisions about documents. You send it a document (the **state**)
and a set of questions with fixed answer options, and it returns, for each question, a probability for every option.
It does not write free text, so its answers can go straight into a table.

Jev's answers about every Item 5.02 filing are this hackathon's labels ([The Project and the
Data]({{ '/task/' | relative_url }}) has the questions and the numbers). Jev is the reference we measure against, not
ground truth: a filing Jev gets wrong stays wrong in the labels.

## Kev: open models you run yourself

**Kev** is an open family of models built to answer the same kind of questions as Jev, through the same request
format. The code (a trainer and a server) and the weights are public under Apache 2.0, so a Kev model runs on any GPU
you have access to. The tracks use Kev models as reference points: their scores before any training are the bar to
beat. [The Project and the Data]({{ '/task/' | relative_url }}#the-kev-models) lists the four sizes and how each scores.

A model you run yourself has a fixed version for replication, keeps confidential documents on Stanford hardware, and
costs only GPU time to rerun on new filings or new questions.

## Distillation

**Distillation** trains a small model to give a large model's answers. Here the training target for each filing is
Jev's whole probability distribution, not just its top answer. When Jev put 60% on "becomes executive chair" and 40% on
"stays as a director only", the student learns that the filing is ambiguous, which carries more information than a single
label.

The **loss** in the training log is the cross-entropy between the student's probabilities and Jev's: it is lowest when
the student puts the same probability on each option as Jev did. It should go down as training goes on.

## Fine-tuning, and what "full" means

**Fine-tuning** continues training a model that is already trained, here on CEO turnover. A **full fine-tune** updates
all of the model's weights, 4 billion for a 4B model, and can be split across GPUs, which the Marlowe tasks do. A
**LoRA** trains a small adapter on top of the model and leaves its weights frozen, so it needs much less GPU memory.

## Model checkpoints and resume points

A **model checkpoint** is a saved copy of a model's weights on disk, for example `$WORK/runs/<run>/` once a
training job has finished (`config.json`, `model-*.safetensors`, `head.pt`). You serve it, score it, or start further
training from it. Training writes one at the end.

A **resume point** is a snapshot of a training job partway through (the weights, the optimizer state, and the position
in the data), so a job that is stopped or preempted can carry on from there instead of starting over. Labeling jobs
need no resume point: a rerun skips filings already answered.

## Steps, batches and epochs

- A **record** is one filing with its questions and Jev's answers.
- An **optimizer step** updates the weights once, after the model has seen a group of records. Every job today takes
  16 records per step, whatever the number of GPUs.
- An **epoch** is one pass over the whole training file: 52,757 records (after dropping the longest), so about 3,300 steps.

Today's training jobs are short, about 100 steps or 10 minutes, a few percent of an epoch. That is enough to measure
speed and see the loss fall, but not to finish training.

## Scaling across GPUs

On one GPU, the whole model and its training state must fit on that GPU and in the node's memory. With more GPUs,
`torchrun` starts one copy of the training program per GPU and **FSDP** (fully sharded data parallel) splits the
weights and optimizer state across them. For a LoRA, each GPU holds a whole copy of the model instead (data parallel).
Either way the GPUs share each step's 16 records, so each step should take less time.
N GPUs are less than N times faster, because the GPUs exchange results at every step. That exchange is slower across
nodes than within one, and slower again without a direct link between the GPUs. The Yen GPUs have no such link (they
talk over the PCIe bus), so on the Yens you train on one GPU. Marlowe's H100s are linked by NVLink, so the scaling
happens there.

## GPU-hours

A **GPU-hour** is one GPU for one hour. Eight GPUs for 30 minutes is 4 GPU-hours. Marlowe allocations and
applications are counted in GPU-hours, so a scale that finishes sooner but uses many more GPUs can cost more.
