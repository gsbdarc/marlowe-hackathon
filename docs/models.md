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
| Kev-4B | 153 MB (adapter) | [Beginner]({{ '/beginner/' | relative_url }}) |
| Qwen3.5-4B-Base | 9 GB (full weights) | [Beginner]({{ '/beginner/' | relative_url }})<br>[Intermediate]({{ '/intermediate/' | relative_url }})<br>[Advanced]({{ '/advanced/' | relative_url }}) |
| Kev-27B | 51 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |
| Qwen3.8-27B | Yens: 23 MB (tokenizer only)<br>Marlowe: 52 GB (full weights) | [Advanced]({{ '/advanced/' | relative_url }}) |

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

Run these from an interactive Yen node as the owner of `/scratch/shared/marlowe_hackathon`, from the shared clone.
`setup_kev.sh` installs Kev and its `hf` command first; if a model is gone it stops at `model missing`, after the
install, which is all the next lines need.

```bash
cd /scratch/shared/marlowe_hackathon
source env/yens.sh
bash scripts/setup_kev.sh
export HF_HUB_OFFLINE=0
HF=$KEV_HOME/kev/.venv/bin/hf
$HF download jaredpalmer/kev-4b --revision v1.0
$HF download Qwen/Qwen3.5-4B-Base --revision main
$HF download jaredpalmer/kev-27b --revision af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf
$HF download Qwen/Qwen3.8-27B --revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0 --exclude "*.safetensors"
chmod -R g-w $HF_HUB_CACHE
```
{: .yens }

| Line | What it does |
|---|---|
| `export HF_HUB_OFFLINE=0` | `env/yens.sh` turns downloads off; this turns them back on for this terminal only |
| `$HF download ...` | downloads one model at one revision into `$HF_HUB_CACHE`; a model already there is checked and skipped |
| `--exclude "*.safetensors"` | skips the weights: Kev-27B needs only its base model's tokenizer and config |
| `chmod -R g-w $HF_HUB_CACHE` | makes the cache read only for everyone but its owner |

Kev-27B took 89 seconds to download. No Hugging Face token is needed: all four models are public.

{: .warning }
> To exclude more than one pattern, repeat the flag: `--exclude "*.safetensors" --exclude "*.bin"`. After a single
> `--exclude`, the `hf` command reads a second pattern as a file name and downloads nothing.

Then open a new terminal, so `HF_HUB_OFFLINE=1` is back, and check:

```bash
cd /scratch/shared/marlowe_hackathon
source env/yens.sh
bash scripts/setup_kev.sh
```
{: .yens }

On Marlowe, run the same lines from the login node, in your clone in `/scratch/m000106/gsb_hackathon/$USER`, with
`source env/marlowe.sh` in place of `source env/yens.sh`. Marlowe keeps the full Qwen3.8-27B, so leave out
`--exclude "*.safetensors"` there.

## Adding a model

When a task needs a new model, download it with the lines above, add a row to the table on this page, and add it to
the model check in `scripts/setup_kev.sh`.
