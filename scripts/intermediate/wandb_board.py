"""Lay out an exercise's W&B project for the board: who ran what, with which options, and the scores side by side.

Everyone at the hackathon shares one W&B key, so W&B's own User column is the same for every run; the table shows config.user, the
SUNet ID each job records. Scores live in each run's summary (score.py), which W&B's default workspace doesn't chart,
so this saves a view named "Board" with a runs table and a bar chart per score.

DARC runs it once per exercise, from a login node, with W&B's wandb-workspaces package in a small environment of its
own (not Kev's):

    $KEV_HOME/bin/uv venv --python 3.12 $WORK/wandb-tools
    $KEV_HOME/bin/uv pip install --python $WORK/wandb-tools/bin/python wandb-workspaces
    set -a; source $HACKATHON/wandb.env; set +a
    $WORK/wandb-tools/bin/python scripts/intermediate/wandb_board.py 1          # prints the new view's link
    $WORK/wandb-tools/bin/python scripts/intermediate/wandb_board.py 1 --url <link>   # lay out that view again

Without --url it saves a new view each time, so pass the link it printed to change the layout later.
"""
import argparse
from urllib.parse import quote, unquote, urlparse

import wandb_workspaces.reports.v2 as wr
import wandb_workspaces.workspaces as ws


def bars(*keys):
    return [wr.BarPlot(title=title, metrics=[wr.SummaryMetric(key)], orientation="h") for key, title in keys]


def i1():
    scores = bars(("test/status_agree_weighted", "Agreement with Jev, weighted to all test filings"),
                  ("test/status_agree_on_ceo_changes", "Agreement with Jev on CEO changes"),
                  ("test/ceo_change_f1", "CEO-change F1"))
    speed = bars(("filings_per_second", "Filings per second"),
                 ("gpu_memory_peak_gb", "Peak GPU memory (GB)"),
                 ("mean_batch", "Average batch the server ran"))
    speed.append(wr.LinePlot(title="Filings per second while labeling", y=["filings_per_second_so_far"]))
    options = wr.ParallelCoordinatesPlot(title="Options against speed and agreement", columns=[
        wr.ParallelCoordinatesPlotColumn(metric=wr.Config(k)) for k in ("gpu", "concurrency", "dtype", "fused")] + [
        wr.ParallelCoordinatesPlotColumn(metric=wr.SummaryMetric(k)) for k in ("filings_per_second", "test/status_agree_weighted")])
    columns = ["config:user", "config:gpu", "config:concurrency", "config:dtype", "config:fused",
               "summary:filings_per_second", "summary:gpu_memory_peak_gb", "summary:test/status_agree_weighted",
               "summary:test/status_agree_on_ceo_changes", "summary:test/ceo_change_f1"]
    sections = [ws.Section(name="Scores", panels=scores, is_open=True),
                ws.Section(name="Speed and GPU memory", panels=speed, is_open=True),
                ws.Section(name="Compare options", panels=[options], is_open=True)]
    return sections, columns, ws.Ordering(ws.Summary("filings_per_second"), ascending=False)


def i2():
    scores = bars(("valid/status_agree_weighted", "Validation: agreement, weighted"),
                  ("valid/status_agree_on_ceo_changes", "Validation: agreement on CEO changes"),
                  ("test/status_agree_weighted", "Test: agreement, weighted"),
                  ("test/status_agree_on_ceo_changes", "Test: agreement on CEO changes"))
    training = [wr.LinePlot(title="Training loss", y=["loss"]),
                wr.LinePlot(title="Seconds per filing", y=["seconds_per_item"])]
    settings = wr.ParallelCoordinatesPlot(title="Settings against validation agreement on CEO changes", columns=[
        wr.ParallelCoordinatesPlotColumn(metric=wr.Config(k)) for k in ("gpu", "lora", "lr", "accum", "weights_dtype")] + [
        wr.ParallelCoordinatesPlotColumn(metric=wr.SummaryMetric("valid/status_agree_on_ceo_changes"))])
    columns = ["config:user", "config:gpu", "config:init_from", "config:lora", "config:lr", "config:accum",
               "config:weights_dtype", "config:max_steps", "summary:valid/status_agree_weighted",
               "summary:valid/status_agree_on_ceo_changes", "summary:test/status_agree_weighted",
               "summary:test/status_agree_on_ceo_changes"]
    sections = [ws.Section(name="Scores", panels=scores, is_open=True),
                ws.Section(name="Training", panels=training, is_open=True),
                ws.Section(name="Compare settings", panels=[settings], is_open=True)]
    # Sorted by validation, the set settings are chosen on
    return sections, columns, ws.Ordering(ws.Summary("valid/status_agree_weighted"), ascending=False)


LAYOUTS = {1: i1, 2: i2}


# wandb-workspaces 0.4.13 builds and reads links without the /wandb/ path this server's W&B app is under
def browser_link(url):
    u = urlparse(url)
    return u._replace(path="/wandb" + quote(u.path)).geturl()


def library_link(url):
    u = urlparse(unquote(url))
    return u._replace(path=u.path.removeprefix("/wandb")).geturl()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exercise", type=int, choices=LAYOUTS, help="1 for Intermediate Exercise 1, 2 for Exercise 2")
    ap.add_argument("--entity", default="Marlowe-Hackathon")
    ap.add_argument("--url", help="the Board view's link, to lay it out again instead of saving a new view")
    a = ap.parse_args()
    sections, columns, order = LAYOUTS[a.exercise]()
    if a.url:
        view = ws.Workspace.from_url(library_link(a.url))
    else:
        view = ws.Workspace(entity=a.entity, project=f"Intermediate Exercise {a.exercise}", name="Board")
    view.sections = sections
    view.runset_settings = ws.RunsetSettings(pinned_columns=columns, order=[order])
    view.settings = ws.WorkspaceSettings(max_runs=100)
    view.save()
    print(browser_link(view.url))


if __name__ == "__main__":
    main()
