import logging
from typing import Any, Dict, List

from rasa_sdk import Action, Tracker  # type: ignore
from rasa_sdk.executor import CollectingDispatcher  # type: ignore
from rasa_sdk.types import DomainDict  # type: ignore

from src.executors.langchain.pipeline import generate_analysis_plan

logger = logging.getLogger(__name__)


class ActionGenerateVisualization(Action):
    """
    Rasa action that uses the planner chain to generate visualizations and statistics.
    """

    def name(self) -> str:
        return "action_generate_visualization"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[str, Any]]:
        try:
            user_message = tracker.latest_message.get("text", "")
            user_id = tracker.sender_id
            logger.info(f"Processing visualization request: '{user_message}' for user: {user_id}")

            # Extract entities from Rasa NLU
            entities = tracker.latest_message.get("entities", [])
            extracted_entities = {entity["entity"]: entity["value"] for entity in entities}

            # Optional language override from Rasa (metadata.language or slot 'language').
            override_language = None
            try:
                meta_any = tracker.latest_message.get("metadata")
                if isinstance(meta_any, dict):
                    meta_dict: Dict[str, Any] = meta_any  # type: ignore[assignment]
                    lang_meta = meta_dict.get("language")
                    if isinstance(lang_meta, str) and lang_meta.strip():
                        override_language = lang_meta
                if override_language is None and hasattr(tracker, "get_slot"):
                    slot_lang = tracker.get_slot("language")  # type: ignore[attr-defined]
                    if isinstance(slot_lang, str) and slot_lang.strip():
                        override_language = slot_lang
            except Exception:
                pass
            if isinstance(override_language, str):
                override_language = override_language.split("-")[0].lower() or None

            plan_obj = generate_analysis_plan(
                question=user_message,
                entities=extracted_entities,
                language=override_language,
                debug=False,
            )

            # Serialize plan (Pydantic model) to JSON and return as single message
            try:
                plan_dict = plan_obj.model_dump() if hasattr(plan_obj, "model_dump") else plan_obj  # type: ignore[attr-defined]
            except Exception as ser_exc:
                plan_dict = f"Serialization error: {ser_exc}"
            dispatcher.utter_message(text=plan_dict)
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            logger.error(error_msg)
            dispatcher.utter_message(text="❌ Error generating visualization.")
            dispatcher.utter_message(text=error_msg)
        return []
