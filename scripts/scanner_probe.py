"""Real scanner diagnostics on isolated staging, with no asset or production mutation."""

import base64
import json
import os
import tempfile
from pathlib import Path

from pwd301 import create_app
from pwd301.services.scanner_service import ClamAVScanner


def run():
    if os.environ.get("PWD301_TEST_DB_DISPOSABLE") != "1" or not os.environ.get(
        "DB_NAME", ""
    ).startswith("pwd301_test_"):
        raise ValueError("Scanner probe requires explicit disposable staging identity.")
    app = create_app("production")
    with (
        app.app_context(),
        tempfile.TemporaryDirectory(dir=app.config["FILE_QUARANTINE_ROOT"]) as temporary,
    ):
        root = Path(temporary)
        clean = root / "clean.txt"
        clean.write_bytes(b"PWD301 staging clean scanner proof")
        sample = root / "scanner-test.txt"
        sample.write_bytes(
            base64.b64decode(
                "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo="
            )
        )
        scanner = ClamAVScanner()
        result = {
            "clean": scanner.scan_file(clean).status,
            "eicar": scanner.scan_file(sample).status,
        }
        original_port = app.config.get("CLAMAV_PORT")
        app.config["CLAMAV_PORT"] = 1
        result["unavailable"] = scanner.scan_file(clean).status
        app.config["CLAMAV_PORT"] = original_port
        oversized = root / "oversized.txt"
        with oversized.open("wb") as stream:
            stream.truncate(int(app.config["CLAMAV_MAX_STREAM_BYTES"]) + 1)
        result["oversized"] = scanner.scan_file(oversized).status
        expected = {"clean": "PASS", "eicar": "FAIL", "unavailable": "ERROR", "oversized": "ERROR"}
        print(json.dumps(result))
        if result != expected:
            raise RuntimeError("Real scanner probe failed; do not release.")


if __name__ == "__main__":
    run()
