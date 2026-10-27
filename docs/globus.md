---
layout: default
title: "Moving Data with Globus"
nav_order: 8
permalink: /globus/
---

# Moving Data with Globus

In this section you copy your training files from the Yens to Marlowe with the Globus command-line tool, with
Claude Code on the Yens running the commands.

Globus copies files between storage systems directly: the data goes from the Yens to Marlowe without passing through
your laptop, it checks every file when the copy finishes, and it retries if the connection drops. Each storage system
appears in Globus as a **collection**. The Yens are the `GSB/DARC yen` collection; Marlowe's `/scratch` is a
collection you find by searching for Marlowe.

You will copy `$WORK/data/` (about 270 MB) from the Yens to the same place on Marlowe:

| | Path |
|---|---|
| From (Yens) | `/scratch/users/<sunet>/ceo-turnover/data/` |
| To (Marlowe) | `/scratch/m000106/gsb_hackathon/<sunet>/ceo-turnover/data/` |

{: .note }
> Jev's labeled filings and the Kev-27B weights are already on Marlowe in the hackathon's shared folders. You only
> copy your own training files.

---

## Step 1: Start Claude Code on the Yens

```bash
ssh <sunet>@yen.stanford.edu
cd /scratch/users/$USER/marlowe-hackathon
ml globus-cli claude-code
claude
```
{: .yens }

If this is your first time using Claude Code on the Yens, sign in with **Continue with SSO** and your Stanford address,
as in the [Yens onboarding course](https://gsbdarc.github.io/yens-onboarding-2026/day1/claude-code/).

## Step 2: Log in to Globus

Ask Claude to start the login:

```
> Run `globus login --no-local-server` and show me the URL it prints.
```
{: .claude }

There is no browser on the Yens, so the login runs across both machines. Open the URL in the browser on your laptop,
choose **Stanford University**, sign in with your SUNet ID and Duo, and click **Allow**. Globus shows an
authorization code: paste it back into the terminal.

The login is saved in your home directory, so you do this once.

## Step 3: Find the two collections

```
> Use the globus CLI to find the collection IDs for "GSB/DARC yen" and for Marlowe's /scratch, and save them as YEN and MARLOWE in ~/.globus-hackathon.env. Then list /scratch/m000106/gsb_hackathon/ on Marlowe to check access.
```
{: .claude }

Read the commands Claude proposes before you approve each one. They should look like this:

```bash
globus endpoint search "GSB/DARC yen"
globus endpoint search "Marlowe"
globus ls "$MARLOWE:/scratch/m000106/gsb_hackathon/"
```
{: .yens }

If `globus ls` says the collection needs more authentication, Globus prints a `globus session consent ...` command.
Run it, sign in again in your laptop's browser, and retry.

## Step 4: Copy your training files

```
> Start a Globus transfer of /scratch/users/$USER/ceo-turnover/data/ on YEN to /scratch/m000106/gsb_hackathon/$USER/ceo-turnover/data/ on MARLOWE, recursive, labeled "ceo-turnover data", then wait for it to finish and show me the task status.
```
{: .claude }

The commands behind it:

```bash
globus transfer "$YEN:/scratch/users/$USER/ceo-turnover/data/" \
  "$MARLOWE:/scratch/m000106/gsb_hackathon/$USER/ceo-turnover/data/" \
  --recursive --label "ceo-turnover data"
globus task wait <task-id>
globus task show <task-id>
```
{: .yens }

A finished transfer shows `Status: SUCCEEDED`. Globus also emails you when a transfer finishes.

## Step 5: Check on Marlowe

```bash
ls -lh /scratch/m000106/gsb_hackathon/$USER/ceo-turnover/data/
wc -l /scratch/m000106/gsb_hackathon/$USER/ceo-turnover/data/*.jsonl
```
{: .marlowe }

```
   1000 .../test1000.jsonl
  54426 .../train.jsonl
   2000 .../valid.jsonl
```
{: .output }

{: .tip }
> The same steps copy results back: the Advanced track's [A3]({{ '/advanced/a3/' | relative_url }}) moves a trained
> model from Marlowe to the Yens.
