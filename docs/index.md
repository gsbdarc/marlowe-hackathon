---
layout: default
title: "Marlowe Hackathon 2026"
nav_order: 0
permalink: /
---

# Marlowe Hackathon 2026

A one-day, hands-on hackathon for Stanford GSB researchers, run by DARC and the HAI Marlowe team. You will fine-tune
an open-weight model on one GPU on the Yens, then scale the same job across GPUs and nodes on Marlowe, Stanford's
H100 cluster. You leave with a working Marlowe job, Slurm templates for your own research, and the measurements a
Marlowe project application asks for.

**Friday, November 13, 2026 · 10:00 am to 5:00 pm · GSB, in person**

---

## The project: CEO turnover in SEC filings

When a public company's CEO leaves, the company files an 8-K under **Item 5.02**. A large hosted model, **Jev**, has
read every Item 5.02 filing since 2004, about 300,000 of them, and answered three questions about each: what happens
to the CEO, why, and whether the change was announced in advance.

You will teach a small open model, **Kev-4B**, to give Jev's answers. This is distillation: the large model's labels,
including how confident it was, become the small model's training targets. A small model you run yourself can then
label filings at scale on a GPU you control.

Kev-4B starts out matching Jev on about half of CEO changes. The day is about closing that gap and measuring what it
costs at each scale. [The task and the data]({{ '/task/' | relative_url }}) has the details.

---

## Checkpoints

Each stage ends in a checkpoint. Post your job ID and a screenshot of the log in the Slack channel and a helper will
confirm it. Checkpoints on Marlowe earn GPU-hours.

| | Where | What counts | Award |
|---|---|---|---|
| [1. One GPU]({{ '/checkpoint-1/' | relative_url }}) | Yens, 1 H200 | The training job finishes; you have its time per step and GPU memory and utilization | Needed to continue |
| [2. Plan the GPU-hours]({{ '/checkpoint-2/' | relative_url }}) | Yens, 1 H200 | A second run with larger micro-batches, and a GPU-hour estimate for a full run | Needed to continue |
| [3. First Marlowe job]({{ '/checkpoint-3/' | relative_url }}) | Marlowe, 1 H100 | The job finishes on Marlowe | 10 GPU-hours |
| [4. One full node]({{ '/checkpoint-4/' | relative_url }}) | Marlowe, 8 H100s | The job runs on all 8 GPUs of one node | 50 GPU-hours |
| [5. Two nodes and resume]({{ '/checkpoint-5/' | relative_url }}) | Marlowe, 16 H100s | The job runs across two nodes and resumes from a saved point | 500 GPU-hours |

Award amounts are proposed and still to be confirmed with the Marlowe team.

After training, [label filings with your model]({{ '/label/' | relative_url }}) on a Yen H200 and score it against Jev.

---

## Schedule

| Time | Session |
|---|---|
| 10:00 | Welcome: goals, checkpoints, the Slack channel, a quick login check on the Yens and Marlowe |
| 10:15 | Talk: an introduction to Marlowe (Marlowe team) |
| 10:50 | Talk: a social science researcher's Marlowe story |
| 11:30 | Break; open a terminal on the Yens |
| 11:40 | **Hands-on 1:** [train on one H200 on the Yens]({{ '/checkpoint-1/' | relative_url }}) |
| 12:30 | Lunch |
| 1:15 | **Hands-on 2:** [tune one GPU and estimate GPU-hours]({{ '/checkpoint-2/' | relative_url }}) |
| 2:00 | **Hands-on 3:** [first job on Marlowe]({{ '/checkpoint-3/' | relative_url }}) |
| 2:30 | Break |
| 2:40 | **Hands-on 4:** [8 GPUs on one node]({{ '/checkpoint-4/' | relative_url }}), then [two nodes]({{ '/checkpoint-5/' | relative_url }}) |
| 4:00 | Awards, templates, next steps for applying |

---

## Before you arrive

Work through [Before You Arrive]({{ '/setup/' | relative_url }}): log in to the Yens and Marlowe, clone this
repository on both, and set up Kev. It takes about 20 minutes.

## Take it home

Every script here is a template you can adapt: swap in your own documents, questions and labels. [Take It
Home]({{ '/take-home/' | relative_url }}) shows what to change.
