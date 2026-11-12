# Instructor setup

`setup/setup.sh` puts everything the class needs on a cluster: the models, the vLLM container, and Jev's data with
the training and test files built from it. Run it once on the Yens and once on Marlowe before the class, and again if
anything is deleted. Each step checks what is already there and skips it, so a rerun on a cluster that is set up
takes a few minutes and changes nothing. Participants never run it. In class they run `scripts/setup_kev.sh`, which only checks the shared Kev and the models.

## Where everything goes

| | Yens | Marlowe |
|---|---|---|
| Shared folder, read only for participants | `/scratch/shared/marlowe_hackathon` | `/scratch/c001/marlowe-hackathon` |
| Each participant's folder | `/scratch/users/<sunet>` | `/scratch/c001/users/<sunet>` |

Inside the shared folder, on both clusters:

```
data/          Jev's release (jev/) and train, valid, test1000
models/        the Hugging Face model cache
containers/    the vLLM container (Marlowe only)
kev/           the shared Kev and its Python
repo/          the instructors' clone, which runs setup/setup.sh
```

Each participant's folder holds their clone (`marlowe-hackathon/`), their work (`ceo-turnover/`, which is `$WORK`)
and `.cache/`, where every cache goes, never the home folder.

The paths come from `env/yens.sh` and `env/marlowe.sh`; change them there.

## Run it

Clone into `repo/` in the shared folder; the script fills in the folders next to it.

On the Yens, from an interactive node. Jev's release is copied from DARC's project space,
`/yen/projects/darc/marlowe_hackathon`:

```bash
git clone https://github.com/gsbdarc/marlowe-hackathon.git /scratch/shared/marlowe_hackathon/repo
cd /scratch/shared/marlowe_hackathon/repo
bash setup/setup.sh
```

On Marlowe, from the login node. Jev's release lives only on the Yens (it is not on GitHub or Hugging Face), so the
script copies it from `/scratch/shared/marlowe_hackathon/data/jev` with `rsync` and asks you to log in to the Yens
once: password, then Duo. Run the Yens setup first.

```bash
git clone https://github.com/gsbdarc/marlowe-hackathon.git /scratch/c001/marlowe-hackathon/repo
cd /scratch/c001/marlowe-hackathon/repo
bash setup/setup.sh
```

The script ends with `setup done`. The first run on
Marlowe downloads about 330 GB, most of it Qwen 235B, so start it well before the class.

## What it does

| Step | What it does | Skipped when |
|---|---|---|
| 1. Models | downloads each model at its pinned revision with `hf download`, using a temporary copy of `huggingface_hub` 1.32.0, the version Kev uses. No token is needed: the models are public. On the Yens, Qwen3.8-27B is tokenizer and config only; on Marlowe it is full weights, and Qwen 235B and the vLLM container are added for A4. Then it makes the cache read only and checks every model with downloads off | the model is already in the cache |
| 2. Kev | builds the shared Kev everyone uses, in `kev/`, with `KEV_BUILD=1 bash scripts/setup_kev.sh`, and makes it read only. Without `KEV_BUILD=1`, as participants run it, `setup_kev.sh` only checks Kev and never changes it. Step 3 needs Kev's Python | Kev is already there |
| 3. Data | copies Jev's release into `data/jev`: on the Yens from DARC's project space (`/yen/projects/darc/marlowe_hackathon`), on Marlowe from the Yens with `rsync`. It checks each file against `MANIFEST.json`, builds `train.jsonl`, `valid.jsonl`, `valid.parquet`, `test1000.jsonl` and `test1000.parquet` with `scripts/make_kev_data.py`, and makes them read only. On Marlowe it also makes `/scratch/c001/users`, where each participant makes a folder for their own clone | the release or the training and test files are already there (the checksums are always checked) |

The files it makes belong to whoever runs it, and only that person can change them afterwards. Run it as the
instructor who will look after the cluster's shared folder.

## Adding a model

Add it to `MODELS` in `setup/setup.sh` and to the model check in `scripts/setup_kev.sh`, add a row to the
website's Models page, and rerun `bash setup/setup.sh`.
