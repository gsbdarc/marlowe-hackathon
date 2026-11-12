---
layout: default
title: "Beginner"
nav_order: 5
has_children: true
permalink: /beginner/
---

# Beginner track

For people who have never used a computing cluster or a GPU. You score a model on the Yens, train it, run the
training on Marlowe, label filings since 2004 on several Marlowe GPUs at once, and turn those labels into a research
finding. By the end you know what a cluster, a GPU and a Slurm job are, you have the GPU-hour numbers a Marlowe
application asks for, and you know how far to trust labels a model made.

Nothing here assumes you have done this before. Every term is explained the first time it appears, and every command
is one you copy and run. Each task asks you to make **one decision**, as a researcher would: which GPU, which learning
rate, how many GPUs, which question. Each choice has a default, so you can always run the default and follow along,
and the room's choices together answer something no single run can. Each task also ends with an optional
**challenge** for when you finish early. If you are already comfortable on a cluster and want to set everything
yourself, the [Intermediate track]({{ '/intermediate/' | relative_url }}) is the same task with every dial exposed.

| Task | Where | What you do | Your decision |
|---|---|---|---|
| [B1. Your first GPU job]({{ '/beginner/b1/' | relative_url }}) | Yens, 1 GPU | Log in, submit your first Slurm job, and score Kev-4B as released on 1,000 filings. | which GPU |
| [B2. Fine-tune the model]({{ '/beginner/b2/' | relative_url }}) | Yens, 1 GPU | Train Kev-4B for about 10 minutes on Jev's labels, choose on validation, and report on test. | which learning rate |
| [B3. Run it on Marlowe]({{ '/beginner/b3/' | relative_url }}) | Marlowe, 1 H100 | Run the same training on Marlowe's H100 and measure how much faster it is. | time or data |
| [B4. Many GPUs at once]({{ '/beginner/b4/' | relative_url }}) | Marlowe, 1 to 8 H100s | Label filings on several GPUs next to one, and work out what the extra GPUs buy and cost. | how many GPUs |
| [B5. From labels to a finding]({{ '/beginner/b5/' | relative_url }}) | Marlowe, no GPU | Turn your labels into a finding about CEO turnover, and test how far to trust it. | which question |

Each task ends with a check-in: post your result in [{{ site.slack_channel }}]({{ site.slack_url }}) on Slack and put
up a 🟩 green sticky, or a 🟥 red one if you are stuck and want a hand.

{% include track_map.html track="beginner" %}
