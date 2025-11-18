import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

from src.domain.dto.charts import union
from src.domain.dto.charts.types import ChartAxis, ChartMetadata, ChartPoint, ChartSeries
from src.domain.dto.response import VisualizationResponse
from src.domain.graphql.request import (
    DataOrigin,
    GraphQLQueryRequest,
    IntegerFilter,
    LogicalFilter,
    MetricRequest,
    SexFilter,
    StrokeFilter,
    TimePeriod,
)
from src.domain.graphql.ssot_enums import GroupByType, MetricType, Operator, SexType, StrokeType
from src.domain.langchain import schema as S
from src.domain.langchain.schema import AnalysisPlan, DistributionSpec, GroupByAge, GroupByCanonicalField, GroupByNIHSS, GroupBySex, GroupBySpec, GroupByStrokeType
from src.executors.graphql.client import GraphQLProxyClient
from src.shared.ssot_loader import get_metric_metadata
from src.util.coalesce import coalesce
from src.util.env import require_all_env

logger = logging.getLogger(__name__)

proxy_url, api_url = require_all_env("GRAPHQL_PROXY_URL", "GRAPHQL_API_URL")
client = GraphQLProxyClient(proxy_url=proxy_url, graphql_url=api_url)


# -----------------------------
# SSOT-driven helpers
# -----------------------------

METRIC_METADATA: Dict[str, Any] = get_metric_metadata()


def _get_metric_meta(metric_code: str) -> Dict[str, Any]:
    code = (metric_code or "").upper()
    meta: Dict[str, Any] = METRIC_METADATA.get(code) or {}
    return meta  # contains optional keys: display_name, unit, range_min, range_max, distribution_default_buckets, numeric{...}


def _derive_distribution_defaults(metric_code: str) -> tuple[int, int, int]:
    """Return (bins, min_value, max_value) using SSOT metadata with sensible fallbacks.

    Priority:
    - Use top-level promoted keys when present: range_min/range_max and distribution_default_buckets
    - Else use nested numeric block fields if present: numeric.default_buckets (and optional range_min/range_max if provided)
    - Else fallback to known safe ranges per metric; else general default (20, 0, 200)
    """
    meta = _get_metric_meta(metric_code)
    # bins
    bins_any: Any = meta.get("distribution_default_buckets")
    numeric_block: Dict[str, Any] = cast(Dict[str, Any], meta.get("numeric") or {})
    bins = bins_any or numeric_block.get("default_buckets") or 20
    # ranges
    rmin: Any = meta.get("range_min")
    rmax: Any = meta.get("range_max")
    if rmin is None or rmax is None:
        # Try nested numeric
        n: Dict[str, Any] = cast(Dict[str, Any], meta.get("numeric") or {})
        rmin = rmin if rmin is not None else n.get("range_min")
        rmax = rmax if rmax is not None else n.get("range_max")
    # Heuristic per well-known metrics if still missing
    if rmin is None or rmax is None:
        defaults: dict[str, tuple[int, int]] = {
            "AGE": (18, 95),
            "ADMISSION_NIHSS": (0, 42),
            "DTN": (0, 120),
        }
        if metric_code.upper() in defaults:
            rmin, rmax = defaults[metric_code.upper()]
        else:
            rmin = rmin if rmin is not None else 0
            rmax = rmax if rmax is not None else 200
    # Coerce to ints
    try:
        bins = int(bins)
    except Exception:
        bins = 20
    try:
        rmin = int(rmin)
        rmax = int(rmax)
    except Exception:
        rmin, rmax = 0, 200
    if rmin > rmax:
        rmin, rmax = rmax, rmin
    return bins, rmin, rmax


def _axis_from_meta(metric_code: str, x_min: int, x_max: int) -> tuple[ChartAxis, ChartAxis]:
    meta = _get_metric_meta(metric_code)
    display = meta.get("display_name") or metric_code.replace("_", " ").title()
    unit_any: Any = meta.get("unit")
    if unit_any is None:
        unit_any = cast(Dict[str, Any], meta.get("numeric") or {}).get("unit")
    unit: Optional[str] = cast(Optional[str], unit_any)
    x_label = f"{display} ({unit})" if unit else display
    x_axis = ChartAxis(label=x_label, min_value=x_min, max_value=x_max)
    y_axis = ChartAxis(label="Cases")
    return x_axis, y_axis


# -----------------------------
# Dimensional grouping helpers
# -----------------------------


