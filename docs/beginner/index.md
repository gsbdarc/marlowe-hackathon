---
layout: default
title: "Beginner Track"
nav_order: 3.5
has_children: true
permalink: /beginner/
---

# Beginner Track

For researchers who have not trained a model or used a GPU cluster before. You score Kev-4B against Jev, fine-tune its
adapter for about 10 minutes on one GPU on the Yens, then use DARC's fine-tuned Kev-4B to label filings on Marlowe,
first on one H100 and then on all eight GPUs of a node. Nothing here needs code of your own: every step is a script in
this repository.

Start with [The Data]({{ '/beginner/data/' | relative_url }}): what the filings are, where Jev's labels come from, and
where everything is stored.

| | Where | What you do | Data | Model |
|---|---|---|---|---|
| 1 | Yens, 1 GPU | Score Kev-4B before training | 1,000 test filings (2022 to 2026) with Jev's labels | Kev-4B as released |
| 2 | Yens, 1 GPU | [Fine-tune Kev-4B's LoRA adapter]({{ '/beginner/finetune/' | relative_url }}) for about 10 minutes, compare settings, then score your best once on test | `train.jsonl` with Jev's soft labels; 2,000 validation filings (2019 to 2021); the 1,000 test filings | Kev-4B's adapter, fine-tuned |
| 3 | Marlowe, 1 H100 | Label a slice of filings | a slice of filings, no labels needed | DARC's fine-tuned Kev-4B |
| 4 | Marlowe, 1 node | The same labeling job on 8 GPUs | 8 slices of filings, no labels needed | DARC's fine-tuned Kev-4B |

The pages for exercises 1, 3 and 4 are coming.
