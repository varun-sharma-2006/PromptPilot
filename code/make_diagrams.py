"""Draw the four Milestone 2 diagrams from what is actually built (code/chain.py, code/app.py).

    python code/make_diagrams.py   -> docs/diagrams/*.png
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams"
LLM = "#dbe8fb"     # LLM prompt step
CODE = "#e6f4e6"    # deterministic code
HUMAN = "#fdebd3"   # human step
DATA = "#f1f1f1"    # data


def box(ax, x, y, w, h, text, color, fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec="#444", lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, label=None, style="-|>", color="#333", ls="-", dx=0.0, dy=0.12, ha="center"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.2, ls=ls))
    if label:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, ha=ha, fontsize=7.5, color="#333")


def legend(ax, x, y):
    for i, (c, t) in enumerate([(LLM, "LLM prompt"), (CODE, "Python code"), (HUMAN, "Human"), (DATA, "Data")]):
        ax.add_patch(FancyBboxPatch((x + i * 1.9, y), 0.35, 0.25, boxstyle="round,pad=0.01", fc=c, ec="#444"))
        ax.text(x + i * 1.9 + 0.45, y + 0.12, t, va="center", fontsize=8)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    ax.set_xlim(0, w * 1.6)
    ax.set_ylim(0, h * 1.6)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def workflow():
    fig, ax = canvas(10, 4.4)
    W, H = 2.5, 1.0
    xs = [0.1, 3.3, 6.5, 9.7, 12.9]
    top, mid, bot = 5.0, 3.0, 1.0
    box(ax, xs[0], top, W, H, "Passage +\ncompetency +\ndifficulty + N", DATA)
    box(ax, xs[1], top, W, H, "T1 Generate\n(JSON MCQs)", LLM, bold=True)
    box(ax, xs[2], top, W, H, "Auto checks (code)\nschema, A-D keys,\nverbatim quote", CODE)
    box(ax, xs[3], top, W, H, "T2 Review\n(5-point rubric)", LLM, bold=True)
    box(ax, xs[4], top, W, H, "T3 Tag\n(competency +\ndifficulty)", LLM, bold=True)
    box(ax, xs[3], mid, W, H, "T1R Revise\nfailed questions", LLM, bold=True)
    box(ax, xs[4], mid, W, H, "Human reviewer\napproves / edits", HUMAN)
    box(ax, xs[3], bot, W, H, "Learner answers\n(synthetic test data)", DATA)
    box(ax, xs[2], bot, W, H, "Counts per\ncompetency (code)", CODE)
    box(ax, xs[1], bot, W, H, "T4 Gap summary", LLM, bold=True)
    box(ax, xs[0], bot, W, H, "Gap table +\nfeedback", DATA)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, a + W, top + H / 2, b, top + H / 2, "pass" if a == xs[3] else None)
    arrow(ax, xs[3] + 0.8, top, xs[3] + 0.8, mid + H, "fail", dx=-0.1, dy=0, ha="right")
    arrow(ax, xs[3] + 1.7, mid + H, xs[3] + 1.7, top, "re-review\n(max 2 rounds)", dx=0.1, dy=-0.2, ha="left")
    arrow(ax, xs[4] + W / 2, top, xs[4] + W / 2, mid + H)
    arrow(ax, xs[4] + W / 2, mid, xs[3] + W, bot + H / 2, "approved quiz", dx=0.3, dy=0.1)
    for a, b in [(xs[3], xs[2]), (xs[2], xs[1]), (xs[1], xs[0])]:
        arrow(ax, a, bot + H / 2, b + W, bot + H / 2)
    ax.text(0.1, 6.5, "KarmaQuiz prompt workflow (5 prompts: T1, T1R, T2, T3, T4)", fontsize=11, fontweight="bold")
    legend(ax, 0.1, 0.1)
    save(fig, "1_prompt_workflow.png")


def decomposition():
    fig, ax = canvas(10, 4.0)
    box(ax, 5.0, 4.6, 6.0, 0.9, "Goal: competency-tagged, checked MCQs + learner gap report", "#ffffff", 10, True)
    cols = [
        ("T1 Generate", ["Find testable facts", "Write stem at level", "4 options, 1 key", "Quote source sentence", "Return fewer if thin"], LLM),
        ("T2 Review", ["Faithful?", "Single key?", "Plausible distractors?", "Clear?", "Right level?"], LLM),
        ("T1R Revise", ["Read reviewer reason", "Rewrite or drop", "Max 2 rounds"], LLM),
        ("T3 Tag", ["Pick competency\nfrom fixed list", "Tag difficulty", "1-line justification"], LLM),
        ("T4 Gaps", ["Count correct/total\n(Python)", "Level per competency", "What to review next"], LLM),
    ]
    for i, (title, items, c) in enumerate(cols):
        x = 0.2 + i * 3.15
        box(ax, x, 3.3, 2.8, 0.8, title, c, 10, True)
        arrow(ax, 8.0, 4.6, x + 1.4, 4.1)
        for j, it in enumerate(items):
            box(ax, x + 0.15, 2.5 - j * 0.62, 2.5, 0.5, it, "#ffffff", 8)
    ax.text(0.2, 5.9, "Task decomposition", fontsize=11, fontweight="bold")
    save(fig, "2_task_decomposition.png")


def io_flow():
    fig, ax = canvas(10, 3.4)
    steps = [
        ("INPUT", "passage (text)\ncompetency label\ndifficulty\nN questions", DATA),
        ("T1 → JSON", "{question, options A-D,\ncorrect, explanation,\nsource_sentence}", LLM),
        ("T2 → JSON", "{id, scores x5 (0/1),\nverdict, reason,\nsuggested_fix}", LLM),
        ("T3 → JSON", "{id, competency,\ndifficulty,\njustification}", LLM),
        ("T4 → JSON", "table {competency,\ncorrect, total}\n+ {overall, gaps,\nnext_step}", LLM),
    ]
    for i, (t, body, c) in enumerate(steps):
        x = 0.2 + i * 3.15
        box(ax, x, 3.0, 2.6, 0.6, t, c, 9.5, True)
        box(ax, x, 0.9, 2.6, 1.9, body, "#ffffff", 8)
        if i:
            arrow(ax, x - 0.55, 3.3, x, 3.3)
    ax.text(0.2, 4.4, "Input-output flow (every step returns JSON; code validates it before the next step)",
            fontsize=11, fontweight="bold")
    save(fig, "3_input_output_flow.png")


def architecture():
    fig, ax = canvas(10, 3.8)
    box(ax, 0.2, 2.4, 2.6, 1.6, "User (trainer /\nlearner / evaluator)\nweb browser", HUMAN)
    box(ax, 3.6, 1.0, 4.4, 4.2, "", "#fafafa")
    ax.text(5.8, 4.9, "Streamlit app (code/app.py)", ha="center", fontsize=9, fontweight="bold")
    box(ax, 3.9, 3.6, 3.8, 0.8, "UI: 3 tabs\n(generate, quiz, run log)", "#ffffff", 7.5)
    box(ax, 3.9, 2.6, 3.8, 0.8, "chain.py\nT1 → checks → T2 ⇄ T1R → T3 ; T4", CODE, 7.5)
    box(ax, 3.9, 1.6, 1.8, 0.8, "checks.py\nprompts.py", CODE, 8)
    box(ax, 5.9, 1.6, 1.8, 0.8, "llm.py\n(API wrapper)", CODE, 8)
    box(ax, 9.0, 3.6, 3.6, 1.0, "prompts/final/*.txt\n(versioned prompt files)", DATA, 8)
    box(ax, 9.0, 2.2, 3.6, 1.0, "test-data/passages\n(public CC BY-SA text)", DATA, 8)
    box(ax, 9.0, 0.6, 3.6, 1.0, "Google Gemini API\ngemini-3.1-flash-lite", LLM, 8.5, True)
    box(ax, 13.2, 2.2, 2.6, 1.0, "Streamlit secret:\nGOOGLE_API_KEY\n(not in repo)", "#ffffff", 7.5)
    arrow(ax, 2.8, 3.2, 3.6, 3.2, style="<|-|>")
    arrow(ax, 7.7, 4.0, 9.0, 4.1)
    arrow(ax, 7.7, 2.9, 9.0, 2.7)
    arrow(ax, 7.7, 2.0, 9.0, 1.1, "HTTPS", style="<|-|>", dx=0.5, dy=0.0)
    arrow(ax, 13.2, 2.5, 12.0, 1.6, ls="--")
    ax.text(0.2, 5.7, "System architecture (app)", fontsize=11, fontweight="bold")
    save(fig, "4_system_architecture.png")


if __name__ == "__main__":
    workflow()
    decomposition()
    io_flow()
    architecture()
