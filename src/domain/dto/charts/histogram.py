from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartType


class HistogramBin(BaseModel):
    range_start: float
    range_end: float
    frequency: float
    density: Optional[float] = None


class Histogram(BaseModel):
    type: Literal[ChartType.HISTOGRAM] = ChartType.HISTOGRAM
    metadata: ChartMetadata
    data: List[HistogramBin]
    bin_count: int
    bin_width: Optional[float] = None
    cumulative: bool = False
