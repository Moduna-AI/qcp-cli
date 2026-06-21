"""LLM provider integration.

Gemini is the default and only built-in provider for the MVP. The
provider interface is intentionally tiny so more providers (OpenAI,
Claude, local models) can be added later without touching the CLI.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .errors import LLMError, NoApiKeyConfiguredError
from . import config as cfg

# Default model. Google regularly retires older Gemini models (gemini-2.0-flash
# was shut down June 1, 2026), so this is overridable without a code change via
# the GEMINI_MODEL env var or `gemini_model` in config (see config.get_gemini_model).
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def get_model() -> str:
    return os.environ.get("GEMINI_MODEL") or cfg.get("gemini_model") or DEFAULT_GEMINI_MODEL


SQL_SYSTEM_PROMPT = """You are a senior data analyst that writes PostgreSQL queries.
Given a database schema and a question in plain English, respond with ONLY a
single valid PostgreSQL SELECT statement that answers the question. Rules:
- Output raw SQL only. No markdown fences, no explanation, no semicolon-separated multiple statements.
- Only use SELECT / WITH statements. Never modify data.
- Use the exact table and column names from the schema provided.
- Add a LIMIT clause (max 200) unless the question implies an aggregate/single row result.
"""

INSIGHTS_SYSTEM_PROMPT = """You are a senior data analyst. Given a database schema and
optionally some sample query results, produce 3-6 concise, concrete insights or
suggested analyses a user could run next. Respond in plain text bullet points,
no markdown headers, no preamble.
"""


def require_api_key() -> str:
    key = cfg.get_gemini_api_key()
    if not key:
        raise NoApiKeyConfiguredError("gemini")
    return key


def _headers(api_key: str) -> dict[str, str]:
    # x-goog-api-key header is Google's current recommended auth method
    # (older docs used a ?key= query param, which still works but is
    # being phased out for unrestricted keys).
    return {"Content-Type": "application/json", "x-goog-api-key": api_key}


def _call_gemini(system_prompt: str, user_prompt: str, api_key: str) -> str:
    url = GEMINI_URL.format(model=get_model())
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise LLMError(f"Gemini API returned {e.code}: {body[:300]}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"could not reach Gemini API: {e.reason}") from e

    try:
        candidates = data["candidates"]
        parts = candidates[0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as e:
        raise LLMError(f"unexpected Gemini response shape: {data}") from e


def _clean_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("sql"):
            text = text[3:]
    return text.strip().rstrip(";").strip()


def generate_sql(question: str, schema_summary: str) -> str:
    api_key = require_api_key()
    user_prompt = f"Schema:\n{schema_summary}\n\nQuestion: {question}\n\nSQL:"
    raw = _call_gemini(SQL_SYSTEM_PROMPT, user_prompt, api_key)
    return _clean_sql(raw)


def generate_insights(schema_summary: str, sample_data: str | None = None) -> str:
    api_key = require_api_key()
    user_prompt = f"Schema:\n{schema_summary}\n"
    if sample_data:
        user_prompt += f"\nSample results from a recent query:\n{sample_data}\n"
    user_prompt += "\nWhat insights or next analyses would you suggest?"
    return _call_gemini(INSIGHTS_SYSTEM_PROMPT, user_prompt, api_key)


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Lightweight check that the key works, used by `qcp auth`.

    Returns (ok, detail). detail is empty on success, or a human-readable
    reason on failure (so callers can show *why* validation failed instead
    of a generic message).
    """
    url = GEMINI_URL.format(model=get_model())
    payload = {"contents": [{"role": "user", "parts": [{"text": "ping"}]}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {e.code}: {body[:300]}"
    except urllib.error.URLError as e:
        return False, f"could not reach Gemini API: {e.reason}"
