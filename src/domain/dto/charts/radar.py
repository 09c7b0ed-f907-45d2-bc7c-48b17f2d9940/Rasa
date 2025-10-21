from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartSeries, ChartType


class RadarChart(BaseModel):
    """Radar chart DTO - spider/web charts"""

    type: Literal[ChartType.RADAR] = ChartType.RADAR
    metadata: ChartMetadata
    series: List[ChartSeries]
    axes: List[str]  # List of axis names/dimensions
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    filled: bool = False
