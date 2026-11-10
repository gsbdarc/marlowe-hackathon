# Settings for the intermediate track on the Yens: env/yens.sh, with DATA pointing at your own copy of Jev's release
# (The Data page has you make it) and quieter logs. Source it from the top of the repo, don't run it:
#   source scripts/intermediate/yens.sh
source env/yens.sh
export DATA=$WORK/data/jev                                   # your copy of Jev-labeled Item 5.02 release
# No W&B or Hugging Face banners and progress bars in the logs; label.py and wandb_watch.py print the W&B run's link
export WANDB_SILENT=true HF_HUB_DISABLE_PROGRESS_BARS=1 HF_HUB_VERBOSITY=error TRANSFORMERS_VERBOSITY=error
# peft warns on every run that Qwen's base model has no adapter config of its own, which is expected here
export PYTHONWARNINGS="ignore:Could not find a config file:UserWarning"
