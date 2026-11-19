"""KarmaQuiz prompt chain: T1 generate -> T2 review (revise up to 2 rounds) -> T3 tag -> T4 gap summary.

Every LLM call is logged (prompt id, model, settings, input, raw output) so a run can be
saved to test-data/outputs and shown in the report.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import checks  # noqa: E402
import llm  # noqa: E402
import prompts  # noqa: E402

VERSION = "final"
MAX_REVISE_ROUNDS = 2

DEFAULT_COMPETENCIES = [
    "Domain: Right to Information",
    "Domain: Sanitation Programmes",
    "Domain: e-Governance",
    "Functional: Public Procurement",
    "Functional: Vigilance and Ethics",
    "Behavioural: Citizen Centricity",
]


class Chain:
    def __init__(self, version=VERSION):
        self.version = version
        self.log = []

    # ---------- one LLM call ----------
    def _run(self, name, **values):
        p = prompts.load(self.version, name)
        user = prompts.fill(p["user"], **values)
        text, meta = llm.call(user, p["system"], p["temperature"], p["json_mode"])
        obj, err = llm.parse_json(text)
        self.log.append({"prompt": p["id"], "meta": meta, "variables": values,
                         "raw_output": text, "parse_error": err})
        return obj, err

    # ---------- T1 ----------
    def generate(self, passage, competency, difficulty, n, feedback=None):
        values = dict(N=n, DIFFICULTY=difficulty, COMPETENCY=competency, PASSAGE=passage)
        name = "T1_generate"
        if feedback:
            name = "T1_revise"
            values["FEEDBACK_JSON"] = json.dumps(feedback, ensure_ascii=False, indent=2)
        obj, err = self._run(name, **values)
        if obj is None:
            return {"questions": [], "note": f"Output was not valid JSON: {err}"}
        qs = checks.extract_questions(obj, prompts.key_order(max(n, 1)).split(", ")) or []
        note = obj.get("note", "") if isinstance(obj, dict) else ""
        # keep only questions that pass the automatic schema/quote checks
        kept, dropped = [], []
        for q in qs:
            c = checks.check_question(q, passage)
            (kept if all(c.values()) else dropped).append((q, c))
        return {"questions": [q for q, _ in kept], "note": note,
                "auto_dropped": [{"question": q, "checks": c} for q, c in dropped]}

    # ---------- T2 ----------
    def review(self, passage, difficulty, questions):
        if not questions:
            return []
        numbered = [dict(id=i + 1, **q) for i, q in enumerate(questions)]
        obj, err = self._run("T2_review", DIFFICULTY=difficulty, PASSAGE=passage,
                             QUESTIONS_JSON=json.dumps(numbered, ensure_ascii=False, indent=2))
        reviews = (obj or {}).get("reviews", []) if isinstance(obj, dict) else []
        by_id = {r.get("id"): r for r in reviews if isinstance(r, dict)}
        out = []
        for i in range(len(questions)):
            r = by_id.get(i + 1) or {"id": i + 1, "verdict": "fail",
                                     "reason": "Reviewer gave no result for this question.", "scores": {}}
            out.append(r)
        return out

    # ---------- T3 ----------
    def tag(self, questions, competencies):
        if not questions:
            return []
        numbered = [dict(id=i + 1, question=q["question"], options=q["options"], correct=q["correct"])
                    for i, q in enumerate(questions)]
        obj, err = self._run("T3_tag", COMPETENCY_LIST="\n".join(f"- {c}" for c in competencies),
                             QUESTIONS_JSON=json.dumps(numbered, ensure_ascii=False, indent=2))
        tags = (obj or {}).get("tags", []) if isinstance(obj, dict) else []
        by_id = {t.get("id"): t for t in tags if isinstance(t, dict)}
        out = []
        for i in range(len(questions)):
            t = by_id.get(i + 1, {})
            comp = t.get("competency")
            if comp not in competencies:  # never accept a tag outside the list
                comp = "UNTAGGED"
            out.append({"competency": comp, "difficulty": t.get("difficulty", "?"),
                        "justification": t.get("justification", "")})
        return out

    # ---------- T4 ----------
    def gap_summary(self, tagged_questions, learner_answers):
        """Scores are counted in Python (LLMs miscount); T4 only writes the summary."""
        table = {}
        for q, a in zip(tagged_questions, learner_answers):
            row = table.setdefault(q["competency"], {"competency": q["competency"], "correct": 0, "total": 0,
                                                      "missed_questions": []})
            row["total"] += 1
            if a == q["correct"]:
                row["correct"] += 1
            else:
                row["missed_questions"].append(q["question"])
        rows = sorted(table.values(), key=lambda r: r["correct"] / r["total"])
        obj, err = self._run("T4_gaps", RESULTS_JSON=json.dumps(rows, ensure_ascii=False, indent=2))
        return {"table": rows, "summary": obj if obj is not None else {"error": err}}

    # ---------- full chain ----------
    def run(self, passage, competency, difficulty, n, competencies=None, progress=print):
        competencies = competencies or DEFAULT_COMPETENCIES
        if competency not in competencies:
            competencies = [competency] + list(competencies)
        if not passage or not passage.strip():
            return {"status": "refused", "reason": "Empty passage: nothing to generate questions from.",
                    "questions": [], "log": self.log}

        progress("T1: generating questions")
        gen = self.generate(passage, competency, difficulty, n)
        rounds = []
        accepted = []
        pending = gen["questions"]
        for rnd in range(MAX_REVISE_ROUNDS + 1):
            if not pending:
                break
            progress(f"T2: reviewing {len(pending)} question(s), round {rnd + 1}")
            reviews = self.review(passage, difficulty, pending)
            rounds.append({"round": rnd + 1, "questions": pending, "reviews": reviews})
            failed = []
            for q, r in zip(pending, reviews):
                if r.get("verdict") == "pass":
                    accepted.append(q)
                else:
                    failed.append((q, r))
            if not failed or rnd == MAX_REVISE_ROUNDS:
                break
            progress(f"T1 (revise): fixing {len(failed)} failed question(s)")
            feedback = [{"question": q, "review": r} for q, r in failed]
            rev = self.generate(passage, competency, difficulty, len(failed), feedback=feedback)
            pending = rev["questions"]

        progress(f"T3: tagging {len(accepted)} accepted question(s)")
        tags = self.tag(accepted, competencies)
        final = [dict(q, **{"competency": t["competency"], "tagged_difficulty": t["difficulty"],
                            "tag_justification": t["justification"]}) for q, t in zip(accepted, tags)]
        return {
            "status": "ok" if final else "no_questions",
            "note": gen.get("note", ""),
            "auto_dropped": gen.get("auto_dropped", []),
            "review_rounds": rounds,
            "questions": final,
            "log": self.log,
        }
