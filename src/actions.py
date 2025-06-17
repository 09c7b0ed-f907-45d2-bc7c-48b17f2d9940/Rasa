import json
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
WEBAPP_PROXY_URL, GRAPHQL_API_URL = env.require_all_env("WEBAPP_PROXY_URL", "GRAPHQL_API_URL")
gqlpc = GQLPC.GraphQLProxyClient(WEBAPP_PROXY_URL, GRAPHQL_API_URL)


# === ROUTER ===
class ActionRouteQuery(Action):
    def name(self) -> str:
        return "action_route_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        return await ActionBuildLLMQuery().run(dispatcher, tracker, domain)


class ActionBuildLLMQuery(Action):
    def name(self) -> str:
        return "action_build_llm_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        user_query = tracker.latest_message.get("text", "")
        logger.info(f"LLM builder received query: {user_query}")
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
            logger.info("Generated GraphQL query:\n%s", gql_query)

            result = gqlpc.query(gql_query, tracker.sender_id)

            if not result:
                dispatcher.utter_message(text="No results found.")
                logger.warning("No results returned from GraphQL.")
                return []

            try:
                from src.charts.chart_converter import convert_graphql_to_charts
                from src.graphql.graphql_result import MetricsQueryResponse

                logger.info("Parsing GraphQL result:\n%s", json.dumps(result, indent=2))
                parsed = MetricsQueryResponse.model_validate(result)
                logger.info("Parsed result: %s", parsed.model_dump_json(indent=2))
            except Exception as e:
                logger.error("Validation error: %s", e)
                dispatcher.utter_message(text=f"Validation error: {e}")
                traceback.print_exc()
                return []

            try:
                converted = convert_graphql_to_charts(result)
                logger.info("Converted parsed result: %s", json.dumps(converted, indent=2))
            except Exception as e:
                logger.error("Chart conversion error: %s", e)
                dispatcher.utter_message(text=f"Chart conversion error: {e}")
                traceback.print_exc()
                return []

            dispatcher.utter_message(json_message={"charts": converted})
            dispatcher.utter_message(text="Query successful. Charts generated.")
            return []

        except Exception as e:
            logger.exception("LLM query error")
            dispatcher.utter_message(text=f"Sorry, LLM interpretation failed: {e}")
            traceback.print_exc()
            return []
