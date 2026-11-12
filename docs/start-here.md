---
layout: default
title: "Start Here"
nav_order: 1
has_children: true
has_toc: false
permalink: /start-here/
---

# Start Here

Read these in order before your first task.

1. Read [The Project and the Data]({{ '/task/' | relative_url }}): the SEC filings, the three questions Jev answered
   about each, the training files, and the Kev models you start from.
2. Skim [Key Ideas]({{ '/concepts/' | relative_url }}), the terms the task pages use, and come back to it when a page
   uses one.
3. Type your SUNet ID in the **Your details** box in the sidebar, so the commands on every page show your own paths.
4. Join [{{ site.slack_channel }}]({{ site.slack_url }}), where you post results and ask questions.
5. Read how the hands-on part works, below.
6. Pick a track and open its first task.

If a command fails, a page is wrong or you spot a typo, click **File an issue** in the sidebar. It opens a GitHub
issue with the page filled in; add what you ran and what happened. You need a GitHub account to file one.

---

## How the hands-on part works

It is self-paced: pick one track and work through its tasks in order, at your own speed. Keep the two sticky notes on
your table:

- 🟥 **Red on your laptop when you need help.** An instructor comes to you.
- 🟩 **Green on your laptop when you finish a task.** Post your result in
  [{{ site.slack_channel }}]({{ site.slack_url }}) on Slack too. An instructor comes round to check it, and each checked
  task counts toward the GPU-hours awarded at the end of the day.

---

## Pick a track

| Track | What you do | First task |
|---|---|---|
| [Beginner]({{ '/beginner/' | relative_url }}) | for people who have never used a computing cluster or a GPU | [B1. Your first GPU job]({{ '/beginner/b1/' | relative_url }}) |
| [Intermediate]({{ '/intermediate/' | relative_url }}) | one model, from one GPU to a full node | [I1. Score before training]({{ '/intermediate/i1/' | relative_url }}) |
| [Advanced]({{ '/advanced/' | relative_url }}) | fine-tune a model too large for one GPU, on one node and then two | [A1. Score before training]({{ '/advanced/a1/' | relative_url }}) |

The tasks in each track:

| Task | [Beginner]({{ '/beginner/' | relative_url }}) | [Intermediate]({{ '/intermediate/' | relative_url }}) | [Advanced]({{ '/advanced/' | relative_url }}) |
|---|---|---|---|
| 1 | [Your first GPU job]({{ '/beginner/b1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/intermediate/i1/' | relative_url }}) (Yens, 1 GPU) | [Score before training]({{ '/advanced/a1/' | relative_url }}) (Yens, 1 H200) |
| 2 | [Fine-tune the model]({{ '/beginner/b2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one GPU]({{ '/intermediate/i2/' | relative_url }}) (Yens, 1 GPU) | [Fine-tune on one node]({{ '/advanced/a2/' | relative_url }}) (Marlowe, 1 H100, then 8 H100s) |
| 3 | [Run it on Marlowe]({{ '/beginner/b3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on one Marlowe GPU]({{ '/intermediate/i3/' | relative_url }}) (Marlowe, 1 H100) | [Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) (Marlowe, 16 H100s) |
| 4 | [Many GPUs at once]({{ '/beginner/b4/' | relative_url }}) (Marlowe, 1 to 8 H100s) | [Fine-tune on a full node]({{ '/intermediate/i4/' | relative_url }}) (Marlowe, 1 node) | [Inference at scale]({{ '/advanced/a4/' | relative_url }}) (Marlowe, 8 H100s) |
| 5 | [From labels to a finding]({{ '/beginner/b5/' | relative_url }}) (Marlowe, no GPU) | [Inference at scale]({{ '/intermediate/i5/' | relative_url }}) (Marlowe, 1 node) | [Distill a student]({{ '/advanced/a5/' | relative_url }}) (Marlowe, 1 H100) |

Each card in the box below links to a task and to the ideas it covers.

{% include track_picker.html %}

The [Reference]({{ '/reference/' | relative_url }}) pages are for when a task sends you there: the models on each
cluster, watching a job while it runs, copying files between the clusters with Globus, and using a model you trained.
