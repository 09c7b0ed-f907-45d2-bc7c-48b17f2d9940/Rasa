from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartSeries, ChartType


class ScatterPlot(BaseModel):
    """Scatter plot DTO - XY plots with optional grouping"""

    type: Literal[ChartType.SCATTER] = ChartType.SCATTER
    metadata: ChartMetadata
    series: List[ChartSeries]
    point_size: Optional[float] = None
    show_trend_line: bool = False
    bubble_size_field: Optional[str] = None  # For bubble charts
