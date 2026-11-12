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

1. **[The Project and the Data]({{ '/task/' | relative_url }}):** the SEC filings, the three questions Jev answered
   about each, the training files, and the Kev models you start from.
2. **[Key Ideas]({{ '/concepts/' | relative_url }}):** the terms the task pages use. Skim it now and come back to it
   when a page uses one.
3. **Your SUNet ID:** type it in the **Your details** box in the sidebar. The commands on every page then show your
   own paths.
4. **Slack:** join [{{ site.slack_channel }}]({{ site.slack_url }}). It is where you post results and ask questions.
5. **How the hands-on part works,** below.
6. **Pick a track** and open its first task.

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
| [Beginner]({{ '/beginner/' | relative_url }}) | for researchers who have not trained a model or used a GPU cluster before | [Beginner]({{ '/beginner/' | relative_url }}) |
| [Intermediate]({{ '/intermediate/' | relative_url }}) | one model, from one GPU to a full node | [I1. Score before training]({{ '/intermediate/i1/' | relative_url }}) |
| [Advanced]({{ '/advanced/' | relative_url }}) | fine-tune a model too large for one GPU, on one node and then two | [A1. Score before training]({{ '/advanced/a1/' | relative_url }}) |

The [Reference]({{ '/reference/' | relative_url }}) pages are for when a task sends you there: the models on each
cluster, watching a job while it runs, copying files between the clusters with Globus, and using a model you trained.
