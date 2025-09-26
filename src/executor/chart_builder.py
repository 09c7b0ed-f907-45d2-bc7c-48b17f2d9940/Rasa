from __future__ import annotations

from typing import List

from src.chart.models import BarChart, ChartAxis, ChartMetadata, ChartPoint, ChartSeries
from src.executor.types import ChartResult, TableResult


def build_basic_bar_charts(tables: List[TableResult]) -> List[ChartResult]:
    """Create simple bar charts from table totals.

    Placeholder implementation mapping bucket -> case_count per KPI.
    """
    results: List[ChartResult] = []
    for t in tables:
        series = [
            ChartSeries(
                name=t.kpi_id,
                data=[ChartPoint(x=row[0], y=row[1]) for row in t.rows],
            )
        ]
        chart = BarChart(
            metadata=ChartMetadata(
                title=f"{t.kpi_id} distribution",
                x_axis=ChartAxis(label="bucket", type="category"),
                y_axis=ChartAxis(label="case_count", type="linear"),
            ),
            series=series,
            stacked=False,
        )
        results.append(ChartResult(chart_type=chart.type.value, spec=chart.model_dump(by_alias=True), kpi_ids=[t.kpi_id]))
    return results
