---
layout: default
title: "Advanced"
nav_order: 7
has_children: true
permalink: /advanced/
---

# Advanced track

Fine-tune a model too large for one GPU. You score Kev-27B on one Yens H200 to set the bar, fine-tune Qwen3.8-27B on
Marlowe on one node and then two, serve Qwen 235B across a full node, and distill a small student from a teacher's
labels.

| Task | Where | What you do |
|---|---|---|
| [A1. Score Kev-27B before training]({{ '/advanced/a1/' | relative_url }}) | Yens, 1 H200 | Serve Kev-27B and score it on 1,000 test filings |
| [A2. Fine-tune Qwen 27B]({{ '/advanced/a2/' | relative_url }}) | Marlowe, 1 H100, then 8 H100s | It runs out of memory on one GPU and fits on 8 with FSDP |
| [A3. Fine-tune on two nodes]({{ '/advanced/a3/' | relative_url }}) | Marlowe, 16 H100s | Run the same fine-tune across 2 nodes and compare with 1 node |
| [A4. Inference at scale with Qwen 235B]({{ '/advanced/a4/' | relative_url }}) | Marlowe, 8 H100s | Load Qwen 235B on one node, time the weight load, and label filings |
| [A5. Distill a student]({{ '/advanced/a5/' | relative_url }}) | Marlowe, 1 H100 | Train Qwen 4B on teacher labels (yours or DARC's) and score it |

Data and models are in place on both clusters before the day, so no task waits on a transfer. If a step runs late,
DARC's result for it lets you go on.

## Data and models

| Task | Data | Model |
|---|---|---|
| A1 | 1,000 test filings (2022 to 2026) with Jev's labels | Kev-27B as released |
| A2 | `train.jsonl`: 54,426 filings (2004 to 2018) with Jev's soft labels | Qwen3.8-27B |
| A3 | `train.jsonl` | Qwen3.8-27B |
| A4 | the training filings, no labels needed | Qwen 235B |
| A5 | the training filings with teacher labels; the 1,000 test filings to score | Qwen3.5-4B-Base |

## Bonus

- Move a run between the Yens and Marlowe with [Globus]({{ '/globus/' | relative_url }}).
- Run the distilled student on the Yens.

{: .note }
> The Advanced track has not had its dry run yet. A2 to A5 are still being written.
