from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel

# -----------------------------
# Chart Type Enum (from SSOT ChartType.yml)
# -----------------------------


class ChartType(str, Enum):
    LINE = "LINE"
    BAR = "BAR"
    BOX = "BOX"
    HISTOGRAM = "HISTOGRAM"
    SCATTER = "SCATTER"
    PIE = "PIE"
    RADAR = "RADAR"
    WATERFALL = "WATERFALL"
    AREA = "AREA"


# -----------------------------
# Common Chart Data Components
# -----------------------------


class ChartPoint(BaseModel):
    """Single data point for charts"""

    x: Union[str, int, float]
    y: Union[int, float]
    label: Optional[str] = None


class ChartSeries(BaseModel):
    """Data series for multi-line/multi-series charts"""

    name: str
    data: List[ChartPoint]
    color: Optional[str] = None
    style: Optional[Dict[str, Any]] = None


class ChartAxis(BaseModel):
    """Chart axis configuration"""

    label: str
    type: Literal["linear", "logarithmic", "category", "time"] = "linear"
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    unit: Optional[str] = None


class ChartMetadata(BaseModel):
    """Common chart metadata"""

    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    x_axis: Optional[ChartAxis] = None
    y_axis: Optional[ChartAxis] = None
    legend: bool = True
    width: Optional[int] = None
    height: Optional[int] = None


# -----------------------------
# Specific Chart DTOs
# -----------------------------


class LineChart(BaseModel):
    """Line chart DTO - supports multiple lines/series"""

    type: Literal[ChartType.LINE] = ChartType.LINE
    metadata: ChartMetadata
    series: List[ChartSeries]
    smooth: bool = False
    show_points: bool = True
    fill_area: bool = False


class BarChart(BaseModel):
    """Bar chart DTO - supports grouped/stacked bars"""

    type: Literal[ChartType.BAR] = ChartType.BAR
    metadata: ChartMetadata
    series: List[ChartSeries]
    orientation: Literal["vertical", "horizontal"] = "vertical"
    stacked: bool = False
    bar_width: Optional[float] = None


class BoxPlot(BaseModel):
    """Box plot DTO - box-and-whisker charts"""

    type: Literal[ChartType.BOX] = ChartType.BOX
    metadata: ChartMetadata
    data: List[Dict[str, Union[str, float, List[float]]]]  # Each box has: name, q1, median, q3, min, max, outliers
    show_outliers: bool = True
    notched: bool = False


class Histogram(BaseModel):
    """Histogram DTO - frequency distributions"""

    type: Literal[ChartType.HISTOGRAM] = ChartType.HISTOGRAM
    metadata: ChartMetadata
    data: List[Dict[str, Union[str, int, float]]]  # bins with: range_start, range_end, frequency, density
    bin_count: int
    bin_width: Optional[float] = None
    cumulative: bool = False


class ScatterPlot(BaseModel):
    """Scatter plot DTO - XY plots with optional grouping"""

    type: Literal[ChartType.SCATTER] = ChartType.SCATTER
    metadata: ChartMetadata
    series: List[ChartSeries]
    point_size: Optional[float] = None
    show_trend_line: bool = False
    bubble_size_field: Optional[str] = None  # For bubble charts


class PieChart(BaseModel):
    """Pie chart DTO - circular charts"""

    type: Literal[ChartType.PIE] = ChartType.PIE
    metadata: ChartMetadata
    data: List[Dict[str, Union[str, float]]]  # Each slice has: label, value, color?
    show_percentages: bool = True
    donut: bool = False  # True for donut chart
    inner_radius: Optional[float] = None


class RadarChart(BaseModel):
    """Radar chart DTO - spider/web charts"""

    type: Literal[ChartType.RADAR] = ChartType.RADAR
    metadata: ChartMetadata
    series: List[ChartSeries]
    axes: List[str]  # List of axis names/dimensions
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    filled: bool = False


class WaterfallChart(BaseModel):
    """Waterfall chart DTO - bridge/cascade charts"""

    type: Literal[ChartType.WATERFALL] = ChartType.WATERFALL
    metadata: ChartMetadata
    data: List[Dict[str, Union[str, float, bool]]]  # Each step: label, value, is_total, is_positive
    show_connectors: bool = True
    start_value: Optional[float] = None


class AreaChart(BaseModel):
    """Area chart DTO - filled area graphs"""

    type: Literal[ChartType.AREA] = ChartType.AREA
    metadata: ChartMetadata
    series: List[ChartSeries]
    stacked: bool = False
    normalize: bool = False  # For 100% stacked areas
    transparency: Optional[float] = None


# -----------------------------
# Union Type for All Charts
# -----------------------------

ChartDTO = Union[
    LineChart,
    BarChart,
    BoxPlot,
    Histogram,
    ScatterPlot,
    PieChart,
    RadarChart,
    WaterfallChart,
    AreaChart,
]


# -----------------------------
# Multi-Chart Response DTO
# -----------------------------


class VisualizationResponse(BaseModel):
    """Response containing multiple charts/visualizations"""

    charts: List[ChartDTO]
    analysis_text: Optional[str] = None  # Optional explanatory text
    statistical_summary: Optional[Dict[str, Any]] = None  # Optional statistical results
    timestamp: Optional[str] = None
    query_context: Optional[str] = None  # Original user query context
