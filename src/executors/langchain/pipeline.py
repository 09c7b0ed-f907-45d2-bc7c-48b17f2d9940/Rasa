import logging
from typing import Any, Callable, Dict, List, Literal, Optional, Type, TypedDict, Union, overload

from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from langchain.prompts import ChatPromptTemplate
from src.domain.langchain.schema import AnalysisPlan
from src.executors.langchain.examples import get_few_shot_examples
from src.util import env

logger = logging.getLogger(__name__)

LLM_MODEL = env.require_all_env("LLM_MODEL")
llm: Any = ChatOpenAI(model=LLM_MODEL, temperature=0)


def get_schema_description(model: Type[Any]) -> str:
    """
    Recursively extract field descriptions from a Pydantic model as a readable schema spec (Pydantic v2 compatible).
    """
    from typing import get_args, get_origin

    def describe(model: Type[Any], indent: int = 0) -> str:
        lines: List[str] = []
        if hasattr(model, "model_fields"):
            for name, field in model.model_fields.items():
                desc = field.description or field.title or ""
                typ = str(field.annotation)
                lines.append(" " * indent + f"- {name} ({typ}): {desc}")
                # Recurse for nested models
                outer = get_origin(field.annotation)
                inner = get_args(field.annotation)
                if outer in (list, List) and inner and hasattr(inner[0], "model_fields"):
                    lines.append(describe(inner[0], indent + 2))
                elif hasattr(field.annotation, "model_fields"):
                    lines.append(describe(field.annotation, indent + 2))
        return "\n".join(lines)

    return f"AnalysisPlan schema:\n{describe(model)}"


SCHEMA_DESCRIPTION: str = get_schema_description(AnalysisPlan)
cot_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(  # type: ignore
    [
        (
            "system",
            "You are a clinical analytics planner. User interface language: {language}. Think step by step about how to answer the user's query, considering all entities. Explain your reasoning in detail in English (for internal clarity) even if the user language is different. Do not output the plan yet.",
        ),
        ("user", "USER_UTTERANCE:\n{question}\n\nENTITIES_DETECTED(JSON):\n{entities}"),
    ]
)

few_shot_examples = get_few_shot_examples()


def _build_few_shots_text() -> str:
    parts: List[str] = []
    for idx, ex in enumerate(few_shot_examples, start=1):
        parts.append(
            "\n".join(
                [
                    f"EXAMPLE {idx}:",
                    f"Description: {ex['description']}",
                    "User Message:",
                    ex["user"],
                    "Assistant Plan JSON:",
                    ex["assistant"],
                    "---",
                ]
            )
        )
    return "\n".join(parts)


FEW_SHOTS_TEXT = _build_few_shots_text()
plan_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(  # type: ignore
    [
        (
            "system",
            "You are a planner. Interface language: {language}. Produce ONLY a valid AnalysisPlan JSON according to the schema. "
            "All 'title' and 'description' fields MUST be written in the interface language ({language}). "
            "Keep enum-like codes (metric, chart_type, test_type, stroke categories, sex categories) in their canonical uppercase English forms. "
            "Use the reasoning and prior examples. Place detected entities into metrics (group_by / filters). "
            "Prefer LINE/BAR for trends or comparisons; BOX/VIOLIN/HISTOGRAM for distributions. "
            "Title guidance: Avoid phrases like 'Over Time' unless there is an explicit temporal grouping. If no time/canonical grouping is specified and a LINE chart is used for a distribution, prefer '<METRIC> Distribution' for the title.",
        ),
        ("system", "SCHEMA:\n" + SCHEMA_DESCRIPTION),
        ("system", "FEW_SHOT_EXAMPLES:\n{few_shots}"),
        ("system", "REASONING (English internal reasoning shown below can differ from output language):\n{reasoning}"),
        ("user", "USER_UTTERANCE:\n{question}\n\nENTITIES_DETECTED(JSON):\n{entities}"),
    ]
)

structured_llm: Any = llm.with_structured_output(AnalysisPlan)

cot_chain: Any = cot_prompt | llm
plan_chain: Any = plan_prompt | structured_llm

full_chain: Any = (
    RunnablePassthrough.assign(
        reasoning=lambda x: cot_chain.invoke(
            {
                "question": x["question"],
                "entities": x["entities"],
                "language": x.get("language", "auto"),
            }
        )
    )
    | plan_chain
)


class GeneratePlanDebug(TypedDict):
    """Typed structure for debug output of generate_analysis_plan."""

    reasoning: Any
    steps: List[Any]
    attempts: List[Any]
    final_output: Optional[AnalysisPlan]


ProgressCallback = Callable[[str], None]


@overload
def generate_analysis_plan(
    question: str,
    entities: Dict[str, Any],
    language: Optional[str],
    max_retries: int,
    debug: Literal[True],
    progress_cb: Optional[ProgressCallback] = None,
) -> GeneratePlanDebug: ...


@overload
def generate_analysis_plan(
    question: str,
    entities: Dict[str, Any],
    language: Optional[str],
    max_retries: int,
    debug: Literal[False],
    progress_cb: Optional[ProgressCallback] = None,
) -> AnalysisPlan: ...


@overload
def generate_analysis_plan(
    question: str,
    entities: Dict[str, Any],
    language: Optional[str],
    max_retries: int,
    debug: bool,
    progress_cb: Optional[ProgressCallback] = None,
) -> Union[AnalysisPlan, GeneratePlanDebug]: ...


