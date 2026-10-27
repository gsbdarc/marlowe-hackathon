---
layout: default
title: "The Data"
parent: "Beginner Track"
nav_order: 1
permalink: /beginner/data/
---

# The Data

**Goal:** know what you will train on, where Jev's labels come from, and where the files live on the Yens, then get
your first numbers from the test set.

You need the [setup]({{ '/setup/' | relative_url }}) done: Kev installed and the training files built. Every command
below runs from your clone of the repository on the Yens.

```bash
cd /scratch/users/$USER/marlowe-hackathon
source env/yens.sh
```
{: .yens }

---

## The filings and the three questions

When a public company's CEO leaves, the company files a Form 8-K with an **Item 5.02** section. Item 5.02 covers every
change of directors and officers, so most of these filings are about someone else: a new director, a CFO who
retires, a change in pay.

The data is 296,477 Item 5.02 filings from August 2004 to October 2026, each answered by **Jev**, a large hosted model.
Jev answered three questions about every filing:

1. **Status:** what happens to the CEO? One of eight options, from "not a CEO change" to "leaves the company
   entirely". This is the main task.
2. **Why** is the CEO leaving, judged only from the filing? One of eight reasons, including "no reason given".
3. **Future:** is the change announced in advance?

[The Task and the Data]({{ '/task/' | relative_url }}) lists every option and how the filings are split into train,
validation and test years.

## Five filings

Here are five filings from the test years (2022 to 2026) with Jev's answers. The numbers are Jev's probabilities.

### 1. The filing is about someone else

