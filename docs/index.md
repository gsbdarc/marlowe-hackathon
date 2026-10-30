---
layout: default
title: "Marlowe Hackathon 2026"
nav_order: 0
permalink: /
---

# Marlowe Hackathon 2026

A one-day, hands-on hackathon for Stanford GSB researchers, run by DARC and the HAI Marlowe team. You pick one of three
tracks: each starts on the Yens and then fine-tunes an open-weight model across GPUs and nodes on Marlowe, Stanford's
H100 cluster. You leave with a working Marlowe job, Slurm templates for your own research, and the measurements a
Marlowe project application asks for.

**Friday, November 13, 2026 · 10:00 am to 5:00 pm · GSB, in person**

---

## The project: CEO turnover in SEC filings

When a public company's CEO leaves, the company files an 8-K under **Item 5.02**. A large hosted model, **Jev**, has
read every Item 5.02 filing since 2004, about 300,000 of them, and answered three questions about each: what happens
to the CEO, why, and whether the change was announced in advance.

You will work with open models from the **Kev** family that answer the same questions. Training a Kev model on Jev's
labels, including how confident Jev was, is distillation: a model you run yourself can then label filings at scale on
a GPU you control.

Before training, Kev-4B agrees with Jev on 58% of CEO changes. During the day you train, label filings at scale, and
measure what each costs on the Yens and on Marlowe. [The task and the data]({{ '/task/' | relative_url }}) has the details.

---

## Tracks

Pick one track. Each task ends in a check-in: post your result in the Slack channel and put
up a 🟩 green sticky, or a 🟥 red one if you are stuck.

| Task | [Beginner]({{ '/beginner/' | relative_url }}) | [Intermediate]({{ '/intermediate/' | relative_url }}) | [Advanced]({{ '/advanced/' | relative_url }}) |
|---|---|---|---|
| 1 | [Score Kev-4B before training]({{ '/beginner/b1/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune and profile Kev-4B]({{ '/intermediate/i1/' | relative_url }}) (Yens, 1 GPU) | [Score Kev-27B before training]({{ '/advanced/a1/' | relative_url }}) (Yens, 1 H200) |
| 2 | [Fine-tune Kev-4B]({{ '/beginner/b2/' | relative_url }}) (Yens, 1 GPU) | [Move your data with Globus]({{ '/intermediate/i2/' | relative_url }}) (Yens to Marlowe) | [Fine-tune Qwen 27B]({{ '/advanced/a2/' | relative_url }}) (Marlowe, 1 H100, then 8 H100s) |
| 3 | [Label filings on one Marlowe GPU]({{ '/beginner/b3/' | relative_url }}) (Marlowe, 1 H100) | [Label the test split on a node]({{ '/intermediate/i3/' | relative_url }}) (Marlowe, 1 node) | [Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) (Marlowe, 16 H100s) |
| 4 | [Label on a full node]({{ '/beginner/b4/' | relative_url }}) (Marlowe, 1 node) | [Label the corpus on two nodes]({{ '/intermediate/i4/' | relative_url }}) (Marlowe, 2 nodes) | [Inference at scale with Qwen 235B]({{ '/advanced/a4/' | relative_url }}) (Marlowe, 8 H100s) |
| 5 | | | [Distill a student]({{ '/advanced/a5/' | relative_url }}) (Marlowe, 1 H100) |

---

## Schedule

| Time | Session |
|---|---|
| 10:00 | Welcome: goals, the three tracks, the Slack channel, a quick login check on the Yens and Marlowe |
| 10:15 | Talk: an introduction to Marlowe (Marlowe team) |
| 10:50 | Talk: a social science researcher's Marlowe story |
| 11:30 | Break; open a terminal on the Yens |
| 11:40 | **Hands-on 1:** task 1 of your track |
| 12:30 | Lunch |
| 1:15 | **Hands-on 2:** task 2 |
| 2:00 | **Hands-on 3:** task 3 |
| 2:30 | Break |
| 2:40 | **Hands-on 4:** task 4 |
| 4:00 | Awards, templates, next steps for applying |

---

## Take it home

Every script here is a template you can adapt: swap in your own documents, questions and labels. [Take It
Home]({{ '/take-home/' | relative_url }}) shows what to change.
