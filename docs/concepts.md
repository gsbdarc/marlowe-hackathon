---
layout: default
title: "Key Ideas"
nav_order: 3
permalink: /concepts/
---

# Key Ideas

The terms used on the other pages, and what each means here.

---

## Jev: the teacher

**Jev** is a hosted model from TypeSafe that makes decisions about documents. You send it a document (the **state**)
and a set of questions with fixed answer options, and it returns, for each question, a probability for every option.
It does not write free text, so its answers can go straight into a table.

DARC sent Jev every Item 5.02 filing since 2004, about 296,000 of them, with three questions: what happens to the
CEO, why, and whether the change was announced in advance. Labeling them all took about 20 minutes and cost about
$19. Those answers are this hackathon's labels. Jev is the reference we measure against, not ground truth: a filing
Jev gets wrong stays wrong in the labels.

## Kev: the student

**Kev** is an open family of models built to answer the same kind of questions as Jev, through the same request
format. The code (a trainer and a server) and the weights are public under Apache 2.0, so a Kev model runs on any GPU
you have access to. Kev comes in four sizes:

| Model | Built on | Weights |
|---|---|---|
| Kev-0.8B | Qwen3.5-0.8B | 1.8 GB |
| **Kev-4B** | Qwen3.5-4B | 9.5 GB |
| Kev-9B | Qwen3.5-9B | 19.5 GB |
| Kev-27B | Qwen3.5-27B | 51 GB |

We use **Kev-4B**. It is small enough to fine-tune quickly and starts out well short of Jev on CEO changes, so the
effect of training is easy to see.

A model you run yourself has a fixed version for replication, keeps confidential documents on Stanford hardware, and
costs only GPU time to rerun on new filings or new questions.

## Distillation

**Distillation** trains a small model to give a large model's answers. Here the training target for each filing is
Jev's whole probability distribution, not just its top answer. When Jev put 60% on "becomes executive chair" and 40% on
"stays as a director only", Kev learns that the filing is ambiguous, which carries more information than a single
label.

The **loss** in the training log is the cross-entropy between Kev's probabilities and Jev's: it is lowest when Kev
puts the same probability on each option as Jev did. It should go down as training goes on.

## Fine-tuning, and what "full" means

**Fine-tuning** continues training a model that is already trained. Kev-4B was trained on general decision tasks; we
fine-tune it on CEO turnover. A **full fine-tune** updates all 4 billion weights. It needs more GPU memory than
training a small add-on (an adapter) but it can be split across GPUs, which the Marlowe checkpoints do.

## Two kinds of checkpoint

**Checkpoint** has two meanings on this site.

- A **hackathon checkpoint** is a stage of the day (Checkpoints 1 to 5). You finish it by running a job and posting
  the result.
- A **model checkpoint** is a saved copy of a model's weights on disk, for example `$WORK/runs/cp1-1gpu/` once the job has finished (`config.json`, `model-*.safetensors`, `head.pt`).
  You serve it, score it, or start further training from it. Training writes one at the end.

A **resume point** is related: a snapshot of a training job partway through (the weights, the optimizer state, and
the position in the data), so a job that is stopped or preempted can carry on from there instead of starting over.
[Checkpoint 5]({{ '/checkpoint-5/' | relative_url }}) uses them.

## Steps, batches and epochs

- A **record** is one filing with its questions and Jev's answers.
- An **optimizer step** updates the weights once, after the model has seen a group of records. Every job today takes
  16 records per step, whatever the number of GPUs.
- An **epoch** is one pass over the whole training file: 52,757 records (after dropping the longest), so about 3,300 steps.

Today's jobs run 100 steps (about 3% of an epoch). That is enough to measure speed and see the loss fall, but not to
finish training.

## Scaling across GPUs

On one GPU, the whole model and its training state must fit on that GPU and in the node's memory. With more GPUs,
`torchrun` starts one copy of the training program per GPU and **FSDP** (fully sharded data parallel) splits the
weights and optimizer state across them. The GPUs share each step's 16 records, so each step should take less time.
N GPUs are less than N times faster, because the GPUs exchange results at every step. That exchange is slower across
nodes than within one, and slower again without a direct link between the GPUs. The Yen GPUs have no such link (they
talk over the PCIe bus), so on the Yens you train on one GPU. Marlowe's H100s are linked by NVLink, so the scaling
happens there, in [Checkpoints 3 to 5]({{ '/checkpoint-3/' | relative_url }}).

## GPU-hours

A **GPU-hour** is one GPU for one hour. Eight GPUs for 30 minutes is 4 GPU-hours. Marlowe allocations and
applications are counted in GPU-hours, so a scale that finishes sooner but uses many more GPUs can cost more.
