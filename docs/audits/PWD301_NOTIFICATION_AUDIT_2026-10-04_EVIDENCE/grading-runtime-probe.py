"""Disposable SQL Server grading/notification reproduction, never a live DB repair."""

from __future__ import annotations

import argparse
import html
import json
import os
import secrets
import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from flask_migrate import upgrade
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.attempt_regrade import AssessmentAttempt, AssessmentResultHistory
from pwd301.models.course import Course, Lesson
from pwd301.models.file_import import LessonResource
from pwd301.models.identity import User
from pwd301.models.notification_audit import (
    AuditEvent,
    EmailDelivery,
    Notification,
    NotificationEvent,
)
from pwd301.models.question_bank import Question
from pwd301.seeds import seed_baseline, seed_demo
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.auth_token_service import (
    SecurityTokenPurpose,
    create_security_token,
    reset_password_with_token,
)
from pwd301.services.course_service import (
    _course_notification_event_key,
    change_course_status,
    create_course,
)
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.question_bank_service import create_question, create_question_revision
from pwd301.services.user_service import (
    assign_role_to_user,
    change_password,
    register_user,
    suspend_user,
)

DATABASE_NAME = "PWD301_AUDIT_GRADE_20261005_1B3A"
COURSE_CODE = "AUDN1005"
ASSESSMENT_TITLE = "Audit thông báo chấm điểm 2026-10-05"
RUNTIME_URL = "http://127.0.0.1:5105"
SQL_GATE_DATABASES = (
    "PWD301_AUDIT_MIG_20261005_1B3A",
    "PWD301_AUDIT_RACE_20261005_1B3A",
)
SUBADMIN_FIXTURES = {
    "ADMIN_COURSE_REVIEW": "audit.course.review@pwd301.local",
    "ADMIN_INSTRUCTOR_REVIEW": "audit.instructor.review@pwd301.local",
    "ADMIN_TEACHING_ASSIGNMENT": "audit.teaching.assignment@pwd301.local",
    "ADMIN_SYSTEM_MONITORING": "audit.system.monitoring@pwd301.local",
}


def base_url():
    source_app = create_app("development")
    url = make_url(source_app.config["SQLALCHEMY_DATABASE_URI"])
    if url.get_backend_name() != "mssql" or url.database == DATABASE_NAME:
        raise RuntimeError("A non-audit SQL Server source connection is required.")
    return url


def audit_app(url):
    os.environ["DATABASE_URL"] = url.set(database=DATABASE_NAME).render_as_string(
        hide_password=False
    )
    app = create_app("development")
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        SESSION_COOKIE_NAME="pwd301_audit_grade",
    )
    with app.app_context():
        if db.engine.url.database != DATABASE_NAME:
            raise RuntimeError("Audit database boundary mismatch.")
    return app


def prepare(url):
    master = create_engine(url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with master.connect() as connection:
            exists = connection.execute(
                text("SELECT COUNT(*) FROM sys.databases WHERE name = :name"),
                {"name": DATABASE_NAME},
            ).scalar_one()
            if exists:
                raise RuntimeError("Refusing to overwrite an existing audit database.")
            connection.exec_driver_sql(f"CREATE DATABASE [{DATABASE_NAME}]")
    finally:
        master.dispose()
    app = audit_app(url)
    with app.app_context():
        upgrade(directory="migrations")
        seed_baseline(db.session)
        seed_demo(db.session)
        instructor = db.session.query(User).filter_by(email="instructor2@pwd301.local").one()
        student = db.session.query(User).filter_by(email="student4@pwd301.local").one()
        admin = db.session.query(User).filter_by(email="admin@pwd301.local").one()
        course = create_course(
            instructor,
            {
                "course_code": COURSE_CODE,
                "title": "Audit notification — SQL Server disposable fixture",
                "level": "INTERMEDIATE",
            },
        )
        change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
        change_course_status(admin, course.id, "APPROVED")
        change_course_status(admin, course.id, "PUBLISHED")
        enroll_student(student, course.id)
        now = datetime.now(UTC)
        assessment = create_assessment(
            instructor,
            course.id,
            {
                "title": ASSESSMENT_TITLE,
                "assessment_type": "FINAL",
                "score_release_policy": "IMMEDIATE",
                "time_limit_minutes": 60,
                "open_at": (now - timedelta(hours=1)).isoformat(),
                "close_at": (now + timedelta(days=1)).isoformat(),
                "passing_percent": 60,
            },
        )
        section = create_section(instructor, assessment.id, {"title": "Audit grading"})
        objective = create_question(
            instructor,
            course.id,
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "Audit đáp án cần hiệu chỉnh: A hay B?",
                "default_points": 10,
                "choices": [
                    {"content": "A", "is_correct": True, "position": 1},
                    {"content": "B", "is_correct": False, "position": 2},
                ],
            },
        )
        essay = create_question(
            instructor,
            course.id,
            {
                "question_type": "ESSAY",
                "difficulty": "APPLY",
                "content": "Giải thích cách bảo toàn tính idempotent của một thao tác.",
                "default_points": 20,
                "rubric": "Khóa định danh 10 điểm; xử lý tương tranh 10 điểm.",
            },
        )
        for question, points in [(objective, 10), (essay, 20)]:
            assign_question(
                instructor,
                assessment.id,
                {
                    "question_id": question.id,
                    "points": points,
                    "section_id": section.id,
                },
            )
        publish_assessment(instructor, assessment.id)
        db.session.commit()
        attempt, lease = start_assessment_attempt(student, assessment.id)
        objective_snapshot = next(
            q for q in attempt.attempt_questions if q.question_type_snapshot == "SINGLE_CHOICE"
        )
        essay_snapshot = next(
            q for q in attempt.attempt_questions if q.question_type_snapshot == "ESSAY"
        )
        choice_b = next(c for c in objective_snapshot.choice_snapshots if c.content_snapshot == "B")
        save_attempt_answer(
            student,
            str(attempt.public_id),
            str(objective_snapshot.public_id),
            {
                "client_sequence": 1,
                "selected_choice_keys": [str(choice_b.choice_key_snapshot)],
            },
            raw_lease_token=lease,
        )
        save_attempt_answer(
            student,
            str(attempt.public_id),
            str(essay_snapshot.public_id),
            {
                "client_sequence": 2,
                "answer_text": "Dùng khóa idempotency và ràng buộc duy nhất để hội tụ các request trùng.",
            },
            raw_lease_token=lease,
        )
        submit_assessment_attempt(student, str(attempt.public_id), raw_lease_token=lease)
        db.session.commit()
        print(
            json.dumps(
                {
                    "database": DATABASE_NAME,
                    "course_id": str(course.public_id),
                    "assessment_id": str(assessment.public_id),
                    "attempt_id": str(attempt.public_id),
                    "essay_snapshot_id": str(essay_snapshot.public_id),
                    "status": attempt.status,
                },
                ensure_ascii=False,
            )
        )


