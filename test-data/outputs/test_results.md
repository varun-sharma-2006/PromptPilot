# Test results (final prompts, gemini-3.1-flash-lite)

| No. | Input (short) | Type | Expected output | Actual output (short) | Pass/Fail |
|---|---|---|---|---|---|
| 1 | RTI Act passage, medium, 4 questions | Normal | 4 accepted questions, quotes verbatim, tagged Domain: Right to Information | 3 accepted; note: Only 3 questions could be generated as the passage content w | Fail |
| 2 | GeM passage, easy, 5 questions | Normal | 5 accepted questions, tagged Functional: Public Procurement | 5 accepted | Fail |
| 3 | Swachh Bharat passage, hard, 3 questions | Normal | 3 accepted questions; T3 tags most of them 'hard' | 3 accepted | Fail |
| 4 | Digital India passage, medium, 4 questions | Normal | 4 accepted questions, tagged Domain: e-Governance | 3 accepted; note: Only 3 medium-difficulty questions could be generated that l | Fail |
| 5 | T4 on test 1 quiz, learner gets 2 of 4 right (synthetic) | Normal | Table shows 2/4; level 'partial' (0.5); summary names the missed ideas | 1/3; Domain: Right to Information: gap | Fail |
| 6 | T2 on a real v1 question whose option A also contains the answer | Edge | verdict fail, single_key = 0 | fail, scores {'faithful': 1, 'single_key': 0, 'plausible_distractors': 1, 'clear': 1, 'right_level': 1} | Pass |
| 7 | T2 on a real v1 question with the wrong answer key | Edge | verdict fail, faithful = 0 (key should be C) | fail, scores {'faithful': 0, 'single_key': 0, 'plausible_distractors': 1, 'clear': 1, 'right_level': 1} | Pass |
| 8 | Very short CVC passage (504 chars), 8 questions asked | Edge | Fewer than 8 questions (at most 5), with a note saying why | 3 accepted; note: Only 3 medium-difficulty questions could be generated as the | Pass |
| 9 | Hindi passage on RTI, easy, 3 questions | Edge | 3 questions in English; source_sentence copied in Hindi, word for word | 3 accepted | Fail |
| 10 | RTI passage changed to say 'ninety days' instead of 'thirty days' | Edge | Any question on reply time uses 90 days (the passage), not 30 (outside knowledge) | 3 accepted | Fail |
| 11 | Sanitation passage but competency set to Public Procurement | Edge | T3 tags the questions Domain: Sanitation Programmes (what they really test), not the requested label | 3 accepted | Pass |
| 12 | RTI passage with a prompt-injection line added | Invalid | Injection ignored: 3 normal MCQs on RTI, no poem | 3 accepted | Pass |
| 13 | Empty passage | Invalid | Refused before any LLM call: 'Empty passage' message, 0 questions | 0 accepted; Empty passage: nothing to generate questions from. | Pass |
| 14 | Gibberish passage | Invalid | 0 questions and a note that the text has no testable facts | 3 accepted | Fail |
| 15 | T4 on test 2 quiz, learner left every answer blank (synthetic) | Edge | Table shows 0/5; level 'gap'; no invented strengths | 0/5; Domain: e-Governance: gap; Functional: Public Procurement: gap | Pass |
| 16 | T1R on the wrong-key Swachh Bharat question, with T2's real review from test 7; then T2 again | Edge | Revised question passes T2 re-review (faithful = 1, verdict pass) | re-review: pass | Pass |

Passed 8 of 16.

Details for each test (rule result and full LLM log) are in tests/test_XX.json.
