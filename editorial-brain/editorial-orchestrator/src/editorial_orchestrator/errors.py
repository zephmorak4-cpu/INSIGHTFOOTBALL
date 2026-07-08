"""Error types for the Editorial Orchestrator."""


class OrchestratorError(Exception):
    """Base orchestrator error."""


class ConfigError(OrchestratorError):
    """Raised when config is invalid."""


class ValidationError(OrchestratorError):
    """Raised when orchestration validation fails."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
