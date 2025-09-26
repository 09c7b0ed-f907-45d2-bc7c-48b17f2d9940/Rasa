import json
from typing import Dict, List, Tuple

from src.langchain.planner_schema import AnalysisPlan, ChartSpec, GroupBySex, GroupByStrokeType, MetricSpec, StatisticalTestSpec


def example_dtn_by_sex() -> Tuple[str, str, str]:
    detected_entities = {"sex": ["MALE", "FEMALE"], "metric": ["DTN"], "chart_type": ["LINE"]}
    plan = AnalysisPlan(
        charts=[
            ChartSpec(
                title="DTN by Sex",
                description="Line graph of Door-to-Needle Time for males and females.",
                chart_type="LINE",
                metrics=[
                    MetricSpec(
                        title="DTN for Males",
                        description="Average DTN for male patients",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["MALE"])],
                        filters=None,
                    ),
                    MetricSpec(
                        title="DTN for Females",
                        description="Average DTN for female patients",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["FEMALE"])],
                        filters=None,
                    ),
                ],
            )
        ],
        statistical_tests=None,
    )
    desc = "Line graph of DTN for males and females."
    user = f"USER_UTTERANCE:\nShow me a line graph of DTN for males and females\n\nENTITIES_DETECTED(JSON):\n{json.dumps(detected_entities)}"
    assistant = plan.model_dump_json(indent=2)
    return desc, user, assistant


def example_dtn_by_sex_and_stroke() -> Tuple[str, str, str]:
    detected_entities = {"sex": ["MALE", "FEMALE"], "metric": ["DTN"], "chart_type": ["BAR"], "stroke_type": ["ISCHEMIC", "INTRACEREBRAL_HEMORRHAGE"]}
    plan = AnalysisPlan(
        charts=[
            ChartSpec(
                title="DTN by Sex and Stroke Type",
                description="Bar chart of Door-to-Needle Time for males and females, grouped by stroke type.",
                chart_type="BAR",
                metrics=[
                    MetricSpec(
                        title="DTN for Males (Ischemic)",
                        description="Average DTN for male patients with ischemic stroke",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["MALE"]), GroupByStrokeType(categories=["ISCHEMIC"])],
                        filters=None,
                    ),
                    MetricSpec(
                        title="DTN for Females (Ischemic)",
                        description="Average DTN for female patients with ischemic stroke",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["FEMALE"]), GroupByStrokeType(categories=["ISCHEMIC"])],
                        filters=None,
                    ),
                    MetricSpec(
                        title="DTN for Males (ICH)",
                        description="Average DTN for male patients with intracerebral hemorrhage",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["MALE"]), GroupByStrokeType(categories=["INTRACEREBRAL_HEMORRHAGE"])],
                        filters=None,
                    ),
                    MetricSpec(
                        title="DTN for Females (ICH)",
                        description="Average DTN for female patients with intracerebral hemorrhage",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["FEMALE"]), GroupByStrokeType(categories=["INTRACEREBRAL_HEMORRHAGE"])],
                        filters=None,
                    ),
                ],
            )
        ],
        statistical_tests=None,
    )
    desc = "Bar chart of DTN for males and females, grouped by stroke type."
    user = f"USER_UTTERANCE:\nShow me a bar chart of DTN for males and females, grouped by stroke type\n\nENTITIES_DETECTED(JSON):\n{json.dumps(detected_entities)}"
    assistant = plan.model_dump_json(indent=2)
    return desc, user, assistant


def example_statistical_test_dtn_by_sex() -> Tuple[str, str, str]:
    detected_entities = {"sex": ["MALE", "FEMALE"], "metric": ["DTN"], "statistical_test_type": ["T_TEST"]}
    plan = AnalysisPlan(
        charts=None,
        statistical_tests=[
            StatisticalTestSpec(
                title="T-Test for DTN by Sex",
                description="T-Test comparing DTN between male and female patients.",
                test_type="T_TEST",
                metrics=[
                    MetricSpec(
                        title="DTN for Males",
                        description="DTN for male patients",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["MALE"])],
                        filters=None,
                    ),
                    MetricSpec(
                        title="DTN for Females",
                        description="DTN for female patients",
                        metric="DTN",
                        group_by=[GroupBySex(categories=["FEMALE"])],
                        filters=None,
                    ),
                ],
            )
        ],
    )
    desc = "T-Test comparing DTN between male and female patients."
    user = f"USER_UTTERANCE:\nRun a t-test comparing DTN between male and female patients\n\nENTITIES_DETECTED(JSON):\n{json.dumps(detected_entities)}"
    assistant = plan.model_dump_json(indent=2)
    return desc, user, assistant


def get_few_shot_examples() -> List[Dict[str, str]]:
    examples: List[Dict[str, str]] = []
    for desc, user, assistant in [
        example_dtn_by_sex(),
        example_dtn_by_sex_and_stroke(),
        example_statistical_test_dtn_by_sex(),
    ]:
        examples.append(
            {
                "description": desc,
                "user": user,
                "assistant": assistant,
            }
        )
    return examples
