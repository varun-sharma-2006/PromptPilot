"""Prompt-version experiment for T1 (Generate MCQs).

Runs one T1 prompt version on the same inputs, several times each, and saves every
raw output plus the automatic check results.

    python code/run_iterations.py v1 [--repeats 3]

Inputs (fixed across versions):
  P1_rti  medium 5 | P2_gem easy 5 | P4_sbm hard 4 | P3_cvc (short) 6
  P3_cvc is deliberately too short for 6 good questions, to test the "return fewer" rule.

    python code/run_iterations.py v1 --judge-only   # add rubric scores to a saved run

Rubric scores come from one FIXED judge prompt (prompts/v2/T2_review.txt, temperature 0) for every
version, so versions are compared with the same yardstick. The judge is an LLM, not a human.
"""
import argparse
import collections
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import checks  # noqa: E402
import llm  # noqa: E402
import prompts  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PASSAGES = ROOT / "test-data" / "passages"
OUT = ROOT / "test-data" / "outputs" / "iterations"

INPUTS = [
    ("P1_rti", "medium", 5),
    ("P2_gem", "easy", 5),
    ("P4_sbm", "hard", 4),
    ("P3_cvc", "medium", 6),
]


def passage(pid):
    return json.loads((PASSAGES / f"{pid}.json").read_text(encoding="utf-8"))


def run_version(version, repeats):
    p = prompts.load(version, "T1_generate")
    runs = []
    for pid, diff, n in INPUTS:
        meta = passage(pid)
        for r in range(repeats):
            user = prompts.fill(p["user"], N=n, DIFFICULTY=diff, COMPETENCY=meta["competency"],
                                PASSAGE=meta["text"], KEY_ORDER=prompts.key_order(n, seed=r))
            text, info = llm.call(user, p["system"], p["temperature"], p["json_mode"])
            obj, err = llm.parse_json(text)
            letters = prompts.key_order(n, seed=r).split(", ")
            res = checks.check_run(obj, meta["text"], letters)
            runs.append({
                "input": pid, "difficulty": diff, "n_requested": n, "repeat": r + 1,
                "meta": info, "parse_error": err, "checks": res, "raw_output": text, "key_letters": letters,
            })
            print(f"{version} {pid} r{r+1}: json={res['json_ok']} schema={res['schema_ok']} n={res['n_questions']}")
    return runs


JUDGE = ("v2", "T2_review")
RUBRIC = ("faithful", "single_key", "plausible_distractors", "clear", "right_level")


def judge(runs):
    p = prompts.load(*JUDGE)
    for r in runs:
        obj, _ = llm.parse_json(r["raw_output"])
        qs = checks.extract_questions(obj, r.get("key_letters")) if obj is not None else None
        if not qs:
            r["judge"] = []
            continue
        meta = passage(r["input"])
        numbered = [dict(id=i + 1, **q) if isinstance(q, dict) else {"id": i + 1, "raw": q} for i, q in enumerate(qs)]
        user = prompts.fill(p["user"], DIFFICULTY=r["difficulty"], PASSAGE=meta["text"],
                            QUESTIONS_JSON=json.dumps(numbered, ensure_ascii=False, indent=2))
        text, _ = llm.call(user, p["system"], p["temperature"], p["json_mode"])
        jo, _ = llm.parse_json(text)
        r["judge"] = (jo or {}).get("reviews", []) if isinstance(jo, dict) else []
        print(f"judged {r['input']} r{r['repeat']}: {sum(x.get('verdict') == 'pass' for x in r['judge'])}/{len(qs)} pass")


def repeated_sources(r):
    """Questions in one run whose source_sentence is the same as another question's."""
    obj, _ = llm.parse_json(r["raw_output"])
    qs = (checks.extract_questions(obj, r.get("key_letters")) or []) if obj is not None else []
    srcs = [checks._norm(str(q.get("source_sentence", ""))).lower() for q in qs if isinstance(q, dict)]
    return sum(srcs.count(s) > 1 for s in srcs)


def summarise(runs):
    per_q = [q for r in runs for q in r["checks"]["per_question"]]
    pos = collections.Counter(p for r in runs for p in r["checks"].get("answer_positions", []))
    short = [r for r in runs if r["input"] == "P3_cvc"]
    out = {
        "runs": len(runs),
        "json_valid": sum(r["checks"]["json_ok"] for r in runs),
        "schema_valid": sum(r["checks"]["schema_ok"] for r in runs),
        "questions": len(per_q),
        "quote_verbatim": sum(q["quote_verbatim"] for q in per_q),
        "four_distinct_options": sum(q["four_options"] for q in per_q),
        "count_as_requested_normal": sum(
            r["checks"]["n_questions"] == r["n_requested"] for r in runs if r["input"] != "P3_cvc"),
        "normal_runs": sum(r["input"] != "P3_cvc" for r in runs),
        "short_passage_question_counts": [r["checks"]["n_questions"] for r in short],
        "answer_positions": dict(sorted(pos.items())),
        "questions_sharing_a_source_sentence": sum(repeated_sources(r) for r in runs),
    }
    judged = [j for r in runs for j in r.get("judge", [])]
    if judged:
        out["judge_questions"] = len(judged)
        out["judge_pass"] = sum(j.get("verdict") == "pass" for j in judged)
        for k in RUBRIC:
            out[f"judge_{k}"] = sum(int(j.get("scores", {}).get(k, 0)) for j in judged)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--judge-only", action="store_true")
    a = ap.parse_args()
    path = OUT / f"T1_{a.version}.json"
    if a.judge_only:
        runs = json.loads(path.read_text(encoding="utf-8"))["runs"]
    else:
        runs = run_version(a.version, a.repeats)
    judge(runs)
    summary = summarise(runs)
    OUT.mkdir(parents=True, exist_ok=True)
    out = {
        "prompt": f"{a.version}/T1_generate",
        "date": datetime.date.today().isoformat(),
        "model": llm.MODEL,
        "summary": summary,
        "runs": runs,
    }
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
