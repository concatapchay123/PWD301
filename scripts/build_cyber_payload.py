"""Comprehensive lesson generator for all 5 chapters of Black Hat Cybersecurity course.
Generates 60 lessons across 5 chapters, each guaranteed to exceed 600 words,
with authentic Vietnamese cybersecurity curriculum, labs, code, and quizzes.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.course_data.common import count_vietnamese_words, validate_lesson_data


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
    quiz_json: list[dict],
) -> str:
    """Compose a full structured lecture of at least 700-1200 words."""
    md = []
    md.append(f"# {title}\n")
    md.append(f"<!-- video_url: {video_url} -->\n")
    md.append(f"<!-- quiz_passing_percent: 80 -->\n")

    # 1. Mục tiêu
    md.append("## 1. Mục Tiêu Bài Học")
    md.append("Sau khi nghiên cứu và thực hành bài học này, học viên sẽ đạt được các chuẩn đầu ra sau:")
    for obj in objective_points:
        md.append(f"- {obj}")
    md.append("")

    # 2. Cơ sở lý thuyết & Kiến trúc kỹ thuật chuyên sâu
    md.append("## 2. Cơ Sở Lý Thuyết & Kiến Trúc Kỹ Thuật Chuyên Sâu")
    for sec_title, sec_body in theory_sections:
        md.append(f"### 2.{len(md)} {sec_title}")
        md.append(sec_body)
        md.append("")

    # 3. Phân tích kịch bản tấn công & phòng thủ thực tế
    md.append("## 3. Phân Tích Kịch Bản Tấn Công & Phòng Thủ Thực Tế")
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

    # 5. Bẫy lỗi thường gặp & Biện pháp khắc phục
    md.append("## 5. Bẫy Lỗi Thường Gặp & Hướng Dẫn Làm Cứng (Hardening)")
    for pitfall in pitfalls:
        md.append(f"- {pitfall}")
    md.append("")

    # 6. Tổng kết bài học & Nghiên cứu mở rộng
    md.append("## 6. Tổng Kết & Gợi Ý Nghiên Cứu Mở Rộng")
    for sm in summary_points:
        md.append(f"- {sm}")
    md.append("")

    # Embed miniquiz
    md.append(f"<!-- mini_quiz: {json.dumps(quiz_json, ensure_ascii=False)} -->\n")

    full_text = "\n".join(md)
    wc = count_vietnamese_words(full_text)
    if wc < 600:
        raise ValueError(f"CRITICAL: Lesson '{title}' has only {wc} words (< 600)!")
    return full_text
