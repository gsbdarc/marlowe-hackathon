# Student training plan (Stage 10 and the hackathon checkpoints)

The student learns the teacher's labels so that one Yen GPU can label every keyword-hit paragraph
from 30 years of 10-Ks. The same script, `scripts/10_train_student.py`, runs every hackathon
checkpoint; only the number of GPUs and the training size change.

## Model and objective

| Item | Choice | Why |
|---|---|---|
| Base model | `Qwen/Qwen3-1.7B` | Runbook; small enough for one GPU at inference, same family and tokenizer as the teacher |
| Input | The teacher's prompt (`config/prompt_v1.txt`: section heading, previous paragraph, paragraph) through the chat template with `enable_thinking=False` | Student and teacher see the same thing, so their answers compare directly |
| Target | One letter, A-E (NONE, RISK, GOVERNANCE, INCIDENT, PRODUCT) | Runbook codebook |
| Loss | Cross-entropy over the five letter logits at the answer position only | The runbook's "loss on the answer letter only"; keeping one position's logits keeps memory small |
| Optional variant | `--soft`: KL divergence to the teacher's five probabilities | Runbook Stage 10 step 5; kept separate from the main runs |
| Training rows | `use_for_training = true` (teacher confidence at least 0.7, valid output) | Runbook |
| Adapter | LoRA, rank 16, alpha 32, dropout 0.05, on all attention and MLP projections | Proposed values for the runbook's `{{FILL}}`; confirm or tune on the 25k run |
| Optimizer | AdamW, learning rate 2e-4, cosine schedule with 3% warm-up, gradient clipping 1.0 | Common LoRA settings |
| Batch | 16 per GPU, global batch 128 kept fixed by gradient accumulation | Results comparable across GPU counts, so the scaling table measures speed only |
| Length | Up to 1,536 tokens (prompts are under about 1,200) | Paragraphs are at most 400 words, context at most 150 |
| Epochs | 1 | 400k one-letter examples; check the 25k curve first |
| Model selection | Best validation macro F1 against the teacher, evaluated every 500 steps | Runbook |
| Seed | 20261106 | Same as the samples |

## Checkpoints

| # | Where | GPUs | Training rows | Command | What participants learn |
|---|---|---|---|---|---|
| 1 | Yens | 1 H200 | 25,000 (`in_25k`) | `sbatch slurm/10_student_yens.slurm --size 25k --name ckpt1` | A full fine-tune on one GPU; score on the test set |
| 2 | Yens | 4 H200 (one node) | 25,000 | `sbatch --gres=gpu:4 --cpus-per-task=60 --mem=240G slurm/10_student_yens.slurm --size 25k --name ckpt2-4gpu` | Scaling: seconds per step and samples per second from `timing.json` for 1 vs 4 GPUs, turned into a GPU-hour estimate for a Marlowe application |
| 3 | Marlowe | 1 H100 | 25,000 | `sbatch slurm/marlowe/10_student.slurm --size 25k --name ckpt3` | Same job on Marlowe; time per step H100 vs H200 |
| 4 | Marlowe | 8 H100 (one node) | 200,000 (`in_200k`) | `sbatch -G 8 --exclusive slurm/marlowe/10_student.slurm --size 200k --name ckpt4` | Data-parallel training on a full node |
| 5 | Marlowe | 16 H100 (two nodes) | 400,000 | `sbatch slurm/marlowe/10_student_2node.slurm --size 400k --name ckpt5`, then the same with `--resume` | Multi-node training and resuming from `checkpoint-last` |

For timing-only runs (for example the scaling table), add `--max-steps 100`.

Each run writes `runs/<name>/`: `best_adapter/`, `checkpoint-last/` (adapter, optimizer,
scheduler, step), `metrics.jsonl` (validation macro F1, accuracy, per-label F1) and `timing.json`.

## Before November 13 (DARC)

1. After the teacher full run: train the three sizes once (checkpoints 1, 4, 5 settings) to check
   the curves, pick the final LoRA settings and record training time per size in the data card.
2. Fill the runbook `{{FILL}}`s: LoRA rank and alpha, training time per size.
3. Dry run of every checkpoint (November 9-11) with the participant instructions.
4. Choose the best student by validation macro F1 for Stage 11 (full-corpus labeling on one H200)
   and Stage 12 (evaluation against the teacher and the hand labels).

## Watch for

- **INCIDENT is rare.** Enrichment added only 6,556 incident-like paragraphs (1.6% of training).
  Check per-label F1 in `metrics.jsonl`; if INCIDENT F1 is low, consider class weights or
  oversampling INCIDENT in a separate run, and report it as a variant.
- **Teacher errors pass to the student.** Compare student and teacher on the hand-checked
  paragraphs (Stage 12), not only student against teacher.
- **Multi-node runs** need DARC's go-ahead (runbook ground rule 5).

## Tested so far

On Yen H200s (see `reports/run_log.md`): `scripts/10_train_student.py` on 1 GPU and on 2 GPUs (DDP),
then resumed from `checkpoint-last`, with throwaway labels; `scripts/07_teacher.py` against the vLLM
container with Qwen3-1.7B on 400 items. The Marlowe Slurm scripts have
not run yet: they need the account and partition, and the multi-node script has not been tried.
