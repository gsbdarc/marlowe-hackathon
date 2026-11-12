# Settings for jobs on Marlowe. Source it, don't run it:  source env/marlowe.sh
# Marlowe home is 32 GB, so code, weights, caches and runs all go to the class's scratch space, /scratch/c001.
export SHARE=/scratch/c001/marlowe-hackathon      # shared, read only: data, models, containers, kev, repo
export ME=/scratch/c001/users/$USER                   # yours: your clone, runs and caches
export DATA=$SHARE/data/jev                         # Jev-labeled Item 5.02 release (read only)
export CLASS_DATA=$SHARE/data                 # train, valid, test1000, built by setup/setup.sh (read only)
export WORK=$ME/ceo-turnover                        # your training data, runs and results
export KEV_HOME=$SHARE/kev                      # Kev and its Python, prebuilt by setup/setup.sh (read only)
export HF_HOME=$ME/.cache/huggingface            # your Hugging Face settings and lock files
export HF_HUB_CACHE=$SHARE/models           # model weights, downloaded by setup/setup.sh (read only)
export HF_HUB_OFFLINE=1                                      # every model is pre-downloaded by DARC: never download
export UV_CACHE_DIR=$KEV_HOME/uv-cache UV_PYTHON_INSTALL_DIR=$KEV_HOME/uv-python
export XDG_CACHE_HOME=$ME/.cache PIP_CACHE_DIR=$ME/.cache/pip
export TRITON_CACHE_DIR=$ME/.cache/triton TORCHINDUCTOR_CACHE_DIR=$ME/.cache/inductor
export APPTAINER_CACHEDIR=$ME/.cache/apptainer   # Marlowe's Apptainer guide: not the 32 GB home
export MPLCONFIGDIR=$ME/.cache/matplotlib CUDA_CACHE_PATH=$ME/.cache/nv FLASHINFER_WORKSPACE_DIR=$ME/.cache/flashinfer
export WANDB_CACHE_DIR=$ME/.cache/wandb WANDB_DATA_DIR=$ME/.cache/wandb WANDB_CONFIG_DIR=$ME/.cache/wandb-config
export KEV_PREFIX_CACHE=0
export HF_HUB_DISABLE_UPDATE_CHECK=1                         # Kev pins huggingface_hub below 2.0: skip the hf CLI's upgrade hint
export PY=$KEV_HOME/kev/.venv/bin/python
export MARLOWE_ACCOUNT=marlowe-c001
# The hackathon's nodes, set aside Friday 11/13 from 12:00 to 17:00. While the reservation is open, sbatch uses it by
# itself; at any other time jobs go to the batch partition like anyone's. A --reservation on the command line wins.
if scontrol show reservation GSB_Hackathon 2>/dev/null | grep -q "State=ACTIVE"; then
  export SBATCH_RESERVATION=GSB_Hackathon
else
  unset SBATCH_RESERVATION
fi
mkdir -p "$WORK/results" "$HF_HOME" "$XDG_CACHE_HOME"   # $WORK/results: label.py and tee write there

# In a terminal, say what was set; jobs and scripts source this quietly
case $- in
  *i*) printf '%s paths for this terminal:\n' "Marlowe"
       printf '  shared, read only:\n'
       printf '    %-10s %s\n' CLASS_DATA "$CLASS_DATA" models "$HF_HUB_CACHE" KEV_HOME "$KEV_HOME" PY "$PY"
       printf '  yours:\n'
       printf '    %-10s %s\n' WORK "$WORK" caches "$XDG_CACHE_HOME"
       printf '  jobs go to:\n    %s\n' "batch${SBATCH_RESERVATION:+, in the $SBATCH_RESERVATION reservation}" ;;
esac
