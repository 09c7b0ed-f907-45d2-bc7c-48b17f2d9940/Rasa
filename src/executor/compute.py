from __future__ import annotations

from typing import Any, Dict, List

from src.executor.types import MetricResult, TableResult
from src.graphql.graphql_response import MetricsQueryResponse


def to_tables(responses: Dict[str, MetricsQueryResponse]) -> List[TableResult]:
    """Convert GraphQL responses into normalized tabular results.

    This is a minimal placeholder that extracts case counts only.
    """
    tables: List[TableResult] = []
    for kpi_id, resp in responses.items():
        # Navigate to metrics data if present
        data = resp.data.get_metrics
        rows: List[list[Any]] = []
        columns = ["bucket", "case_count"]

        if data.metrics and f"metric_{kpi_id}" in data.metrics:
            metric = data.metrics[f"metric_{kpi_id}"]
            for group in metric.kpi_group:
                count = sum(group.kpi1.case_count)
                bucket = group.grouped_by.group_item_name if group.grouped_by else "ALL"
                rows.append([bucket, count])

        tables.append(TableResult(kpi_id=kpi_id, columns=columns, rows=rows, metadata={}))
    return tables


def compute_metrics(tables: List[TableResult]) -> List[MetricResult]:
    """Compute simple derived metrics over the tables.

    Placeholder: pass-through with totals.
    """
    results: List[MetricResult] = []
    for t in tables:
        total = sum(int(r[1]) for r in t.rows)
        results.append(MetricResult(kpi_id=t.kpi_id, values={"total": total}, metadata={}))
    return results
