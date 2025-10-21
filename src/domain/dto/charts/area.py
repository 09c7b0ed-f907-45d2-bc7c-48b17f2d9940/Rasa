from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartSeries, ChartType


class AreaChart(BaseModel):
    type: Literal[ChartType.AREA] = ChartType.AREA
    metadata: ChartMetadata
    series: List[ChartSeries]
    stacked: bool = False
    normalize: bool = False
    transparency: Optional[float] = None
