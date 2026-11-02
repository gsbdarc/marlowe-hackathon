---
layout: default
title: "Beginner Track"
nav_order: 3.5
has_children: true
permalink: /beginner/
---

# Beginner Track

For researchers who have not trained a model or used a GPU cluster before. You score Kev-4B against Jev and fine-tune its
adapter for about 10 minutes on one GPU on the Yens, then run the same fine-tune on Marlowe, first on one H100 and then
on all eight GPUs of a node, and finally label filings with your model on all eight GPUs at once. Nothing here needs
code of your own: every step is a script in this repository.

Start with [The Data]({{ '/beginner/data/' | relative_url }}): what the filings are, where Jev's labels come from, and
where everything is stored.

| | Where | What you do | Data | Model |
|---|---|---|---|---|
| B1 | Yens, 1 GPU | Score Kev-4B before training | 1,000 test filings (2022 to 2026) with Jev's labels | Kev-4B as released |
| B2 | Yens, 1 GPU | [Fine-tune Kev-4B's LoRA adapter]({{ '/beginner/finetune/' | relative_url }}) for about 10 minutes, compare settings, then score your best once on test | `train.jsonl` with Jev's soft labels; 2,000 validation filings (2019 to 2021); the 1,000 test filings | Kev-4B's adapter, fine-tuned |
| B3 | Marlowe, 1 H100 | Run the same fine-tune and compare its speed with the Yens GPU | `train.jsonl` with Jev's soft labels | Kev-4B's adapter, fine-tuned |
| B4 | Marlowe, 8 H100s | Run the same fine-tune on all 8 GPUs of a node and compare seconds per step | `train.jsonl` with Jev's soft labels | Kev-4B's adapter, fine-tuned |
| B5 | Marlowe, 8 H100s | Label filings with your model, one shard per GPU, and tune GPU utilization | 8 shards of filings, no labels needed | Your fine-tuned Kev-4B |

The pages for B1, B3, B4 and B5 are coming.
