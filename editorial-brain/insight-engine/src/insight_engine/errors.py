"""Error types for Insight Engine."""


class InsightEngineError(Exception):
    """Base Insight Engine failure."""


class ConfigError(InsightEngineError):
    """Raised when configuration is invalid."""


class PromptLoadError(InsightEngineError):
    """Raised when the prompt cannot be loaded."""


class LLMError(InsightEngineError):
    """Raised when the LLM adapter fails."""


class ValidationError(InsightEngineError):
    """Raised when validation fails."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
