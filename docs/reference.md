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
| `scripts/setup_kev.sh` | checks the shared Kev (commit `53cb0b5`) and the models; it never changes Kev. Instructors build Kev with `setup/setup.sh` |
| `scripts/questions.py` | Jev's three questions and the text the model reads |
| `scripts/look.py` | counts and examples from Jev's labels |
| `scripts/make_kev_data.py` | Jev's labels to Kev training records: `train.jsonl`, `valid.jsonl`, `test1000.jsonl` |
| `scripts/label.py` | sends filings to a running Kev server and saves the answers |
| `scripts/score.py` | agreement with Jev on the test sample |
| `slurm/train_args.sh` | the Kev-4B training job the Yens and Marlowe scripts share |

## Slurm on the two clusters

| | Yens | Marlowe |
|---|---|---|
| GPU partition | `gpu`, with `-C GPU_MODEL:H200` for the H200s | `batch`, account `marlowe-c001` |
| GPUs | 2 H200 (141 GB) on yen-gpu4; A40s and A30s on the other GPU nodes | 8 H100 (80 GB) per node |
| Time limit | 1 day | 2 days on `batch` |
| Memory per CPU | at most 4,000 MB on `gpu` | see `scontrol show partition batch` |
| Before a GPU job | nothing | `module load slurm mps` |

Common commands:

```bash
squeue --me                          # your jobs
sacct -j <jobid> -o JobID,State,Elapsed,MaxRSS
scontrol show job <jobid>            # why a job is pending, where it runs
scancel <jobid>
tail -f logs/<name>-<jobid>.out
```

## Reservations

On the day, each cluster holds GPUs for this class only, so your jobs do not wait behind the rest of Stanford. A job
uses them when you add `--reservation=` and the reservation's name after `sbatch`; every command on the track pages
already has it.

| | Yens | Marlowe |
|---|---|---|
| Name | `hackathon` | `GSB_Hackathon` |
| When | Friday, November 13, 9:30 to 18:30 | Friday, November 13, 12:00 to 17:00 |
| What | yen-gpu3 (4 A40s) and yen-gpu4 (2 H200s) | 4 nodes, 32 H100s, on partition `batch`, account `marlowe-c001` |
| Add after `sbatch` | `--reservation=hackathon` | `--reservation=GSB_Hackathon` |

```bash
sbatch --reservation=hackathon <job file>          # on the Yens
sbatch --reservation=GSB_Hackathon <job file>      # on Marlowe
```

- **Before it opens**, a job you submit with the reservation waits in the queue (`PD`) and starts when the reservation
  does. On Marlowe that is the gap from the start of the day to 12:00: submit, and it starts at noon.
- **After it closes**, or after the event, leave `--reservation=...` off. The same job then runs in the normal queue,
  with everyone else's.
- **To see a reservation's hours and nodes**: `scontrol show reservation` (on Marlowe, the reservation is
  `GSB_Hackathon`).
- **The room shares these nodes.** Marlowe's 4 nodes are for everyone in all three tracks, so cancel a job you no
  longer need with `scancel` and its job ID, rather than letting it run to its time limit.

## When something goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| A GPU job pends with `ReqNodeNotAvail` or `Resources` | the GPUs you asked for are taken | `squeue -p gpu` shows who holds them; for a quick test, `sbatch -C GPU_MODEL:A40 ...` |
| A gpu-partition job asks for more CPUs than you set | memory above 4,000 MB per CPU raises the CPU count | ask for 4,000 MB or less per CPU |
| `--init_from ... lora is 16 there and 0 here` | full fine-tuning started from the LoRA release | run `slurm/yens/00_merge_kev.slurm` and train from `$WORK/kev-4b-full/checkpoint` |
| `Kev server stopped` | the model failed to load | read `logs/kev-server-<jobid>.log` |
| `CUDA_ERROR_MPS_CONNECTION_FAILED` on Marlowe | MPS not loaded | `module load slurm mps` at the top of the job |
| Disk quota exceeded in home on Marlowe | a cache went to home (32 GB) | source `env/marlowe.sh` before running anything |
| `Requested reservation is invalid` | the other cluster's reservation name, or the reservation has ended | `hackathon` on the Yens, `GSB_Hackathon` on Marlowe ([Reservations](#reservations)); after it ends, leave `--reservation` off |

## Links

- [Kev](https://github.com/jaredpalmer/kev) and the [Kev-4B model card](https://huggingface.co/jaredpalmer/kev-4b)
- [Marlowe documentation](https://marlowe-research.stanford.edu/documentation/)
- [Yens Slurm guide](https://rcpedia.stanford.edu/_user_guide/slurm/) and [GPUs on the Yens](https://rcpedia.stanford.edu/_user_guide/using_gpu/)
- [SEC Form 8-K, Item 5.02](https://www.sec.gov/about/forms/form8-k.pdf)
