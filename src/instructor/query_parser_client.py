import logging
from typing import Any, Optional

from openai import OpenAI

import instructor
import src.instructor.filter_models as filter_models
import src.instructor.filter_prompt as filter_prompt
import src.instructor.metric_models as metric_models
import src.instructor.metric_prompt as metric_prompt
import src.instructor.models as models

logger = logging.getLogger(__name__)


class QueryParserClient:
    """
    Helper class for parsing queries into LogicalFilter and MetricsRequest using LLM.
    """

    def __init__(
        self,
        llm_api_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize QueryParserClient.

        Use Ollama if llm_api_url and llm_model are provided.
        Use OpenAI if openai_api_key and llm_model are provided.
        """
        self.llm_api_url = llm_api_url
        self.llm_model = llm_model
        self.openai_api_key = openai_api_key

        if llm_api_url and openai_api_key:
            raise ValueError("Cannot provide both Ollama and OpenAI credentials at the same time.")
        if not (llm_api_url or openai_api_key):
            raise ValueError("Must provide either (llm_api_url and llm_model) for Ollama or (openai_api_key and llm_model) for OpenAI, but not both.")

        if llm_api_url:
            # Use Ollama with TOOLS mode instead of JSON for better compatibility
            self.client = instructor.from_openai(
                OpenAI(
                    base_url=llm_api_url,
                    api_key="ollama",
                ),
                mode=instructor.Mode.TOOLS,
            )
        elif openai_api_key:
            # Use OpenAI
            self.client = instructor.from_openai(
                OpenAI(
                    api_key=openai_api_key,
                ),
                mode=instructor.Mode.JSON,
            )
        else:
            raise ValueError("Must provide either (llm_api_url and llm_model) for Ollama or (openai_api_key and llm_model) for OpenAI.")

        def log_completion_kwargs(*args: Any) -> None:
            logger.info(f"Function called with args: {args}")

        self.client.on("completion:kwargs", log_completion_kwargs)
        self.client.on("completion:error", lambda exception: logger.error(f"An exception occurred: {str(exception)}"))
        self.client.on("parse:error", lambda exception: logger.error(f"An exception occurred: {str(exception)}"))
        self.client.on("completion:response", lambda response: logger.info(f"LLM response: {response}"))
        self.client.on("completion:last_attempt", lambda attempt: logger.info(f"LLM last attempt: {attempt}"))

    def parse(self, query: str):
        logger.info(f"Parsing query: {query}")

        try:
            filter_response = self.client.chat.completions.create(
                model=self.llm_model,
                max_retries=5,
                response_model=filter_models.FilterResponse,
                messages=[
                    {
                        "role": "system",
                        "content": filter_prompt.get_prompt(),
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
            )
            logger.debug(f"Filter response: {filter_response}")
        except Exception as e:
            logger.warning(f"Filter parsing failed: {e}. Using empty filter.")
            filter_response = filter_models.FilterResponse(logicalFilter=None)

        try:
            metric_response = self.client.chat.completions.create(
                model=self.llm_model,
                max_retries=3,
                response_model=metric_models.MetricResponse,
                messages=[
                    {
                        "role": "system",
                        "content": metric_prompt.get_prompt(),
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
            )
            logger.debug(f"Metric response: {metric_response}")
        except Exception as e:
            logger.error(f"Metric parsing failed: {e}")
            raise

        return models.MetricCalculatorResponse(
            FilterResponse=filter_response,
            MetricResponse=metric_response,
        )
