"""Build the Milestone 2 PDF and the supporting document from the repository contents.

    python docs/build_pdf.py

Reads docs/team.json, docs/report.json (narrative text, iteration log, modules, limitations,
contribution table), the prompt files, the saved test outputs and the screenshots, so every
number in the PDF comes from a file in this repository.
"""
import json
import pathlib
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TEAM = json.loads((DOCS / "team.json").read_text(encoding="utf-8"))
REPORT = json.loads((DOCS / "report.json").read_text(encoding="utf-8"))

# Fonts with Devanagari-free Unicode coverage for ₹, –, → etc. (Windows fonts)
FONT_DIR = pathlib.Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "consola.ttf")))
pdfmetrics.registerFont(TTFont("Deva", str(FONT_DIR / "Nirmala.ttc"), subfontIndex=0)
                        if (FONT_DIR / "Nirmala.ttc").exists() else TTFont("Deva", str(FONT_DIR / "Nirmala.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily  # noqa: E402
registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")

ss = getSampleStyleSheet()
BODY = ParagraphStyle("b", parent=ss["Normal"], fontName="Body", fontSize=9.5, leading=13, spaceAfter=4)
SMALL = ParagraphStyle("s", parent=BODY, fontSize=8, leading=10.5, spaceAfter=0)
CELL = ParagraphStyle("c", parent=BODY, fontSize=7.8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("cb", parent=CELL, fontName="Body-Bold")
H1 = ParagraphStyle("h1", parent=BODY, fontName="Body-Bold", fontSize=15, leading=19, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Body-Bold", fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4)
H3 = ParagraphStyle("h3", parent=BODY, fontName="Body-Bold", fontSize=10, leading=13, spaceBefore=6, spaceAfter=3)
TITLE = ParagraphStyle("t", parent=H1, fontSize=20, leading=25, alignment=TA_CENTER)
CENTER = ParagraphStyle("ctr", parent=BODY, alignment=TA_CENTER)
CODE = ParagraphStyle("code", parent=BODY, fontName="Mono", fontSize=7, leading=8.8, backColor="#f4f4f4",
                      borderPadding=4, spaceBefore=3, spaceAfter=6)
CAPTION = ParagraphStyle("cap", parent=SMALL, alignment=TA_CENTER, spaceAfter=8, textColor="#333333")

DEV = re.compile(r"([\u0900-\u097F][\u0900-\u097F\s,।।.\-–()]*)")


def deva(s):
    """Wrap Devanagari runs in a font that has the glyphs."""
    return DEV.sub(lambda m: f'<font name="Deva">{m.group(1)}</font>', s)


def P(text, style=BODY):
    return Paragraph(deva(text), style)


def T(text, style=CELL):
    return Paragraph(deva(escape(str(text))).replace("\n", "<br/>"), style)


def code(text, limit=None):
    lines = text.rstrip("\n").splitlines()
    if limit and len(lines) > limit:
        lines = lines[:limit] + [f"... ({len(text.splitlines()) - limit} more lines in the repository file)"]
    out = []
    for ln in lines:
        lead = len(ln) - len(ln.lstrip(" "))
        out.append("&nbsp;" * lead + deva(escape(ln.lstrip(" "))))
    return Paragraph("<br/>".join(out), CODE)


def table(rows, widths, header=True, font=CELL):
    data = [[c if not isinstance(c, str) else T(c, CELLB if (header and i == 0) else font) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef6")))
    t.setStyle(TableStyle(style))
    return t


def img(path, width_mm, caption=None):
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(path)).getSize()
    width = width_mm * mm
    height = width * h / w
    max_h = 230 * mm
    if height > max_h:
        width, height = width * max_h / height, max_h
    out = [Image(str(path), width=width, height=height)]
    if caption:
        out.append(P(caption, CAPTION))
    return KeepTogether(out)


def prompt_file(rel):
    return (ROOT / "prompts" / rel).read_text(encoding="utf-8")


def prompt_parts(rel):
    raw = prompt_file(rel)
    body = "\n".join(l for l in raw.splitlines() if not l.startswith("###"))
    parts = dict(re.findall(r"=== (\w+) ===\n(.*?)(?=\n=== \w+ ===|\Z)", body, re.S))
    return {k: v.strip() for k, v in parts.items()}


def test_record(no):
    return json.loads((ROOT / "test-data" / "outputs" / "tests" / f"test_{no:02d}.json").read_text(encoding="utf-8"))


def sample_run(spec):
    """spec = {"test": 1, "prompt": "final/T1_generate"} -> the first matching logged call in that test."""
    rec = test_record(spec["test"])
    for entry in rec["result"]["log"]:
        if entry["prompt"] == spec["prompt"]:
            v = entry["variables"]
            template = prompt_file(spec["prompt"].replace("final/", "final/") + ".txt")
            lines = []
            for k, val in v.items():
                if "{" + k + "}" not in template:  # only variables this prompt really uses
                    continue
                val = str(val)
                if k == "PASSAGE" and len(val) > 300:
                    val = val[:300] + f"... [{len(v[k])} characters; full passage in test-data/passages]"
                lines.append(f"{{{k}}} = {val}")
            meta = entry["meta"]
            label = (f"Test {spec['test']}, model {meta['model']}, temperature {meta['temperature']}, "
                     f"{meta['seconds']} s")
            return {"label": label, "input": "\n".join(lines), "output": entry["raw_output"]}
    raise KeyError(spec)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18 * mm, 10 * mm, f"{TEAM['team_id']} · {TEAM['team_name']} · {TEAM['short_title']} · Milestone 2")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ======================================================================
def cover():
    L = TEAM["links"]
    s = [Spacer(1, 18 * mm), P("Milestone 2", CENTER), P(escape(TEAM["project_title"]), TITLE), Spacer(1, 4 * mm),
         P(TEAM["course"], CENTER), Spacer(1, 8 * mm)]
    rows = [["Item", "Detail"],
            ["Team ID", TEAM["team_id"]], ["Team name", TEAM["team_name"]],
            ["Project title", TEAM["project_title"]], ["Batch", TEAM["batch"]],
            ["Faculty", TEAM["faculty"]]]
    s.append(table(rows, [40, 134]))
    s.append(Spacer(1, 6 * mm))
    mrows = [["Member", "Enrollment no.", "Role"]]
    for m in TEAM["members"]:
        mrows.append([m["name"] + (" (team leader)" if m["leader"] else ""), m["enrollment"],
                      REPORT["contribution"][[c["name"] for c in REPORT["contribution"]].index(m["name"])]["role"]])
    s.append(table(mrows, [55, 45, 74]))
    s.append(Spacer(1, 6 * mm))
    lrows = [["Link", "URL"], ["1. Prototype", L["prototype"]], ["2. Repository", L["repository"]],
             ["3. Reel", f"{L['reel']}  (length: {L['reel_seconds']} s)"]]
    s.append(table(lrows, [40, 134]))
    s.append(Spacer(1, 6 * mm))
    c = REPORT["counts"]
    s.append(table([["Count", "Value"], ["Final prompts (prompt sheets in Section 2)", str(c["prompts"])],
                    ["Test inputs (rows in Section 4 test table)", str(c["tests"])],
                    ["Prompt versions in iteration log (Section 3)", str(c["versions"])]], [100, 74]))
    s.append(PageBreak())
    return s


def section2():
    s = [P("2. Prompt and solution design", H1), P("(a) Design summary", H2)]
    for para in REPORT["design_summary"]:
        s.append(P(para))
    s.append(P("(b) Diagrams", H2))
    s.append(P("All four diagrams were drawn by our script code/make_diagrams.py from the modules we built. "
               "We use no agents and no retrieval, so there is no agent-loop or RAG diagram."))
    d = DOCS / "diagrams"
    s.append(img(d / "1_prompt_workflow.png", 174, "Figure 1. Prompt workflow"))
    s.append(img(d / "2_task_decomposition.png", 174, "Figure 2. Task decomposition"))
    s.append(img(d / "3_input_output_flow.png", 174, "Figure 3. Input-output flow"))
    s.append(img(d / "4_system_architecture.png", 174, "Figure 4. System architecture (app)"))
    s.append(PageBreak())
    s.append(P("(c) Prompt sheets", H2))
    s.append(P(f"One sheet per final prompt ({len(REPORT['prompt_sheets'])} prompts). Prompts are pasted as text "
               "exactly as stored in prompts/final/. Variables are in curly brackets."))
    for i, sh in enumerate(REPORT["prompt_sheets"]):
        parts = prompt_parts(sh["file"])
        settings = parts.get("SETTINGS", "").replace("\n", "; ")
        rows = [["Field", "Value"],
                ["Prompt ID and name", sh["id_name"]], ["Step in the workflow", sh["step"]],
                ["Purpose", sh["purpose"]], ["Tool and model", REPORT["tool_model"]],
                ["Settings", settings + "; all other settings default"],
                ["Variables", sh["variables"]], ["Number of examples included", sh["examples"]],
                ["Output format", sh["output_format"]]]
        block = [P(f"Prompt sheet {i + 1}: {sh['id_name']}", H3), table(rows, [42, 132]),
                 P("<b>Full system prompt</b>", SMALL)]
        s.append(KeepTogether(block[:2]))
        s.append(block[2])
        s.append(code(parts.get("SYSTEM", "none")))
        s.append(P("<b>Full user prompt template</b>", SMALL))
        s.append(code(parts["USER"]))
        run = sample_run(sh["sample_run"])
        s.append(P(f"<b>Sample run</b> ({escape(run['label'])})", SMALL))
        s.append(P("Real input (variables):", SMALL))
        s.append(code(run["input"], limit=24))
        s.append(P("Actual output (raw, as returned by the model):", SMALL))
        s.append(code(run["output"], limit=sh["sample_run"].get("limit", 45)))
        s.append(Spacer(1, 3 * mm))
    s.append(PageBreak())
    return s


def section3():
    s = [P("3. Implementation", H1), P("What is built", H2)]
    for para in REPORT["what_is_built"]:
        s.append(P(para))
    s.append(P("Module status", H2))
    rows = [["Module", "What it does", "Status", "Notes"]] + \
        [[m["module"], m["does"], m["status"], m["notes"]] for m in REPORT["modules"]]
    s.append(table(rows, [34, 62, 22, 56]))
    s.append(P("Prompt iteration log", H2))
    s.append(P(REPORT["iteration_intro"]))
    rows = [["Version", "What changed", "Why it was changed", "Result after the change"]] + \
        [[v["version"], v["changed"], v["why"], v["result"]] for v in REPORT["iterations"]]
    s.append(table(rows, [18, 52, 40, 64]))
    if REPORT.get("iteration_metrics"):
        s.append(Spacer(1, 3 * mm))
        s.append(P("Measured results per T1 version (same 4 inputs × 3 runs each = 12 runs per version)", H3))
        m = REPORT["iteration_metrics"]
        s.append(table(m, [58] + [116 / (len(m[0]) - 1)] * (len(m[0]) - 1)))
        s.append(P(REPORT["iteration_metrics_note"], SMALL))
    s.append(P("Full text of each version", H2))
    for v in REPORT["iterations"]:
        for f in v["files"]:
            s.append(P(f"{v['version']}: prompts/{f}", H3))
            s.append(code(prompt_file(f)))
    s.append(PageBreak())
    return s


def section4():
    s = [P("4. Demonstration and testing", H1), P("Test table", H2)]
    s.append(P(REPORT["test_intro"]))
    rows = [["No.", "Input (short)", "Type", "Expected output", "Actual output (short)", "Pass / Fail"]]
    passed = 0
    for no in range(1, REPORT["counts"]["tests"] + 1):
        r = test_record(no)
        c = r["case"]
        passed += r["pass"]
        note = REPORT.get("test_notes", {}).get(str(no))
        actual = r["rule_detail"] + (f"\nOur note: {note}" if note else "")
        rows.append([str(no), c["short"], c["type"], c["expect"], actual, "Pass" if r["pass"] else "Fail"])
    s.append(table(rows, [9, 33, 13, 38, 66, 15]))
    s.append(P(f"Result: {passed} of {REPORT['counts']['tests']} tests passed. "
               "Raw outputs for every test are in test-data/outputs/tests/.", SMALL))
    s.append(P("Screenshots of real runs", H2))
    for sh in REPORT["screenshots"]:
        s.append(img(DOCS / "screenshots" / sh["file"], sh.get("width", 150), sh["caption"]))
    s.append(P("Known limitations and what we will try next", H2))
    rows = [["Limitation", "What we will try next"]] + [[l["limit"], l["next"]] for l in REPORT["limitations"]]
    s.append(table(rows, [90, 84]))
    s.append(PageBreak())
    return s


def section5():
    s = [P("5. Repository", H1), P(f"Repository: {TEAM['links']['repository']}")]
    shot = DOCS / "screenshots" / "repository.png"
    if shot.exists():
        s.append(img(shot, 160, "Figure. Repository home page on GitHub"))
    s.append(P("What changed since Milestone 1", H2))
    for line in REPORT["repo_changes"]:
        s.append(P("• " + line))
    s.append(PageBreak())
    return s


def abstract_flow(heading_style=H1, numbered=True):
    a = REPORT["abstract"]
    s = [P(("6. Supporting document: " if numbered else "") + "Research abstract", heading_style),
         P(f"<b>{escape(a['title'])}</b>"), P(f"{TEAM['team_name']} ({TEAM['team_id']}) · " +
                                              ", ".join(m['name'] for m in TEAM['members']), SMALL),
         Spacer(1, 3 * mm)]
    for k in ("Problem", "Method", "Results", "Conclusion"):
        s.append(P(f"<b>{k}.</b> {a[k.lower()]}"))
    s.append(P(f"<i>Word count: {sum(len(a[k].split()) for k in ('problem', 'method', 'results', 'conclusion'))}</i>",
               SMALL))
    if a.get("table"):
        s.append(Spacer(1, 2 * mm))
        s.append(table(a["table"], [60] + [114 / (len(a["table"][0]) - 1)] * (len(a["table"][0]) - 1)))
        s.append(P(a.get("table_note", ""), SMALL))
    return s


def section7():
    s = [P("7. Team contribution", H1)]
    rows = [["Member name", "Enrollment no.", "Role", "Tasks done in Milestone 2", "Evidence", "Contribution (%)"]]
    enr = {m["name"]: m["enrollment"] for m in TEAM["members"]}
    for c in REPORT["contribution"]:
        rows.append([c["name"], enr[c["name"]], c["role"], c["tasks"], c["evidence"], str(c["percent"])])
    s.append(table(rows, [24, 22, 22, 46, 44, 16]))
    total = sum(c["percent"] for c in REPORT["contribution"])
    s.append(P(f"Total: {total}%. All members have read and agreed to this table.", SMALL))
    return s


def build():
    name = f"M2_{TEAM['team_id']}_{TEAM['short_title']}.pdf"
    doc = SimpleDocTemplate(str(DOCS / name), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=f"Milestone 2 - {TEAM['short_title']}",
                            author=TEAM["team_name"])
    story = cover() + section2() + section3() + section4() + section5() + abstract_flow() + [PageBreak()] + section7()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", name)

    sup = f"{TEAM['team_name']}_ResearchAbstract.pdf"
    doc2 = SimpleDocTemplate(str(DOCS / sup), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                             topMargin=18 * mm, bottomMargin=16 * mm, title="Research abstract", author=TEAM["team_name"])
    doc2.build(abstract_flow(H1, numbered=False), onFirstPage=footer, onLaterPages=footer)
    print("wrote", sup)


if __name__ == "__main__":
    build()
