"""Regression coverage for Moodle question image extraction safety."""

from unittest.mock import patch

import pwd301.services.moodle_exam_service as moodle_exam_service


def _moodle_question(question_text: str, files: str = "", name: str = "Geometry") -> str:
    return f"""<quiz>
      <question type="multichoice">
        <name><text>{name}</text></name>
        <questiontext format="html"><text><![CDATA[{question_text}]]></text>{files}</questiontext>
        <single>true</single>
        <answer fraction="100"><text>A</text></answer>
        <answer fraction="0"><text>B</text></answer>
      </question>
    </quiz>"""


def test_moodle_image_only_question_uses_question_name_and_keeps_image() -> None:
    xml = _moodle_question(
        '<img src="@@PLUGINFILE@@/triangle.png"/>',
        '<file name="triangle.png" path="/" encoding="base64">aW1hZ2U=</file>',
    )

    result = moodle_exam_service.parse_moodle_xml(xml)

    assert result["total_questions"] == 1
    question = result["questions"][0]
    assert question["stem"] == "Geometry"
    assert question["images"][0]["broken"] is False


def test_moodle_unresolved_or_invalid_image_is_reported_as_broken() -> None:
    xml = _moodle_question(
        '<p>Choose the shown angle.</p><img src="@@PLUGINFILE@@/missing.png"/>',
        '<file name="broken.png" path="/" encoding="base64">%%%not-base64%%%</file>',
    )

    result = moodle_exam_service.parse_moodle_xml(xml)

    assert result["total_questions"] == 1
    assert result["questions"][0]["images"][0]["broken"] is True
    assert any("hình ảnh" in warning.lower() for warning in result["warnings"])


def test_moodle_keeps_remote_image_reference_visible_for_review() -> None:
    xml = _moodle_question('<img src="https://example.invalid/diagram.png"/>')

    result = moodle_exam_service.parse_moodle_xml(xml)

    assert result["total_questions"] == 1
    question = result["questions"][0]
    assert question["stem"] == "Geometry"
    assert question["images"][0]["broken"] is True
    assert any("hình ảnh" in warning.lower() for warning in result["warnings"])


def test_moodle_rejects_oversized_base64_before_decoding() -> None:
    xml = _moodle_question(
        '<p>Choose the shown angle.</p><img src="@@PLUGINFILE@@/triangle.png"/>',
        '<file name="triangle.png" path="/" encoding="base64">AAAAAAAAAAAA</file>',
    )

    with (
        patch.object(moodle_exam_service, "MAX_EMBEDDED_IMAGE_BYTES", 8),
        patch.object(
            moodle_exam_service.base64,
            "b64decode",
            side_effect=AssertionError("oversized content must be rejected before decoding"),
        ),
    ):
        result = moodle_exam_service.parse_moodle_xml(xml)

    assert result["questions"][0]["images"][0]["broken"] is True
    assert any("hình ảnh" in warning.lower() for warning in result["warnings"])
