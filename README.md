# Cyber Disclosure Labeling: Agent Runbook

Runbook for an AI coding agent (or a person) preparing the cybersecurity exercise for the Marlowe hackathon on November 13, 2026. It describes the data, the labeling codebook, each pipeline stage with its checks, and a data card the agent fills in as it works.

Owner: DARC, Stanford GSB (nrapstin@stanford.edu). Last updated: 2026-10-13. Runbook version: v2 (v1 plus the changes listed under Changes from v1). The copy in the project directory on the Yens is the master; the Drive copy is a snapshot.

## How to use this file

- Work through the stages in order. Each stage lists its inputs, outputs and checks.
- Fill every `{{FILL}}` marker in the Data card section when you finish the stage that produces it. If you cannot fill one, write `UNKNOWN (reason)`. Never estimate a number you can measure.
- Run `grep -n "{{FILL" README.md` to list what is left.
- Log every command you run, with the date and the git commit, in `reports/run_log.md`.
- Every step is a script in `scripts/` or `slurm/` and appears under Reproduce from scratch. No step is run by hand outside a script. If you need a new step, add a script and list it there.
- Stop and wait for a person at every **Stop and ask** point. The full list is near the end of this file.

## Reproduce from scratch

Run from the project root, `/zfs/projects/darc/marlowe_hackathon/cyber-distill`. Each line lists where it runs and how long it took.

```bash
# Setup, once
../.venv/bin/pip install -r requirements.txt
echo 'REDIVIS_API_TOKEN=<token with the data scope>' > .env && chmod 600 .env
mkdir -p logs
bash scripts/globus/setup.sh          # in your own terminal: Globus login and consent (interactive)
bash scripts/globus/mkdirs.sh         # creates the Marlowe directories

# Stage 0: filing lists from Redivis (login node, ~1 min)
../.venv/bin/python scripts/00_query_redivis.py

# Stage 1: headers, then selection
sbatch slurm/01_headers.slurm         # array of 31 tasks, filing years 1996-2026, <2 min each
../.venv/bin/python scripts/01_select.py   # login node, ~1 min, after the array finishes

# Transfers to Marlowe (any time after the files exist)
bash scripts/globus/push.sh data/final
```

Outputs are deterministic given the same Redivis table version (`v3_206`) and mirror contents. `data/interim/*.json` records the query and its time.

## Changes from v1

| Where | v1 said | Now | Why |
|---|---|---|---|
| Forms | 10-K, 10-K405, 10-KSB, 10-KSB40, 10-KT | Also `10KSB`, `10KSB40`, `10KT405`, `10QSB` (no hyphen) | The Redivis table and the SEC headers code small-business forms without a hyphen. `10-KSB` matches 1 filing; `10KSB` matches 36,912 |
| Stage 0 | Count from the index files in `/zfs/tools/darc/edgar_https/data/index/` | Count from the Redivis table `stanfordgsblibrary.edgar_filings` (v3_206), whose `filepath` column is the path on the Yens | Same source as the 13F exercise, versioned, and gives paths directly |
| Stage 1, fiscal year | Fiscal year from `CONFORMED PERIOD OF REPORT` | Same, but Redivis has only the filing year, so the headers of all filings from filing years 1996-2026 are read and fiscal year is set from the header | Redivis has no period of report, SIC or state |
| Stage 1, Item 1.05 | Header lists Item 1.05 | Header writes it as `ITEM INFORMATION: <ITEMS>1.05`, without a name; match that or the name | Matching the name "Material Cybersecurity Incidents" finds none |
| Stage 1, SIC | SIC from the header | SIC from the header, filled from the same CIK's most common SIC when missing; `sic_from_header` flags which | About 25% of fiscal 2000 headers have no SIC line |
| Stage 1, joint filings | Not covered | One accession listed under several CIKs (utility and subsidiaries, REIT and operating partnership, ABS trust and depositor) is kept once, under the CIK with the most selected annual reports, then the lowest CIK | Otherwise the same document counts several times |

## Goal

Label 10-K paragraphs from fiscal years 1996 to 2025 with one of five cybersecurity labels, using a small model that runs on one Yen GPU. The small model (the student) learns from labels produced by a large model (the teacher) on Marlowe. The labels feed descriptive plots of how cyber disclosure changed over time.

The plots are a teaching demo. Do not describe them as a new research measure or draw causal conclusions from them.

## Ground rules

