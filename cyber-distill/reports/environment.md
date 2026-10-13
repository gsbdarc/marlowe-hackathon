# Environment

| What | Version / location |
|---|---|
| Python | 3.11.3, shared venv `/zfs/projects/darc/marlowe_hackathon/.venv` |
| Python packages (Stages 0-1) | `requirements.txt`: numpy 2.4.6, pandas 3.0.6, pyarrow 25.0.1, python-dotenv 1.2.4, redivis 0.20.15 |
| Globus CLI | 3.43.0, own venv `/scratch/users/$USER/globus-venv` (installed by `scripts/globus/setup.sh`) |
| Redivis table | `stanfordgsblibrary.edgar_filings:dq12:v3_206.edgar_filings:kc0j` (version v3_206) |
| Slurm (Yens) | partitions `normal` (CPU) and `gpu` (H200 NVL, 4 per node) |
| vLLM | container `docker://vllm/vllm-openai:v0.31.0` (vLLM 0.31.0, torch 2.13.0+cu130) as `/scratch/shared/$USER/vllm/vllm-openai_v0.31.0.sif`, Apptainer 1.3.6 (`module load apptainer`), wrapper `vllm.sh` from gsbdarc/vllm_helper at `db1c923` |
| Training (Yens) | shared `.venv`: torch 2.14.1, transformers 5.19.0, peft 0.21.2, accelerate 1.15.0 |
| Marlowe | `requirements-marlowe.txt` (same versions as the Yens .venv for client and training); vLLM from the same container |
| git | 2.34.1 |

Install: `../.venv/bin/pip install -r requirements.txt`. Add packages for later stages here and to `requirements.txt` when they are first used.
