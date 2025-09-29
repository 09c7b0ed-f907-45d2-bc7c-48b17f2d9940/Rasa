# Semantic parser + deterministic executor = LLM-driven planner
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import yaml
from pydantic import BaseModel, Field, field_validator


def _extract_canonical(entry: Any) -> Optional[str]:
    if isinstance(entry, dict):
        cast_entry: Dict[str, Any] = cast(Dict[str, Any], entry)
        val = cast_entry.get("canonical")
        if isinstance(val, str):
            return val
    return None


def load_dynamic_enum(yaml_path: str) -> List[str]:
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing SSOT file: {yaml_path}\n"
            f"Working dir: {Path.cwd()}\n"
            "Diagnostics: The SSOT YAML files were not found inside the container. "
            "If you are building a Docker image ensure that .dockerignore does not exclude 'src/shared/SSOT'.\n"
            "Suggested steps:\n"
            "  1. docker build --no-cache -t action-server .\n"
            "  2. docker run --rm action-server ls -l /app/src/shared/SSOT\n"
            "  3. Confirm host path has files: ls -l src/shared/SSOT\n"
            "If you are volume-mounting src into the container, ensure the host directory actually contains the SSOT files."
        )
    with path.open("r") as f:
        raw_any: Any = yaml.safe_load(f)
    if not isinstance(raw_any, list):
        return []
    raw_list: List[Any] = cast(List[Any], raw_any)
    values: List[str] = []
    for entry in raw_list:
        canonical = _extract_canonical(entry)
        if canonical is not None:
            values.append(canonical)
    return values


# Load all SSOT-driven types dynamically
BOOLEAN_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/BooleanType.yml").resolve()
BooleanType = load_dynamic_enum(str(BOOLEAN_TYPE_YAML))

CHART_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/ChartType.yml").resolve()
ChartType = load_dynamic_enum(str(CHART_TYPE_YAML))

GROUP_BY_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/GroupByType.yml").resolve()
CanonicalGroupByField = load_dynamic_enum(str(GROUP_BY_TYPE_YAML))

METRIC_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/MetricType.yml").resolve()
MetricType = load_dynamic_enum(str(METRIC_TYPE_YAML))

OPERATOR_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/OperatorType.yml").resolve()
OperatorType = load_dynamic_enum(str(OPERATOR_TYPE_YAML))

SEX_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/SexType.yml").resolve()
SexType = load_dynamic_enum(str(SEX_TYPE_YAML))

STATISTICAL_TEST_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/StatisticalTestType.yml").resolve()
StatisticalTestType = load_dynamic_enum(str(STATISTICAL_TEST_TYPE_YAML))

STROKE_TYPE_YAML = (Path(__file__).parent / "../shared/SSOT/StrokeType.yml").resolve()
StrokeType = load_dynamic_enum(str(STROKE_TYPE_YAML))


class DateFilter(BaseModel):
    """
    Filter for date fields using an operator and an ISO 8601 date string.

    Attributes:
        operator: The comparison operator (e.g., 'GE', 'LE', etc.), must be in OperatorType.
        value: The date value to compare, as an ISO 8601 string.
    """

    operator: str
    value: str  # ISO 8601 date string

    @field_validator("operator")
    def validate_operator_type(cls, v: str) -> str:
        if v not in OperatorType:
            raise ValueError(f"{v} is not a valid OperatorType. Allowed: {OperatorType}")
        return v

    @field_validator("value")
    def validate_date_value(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"{v} is not a valid ISO 8601 date or datetime string.")
        return v


class AgeFilter(BaseModel):
    """
    Filter for patient age using an operator and a numeric value.

    Attributes:
        operator: The comparison operator (e.g., 'GE', 'LE', etc.), must be in OperatorType.
        value: The age value to compare (float).
    """

    operator: str
    value: float

    @field_validator("operator")
    def validate_operator_type(cls, v: str) -> str:
        if v not in OperatorType:
            raise ValueError(f"{v} is not a valid OperatorType. Allowed: {OperatorType}")
        return v


