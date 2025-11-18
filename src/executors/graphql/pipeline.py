"""Plan execution pipeline: AnalysisPlan -> GraphQL -> VisualizationResponse.

This module orchestrates translation from the planning schema to GraphQL
requests, executes them against the proxy, and assembles chart DTOs for Rasa.

Initial scope: handle charts (LINE, BAR) without statistical tests.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.domain.dto.charts.union import ChartDTO
from src.domain.dto.response import VisualizationResponse
from src.domain.graphql.request import DataOrigin, TimePeriod
from src.domain.graphql.response import Metric as GqlMetric
from src.domain.graphql.response import MetricsQueryResponse
from src.domain.langchain.schema import AnalysisPlan, ChartSpec
from src.executors.graphql.client import GraphQLProxyClient
from src.translators.gpl_to.chart_dto import to_chart_dto
from src.translators.plan_to.gql_request import BuiltRequest, ExecutionContext, build_requests_from_plan
from src.util import env

logger = logging.getLogger(__name__)


@dataclass
class PlanExecutionContext:
    time_period_start: str
    time_period_end: str
    provider_group_ids: List[int]


def _env_graphql_client() -> GraphQLProxyClient:
    proxy_url, api_url = env.require_all_env("GRAPHQL_PROXY_URL", "GRAPHQL_API_URL")  # type: ignore[assignment]
    return GraphQLProxyClient(proxy_url=proxy_url, graphql_url=api_url)


def _collect_chart_alias_map(
    built_requests: List[BuiltRequest],
    gql_responses: List[Tuple[BuiltRequest, Optional[MetricsQueryResponse]]],
) -> Dict[int, Dict[str, Tuple[str, GqlMetric]]]:
    """Return mapping: chart_index -> { alias: (metric_code, GqlMetric) }"""

    by_chart: Dict[int, Dict[str, Tuple[str, GqlMetric]]] = defaultdict(dict)
    for br, resp in gql_responses:
        if not resp or not resp.data or not resp.data.get_metrics or not resp.data.get_metrics.metrics:
            continue
        metrics_map = resp.data.get_metrics.metrics
        # Expect single metric per request
        for alias, metric in metrics_map.items():
            # Recover metric code from request alias (request stores it on the MetricRequest)
            metric_req = br.request.metrics[0]
            metric_code = metric_req.metric_type.value  # dynamic enum
            by_chart[br.chart_index][alias] = (metric_code, metric)
    return by_chart


def execute_plan_to_visualization(
    plan: AnalysisPlan,
    session_token: str,
    ctx: PlanExecutionContext,
) -> VisualizationResponse:
    """Execute a plan end-to-end and return VisualizationResponse.

    - Translates plan to GraphQL requests
    - Executes via proxy client
    - Converts results into chart DTOs
    """

    # Build GraphQL execution context
    gql_ctx = ExecutionContext(
        time_period=TimePeriod(startDate=ctx.time_period_start, endDate=ctx.time_period_end),
        data_origin=DataOrigin(providerGroupId=ctx.provider_group_ids),
    )

    built: List[BuiltRequest] = build_requests_from_plan(plan, gql_ctx)
    logger.info("[execute_plan_to_visualization] Built %d GraphQL request(s) for %d chart(s)", len(built), len(plan.charts or []))
    try:
        for idx, br in enumerate(built):
            # Build a string summary to avoid typing issues in logs
            parts: List[str] = []
            for m in br.request.metrics:
                alias = getattr(m, "alias", None)
                s = getattr(m, "include_stats", False)
                d = getattr(m, "include_distribution", False)
                has_opts = getattr(m, "distribution_options", None) is not None
                has_bounds = getattr(m, "metric_options", None) is not None and getattr(getattr(m, "metric_options", None), "lower_boundary", None) is not None and getattr(getattr(m, "metric_options", None), "upper_boundary", None) is not None
                parts.append(f"alias={alias} stats={s} dist={d} opts={has_opts} bounds={has_bounds}")
            logger.debug("[execute_plan_to_visualization] Request %d metric flags: %s", idx, "; ".join(parts))
    except Exception:
        pass

    client = _env_graphql_client()

    # Execute all requests (sequential for simplicity)
    results: List[Tuple[BuiltRequest, Optional[MetricsQueryResponse]]] = []
    for br in built:
        query_str = br.request.to_graphql_string()
        logger.debug("[execute_plan_to_visualization] Executing GraphQL query: %s", query_str)
        resp = client.query(query_str, session_token=session_token)
        results.append((br, resp))
    none_responses = sum(1 for _, r in results if r is None)
    if none_responses:
        logger.warning("[execute_plan_to_visualization] %d/%d GraphQL response(s) were None (HTTP error or validation failure)", none_responses, len(results))
    # Log GraphQL errors when present
    for _, r in results:
        try:
            if r is not None and getattr(r, "errors", None):
                logger.warning("[execute_plan_to_visualization] GraphQL errors: %s", r.errors)
        except Exception:
            pass

    # Collect results per chart
    chart_alias_map = _collect_chart_alias_map(built, results)
    try:
        for ci, alias_map in chart_alias_map.items():
            logger.info("[execute_plan_to_visualization] Chart %d returned %d alias metric(s): %s", ci, len(alias_map), list(alias_map.keys()))
    except Exception:
        pass

    # Assemble ChartDTOs
    chart_dtos: List[ChartDTO] = []
    charts: List[ChartSpec] = plan.charts or []
    for idx, chart in enumerate(charts):
        alias_to_metric = chart_alias_map.get(idx, {})
        if not alias_to_metric:
            logger.warning("[execute_plan_to_visualization] Chart index %d produced no metrics (empty alias map)", idx)
        dto = to_chart_dto(chart, alias_to_metric)
        if dto is not None:
            chart_dtos.append(dto)

    return VisualizationResponse(charts=chart_dtos, stats=[], timestamp=datetime.now(timezone.utc))
