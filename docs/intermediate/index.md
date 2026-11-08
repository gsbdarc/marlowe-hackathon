---
layout: default
title: "Intermediate"
nav_order: 6
has_children: true
permalink: /intermediate/
---

# Intermediate track

One model, from one GPU to a full node. You score Kev-4B against Jev and fine-tune it on one GPU on the Yens, then move
to Marlowe: the same fine-tune on one H100, every weight trained on one H100 and then on all eight GPUs of a node, and
finally every filing labeled on all eight GPUs at once. Every step is a script in this repository: you pick the
settings, run the jobs, and compare what each one costs.

| Task | Where | What you do |
|---|---|---|
| [I1. Score before training]({{ '/intermediate/i1/' | relative_url }}) | Yens, 1 GPU | Score Kev-4B as released on 1,000 test filings. |
| [I2. Fine-tune on one GPU]({{ '/intermediate/i2/' | relative_url }}) | Yens, 1 GPU | Fine-tune for 10 minutes on Jev's labels, getting as far as you can, then score it against Kev-4B. |
| [I3. Fine-tune on one Marlowe GPU]({{ '/intermediate/i3/' | relative_url }}) | Marlowe, 1 H100 | Run the same fine-tune and compare its speed with the Yens GPU, then train every weight. |
| [I4. Fine-tune on a full node]({{ '/intermediate/i4/' | relative_url }}) | Marlowe, 8 H100s | Run the full fine-tune on all 8 GPUs and compare its time and GPU-hours with one GPU. |
| [I5. Inference at scale]({{ '/intermediate/i5/' | relative_url }}) | Marlowe, 8 H100s | Label all 296,477 filings, one shard per GPU, and work out what it costs against Jev. |
