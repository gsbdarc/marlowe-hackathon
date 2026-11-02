---
layout: default
title: "2. Fine-Tune Kev-4B"
parent: "Beginner Track"
nav_order: 3
permalink: /beginner/finetune/
---

# Fine-Tune Kev-4B

**Goal:** know what Kev-4B is made of and what LoRA is, fine-tune Kev-4B's adapter for about 10 minutes on one GPU
(enough for 1% of the training data), and find out which settings make it agree with Jev most often on filings it has
never seen.

You need exercise 1 done: you have scored Kev-4B as released, and you know how fast it labels filings on an A40.
Every command below runs from your clone of the repository on the Yens.

```bash
cd /scratch/users/$USER/marlowe-hackathon
source scripts/beginner/yens.sh
```
{: .yens }

---

## What Kev-4B is made of

Kev-4B is a large model that stays as it is, plus two small trained parts on top. Only the small parts are in the
release, so they are what you download and what you train.

| Part | What it is | Size | Trained here? |
|---|---|---|---|
| Backbone | Qwen3.5-4B-Base: 32 layers (24 linear attention, Gated DeltaNet, and 8 full attention), each 2,560 numbers wide | 4.21 billion numbers, 8.4 GB in bf16 | No: frozen |
| Adapter | LoRA of rank 16 on 12 kinds of matrix in every layer | 32.5 million numbers, 130 MB | Yes |
| Answer head | two small projections that score each answer option | 1.3 million numbers, 5 MB | Yes |
| Temperature | one number that softens the probabilities: 2.41 | 1 | No |

Kev never writes text. It reads the filing, then each question laid out as the instructions, the options, and a final
`<decide>` marker:

```
<state> ADVANCED MICRO DEVICES INC  Form 8-K filed 2023-01-11, Item 5.02 ...
<q> What happens to the company's chief executive officer, according to this filing?
<opt> the CEO is not leaving the CEO position (the filing is about someone else) </opt>
<opt> the CEO is stepping away temporarily (medical or other leave) and is expected to return </opt>
... six more options ...
<decide>
```
{: .output }

