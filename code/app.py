"""KarmaQuiz web prototype (Streamlit).

Run locally:   streamlit run code/app.py      (needs GOOGLE_API_KEY in the environment)
Deployed:      Streamlit Community Cloud, key stored as a secret (never in the repo).
"""
import json
import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import chain  # noqa: E402
import llm  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PASSAGES = sorted((ROOT / "test-data" / "passages").glob("*.json"))

st.set_page_config(page_title="KarmaQuiz", page_icon="📝", layout="wide")
st.title("KarmaQuiz")
st.caption("Generate, review and competency-tag MCQs from training material, then find a learner's "
           f"competency gaps. Team PromptPilot (PE-B37-07). Model: {llm.MODEL}. "
           "Every question is a draft for a human reviewer to approve.")

tab_gen, tab_quiz, tab_log = st.tabs(["1. Generate and review", "2. Take quiz and get gap summary", "Run log"])

# ---------------- Tab 1: T1 -> T2 -> T3 ----------------
with tab_gen:
    samples = {"(paste your own)": None}
    for p in PASSAGES:
        d = json.loads(p.read_text(encoding="utf-8"))
        samples[f"{d['id']}: {d['title']}"] = d
    pick = st.selectbox("Sample passage (public text, CC BY-SA)", list(samples))
    sample = samples[pick]
    passage = st.text_area("Source passage", value=sample["text"] if sample else "", height=220)
    if sample:
        st.caption(f"Source: {sample['source']} · Licence: {sample['licence']}")
    c1, c2, c3 = st.columns(3)
    comps = list(chain.DEFAULT_COMPETENCIES)
    default_comp = sample["competency"] if sample else comps[0]
    competency = c1.selectbox("Competency", comps, index=comps.index(default_comp) if default_comp in comps else 0)
    difficulty = c2.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    n = c3.number_input("Number of questions", min_value=1, max_value=10, value=4)

    if st.button("Run the chain (T1 → T2 → T3)", type="primary"):
        status = st.status("Running…", expanded=True)
        try:
            result = chain.Chain().run(passage, competency, difficulty, int(n), progress=status.write)
            status.update(label="Done", state="complete")
        except Exception as e:
            status.update(label="Error", state="error")
            st.error(f"The model call failed: {e}")
            result = None
        if result:
            st.session_state["result"] = result
            st.session_state.pop("answers", None)

    result = st.session_state.get("result")
    if result:
        if result["status"] == "refused":
            st.warning(result["reason"])
        if result.get("note"):
            st.info(f"Generator note: {result['note']}")
        if result.get("auto_dropped"):
            st.warning(f"{len(result['auto_dropped'])} question(s) removed by the automatic checks "
                       "(bad options or source sentence not found in the passage).")
        for rnd in result.get("review_rounds", []):
            passed = sum(r.get("verdict") == "pass" for r in rnd["reviews"])
            with st.expander(f"T2 review round {rnd['round']}: {passed}/{len(rnd['reviews'])} passed"):
                for q, r in zip(rnd["questions"], rnd["reviews"]):
                    icon = "✅" if r.get("verdict") == "pass" else "❌"
                    st.markdown(f"{icon} **{q['question']}**  \nscores: `{r.get('scores')}`  \n"
                                f"{r.get('reason', '')} {('Fix: ' + r['suggested_fix']) if r.get('suggested_fix') else ''}")
        st.subheader(f"Accepted questions ({len(result['questions'])})")
        for i, q in enumerate(result["questions"], 1):
            st.markdown(f"**Q{i}. {q['question']}**")
            for k in "ABCD":
                mark = " ✔" if k == q["correct"] else ""
                st.markdown(f"- {k}. {q['options'][k]}{mark}")
            st.caption(f"Competency: {q['competency']} · Difficulty: {q['tagged_difficulty']} · "
                       f"{q['tag_justification']}")
            st.caption(f"Source: “{q['source_sentence']}”  \nExplanation: {q['explanation']}")
        st.download_button("Download questions (JSON)",
                           json.dumps(result["questions"], ensure_ascii=False, indent=2),
                           "karmaquiz_questions.json", "application/json")

# ---------------- Tab 2: quiz + T4 ----------------
with tab_quiz:
    result = st.session_state.get("result")
    if not result or not result.get("questions"):
        st.info("Generate questions in tab 1 first.")
    else:
        st.write("Answer the questions, or fill in test answers, then ask for the gap summary. "
                 "Answers entered here are treated as synthetic test data.")
        answers = []
        for i, q in enumerate(result["questions"], 1):
            a = st.radio(f"Q{i}. {q['question']}", list("ABCD"), key=f"ans{i}", horizontal=True,
                         format_func=lambda k, q=q: f"{k}. {q['options'][k]}", index=None)
            answers.append(a)
        if st.button("Get gap summary (T4)", type="primary"):
            with st.spinner("Writing summary…"):
                st.session_state["gaps"] = chain.Chain().gap_summary(result["questions"], answers)
        gaps = st.session_state.get("gaps")
        if gaps:
            st.table([{k: r[k] for k in ("competency", "correct", "total")} for r in gaps["table"]])
            s = gaps["summary"]
            if "overall" in s:
                st.markdown(f"**{s['overall']}**")
                for g in s.get("gaps", []):
                    st.markdown(f"- **{g.get('competency')}** ({g.get('level')}): {g.get('what_to_review')}")
                st.markdown(f"*Next step:* {s.get('next_step', '')}")
            else:
                st.error(s)

# ---------------- Tab 3: log ----------------
with tab_log:
    result = st.session_state.get("result")
    if result:
        st.write("Every LLM call in the last run (prompt id, settings, raw output).")
        for entry in result["log"]:
            with st.expander(f"{entry['prompt']} · {entry['meta']['seconds']} s"):
                st.json(entry["meta"])
                st.code(entry["raw_output"], language="json")
    else:
        st.info("No run yet.")
