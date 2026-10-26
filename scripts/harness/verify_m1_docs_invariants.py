"""
Standalone verification script to rigorously check all active documentation files
for Milestone 1 (Purge Legacy Contracts and Specs) of PWD301 Media & Completion Overhaul.

Checks:
1. No active documentation file contains "PPTX 100MB" or "100 MB" (case-insensitive).
   Excludes docs/archive/.
2. The exact Vietnamese archive rejection message exists in AGENTS.md:
   "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
3. The 4 platform invariants (50MB non-archive, Clean Player YouTube intro,
   sequential completion, header badge removal) are present and consistent in AGENTS.md.
"""

import os
import sys
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

VIETNAMESE_REJECTION_MESSAGE = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). "
    "Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)

def find_active_doc_files(root_dir: str):
    active_files = []
    # Key root docs
    root_docs = ["AGENTS.md", "README.md", "PROJECT.md", os.path.join("tasks", "CURRENT.md")]
    for rd in root_docs:
        full_path = os.path.join(root_dir, rd)
        if os.path.exists(full_path):
            active_files.append(full_path)

    # docs/ excluding docs/archive/
    docs_dir = os.path.join(root_dir, "docs")
    for root, dirs, files in os.walk(docs_dir):
        # Exclude archive directory
        if "archive" in os.path.split(root)[1].lower() or "docs\\archive" in root.lower() or "docs/archive" in root.lower():
            continue
        for file in files:
            if file.endswith((".md", ".txt", ".rst")):
                active_files.append(os.path.join(root, file))

    return active_files

def check_100mb_and_pptx(active_files):
    violations = []
    pattern_100mb = re.compile(r"100\s*mb", re.IGNORECASE)
    pattern_pptx_100 = re.compile(r"pptx[^\n]*100\s*mb", re.IGNORECASE)

    for file_path in active_files:
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, 1):
                if pattern_100mb.search(line) or pattern_pptx_100.search(line):
                    violations.append({
                        "file": rel_path,
                        "line": idx,
                        "content": line.strip()
                    })
    return violations

def check_agents_md(root_dir: str):
    agents_path = os.path.join(root_dir, "AGENTS.md")
    if not os.path.exists(agents_path):
        return ["AGENTS.md does not exist!"]

    with open(agents_path, "r", encoding="utf-8") as f:
        content = f.read()

    issues = []

    # 1. Exact Vietnamese rejection message
    if VIETNAMESE_REJECTION_MESSAGE not in content:
        issues.append("Exact Vietnamese archive rejection message missing from AGENTS.md")

    # 2. Invariant 1: 50MB non-archive attachment policy
    inv1_checks = [
        "50MB Non-Archive Attachment Policy",
        "50 MB",
        "50,000,000 bytes",
        ".zip",
        ".rar",
        ".7z"
    ]
    for req in inv1_checks:
        if req not in content:
            issues.append(f"Invariant 1 (50MB Non-Archive) missing keyword: '{req}'")

    # 3. Invariant 2: Clean Player YouTube intro
    inv2_checks = [
        "Clean Player Shell",
        "-14% top",
        "128% height",
        "pointer-events: none",
        "autoplay",
        "mute",
        "loop",
        "zero YouTube branding"
    ]
    for req in inv2_checks:
        if req.lower() not in content.lower():
            issues.append(f"Invariant 2 (Clean Player YouTube Intro) missing keyword: '{req}'")

    # 4. Invariant 3: Sequential completion gate
    inv3_checks = [
        "Sequential Lesson Completion Gate",
        "dwell time >= 60 seconds",
        "100% watched",
        "miniquiz",
        "default 80%",
        "bg-slate-200 text-slate-400 cursor-not-allowed",
        "bg-emerald-600 text-white cursor-pointer"
    ]
    for req in inv3_checks:
        if req.lower() not in content.lower():
            issues.append(f"Invariant 3 (Sequential Completion Gate) missing keyword: '{req}'")

    # 5. Invariant 4: Header badge removal
    inv4_checks = [
        "#console-course-progress-badge",
        "removed from the header entirely",
        "eliminating obsolete header badge dynamic calculation"
    ]
    for req in inv4_checks:
        if req.lower() not in content.lower():
            issues.append(f"Invariant 4 (Header Badge Removal) missing keyword: '{req}'")

    return issues

def main():
    print("=" * 80)
    print("CHALLENGER 2 EMPIRICAL VERIFICATION HARNESS - MILESTONE 1")
    print(f"Project root: {PROJECT_ROOT}")
    print("=" * 80)

    active_files = find_active_doc_files(PROJECT_ROOT)
    print(f"\n[INFO] Found {len(active_files)} active documentation files (excluding docs/archive/).")

    # Check 1: 100MB / PPTX 100MB
    print("\n[CHECK 1] Scanning for 'PPTX 100MB' and '100 MB' in active documentation...")
    mb_violations = check_100mb_and_pptx(active_files)
    if mb_violations:
        print(f"[FAIL] Found {len(mb_violations)} violation(s) in active documentation:")
        for v in mb_violations:
            print(f"  - {v['file']}:{v['line']}: {v['content']}")
    else:
        print("[PASS] Zero instances of 'PPTX 100MB' or '100 MB' in active documentation.")

    # Check 2 & 3: AGENTS.md checks
    print("\n[CHECK 2 & 3] Verifying AGENTS.md invariants and rejection message...")
    agents_issues = check_agents_md(PROJECT_ROOT)
    if agents_issues:
        print(f"[FAIL] Found {len(agents_issues)} issue(s) in AGENTS.md:")
        for issue in agents_issues:
            print(f"  - {issue}")
    else:
        print("[PASS] AGENTS.md contains exact Vietnamese rejection message and all 4 platform invariants.")

    print("\n" + "=" * 80)
    total_failures = len(mb_violations) + len(agents_issues)
    if total_failures > 0:
        print(f"VERDICT: REQUEST_CHANGES ({total_failures} failure(s) detected)")
        print("=" * 80)
        sys.exit(1)
    else:
        print("VERDICT: APPROVE (All empirical assertions passed)")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    main()
