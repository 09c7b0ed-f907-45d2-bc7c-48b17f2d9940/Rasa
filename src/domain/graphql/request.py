"""
Pydantic-based GraphQL query input models that mirror the output structure.
Clean, type-safe alternative to the builder pattern approach.
Uses SSOT-based enums for consistency across the system.
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

# Import GraphQL-specific SSOT-based enums
from src.domain.graphql.ssot_enums import BooleanPropertyType, GroupByType, MetricType, Operator, SexType, StrokeType

# -----------------------------
# Filter Models
# -----------------------------


class IntegerFilter(BaseModel):
    """Filter for integer/numeric values"""

    property: Literal["AGE", "ADMISSION_NIHSS", "GLUCOSE", "CHOLESTEROL", "SYSTOLIC_PRESSURE", "DIASTOLIC_PRESSURE"]
    operator: Operator
    value: int


class BooleanFilter(BaseModel):
    """Filter for boolean values - uses SSOT BooleanPropertyType"""

    property: BooleanPropertyType
    value: bool


class SexFilter(BaseModel):
    """Filter for sex/gender"""

    sex_type: SexType = Field(alias="sexType")
    contains: bool = True


class StrokeFilter(BaseModel):
    """Filter for stroke type"""

    stroke_type: StrokeType = Field(alias="strokeType")
    contains: bool = True


class DateFilter(BaseModel):
    """Filter for date values"""

    property: Literal["DISCHARGE_DATE", "ADMISSION_DATE", "ONSET_DATE"]
    operator: Operator
    value: str  # ISO date string


class LogicalFilter(BaseModel):
    """Logical combination of filters (AND, OR, NOT)"""

    operator: Literal["AND", "OR", "NOT"]
    children: List[Union["LogicalFilter", IntegerFilter, BooleanFilter, SexFilter, StrokeFilter, DateFilter]]


# Enable forward references
LogicalFilter.model_rebuild()


# Union type for all filters
FilterType = Union[LogicalFilter, IntegerFilter, BooleanFilter, SexFilter, StrokeFilter, DateFilter]


# -----------------------------
# Metric Configuration
# -----------------------------


class MetricOptions(BaseModel):
    """Options for metric calculation"""

    lower_boundary: Optional[int] = Field(default=None, alias="lowerBoundary")
    upper_boundary: Optional[int] = Field(default=None, alias="upperBoundary")


class DistributionOptions(BaseModel):
    """Options for distribution calculation"""

    bin_count: int = Field(default=20, alias="binCount")
    lower_bound: int = Field(alias="lowerBound")
    upper_bound: int = Field(alias="upperBound")


class MetricRequest(BaseModel):
    """Request for a specific metric with options"""

    metric_type: MetricType = Field(alias="metricType")
    alias: Optional[str] = None

    # Analysis options
    include_stats: bool = Field(default=False, alias="includeStats")
    include_distribution: bool = Field(default=False, alias="includeDistribution")
    include_grouping: bool = Field(default=False, alias="includeGrouping")

    # Metric-specific options
    metric_options: Optional[MetricOptions] = Field(default=None, alias="metricOptions")
    distribution_options: Optional[DistributionOptions] = Field(default=None, alias="distributionOptions")

    @model_validator(mode="after")
    def validate_distribution_options(self):
        """Ensure distribution options are provided when distribution is requested"""
        if self.include_distribution and not self.distribution_options:
            # Set sensible defaults based on metric type
            if self.metric_type.value == "AGE":
                self.distribution_options = DistributionOptions(binCount=20, lowerBound=18, upperBound=95)
            elif self.metric_type.value == "DTN":
                self.distribution_options = DistributionOptions(binCount=24, lowerBound=0, upperBound=120)
            elif self.metric_type.value == "ADMISSION_NIHSS":
                self.distribution_options = DistributionOptions(binCount=21, lowerBound=0, upperBound=42)
            else:
                self.distribution_options = DistributionOptions(binCount=20, lowerBound=0, upperBound=100)

        return self

    def with_stats(self) -> "MetricRequest":
        """Builder method: include statistical measures"""
        self.include_stats = True
        return self

    def with_distribution(self, bin_count: int = 20, lower: int = 0, upper: int = 100) -> "MetricRequest":
        """Builder method: include distribution data"""
        self.include_distribution = True
        self.distribution_options = DistributionOptions(binCount=bin_count, lowerBound=lower, upperBound=upper)
        # Ensure kpiOptions carry the range as some providers require lower/upper boundary for distributions
        if not self.metric_options:
            self.metric_options = MetricOptions()
        self.metric_options.lower_boundary = lower
        self.metric_options.upper_boundary = upper
        return self

    def with_bounds(self, lower: int, upper: int) -> "MetricRequest":
        """Builder method: set metric boundaries"""
        if not self.metric_options:
            self.metric_options = MetricOptions()
        self.metric_options.lower_boundary = lower
        self.metric_options.upper_boundary = upper
        return self


# -----------------------------
# Time Period and Data Origin
# -----------------------------


class TimePeriod(BaseModel):
    """Time period for the query"""

    start_date: str = Field(alias="startDate")  # ISO date string
    end_date: str = Field(alias="endDate")  # ISO date string


class DataOrigin(BaseModel):
    """Data source configuration"""

    provider_group_id: List[int] = Field(alias="providerGroupId")


# -----------------------------
# Main Query Model
# -----------------------------


class GraphQLQueryRequest(BaseModel):
    """Main GraphQL query request model"""

    # Required fields
    metrics: List[MetricRequest]
    time_period: TimePeriod = Field(alias="timePeriod")
    data_origin: DataOrigin = Field(alias="dataOrigin")

    # Optional fields
    case_filter: Optional[FilterType] = Field(default=None, alias="caseFilter")
    group_by: Optional[GroupByType] = Field(default=None, alias="groupBy")
    include_general_stats: bool = Field(default=False, alias="includeGeneralStats")

    @model_validator(mode="after")
    def set_grouping_on_metrics(self):
        """Automatically enable grouping on all metrics if group_by is specified"""
        if self.group_by:
            for metric in self.metrics:
                metric.include_grouping = True
        return self

    def to_graphql_string(self) -> str:
        """Convert this request to a GraphQL query string"""
        return GraphQLQueryGenerator.generate(self)


# -----------------------------
# Query Generation
# -----------------------------


class GraphQLQueryGenerator:
    """Generates GraphQL query strings from Pydantic models"""

    @staticmethod
    def generate(request: GraphQLQueryRequest) -> str:
        """Generate GraphQL query string from request model"""

        # Build filter arguments
        filter_args: List[str] = []

        # Time period (required) as a single input object
        filter_args.append(f'timePeriod: {{ startDate: "{request.time_period.start_date}", endDate: "{request.time_period.end_date}" }}')

        # Data origin (required)
        provider_ids = ", ".join(str(id) for id in request.data_origin.provider_group_id)
        filter_args.append(f"""
            dataOrigin: {{providerGroupId: [{provider_ids}]}}
        """)

        # Case filter (optional)
        if request.case_filter:
            filter_args.append(f"caseFilter: {GraphQLQueryGenerator._generate_filter(request.case_filter)}")

        filter_string = ", ".join(filter_args)

        # Build main query arguments
        query_args = [f"filter: {{{filter_string}}}"]

        if request.group_by:
            # groupBy is an enum; render without quotes
            query_args.append(f"groupBy: {request.group_by.value}")

        # Build metric fields
        metric_fields: List[str] = []
        for metric in request.metrics:
            metric_fields.append(GraphQLQueryGenerator._generate_metric_field(metric))

        # Add general stats if requested
        if request.include_general_stats:
            metric_fields.append("""
                generalStatsGroup {
                    generalStatistics {
                        casesInPeriod
                        filteredCasesInPeriod
                    }
                }
            """)

        # Combine into final query
        query = f"""
        query {{
            getMetrics({", ".join(query_args)}) {{
                {" ".join(metric_fields)}
            }}
        }}
        """

        return GraphQLQueryGenerator._clean_query(query)

    @staticmethod
    def _generate_filter(filter_obj: FilterType) -> str:
        """Generate filter GraphQL from filter models"""

        if isinstance(filter_obj, LogicalFilter):
            # Render enum operator without quotes and children as objects (no extra brackets)
            children_str = ", ".join([GraphQLQueryGenerator._generate_filter(child) for child in filter_obj.children])
            return f"""{{
                node: {{
                    logicalOperator: {filter_obj.operator},
                    children: [{children_str}]
                }}
            }}"""

        elif isinstance(filter_obj, IntegerFilter):
            return f'''{{
                leaf: {{
                    integerCaseFilter: {{
                        property: "{filter_obj.property}",
                        operator: "{filter_obj.operator.value}",
                        value: {filter_obj.value}
                    }}
                }}
            }}'''

        elif isinstance(filter_obj, BooleanFilter):
            return f'''{{
                leaf: {{
                    booleanCaseFilter: {{
                        property: "{filter_obj.property}",
                        value: {str(filter_obj.value).lower()}
                    }}
                }}
            }}'''

        elif isinstance(filter_obj, SexFilter):
            # Render enum values without quotes and as a list
            return f"""{{
                leaf: {{
                    enumCaseFilter: {{
                        sexType: {{
                            values: [{filter_obj.sex_type.value}],
                            contains: {str(filter_obj.contains).lower()}
                        }}
                    }}
                }}
            }}"""

        elif isinstance(filter_obj, StrokeFilter):
            # Render enum values without quotes and as a list
            return f"""{{
                leaf: {{
                    enumCaseFilter: {{
                        strokeType: {{
                            values: [{filter_obj.stroke_type.value}],
                            contains: {str(filter_obj.contains).lower()}
                        }}
                    }}
                }}
            }}"""

        elif type(filter_obj).__name__ == "DateFilter":
            return f'''{{
                leaf: {{
                    dateCaseFilter: {{
                        property: "{filter_obj.property}",
                        operator: "{filter_obj.operator.value}",
                        value: "{filter_obj.value}"
                    }}
                }}
            }}'''

        return "{}"

    @staticmethod
    def _generate_metric_field(metric: MetricRequest) -> str:
        """Generate GraphQL field for a metric request"""

        alias = metric.alias or f"metric_{metric.metric_type.value}"

        # Build KPI fields
        kpi_fields = ["caseCount"]

        if metric.include_stats:
            kpi_fields.extend(["percents", "normalizedPercents", "cohortSize", "normalizedCohortSize", "median", "mean", "variance", "confidenceIntervalMean", "confidenceIntervalMedian", "interquartileRange", "quartiles"])

        if metric.include_distribution and metric.distribution_options:
            kpi_fields.append(f"""
                d1: distribution(binCount: {metric.distribution_options.bin_count}) {{
                    edges
                    caseCount
                    percents
                    normalizedPercents
                }}
            """)

        # Build KPI options
        kpi_options = ""
        if metric.metric_options:
            options: List[str] = []
            if metric.metric_options.lower_boundary is not None:
                options.append(f"lowerBoundary: {metric.metric_options.lower_boundary}")
            if metric.metric_options.upper_boundary is not None:
                options.append(f"upperBoundary: {metric.metric_options.upper_boundary}")

            if options:
                kpi_options = f"kpiOptions: {{{', '.join(options)}}}"

        # Build kpiGroup fields; omit parentheses if no options
        kpi_call = f"kpi({kpi_options})" if kpi_options else "kpi"
        kpi_group_fields = [
            f"""
            kpi1: {kpi_call} {{
                {" ".join(kpi_fields)}
            }}
        """
        ]

        if metric.include_grouping:
            kpi_group_fields.append("""
                groupedBy {
                    groupItemName
                }
            """)

        return f"""
            {alias}: metric(metricId: {metric.metric_type.value}) {{
                kpiGroup {{
                    {" ".join(kpi_group_fields)}
                }}
            }}
        """

    @staticmethod
    def _clean_query(query: str) -> str:
        """Clean up the generated query string"""
        import re

        # Remove extra whitespace and newlines
        query = re.sub(r"\s+", " ", query)
        query = re.sub(r"\s*{\s*", " { ", query)
        query = re.sub(r"\s*}\s*", " } ", query)
        query = query.strip()

        return query


# -----------------------------
# Convenience Functions
# -----------------------------


def create_age_filter(operator: Operator, value: int) -> IntegerFilter:
    """Create an age filter"""
    return IntegerFilter(property="AGE", operator=operator, value=value)


def create_sex_filter(sex: SexType, contains: bool = True) -> SexFilter:
    """Create a sex filter"""
    return SexFilter(sexType=sex, contains=contains)


def create_stroke_filter(stroke_type: StrokeType, contains: bool = True) -> StrokeFilter:
    """Create a stroke type filter"""
    return StrokeFilter(strokeType=stroke_type, contains=contains)


def create_and_filter(*filters: FilterType) -> LogicalFilter:
    """Create an AND logical filter"""
    return LogicalFilter(operator="AND", children=list(filters))


def create_or_filter(*filters: FilterType) -> LogicalFilter:
    """Create an OR logical filter"""
    return LogicalFilter(operator="OR", children=list(filters))


def create_not_filter(filter_obj: FilterType) -> LogicalFilter:
    """Create a NOT logical filter"""
    return LogicalFilter(operator="NOT", children=[filter_obj])
