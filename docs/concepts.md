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

We sent Jev every Item 5.02 filing since 2004, about 296,000 of them, with three questions: what happens to the
CEO, why, and whether the change was announced in advance. Labeling them all took about 20 minutes and cost about
$14.38: about 342 million input tokens, at TypeSafe's $42 per billion. Those answers are this hackathon's labels. Jev
is the reference we measure against, not ground truth: a filing Jev gets wrong stays wrong in the labels.

### Why a decision model, and not a chat model?

You could paste each filing into a chat model such as ChatGPT or Claude and ask the same three questions. For
labeling data at scale, a decision model like Jev has five advantages:

- **Every answer is one of your options.** A chat model writes text, which you then have to read and sort, and it can
  answer outside your options or not at all. Jev's answers go straight into a table, one column per question.
- **A probability for every option, not one answer.** You see how sure the model is, so you can find the unsure
  filings and check those by hand. The unsure labels are where the mistakes are: when we labeled every filing with
  Kev-4B, the filings where it disagreed with Jev were mostly ones it was only 20 to 30% sure of.
- **The probabilities are what a small model learns from.** Kev trains on Jev's whole spread of probabilities, not
  only its top choice, so it also learns which filings are close calls. A chat model's one answer would teach it only
  the answer.
- **It is cheap and fast at scale.** All 296,477 filings cost $14.38 and took about 20 minutes. Output is free; you
  pay only for the text you send.
- **Kev answers in the same format.** A Kev server takes the same requests and returns the same answers, so a Kev you
  fine-tune can replace Jev without changing any code.

A chat model is the better tool when the question is open-ended, when you need text pulled out of the document (a
name, a date, a dollar amount), or when you want an explanation rather than a choice. The Intermediate track's
[I1]({{ '/intermediate/i1/' | relative_url }}#where-the-labels-come-from-jev-and-system-one) has the full version,
with an example request, how Jev's confidence is measured, and TypeSafe's documentation for each point.

## Kev: open models you run yourself

**Kev** is an open family of models built to answer the same kind of questions as Jev, through the same request
format. The code (a trainer and a server) and the weights are public under Apache 2.0, so a Kev model runs on any GPU
you have access to. Kev comes in four sizes:

| Model | Built on | Weights |
|---|---|---|
| Kev-0.8B | Qwen3.5-0.8B | 1.8 GB |
| **Kev-4B** | Qwen3.5-4B | 9.5 GB |
| Kev-9B | Qwen3.5-9B | 19.5 GB |
| Kev-27B | Qwen3.8-27B | 51 GB |

The tracks use Kev models as reference points: their scores before any training are the bar to beat. Each track's
pages say which model it scores and which it fine-tunes.

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
all of the model's weights, 4 billion for a 4B model. It needs more GPU memory than
training a small add-on (an adapter) but it can be split across GPUs, which the Marlowe tasks do.

## Model checkpoints and resume points

A **model checkpoint** is a saved copy of a model's weights on disk, for example `$WORK/runs/<run>/` once a
training job has finished (`config.json`, `model-*.safetensors`, `head.pt`). You serve it, score it, or start further
training from it. Training writes one at the end.

A **resume point** is a snapshot of a training job partway through (the weights, the optimizer state, and the position
in the data), so a job that is stopped or preempted can carry on from there instead of starting over. Labeling jobs
resume more simply: a rerun skips filings already answered.

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
happens there.

## GPU-hours

A **GPU-hour** is one GPU for one hour. Eight GPUs for 30 minutes is 4 GPU-hours. Marlowe allocations and
applications are counted in GPU-hours, so a scale that finishes sooner but uses many more GPUs can cost more.