1. The EDGAR mirror is read-only. Never write, move or delete anything under `/zfs/data/NODR/EDGAR_HTTPS/` or `/zfs/tools/darc/edgar_https/`.
2. Write only inside the project directory (see Project layout).
3. Run anything longer than a few minutes as a Slurm job, never on a login node.
4. Size Slurm requests to the job. On the Yen GPU partition, Slurm assigns CPUs from requested memory at about 3.9 GB per CPU, so a large `--mem` with few CPUs can reserve a whole node and wait hours to start. Set `--mem` close to what the job uses.
5. Stop and ask before any job expected to use more than {{FILL: GPU-hour limit agreed with DARC}} GPU-hours, any multi-node Marlowe job, and any job outside the reserved hackathon nodes.
6. All labeling runs on open models on Marlowe or the Yens. Do not call commercial model APIs.
7. Do not fill in the hand-check labels. Two DARC staff members do that.
8. Once the company split exists (Stage 5), never regenerate it.
9. Pin package versions and record them in `reports/environment.md`.
10. Raw EDGAR files never leave the Yens. Only the files in `data/final/` and `config/` go to Marlowe.

## About the data

All text comes from SEC EDGAR, the SEC's free public database of company filings. DARC mirrors EDGAR on the Yens.

**Forms used**

| Form | What it is | Used for |
|---|---|---|
| 10-K, 10-K405, 10KSB, 10KSB40, 10-KT, 10KT405 | Annual report. 10-K405 ended in 2002 and 10-KSB was phased out by 2009; both are annual reports and are treated as 10-Ks here. 10-KT is a transition-period report. Small-business forms are coded without a hyphen in the mirror. | Paragraphs for training and for every plot |
| 10-Q, 10QSB, 10-QT | Quarterly report | Only the first 10-Q or 10-K after each Item 1.05 8-K, for the Item 1.05 check and plot 6 |
| 8-K | Current report on a material event | Item 1.05 and Item 8.01 sections, for plots 5 and 6 |

Amendments (forms ending in `/A`) are excluded.

**Sections that matter in a 10-K**

| Section | Content | Present from |
|---|---|---|
| Item 1A, Risk Factors | Most cyber RISK paragraphs | Fiscal years ending on or after December 1, 2005 |
| Item 1C, Cybersecurity | Cyber risk management and board oversight (mostly GOVERNANCE) | Fiscal years ending on or after December 15, 2023 |
| Item 7, MD&A | Some INCIDENT paragraphs (costs, effects on results) | All years |

**8-K items**

- Item 1.05, Material Cybersecurity Incidents: required since December 18, 2023 (June 15, 2024 for smaller reporting companies). The header writes it as `<ITEMS>1.05`.
- Item 8.01, Other Events: since May 2024 SEC staff guidance, companies are encouraged to report incidents they have not found material here instead of under Item 1.05.
- The filing header lists the items in each 8-K (`ITEM INFORMATION` lines), so no text parsing is needed to find Item 1.05 filings.

**Formats change over time.** Most filings before about 2001 are plain text. HTML takes over in the early 2000s, and inline XBRL (HTML with embedded XBRL tags) is phased in from 2019 by filer size. The extractor must handle all three, and every check below is reported by fiscal year so that a format problem in one era shows up.

**Header fields to keep:** accession number, CIK, company name, form type, filing date, `CONFORMED PERIOD OF REPORT`, SIC code and state of incorporation.

## Clusters and paths

| What | Where |
|---|---|
| EDGAR mirror (filings) | `/zfs/data/NODR/EDGAR_HTTPS/` (Yens) |
| EDGAR filing indexes | `/zfs/tools/darc/edgar_https/data/index/` (Yens) |
| Filing list with paths | Redivis `stanfordgsblibrary.edgar_filings` v3_206; token in `.env` (`REDIVIS_API_TOKEN`, data scope) |
| Mirror documentation | https://github.com/gsbdarc/edgar-yens-mirror |
| Yens project directory | `/zfs/projects/darc/marlowe_hackathon/cyber-distill` |
| Yen GPU partition name | `{{FILL}}` |
| Marlowe project directory | `/scratch/m000106/gsb_hackathon/cyber-distill` (`data/final`, `data/interim`, `data/teacher`, `models`, `config`) |
| Marlowe Slurm account and partition | `{{FILL}}` |
| Marlowe model cache (shared, or our own directory) | `{{FILL}}` |
| Transfer method, Yens to Marlowe, and the command used | Globus CLI 3.43.0. Yens collection "GSB/DARC yen" `2556f515-7a87-407b-a24d-18ed16237588` (full `/zfs` paths); Marlowe collection "Marlowe /scratch directories" `56ac92ca-0bad-4009-baaa-513525b3e648`, whose root is `/scratch`, so `/scratch/m000106/...` is `/m000106/...` in Globus. Command: `bash scripts/globus/push.sh <path>` (checksum sync, MANIFEST.sha256 per directory) |

