from typing import List, Literal, Optional

from pydantic import BaseModel

from .types import ChartMetadata, ChartType


class PieSlice(BaseModel):
    label: str
    value: float
    color: Optional[str] = None


class PieChart(BaseModel):
    """Pie chart DTO - circular charts"""

    type: Literal[ChartType.PIE] = ChartType.PIE
    metadata: ChartMetadata
    data: List[PieSlice]
    show_percentages: bool = True
    donut: bool = False  # True for donut chart
    inner_radius: Optional[float] = None
