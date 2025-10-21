from typing import Any, Dict, List, Text, cast

from rasa.engine.graph import ExecutionContext, GraphComponent  # type: ignore
from rasa.engine.recipes.default_recipe import DefaultV1Recipe  # type: ignore
from rasa.engine.storage.resource import Resource  # type: ignore
from rasa.engine.storage.storage import ModelStorage  # type: ignore
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
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
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

        for message in messages:
            text: str = str(message.get("text") or "").strip()
            for prefix in prefixes:
                if text.startswith(prefix):
                    trimmed: str = text[len(prefix) :].strip()
                    message.set("intent", {"name": intent_name, "confidence": 1.0}, add_to_output=True)
                    message.set(
                        "intent_ranking",
                        [{"name": intent_name, "confidence": 1.0}],
                        add_to_output=True,
                    )
                    md_any: Any = message.get("metadata")
                    md: Dict[str, Any] = dict(cast(Dict[str, Any], md_any)) if isinstance(md_any, dict) else {}
                    md["cli_command_text"] = trimmed
                    message.set("metadata", md, add_to_output=True)
                    break
        return messages
