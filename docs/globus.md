---
layout: default
title: "Moving Data with Globus"
nav_order: 3
parent: "Reference"
permalink: /globus/
---

# Moving Data with Globus

The class data and models are already on both clusters, so most tasks need no copying. You copy your own files
when a task moves work between the Yens and Marlowe:

| Task | What you copy | From | To |
|---|---|---|---|
| [A2]({{ '/advanced/a2/' | relative_url }}), after the workshop | your A1 answers, `results/kev-27b-zeroshot.jsonl` | Yens | Marlowe |
| [A5]({{ '/advanced/a5/' | relative_url }}) | a student you trained, `runs/a5-<teacher>/` | Marlowe | Yens |
| [Use your trained model]({{ '/label/' | relative_url }}) | a run you trained, `runs/<run>/` | Marlowe | Yens |

Globus copies files between the two clusters directly, without passing them through your laptop. It checks every file
when the copy finishes and retries if the connection drops. Each storage system is a **collection** in Globus:

| Cluster | Collection | ID | Your folder (`$WORK`) |
|---|---|---|---|
| Yens | `GSB/DARC yen` | `2556f515-7a87-407b-a24d-18ed16237588` | `/scratch/users/<sunet>/ceo-turnover` |
| Marlowe | `Marlowe /scratch directories` | `56ac92ca-0bad-4009-baaa-513525b3e648` | `/scratch/c001/users/<sunet>/ceo-turnover` |

Two collections are named `GSB/DARC yen`. Use the ID above: the other one returns an error.

The steps below use the Globus command-line tool on the Yens. You can also make the same copy in a browser at
[app.globus.org](https://app.globus.org): sign in with Stanford, open the two collections side by side, and drag the
folder across.

---

## Step 1: Log in to Globus, once

On a Yens login node:

```bash
ml globus-cli
globus login --no-local-server
```
{: .yens }

The Yens have no browser, so `globus login` prints a URL. Open it on your laptop, choose **Stanford University**, sign
in with your SUNet ID and Duo, and click **Allow**. Globus shows an authorization code: paste it into the terminal.
The login is saved in your home directory.

## Step 2: Check you can reach both collections

Save the two IDs, then list your folder on each side:

```bash
export YEN=2556f515-7a87-407b-a24d-18ed16237588
export MARLOWE=56ac92ca-0bad-4009-baaa-513525b3e648
globus ls "$YEN:/scratch/users/$USER/ceo-turnover/"
globus ls "$MARLOWE:/scratch/c001/users/$USER/"
```
{: .yens }

The first listing on each collection may stop with `Session reauthentication required` and a command to run, for
example `globus session update stanford.edu`. Run it, sign in again in your laptop's browser, and list again.

## Step 3: Start the copy

A single file, here your A1 answers to Marlowe. Make the folder on Marlowe first, from a Marlowe terminal:

```bash
mkdir -p /scratch/c001/users/$USER/ceo-turnover/results
```
{: .marlowe }

Then start the transfer from the Yens:

```bash
globus transfer "$YEN:/scratch/users/$USER/ceo-turnover/results/kev-27b-zeroshot.jsonl" \
  "$MARLOWE:/scratch/c001/users/$USER/ceo-turnover/results/kev-27b-zeroshot.jsonl" \
  --label "A1 answers"
```
{: .yens }

A folder, here an A5 student back to the Yens, takes `--recursive`. Change `qwen-235b` to the teacher you trained on:

```bash
globus transfer "$MARLOWE:/scratch/c001/users/$USER/ceo-turnover/runs/a5-qwen-235b/" \
  "$YEN:/scratch/users/$USER/ceo-turnover/runs/a5-qwen-235b/" \
  --recursive --label "A5 student"
```
{: .yens }

`globus transfer` prints a `Task ID` and returns straight away. The copy runs on Globus's side, so you can close the
terminal.

## Step 4: Wait for it and check

```bash
globus task wait <task-id>
globus task show <task-id>
```
{: .yens }

A finished copy shows `Status: SUCCEEDED`, and Globus emails you when it ends. Then list the folder on the other
cluster to see the files there.

{: .tip }
> Claude Code can run these steps for you. Load it on the Yens with `ml claude-code` and start `claude`; the first
> time, sign in with **Continue with SSO** and your Stanford address. Then ask, for example, to copy your A5 student
> to the Yens with the Globus CLI. Read each command before you approve it.
