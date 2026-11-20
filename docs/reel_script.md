# Reel script (target 120 s; must be 90–150 s)

Screen recording plus a teammate's voice-over. The demo part must be a **real run**. Record it
live in the Streamlit app (`streamlit run code/app.py`) or the Colab notebook, not from screenshots.

| Time | Part | Show on screen | Say |
|---|---|---|---|
| 0–12 s | 1. Problem | README title, then the iGOT Karmayogi / SIH26101 line | "iGOT Karmayogi trains about 2 crore government employees and needs a steady supply of correct, competency-tagged quiz questions. KarmaQuiz is a five-prompt chain that writes, checks and tags them." |
| 12–50 s | 2. Prompt experiment | `prompts/v1/T1_generate.txt`, then a v1 output from `test-data/outputs/iterations/T1_v1_gemini-3-flash-preview.json` with the wrong Phase 2 key; then `prompts/final/T1_generate.txt` and the metrics table in the PDF | "Our first prompt gave a question whose marked answer contradicted its own source sentence, and it never used option D as the key. Across five measured versions, the final prompt lets code place the options and gives a pattern per difficulty. Rubric pass rate went from 77% to 98%." |
| 50–105 s | 3. Working demo | Streamlit app: pick the RTI passage, medium, 4 → Run → T2 review round → accepted questions with source and tags → Quiz tab → answer → Get gap summary | "We paste a public passage and pick a competency and level. T1 writes the questions, code checks each source sentence, T2 scores them on our rubric, and T3 tags the competency. A learner answers, Python counts the score, and T4 explains the gap." |
| 105–120 s | 4. Progress and next steps | Test table (8/16 pass) and the limitations table | "Eight of sixteen tests pass. We keep the failures: gibberish input still produced questions, and difficulty tags are inconsistent. For Milestone 3: a meaningful-content check, a count retry, and hand-scoring 40 questions to check our LLM judge." |

After uploading, set the link to "Anyone with the link can view", test it in a private window,
and enter the exact length in seconds in `docs/team.json` (`reel_seconds`) and form Q14.

## Recording checklist

- [ ] Set `GOOGLE_API_KEY` in the terminal **before** you start recording, and never show it on screen
      (no `echo`, no `.streamlit/secrets.toml` in an open editor tab).
- [ ] Run `python code/check_secrets.py` first. Close every tab that isn't needed.
- [ ] Use 1920×1080 and zoom the browser to 125% so table text is readable on a phone.
- [ ] Do one practice run first: the free API tier can return a 429 error. If it does, wait one
      minute and run again rather than cutting in an old result.
- [ ] Cut waiting time while the model runs, but don't cut between the button press and the result
      in a way that hides that the run is real.
- [ ] Voice-over: record in a quiet room, separately if needed, and keep it within 90–150 s in total.
- [ ] Export as MP4, upload, set "Anyone with the link can view", open it in a private window, and
      write the exact length in `docs/team.json` → `links.reel_seconds`.
