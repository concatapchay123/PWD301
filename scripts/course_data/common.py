"""Common helpers and validation routines for Black Hat Cybersecurity course generation."""

from __future__ import annotations

import re
from typing import Any


def count_vietnamese_words(text: str) -> int:
    """Count words in text, ignoring HTML comments and code fences if needed,
    or counting pure words separated by whitespace.
    """
    # Clean HTML comments like <!-- ... -->
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Split by whitespace
    words = [w for w in cleaned.split() if w.strip()]
    return len(words)


def validate_lesson_data(lesson: dict[str, Any]) -> None:
    """Validate that lesson satisfies all mandatory rules."""
    title = lesson.get("title", "")
    content = lesson.get("markdown_content", "")
    video_url = lesson.get("video_url", "")
    quiz = lesson.get("quiz", [])

    if not title:
        raise ValueError("Lesson title cannot be empty")

    word_count = count_vietnamese_words(content)
    if word_count < 600:
        raise ValueError(
            f"Lesson '{title}' has only {word_count} words! Minimum required is 600 words."
        )

    if not video_url or not video_url.startswith("https://www.youtube.com/watch?v="):
        raise ValueError(f"Lesson '{title}' must have a valid YouTube video URL.")

    if not quiz:
        # Extract from markdown_content <!-- mini_quiz: (...) -->
        import json
        m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", content, re.DOTALL)
        if m:
            try:
                quiz = json.loads(m.group(1))
            except Exception:
                quiz = []

    if not quiz or not isinstance(quiz, list) or len(quiz) < 3:
        raise ValueError(f"Lesson '{title}' must have a comprehensive quiz with at least 3 questions.")

    types_in_quiz = {q.get("type") for q in quiz}
    if not types_in_quiz:
        raise ValueError(f"Lesson '{title}' quiz has no valid question types.")
