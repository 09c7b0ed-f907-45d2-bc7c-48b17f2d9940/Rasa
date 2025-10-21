from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartType


class BoxEntry(BaseModel):
    name: str
    q1: float
    median: float
    q3: float
    min: float
    max: float
    outliers: Optional[List[float]] = None


class BoxPlot(BaseModel):
    type: Literal[ChartType.BOX] = ChartType.BOX
    metadata: ChartMetadata
    data: List[BoxEntry]
    show_outliers: bool = True
    notched: bool = False
