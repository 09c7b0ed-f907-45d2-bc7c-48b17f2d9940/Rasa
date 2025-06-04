import logging
from typing import Any

from chart_converter import convert_graphql_to_charts
from pydantic import ValidationError
from rasa_sdk import Action, Tracker  # type: ignore
from rasa_sdk.executor import CollectingDispatcher  # type: ignore
from rasa_sdk.types import DomainDict  # type: ignore

from env import require_env
from graphql_builder import (
    AND,
    Group,
    Metric,
    MetricBuilder,
    SexFilter,
    SexProperty,
    build_query,
)
from graphql_proxy_client import GraphQLProxyClient
from models.graphql_result import Welcome

logger = logging.getLogger(__name__)

WEBAPP_PROXY_URL, GRAPHQL_API_URL = require_env("WEBAPP_PROXY_URL", "GRAPHQL_API_URL")

GQLPC = GraphQLProxyClient(WEBAPP_PROXY_URL, GRAPHQL_API_URL)


class ActionTestAPIs(Action):
    def name(self) -> str:
        return "action_test_apis"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        # Define filters
        filters = AND(
            SexFilter(SexProperty.Male),
        )

        # Define metrics to query
        metrics = [
            MetricBuilder(Metric.Dtn).with_distribution(bin_count=24, lower=0, upper=120).with_stats(),
            MetricBuilder(Metric.Age).with_distribution(bin_count=20, lower=0, upper=100),
            MetricBuilder(Metric.Dti).with_stats(),
        ]

        # Build and execute query
        query = build_query(metrics, filters, groupBy=Group.FirstContactPlace, generalStats=True)
        result = GQLPC.query(query, tracker.sender_id)

        if not result:
            dispatcher.utter_message(text="Failed to query GraphQL API.")
            logger.error("Query returned no data.")
            return []

        try:
            parsed = Welcome.model_validate(result)
            logger.info("Parsed result: %s", parsed)
        except ValidationError as e:
            logger.error("Validation error: %s", e)
            dispatcher.utter_message(text=f"Validation error: {e}")
            return []

        try:
            converted = convert_graphql_to_charts(result)
            logger.info("Converted parsed result: %s", converted)
        except ValidationError as e:
            logger.error("Validation error: %s", e)
            dispatcher.utter_message(text=f"Validation error: {e}")
            return []

        dispatcher.utter_message(json_message={"charts": converted})
        dispatcher.utter_message(text="GraphQL API query successful. Charts generated.")

        return []


class ActionGetDTN(Action):
    def name(self) -> str:
        return "action_get_dtn"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        result = GQLPC.query(build_query([MetricBuilder(Metric.Dtn).with_stats()]), tracker.sender_id)

        if result:
            dispatcher.utter_message(text="GraphQL API query successful.")
            dispatcher.utter_message(json_message=result)
            logger.info(f"GraphQL API result: {result}")
        else:
            dispatcher.utter_message(text="Failed to query GraphQL API.")
            logger.error("Query returned no data.")

        return []
