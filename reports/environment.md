# Environment

| What | Version / location |
|---|---|
| Python | 3.11.3, shared venv `/zfs/projects/darc/marlowe_hackathon/.venv` |
| Python packages (Stages 0-1) | `requirements.txt`: numpy 2.4.6, pandas 3.0.6, pyarrow 25.0.1, python-dotenv 1.2.4, redivis 0.20.15 |
| Globus CLI | 3.43.0, own venv `/scratch/users/$USER/globus-venv` (installed by `scripts/globus/setup.sh`) |
| Redivis table | `stanfordgsblibrary.edgar_filings:dq12:v3_206.edgar_filings:kc0j` (version v3_206) |
| Slurm (Yens) | partition `normal` |
| git | 2.34.1 |

Install: `../.venv/bin/pip install -r requirements.txt`. Add packages for later stages here and to `requirements.txt` when they are first used.
