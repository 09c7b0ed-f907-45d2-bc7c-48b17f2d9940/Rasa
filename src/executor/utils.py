from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Dict, Iterator


@contextmanager
def timer(timings: Dict[str, float], key: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        timings[key] = time.perf_counter() - start
