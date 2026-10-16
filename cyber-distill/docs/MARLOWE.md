# Running cyber-distill on Marlowe

How to run the teacher (Stage 7) and the student (Stage 10) on Marlowe. The data is already there;
this page covers setup, the pilot, the full run and moving results back to the Yens. Status and
numbers live in the main [README](../README.md); log every command in `reports/run_log.md`.

vLLM runs in a container, following DARC's [vllm_helper](https://github.com/gsbdarc/vllm_helper)
and the RCpedia post
[Fine-Tuning Open Source Models with Together + vLLM](https://rcpedia.stanford.edu/blog/2025/11/07/fine-tuning-open-source-models/):
the `vllm/vllm-openai` image under Apptainer, started with `vllm.sh`, with the image, model weights
and caches in scratch. `scripts/07_teacher.py` is a client of that server.

## What is already on Marlowe

`/scratch/m000106/gsb_hackathon/cyber-distill/` (copied from the Yens with Globus, checksums verified):

| Path | Contents |
|---|---|
| `data/final/train_400k.parquet` | 400,000 training paragraphs (`in_25k`, `in_200k` mark the checkpoint subsets) |
| `data/final/val.parquet`, `test.parquet`, `test_incident_slice.parquet` | Frozen evaluation sets: 2,000, 5,000, 500 |
| `data/final/filings.parquet`, `company_split.parquet` | Filing metadata, frozen company split |
| `config/prompt_v1.txt`, `codebook.md`, `keywords.yaml` | Teacher prompt, codebook v1, prefilter terms |
| `scripts/`, `slurm/`, `docs/`, `requirements-marlowe.txt`, `README.md` | Code (also in `gsbdarc/marlowe-hackathon`, folder `cyber-distill/`) |
| `data/teacher/`, `models/` | Empty; teacher shards are written to `data/teacher/` |

Check the data after any transfer:

```bash
cd /scratch/m000106/gsb_hackathon/cyber-distill/data/final && sha256sum -c MANIFEST.sha256
```

## Before the first run: fill these in

| What | Where | Status |
|---|---|---|
| Slurm account and partition | `marlowe-m000106` on `preempt` (basic access), set in `slurm/marlowe/*.slurm`. `sinfo -p preempt` shows a **4:00:00 time limit** (31 nodes, 8 GPUs each; checked 2026-10-15), so every job asks for at most 4 hours and the full teacher run is a chain of jobs (step 5). Preempted jobs restart from the beginning: the teacher skips finished shards, the student takes `--resume` | Done (2026-10-15) |
| Apptainer on Marlowe | On the PATH, no module needed ([Marlowe Apptainer docs](https://marlowe-research.stanford.edu/documentation/software/apptainer/)). Home is 32 GB, so `APPTAINER_CACHEDIR` must be in scratch: `scripts/vllm/env.sh` sets it to `$SCRATCH_BASE/.apptainer` | Done in the scripts |
| Python for the client and training venv | Marlowe's system Python is 3.10 (modules: only `python3`, `python39`), too old for pandas 3 and numpy 2.4. `setup_venv.sh` installs uv 0.13.1 into `$MARLOWE_SHARE/tools` and builds the venv with Python 3.12; uv's Python and cache stay in scratch. Login nodes have internet (Hugging Face reachable) | Done in the scripts (2026-10-15) |
| Room in scratch for the image (12 GB) and teacher weights (~240 GB) | `/scratch/m000106` has a 10 TB limit (confirmed 2026-10-13); `SCRATCH_BASE` in `scripts/vllm/env.sh` defaults to `/scratch/m000106/gsb_hackathon/$USER` | Done. Still to confirm: no purge before Nov 13 |
| Teacher revision (commit hash) | `TEACHER_REVISION` in `scripts/marlowe/env.sh`: `e156cb4efae43fbee1a1ab073f946a1377e6b969` (224 GB, downloaded in about 4 min on the login node) | Done (2026-10-16) |

The scripts read data relative to `CYBER_ROOT` (set in `scripts/marlowe/env.sh`), so the code can
run from this directory or from a clone of the repository. Run everything from the code directory.

## Nothing in home

Marlowe home is 32 GB, so nothing from this project is written there. `scripts/marlowe/env.sh`
(sourced by every Marlowe job and by setup) sets the project paths and sources
`scripts/cache_env.sh`, which points every cache and config at scratch; `scripts/vllm/env.sh` does
the same for Apptainer and the container. The Yens use the same `cache_env.sh` through
`scripts/yens/env.sh`, with `/scratch/users/$USER` as the base (every job in `slurm/` sources it):

| Variable | Set to | Replaces default |
|---|---|---|
| `VENV` | `$MARLOWE_SHARE/envs/cyber` | |
| `HF_HOME` | `$MARLOWE_SHARE/hf_cache` (student base model) | `~/.cache/huggingface` |
| `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR` | `$MARLOWE_SHARE/.cache/uv`, `$MARLOWE_SHARE/tools/python` (uv itself: `$MARLOWE_SHARE/tools/uv`) | `~/.cache/uv`, `~/.local/share/uv` |
| `XDG_CACHE_HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME` | `$MARLOWE_SHARE/$USER/{.cache,.config,.local/share}` | `~/.cache`, `~/.config`, `~/.local/share` |
| `PIP_CACHE_DIR`, `TORCH_HOME`, `TORCHINDUCTOR_CACHE_DIR`, `TRITON_CACHE_DIR`, `CUDA_CACHE_PATH`, `MPLCONFIGDIR`, `PYTHONPYCACHEPREFIX` | under `$XDG_CACHE_HOME` | `~/.cache/...`, `~/.triton`, `~/.nv` |
| `APPTAINER_CACHEDIR`, `APPTAINER_CONFIGDIR` | `$SCRATCH_BASE/.apptainer`, `$SCRATCH_BASE/.apptainer-config` | `~/.apptainer` |
| `VLLM_CONTAINER_HOME` | `$SCRATCH_BASE/vllm/home`: the container's `/root` | real home mounted in the container |

`$SCRATCH_BASE` is `$MARLOWE_SHARE/$USER`. Inside the container, `vllm.sh` binds its Hugging Face,
compile caches and `/tmp` to `$SCRATCH_BASE/vllm`; `setup.sh` and `download_model.sh` run the
container with `--contain --cleanenv` and the same scratch home (without `--cleanenv`, the host's
cache variables point at `/scratch` paths the contained container cannot see).

Two checks keep it that way: the env files refuse to load (return 1, which stops a Slurm job, since
the jobs run `set -e`) if any of these paths is inside `$HOME`; and `setup_venv.sh`, `setup.sh` and
`download_model.sh` end with `home_check` (`scripts/home_check.sh`), which lists any file the step
wrote under `$HOME` and exits 1. Both passed on Marlowe on 2026-10-15.

## 1. Setup (once)

```bash
cd /scratch/m000106/gsb_hackathon/cyber-distill
mkdir -p logs
source scripts/marlowe/env.sh && source scripts/vllm/env.sh   # each refuses (returns 1) if a cache path is in home
bash scripts/marlowe/setup_venv.sh       # uv 0.13.1 + Python 3.12 venv in $VENV (requirements-marlowe.txt)
bash scripts/vllm/setup.sh               # vllm_helper at db1c923 and vllm/vllm-openai:v0.31.0 as a SIF in SCRATCH_BASE
```

`setup.sh` builds a 12 GB image; if Marlowe's login nodes discourage that, run it in a short CPU job.

## 2. Smoke test on one GPU (before the big download)

```bash
sbatch slurm/marlowe/07_teacher_smoke.slurm
```

Same container, wrapper and client as the pilot, with Qwen3-1.7B on one GPU and 400 items (as
tested on the Yens). It checks Apptainer, the model download from inside the container, MPS and
the client. Marlowe GPUs run NVIDIA MPS; the Marlowe Slurm docs say to `module load mps` to avoid
`CUDA_ERROR_MPS_CONNECTION_FAILED`, and every job in `slurm/marlowe/` does. `vllm.sh` starts the
container with `--contain --cleanenv` and its own `/tmp`, so if the server log
(`logs/vllm_server_<jobid>.log`) still shows an MPS connection error, the container cannot reach
the MPS daemon: try `srun -N 1 -G 1 -A <account> -p <partition> --pty bash`, `module load mps`,
then `env | grep -i mps` to find its pipe directory, and pass it through (an extra `--bind` and
`--env CUDA_MPS_PIPE_DIRECTORY=...` in a local copy of `vllm.sh`), or ask the Marlowe team.

## 3. Teacher weights (once, ~240 GB)

```bash
source scripts/marlowe/env.sh && source scripts/vllm/env.sh
bash scripts/vllm/download_model.sh Qwen/Qwen3-235B-A22B-Instruct-2507-FP8   # in tmux, on a node with internet
```

It saves into `$SCRATCH_BASE/vllm/models` (the container's `/models`) and prints the revision.
Put the revision in `scripts/marlowe/env.sh` (`TEACHER_REVISION`) and in the README data card.

## 4. Pilot: 10,000 training items (by October 23)

```bash
sbatch slurm/marlowe/07_teacher.slurm --run-id pilot --samples train --limit 10000
# when it finishes:
source scripts/marlowe/env.sh
$VENV/bin/python scripts/07_report.py --run-id pilot --gpus 8
```

The job starts the vLLM server (tensor parallel 8, max length 4,096, top 20 log probabilities),
waits until it answers, runs the client and stops the server. The server log is
`logs/vllm_server_<jobid>.log`. `07_report.py` writes `data/teacher/pilot/report.json`:
throughput, GPU-hours, GPU-hours per 100k items, label distribution, invalid rate, mean
confidence and the Stage 7 checks.

**Stop and ask** (runbook) before the full run, and also if any check fails:

- any label under 1% or over 90% of keyword-hit items;
- mean confidence under 0.8;
- more than 0.5% invalid outputs (`invalid_top_tokens` in the report shows what the model said instead).

If vLLM fails to start with tensor parallel 8 on the FP8 checkpoint (a block-size divisibility
error in the server log), resubmit with `VLLM_EXTRA="--enable-expert-parallel" sbatch ...`, or
with `VLLM_TP=4`, and record what worked. The full-run GPU-hour estimate is
`gpu_hours_per_100k_items` x 4.075 (407,500 items).

## 5. Full run: 407,500 items

```bash
ARGS="--run-id full --samples train val test test_incident_slice"
J=$(sbatch --parsable slurm/marlowe/07_teacher.slurm $ARGS)
for i in 1 2 3; do J=$(sbatch --parsable --dependency=afterany:$J slurm/marlowe/07_teacher.slurm $ARGS); done
# when the last one finishes (ls data/teacher/full | wc -l: 40 train + 1 val + 1 test + 1 slice shards):
$VENV/bin/python scripts/07_report.py --run-id full --gpus 8 --write-final
```

`preempt` allows 4 hours per job, so the run is a chain: each job starts the server again (count
its load time from the server log), and the client writes 10,000-item shards and skips finished
ones. Set the number of jobs from the pilot's `gpu_hours_per_100k_items`; if shards remain after
the chain, submit the same command again. `--write-final` writes `data/final/teacher_labels.parquet`.

## 6. Back to the Yens

From the Yens (the Globus CLI is set up there):

```bash
source /zfs/projects/darc/marlowe_hackathon/cyber-distill/scripts/globus/env.sh
$GLOBUS transfer "$MARLOWE:$MARLOWE_ROOT/data/teacher" "$YEN:$YEN_ROOT/data/teacher" --recursive \
    --sync-level checksum --verify-checksum --label "cyber-distill teacher labels"
$GLOBUS transfer "$MARLOWE:$MARLOWE_ROOT/data/final/teacher_labels.parquet" \
    "$YEN:$YEN_ROOT/data/final/teacher_labels.parquet" --sync-level checksum --verify-checksum
```

Then the hand check (Stage 8) and the free checks (Stage 9) on the Yens. Student training
(Stage 10) needs `teacher_labels.parquet` on whichever cluster trains; see
[TRAINING_PLAN.md](TRAINING_PLAN.md). Labeling the full corpus with the trained student
(Stage 11) can use the same container with the adapter (`VLLM_ENABLE_LORA=1`,
`VLLM_LORAS="student=/models/<adapter>"`), as in the vllm_helper guide.

## GPU-hours used

From the Marlowe Slurm docs, for the allocation and the go/no-go estimate:

```bash
sreport cluster UserUtilizationByAccount -T gres/gpu Start=<start of billing cycle> End=now \
    account=<our account> -t hours
```

## Tested so far

On one Yen H200 (`reports/run_log.md`): the container setup, the server start and the client with a
small model (Qwen3-1.7B); student training on 1 and 2 GPUs, and resume.

On Marlowe: setup (venv, image) on 2026-10-15; the smoke test (`07_teacher_smoke.slurm`, job 520344)
passed on 2026-10-16 on one H100: no MPS error, compute nodes reach Hugging Face, 400 items with 0
errors and 0 invalid at ~148 items/s, server ready in ~2.5 min. Preempt queue wait was about a day.
Not yet run on Marlowe: the teacher at 8 GPUs, student training, the two-node script.
