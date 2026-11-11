# Marlowe Hackathon 2026

Materials for the DARC and Marlowe GPU hackathon at Stanford GSB, November 13, 2026.

**Website: <https://gsbdarc.github.io/marlowe-hackathon/>**

Participants fine-tune open models to answer three questions about CEO turnover in SEC 8-K Item 5.02 filings the way
**Jev**, a large hosted model, answered them. They pick one of three tracks (Beginner, Intermediate, Advanced), start
on the Yens, then scale the training to 1, 8 and 16 H100s on Marlowe, and measure time per step and GPU-hours at each
scale.

## What is here

| Path | What |
|---|---|
| `docs/` | the website (Jekyll, just-the-docs), deployed by `.github/workflows/pages.yml` on every push to `main` |
| `setup/` | instructor setup: models, container, Kev and data on each cluster, run once per cluster ([setup/README.md](setup/README.md)) |
| `env/` | `yens.sh` and `marlowe.sh`: every path and cache setting. Every job sources one; in a terminal it also prints the paths |
| `scripts/` | tools the tracks share: `setup_kev.sh` (checks the shared Kev and models), `label.py`, `score.py`, `step_times.py`, `make_kev_data.py` |
| `scripts/advanced/`, `scripts/intermediate/` | each track's own scripts |
| `slurm/yens/`, `slurm/marlowe/` | job files, in a folder per track (`advanced/`, `intermediate/`), plus the shared `serve_and_label.slurm` |
| `slurm/train_args.sh` | training settings the track jobs share |

## On the clusters

No data, results or model weights are in this repository. `.gitignore` is a whitelist: only the paths above are
tracked, and data files are ignored everywhere in the tree.

| | Yens | Marlowe |
|---|---|---|
| Shared folder, read only: `data/`, `models/`, `kev/`, `containers/` (Marlowe), `repo/` | `/scratch/shared/marlowe_hackathon` | `/scratch/c001/marlowe-hackathon` |
| Each participant's folder: their clone, `$WORK`, caches | `/scratch/users/<sunet>` | `/scratch/c001/users/<sunet>` |

Instructors fill the shared folders with `setup/setup.sh`: see [setup/README.md](setup/README.md).

## Build the site locally

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Then open <http://localhost:4000/marlowe-hackathon/>.
