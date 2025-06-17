import logging
from typing import List

import src.graphql.graphql_builder as GB
import src.instructor.models as IM

logger = logging.getLogger(__name__)


def Build_query_from_instructor_models(MetricCalculatorResponse: IM.MetricCalculatorResponse) -> str:
    metricCollection = MetricCalculatorResponse.MetricResponse.metricsCollection
    metrics = MetricsRequest_to_MetricBuilder(metricCollection) if metricCollection else []
    if not metrics:
        logger.warning("No metrics are selected")
    groupBy = GB.Group(metricCollection.group_by) if metricCollection and metricCollection.group_by else None

    logicalFilter = MetricCalculatorResponse.FilterResponse.logicalFilter
    caseFilters = LogicFilter_to_LogicalNode(logicalFilter) if logicalFilter else None

    return GB.build_query(metrics, caseFilters, groupBy=groupBy)


def MetricsRequest_to_MetricBuilder(MetricsRequest: IM.MetricsCollection) -> List[GB.MetricBuilder]:
    metrics: List[GB.MetricBuilder] = []
    for metric in MetricsRequest.metrics:
        new_metric = GB.MetricBuilder(metric.kpi)
        if metric.stats:
            new_metric.with_stats()
        if metric.distribution:
            new_metric.with_distribution(metric.distribution.bin_count, metric.distribution.lower, metric.distribution.upper)
        metrics.append(new_metric)
    return metrics


def LogicFilter_to_LogicalNode(LogicalFilter: IM.LogicalFilter) -> GB.LogicalNode | None:
    if not LogicalFilter.children:
        logger.warning("Logical filter had no children, deleteing node")
        return None

    new_children: List[GB.BaseFilter] = []
    for child in LogicalFilter.children:
        match child:
            case IM.LogicalFilter():
                LogicFilter_to_LogicalNode(child)
            case IM.AgeFilter():
                new_children.append(
                    GB.AgeFilter(
                        GB.Operator(child.operator),
                        child.value,
                    )
                )
            case IM.NIHSSFilter():
                new_children.append(
                    GB.NIHSSFilter(
                        GB.Operator(child.operator),
                        child.value,
                    )
                )
            case IM.SexFilter():
                new_children.append(GB.SexFilter(GB.SexProperty(child.value), True))
            case IM.StrokeFilter():
                new_children.append(GB.StrokeFilter(GB.StrokeProperty(child.value), True))
            case IM.DateFilter():
                new_children.append(
                    GB.DateFilter(
                        GB.DateProperty(child.type),
                        GB.Operator(child.operator),
                        child.value,
                    )
                )
            case IM.BooleanFilter():
                new_children.append(GB.BooleanFilter(GB.BooleanProperty(child.property), True))

    match LogicalFilter.operator:
        case IM.OperatorProperty.AND:
            return GB.AND(*new_children)
        case IM.OperatorProperty.OR:
            return GB.OR(*new_children)
        case IM.OperatorProperty.NOT:
            return GB.NOT(*new_children)