The answer head turns the model's state at `<decide>` into a list of 256 numbers (the query) and its state at each
`</opt>` into another (that option's key). Each option scores how closely its key matches the query, and a softmax
turns the scores into probabilities that add up to 1. Dividing the scores by the temperature first makes the
probabilities less extreme; Kev-4B's 2.41 was fitted after its training so that its confidence matches how often it is
right.

---

## What LoRA is

Each layer of the backbone multiplies what comes in, a list of numbers `x`, by a weight matrix `W`. Training the
whole model means changing every `W`: all 4.21 billion numbers. LoRA (low-rank adaptation) keeps `W` frozen and learns
a small correction made of two thin matrices, `A` and `B`:

```
y = W x + (α / r) · B (A x)
```
{: .output }

`A` turns the input into `r` numbers and `B` turns those `r` numbers into a full-size output. `r` is the **rank**: 16
for Kev-4B. `α` is a fixed scale, 32 for Kev-4B, so the correction is doubled.

An example: the MLP's `gate_proj` takes 2,560 numbers in and gives 9,216 out, so its `W` holds 2,560 × 9,216 =
23,592,960 numbers. Its `A` and `B` hold 16 × (2,560 + 9,216) = 188,416, 0.8% of `W`. The same holds across the 12 kinds
of matrix in all 32 layers: 32.5 million numbers, 0.8% of the backbone.

Three things follow:

- **Training starts exactly where Kev-4B left off.** A new `B` starts at zero, so `B · A` adds nothing until training
  moves it. Continuing Kev-4B's own adapter starts from its trained `A` and `B`.
- **Serving costs nothing extra.** When `kev.serve` loads an adapter it adds `(α / r) · B · A` into `W` once, so a
  fine-tuned Kev-4B labels as fast as the one you timed in exercise 1.
- **It needs little memory.** The optimizer, AdamW, keeps two running averages for every number it trains. For the
  33.8 million numbers of the adapter and head, the numbers, their gradients and the averages take 0.54 GB. For all
  4.21 billion they would take 67 GB, more than an A40 holds.

A higher rank gives the adapter more numbers to learn with: rank 4 is 8.1 million, rank 16 is 32.5 million, rank 64
is 130 million. Kev-4B's adapter is rank 16, and continuing it keeps rank 16: the trainer refuses any other rank, since
Kev-4B's `A` and `B` have 16 rows and columns. To try another rank, you train a new adapter from the base model.

---

## How fine-tuning works

Training repeats one **step** until it has used the filings you give it:

1. Take the next filings from `train.jsonl`: 8 per step by default.
2. **Forward:** run each filing and its questions through the model and get the probabilities for each option.
3. **Loss:** compare them with Jev's probabilities. The loss is the cross-entropy, −Σ Jev's probability × log
   Kev's probability. It is lowest when Kev's probabilities match Jev's, including where Jev was unsure.
4. **Backward:** work out how each trained number should change to lower the loss. The gradients flow back through
   the frozen backbone, which stays unchanged, into `A` and `B` in every layer and into the answer head.
5. **Clip:** if the gradients' overall size is above 1.0, scale them down to 1.0, so that one odd filing can't
   throw the adapter off.
6. **Update:** AdamW moves each trained number by a small amount set by the **learning rate**.

The settings around a step:

- **Records per step.** The gradients from several filings are added up before one update. More per step means
  smoother updates, but fewer of them from the same filings.
- **The learning rate changes during the run.** Over the first 10% of steps it climbs from a twenty-fifth of the
  learning rate to the full rate, then falls along a curve to almost zero at the last step. That is why the job works
  out the number of steps before it starts: filings ÷ records per step.
- **Mixed precision.** The job does the arithmetic in bf16, which the A40 runs on its fast tensor cores (exercise 1),
  but keeps the trained numbers in fp32. `WEIGHTS` sets how the frozen backbone is stored: fp32 (16.8 GB), as Kev-4B
  was trained, or bf16 (8.4 GB).
- **Gradient checkpointing** is on. The backward step needs every layer's intermediate results; instead of keeping
  them all, the model keeps a few and recomputes the rest, trading time for memory.

The job continues Kev-4B's adapter with `kev.train`, Kev's own trainer:

```bash
python -m kev.train --data $WORK/data/train.jsonl --init_from jaredpalmer/kev-4b@v1.0 \
  --base Qwen/Qwen3.5-4B-Base --base_revision 1001bb4d826a52d1f399e183466143f4da7b741b \
  --device cuda --dtype bf16 --weights_dtype fp32 --checkpointing 1 --max_state 2048 --seed 0 \
  --lora 16 --lr 2e-5 --batch 1 --accum 8 --max_steps 64 --out $WORK/runs/b2/<jobid>
```
{: .output }

`--max_state 2048` skips the 1,669 filings longer than 2,048 tokens, and `--seed 0` gives every run the same filings
in the same order, so runs differ only in their settings.

---

## What uses GPU memory when training

Training needs what inference needs, plus the gradients and the intermediate results of the backward step. Measured
on an A40 (peak memory PyTorch allocated, 64 steps of 8 filings):

| | fp32 backbone | bf16 backbone |
|---|---|---|
| Frozen weights | 16.8 GB | 8.4 GB |
| Adapter, head, gradients and AdamW | 0.5 GB | 0.5 GB |
| The rest: intermediate results and temporary bf16 copies | 5.0 GB | 3.7 GB |
| **Peak on the GPU** | **22.3 GB** | **12.6 GB** |
| Peak in the node's memory | 26.4 GB | 9.8 GB |
| Minutes to train on 512 filings | 9.2 | 8.6 |

Both fit an A40's 48 GB with room to spare. The fp32 backbone also needs 26 GB of the node's own memory while it
loads, which is why the job asks for 32 GB.

---

## Run it

```bash
sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

The job takes about 17 minutes on an A40. It loads the model and the filings (2 to 3 minutes), trains on 512 filings,
1% of `train.jsonl`, in 64 steps of 8 (9 minutes; see [What 10 minutes covers](#what-10-minutes-covers)), then
serves the new adapter, labels the 2,000 validation filings with it and scores the answers against Jev's (5 minutes).
On an H200 the job trains on 1,920 filings in the same 10 minutes and labels about 3.7 times as fast. Its log is
`logs/ceo-finetune-<jobid>.out`. The parts to read:

```
device=cuda world=1 trainable params=33.8M
dropped 1669 of 54426 records that exceed the training context (2048 state / 2688 branch / 3712 packed tokens)
ep0 step 10/64 loss 0.350 kl 0.000 anchor 0.000 0.957s/rec
ep0 step 20/64 loss 0.468 kl 0.000 anchor 0.000 1.053s/rec
ep0 step 30/64 loss 0.215 kl 0.000 anchor 0.000 1.030s/rec
ep0 step 40/64 loss 0.319 kl 0.000 anchor 0.000 1.033s/rec
ep0 step 50/64 loss 0.243 kl 0.000 anchor 0.000 1.033s/rec
ep0 step 60/64 loss 0.242 kl 0.000 anchor 0.000 1.033s/rec
saved /scratch/users/<sunet>/ceo-turnover/runs/b2/<jobid>
run              GPUs steps  s/step peak GPU GB epoch hours epoch GPU-hours
<jobid>             1    64    8.17        22.3        15.0            15.0
...
               run  answered  status_agree_weighted  status_agree_on_ceo_changes  ceo_change_f1  reason_agree_on_ceo_changes  filings_per_second
<jobid>-valid.jsonl      2000                  0.961                        0.744          0.912                        0.923                7.91
<jobid>-valid.jsonl: status agreement by Jev's status
  not a CEO change         98.9%
  temporary leave          78.6%
  becomes exec chair       83.1%
  becomes non-exec chair   40.0%
  director only            84.4%
  other role at company    70.2%
  leaves entirely          77.8%
  interim steps aside      61.2%
```
{: .output }

- **`trainable params=33.8M`**: the adapter and the answer head. Everything else is frozen.
- **`loss`** is the average over the last 10 steps. It jumps around because each 10 steps see different filings; read
  the trend, not one line. `kl` and `anchor` are extra losses that this job leaves off.
- **`s/rec`** is seconds per filing so far, and **`epoch hours`** is how long one full pass through `train.jsonl`
  would take at this speed.
- **The scores** are the same measures as in exercise 1, on the validation filings. Against Kev-4B as released
  (below), weighted agreement rose from 0.882 to 0.961 and agreement on CEO changes from 0.442 to 0.744.

{: .note }
> Your first training run with each `WEIGHTS` setting compiles its GPU kernels, which adds up to two and a half
> minutes to its first step. Later runs reuse them from `/scratch/users/$USER/.cache/triton`.

---

## The settings

Change one setting at a time, so you know which one made the difference:

| Setting | How to set it | Values | Default |
|---|---|---|---|
| Learning rate | `LR=2e-4 sbatch ...` | any; try 2e-6 to 2e-4 | 2e-5 (2e-4 from scratch) |
| Records per step | `RECORDS_PER_STEP=32 sbatch ...` | 2, 8, 32 | 8 |
| Frozen backbone | `WEIGHTS=bf16 sbatch ...` | fp32, bf16 | fp32 |
| Start from | `INIT=scratch RANK=4 sbatch ...` | `kev` (continue Kev-4B), `scratch` (new adapter, rank 4, 16 or 64) | `kev` |
| GPU | `sbatch -C GPU_MODEL:H200 ...` | A40, H200 | A40 |
| Filings to train on | `FILINGS=1024 sbatch ...` | up to about 1,800 on an A40, 7,000 on an H200 (the job's 45-minute limit) | 512 on an A40, 1,920 on an H200 |

Unless you change `FILINGS`, every run trains for about 10 minutes, whatever the other settings: on 512 filings on an
A40 (9.2 minutes, or 8.6 with the bf16 backbone) and on 1,920 on an H200 (9.4 to 9.8 minutes). The other settings
change what the model learns from those filings, not how long it takes.

To compare two runs side by side, score them together:

```bash
$PY scripts/beginner/score.py $WORK/results/b2/<jobid>-valid.jsonl $WORK/results/b2/<other jobid>-valid.jsonl --sample $WORK/data/valid.parquet
```
{: .yens }

**How big a difference matters.** The 2,000 validation filings are a sample, and a different sample would move every
score a little. Between two runs scored on the same filings, a difference smaller than about 0.005 in weighted
agreement, or 0.03 in agreement on CEO changes, could come from which filings happen to be in the sample. That is
only the sample's noise: training on different filings would move the scores too.

---

## Tune on validation, then test once

Every run is scored on the 2,000 **validation** filings (2019 to 2021). They come from years the model never trains
on, and they are separate from the test filings you scored in exercise 1.

If you tried ten settings and kept whichever scored best on the test filings, part of its score would be luck: you
would have picked the setting that happened to suit those 1,000 filings. The test score would then overstate how well
the model does on new filings. So choose your settings on validation, and score your one chosen adapter on the test
filings once, at the end:

```bash
EVAL=test RUN=$WORK/runs/b2/<jobid> sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

`RUN` scores a run without training it again. Compare its test score with what Kev-4B scored before training, in
exercise 1, on the same 1,000 filings.

{: .warning }
> Compare runs on the same set only. "Agreement on CEO changes" counts every CEO change in the sample equally, and the
> two samples hold different mixes: half of the validation CEO changes are "leaves entirely", against 29% of the test
> ones. Kev-4B as released agrees on 0.442 of the validation CEO changes but 0.587 of the test ones, though it is the
> same model. The weighted agreement stands for the whole split in both: 0.882 and 0.884.

Kev-4B as released, on the validation filings, is the baseline every run is compared with:

| Kev-4B as released, 2,000 validation filings | |
|---|---|
| Agreement, weighted | 0.882 |
| Agreement on CEO changes | 0.442 |
| CEO-change F1 | 0.743 |
| "Leaves entirely" | 21.0% |

To score it yourself: `RUN=jaredpalmer/kev-4b@v1.0 sbatch slurm/yens/beginner/finetune_kev.slurm`.

---

## The room's dashboard

Every job logs to this exercise's project in the hackathon's W&B team,
[Marlowe-Hackathon/exercise-2-finetune](https://forge.coreweave.com/wandb/Marlowe-Hackathon/exercise-2-finetune), under
a name made of your SUNet ID, the GPU and the settings, for example `<sunet>-a40-kev-lr2e-5-rps8-fp32-<jobid>`. Each run
holds the loss every 10 steps, its settings, and its validation scores, named `valid/...`. The System tab shows the GPU's
memory and use. Scoring the run on the test filings (`EVAL=test RUN=...`) adds its test scores, named `test/...`, to the
same run.

---

## What 10 minutes covers

Each run gets about 10 minutes of training, so it can only use a small slice of the training data: 512 of the 52,757
filings in `train.jsonl` on an A40 (1%), or 1,920 on an H200 (3.6%).

| On one GPU | Filings | Share of `train.jsonl` | Training time |
|---|---|---|---|
| One run of this exercise, A40 | 512 | 1% | 9.2 minutes |
| One run of this exercise, H200 | 1,920 | 3.6% | 9.7 minutes |
| One full pass, A40 | 52,757 | 100% | 15.0 hours (13.7 with the bf16 backbone) |
| One full pass, H200 | 52,757 | 100% | 4.4 hours (4.2 with the bf16 backbone) |

The job stops after a set number of filings, not after a set time. The learning rate's schedule needs the number of
steps before training starts, so `FILINGS` is set to what fits in about 10 minutes on the GPU the job lands on: 512
filings at 1.08 seconds each on an A40, 1,920 at 0.31 seconds on an H200. The job's 45-minute limit allows up to about
1,800 on an A40 and 7,000 on an H200. Runs on the same GPU see the same filings, chosen by `--seed 0`. The full-pass
time is the `epoch hours` in your log.

So the scores in this exercise show what a few percent of the data can do. On an A40, weighted agreement on
validation went from 0.882 to 0.961. The H200's extra filings, in the same 10 minutes, mostly helped on CEO changes:
with the default settings, agreement on them rose from 0.744 to 0.840 on validation, while weighted agreement barely
moved (0.961 to 0.962). Neither shows how much a full pass would add. On Marlowe, with many more GPUs, a full pass
becomes practical.

---

## Exercises

### Count what LoRA trains

<details class="quiz" markdown="1">
<summary><span class="qnum">1</span><span class="qtext">How many numbers does LoRA add to <code>gate_proj</code> at rank 4, and at rank 64? How many does the whole model train at each rank?</span></summary>

Each unit of rank adds one row to `A` (2,560 numbers) and one column to `B` (9,216): 11,776 numbers. Rank 4 adds
47,104 to `gate_proj`, 0.2% of its `W`; rank 64 adds 753,664, 3.2%.

For the whole model, a run's log says how many numbers it trains: the adapter plus the answer head's 1.3 million.

```bash
grep 'trainable params' logs/ceo-finetune-<jobid>.out
```
{: .yens }

| Rank | `trainable params` |
|---|---|
| 4 | 9.4M |
| 16 | 33.8M |
| 64 | 131.2M |

Rank 64 trains 16 times as many adapter numbers as rank 4, and still only 3% of the backbone.

</details>

### Compare settings

Each question changes one setting from the default. Run the jobs, then compare their scores with the default run's.
Our answers come from one run of each setting on an A40.

<details class="quiz" markdown="1">
<summary><span class="qnum">2</span><span class="qtext">Does storing the frozen backbone in bf16 instead of fp32 change memory, speed or the answers?</span></summary>

```bash
WEIGHTS=bf16 sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

| | fp32 backbone (default) | bf16 backbone |
|---|---|---|
| Peak GPU memory | 22.3 GB | 12.6 GB |
| Peak node memory | 26.4 GB | 9.8 GB |
| Training time | 9.2 min | 8.6 min |
| Agreement, weighted | 0.961 | 0.961 |
| Agreement on CEO changes | 0.744 | 0.740 |

It saves memory and a little time, and barely changes the answers: the two adapters gave the same status on 1,991
of the 2,000 filings. With mixed precision, the matrix multiplications run in bf16 either way: an fp32 backbone is
rounded to a temporary bf16 copy for each one, so storing it in bf16 only skips those copies. The numbers being
trained, `A`, `B` and the head, stay in fp32 in both runs.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">3</span><span class="qtext">What happens with a learning rate ten times smaller (2e-6) or ten times larger (2e-4)?</span></summary>

```bash
LR=2e-6 sbatch slurm/yens/beginner/finetune_kev.slurm
LR=2e-4 sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

| Learning rate | Agreement, weighted | On CEO changes | Reason | "Temporary leave" | Loss at step 60 |
|---|---|---|---|---|---|
| 2e-6 | 0.938 | 0.636 | 0.890 | 78.6% | 0.304 |
| 2e-5 (default) | 0.961 | 0.744 | 0.923 | 78.6% | 0.242 |
| 2e-4 | 0.962 | 0.706 | 0.888 | 57.1% | 0.212 |

At 2e-6 the steps are too small: in 64 steps the adapter moves only part of the way from Kev-4B as released (0.882
and 0.442). At 2e-4 the weighted agreement matches the default, but agreement on CEO changes and their reasons
falls: the steps are big enough to undo some of what Kev-4B knew. "Temporary leave" fell from 11 of its 14 filings to
8. The training loss can't tell 2e-5 and 2e-4 apart, since it moves more than that from one line to the next;
the validation scores can.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">4</span><span class="qtext">Train on the same 512 filings with 2 or with 32 records per step. Which does better, and which is faster?</span></summary>

```bash
RECORDS_PER_STEP=2 sbatch slurm/yens/beginner/finetune_kev.slurm
RECORDS_PER_STEP=32 sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

| Records per step | Steps | Agreement, weighted | On CEO changes | CEO-change F1 | Reason | Training time |
|---|---|---|---|---|---|---|
| 2 | 256 | 0.961 | 0.802 | 0.946 | 0.947 | 9.3 min |
| 8 (default) | 64 | 0.961 | 0.744 | 0.912 | 0.923 | 9.2 min |
| 32 | 16 | 0.956 | 0.739 | 0.919 | 0.909 | 9.2 min |

Neither is faster: every filing goes forward and backward through the model once whatever the setting, so the GPU
does the same work. What changes is the number of updates. Two per step was the best run we measured: 0.058 more
agreement on CEO changes than the default, well beyond chance, and the only run that did at least as well as Kev-4B
as released on every status. AdamW moves each number by up to about the learning rate at every update, however many
filings went into it, so 256 updates moved the adapter further than 64 or 16. With 32 per step, the model picks
"leaves entirely" more often than Jev does, 536 times against Jev's 509, and "interim steps aside" fell to 47.9%.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">5</span><span class="qtext">Train a new adapter from the base model at ranks 4, 16 and 64. How does it compare with continuing Kev-4B's?</span></summary>

```bash
INIT=scratch RANK=4 sbatch slurm/yens/beginner/finetune_kev.slurm
INIT=scratch RANK=16 sbatch slurm/yens/beginner/finetune_kev.slurm
INIT=scratch RANK=64 sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

| Start from | Rank | Agreement, weighted | On CEO changes | Reason | Peak GPU memory |
|---|---|---|---|---|---|
| Kev-4B as released, no training | 16 | 0.882 | 0.442 | 0.869 | |
| Continue Kev-4B (default) | 16 | 0.961 | 0.744 | 0.923 | 22.3 GB |
| Scratch, learning rate 2e-4 | 4 | 0.946 | 0.655 | 0.920 | 21.9 GB |
| Scratch, learning rate 2e-4 | 16 | 0.953 | 0.642 | 0.897 | 22.3 GB |
| Scratch, learning rate 2e-4 | 64 | 0.950 | 0.626 | 0.729 | 23.9 GB |

A new adapter and a new answer head, trained on 512 filings, already beat Kev-4B as released at every rank. But
continuing Kev-4B's adapter did better still: what Kev-4B had learned before is worth about 0.1 in agreement on CEO
changes here. The rank made no clear difference to agreement: 0.655, 0.642 and 0.626 are within chance of each
other. With only 512 filings, more numbers to learn don't help: rank 64 agreed with Jev's reasons less often and
missed all 14 temporary leaves. Memory hardly grows with rank, since even rank 64 is small next to the backbone.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">6</span><span class="qtext">Which statuses did training help most? Did any get worse?</span></summary>

Read the "status agreement by Jev's status" lines at the end of each log:

| Jev's status | Validation filings | Kev-4B as released | Default | 2 per step |
|---|---|---|---|---|
| not a CEO change | 981 | 93.8% | 98.9% | 98.2% |
| temporary leave | 14 | 78.6% | 78.6% | 78.6% |
| becomes exec chair | 83 | 67.5% | 83.1% | 80.7% |
| becomes non-exec chair | 20 | 40.0% | 40.0% | 65.0% |
| director only | 64 | 76.6% | 84.4% | 87.5% |
| other role at company | 208 | 66.3% | 70.2% | 71.2% |
| leaves entirely | 509 | 21.0% | 77.8% | 85.9% |
| interim steps aside | 121 | 66.9% | 61.2% | 70.2% |

"Leaves entirely" gained most: from 21% to 78%. Kev-4B as released answered "not a CEO change" for 287 of those 509
filings; after the default run, 81 were left. Most other statuses rose too, but in
the default run "interim steps aside" fell, from 66.9% to 61.2%; with 2 per step it rose instead. Small groups move
in big jumps: one temporary leave is 7 points.

</details>

### Test once

<details class="quiz" markdown="1">
<summary><span class="qnum">7</span><span class="qtext">Pick your best setting on validation and score it once on the test filings. How much did 10 minutes of training change Kev-4B?</span></summary>

Of our runs, 2 records per step did best on validation: the same weighted agreement as the default and clearly more
on CEO changes, F1 and reasons. Scored once on the 1,000 test filings:

```bash
EVAL=test RUN=$WORK/runs/b2/<jobid of your best run> sbatch slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

| 1,000 test filings | Kev-4B as released (exercise 1) | After 512 filings, 2 per step |
|---|---|---|
| Agreement, weighted | 0.884 | 0.972 |
| Agreement on CEO changes | 0.587 | 0.844 |
| CEO-change F1 | 0.843 | 0.972 |
| Reason, on CEO changes | 0.826 | 0.917 |
| "Leaves entirely" | 20.9% | 91.7% |

Nine minutes of training on 1% of `train.jsonl` cut Kev-4B's disagreements with Jev by three quarters, from 11.6% of
the test split's filings to 2.8%. Every status rose except "interim steps aside", 84.8% before and 82.8% after, which is 2
of its 99 filings. This is the number to report, because nothing was chosen to suit these filings.

</details>

### More filings in the same time

<details class="quiz" markdown="1">
<summary><span class="qnum">8</span><span class="qtext">Run a setting on an H200, which trains on 1,920 filings in the same 10 minutes. What do 3.75 times as many filings buy, and do the settings still matter as much?</span></summary>

```bash
sbatch -C GPU_MODEL:H200 slurm/yens/beginner/finetune_kev.slurm
```
{: .yens }

Agreement on the validation CEO changes, one run of each setting on each GPU:

| Setting | A40, 512 filings | H200, 1,920 filings |
|---|---|---|
| Default | 0.744 | 0.840 |
| lr 2e-6 | 0.636 | 0.761 |
| lr 2e-4 | 0.706 | 0.856 |
| 2 per step | 0.802 | 0.861 |
| 32 per step | 0.739 | 0.815 |
| bf16 backbone | 0.740 | 0.839 |
| New adapter, rank 4 | 0.655 | 0.856 |
| New adapter, rank 16 | 0.642 | 0.848 |
| New adapter, rank 64 | 0.626 | 0.798 |

Every setting gained, and most of the gaps between them closed: 2 per step, lr 2e-4 and a new rank-4 adapter all
reached 0.856 to 0.861, within chance of each other and of the default. A new adapter trained on 1,920 filings
matches continuing Kev-4B, so what Kev-4B learned before matters less once there is more data. Only lr 2e-6 and rank
64 stayed clearly behind. On the test filings, 2 per step on the H200 reached 0.976 weighted and 0.869 on CEO
changes, against 0.972 and 0.844 on the A40.

</details>

---

## If you have time

- Look at what training wrote: `ls -lh $WORK/runs/b2/<jobid>`. The adapter, `adapter_model.safetensors`, is 130 MB;
  the backbone it adapts is 8.4 GB.
- Train your best setting on twice the filings: add `FILINGS=1024`, and the job trains for about 18 minutes. Does
  validation agreement keep rising?
