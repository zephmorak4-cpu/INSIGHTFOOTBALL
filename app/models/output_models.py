from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    stage: str
    message: str
    retryable: bool
    run_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "stage": self.stage, "message": self.message, "retryable": self.retryable, "run_id": self.run_id}
