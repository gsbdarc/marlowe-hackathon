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
| Marlowe | `/scratch/m000106/gsb_hackathon/hf_cache/hub` |

## What is in the cache

| Model | Size | Used by |
|---|---|---|
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 153 MB (adapter) | [Beginner]({{ '/beginner/' | relative_url }}) |
| [Qwen3.5-4B-Base](https://huggingface.co/Qwen/Qwen3.5-4B-Base) | 9 GB (full weights) | [Beginner]({{ '/beginner/' | relative_url }})<br>[Intermediate]({{ '/intermediate/' | relative_url }})<br>[Advanced]({{ '/advanced/' | relative_url }}) |
| [Kev-27B](https://huggingface.co/jaredpalmer/kev-27b) | 51 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Yens: 23 MB (tokenizer only)<br>Marlowe: 52 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |

An adapter is a small set of changes that runs on top of a base model: Kev-4B runs on Qwen3.5-4B-Base. Kev-27B
reads its tokenizer from Qwen3.8-27B, which is all the Yens need of that model. Each model is pinned to one
revision, a fixed version on Hugging Face, so everyone uses the same weights; the download commands below list them.

## Check the cache

`setup_kev.sh` checks every model without downloading anything:

```bash
source env/yens.sh
bash scripts/setup_kev.sh
```
{: .yens }

It ends with one `model ok` line per model, `tokenizer ok`, and `Kev ready`. A missing model stops it with
`model missing from ...` and the model's name.

## Download them again

`scripts/download_models.sh` downloads every model into the cache of the cluster it runs on. Run it from your clone of
this repository, as the organizer who owns the cache: on the Yens from an interactive node, on Marlowe from the login
node.

```bash
bash scripts/download_models.sh
```
{: .yens }

```bash
bash scripts/download_models.sh
```
{: .marlowe }

It works out the cluster from the node's name, then:

| Step | What it does |
|---|---|
| `source env/yens.sh` or `env/marlowe.sh` | sets the cache path for that cluster |
| `bash scripts/setup_kev.sh` | installs Kev, for its `hf` command; its model check fails while models are missing, which is expected |
| `hf download ...` | downloads each model at its pinned revision; a model already in the cache is checked and skipped |
| Qwen3.8-27B | tokenizer and config only on the Yens (`--exclude "*.safetensors"`), full weights on Marlowe |
| `chmod -R g-w` | Yens only: makes the cache read only for everyone but its owner. Marlowe's cache stays writable by the project group (`marlowe-m000106`) |
| `bash scripts/setup_kev.sh` again | checks every model with downloads off (`HF_HUB_OFFLINE=1`) |

It ends with three `model ok` lines, `tokenizer ok` and `Kev ready`. Kev-27B took 89 seconds to download on the Yens.
No Hugging Face token is needed: all four models are public.

## Adding a model

When a task needs a new model, add a download line to `scripts/download_models.sh`, add it to the model check in
`scripts/setup_kev.sh`, and add a row to the table on this page.
