"""Lay out an exercise's W&B project for the board: who ran what, with which options, and the scores side by side.

Everyone at the hackathon shares one W&B key, so W&B's own User column is the same for every run; the table shows config.user, the
SUNet ID each job records. Scores live in each run's summary (score.py), which W&B's default workspace doesn't chart,
so this saves a view named "Board" with a runs table and charts of those numbers: for I1, mostly scatter plots
(one point per run) of speed against agreement, batch size, latency and memory, and bars averaged by option. I3 and I4
open with "Who is leading", the runs sorted by validation agreement on CEO changes; I5 sorts by filings per second.

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


def scatter(title, x, y, z=None, **kw):
    """One point per run. x, y and z (the points' color) are summary names, or ("config", name) for a setting."""
    m = lambda k: k and (wr.Config(k[1]) if isinstance(k, tuple) else wr.SummaryMetric(k))
    return wr.ScatterPlot(title=title, x=m(x), y=m(y), z=m(z), **kw)


def by_option(title, key, option):
    """A bar per value of the option (config), the mean of its runs, with their range."""
    return wr.BarPlot(title=title, metrics=[wr.SummaryMetric(key)], orientation="v", groupby=wr.Config(option),
                      groupby_aggfunc="mean", groupby_rangefunc="minmax")


def i1():
    batch = ("config", "concurrency")
    tradeoff = [scatter("Speed against agreement (color: batch size)", "filings_per_second", "test/status_agree_weighted", batch),
                scatter("Speed against agreement on CEO changes", "filings_per_second", "test/status_agree_on_ceo_changes", batch)]
    batches = [scatter("Batch size against filings per second", batch, "filings_per_second"),
               scatter("Batch size against seconds per filing (median)", batch, "latency_p50"),
               scatter("Batch size asked for against the batch the server ran", batch, "mean_batch"),
               scatter("Batch size against peak GPU memory (GB)", batch, "gpu_memory_peak_gb")]
    speed = [scatter("Seconds per filing (median) against filings per second", "latency_p50", "filings_per_second"),
             scatter("Peak GPU memory (GB) against filings per second", "gpu_memory_peak_gb", "filings_per_second"),
             scatter("Job time (s, load + label) against filings labeled", "total_seconds", "succeeded"),
             wr.LinePlot(title="Filings per second while labeling", y=["filings_per_second_so_far"])]
    options = [by_option("Filings per second by GPU", "filings_per_second", "gpu"),
               by_option("Filings per second by number format", "filings_per_second", "dtype"),
               by_option("Filings per second by fused kernels", "filings_per_second", "fused"),
               by_option("Peak GPU memory (GB) by number format", "gpu_memory_peak_gb", "dtype")]
    scores = bars(("test/status_agree_weighted", "Agreement with Jev, weighted to all test filings"),
                  ("test/status_agree_on_ceo_changes", "Agreement with Jev on CEO changes"),
                  ("filings_per_second", "Filings per second"),
                  ("succeeded", "Filings labeled (of 1,000, within 10 minutes)"))
    compare = wr.ParallelCoordinatesPlot(title="Options against speed and agreement", columns=[
        wr.ParallelCoordinatesPlotColumn(metric=wr.Config(k)) for k in ("gpu", "concurrency", "dtype", "fused")] + [
        wr.ParallelCoordinatesPlotColumn(metric=wr.SummaryMetric(k)) for k in ("filings_per_second", "test/status_agree_weighted")])
    columns = ["config:user", "config:gpu", "config:concurrency", "config:dtype", "config:fused",
               "summary:succeeded", "summary:cut_off", "summary:load_seconds", "summary:wall_seconds", "summary:total_seconds",
               "summary:filings_per_second", "summary:latency_p50", "summary:mean_batch", "summary:gpu_memory_peak_gb",
               "summary:test/status_agree_weighted", "summary:test/status_agree_on_ceo_changes", "summary:test/ceo_change_f1"]
    sections = [ws.Section(name="Speed against agreement", panels=tradeoff, is_open=True),
                ws.Section(name="What batch size does", panels=batches, is_open=True),
                ws.Section(name="Speed, waiting and memory", panels=speed, is_open=True),
                ws.Section(name="Each option on average", panels=options, is_open=True),
                ws.Section(name="Scores, run by run", panels=scores, is_open=True),
                ws.Section(name="Compare options", panels=[compare], is_open=True)]
    return sections, columns, ws.Ordering(ws.Summary("filings_per_second"), ascending=False)


def i2():
    ceo = "valid/status_agree_on_ceo_changes"
    held_out = [scatter("Validation against test: agreement, weighted", "valid/status_agree_weighted", "test/status_agree_weighted"),
                scatter("Validation against test: agreement on CEO changes", ceo, "test/status_agree_on_ceo_changes")]
    training = [wr.LinePlot(title="Training loss", y=["loss"]),
                scatter("Final training loss against validation agreement on CEO changes", "loss", ceo),
                wr.LinePlot(title="Seconds per filing", y=["seconds_per_item"])]
    settings = [scatter("Learning rate against validation agreement on CEO changes", ("config", "lr"), ceo, log_x=True),
                scatter("Filings per step against validation agreement on CEO changes", ("config", "accum"), ceo),
                scatter("Adapter rank against validation agreement on CEO changes", ("config", "lora"), ceo),
                by_option("Validation agreement on CEO changes by number format", ceo, "weights_dtype"),
                by_option("Validation agreement on CEO changes by GPU", ceo, "gpu")]
    scores = bars(("valid/status_agree_weighted", "Validation: agreement, weighted"),
                  (ceo, "Validation: agreement on CEO changes"),
                  ("test/status_agree_weighted", "Test: agreement, weighted"),
                  ("test/status_agree_on_ceo_changes", "Test: agreement on CEO changes"))
    compare = wr.ParallelCoordinatesPlot(title="Settings against validation agreement on CEO changes", columns=[
        wr.ParallelCoordinatesPlotColumn(metric=wr.Config(k)) for k in ("gpu", "lora", "lr", "accum", "weights_dtype")] + [
        wr.ParallelCoordinatesPlotColumn(metric=wr.SummaryMetric(ceo))])
    columns = ["config:user", "config:gpu", "config:init_from", "config:lora", "config:lr", "config:accum",
               "config:weights_dtype", "config:max_steps", "summary:loss", "summary:valid/status_agree_weighted",
               "summary:valid/status_agree_on_ceo_changes", "summary:test/status_agree_weighted",
               "summary:test/status_agree_on_ceo_changes"]
    sections = [ws.Section(name="Validation against test", panels=held_out, is_open=True),
                ws.Section(name="Training", panels=training, is_open=True),
                ws.Section(name="What each setting does", panels=settings, is_open=True),
                ws.Section(name="Scores, run by run", panels=scores, is_open=True),
                ws.Section(name="Compare settings", panels=[compare], is_open=True)]
    # Sorted by validation, the set settings are chosen on
    return sections, columns, ws.Ordering(ws.Summary("valid/status_agree_weighted"), ascending=False)


def leading(*keys):
    """The leaderboard: one bar per run, in the table's order (best first)."""
    return ws.Section(name="Who is leading", panels=bars(*keys), is_open=True)


def i3():
    ceo = "valid/status_agree_on_ceo_changes"
    held_out = [scatter("Validation against test: agreement on CEO changes", ceo, "test/status_agree_on_ceo_changes"),
                scatter("Validation against test: agreement, weighted", "valid/status_agree_weighted", "test/status_agree_weighted")]
    training = [wr.LinePlot(title="Training loss", y=["loss"]),
                scatter("Final training loss against validation agreement on CEO changes", "loss", ceo),
                wr.LinePlot(title="Seconds per filing", y=["seconds_per_item"])]
    settings = [by_option("Validation agreement on CEO changes: LoRA (16) or full fine-tune", ceo, "lora"),
                scatter("Learning rate against validation agreement on CEO changes", ("config", "lr"), ceo, log_x=True),
                scatter("Filings per step against validation agreement on CEO changes", ("config", "accum"), ceo),
                scatter("Steps against validation agreement on CEO changes", ("config", "max_steps"), ceo)]
    compare = wr.ParallelCoordinatesPlot(title="Settings against validation agreement on CEO changes", columns=[
        wr.ParallelCoordinatesPlotColumn(metric=wr.Config(k)) for k in ("lora", "lr", "accum", "max_steps")] + [
        wr.ParallelCoordinatesPlotColumn(metric=wr.SummaryMetric(ceo))])
    columns = ["config:user", "config:lora", "config:lr", "config:accum", "config:max_steps", "config:weights_dtype",
               "summary:loss", "summary:valid/status_agree_on_ceo_changes", "summary:valid/ceo_change_f1",
               "summary:valid/status_agree_weighted", "summary:test/status_agree_on_ceo_changes"]
    sections = [leading((ceo, "Validation: agreement on CEO changes"), ("valid/ceo_change_f1", "Validation: CEO-change F1"),
                        ("valid/status_agree_weighted", "Validation: agreement, weighted")),
                ws.Section(name="Validation against test", panels=held_out, is_open=True),
                ws.Section(name="Training", panels=training, is_open=True),
                ws.Section(name="What each setting does", panels=settings, is_open=True),
                ws.Section(name="Compare settings", panels=[compare], is_open=True)]
    return sections, columns, ws.Ordering(ws.Summary(ceo), ascending=False)


def i4():
    ceo = "valid/status_agree_on_ceo_changes"
    speed = [scatter("Seconds per filing (per GPU) against validation agreement on CEO changes (color: GPUs)",
                     "seconds_per_item", ceo, ("config", "gpus")),
             scatter("GPUs against seconds per filing (per GPU)", ("config", "gpus"), "seconds_per_item"),
             by_option("Seconds per filing (per GPU) by method: LoRA (16) or full fine-tune", "seconds_per_item", "lora")]
    methods = [by_option("Validation agreement on CEO changes by method: LoRA (16) or full fine-tune", ceo, "lora"),
               by_option("Validation agreement on CEO changes by GPUs (8: 10,000 filings; 4: 4,800)", ceo, "gpus"),
               scatter("Learning rate against validation agreement on CEO changes", ("config", "lr"), ceo, log_x=True),
               scatter("Steps against validation agreement on CEO changes", ("config", "max_steps"), ceo)]
    training = [wr.LinePlot(title="Training loss", y=["loss"]),
                wr.LinePlot(title="Seconds per step", y=["seconds_per_step"])]
    held_out = [scatter("Validation against test: agreement on CEO changes", ceo, "test/status_agree_on_ceo_changes")]
    columns = ["config:user", "config:gpus", "config:lora", "config:lr", "config:accum", "config:max_steps",
               "summary:seconds_per_item", "summary:loss", "summary:valid/status_agree_on_ceo_changes",
               "summary:valid/ceo_change_f1", "summary:test/status_agree_on_ceo_changes"]
    sections = [leading((ceo, "Validation: agreement on CEO changes"), ("valid/ceo_change_f1", "Validation: CEO-change F1")),
                ws.Section(name="Method, GPUs and settings", panels=methods, is_open=True),
                ws.Section(name="Speed", panels=speed, is_open=True),
                ws.Section(name="Training", panels=training, is_open=True),
                ws.Section(name="Validation against test", panels=held_out, is_open=True)]
    return sections, columns, ws.Ordering(ws.Summary(ceo), ascending=False)


def i5():
    gpus = ("config", "gpus")
    scaling = [scatter("GPUs against filings per second", gpus, "filings_per_second"),
               scatter("GPUs against filings per second per GPU", gpus, "filings_per_second_per_gpu"),
               scatter("GPUs against hours to label all 296,477 filings", gpus, "all_filings_hours"),
               scatter("GPUs against GPU-hours to label all 296,477 filings", gpus, "all_filings_gpu_hours"),
               scatter("GPUs against load time (s)", gpus, "load_seconds")]
    cost = bars(("all_filings_gpu_dollars", "GPUs $ for all 296,477 filings, at $3 per GPU-hour"),
                ("all_filings_jev_dollars", "Jev $ for the same filings"))
    columns = ["config:user", "config:gpus", "config:node", "summary:filings", "summary:failed",
               "summary:filings_per_second", "summary:filings_per_second_per_gpu", "summary:load_seconds",
               "summary:label_minutes", "summary:all_filings_hours", "summary:all_filings_gpu_hours",
               "summary:all_filings_gpu_dollars"]
    sections = [leading(("filings_per_second", "Filings per second, all the job's GPUs"),
                        ("filings_per_second_per_gpu", "Filings per second per GPU")),
                ws.Section(name="How it scales", panels=scaling, is_open=True),
                ws.Section(name="What it costs", panels=cost, is_open=True)]
    return sections, columns, ws.Ordering(ws.Summary("filings_per_second"), ascending=False)


LAYOUTS = {1: i1, 2: i2, 3: i3, 4: i4, 5: i5}


# wandb-workspaces 0.4.13 builds and reads links without the /wandb/ path this server's W&B app is under
def browser_link(url):
    u = urlparse(url)
    return u._replace(path="/wandb" + quote(u.path)).geturl()


def library_link(url):
    u = urlparse(unquote(url))
    return u._replace(path=u.path.removeprefix("/wandb")).geturl()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exercise", type=int, choices=LAYOUTS, help="the Intermediate exercise, 1 to 5")
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
