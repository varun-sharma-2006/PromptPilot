"""Take screenshots of REAL runs of the Streamlit app (used in the Milestone 2 PDF, Section 4).

Starts the app locally, drives it with Playwright (system Chrome), runs the chain on a test input
and saves full-page screenshots to docs/screenshots/.

    python code/screenshots.py
"""
import pathlib
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
PORT = 8599


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    app = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "code" / "app.py"),
                            "--server.port", str(PORT), "--server.headless", "true"],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(8)
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            page = b.new_page(viewport={"width": 1280, "height": 900})
            page.goto(f"http://localhost:{PORT}")
            page.get_by_text("Sample passage").wait_for(timeout=60000)

            # Test 1 input: RTI passage, medium, 4 questions
            page.locator("div[data-baseweb=select]").first.click()
            page.get_by_role("option", name="P1_rti: Right to Information Act, 2005").click()
            nbox = page.get_by_label("Number of questions")
            nbox.fill("4")
            nbox.press("Enter")
            time.sleep(1)
            page.get_by_role("button", name="Run the chain (T1 → T2 → T3)").click()
            page.get_by_text("Accepted questions").wait_for(timeout=600000)
            time.sleep(2)
            page.screenshot(path=str(SHOTS / "run_generate_full.png"), full_page=True)

            # quiz tab: answer first half correctly (synthetic learner), then T4
            page.get_by_role("tab", name="2. Take quiz and get gap summary").click()
            time.sleep(2)
            groups = page.locator("div[role=radiogroup]")
            n = groups.count()
            for i in range(n):
                opts = groups.nth(i).locator("label")
                opts.nth(0 if i % 2 == 0 else 1).click()
                time.sleep(0.5)
            page.get_by_role("button", name="Get gap summary (T4)").click()
            page.get_by_text("Next step:").wait_for(timeout=300000)
            time.sleep(2)
            page.screenshot(path=str(SHOTS / "run_gap_summary.png"), full_page=True)

            page.get_by_role("tab", name="Run log").click()
            time.sleep(2)
            page.screenshot(path=str(SHOTS / "run_log.png"), full_page=False)
            b.close()
        print("screenshots saved to", SHOTS)
    finally:
        app.terminate()


if __name__ == "__main__":
    main()
