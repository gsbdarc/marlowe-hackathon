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
(no exhibits), a median of 222 words. The data is on the Yens and on Marlowe, not in this repository:
[Where the data is stored](#where-the-data-is-stored) has the folders.

Look at it first:

```bash
source env/yens.sh
$PY scripts/look.py --examples 3
```
{: .yens }

## The training files

Kev doesn't train on all 296,477 filings Jev labeled. `scripts/make_kev_data.py` draws three files from the three
splits. DARC ran it once for the class data folder, `$CLASS_DATA`; the Intermediate track copies that folder into
`$WORK/data` in I1.

| File | Drawn from | Records | Which filings |
|---|---|---|---|
| `train.jsonl` | train split, 202,951 filings | 54,426 | all 27,213 CEO changes, plus 27,213 of the 175,738 other filings, picked at random |
| `valid.jsonl` | validation split, 37,192 | 2,000 | picked at random from the 4,207 CEO changes and as many other filings, so about half are CEO changes |
| `test1000.jsonl` | test split, 56,334 | 1,000 | 700 CEO changes spread across the seven statuses, and 300 that are not CEO changes |

<style>
.td { margin: 1.25rem 0 1.5rem; }
.td-row { margin: 0 0 0.9rem; }
.td-head { font-size: 0.875rem; line-height: 1.4; margin-bottom: 0.25rem; }
.td-head b { font-weight: 600; }
.td-head span { color: #55524d; }
.td-bar { display: flex; height: 1.5rem; background: #f7f5f2; border: 1px solid #c9c3ba; border-radius: 4px; overflow: hidden; }
.td-ceo { background: #8c1515; }
.td-not { background: repeating-linear-gradient(135deg, #8c1515 0 3px, #ecd0d0 3px 7px); }
.td-ceo-out { background: #ecd0d0; }
.td-key { display: flex; flex-wrap: wrap; gap: 0.4rem 1.25rem; font-size: 0.8125rem; color: #55524d; margin-top: 0.75rem; }
.td-key i { display: inline-block; width: 0.9rem; height: 0.9rem; vertical-align: -0.15rem; margin-right: 0.35rem; border: 1px solid #c9c3ba; border-radius: 2px; }
</style>
<div class="td" role="img" aria-label="Each split drawn to scale, with the part that goes into its file. Train: 54,426 of 202,951 filings, every CEO change and as many other filings. Validation: 2,000 of 37,192. Test: 1,000 of 56,334.">
  <div class="td-row">
    <div class="td-head"><b>Train split</b> 202,951 filings <span>· 54,426 in <code>train.jsonl</code>, 27%</span></div>
    <div class="td-bar" style="width: 100%"><div class="td-ceo" style="width: 13.41%"></div><div class="td-not" style="width: 13.41%"></div></div>
  </div>
  <div class="td-row">
    <div class="td-head"><b>Validation split</b> 37,192 <span>· 2,000 in <code>valid.jsonl</code>, 5%</span></div>
    <div class="td-bar" style="width: 18.33%"><div class="td-ceo" style="width: 2.69%"></div><div class="td-not" style="width: 2.69%"></div><div class="td-ceo-out" style="width: 8.62%"></div></div>
  </div>
  <div class="td-row">
    <div class="td-head"><b>Test split</b> 56,334 <span>· 1,000 in <code>test1000.jsonl</code>, 2%</span></div>
    <div class="td-bar" style="width: 27.76%"><div class="td-ceo" style="width: 1.24%"></div><div class="td-not" style="width: 0.53%"></div><div class="td-ceo-out" style="width: 10.73%"></div></div>
  </div>
  <div class="td-key">
    <span><i style="background: #8c1515"></i>CEO changes in the file</span>
    <span><i style="background: repeating-linear-gradient(135deg, #8c1515 0 3px, #ecd0d0 3px 7px)"></i>other filings in the file</span>
    <span><i style="background: #ecd0d0"></i>CEO changes left out</span>
    <span><i style="background: #f7f5f2"></i>other filings left out</span>
  </div>
</div>

The filings are left out on purpose:

- **Training.** 87% of filings are not CEO changes. With every filing in, most of each training step would go to
  filings that are not about the CEO, the easy call. Keeping as many of those as there are CEO changes means half of
  every step is a CEO change. The other 148,525 filings that are not CEO changes stay unused.
- **Scoring.** To score Kev, you label every filing in the file with it. On an A40, Kev-4B labels the 1,000 test filings
  in about 3 minutes; all 56,334 would take more than 2½ hours. The test sample oversamples rare statuses so each is
  measurable, and every filing carries a weight back to the whole test split: `scripts/score.py` uses the weights to
  estimate agreement over all 56,334 test filings.

Each record is a request in Kev's API format plus Jev's answer. The **target** is Jev's whole probability
distribution, not only its top choice: when Jev was torn between two options, the student learns that too. Filings
that are not CEO changes carry only the status question.

Training also drops the 1,669 records whose filing is longer than 2,048 tokens (`--max_state 2048` in every training
job), so each epoch trains on 52,757 records.

## Where the data is stored

The data lives on the clusters, not in this repository. Before the event, DARC fills a class data folder on each
cluster, `$CLASS_DATA`, with Jev's release (`jev/`) and the five files from [The training files](#the-training-files).
Everyone can read it, and no one can change it. What you make goes in your own work folder, `$WORK`.
`source env/yens.sh` on the Yens, or `source env/marlowe.sh` on Marlowe, sets both:

| | Yens | Marlowe |
|---|---|---|
| Class data, `$CLASS_DATA` | `/scratch/shared/marlowe_hackathon/data` | `/scratch/c001/marlowe-hackathon/data` |
| Your work folder, `$WORK` | `/scratch/users/<sunet>/ceo-turnover` | `/scratch/c001/users/<sunet>/ceo-turnover` |

The Advanced track reads the class data in place. The Intermediate track copies it into `$WORK/data` first, in
[I1]({{ '/intermediate/i1/' | relative_url }}#copy-the-data).

### Scratch is shared storage

Scratch is one large file system, about 100 TB, shared by everyone who uses the Yens. Every Yen machine can see it,
both the login node you type on and the GPU nodes where Slurm runs your jobs. So a GPU job can read files you made
or copied from the login node, without copying them again. Your own folder, `/scratch/users/$USER`, is private to
you by default.

Use scratch for working files, not for keeping things. It isn't backed up, and at each scheduled downtime, about every
two months, files older than 90 days are deleted.

```bash
gsbquota /scratch/users/$USER
```
{: .yens }

```
/scratch/users/<sunet>: currently using 40% (40T) of 100T available
```
{: .output }

The 40 TB is everyone's use, not just yours, because the space is shared. To see your own, run `du -sh $WORK`.

### Storage on the Yens

| | Path | Size | Kept? | Use it for |
|---|---|---|---|---|
| Home | `/home/users/$USER` | 80 GB | yes | small scripts and settings |
| Project space | `/zfs/projects/...` (also `/yen/projects/...`) | 1 TB for a faculty project, 200 GB for a student project | yes, with snapshots to recover deleted files | data and results you keep and share with your team |
| Scratch | `/scratch/users/$USER` | about 100 TB, shared | no: files older than 90 days are deleted | large working files: model weights, training runs |
| Local `/tmp` | `/tmp` on each node | about 1 TB per node | no: cleared when the job ends | fast, throwaway files inside one job |

[Yen storage on RCpedia](https://rcpedia.stanford.edu/_user_guide/storage/) has the details.

{: .warning }
> Home holds only 80 GB, and Kev-4B's weights alone take about 9 GB. That is why `env/yens.sh` puts Kev, its weights
> and every cache in scratch. After the hackathon, copy anything you want to keep, such as your results or a model you
> trained, to a project space.

### Storage on Marlowe

Marlowe's scratch is shared the same way: the login nodes and every compute node see the same files. Each project
has its own folder in it. The class's project is `c001`, so everyone at the hackathon shares `/scratch/c001`:
DARC's class folder is `/scratch/c001/marlowe-hackathon`, and yours is `/scratch/c001/users/<sunet>`.

| | Path | Size | Kept? | Use it for |
|---|---|---|---|---|
| Home | `/users/$USER` | 32 GB | yes, backed up every 24 hours | small scripts and settings, not large files or conda environments |
| Project space | `/projects/<project-ID>` | set by the project's allocation, and billed separately | yes, backed up every 24 hours | final results you keep and share with your project |
| Scratch | `/scratch/<project-ID>`, here `/scratch/c001` | 10 TB for a project by default, shared by everyone in it | no: not backed up, and files may be purged | large working files: model weights, training runs |
| Node-local scratch | `/local_scratch/$USER.$SLURM_JOB_ID` | not stated in the Marlowe docs | no: wiped when the job ends | fast, throwaway files inside one job |

To see how much of the class's scratch is in use, and how much is yours:

```bash
module load marlowe-scripts
storage-quota /scratch/c001
du -sh $WORK
```
{: .marlowe }

As on the Yens, `storage-quota` reports the whole project, everyone's files, and `du -sh $WORK` reports only yours.
[Filesystems](https://marlowe-research.stanford.edu/documentation/getting-started/filesystems/) in the Marlowe
documentation has the details.

{: .warning }
> Home holds only 32 GB. That is why `env/marlowe.sh` puts code, weights, caches and runs in `/scratch/c001`. Scratch
> isn't backed up, so copy anything you want to keep to a project space.

Two questions about scratch:

<details class="quiz" markdown="1">
<summary><span class="qnum">1</span><span class="qtext">Is <code>$WORK</code> backed up? What happens to it in three months?</span></summary>

`$WORK` is in scratch, which isn't backed up, and files older than 90 days are deleted at a scheduled downtime. That
includes any copy of the class data you made, which is no real loss: you can copy it again from `$CLASS_DATA`, as in
[I1]({{ '/intermediate/i1/' | relative_url }}#copy-the-data). A model you spent hours training is worth copying to a project
space.

</details>

<details class="quiz" markdown="1">
<summary><span class="qnum">2</span><span class="qtext"><code>gsbquota /scratch/users/$USER</code> says 100T. Is that your space?</span></summary>

No. Scratch is one pool shared by everyone on the Yens, and `gsbquota` reports the whole pool. `du -sh $WORK` shows
what you use.

</details>

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
