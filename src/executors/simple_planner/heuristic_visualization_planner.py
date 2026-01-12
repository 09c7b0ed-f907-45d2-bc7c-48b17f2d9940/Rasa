from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, cast

from src.domain.langchain.schema import AnalysisPlan, ChartSpec, GroupBySex, GroupByStrokeType, GroupByTime, MetricSpec, TimeWindow
from src.shared.ssot_loader import get_metric_metadata

logger = logging.getLogger(__name__)


# Build a lightweight synonym index for metrics from SSOT so we can
# recognise more than just DTN in simple queries.
_METRIC_META: Dict[str, Dict[str, Any]] = get_metric_metadata()


def _build_metric_synonym_index() -> Dict[str, Set[str]]:
    index: Dict[str, Set[str]] = {}
    for code, meta in _METRIC_META.items():
        code_up = (code or "").upper()
        names: Set[str] = set()

        # Canonical code as token.
        if code_up:
            names.add(code_up.lower())

        # Display name and synonyms.
        display = meta.get("display_name")
        if isinstance(display, str) and display.strip():
            names.add(display.strip().lower())
        syn_any = meta.get("synonyms")
        if isinstance(syn_any, list):
            syn_list = cast(List[Any], syn_any)
            for s in syn_list:
                if isinstance(s, str) and s.strip():
                    names.add(s.strip().lower())

        if names:
            index[code_up] = names
    return index


_METRIC_SYNONYMS: Dict[str, Set[str]] = _build_metric_synonym_index()


def _tokenise(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def _find_metric_from_text(q_lower: str) -> Optional[str]:
    tokens = _tokenise(q_lower)
    candidates: Set[str] = set()

    for code, names in _METRIC_SYNONYMS.items():
        for name in names:
            if not name:
                continue
            if " " in name:
                # Multi-word synonym: simple substring match.
                if name in q_lower:
                    candidates.add(code)
                    break
            else:
                # Single token: require token match to avoid spurious substring hits.
                if name in tokens:
                    candidates.add(code)
                    break

    if len(candidates) == 1:
        return next(iter(candidates))
    return None


class HeuristicVisualizationPlanner:
    """Lightweight, non-LLM planner for simple visualization requests.

    This is intentionally conservative: it only handles very simple patterns
    (e.g. "show a line chart of DTN"). When it cannot confidently interpret
    the request, it returns None so the caller can fall back to the LangChain
    planner.
    """

    @staticmethod
    def try_plan(question: str, entities: Dict[str, Any], language: Optional[str]) -> Optional[AnalysisPlan]:
        text = (question or "").strip()
        if not text:
            return None

        q_lower = text.lower()

        # Reject obviously complex requests so we defer to the LLM planner.
        # We *allow* certain simple "by X" patterns that we know how to
        # handle (e.g. "by sex", "by stroke type"). Any other use of
        # "by", or markers like "vs"/"compare", is treated as complex.
        complexity_markers = [" vs ", " versus ", " compare ", " correlation", " impact ", " per "]
        if any(marker in q_lower for marker in complexity_markers):
            return None

        # 1) Detect chart type from simple keywords. Default to LINE.
        chart_type = "LINE"
        if "bar chart" in q_lower or "bar graph" in q_lower:
            chart_type = "BAR"
        elif "area chart" in q_lower or "area graph" in q_lower:
            chart_type = "AREA"
        elif "histogram" in q_lower or "distribution" in q_lower:
            chart_type = "HISTOGRAM"
        elif "line chart" in q_lower or "line graph" in q_lower or "trend" in q_lower:
            chart_type = "LINE"

        # 2) Detect a single metric.
        metric_code: Optional[str] = None

        # a) Check entities for a metric-like code.
        metric_entity_keys = ["metric", "metric_code", "metric_type"]
        for key in metric_entity_keys:
            if key in entities and isinstance(entities[key], str):
                metric_code = entities[key].upper()
                break

        # b) Fallback to simple keyword/synonym match using SSOT metadata.
        if metric_code is None:
            metric_code = _find_metric_from_text(q_lower)

        if metric_code is None:
            # Not a simple, known metric → let the LangChain planner handle it.
            return None

        # 3) Optional simple group_by patterns we know how to handle.
        group_by: list[Any] = []

        # "by sex" / "by gender" → GroupBySex
        if "by sex" in q_lower or "by gender" in q_lower:
            try:
                group_by.append(GroupBySex())
            except Exception:
                pass

        # "by stroke type" / "by stroke" → GroupByStrokeType
        if "by stroke type" in q_lower or "by stroke" in q_lower:
            try:
                group_by.append(GroupByStrokeType())
            except Exception:
                pass

        # "over time" / "time series" / "over the last" → GroupByTime (last 6 months by month).
        if "over time" in q_lower or "time series" in q_lower or "over the last" in q_lower:
            try:
                window = TimeWindow(last_n=6, unit="MONTH")
                group_by.append(GroupByTime(grain="MONTH", window=window, include_partial=True))
            except Exception:
                pass

        # If the user mentioned "by" but we didn't recognise any safe
        # group_by pattern, treat it as complex and let the LLM handle it.
        if " by " in q_lower and not group_by:
            return None

        try:
            metric_spec = MetricSpec(metric=metric_code)
            chart_spec = ChartSpec(chart_type=chart_type, metrics=[metric_spec], group_by=group_by or None)
            plan = AnalysisPlan(charts=[chart_spec], statistical_tests=None)
        except Exception as exc:
            logger.debug("HeuristicVisualizationPlanner failed to build plan for question %r: %s", question, exc)
            return None

        logger.info(
            "HeuristicVisualizationPlanner produced a simple plan for question %r (metric=%s, chart_type=%s, group_by=%s)",
            question,
            metric_code,
            chart_type,
            group_by,
        )
        return plan
