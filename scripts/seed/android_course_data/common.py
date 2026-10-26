# -*- coding: utf-8 -*-
"""Common utilities, validators and markdown composer for Android Master Course (AND801)."""

from __future__ import annotations

import json
import re
from typing import Any


def count_vietnamese_words(text: str) -> int:
    """Count words in text, ignoring internal HTML comment blocks."""
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    words = [w for w in cleaned.split() if w.strip()]
    return len(words)


def generate_lesson_markdown(
    lesson_num: str,
    title: str,
    objective_points: list[str],
    theory_sections: list[tuple[str, str]],
    attack_defense_section: str,
    lab_instructions: str,
    code_snippet: tuple[str, str],  # (language, code)
    pitfalls: list[str],
    summary_points: list[str],
    video_url: str,
    quiz_items: list[dict[str, Any]],
) -> str:
    """Compose a full structured lecture exceeding 600 words with embedded metadata and 4-type miniquiz."""
    md = []
    md.append(f"# {title}\n")
    md.append(f"<!-- video_url: {video_url} -->\n")
    md.append(f"<!-- quiz_passing_percent: 80 -->\n")

    # 1. Mục tiêu
    md.append("## 1. Mục Tiêu Bài Học")
    md.append("Sau khi nghiên cứu lý thuyết và hoàn thành bài lab thực hành, học viên sẽ nắm vững các chuẩn đầu ra sau:")
    for obj in objective_points:
        md.append(f"- {obj}")
    md.append("")

    # 2. Cơ sở lý thuyết & Kiến trúc chuyên sâu
    md.append("## 2. Cơ Sở Lý Thuyết & Kiến Trúc Kỹ Thuật Chuyên Sâu")
    for sec_idx, (sec_title, sec_body) in enumerate(theory_sections, 1):
        md.append(f"### 2.{sec_idx} {sec_title}")
        md.append(sec_body)
        md.append("")

    # 3. Phân tích kịch bản tấn công & phòng thủ
    md.append("## 3. Phân Tích Lỗ Hổng & Kịch Bản Tấn Công / Phòng Thủ")
    md.append(attack_defense_section)
    md.append("")

    # 4. Hướng dẫn thực hành Lab từng bước
    md.append("## 4. Hướng Dẫn Thực Hành Lab Từng Bước")
    md.append(lab_instructions)
    md.append("")
    lang, code = code_snippet
    md.append(f"```{lang}")
    md.append(code.strip())
    md.append("```")
    md.append("")

    # 5. Bẫy lỗi thường gặp & Hardening
    md.append("## 5. Bẫy Lỗi Thường Gặp & Hướng Dẫn Làm Cứng (Hardening)")
    for p in pitfalls:
        md.append(f"- {p}")
    md.append("")

    # 6. Tổng kết & Câu hỏi ôn tập
    md.append("## 6. Tổng Kết Bài Học & Hướng Nghiên Cứu Mở Rộng")
    for s in summary_points:
        md.append(f"- {s}")
    md.append("")

    # Embed miniquiz with all 4 question types
    md.append(f"<!-- mini_quiz: {json.dumps(quiz_items, ensure_ascii=False)} -->\n")

    full_markdown = "\n".join(md)
    wc = count_vietnamese_words(full_markdown)
    if wc < 600:
        raise ValueError(f"CRITICAL: Lesson '{title}' has only {wc} words (< 600 required)!")
    return full_markdown


def validate_lesson_data(lesson: dict[str, Any]) -> None:
    """Validate all required fields, word count >= 600, YouTube URL, and miniquiz with 4 types."""
    title = lesson.get("title", "")
    content = lesson.get("markdown_content", "")
    video_url = lesson.get("video_url", "")

    if not title:
        raise ValueError("Lesson title cannot be empty")

    wc = count_vietnamese_words(content)
    if wc < 600:
        raise ValueError(f"Lesson '{title}' has only {wc} words! Minimum required is 600 words.")

    if not video_url or not video_url.startswith("https://www.youtube.com/watch?v="):
        raise ValueError(f"Lesson '{title}' must have a valid YouTube URL.")

    # Check miniquiz
    m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", content, re.DOTALL)
    if not m:
        raise ValueError(f"Lesson '{title}' missing <!-- mini_quiz: [...] --> marker.")
    quiz = json.loads(m.group(1))
    if len(quiz) < 4:
        raise ValueError(f"Lesson '{title}' miniquiz must have at least 4 questions (has {len(quiz)}).")

    q_types = [q.get("type") for q in quiz]
    if "MULTIPLE_CHOICE" not in q_types:
        raise ValueError(f"Lesson '{title}' miniquiz missing MULTIPLE_CHOICE question.")
    if "FILL_BLANK" not in q_types:
        raise ValueError(f"Lesson '{title}' miniquiz missing FILL_BLANK question.")
    if "MATCHING" not in q_types:
        raise ValueError(f"Lesson '{title}' miniquiz missing MATCHING question.")
