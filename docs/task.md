---
layout: default
title: "The Project and the Data"
nav_order: 1
parent: "Start Here"
permalink: /task/
---

# The Project and the Data

When a public company's CEO leaves, the company files an 8-K under **Item 5.02**. A large hosted model, **Jev**, has
read every Item 5.02 filing since 2004, about 300,000 of them, and answered three questions about each: what happens
to the CEO, why, and whether the change was announced in advance.

You will work with open models from the **Kev** family that answer the same questions. Training a Kev model on Jev's
labels, including how confident Jev was, is distillation: a model you run yourself can then label filings at scale on
a GPU you control. During the day you train, label filings at scale, and measure what each costs on the Yens and on
Marlowe.

## Item 5.02 filings

A public company files a Form 8-K within four business days of a major event. **Item 5.02** covers the departure and
appointment of directors and officers, so every change of CEO since August 2004 has one. Most Item 5.02 filings are
about someone else (a director, a CFO, a pay change), and the ones that are about the CEO rarely say why the CEO left.

## Jev's three questions

**Jev** is TypeSafe's hosted decision model. It reads a document and chooses among fixed options, returning a
probability for each. We asked Jev three questions about every Item 5.02 filing (`scripts/questions.py`):

1. **Status:** what happens to the CEO? Not a CEO change, temporary leave, becomes executive chair, becomes
   non-executive chair, stays as a director only, takes another role at the company, leaves the company entirely, or
   an interim CEO steps aside.
2. **Why** the CEO is leaving, judged only from the filing: died, illness, pushed out over performance, dismissed over
   legal or policy violations, retired, new job, other, or no reason given.
3. **Future:** is the change announced in advance?

Status is the main task. Most filings give no reason, so **why** is mostly "no reason given".

## The data

| | Filings | CEO changes |
|---|---|---|
| Item 5.02 filings, August 2004 to October 2026 | 303,146 | |
| Labeled by Jev (`jev-1.14.0`) | 296,477 | 38,162 |
| Train split, filed 2004-2018 | 202,951 | 27,213 |
| Validation split, 2019-2021 | 37,192 | 4,207 |
| Test split, 2022-2026 | 56,334 | 6,742 |

Labeling all 296,477 filings with Jev took about 20 minutes and $19. Each filing is the Item 5.02 section of the 8-K
(no exhibits), a median of 222 words. The data is on the Yens and on Marlowe; it is not in this repository.

Look at it first:

```bash
source env/yens.sh
$PY scripts/look.py --examples 3
```
{: .yens }

## The training files

`setup/setup.sh` builds the training files once on each cluster, with `scripts/make_kev_data.py`, into the class's
shared, read-only `$CLASS_DATA` folder. `env/yens.sh` and `env/marlowe.sh` both set `$CLASS_DATA`, so every task reads
the same files:

| File | Records | What |
|---|---|---|
| `train.jsonl` | 54,426 | every CEO change in the train split, plus as many filings that are not CEO changes |
| `valid.jsonl` | 2,000 | from the validation split, half CEO changes |
| `test1000.jsonl` | 1,000 | from the test split: 300 not CEO changes and 700 CEO changes spread across the seven statuses |

`valid.parquet` and `test1000.parquet` hold the same filings with Jev's answers, for `scripts/score.py`.

Each record is a request in Kev's API format plus Jev's answer. The **target** is Jev's whole probability
distribution, not only its top choice: when Jev was torn between two options, the student learns that too. Filings
that are not CEO changes carry only the status question.

Training drops the 1,669 records whose filing is longer than 2,048 tokens (`--max_state 2048`, set in every training
job), so each epoch trains on 52,757 records.

The test sample oversamples rare statuses so each is measurable, and every filing carries a weight back to the whole
test split. `scripts/score.py` uses the weights to estimate agreement over all 56,334 test filings.

## The student: Kev-4B

[Kev](https://github.com/jaredpalmer/kev) is an open family of Jev-like models built on Qwen, released under Apache
2.0. It comes in four sizes, from 0.8B to 27B parameters. We use **Kev-4B**: Qwen3.5-4B (9.3 GB of weights) plus
Kev's trained adapter and answer head.

How the Kev models agree with Jev before any training, on 1,000 filings:

| Model | Status agreement, all filings (weighted) | Status agreement, CEO changes | Filings per second |
|---|---|---|---|
| Kev-0.8B | 13% | 23% | 18 (A40) |
| **Kev-4B** | **88%** | **58%** | **6 (A40)** |
| Kev-9B | 85% | 73% | 5 (A40) |
| Kev-27B | 96% | 84% | 6 (H200) |

Kev-4B gets the big call right (is this filing about the CEO at all?) and misses many of the finer ones. It is
weakest when the CEO leaves the company entirely: it agrees with Jev on only 20% of those.

{: .note }
> Agreement with Jev measures how well the student copies the teacher. Jev is the reference here, not ground truth.
