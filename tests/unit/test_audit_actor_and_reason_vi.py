# -*- coding: utf-8 -*-
"""Unit tests for Audit Log Actor Name and Vietnamese Reason Localization."""

import pytest
from backend.models.notification_audit import AuditEvent, _localize_audit_reason


def test_localize_audit_reason_mappings():
    assert (
        _localize_audit_reason(
            "Client attempted to forge 100% completion via zero-time reconcile bypass without required dwell time or video watch."
        )
        == "Phát hiện hành vi gian lận tiến độ học: Bỏ qua thời lượng học thực tế hoặc xem video bằng yêu cầu đồng bộ tức thì."
    )
    assert (
        _localize_audit_reason("Student started attempt #3")
        == "Học viên bắt đầu làm bài thi (lần thi #3)"
    )
    assert (
        _localize_audit_reason("Student submitted attempt #2")
        == "Học viên đã nộp bài thi (lần thi #2)"
    )
    assert (
        _localize_audit_reason("Reordered 12 questions")
        == "Đã sắp xếp lại thứ tự 12 câu hỏi"
    )
    assert (
        _localize_audit_reason("Course completion criteria satisfied")
        == "Đã thỏa mãn đầy đủ điều kiện hoàn thành khóa học"
    )
    assert (
        _localize_audit_reason("Updated lesson metadata")
        == "Cập nhật thông tin bài học"
    )


def test_audit_event_to_dict_localization():
    event = AuditEvent(
        action="SECURITY_ALERT_PROGRESS_FORGERY_ATTEMPT",
        actor_user_id=1,
        actor_roles_snapshot="ADMIN,INSTRUCTOR",
        target_type="Lesson",
        target_id=10,
        reason="Client attempted to forge 100% completion via zero-time reconcile bypass without required dwell time or video watch.",
    )
    d = event.to_dict()
    assert (
        d["reason"]
        == "Phát hiện hành vi gian lận tiến độ học: Bỏ qua thời lượng học thực tế hoặc xem video bằng yêu cầu đồng bộ tức thì."
    )
    assert d["action"] == "SECURITY_ALERT_PROGRESS_FORGERY_ATTEMPT"
