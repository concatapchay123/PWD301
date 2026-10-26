"""Safe, automated import refactoring script: pwd301 -> backend.

Replaces:
- 'from backend.' -> 'from backend.'
- 'from backend ' -> 'from backend '
- 'import backend.' -> 'import backend.'
- 'import backend' -> 'import backend'
- '"backend" -> '"backend' (when referring to package module)
"""

from __future__ import annotations

import os
import re
from pathlib import Path

TARGET_DIRS = ["backend", "tests", "scripts", "migrations"]
EXTENSIONS = [".py", ".sh", ".ps1", ".yml", ".yaml", ".json", ".toml", ".ini", ".conf", ".md"]

PATTERNS = [
    (re.compile(r'\bfrom\s+pwd301\b'), 'from backend'),
    (re.compile(r'\bimport\s+pwd301\b'), 'import backend'),
    (re.compile(r'\bpwd301\.'), 'backend.'),
    (re.compile(r'["\']pwd301["\']'), '"backend"'),
    (re.compile(r'["\']pwd301\.'), '"backend.'),
]

def refactor_file(file_path: Path) -> int:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        return 0

    original = content
    for pattern, replacement in PATTERNS:
        content = pattern.sub(replacement, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        return 1
    return 0

def main():
    root = Path.cwd()
    modified_count = 0
    total_files = 0

    for d in TARGET_DIRS:
        target_path = root / d
        if not target_path.exists():
            continue
        for root_dir, _, files in os.walk(target_path):
            for file in files:
                f_path = Path(root_dir) / file
                if f_path.suffix in EXTENSIONS:
                    total_files += 1
                    if refactor_file(f_path):
                        modified_count += 1

    # Also check root entrypoint files
    root_files = ["wsgi.py", "Dockerfile", "docker-compose.yml", "pyproject.toml", ".env.example", ".env.production.example"]
    for rf in root_files:
        f_path = root / rf
        if f_path.exists():
            total_files += 1
            if refactor_file(f_path):
                modified_count += 1

    print(f"Refactored {modified_count} of {total_files} scanned files.")

if __name__ == "__main__":
    main()
