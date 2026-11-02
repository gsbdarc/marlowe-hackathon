---
layout: default
title: "Reference"
nav_order: 11
permalink: /reference/
---

# Reference

## Scripts

| Script | What it does |
|---|---|
| `env/yens.sh`, `env/marlowe.sh` | every path and cache setting; every job sources one |
| `scripts/setup_kev.sh` | installs Kev (commit `53cb0b5`), its Python environment and the Kev-4B weights |
| `scripts/questions.py` | Jev's three questions and the text the model reads |
| `scripts/look.py` | counts and examples from Jev's labels |
| `scripts/make_kev_data.py` | Jev's labels to Kev training records: `train.jsonl`, `valid.jsonl`, `test1000.jsonl` |
| `scripts/label.py` | sends filings to a running Kev server and saves the answers |
| `scripts/score.py` | agreement with Jev on the test sample |
| `slurm/train_args.sh` | the Kev-4B training job the Yens and Marlowe scripts share |

## Slurm on the two clusters

| | Yens | Marlowe |
|---|---|---|
| GPU partition | `gpu`, with `-C GPU_MODEL:H200` for the H200s | `preempt` (basic access), account `marlowe-m000106` |
| GPUs | 2 H200 (141 GB) on yen-gpu4; A40s and A30s on the other GPU nodes | 8 H100 (80 GB) per node |
| Time limit | 1 day | 4 hours on `preempt`; a preempted job is requeued and starts again |
| Memory per CPU | at most 4,000 MB on `gpu` | see `scontrol show partition preempt` |
| Before a GPU job | nothing | `module load slurm mps` |

Common commands:

```bash
squeue --me                          # your jobs
sacct -j <jobid> -o JobID,State,Elapsed,MaxRSS
scontrol show job <jobid>            # why a job is pending, where it runs
scancel <jobid>
tail -f logs/<name>-<jobid>.out
```

## When something goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| A GPU job pends with `ReqNodeNotAvail` or `Resources` | the GPUs you asked for are taken | `squeue -p gpu` shows who holds them; for a quick test, `sbatch -C GPU_MODEL:A40 ...` |
| A gpu-partition job asks for more CPUs than you set | memory above 4,000 MB per CPU raises the CPU count | ask for 4,000 MB or less per CPU |
| `--init_from ... lora is 16 there and 0 here` | full fine-tuning started from the LoRA release | run `slurm/yens/00_merge_kev.slurm` and train from `$WORK/kev-4b-full/checkpoint` |
| `Kev server stopped` | the model failed to load | read `logs/kev-server-<jobid>.log` |
| `CUDA_ERROR_MPS_CONNECTION_FAILED` on Marlowe | MPS not loaded | `module load slurm mps` at the top of the job |
| Disk quota exceeded in home on Marlowe | a cache went to home (32 GB) | source `env/marlowe.sh` before running anything |

## Links

- [Kev](https://github.com/jaredpalmer/kev) and the [Kev-4B model card](https://huggingface.co/jaredpalmer/kev-4b)
- [Marlowe documentation](https://marlowe-research.stanford.edu/documentation/)
- [Yens Slurm guide](https://rcpedia.stanford.edu/_user_guide/slurm/) and [GPUs on the Yens](https://rcpedia.stanford.edu/_user_guide/using_gpu/)
- [SEC Form 8-K, Item 5.02](https://www.sec.gov/about/forms/form8-k.pdf)
