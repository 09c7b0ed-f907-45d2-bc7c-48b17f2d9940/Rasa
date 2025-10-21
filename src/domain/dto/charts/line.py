from typing import List, Literal

from pydantic import BaseModel

from .types import ChartMetadata, ChartSeries, ChartType


class LineChart(BaseModel):
    type: Literal[ChartType.LINE] = ChartType.LINE
    metadata: ChartMetadata
    series: List[ChartSeries]
    smooth: bool = False
    show_points: bool = True
    fill_area: bool = False
