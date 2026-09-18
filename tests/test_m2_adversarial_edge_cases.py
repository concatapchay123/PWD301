"""Adversarial challenge tests for Milestone 2: Parsing & Rendering Edge Cases.

Empirically tests:
1. Course._parse_string_list with:
   - None, empty string "", whitespace only "   \n\t  "
   - Valid JSON arrays (simple, unicode, mixed types, empty array, array with whitespace)
   - Malformed/Edge-case JSON strings:
     - Unescaped control characters (e.g. raw tab inside JSON string literal)
     - Trailing comma in JSON: '["A", "B",]'
     - Single quotes JSON: "['Item 1', 'Item 2']"
     - Starts with '[' and ends with ']' but invalid JSON syntax inside
     - Non-array JSON (e.g. object '{"a": 1}')
   - Newline-delimited strings with blank lines, leading/trailing whitespace, mixed CRLF/LF
   - Massive multiline strings (10,000 lines, 1MB payload)
2. Student course_detail view when course has None, empty, whitespace, or malformed fields:
   - None learning objectives, target audience, completion requirements, and description
   - Empty strings vs whitespace-only strings ("   \n\t  \n  ")
   - XSS payload in objectives and audience (verify auto-escaping)
3. Completion rule rendering under diverse edge cases:
   - Rule is None with/without completion_requirements
   - minimum_progress_percent = 0.0 (boundary check for falsey 0)
   - minimum_progress_percent = 100.0
   - minimum_progress_percent = None with mixed boolean flags
   - All flags False, all flags True
"""

from __future__ import annotations

import json
import uuid

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import _parse_string_list
from pwd301.models.identity import Role, User
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def test_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess: Session = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def m2_instructor(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create an instructor user for edge case testing."""
    email = f"inst_edge_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Edge Case")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def m2_student(app: Flask, test_roles: dict[str, Role]) -> User:
    """Create a student user for edge case testing."""
    email = f"stud_edge_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Student Edge Case")
    return assign_role_to_user(u.id, "STUDENT")


# ==============================================================================
# 1. Adversarial Tests for Course._parse_string_list
# ==============================================================================


class TestParseStringListEdgeCases:
    """Adversarial stress-testing of _parse_string_list."""

    def test_none_empty_and_whitespace(self) -> None:
        """Test None, empty string, and various whitespace variants."""
        assert _parse_string_list(None) == []
        assert _parse_string_list("") == []
        assert _parse_string_list("   ") == []
        assert _parse_string_list("\t\n\r  \n  \t") == []
        assert _parse_string_list("\n\n\n") == []

    def test_valid_json_arrays(self) -> None:
        """Test valid JSON arrays of various shapes using standard json.dumps."""
        # Simple array
        assert _parse_string_list('["Item 1", "Item 2"]') == ["Item 1", "Item 2"]

        # Formatted JSON with whitespace inside items
        formatted_json = json.dumps(
            [
                "  Python Architecture  ",
                "   Microservices Design \t",
                "   ",
            ],
            indent=4,
        )
        assert _parse_string_list(formatted_json) == [
            "Python Architecture",
            "Microservices Design",
        ]

        # Empty array
        assert _parse_string_list("[]") == []
        assert _parse_string_list("[   ]") == []

        # Unicode / Vietnamese array
        vn_json = json.dumps(["Lập trình hướng đối tượng", "Kiến trúc hệ thống phân tán"])
        assert _parse_string_list(vn_json) == [
            "Lập trình hướng đối tượng",
            "Kiến trúc hệ thống phân tán",
        ]

        # Array with non-string primitive items (integers, booleans, floats)
        mixed_json = json.dumps([101, 202.5, True, False])
        assert _parse_string_list(mixed_json) == ["101", "202.5", "True", "False"]

    def test_json_with_unescaped_control_character_behavior(self) -> None:
        """JSON string with raw literal tab character fails strict json.loads."""
        # Raw tab inside JSON string literal (RFC 8259 violation without escape)
        raw_tab_json = '[\n  "Python\tArchitecture"\n]'
        # Due to strict=True in json.loads, this raises JSONDecodeError and falls back to splitlines
        result = _parse_string_list(raw_tab_json)
        # Note: it falls back to newline split, preserving lines:
        assert "[" in result[0]

    def test_trailing_comma_json_falls_back_to_newlines(self) -> None:
        """JSON with trailing comma (invalid strict JSON) falls back to splitlines."""
        trailing_comma = '[\n  "Item A",\n  "Item B",\n]'
        result = _parse_string_list(trailing_comma)
        # Because json.loads fails on trailing comma, it splits by line
        assert len(result) == 4
        assert result[0] == "["
        assert '"Item A",' in result[1]
        assert result[3] == "]"

    def test_single_quotes_array_falls_back_to_newlines(self) -> None:
        """Single-quoted array (Python style) fails json.loads and returns single line."""
        single_quote = "['Item 1', 'Item 2']"
        result = _parse_string_list(single_quote)
        assert result == ["['Item 1', 'Item 2']"]

    def test_invalid_json_strings_fallback_to_newlines(self) -> None:
        """Test invalid JSON strings fallback gracefully to newline-delimited parsing."""
        # 1. Starts with '[' but does not end with ']'
        assert _parse_string_list("[broken json") == ["[broken json"]

        # 2. JSON object instead of array
        assert _parse_string_list("{invalid}") == ["{invalid}"]

        # 3. Starts with '[' and ends with ']' but invalid syntax inside
        assert _parse_string_list("[broken json]") == ["[broken json]"]
        assert _parse_string_list("[1, 2, unquoted_val]") == ["[1, 2, unquoted_val]"]

        # 4. Multiline invalid JSON
        multiline_broken = "[line 1\nline 2\nline 3]"
        assert _parse_string_list(multiline_broken) == ["[line 1", "line 2", "line 3]"]

    def test_newline_delimited_strings(self) -> None:
        """Test newline-delimited strings with blank lines and irregular spacing."""
        # Leading/trailing blank lines and whitespace
        text = "\n\n  Objective Alpha  \n   \n\t  Objective Beta  \n\n  Objective Gamma \n\n"
        assert _parse_string_list(text) == [
            "Objective Alpha",
            "Objective Beta",
            "Objective Gamma",
        ]

        # Mixed Windows (CRLF) and Unix (LF) and Mac (CR) line endings
        mixed_endings = "Line 1\r\nLine 2\nLine 3\rLine 4\r\n\r\nLine 5"
        assert _parse_string_list(mixed_endings) == [
            "Line 1",
            "Line 2",
            "Line 3",
            "Line 4",
            "Line 5",
        ]

        # Single line with no newlines
        assert _parse_string_list("Sole Requirement") == ["Sole Requirement"]

    def test_massive_multiline_strings(self) -> None:
        """Stress-test parser performance with massive inputs (10,000 lines)."""
        lines_count = 10000
        massive_text = "\n".join(f"  Learning Objective #{i}  " for i in range(lines_count))
        result = _parse_string_list(massive_text)
        assert len(result) == lines_count
        assert result[0] == "Learning Objective #0"
        assert result[-1] == f"Learning Objective #{lines_count - 1}"

        # Massive JSON array
        massive_json = json.dumps([f"Target Audience #{i}" for i in range(lines_count)])
        result_json = _parse_string_list(massive_json)
        assert len(result_json) == lines_count
        assert result_json[0] == "Target Audience #0"

        # 1MB multiline payload
        one_mb_payload = ("A" * 100 + "\n") * 10000
        result_1mb = _parse_string_list(one_mb_payload)
        assert len(result_1mb) == 10000
        assert result_1mb[0] == "A" * 100
