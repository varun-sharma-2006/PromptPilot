# Changelog

All changes since Milestone 1 (submitted 7 October 2026). The git history has the exact commit
times and authors.

## 2026-11-20

### Added
- Offline tests in `tests/` (56 tests, no API key): automatic checks, every prompt file and its
  `{VARIABLES}`, and consistency of the saved test data with the test table.
- `code/check_secrets.py`: scans tracked files for API keys and passwords.
- GitHub Actions workflow (`.github/workflows/offline-checks.yml`) runs both on every push.
- `prompts/README.md` and `test-data/README.md`.

## 2026-11-19

### Added
- Repository structure required by the Milestone 2 guidelines (`prompts/`, `code/`, `test-data/`, `docs/`).
- Gemini API wrapper (`code/llm.py`). The key is read from the environment or a Streamlit secret and is never committed.
- Six public test passages with Wikipedia revision IDs and licence (`test-data/passages/`).
- Automatic non-LLM checks: JSON, A–D options, verbatim source sentence (`code/checks.py`).
- T1 version experiment runner with a fixed LLM judge (`code/run_iterations.py`), and saved results for every version.
- Prompt versions: T1 v1 (the Milestone 1 baseline), v2, v3, final; T2 v1, v2, final.
- New prompts beyond Milestone 1: T1R (revise failed questions) and T4 counts moved into code.
- The prompt chain (`code/chain.py`), the Streamlit prototype (`code/app.py`) and four diagrams.
- 16 test cases (normal, edge, invalid) with pre-written pass/fail rules (`code/run_tests.py`) and their saved outputs.
- Milestone 2 PDF and research abstract (`docs/`).

### Changed
- Model: Milestone 1 planned "one general-purpose LLM through its chat interface". We now call
  `gemini-3.1-flash-lite` through the API, so every run is logged with its settings.
  `gemini-2.5-flash` is not offered to new keys; `gemini-3-flash-preview` was tried first (12 v1 runs,
  kept in `test-data/outputs/iterations/T1_v1_gemini-3-flash-preview.json`), but its free tier
  allows only 20 requests per day.
- T4 no longer asks the model to count scores. Python counts correct/total and the model only writes the summary.
- T1 went through five measured versions (v1 baseline → v5 final); see `test-data/outputs/iterations/`.
  v4 (facts-first) scored worse than v3 and is kept as a recorded failure.
- From v5, the model returns the answer and three distractors, and code places them at A–D.

### Tests
- 16 tests on the final prompts: 8 pass, 8 fail. Failures are kept and explained in the PDF, Section 4.
