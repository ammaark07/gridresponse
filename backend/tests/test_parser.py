"""Tests for the LLM report parser fallback (app/llm/parser.py).

These exercise _keyword_fallback() directly so they run fully offline with
no API key required. They also exercise the public parse_report() entry
point with no key set (which must degrade gracefully to the fallback).
"""
from __future__ import annotations

import pytest

from app.llm.parser import _keyword_fallback, parse_report
from app.schemas import ParsedReport

# ---------------------------------------------------------------------------
# _keyword_fallback — deterministic, no network dependency
# ---------------------------------------------------------------------------


def test_fallback_returns_parsed_report_schema():
    result = _keyword_fallback("power line down on Oak St")
    assert isinstance(result, ParsedReport)


def test_fallback_detects_downed_line_hazard():
    result = _keyword_fallback("There is a downed power line in the intersection.")
    assert "downed power line" in result.hazards


def test_fallback_detects_fallen_tree():
    result = _keyword_fallback("A large tree has fallen across the road.")
    assert "fallen tree" in result.hazards


def test_fallback_detects_fire():
    result = _keyword_fallback("Transformer sparking and there is a fire nearby.")
    assert "fire" in result.hazards


def test_fallback_access_blocked_true():
    result = _keyword_fallback("Road is closed, crews cannot access the site.")
    assert result.access_blocked is True


def test_fallback_access_blocked_false():
    result = _keyword_fallback("Minor outage on Elm Street, no access issues.")
    assert result.access_blocked is False


def test_fallback_customer_count_explicit():
    result = _keyword_fallback("Approximately 350 customers are without power.")
    assert result.est_customers == 350


def test_fallback_customer_count_hundreds_heuristic():
    result = _keyword_fallback("Hundreds of residents affected by the storm.")
    assert result.est_customers > 0


def test_fallback_severity_high_on_fire():
    result = _keyword_fallback("Major fire at substation, emergency crews on scene.")
    assert result.severity_signal == "high"


def test_fallback_severity_medium_on_outage():
    result = _keyword_fallback("Downed line causing outage on several blocks.")
    assert result.severity_signal in {"medium", "high"}


def test_fallback_severity_low_on_minimal_report():
    result = _keyword_fallback("Lights flickering at one address, no visible damage.")
    assert result.severity_signal == "low"


def test_fallback_empty_text_returns_defaults():
    result = _keyword_fallback("")
    assert result.hazards == []
    assert result.est_customers == 0
    assert result.severity_signal == "low"
    assert result.access_blocked is False


# ---------------------------------------------------------------------------
# parse_report() — public entry point without an API key (offline path)
# ---------------------------------------------------------------------------


def test_parse_report_no_key_uses_fallback(monkeypatch):
    """parse_report() must not raise when OPENAI_API_KEY is empty."""
    monkeypatch.setattr("app.llm.parser.OPENAI_API_KEY", "")
    result = parse_report("Tree on the wire, about 80 customers affected.")
    assert isinstance(result, ParsedReport)
    assert result.est_customers == 80


def test_parse_report_empty_string_returns_safe_defaults(monkeypatch):
    monkeypatch.setattr("app.llm.parser.OPENAI_API_KEY", "")
    result = parse_report("")
    assert result.hazards == []
    assert result.severity_signal == "low"


@pytest.mark.parametrize(
    "text,expected_hazard",
    [
        ("flooding on the road near the substation", "flooding"),
        ("gas leak reported two blocks from the pole", "gas leak"),
        ("transformer damaged by fallen debris", "damaged transformer"),
    ],
)
def test_parse_report_parametrized_hazards(
    monkeypatch, text: str, expected_hazard: str
):
    monkeypatch.setattr("app.llm.parser.OPENAI_API_KEY", "")
    result = parse_report(text)
    assert expected_hazard in result.hazards
