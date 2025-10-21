from typing import Union

from .area import AreaChart
from .bar import BarChart
from .box import BoxPlot
from .histogram import Histogram
from .line import LineChart
from .pie import PieChart
from .radar import RadarChart
from .scatter import ScatterPlot
from .waterfall import WaterfallChart

ChartDTO = Union[
    LineChart,
    BarChart,
    BoxPlot,
    Histogram,
    ScatterPlot,
    PieChart,
    RadarChart,
    WaterfallChart,
    AreaChart,
]
