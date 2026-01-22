import json
import logging
from typing import Any, Dict, List, cast

from src.actions.long_action.long_action import LongAction
from src.actions.long_action.long_action_context import LongActionContext
from src.domain.langchain import schema as lang_schema
from src.executors import plan_executor
from src.executors.langchain import pipeline as lang_pipeline
from src.executors.simple_planner import HeuristicVisualizationPlanner
from src.shared import ssot_loader
from src.util.hospital_statistics import HospitalStatistics

logger = logging.getLogger(__name__)

try:
    ssot_loader.validate_metric_metadata_complete(logger)
except Exception as _e:
    logger.debug("SSOT validation skipped due to: %s", _e)


class ActionGenerateVisualization(LongAction):
    """Long action that uses the planner chain to generate visualizations and statistics.

    In callback mode this streams messages via the long-action callback URL;
    otherwise it behaves like a normal synchronous action and uses the
    dispatcher directly.
    """

    def name(self) -> str:
        return "action_generate_visualization"

    async def work(self, ctx: LongActionContext) -> Any:
        try:
            user_message = ctx.text
            session_token = ctx.sender_id
            logger.info("Processing visualization request: '%s'", user_message)

            latest_meta = ctx.metadata

            latest_any = ctx.tracker_snapshot.get("latest_message")
            entities_list: List[Dict[str, Any]] = []
            if isinstance(latest_any, dict):
                latest_msg = cast(Dict[str, Any], latest_any)
                ents_any = latest_msg.get("entities", [])
                if isinstance(ents_any, list):
                    ents_list = cast(List[Any], ents_any)
                    for e_any in ents_list:
                        if isinstance(e_any, dict):
                            entities_list.append(cast(Dict[str, Any], e_any))
            extracted_entities: Dict[str, Any] = {ent["entity"]: ent["value"] for ent in entities_list if isinstance(ent.get("entity"), str) and "value" in ent}

            override_language: Any = None
            try:
                lang_meta = latest_meta.get("language")
                if isinstance(lang_meta, str) and lang_meta.strip():
                    override_language = lang_meta
                if override_language is None:
                    slot_lang = ctx.slots.get("language")
                    if isinstance(slot_lang, str) and slot_lang.strip():
                        override_language = slot_lang
            except Exception:
                pass
            if isinstance(override_language, str):
                override_language = override_language.split("-")[0].lower() or None

            def progress(msg: str) -> None:
                ctx.say(progress=msg)

            heuristic_plan = HeuristicVisualizationPlanner.try_plan(
                question=user_message,
                entities=extracted_entities,
                language=override_language,
            )

            if heuristic_plan is not None:
                progress("Using simple heuristic plan (no LLM needed)")
                plan_obj: lang_schema.AnalysisPlan = heuristic_plan
            else:
                progress("Calling planner LLM to build a plan")
                plan_obj = lang_pipeline.generate_analysis_plan(
                    question=user_message,
                    entities=extracted_entities,
                    language=override_language,
                    max_retries=2,
                    debug=False,
                    progress_cb=progress,
                )

            visualization = await plan_executor.execute_plan_async(
                plan_obj,
                session_token=session_token,
                max_concurrency=4,
                progress_cb=progress,
            )

            ctx.say(json_message=json.loads(visualization.model_dump_json()))
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            logger.error(error_msg)
            ctx.say(text="❌ Error generating visualization.")
            ctx.say(text=error_msg)
        finally:
            ctx.say(text="✅ Visualization generation complete.")
            ctx.done()
        return None


class ActionCompareHospitals(LongAction):
    """Long action that compares door-to-needle times between two hospitals.

    Performs statistical analysis using Shapiro-Wilk normality tests and
    appropriate comparison tests (t-test or Wilcoxon rank-sum test).
    Currently uses synthetic data for demonstration purposes.
    """

    def name(self) -> str:
        return "action_compare_hospitals"

    async def work(self, ctx: LongActionContext) -> Any:
        try:
            user_message = ctx.text
            logger.info("Processing hospital comparison request: '%s'", user_message)

            def progress(msg: str) -> None:
                ctx.say(progress=msg)

            progress("🏥 Initializing hospital comparison analysis...")
            
            # Initialize the statistical analyzer
            stats = HospitalStatistics(alpha=0.05)
            
            progress("📊 Generating synthetic hospital datasets...")
            
            # Generate synthetic data for two hospitals
            # In production, this would be replaced with real data from a database
            result = stats.run_analysis(n_rows=50, random_state=42)
            
            progress("🔬 Performing statistical tests...")
            
            # Get the formatted summary
            summary = result.get_summary()
            
            # Send the complete analysis as text
            ctx.say(text=summary)
            
            # Also send structured data for potential frontend rendering
            result_dict = result.to_dict()
            
            # Create a user-friendly interpretation message
            if result.is_significant():
                interpretation = (
                    f"✅ **Significant Difference Detected**\n\n"
                    f"The statistical analysis shows a **SIGNIFICANT difference** "
                    f"between the two hospitals (p-value = {result.test_result.p_value:.4f}).\n\n"
                    f"Test used: **{result.test_type.upper()}**\n"
                    f"Hospital 1: {result.expanded_size_1} observations\n"
                    f"Hospital 2: {result.expanded_size_2} observations\n\n"
                    f"This suggests that the door-to-needle times are statistically different between the two hospitals."
                )
            else:
                interpretation = (
                    f"ℹ️ **No Significant Difference**\n\n"
                    f"The statistical analysis shows **NO significant difference** "
                    f"between the two hospitals (p-value = {result.test_result.p_value:.4f}).\n\n"
                    f"Test used: **{result.test_type.upper()}**\n"
                    f"Hospital 1: {result.expanded_size_1} observations\n"
                    f"Hospital 2: {result.expanded_size_2} observations\n\n"
                    f"This suggests that the door-to-needle times are similar between the two hospitals."
                )
            
            ctx.say(text=interpretation)
            
            # Send structured data for APIs/frontend
            ctx.say(json_message=result_dict)
            
        except Exception as e:
            error_msg = f"Error comparing hospitals: {str(e)}"
            logger.error(error_msg)
            ctx.say(text="❌ Error performing hospital comparison analysis.")
            ctx.say(text=error_msg)
        finally:
            ctx.say(text="✅ Hospital comparison complete.")
            ctx.done()
        return None
