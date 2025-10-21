from typing import Optional

from pydantic import BaseModel


class MetricSummary(BaseModel):
    """Basic descriptive statistics for a metric."""

    metric: str
    count: Optional[int] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
