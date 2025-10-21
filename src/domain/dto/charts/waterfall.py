from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartType


class WaterfallStep(BaseModel):
    label: str
    value: float
    is_total: Optional[bool] = None
    is_positive: Optional[bool] = None


class WaterfallChart(BaseModel):
    """Waterfall chart DTO - bridge/cascade charts"""

    type: Literal[ChartType.WATERFALL] = ChartType.WATERFALL
    metadata: ChartMetadata
    data: List[WaterfallStep]
    show_connectors: bool = True
    start_value: Optional[float] = None
