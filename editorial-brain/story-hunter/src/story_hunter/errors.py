"""Error types for Story Hunter."""


class StoryHunterError(Exception):
    """Base Story Hunter failure."""


class ConfigError(StoryHunterError):
    """Raised when configuration is invalid."""


class PromptLoadError(StoryHunterError):
    """Raised when the prompt cannot be loaded."""


class LLMError(StoryHunterError):
    """Raised when the LLM adapter fails."""


class ValidationError(StoryHunterError):
    """Raised when validation fails."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
