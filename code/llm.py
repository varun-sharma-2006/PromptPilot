"""Thin wrapper around the Gemini API used by every KarmaQuiz prompt.

The API key is read from the GOOGLE_API_KEY environment variable (or from
Streamlit secrets when running the web app). It is never stored in the repo.
"""
import json
import os
import re
import time

from google import genai
from google.genai import types

# Model choice (19 Nov 2026): gemini-2.5-flash is no longer offered to new API keys, the 3.5+ Flash
# models returned 503 (high demand), and gemini-3-flash-preview allows only 20 free requests a day.
# gemini-3.1-flash-lite is stable, free, and has enough daily quota for the experiments, so every
# recorded run uses it. Override with the KARMAQUIZ_MODEL environment variable.
MODEL = os.environ.get("KARMAQUIZ_MODEL", "gemini-3.1-flash-lite")

_client = None


def _get_key():
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        try:  # Streamlit Cloud secrets
            import streamlit as st
            key = st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            key = None
    if not key:
        raise RuntimeError("Set GOOGLE_API_KEY (environment variable or Streamlit secret).")
    return key


def client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=_get_key(),
                               http_options=types.HttpOptions(timeout=120_000))  # ms; avoid hung calls
    return _client


def call(user_prompt, system_prompt=None, temperature=None, json_mode=False, retries=4):
    """Send one prompt to Gemini and return (text, meta)."""
    cfg = {}
    if system_prompt:
        cfg["system_instruction"] = system_prompt
    if temperature is not None:
        cfg["temperature"] = temperature
    if json_mode:
        cfg["response_mime_type"] = "application/json"
    last_err = None
    for attempt in range(retries):
        try:
            t0 = time.time()
            resp = client().models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(**cfg) if cfg else None,
            )
            return resp.text or "", {
                "model": MODEL,
                "temperature": temperature if temperature is not None else "default",
                "json_mode": json_mode,
                "seconds": round(time.time() - t0, 1),
            }
        except Exception as e:  # rate limits / transient errors
            last_err = e
            msg = str(e)
            if "PerDay" in msg:  # daily free quota used up: waiting will not help
                raise
            time.sleep((20 if "429" in msg else 5) * (attempt + 1))
    raise last_err


def parse_json(text):
    """Parse model output as JSON. Strips ``` fences if present.

    Returns (obj, error_message). obj is None if parsing failed.
    """
    s = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, re.S)
    if m:
        s = m.group(1)
    try:
        return json.loads(s), None
    except json.JSONDecodeError as e:
        return None, str(e)
