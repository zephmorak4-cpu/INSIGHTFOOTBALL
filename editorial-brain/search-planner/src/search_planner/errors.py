from __future__ import annotations


class ValidationError(Exception):
    def __init__(self, message: str, issues: list[str]):
        super().__init__(message)
        self.issues = issues

