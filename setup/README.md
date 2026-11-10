# Instructor setup

`setup/setup.sh` puts everything the class needs on a cluster: the models, the vLLM container, and Jev's data with
the training and test files built from it. Run it once on the Yens and once on Marlowe before the class, and again if
anything is deleted. Each step checks what is already there and skips it, so a rerun on a cluster that is set up
takes a few minutes and changes nothing. Participants never run it; they run `scripts/setup_kev.sh` in class.

## Where everything goes

| | Yens | Marlowe |
|---|---|---|
| Shared folder: the instructors' clone, read only for participants | `/scratch/shared/marlowe_hackathon` | `/scratch/c001/marlowe-hackathon` |
| Models | `hf/hub` | `hf_cache/hub` |
| vLLM container | | `containers/vllm-openai_v0.31.0.sif` |
| Jev's release | `data/jev` | `data/jev` |
| Training and test files | `data/` | `data/` |
| Each participant's folder | `/scratch/users/<sunet>` | `/scratch/c001/users/<sunet>` |

The paths come from `env/yens.sh` and `env/marlowe.sh`; change them there.

## Run it

On the Yens, from an interactive node:

```bash
cd /scratch/shared/marlowe_hackathon
bash setup/setup.sh
```

On Marlowe, from the login node, clone into the shared folder itself, as on the Yens. Jev's release lives only on the Yens, in
`/scratch/shared/marlowe_hackathon/data/jev` (it is not on GitHub or Hugging Face), so the script copies it over with
`rsync` and asks you to log in to the Yens once: password, then Duo.

```bash
git clone https://github.com/gsbdarc/marlowe-hackathon.git /scratch/c001/marlowe-hackathon
cd /scratch/c001/marlowe-hackathon
bash setup/setup.sh
```

The script ends with `setup done`. The first run on
Marlowe downloads about 330 GB, most of it Qwen 235B, so start it well before the class.

## What it does

| Step | What it does | Skipped when |
|---|---|---|
| 1. Models | downloads each model at its pinned revision with `hf download`, using a temporary copy of `huggingface_hub` 1.32.0, the version Kev uses. No token is needed: the models are public. On the Yens, Qwen3.8-27B is tokenizer and config only; on Marlowe it is full weights, and Qwen 235B and the vLLM container are added for A4. Then it makes the cache read only and checks every model with downloads off | the model is already in the cache |
| 2. Kev | runs `scripts/setup_kev.sh` for you, the same setup participants run. Step 3 needs Kev's Python | each part already installed |
| 3. Data | on Marlowe copies Jev's release from the Yens with `rsync`, checks each file in `data/jev` against `MANIFEST.json`, builds `train.jsonl`, `valid.jsonl`, `test1000.jsonl` and `test1000.parquet` with `scripts/make_kev_data.py`, and makes them read only. On Marlowe it also makes `/scratch/c001/users`, where each participant makes a folder for their own clone | the release or the training and test files are already there (the checksums are always checked) |

Git ignores the data, models and container inside the clone: only the code is tracked. The files it makes belong to whoever runs it, and only that person can change them afterwards. Run it as the
instructor who will look after the cluster's shared folder.

## Adding a model

Add it to `MODELS` in `setup/setup.sh` and to the model check in `scripts/setup_kev.sh`, add a row to the
website's Models page, and rerun `bash setup/setup.sh`.