def status(app):
    with app.app_context():
        course = db.session.query(Course).filter_by(course_code=COURSE_CODE).one()
        attempt = (
            db.session.query(AssessmentAttempt)
            .join(AssessmentAttempt.assessment)
            .filter_by(title=ASSESSMENT_TITLE)
            .one()
        )
        notices = (
            db.session.query(Notification, NotificationEvent)
            .join(
                NotificationEvent,
                Notification.notification_event_id == NotificationEvent.id,
            )
            .filter(Notification.title.contains(ASSESSMENT_TITLE))
            .all()
        )
        print(
            json.dumps(
                {
                    "database": db.engine.url.database,
                    "course_id": str(course.public_id),
                    "assessment_id": str(attempt.assessment.public_id),
                    "attempt_id": str(attempt.public_id),
                    "status": attempt.status,
                    "raw_score": str(attempt.result.raw_score),
                    "score_status": attempt.result.status,
                    "questions": [
                        {
                            "id": str(q.public_id),
                            "type": q.question_type_snapshot,
                            "row_version": q.current_grade.row_version.hex()
                            if q.current_grade and q.current_grade.row_version
                            else None,
                        }
                        for q in attempt.attempt_questions
                    ],
                    "result_history": [
                        {"old": str(h.old_score), "new": str(h.new_score), "reason": h.reason_code}
                        for h in db.session.query(AssessmentResultHistory)
                        .filter_by(attempt_id=attempt.id)
                        .order_by(AssessmentResultHistory.id)
                    ],
                    "notifications": [
                        {
                            "id": str(n.public_id),
                            "event_type": e.event_type,
                            "title": n.title,
                            "body": n.body,
                            "role": n.target_role,
                            "recipient": n.recipient.email,
                            "payload": json.loads(e.payload_json or "{}"),
                        }
                        for n, e in notices
                    ],
                },
                ensure_ascii=False,
            )
        )


def correct_answer(app):
    with app.app_context():
        course = db.session.query(Course).filter_by(course_code=COURSE_CODE).one()
        instructor = db.session.query(User).filter_by(email="instructor2@pwd301.local").one()
        question = (
            db.session.query(Question)
            .filter(
                Question.course_id == course.id,
                Question.current_revision.has(question_type="SINGLE_CHOICE"),
            )
            .one()
        )
        revision = max(question.revisions, key=lambda item: item.revision_no)
        _, correction = create_question_revision(
            instructor,
            question.id,
            {
                "change_type": "ANSWER_CHANGE",
                "correction_type": "ANSWER_ONLY",
                "change_reason": "Audit hiệu chỉnh đáp án: B đúng, bảo toàn snapshot cũ.",
                "choices": [
                    {
                        "choice_key": str(c.choice_key),
                        "content": c.content,
                        "is_correct": c.content == "B",
                        "position": c.position,
                    }
                    for c in revision.choices
                ],
            },
        )
        db.session.commit()
        print(json.dumps({"correction_created": correction is not None}))


