import logging
from typing import Dict, List, Optional

from src.charts.box_plot import BoxPlot, BoxPlotSeries
from src.charts.line_plot import LinePlot, LinePlotSeries
from src.charts.plots import PlotCollection
from src.graphql.graphql_result import Kpi1, Metric, MetricsQueryResponse

logger = logging.getLogger()


def extract_metrics(response: MetricsQueryResponse) -> Dict[str, Metric]:
    metrics: Dict[str, Metric] = {}
    get_metrics = response.data.get_metrics
    if get_metrics.metrics:
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


def convert_graphql_to_charts(result: MetricsQueryResponse) -> PlotCollection:
    metrics = extract_metrics(result)
    # logger.debug("Extracted metrics: %s", metrics)

    line_plots: List[LinePlot] = []
    box_plots: List[BoxPlot] = []

    for metric_key, metric in metrics.items():
        metric_id = metric_id_from_key(metric_key)
        if line := build_line_plot(metric_id, metric):
            line_plots.append(line)
        if box := build_box_plot(metric_id, metric):
            box_plots.append(box)

    return PlotCollection(
        linePlots=line_plots,
        boxPlots=box_plots,
    )
