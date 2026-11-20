# Reel script: KarmaQuiz (target 135 s)

**Hard limit: 90–150 seconds.** The guidelines (form Q14) take marks off for anything shorter or
longer, so do **not** make it 2–3 minutes. About 135 s leaves room for pauses. Read the voice-over at a
normal pace: the full text is about 300 words, which comes to about 130 s.

Format: screen recording with voice-over, horizontal 1920×1080. Faces are optional. Part 3 must be a
**real run** recorded live. Old screenshots or a mock-up get 0 marks for the demo.
Suggested voices: Varun for Parts 1 and 4, Yashika for Part 2, Om for Part 3. One voice is also fine.

---

## Part 1: Problem (0:00–0:12, about 12 s)

**Screen:** the GitHub README title "KarmaQuiz (Team PromptPilot, PE-B37-07)", then zoom on the
SIH26101 / iGOT Karmayogi line.

**Voice-over:**
> iGOT Karmayogi trains crores of government employees, and every course needs quiz questions that
> are correct and linked to a competency. Writing them by hand is slow. KarmaQuiz is our five-prompt
> chain that writes, checks and tags these questions automatically.

---

## Part 2: Prompt experiment, before and after (0:12–0:50, about 38 s)

**Screen, in this order:**
1. (0:12) `prompts/v1/T1_generate.txt`: show it is a short, plain instruction.
2. (0:18) Its real output: open `test-data/cases/test_cases.json`, case 7, the Swachh Bharat Phase 2
   question. Highlight `"correct": "B"`, then the explanation and source sentence saying Phase 2 is
   "to reinforce the achievements of Phase 1" (option C).
3. (0:30) `prompts/final/T1_generate.txt`: scroll past the header that says "the model returns the
   answer and three distractors; code shuffles them into A–D" and the difficulty patterns.
4. (0:38) The final output on the same fact: `test-data/outputs/tests/test_03.json`, the question
   whose key is "Phase 2 is being implemented to reinforce the achievements of Phase 1".
5. (0:44) The metrics table in the Milestone 2 PDF, Section 3 (judge pass row).

**Voice-over:**
> This is our first prompt, version 1. Here is a real output. It asks about Phase 2 of Swachh Bharat
> and marks B as correct, but its own source sentence says Phase 2 reinforces Phase 1. That is
> option C. The model contradicted itself, and it never once used D as the answer.
> We measured five versions. In the final prompt the model writes the answer and three wrong
> options, our code places them at A to D, and each difficulty level has a pattern. Same fact, now
> correctly keyed. Our rubric pass rate went from 77 percent to 98 percent.

---

## Part 3: Working demo, a real run (0:50–1:50, about 60 s)

Start `streamlit run code/app.py` **before** recording, with the key already set. Cut the waiting
while the model runs, but keep the button click and the result in the same shot.

**Screen:**
1. (0:50) Tab "1. Generate and review": choose sample passage **P2_gem: Government e Marketplace**,
   difficulty **easy**, number of questions **4**. Click **Run the chain (T1 → T2 → T3)**.
2. (1:00) Show the progress lines, then the T2 review scores for each question.
3. (1:10) Scroll the **Accepted questions**: options, key, explanation, quoted source sentence,
   competency tag and difficulty.
4. (1:25) Tab "2. Take quiz and get gap summary": answer about half right on purpose, then click
   **Get gap summary (T4)**. Show the score table and the summary.
5. (1:42) Tab "Run log": open one entry to show the prompt ID, temperature and raw JSON output.

**Voice-over:**
> Here is the live app. We pick a public passage on the Government e-Marketplace, choose easy, and ask
> for four questions. Prompt T1 writes them. Our Python code checks that every quoted source sentence
> really exists in the passage. Prompt T2 then reviews each question on our five-point rubric:
> faithful, one correct answer, plausible wrong options, clear, and the right level. If one fails,
> T1R repairs it and T2 checks it again. Prompt T3 tags each question with a competency from a fixed
> list.
> Now a learner takes the quiz. Python counts the score for each competency, and T4 writes the gap
> summary: what to revise and a next step. Every call is saved in the run log with its prompt
> version and settings.

---

## Part 4: Progress and next steps (1:50–2:10, about 20 s)

**Screen:** the test table in the PDF, Section 4 (8 of 16 pass), then the limitations table, then
the GitHub commit list for a second.

**Voice-over:**
> Status: five prompts, sixteen tests, eight passing. We kept every failure. Gibberish text still
> produced questions, and difficulty tags are inconsistent. For Milestone 3 we will add a
> meaningful-content check, retry when too few questions come back, and hand-score forty
> questions to check our AI reviewer. Thank you.

---

## Timing check

| Part | Required by guidelines | This script |
|---|---|---|
| 1. Problem | ~10 s | 0:00–0:12 (12 s) |
| 2. Prompt experiment | ~30–40 s | 0:12–0:50 (38 s) |
| 3. Working demo | ~40–60 s | 0:50–1:50 (60 s) |
| 4. Progress and next steps | ~15–20 s | 1:50–2:10 (20 s) |
| **Total** | **90–150 s** | **about 130 s** |

If the final cut runs over 150 s, shorten Part 3 first: skip the Run log tab (saves ~8 s).

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