def http_request(method, path, token=None, payload=None, extra_headers=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(RUNTIME_URL + path, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def login_token(email):
    code, body = http_request(
        "POST",
        "/api/v1/auth/login",
        payload={
            "email": email,
            "password": "Password123!",
        },
    )
    assert code == 200, f"Demo login failed: {code}"
    return body["access_token"]


def flag_status(app, phase):
    """Read only the owned CS301 fixture; never infer persistence from HTTP status."""
    with app.app_context():
        course = db.session.query(Course).filter_by(course_code="CS301").one()
        lesson = db.session.query(Lesson).filter_by(course_id=course.id).one()
        events = db.session.query(NotificationEvent).filter_by(event_type="COURSE_CONTENT_FLAGGED")
        event_ids = events.with_entities(NotificationEvent.id)
        result = {
            "phase": phase,
            "database": db.engine.url.database,
            "course_id": str(course.public_id),
            "lesson_id": str(lesson.public_id),
            "lesson_flag": lesson.material_change_summary,
            "audits": db.session.query(AuditEvent)
            .filter_by(action="CONTENT_FLAGGED", target_type="LESSON", target_id=lesson.id)
            .count(),
            "events": events.count(),
            "notices": db.session.query(Notification)
            .filter(Notification.notification_event_id.in_(event_ids))
            .count(),
        }
        print(json.dumps(result, ensure_ascii=False))
        return result


def flag_probe(app):
    """Capture REST boundaries and return nonzero when the expected workflow fails."""
    baseline = flag_status(app, "before_rest_probe")
    course_id, lesson_id = baseline["course_id"], baseline["lesson_id"]
    path = f"/api/admin/courses/{course_id}/lessons/{lesson_id}/flag"
    tokens = {
        role: login_token(email)
        for role, email in {
            "ADMIN": "admin@pwd301.local",
            "INSTRUCTOR": "instructor2@pwd301.local",
            "STUDENT": "student4@pwd301.local",
        }.items()
    }
    reason = "Audit 2026-10-05: bổ sung nguồn trích dẫn cho nội dung LLM."
    cases = [
        ("guest_denied", None, path, {"reason": reason}, 401),
        ("instructor_denied", "INSTRUCTOR", path, {"reason": reason}, 403),
        ("student_denied", "STUDENT", path, {"reason": reason}, 403),
        ("empty_reason", "ADMIN", path, {"reason": ""}, 400),
        ("four_character_reason", "ADMIN", path, {"reason": "abcd"}, 400),
        (
            "missing_lesson",
            "ADMIN",
            f"/api/admin/courses/{course_id}/lessons/00000000-0000-0000-0000-000000000001/flag",
            {"reason": reason},
            404,
        ),
        ("json_string", "ADMIN", path, "invalid", 400),
        ("json_nonempty_list", "ADMIN", path, ["invalid"], 400),
        ("valid_reason", "ADMIN", path, {"reason": reason}, 200),
        ("five_character_reason", "ADMIN", path, {"reason": "abcde"}, 200),
    ]
    failed = 0
    for case, role, endpoint, payload, expected_status in cases:
        code, body = http_request("POST", endpoint, token=tokens.get(role), payload=payload)
        matched = code == expected_status
        failed += int(not matched)
        print(
            json.dumps(
                {
                    "case": case,
                    "role": role or "GUEST",
                    "expected_status": expected_status,
                    "status": code,
                    "matches_expected": matched,
                    "response": body,
                },
                ensure_ascii=False,
            )
        )
        current = flag_status(app, f"after_{case}")
        if code != 200:
            for key in ("lesson_flag", "audits", "events", "notices"):
                if current[key] != baseline[key]:
                    raise RuntimeError(f"Rejected flag operation changed durable {key}.")
    print(json.dumps({"cases": len(cases), "failed_expectations": failed, "skipped": 0}))
    return int(failed > 0)


def prepare_subadmins(app):
    """Create only disposable synthetic identities via existing account/role services."""
    with app.app_context():
        admin = db.session.query(User).filter_by(email="admin@pwd301.local").one()
        for sub_role, email in SUBADMIN_FIXTURES.items():
            user = db.session.query(User).filter_by(email=email).first()
            if user is None:
                user = register_user(email, "Password123!", f"Audit {sub_role}")
                user = assign_role_to_user(
                    user.id,
                    "ADMIN",
                    assigned_by_user_id=admin.id,
                    admin_sub_role=sub_role,
                    reason="Audit 2026-10-05: xác minh quyền và thông báo Admin phụ trên DB tạm.",
                )
            elif user.admin_sub_role != sub_role:
                raise RuntimeError(f"Refusing to alter existing synthetic identity {email}.")
            notice_rows = (
                db.session.query(Notification, NotificationEvent)
                .join(
                    NotificationEvent,
                    Notification.notification_event_id == NotificationEvent.id,
                )
                .filter(
                    Notification.recipient_user_id == user.id,
                    NotificationEvent.event_type == "ROLE_CHANGED",
                )
                .all()
            )
            print(
                json.dumps(
                    {
                        "database": db.engine.url.database,
                        "email": email,
                        "roles": sorted(user.role_codes),
                        "admin_sub_role": user.admin_sub_role,
                        "course_review_allowed": user.has_admin_permission("COURSE_REVIEW"),
                        "role_audits": db.session.query(AuditEvent)
                        .filter_by(
                            action="USER_ROLE_ASSIGNED", target_type="USER", target_id=user.id
                        )
                        .count(),
                        "notices": [
                            {
                                "id": str(notice.public_id),
                                "event_key": str(event.event_key),
                                "event_type": event.event_type,
                                "title": notice.title,
                                "body": notice.body,
                                "action_url": notice.to_dict()["action_url"],
                                "target_role": notice.target_role,
                                "is_read": notice.is_read,
                            }
                            for notice, event in notice_rows
                        ],
                    },
                    ensure_ascii=False,
                )
            )
            if len(notice_rows) != 1 or user.admin_sub_role != sub_role:
                raise RuntimeError("Synthetic role assignment/notice did not persist as expected.")


def probe_subadmins(app):
    baseline = flag_status(app, "before_subadmin_probe")
    endpoint = f"/api/admin/courses/{baseline['course_id']}/lessons/{baseline['lesson_id']}/flag"
    failures = 0
    for sub_role, email in SUBADMIN_FIXTURES.items():
        token = login_token(email)
        list_status, list_body = http_request("GET", "/api/notifications?role=ADMIN", token=token)
        items = list_body.get("items", [])
        list_matches = (
            list_status == 200
            and len(items) == 1
            and items[0].get("event_type") == "ROLE_CHANGED"
            and items[0].get("is_read") in (True, False)
        )
        failures += int(not list_matches)
        print(
            json.dumps(
                {
                    "case": "own_role_notice_list_after_browser",
                    "sub_role": sub_role,
                    "status": list_status,
                    "response_keys": sorted(list_body),
                    "total": list_body.get("total"),
                    "unread_count": list_body.get("unread_count"),
                    "items": items,
                    "matches_expected": list_matches,
                },
                ensure_ascii=False,
            )
        )
        expected = 200 if sub_role == "ADMIN_COURSE_REVIEW" else 403
        before = flag_status(app, f"before_{sub_role}")
        code, body = http_request(
            "POST",
            endpoint,
            token=token,
            payload={"reason": "Audit 2026-10-05: xác minh phạm vi quyền Admin phụ."},
        )
        failures += int(code != expected)
        print(
            json.dumps(
                {
                    "sub_role": sub_role,
                    "expected_status": expected,
                    "status": code,
                    "matches_expected": code == expected,
                    "response": body,
                },
                ensure_ascii=False,
            )
        )
        current = flag_status(app, f"after_{sub_role}")
        if code != 200 and any(
            current[key] != before[key] for key in ("lesson_flag", "audits", "events", "notices")
        ):
            raise RuntimeError("Rejected Sub-Admin operation mutated durable moderation state.")
    print(json.dumps({"cases": 8, "failed_expectations": failures, "skipped": 0}))
    return int(failures > 0)


def flag_idempotency_probe(app):
    """Verify SQL-backed lesson-flag retries converge to one durable outcome."""
    baseline = flag_status(app, "before_flag_idempotency_probe")
    path = f"/api/admin/courses/{baseline['course_id']}/lessons/{baseline['lesson_id']}/flag"
    token = login_token("admin@pwd301.local")
    key = str(uuid.uuid4())
    headers = {"X-Idempotency-Key": key}
    payload = {
        "reason": "Audit retry safety",
        "content_type": "lesson",
    }

    first_code, first_body = http_request(
        "POST", path, token=token, payload=payload, extra_headers=headers
    )
    second_code, second_body = http_request(
        "POST", path, token=token, payload=payload, extra_headers=headers
    )
    conflict_code, conflict_body = http_request(
        "POST",
        path,
        token=token,
        payload={**payload, "reason": "Audit changed retry"},
        extra_headers=headers,
    )
    after = flag_status(app, "after_flag_idempotency_probe")
    result = {
        "first": {
            "http": first_code,
            "idempotent_replay": first_body.get("idempotent_replay"),
        },
        "second": {
            "http": second_code,
            "idempotent_replay": second_body.get("idempotent_replay"),
        },
        "changed_payload": {
            "http": conflict_code,
            "error_code": conflict_body.get("error", {}).get("code"),
        },
        "durable_deltas": {
            key: after[key] - baseline[key]
            for key in ("audits", "events", "notices")
        },
        "skipped": 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    expected = (
        first_code == 200
        and first_body.get("idempotent_replay") is False
        and second_code == 200
        and second_body.get("idempotent_replay") is True
        and conflict_code == 409
        and conflict_body.get("error", {}).get("code") == "CONFLICT"
        and result["durable_deltas"] == {"audits": 1, "events": 1, "notices": 1}
    )
    print(json.dumps({"cases": 3, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def notification_copy_probe(app):
    """Verify SQL-backed distinct events with identical copy stay visible in REST."""
    title = f"AUDIT_COPY_VISIBILITY_{uuid.uuid4().hex[:10]}"
    body = "Two distinct events intentionally share this copy."
    fixed_key = uuid.uuid4()
    with app.app_context():
        student = db.session.query(User).filter_by(email="student4@pwd301.local").one()
        from pwd301.services.exceptions import ConflictError
        from pwd301.services.notification_service import dispatch_notification, emit_event

        dispatch_notification(
            student,
            "SYSTEM_NOTICE",
            title,
            body,
            category="SYSTEM",
            session=db.session,
        )
        dispatch_notification(
            student,
            "COURSE_ANNOUNCEMENT",
            title,
            body,
            category="COURSE",
            session=db.session,
        )
        emit_event(
            event_type="AUDIT_IDEMPOTENCY",
            payload={"value": 1},
            actor_user_id=student.id,
            target_type="USER",
            target_id=student.id,
            event_key=fixed_key,
            session=db.session,
        )
        db.session.commit()
        conflict_raised = False
        try:
            emit_event(
                event_type="AUDIT_IDEMPOTENCY_CHANGED",
                payload={"value": 2},
                actor_user_id=student.id,
                target_type="USER",
                target_id=student.id,
                event_key=fixed_key,
                session=db.session,
            )
        except ConflictError:
            conflict_raised = True
            db.session.rollback()
        sql_rows = (
            db.session.query(Notification, NotificationEvent)
            .join(NotificationEvent, Notification.notification_event_id == NotificationEvent.id)
            .filter(
                Notification.recipient_user_id == student.id,
                Notification.title == title,
            )
            .all()
        )
        event_key_rows = db.session.query(NotificationEvent).filter_by(event_key=fixed_key).count()

    token = login_token("student4@pwd301.local")
    status_code, response_body = http_request(
        "GET", "/api/notifications?per_page=100", token=token
    )
    api_rows = [item for item in response_body.get("items", []) if item.get("title") == title]
    event_types = sorted(item.get("event_type") for item in api_rows)
    result = {
        "database": app.config.get("SQLALCHEMY_DATABASE_URI", "").split("/")[-1],
        "sql_rows": len(sql_rows),
        "sql_event_types": sorted(event.event_type for _notification, event in sql_rows),
        "api_http": status_code,
        "api_rows": len(api_rows),
        "api_event_types": event_types,
        "event_key_conflict": conflict_raised and event_key_rows == 1,
        "skipped": 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    expected = (
        len(sql_rows) == 2
        and result["sql_event_types"] == ["COURSE_ANNOUNCEMENT", "SYSTEM_NOTICE"]
        and status_code == 200
        and len(api_rows) == 2
        and event_types == ["COURSE_ANNOUNCEMENT", "SYSTEM_NOTICE"]
        and result["event_key_conflict"]
    )
    print(json.dumps({"cases": 2, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def seed_idempotency_probe(app):
    """Verify a second demo seed run changes neither SQL counts nor durable notices."""
    with app.app_context():
        model_counts_before = {
            "users": db.session.query(User).count(),
            "courses": db.session.query(Course).count(),
            "questions": db.session.query(Question).count(),
            "attempts": db.session.query(AssessmentAttempt).count(),
            "resources": db.session.query(LessonResource).count(),
            "notifications": db.session.query(Notification).count(),
            "audits": db.session.query(AuditEvent).count(),
        }
        summary = seed_demo(db.session)
        model_counts_after = {
            "users": db.session.query(User).count(),
            "courses": db.session.query(Course).count(),
            "questions": db.session.query(Question).count(),
            "attempts": db.session.query(AssessmentAttempt).count(),
            "resources": db.session.query(LessonResource).count(),
            "notifications": db.session.query(Notification).count(),
            "audits": db.session.query(AuditEvent).count(),
        }
        result = {
            "database": db.engine.url.database,
            "created_lists_empty": all(
                not summary[key]
                for key in (
                    "users_created",
                    "courses_created",
                    "lessons_created",
                    "questions_created",
                    "assessments_created",
                    "enrollments_created",
                    "attempts_created",
                )
            ),
            "notifications_created": summary["notifications_created"],
            "audit_events_created": summary["audit_events_created"],
            "counts_unchanged": model_counts_before == model_counts_after,
            "before": model_counts_before,
            "after": model_counts_after,
            "skipped": 0,
        }
        print(json.dumps(result, ensure_ascii=False))
        expected = (
            result["created_lists_empty"]
            and result["notifications_created"] == 0
            and result["audit_events_created"] == 0
            and result["counts_unchanged"]
        )
    print(json.dumps({"cases": 1, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def enrollment_idempotency_probe(app):
    """Verify SQL-backed enrollment notices use stable recipient-scoped keys."""
    with app.app_context():
        instructor = db.session.query(User).filter_by(email="instructor2@pwd301.local").one()
        student = db.session.query(User).filter_by(email="student4@pwd301.local").one()
        admin = db.session.query(User).filter_by(email="admin@pwd301.local").one()
        course = create_course(
            instructor,
            {
                "course_code": f"AKEY{uuid.uuid4().hex[:6].upper()}",
                "title": "Audit enrollment notification key",
                "level": "BEGINNER",
            },
        )
        change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
        change_course_status(admin, course.id, "APPROVED")
        change_course_status(admin, course.id, "PUBLISHED")
        enrollment = enroll_student(student, course.id, session=db.session)
        keys = {
            "INSTRUCTOR": uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"pwd301:enrollment:{enrollment.id}:STUDENT_ENROLLED:INSTRUCTOR",
            ),
            "STUDENT": uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"pwd301:enrollment:{enrollment.id}:STUDENT_ENROLLED:STUDENT",
            ),
        }
        events_before = (
            db.session.query(NotificationEvent)
            .filter(NotificationEvent.event_key.in_(list(keys.values())))
            .all()
        )
        notifications_before = db.session.query(Notification).filter(
            Notification.notification_event_id.in_([event.id for event in events_before])
        ).count()

        from pwd301.services.notification_service import dispatch_notification

        dispatch_notification(
            recipient_user=instructor.id,
            event_type="STUDENT_ENROLLED",
            title="Học viên mới tham gia khóa học",
            body=f"Học viên {student.display_name} vừa đăng ký tham gia khóa học '{course.title}'.",
            action_url=f"#/instructor/courses/manage?id={course.public_id}",
            category="COURSE",
            target_role="INSTRUCTOR",
            event_key=keys["INSTRUCTOR"],
            session=db.session,
        )
        dispatch_notification(
            recipient_user=student.id,
            event_type="STUDENT_ENROLLED",
            title="Đăng ký khóa học thành công",
            body=f"Bạn đã đăng ký thành công khóa học '{course.title}'. Bắt đầu học ngay hôm nay!",
            action_url=f"#/student/courses/detail?id={course.public_id}",
            category="COURSE",
            target_role="STUDENT",
            event_key=keys["STUDENT"],
            session=db.session,
        )
        db.session.commit()
        events_after = (
            db.session.query(NotificationEvent)
            .filter(NotificationEvent.event_key.in_(list(keys.values())))
            .all()
        )
        notifications_after = db.session.query(Notification).filter(
            Notification.notification_event_id.in_([event.id for event in events_after])
        ).count()
        result = {
            "database": db.engine.url.database,
            "enrollment_id": enrollment.id,
            "expected_keys_present": {role: key in {event.event_key for event in events_before} for role, key in keys.items()},
            "event_rows_before_after": [len(events_before), len(events_after)],
            "notification_rows_before_after": [notifications_before, notifications_after],
            "skipped": 0,
        }
    print(json.dumps(result, ensure_ascii=False))
    expected = (
        all(result["expected_keys_present"].values())
        and result["event_rows_before_after"] == [2, 2]
        and result["notification_rows_before_after"] == [2, 2]
    )
    print(json.dumps({"cases": 3, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def course_idempotency_probe(app):
    """Verify SQL-backed course lifecycle notices replay by their audit-scoped key."""
    with app.app_context():
        instructor = db.session.query(User).filter_by(email="instructor2@pwd301.local").one()
        course = db.session.query(Course).filter_by(course_code=COURSE_CODE).one()
        audit_entry = (
            db.session.query(AuditEvent)
            .filter_by(action="COURSE_APPROVED", target_type="COURSE", target_id=course.id)
            .order_by(AuditEvent.id.desc())
            .first()
        )
        if audit_entry is None:
            raise RuntimeError("Disposable course fixture has no approval audit event.")
        expected_key = _course_notification_event_key(audit_entry, instructor.id)
        event = db.session.query(NotificationEvent).filter_by(event_key=expected_key).one()
        notification = (
            db.session.query(Notification)
            .filter_by(notification_event_id=event.id, recipient_user_id=instructor.id)
            .one()
        )
        payload = json.loads(event.payload_json or "{}")
        contract = payload.get("_dispatch_contract") or {}
        replay_payload = {
            key: value for key, value in payload.items() if key != "_dispatch_contract"
        }
        events_before = db.session.query(NotificationEvent).filter_by(event_key=expected_key).count()
        notifications_before = (
            db.session.query(Notification)
            .filter_by(notification_event_id=event.id, recipient_user_id=instructor.id)
            .count()
        )

        from pwd301.services.notification_service import dispatch_notification

        dispatch_notification(
            recipient_user=instructor.id,
            event_type=event.event_type,
            title=html.unescape(str(contract.get("title", notification.title))),
            body=html.unescape(str(contract.get("body", notification.body))),
            action_url=payload.get("action_url"),
            category=contract.get("category", notification.category),
            target_role=contract.get("target_role", notification.target_role),
            force_email=bool(contract.get("force_email", False)),
            payload=replay_payload,
            event_key=expected_key,
            session=db.session,
        )
        db.session.commit()
        events_after = db.session.query(NotificationEvent).filter_by(event_key=expected_key).count()
        notifications_after = (
            db.session.query(Notification)
            .filter_by(notification_event_id=event.id, recipient_user_id=instructor.id)
            .count()
        )
        result = {
            "database": db.engine.url.database,
            "course_id": str(course.public_id),
            "audit_id": audit_entry.id,
            "expected_key": str(expected_key),
            "key_present": event.event_key == expected_key,
            "event_rows_before_after": [events_before, events_after],
            "notification_rows_before_after": [notifications_before, notifications_after],
            "skipped": 0,
        }
    print(json.dumps(result, ensure_ascii=False))
    expected = (
        result["key_present"]
        and result["event_rows_before_after"] == [1, 1]
        and result["notification_rows_before_after"] == [1, 1]
    )
    print(json.dumps({"cases": 4, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def password_idempotency_probe(app):
    """Verify password-change security notices use the durable auth version key."""
    with app.app_context():
        email = f"audit.password.{uuid.uuid4().hex[:10]}@pwd301.local"
        user = register_user(email, "OldPassword@123", "Audit Password Key")
        change_password(user.id, "OldPassword@123", "NewPassword@123")
        expected_key = uuid.uuid5(
            uuid.NAMESPACE_URL, f"pwd301:password-change:{user.id}:{user.auth_version}"
        )
        from pwd301.services.notification_service import dispatch_notification

        events_before = (
            db.session.query(NotificationEvent).filter_by(event_key=expected_key).all()
        )
        notifications_before = db.session.query(Notification).filter(
            Notification.notification_event_id.in_([event.id for event in events_before])
        ).count()
        deliveries_before = db.session.query(EmailDelivery).filter(
            EmailDelivery.notification_event_id.in_([event.id for event in events_before])
        ).count()
        dispatch_notification(
            recipient_user=user.id,
            event_type="SECURITY_PASSWORD_CHANGED",
            title="Mật khẩu của bạn đã được thay đổi",
            body=(
                "Mật khẩu tài khoản của bạn vừa được thay đổi thành công. "
                "Nếu bạn không thực hiện thao tác này, vui lòng liên hệ quản trị viên ngay lập tức."
            ),
            category="SECURITY",
            force_email=True,
            target_role=None,
            event_key=expected_key,
            session=db.session,
        )
        db.session.commit()
        events_after = (
            db.session.query(NotificationEvent).filter_by(event_key=expected_key).all()
        )
        notifications_after = db.session.query(Notification).filter(
            Notification.notification_event_id.in_([event.id for event in events_after])
        ).count()
        deliveries_after = db.session.query(EmailDelivery).filter(
            EmailDelivery.notification_event_id.in_([event.id for event in events_after])
        ).count()
        reset_email = f"audit.password.reset.{uuid.uuid4().hex[:10]}@pwd301.local"
        reset_user = register_user(reset_email, "OldResetPassword@123", "Audit Reset Key")
        _, raw_reset_token = create_security_token(
            reset_user.id,
            SecurityTokenPurpose.PASSWORD_RESET,
            session=db.session,
        )
        reset_password_with_token(
            raw_reset_token,
            "NewResetPassword@123",
            session=db.session,
        )
        expected_reset_key = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"pwd301:password-change:{reset_user.id}:{reset_user.auth_version}",
        )
        reset_event = (
            db.session.query(NotificationEvent).filter_by(event_key=expected_reset_key).one()
        )
        reset_notification = (
            db.session.query(Notification)
            .filter_by(
                notification_event_id=reset_event.id,
                recipient_user_id=reset_user.id,
            )
            .one()
        )
        reset_payload = json.loads(reset_event.payload_json or "{}")
        reset_contract = reset_payload.get("_dispatch_contract") or {}
        reset_replay_payload = {
            key: value for key, value in reset_payload.items() if key != "_dispatch_contract"
        }
        reset_events_before = db.session.query(NotificationEvent).filter_by(
            event_key=expected_reset_key
        ).count()
        reset_notifications_before = db.session.query(Notification).filter_by(
            notification_event_id=reset_event.id,
            recipient_user_id=reset_user.id,
        ).count()
        reset_deliveries_before = db.session.query(EmailDelivery).filter_by(
            notification_event_id=reset_event.id
        ).count()
        dispatch_notification(
            recipient_user=reset_user.id,
            event_type=reset_event.event_type,
            title=html.unescape(str(reset_contract.get("title", reset_notification.title))),
            body=html.unescape(str(reset_contract.get("body", reset_notification.body))),
            category=reset_contract.get("category", reset_notification.category),
            force_email=bool(reset_contract.get("force_email", True)),
            target_role=reset_contract.get("target_role", reset_notification.target_role),
            payload=reset_replay_payload,
            event_key=expected_reset_key,
            session=db.session,
        )
        db.session.commit()
        reset_events_after = db.session.query(NotificationEvent).filter_by(
            event_key=expected_reset_key
        ).count()
        reset_notifications_after = db.session.query(Notification).filter_by(
            notification_event_id=reset_event.id,
            recipient_user_id=reset_user.id,
        ).count()
        reset_deliveries_after = db.session.query(EmailDelivery).filter_by(
            notification_event_id=reset_event.id
        ).count()
        suspension_email = f"audit.suspension.{uuid.uuid4().hex[:10]}@pwd301.local"
        suspension_user = register_user(
            suspension_email,
            "InitialSuspendPassword@123",
            "Audit Suspension Key",
        )
        suspend_user(suspension_user.id, reason="Security review", session=db.session)
        expected_suspension_key = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"pwd301:account-suspension:{suspension_user.id}:{suspension_user.auth_version}",
        )
        suspension_event = (
            db.session.query(NotificationEvent)
            .filter_by(event_key=expected_suspension_key)
            .one()
        )
        suspension_notification = (
            db.session.query(Notification)
            .filter_by(
                notification_event_id=suspension_event.id,
                recipient_user_id=suspension_user.id,
            )
            .one()
        )
        suspension_payload = json.loads(suspension_event.payload_json or "{}")
        suspension_contract = suspension_payload.get("_dispatch_contract") or {}
        suspension_replay_payload = {
            key: value
            for key, value in suspension_payload.items()
            if key != "_dispatch_contract"
        }
        suspension_events_before = db.session.query(NotificationEvent).filter_by(
            event_key=expected_suspension_key
        ).count()
        suspension_notifications_before = db.session.query(Notification).filter_by(
            notification_event_id=suspension_event.id,
            recipient_user_id=suspension_user.id,
        ).count()
        suspension_deliveries_before = db.session.query(EmailDelivery).filter_by(
            notification_event_id=suspension_event.id
        ).count()
        dispatch_notification(
            recipient_user=suspension_user.id,
            event_type=suspension_event.event_type,
            title=html.unescape(
                str(suspension_contract.get("title", suspension_notification.title))
            ),
            body=html.unescape(
                str(suspension_contract.get("body", suspension_notification.body))
            ),
            category=suspension_contract.get("category", suspension_notification.category),
            force_email=bool(suspension_contract.get("force_email", True)),
            target_role=suspension_contract.get(
                "target_role", suspension_notification.target_role
            ),
            payload=suspension_replay_payload,
            event_key=expected_suspension_key,
            session=db.session,
        )
        db.session.commit()
        suspension_events_after = db.session.query(NotificationEvent).filter_by(
            event_key=expected_suspension_key
        ).count()
        suspension_notifications_after = db.session.query(Notification).filter_by(
            notification_event_id=suspension_event.id,
            recipient_user_id=suspension_user.id,
        ).count()
        suspension_deliveries_after = db.session.query(EmailDelivery).filter_by(
            notification_event_id=suspension_event.id
        ).count()
        result = {
            "database": db.engine.url.database,
            "auth_version": user.auth_version,
            "key_present": len(events_before) == 1,
            "event_rows_before_after": [len(events_before), len(events_after)],
            "notification_rows_before_after": [notifications_before, notifications_after],
            "email_rows_before_after": [deliveries_before, deliveries_after],
            "reset_auth_version": reset_user.auth_version,
            "reset_key_present": True,
            "reset_event_rows_before_after": [reset_events_before, reset_events_after],
            "reset_notification_rows_before_after": [
                reset_notifications_before,
                reset_notifications_after,
            ],
            "reset_email_rows_before_after": [reset_deliveries_before, reset_deliveries_after],
            "suspension_auth_version": suspension_user.auth_version,
            "suspension_key_present": True,
            "suspension_event_rows_before_after": [
                suspension_events_before,
                suspension_events_after,
            ],
            "suspension_notification_rows_before_after": [
                suspension_notifications_before,
                suspension_notifications_after,
            ],
            "suspension_email_rows_before_after": [
                suspension_deliveries_before,
                suspension_deliveries_after,
            ],
            "skipped": 0,
        }
    print(json.dumps(result, ensure_ascii=False))
    expected = (
        result["auth_version"] == 2
        and result["key_present"]
        and result["event_rows_before_after"] == [1, 1]
        and result["notification_rows_before_after"] == [1, 1]
        and result["email_rows_before_after"] == [1, 1]
        and result["reset_auth_version"] == 2
        and result["reset_key_present"]
        and result["reset_event_rows_before_after"] == [1, 1]
        and result["reset_notification_rows_before_after"] == [1, 1]
        and result["reset_email_rows_before_after"] == [1, 1]
        and result["suspension_auth_version"] == 2
        and result["suspension_key_present"]
        and result["suspension_event_rows_before_after"] == [1, 1]
        and result["suspension_notification_rows_before_after"] == [1, 1]
        and result["suspension_email_rows_before_after"] == [1, 1]
    )
    print(json.dumps({"cases": 9, "failed_expectations": int(not expected), "skipped": 0}))
    return int(not expected)


def probe_ids(app):
    with app.app_context():
        attempt = (
            db.session.query(AssessmentAttempt)
            .join(
                AssessmentAttempt.assessment,
            )
            .filter_by(title=ASSESSMENT_TITLE)
            .one()
        )
        essay = next(q for q in attempt.attempt_questions if q.question_type_snapshot == "ESSAY")
        return str(attempt.public_id), str(attempt.assessment.public_id), str(essay.public_id)


def manual_probe(app):
    attempt, _, essay = probe_ids(app)
    instructor = login_token("instructor2@pwd301.local")
    student = login_token("student4@pwd301.local")
    result_path = f"/api/attempts/{attempt}/result"
    grading_path = f"/instructor/attempts/{attempt}/grading"
    grade_path = f"/api/attempts/{attempt}/grades/{essay}"
    code, before = http_request("GET", result_path, student)
    assert code == 200 and before["score_status"] == "SCORE_HIDDEN"
    assert before["raw_score"] is None
    print(json.dumps({"before": before["status"], "score_status": before["score_status"]}))
    code, detail = http_request("GET", grading_path, instructor)
    assert code == 200
    initial_version = next(
        q["row_version"] for q in detail["questions"] if q["attempt_question_id"] == essay
    )
    cases = [
        ("student_forbidden", student, 18, initial_version, 403),
        ("negative", instructor, -1, initial_version, 400),
        ("above_max", instructor, 21, initial_version, 400),
        ("nan", instructor, "NaN", initial_version, 400),
        ("stale_version", instructor, 18, "0000000000000000", 409),
    ]
    for label, token, score, version, expected_code in cases:
        code, body = http_request(
            "POST",
            grade_path,
            token,
            {
                "awarded_points": score,
                "row_version": version,
                "reason": "Audit rejected boundary",
            },
        )
        assert code == expected_code, f"{label}: unexpected HTTP {code}"
        print(
            json.dumps(
                {"case": label, "http": code, "error_code": body.get("error", {}).get("code")}
            )
        )
    code, body = http_request(
        "POST",
        grade_path,
        instructor,
        {
            "awarded_points": 18,
            "row_version": initial_version,
            "reason": "Audit first manual release",
        },
    )
    assert code == 200 and body["attempt_status"] == "GRADED" and body["is_finalized"]
    print(json.dumps({"case": "manual_grade", "http": code, "finalized": body["is_finalized"]}))
    code, detail = http_request("GET", grading_path, instructor)
    assert code == 200
    fresh_version = next(
        q["row_version"] for q in detail["questions"] if q["attempt_question_id"] == essay
    )
    assert fresh_version != initial_version
    code, body = http_request(
        "POST",
        grade_path,
        instructor,
        {
            "awarded_points": 18,
            "row_version": fresh_version,
            "reason": "Audit unchanged retry",
        },
    )
    assert code == 200
    code, after = http_request("GET", result_path, student)
    assert code == 200 and after["raw_score"] == 18 and after["max_score"] == 30
    assert after["score_status"] == "RELEASED"
    with app.app_context():
        notices = (
            db.session.query(Notification)
            .join(NotificationEvent)
            .filter(
                Notification.title.contains(ASSESSMENT_TITLE),
                NotificationEvent.event_type == "ASSESSMENT_GRADED",
            )
            .all()
        )
        assert len(notices) == 1, f"Expected one durable first-release notice, got {len(notices)}"
        assert notices[0].recipient.email == "student4@pwd301.local"
        assert notices[0].to_dict()["action_url"] == f"#/student/assessments/results?id={attempt}"
    print(json.dumps({"manual_score": after["raw_score"], "retry_notice_count": len(notices)}))


def regrade_probe(app):
    attempt, assessment, _ = probe_ids(app)
    instructor = login_token("instructor2@pwd301.local")
    student = login_token("student4@pwd301.local")
    path = f"/api/assessments/{assessment}/regrade"
    code, body = http_request("POST", path, instructor, {"reason": "Audit answer-only correction"})
    assert code == 200 and len(body["jobs"]) == 1
    job_id = body["jobs"][0]["job_id"]
    code, job = http_request("GET", f"/api/regrade-jobs/{job_id}", instructor)
    assert code == 200 and job["status"] == "COMPLETED"
    assert job["processed_items"] == 1 and job["changed_results"] == 1
    code, result = http_request("GET", f"/api/attempts/{attempt}/result", student)
    assert code == 200 and result["raw_score"] == 28 and result["score_status"] == "RELEASED"
    code, history = http_request("GET", f"/api/attempts/{attempt}/grade-history", student)
    assert code == 200
    changes = [h for h in history["overall_history"] if h["reason_code"] == "REGRADE"]
    assert len(changes) == 1 and changes[0]["old_score"] == 18 and changes[0]["new_score"] == 28
    code, repeated = http_request(
        "POST", path, instructor, {"reason": "Audit duplicate regrade request"}
    )
    assert code == 200 and repeated["jobs"][0]["job_id"] == job_id
    code, history_after = http_request("GET", f"/api/attempts/{attempt}/grade-history", student)
    assert code == 200 and history_after["overall_history"] == history["overall_history"]
    with app.app_context():
        notices = (
            db.session.query(Notification, NotificationEvent)
            .join(
                NotificationEvent,
                Notification.notification_event_id == NotificationEvent.id,
            )
            .filter(Notification.title.contains(ASSESSMENT_TITLE))
            .all()
        )
        assert len(notices) == 2
        assert sorted(e.event_type for _, e in notices) == [
            "ASSESSMENT_GRADED",
            "SCORE_CHANGED_AFTER_REGRADE",
        ]
        for notification, _ in notices:
            assert notification.recipient.email == "student4@pwd301.local"
            assert (
                notification.to_dict()["action_url"]
                == f"#/student/assessments/results?id={attempt}"
            )
        persisted_attempt = db.session.query(AssessmentAttempt).filter_by(public_id=attempt).one()
        objective = next(
            q
            for q in persisted_attempt.attempt_questions
            if q.question_type_snapshot == "SINGLE_CHOICE"
        )
        snapshot_correct = [
            c.content for c in objective.source_question_revision.choices if c.is_correct
        ]
        assert all(
            c.source_choice.question_revision_id == objective.source_question_revision_id
            and c.content_snapshot == c.source_choice.content
            for c in objective.choice_snapshots
        )
        assert snapshot_correct == ["A"], "Regrade must preserve the original attempt snapshot."
    print(
        json.dumps(
            {
                "job": job_id,
                "status": job["status"],
                "raw_score": result["raw_score"],
                "duplicate_job_same": True,
                "history_unchanged_on_retry": True,
                "notice_count": len(notices),
                "original_snapshot_correct": snapshot_correct,
            }
        )
    )


def cleanup(url, database_name=DATABASE_NAME):
    if database_name not in (DATABASE_NAME, *SQL_GATE_DATABASES):
        raise RuntimeError("Refusing to drop a database outside the exact audit allowlist.")
    master = create_engine(url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with master.connect() as connection:
            exists = connection.execute(
                text("SELECT COUNT(*) FROM sys.databases WHERE name = :name"),
                {"name": database_name},
            ).scalar_one()
            if exists:
                connection.exec_driver_sql(
                    f"ALTER DATABASE [{database_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"
                )
                connection.exec_driver_sql(f"DROP DATABASE [{database_name}]")
            remaining = connection.execute(
                text("SELECT COUNT(*) FROM sys.databases WHERE name = :name"),
                {"name": database_name},
            ).scalar_one()
            print(json.dumps({"database": database_name, "audit_database_remaining": remaining}))
    finally:
        master.dispose()


def sql_gates(url):
    """Execute every integration item, including both SQL gates, without skips."""
    created = []
    master = create_engine(url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with master.connect() as connection:
            for name in SQL_GATE_DATABASES:
                exists = connection.execute(
                    text("SELECT COUNT(*) FROM sys.databases WHERE name = :name"),
                    {"name": name},
                ).scalar_one()
                if exists:
                    raise RuntimeError(f"Refusing to overwrite existing audit database {name}.")
                connection.exec_driver_sql(f"CREATE DATABASE [{name}]")
                created.append(name)
        environment = os.environ.copy()
        environment.update(
            PYTHONUTF8="1",
            SQLSERVER_MIGRATION_URL=url.set(database=SQL_GATE_DATABASES[0]).render_as_string(
                hide_password=False
            ),
            SQLSERVER_CONCURRENCY_URL=url.set(database=SQL_GATE_DATABASES[1]).render_as_string(
                hide_password=False
            ),
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/integration", "-q"],
            env=environment,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"Integration verification failed with exit code {result.returncode}."
            )
    finally:
        master.dispose()
        for name in created:
            cleanup(url, name)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "prepare",
            "serve",
            "status",
            "correct-answer",
            "manual-probe",
            "regrade-probe",
            "flag-status",
            "flag-probe",
            "flag-idempotency-probe",
            "notification-copy-probe",
            "seed-idempotency-probe",
            "enrollment-idempotency-probe",
            "course-idempotency-probe",
            "password-idempotency-probe",
            "subadmin-prepare",
            "subadmin-probe",
            "migrate",
            "sql-gates",
            "cleanup",
        ],
    )
    args = parser.parse_args()
    source_url = base_url()
    if args.action == "prepare":
        prepare(source_url)
    elif args.action == "cleanup":
        cleanup(source_url)
    elif args.action == "sql-gates":
        sql_gates(source_url)
    else:
        runtime = audit_app(source_url)
        if args.action == "serve":
            runtime.run(host="127.0.0.1", port=5105, debug=False, use_reloader=False)
        elif args.action == "status":
            status(runtime)
        elif args.action == "manual-probe":
            manual_probe(runtime)
        elif args.action == "regrade-probe":
            regrade_probe(runtime)
        elif args.action == "flag-status":
            flag_status(runtime, "current")
        elif args.action == "flag-probe":
            sys.exit(flag_probe(runtime))
        elif args.action == "flag-idempotency-probe":
            sys.exit(flag_idempotency_probe(runtime))
        elif args.action == "notification-copy-probe":
            sys.exit(notification_copy_probe(runtime))
        elif args.action == "seed-idempotency-probe":
            sys.exit(seed_idempotency_probe(runtime))
        elif args.action == "enrollment-idempotency-probe":
            sys.exit(enrollment_idempotency_probe(runtime))
        elif args.action == "course-idempotency-probe":
            sys.exit(course_idempotency_probe(runtime))
        elif args.action == "password-idempotency-probe":
            sys.exit(password_idempotency_probe(runtime))
        elif args.action == "subadmin-prepare":
            prepare_subadmins(runtime)
        elif args.action == "subadmin-probe":
            sys.exit(probe_subadmins(runtime))
        elif args.action == "migrate":
            with runtime.app_context():
                upgrade(directory="migrations")
        else:
            correct_answer(runtime)
