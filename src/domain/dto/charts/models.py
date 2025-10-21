"""Compatibility shim for existing imports.

This module re-exports chart DTOs and types from the split submodules.
Prefer importing from `src.domain.dto.charts` package modules directly.
"""

from ..response import VisualizationResponse  # noqa: F401
from .area import AreaChart  # noqa: F401
from .bar import BarChart  # noqa: F401
from .box import BoxPlot  # noqa: F401
from .histogram import Histogram  # noqa: F401
from .line import LineChart  # noqa: F401
from .pie import PieChart  # noqa: F401
from .radar import RadarChart  # noqa: F401
from .scatter import ScatterPlot  # noqa: F401
from .types import (  # noqa: F401
    ChartAxis,
    ChartMetadata,
    ChartPoint,
    ChartSeries,
    ChartType,
)
from .union import ChartDTO  # noqa: F401
from .waterfall import WaterfallChart  # noqa: F401

__all__ = [
    "ChartType",
    "ChartPoint",
    "ChartSeries",
    "ChartAxis",
    "ChartMetadata",
    "LineChart",
    "BarChart",
    "BoxPlot",
    "Histogram",
    "ScatterPlot",
    "PieChart",
    "RadarChart",
    "WaterfallChart",
    "AreaChart",
    "ChartDTO",
    "VisualizationResponse",
]
