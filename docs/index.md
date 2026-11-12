---
layout: default
title: "Marlowe Hackathon 2026"
nav_order: 0
permalink: /
---

# Marlowe Hackathon 2026

Welcome to the Marlowe Hackathon, a one-day, hands-on event for Stanford GSB researchers, run by DARC and the HAI
Marlowe team. You fine-tune open-weight models, first on the Yens and then on Marlowe, Stanford's H100 cluster.

---

## Objectives

By the end of the day you will have:

- run GPU jobs on Marlowe
- run the same job on one GPU and on a full node of 8 H100s, and compared the time per step, the GPU memory and the
  GPU-hours
- fine-tuned a model, scored it, and posted the result in [{{ site.slack_channel }}]({{ site.slack_url }})
- followed a running job through its log, its GPU use and its loss in Weights & Biases
  ([Monitoring Training]({{ '/monitoring/' | relative_url }}))
- job files to adapt for your own research ([Take It Home]({{ '/take-home/' | relative_url }}))
- an outline of how your PI's group applies for Marlowe and what the application asks for
  ([Applying for Marlowe]({{ '/take-home/' | relative_url }}#applying-for-marlowe))
- places to get help afterwards: [RCpedia](https://rcpedia.stanford.edu) for the Yens,
  [Marlowe's documentation](https://marlowe-research.stanford.edu/documentation/), and the Slack channel

---

## Schedule

| Time | Session |
|---|---|
| 9:30 | Coffee |
| 10:00 | Welcome, and a check that you can log in to the Yens and Marlowe |
| 10:15 | An introduction to Marlowe, from the Marlowe team |
| 10:50 | A social science researcher's Marlowe story |
| 11:30 | Break |
| 11:40 | Hands-on: start the first task of your track |
| 12:30 | Lunch |
| 1:15 | Hands-on |
| 2:30 | Break |
| 2:40 | Hands-on |
| 4:00 | Awards, and next steps for applying for Marlowe |

---

## Tracks

Pick one track and work through its tasks in order.

| Task | [Beginner]({{ '/beginner/' | relative_url }}) | [Intermediate]({{ '/intermediate/' | relative_url }}) | [Advanced]({{ '/advanced/' | relative_url }}) |
|---|---|---|---|
| 1 | [Being written]({{ '/beginner/' | relative_url }}) | [Score before training]({{ '/intermediate/i1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/advanced/a1/' | relative_url }}) (Yens, 1 H200) |
| 2 | | [Fine-tune on one GPU]({{ '/intermediate/i2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one node]({{ '/advanced/a2/' | relative_url }}) (Marlowe, 1 H100, then 8 H100s) |
| 3 | | [Fine-tune on one Marlowe GPU]({{ '/intermediate/i3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) (Marlowe, 16 H100s) |
| 4 | | [Fine-tune on a full node]({{ '/intermediate/i4/' | relative_url }}) (Marlowe, 1 node) | [Inference at scale]({{ '/advanced/a4/' | relative_url }}) (Marlowe, 8 H100s) |
| 5 | | [Inference at scale]({{ '/intermediate/i5/' | relative_url }}) (Marlowe, 1 node) | [Distill a student]({{ '/advanced/a5/' | relative_url }}) (Marlowe, 1 H100) |

### The Advanced track at a glance

Each card links to its task and to the ideas it covers.

{% include track_map.html track="advanced" %}

---

## Take it home

The scripts and job files are templates: swap in your own documents, questions and labels.
[Take It Home]({{ '/take-home/' | relative_url }}) shows what to change.

{% if site.show_survey %}
---

## Post-class survey

At the end of the day, tell us how it went: [darc.stanford.edu/hackathon-survey](https://darc.stanford.edu/hackathon-survey).
{% endif %}
