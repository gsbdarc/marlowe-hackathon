---
layout: default
title: "Beginner Track"
nav_order: 3.5
has_children: true
permalink: /beginner/
---

# Beginner Track

For researchers who have not trained a model or used a GPU cluster before. You score Kev-4B against Jev, train it for
100 steps on one GPU on the Yens, then use DARC's fine-tuned Kev-4B to label filings on Marlowe, first on one H100
and then on all eight GPUs of a node. Nothing here needs code of your own: every step is a script in this repository.

Start with [The Data]({{ '/beginner/data/' | relative_url }}): what the filings are, where Jev's labels come from, and
where everything is stored.

| | Where | What you do | Data | Model |
|---|---|---|---|---|
| 1 | Yens, 1 GPU | Score Kev-4B before training | 1,000 test filings (2022 to 2026) with Jev's labels | Kev-4B as released |
| 2 | Yens, 1 GPU | Fine-tune Kev-4B for 100 steps, then score it again | `train.jsonl` with Jev's soft labels; the 1,000 test filings | Kev-4B, merged to full weights, then fine-tuned |
| 3 | Marlowe, 1 H100 | Label a slice of filings | a slice of filings, no labels needed | DARC's fine-tuned Kev-4B |
| 4 | Marlowe, 1 node | The same labeling job on 8 GPUs | 8 slices of filings, no labels needed | DARC's fine-tuned Kev-4B |

The pages for exercises 1 to 4 are coming.
