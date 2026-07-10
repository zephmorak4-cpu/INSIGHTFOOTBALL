from __future__ import annotations


class MVPError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, object] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, object]:
        return {"success": False, "error": {"code": self.code, "message": self.message, "details": self.details}}