**Remitly Global, filed May 13, 2024** ([on EDGAR](https://www.sec.gov/Archives/edgar/data/1782170/000178217024000140/0001782170-24-000140-index.htm))

> Effective May 13, 2024, Joshua Hug transitioned from his role as the Company's Chief Operating Officer to a new role
> as Vice Chair, in which he will contribute to our company and product strategy and lead other key projects to
> accelerate customer delivery. Mr. Hug will remain on our board of directors. The change to Mr. Hug's title was
> approved by the board of directors on May 9, 2024.

- **Status:** not a CEO change, 1.00

The chief operating officer changes jobs; the CEO is not mentioned. 87% of filings are like this. Jev answers the
other two questions too, but they mean nothing when the CEO stays, so the training files leave them out.

### 2. The CEO leaves for another job

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

The filing came out on December 21 and the CEO leaves on December 31, so the change is announced in advance.

### 3. The CEO retires and becomes executive chair

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

### 4. A close call

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

"Executive Vice Chairman" is neither quite executive chair nor quite another role, and Jev splits its answer. Kev
trains on both numbers, so it learns that this filing is a close call. The filing also reports a change first
announced in an earlier 8-K on January 31, so the same CEO change appears in two filings: the data counts filings,
not events.

### 5. Jev gets it wrong

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

The executive chair died. He had been CEO until earlier that year, but the two co-CEOs stay in their jobs, so the
right status is "not a CEO change". Jev leans the other way, and because Jev's answers are the training targets, Kev
learns to lean that way too.

To print more filings, three CEO changes picked at random:

```bash
$PY scripts/look.py --examples 3
```
{: .yens }

---

## Where the labels come from: Jev and System One

Every label you train on is an answer from Jev. Training Kev means teaching it to give Jev's answers, so it is worth
knowing what Jev is and what DARC asked it.

### A model that makes decisions, not text

Jev is TypeSafe's flagship model and its first **System One** model, which TypeSafe describes as "built to make fast,
structured decisions that software can use directly" ([System One](https://docs.typesafe.ai/concepts/system-one)).
You send it a document, called the **state**, and questions with fixed answers. It does not write a reply. It returns
a probability for every answer.

There are three kinds of question:

| Type | You give | Jev returns | Here |
|---|---|---|---|
| Choice | a set of named options | the most likely option, a probability for each option, and a confidence | status (8 options), why (8 options) |
| Noul | a yes-or-no question | the probability of yes | future |
| Score | ordered levels, lowest to highest | the expected level and a probability for each level | not used |

### What DARC sent Jev

One request per filing. This is the request for OSI Systems (filing 3), shortened: the filing text is cut off, and the
`why` question shows one of its eight reasons. The wording comes from `scripts/questions.py`:

```json
{
  "state": "OSI SYSTEMS INC\nForm 8-K filed 2024-05-03, Item 5.02\n\nOSI Systems, Inc. (the \"Company\") announced today that Chairman and Chief Executive Officer Deepak Chopra has informed the Company's Board of Directors of his plans to retire ...",
  "questions": {
    "status": {
      "type": "choice",
      "instructions": "What happens to the company's chief executive officer, according to this filing?",
      "criteria": {
        "the CEO is not leaving the CEO position (the filing is about someone else)": null,
        "the CEO is stepping away temporarily (medical or other leave) and is expected to return": null,
        "the CEO gives up the CEO title and becomes executive chair": null,
        "the CEO gives up the CEO title and becomes non-executive (independent) chair": null,
        "the CEO gives up the CEO title and stays only as a board member (not chair)": null,
        "the CEO gives up the CEO title but stays at the company in another executive or advisory role": null,
        "the CEO is leaving the company entirely (including death)": null,
        "an interim or acting CEO is stepping aside for a permanent one": null
      }
    },
    "why": {
      "type": "choice",
      "instructions": "If the chief executive is leaving the CEO position, why, according to this filing? Judge only from what the filing says.",
      "criteria": {"the departing CEO retired voluntarily": null}
    },
    "future": {
      "type": "noul",
      "instructions": "Does the change to the CEO position take effect at a future date (announced in advance), rather than immediately or already?"
    }
  }
}
```

Jev answered with a probability for each of the eight statuses (0.93 on executive chair, 0.07 on another role, 0 on
the rest), the same for the eight reasons, and 0.98 for "announced in advance". Those numbers are the columns
`p_status_1` to `p_status_8`, `p_why_1` to `p_why_8` and `p_future` in the data.

The probabilities for one question add up to 1. Jev also reports a **confidence** for each Choice question: 0 when the
probability is spread evenly over the options, 1 when it is all on one. With eight options it is (top probability −
1/8) ÷ (7/8), so OSI's 0.93 is a confidence of 0.92. In the data it is the column `status_conf`.

### Why a decision model and not a chat model?

You could paste each filing into a chat model such as ChatGPT or Claude and ask the same three questions. For labeling
data, a decision model like Jev has advantages:

- **Every answer is one of your options.** A chat model writes text, which you then have to parse, and it can answer
  outside your options or not at all. Jev's answers go straight into a table.
- **A probability for every option.** You can see how sure the model is, and check the unsure filings by hand.
- **The probabilities are meant to be calibrated.** TypeSafe trains Jev so that its probabilities match how often it
  is right: of all the answers it gives 0.8, about 80% should be right. That holds across many answers, not for any
  single one ([TypeSafe's primer](https://docs.typesafe.ai/introduction/machine-learning-primer)).
- **The probabilities are what Kev learns from.** Kev trains on Jev's whole distribution, the **soft label**. A chat
  model's one answer would give only a hard label, and Kev could not learn that Huntington Ingalls (filing 4) is a
  close call.
- **It is cheap to run at scale.** Jev costs $42 per billion input tokens, and output is free
  ([TypeSafe's models](https://docs.typesafe.ai/models)). All 296,477 filings are about 342 million input tokens.
- **Kev speaks the same language.** A Kev server answers the same requests in the same format, so a fine-tuned Kev
  can replace Jev without changing your code ([Key Ideas]({{ '/concepts/' | relative_url }})).

A chat model is still the better tool when the question is open-ended, when you need text pulled out of the document
(a name, a date, a dollar amount), or when you want an explanation.

### Name the version

TypeSafe's alias `jev-latest` points to its newest release, so the same request can get a different answer after an
update. For research, record the version. Every label here came from `jev-1.14.0`, with DARC's questions version
`2026-10-24`, and both are columns in the data (`jev_model`, `jev_questions_version`). The wording of the questions
matters as much: change a word of an option and you change the task.

{: .note }
> Jev is the reference here, not ground truth. A filing Jev gets wrong, like HEICO above, stays wrong in the labels,
> and Kev learns the mistake. Agreement with Jev measures how well Kev copies Jev.

---

## Where the data lives: project space and scratch

`env/yens.sh` sets two folders:

| Variable | Folder | Storage | What is in it |
|---|---|---|---|
| `$DATA` | `/yen/projects/darc/marlowe_hackathon/ceo-turnover/data/jev` | project space | Jev's labeled filings: read only, one copy for everyone |
| `$WORK` | `/scratch/users/$USER/ceo-turnover` | your scratch | the training files setup built, and later your runs and results |

### Scratch is shared storage

Scratch is one large file system, about 100 TB, shared by every Yens user. Every Yen machine sees it: the login node
you type on and the GPU nodes where Slurm runs your jobs. That is why a GPU job can read the training files you built
from the login node, with nothing to copy. Your own folder, `/scratch/users/$USER`, is private to you by default.

Scratch is for working files, not for keeping them. It is not backed up, and files older than 90 days are deleted at
each scheduled downtime, about every two months.

```bash
gsbquota /scratch/users/$USER
```
{: .yens }

```
/scratch/users/<sunet>: currently using 40% (40T) of 100T available
```
{: .output }

The 40 TB is everyone's use, not yours: the space is shared. To see your own, run `du -sh $WORK`.

### Storage on the Yens

| | Path | Size | Kept? | Use it for |
|---|---|---|---|---|
| Home | `/home/users/$USER` | 80 GB | yes | small scripts and settings |
| Project space | `/zfs/projects/...` (also `/yen/projects/...`) | 1 TB for a faculty project, 200 GB for a student project | yes, with snapshots to recover deleted files | data and results you keep and share with your team |
| Scratch | `/scratch/users/$USER` | about 100 TB, shared | no: files older than 90 days are deleted | large working files: model weights, training runs |
| Local `/tmp` | `/tmp` on each node | about 1 TB per node | no: cleared when the job ends | fast, throwaway files inside one job |

[Yen storage on RCpedia](https://rcpedia.stanford.edu/_user_guide/storage/) has the details.

{: .warning }
> Home holds only 80 GB and Kev-4B's weights alone are about 9 GB, so `env/yens.sh` puts Kev, the weights and every cache in
> scratch. After the hackathon, copy anything you want to keep, such as your results or a model you trained, to a
> project space.

---

## Exercises

### Find the test set

Use the terminal for these.

<details class="quiz" markdown="1">
<summary><span class="qnum">1</span><span class="qtext">Where is Jev's labeled data, and how big is it?</span></summary>

```bash
echo $DATA
ls -lh $DATA
```
{: .yens }

```
total 342M
-rw-r--r--+ 1 nrapstin operator  878 Oct 24 10:57 MANIFEST.json
-rw-r--r--+ 1 nrapstin operator  65M Oct 24 10:57 index_8k_items_2004_2026.parquet
-rw-r--r--+ 1 nrapstin operator 3.3M Oct 24 10:57 item502_registrants_v1.parquet
-rw-r--r--+ 1 nrapstin operator 274M Oct 24 10:57 item502_v1.parquet
```
{: .output }

`item502_v1.parquet` is the one you need: 274 MB, every filing with its text and Jev's answers. It is in project
space: you can read it but not change it.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">2</span><span class="qtext">Where is the test set?</span></summary>

In two places. The whole test split, the 56,334 filings from 2022 to 2026, is inside `item502_v1.parquet`: the rows
whose `split` column is `test`. Setup drew a sample of 1,000 of them into your `$WORK/data`:

```bash
ls -lh $WORK/data
```
{: .yens }

```
total 268M
-rw-r--r-- 1 <sunet> operator 6.0M Oct 27 12:09 test1000.jsonl
-rw-r--r-- 1 <sunet> operator 136K Oct 27 12:09 test1000.parquet
-rw-r--r-- 1 <sunet> operator 252M Oct 27 12:09 train.jsonl
-rw-r--r-- 1 <sunet> operator  11M Oct 27 12:09 valid.jsonl
```
{: .output }

`test1000.jsonl` is what Kev reads: one request per line, like the one DARC sent Jev. `test1000.parquet` keeps
Jev's answers for scoring.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">3</span><span class="qtext">Is <code>$WORK</code> backed up? What happens to it in three months?</span></summary>

`$WORK` is in scratch, which is not backed up, and files older than 90 days are deleted at a scheduled downtime. That
is fine for these files, because `slurm/yens/00_data.slurm` rebuilds them in a minute. A model you spent hours
training is worth copying to a project space.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">4</span><span class="qtext"><code>gsbquota /scratch/users/$USER</code> says 100T. Is that your space?</span></summary>

No. Scratch is one pool shared by every Yens user, and `gsbquota` reports the whole pool. `du -sh $WORK` shows what
you use.

</details>

### Describe the test set

Start Python from Kev's environment, which has pandas:

```bash
$PY
```
{: .yens }

Then load the data. It takes a couple of seconds:

```python
import os
import pandas as pd
d = pd.read_parquet(os.path.join(os.environ["DATA"], "item502_v1.parquet"))
d = d[d.labeled]
test = d[d.split == "test"]
```
{: .python-repl }

`d` is every filing Jev answered, one row per filing, and `test` is the rows from the test years. `d.columns` lists
the columns. These are the ones you need:

| Column | What it is |
|---|---|
| `company_name`, `date_filed`, `year` | who filed and when |
| `words`, `text_502` | the length of the Item 5.02 text, and the text |
| `ceo_change` | `True` if Jev's status is anything but "not a CEO change" |
| `status_name`, `status_conf` | Jev's status and its confidence |
| `why_name`, `p_future` | Jev's reason, and the probability the change is announced in advance |
| `jev_model`, `jev_input_tokens` | which Jev answered, and the tokens it read |
| `edgar_url` | the filing on the SEC's website |

<details class="quiz" markdown="1">
<summary><span class="qnum">5</span><span class="qtext">Open the first record of <code>test1000.jsonl</code>. What does Kev read, and what does it learn?</span></summary>

```python
import json
rec = json.loads(open(os.path.join(os.environ["WORK"], "data", "test1000.jsonl")).readline())
rec.keys()
rec["state"][:100]
rec["questions"].keys()
rec["questions"]["status"]["label"]
```
{: .python-repl }

```
dict_keys(['state', 'questions', '_meta'])
'ADVANCED MICRO DEVICES INC\nForm 8-K filed 2023-01-11, Item 5.02\n\nRetirement of Devinder Kumar as Chi'
dict_keys(['status'])
'the CEO is not leaving the CEO position (the filing is about someone else)'
```
{: .output }

The `state` and the `questions` are the request, the same shape DARC sent Jev. Each question also carries Jev's
answer: `label` is its top choice and `target` its probabilities. AMD's CFO is retiring, not the CEO, so the record
has only the status question.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">6</span><span class="qtext">How many filings are in the test split, and how many are CEO changes?</span></summary>

```python
len(test)
test.ceo_change.value_counts()
```
{: .python-repl }

```
56334
ceo_change
False    49592
True      6742
Name: count, dtype: int64
```
{: .output }

56,334 filings, of which 6,742 (12%) are CEO changes.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">7</span><span class="qtext">How many filings are there each year? Why does 2026 have fewer?</span></summary>

```python
test.year.value_counts().sort_index()
test.date_filed.max()
```
{: .python-repl }

```
year
2022    12724
2023    12320
2024    11413
2025    11308
2026     8569
Name: count, dtype: int64
datetime.date(2026, 10, 2)
```
{: .output }

About 11,000 to 13,000 a year. The data ends on October 2, 2026, so 2026 is nine months.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">8</span><span class="qtext">When the CEO changes, what does Jev say happens most often?</span></summary>

```python
ceo = test[test.ceo_change]
ceo.status_name.value_counts()
```
{: .python-repl }

```
status_name
leaves entirely           3192
other role at company     1523
interim steps aside        735
becomes exec chair         563
director only              471
becomes non-exec chair     173
temporary leave             85
Name: count, dtype: int64
```
{: .output }

The CEO leaves the company entirely in 3,192 of 6,742 changes (47%). Only 85 are temporary leaves.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">9</span><span class="qtext">Why do CEOs leave, according to the filings?</span></summary>

```python
ceo.why_name.value_counts()
```
{: .python-repl }

```
why_name
no reason       3799
other           1384
retired         1137
new job          204
illness           79
legal/policy      71
died              61
performance        7
Name: count, dtype: int64
```
{: .output }

Most filings give no reason (3,799 of 6,742, 56%), and only 7 say the CEO was pushed out over performance:
companies rarely write that down. That is why status, not why, is the main task.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">10</span><span class="qtext">How long is a filing?</span></summary>

```python
test.words.describe()
```
{: .python-repl }

```
count    56334.000000
mean       376.334310
std        408.761517
min          0.000000
25%        125.000000
50%        259.000000
75%        476.000000
max      10612.000000
Name: words, dtype: float64
```
{: .output }

Half the filings are under 259 words, about a page. The longest is 10,612 words. The mean (376) is above the median
because a few filings are very long. The minimum is 0: 46 test filings have no Item 5.02 text at all, and Jev
answered them anyway. It is worth looking at data like this before you train on it.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">11</span><span class="qtext">How sure is Jev, on CEO changes and on everything else?</span></summary>

```python
test.groupby("ceo_change").status_conf.mean()
(ceo.status_conf < 0.6).value_counts()
```
{: .python-repl }

```
ceo_change
False    0.979744
True     0.813053
Name: status_conf, dtype: float64
status_conf
False    5398
True     1344
Name: count, dtype: int64
```
{: .output }

Jev is nearly certain when a filing is not a CEO change (average confidence 0.98) and less sure about what happens to
the CEO (0.81). On 1,344 CEO changes, one in five, its confidence is below 0.6: close calls like Huntington Ingalls.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">12</span><span class="qtext">Which Jev answered, and what would the test split cost at today's price?</span></summary>

```python
test.jev_model.value_counts()
tokens = test.jev_input_tokens.sum()
print(f"{tokens:,.0f} tokens, ${tokens / 1e9 * 42:.2f}")
```
{: .python-repl }

```
jev_model
jev-1.14.0    56334
Name: count, dtype: int64
68,057,358 tokens, $2.86
```
{: .output }

Every filing was answered by `jev-1.14.0`. At $42 per billion input tokens, the test split's 68 million tokens cost
about $2.86.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">13</span><span class="qtext">In <code>test1000</code>, 700 of the 1,000 filings are CEO changes, but in the test split only 12% are. Why?</span></summary>

```python
s = pd.read_parquet(os.path.join(os.environ["WORK"], "data", "test1000.parquet"))
s.ceo_change.value_counts()
s.groupby("ceo_change").weight.sum()
```
{: .python-repl }

```
ceo_change
True     700
False    300
Name: count, dtype: int64
ceo_change
False    49592.0
True      6742.0
Name: weight, dtype: float64
```
{: .output }

The sample is drawn on purpose with more CEO changes, and more of the rare statuses, so each can be measured: a
random 1,000 would hold only one or two temporary leaves. Each filing carries a `weight`, the number of test filings
it stands for. Add up the weights and you get the whole test split back: 49,592 and 6,742. When you score Kev-4B on
these 1,000 filings, `scripts/score.py` uses the weights to estimate agreement on all 56,334.

</details>

---

## If you have time

- Find the CEO change Jev was least sure about, among filings of at least 50 words, and read it:
  `print(ceo[ceo.words >= 50].sort_values("status_conf").iloc[0].text_502)`. What would you answer?
- Look up a company you know: `d[d.company_name.str.contains("APPLE", case=False)][["date_filed", "status_name"]]`.

Next, exercise 1 scores Kev-4B on these 1,000 test filings before any training.
