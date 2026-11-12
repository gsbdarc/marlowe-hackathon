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

---

## Objectives

The day works if, by the end of it:

- **Everyone runs a GPU job on Marlowe.** Every track reaches Marlowe, whatever your starting point.
- **Each track table leaves with a working result:** a model you trained or ran, scored against Jev's labels and
  posted in [{{ site.slack_channel }}]({{ site.slack_url }}).
- **Everyone knows where to get help afterwards:** [RCpedia](https://rcpedia.stanford.edu) for the Yens,
  [Marlowe's documentation](https://marlowe-research.stanford.edu/documentation/) for Marlowe, and the Slack channel.
- **Everyone knows how their PI's group signs up for Marlowe,** with the GPU-hour numbers a project application asks
  for ([Applying for Marlowe]({{ '/take-home/' | relative_url }}#applying-for-marlowe)).

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

Pick one track. Each task ends in a check-in: post your result in [{{ site.slack_channel }}]({{ site.slack_url }}) on Slack and put
up a 🟩 green sticky, or a 🟥 red one if you are stuck.

| Task | [Beginner]({{ '/beginner/' | relative_url }}) | [Intermediate]({{ '/intermediate/' | relative_url }}) | [Advanced]({{ '/advanced/' | relative_url }}) |
|---|---|---|---|
| 1 | [Your first GPU job]({{ '/beginner/b1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/intermediate/i1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/advanced/a1/' | relative_url }}) (Yens, 1 H200) |
| 2 | [Fine-tune the model]({{ '/beginner/b2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one GPU]({{ '/intermediate/i2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one node]({{ '/advanced/a2/' | relative_url }}) (Marlowe, 1 H100, then 8 H100s) |
| 3 | [Run it on Marlowe]({{ '/beginner/b3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on one Marlowe GPU]({{ '/intermediate/i3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) (Marlowe, 16 H100s) |
| 4 | [Many GPUs at once]({{ '/beginner/b4/' | relative_url }}) (Marlowe, 1 to 8 H100s) | [Fine-tune on a full node]({{ '/intermediate/i4/' | relative_url }}) (Marlowe, 1 node) | [Inference at scale]({{ '/advanced/a4/' | relative_url }}) (Marlowe, 8 H100s) |
| 5 | [From labels to a finding]({{ '/beginner/b5/' | relative_url }}) (Marlowe, no GPU) | [Inference at scale]({{ '/intermediate/i5/' | relative_url }}) (Marlowe, 1 node) | [Distill a student]({{ '/advanced/a5/' | relative_url }}) (Marlowe, 1 H100) |

### The Advanced track at a glance

Each card links to its page and to the main ideas the page teaches.

{% include track_map.html track="advanced" %}

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
| 2:40 | **Hands-on 4:** tasks 4 and 5 |
| 4:00 | Awards, templates, next steps for applying |

---

## Take it home

Every script here is a template you can adapt: swap in your own documents, questions and labels. [Take It
Home]({{ '/take-home/' | relative_url }}) shows what to change.

{% if site.show_survey %}
---

## Post-class survey

At the end of the day, tell us how it went: [darc.stanford.edu/hackathon-survey](https://darc.stanford.edu/hackathon-survey).
{% endif %}
