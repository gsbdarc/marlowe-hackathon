---
layout: default
title: "Beginner"
nav_order: 5
has_children: true
permalink: /beginner/
---

# Beginner track

For researchers who have not trained a model or used a GPU cluster before. You score Kev-4B against Jev and fine-tune
Qwen 4B on one GPU on the Yens, then run the same fine-tune on Marlowe, first on one H100 and then on all eight GPUs of a
node, and finally label filings with your model on all eight GPUs at once. Nothing here needs code of your own: every
step is a script in this repository.

| Task | Where | What you do |
|---|---|---|
| [B1. Score Kev-4B before training]({{ '/beginner/b1/' | relative_url }}) | Yens, 1 GPU | Score Kev-4B as released on 1,000 test filings. |
| [B2. Fine-tune Qwen 4B]({{ '/beginner/b2/' | relative_url }}) | Yens, 1 GPU | Fine-tune for 100 steps on Jev's labels, then score it against Kev-4B. |
| [B3. Fine-tune on one Marlowe GPU]({{ '/beginner/b3/' | relative_url }}) | Marlowe, 1 H100 | Run the same fine-tune and compare its speed with the Yens GPU. |
| [B4. Fine-tune on a full node]({{ '/beginner/b4/' | relative_url }}) | Marlowe, 8 H100s | Run the same fine-tune on 8 GPUs and compare seconds per step. |
| [B5. Inference at scale]({{ '/beginner/b5/' | relative_url }}) | Marlowe, 8 H100s | Label filings with your model, one shard per GPU, and tune GPU utilization. |
