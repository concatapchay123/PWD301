import sys
import os
import io
import json
import uuid

# Force utf-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

from backend import create_app, db
from backend.models.identity import User
from backend.models.course import Course, Enrollment

def run_verification():
    app = create_app('development')
    with app.app_context():
        # 1. Verify Student User
        student = db.session.query(User).filter(User.display_name.like('%Ho%ng Ph%c%')).first()
        if not student:
            student = db.session.query(User).first()
        print(f"[AUTH] Testing with Student: {student.id} | {student.display_name} ({student.email})")

        # 2. Verify Course 213 (public_id: 182bc6b0-13eb-4956-a75f-c8e5e7071f75)
        c213_uuid = uuid.UUID('182bc6b0-13eb-4956-a75f-c8e5e7071f75')
        c213 = db.session.query(Course).filter_by(public_id=c213_uuid).first()
        assert c213 is not None, "Course 213 not found in DB!"
        print(f"[COURSE 213] Found in DB: id={c213.id}, code={c213.course_code}, title={c213.title}, status={c213.status}")

        with app.test_client() as client:
            from backend.services.session_auth_service import create_auth_session
            _, raw_key = create_auth_session(student, session=db.session)
            db.session.commit()
            with client.session_transaction() as sess:
                sess["_user_id"] = str(student.id)
                sess["auth_session_key"] = raw_key
                sess["auth_version"] = student.auth_version
                sess["auth_source"] = "SESSION"

            # 3. Call GET /student/courses/182bc6b0-13eb-4956-a75f-c8e5e7071f75
            resp = client.get(f'/student/courses/{str(c213.public_id)}')
            print(f"[API TEST 1] GET /student/courses/{c213.public_id} -> Status: {resp.status_code}")
            assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.get_data(as_text=True)}"
            
            data = resp.get_json()
            assert 'course' in data, f"Missing 'course' in response: {data}"
            course_res = data['course']
            print(f"  -> Title: {course_res.get('title')}")
            print(f"  -> Code: {course_res.get('course_code')}")
            print(f"  -> Lessons Count: {len(course_res.get('lessons', []))}")
            print(f"  -> Assessments Count: {len(course_res.get('assessments', []))}")
            assert course_res.get('title') == c213.title, "Course title mismatch!"
            print("[API TEST 1] PASS! Course 213 detail loaded with zero 500 error!")

            # 4. Verify Certificate Download for Completed Course
            completed_enr = (
                db.session.query(Enrollment)
                .filter(Enrollment.student_user_id == student.id, Enrollment.status == 'COMPLETED')
                .first()
            )
            assert completed_enr is not None, "Student has no completed course to test certificate!"
            cert_course = db.session.query(Course).get(completed_enr.course_id)
            print(f"[CERT TEST] Using completed course: {cert_course.id} ({cert_course.course_code}) - {cert_course.title}")

            # Send request with standard browser headers (Accept: text/html,...)
            browser_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            cert_resp = client.get(
                f'/student/courses/{cert_course.public_id}/certificate',
                headers=browser_headers
            )
            print(f"[API TEST 2] GET /student/courses/{cert_course.public_id}/certificate -> Status: {cert_resp.status_code}")
            assert cert_resp.status_code == 200, f"Expected 200 but got {cert_resp.status_code}"
            assert cert_resp.mimetype == 'application/pdf', f"Expected application/pdf but got {cert_resp.mimetype}"
            
            content_disp = cert_resp.headers.get('Content-Disposition', '')
            print(f"  -> Content-Type: {cert_resp.mimetype}")
            print(f"  -> Content-Disposition: {content_disp}")
            assert 'attachment' in content_disp, f"Expected attachment disposition but got: {content_disp}"
            assert f'Chung_chi_{cert_course.course_code}' in content_disp, f"Filename mismatch: {content_disp}"

            pdf_bytes = cert_resp.get_data()
            print(f"  -> PDF Byte Size: {len(pdf_bytes)} bytes")
            assert pdf_bytes.startswith(b'%PDF'), "Data does not start with %PDF header!"
            print("[API TEST 2] PASS! Certificate successfully streams valid PDF attachment under browser Accept: text/html headers!")

            # Test format=html still works when explicitly requested
            html_resp = client.get(
                f'/student/courses/{cert_course.public_id}/certificate?format=html'
            )
            assert html_resp.status_code == 200
            assert 'text/html' in html_resp.mimetype
            print("[API TEST 3] PASS! Certificate format=html returns valid HTML when explicitly requested!")

        print("\n==========================================")
        print("ALL VERIFICATIONS COMPLETED WITH 100% PASS!")
        print("==========================================")

if __name__ == '__main__':
    run_verification()
