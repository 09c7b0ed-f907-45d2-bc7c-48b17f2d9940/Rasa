import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Dict

from src.instructor.metric_models import KPI, Distribution, GroupProperty, Metric, MetricsCollection


def get_examples() -> Dict[str, MetricsCollection]:
    return {
        "Show a line graph for DTN and DIDO for male and female patients between 40 and 60": MetricsCollection(
            metrics=[
                Metric(
                    kpi=KPI.Dtn,
                    distribution=Distribution(
                        bin_count=100,
                        lower=0,
                        upper=100,
                    ),
                    stats=None,
                ),
                Metric(
                    kpi=KPI.Dido,
                    distribution=Distribution(
                        bin_count=100,
                        lower=0,
                        upper=100,
                    ),
                    stats=None,
                ),
            ],
            group_by=None,
        ),
        "Give me a chart of the age of patients gruped by initial point of contact, but Exclude ischemic stroke patients, between the age of 20 to 90": MetricsCollection(
            metrics=[
                Metric(
                    kpi=KPI.Age,
                    distribution=Distribution(
                        bin_count=70,
                        lower=20,
                        upper=90,
                    ),
                    stats=None,
                ),
            ],
            group_by=GroupProperty.FirstContactPlace,
        ),
        "Duration at referring hospital for patients with NIHSS >= 5 who received thrombolysis, between March 4th, 2023 and July 5th, 2024": MetricsCollection(
            metrics=[
                Metric(
                    kpi=KPI.Dido,
                    distribution=Distribution(
                        bin_count=120,
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
- `distribution`: Optional. Define `bin_count`, `lower`, and `upper` for histogram buckets. Be mindful on which distribution ranges fit to what metrics:
  - DTN and DIDO are typically between 0 and 100 minutes with bin count 100.
  - Age is usually between 0 and 120 years with bin count 120.
  - MRS is typically between 0 and 6 with bin count 6.
  - NIHSS is usually between 0 and 42 with bin count 42.
  - bin_count should high enough to capture the distribution accurately and a clean fraction of upper limit. But sometimes if values are discrete like MRS it's best to just set bin_count equal to upper limit
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
