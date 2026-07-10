from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_once(fn: Callable[[], T], retryable: tuple[type[BaseException], ...]) -> T:
    try:
        return fn()
    except retryable:
        time.sleep(1)
        return fn()
