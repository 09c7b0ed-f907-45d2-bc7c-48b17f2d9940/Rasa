from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from rasa_sdk.events import EventType  # type: ignore

from src.domain.dto.charts.area import AreaChart
from src.domain.dto.charts.bar import BarChart
from src.domain.dto.charts.box import BoxEntry, BoxPlot
from src.domain.dto.charts.histogram import Histogram, HistogramBin
from src.domain.dto.charts.line import LineChart
from src.domain.dto.charts.pie import PieChart, PieSlice
from src.domain.dto.charts.radar import RadarChart
from src.domain.dto.charts.scatter import ScatterPlot
from src.domain.dto.charts.types import ChartMetadata, ChartPoint, ChartSeries
from src.domain.dto.charts.waterfall import WaterfallChart, WaterfallStep

# Intentionally construct a plain payload dict for maximum flexibility in tests
from .. import command


@command("test_charts")
def test_charts(dispatcher: Any, tracker: Any, domain: Any, args: List[str], opts: Dict[str, Any]) -> List[EventType]:
    today = date.today()
    # Line
    points = [ChartPoint(x=(today - timedelta(days=2 - i)).isoformat(), y=float(i)) for i in range(3)]
    line = LineChart(metadata=ChartMetadata(title="Line"), series=[ChartSeries(name="L", data=points)])

    # Bar (more categories)
    bars = BarChart(
        metadata=ChartMetadata(title="Bar"),
        series=[
            ChartSeries(name="2019", data=[ChartPoint(x="A", y=3), ChartPoint(x="B", y=5), ChartPoint(x="C", y=2)]),
            ChartSeries(name="2020", data=[ChartPoint(x="A", y=4), ChartPoint(x="B", y=3), ChartPoint(x="C", y=6)]),
        ],
    )

    # Pie
    pie = PieChart(metadata=ChartMetadata(title="Pie"), data=[PieSlice(label="A", value=30), PieSlice(label="B", value=70)])

    # Histogram
    hist = Histogram(metadata=ChartMetadata(title="Hist"), data=[HistogramBin(range_start=0, range_end=1, frequency=5)], bin_count=1)

    # Box
    box = BoxPlot(metadata=ChartMetadata(title="Box"), data=[BoxEntry(name="A", q1=1, median=2, q3=3, min=0, max=4)])

    # Scatter (more points)
    scat = ScatterPlot(
        metadata=ChartMetadata(title="Scatter"),
        series=[ChartSeries(name="S", data=[ChartPoint(x=1, y=2), ChartPoint(x=2, y=1.5), ChartPoint(x=3, y=3.2)])],
    )

    # Radar (richer sample)
    radar_axes = ["Speed", "Agility", "Strength", "Endurance", "IQ"]
    r = RadarChart(
        metadata=ChartMetadata(title="Radar"),
        series=[
            ChartSeries(
                name="Player",
                data=[
                    ChartPoint(x="Speed", y=8),
                    ChartPoint(x="Agility", y=6),
                    ChartPoint(x="Strength", y=7),
                    ChartPoint(x="Endurance", y=5),
                    ChartPoint(x="IQ", y=9),
                ],
            ),
            ChartSeries(
                name="Peer Avg",
                data=[
                    ChartPoint(x="Speed", y=6),
                    ChartPoint(x="Agility", y=5),
                    ChartPoint(x="Strength", y=6),
                    ChartPoint(x="Endurance", y=6),
                    ChartPoint(x="IQ", y=7),
                ],
            ),
        ],
        axes=radar_axes,
    )

    # Waterfall
    wf = WaterfallChart(metadata=ChartMetadata(title="Waterfall"), data=[WaterfallStep(label="Start", value=100), WaterfallStep(label="End", value=100, is_total=True)])

    # Area (stacked-like sample with two series)
    area = AreaChart(
        metadata=ChartMetadata(title="Area"),
        series=[
            ChartSeries(name="Series 1", data=[ChartPoint(x=1, y=1), ChartPoint(x=2, y=2), ChartPoint(x=3, y=1.5)]),
            ChartSeries(name="Series 2", data=[ChartPoint(x=1, y=0.5), ChartPoint(x=2, y=1), ChartPoint(x=3, y=1.2)]),
        ],
    )

    charts: List[Dict[str, Any]] = [
        line.model_dump(exclude_none=True),
        bars.model_dump(exclude_none=True),
        pie.model_dump(exclude_none=True),
        hist.model_dump(exclude_none=True),
        box.model_dump(exclude_none=True),
        scat.model_dump(exclude_none=True),
        r.model_dump(exclude_none=True),
        wf.model_dump(exclude_none=True),
        area.model_dump(exclude_none=True),
    ]
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "charts": charts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    dispatcher.utter_message(json_message=payload)
    return []
