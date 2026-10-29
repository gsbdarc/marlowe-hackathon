---
layout: default
title: "Label with Your Model"
nav_order: 9
permalink: /label/
---

# Label with Your Model

**Goal:** serve your fine-tuned Kev-4B on a Yen H200, score it against Jev on the test sample, and see how fast it
labels filings.

---

## Step 1: Score your model

`serve_and_label.slurm` takes the model to serve and a name for the results. Point it at any finished run:

```bash
sbatch -C GPU_MODEL:H200 slurm/yens/serve_and_label.slurm $WORK/runs/cp1-1gpu cp1
```
{: .yens }

The job starts a Kev server on the GPU, sends it the same 1,000 test filings as the
[zero-shot comparison]({{ '/task/' | relative_url }}), and scores the answers. A run trained on Marlowe works too: copy
its run directory to the Yens with Globus, or use `slurm/marlowe/serve_and_label.slurm` on Marlowe.

## Step 2: Compare with the starting point

```bash
$PY scripts/score.py $WORK/results/kev-4b-zeroshot.jsonl $WORK/results/cp1.jsonl
```
{: .yens }

Did agreement on CEO changes go up? Did "leaves entirely" improve? 100 steps is about 3% of an epoch, so expect a
change, not the whole gap closed. A longer run is how you would close it.

{: .note }
> The test filings are from 2022 to 2026 and the training filings from 2004 to 2018, so a gain here is a gain on
> filings the model has never seen, from years it was not trained on.

## Step 3: Label at scale

The same job labels any set of filings. Give it a third argument, a file in the format of `test1000.jsonl`, or Jev's
parquet itself:

```bash
sbatch -C GPU_MODEL:H200 slurm/yens/serve_and_label.slurm $WORK/runs/cp1-1gpu cp1-all $DATA/item502_v1.parquet
```
{: .yens }

`$WORK/results/cp1-all_summary.json` reports filings per second. At about 6 filings per second, all 296,477 filings
take about 14 hours on one GPU. The job stops at its 2-hour limit; submit the same command again and it carries on,
because `label.py` skips filings already answered. To finish in fewer runs, ask for more time with
`sbatch -t 1-00:00:00 ...` (the `gpu` partition allows up to a day).

{: .warning }
> Run one `serve_and_label` job at a time while you test. The server picks a free port, but every job loads the model
> onto its own GPU, and the Yens' two H200s are shared by everyone in the room.
