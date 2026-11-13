# Settings for the intermediate track on the Yens: env/yens.sh, with DATA pointing at your own copy of Jev's release
# (I1 has you copy the class data folder into $WORK/data) and quieter logs. Source it from the top of the repo, don't
# run it:
#   source scripts/intermediate/yens.sh
source env/yens.sh
export DATA=$WORK/data/jev                                   # your copy of Jev-labeled Item 5.02 release
# No W&B or Hugging Face banners and progress bars in the logs; label.py and wandb_watch.py print the W&B run's link
export WANDB_SILENT=true HF_HUB_DISABLE_PROGRESS_BARS=1 HF_HUB_VERBOSITY=error TRANSFORMERS_VERBOSITY=error
# peft warns on every run that Qwen's base model has no adapter config of its own, which is expected here
export PYTHONWARNINGS="ignore:Could not find a config file:UserWarning"
# The hackathon's Yens GPU nodes, yen-gpu3 (4 A40s) and yen-gpu4 (both H200s), set aside Friday 11/13 from 09:30 to
# 18:30. While the reservation is open, sbatch uses it by itself; at any other time jobs go to the gpu partition like
# anyone's. A --reservation on the command line wins.
if scontrol show reservation hackathon 2>/dev/null | grep -q "State=ACTIVE"; then
  export SBATCH_RESERVATION=hackathon
else
  unset SBATCH_RESERVATION
fi
case $- in   # in a terminal, finish env/yens.sh's list of paths with where jobs go
  *i*) printf '  jobs go to:\n    %s\n' "gpu${SBATCH_RESERVATION:+, in the $SBATCH_RESERVATION reservation}" ;;
esac
