import json
from types import SimpleNamespace

import pytest

from pwd301.blueprints.instructor.routes import (
    _extract_video_urls_from_markdown,
    _validate_video_urls,
)
from pwd301.blueprints.student.routes import _serialize_student_lesson
from pwd301.services.exceptions import ValidationError
from pwd301.services.lesson_service import _lesson_requires_video_watch


def test_video_urls_accepts_two_youtube_links_and_preserves_order():
    urls = [f"https://www.youtube.com/watch?v=abcde1234{i}A" for i in range(2)]
    assert _validate_video_urls(urls) == urls


def test_video_urls_rejects_three_or_untrusted_links():
    urls = [f"https://www.youtube.com/watch?v=abcde1234{i}A" for i in range(3)]
    with pytest.raises(ValidationError):
        _validate_video_urls(urls)
    with pytest.raises(ValidationError):
        _validate_video_urls(["javascript:alert(1)"])


def test_existing_vimeo_link_remains_editable():
    assert _validate_video_urls(["https://vimeo.com/12345678"]) == ["https://vimeo.com/12345678"]


def test_youtube_live_link_is_accepted():
    assert _validate_video_urls(["https://www.youtube.com/live/abcde12345A"]) == [
        "https://www.youtube.com/watch?v=abcde12345A"
    ]


def test_video_urls_reads_legacy_single_link():
    assert _extract_video_urls_from_markdown(
        "<!-- video_url: https://youtu.be/abcde12345A -->"
    ) == ["https://youtu.be/abcde12345A"]


def test_student_lesson_exposes_all_links_without_metadata_comment():
    urls = ["https://www.youtube.com/watch?v=abcde12345A", "https://youtu.be/abcde12345B"]
    lesson = SimpleNamespace(
        public_id="lesson",
        course=SimpleNamespace(public_id="course"),
        title="Geometry",
        summary="",
        markdown_content=f"<!-- video_urls: {json.dumps(urls)} -->\nCâu hỏi hình học",
        position=1,
        estimated_duration_minutes=10,
        minimum_completion_seconds=0,
        viewed_fraction_required=1.0,
        resources=[],
    )
    result = _serialize_student_lesson(lesson, None)
    assert result["video_urls"] == urls
    assert result["video_url"] == urls[0]
    assert "video_urls" not in result["markdown_content"]
    assert _lesson_requires_video_watch(lesson)
