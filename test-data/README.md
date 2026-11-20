# Test data

Everything the Milestone 2 numbers are based on. Nothing here needs an API key to read.

| Path | What it is |
|---|---|
| `passages/` | 6 public passages (Wikipedia introductions, CC BY-SA 4.0) with revision IDs. See `passages/README.md` |
| `cases/test_cases.json` | The 16 test inputs. `expect` (the expected output) and `auto` (the pass/fail rule) were written **before** the tests were run |
| `outputs/tests/test_XX.json` | One file per test: the case, model, pass/fail, rule detail and the full LLM log (every prompt's variables and raw output) |
| `outputs/test_results.md` | The test table used in the Milestone 2 PDF, Section 4 (8 of 16 pass) |
| `outputs/iterations/T1_<version>.json` | The prompt-version experiment: 12 runs per T1 version (4 inputs × 3 repeats), scored by the fixed v2 judge |

## The 16 cases

| Type | Count | Tests |
|---|---|---|
| Normal | 5 | 1–5: four passages through the full chain, and T4 on a synthetic learner |
| Edge | 8 | 6–11, 15, 16: real faulty questions for T2, a very short passage, Hindi input, a changed fact, a wrong competency label, a blank quiz, the T1R repair loop |
| Invalid | 3 | 12–14: prompt injection, empty passage, gibberish |

Learner answers in tests 5 and 15 are **synthetic** (made up for the test), not real people.

## Reproduce

```bash
python code/run_tests.py            # all 16 (needs GOOGLE_API_KEY); or e.g. python code/run_tests.py 9 14
python code/run_iterations.py final # one T1 version, 12 runs
python -m pytest tests -q           # offline: checks that the saved files above are consistent
```

`tests/test_data.py` checks that every case has a saved output, that the pass count in
`test_results.md` matches the JSON files, and that every accepted question's source sentence is
found word for word in the passage it was given.