def generate_analysis_plan(
    question: str,
    entities: Dict[str, Any],
    language: str | None = None,
    max_retries: int = 2,
    debug: bool = False,
    progress_cb: Optional[ProgressCallback] = None,
) -> Union[AnalysisPlan, GeneratePlanDebug]:
    """
    Generate a validated AnalysisPlan from user input, with chain-of-thought reasoning and automatic
    correction/retry on validation failure.

    Returns:
    - AnalysisPlan when debug is False (default).
    - GeneratePlanDebug when debug is True, including reasoning, steps, attempts, and final_output
      (which will be an AnalysisPlan or None on failure).

    Always includes 'reasoning' in the debug output, even if an error occurs.
    """
    import json
    import logging

    from pydantic import ValidationError

    logger = logging.getLogger(__name__)
    if not language:
        language = "auto"

    # High-level notification that planning has started.
    if progress_cb is not None:
        progress_cb("Thinking about a plan.")

    input_dict: Dict[str, Any] = {
        "question": question,
        "entities": json.dumps(entities),
        "few_shots": FEW_SHOTS_TEXT,
        "language": language,
    }
    logger.info(f"[Planner] input_dict: {input_dict}")
    _chain: Any = full_chain
    steps: List[Any] = []
    attempts: List[Any] = []
    reasoning: Any = None
    cot_inputs: Dict[str, Any] = {
        "question": question,
        "entities": json.dumps(entities),
        "language": language,
    }
    logger.info(f"[Planner] cot_inputs: {cot_inputs}")
    try:
        cot_prompt_rendered: str = cot_prompt.format_prompt(**cot_inputs).to_string()
        logger.info(f"[Planner] cot_prompt_rendered: {cot_prompt_rendered}")
        cot_response: Any = cot_chain.invoke(cot_inputs)
        logger.info(f"[Planner] cot_response: {cot_response}")
        steps.append(
            {
                "step": "chain_of_thought",
                "prompt": cot_prompt_rendered,
                "response": cot_response,
            }
        )
        reasoning = cot_response
    except Exception as cot_exc:
        logger.error(f"[Planner] COT Exception: {cot_exc}")
        steps.append(
            {
                "step": "chain_of_thought",
                "prompt": cot_prompt.format_prompt(**cot_inputs).to_string(),
                "response": f"ERROR: {cot_exc}",
            }
        )
        reasoning = f"ERROR: {cot_exc}"
    plan_inputs: Dict[str, Any] = {
        "question": question,
        "entities": json.dumps(entities),
        "reasoning": reasoning,
        "few_shots": FEW_SHOTS_TEXT,
        "language": language,
    }
    logger.info(f"[Planner] plan_inputs: {plan_inputs}")
    plan_prompt_rendered: str = plan_prompt.format_prompt(**plan_inputs).to_string()
    logger.info(f"[Planner] plan_prompt_rendered: {plan_prompt_rendered}")
    for attempt in range(max_retries + 1):
        if progress_cb is not None:
            dots = "." * (attempt + 1)
            progress_cb(f"Thinking about a plan.{dots}")
        try:
            logger.info(f"[Planner] Attempt {attempt + 1}: invoking _chain with input_dict: {input_dict}")
            result: Any = _chain.invoke(input_dict)
            logger.info(f"[Planner] Attempt {attempt + 1}: result: {result}")
            steps.append(
                {
                    "step": f"plan_attempt_{attempt + 1}",
                    "prompt": plan_prompt_rendered,
                    "response": result,
                }
            )
            if not isinstance(result, AnalysisPlan):
                try:
                    result = AnalysisPlan.model_validate(result)
                except Exception:
                    pass

            if debug:
                debug_payload: GeneratePlanDebug = {
                    "reasoning": reasoning,
                    "steps": steps,
                    "attempts": attempts,
                    "final_output": result if isinstance(result, AnalysisPlan) else None,
                }
                if progress_cb is not None:
                    progress_cb("Finished thinking about a plan.")
                return debug_payload
            assert isinstance(result, AnalysisPlan), "Expected AnalysisPlan from structured output"
            if progress_cb is not None:
                progress_cb("Finished thinking about a plan.")
            return result
        except ValidationError as ve:
            logger.error(f"[Planner] ValidationError: {ve}")
            attempts.append(
                {
                    "error": str(ve),
                    "input": input_dict,
                    "output": ve.json() if hasattr(ve, "json") else str(ve),
                }
            )
            if attempt == max_retries:
                if debug:
                    return {
                        "reasoning": reasoning,
                        "steps": steps,
                        "attempts": attempts,
                        "final_output": None,
                    }
                raise
            invalid_output: str = ve.json() if hasattr(ve, "json") else str(ve)
            critique_prompt_obj: ChatPromptTemplate = ChatPromptTemplate.from_messages(  # type: ignore
                [
                    ("system", "The following output did not pass validation. Critique the output, explain what is wrong, and then return a corrected valid AnalysisPlan JSON. Only fix the error described."),
                    ("user", f"Original user input: {input_dict}\n\nInvalid output: {invalid_output}\n\nValidation error: {str(ve)}"),
                ]
            )
            critique_prompt_rendered: str = critique_prompt_obj.format_prompt().to_string()
            logger.info(f"[Planner] critique_prompt_rendered: {critique_prompt_rendered}")
            critique_chain: Any = critique_prompt_obj | llm.with_structured_output(AnalysisPlan)
            critique_response: Any = critique_chain.invoke({})
            logger.info(f"[Planner] critique_response: {critique_response}")
            steps.append(
                {
                    "step": f"correction_attempt_{attempt + 1}",
                    "prompt": critique_prompt_rendered,
                    "response": critique_response,
                }
            )
            _chain = critique_chain
    # Should never reach here; all paths either return or raise inside the loop
    raise RuntimeError("generate_analysis_plan failed to produce a result")
