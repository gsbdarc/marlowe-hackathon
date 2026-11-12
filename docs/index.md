---
layout: default
title: "Marlowe Hackathon 2026"
nav_order: 0
permalink: /
---

# Marlowe Hackathon 2026

Welcome! This is a one-day, hands-on hackathon for Stanford GSB researchers, run by DARC and the HAI Marlowe team. You
start on the Yens and then fine-tune an open-weight model across GPUs and nodes on Marlowe, Stanford's H100 cluster.
You leave with a working Marlowe job, Slurm templates for your own research, and a way to measure what your own jobs
would need on Marlowe.

---

## Objectives

By the end of the day, everyone:

- **Runs GPU jobs on Marlowe.**
- **Scales a job past one GPU and measures what it buys:** the same job on one GPU and then on a full Marlowe node of
  8 H100s, comparing the time per step, the GPU memory and the GPU-hours at each scale, to see when more GPUs help
  and when they do not.
- **Fine-tunes a model and scores it** against the labels it learned from, and posts the result in
  [{{ site.slack_channel }}]({{ site.slack_url }}).
- **Watches a job while it runs:** its log, its GPUs' use and memory, and its loss in Weights & Biases
  ([Monitoring Training]({{ '/monitoring/' | relative_url }})).
- **Leaves with job files for their own research,** from one GPU to two nodes, and knows what to change in them
  ([Take It Home]({{ '/take-home/' | relative_url }})).
- **Knows how their PI's group applies for Marlowe,** and how to measure the GPU-hours and scaling a project
  application asks for ([Applying for Marlowe]({{ '/take-home/' | relative_url }}#applying-for-marlowe)).
- **Knows where to get help afterwards:** [RCpedia](https://rcpedia.stanford.edu) for the Yens,
  [Marlowe's documentation](https://marlowe-research.stanford.edu/documentation/) for Marlowe, and the Slack channel.

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

## Tracks

Pick one track and work through its tasks at your own pace.

| Task | [Beginner]({{ '/beginner/' | relative_url }}) | [Intermediate]({{ '/intermediate/' | relative_url }}) | [Advanced]({{ '/advanced/' | relative_url }}) |
|---|---|---|---|
| 1 | [Being written]({{ '/beginner/' | relative_url }}) | [Score before training]({{ '/intermediate/i1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/advanced/a1/' | relative_url }}) (Yens, 1 H200) |
| 2 | | [Fine-tune on one GPU]({{ '/intermediate/i2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one node]({{ '/advanced/a2/' | relative_url }}) (Marlowe, 1 H100, then 8 H100s) |
| 3 | | [Fine-tune on one Marlowe GPU]({{ '/intermediate/i3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) (Marlowe, 16 H100s) |
| 4 | | [Fine-tune on a full node]({{ '/intermediate/i4/' | relative_url }}) (Marlowe, 1 node) | [Inference at scale]({{ '/advanced/a4/' | relative_url }}) (Marlowe, 8 H100s) |
| 5 | | [Inference at scale]({{ '/intermediate/i5/' | relative_url }}) (Marlowe, 1 node) | [Distill a student]({{ '/advanced/a5/' | relative_url }}) (Marlowe, 1 H100) |

### The Advanced track at a glance

Each card links to its page and to the main ideas the page teaches.

{% include track_map.html track="advanced" %}

---

---

## Take it home

Every script here is a template you can adapt: swap in your own documents, questions and labels. [Take It
Home]({{ '/take-home/' | relative_url }}) shows what to change.

{% if site.show_survey %}
---

## Post-class survey

At the end of the day, tell us how it went: [darc.stanford.edu/hackathon-survey](https://darc.stanford.edu/hackathon-survey).
{% endif %}
