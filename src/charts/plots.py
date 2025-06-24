from typing import List

from pydantic import BaseModel

from src.charts.box_plot import BoxPlot
from src.charts.line_plot import LinePlot


class PlotCollection(BaseModel):
    linePlots: List[LinePlot] = []
    boxPlots: List[BoxPlot] = []
