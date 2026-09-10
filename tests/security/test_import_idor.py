"""Security and IDOR negative tests for DOCX/PDF assessment import engine (TASK-020).

Validates:
- Fail-closed security: quarantined or unscanned files reject import creation.
- Infected files reject import creation (403 FileSecurityQuarantineError).
- Cross-course file isolation: cannot import a file belonging to a different course.
- Foreign instructors cannot operate on other instructors' import jobs.
- Students are forbidden (403) from all import routes and service actions.
- Admins possess platform-wide authority to manage and commit import jobs.
- ADR-002: Zero leakage of internal BIGINT PK/FK or physical paths in representations.
"""

from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset, FileScanResult
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    FileSecurityQuarantineError,
    ForbiddenError,
)
from pwd301.services.file_service import store_file_stream
from pwd301.services.import_service import (
    cancel_import_job,
    commit_import_job,
    create_import_job,
    get_import_job_detail,
    process_import_job,
    set_import_question_decision,
    update_import_question,
)
from pwd301.services.user_service import assign_role_to_user, register_user


def create_sample_docx(paragraphs: list[str]) -> bytes:
    """Generate in-memory valid OpenXML DOCX bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        p_elements = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f"  <w:body>{p_elements}</w:body>\n"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
    return buffer.getvalue()


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
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
def instructor_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary instructor A."""
    u = register_user(
        f"import_idor_a_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor A"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create foreign instructor B."""
    u = register_user(
        f"import_idor_b_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor B"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user(
        f"import_idor_s_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student S"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create admin user."""
    u = register_user(
        f"import_idor_adm_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Admin S"
    )
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def course_a(app: Flask, instructor_a: User) -> Course:
    """Create course managed by Instructor A."""
    c = create_course(
        instructor_a,
        {
            "course_code": f"SEC-A-{uuid.uuid4().hex[:4].upper()}",
            "title": "Import Security Course A",
            "summary": "Course A Summary",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def course_b(app: Flask, instructor_b: User) -> Course:
    """Create course managed by Instructor B."""
    c = create_course(
        instructor_b,
        {
            "course_code": f"SEC-B-{uuid.uuid4().hex[:4].upper()}",
            "title": "Import Security Course B",
            "summary": "Course B Summary",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def clean_file_asset_a(instructor_a: User, course_a: Course) -> FileAsset:
    """Upload a clean DOCX file to Course A."""
    docx_bytes = create_sample_docx(
        [
            "Câu 1: Thủ đô của Việt Nam là gì?",
            "A. Hà Nội",
            "B. Hải Phòng",
            "Đáp án: A",
        ]
    )
    asset = store_file_stream(
        actor=instructor_a,
        course_id=course_a.id,
        file_stream=io.BytesIO(docx_bytes),
        filename="clean_questions.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        asset_type="IMPORT_SOURCE",
        session=db.session,
    )
    return asset


class TestImportSecurityAndIDOR:
    """Security, Authorization, and IDOR negative test cases."""

    def test_fail_closed_quarantined_file_rejected(
        self,
        instructor_a: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Files with quarantined revision must be rejected with FileSecurityQuarantineError."""
        assert clean_file_asset_a.current_revision is not None
        clean_file_asset_a.current_revision.status = "QUARANTINED"
        db.session.commit()

        with pytest.raises(FileSecurityQuarantineError, match="quarantined"):
            create_import_job(
                actor=instructor_a,
                course_id=course_a.id,
                file_asset_id=clean_file_asset_a.id,
                session=db.session,
            )

    def test_fail_closed_failing_scan_rejected(
        self,
        instructor_a: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Files with scan status != PASS must be rejected."""
        rev = clean_file_asset_a.current_revision
        assert rev is not None
        scan = (
            db.session.query(FileScanResult)
            .filter(FileScanResult.file_revision_id == rev.id)
            .first()
        )
        if scan:
            scan.status = "FAIL"
            scan.details_json = '{"threat": "Win32.TestThreat"}'
        else:
            scan = FileScanResult(
                file_revision_id=rev.id,
                scan_type="MALWARE",
                engine="CLAMAV",
                status="FAIL",
                details_json='{"threat": "Win32.TestThreat"}',
            )
            db.session.add(scan)
        db.session.commit()

        with pytest.raises(FileSecurityQuarantineError, match="malware security verification"):
            create_import_job(
                actor=instructor_a,
                course_id=course_a.id,
                file_asset_id=clean_file_asset_a.id,
                session=db.session,
            )

    def test_cross_course_file_asset_rejected(
        self,
        instructor_b: User,
        course_b: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Instructor B cannot use a FileAsset belonging to Course A to import into Course B."""
        with pytest.raises(
            FileSecurityQuarantineError, match="does not belong to the target course"
        ):
            create_import_job(
                actor=instructor_b,
                course_id=course_b.id,
                file_asset_id=clean_file_asset_a.id,
                session=db.session,
            )

    def test_foreign_instructor_cannot_create_import_job(
        self,
        instructor_b: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Instructor B cannot create an import job on Course A."""
        with pytest.raises(ForbiddenError):
            create_import_job(
                actor=instructor_b,
                course_id=course_a.id,
                file_asset_id=clean_file_asset_a.id,
                session=db.session,
            )

    def test_foreign_instructor_cannot_operate_on_import_job(
        self,
        instructor_a: User,
        instructor_b: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Instructor B cannot process, get details, edit, or commit Instructor A's job."""
        job = create_import_job(
            actor=instructor_a,
            course_id=course_a.id,
            file_asset_id=clean_file_asset_a.id,
            session=db.session,
        )

        with pytest.raises(ForbiddenError):
            process_import_job(actor=instructor_b, job_id=job.id, session=db.session)

        with pytest.raises(ForbiddenError):
            get_import_job_detail(actor=instructor_b, job_id=job.id, session=db.session)

        with pytest.raises(ForbiddenError):
            set_import_question_decision(
                actor=instructor_b,
                job_id=job.id,
                temp_id=1,
                decision="ACCEPTED",
                session=db.session,
            )

        with pytest.raises(ForbiddenError):
            update_import_question(
                actor=instructor_b,
                job_id=job.id,
                temp_id=1,
                payload={"content": "Hacked stem"},
                session=db.session,
            )

        with pytest.raises(ForbiddenError):
            commit_import_job(actor=instructor_b, job_id=job.id, session=db.session)

        with pytest.raises(ForbiddenError):
            cancel_import_job(actor=instructor_b, job_id=job.id, session=db.session)

    def test_student_forbidden_from_import_operations(
        self,
        instructor_a: User,
        student_user: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Student cannot create or view any import jobs."""
        with pytest.raises(ForbiddenError):
            create_import_job(
                actor=student_user,
                course_id=course_a.id,
                file_asset_id=clean_file_asset_a.id,
                session=db.session,
            )

        job = create_import_job(
            actor=instructor_a,
            course_id=course_a.id,
            file_asset_id=clean_file_asset_a.id,
            session=db.session,
        )

        with pytest.raises(ForbiddenError):
            get_import_job_detail(actor=student_user, job_id=job.id, session=db.session)

    def test_admin_has_platform_wide_access(
        self,
        instructor_a: User,
        admin_user: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Admin can access and process import jobs created by instructors."""
        job = create_import_job(
            actor=instructor_a,
            course_id=course_a.id,
            file_asset_id=clean_file_asset_a.id,
            session=db.session,
        )

        detail = get_import_job_detail(actor=admin_user, job_id=job.id, session=db.session)
        assert detail["id"] == str(job.public_id)

        processed = process_import_job(actor=admin_user, job_id=job.id, session=db.session)
        assert processed.status == "REVIEW_REQUIRED"

    def test_adr002_zero_pk_leakage(
        self,
        instructor_a: User,
        course_a: Course,
        clean_file_asset_a: FileAsset,
    ) -> None:
        """Serialized representations must only expose public UUIDs, never internal IDs."""
        job = create_import_job(
            actor=instructor_a,
            course_id=course_a.id,
            file_asset_id=clean_file_asset_a.id,
            session=db.session,
        )
        process_import_job(actor=instructor_a, job_id=job.id, session=db.session)

        detail = get_import_job_detail(actor=instructor_a, job_id=job.id, session=db.session)

        # Verify job level
        assert "public_id" not in detail or detail["id"] == str(job.public_id)
        assert isinstance(detail["id"], str)
        assert uuid.UUID(detail["id"])
        assert "internal_id" not in detail
        assert "storage_path" not in detail

        # Verify questions level
        for q in detail.get("questions", []):
            assert "id" in q
            assert uuid.UUID(q["id"])
            assert "import_job_id" not in q
            assert (
                "approved_question_id" not in q
                or q["approved_question_id"] is None
                or isinstance(q["approved_question_id"], str)
            )
            for c in q.get("candidates", []):
                assert "candidate_question_id" not in c or isinstance(
                    c["candidate_question_id"], str
                )
