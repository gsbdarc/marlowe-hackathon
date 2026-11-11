---
layout: default
title: "The Task and the Data"
nav_order: 2
permalink: /task/
---

# The Task and the Data

## The filings and the three questions

When a public company's CEO leaves, the company files a Form 8-K that includes an **Item 5.02** section, within four
business days. Item 5.02 covers every change of directors and officers, so most of these filings are about someone
else, such as a new director, a CFO who retires, or a change in pay. The ones that are about the CEO rarely say why the
CEO left.

**Jev**, TypeSafe's hosted decision model, answered three questions about 296,477 Item 5.02 filings, from August 2004
to October 2026 (`scripts/questions.py`). Jev reads a filing and chooses among fixed options, giving a probability for
each:

1. **Status.** What happens to the CEO? This is the main task. There are eight possible answers: not a CEO change,
   temporary leave, becomes executive chair, becomes non-executive chair, stays as a director only, takes another role
   at the company, leaves the company entirely, or an interim CEO steps aside.
2. **Why.** Why is the CEO leaving, judging only from the filing? There are eight possible reasons: died, illness,
   pushed out over performance, dismissed over legal or policy violations, retired, new job, other, or no reason
   given. Most filings give no reason, so this is mostly "no reason given".
3. **Future.** Was the change announced in advance?

## Five filings

Here are five filings from the test years (2022 to 2026), with Jev's answers. The numbers are Jev's probabilities.

<details markdown="1">
<summary>1. The filing is about someone else</summary>

**Remitly Global, filed May 13, 2024** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/1782170/000178217024000140/0001782170-24-000140-index.htm))

> Effective May 13, 2024, Joshua Hug transitioned from his role as the Company's Chief Operating Officer to a new role
> as Vice Chair, in which he will contribute to our company and product strategy and lead other key projects to
> accelerate customer delivery. Mr. Hug will remain on our board of directors. The change to Mr. Hug's title was
> approved by the board of directors on May 9, 2024.

- **Status:** not a CEO change, 1.00

The chief operating officer changes jobs, and the CEO isn't mentioned. 87% of filings are like this. Jev answers the
other two questions as well, but they mean nothing when the CEO stays, so the training files leave them out.

</details>

<details markdown="1">
<summary>2. The CEO leaves for another job</summary>

**AgEagle Aerial Systems, filed December 21, 2023** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/8504/000149315223045763/0001493152-23-045763-index.htm))

> On December 17, 2023, AgEagle Aerial Systems Inc. (the "Company") received notice (the "Notice") from Mr. Barrett
> Mooney, the Company's Chief Executive Officer, that he has decided to depart the Company as Chief Executive Officer
> and Director to pursue another professional opportunity, effective December 31, 2023.
>
> The Board of Directors of the Company has retained an executive search firm to recruit a replacement for the Chief
> Executive Officer position.

- **Status:** leaves the company entirely, 1.00
- **Why:** a new job, 0.97
- **Announced in advance:** 0.98

The filing came out on December 21 and the CEO leaves on December 31, so the change was announced in advance.

</details>

<details markdown="1">
<summary>3. The CEO retires and becomes executive chair</summary>

**OSI Systems, filed May 3, 2024** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/1039065/000110465924057065/0001104659-24-057065-index.htm))

> OSI Systems, Inc. (the "Company") announced today that Chairman and Chief Executive Officer Deepak Chopra has
> informed the Company's Board of Directors of his plans to retire from his roles as President and Chief Executive
> Officer by the end of the current calendar year, after the appointment of a successor. Following his retirement as
> President and CEO, Mr. Chopra will continue to work with the Company as Executive Chairman of the Board.
>
> A copy of the press release announcing Mr. Chopra's retirement is attached hereto as Exhibit 99.1 and incorporated
> herein by this reference.

- **Status:** becomes executive chair, 0.93; stays in another role at the company, 0.07
- **Why:** retired, 0.99
- **Announced in advance:** 0.98

</details>

<details markdown="1">
<summary>4. A close call</summary>

**Huntington Ingalls Industries, filed March 4, 2022** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/1501585/000119312522065623/0001193125-22-065623-index.htm))

> On January 31, 2022, Huntington Ingalls Industries, Inc. (the "Company") filed a Current Report on Form 8-K
> disclosing that C. Michael Petters would retire from his position as President and Chief Executive Officer
> (Principal Executive Officer) and transition to his new position as an employee of the Company and Executive Vice
> Chairman of the Board of Directors, effective March 1, 2022. In connection with the transition, Mr. Petters's (i)
> annual base salary was increased from $1 to $770,000, effective February 28, 2022 and (ii) the target amount of his
> 2022 grant of restricted performance stock rights under the Company's 2012 Long-Term Incentive Stock Plan was
> decreased from $4.40 million the prior year to $1.45 million.

- **Status:** becomes executive chair, 0.56; stays in another role at the company, 0.44
- **Why:** retired, 0.82; no reason given, 0.15
- **Announced in advance:** 0.92

"Executive Vice Chairman" isn't quite executive chair and isn't quite another role, so Jev splits its answer between
the two. Kev trains on both numbers, so it learns that this filing is a close call. This filing also reports a change
first announced in an earlier 8-K, on January 31. The same CEO change appears in two filings, because the data counts
filings, not events.

</details>

<details markdown="1">
<summary>5. Jev gets it wrong</summary>

**HEICO, filed September 29, 2025** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/46619/000004661925000064/0000046619-25-000064-index.htm))

> HEICO Corporation (the "Company") regrets to report that Laurans A. Mendelson, Executive Chairman of the Board of
> Directors, passed away on September 27, 2025, at the age of 87. Mr. Mendelson served the Company in numerous
> leadership roles during his tenure, including as Chairman and Chief Executive Officer from 1990 until earlier this
> year. Following Mr. Mendelson's passing, and in accordance with the Company's long-standing succession plans
> previously approved by the Board of Directors, Eric A. Mendelson and Victor H. Mendelson, the Company's Co-Vice
> Chairmen and Co-Chief Executive Officers, were appointed Co-Chairmen of the Board of Directors, effective
> immediately. They will continue to serve as the Company's Co-Chief Executive Officers. [...]

- **Status:** leaves the company entirely, 0.61; not a CEO change, 0.38
- **Why:** died, 0.90

The executive chair died. He had been CEO until earlier that year, but the two co-CEOs keep their jobs, so the right
status is "not a CEO change". Jev leans the other way. Jev's answers are what Kev trains on, so Kev learns to lean
that way too.

</details>

To print three more CEO changes, picked at random, run `scripts/look.py` as shown in [The data](#the-data).

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