class NIHSSFilter(BaseModel):
    """
    Filter for NIHSS score using an operator and a numeric value.

    Attributes:
        operator: The comparison operator (e.g., 'GE', 'LE', etc.), must be in OperatorType.
        value: The NIHSS score to compare (float).
    """

    operator: str
    value: float

    @field_validator("operator")
    def validate_operator_type(cls, v: str) -> str:
        if v not in OperatorType:
            raise ValueError(f"{v} is not a valid OperatorType. Allowed: {OperatorType}")
        return v


class AndFilter(BaseModel):
    """
    Logical AND of multiple filter nodes.

    Attributes:
        and_: List of filter nodes to combine with AND logic.
    """

    and_: List["FilterNode"]


class OrFilter(BaseModel):
    """
    Logical OR of multiple filter nodes.

    Attributes:
        or_: List of filter nodes to combine with OR logic.
    """

    or_: List["FilterNode"]


class NotFilter(BaseModel):
    """
    Logical NOT of a filter node.

    Attributes:
        not_: The filter node to negate.
    """

    not_: "FilterNode"


class SexFilter(BaseModel):
    """
    Filter for patient sex.

    Attributes:
        value: The sex value to filter by (must be in SexType).
    """

    value: str  # Should be a value from SexType

    @field_validator("value")
    def validate_sex_type(cls, v: str) -> str:
        if v not in SexType:
            raise ValueError(f"{v} is not a valid SexType. Allowed: {SexType}")
        return v


class StrokeFilter(BaseModel):
    """
    Filter for stroke type.

    Attributes:
        value: The stroke type to filter by (must be in StrokeType).
    """

    value: str  # Should be a value from StrokeType

    @field_validator("value")
    def validate_stroke_type(cls, v: str) -> str:
        if v not in StrokeType:
            raise ValueError(f"{v} is not a valid StrokeType. Allowed: {StrokeType}")
        return v


class BooleanFilter(BaseModel):
    """
    Filter for boolean fields.

    Attributes:
        boolean_type: The boolean field to filter by (must be in BooleanType).
        value: The boolean value to match (True/False).
    """

    boolean_type: str  # Should be a value from BooleanType
    value: bool

    @field_validator("boolean_type")
    def validate_boolean_type(cls, v: str) -> str:
        if v not in BooleanType:
            raise ValueError(f"{v} is not a valid BooleanType. Allowed: {BooleanType}")
        return v


FilterNode = Union[AndFilter, OrFilter, NotFilter, DateFilter, AgeFilter, NIHSSFilter, SexFilter, StrokeFilter, BooleanFilter]


class GroupBySex(BaseModel):
    """
    Grouping by patient sex.

    Attributes:
        categories: List of sex categories to group by (must be in SexType). None = all.
    """

    categories: Optional[List[str]] = Field(default=None, description="List of sex categories to group by. None = all.")

    @field_validator("categories")
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for val in v:
                if val not in SexType:
                    raise ValueError(f"{val} is not a valid SexType. Allowed: {SexType}")
        return v


class Bucket(BaseModel):
    """
    Represents a bucket for grouping (e.g., age or NIHSS score range).

    Attributes:
        min: Minimum value of the bucket (inclusive).
        max: Maximum value of the bucket (inclusive).
    """

    min: int
    max: int


class GroupByAge(BaseModel):
    """
    Grouping by age buckets.

    Attributes:
        buckets: List of age buckets (each a Bucket object).
    """

    buckets: List[Bucket] = Field(description="List of age buckets.")


class GroupByNIHSS(BaseModel):
    """
    Grouping by NIHSS score buckets.

    Attributes:
        buckets: List of NIHSS score buckets (each a Bucket object).
    """

    buckets: List[Bucket] = Field(description="List of NIHSS score buckets.")


class GroupByStrokeType(BaseModel):
    """
    Grouping by stroke type.

    Attributes:
        categories: List of stroke types to group by (must be in StrokeType). None = all.
    """

    categories: Optional[List[str]] = Field(default=None, description="List of stroke types to group by. None = all.")

    @field_validator("categories")
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for val in v:
                if val not in StrokeType:
                    raise ValueError(f"{val} is not a valid StrokeType. Allowed: {StrokeType}")
        return v


