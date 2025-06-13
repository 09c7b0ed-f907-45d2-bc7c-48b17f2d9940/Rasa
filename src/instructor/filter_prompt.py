from typing import Dict

from filter_models import (
    AgeFilter,
    BooleanFilter,
    BooleanProperty,
    ComparisonProperty,
    DateFilter,
    LogicalFilter,
    NIHSSFilter,
    OperatorProperty,
    SexFilter,
    SexProperty,
    StrokeFilter,
    StrokeProperty,
)


def get_examples() -> Dict[str, LogicalFilter]:
    return {
        "Show a line graph for DTN and DIDO for male and female patients between 40 and 60": LogicalFilter(
            operator=OperatorProperty.AND,
            children=[
                LogicalFilter(
                    operator=OperatorProperty.OR,
                    children=[
                        SexFilter(value=SexProperty.Male),
                        SexFilter(value=SexProperty.Female),
                    ],
                ),
                AgeFilter(operator=ComparisonProperty.GreaterOrEqual, value=40),
                AgeFilter(operator=ComparisonProperty.LessOrEqual, value=60),
            ],
        ),
        "Give me a chart of the age of patients gruped by initial point of contact, but Exclude ischemic stroke patients": LogicalFilter(
            operator=OperatorProperty.NOT,
            children=[StrokeFilter(value=StrokeProperty.Ischemic)],
        ),
        "Duration at referring hospital for patients with NIHSS >= 5 who received thrombolysis, between March 4th, 2023 and July 5th, 2024": LogicalFilter(
            operator=OperatorProperty.AND,
            children=[
                NIHSSFilter(operator=ComparisonProperty.GreaterOrEqual, value=5),
                BooleanFilter(property=BooleanProperty.Thrombolysis, value=True, type="BooleanFilter"),
                DateFilter(operator=ComparisonProperty.GreaterOrEqual, value="2023-03-04", type="DateFilter"),
                DateFilter(operator=ComparisonProperty.LessThan, value="2024-07-05", type="DateFilter"),
            ],
        ),
    }


def get_formatted_examples() -> str:
    return "\n\n".join(f"Input: {name}\nOutput:\n{example.model_dump_json(indent=2)}" for name, example in get_examples().items())


def get_prompt(prompt: str | None = None) -> str:
    full_prompt: str = f"""\
Interpret the user's intent and return a structured filter expression matching the schema.

Supported filter types:
- AgeFilter
- NIHSSFilter
- SexFilter
- StrokeFilter
- DateFilter
- BooleanFilter
...combined with LogicalFilter using "AND", "OR", "NOT".

Examples:
{get_formatted_examples()}
"""

    if prompt:
        full_prompt += f"\n\n Now convert this:\n{prompt}"

    return full_prompt


if __name__ == "__main__":
    print(get_prompt())
