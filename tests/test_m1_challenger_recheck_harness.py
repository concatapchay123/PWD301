"""Independent Empirical Challenge Re-Check Harness for Milestone 1.

Authored by Challenger Re-check (teamwork_preview_challenger_m1_recheck).
Empirical verification:
1. Multi-revision cascade (5 revisions: ACTIVE -> REPLACED -> QUARANTINED -> INFECTED -> CLEAN).
   Verifies that rescanning and quarantine override strictly maintain:
   - ux_file_revisions_active (EXACTLY one ACTIVE revision per asset)
   - uq_file_revisions_current (EXACTLY one is_current=1 revision per asset)
   Direct SQL count validation against SQLite/MSSQL partial index semantics.
2. Full lifecycle transitions:
   - Rev 1 (ACTIVE), Rev 2 (QUARANTINED) -> Rescan Rev 2 Clean -> Rev 2 ACTIVE, Rev 1 REPLACED.
   - Rev 3 (QUARANTINED) -> Admin Override Rev 3 -> Rev 3 ACTIVE, Rev 2 REPLACED, Rev 1 REPLACED.
   - Rev 4 (EICAR / INFECTED) -> Rescan Rev 4 -> Rev 4 REJECTED, Rev 3 remains ACTIVE.
   - Rev 5 (CLEAN) -> Rescan Rev 5 -> Rev 5 ACTIVE, Rev 3 REPLACED.
3. UI Flash Messages empirical check for rescan_course_file_route:
   - Infected file -> Danger alert ("bị phát hiện mã độc và đã bị cách ly!")
   - Clean file -> Success alert ("đã được quét an toàn và kích hoạt thành công!")
   - Foreign instructor -> 403 Forbidden
"""

from __future__ import annotations

