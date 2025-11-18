import json
import logging
from typing import Any, Dict, List

from rasa_sdk import Action, Tracker  # type: ignore
from rasa_sdk.executor import CollectingDispatcher  # type: ignore
from rasa_sdk.types import DomainDict  # type: ignore

from src.domain.langchain.schema import AnalysisPlan
from src.executors.langchain.pipeline import generate_analysis_plan
from src.executors.plan_executor import execute_plan
from src.shared.ssot_loader import validate_metric_metadata_complete

logger = logging.getLogger(__name__)

# Emit SSOT completeness warnings once on module import
try:
    validate_metric_metadata_complete(logger)
except Exception as _e:
    logger.debug("SSOT validation skipped due to: %s", _e)


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
            session_token = tracker.sender_id
            logger.info(f"Processing visualization request: '{user_message}' for user: {session_token}")

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

            plan_obj: AnalysisPlan = generate_analysis_plan(
                question=user_message,
                entities=extracted_entities,
                language=override_language,
                max_retries=2,
                debug=False,
            )

            visualization = execute_plan(plan_obj, session_token=session_token)
            dispatcher.utter_message(json_message=json.loads(visualization.model_dump_json()))
            dispatcher.utter_message(text="Hopefully that did something lol.")
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            logger.error(error_msg)
            dispatcher.utter_message(text="❌ Error generating visualization.")
            dispatcher.utter_message(text=error_msg)
        return []
