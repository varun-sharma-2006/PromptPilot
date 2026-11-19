"""Load prompt files from prompts/<version>/ and fill their {VARIABLES}.

Prompt file format:
    ### comments (ignored)
    === SETTINGS ===
    temperature: 0.2 | default
    json_mode: true | false
    === SYSTEM ===
    <system prompt or "none">
    === USER ===
    <user prompt template with {VARIABLES}>
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"


def load(version, name):
    """version: 'v1', 'v2', 'v3' or 'final'; name: e.g. 'T1_generate'."""
    raw = (PROMPTS / version / f"{name}.txt").read_text(encoding="utf-8")
    raw = "\n".join(l for l in raw.splitlines() if not l.startswith("###"))
    parts = dict(re.findall(r"=== (\w+) ===\n(.*?)(?=\n=== \w+ ===|\Z)", raw, re.S))
    settings = {}
    for line in parts.get("SETTINGS", "").strip().splitlines():
        k, v = [x.strip() for x in line.split(":", 1)]
        settings[k] = v
    temp = settings.get("temperature", "default")
    system = parts.get("SYSTEM", "none").strip()
    return {
        "id": f"{version}/{name}",
        "system": None if system.lower() == "none" else system,
        "user": parts["USER"].strip(),
        "temperature": None if temp == "default" else float(temp),
        "json_mode": settings.get("json_mode", "false").lower() == "true",
    }


def fill(template, **values):
    """Replace {NAME} placeholders. Uses plain replace so JSON braces stay intact."""
    out = template
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def key_order(n, seed=0):
    """Balanced, shuffled answer letters for n questions, e.g. 'C, A, D, B, A'.

    From v3 the code (not the model) decides where the correct answer goes, because the model
    ignored the instruction to spread answers (key on D only 2 times in 49 in the v2 runs).
    """
    import random
    rng = random.Random(seed * 1000 + n)
    letters = []
    while len(letters) < n:
        block = list("ABCD")
        rng.shuffle(block)
        letters += block
    return ", ".join(letters[:n])
