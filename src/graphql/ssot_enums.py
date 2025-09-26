"""
Dynamic SSOT-based enums for GraphQL models.
Loads enum values directly from SSOT YAML files at runtime.
"""

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    # Type stubs for static analysis
    class SexType(str, Enum): ...

    class StrokeType(str, Enum): ...

    class MetricType(str, Enum): ...

    class GroupByType(str, Enum): ...

    class BooleanPropertyType(str, Enum): ...

    class Operator(str, Enum): ...


def load_ssot_values(yaml_filename: str) -> list[str]:
    """Load canonical enum values from SSOT YAML file"""
    ssot_path = Path(__file__).parent.parent / "shared" / "SSOT" / yaml_filename

    with open(ssot_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return [item["canonical"] for item in data if "canonical" in item]


def create_dynamic_enum(name: str, yaml_filename: str) -> Any:
    """Create a dynamic enum class from SSOT YAML file"""
    values = load_ssot_values(yaml_filename)

    # Create the enum class using Enum functional API
    # This creates a proper enum that inherits from str
    DynamicEnum = Enum(name, [(value, value) for value in values], type=str)

    return DynamicEnum


# Create dynamic enums from SSOT
SexType = create_dynamic_enum("SexType", "SexType.yml")
StrokeType = create_dynamic_enum("StrokeType", "StrokeType.yml")
MetricType = create_dynamic_enum("MetricType", "KPIType.yml")
GroupByType = create_dynamic_enum("GroupByType", "GroupByType.yml")
BooleanPropertyType = create_dynamic_enum("BooleanPropertyType", "BooleanType.yml")
Operator = create_dynamic_enum("Operator", "ComparisonType.yml")


# For backwards compatibility and type hints
__all__ = ["SexType", "StrokeType", "MetricType", "GroupByType", "BooleanPropertyType", "Operator"]


if __name__ == "__main__":
    print("🔄 Dynamic SSOT Enum System")
    print("=" * 40)

    # Use getattr to avoid type checker issues with dynamic enums
    sex_enum = globals()["SexType"]
    print(f"✅ SexType: {len(sex_enum)} values")
    print(f"   Values: {[s.value for s in sex_enum]}")

    stroke_enum = globals()["StrokeType"]
    print(f"✅ StrokeType: {len(stroke_enum)} values")
    print(f"   Sample: {list(stroke_enum)[:3]}...")

    metric_enum = globals()["MetricType"]
    print(f"✅ MetricType: {len(metric_enum)} values")
    print(f"   Sample: {list(metric_enum)[:3]}...")

    group_enum = globals()["GroupByType"]
    print(f"✅ GroupByType: {len(group_enum)} values")

    bool_enum = globals()["BooleanPropertyType"]
    print(f"✅ BooleanPropertyType: {len(bool_enum)} values")

    op_enum = globals()["Operator"]
    print(f"✅ Operator: {len(op_enum)} values")
    print(f"   Values: {[op.value for op in op_enum]}")

    print("\n🎯 ALL enums now from SSOT YAML files!")
    print("   No hardcoded values - everything dynamically loaded")