Read the mirror documentation before Stage 0 and describe the directory structure in the Data card.

| Stage | Cluster | Hardware |
|---|---|---|
| 0 to 6, data prep | Yens | CPU |
| 7 to 9, teacher labeling and checks | Marlowe | 1 node, 8 H100 GPUs |
| 10, student training | Marlowe | 1 GPU up to 2 nodes |
| 11, full-corpus labeling | Yens | 1 H200 GPU |
| 12 and 13, evaluation and plots | Yens | CPU |

## Project layout

```
cyber-distill/
  README.md              this file
  requirements.txt       pinned packages
  .env                   Redivis token (not in git)
  config/
    keywords.yaml        prefilter terms (Stage 4)
    codebook.md          copy of the Codebook section, versioned
    prompt_v1.txt        teacher prompt (Stage 7)
  scripts/               one script per stage, 00_query_redivis.py to 13_plots.py
    globus/              setup.sh, mkdirs.sh, push.sh, env.sh
  slurm/                 one job script per stage that runs under Slurm
  data/                  (not in git)
    interim/             large intermediate files, safe to delete and rebuild
    final/               the files listed under Data files
  logs/                  Slurm logs (not in git)
  reports/
    run_log.md
    environment.md
    data_report.md       per-year tables from every stage
    plots/               PNG plus the CSV of plotted values for each plot
```

## Codebook

Each paragraph gets one label, no more. The models score the answer letter.

| Letter | Label | Definition |
|---|---|---|
| A | NONE | Not about cybersecurity. |
| B | RISK | Cyber threats described as possible future harm to the company. |
| C | GOVERNANCE | How the company manages cyber risk: security leadership, board or committee oversight, frameworks such as NIST, audits, training, insurance, incident response plans. |
| D | INCIDENT | A specific cybersecurity incident that happened to the company, or to a vendor in a way that affected the company. It gives at least one concrete detail: when it happened, the system or data affected, a consequence, or the response. |
| E | PRODUCT | Cybersecurity products or services the company sells, or the market for them. |

If a paragraph fits more than one label, choose in this order: INCIDENT, GOVERNANCE, RISK, PRODUCT, NONE.

**Edge cases**

| Example text | Label | Rule |
|---|---|---|
| We have experienced cyberattacks in the past, none of which were material. | RISK | No specific incident. |
| In March 2025, a breach at our payroll vendor exposed employee Social Security numbers, and we notified affected employees. | INCIDENT | Vendor incident that affected the company. |
| A breach of the financial covenants in our credit agreement could result in an event of default. | NONE | Contract or covenant breach. |
| The virus and related restrictions reduced store traffic during 2020. | NONE | Disease. |
| We have completed Year 2000 readiness testing of our computer systems. | NONE | Date-handling problem with no attacker. |
| A global IT outage caused by a faulty software update disrupted our operations. | NONE | No malicious actor. DARC decision; revisit after the hand check. |
| We are subject to privacy laws such as the GDPR and the CCPA. | NONE | Privacy compliance with no security content. |
| Privacy laws require us to notify customers if their data is breached. | RISK | Security content present. |
| We maintain cyber liability insurance. | GOVERNANCE | Insurance is risk management. |
| A security software company describing a breach of its own systems | INCIDENT | Label what happened, not what the company sells. |

Any codebook change after Stage 7 starts means relabeling. Bump the version (`codebook_v2`, `prompt_v2.txt`) and log the change.

## Pipeline

### Stage 0. Inventory the mirror (Yens, CPU)

Script: `scripts/00_query_redivis.py`.

1. Read the mirror documentation and record the directory structure in the Data card.
2. From the Redivis filing list, count filings by form type and filing year for every form in About the data, including amendments. Save the lists to `data/interim/edgar_index_{10k,10q,8k}.parquet`, each with a JSON record of the SQL, table version, query time and counts.
3. Write the counts to `reports/data_report.md` as a table with one row per year.

