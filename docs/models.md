---
layout: default
title: "Models"
nav_order: 1
permalink: /models/
---

# Models

{: .note }
> The organizers have pre-downloaded the models to both clusters.

---

## Where the models are

Each cluster has one shared, read-only model cache. `env/yens.sh` and `env/marlowe.sh` point `HF_HUB_CACHE` at it
and set `HF_HUB_OFFLINE=1`, so setup and jobs read from the cache and never download.

| Cluster | Shared cache (`HF_HUB_CACHE`) |
|---|---|
| Yens | `/scratch/shared/marlowe_hackathon/hf/hub` |
| Marlowe | `/scratch/c001/marlowe-hackathon/hf_cache/hub` |

## What is in the cache

| Model | Size | Used by |
|---|---|---|
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 160 MB (adapter) | [Intermediate]({{ '/intermediate/' | relative_url }}) |
| [Qwen3.5-4B-Base](https://huggingface.co/Qwen/Qwen3.5-4B-Base) | 9.3 GB (full weights) | [Intermediate]({{ '/intermediate/' | relative_url }})<br>[Advanced]({{ '/advanced/' | relative_url }}) |
| [Kev-27B](https://huggingface.co/jaredpalmer/kev-27b) | 51 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Yens: 23 MB (tokenizer only)<br>Marlowe: 56 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |
| [Qwen3-235B-A22B-Instruct-2507-FP8](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8) | Marlowe only: 237 GB (full weights, FP8) | [Advanced]({{ '/advanced/' | relative_url }}) |

An adapter is a small set of changes that runs on top of a base model: Kev-4B runs on Qwen3.5-4B-Base. Kev-27B
reads its tokenizer from Qwen3.8-27B, which is all the Yens need of that model. Each model is pinned to one
revision, a fixed version on Hugging Face, so everyone uses the same weights; `setup/setup.sh` lists them.

## How the models got there

Before the class, an instructor runs `setup/setup.sh` once on each cluster. It downloads every model into the
cluster's cache at its pinned revision, along with the data and, on Marlowe, the vLLM container. The steps, and how
to run it again if a model is deleted, are in the repository's [setup README](https://github.com/gsbdarc/marlowe-hackathon/blob/main/setup/README.md).

## Check the cache

`setup_kev.sh` checks every model without downloading anything:

```bash
source env/yens.sh
bash scripts/setup_kev.sh
```
{: .yens }

It ends with one `model ok` line per model, `tokenizer ok`, and `Kev ready`. A missing model stops it with
`model missing from ...` and the model's name.

## Adding a model

When a task needs a new model, add it to the `MODELS` list in `setup/setup.sh` and to the model check in
`scripts/setup_kev.sh`, and add a row to the table on this page.
