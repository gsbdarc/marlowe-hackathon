"""Download Kev checkpoints and the Qwen3.5 base each adapter needs into HF_HOME, so GPU jobs start from a warm cache.

A LoRA checkpoint (Kev-4B, Kev-9B) records its base and base revision in training_config.json; the trainer loads that
exact revision, so it is fetched here too. Kev-27B v1.0 holds full weights and needs no base. Prints the commit each
name resolved to, for the tutorial's environment notes.

  $KEV_VENV/bin/python kev/scripts/k00_download.py $KEV_4B $KEV_9B $KEV_27B
"""

import json
import sys
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def fetch(repo, rev):
    path = Path(snapshot_download(repo, revision=rev))
    sha = HfApi().model_info(repo, revision=rev).sha
    size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e9
    print(f"{repo}@{rev}: commit {sha}, {size:.1f} GB, {path}", flush=True)
    return path


for name in sys.argv[1:]:
    repo, _, rev = name.partition("@")
    path = fetch(repo, rev or None)
    cfg = path / "training_config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text())
        fetch(c["args"]["base"], c.get("base_revision") or c["args"]["base_revision"])
