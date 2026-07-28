"""Pure, rasa-independent helpers for validating LLM output against a closed
set of real intents. Kept separate from llm_intent_fallback.py so it's
testable without importing rasa at all.
"""
from __future__ import annotations

from typing import List, Optional


def match_intent_strict(raw_response: str, valid_intents: List[str]) -> Optional[str]:
    """Strict allow-list match only -- the model's raw text is never trusted
    beyond "does it exactly equal one of our real intents". The *entire*
    stripped response must reduce to exactly one intent name; anything with
    extra content (even on a second line) is discarded, not interpreted.
    This is what keeps the component safe against prompt injection: there's
    no code path that acts on the model's text as anything other than a
    single closed-set label lookup, and no way to smuggle extra content
    past the check by putting it after the label."""
    if not raw_response:
        return None
    if len(raw_response.strip().splitlines()) > 1:
        return None
    candidate = raw_response.strip().strip(".\"'").lower()
    for intent in valid_intents:
        if intent.lower() == candidate:
            return intent
    return None
