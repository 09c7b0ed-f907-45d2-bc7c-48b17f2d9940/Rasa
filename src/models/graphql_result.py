from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------
# Base Components
# -----------------------------


class GeneralStatistics(BaseModel):
    cases_in_period: int = Field(..., alias="casesInPeriod")
    filtered_cases_in_period: int = Field(..., alias="filteredCasesInPeriod")

    model_config = ConfigDict(populate_by_name=True)


class GeneralStatsGroup(BaseModel):
    general_statistics: GeneralStatistics = Field(..., alias="generalStatistics")

    model_config = ConfigDict(populate_by_name=True)


class GroupedBy(BaseModel):
    group_item_name: str = Field(..., alias="groupItemName")

    model_config = ConfigDict(populate_by_name=True)


class D1(BaseModel):
    edges: List[int]
    case_count: List[int] = Field(..., alias="caseCount")
    percents: List[float]
    normalized_percents: List[float] = Field(..., alias="normalizedPercents")

    model_config = ConfigDict(populate_by_name=True)


# -----------------------------
# Unified KPI + Group Models
# -----------------------------


class Kpi1(BaseModel):
    case_count: List[int] = Field(..., alias="caseCount")
    percents: Optional[List[float]] = None
    normalized_percents: Optional[List[float]] = Field(default=None, alias="normalizedPercents")
    cohort_size: Optional[int] = Field(default=None, alias="cohortSize")
    normalized_cohort_size: Optional[List[int]] = Field(default=None, alias="normalizedCohortSize")
    median: Optional[int] = None
    mean: Optional[float] = None
    variance: Optional[float] = None
    confidence_interval_mean: Optional[List[float]] = Field(default=None, alias="confidenceIntervalMean")
    confidence_interval_median: Optional[List[int]] = Field(default=None, alias="confidenceIntervalMedian")
    interquartile_range: Optional[int] = Field(default=None, alias="interquartileRange")
    quartiles: Optional[List[int]] = None
    d1: Optional[D1] = None

    model_config = ConfigDict(populate_by_name=True)


class MetricKpiGroup(BaseModel):
    kpi1: Kpi1
    grouped_by: Optional[GroupedBy] = Field(default=None, alias="groupedBy")

    model_config = ConfigDict(populate_by_name=True)


class Metric(BaseModel):
    kpi_group: List[MetricKpiGroup] = Field(..., alias="kpiGroup")

    model_config = ConfigDict(populate_by_name=True)


# -----------------------------
# Top-Level Structures
# -----------------------------


class GetMetrics(BaseModel):
    general_stats_group: Optional[List[GeneralStatsGroup]] = Field(default=None, alias="generalStatsGroup")

    # Known metrics for autocomplete + type hints
    metric_AGE: Optional[Metric] = None
    metric_DTN: Optional[Metric] = None
    metric_DTI: Optional[Metric] = None

    # Accept any additional metrics
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Data(BaseModel):
    get_metrics: GetMetrics = Field(..., alias="getMetrics")

    model_config = ConfigDict(populate_by_name=True)


class Welcome(BaseModel):
    data: Data
    errors: Optional[List[Dict[str, Any]]] = None  # GraphQL typically uses structured errors

    model_config = ConfigDict(populate_by_name=True)
