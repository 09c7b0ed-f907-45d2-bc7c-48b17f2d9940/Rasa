from pydantic import BaseModel

import src.instructor.filter_models as fm
import src.instructor.metric_models as mr
from src.instructor.filter_models import *
from src.instructor.metric_models import *


class MetricCalculatorResponse(BaseModel):
    FilterResponse: fm.FilterResponse
    MetricResponse: mr.MetricResponse