**Check:** counts should change smoothly from year to year. List any year that is missing or more than 30% below its neighbors.

### Stage 1. Select filings (Yens, CPU)

Scripts: `scripts/01_headers.py` (Slurm array `slurm/01_headers.slurm`, one task per filing year), then `scripts/01_select.py`.

1. Annual reports: keep the 10-K family, drop amendments.
2. Fiscal year is the calendar year of `CONFORMED PERIOD OF REPORT`. Keep fiscal years 1996 to 2025.
3. Keep one annual report per CIK per fiscal year. If there are several, keep the earliest-filed original and count the rest as dropped. Keep a jointly filed accession once (see Changes from v1).
4. 8-Ks: all 8-Ks filed on or after December 18, 2023 whose header lists Item 1.05 or Item 8.01.
5. 10-Qs: for each Item 1.05 8-K, the same company's first 10-Q or 10-K filed after it.
6. Output `data/final/filings.parquet` (schema under Data files) and `data/interim/select_stats.json`.

### Stage 2. Extract text (Yens, CPU)

1. Use the main document only: the document in the submission whose type matches the form type. Skip exhibits.
2. Convert HTML and inline XBRL to text. Remove the hidden inline XBRL header block. Keep plain-text filings as they are.
3. Remove page numbers, running headers and footers, and table of contents lines.
4. Drop tables where more than half of the cells are numbers. Keep text tables.
5. Record each failure with its accession number and reason in `data/interim/parse_failures.csv`.

**Check:** report the failure rate by fiscal year. **Stop and ask** if any year is above 5%.

### Stage 3. Paragraphs and sections (Yens, CPU)

1. Split on blank lines and block-level HTML elements. In plain-text filings, join lines that were wrapped mid-sentence.
2. Keep paragraphs of at least 15 words. Split paragraphs longer than 400 words at sentence boundaries into chunks of at most 400 words.
3. Assign a section: `1A`, `1C`, `7` or `OTHER`. Match Item headings with a pattern that skips the table of contents (use the heading that is followed by substantial text, not the first match).
4. For each paragraph, store the nearest heading above it and the previous paragraph (truncated to 150 words).
5. Store a SHA-1 hash of the normalized text for deduplication.
6. Output `data/interim/paragraphs.parquet`.

**Check:** report section detection rates by fiscal year. **Stop and ask** if Item 1A is found in fewer than 80% of filings from fiscal 2006 on, or Item 1C in fewer than 80% from fiscal 2024 on.

### Stage 4. Keyword prefilter (Yens, CPU)

The prefilter cuts the volume the models need to label. Trap terms are included on purpose so the models see the hard cases.

`config/keywords.yaml`:

```yaml
core:
  - cyber          # prefix match: cybersecurity, cyberattack, cyber-attack
  - hack           # prefix match: hacker, hacking, hacked
  - ransomware
  - malware
  - phishing
  - unauthorized access
  - information security
  - data security
  - network security
  - security breach
  - security incident
  - data breach
  - intrusion
  - denial of service
  - threat actor
  - encryption
traps:
  - breach
  - virus
  - year 2000
  - y2k
  - computer systems
  - personal information
  - personally identifiable
  - system outage
  - network outage
```

1. Match case-insensitively on word boundaries (prefix match where noted). Store the list of matched terms per paragraph.
2. Random sample: from paragraphs with no match, draw 1% per fiscal year with seed 20261106. These measure what the prefilter misses.
3. If you add terms, add them to the file and log why.

**Check:** report hits per term per fiscal year in `reports/data_report.md`.

### Stage 5. Company split (Yens, CPU)

1. For each CIK, compute `int(sha256(str(cik)), 16) % 10`. Values 0 to 7 are train, 8 is validation, 9 is test.
2. Save `data/final/company_split.parquet` and add the `split` column to the paragraphs file.
3. Never regenerate this file. Every later sample depends on it.

### Stage 6. Build the teacher samples (Yens, CPU)

The pool is the keyword hits plus the random sample.

