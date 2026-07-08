"""Error types for the Match Selector module."""


class MatchSelectorError(Exception):
    """Base class for Match Selector failures."""


class ConfigError(MatchSelectorError):
    """Raised when configuration is invalid."""


class PromptLoadError(MatchSelectorError):
    """Raised when the Match Selector prompt cannot be loaded."""


class LLMError(MatchSelectorError):
    """Raised when an LLM client fails."""


class ValidationError(MatchSelectorError):
    """Raised when input or output validation fails."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
