"""Pure, rasa-independent helpers for the LLM intent fallback prompt/response
handling. Kept separate from llm_intent_fallback.py so all of it is testable
without importing rasa at all.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

_PLACEHOLDER_PREFIX = "[placeholder]"


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


def bucket_examples(raw_examples: List[Tuple[str, str]], examples_per_intent: int) -> Dict[str, List[str]]:
    """Group (intent, text) pairs into an intent -> [examples] map, filtering
    out hand-authored placeholder text ("[placeholder] ...", used by base-
    layer NLU files that a locale overlay hasn't translated) and duplicates,
    capped at `examples_per_intent` per intent. An intent with no real
    examples simply gets an empty list -- never placeholder text."""
    if examples_per_intent <= 0:
        return {}

    by_intent: Dict[str, List[str]] = OrderedDict()
    for intent, text in raw_examples:
        text = (text or "").strip()
        if not text or text.startswith(_PLACEHOLDER_PREFIX):
            continue
        bucket = by_intent.setdefault(intent, [])
        if text in bucket or len(bucket) >= examples_per_intent:
            continue
        bucket.append(text)

    return by_intent


def build_intent_list_block(intents: List[str], examples: Dict[str, List[str]]) -> str:
    """Render the intent list (with example utterances where available) for
    the classifier prompt."""
    lines: List[str] = []
    for name in intents:
        lines.append(f"- {name}")
        for example_text in examples.get(name, []):
            lines.append(f'  e.g. "{example_text}"')
    return "\n".join(lines)