class Dimension:
    """Represents one grouping dimension and how to enumerate categories/filters."""

    def __init__(self, spec: GroupBySpec):
        self.spec = spec
        self.kind = type(spec)

    def is_canonical(self) -> bool:
        return isinstance(self.spec, GroupByCanonicalField)

    def categories(self) -> Sequence[Any]:
        # Sex / StrokeType: use explicit categories or SSOT defaults
        if isinstance(self.spec, GroupBySex):
            return list(self.spec.categories or list(SexType))
        if isinstance(self.spec, GroupByStrokeType):
            return list(self.spec.categories or list(StrokeType))
        # Age / NIHSS buckets come from the plan
        if isinstance(self.spec, GroupByAge):
            return list(self.spec.buckets)
        if isinstance(self.spec, GroupByNIHSS):
            return list(self.spec.buckets)
        # Boolean/canonical/custom have no client-side enumeration by default
        return []

    def label_for(self, cat: Any) -> str:
        if isinstance(self.spec, GroupBySex):
            val = cat if isinstance(cat, SexType) else SexType(cat)
            return getattr(val, "value", str(val))
        if isinstance(self.spec, GroupByStrokeType):
            val = cat if isinstance(cat, StrokeType) else StrokeType(cat)
            return getattr(val, "value", str(val))
        if isinstance(self.spec, (GroupByAge, GroupByNIHSS)):
            return f"{cat.min}-{cat.max}"
        if isinstance(self.spec, GroupByCanonicalField):
            # Server-side grouped; label comes from response groupedBy
            return self.spec.field
        return str(cat)

    def filter_for(self, cat: Any) -> Optional[Any]:
        # Build per-category filter for client-side filtering dims
        if isinstance(self.spec, GroupBySex):
            val = cat if isinstance(cat, SexType) else SexType(cat)
            return SexFilter(sexType=val)
        if isinstance(self.spec, GroupByStrokeType):
            val = cat if isinstance(cat, StrokeType) else StrokeType(cat)
            return StrokeFilter(strokeType=val)
        if isinstance(self.spec, GroupByAge):
            return LogicalFilter(
                operator="AND",
                children=[
                    IntegerFilter(property="AGE", operator=Operator("GTE"), value=cat.min),
                    IntegerFilter(property="AGE", operator=Operator("LT"), value=cat.max),
                ],
            )
        if isinstance(self.spec, GroupByNIHSS):
            return LogicalFilter(
                operator="AND",
                children=[
                    IntegerFilter(property="ADMISSION_NIHSS", operator=Operator("GTE"), value=cat.min),
                    IntegerFilter(property="ADMISSION_NIHSS", operator=Operator("LT"), value=cat.max),
                ],
            )
        # Boolean / Canonical / Custom not implemented here
        return None


# -----------------------------
# Dimensional executor
# -----------------------------


def execute_plan(plan: AnalysisPlan, session_token: str) -> VisualizationResponse:
    """Sync wrapper that delegates to the async implementation with concurrency=1.

    - If no event loop is running, run the coroutine directly with asyncio.run.
    - If an event loop is already running, offload to a new thread and run a fresh loop there.
    """
    coro = execute_plan_async(plan, session_token, max_concurrency=1)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Running loop detected
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(asyncio.run, coro)
        return fut.result()


