#!/usr/bin/env python3
"""
scripts/generate_gemini_context.py
Generates a comprehensive, single-file Markdown bundle containing all code,
configuration, documentation, and database architecture for LLM context (e.g. Gemini).
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "PROJECT_CONTEXT_FOR_GEMINI.md"

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "htmlcov",
    "storage",
    "uploads",
    "quarantine",
    "backups",
    "exports",
}

EXCLUDED_FILES = {
    "PROJECT_CONTEXT_FOR_GEMINI.md",
    "PROJECT_CONTEXT_FOR_GEMINI_AI.md",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
}

EXT_LANG_MAP = {
    ".py": "python",
    ".sql": "sql",
    ".md": "markdown",
    ".toml": "toml",
    ".txt": "text",
    ".sh": "bash",
    ".ps1": "powershell",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".js": "javascript",
    ".example": "text",
    ".gitattributes": "text",
    ".gitignore": "text",
    ".editorconfig": "ini",
    ".gitkeep": "text",
}


def get_all_files() -> list[Path]:
    collected: list[Path] = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = sorted([d for d in dirs if d not in EXCLUDED_DIRS])
        for f in sorted(files):
            if f in EXCLUDED_FILES:
                continue
            collected.append(Path(root) / f)
    return collected


def sort_key_for_file(p: Path) -> tuple[int, str]:
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    root_files = [
        "AGENTS.md",
        "AGENT.md",
        "BOOTSTRAP_MANIFEST.md",
        "CONTRIBUTING.md",
        "VIBECODE_SUPPLEMENT_FILES.md",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        ".env.example",
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
    ]
    if rel in root_files:
        return (1, rel)
    if rel.startswith("tasks/"):
        return (2, rel)
    if rel.startswith("prompts/"):
        return (3, rel)
    if rel.startswith("src/"):
        return (4, rel)
    if rel.startswith("tests/"):
        return (5, rel)
    if rel.startswith("scripts/"):
        return (6, rel)
    if rel == "README.md":
        return (7, rel)
    if rel.startswith("docs/database/"):
        return (8, rel)
    if rel.startswith("docs/system/"):
        return (9, rel)
    return (10, rel)


def build_tree(paths: list[Path]) -> str:
    lines = ["```text", "PWD301/"]
    tree = {}
    for p in paths:
        rel = p.relative_to(ROOT)
        parts = rel.parts
        curr = tree
        for part in parts[:-1]:
            curr = curr.setdefault(part, {})
        curr[parts[-1]] = None

    def render(d: dict, prefix: str = "") -> list[str]:
        res = []
        keys = sorted(d.keys(), key=lambda k: (d[k] is None, k))
        for i, k in enumerate(keys):
            is_last = i == len(keys) - 1
            connector = "└── " if is_last else "├── "
            res.append(f"{prefix}{connector}{k}")
            if d[k] is not None:
                sub_prefix = prefix + ("    " if is_last else "│   ")
                res.extend(render(d[k], sub_prefix))
        return res

    lines.extend(render(tree))
    lines.append("```")
    return "\n".join(lines)


def make_anchor(rel_path: str) -> str:
    clean = (
        rel_path.lower().replace("/", "-").replace("\\", "-").replace(".", "-").replace("_", "-")
    )
    return f"file-{clean}"


def main() -> None:
    raw_files = get_all_files()
    files = sorted(raw_files, key=sort_key_for_file)
    print(f"Total files identified to bundle: {len(files)}")

    output_lines: list[str] = []

    output_lines.append("# PWD301 — FULL PROJECT CONTEXT FOR GEMINI AI")
    output_lines.append("")
    output_lines.append("> **VAI TRÒ CỦA BẠN (ROLE FOR GEMINI)**:")
    output_lines.append(
        "> Bạn là **Principal Software Architect & Lead Fullstack Python/Flask Engineer** chuyên trách dự án **PWD301 — Online Course Management Platform**."
    )
    output_lines.append(">")
    output_lines.append(
        "> File Markdown này là tài liệu đóng gói hoàn chỉnh (Full Codebase & Architecture Context Dump), chứa:"
    )
    output_lines.append(
        "> 1. Toàn bộ mã nguồn hiện tại, kịch bản kiểm thử, shell/powershell scripts."
    )
    output_lines.append("> 2. Toàn bộ tài liệu đặc tả kiến trúc hệ thống (System Specification).")
    output_lines.append(
        "> 3. Toàn bộ tài liệu kiến trúc cơ sở dữ liệu chuẩn (Canonical Database Architecture) và 71 bảng DDL SQL Server."
    )
    output_lines.append(
        "> 4. Toàn bộ quy tắc nghiệp vụ (73 Business Rules), ma trận kiểm thử, luồng người dùng và máy trạng thái (State Machines)."
    )
    output_lines.append(">")
    output_lines.append(
        "> Hãy sử dụng toàn bộ thông tin trong tài liệu này làm nguồn sự thật duy nhất (Single Source of Truth) khi người dùng hỏi, yêu cầu viết code, review code hoặc debug."
    )
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## 1. HƯỚNG DẪN QUAN TRỌNG DÀNH CHO GEMINI (CORE INVARIANTS)")
    output_lines.append("")
    output_lines.append(
        "Khi làm việc với dự án PWD301, Gemini **tuyệt đối không được vi phạm** các quy tắc bất biến sau:"
    )
    output_lines.append("")
    output_lines.append("### 1.1. Thứ bậc nguồn sự thật (Source-of-Truth Hierarchy)")
    output_lines.append(
        "1. `docs/system/PWD301_SYSTEM_SPECIFICATION/`: Đặc tả hành vi hệ thống và nghiệp vụ đã được xác nhận (Mức ưu tiên cao nhất)."
    )
    output_lines.append(
        "2. `docs/database/PWD301_DATABASE_ARCHITECTURE/`: Kiến trúc CSDL chuẩn duy nhất (Canonical SQL Server DDL gồm 71 bảng). Không tạo bản copy schema thứ hai."
    )
    output_lines.append("3. `README.md` (root): Kho tri thức tổng hợp toàn bộ dự án.")
    output_lines.append("4. `AGENTS.md`: Hợp đồng vận hành của Coding Agent.")
    output_lines.append(
        "5. `tasks/CURRENT.md`: Phạm vi công việc của tác vụ hiện tại (hiện đang là **TASK-001**)."
    )
    output_lines.append(
        "6. Mã nguồn và kiểm thử hiện có: Bằng chứng triển khai; nếu có mâu thuẫn với các tầng trên, phải coi mã nguồn là khiếm khuyết cần sửa, không được tự ý sửa đặc tả."
    )
    output_lines.append("")
    output_lines.append("### 1.2. Các quy tắc bất biến kỹ thuật và nghiệp vụ")
    output_lines.append(
        "- **Technology Stack**: Python 3.11+, Flask, Flask-SQLAlchemy, Flask-WTF, Flask-Login, Flask-Migrate (Alembic), Microsoft SQL Server, Jinja2, Bootstrap 5, Docker."
    )
    output_lines.append("- **Xác thực kép (Authentication Split)**:")
    output_lines.append(
        "  - Web UI / Jinja2 / AJAX: Dùng **Flask session cookies + CSRF protection**. Tuyệt đối **không** lưu JWT vào `localStorage` cho Web UI."
    )
    output_lines.append("  - REST API: Dùng **JWT Bearer token** theo chuẩn RFC 7519.")
    output_lines.append(
        "- **Khóa tài khoản (Suspension)**: Phải lập tức thu hồi/chặn active session và token JWT."
    )
    output_lines.append(
        "- **Quyền hạn giảng viên (Instructor Scope)**: Giảng viên chỉ được quản lý khóa học và sinh viên thuộc khóa học mà họ đang phụ trách."
    )
    output_lines.append(
        "- **Ghi danh (Enrollment)**: Tối đa 1 bản ghi `Enrollment` trạng thái `active` cho mỗi cặp `(Student, Course)`."
    )
    output_lines.append(
        "- **Tiên quyết (Prerequisites)**: Cấm tuyệt đối chu kỳ phụ thuộc (DAG validation required)."
    )
    output_lines.append("- **Ngân hàng câu hỏi & Bài thi (Assessment & Question Bank)**:")
    output_lines.append(
        "  - Dữ liệu câu hỏi lịch sử hiển thị cho sinh viên hoặc dùng chấm điểm phải được bảo lưu thông qua `QuestionRevision`."
    )
    output_lines.append(
        "  - `AssessmentAttempt` phải đóng băng snapshot câu hỏi/lựa chọn/điểm số tại thời điểm làm bài."
    )
    output_lines.append(
        "  - Thời gian thi (timing) khóa sau khi Publish. Cấu trúc câu hỏi khóa sau khi thí sinh đầu tiên bắt đầu làm bài."
    )
    output_lines.append("  - Nộp bài (Submit) phải đảm bảo **Idempotent** (chống double submit).")
    output_lines.append(
        "  - Chấm lại (Regrading) phải có khả năng tiếp tục (resumable) và lưu lịch sử điểm."
    )
    output_lines.append(
        "- **An toàn tệp tin (File Security)**: Thiết kế `Fail-closed`; tệp chưa quét virus hoặc đang cách ly không cho sinh viên truy cập."
    )
    output_lines.append(
        "- **Giới hạn video**: Video upload tối đa `< 1 GB` (các tài liệu cũ ghi `~2 GB` đã bị bãi bỏ)."
    )
    output_lines.append(
        "- **RAG & AI Chat**: Kiểm tra quyền truy cập trước khi truy xuất dữ liệu RAG (loại bỏ khóa học đã lưu trữ `archived`). Dữ liệu chat thô xóa sau 5 phút không hoạt động."
    )
    output_lines.append(
        "- **Audit Log**: Bản ghi Audit là `Append-only`. Nếu không ghi được Audit, hành động nhạy cảm phải bị từ chối."
    )
    output_lines.append(
        "- **Trạng thái hiện tại**: Dự án đang ở giai đoạn `TASK-001 — Project Foundation & Flask Bootstrap`."
    )
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## 2. TỔNG QUAN CẤU TRÚC THƯ MỤC (REPOSITORY DIRECTORY TREE)")
    output_lines.append("")
    output_lines.append(build_tree(files))
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## 3. MỤC LỤC TẤT CẢ TỆP TIN TRONG DỰ ÁN")
    output_lines.append("")
    for p in files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        anchor = make_anchor(rel)
        sz = p.stat().st_size
        output_lines.append(f"- [{rel}](#{anchor}) *({sz:,} bytes)*")

    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## 4. NỘI DUNG CHI TIẾT TOÀN BỘ TỆP TIN DỰ ÁN")
    output_lines.append("")

    for idx, p in enumerate(files, 1):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        anchor = make_anchor(rel)
        ext = p.suffix.lower() or p.name
        lang = EXT_LANG_MAP.get(ext, "")

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as err:
            content = f"[ERROR READING FILE: {err}]"

        lines_count = len(content.splitlines())
        size_bytes = p.stat().st_size

        output_lines.append(f'<a id="{anchor}"></a>')
        output_lines.append(f"### File [{idx}/{len(files)}]: `{rel}`")
        output_lines.append(f"- **Đường dẫn**: `{rel}`")
        output_lines.append(f"- **Kích thước**: {size_bytes:,} bytes | {lines_count:,} dòng")
        output_lines.append(f"- **Định dạng**: `{lang or 'text'}`")
        output_lines.append("")
        output_lines.append(chr(96) * 4 + lang)
        output_lines.append(content)
        output_lines.append(chr(96) * 4)
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    final_text = "\n".join(output_lines)

    tick3 = chr(96) * 3
    if final_text.count(tick3) % 2 != 0:
        final_text += f"\n<!-- Fence balance guard: {tick3} -->\n"

    OUTPUT_FILE.write_text(final_text, encoding="utf-8")
    ai_file = ROOT / "PROJECT_CONTEXT_FOR_GEMINI_AI.md"
    ai_file.write_text(final_text, encoding="utf-8")
    print(f"Successfully generated: {OUTPUT_FILE}")
    print(f"Successfully generated: {ai_file}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"Total lines: {len(final_text.splitlines()):,}")


if __name__ == "__main__":
    main()
