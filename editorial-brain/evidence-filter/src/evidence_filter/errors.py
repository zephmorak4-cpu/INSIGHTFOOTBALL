"""Error types for Evidence Filter."""


class EvidenceFilterError(Exception):
    """Base Evidence Filter failure."""


class ConfigError(EvidenceFilterError):
    """Raised when configuration is invalid."""


class PromptLoadError(EvidenceFilterError):
    """Raised when the prompt cannot be loaded."""


class LLMError(EvidenceFilterError):
    """Raised when the LLM adapter fails."""


class ValidationError(EvidenceFilterError):
    """Raised when validation fails."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