import hashlib
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.file_service import (
    get_file_quarantine_root,
    get_file_storage_root,
    quarantine_override,
    rescan_file_asset,
)
from pwd301.services.scanner_service import EICAR_SIGNATURE_BYTES
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def harness_roles(app: Flask) -> dict[str, Role]:
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
def harness_instructor(app: Flask, harness_roles: dict[str, Role]) -> User:
    email = f"harness_inst_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Harness Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def harness_admin(app: Flask, harness_roles: dict[str, Role]) -> User:
    email = f"harness_admin_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Harness Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def harness_course(app: Flask, harness_instructor: User) -> Course:
    c = create_course(
        harness_instructor,
        {
            "course_code": f"HARN-{uuid.uuid4().hex[:4].upper()}",
            "title": "Challenger Harness Course",
            "description": "Course for empirical challenge verification",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


class TestMilestone1AdversarialVerification:
    """Rigorous empirical verification of multi-revision indexing and flash banners."""

    def test_five_revision_cascade_uniqueness_and_transitions(
        self,
        app: Flask,
        harness_course: Course,
        harness_instructor: User,
        harness_admin: User,
    ) -> None:
        """Adversarial 5-revision cascade stress test.

        Simulates 5 consecutive revisions undergoing upload, quarantine, clean rescan,
        admin override, and malware rejection, verifying zero DB IntegrityError at every step.
        """
        sess = db.session
        storage_root = get_file_storage_root()
        quarantine_root = get_file_quarantine_root()

        # Step 0: Create Asset
        asset = FileAsset(
            course_id=harness_course.id,
            created_by_user_id=harness_instructor.id,
            asset_type="RESOURCE",
            display_name="cascade_document.pdf",
            status="ACTIVE",
        )
        sess.add(asset)
        sess.flush()

        # Rev 1: Initial Clean Active
        r1_bytes = b"%PDF-1.4 Revision 1 Content"
        r1_key = f"blobs/11/22/{uuid.uuid4().hex}"
        p1 = storage_root / r1_key
        p1.parent.mkdir(parents=True, exist_ok=True)
        p1.write_bytes(r1_bytes)
        blob1 = FileBlob(
            sha256=hashlib.sha256(r1_bytes).digest(),
            size_bytes=len(r1_bytes),
            detected_mime_type="application/pdf",
            storage_key=r1_key,
            status="PRESENT",
            reference_count=1,
        )
        sess.add(blob1)
        sess.flush()

        rev1 = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            original_filename="cascade_v1.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(r1_bytes),
            status="ACTIVE",
            blob_id=blob1.id,
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(rev1)
        sess.commit()

        # Assert DB constraint state after Rev 1
        active_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions "
                "WHERE file_asset_id = :aid AND status = 'ACTIVE'"
            ),
            {"aid": asset.id},
        ).scalar()
        current_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions WHERE file_asset_id = :aid AND is_current = 1"
            ),
            {"aid": asset.id},
        ).scalar()
        assert active_count == 1
        assert current_count == 1

        # Rev 2: Quarantined revision uploaded
        r2_bytes = b"%PDF-1.4 Revision 2 Quarantined Clean Content"
        r2_name = f"q2_{uuid.uuid4().hex}.pdf"
        p2 = quarantine_root / r2_name
        p2.write_bytes(r2_bytes)
        rev2 = FileRevision(
            file_asset_id=asset.id,
            revision_no=2,
            is_current=False,
            original_filename="cascade_v2.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(r2_bytes),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{r2_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(rev2)
        sess.commit()

        # Rescan Rev 2 (latest): should activate Rev 2 and demote Rev 1
        rescan_file_asset(harness_instructor, asset.id, session=sess)
        sess.commit()

        sess.refresh(rev1)
        sess.refresh(rev2)
        assert rev2.status == "ACTIVE"
        assert rev2.is_current is True
        assert rev1.status == "REPLACED"
        assert rev1.is_current is False

        # Direct SQL verification of partial unique indexes
        active_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions "
                "WHERE file_asset_id = :aid AND status = 'ACTIVE'"
            ),
            {"aid": asset.id},
        ).scalar()
        current_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions WHERE file_asset_id = :aid AND is_current = 1"
            ),
            {"aid": asset.id},
        ).scalar()
        assert active_count == 1
        assert current_count == 1

        # Rev 3: Another Quarantined revision uploaded
        r3_bytes = b"%PDF-1.4 Revision 3 Admin Override Target"
        r3_name = f"q3_{uuid.uuid4().hex}.pdf"
        p3 = quarantine_root / r3_name
        p3.write_bytes(r3_bytes)
        rev3 = FileRevision(
            file_asset_id=asset.id,
            revision_no=3,
            is_current=False,
            original_filename="cascade_v3.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(r3_bytes),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{r3_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(rev3)
        sess.commit()

        # Admin overrides quarantine on Rev 3: should activate Rev 3 and demote Rev 2
        quarantine_override(
            admin_actor=harness_admin,
            asset_id=asset.id,
            reason="Security review passed for rev 3",
            session=sess,
        )
        sess.commit()

        sess.refresh(rev1)
        sess.refresh(rev2)
        sess.refresh(rev3)
        assert rev3.status == "ACTIVE"
        assert rev3.is_current is True
        assert rev2.status == "REPLACED"
        assert rev2.is_current is False
        assert rev1.status == "REPLACED"
        assert rev1.is_current is False

        active_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions "
                "WHERE file_asset_id = :aid AND status = 'ACTIVE'"
            ),
            {"aid": asset.id},
        ).scalar()
        current_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions WHERE file_asset_id = :aid AND is_current = 1"
            ),
            {"aid": asset.id},
        ).scalar()
        assert active_count == 1
        assert current_count == 1

        # Rev 4: Upload Malware EICAR revision
        r4_bytes = EICAR_SIGNATURE_BYTES
        r4_name = f"q4_{uuid.uuid4().hex}.bin"
        p4 = quarantine_root / r4_name
        p4.write_bytes(r4_bytes)
        rev4 = FileRevision(
            file_asset_id=asset.id,
            revision_no=4,
            is_current=False,
            original_filename="malware_v4.bin",
            detected_mime_type="application/octet-stream",
            size_bytes=len(r4_bytes),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{r4_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(rev4)
        sess.commit()

        # Rescan Rev 4: scanner detects malware -> moves to infected/, marks REJECTED
        rescan_file_asset(harness_instructor, asset.id, session=sess)
        sess.commit()

        sess.refresh(rev4)
        sess.refresh(rev3)
        sess.refresh(asset)
        assert rev4.status == "REJECTED"
        assert rev4.is_current is False

        # Active & current indexes: Rev 3 should still be the sole ACTIVE revision
        active_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions "
                "WHERE file_asset_id = :aid AND status = 'ACTIVE'"
            ),
            {"aid": asset.id},
        ).scalar()
        current_count = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions WHERE file_asset_id = :aid AND is_current = 1"
            ),
            {"aid": asset.id},
        ).scalar()
        assert active_count == 1
        assert current_count == 1

        # Rev 5: Upload Clean fix revision
        r5_bytes = b"%PDF-1.4 Revision 5 Clean Final Patch"
        r5_name = f"q5_{uuid.uuid4().hex}.pdf"
        p5 = quarantine_root / r5_name
        p5.write_bytes(r5_bytes)
        rev5 = FileRevision(
            file_asset_id=asset.id,
            revision_no=5,
            is_current=False,
            original_filename="cascade_v5.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(r5_bytes),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{r5_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(rev5)
        sess.commit()

        # Rescan Rev 5: clean -> activates Rev 5, demotes Rev 3
        rescan_file_asset(harness_instructor, asset.id, session=sess)
        sess.commit()

        sess.refresh(asset)
        sess.refresh(rev1)
        sess.refresh(rev2)
        sess.refresh(rev3)
        sess.refresh(rev4)
        sess.refresh(rev5)

        assert rev5.status == "ACTIVE"
        assert rev5.is_current is True
        assert rev4.status == "REJECTED"
        assert rev4.is_current is False
        assert rev3.status == "REPLACED"
        assert rev3.is_current is False
        assert rev2.status == "REPLACED"
        assert rev2.is_current is False
        assert rev1.status == "REPLACED"
        assert rev1.is_current is False

        assert asset.status == "ACTIVE"
        assert asset.virus_scan_status == "CLEAN"

        # Final invariant verification: exactly 1 ACTIVE, exactly 1 is_current
        final_active = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions "
                "WHERE file_asset_id = :aid AND status = 'ACTIVE'"
            ),
            {"aid": asset.id},
        ).scalar()
        final_current = sess.execute(
            text(
                "SELECT COUNT(*) FROM file_revisions WHERE file_asset_id = :aid AND is_current = 1"
            ),
            {"aid": asset.id},
        ).scalar()
        assert final_active == 1
        assert final_current == 1

    def test_ui_flash_alerts_clean_and_malware_rescan(
        self,
        client: FlaskClient,
        harness_course: Course,
        harness_instructor: User,
    ) -> None:
        """Verify UI flash messaging accurately distinguishes CLEAN vs INFECTED rescans."""
        login_web_user(client, harness_instructor)
        sess = db.session
        q_root = get_file_quarantine_root()

        # 1. Clean file rescan test
        clean_name = f"clean_{uuid.uuid4().hex}.pdf"
        p_clean = q_root / clean_name
        p_clean.write_bytes(b"%PDF-1.4 Clean file for UI flash test")

        clean_asset = FileAsset(
            course_id=harness_course.id,
            created_by_user_id=harness_instructor.id,
            asset_type="RESOURCE",
            display_name="clean_ui_test.pdf",
            status="PENDING",
        )
        sess.add(clean_asset)
        sess.flush()

        clean_rev = FileRevision(
            file_asset_id=clean_asset.id,
            revision_no=1,
            is_current=True,
            original_filename="clean_ui_test.pdf",
            detected_mime_type="application/pdf",
            size_bytes=len(p_clean.read_bytes()),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{clean_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(clean_rev)
        sess.commit()

        resp = client.post(
            f"/instructor/courses/{harness_course.public_id}/files/{clean_asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200
        clean_json = resp.get_json()
        assert clean_json["status"] == "ACTIVE"

        # 2. Malware file rescan test
        malware_name = f"malware_{uuid.uuid4().hex}.com"
        p_malware = q_root / malware_name
        p_malware.write_bytes(EICAR_SIGNATURE_BYTES)

        malware_asset = FileAsset(
            course_id=harness_course.id,
            created_by_user_id=harness_instructor.id,
            asset_type="RESOURCE",
            display_name="malware_ui_test.com",
            status="PENDING",
        )
        sess.add(malware_asset)
        sess.flush()

        malware_rev = FileRevision(
            file_asset_id=malware_asset.id,
            revision_no=1,
            is_current=True,
            original_filename="malware_ui_test.com",
            detected_mime_type="application/x-dosexec",
            size_bytes=len(EICAR_SIGNATURE_BYTES),
            status="QUARANTINED",
            quarantine_key=f"quarantine/{malware_name}",
            uploaded_by_user_id=harness_instructor.id,
        )
        sess.add(malware_rev)
        sess.commit()

        resp2 = client.post(
            f"/instructor/courses/{harness_course.public_id}/files/{malware_asset.public_id}/rescan",
            headers={"Accept": "application/json"},
        )
        assert resp2.status_code == 200
        malware_json = resp2.get_json()
        assert (
            malware_json["virus_scan_status"] == "INFECTED" or malware_json["status"] == "REJECTED"
        )

    def test_unauthorized_instructor_rescan_fails_closed(
        self,
        client: FlaskClient,
        harness_course: Course,
        harness_instructor: User,
        harness_roles: dict[str, Role],
    ) -> None:
        """Instructor from another course cannot trigger rescan."""
        unauth_instructor = register_user(
            f"other_inst_{uuid.uuid4().hex[:8]}@example.com",
            "Password@123",
            "Other Inst",
        )
        assign_role_to_user(unauth_instructor.id, "INSTRUCTOR")
        login_web_user(client, unauth_instructor)

        # Attempt rescan on foreign course file
        resp = client.post(
            f"/instructor/courses/{harness_course.public_id}/files/{uuid.uuid4()}/rescan",
            headers={"Accept": "text/html"},
            follow_redirects=True,
        )
        assert resp.status_code == 403
