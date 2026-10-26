import json
import pytest
from flask import Flask
from flask.testing import FlaskClient
from backend.extensions import db
from backend.models.course import Course
from backend.models.identity import Role, User
from backend.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user

@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("admin_task135@example.com", "Password@123", "Admin 135")
    return assign_role_to_user(u.id, "ADMIN")

def test_admin_course_detail_cleans_description_and_extracts_contact_info(
    client: FlaskClient, admin_user: User
) -> None:
    # Setup course with raw directive comments in description
    contact_payload = {
        "email": "teacher135@gmail.com",
        "phone": "0988776655",
        "group": "zalo.me/g/test135",
        "office_hours": "T2-T4 14:00 - 16:00",
    }
    raw_desc = (
        "Khóa học lập trình cao cấp cho kỹ sư phần mềm.\n\n"
        f"<!-- contact_info: {json.dumps(contact_payload)} -->\n"
        "<!-- trailer_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ -->"
    )
    course = Course(
        course_code="TASK135",
        course_code_normalized="task135",
        title="Khóa học Task 135",
        title_normalized="khoa hoc task 135",
        description=raw_desc,
        status="SUBMITTED_FOR_REVIEW",
        price=500000,
        difficulty="INTERMEDIATE",
        category="Công nghệ phần mềm",
    )
    db.session.add(course)
    db.session.commit()

    login_web_user(client, admin_user)

    res = client.get(f"/admin/courses/{course.public_id}")
    assert res.status_code == 200
    data = res.get_json()

    # 1. Description must be pure clean text without internal directives
    assert "<!-- contact_info:" not in data["description"]
    assert "<!-- trailer_url:" not in data["description"]
    assert "Khóa học lập trình cao cấp cho kỹ sư phần mềm." in data["description"]

    # 2. contact_info must be isolated into first-class object
    assert "contact_info" in data
    assert data["contact_info"]["email"] == "teacher135@gmail.com"
    assert data["contact_info"]["phone"] == "0988776655"
    assert data["contact_info"]["group"] == "zalo.me/g/test135"
    assert data["contact_info"]["office_hours"] == "T2-T4 14:00 - 16:00"

    # 3. Price must be correctly returned
    assert data["price"] == 500000
