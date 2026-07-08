"""Scriptwriter exceptions."""

from __future__ import annotations


class ConfigError(Exception):
    """Raised when configuration is invalid."""


class LLMError(Exception):
    """Raised when an LLM adapter fails."""


class ValidationError(Exception):
    """Raised when input or output validation fails."""

    def __init__(self, message: str, issues: list[str]):
        super().__init__(message)
        self.issues = issues

