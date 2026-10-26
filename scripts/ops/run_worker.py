"""Run the durable PWD301 background worker process."""

from __future__ import annotations

import os

from backend import create_app
from backend.services.background_job_service import run_worker_loop


def main() -> None:
    """Create the application context and poll the shared job/outbox queues."""
    poll_interval = float(os.environ.get("WORKER_POLL_INTERVAL_SECONDS", "2"))
    app = create_app(os.environ.get("APP_ENV", "development"))
    with app.app_context():
        run_worker_loop(poll_interval_seconds=poll_interval)


if __name__ == "__main__":
    main()
