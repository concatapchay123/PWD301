"""Check worker liveness independently of the Web HTTP server."""

import json
import math
import os
import time
from pathlib import Path


def heartbeat_is_current(path: Path, *, now: float | None = None) -> bool:
    try:
        timestamp = json.loads(path.read_text(encoding="utf-8"))["timestamp"]
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            return False
        elapsed = (time.time() if now is None else now) - timestamp
        return math.isfinite(elapsed) and 0 <= elapsed <= 30
    except (OSError, ValueError, TypeError, KeyError):
        return False


if __name__ == "__main__":
    destination = os.environ.get("WORKER_HEARTBEAT_PATH")
    raise SystemExit(0 if destination and heartbeat_is_current(Path(destination)) else 1)
