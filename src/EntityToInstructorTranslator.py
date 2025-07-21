import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from src.instructor.filter_models import (
    AgeFilter,
    BooleanFilter,
    BooleanProperty,
    ComparisonProperty,
    DateFilter,
    FilterResponse,
    LogicalFilter,
    NIHSSFilter,
    OperatorProperty,
    SexFilter,
    SexProperty,
    StrokeFilter,
    StrokeProperty,
)
from src.instructor.metric_models import (
    KPI,
    Distribution,
    GroupProperty,
    Metric,
    MetricResponse,
    MetricsCollection,
)
from src.instructor.models import MetricCalculatorResponse

logger = logging.getLogger(__name__)


@dataclass
class ComplexityCheck:
    is_too_complex: bool
    reason: str
    confidence: float


class EntityToInstructorTranslator:
    """Translates Rasa entities to Instructor models"""

    def __init__(self):
        self.exclusion_keywords = ["exclude", "excluding", "but not", "except", "without", "not", "dont", "don't", "remove", "skip"]

    def is_too_complex_for_rules(self, entities: List[Dict[str, Any]], user_message: str, rasa_confidence: float = 1.0) -> ComplexityCheck:
        """Simple check: is this too complex for rule-based handling?"""

        # 1. Rasa has low confidence
        if rasa_confidence < 0.6:
            return ComplexityCheck(True, "Low Rasa confidence", rasa_confidence)

        # 2. No entities extracted (Rasa didn't understand anything)
        if not entities:
            return ComplexityCheck(True, "No entities extracted", 0.0)

        # 3. No KPI found (we need at least one metric)
        has_kpi = any(e.get("entity") == "kpi" for e in entities)
        if not has_kpi:
            return ComplexityCheck(True, "No metrics/KPIs identified", 0.3)

        # 4. Too many logical operators (complex query structure)
        logical_words = ["and", "or", "but", "except", "excluding", "not", "however", "although"]
        logical_count = sum(1 for word in logical_words if word in user_message.lower())
        if logical_count > 2:
            return ComplexityCheck(True, f"Too many logical operators ({logical_count})", 0.4)

        # 5. Multiple negations (hard to parse with rules)
        negation_words = ["not", "dont", "don't", "never", "no", "exclude", "without"]
        negation_count = sum(1 for word in negation_words if word in user_message.lower())
        if negation_count > 1:
            return ComplexityCheck(True, f"Multiple negations ({negation_count})", 0.4)

        # 6. Query is very long (likely complex)
        word_count = len(user_message.split())
        if word_count > 25:
            return ComplexityCheck(True, f"Query too long ({word_count} words)", 0.5)

        # 7. Contains ambiguous references
        ambiguous_words = ["it", "that", "this", "them", "those", "they"]
        if any(word in user_message.lower().split() for word in ambiguous_words):
            return ComplexityCheck(True, "Contains ambiguous references", 0.6)

        # 8. Unknown entities (entities we can't map)
        unmappable_count = 0
        for entity in entities:
            if not self._can_map_entity(entity):
                unmappable_count += 1

        if unmappable_count > len(entities) * 0.3:  # More than 30% unmappable
            return ComplexityCheck(True, f"Too many unmappable entities ({unmappable_count}/{len(entities)})", 0.5)

        # If we made it here, it's probably handleable with rules
        return ComplexityCheck(False, "Query appears suitable for rule-based handling", rasa_confidence)

    def _can_map_entity(self, entity: Dict[str, Any]) -> bool:
        """Quick check if we can map this entity to our models"""
        entity_type = entity.get("entity")
        value = entity.get("value", "")

        try:
            if entity_type == "kpi":
                KPI(value)
            elif entity_type == "sex":
                SexProperty(value)
            elif entity_type == "stroke_type":
                StrokeProperty(value)
            elif entity_type == "group_by":
                GroupProperty(value)
            elif entity_type == "boolean_type":
                BooleanProperty(value)
            elif entity_type in ["age", "nihss"]:
                int(value)
            # Add other entity types as needed
            return True
        except (ValueError, TypeError):
            return False

    def translate(self, entities: List[Dict[str, Any]], user_message: str) -> MetricCalculatorResponse:
        """Main translation method"""

        # Determine if exclusion context exists
        is_exclusion_context = self._has_exclusion_context(user_message)

        # Extract and organize entities
        organized = self._organize_entities(entities)

        # Build filters
        filter_response = self._build_filters(organized, is_exclusion_context)

        # Build metrics
        metric_response = self._build_metrics(organized)

        return MetricCalculatorResponse(FilterResponse=filter_response, MetricResponse=metric_response)

    def _has_exclusion_context(self, message: str) -> bool:
        """Check if message contains exclusion keywords"""
        return any(keyword in message.lower() for keyword in self.exclusion_keywords)

    def _organize_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize entities by type and role"""
        organized: Dict[str, Any] = {
            "kpis": [],
            "sex_filters": [],
            "stroke_types": [],
            "boolean_filters": [],
            "chart_type": None,
            "group_by": None,
            "age_range": {},
            "date_range": {},
            "nihss_range": {},
        }

        for entity in entities:
            entity_type = entity.get("entity")
            value = entity.get("value")
            role = entity.get("role")

            if value is not None:
                if entity_type == "kpi":
                    organized["kpis"].append(value)
                elif entity_type == "sex":
                    organized["sex_filters"].append(value)
                elif entity_type == "stroke_type":
                    organized["stroke_types"].append(value)
                elif entity_type == "boolean_type":
                    organized["boolean_filters"].append(value)
                elif entity_type == "chart_type":
                    organized["chart_type"] = value
                elif entity_type == "group_by":
                    organized["group_by"] = value
                elif entity_type == "age" and role:
                    organized["age_range"][role] = int(value)
                elif entity_type == "date" and role:
                    organized["date_range"][role] = value
                elif entity_type == "nihss" and role:
                    organized["nihss_range"][role] = int(value)

        return organized

    def _build_filters(self, organized: Dict[str, Any], is_exclusion: bool) -> FilterResponse:
        """Build filter response from organized entities"""
        filters: List[Any] = []

        # Age filters
        age_range = organized.get("age_range", {})
        if "lower" in age_range:
            filters.append(AgeFilter(operator=ComparisonProperty.GreaterOrEqual, value=age_range["lower"]))
        if "upper" in age_range:
            filters.append(AgeFilter(operator=ComparisonProperty.LessOrEqual, value=age_range["upper"]))

        # NIHSS filters
        nihss_range = organized.get("nihss_range", {})
        if "lower" in nihss_range:
            filters.append(NIHSSFilter(operator=ComparisonProperty.GreaterOrEqual, value=nihss_range["lower"]))
        if "upper" in nihss_range:
            filters.append(NIHSSFilter(operator=ComparisonProperty.LessOrEqual, value=nihss_range["upper"]))

        # Date filters
        date_range = organized.get("date_range", {})
        if "lower" in date_range:
            filters.append(DateFilter(operator=ComparisonProperty.GreaterOrEqual, value=date_range["lower"]))
        if "upper" in date_range:
            filters.append(DateFilter(operator=ComparisonProperty.LessOrEqual, value=date_range["upper"]))

        # Sex filters
        sex_filters = organized.get("sex_filters", [])
        if sex_filters:
            sex_filter_objects: List[SexFilter] = []
            for sex in sex_filters:
                try:
                    sex_prop = SexProperty(sex)
                    sex_filter_objects.append(SexFilter(value=sex_prop))
                except ValueError:
                    logger.warning(f"Unknown sex value: {sex}")

            if sex_filter_objects:
                if len(sex_filter_objects) == 1:
                    filters.extend(sex_filter_objects)
                else:
                    filters.append(LogicalFilter(operator=OperatorProperty.OR, children=list(sex_filter_objects)))

        # Stroke type filters
        stroke_types = organized.get("stroke_types", [])
        if stroke_types:
            stroke_filter_objects: List[StrokeFilter] = []
            for stroke in stroke_types:
                try:
                    stroke_prop = StrokeProperty(stroke)
                    stroke_filter_objects.append(StrokeFilter(value=stroke_prop))
                except ValueError:
                    logger.warning(f"Unknown stroke type: {stroke}")

            if stroke_filter_objects:
                if is_exclusion:
                    # Exclude these stroke types
                    for stroke_filter in stroke_filter_objects:
                        filters.append(LogicalFilter(operator=OperatorProperty.NOT, children=[stroke_filter]))
                else:
                    # Include these stroke types
                    if len(stroke_filter_objects) == 1:
                        filters.extend(stroke_filter_objects)
                    else:
                        filters.append(LogicalFilter(operator=OperatorProperty.OR, children=list(stroke_filter_objects)))

        # Boolean filters
        boolean_filters = organized.get("boolean_filters", [])
        for boolean_val in boolean_filters:
            try:
                bool_prop = BooleanProperty(boolean_val)
                filters.append(
                    BooleanFilter(
                        property=bool_prop,
                        value=True,  # Assuming presence means True
                    )
                )
            except ValueError:
                logger.warning(f"Unknown boolean property: {boolean_val}")

        # Combine all filters
        if not filters:
            return FilterResponse(logicalFilter=None)
        elif len(filters) == 1:
            return FilterResponse(logicalFilter=LogicalFilter(operator=OperatorProperty.AND, children=filters))
        else:
            return FilterResponse(logicalFilter=LogicalFilter(operator=OperatorProperty.AND, children=filters))

    def _build_metrics(self, organized: Dict[str, Any]) -> MetricResponse:
        """Build metric response from organized entities"""
        kpis = organized.get("kpis", [])
        group_by = organized.get("group_by")

        if not kpis:
            return MetricResponse(metricsCollection=None)

        metrics: List[Metric] = []
        for kpi_value in kpis:
            try:
                kpi_enum = KPI(kpi_value)

                # Determine if we should add stats or distribution
                stats = False
                distribution = None

                # For certain KPIs, add distribution by default
                if kpi_enum in [KPI.Age, KPI.Dtn, KPI.Dido, KPI.AdmissionNihss, KPI.Dti]:
                    # Set reasonable defaults based on KPI type
                    if kpi_enum == KPI.Age:
                        distribution = Distribution(bin_count=10, lower=0, upper=100)
                    elif kpi_enum == KPI.Dtn:
                        distribution = Distribution(bin_count=12, lower=0, upper=120)
                    elif kpi_enum == KPI.Dido:
                        distribution = Distribution(bin_count=20, lower=0, upper=200)
                    elif kpi_enum == KPI.AdmissionNihss:
                        distribution = Distribution(bin_count=21, lower=0, upper=21)
                    elif kpi_enum == KPI.Dti:
                        distribution = Distribution(bin_count=10, lower=0, upper=100)

                    stats = True  # Also include stats for numeric KPIs

                metrics.append(Metric(kpi=kpi_enum, stats=stats, distribution=distribution))

            except ValueError:
                logger.warning(f"Unknown KPI: {kpi_value}")

        # Handle group_by
        group_by_enum = None
        if group_by:
            try:
                group_by_enum = GroupProperty(group_by)
            except ValueError:
                logger.warning(f"Unknown group_by property: {group_by}")

        if metrics:
            return MetricResponse(metricsCollection=MetricsCollection(metrics=metrics, group_by=group_by_enum))
        else:
            return MetricResponse(metricsCollection=None)
