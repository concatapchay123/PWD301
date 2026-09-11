from __future__ import annotations

from pathlib import Path

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.models.identity import Role, User
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student, leave_course, re_enroll_student
from pwd301.services.exceptions import EnrollmentCapacityExceededError
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess = db.session
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor."""
    u = register_user("conc_inst@example.com", "Password@123", "Conc Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Admin."""
    u = register_user("conc_admin@example.com", "Password@123", "Conc Admin")
    return assign_role_to_user(u.id, "ADMIN")


def _create_published_course(
    instructor: User,
    admin: User,
    code: str,
    title: str,
    capacity: int | None = None,
) -> Course:
    course = create_course(
        instructor,
        {
            "course_code": code,
            "title": title,
            "capacity": capacity,
        },
    )
    change_course_status(instructor, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course.id, "APPROVED")
    change_course_status(instructor, course.id, "PUBLISHED")
    db.session.commit()
    return course


def test_capacity_exact_limit_sequential_simulation(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Verify that when capacity=1, first student enrolls and subsequent students are rejected."""
    course = _create_published_course(
        instructor_user, admin_user, code="CONC-1", title="Conc Course 1", capacity=1
    )
    sess = db.session

    s1 = register_user("stud_conc_1@example.com", "Password@123", "Student 1")
    s2 = register_user("stud_conc_2@example.com", "Password@123", "Student 2")
    s3 = register_user("stud_conc_3@example.com", "Password@123", "Student 3")
    sess.commit()

    # Student 1 succeeds
    e1 = enroll_student(actor=s1, course_id=course.id, session=sess)
    sess.commit()
    assert e1.status == "ACTIVE"

    # Student 2 is rejected
    with pytest.raises(EnrollmentCapacityExceededError, match="capacity of 1 has been reached"):
        enroll_student(actor=s2, course_id=course.id, session=sess)

    # Student 3 is rejected
    with pytest.raises(EnrollmentCapacityExceededError, match="capacity of 1 has been reached"):
        enroll_student(actor=s3, course_id=course.id, session=sess)

    # Total active enrollments remains exactly 1
    total_active = (
        sess.query(Enrollment)
        .filter(Enrollment.course_id == course.id, Enrollment.status == "ACTIVE")
        .count()
    )
    assert total_active == 1


def test_capacity_seat_freed_on_leave_allows_new_enrollment(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Verify that when a course is full (capacity=1), leaving frees the slot for another."""
    course = _create_published_course(
        instructor_user, admin_user, code="CONC-FREE", title="Freed Seat Course", capacity=1
    )
    sess = db.session

    s1 = register_user("stud_free_1@example.com", "Password@123", "Student 1")
    s2 = register_user("stud_free_2@example.com", "Password@123", "Student 2")
    sess.commit()

    # Student 1 enrolls -> full
    enroll_student(actor=s1, course_id=course.id, session=sess)
    sess.commit()

    # Student 2 fails
    with pytest.raises(EnrollmentCapacityExceededError):
        enroll_student(actor=s2, course_id=course.id, session=sess)

    # Student 1 leaves -> seat freed
    leave_course(actor=s1, course_id=course.id, session=sess)
    sess.commit()

    # Student 2 can now enroll successfully
    e2 = enroll_student(actor=s2, course_id=course.id, session=sess)
    sess.commit()
    assert e2.status == "ACTIVE"

    # Student 1 now fails to re-enroll because student 2 holds the only seat
    with pytest.raises(EnrollmentCapacityExceededError):
        re_enroll_student(actor=s1, course_id=course.id, session=sess)


def test_capacity_none_allows_unlimited_enrollments(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    setup_roles: dict[str, Role],
) -> None:
    """Verify that when capacity is None, multiple students can enroll without restriction."""
    course = _create_published_course(
        instructor_user, admin_user, code="CONC-UNLTD", title="Unlimited Course", capacity=None
    )

    sess = db.session

    students = [
        register_user(f"unltd_{i}@example.com", "Password@123", f"Unltd Student {i}")
        for i in range(5)
    ]
    sess.commit()

    for st in students:
        e = enroll_student(actor=st, course_id=course.id, session=sess)
        assert e.status == "ACTIVE"
    sess.commit()

    total_active = (
        sess.query(Enrollment)
        .filter(Enrollment.course_id == course.id, Enrollment.status == "ACTIVE")
        .count()
    )
    assert total_active == 5


def test_concurrent_threads_enrollment_capacity_race(tmp_path: Path) -> None:
    """Five threads race to enroll for the last 1 seat; exactly 1 wins and 4 are rejected."""
    import concurrent.futures

    from pwd301 import create_app

    db_file = tmp_path / "capacity_race.db"
    test_app = create_app(
        "testing",
        config_override={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file.as_posix()}?timeout=30"},
    )

    with test_app.app_context():
        db.create_all()
        sess = db.session

        for code, name in [
            ("STUDENT", "Student"),
            ("INSTRUCTOR", "Instructor"),
            ("ADMIN", "System Administrator"),
        ]:
            if not sess.query(Role).filter_by(code=code).first():
                sess.add(Role(code=code, name=name))
        sess.commit()

        inst = assign_role_to_user(
            register_user("c_inst@example.com", "Password@123", "C Inst").id, "INSTRUCTOR"
        )
        adm = assign_role_to_user(
            register_user("c_adm@example.com", "Password@123", "C Adm").id, "ADMIN"
        )
        course = _create_published_course(inst, adm, code="CRACE-1", title="Race 1", capacity=1)
        course_id = course.id

        students = [
            register_user(f"rstud_{i}@example.com", "Password@123", f"R Student {i}")
            for i in range(5)
        ]
        student_ids = [s.id for s in students]
        sess.commit()

        def try_enroll(s_id: int) -> tuple[int, bool, str | None]:
            with test_app.app_context():
                w_sess = db.session
                actor = w_sess.get(User, s_id)
                assert actor is not None
                try:
                    enroll_student(actor=actor, course_id=course_id, session=w_sess)
                    w_sess.commit()
                    return (s_id, True, None)
                except EnrollmentCapacityExceededError as ex:
                    w_sess.rollback()
                    return (s_id, False, str(ex))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(try_enroll, s_id) for s_id in student_ids]
            for f in futures:
                results.append(f.result())

        successes = [r for r in results if r[1] is True]
        failures = [r for r in results if r[1] is False]

        assert len(successes) == 1
        assert len(failures) == 4
        for _, _, err in failures:
            assert "capacity" in str(err).lower()

        sess.expire_all()
        active_count = (
            sess.query(Enrollment)
            .filter(Enrollment.course_id == course_id, Enrollment.status == "ACTIVE")
            .count()
        )
        assert active_count == 1
