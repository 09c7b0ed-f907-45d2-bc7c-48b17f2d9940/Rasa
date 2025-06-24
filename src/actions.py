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
from src.cli.cli_token_parser import parse_cli_to_metric_response
from src.graphql.graphql_result import MetricsQueryResponse
from src.instructor.models import MetricCalculatorResponse

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


class ActionBuildCLIQuery(Action):
    def name(self) -> str:
        return "action_cli_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        user_query = tracker.latest_message.get("text", "")

        try:
            # Parse CLI string into Pydantic model
            parsed: MetricCalculatorResponse = parse_cli_to_metric_response(user_query)
            logger.debug("Parsed MetricCalculatorResponse:\n%s", parsed.model_dump_json(indent=2))

            # Convert to GraphQL
            gql_query: str = ITG.Build_query_from_instructor_models(parsed)
            logger.debug("Generated GraphQL query:\n%s", gql_query)

            # Execute query
            result = gqlpc.query(gql_query, tracker.sender_id)
            if not result:
                dispatcher.utter_message(text="No results found.")
                return []
            logger.debug("GraphQL result:\n%s", result.model_dump_json(indent=2))

            # Convert to chart-friendly format
            converted = convert_graphql_to_charts(result)
            logger.debug("Converted charts:\n%s", converted.model_dump_json(indent=2))

            dispatcher.utter_message(json_message=converted.model_dump())
            dispatcher.utter_message(text="Query successful. Charts generated.")

        except Exception as e:
            dispatcher.utter_message(text=f"❌ Error processing query: {e}")
            traceback.print_exc()
            return []

        return []


class ActionBuildLLMQuery(Action):
    def name(self) -> str:
        return "action_nl_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        user_query = tracker.latest_message.get("text", "")
        logger.debug(f"LLM builder received query: {user_query}")
        if not user_query:
            dispatcher.utter_message(text="I didn't receive a query to interpret.")
            logger.warning("No user query found in tracker.")
            return []

        llm_model: str = env.require_all_env("LLM_MODEL")
        llm_api_url, openai_api_key = env.require_any_env("LLM_API_URL", "OPENAI_API_KEY")

        parser = QPC.QueryParserClient(llm_api_url, llm_model, openai_api_key)

        try:
            mcresponse = parser.parse(user_query)

            if not mcresponse or not mcresponse.FilterResponse or not mcresponse.MetricResponse:
                dispatcher.utter_message(text="Failed to parse query into logical filter and metrics request.")
                logger.warning("Parsed query returned empty logicalFilter or metricsRequest.")
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
