"""
Chart Models for Rasa Action Server Visualizations.

This module defines Pydantic models for structured chart data that can be consumed
by the webapp frontend for visualizations. Uses SSOT ChartType enum for type safety.

Supported chart types from SSOT: LINE, BAR, BOX, HISTOGRAM, SCATTER, PIE, RADAR, WATERFALL, AREA
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

# Dynamic imports and type handling for ChartType enum
try:
    from src.langchain import ChartType, validate_enum_value

    _chart_type_available = True
except ImportError:
    _chart_type_available = False
    ChartType = None
    validate_enum_value = None

# Get the enum values for defaults - define at module level
if _chart_type_available and ChartType is not None:
    line_default = ChartType.LINE
    box_default = ChartType.BOX
    bar_default = ChartType.BAR
    scatter_default = ChartType.SCATTER
    pie_default = ChartType.PIE
    histogram_default = ChartType.HISTOGRAM
else:
    # Fallback defaults
    line_default = "LINE"
    box_default = "BOX"
    bar_default = "BAR"
    scatter_default = "SCATTER"
    pie_default = "PIE"
    histogram_default = "HISTOGRAM"

# Fallback validation values
_fallback_chart_types = ["LINE", "BOX", "BAR", "SCATTER", "PIE", "HISTOGRAM", "RADAR", "WATERFALL", "AREA"]


class BasePlot(BaseModel):
    """Base model for all plot types with common fields."""

    chart_title: str = Field(description="Title of the chart")
    x_axis_label: Optional[str] = Field(default=None, description="Label for X-axis")
    y_axis_label: str = Field(description="Label for Y-axis")
    source_metric_id: Optional[str] = Field(default=None, description="ID of the source metric")
    plot_style: Literal["single", "grouped"] = Field(description="Plot style: single or grouped")
    # Accept either ChartType enum or string, always store as string
    plot_type: str = Field(description="Type of chart from SSOT ChartType enum")

    @field_validator("plot_type")
    @classmethod
    def validate_plot_type(cls, v: Any) -> str:
        """Validate plot_type against available enum or fallback list."""
        if validate_enum_value is not None:
            # Use the centralized validation utility
            return validate_enum_value(v, ChartType, _fallback_chart_types)
        else:
            # Simple fallback validation
            v_str = str(v)
            if v_str not in _fallback_chart_types:
                raise ValueError(f"plot_type must be one of {_fallback_chart_types}, got {v}")
            return v_str


class LinePlotSeries(BaseModel):
    """Data series for line plots."""

    label: str = Field(description="Series label/name")
    values: List[float] = Field(description="Y-axis values for the series")


class LinePlot(BasePlot):
    """Line plot model for time series and continuous data."""

    plot_type: str = Field(default=line_default, description="Chart type: LINE")
    bins: List[float] = Field(description="X-axis values (time points, categories, etc.)")
    series: List[LinePlotSeries] = Field(description="Data series for the line plot")


class BoxPlotSeries(BaseModel):
    """Data series for box plots with statistical summary."""

    label: str = Field(description="Series label/name")
    min_value: float = Field(alias="min", description="Minimum value")
    q1: float = Field(description="First quartile (25th percentile)")
    median: float = Field(description="Median value (50th percentile)")
    q3: float = Field(description="Third quartile (75th percentile)")
    max_value: float = Field(alias="max", description="Maximum value")
    mean: float = Field(description="Mean/average value")
    ci_mean: Optional[List[float]] = Field(default=None, description="Confidence interval for mean [lower, upper]")
    ci_median: Optional[List[float]] = Field(default=None, description="Confidence interval for median [lower, upper]")


class BoxPlot(BasePlot):
    """Box plot model for statistical data visualization."""

    plot_type: str = Field(default=box_default, description="Chart type: BOX")
    series: List[BoxPlotSeries] = Field(description="Box plot data series")


class BarPlotSeries(BaseModel):
    """Data series for bar charts."""

    label: str = Field(description="Series label/name")
    values: List[float] = Field(description="Bar values")


class BarPlot(BasePlot):
    """Bar plot model for categorical data."""

    plot_type: str = Field(default=bar_default, description="Chart type: BAR")
    categories: List[str] = Field(description="Category labels for bars")
    series: List[BarPlotSeries] = Field(description="Data series for the bar chart")


class ScatterPlotSeries(BaseModel):
    """Data series for scatter plots."""

    label: str = Field(description="Series label/name")
    x_values: List[float] = Field(description="X-coordinate values")
    y_values: List[float] = Field(description="Y-coordinate values")


class ScatterPlot(BasePlot):
    """Scatter plot model for correlation analysis."""

    plot_type: str = Field(default=scatter_default, description="Chart type: SCATTER")
    series: List[ScatterPlotSeries] = Field(description="Data series for the scatter plot")


class PieChartSeries(BaseModel):
    """Data series for pie charts."""

    label: str = Field(description="Slice label/name")
    value: float = Field(description="Slice value")
    percentage: float = Field(description="Percentage of total (computed by Action Service)")


class PieChart(BasePlot):
    """Pie chart model for proportional data."""

    plot_type: str = Field(default=pie_default, description="Chart type: PIE")
    series: List[PieChartSeries] = Field(description="Data series for the pie chart")

    @classmethod
    def create_with_computed_percentages(
        cls,
        chart_title: str,
        y_axis_label: str,
        data: List[tuple[str, Union[int, float]]],  # List of (label, value) tuples
        plot_style: Literal["single", "grouped"] = "single",
        x_axis_label: Optional[str] = None,
        source_metric_id: Optional[str] = None,
    ) -> "PieChart":
        """
        Create a PieChart with automatically computed percentages.

        Args:
            chart_title: Title of the chart
            y_axis_label: Y-axis label
            data: List of (label, value) tuples
            plot_style: Plot style (default: "single")
            x_axis_label: Optional X-axis label
            source_metric_id: Optional source metric ID

        Returns:
            PieChart with computed percentages

        Example:
            pie_chart = PieChart.create_with_computed_percentages(
                chart_title="Sales by Region",
                y_axis_label="Revenue ($)",
                data=[("North", 125000), ("South", 98000), ("East", 156000)]
            )
        """
        # Calculate total for percentage computation
        total_value = sum(value for _, value in data)

        if total_value == 0:
            raise ValueError("Total value cannot be zero for pie chart percentages")

        # Create series with computed percentages
        series = [PieChartSeries(label=label, value=value, percentage=round((value / total_value) * 100, 2)) for label, value in data]

        return cls(chart_title=chart_title, x_axis_label=x_axis_label, y_axis_label=y_axis_label, source_metric_id=source_metric_id, plot_style=plot_style, plot_type=pie_default, series=series)


class HistogramPlot(BasePlot):
    """Histogram model for frequency distribution."""

    plot_type: str = Field(default=histogram_default, description="Chart type: HISTOGRAM")
    bins: List[float] = Field(description="Bin edges")
    frequencies: List[int] = Field(description="Frequency counts for each bin")
    bin_labels: Optional[List[str]] = Field(default=None, description="Optional labels for bins")


# Union type for all possible plot types
Plot = Union[LinePlot, BoxPlot, BarPlot, ScatterPlot, PieChart, HistogramPlot]


class PlotCollection(BaseModel):
    """Collection of plots that can be rendered together."""

    title: str = Field(description="Overall title for the collection")
    description: Optional[str] = Field(default=None, description="Description of the plot collection")
    plots: List[Plot] = Field(description="List of plots (can be mixed types)")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Additional metadata for the collection")


class ChartResponse(BaseModel):
    """Response model for Rasa Action server chart data."""

    success: bool = Field(description="Whether the chart generation was successful")
    message: Optional[str] = Field(default=None, description="Success or error message")
    data: Optional[PlotCollection] = Field(default=None, description="Chart data if successful")
    chart_count: int = Field(default=0, description="Number of charts in the response")

    def model_post_init(self, __context: Any) -> None:
        """Auto-calculate chart_count after initialization."""
        if self.data and self.data.plots:
            self.chart_count = len(self.data.plots)
