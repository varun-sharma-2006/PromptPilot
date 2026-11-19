"""Automatic (non-LLM) checks on T1 output. These give the numbers in the iteration log.

Checks per run:
  json_ok        output parses as JSON (after stripping ``` fences)
  schema_ok      every question has question/options A-D/correct/explanation/source_sentence
Checks per question:
  four_options   exactly the keys A, B, C, D, all non-empty and all different
  key_ok         "correct" is one of A-D
  quote_verbatim source_sentence appears word for word in the passage
                 (whitespace, outer quotes and leading/trailing "..." ignored)
"""
import re

FIELDS = ("question", "options", "correct", "explanation", "source_sentence")


def _norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def quote_in_passage(quote, passage):
    q = _norm(quote or "")
    q = re.sub(r'^(\.\.\.|…)\s*', "", q)
    q = re.sub(r'\s*(\.\.\.|…)$', "", q)
    q = q.strip(' "\'')
    if len(q) < 10:
        return False
    return q.lower() in _norm(passage).lower()


def extract_questions(obj):
    """v1 asks for a bare list, later versions for {"questions": [...]}."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("questions", "mcqs", "items"):
            if isinstance(obj.get(k), list):
                return obj[k]
    return None


def check_question(q, passage):
    opts = q.get("options") if isinstance(q, dict) else None
    four = (
        isinstance(opts, dict)
        and sorted(opts.keys()) == ["A", "B", "C", "D"]
        and all(str(v).strip() for v in opts.values())
        and len({_norm(str(v)).lower() for v in opts.values()}) == 4
    )
    return {
        "fields_ok": isinstance(q, dict) and all(f in q for f in FIELDS),
        "four_options": bool(four),
        "key_ok": isinstance(q, dict) and str(q.get("correct", "")).strip() in ("A", "B", "C", "D"),
        "quote_verbatim": isinstance(q, dict) and quote_in_passage(str(q.get("source_sentence", "")), passage),
    }


def check_run(obj, passage):
    qs = extract_questions(obj) if obj is not None else None
    if qs is None:
        return {"json_ok": obj is not None, "schema_ok": False, "n_questions": 0, "per_question": []}
    per = [check_question(q, passage) for q in qs]
    return {
        "json_ok": True,
        "schema_ok": all(p["fields_ok"] and p["four_options"] and p["key_ok"] for p in per),
        "n_questions": len(qs),
        "per_question": per,
        "answer_positions": [str(q.get("correct", "?")).strip() for q in qs if isinstance(q, dict)],
    }