1. **Training sample, 400,000 paragraphs** from train-split companies, stratified by fiscal year (per-year cap in the Data card). Mark nested subsets of 25,000 and 200,000 with `in_25k` and `in_200k`, drawn with the same seed and the same stratification. These match the hackathon checkpoints.
2. Remove exact duplicate texts within the training sample and store the duplicate count. Repeated boilerplate would otherwise dominate.
3. **Incident enrichment:** INCIDENT is rare. Add all keyword-hit paragraphs from the 10-Qs and 10-Ks in Stage 1 step 5, and paragraphs matching incident cues (`we detected`, `we discovered`, `we became aware`, `unauthorized third party`, `forensic`). Store a `sample_weight` so evaluation can correct for the enrichment.
4. **Validation, 2,000 paragraphs** from validation-split companies, natural distribution.
5. **Test, 5,000 paragraphs** from test-split companies, natural distribution, stratified by era: fiscal 1996 to 2010, 2011 to 2017, 2018 to 2022, and 2023 to 2025. Add a separate 500-paragraph incident-enriched slice, reported on its own.
6. Freeze validation and test before Stage 7. Do not change them after the teacher has seen them.

### Stage 7. Teacher labeling (Marlowe, 1 node)

1. Model: `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8` (Apache 2.0). Record the exact revision hash.
2. Engine: vLLM on one node with 8 H100 GPUs, tensor parallel 8. If vLLM rejects tensor parallel 8 for the FP8 checkpoint (a block-size divisibility error), try `--enable-expert-parallel` or tensor parallel 4. Record what worked.
3. Prompt: `config/prompt_v1.txt` (below), applied with the model's chat template.
4. Decoding: temperature 0, one output token, with log probabilities. Take the probabilities of the five letter tokens and renormalize them to sum to 1. If the top token is not one of the letters, record the item as invalid.
5. Store `label` (the top letter), `confidence` (its probability) and all five probabilities. Items with confidence below 0.7 stay in the file with `use_for_training = false`.
6. Write output in shards of 10,000 items and skip finished shards on restart.
7. **Pilot first:** run 10,000 items from the training sample. Report throughput, GPU-hours, label distribution and invalid rate. **Stop and ask** before the full run.
8. Full run: training sample, validation, test and the incident slice.

`config/prompt_v1.txt`:

```
You label paragraphs from SEC filings for cybersecurity content.

A = NONE: not about cybersecurity. This includes breach of contract or covenants, disease viruses, Year 2000 date problems, IT outages with no attacker, and privacy-law compliance with no security content.
B = RISK: cyber threats described as possible future harm, including general statements that the company has faced attacks before.
C = GOVERNANCE: how the company manages cyber risk, such as security leadership, board oversight, frameworks, audits, training, insurance or response plans.
D = INCIDENT: a specific incident that happened to the company, or to a vendor in a way that affected the company, with at least one concrete detail (when, what system or data, a consequence, or the response).
E = PRODUCT: cybersecurity products or services the company sells, or their market.
If more than one fits, choose in this order: D, C, B, E, A.

Section: {heading}
Previous paragraph: {prev_text}
Paragraph: {text}

Answer with one letter.
```

**Stop and ask** if any label is under 1% or over 90% of keyword-hit items, mean confidence is under 0.8, or more than 0.5% of outputs are invalid.

### Stage 8. Hand check (people, with agent support)

