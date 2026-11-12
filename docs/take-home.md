---
layout: default
title: "Take It Home"
nav_order: 10
permalink: /take-home/
---

# Take It Home

Everything in this repository is a template. The CEO-turnover task is one example of a common research pattern: a
large model answers questions about many documents, and you want a small model you run yourself to answer them the
same way, at scale, on your own GPU. To reuse it for your own project, change the documents, the questions and the
labels, then pick the job files that match the scale you need.

## 1. Your documents

`scripts/make_kev_data.py` reads Jev's parquet and builds a **state** for each document with `questions.state()`: the
text the model reads. Point it at your own table and build the state from your own columns. Keep states short: Kev-4B
was trained on states of up to 7,552 tokens and is validated to 8,192.

## 2. Your questions

`scripts/questions.py` defines the questions in the System One request shape that Jev and Kev share:

- `choice`: pick one of several options. The option text is the label, so write each option as a full description.
- `noul`: yes or no.
- `score`: an ordered scale.

Change the instructions and options to your own. The wording is the task: version it, and do not edit it after you
have labels.

## 3. Your labels

Each training record needs a `label` on every question. You can also give a `target`, a probability for each option,
when your labels come from a model that reports them (as Jev's do) or from several human coders who disagree. Kev
trains on the target when there is one.

Labels can come from Jev or another teacher model, from hand coding, or from an existing dataset. Keep a test set the
model never trains on, chosen before you look at results, and split it so the same company or document never appears
on both sides. [A5]({{ '/advanced/a5/' | relative_url }}) shows how to get labels from an open model you serve
yourself.

## 4. The job files

Each job file is one step at one scale. Start from the one closest to what you need:

| You want to | Scale | Job file |
|---|---|---|
| Label documents with a Kev model | 1 Yen GPU | `slurm/yens/serve_and_label.slurm` |
| | 1 H100 | `slurm/marlowe/serve_and_label.slurm` |
| | 8 H100s, one server per GPU, the documents split 8 ways | `slurm/marlowe/intermediate/label_8gpu.slurm` |
| Serve a model too large for one GPU | 8 H100s, each layer split across them | `slurm/marlowe/advanced/a4_serve_qwen235b.slurm` |
| Train a LoRA adapter | 1 Yen GPU | `slurm/yens/intermediate/finetune_kev.slurm` |
| | 1, 4 or 8 H100s, data parallel | `slurm/marlowe/intermediate/lora_1gpu.slurm`, `lora_4gpu.slurm`, `lora_8gpu.slurm` |
| | a 27B model on 1 H100 | `slurm/marlowe/advanced/a3_lora_1gpu.slurm` |
| Train every weight (full fine-tune) | 1 H100 | `slurm/marlowe/intermediate/full_ft_1gpu.slurm` |
| | 8 H100s, sharded with FSDP | `slurm/marlowe/intermediate/full_ft_8gpu.slurm`, `slurm/marlowe/advanced/a2_train_8gpu.slurm` |
| | 2 nodes, 16 H100s | `slurm/marlowe/advanced/a3_train_2node.slurm` |
| Distill a small student from a teacher's labels | 1 H100 | `slurm/marlowe/advanced/a5_train_student.slurm` |

The training settings sit next to the job files: `slurm/marlowe/intermediate/lora.sh` and `full_ft.sh` for Kev-4B,
`slurm/marlowe/advanced/train_27b_args.sh` for the 27B runs. Change the model, learning rate or number of steps there,
so every scale runs the same training.

To run them under your own group's account, change these lines in each Marlowe job file:

- `--account=marlowe-c001` and `--partition=batch` are the class's. Use the account and partition Marlowe gives your
  group when it gets access.
- `--reservation=GSB_Hackathon` on the page's `sbatch` commands works only on the day. Leave it out.
- `--mail-user=<sunet>@stanford.edu`: your own address.
- `env/marlowe.sh` points at the class's shared folders under `/scratch/c001/marlowe-hackathon`. Point `SHARE` and
  `ME` at your group's folders, and run `setup/setup.sh` there to download the models and build Kev.

## Applying for Marlowe

Access starts with the faculty PI. Marlowe's [access page](https://marlowe-research.stanford.edu/access/) has the
current details:

- **Basic Access:** the PI fills in the form personally. It gives a new PI's group 5,000 free GPU-hours for one year,
  in jobs that can be preempted. Students and postdocs run under the PI's allocation.
- **Medium and Large Projects:** up to 10,000 GPU-hours per cycle of about 12 weeks, or more, in jobs that are not
  preempted. A group applies after it has Basic Access. Usage is billed to the PI's research account at Marlowe's
  [recharge rates](https://marlowe-research.stanford.edu/access/#recharge).

A project application ([application guide](https://marlowe-research.stanford.edu/access/application-guide/)) asks for
the shape of your jobs: their wall time, GPUs and nodes, how many run at once, the storage they need, and scaling
evidence, such as the same job timed at more than one scale. Today's runs are short, a few minutes of training rather
than a full run, so their numbers are practice, not your project's figures. Measure your own job the same way:

- **Time per step at 1, 8 and 16 GPUs** (`step_times.py`) is a small scaling study.
- **GPU-hours for a full run:** seconds per step × the steps a full run needs × GPUs ÷ 3,600. `step_times.py` prints
  it for one epoch as `epoch GPU-hours`. For labeling: documents ÷ documents per second × GPUs ÷ 3,600.
- **GPU utilization and peak memory** (`scripts/advanced/gpu_util.py`) show how well the job uses the GPUs it asks for.

Measure on short runs at two or three scales, multiply up to a full run, and add a margin for reruns and tuning.
