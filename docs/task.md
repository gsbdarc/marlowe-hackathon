---
layout: default
title: "The Task and the Data"
nav_order: 2
permalink: /task/
---

# The Task and the Data

## Item 5.02 filings

A public company files a Form 8-K within four business days of a major event. **Item 5.02** covers the departure and
appointment of directors and officers, so every change of CEO since August 2004 has one. Most Item 5.02 filings are
about someone else (a director, a CFO, a pay change), and the ones that are about the CEO rarely say why the CEO left.

## Jev's three questions

**Jev** is TypeSafe's hosted decision model. It reads a document and chooses among fixed options, returning a
probability for each. DARC asked Jev three questions about every Item 5.02 filing (`scripts/questions.py`):

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

`scripts/make_kev_data.py` (run by `slurm/yens/00_data.slurm`) writes three files to `$WORK/data/`:

| File | Records | What |
|---|---|---|
| `train.jsonl` | 54,426 | every CEO change in the train split, plus as many filings that are not CEO changes |
| `valid.jsonl` | 2,000 | from the validation split, half CEO changes |
| `test1000.jsonl` | 1,000 | from the test split: 300 not CEO changes and 700 CEO changes spread across the seven statuses |

Each record is a request in Kev's API format plus Jev's answer. The **target** is Jev's whole probability
distribution, not only its top choice: when Jev was torn between two options, the student learns that too. Filings
that are not CEO changes carry only the status question.

Training drops the 1,669 records whose filing is longer than 2,048 tokens (`--max_state` in `slurm/train_args.sh`),
so each epoch trains on 52,757 records.

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
