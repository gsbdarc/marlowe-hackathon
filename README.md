# Marlowe hackathon examples on the Yens

Each example lives in its own directory with its own README, requirements, and
Slurm script. Submit jobs from inside the example's directory.

| Directory | What it does |
|---|---|
| `financial_sentiment/` | LoRA fine-tune of Qwen3-4B to label financial news sentences as negative, neutral, or positive (Financial PhraseBank). |

## Shared setup

- `.venv/`: one shared Python environment (Python 3.11, torch with CUDA). Add a
  new example's packages with `../.venv/bin/pip install -r requirements.txt`.
- Caches go to scratch, not here: `HF_HOME=/scratch/users/$USER/hf_cache`,
  `PIP_CACHE_DIR=/scratch/users/$USER/pip_cache`, `WANDB_DIR=/scratch/users/$USER/wandb`.
