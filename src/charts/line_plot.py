from typing import List, Optional

from pydantic import BaseModel


class LinePlotSeries(BaseModel):
    label: str
    values: List[float]


class LinePlot(BaseModel):
    chartTitle: str
    xAxisLabel: str
    yAxisLabel: str
    bins: List[float]
    series: List[LinePlotSeries]
    grouped: bool = True
    sourceMetricId: Optional[str] = None
