from __future__ import annotations


class ExecutorError(Exception):
    """Base class for executor-related errors."""


class PlanValidationError(ExecutorError):
    """Raised when an AnalysisPlan is structurally or semantically invalid for execution."""


class GraphQLExecutionError(ExecutorError):
    """Raised when GraphQL translation or execution fails."""


class ChartGenerationError(ExecutorError):
    """Raised when chart generation fails for a given plan or dataset."""
