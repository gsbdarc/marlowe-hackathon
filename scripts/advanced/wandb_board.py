"""Lay out an Advanced task's W&B project for the screen in the room: what one epoch would cost at each run's speed,
the training as it goes, and the GPUs, with a table of who ran what.

The Advanced training jobs report to the Marlowe-Hackathon team, in projects advanced-a2, advanced-a3 and advanced-a5
(slurm/marlowe/advanced/wandb.sh). Everyone shares one W&B key, so the table shows config.user, the SUNet ID each job
records, rather than W&B's own User column. This saves a view named "Board" in the project.

Run it from a login node, with W&B's wandb-workspaces package in a small environment of its own (not Kev's):

    $KEV_HOME/bin/uv venv --python 3.12 $WORK/wandb-tools
    $KEV_HOME/bin/uv pip install --python $WORK/wandb-tools/bin/python wandb-workspaces
    set -a; source $SHARE/wandb.env; set +a            # $HACKATHON/wandb.env on the Yens
    $WORK/wandb-tools/bin/python scripts/advanced/wandb_board.py a2                # prints the new view's link
    $WORK/wandb-tools/bin/python scripts/advanced/wandb_board.py a2 --url <link>   # lay out that view again

Without --url it saves a new view each time, so pass the link it printed to change the layout later. A project that
has no runs yet is created first.
"""
import argparse
from urllib.parse import quote, unquote, urlparse

import wandb
import wandb_workspaces.reports.v2 as wr
import wandb_workspaces.workspaces as ws

ORDER = {"a2": "epoch_hours", "a3": "epoch_hours", "a5": "median_seconds_per_step"}


def bars(*keys):
    # A metric name, not wr.SummaryMetric: this W&B server draws no bars for summary_metrics.<key>, and a bar for a
    # logged metric shows each run's latest value. wandb_watch.py logs these keys as well as putting them in the summary.
    return [wr.BarPlot(title=title, metrics=[key], orientation="h") for key, title in keys]


def layout():
    cost = bars(("epoch_hours", "Hours for one epoch at this speed"),
                ("epoch_gpu_hours", "GPU-hours for one epoch (hours x GPUs)"),
                ("median_seconds_per_step", "Seconds per optimizer step (median)"),
                ("peak_gpu_gb", "Peak GPU memory, GB (of 80 on an H100)"))
    live = [wr.LinePlot(title="Seconds per optimizer step", x="Step", y=["seconds_per_step"]),
            wr.LinePlot(title="Projected epoch hours, as it trains", x="Step", y=["epoch_hours_so_far"]),
            wr.LinePlot(title="Training loss", x="Step", y=["loss"])]
    gpus = [wr.LinePlot(title="Busiest GPU's memory (GB)", x="Step", y=["gpu_memory_gb"]),
            wr.LinePlot(title="Average GPU use (%)", x="Step", y=["gpu_use_percent"])]
    columns = ["config:user", "config:gpus", "config:lora", "config:batch", "config:accum", "config:records_per_step",
               "summary:median_seconds_per_step", "summary:epoch_hours", "summary:epoch_gpu_hours",
               "summary:peak_gpu_gb", "summary:loss", "summary:result"]
    return [ws.Section(name="What one epoch would cost", panels=cost, is_open=True),
            ws.Section(name="While it trains", panels=live, is_open=True),
            ws.Section(name="GPUs", panels=gpus, is_open=True)], columns


# wandb-workspaces builds and reads links without the /wandb/ path this server's W&B app is under
def browser_link(url):
    u = urlparse(url)
    return u._replace(path="/wandb" + quote(u.path)).geturl()


def library_link(url):
    u = urlparse(unquote(url))
    return u._replace(path=u.path.removeprefix("/wandb")).geturl()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", choices=ORDER, help="a2, a3 or a5: the project advanced-<task>")
    ap.add_argument("--entity", default="Marlowe-Hackathon")
    ap.add_argument("--url", help="the Board view's link, to lay it out again instead of saving a new view")
    ap.add_argument("--project", help="another project to lay out the same way (default: advanced-<task>)")
    a = ap.parse_args()
    project = a.project or f"advanced-{a.task}"
    if not a.url:
        api = wandb.Api()
        if project not in {p.name for p in api.projects(a.entity)}:
            api.create_project(project, a.entity)
    sections, columns = layout()
    view = ws.Workspace.from_url(library_link(a.url)) if a.url else ws.Workspace(entity=a.entity, project=project, name="Board")
    view.sections = sections
    view.runset_settings = ws.RunsetSettings(pinned_columns=columns, order=[ws.Ordering(ws.Summary(ORDER[a.task]))])
    view.settings = ws.WorkspaceSettings(max_runs=100)
    view.save()
    print(browser_link(view.url))


if __name__ == "__main__":
    main()
