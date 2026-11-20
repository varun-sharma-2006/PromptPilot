"""Offline tests for code/checks.py (no API key, no network).

    python -m pytest tests -q
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "code"))

import checks  # noqa: E402

PASSAGE = ("The Right to Information Act, 2005 lets citizens request information from a public "
           "authority. The authority must reply within thirty days. If the matter concerns the "
           "life or liberty of a person, the reply is due within 48 hours.")
QUOTE = "The authority must reply within thirty days."


def good_question(**changes):
    q = {
        "question": "Within how many days must a public authority reply to an RTI request?",
        "options": {"A": "Thirty days", "B": "Ten days", "C": "Ninety days", "D": "Seven days"},
        "correct": "A",
        "explanation": "The passage gives thirty days.",
        "source_sentence": QUOTE,
    }
    q.update(changes)
    return q


# quote_in_passage --------------------------------------------------------------------------

def test_exact_quote_found():
    assert checks.quote_in_passage(QUOTE, PASSAGE)


def test_quote_ignores_case_whitespace_and_outer_quotes():
    assert checks.quote_in_passage('  "the authority   must reply within THIRTY days."  ', PASSAGE)


def test_quote_ignores_leading_and_trailing_ellipsis():
    assert checks.quote_in_passage("...must reply within thirty days...", PASSAGE)


def test_curly_quotes_and_dashes_are_normalised():
    assert checks.quote_in_passage("“request it from a public authority”",
                                   "You can request it from a public authority.")
    assert checks.quote_in_passage("the officer’s reply is due", "The officer's reply is due today.")
    assert checks.quote_in_passage("rules – 2005 version", "rules - 2005 version")


def test_paraphrase_is_rejected():
    assert not checks.quote_in_passage("The authority has to answer in thirty days.", PASSAGE)


def test_very_short_or_empty_quote_is_rejected():
    assert not checks.quote_in_passage("thirty", PASSAGE)
    assert not checks.quote_in_passage("", PASSAGE)
    assert not checks.quote_in_passage(None, PASSAGE)


# assemble / extract_questions --------------------------------------------------------------

def test_assemble_places_answer_at_given_letter():
    q = {"question": "Q?", "answer": "right", "distractors": ["w1", "w2", "w3"],
         "explanation": "e", "source_sentence": QUOTE}
    out = checks.assemble([q, dict(q)], ["C", "A"])
    assert out[0]["correct"] == "C" and out[0]["options"]["C"] == "right"
    assert out[1]["correct"] == "A" and out[1]["options"]["A"] == "right"
    assert sorted(out[0]["options"]) == ["A", "B", "C", "D"]
    assert "answer" not in out[0] and "distractors" not in out[0]


def test_assemble_keeps_old_format_unchanged():
    q = good_question()
    assert checks.assemble([q], ["D"]) == [q]


def test_extract_accepts_bare_list_and_wrapped_dict():
    q = good_question()
    assert checks.extract_questions([q]) == [q]
    assert checks.extract_questions({"questions": [q]}) == [q]
    assert checks.extract_questions({"mcqs": [q]}) == [q]


def test_extract_returns_none_for_unknown_shape():
    assert checks.extract_questions({"note": "nothing"}) is None
    assert checks.extract_questions("text") is None


# check_question / check_run ----------------------------------------------------------------

def test_good_question_passes_every_check():
    assert all(checks.check_question(good_question(), PASSAGE).values())


def test_duplicate_options_fail():
    q = good_question(options={"A": "Thirty days", "B": "thirty days", "C": "Ten", "D": "Seven"})
    assert not checks.check_question(q, PASSAGE)["four_options"]


def test_three_options_fail():
    q = good_question(options={"A": "Thirty days", "B": "Ten days", "C": "Seven days"})
    assert not checks.check_question(q, PASSAGE)["four_options"]


def test_bad_key_fails():
    assert not checks.check_question(good_question(correct="E"), PASSAGE)["key_ok"]


def test_missing_field_fails():
    q = good_question()
    del q["explanation"]
    assert not checks.check_question(q, PASSAGE)["fields_ok"]


def test_check_run_on_invalid_json():
    r = checks.check_run(None, PASSAGE)
    assert r == {"json_ok": False, "schema_ok": False, "n_questions": 0, "per_question": []}


def test_check_run_counts_and_positions():
    r = checks.check_run({"questions": [good_question(), good_question(correct="B")]}, PASSAGE)
    assert r["json_ok"] and r["n_questions"] == 2
    assert r["answer_positions"] == ["A", "B"]
