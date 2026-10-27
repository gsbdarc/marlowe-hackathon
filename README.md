# Marlowe Hackathon 2026

Materials for the DARC and Marlowe GPU hackathon at Stanford GSB, November 13, 2026.

**Website: <https://gsbdarc.github.io/marlowe-hackathon/>**

Participants fine-tune **Kev-4B**, a small open model, to answer three questions about CEO turnover in SEC 8-K Item 5.02
filings the way **Jev**, a large hosted model, answered them. They train on one GPU on the Yens, scale to two, then
run the same job on 1, 8 and 16 H100s on Marlowe, and measure time per step and GPU-hours at each scale.

## What is here

| Path | What |
|---|---|
| `docs/` | the website (Jekyll, just-the-docs), deployed by `.github/workflows/pages.yml` on every push to `main` |
| `env/` | paths and cache settings for the Yens (`yens.sh`) and Marlowe (`marlowe.sh`) |
| `scripts/` | setup, data preparation, labeling, scoring, step timing, and the Weights & Biases sidecar |
| `slurm/train_args.sh` | the training job every checkpoint runs |
| `slurm/yens/` | Checkpoints 1 and 2, data preparation, and serving a model to label filings |
| `slurm/marlowe/` | Checkpoints 3, 4 and 5 |

No data, results or model weights are in this repository. Jev's labeled filings are on the Yens at
`/yen/projects/darc/marlowe_hackathon/ceo-turnover/data/jev` and on Marlowe at
`/scratch/m000106/gsb_hackathon/ceo-turnover/data/jev`. `.gitignore` is a whitelist: only the paths above are
tracked, and data files are ignored everywhere in the tree.

## Build the site locally

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Then open <http://localhost:4000/marlowe-hackathon/>.

## Earlier work

The cybersecurity-disclosure pilot that preceded this project is in the git history and on the `kev-finetune`
branch.