1. After Stage 7, draw 300 test paragraphs, 60 per teacher label, spread across the four eras. Export them to `data/final/handcheck.csv` with the text, heading, previous paragraph and empty columns `rater1`, `rater2`, `final_label` and `notes`. Do not include the teacher's label in the file.
2. Two DARC staff members label independently using `config/codebook.md`, then agree on `final_label`.
3. Report rater agreement (Cohen's kappa) and teacher accuracy against `final_label`, overall, per label and per era.

**Stop and ask** if teacher accuracy is below 85% overall or below 70% on any label. The usual fix is a codebook change.

### Stage 9. Free checks (Marlowe, then Yens)

These need no hand labels.

1. **Item 1.05:** share of companies with an Item 1.05 8-K whose next 10-Q or 10-K has at least one INCIDENT paragraph.
2. **Item 1C:** share of Item 1C paragraphs labeled GOVERNANCE.
3. **Virus:** among fiscal 2020 to 2022 paragraphs whose only keyword hit is `virus`, the share labeled NONE.
4. **Prefilter recall:** share of random-sample (no keyword match) paragraphs labeled anything other than NONE. **Stop and ask** if it is above 1%; the keyword list is missing terms.

### Stage 10. Student training (Marlowe)

1. Model: `Qwen/Qwen3-1.7B` with LoRA (rank {{FILL}}, alpha {{FILL}}). Apply the chat template with `enable_thinking=False`.
2. Same prompt and letters as the teacher. Compute the loss on the answer letter only. Train on items with `use_for_training = true`.
3. Three runs, one per training size (25,000, 200,000 and 400,000), matching hackathon checkpoints 1 to 5.
4. Choose the checkpoint by validation macro F1. Save the LoRA adapter and a merged model.
5. A variant that trains on the teacher's five probabilities (soft labels) is optional; keep it separate from the main runs.

### Stage 11. Full-corpus labeling (Yens, 1 H200)

1. The best student labels every keyword-hit paragraph and the random sample, for all fiscal years, plus the 8-K and 10-Q paragraphs from Stage 1. Paragraphs outside the prefilter and the random sample are counted as NONE; Stage 9 check 4 says how much that misses.
2. Run as a Slurm job array with one task per fiscal year.
3. Record items per second and total GPU-hours.
4. Output `data/final/labels_full.parquet`.

### Stage 12. Evaluation (Yens, CPU)

Score each method on the frozen test set, against the teacher and against the hand labels:

| Method | Macro F1 vs teacher | Macro F1 vs hand labels | INCIDENT F1 vs hand labels | Items per second |
|---|---|---|---|---|
| Keyword baseline (any core term is RISK, incident cue is INCIDENT, else NONE) | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| Student before training | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| Teacher | n/a | {{FILL}} | {{FILL}} | {{FILL}} |
| Student, 25,000 | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| Student, 200,000 | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |
| Student, 400,000 | {{FILL}} | {{FILL}} | {{FILL}} | {{FILL}} |

Also rebuild plot 1 from each student's labels on the test companies and overlay it on the teacher's line.

### Stage 13. Plots (Yens, CPU)

Save each plot as a PNG and the plotted values as a CSV in `reports/plots/`. Every plot gets a title, labeled axes and a source line: "Source: SEC EDGAR filings, DARC student model v1."

| Plot | Definition |
|---|---|
| 1. Cyber disclosure over time | Share of selected 10-Ks with at least one paragraph not labeled NONE, by fiscal year. Denominator: selected 10-Ks that parsed. Vertical lines at October 2011 (SEC staff guidance), February 2018 (Commission guidance) and July 2023 (final rules). |
| 2. Mix of cyber content | Mean paragraphs per 10-K for each label except NONE, stacked, by fiscal year. |
| 3. Keyword count vs model | Share of 10-Ks with any keyword hit vs share with any label other than NONE, by fiscal year. |
| 4. Incidents by industry | Share of 10-Ks with at least one INCIDENT paragraph, by fiscal year and SIC division. |
| 5. Cyber 8-Ks by item | Monthly count of 8-Ks with Item 1.05, and of 8-Ks with an Item 8.01 section labeled INCIDENT, from December 2023. |
| 6. Disclosure lag | Days from each Item 1.05 8-K to the same company's first later 10-Q or 10-K with an INCIDENT paragraph. |
| 1b. Fixed panel | Plot 1 for companies with a 10-K in every fiscal year from 2012 to 2025, so changes in which companies file do not drive the trend. |

## Data files

`data/final/filings.parquet`, one row per selected filing (annual reports, Item 1.05 and 8.01 8-Ks, and Item 1.05 follow-ups):

| Column | Type | Notes |
|---|---|---|
| accession | string | Primary key |
| cik | int | |
| company_name | string | As of this filing (from the header) |
| form_type | string | As coded in the mirror, e.g. `10KSB` |
| filing_date | date | |
| period_of_report | date | |
| fiscal_year | int | Calendar year of period_of_report; null for 8-Ks |
| sic | int | Nullable; filled from the same CIK's other filings when the header lacks it |
| sic_from_header | bool | False when `sic` was filled |
| state_of_inc | string | Nullable |
| doc_count | int | PUBLIC DOCUMENT COUNT |
| file_bytes | int | Size of the full submission file |
| filepath | string | Path on the Yens |
| is_annual, is_8k, is_followup | bool | Why the filing was selected (a 10-K can be both annual and a follow-up) |
| has_item_105, has_item_801 | bool | 8-K items from the header |
| followup_of | list of strings | Item 1.05 8-K accessions this filing follows up |
| parse_status | string | ok, failed, or empty (Stage 2) |

`data/interim/paragraphs.parquet`, one row per paragraph:

| Column | Type | Notes |
|---|---|---|
| para_id | string | accession plus paragraph index |
| accession, cik, form_type, fiscal_year | | From filings |
| section | string | 1A, 1C, 7, OTHER, or the 8-K item number |
| heading | string | Nearest heading above |
| prev_text | string | Previous paragraph, at most 150 words |
| text | string | |
| n_words | int | |
| text_sha1 | string | Of normalized text |
| kw_terms | list of strings | Empty if no match |
| in_random_sample | bool | |
| split | string | train, val or test |

Sample files `train_400k.parquet` (with `in_25k`, `in_200k`, `sample_weight`), `val.parquet`, `test.parquet` and `test_incident_slice.parquet` carry the paragraph columns plus the teacher columns once Stage 7 is done.

`data/final/teacher_labels.parquet`: `para_id`, `label`, `confidence`, `p_A` to `p_E`, `use_for_training`, `invalid`, `teacher_model`, `teacher_revision`, `prompt_version`, `run_id`.

`data/final/labels_full.parquet`: `para_id`, `label`, `confidence`, `student_model`, `run_id`.

## Data card (fill in)

### Source

| Item | Value |
|---|---|
| Mirror snapshot date | UNKNOWN (not recorded in the mirror or the Redivis table; latest filing below is the best proxy) |
| Mirror directory structure (two or three sentences) | One file per submission at `/zfs/data/NODR/EDGAR_HTTPS/edgar/data/<cik>/<accession>.txt`: the full SGML submission with the `<SEC-HEADER>` block followed by every document (main form, exhibits, XBRL, graphics). Quarterly index files are in `/zfs/tools/darc/edgar_https/data/index/index_<year>_<quarter>.csv`. The Redivis table `stanfordgsblibrary.edgar_filings` lists every file (27,288,589 rows) with its path. |
| Latest filing date in the mirror | 2026-10-02 |

### Filings (Stages 0 and 1)

| Item | Value |
|---|---|
| Annual reports in mirror, fiscal 1996 to 2025, before selection | 290,443 originals with a readable header (296,058 originals filed 1996-2026 read; 9 header errors, 2 without a period, 5,604 outside fiscal 1996-2025) |
| Amendments excluded | 62,314 annual-report amendments filed 1996-2026 (10-K/A, 10-K405/A, 10KSB/A, 10KSB40/A, 10-KT/A, 10KT405/A) |
| Dropped as second filing for the same company and year | 4,942, plus 8,172 jointly filed duplicates of one accession |
| Selected 10-Ks | 277,329 (10-K 220,569; 10KSB 35,599; 10-K405 17,652; 10KSB40 3,273; 10-KT 199; 10KT405 37) |
| Distinct companies | 42,883 |
| Fiscal year with the fewest and the most 10-Ks | Fewest 2025 (6,366; late filers not yet in the mirror); most 2000 (12,942) |
| 8-Ks with Item 1.05 | 58, from 57 companies |
| 8-Ks with Item 8.01 since December 18, 2023 | 46,873 |
| 10-Qs and 10-Ks after an Item 1.05 8-K | 49 (35 10-Qs, 14 10-Ks); 8 Item 1.05 8-Ks have no later filing yet |
| Raw size of selected annual reports | 1.63 TB of full submission files (measured from file sizes); most of it is exhibits and XBRL after 2010 |
| Per-year table | `reports/data_report.md`, section Filings selected (Stage 1) |

### Text extraction and paragraphs (Stages 2 and 3)

| Item | Value |
|---|---|
| Parser and version | {{FILL}} |
| Parse failure rate, overall and worst year | {{FILL}} |
| Paragraphs, total | {{FILL}} |
| Median and 95th percentile words per paragraph | {{FILL}} |
| Paragraphs split for length | {{FILL}} |
| Item 1A found, share of 10-Ks from fiscal 2006 | {{FILL}} |
| Item 1C found, share of 10-Ks from fiscal 2024 | {{FILL}} |
| Item 7 found, share of all 10-Ks | {{FILL}} |
| Size on disk of paragraphs.parquet | {{FILL}} |
| Wall time and CPU-hours for Stages 2 and 3 | {{FILL}} |

### Prefilter (Stage 4)

| Item | Value |
|---|---|
| Keyword-hit paragraphs, total and share of all paragraphs | {{FILL}} |
| Five terms with the most hits | {{FILL}} |
| Random-sample paragraphs | {{FILL}} |
| Terms added beyond the list above, and why | {{FILL}} |

### Split and samples (Stages 5 and 6)

| Item | Value |
|---|---|
| Companies in train, validation and test | {{FILL}} |
| Per-year cap in the training sample | {{FILL}} |
| Exact duplicates removed from the training sample | {{FILL}} |
| Share of the training sample from the random sample | {{FILL}} |
| Share of the training sample from incident enrichment | {{FILL}} |
| Test paragraphs per era | {{FILL}} |
| Total items for the teacher | {{FILL}} |

### Teacher (Stage 7)

| Item | Value |
|---|---|
| Model revision hash | {{FILL}} |
| vLLM version and parallel settings that worked | {{FILL}} |
| Pilot: items per second, GPU-hours | {{FILL}} |
| Full run: items, wall time, GPU-hours | {{FILL}} |
| Label distribution, A to E | {{FILL}} |
| Share with confidence below 0.7 | {{FILL}} |
| Invalid outputs | {{FILL}} |

### Checks (Stages 8 and 9)

| Item | Value |
|---|---|
| Rater agreement (Cohen's kappa) | {{FILL}} |
| Teacher accuracy vs hand labels, overall, per label, per era | {{FILL}} |
| Item 1.05 check | {{FILL}} |
| Item 1C check | {{FILL}} |
| Virus check | {{FILL}} |
| Prefilter recall check | {{FILL}} |

### Student and full corpus (Stages 10 and 11)

| Item | Value |
|---|---|
| Training time per size, on which hardware | {{FILL}} |
| Paragraphs labeled in the full run | {{FILL}} |
| Full run: wall time, Yen GPU-hours | {{FILL}} |
| Items per GPU-hour, student vs teacher | {{FILL}} |

### Known issues

- Fiscal 1996 annual reports filed in 1996 are fiscal 1995 or earlier and are dropped; fiscal 1996 comes mostly from filings in 1997. EDGAR filing became mandatory for all registrants in May 1996, so filing-year 1996 counts are low (Stage 0 flag).
- 9 filing-year-1996 annual reports have unreadable headers (listed in `data/interim/headers/headers_1996.parquet`, `status = header_error`).
- 2,660 selected annual reports have no SIC even after filling, mostly trusts and asset-backed issuers.
- Asset-backed issuers (SIC 6189 and many without SIC) file boilerplate 10-Ks. They are still in the selection; decide before Stage 6 whether to exclude them from the denominator of plot 1.
- Fiscal 2025 is incomplete: the mirror ends 2026-10-02, so late filers are missing.

## Stop and ask

Stop and wait for a person when:

- a job would use more than the agreed GPU-hour limit, run across Marlowe nodes, or run outside the reserved nodes;
- any fiscal year has a parse failure rate above 5% (Stage 2);
- Item 1A or Item 1C detection is below 80% in the years it should appear (Stage 3);
- the teacher pilot is done, before the full run (Stage 7);
- teacher output looks wrong: a label under 1% or over 90% of keyword hits, mean confidence under 0.8, or invalid outputs above 0.5% (Stage 7);
- teacher accuracy on the hand check is below 85% overall or 70% on any label (Stage 8);
- prefilter recall check is above 1% (Stage 9);
- you want to change the codebook, the prompt, the split or the frozen test set.

The thresholds are starting values. Change them only with DARC's agreement, and log the change.

## Later extensions

- A third-party flag on INCIDENT paragraphs (vendor incidents).
- Full 10-Q coverage for quarterly plots.
- Boilerplate share of cyber paragraphs over time, using the boilerplate task.

## References

- DARC EDGAR mirror on the Yens: https://github.com/gsbdarc/edgar-yens-mirror
- Redivis table and how to query it: https://rcpedia.stanford.edu/blog/2023/05/16/sec-filings/
- SEC cybersecurity disclosure rules (2023): https://www.sec.gov/newsroom/press-releases/2023-139
- SEC compliance guide for the cybersecurity rules: https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/cybersecurity-risk-management-strategy-governance-incident-disclosure
- Teacher model card: https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
- Hackathon agenda: https://docs.google.com/document/d/18w-0TrEuLV2QRx-AbTNy4Vd3FGijSGh6Mx6UcxwiR10/edit
- Four-task overview: https://docs.google.com/document/d/131hM3Bfbs8LUMdc_snNZ3VqiT1l6F45hetNND40krMY/edit
