"""Scan every file tracked by git for API keys or passwords before a push.

The Milestone 2 guidelines give 0 marks for the repository if a key is visible, so run this
before every push (it also runs in GitHub Actions):

    python code/check_secrets.py

Exit code 0 = nothing found, 1 = possible secret (file and line are printed, the value is masked).
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    "GitHub token": re.compile(r"\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}"),
    "Private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Key assigned in code": re.compile(
        r"(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"'\s]{16,}[\"']", re.I),
}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".ttf", ".woff", ".woff2"}
FORBIDDEN_FILES = {".env", "secrets.toml"}


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


def mask(s):
    return s[:4] + "*" * max(len(s) - 8, 4) + s[-4:] if len(s) > 8 else "****"


def main():
    problems = []
    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_FILES:
            problems.append(f"{rel}: this file must never be committed")
            continue
        if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for no, line in enumerate(text.splitlines(), 1):
            for label, rx in PATTERNS.items():
                for m in rx.finditer(line):
                    problems.append(f"{rel}:{no}: {label}: {mask(m.group(0))}")
    if problems:
        print("Possible secrets found. Remove them, rotate the key, and do not push:")
        print("\n".join("  " + p for p in problems))
        return 1
    print(f"No secrets found in {len(tracked_files())} tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
