from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.langchain.planner_schema import AnalysisPlan

__all__ = [
    "ExecutionConfig",
    "TableResult",
    "MetricResult",
    "StatisticalTestResult",
    "ChartResult",
    "ExecutionReport",
    "AnalysisResult",
]


class ExecutionConfig(BaseModel):
    """Configuration for executor behavior."""

    debug: bool = False
    include_raw_samples: bool = False
    max_sample_rows: int = 20


class TableResult(BaseModel):
    """Tabular normalized results per metric/KPI."""

    kpi_id: str
    columns: List[str]
    rows: List[List[Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    """Computed metric outputs (post-processing/aggregations)."""

    kpi_id: str
    values: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StatisticalTestResult(BaseModel):
    """Result of running a statistical test."""

    test_type: str
    input_kpis: List[str]
    result: Dict[str, Any]
    p_value: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChartResult(BaseModel):
    """Wrapper around chart DTOs to keep a unified type for the executor output."""

    chart_type: str
    spec: Dict[str, Any]  # JSON-serializable chart payload compatible with frontend
    kpi_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionReport(BaseModel):
    """Debug/provenance information captured during execution."""

    graphql_queries: List[Dict[str, Any]] = Field(default_factory=list)
    timings: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    raw_data_sample: Optional[Dict[str, Any]] = None
    notes: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Top-level result returned by the executor back to the action layer."""

    plan: AnalysisPlan
    tables: List[TableResult] = Field(default_factory=list)
    metrics: List[MetricResult] = Field(default_factory=list)
    statistical_tests: List[StatisticalTestResult] = Field(default_factory=list)
    charts: List[ChartResult] = Field(default_factory=list)
    report: ExecutionReport = Field(default_factory=ExecutionReport)
