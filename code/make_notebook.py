"""Create and execute code/KarmaQuiz_demo.ipynb (a Colab-ready demo with saved outputs).

    python code/make_notebook.py

The notebook reads the API key from Colab secrets or the environment; the key is never written
into the notebook. Outputs saved in the file are from a real execution.
"""
import pathlib

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = pathlib.Path(__file__).resolve().parent.parent
NB = ROOT / "code" / "KarmaQuiz_demo.ipynb"

cells = [
    nbformat.v4.new_markdown_cell(
        "# KarmaQuiz demo (Team PromptPilot, PE-B37-07)\n\n"
        "Runs the full prompt chain on a public passage: **T1 generate → automatic checks → T2 review "
        "(⇄ T1R revise) → T3 tag**, then **T4 gap summary** on synthetic learner answers.\n\n"
        "The outputs below were saved from a real run. To run it again in Colab, add your Gemini key as "
        "a Colab secret named `GOOGLE_API_KEY` (key icon on the left), then choose *Runtime → Run all*."),
    nbformat.v4.new_code_cell(
        "import os, sys, pathlib, json\n"
        "if 'google.colab' in sys.modules:\n"
        "    !git clone -q https://github.com/varun-sharma-2006/PromptPilot.git 2>/dev/null || true\n"
        "    !pip -q install google-genai\n"
        "    from google.colab import userdata\n"
        "    os.environ['GOOGLE_API_KEY'] = userdata.get('GOOGLE_API_KEY')\n"
        "    ROOT = pathlib.Path('PromptPilot')\n"
        "else:\n"
        "    ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == 'code' else pathlib.Path.cwd()\n"
        "sys.path.insert(0, str(ROOT / 'code'))\n"
        "import chain, llm\n"
        "print('Model:', llm.MODEL)"),
    nbformat.v4.new_code_cell(
        "p = json.loads((ROOT / 'test-data/passages/P2_gem.json').read_text(encoding='utf-8'))\n"
        "print(p['title'], '|', p['source'], '|', p['licence'])\n"
        "print(p['text'][:600], '...')"),
    nbformat.v4.new_code_cell(
        "c = chain.Chain()\n"
        "result = c.run(p['text'], p['competency'], 'medium', 3)\n"
        "for rnd in result['review_rounds']:\n"
        "    print(f\"T2 round {rnd['round']}:\", [r.get('verdict') for r in rnd['reviews']])\n"
        "print('Generator note:', result['note'] or '(none)')\n"
        "for i, q in enumerate(result['questions'], 1):\n"
        "    print(f\"\\nQ{i}. {q['question']}\")\n"
        "    for k in 'ABCD':\n"
        "        print(f\"   {k}. {q['options'][k]}{'   <-- key' if k == q['correct'] else ''}\")\n"
        "    print('   Source:', q['source_sentence'])\n"
        "    print('   Tag:', q['competency'], '|', q['tagged_difficulty'], '|', q['tag_justification'])"),
    nbformat.v4.new_code_cell(
        "# Synthetic learner: answers the first question correctly and the rest wrongly\n"
        "qs = result['questions']\n"
        "wrong = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'A'}\n"
        "answers = [q['correct'] if i == 0 else wrong[q['correct']] for i, q in enumerate(qs)]\n"
        "gaps = c.gap_summary(qs, answers)\n"
        "for row in gaps['table']:\n"
        "    print(f\"{row['competency']}: {row['correct']}/{row['total']}\")\n"
        "print(json.dumps(gaps['summary'], indent=2, ensure_ascii=False))"),
    nbformat.v4.new_code_cell(
        "print(f'{len(c.log)} LLM calls in this run:')\n"
        "for e in c.log:\n"
        "    print(' -', e['prompt'], e['meta'])"),
]

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
ExecutePreprocessor(timeout=1800, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(ROOT / "code")}})
NB.write_text(nbformat.writes(nb), encoding="utf-8")
print("wrote", NB)
