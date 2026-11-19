"""Copy the measured T1 numbers from test-data/outputs/iterations/*.json into docs/report.json
(iteration_metrics table), so the PDF table always matches the saved runs.

    python docs/fill_metrics.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
IT = ROOT / "test-data" / "outputs" / "iterations"
REP = ROOT / "docs" / "report.json"

VERSIONS = ["v1", "v2", "v3", "v4", "final"]


def load(v):
    return json.loads((IT / f"T1_{v}.json").read_text(encoding="utf-8"))["summary"]


def main():
    sums = {v: load(v) for v in VERSIONS if (IT / f"T1_{v}.json").exists()}
    vs = list(sums)
    rows = [["Measure"] + [("v5 (final)" if v == "final" else v) for v in vs]]

    def add(label, fn):
        rows.append([label] + [fn(sums[v]) for v in vs])

    add("Valid JSON (runs)", lambda s: f"{s['json_valid']}/{s['runs']}")
    add("Schema valid (runs)", lambda s: f"{s['schema_valid']}/{s['runs']}")
    add("Normal inputs: got the N asked", lambda s: f"{s['count_as_requested_normal']}/{s['normal_runs']}")
    add("Short CVC passage, asked 6: questions returned", lambda s: ", ".join(map(str, s["short_passage_question_counts"])))
    add("Source sentence verbatim (questions)", lambda s: f"{s['quote_verbatim']}/{s['questions']}")
    add("Questions sharing a source sentence", lambda s: str(s["questions_sharing_a_source_sentence"]))
    add("Correct option A/B/C/D", lambda s: "/".join(str(s["answer_positions"].get(k, 0)) for k in "ABCD"))
    add("Judge: pass (all 5 rubric items)", lambda s: f"{s['judge_pass']}/{s['judge_questions']}")
    add("Judge: faithful", lambda s: f"{s['judge_faithful']}/{s['judge_questions']}")
    add("Judge: right level", lambda s: f"{s['judge_right_level']}/{s['judge_questions']}")
    rep = json.loads(REP.read_text(encoding="utf-8"))
    rep["iteration_metrics"] = rows
    REP.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(" | ".join(r))


if __name__ == "__main__":
    main()
