---
layout: default
title: "Beginner"
nav_order: 5
has_children: true
permalink: /beginner/
---

# Beginner track

First GPU jobs. Most of the work is on the Yens; Marlowe comes at the end, with one GPU and then a full node.

| Task | Where | What you do |
|---|---|---|
| [B1. Score Kev-4B before training]({{ '/beginner/b1/' | relative_url }}) | Yens, 1 GPU | Score Kev-4B before training on 1,000 test filings. |
| [B2. Fine-tune Kev-4B]({{ '/beginner/b2/' | relative_url }}) | Yens, 1 GPU | Fine-tune Kev-4B for 100 steps, then score it again. |
| [B3. Label filings on one Marlowe GPU]({{ '/beginner/b3/' | relative_url }}) | Marlowe, 1 H100 | Label a slice of filings with the fine-tuned Kev-4B. |
| [B4. Label on a full node]({{ '/beginner/b4/' | relative_url }}) | Marlowe, 1 node (8 H100s) | Run the same labeling job on 8 GPUs, one slice each. |
