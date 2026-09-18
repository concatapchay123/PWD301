import pytest
from flask import Flask
from flask.testing import FlaskClient
from datetime import timedelta

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.models.course import Course
from pwd301.models.assessment import Assessment
from pwd301.services.user_service import register_user, assign_role_to_user
from pwd301.services.course_service import create_course
from pwd301.services.assessment_service import create_assessment, publish_assessment
from pwd301.services.question_bank_service import create_question
from pwd301.services.assessment_service import assign_question
from pwd301.models.types import utc_now
from tests.conftest import login_web_user

def test_template_rendering_and_defensive_ux(app: Flask, client: FlaskClient):
    # Ensure Roles
    for code, name in [('STUDENT', 'Student'), ('INSTRUCTOR', 'Instructor'), ('ADMIN', 'Admin')]:
        if not db.session.query(Role).filter_by(code=code).first():
            db.session.add(Role(code=code, name=name))
    db.session.commit()
    
    inst = register_user('render_test@example.com', 'Pass@123', 'Render Tester')
    inst = assign_role_to_user(inst.id, 'INSTRUCTOR')
    course = create_course(inst, {'course_code': 'RND-101', 'title': 'Render Course'})
    now = utc_now()
    asm = create_assessment(inst, course.id, {
        'title': 'Test Render Exam',
        'assessment_type': 'MIDTERM',
        'open_at': (now + timedelta(days=1)).isoformat(),
        'close_at': (now + timedelta(days=3)).isoformat(),
        'time_limit_minutes': 60,
    })
    
    login_web_user(client, inst)
    
    # 1. Draft state render: action buttons and modals present, lock banners absent
    resp_draft = client.get(f'/instructor/assessments/{asm.public_id}', headers={'Accept': 'text/html'})
    assert resp_draft.status_code == 200
    html = resp_draft.text
    assert '+ Tạo câu hỏi mới' in html
    assert 'Upload PDF/DOCX tạo đề tự động' in html
    assert '+ Thêm từ Ngân hàng' in html
    assert 'id="createQuestionModal"' in html
    assert 'id="importDocumentModal"' in html
    assert 'Khóa Thời gian' not in html
    assert 'Khóa Cấu trúc' not in html

    # Add a question to the assessment
    q = create_question(inst, course.id, {
        'question_type': 'SINGLE_CHOICE',
        'difficulty': 'UNDERSTAND',
        'content': 'Capital of France?',
        'default_points': 2.0,
        'choices': [
            {'content': 'Paris', 'is_correct': True, 'position': 1},
            {'content': 'Lyon', 'is_correct': False, 'position': 2}
        ]
    })
    assign_question(inst, asm.id, {'question_id': q.id, 'points': 2.0, 'source_type': 'MANUAL'})

    # 2. Render with question: quick edit form, "Sửa" button, and modal present with CSRF
    resp_with_q = client.get(f'/instructor/assessments/{asm.public_id}', headers={'Accept': 'text/html'})
    assert resp_with_q.status_code == 200
    html_q = resp_with_q.text
    assert f'id="editQuestionModal_{q.public_id}"' in html_q
    assert 'Capital of France?' in html_q
    assert 'name="points"' in html_q
    assert 'name="csrf_token"' in html_q
    assert 'Sửa' in html_q

    # 3. Published state (Timing Locked): timing warning banner present
    publish_assessment(inst, asm.id)
    resp_pub = client.get(f'/instructor/assessments/{asm.public_id}', headers={'Accept': 'text/html'})
    assert resp_pub.status_code == 200
    html_pub = resp_pub.text
    assert 'Khóa Thời gian đang kích hoạt (Timing Lock — BR-031 / Invariant 13)' in html_pub
    assert 'Khóa Cấu trúc Toàn diện' not in html_pub

    # 4. Attempt started (Structural Freeze): danger banner present, controls locked
    asm.first_attempt_started_at = utc_now()
    db.session.commit()
    resp_frozen = client.get(f'/instructor/assessments/{asm.public_id}', headers={'Accept': 'text/html'})
    assert resp_frozen.status_code == 200
    html_frozen = resp_frozen.text
    assert 'Khóa Cấu trúc Toàn diện đang kích hoạt (Structural Freeze — BR-030 / Invariant 14)' in html_frozen
    assert 'Cấu trúc đã khóa (Đang có thí sinh thi)' in html_frozen
    assert f'id="editQuestionModal_{q.public_id}"' not in html_frozen
    assert '+ Tạo câu hỏi mới' not in html_frozen
