import logging
from typing import Any

from rasa_sdk import Action, Tracker  # type: ignore
from rasa_sdk.executor import CollectingDispatcher  # type: ignore
from rasa_sdk.types import DomainDict  # type: ignore

import src.graphql.graphql_proxy_client as GQL_Client
import src.instructor.query_parser_client as QP_Client
from src import env

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
WEBAPP_PROXY_URL, GRAPHQL_API_URL = env.require_all_env("WEBAPP_PROXY_URL", "GRAPHQL_API_URL")
GQLPC = GQL_Client.GraphQLProxyClient(WEBAPP_PROXY_URL, GRAPHQL_API_URL)


"""def get_slot(tracker: Tracker, key: str) -> Optional[Any]:
    get_slot_fn: Callable[[str], Optional[Any]] = cast(Callable[[str], Optional[Any]], getattr(tracker, "get_slot"))
    value = get_slot_fn(key)
    logger.debug(f"Slot '{key}': {value!r}")
    return value"""


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
        """ user_query = tracker.latest_message.get("text", "").lower()
            logger.info(f"Routing query: {user_query}")
            complex_keywords = [" or ", " and ", " not ", "(", ")", "between", ">=", "<=", " excluding "]

            if any(k in user_query for k in complex_keywords):
                logger.debug("Detected complex keywords, routing to LLM builder.")
                return await ActionBuildLLMQuery().run(dispatcher, tracker, domain)
            logger.debug("No complex keywords detected, routing to structured builder.")
            return await ActionBuildStructuredQuery().run(dispatcher, tracker, domain)"""


# === STRUCTURED BUILDER ===
class ActionBuildStructuredQuery(Action):
    def name(self) -> str:
        return "action_build_structured_query"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[dict[str, Any]]:
        """try:
            filters: list[Any] = []
            logger.info("Building structured query from slots.")

            sex = get_slot(tracker, "sex")
            if sex is not None:
                logger.debug(f"Adding SexFilter for value: {sex}")
                prop = {"male": SexProperty.Male, "female": SexProperty.Female}.get(str(sex).lower(), SexProperty.Unknown)
                filters.append(SexFilter(prop))

            age_min = get_slot(tracker, "age_min")
            if age_min is not None:
                logger.debug(f"Adding AgeFilter >= {age_min}")
                filters.append(AgeFilter(Operator.GreaterOrEqual, int(age_min)))
            age_max = get_slot(tracker, "age_max")
            if age_max is not None:
                logger.debug(f"Adding AgeFilter <= {age_max}")
                filters.append(AgeFilter(Operator.LessOrEqual, int(age_max)))

            nihss_min = get_slot(tracker, "nihss_min")
            if nihss_min is not None:
                logger.debug(f"Adding NIHSSFilter >= {nihss_min}")
                filters.append(NIHSSFilter(Operator.GreaterOrEqual, int(nihss_min)))
            nihss_max = get_slot(tracker, "nihss_max")
            if nihss_max is not None:
                logger.debug(f"Adding NIHSSFilter <= {nihss_max}")
                filters.append(NIHSSFilter(Operator.LessOrEqual, int(nihss_max)))

            d_min = get_slot(tracker, "discharge_date_min")
            if d_min is not None:
                logger.debug(f"Adding DischargeDateFilter > {d_min}")
                filters.append(DischargeDateFilter(Operator.GreaterThan, d_min))
            d_max = get_slot(tracker, "discharge_date_max")
            if d_max is not None:
                logger.debug(f"Adding DischargeDateFilter < {d_max}")
                filters.append(DischargeDateFilter(Operator.LessThan, d_max))

            full_filter = AND(*filters) if filters else None
            logger.debug(f"Full filter: {full_filter}")
            metrics = [
                MetricBuilder(Metric.Age).with_distribution(120, 0, 120),
            ]
            logger.debug(f"Metrics: {metrics}")
            query = build_query(metrics, full_filter)
            logger.info(f"Built query: {query}")

            result = GQLPC.query(query, tracker.sender_id)
            logger.debug(f"GraphQL result: {result}")
            if not result:
                dispatcher.utter_message(text="No results found.")
                logger.warning("No results returned from GraphQL.")
                return []

            charts = convert_graphql_to_charts(result)
            logger.debug(f"Charts: {charts}")
            dispatcher.utter_message(json_message={"charts": charts})
            dispatcher.utter_message(text="Query successful using structured filters.")
            return []

        except Exception as e:
            logger.exception("Structured query error")
            dispatcher.utter_message(text=f"Something went wrong: {e}")"""
        return []


# === LLM BUILDER ===


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

        try:
            llm_model, _ = env.require_all_env("LLM_MODEL")
            llm_api_url, openai_api_key = env.require_any_env("LLM_API_URL", "OPENAI_API_KEY")

            parser = (
                QP_Client.QueryParserClient(
                    llm_model=llm_model,
                    llm_api_url=llm_api_url,
                )
                if llm_api_url
                else QP_Client.QueryParserClient(
                    llm_model=llm_model,
                    openai_api_key=openai_api_key,
                )
            )

            logical_filter, metrics_request = parser.parse(user_query)
            if logical_filter:
                dispatcher.utter_message(text=logical_filter.model_dump_json(indent=2))
            else:
                dispatcher.utter_message(text="No logical filter parsed from user query.")

            if metrics_request:
                dispatcher.utter_message(text=metrics_request.model_dump_json(indent=2))
            else:
                logger.warning("No metrics request parsed from user query.")
            return []

        except Exception as e:
            logger.exception("LLM query error")
            dispatcher.utter_message(text=f"Sorry, LLM interpretation failed: {e}")
            return []
