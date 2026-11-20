"""Offline consistency checks on test-data/ (no API key, no network).

Makes sure the test table in the PDF matches the saved outputs: every case has a saved result,
the pass count in test_results.md matches the JSON files, and every accepted question's source
sentence really is in the passage that was sent to the model.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "test-data"
sys.path.insert(0, str(ROOT / "code"))

import checks  # noqa: E402

CASES = json.loads((DATA / "cases" / "test_cases.json").read_text(encoding="utf-8"))["cases"]


def saved(no):
    return json.loads((DATA / "outputs" / "tests" / f"test_{no:02d}.json").read_text(encoding="utf-8"))


def test_cases_are_numbered_1_to_n():
    assert [c["no"] for c in CASES] == list(range(1, len(CASES) + 1))


def test_guideline_minimums():
    # Milestone 2: at least 10 tests, at least 3 edge cases
    assert len(CASES) >= 10
    assert sum(c["type"] == "Edge" for c in CASES) >= 3


def test_every_case_has_expected_output_and_rule():
    for c in CASES:
        assert c["expect"].strip() and c["auto"].strip(), c["no"]


def test_referenced_passages_exist():
    for c in CASES:
        if c.get("passage"):
            assert (DATA / "passages" / f"{c['passage']}.json").exists(), c["passage"]


def test_every_case_has_a_saved_output_for_that_case():
    for c in CASES:
        assert saved(c["no"])["case"]["no"] == c["no"]


def test_results_table_matches_saved_outputs():
    passed = sum(bool(saved(c["no"])["pass"]) for c in CASES)
    md = (DATA / "outputs" / "test_results.md").read_text(encoding="utf-8")
    m = re.search(r"Passed (\d+) of (\d+)", md)
    assert m and (int(m.group(1)), int(m.group(2))) == (passed, len(CASES))


def test_accepted_questions_quote_the_passage_they_were_given():
    for c in CASES:
        res = saved(c["no"])["result"]
        if c["kind"] != "chain" or not isinstance(res, dict) or not res.get("questions"):
            continue
        t1 = next(e for e in res["log"] if e["prompt"].endswith("T1_generate"))
        passage = t1["variables"]["PASSAGE"]
        for q in res["questions"]:
            assert checks.quote_in_passage(q["source_sentence"], passage), (c["no"], q["question"])


def test_passages_record_source_and_licence():
    for path in (DATA / "passages").glob("*.json"):
        p = json.loads(path.read_text(encoding="utf-8"))
        assert p["source"] and "CC BY-SA" in p["licence"] and p["text"].strip(), path.name
