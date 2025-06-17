from typing import List, Optional

from pydantic import BaseModel


class BoxPlotSeries(BaseModel):
    label: str
    min: Optional[float]
    q1: float
    median: float
    q3: float
    max: Optional[float]
    mean: Optional[float] = None
    ci_mean: Optional[List[float]] = None
    ci_median: Optional[List[float]] = None


class BoxPlot(BaseModel):
    chartTitle: str
    yAxisLabel: str
    series: List[BoxPlotSeries]
    sourceMetricId: Optional[str] = None
