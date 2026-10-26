"""Tests package root."""
from __future__ import annotations

# Re-exports for test modules that register fixtures or cross-import from tests.*
from tests.unit import test_lesson_revision_lifecycle  # noqa: F401
from tests.api import test_m1_file_access  # noqa: F401
from tests.security import test_admin_security_remediation  # noqa: F401
from tests.integration import test_m3_challenger_stress  # noqa: F401
