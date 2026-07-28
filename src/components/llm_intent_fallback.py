# pyright: reportMissingTypeStubs=false, reportMissingModuleSource=false, reportUntypedClassDecorator=false, reportUntypedBaseClass=false
"""LLM-backed intent reclassification, triggered only when Rasa's own
classifier has already given up.

Runs strictly after FallbackClassifier in the pipeline and only does
anything when FallbackClassifier actually fired (i.e. this is genuinely a
fallback, not a second opinion on every message). The LLM is asked to pick
exactly one label from the real, domain-derived intent list; any response
that isn't an exact match to that closed set is discarded and the original
nlu_fallback prediction is left untouched. That closed-set validation is
what keeps this safe against prompt injection -- the model's raw text is
never trusted or interpreted, only compared against a fixed allow-list.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Text

from rasa.engine.graph import ExecutionContext, GraphComponent
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.nlu.classifiers.fallback_classifier import is_fallback_classifier_prediction
from rasa.shared.nlu.constants import INTENT, INTENT_NAME_KEY, INTENT_RANKING_KEY, PREDICTED_CONFIDENCE_KEY
from rasa.shared.nlu.training_data.message import Message

from src.components.intent_matching import match_intent_strict
from src.components.layered_importer import OverlayImporter
from src.components.llm_client import ChatMessage, OpenAICompatibleLLMClient, build_default_client

logger = logging.getLogger(__name__)

_EXCLUDED_INTENTS = {"nlu_fallback"}

_SYSTEM_PROMPT_TEMPLATE = """You are an intent classifier. Read the user's message and reply with \
exactly one label from this list, and nothing else -- no punctuation, no explanation:

{intent_list}

If none of the labels genuinely fit, reply with: {fallback_label}"""


def _load_domain_intents() -> List[str]:
    """Reuse OverlayImporter (the same code that builds the real, locale-merged
    domain at train/serve time) rather than re-deriving the intent list from
    scratch -- this way it always reflects the live domain, no separate list
    to keep in sync."""
    try:
        domain = OverlayImporter().get_domain()
        intents = getattr(domain, "intents", None) or []
        return sorted({str(i) for i in intents if str(i) not in _EXCLUDED_INTENTS})
    except Exception:
        logger.warning("Could not load domain intents for LLM fallback; component will be a no-op", exc_info=True)
        return []


@DefaultV1Recipe.register(DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER, is_trainable=False)
class LLMIntentFallback(GraphComponent):
    """If FallbackClassifier gave up on a message, ask an LLM to pick one of
    the real intents before accepting defeat. Never runs on messages Rasa was
    already confident about."""

    def __init__(self, config: Dict[Text, Any], llm_client: Optional[OpenAICompatibleLLMClient] = None) -> None:
        self._config = config or {}
        self._enabled = bool(self._config.get("enabled", True))
        self._llm_confidence = float(self._config.get("llm_confidence", 0.5))
        self._max_tokens = int(self._config.get("max_tokens", 20))
        self._debug = bool(self._config.get("debug_logging", False))

        timeout_seconds = float(self._config.get("timeout_seconds", 8.0))
        self._client = llm_client if llm_client is not None else build_default_client(timeout_seconds)

        self._intents: List[str] = _load_domain_intents()
        if self._enabled and not self._client.enabled:
            logger.info("LLMIntentFallback: LLM client not configured, component will be a no-op")
        if self._enabled and not self._intents:
            logger.info("LLMIntentFallback: no domain intents loaded, component will be a no-op")

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> "LLMIntentFallback":
        return cls(config)

    def process(self, messages: List[Message]) -> List[Message]:  # type: ignore[override]
        if not self._enabled or not self._client.enabled or not self._intents:
            return messages

        for message in messages:
            if not is_fallback_classifier_prediction(message.data):
                continue

            text = message.get("text") or ""
            if not text.strip():
                continue

            llm_intent = self._classify(text)
            if llm_intent is None:
                if self._debug:
                    logger.info(f"LLMIntentFallback: no usable answer for {text!r}, keeping nlu_fallback")
                continue

            if self._debug:
                logger.info(f"LLMIntentFallback: reclassified {text!r} -> {llm_intent!r}")

            new_prediction = {INTENT_NAME_KEY: llm_intent, PREDICTED_CONFIDENCE_KEY: self._llm_confidence, "llm_fallback": True}
            message.data[INTENT] = new_prediction
            message.data.setdefault(INTENT_RANKING_KEY, [])
            message.data[INTENT_RANKING_KEY].insert(0, new_prediction)

        return messages

    def _classify(self, text: str) -> Optional[str]:
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            intent_list="\n".join(f"- {name}" for name in self._intents),
            fallback_label="none",
        )
        messages: List[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        raw = self._client.complete(messages, max_tokens=self._max_tokens, temperature=0.0)
        if raw is None:
            return None

        return match_intent_strict(raw, self._intents)
        return None
