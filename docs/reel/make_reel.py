"""Record the Milestone 2 reel: a real screen recording with burned-in captions.

    python docs/reel/make_reel.py          (needs GOOGLE_API_KEY, Playwright + Chrome, imageio-ffmpeg)

What it does
  1. Builds simple viewer pages from the REAL repository files (prompts, saved outputs, metrics,
     test table), so Part 2 and Part 4 show actual content.
  2. Starts the Streamlit app and drives it with Playwright: Part 3 is a LIVE run on the Gemini API.
  3. Records everything with Playwright's video recorder and logs every waiting period
     (page loads, model calls).
  4. Cuts only the waiting periods with ffmpeg and exports an MP4 (1920x1080, 30 fps).
     The caption says when waiting time was cut and how long the real call took.

Output (outside the repo, the video is too large to commit): ../reel_out/KarmaQuiz_reel.mp4
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import time

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT.parent / "reel_out"
BUILD = OUT / "pages"
PORT = 8611
W, H = 1280, 720

CSS = """
*{box-sizing:border-box} body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:#f6f7f9;color:#1d2330}
.wrap{padding:28px 40px 120px} .path{display:inline-block;font:600 15px Consolas,monospace;background:#1d2330;
color:#fff;padding:6px 12px;border-radius:6px;margin-bottom:6px} .sub{color:#5a6372;font-size:15px;margin:2px 0 14px}
pre{background:#fff;border:1px solid #dde1e7;border-radius:8px;padding:14px 0;font:16px/1.5 Consolas,monospace;
white-space:pre-wrap;margin:0} .ln{display:block;padding:0 16px 0 0} .ln i{display:inline-block;width:46px;
text-align:right;color:#9aa3b1;font-style:normal;margin-right:14px;user-select:none}
.hl{background:#fff1a8} .bad{background:#ffd6d6} .good{background:#d4f5dc} .cmt{color:#6b7280}
table{border-collapse:collapse;background:#fff;font-size:15px;width:100%} td,th{border:1px solid #dde1e7;padding:6px 9px;
text-align:left;vertical-align:top} th{background:#1d2330;color:#fff} tr.hl td{background:#fff1a8}
.pass{color:#137333;font-weight:700} .fail{color:#b3261e;font-weight:700} h1{margin:0 0 4px;font-size:30px}
.card{height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
background:linear-gradient(135deg,#1d2a4a,#2e5aa8);color:#fff} .card h1{font-size:64px;margin:0}
.card p{font-size:24px;margin:8px 0;opacity:.95} .card .small{font-size:18px;opacity:.8}
ul.lim li{margin:8px 0;font-size:18px} .next{color:#2e5aa8}
"""

CAPTION_JS = """
(args) => {
  let bar = document.getElementById('reel-cap');
  if (!bar) {
    bar = document.createElement('div'); bar.id = 'reel-cap';
    bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:2147483647;padding:14px 28px 16px;' +
      'pointer-events:none;background:rgba(15,20,32,.88);color:#fff;font:600 23px/1.35 "Segoe UI",Arial,sans-serif;text-align:center;';
    const chip = document.createElement('div'); chip.id = 'reel-chip';
    chip.style.cssText = 'position:fixed;top:12px;right:14px;z-index:2147483647;background:#f4b400;color:#1d2330;' +
      'pointer-events:none;font:700 15px "Segoe UI",Arial,sans-serif;padding:5px 12px;border-radius:14px;';
    document.body.appendChild(bar); document.body.appendChild(chip);
  }
  bar.textContent = args.text; bar.style.display = args.text ? 'block' : 'none';
  const chip = document.getElementById('reel-chip');
  chip.textContent = args.chip; chip.style.display = args.chip ? 'block' : 'none';
}
"""


def page_html(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")


def code_view(path_label, sub, lines, marks=None, start=1):
    marks = marks or {}
    rows = []
    for i, line in enumerate(lines, start):
        cls = marks.get(i, "cmt" if line.startswith("###") else "")
        rows.append(f"<span class='ln {cls}' id='L{i}'><i>{i}</i>{html.escape(line) or ' '}</span>")
    return (f"<div class='wrap'><div class='path'>{html.escape(path_label)}</div><div class='sub'>{sub}</div>"
            f"<pre>{''.join(rows)}</pre></div>")


def build_pages():
    BUILD.mkdir(parents=True, exist_ok=True)
    rd = lambda p: (ROOT / p).read_text(encoding="utf-8")
    team = json.loads(rd("docs/team.json"))
    report = json.loads(rd("docs/report.json"))
    pages = {}

    members = " · ".join(m["name"] for m in team["members"])
    pages["title"] = page_html("title", f"""<div class='card'><p class='small'>SCSE4041 Prompt Engineering · Milestone 2</p>
      <h1>KarmaQuiz</h1><p>Generate, quality-check and competency-tag MCQs from training material</p>
      <p>Team PromptPilot · {team['team_id']} · SIH26101 (iGOT Karmayogi)</p><p class='small'>{members}</p></div>""")

    v1 = rd("prompts/v1/T1_generate.txt").splitlines()
    pages["v1_prompt"] = page_html("v1", code_view(
        "prompts/v1/T1_generate.txt", "BEFORE: T1 version 1, the Milestone 1 baseline prompt", v1,
        {i: "hl" for i, l in enumerate(v1, 1) if l.startswith(("Task:", "Output:"))}))

    case7 = next(c for c in json.loads(rd("test-data/cases/test_cases.json"))["cases"] if c["no"] == 7)
    q = case7["question"]
    lines = json.dumps(q, ensure_ascii=False, indent=2).splitlines()
    marks = {}
    for i, l in enumerate(lines, 1):
        if '"correct": "B"' in l:
            marks[i] = "bad"
        elif l.strip().startswith(('"C":', '"source_sentence"')):
            marks[i] = "good"
    pages["v1_output"] = page_html("v1 out", code_view(
        "test-data/cases/test_cases.json → case 7", "A real question written by the v1 prompt "
        "(Swachh Bharat Mission passage, saved from the v1 experiment runs)", lines, marks))

    fin = rd("prompts/final/T1_generate.txt").splitlines()
    fmarks = {}
    for i, l in enumerate(fin, 1):
        if "distractors" in l and l.startswith("###") or "Question pattern" in l or l.startswith(("- easy", "- medium", "- hard")):
            fmarks[i] = "hl"
    pages["final_prompt"] = page_html("final", code_view(
        "prompts/final/T1_generate.txt", "AFTER: T1 final (version 5)", fin[:26], fmarks))

    t3 = json.loads(rd("test-data/outputs/tests/test_03.json"))["result"]["questions"]
    fq = next(x for x in t3 if "reinforce" in x["source_sentence"])
    fq = {k: fq[k] for k in ("question", "options", "correct", "explanation", "source_sentence")}
    lines = json.dumps(fq, ensure_ascii=False, indent=2).splitlines()
    key = fq["correct"]
    marks = {i: "good" for i, l in enumerate(lines, 1)
             if l.strip().startswith((f'"{key}":', '"correct"', '"source_sentence"'))}
    pages["final_output"] = page_html("final out", code_view(
        "test-data/outputs/tests/test_03.json", "Final prompt, same passage and same fact "
        "(Phase 2 of Swachh Bharat): answer key matches the source sentence", lines, marks))

    rows = report["iteration_metrics"]
    keep = {"Valid JSON (runs)", "Correct option A/B/C/D", "Questions sharing a source sentence",
            "Judge: faithful", "Judge: pass (all 5 rubric items)"}
    trs = "".join(f"<tr class='{'hl' if r[0].startswith(('Judge: pass', 'Correct option')) else ''}'>" +
                  "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:] if r[0] in keep)
    pages["metrics"] = page_html("metrics", f"""<div class='wrap'><div class='path'>Milestone 2 PDF · Section 3 · Iteration log</div>
      <div class='sub'>Each T1 version: 12 runs (4 passages × 3 repeats), every question scored by the same fixed reviewer prompt (T2 v2, temperature 0)</div>
      <table><tr>{''.join(f'<th>{html.escape(c)}</th>' for c in rows[0])}</tr>{trs}</table></div>""")

    md = rd("test-data/outputs/test_results.md")
    trs = []
    for line in md.splitlines():
        m = re.match(r"\| (\d+) \| (.*?) \| (\w+) \| .*? \| .*? \| (Pass|Fail) \|", line)
        if m:
            no, short, typ, res = m.groups()
            trs.append(f"<tr><td>{no}</td><td>{html.escape(short)}</td><td>{typ}</td>"
                       f"<td class='{res.lower()}'>{res}</td></tr>")
    pages["tests"] = page_html("tests", f"""<div class='wrap'><div class='path'>test-data/outputs/test_results.md</div>
      <div class='sub'>16 test inputs on the final prompts, expected outputs written before running · <b>8 of 16 pass</b></div>
      <table style='font-size:13.5px'><tr><th>No.</th><th>Input</th><th>Type</th><th>Result</th></tr>{''.join(trs)}</table></div>""")

    lis = "".join(f"<li>{html.escape(x['limit'])}<br><span class='next'>Next: {html.escape(x['next'])}</span></li>"
                  for x in report["limitations"][:3])
    pages["limits"] = page_html("limits", f"""<div class='wrap'><div class='path'>Milestone 2 PDF · Section 4 · Limitations</div>
      <div class='sub'>What does not work yet, and the Milestone 3 plan</div><ul class='lim'>{lis}</ul></div>""")

    pages["end"] = page_html("end", f"""<div class='card'><h1>KarmaQuiz</h1><p>Team PromptPilot · {team['team_id']}</p>
      <p class='small'>{team['links']['repository']}</p><p class='small'>All prompts, code, test data and outputs are in the repository</p></div>""")

    urls = {}
    for name, content in pages.items():
        f = BUILD / f"{name}.html"
        f.write_text(content, encoding="utf-8")
        urls[name] = f.as_uri()
    return urls


class Recorder:
    def __init__(self, page):
        self.page, self.t0, self.cuts, self.chip = page, time.monotonic(), [], ""

    def now(self):
        return time.monotonic() - self.t0

    def cap(self, text, chip=None):
        if chip is not None:
            self.chip = chip
        self.page.evaluate(CAPTION_JS, {"text": text, "chip": self.chip})

    def hold(self, seconds):
        self.page.wait_for_timeout(int(seconds * 1000))

    def goto(self, url, text="", chip=None, settle=0.6):
        start = self.now()
        self.page.goto(url, wait_until="load")
        self.hold(settle)
        self.cap(text, chip)
        self.hold(0.15)
        self.cuts.append((start, self.now()))

    def scroll(self, total, seconds, x=640, y=360):
        self.page.mouse.move(x, y)
        steps = max(1, int(seconds * 25))
        for _ in range(steps):
            self.page.mouse.wheel(0, total / steps)
            self.page.wait_for_timeout(40)


def record(urls):
    app = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "code" / "app.py"),
                            "--server.port", str(PORT), "--server.headless", "true",
                            "--browser.gatherUsageStats", "false"],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    timings = {}
    try:
        time.sleep(8)
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            ctx = b.new_context(viewport={"width": W, "height": H},
                                record_video_dir=str(OUT / "raw"), record_video_size={"width": W, "height": H})
            page = ctx.new_page()
            r = Recorder(page)

            # ---------- Part 1: Problem (~12 s) ----------
            r.goto(urls["title"], "", "1 · Problem")
            r.hold(3.5)
            r.goto("https://github.com/varun-sharma-2006/PromptPilot#readme",
                   "iGOT Karmayogi trains crores of government employees. Every course needs quiz "
                   "questions that are correct and tied to a competency.", settle=2.5)
            r.scroll(260, 1.0)
            r.hold(3.2)
            r.cap("KarmaQuiz: a chain of 5 prompts that writes, checks and competency-tags MCQs "
                  "from any training passage, then finds a learner's gaps.")
            r.scroll(220, 1.0)
            r.hold(3.5)

            # ---------- Part 2: Prompt experiment (~38 s) ----------
            r.goto(urls["v1_prompt"], "BEFORE: our first prompt (v1, from Milestone 1) is one plain "
                   "instruction, with no rules for checking the answer key.", "2 · Prompt experiment")
            r.hold(6)
            r.goto(urls["v1_output"], "Real v1 output on the Swachh Bharat passage: it marks B as the "
                   "correct answer…")
            r.hold(4.5)
            r.cap("…but its own source sentence says Phase 2 is to reinforce Phase 1. That is option C. "
                  "Across all v1 runs, D was never used as the key.")
            r.hold(6.5)
            r.goto(urls["final_prompt"], "AFTER: final prompt (v5). The model writes the answer + 3 wrong "
                   "options and our code places them at A–D. Each difficulty level has a pattern.")
            r.hold(3.5)
            r.scroll(200, 1.2)
            r.hold(3.8)
            r.goto(urls["final_output"], "Same passage, same fact, final prompt: the answer key now "
                   "matches the source sentence.")
            r.hold(6)
            r.goto(urls["metrics"], "5 versions × 12 runs, scored by one fixed reviewer prompt: rubric "
                   "pass 37/48 (77%) → 42/43 (98%), answer letters now balanced.")
            r.hold(8)

            # ---------- Part 3: Live demo (~55-60 s) ----------
            r.goto(f"http://localhost:{PORT}", "LIVE DEMO: a real run of our Streamlit app, calling the "
                   "Gemini API (gemini-3.1-flash-lite).", "3 · Live demo", settle=0.5)
            start = r.now()
            page.get_by_text("Sample passage").wait_for(timeout=60000)
            r.hold(1.0)
            r.cap("LIVE DEMO: a real run of our Streamlit app, calling the Gemini API (gemini-3.1-flash-lite).")
            r.cuts.append((start, r.now()))
            r.hold(3.5)
            r.cap("Input: a public passage on the Government e-Marketplace (GeM) · difficulty easy · 4 questions")
            selects = page.locator("div[data-baseweb=select]")
            selects.first.click()
            r.hold(0.8)
            page.get_by_role("option", name="P2_gem: Government e Marketplace").click()
            r.hold(1.5)
            selects.nth(2).click()
            r.hold(0.7)
            page.get_by_role("option", name="easy", exact=True).click()
            r.hold(2.0)
            btn = page.get_by_role("button", name="Run the chain (T1 → T2 → T3)")
            btn.scroll_into_view_if_needed()
            r.hold(0.8)
            r.cap("T1 writes the questions → code checks every quote is in the passage → T2 reviews each "
                  "on a 5-point rubric → T3 tags the competency")
            btn.click()
            t_click = time.monotonic()
            r.hold(3.5)
            cut_start = r.now()
            page.get_by_text("Accepted questions").wait_for(timeout=420000)
            secs = round(time.monotonic() - t_click)
            timings["chain_seconds"] = secs
            r.cap(f"Done. (Waiting time cut from the video: this real run took {secs} s.)")
            r.hold(0.3)
            r.cuts.append((cut_start, r.now() - 1.0))
            r.hold(2.8)
            r.cap("The T2 reviewer scores every question: faithful · one correct answer · plausible wrong "
                  "options · clear · right level")
            exp = page.locator("summary").filter(has_text="T2 review round 1")
            exp.first.scroll_into_view_if_needed()
            exp.first.click()
            r.hold(4.5)
            r.cap("Accepted questions: answer key ✔, competency tag, difficulty, and the exact source "
                  "sentence from the passage.")
            page.get_by_text("Accepted questions").first.scroll_into_view_if_needed()
            r.hold(1.5)
            r.scroll(700, 4.5)
            r.hold(2.5)

            page.get_by_role("tab", name="2. Take quiz and get gap summary").click()
            r.cap("Take the quiz: a synthetic learner answers (test data, not a real person).")
            r.hold(1.5)
            groups = page.locator("div[role=radiogroup]")
            for i in range(groups.count()):
                groups.nth(i).scroll_into_view_if_needed()
                groups.nth(i).locator("label").nth(0 if i % 2 == 0 else 1).click()
                r.hold(0.7)
            gbtn = page.get_by_role("button", name="Get gap summary (T4)")
            gbtn.scroll_into_view_if_needed()
            r.hold(0.6)
            r.cap("Python counts the score per competency. T4 writes the gap summary and the next step.")
            r.hold(1.5)  # let Streamlit finish the rerun from the last answer before clicking
            gbtn.click()
            t_click = time.monotonic()
            r.hold(1.5)
            cut_start = r.now()
            for attempt in range(4):
                try:
                    page.get_by_text("Next step:").wait_for(timeout=45000)
                    break
                except Exception:
                    page.screenshot(path=str(OUT / f"debug_t4_{attempt}.png"))
                    gbtn.click()
            else:
                raise RuntimeError("T4 summary never appeared")
            secs = round(time.monotonic() - t_click)
            timings["t4_seconds"] = secs
            r.hold(0.3)
            r.cuts.append((cut_start, r.now() - 0.3))
            page.get_by_text("Next step:").scroll_into_view_if_needed()
            r.hold(0.5)
            r.scroll(-150, 0.6)
            r.hold(5.5)

            page.get_by_role("tab", name="Run log").click()
            r.cap("Every LLM call is logged: prompt version, temperature, time and the raw JSON output.")
            r.hold(1.0)
            page.get_by_text("final/T1_generate").first.click()
            r.hold(4.5)

            # ---------- Part 4: Progress and next steps (~20 s) ----------
            r.goto(urls["tests"], "Testing: 16 inputs (normal, edge and invalid cases). 8 pass and 8 fail, "
                   "and we kept every failure.", "4 · Progress and next steps")
            r.hold(3.0)
            r.scroll(260, 1.5)
            r.hold(3.0)
            r.goto(urls["limits"], "Still failing: gibberish text produced questions, too few questions at "
                   "medium/hard, inconsistent difficulty tags.")
            r.hold(4.5)
            r.cap("Milestone 3: a meaningful-content check, a retry when questions are short, and "
                  "hand-scoring 40 questions to check our AI reviewer.")
            r.hold(5.0)
            r.goto(urls["end"], "", "")
            r.hold(3.0)
            total = r.now()
            video = page.video.path()
            ctx.close()
            b.close()
        return pathlib.Path(video), r.cuts, total, timings
    finally:
        app.terminate()


def keep_segments(cuts, total):
    keep, pos = [], 0.0
    for a, b in sorted(cuts):
        if a > pos:
            keep.append((pos, a))
        pos = max(pos, b)
    if total > pos:
        keep.append((pos, total))
    return [(a, b) for a, b in keep if b - a > 0.05]


def render(video, segs, out):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    parts = []
    for i, (a, b) in enumerate(segs):
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[c]"
    flt = ";".join(parts + [concat, "[c]fps=30,scale=1920:1080:flags=lanczos,format=yuv420p[out]"])
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(video), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", flt, "-map", "[out]", "-map", "1:a", "-shortest",
                    "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "aac", "-movflags", "+faststart",
                    str(out)], check=True)


def duration(path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    err = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    OUT.mkdir(exist_ok=True)
    urls = build_pages()
    video, cuts, total, timings = record(urls)
    segs = keep_segments(cuts, total)
    out = OUT / "KarmaQuiz_reel.mp4"
    render(video, segs, out)
    d = duration(out)
    info = {"raw_seconds": round(total, 1), "final_seconds": round(d, 2), "cuts": len(cuts), **timings}
    (OUT / "reel_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))
    print("saved", out)


if __name__ == "__main__":
    main()
