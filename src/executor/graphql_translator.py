from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from src.graphql.graphql_request import (
    DataOrigin,
    GraphQLQueryRequest,
    MetricRequest,
    TimePeriod,
)
from src.graphql.ssot_enums import MetricType
from src.langchain.planner_schema import AnalysisPlan, ChartSpec, MetricSpec


class GraphQLRequestSpec(TypedDict):
    """Normalized spec to execute a GraphQL request and map back to plan elements."""

    kpi_id: str
    query: str
    variables: Dict[str, Any]


class GraphQLTranslator:
    """Translate AnalysisPlan into one or more GraphQL query specs."""

    def __init__(self, default_provider_group_ids: Optional[List[int]] = None):
        self.default_provider_group_ids = default_provider_group_ids or [1]

    def translate(self, plan: AnalysisPlan) -> List[GraphQLRequestSpec]:
        specs: List[GraphQLRequestSpec] = []

        if not plan.charts and not plan.statistical_tests:
            return specs

        # For now: create one request per metric across all charts/tests
        metric_items: List[tuple[str, MetricSpec, Optional[ChartSpec]]] = []
        for chart in plan.charts or []:
            for m in chart.metrics:
                kpi_id = m.metric
                metric_items.append((kpi_id, m, chart))

        for kpi_id, _metric_spec, _chart in metric_items:
            request = GraphQLQueryRequest(
                metrics=[MetricRequest(metricType=MetricType[kpi_id])],
                timePeriod=TimePeriod(startDate="2020-01-01", endDate="2030-01-01"),  # TODO: derive from plan
                dataOrigin=DataOrigin(providerGroupId=self.default_provider_group_ids),
                includeGeneralStats=False,
            )
            # TODO: map filters/group_by from plan -> request.caseFilter/groupBy

            query_str = request.to_graphql_string()
            specs.append(GraphQLRequestSpec(kpi_id=kpi_id, query=query_str, variables={}))

        return specs
