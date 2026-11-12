"""B5, your own analysis: five short exercises on the labels you made in B4. Edit this file, then run it:

    $PY scripts/beginner/my_analysis.py $WORK/results/b4/$ONE $WORK/results/b4/$MINE

Each exercise has a TODO. Until you fill one in, the script says it is not done yet and moves on, so you can run the
file after every change. The B5 page has hints and a worked answer for each. Each run also puts your progress, your
Exercise 5 slopes and your charts on the room's W&B board (project beginner-5-analysis, under your SUNet ID).
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")                  # draw to a file: there is no screen on a cluster
import matplotlib.pyplot as plt        # noqa: E402
import pandas as pd                    # noqa: E402
from scipy.stats import linregress     # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from findings import load              # noqa: E402
from wandb_log import analysis         # noqa: E402

pd.set_option("display.width", 120)
OUT = os.environ.get("WORK", ".")      # where the charts go: $WORK, your folder in scratch

# One row per filing. The columns you need:
#   year, month          when the filing was made (month is 1 to 12)
#   cik, company_name    the company (cik is the SEC's number for it)
#   words                how long the Item 5.02 text is, in words
#   kev_change           True if Kev says the CEO is leaving the job
#   kev_status_conf      how sure Kev was of that answer, from 0 to 1
#   kev_forced           True if Kev says the CEO left and was forced out (performance, or legal or policy)
#   kev_future           Kev's probability, 0 to 1, that the change was announced ahead of time
#   status               Jev's answer: 1 means not a CEO change, 2 to 8 are kinds of CEO change
#   p_future             Jev's probability that the change was announced ahead of time
d = load(sys.argv[1:])
d["jev_change"] = d.status != 1        # True if Jev says the CEO is leaving the job


def chart(table, title, ylabel, filename, kind="line"):
    """Draw a table or a series to a PNG in $WORK: one line per column, the index along the bottom.
    kind="bar" or kind="barh" draws bars instead, for a table that is not a time series (companies, say)."""
    ax = table.plot(kind=kind, figsize=(8, 4.5), title=title, marker="o" if kind == "line" else None)
    ax.set_ylabel(ylabel)
    ax.get_figure().tight_layout()
    ax.get_figure().savefig(os.path.join(OUT, filename), dpi=150)
    plt.close(ax.get_figure())
    print(f"saved {os.path.join(OUT, filename)}")


# ---------------------------------------------------------------------------------------------------------------------
# Exercise 1. CEO changes per 100 filings, by year, from Kev. It should match the Kev column of `findings.py trend`.
# Hint: d.groupby("year") groups the filings by year; .kev_change.mean() is the share that are CEO changes.
per_year = None                        # TODO: replace None with your answer

if per_year is None:
    print("Exercise 1: not done yet\n")
else:
    print("Exercise 1: CEO changes per 100 filings, by Kev\n")
    print(per_year.round(1).to_string(), "\n")


# ---------------------------------------------------------------------------------------------------------------------
# Exercise 2. Can confidence fix the trend? Keep only the filings Kev was at least MIN_CONF sure of, and compare Kev's
# and Jev's CEO changes per 100 filings by year on those filings. Try MIN_CONF = 0.5, then 0.8.
MIN_CONF = 0.5
sure = None                            # TODO: the rows of d where kev_status_conf is at least MIN_CONF
compare = None                         # TODO: a table by year with three columns: kev, jev and kept (the share of filings kept)

if compare is None:
    print("Exercise 2: not done yet\n")
else:
    print(f"Exercise 2: per 100 filings, on the filings Kev was at least {MIN_CONF:.0%} sure of\n")
    print(compare.round(1).to_string(), "\n")


# ---------------------------------------------------------------------------------------------------------------------
# Exercise 3. A chart: Kev's and Jev's CEO changes per 100 filings, by year, as two lines. Saved as a PNG to copy to
# your laptop. Fill in the two series; the drawing code is done for you.
kev_line = None                        # TODO: CEO changes per 100 filings by year, from Kev (all filings)
jev_line = None                        # TODO: the same from Jev

if kev_line is None or jev_line is None:
    print("Exercise 3: not done yet\n")
else:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(kev_line.index, kev_line.values, marker="o", label="Kev-4B as released")
    ax.plot(jev_line.index, jev_line.values, marker="o", label="Jev")
    ax.set_xlabel("year filed")
    ax.set_ylabel("CEO changes per 100 Item 5.02 filings")
    ax.set_title("CEO turnover by year: same filings, two labelers")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "b5-trend.png"), dpi=150)
    print(f"Exercise 3: saved {os.path.join(OUT, 'b5-trend.png')}\n")


# ---------------------------------------------------------------------------------------------------------------------
# Exercise 4. Your own question. Pick one, compute a table in `mine`, and draw it to b5-mine.png with chart():
#   a. Do CEO changes cluster in some months of the year? (month)
#   b. Which companies changed CEO most often? (cik, company_name)
#   c. Are CEO changes announced ahead of time more often now than in 2005? (kev_future, p_future)
#   d. Are forced departures described in longer filings? (words, kev_forced)
mine = None                            # TODO: your table (a few lines of your own above this one are fine)

if mine is None:
    print("Exercise 4: not done yet")
else:
    print("Exercise 4\n")
    print(mine.round(2).to_string() if hasattr(mine, "to_string") else mine)   # a table, or a single number
# TODO, once `mine` is a table: draw it by taking the # off the next line and changing the title and label.
# chart(mine, "My title", "what the numbers are", "b5-mine.png")


# ---------------------------------------------------------------------------------------------------------------------
# Exercise 5. A regression. On the filings from 2004 to 2019, regress CEO change (0 or 1, times 100, so the slope is in
# CEO changes per 100 filings) on the year, once with Kev's labels and once with Jev's. linregress(x, y) returns the
# slope and its standard error (.slope, .stderr). Same filings, same regression: only the labels differ.
# Hint: p = d[d.year.between(2004, 2019)], then linregress(p.year, p.kev_change.astype(float) * 100).
kev_fit = None                         # TODO: the regression with Kev's labels
jev_fit = None                         # TODO: the same with Jev's

if kev_fit is None or jev_fit is None:
    print("\nExercise 5: not done yet")
else:
    print("\nExercise 5: CEO changes per 100 filings, regressed on year, 2004 to 2019\n")
    for name, fit in [("Kev", kev_fit), ("Jev", jev_fit)]:
        print(f"{name}: slope {fit.slope:+.3f} a year, standard error {fit.stderr:.3f}, t = {fit.slope / fit.stderr:.1f}")


# ---------------------------------------------------------------------------------------------------------------------
# Your progress on the room's board: which exercises are done, your slopes, and your charts. Nothing to change here.
done = {"e1": per_year is not None, "e2": compare is not None, "e3": kev_line is not None and jev_line is not None,
        "e4": mine is not None, "e5": kev_fit is not None and jev_fit is not None}
charts = [os.path.join(OUT, f) for f, e in (("b5-trend.png", "e3"), ("b5-mine.png", "e4")) if done[e]]
analysis(done, kev_fit, jev_fit, charts)
