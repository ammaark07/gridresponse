"""Free-text field-report parser.

Turns a free-text storm field report into strict JSON:

    {
      "hazards": string[],
      "est_customers": int,
      "severity_signal": "low" | "medium" | "high",
      "access_blocked": bool
    }

Primary path uses the OpenAI API with a strict-JSON system prompt. If
``OPENAI_API_KEY`` is unset (or the API call/parse fails), it falls back to a
deterministic keyword matcher so the app keeps working fully offline.
"""
from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.schemas import ParsedReport

SYSTEM_PROMPT = (
    "You are an assistant for an electrical-utility storm response team. "
    "Extract structured data from a free-text field report. "
    "Respond with ONLY a single JSON object and no prose, matching exactly this schema:\n"
    "{\n"
    '  "hazards": string[],            // short hazard phrases, e.g. "downed power line", "fallen tree"\n'
    '  "est_customers": integer,       // best estimate of customers affected; 0 if unknown\n'
    '  "severity_signal": "low" | "medium" | "high",\n'
    '  "access_blocked": boolean       // true if crews cannot reach the site\n'
    "}\n"
    "Use lowercase hazard phrases. Do not invent details not implied by the report."
)

# ----------------------------------------------------------- keyword tables ---
_HAZARD_KEYWORDS: list[tuple[str, str]] = [
    ("downed power line", r"down(ed)?\s+(power\s+)?lines?|wires?\s+down|live\s+wire"),
    ("fallen tree", r"\btrees?\b|branch(es)?|limb"),
    ("fire", r"\bfire\b|smoke|sparking|sparks|burning"),
    ("flooding", r"flood(ing|ed)?|water\s+rising|submerged"),
    ("gas leak", r"gas\s+leak|smell\s+of\s+gas|natural\s+gas"),
    ("damaged pole", r"\bpole\b|cross-?arm"),
    ("damaged transformer", r"transformer|substation"),
    ("ice accumulation", r"\bice\b|ice\s+storm|freezing\s+rain"),
    ("debris", r"debris|rubble|wreckage"),
]

_HIGH_SEVERITY = re.compile(
    r"\b(fire|explosion|gas\s+leak|live\s+wire|injur|trapped|emergency|hospital|critical|major|widespread)\b",
    re.IGNORECASE,
)
_MEDIUM_SEVERITY = re.compile(
    r"\b(downed|down|fallen\s+tree|flood|spark|several|multiple|outage)\b",
    re.IGNORECASE,
)
_ACCESS_BLOCKED = re.compile(
    r"\b(road\s+(closed|blocked)|impassable|cannot\s+(access|reach)|can'?t\s+(access|reach)"
    r"|blocked|inaccessible|tree\s+(across|blocking)|access\s+blocked)\b",
    re.IGNORECASE,
)


def _estimate_customers(text: str) -> int:
    """Pull a customer count from the text, with rough heuristics."""
    # Explicit "<n> customers/homes/households/people".
    m = re.search(
        r"(\d[\d,]*)\s+(customers?|homes?|households?|residents?|people|buildings?)",
        text,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(1).replace(",", ""))

    # "a few hundred", "hundreds", "thousands".
    if re.search(r"thousands?", text, re.IGNORECASE):
        return 2000
    if re.search(r"hundreds?", text, re.IGNORECASE):
        return 300

    # Vague scale words.
    lower = text.lower()
    if any(w in lower for w in ("neighbourhood", "neighborhood", "subdivision", "widespread")):
        return 150
    if any(w in lower for w in ("block", "street", "several homes")):
        return 40
    if any(w in lower for w in ("home", "house", "single")):
        return 5
    return 0


def _keyword_fallback(text: str) -> ParsedReport:
    """Deterministic offline parser used when the LLM is unavailable."""
    hazards: list[str] = []
    for label, pattern in _HAZARD_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            hazards.append(label)

    if _HIGH_SEVERITY.search(text):
        severity = "high"
    elif _MEDIUM_SEVERITY.search(text) or hazards:
        severity = "medium"
    else:
        severity = "low"

    return ParsedReport(
        hazards=hazards,
        est_customers=_estimate_customers(text),
        severity_signal=severity,  # type: ignore[arg-type]
        access_blocked=bool(_ACCESS_BLOCKED.search(text)),
    )


def _llm_parse(text: str) -> ParsedReport:
    """Call the OpenAI API and validate the strict-JSON response."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    # Validate/coerce against the strict schema; raises on mismatch.
    return ParsedReport.model_validate(data)


def parse_report(text: str) -> ParsedReport:
    """Parse a field report into a validated ``ParsedReport``.

    Uses the OpenAI API when a key is configured; otherwise (or on any
    error) falls back to deterministic keyword matching.
    """
    if not text or not text.strip():
        return ParsedReport(
            hazards=[], est_customers=0, severity_signal="low", access_blocked=False
        )

    if OPENAI_API_KEY:
        try:
            return _llm_parse(text)
        except (json.JSONDecodeError, ValidationError, Exception):
            # Any API/parse failure degrades gracefully to the offline path.
            return _keyword_fallback(text)

    return _keyword_fallback(text)
