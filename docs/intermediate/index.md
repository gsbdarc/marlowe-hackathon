---
layout: default
title: "Intermediate"
nav_order: 6
has_children: true
permalink: /intermediate/
---

# Intermediate track

Scaling a real workload: fine-tune and profile on the Yens, move your data to Marlowe, then label the whole corpus.

| Task | Where | What you do |
|---|---|---|
| [I1. Fine-tune and profile Kev-4B]({{ '/intermediate/i1/' | relative_url }}) | Yens, 1 GPU | Fine-tune Kev-4B and measure time per step. |
| [I2. Move your data with Globus]({{ '/intermediate/i2/' | relative_url }}) | Yens to Marlowe | Move your run and data with the Globus CLI and Claude Code. |
| [I3. Label the test split on a node]({{ '/intermediate/i3/' | relative_url }}) | Marlowe, 1 node | Label the test split (56,334 filings) on 8 GPUs and score it. |
| [I4. Label the corpus on two nodes]({{ '/intermediate/i4/' | relative_url }}) | Marlowe, 2 nodes | Label all 296,477 filings on 16 GPUs. |
