"""Offline tests for the prompt files and code/prompts.py (no API key, no network).

These catch the mistakes that are easy to make when a prompt file is edited by hand:
a missing section, a misspelt {VARIABLE}, or a bad temperature line.
"""
import pathlib
import re
import sys
from collections import Counter

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

import prompts  # noqa: E402

ALL_FILES = sorted((ROOT / "prompts").glob("*/*.txt"))

# variables that code/chain.py fills for each final prompt
FINAL_VARIABLES = {
    "T1_generate": {"PASSAGE", "COMPETENCY", "DIFFICULTY", "N"},
    "T1_revise": {"PASSAGE", "COMPETENCY", "DIFFICULTY", "N", "FEEDBACK_JSON"},
    "T2_review": {"PASSAGE", "DIFFICULTY", "QUESTIONS_JSON"},
    "T3_tag": {"QUESTIONS_JSON", "COMPETENCY_LIST"},
    "T4_gaps": {"RESULTS_JSON"},
}


def placeholders(text):
    return set(re.findall(r"\{([A-Z_]+)\}", text))


def test_every_version_folder_exists():
    names = {p.name for p in (ROOT / "prompts").iterdir() if p.is_dir()}
    assert {"v1", "v2", "v3", "v4", "final"} <= names


@pytest.mark.parametrize("path", ALL_FILES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_prompt_file_loads(path):
    p = prompts.load(path.parent.name, path.stem)
    assert p["user"], "USER section is empty"
    assert p["temperature"] is None or 0 <= p["temperature"] <= 2
    assert isinstance(p["json_mode"], bool)


@pytest.mark.parametrize("name", sorted(FINAL_VARIABLES))
def test_final_prompt_uses_exactly_the_filled_variables(name):
    p = prompts.load("final", name)
    used = placeholders(p["user"]) | placeholders(p["system"] or "")
    assert used == FINAL_VARIABLES[name]


@pytest.mark.parametrize("name", sorted(FINAL_VARIABLES))
def test_final_prompts_ask_for_json(name):
    assert prompts.load("final", name)["json_mode"]


def test_fill_keeps_json_braces():
    out = prompts.fill('Return {"questions": []} for {N} items', N=3)
    assert out == 'Return {"questions": []} for 3 items'


def test_comment_lines_are_removed():
    for path in ALL_FILES:
        p = prompts.load(path.parent.name, path.stem)
        assert "\n###" not in "\n" + p["user"]


@pytest.mark.parametrize("n", [1, 4, 5, 6, 10, 13])
def test_key_order_is_balanced(n):
    letters = prompts.key_order(n).split(", ")
    assert len(letters) == n and set(letters) <= set("ABCD")
    counts = Counter(letters)
    assert max(counts.values()) - min(counts.get(k, 0) for k in "ABCD") <= 1 or n < 4


def test_key_order_is_repeatable():
    assert prompts.key_order(6, seed=2) == prompts.key_order(6, seed=2)
