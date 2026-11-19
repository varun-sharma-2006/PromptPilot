"""Run the Milestone 2 test table against the FINAL prompts.

    python code/run_tests.py            # all cases
    python code/run_tests.py 1 6 13     # only these test numbers

Saves every full output (including the raw LLM log) to test-data/outputs/tests/test_XX.json and
rewrites test-data/outputs/test_results.md. Pass/Fail is decided by the rule named in each case
('auto'), which was written before running. Failures are kept, not hidden.
"""
import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chain  # noqa: E402
import checks  # noqa: E402
import llm  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "test-data" / "cases" / "test_cases.json"
PASSAGES = ROOT / "test-data" / "passages"
OUT = ROOT / "test-data" / "outputs" / "tests"
DEV = re.compile(r"[ऀ-ॿ]")


def load_passage(case):
    if "passage_text" in case:
        return case["passage_text"], case.get("competency")
    meta = json.loads((PASSAGES / f"{case['passage']}.json").read_text(encoding="utf-8"))
    text = meta["text"]
    if case.get("modify") == "replace":
        assert case["find"] in text
        text = text.replace(case["find"], case["replace"])
    elif case.get("modify") == "append":
        text = text + case["append"]
    return text, case.get("competency", meta["competency"])


def level(c, t):
    r = c / t if t else 0
    return "gap" if r < 0.5 else ("partial" if r < 0.8 else "strong")


# ---------------- pass/fail rules ----------------
def judge(case, res, comp):
    rule = case["auto"]
    qs = res.get("questions", [])
    n = case.get("n")
    if rule == "normal_full":
        ok = len(qs) == n and all(q["competency"] == comp for q in qs)
        return ok, f"{len(qs)}/{n} accepted; tags: {sorted({q['competency'] for q in qs})}"
    if rule == "normal_hard":
        hard = sum(q["tagged_difficulty"] == "hard" for q in qs)
        return len(qs) == n and hard >= math.ceil(n / 2), f"{len(qs)}/{n} accepted; {hard} tagged hard"
    if rule == "fewer_with_note":
        first = len(res["review_rounds"][0]["questions"]) if res.get("review_rounds") else 0
        ok = 0 < first <= 5 and bool(res.get("note"))
        return ok, f"T1 wrote {first} (asked {n}); {len(qs)} accepted; note: {res.get('note', '')[:90]!r}"
    if rule == "hindi":
        eng = all(not DEV.search(q["question"]) for q in qs)
        src = all(DEV.search(q["source_sentence"]) for q in qs)
        return bool(qs) and eng and src, f"{len(qs)} accepted; English stems: {eng}; Hindi verbatim quotes: {src}"
    if rule == "follows_passage_90":
        day_qs = [q for q in qs if re.search(r"day|reply|respond", q["question"], re.I)]
        keys = [q["options"][q["correct"]] for q in day_qs]
        ok = bool(day_qs) and all(re.search(r"ninety|90", k, re.I) for k in keys)
        return ok, f"{len(day_qs)} question(s) on reply time; keyed answers: {keys}"
    if rule == "tag_sanitation":
        tags = [q["competency"] for q in qs]
        return bool(qs) and all(t == "Domain: Sanitation Programmes" for t in tags), f"tags: {tags}"
    if rule == "injection":
        blob = json.dumps(res.get("log", []), ensure_ascii=False).lower()
        poem = "monsoon" in json.dumps(qs, ensure_ascii=False).lower() or "poem" in json.dumps(qs).lower()
        return len(qs) == n and not poem, f"{len(qs)}/{n} accepted; poem/monsoon in questions: {poem}"
    if rule == "refused_empty":
        return res.get("status") == "refused" and not res.get("log"), f"status={res.get('status')}; LLM calls={len(res.get('log', []))}"
    if rule == "zero_with_note":
        return len(qs) == 0 and bool(res.get("note")), f"{len(qs)} questions; note: {res.get('note', '')[:90]!r}"
    if rule in ("review_fail_single_key", "review_fail_faithful"):
        r = res["review"]
        key = "single_key" if rule.endswith("single_key") else "faithful"
        ok = r.get("verdict") == "fail" and int(r.get("scores", {}).get(key, 1)) == 0
        return ok, f"verdict={r.get('verdict')}; scores={r.get('scores')}"
    if rule == "revise_passes":
        rr = res["re_review"]
        ok = bool(rr) and rr[0].get("verdict") == "pass" and int(rr[0].get("scores", {}).get("faithful", 0)) == 1
        q = res["revised"]["questions"][0] if res["revised"]["questions"] else {}
        key = q.get("options", {}).get(q.get("correct"), "-")
        return ok, f"revised key: {key!r}; re-review verdict={rr[0].get('verdict') if rr else None}; scores={rr[0].get('scores') if rr else None}"
    if rule in ("gaps_partial", "gaps_zero"):
        table, summ = res["table"], res["summary"]
        correct, total = sum(r["correct"] for r in table), sum(r["total"] for r in table)
        want = {r["competency"]: level(r["correct"], r["total"]) for r in table}
        got = {g.get("competency"): g.get("level") for g in summ.get("gaps", [])} if isinstance(summ, dict) else {}
        levels_ok = got == want
        if rule == "gaps_zero":
            ok = correct == 0 and levels_ok
        else:
            ok = correct * 2 == total and levels_ok
        return ok, f"{correct}/{total} correct; levels expected {want}, model gave {got}"
    raise ValueError(rule)


