# Marlowe hackathon examples on the Yens

Each example lives in its own directory with its own README, requirements, and
Slurm script. Submit jobs from inside the example's directory.

| Directory | What it does |
|---|---|
| `financial_sentiment/` | LoRA fine-tune of Qwen3-4B to label financial news sentences as negative, neutral, or positive (Financial PhraseBank). |
| `cyber-distill/` | Cybersecurity disclosure in 10-K filings, fiscal 1996-2025: a large teacher model on Marlowe labels paragraphs, a small student model learns from them. Runbook and status in its README. |

## Shared setup

- `.venv/`: one shared Python environment (Python 3.11, torch with CUDA). Add a
  new example's packages with `../.venv/bin/pip install -r requirements.txt`.
- Caches go to scratch, not here: `HF_HOME=/scratch/users/$USER/hf_cache`,
  `PIP_CACHE_DIR=/scratch/users/$USER/pip_cache`, `WANDB_DIR=/scratch/users/$USER/wandb`.

## Git

This folder is the repository `gsbdarc/marlowe-hackathon` (private). `.gitignore` is a whitelist:
only listed example directories are tracked. To add an example, check it holds no `.env`,
licensed data (for example CUSIPs) or large files, then add a `!/<dir>/` line to `.gitignore`.
