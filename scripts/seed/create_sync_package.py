import os
import sys
import tarfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_TAR = Path("backups/pwd301_sync_package.tar.gz")

INCLUDE_DIRS = [
    "src",
    "frontend",
    "migrations",
    "deploy",
    "scripts",
]

INCLUDE_FILES = [
    "requirements.txt",
    "AGENTS.md",
    "Dockerfile",
    "wsgi.py",
    "pyproject.toml",
]

EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
    "*.pyc",
    "*.pyo",
    "screenshots",
    "*.log",
    "course_data",
    "android_course_data",
]

def filter_tar(tarinfo):
    name = tarinfo.name
    for pat in ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".pyc", "course_data", "android_course_data"]:
        if pat in name:
            return None
    return tarinfo

print(f"Creating sync package: {OUTPUT_TAR}...")
with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
    for d in INCLUDE_DIRS:
        dp = Path(d)
        if dp.exists():
            print(f"  Adding dir: {d}")
            tar.add(d, filter=filter_tar)
    for f in INCLUDE_FILES:
        fp = Path(f)
        if fp.exists():
            print(f"  Adding file: {f}")
            tar.add(f)

print(f"Sync package created! Size: {OUTPUT_TAR.stat().st_size / (1024*1024):.2f} MB")
