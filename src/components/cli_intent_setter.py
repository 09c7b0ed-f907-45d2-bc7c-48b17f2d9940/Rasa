# pyright: reportUntypedClassDecorator=false, reportUntypedBaseClass=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any, Dict, List, Text, cast

from rasa.engine.graph import GraphComponent  # type: ignore
from rasa.engine.recipes.default_recipe import DefaultV1Recipe  # type: ignore
from rasa.shared.nlu.training_data.message import Message  # type: ignore


@DefaultV1Recipe.register(DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER, is_trainable=False)
class CLIIntentSetter(GraphComponent):
    """Force intent when text starts with a configured CLI prefix (e.g., '/cli')."""

    def __init__(self, config: Dict[Text, Any]) -> None:
        defaults: Dict[Text, Any] = {"prefixes": ["/cli"], "intent_name": "cli_command"}
        merged: Dict[Text, Any] = dict(defaults)
        if config:
            merged.update(config)
        self._config = merged

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: Any,
        resource: Any,
        execution_context: Any,
    ) -> "CLIIntentSetter":
        return cls(config)

    def process(self, messages: List[Message]) -> List[Message]:  # type: ignore[override]
        prefixes_any: Any = self._config.get("prefixes", ["/cli"])
        prefixes: List[str] = []
        if isinstance(prefixes_any, list):
            prefixes_list: List[Any] = cast(List[Any], prefixes_any)
            for item in prefixes_list:
                prefixes.append(str(item))
        else:
            prefixes = [str(prefixes_any)]

        intent_name_any: Any = self._config.get("intent_name", "cli_command")
        intent_name: str = intent_name_any if isinstance(intent_name_any, str) else str(intent_name_any)

        for message_any in cast(List[Any], messages):
            text: str = str(message_any.get("text") or "").strip()
            for prefix in prefixes:
                if text.startswith(prefix):
                    trimmed: str = text[len(prefix) :].strip()
                    message_any.set("intent", {"name": intent_name, "confidence": 1.0}, add_to_output=True)
                    message_any.set(
                        "intent_ranking",
                        [{"name": intent_name, "confidence": 1.0}],
                        add_to_output=True,
                    )
                    md_any: Any = message_any.get("metadata")
                    md: Dict[str, Any] = dict(cast(Dict[str, Any], md_any)) if isinstance(md_any, dict) else {}
                    md["cli_command_text"] = trimmed
                    message_any.set("metadata", md, add_to_output=True)
                    break
        return messages
