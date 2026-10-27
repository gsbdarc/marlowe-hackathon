---
layout: default
title: "Advanced"
nav_order: 7
has_children: true
permalink: /advanced/
---

# Advanced track

Train on Marlowe, run on the Yens. You fine-tune a large teacher model, Kev-27B, on Marlowe, have it label the training
filings on 16 GPUs, and distill a small student, Kev-4B, from its labels. Then you copy the student to the Yens, where
it labels filings on one GPU.

| Task | Where | What you do |
|---|---|---|
| [A1. Fine-tune the teacher]({{ '/advanced/a1/' | relative_url }}) | Marlowe, 1 GPU, then 1 node | Fine-tune Kev-27B. It runs out of memory on one H100 and fits on eight. |
| [A2. The teacher labels the filings]({{ '/advanced/a2/' | relative_url }}) | Marlowe, 2 nodes | Kev-27B labels the training and test filings on 16 GPUs |
| [A3. Distill the student]({{ '/advanced/a3/' | relative_url }}) | Marlowe, 1 GPU | Train Kev-4B on the teacher's labels, then move it to the Yens with Globus |
| [A4. Inference on the Yens]({{ '/advanced/a4/' | relative_url }}) | Yens, 1 GPU | Label filings with the distilled Kev-4B and score it against Jev |

Each task uses the result of the one before. If a step runs late, DARC's precomputed result for it lets you go on.

## Setup

Everything for this track is in one shared folder on Marlowe:

```bash
ssh <sunet>@login.marlowe.stanford.edu
source /scratch/m000106/gsb_hackathon/advanced/env.sh
cd $WORK
bash -l $ADV/check.sh
```
{: .marlowe }

`env.sh` sets every path the track uses. `$WORK` is your own folder, `/scratch/m000106/gsb_hackathon/advanced/<sunet>`;
your runs, labels and logs go there. Submit every job from `$WORK`, so its log lands in `$WORK/logs/`. `check.sh` lists
what is in place and submits nothing. Every line under "Shared setup" should say `OK`.

| | |
|---|---|
| Teacher | Kev-27B (`jaredpalmer/kev-27b@af0e6d5`), 51 GB of full weights, built on `Qwen/Qwen3.8-27B` |
| Student | Kev-4B (`jaredpalmer/kev-4b@v1.0`), merged to full weights, built on `Qwen/Qwen3.5-4B-Base` |
| Training data | `$DATA/train.jsonl`: 54,426 filings from 2004 to 2018 with Jev's soft labels |
| Test data | `$DATA/test1000.jsonl`: 1,000 filings from 2022 to 2026 with Jev's labels, for scoring |

{: .note }
> The Advanced track has not had its dry run yet. Times on these pages are estimates.
