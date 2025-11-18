"""Dynamic SSOT-based enums for GraphQL models.

Refactored to use central loader (src/shared/ssot_loader.py) for:
 - Cached YAML access
 - Single canonical source of enum creation
 - Future metadata access (e.g., labels, units) via get_metric_metadata()
"""

from enum import Enum
from typing import TYPE_CHECKING

from src.shared.ssot_loader import create_enum, get_metric_metadata

if TYPE_CHECKING:  # Type stubs (match runtime signature: str subclass of Enum)

    class SexType(str, Enum): ...

    class StrokeType(str, Enum): ...

    class MetricType(str, Enum): ...

    class GroupByType(str, Enum): ...

    class BooleanPropertyType(str, Enum): ...

    class Operator(str, Enum): ...


# Create dynamic enums from SSOT via unified loader
SexType = create_enum("SexType", "SexType.yml")
StrokeType = create_enum("StrokeType", "StrokeType.yml")
MetricType = create_enum("MetricType", "MetricType.yml")
GroupByType = create_enum("GroupByType", "GroupByType.yml")
BooleanPropertyType = create_enum("BooleanPropertyType", "BooleanType.yml")
Operator = create_enum("Operator", "OperatorType.yml")

# Expose metric metadata (optional consumers can import)
MetricMetadata = get_metric_metadata()

__all__ = [
    "SexType",
    "StrokeType",
    "MetricType",
    "GroupByType",
    "BooleanPropertyType",
    "Operator",
    "MetricMetadata",
]

if __name__ == "__main__":  # Diagnostic output
    print("🔄 Dynamic SSOT Enum System (Unified Loader)")
    print("=" * 40)
    print(f"✅ SexType: {len(list(SexType))} values")  # type: ignore[arg-type]
    print(f"✅ StrokeType: {len(list(StrokeType))} values")  # type: ignore[arg-type]
    print(f"✅ MetricType: {len(list(MetricType))} values (metadata entries: {len(MetricMetadata)})")  # type: ignore[arg-type]
    sample_metrics = list(MetricType)[:3]  # type: ignore[arg-type]
    print(f"   Sample metrics: {[m.value for m in sample_metrics]}")
    print(f"✅ GroupByType: {len(list(GroupByType))} values")  # type: ignore[arg-type]
    print(f"✅ BooleanPropertyType: {len(list(BooleanPropertyType))} values")  # type: ignore[arg-type]
    print(f"✅ Operator: {len(list(Operator))} values")  # type: ignore[arg-type]
    # Show one metadata example if available
    for sm in sample_metrics:
        meta = MetricMetadata.get(sm.value)
        if meta:
            print(f"   • {sm.value} meta keys: {list(meta.keys())}")
    print("\n🎯 Enums & metadata now via shared loader.")
