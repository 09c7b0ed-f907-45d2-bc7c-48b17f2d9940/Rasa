from typing import Any, Dict, List, Optional, Union

from src.graphql.graphql_result import Kpi1, Metric, MetricsQueryResponse

from .box_plot import BoxPlot, BoxPlotSeries
from .line_plot import LinePlot, LinePlotSeries


def extract_metrics(response: Union[MetricsQueryResponse, Dict[str, Any]]) -> Dict[str, Metric]:
    metrics: Dict[str, Metric] = {}

    # Accept both Pydantic model and dict
    if isinstance(response, dict):
        data = response.get("data") or response.get("result", {})
        get_metrics = data.get("get_metrics") or data.get("getMetrics")
        if not get_metrics:
            return {}
        metrics_dict = get_metrics.get("metrics", {})
        # If values are dicts, parse them as Metric
        for k, v in metrics_dict.items():
            metrics[k] = v if isinstance(v, Metric) else Metric.model_validate(v)
        return metrics

    # If it's a Pydantic model
    get_metrics = response.data.get_metrics
    if hasattr(get_metrics, "metrics") and get_metrics.metrics:
        for k, v in get_metrics.metrics.items():
            metrics[k] = v
    return metrics


def metric_id_from_key(key: str) -> str:
    return key.replace("metric_", "")


def build_line_plot(metric_id: str, metric: Metric) -> Optional[LinePlot]:
    for group in metric.kpi_group:
        kpi: Kpi1 = group.kpi1
        if kpi.d1:
            d1 = kpi.d1
            label = group.grouped_by.group_item_name if group.grouped_by else "All"
            series = [LinePlotSeries(label=label, values=[float(v) for v in d1.case_count])]
            if len(metric.kpi_group) > 1 or group.grouped_by:
                series: List[LinePlotSeries] = []
                for g in metric.kpi_group:
                    label = g.grouped_by.group_item_name if g.grouped_by else "All"
                    if g.kpi1.d1:
                        series.append(LinePlotSeries(label=label, values=[float(v) for v in g.kpi1.d1.case_count]))
            return LinePlot(
                chartTitle=f"{metric_id} Distribution",
                xAxisLabel="Bins",
                yAxisLabel="Count",
                bins=d1.edges,
                series=series,
                grouped=bool(group.grouped_by),
                sourceMetricId=metric_id,
            )
    return None


def build_box_plot(metric_id: str, metric: Metric) -> Optional[BoxPlot]:
    series: List[BoxPlotSeries] = []
    for group in metric.kpi_group:
        kpi: Kpi1 = group.kpi1
        if kpi.quartiles and len(kpi.quartiles) == 3:
            label = group.grouped_by.group_item_name if group.grouped_by else "All"
            box = BoxPlotSeries(
                label=label,
                min=float(val) if (val := getattr(kpi, "min", None)) is not None else None,
                q1=kpi.quartiles[0],
                median=kpi.quartiles[1],
                q3=kpi.quartiles[2],
                max=float(val) if (val := getattr(kpi, "max", None)) is not None else None,
                mean=kpi.mean,
                ci_mean=kpi.confidence_interval_mean,
                ci_median=kpi.confidence_interval_median,
            )
            series.append(box)
    if series:
        return BoxPlot(
            chartTitle=f"{metric_id} Summary",
            yAxisLabel=metric_id,
            series=series,
            sourceMetricId=metric_id,
        )
    return None


def convert_graphql_to_charts(result: Union[MetricsQueryResponse, Dict[str, Any]]) -> List[Dict[str, Any]]:
    metrics = extract_metrics(result)
    charts: List[Union[LinePlot, BoxPlot]] = []
    for metric_key, metric in metrics.items():
        metric_id = metric_id_from_key(metric_key)
        line = build_line_plot(metric_id, metric)
        if line:
            charts.append(line)
        box = build_box_plot(metric_id, metric)
        if box:
            charts.append(box)
    # Return as dicts for JSON serialization
    return [chart.model_dump(by_alias=True) for chart in charts]