async def execute_plan_async(plan: AnalysisPlan, session_token: str, max_concurrency: int = 4) -> VisualizationResponse:
    """Async version that runs GraphQL requests concurrently.

    - Uses asyncio.to_thread to run the existing synchronous client in a thread pool.
    - Limits concurrency via a semaphore to avoid overloading the proxy/backend.
    - Produces one chart per canonical GroupBy (or one overall if none), matching sync behavior.
    """
    planCharts = coalesce(plan.charts, [])
    # Note: Statistical tests are not yet implemented; we log and ignore them for now
    if plan.statistical_tests:
        logger.warning("Statistical tests are defined in the plan but not implemented in this executor yet. They will be ignored.")
    response: VisualizationResponse = VisualizationResponse()

    sem = asyncio.Semaphore(max_concurrency)

    # --- helper: translate schema FilterNode -> GraphQL FilterType ---
    def _to_gql_filter(node: Optional[S.FilterNode]) -> Optional[Any]:
        if node is None:
            return None
        # Logical nodes
        if isinstance(node, S.AndFilter):
            children = [c for c in (node.and_ or [])]
            return LogicalFilter(operator="AND", children=[_to_gql_filter(c) for c in children if _to_gql_filter(c) is not None])  # type: ignore[arg-type]
        if isinstance(node, S.OrFilter):
            children = [c for c in (node.or_ or [])]
            return LogicalFilter(operator="OR", children=[_to_gql_filter(c) for c in children if _to_gql_filter(c) is not None])  # type: ignore[arg-type]
        if isinstance(node, S.NotFilter):
            child = _to_gql_filter(node.not_)
            if child is None:
                return None
            return LogicalFilter(operator="NOT", children=[child])
        # Leaf nodes
        if isinstance(node, S.AgeFilter):
            return IntegerFilter(property="AGE", operator=Operator(node.operator), value=int(node.value))
        if isinstance(node, S.NIHSSFilter):
            return IntegerFilter(property="ADMISSION_NIHSS", operator=Operator(node.operator), value=int(node.value))
        if isinstance(node, S.SexFilter):
            return SexFilter(sexType=SexType(node.value))
        if isinstance(node, S.StrokeFilter):
            return StrokeFilter(strokeType=StrokeType(node.value))
        if isinstance(node, S.BooleanFilter):
            # Boolean property filter not yet wired in this executor
            return None
        if type(node).__name__ == "DateFilter":
            from src.domain.graphql.request import DateFilter as GQLDateFilter

            return GQLDateFilter(property="ADMISSION_DATE", operator=Operator(node.operator), value=node.value)
        return None

    async def run_one(
        req: GraphQLQueryRequest,
        label_parts: List[str],
        include_metric_alias: bool,
        group_by_field: Optional[str],
    ) -> List[ChartSeries]:
        logger.debug(
            "[test2] Executing GraphQL: groupBy=%s labels=%s",
            group_by_field,
            " - ".join([p for p in label_parts if p]) or "(none)",
        )
        async with sem:
            query_str = req.to_graphql_string()
            resp = await asyncio.to_thread(client.query, query_str, session_token)
        series: List[ChartSeries] = []
        if resp is None:
            logger.error(
                "[test2] GraphQL returned None (likely proxy error). groupBy=%s labels=%s",
                group_by_field,
                " - ".join([p for p in label_parts if p]) or "(none)",
            )
            return series
        if getattr(resp, "errors", None):
            logger.error("[test2] GraphQL errors: %s", resp.errors)
        if (x := resp) and (x := x.data) and (x := x.get_metrics) and (x := x.metrics):
            for metricName, metric in x.items():
                for kpi in metric.kpi_group:
                    if not kpi.kpi1.d1:
                        continue
                    server_label = kpi.grouped_by.group_item_name if kpi.grouped_by else None
                    parts = [p for p in label_parts if p]
                    if server_label:
                        parts.append(server_label)
                    if include_metric_alias:
                        parts.append(metricName)
                    series_name = " - ".join(parts) if parts else metricName
                    series.append(
                        ChartSeries(
                            name=series_name,
                            data=[ChartPoint(x=x, y=y) for x, y in zip(kpi.kpi1.d1.edges, kpi.kpi1.d1.case_count)],
                        )
                    )
        else:
            # Provide clarity when response contains no metrics
            try:
                has_data = bool(getattr(resp, "data", None))
            except Exception:
                has_data = False
            logger.debug(
                "[test2] No metrics in response. has_data=%s groupBy=%s labels=%s",
                has_data,
                group_by_field,
                " - ".join([p for p in label_parts if p]) or "(none)",
            )
        return series

    for planChart in planCharts:
        if planChart.chart_type != "LINE":
            logger.warning("Only LINE charts are implemented in test2 async; got %s", planChart.chart_type)
            continue

        metric_requests: List[MetricRequest] = []
        # Use SSOT metadata for defaults when distribution not provided
        derived_axes: Optional[tuple[ChartAxis, ChartAxis]] = None
        for metric in planChart.metrics:
            if metric.distribution is not None:
                distribution = metric.distribution
            else:
                bins, rmin, rmax = _derive_distribution_defaults(metric.metric)
                distribution = DistributionSpec(num_buckets=bins, min_value=rmin, max_value=rmax)
                # Prepare axes from metadata for single-metric charts
                if len(planChart.metrics) == 1:
                    derived_axes = _axis_from_meta(metric.metric, rmin, rmax)
            metric_requests.append(MetricRequest(metricType=MetricType(metric.metric)).with_distribution(distribution.num_buckets, distribution.min_value, distribution.max_value))

        # Use chart-level group_by
        collected_groups: List[GroupBySpec] = list(coalesce(planChart.group_by, []))

        # Deduplicate group specs while preserving order; do not normalize or merge.
        seen: set[GroupBySpec] = set()
        uniq_groups: List[GroupBySpec] = []
        for g in collected_groups:
            if g not in seen:
                seen.add(g)
                uniq_groups.append(g)
        dims: List[Dimension] = [Dimension(g) for g in uniq_groups]

        # Collect all canonical dims; we'll produce one chart per canonical dim.
        server_dims: List[Optional[Dimension]] = [d for d in dims if d.is_canonical()]
        if not server_dims:
            server_dims = [None]

        for server_dim in server_dims:
            filter_dims: List[Dimension] = [d for d in dims if d is not server_dim]

            # Enumerate combos of filter dims (Cartesian product); empty product yields one empty combo
            filter_categories: List[Sequence[Any]] = []
            for d in filter_dims:
                cats = d.categories()
                if not cats:
                    logger.warning("Skipping non-enumerable filter dimension: %s", d.kind.__name__)
                    continue
                filter_categories.append(cats)

            if not filter_categories:
                combos_list: List[Tuple[Any, ...]] = [tuple()]  # single empty combo
            else:
                combos_list = list(product(*filter_categories))

            tasks: List[asyncio.Task[List[ChartSeries]]] = []
            include_metric_alias = len(planChart.metrics) > 1
            combo_count = len(combos_list)
            gb_field = server_dim.spec.field if server_dim and isinstance(server_dim.spec, GroupByCanonicalField) else None
            logger.debug("[test2] combos=%d groupBy=%s", combo_count, gb_field)

            chart_filter = _to_gql_filter(coalesce(planChart.filters, None))

            for combo in combos_list:
                combo_filters: List[Any] = []
                label_parts: List[str] = []
                for dim, cat in zip(filter_dims, combo):
                    f = dim.filter_for(cat)
                    if f is not None:
                        combo_filters.append(f)
                    label_parts.append(dim.label_for(cat))

                # Merge chart-level filter with combo filters
                if len(combo_filters) == 0:
                    case_filter: Optional[Any] = chart_filter
                elif len(combo_filters) == 1 and chart_filter is None:
                    case_filter = combo_filters[0]
                else:
                    merged_children: List[Any] = []
                    if chart_filter is not None:
                        merged_children.append(chart_filter)
                    merged_children.extend(combo_filters)
                    case_filter = LogicalFilter(operator="AND", children=merged_children)  # type: ignore[arg-type]

                req = GraphQLQueryRequest(
                    metrics=metric_requests,
                    timePeriod=TimePeriod(startDate="2022-01-01", endDate="2025-12-31"),
                    dataOrigin=DataOrigin(providerGroupId=[1]),
                    includeGeneralStats=True,
                    caseFilter=case_filter,
                    groupBy=(GroupByType(server_dim.spec.field) if server_dim and isinstance(server_dim.spec, GroupByCanonicalField) else None),
                )

                tasks.append(asyncio.create_task(run_one(req, label_parts, include_metric_alias, gb_field)))

            all_series: List[ChartSeries] = []
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=False)
                for lst in results:
                    all_series.extend(lst)

            # Build chart title suffix if multiple canonical charts
            suffix = f" (by {server_dim.spec.field})" if server_dim and isinstance(server_dim.spec, GroupByCanonicalField) else ""
            if not all_series:
                logger.warning(
                    "[test2] No series generated for chart '%s'%s. This often indicates a backend error or empty results.",
                    planChart.title or "Line Chart",
                    suffix,
                )
            # Build improved metadata: title and axes from SSOT when possible
            if planChart.title:
                title_text = planChart.title + suffix
            else:
                # Prefer a descriptive title from first metric display name
                first_metric_code = planChart.metrics[0].metric if planChart.metrics else ""
                display_name = _get_metric_meta(first_metric_code).get("display_name") or first_metric_code or "Line Chart"
                title_text = f"{display_name} Distribution" + suffix

            meta_kwargs: dict[str, Any] = {
                "title": title_text,
                "description": planChart.description,
            }
            if derived_axes is not None:
                meta_kwargs["x_axis"], meta_kwargs["y_axis"] = derived_axes

            visChart: union.LineChart = union.LineChart(
                metadata=ChartMetadata(**meta_kwargs),
                series=all_series,
            )
            response.charts.append(visChart)

    return response
