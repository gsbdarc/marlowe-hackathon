"""Turn a teacher's answers from label.py into Kev training records, for a student to learn from.

label.py --api chat saves one line per filing with the choice the teacher wrote for each question. This script finds
each filing in train.jsonl (same id) and replaces Jev's labels with the teacher's. A teacher that writes its answer
gives no probabilities, so every target puts all its weight on the teacher's choice (a hard label). As with Jev's
labels, a filing the teacher calls "not a CEO change" keeps only the status question.

It also writes the same filings with Jev's labels, so you can train a second student on the same filings and see
whether the teacher made the difference.

    $PY scripts/make_teacher_data.py $WORK/results/qwen-235b-train.jsonl
    # writes $WORK/data/teacher-qwen-235b-train.jsonl and $WORK/data/teacher-jev.jsonl
"""
import argparse
import json
import os

from questions import STATUS, questions

NOT_A_CHANGE = STATUS[1]


def one_hot(options, choice):
    return {o: float(o == choice) for o in options}


def teacher_record(rec, answers):
    status = answers["status"]["choice"]
    q = questions(with_why=status != NOT_A_CHANGE)
    q["status"]["label"] = status
    q["status"]["target"] = one_hot(q["status"]["criteria"], status)
    if status != NOT_A_CHANGE:
        why = answers["why"]["choice"]
        future = answers["future"]["noul"] >= 0.5
        q["why"]["label"] = why
        q["why"]["target"] = one_hot(q["why"]["criteria"], why)
        q["future"]["label"] = future
        q["future"]["target"] = {"false": float(not future), "true": float(future)}
    return {"state": rec["state"], "questions": q, "_meta": rec["_meta"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("answers", help="label.py --out file with the teacher's answers on training filings")
    ap.add_argument("--data", default=os.path.join(os.environ.get("WORK", "."), "data", "train.jsonl"))
    ap.add_argument("--out", help="default: $WORK/data/teacher-<name of the answers file>.jsonl")
    ap.add_argument("--jev-out", help="default: $WORK/data/teacher-jev.jsonl")
    a = ap.parse_args()
    data_dir = os.path.dirname(os.path.abspath(a.data))
    name = os.path.splitext(os.path.basename(a.answers))[0]
    out = a.out or os.path.join(data_dir, f"teacher-{name}.jsonl")
    jev_out = a.jev_out or os.path.join(data_dir, "teacher-jev.jsonl")

    answers = {}
    for line in open(a.answers):
        r = json.loads(line)
        if r.get("ok") and r.get("answers"):
            answers[r["id"]] = r["answers"]

    n = changes = 0
    with open(out, "w") as fo, open(jev_out, "w") as fj:
        for line in open(a.data):
            rec = json.loads(line)
            ans = answers.get(rec["_meta"]["id"])
            if ans is None:
                continue
            t = teacher_record(rec, ans)
            fo.write(json.dumps(t) + "\n")
            fj.write(line if line.endswith("\n") else line + "\n")
            n += 1
            changes += t["questions"]["status"]["label"] != NOT_A_CHANGE
    print(f"{len(answers):,} teacher answers; {n:,} filings matched in {a.data}")
    print(f"the teacher calls {changes:,} of them CEO changes")
    print(f"wrote {out}")
    print(f"wrote {jev_out} (the same filings with Jev's labels)")


if __name__ == "__main__":
    main()
