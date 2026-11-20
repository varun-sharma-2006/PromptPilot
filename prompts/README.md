# Prompts

One `.txt` file per prompt. Older versions are kept unchanged so every number in the iteration
log can be reproduced (`python code/run_iterations.py <version>`).

| Folder | What it holds |
|---|---|
| `v1/` | Milestone 1 baseline: T1 generate, T2 review (first draft) |
| `v2/` | T1 v2 and T2 v2. **T2 v2 is the fixed judge** that scores every T1 version |
| `v3/` | T1 v3: code chooses the answer letter, one-fact definition, self-check |
| `v4/` | T1 v4: facts listed first. Scored worse than v3; kept as a recorded failure |
| `final/` | The five prompts the app uses: T1 (v5), T1R, T2, T3, T4 |

## File format

```
### comment lines start with three hashes and are never sent to the model
=== SETTINGS ===
temperature: 0.2          (or "default")
json_mode: true           (true = the API is asked for JSON output)
=== SYSTEM ===
system prompt, or "none"
=== USER ===
user prompt with {VARIABLES}
```

`code/prompts.py` reads the file and fills each `{VARIABLE}` with a plain text replace, so JSON
braces such as `{"questions": []}` inside a prompt are left alone.

## Variables in the final prompts

| Prompt | Variables | Temperature |
|---|---|---|
| T1_generate | PASSAGE, COMPETENCY, DIFFICULTY, N | 0.2 |
| T1_revise | PASSAGE, COMPETENCY, DIFFICULTY, N, FEEDBACK_JSON | 0.2 |
| T2_review | PASSAGE, DIFFICULTY, QUESTIONS_JSON | 0 |
| T3_tag | QUESTIONS_JSON, COMPETENCY_LIST | 0 |
| T4_gaps | RESULTS_JSON | 0.2 |

## Before you change a prompt

1. Copy the current file to a new version folder instead of editing an old version.
2. Write the reason for each change in the `###` header, with the measured problem it fixes.
3. Run `python -m pytest tests -q`. `tests/test_prompts.py` fails if a section is missing or a
   `{VARIABLE}` does not match what `code/chain.py` fills.
4. Re-run `python code/run_iterations.py <version>` and add the numbers to the iteration log.
