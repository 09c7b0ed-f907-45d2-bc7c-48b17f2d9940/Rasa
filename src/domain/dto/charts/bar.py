from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartSeries, ChartType


class BarChart(BaseModel):
    type: Literal[ChartType.BAR] = ChartType.BAR
    metadata: ChartMetadata
    series: List[ChartSeries]
    orientation: Literal["vertical", "horizontal"] = "vertical"
    stacked: bool = False
    bar_width: Optional[float] = None
