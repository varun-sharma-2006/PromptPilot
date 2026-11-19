# KarmaQuiz (Team PromptPilot, PE-B37-07)

**KarmaQuiz** is a chain of prompts that turns a passage of government training material into
multiple-choice questions (MCQs). Each question has one answer key, an explanation and a quoted
source sentence. A second reviewer prompt checks every question against a 5-point rubric, another
prompt tags each question with a competency and difficulty, and a final prompt summarises a
learner's competency gaps from their quiz answers.

- Problem statement: **SIH26101**, AI-enabled learning platform for competency-gap detection and
  auto-generated quizzes (iGOT Karmayogi), from the course Problem Bank
- Course: SCSE4041 Prompt Engineering Mini Project, Bennett University
- Model: **Google Gemini `gemini-3.1-flash-lite`** through the Gemini API (see `code/llm.py` for why)
- Prototype: **TODO: Streamlit app link** (see "Deploy" below)

## Team

| Member | Main task |
|---|---|
| Varun Sharma (leader) | Chain code, T1/T1R/T2 final prompts, Streamlit app, Milestone 2 PDF |
| Yashika Garg | Test data and test table, prompt versions v2 and v3, experiment runner and checks, diagrams, research abstract |
| Om Bansal | TODO: confirm task (planned: reel recording and voice-over, hands-on comparison with existing quiz tools) |

## The chain (5 prompts)

| ID | Prompt | Input | Output |
|---|---|---|---|
| T1 | Generate MCQs | passage, competency, difficulty, N | JSON questions with options A–D, key, explanation, verbatim source sentence |
| T2 | Review | passage, difficulty, questions | JSON rubric scores (faithful, single key, plausible distractors, clear, right level), verdict, fix |
| T1R | Revise | failed questions + reviewer comments | repaired questions (at most 2 rounds) |
| T3 | Tag | accepted questions, competency list | competency (from the list only), difficulty, one-line justification |
| T4 | Gap summary | per-competency counts (computed in Python) | overall line, level per competency, what to review, next step |

Between T1 and T2, plain Python checks (`code/checks.py`) drop any question without exactly four
options A–D, or whose source sentence is not found word for word in the passage.

## Repository layout

```
README.md            this file
CHANGELOG.md         dated changes since Milestone 1
requirements.txt
prompts/
  v1/ v2/ v3/        older prompt versions (one .txt per prompt)
  final/             final prompts: T1_generate, T1_revise, T2_review, T3_tag, T4_gaps
code/
  app.py             Streamlit prototype
  chain.py           the prompt chain
  llm.py             Gemini API wrapper (key read from environment / Streamlit secret)
  prompts.py         loads prompt files, fills {VARIABLES}
  checks.py          automatic (non-LLM) checks
  run_iterations.py  prompt-version experiment (iteration log numbers)
  run_tests.py       test table runner
  fetch_passages.py  downloads the public test passages
  make_diagrams.py   draws docs/diagrams
  screenshots.py     screenshots of real app runs
test-data/
  passages/          6 public passages (Wikipedia, CC BY-SA 4.0) with revision IDs
  cases/             the 15 test inputs with expected outputs
  outputs/           every saved output: iterations/ (per prompt version) and tests/ (per test)
docs/
  diagrams/  screenshots/  Milestone 2 PDF and supporting document
```

## Run it locally

```bash
pip install -r requirements.txt
# PowerShell:  $env:GOOGLE_API_KEY = "your key"      bash:  export GOOGLE_API_KEY=your key
streamlit run code/app.py
```

Reproduce the numbers in the report:

```bash
python code/run_iterations.py v1     # also v2, v3, final
python code/run_tests.py
```

## Deploy (Streamlit Community Cloud)

1. Sign in at share.streamlit.io with GitHub and choose **New app**.
2. Repository `varun-sharma-2006/PromptPilot`, branch `main`, main file `code/app.py`.
3. Under **Advanced settings → Secrets**, add `GOOGLE_API_KEY = "..."`. Never put the key in the repo.
4. Deploy, then open the app link in a private window to check that it works without a login.

## Data and responsible use

Test passages are public, openly licensed text. Learner answers are synthetic and labelled that way.
No personal data is used. Every generated question is a draft that a human reviewer must approve.
