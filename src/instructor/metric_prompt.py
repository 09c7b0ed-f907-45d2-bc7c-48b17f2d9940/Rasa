from typing import Dict

from src.instructor.metric_models import KPI, Distribution, GroupProperty, Metric, MetricsRequest


def get_examples() -> Dict[str, MetricsRequest]:
    return {
        "Show a line graph for DTN and DIDO for male and female patients between 40 and 60": MetricsRequest(
            metrics=[
                Metric(
                    kpi=KPI.Dtn,
                    distribution=Distribution(
                        bin_count=1,
                        lower=0,
                        upper=100,
                    ),
                    stats=None,
                ),
                Metric(
                    kpi=KPI.Dido,
                    distribution=Distribution(
                        bin_count=1,
                        lower=0,
                        upper=100,
                    ),
                    stats=None,
                ),
            ],
            group_by=None,
        ),
        "Give me a chart of the age of patients gruped by initial point of contact, but Exclude ischemic stroke patients": MetricsRequest(
            metrics=[
                Metric(
                    kpi=KPI.Age,
                    distribution=Distribution(
                        bin_count=1,
                        lower=0,
                        upper=120,
                    ),
                    stats=None,
                ),
            ],
            group_by=GroupProperty.FirstContactPlace,
        ),
        "Duration at referring hospital for patients with NIHSS >= 5 who received thrombolysis, between March 4th, 2023 and July 5th, 2024": MetricsRequest(
            metrics=[
                Metric(
                    kpi=KPI.Dido,
                    distribution=Distribution(
                        bin_count=1,
                        lower=0,
                        upper=120,
                    ),
                    stats=None,
                ),
            ],
            group_by=None,
        ),
    }


def get_formatted_examples() -> str:
    return "\n\n".join(f"Input: {name}\nOutput:\n{example.model_dump_json(indent=2)}" for name, example in get_examples().items())


def get_prompt(prompt: str | None = None) -> str:
    full_prompt: str = f"""\
Interpret the user's intent and return a structured JSON object matching the `MetricsRequest` schema.

Each request must specify one or more metrics to analyze, optionally grouped by a category (e.g., EMS_PRENOTIFICATION). 
Metrics may include distribution histograms and summary statistics.

Field descriptions:
- `kpi`: The metric or key performance indicator to visualize (e.g., AGE, DTN, DIDO).
- `distribution`: Optional. Define `bin_count`, `lower`, and `upper` for histogram buckets.
- `stats`: Optional. If true, return summary statistics such as mean, min, max, interquartile range etc.
- `group_by`: Optional. Used to segment the metric by a categorical property (e.g., ARRIVAL_MODE, SEX).

Examples:
{get_formatted_examples()}
"""

    if prompt:
        full_prompt += f"\n\n Now convert this:\n{prompt}"

    return full_prompt


if __name__ == "__main__":
    print(get_prompt())
