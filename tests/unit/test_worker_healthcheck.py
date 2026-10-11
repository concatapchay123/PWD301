import json
from pathlib import Path

import pytest


@pytest.mark.parametrize("timestamp,expected", [(100, True), (69, False), (101, False)])
def test_worker_health_requires_recent_heartbeat(tmp_path, timestamp, expected):
    from scripts.worker_healthcheck import heartbeat_is_current

    heartbeat = tmp_path / "heartbeat.json"
    heartbeat.write_text(json.dumps({"timestamp": timestamp}))
    assert heartbeat_is_current(heartbeat, now=100) is expected


def test_worker_health_missing_or_malformed_fails_closed(tmp_path):
    from scripts.worker_healthcheck import heartbeat_is_current

    heartbeat = tmp_path / "heartbeat.json"
    assert not heartbeat_is_current(heartbeat, now=100)
    for content in ('{"timestamp": "nan"}', '{"timestamp": true}', "invalid"):
        heartbeat.write_text(content)
        assert not heartbeat_is_current(heartbeat, now=100)


def test_worker_compose_overrides_inherited_web_probe():
    compose = Path("deploy/compose.production.yml").read_text()
    worker = compose.split("  worker:", 1)[1].split("  proxy:", 1)[0]
    assert "scripts/worker_healthcheck.py" in worker