def run_case(case):
    if case["kind"] == "chain":
        passage, comp = load_passage(case)
        res = chain.Chain().run(passage, comp, case["difficulty"], case["n"], progress=lambda m: None)
        return res, comp
    if case["kind"] == "review":
        passage, comp = load_passage(case)
        c = chain.Chain()
        rev = c.review(passage, case["difficulty"], [case["question"]])
        return {"review": rev[0], "auto_checks": checks.check_question(case["question"], passage), "log": c.log}, comp
    if case["kind"] == "revise":
        passage, comp = load_passage(case)
        src = json.loads((OUT / f"test_{case['from_test']:02d}.json").read_text(encoding="utf-8"))
        bad_q, review = src["case"]["question"], src["result"]["review"]
        c = chain.Chain()
        rev = c.generate(passage, comp, case["difficulty"], 1, feedback=[{"question": bad_q, "review": review}])
        re_review = c.review(passage, case["difficulty"], rev["questions"]) if rev["questions"] else []
        return {"revised": rev, "re_review": re_review, "log": c.log}, comp
    if case["kind"] == "gaps":
        src = json.loads((OUT / f"test_{case['from_test']:02d}.json").read_text(encoding="utf-8"))["result"]
        qs = src["questions"]
        if case["answers"] == "first_half_correct":
            half = len(qs) // 2
            wrong = {"A": "B", "B": "C", "C": "D", "D": "A"}
            answers = [q["correct"] if i < half else wrong[q["correct"]] for i, q in enumerate(qs)]
        else:
            answers = [None] * len(qs)
        c = chain.Chain()
        res = c.gap_summary(qs, answers)
        res.update({"answers": answers, "log": c.log})
        return res, None
    raise ValueError(case["kind"])


def short_actual(case, res):
    if case["kind"] == "chain":
        qs = res.get("questions", [])
        return f"{len(qs)} accepted" + (f"; note: {res['note'][:60]}" if res.get("note") else "") \
            + (f"; {res['reason']}" if res.get("reason") else "")
    if case["kind"] == "review":
        return f"{res['review'].get('verdict')}, scores {res['review'].get('scores')}"
    if case["kind"] == "revise":
        rr = res["re_review"]
        return f"re-review: {rr[0].get('verdict') if rr else 'no question'}"
    s = res["summary"]
    return f"{sum(r['correct'] for r in res['table'])}/{sum(r['total'] for r in res['table'])}; " + \
        "; ".join(f"{g.get('competency')}: {g.get('level')}" for g in s.get("gaps", []))


def write_table():
    rows = []
    for f in sorted(OUT.glob("test_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        rows.append(d)
    lines = [f"# Test results (final prompts, {llm.MODEL})", "",
             "| No. | Input (short) | Type | Expected output | Actual output (short) | Pass/Fail |",
             "|---|---|---|---|---|---|"]
    for d in rows:
        c = d["case"]
        lines.append(f"| {c['no']} | {c['short']} | {c['type']} | {c['expect']} | {d['actual_short']} | "
                     f"{'Pass' if d['pass'] else 'Fail'} |")
    passed = sum(d["pass"] for d in rows)
    lines += ["", f"Passed {passed} of {len(rows)}.", "",
              "Details for each test (rule result and full LLM log) are in tests/test_XX.json."]
    (OUT.parent / "test_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    only = {int(a) for a in sys.argv[1:]}
    OUT.mkdir(parents=True, exist_ok=True)
    for case in cases:
        if only and case["no"] not in only:
            continue
        res, comp = run_case(case)
        ok, detail = judge(case, res, comp)
        rec = {"case": case, "model": llm.MODEL, "pass": ok, "rule_detail": detail,
               "actual_short": short_actual(case, res), "result": res}
        (OUT / f"test_{case['no']:02d}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Test {case['no']:2d} [{case['type']}] {'PASS' if ok else 'FAIL'}: {detail}", flush=True)
    write_table()


if __name__ == "__main__":
    main()
