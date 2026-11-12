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
2. Skim [Key Ideas]({{ '/concepts/' | relative_url }}): what Jev and Kev are, how fine-tuning works, and how a job
   scales across GPUs. Come back to it when a task page links there.
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

Each track starts on the Yens and moves to Marlowe. If you have never used a GPU, pick Beginner. If you have run jobs
on the Yens, pick Intermediate, or Advanced to train a model too large for one GPU.

| Track | For you if | How it goes |
|---|---|---|
| [Beginner]({{ '/beginner/' | relative_url }}) | you have never used a GPU | Score a 4B model on one Yens GPU and train it, run the same training on Marlowe, label filings since 2004 on several Marlowe GPUs at once, and turn the labels into a research finding. Every step is a script you run. |
| [Intermediate]({{ '/intermediate/' | relative_url }}) | you have run jobs on the Yens | Score Kev-4B and fine-tune it on one Yens GPU, run the same fine-tune on one H100, train every weight on one H100 and then on a full node of 8, and label every filing on all 8 GPUs at once. You pick the settings and compare what each run costs. |
| [Advanced]({{ '/advanced/' | relative_url }}) | you have run jobs on the Yens and want to train a model too large for one GPU | Score Kev-27B on a Yens H200, fully fine-tune a 27B model on one Marlowe node and then two, serve a 235B model across a node, and distill a small model from its labels. |

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
