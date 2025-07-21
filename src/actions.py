import logging
import traceback
from typing import Any

from rasa_sdk import Action, Tracker  # type: ignore
from rasa_sdk.executor import CollectingDispatcher  # type: ignore
from rasa_sdk.types import DomainDict  # type: ignore

import src.graphql.graphql_proxy_client as GQLPC
import src.graphql.instructor_to_graphql as ITG
import src.instructor.query_parser_client as QPC
from src import env
from src.charts.chart_converter import convert_graphql_to_charts
from src.EntityToInstructorTranslator import EntityToInstructorTranslator
from src.graphql.graphql_result import MetricsQueryResponse

LOG_LEVEL = env.require_any_env("LOGLEVEL") or "INFO"

# Remove all handlers associated with the root logger
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add a StreamHandler with the correct level and formatter
handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    GREY = "\033[90m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Color levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        # Color asctime and name grey
        record.name = f"{self.GREY}{record.name}{self.RESET}"
        # Add clickable file:line link (works in some terminals/IDEs)
        record.link = f"\033[34m{record.pathname}:{record.lineno}\033[0m"
        return super().format(record)


formatter = ColorFormatter("%(asctime)s %(levelname)-16s %(name)-32s [%(link)s] \n%(message)s\n")
handler.setFormatter(formatter)
root_logger.addHandler(handler)
root_logger.setLevel(LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

logger.info(f"Logger level is: {logging.getLevelName(logger.level)}")

WEBAPP_PROXY_URL, GRAPHQL_API_URL = env.require_all_env("WEBAPP_PROXY_URL", "GRAPHQL_API_URL")
gqlpc = GQLPC.GraphQLProxyClient(WEBAPP_PROXY_URL, GRAPHQL_API_URL)


llm_model: str = env.require_all_env("LLM_MODEL")
llm_api_url, openai_api_key = env.require_any_env("LLM_API_URL", "OPENAI_API_KEY")
llm_parser = QPC.QueryParserClient(llm_api_url, llm_model, openai_api_key)


class ActionGenerateVisualization(Action):
    def name(self) -> str:
        return "action_generate_visualization"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        entities = tracker.latest_message.get("entities", [])
        user_message = tracker.latest_message["text"]

        # Get Rasa's confidence for this intent
        intent_ranking = tracker.latest_message.get("intent_ranking", [])
        rasa_confidence = intent_ranking[0].get("confidence", 1.0) if intent_ranking else 1.0

        translator = EntityToInstructorTranslator()

        # Check if query is too complex for rule-based handling
        complexity_check = translator.is_too_complex_for_rules(entities, user_message, rasa_confidence)

        if complexity_check.is_too_complex:
            logger.info(f"Query too complex for rules: {complexity_check.reason}. Using LLM fallback.")
            try:
                mcresponse = llm_parser.parse(user_message)
            except Exception as e:
                logger.error(f"LLM parsing failed: {e}")
                dispatcher.utter_message(text="Sorry, I couldn't understand your query. Please try rephrasing it.")
                return []
        else:
            logger.info(f"Using rule-based parsing. Confidence: {complexity_check.confidence:.2f}")
            try:
                mcresponse = translator.translate(entities, user_message)
            except Exception as e:
                logger.warning(f"Rule-based parsing failed: {e}. Falling back to LLM.")
                try:
                    mcresponse = llm_parser.parse(user_message)
                except Exception as llm_error:
                    logger.error(f"LLM fallback also failed: {llm_error}")
                    dispatcher.utter_message(text="Sorry, I couldn't understand your query. Please try rephrasing it.")
                    return []

        # Rest of your existing code unchanged
        if not mcresponse:
            dispatcher.utter_message(text="Failed to parse query.")
            logger.warning("Parsed query returned None.")
            return []

        # Check if we have metrics (required) - filters are optional
        if not mcresponse.MetricResponse or not mcresponse.MetricResponse.metricsCollection:
            dispatcher.utter_message(text="No metrics specified in query. Please specify what data you want to analyze.")
            logger.warning("No metrics found in parsed query.")
            return []

        gql_query: str = ITG.Build_query_from_instructor_models(mcresponse)
        # logger.debug("Generated GraphQL query:\n%s", gql_query)

        result = gqlpc.query(gql_query, tracker.sender_id)

        if not result:
            dispatcher.utter_message(text="No results found.")
            logger.warning("No results returned from GraphQL.")
            return []

        try:
            # logger.debug("Parsing GraphQL result:\n%s", result.model_dump_json(indent=2))
            parsed = MetricsQueryResponse.model_validate(result)
            # logger.debug("Parsed result: %s", parsed.model_dump_json(indent=2))
        except Exception as e:
            logger.error("Validation error: %s", e)
            dispatcher.utter_message(text=f"Validation error: {e}")
            traceback.print_exc()
            return []

        try:
            converted = convert_graphql_to_charts(result)
            # logger.debug("Converted parsed result: %s", converted.model_dump_json(indent=2))
        except Exception as e:
            logger.error("Chart conversion error: %s", e)
            dispatcher.utter_message(text=f"Chart conversion error: {e}")
            traceback.print_exc()
            return []

        dispatcher.utter_message(json_message=converted.model_dump())
        dispatcher.utter_message(text="Query successful. Charts generated.")
        return []


class ActionBuildLLMQuery(Action):
    def name(self) -> str:
        return "action_build_llm_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        # This action now just forces LLM usage (useful for testing or when Rasa completely fails)
        user_query = tracker.latest_message.get("text", "")
        logger.debug(f"LLM builder received query: {user_query}")

        if not user_query:
            dispatcher.utter_message(text="I didn't receive a query to interpret.")
            logger.warning("No user query found in tracker.")
            return []

        logger.info("Forcing LLM parsing (bypassing rule-based logic)")

        try:
            mcresponse = llm_parser.parse(user_query)
            logger.debug(f"Parsed response: {mcresponse}")

            # Rest of processing same as ActionGenerateVisualization
            if not mcresponse:
                dispatcher.utter_message(text="Failed to parse query.")
                logger.warning("Parsed query returned None.")
                return []

            if not mcresponse.MetricResponse or not mcresponse.MetricResponse.metricsCollection:
                dispatcher.utter_message(text="No metrics specified in query. Please specify what data you want to analyze.")
                logger.warning("No metrics found in parsed query.")
                return []

            gql_query: str = ITG.Build_query_from_instructor_models(mcresponse)
            logger.debug("Generated GraphQL query:\n%s", gql_query)

            result = gqlpc.query(gql_query, tracker.sender_id)

            if not result:
                dispatcher.utter_message(text="No results found.")
                logger.warning("No results returned from GraphQL.")
                return []

            try:
                logger.debug("Parsing GraphQL result:\n%s", result.model_dump_json(indent=2))
                parsed = MetricsQueryResponse.model_validate(result)
                logger.debug("Parsed result: %s", parsed.model_dump_json(indent=2))
            except Exception as e:
                logger.error("Validation error: %s", e)
                dispatcher.utter_message(text=f"Validation error: {e}")
                traceback.print_exc()
                return []

            try:
                converted = convert_graphql_to_charts(result)
                logger.debug("Converted parsed result: %s", converted.model_dump_json(indent=2))
            except Exception as e:
                logger.error("Chart conversion error: %s", e)
                dispatcher.utter_message(text=f"Chart conversion error: {e}")
                traceback.print_exc()
                return []

            dispatcher.utter_message(json_message=converted.model_dump())
            dispatcher.utter_message(text="Query successful. Charts generated.")
            return []

        except Exception as e:
            logger.exception("LLM query error")
            dispatcher.utter_message(text=f"Sorry, LLM interpretation failed: {e}")
            traceback.print_exc()
            return []