class GroupByBoolean(BaseModel):
    """
    Grouping by boolean field.

    Attributes:
        boolean_type: The boolean field to group by (must be in BooleanType).
        values: List of boolean values to group by. None = all.
    """

    boolean_type: str = Field(description="The boolean field to group by. Should be a value from BooleanType.")
    values: Optional[List[bool]] = Field(default=None, description="Boolean values to group by. None = all.")

    @field_validator("boolean_type")
    def validate_boolean_type(cls, v: str) -> str:
        if v not in BooleanType:
            raise ValueError(f"{v} is not a valid BooleanType. Allowed: {BooleanType}")
        return v


class GroupByCanonicalField(BaseModel):
    """
    Grouping by a canonical field from SSOT/GraphQL.

    Attributes:
        field: The canonical field name (must be in CanonicalGroupByField).
        values: List of values to group by. None = all.
    """

    field: str = Field(description="Canonical field name, should be a value from CanonicalGroupByField.")
    values: Optional[List[str]] = Field(default=None, description="Values to group by. None = all.")

    @field_validator("field")
    def validate_field(cls, v: str) -> str:
        if v not in CanonicalGroupByField:
            raise ValueError(f"{v} is not a valid CanonicalGroupByField. Allowed: {CanonicalGroupByField}")
        return v


class CustomGroup(BaseModel):
    """
    Custom group defined by filters.

    Attributes:
        label: Label for the custom group.
        filters: List of filters defining this group.
    """

    label: str = Field(description="Label for the custom group.")
    filters: List[FilterNode] = Field(description="Filters defining this group.")


GroupBySpec = Union[GroupBySex, GroupByAge, GroupByNIHSS, GroupByStrokeType, GroupByBoolean, GroupByCanonicalField, CustomGroup]


class MetricSpec(BaseModel):
    """
    Specification for a metric to be analyzed or visualized.

    Attributes:
        title: Optional title for the metric.
        description: Optional description for the metric.
        metric: The metric type (must be in MetricType).
        group_by: Optional list of groupings to apply.
        filters: Optional filter node to apply.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    metric: str  # Should be a value from MetricType
    group_by: Optional[List[GroupBySpec]] = None
    filters: Optional[FilterNode] = None

    @field_validator("metric")
    def validate_metric_type(cls, v: str) -> str:
        v_norm = v.upper()
        if v_norm not in MetricType:
            raise ValueError(f"{v} is not a valid MetricType. Allowed: {MetricType}")
        return v_norm


class ChartSpec(BaseModel):
    """
    Specification for a chart to be generated.

    Attributes:
        title: Optional title for the chart.
        description: Optional description for the chart.
        chart_type: The chart type (must be in ChartType).
        metrics: List of metrics to include in the chart.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    chart_type: str  # Should be a value from ChartType
    metrics: List[MetricSpec]

    @field_validator("chart_type")
    def validate_chart_type(cls, v: str) -> str:
        v_norm = v.upper()
        if v_norm not in ChartType:
            raise ValueError(f"{v} is not a valid ChartType. Allowed: {ChartType}")
        return v_norm


class StatisticalTestSpec(BaseModel):
    """
    Specification for a statistical test to be performed.

    Attributes:
        title: Optional title for the test.
        description: Optional description for the test.
        test_type: The statistical test type (must be in StatisticalTestType).
        metrics: List of metrics to include in the test.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    test_type: str  # Should be a value from StatisticalTestType
    metrics: List[MetricSpec]

    @field_validator("test_type")
    def validate_test_type(cls, v: str) -> str:
        v_norm = v.upper()
        if v_norm not in StatisticalTestType:
            raise ValueError(f"{v} is not a valid StatisticalTestType. Allowed: {StatisticalTestType}")
        return v_norm


class AnalysisPlan(BaseModel):
    """
    The top-level plan object returned by the planner.

    Attributes:
        charts: List of chart specifications to generate.
        statistical_tests: List of statistical test specifications to perform.
    """

    charts: Optional[List[ChartSpec]] = None
    statistical_tests: Optional[List[StatisticalTestSpec]] = None
