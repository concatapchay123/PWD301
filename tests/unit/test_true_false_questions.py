import pytest
from backend.services.lesson_service import (
    _lesson_quiz_answers_complete,
    _score_lesson_quiz_answers,
)


def test_lesson_quiz_true_false_validation():
    """Verify that lesson mini-quizzes correctly validate True/False answers."""
    questions = [
        {"type": "TRUE_FALSE", "correct_value": True, "question": "Trái Đất quay quanh Mặt Trời."},
        {"type": "TRUE_FALSE", "correct_value": False, "question": "Mặt Trời quay quanh Trái Đất."}
    ]

    # Valid boolean submissions
    assert _lesson_quiz_answers_complete(questions, [True, False]) is True
    assert _lesson_quiz_answers_complete(questions, [False, True]) is True

    # Valid string submissions ('true', 'false')
    assert _lesson_quiz_answers_complete(questions, ["true", "false"]) is True
    assert _lesson_quiz_answers_complete(questions, ["True", "False"]) is True

    # Incomplete or invalid submissions
    assert _lesson_quiz_answers_complete(questions, [True]) is False
    assert _lesson_quiz_answers_complete(questions, [True, "invalid"]) is False
    assert _lesson_quiz_answers_complete(questions, [None, False]) is False


def test_lesson_quiz_true_false_scoring():
    """Verify that lesson mini-quizzes correctly score True/False questions."""
    questions = [
        {"type": "TRUE_FALSE", "correct_value": True, "question": "Câu 1"},
        {"type": "TRUE_FALSE", "correct_value": False, "question": "Câu 2"}
    ]

    # 100% score: Both correct
    correct_count, total, percent = _score_lesson_quiz_answers(questions, [True, False])
    assert correct_count == 2
    assert total == 2
    assert percent == 100.0

    # 50% score: 1 correct, 1 wrong
    correct_count, total, percent = _score_lesson_quiz_answers(questions, [True, True])
    assert correct_count == 1
    assert total == 2
    assert percent == 50.0

    # 0% score: Both wrong
    correct_count, total, percent = _score_lesson_quiz_answers(questions, [False, True])
    assert correct_count == 0
    assert total == 2
    assert percent == 0.0

    # String values ('true' / 'false')
    correct_count, total, percent = _score_lesson_quiz_answers(questions, ["true", "false"])
    assert correct_count == 2
    assert percent == 100.0
