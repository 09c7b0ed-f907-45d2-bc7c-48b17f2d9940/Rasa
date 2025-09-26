from __future__ import annotations

import logging
from typing import Optional

from src.analytics.statistics import run_basic_stats
from src.executor.chart_builder import build_basic_bar_charts
from src.executor.compute import compute_metrics, to_tables
from src.executor.errors import GraphQLExecutionError, PlanValidationError
from src.executor.graphql_runner import GraphQLRunner
from src.executor.graphql_translator import GraphQLTranslator
from src.executor.types import AnalysisResult, ExecutionConfig
from src.executor.utils import timer
from src.langchain.planner_schema import AnalysisPlan

logger = logging.getLogger(__name__)


class PlanExecutor:
    def __init__(self, runner: GraphQLRunner, translator: Optional[GraphQLTranslator] = None):
        self.runner = runner
        self.translator = translator or GraphQLTranslator()

    def execute(self, plan: AnalysisPlan, *, session_token: str, config: Optional[ExecutionConfig] = None) -> AnalysisResult:
        _cfg = config or ExecutionConfig()
        result = AnalysisResult(plan=plan)

        # 1) validate
        if not plan.charts and not plan.statistical_tests:
            raise PlanValidationError("Plan has neither charts nor statistical_tests")

        # 2) translate to GraphQL
        with timer(result.report.timings, "translate"):
            specs = self.translator.translate(plan)
            result.report.graphql_queries = [{"kpi_id": s["kpi_id"], "query": s["query"], "variables": s.get("variables", {})} for s in specs]

        if not specs:
            raise PlanValidationError("Translator produced no GraphQL requests")

        # 3) run GraphQL
        with timer(result.report.timings, "graphql"):
            responses = self.runner.run_many(specs, session_token=session_token)
            if not responses:
                raise GraphQLExecutionError("No GraphQL responses returned")

        # 4) to tables
        with timer(result.report.timings, "to_tables"):
            tables = to_tables(responses)
            result.tables = tables

        # 5) compute metrics
        with timer(result.report.timings, "compute_metrics"):
            metrics = compute_metrics(tables)
            result.metrics = metrics

        # 5b) optional statistical tests
        if plan.statistical_tests:
            with timer(result.report.timings, "run_stats"):
                result.statistical_tests = run_basic_stats(tables)

        # 6) build charts (placeholder)
        with timer(result.report.timings, "build_charts"):
            charts = build_basic_bar_charts(tables)
            result.charts = charts

        return result
