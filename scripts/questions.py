"""Jev's three questions about an Item 5.02 filing, and the text Jev reads.

Copied from Alex Storer's item502/questions.py (questions version 2026-10-24) so the labels mean the same thing here.
The option wording is the label: change a word and you change the task.
"""

QUESTIONS_VERSION = "2026-10-24"

STATUS = {   # what happens to the CEO
    1: "the CEO is not leaving the CEO position (the filing is about someone else)",
    2: "the CEO is stepping away temporarily (medical or other leave) and is expected to return",
    3: "the CEO gives up the CEO title and becomes executive chair",
    4: "the CEO gives up the CEO title and becomes non-executive (independent) chair",
    5: "the CEO gives up the CEO title and stays only as a board member (not chair)",
    6: "the CEO gives up the CEO title but stays at the company in another executive or advisory role",
    7: "the CEO is leaving the company entirely (including death)",
    8: "an interim or acting CEO is stepping aside for a permanent one",
}
STATUS_SHORT = {1: "not a CEO change", 2: "temporary leave", 3: "becomes exec chair", 4: "becomes non-exec chair",
                5: "director only", 6: "other role at company", 7: "leaves entirely", 8: "interim steps aside"}

REASON = {   # why, judged from the filing only
    1: "the departing CEO died in office",
    2: "the departing CEO left because of illness",
    3: "the departing CEO was pushed out over job performance",
    4: "the departing CEO was dismissed over legal or policy violations",
    5: "the departing CEO retired voluntarily",
    6: "the departing CEO left for a new job or venture",
    7: "other: interim CEO stepping aside, merger or acquisition, company closed, or not a real turnover",
    8: "the filing gives no reason for the departure",
}
REASON_SHORT = {1: "died", 2: "illness", 3: "performance", 4: "legal/policy", 5: "retired", 6: "new job", 7: "other", 8: "no reason"}

STATUS_INSTRUCTIONS = "What happens to the company's chief executive officer, according to this filing?"
WHY_INSTRUCTIONS = ("If the chief executive is leaving the CEO position, why, according to this filing? "
                    "Judge only from what the filing says.")
FUTURE_INSTRUCTIONS = ("Does the change to the CEO position take effect at a future date (announced in advance), "
                       "rather than immediately or already?")


def state(company, date_filed, text_502, max_chars=40_000):
    """What the model reads: a two-line header and the Item 5.02 text, as in Jev's labeling run."""
    return f"{company}\nForm 8-K filed {date_filed}, Item 5.02\n\n{text_502}"[:max_chars]


def questions(with_why=True):
    """The questions in the System One request shape (Jev's API, which Kev serves)."""
    q = {"status": {"type": "choice", "instructions": STATUS_INSTRUCTIONS, "criteria": {v: None for v in STATUS.values()}}}
    if with_why:
        q["why"] = {"type": "choice", "instructions": WHY_INSTRUCTIONS, "criteria": {v: None for v in REASON.values()}}
        q["future"] = {"type": "noul", "instructions": FUTURE_INSTRUCTIONS}
    return q
