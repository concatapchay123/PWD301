# Handoff Report: Milestone 1 Empirical Challenge (Challenger 2)

**Author**: Challenger 2 (`teamwork_preview_challenger_m1_2`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_challenger_m1_2`  
**Date**: 2026-09-13T22:54:00Z  
**Target Milestone**: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)  
**Handoff Type**: Hard (Challenge Complete)  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 HTTP Range Requests Verification (PASS)
Executed 6 test scenarios in `tests/test_m1_challenger_stress.py::TestHttpRangeRequests`:
1. **Instructor Web Download Route** (`/instructor/courses/<course_id>/files/<asset_id>/download`):
   - `Range: bytes=0-100` returned HTTP `206 Partial Content`, `Content-Length: 101`, `Content-Range: bytes 0-100/1024`, and exact byte slice matching `original_bytes[0:101]`.
   - Middle chunk `bytes=200-499` returned HTTP `206 Partial Content`, `Content-Length: 300`, `Content-Range: bytes 200-499/1024`.
   - Suffix range `bytes=-64` returned HTTP `206 Partial Content`, `Content-Length: 64`, `Content-Range: bytes 960-1023/1024`.
   - Open-ended range `bytes=512-` returned HTTP `206 Partial Content`, `Content-Length: 512`, `Content-Range: bytes 512-1023/1024`.
   - Unsatisfiable range beyond EOF `bytes=1000-2000` on 500-byte file returned HTTP `416 Range Not Satisfiable`.
2. **Student Web Download Route** (`/student/courses/<course_id>/files/<asset_id>/download` and `/student/files/<asset_id>/download`):
   - Enrolled student successfully received HTTP `206 Partial Content` with accurate byte slicing.
   - Fail-closed verification: Unenrolled student attempting download with Range header was rejected with HTTP `403 Forbidden`.
   - Fail-closed verification: Enrolled student attempting download of quarantined file with Range header was rejected with HTTP `403 Forbidden`.
3. **Safe GET API Route** (`/api/files/<asset_id>/download`):
   - Both Web session authentication and JWT Bearer authentication returned HTTP `206 Partial Content` with `X-Content-Type-Options: nosniff`.

### 1.2 Unsticking Mechanism & Rescan Workflow (FAIL on Multi-Revision, PASS on Single-Revision)
1. **Single Revision Clean Rescan**:
   - Rescanning a quarantined file in `quarantine/` promoted `FileAsset.status` to `'ACTIVE'`, `FileRevision.status` to `'ACTIVE'`, `FileRevision.is_current` to `True`, `FileAsset.virus_scan_status` to `'CLEAN'`, migrated the file to permanent deduplicated storage `blobs/ab/cd/<sha256>`, and enabled immediate student download.
2. **Malware / EICAR Rescan**:
   - Rescanning a file containing `EICAR_SIGNATURE_BYTES` moved the file to `infected/<sha256>`, marked `FileRevision.status = "REJECTED"`, set `FileAsset.virus_scan_status = "INFECTED"`, and blocked all access with HTTP `403 Forbidden`.
3. **Defect 1 Observed (CRITICAL - Database Integrity Crash on Multi-Revision Rescan & Override)**:
   - In `src/pwd301/services/file_service.py` lines 1329–1335:
     ```python
     revision.blob_id = blob.id
     revision.status = "ACTIVE"
     revision.is_current = True
     revision.rejection_reason = None
     revision.security_checks_completed_at = now
     revision.activated_at = now
     asset.status = "ACTIVE"
     ```
   - In `src/pwd301/models/file_import.py` lines 381–393:
     ```python
     sa.Index("ux_file_revisions_active", "file_asset_id", unique=True, mssql_where=sa.text("status='ACTIVE'"), sqlite_where=sa.text("status='ACTIVE'"))
     sa.Index("uq_file_revisions_current", "file_asset_id", unique=True, mssql_where=sa.text("is_current = 1"), sqlite_where=sa.text("is_current = 1"))
     ```
   - When an asset already had an active revision (e.g. Revision 1 `status="ACTIVE"`, `is_current=True`) and a newly uploaded revision (Revision 2) was quarantined and subsequently rescanned or overridden, `rescan_file_asset` and `quarantine_override` set `revision.status = "ACTIVE"` and `revision.is_current = True` without demoting Revision 1 (`is_current = False`, `status = "REPLACED"`).
   - **Verbatim Error**:
     ```
     sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: file_revisions.file_asset_id
     [SQL: UPDATE file_revisions SET is_current=?, blob_id=?, status=?, security_checks_completed_at=?, activated_at=? WHERE file_revisions.id = ?]
     [parameters: (1, 2, 'ACTIVE', '2026-09-13 22:52:05.266854', '2026-09-13 22:52:05.266854', 2)]
     ```
4. **Defect 2 Observed (MEDIUM - UI Flash Badge Mismatch in `rescan_course_file_route`)**:
   - In `src/pwd301/blueprints/instructor/routes.py` lines 725–739:
     ```python
     asset = rescan_file_asset(actor, asset_id, session=db.session)
     db.session.commit()
     if asset.status == "ACTIVE":
         flash(f"Tệp tin '{asset.display_name}' đã được quét an toàn và kích hoạt thành công!", "success")
     elif asset.status == "REJECTED":
         flash(f"Cảnh báo: Tệp tin '{asset.display_name}' bị phát hiện mã độc và đã bị cách ly!", "danger")
     else:
         flash(f"Đã kích hoạt quét lại '{asset.display_name}'. Trạng thái: {asset.status}.", "info")
     ```
   - In `src/pwd301/models/file_import.py` line 174:
     `sa.CheckConstraint("status IN ('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')", name="ck_file_assets_2")`
   - Because `FileAsset.status` cannot be `'REJECTED'`, `rescan_file_asset` sets `asset.status = "PENDING"` and `revision.status = "REJECTED"`, which results in `asset.virus_scan_status == "INFECTED"`.
   - As a consequence, `elif asset.status == "REJECTED"` is NEVER True! When malware is detected upon rescan, the instructor is misleadingly flashed:
     `"Đã kích hoạt quét lại 'malware.bin'. Trạng thái: PENDING."` with an INFO badge, instead of the danger warning.
5. **Defect 3 Observed (MEDIUM - Concurrency Race Condition with Async Background Worker)**:
   - In `src/pwd301/services/file_service.py` line 489 and line 790:
     `enqueue_background_job(job_type="FILE_SCAN", payload={"asset_id": asset.id, "user_id": actor.id}, session=sess)`
   - By default, `enqueue_background_job` executes with `run_async=True`, asynchronously launching a thread in `_WORKER_EXECUTOR` that races with the active caller session. Under multi-test execution, this triggered:
     `sqlalchemy.orm.exc.ObjectDeletedError: Instance '<FileAsset>' has been deleted, or its row is otherwise not present.` in `tests/test_m1_file_access.py::test_scanner_error_enqueues_background_job`.

### 1.3 MIME Type & Size Calculations Edge Cases Verification (PASS)
1. **0-Byte Files**:
   - `ck_file_revisions_2` (`CHECK(size_bytes > 0)`) and `ck_file_blobs_1` (`CHECK(size_bytes > 0)`) strictly prohibit persisting 0-byte revisions or blobs.
   - `store_file_stream` validates `size_bytes <= 0` and rejects 0-byte uploads with `FileValidationError("Uploaded file is empty (0 bytes).")`.
   - In-memory / detached `FileAsset` with a mock 0-byte revision evaluates `fa.size_bytes == 0`, `fa.file_size_bytes == 0`, `fa.mime_type == "text/plain"`, `fa.is_video == False`, `fa.is_pdf == False`.
2. **Missing Revision Edge Case**:
   - When a `FileAsset` has 0 revisions (`revisions = []`, `current_revision = None`), all convenience properties safely return non-crashing defaults:
     - `fa.original_filename` -> `fa.display_name`
     - `fa.original_file_name` -> `fa.display_name`
     - `fa.file_name` -> `fa.display_name`
     - `fa.size_bytes` -> `0`
     - `fa.file_size_bytes` -> `0`
     - `fa.mime_type` -> `"application/octet-stream"`
     - `fa.detected_mime_type` -> `"application/octet-stream"`
     - `fa.virus_scan_status` -> `"PENDING"`
     - `fa.is_video` -> `False`
     - `fa.is_pdf` -> `False`
   - Accessing `get_file_for_download` fails closed with `FileSecurityQuarantineError`.
   - Invoking `rescan_file_asset` raises `FileValidationError("File asset has no revisions to rescan.")`.
3. **Multi-MB Files**:
   - 5 MB (5,242,880 bytes) and 25 MB files report exact byte sizes.
   - Template rendering in `course_manage.html` renders size formatted as `5.00 MB` or `5.0 MB`.
   - 1 MB chunk HTTP Range requests (`Range: bytes=1048576-2097151`) stream exactly 1,048,576 bytes with HTTP `206 Partial Content`.

---

## 2. Logic Chain

1. **Premise 1 (HTTP Range Requests)**:
   - Worker implemented `send_file(..., conditional=True)` in instructor, student, and API download routes.
   - Tests in `TestHttpRangeRequests` directly executed requests with `Range: bytes=0-100`, `200-499`, `-64`, `512-`, and out-of-bounds `1000-2000`.
   - All assertions passed: Werkzeug correctly negotiates 206 Partial Content and 416 Range Not Satisfiable, preserving Content-Range, Content-Length, and Accept-Ranges. Fail-closed authorization remains strictly intact.

2. **Premise 2 (Database Uniqueness Invariants on Revisions)**:
   - The database schema defines partial unique indexes `uq_file_revisions_current` (`UNIQUE(file_asset_id) WHERE is_current=1`) and `ux_file_revisions_active` (`UNIQUE(file_asset_id) WHERE status='ACTIVE'`).
   - In `add_file_revision`, the author correctly demoted existing revisions:
     ```python
     for rev in asset.revisions:
         if rev.is_current:
             rev.is_current = False
             rev.status = "REPLACED"
             rev.replaced_at = now
     ```
   - However, in `rescan_file_asset` (lines 1329–1335) and `quarantine_override` (lines 1480–1486), the author directly set `revision.status = "ACTIVE"` and `revision.is_current = True` without demoting prior active revisions.
   - When an existing asset with Revision 1 (`status="ACTIVE"`) receives a Revision 2 that is initially quarantined and then un-quarantined via `rescan_file_asset` or `quarantine_override`, the commit statement violates both unique indexes, crashing with an unhandled `IntegrityError`.
   - Therefore, multi-revision rescan and admin quarantine override are broken.

3. **Premise 3 (Status Alignment between Route and Model)**:
   - `ck_file_assets_2` restricts `FileAsset.status` to `('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')`.
   - When a malware scan fails, `rescan_file_asset` sets `revision.status = "REJECTED"` and `asset.status = "PENDING"`.
   - `FileAsset.virus_scan_status` correctly computes `"INFECTED"` by checking `rev_status == "REJECTED"`.
   - However, `rescan_course_file_route` branches on `elif asset.status == "REJECTED"`, which is never satisfied.
   - Therefore, instructors receive an `info` message stating "Trạng thái: PENDING" instead of a `danger` warning that malware was quarantined.

---

## 3. Caveats

- **Reverse Proxy Acceleration (`USE_X_ACCEL_REDIRECT`)**: In production with Nginx, `send_file(..., conditional=True)` is bypassed in favor of `X-Accel-Redirect` delegation. The upstream Nginx server is responsible for range negotiation when offloading is enabled.
- **SQLite vs MSSQL Unique Partial Indexes**: Both SQLite and Microsoft SQL Server enforce filtered unique indexes (`WHERE is_current = 1` and `WHERE status = 'ACTIVE'`); the `IntegrityError` failure reproduces identically on both database engines.

---

## 4. Conclusion

Milestone 1 shows solid progress: HTTP Range requests (`send_file(..., conditional=True)`), student session download routes, 0-byte/multi-MB calculations, and missing revision edge cases are well-designed and pass all stress tests.

However, Milestone 1 **CANNOT BE APPROVED** in its current state due to a **CRITICAL database integrity violation** and a **MEDIUM UI alert defect**:

1. **CRITICAL Defect**: `rescan_file_asset` and `quarantine_override` in `src/pwd301/services/file_service.py` crash with `IntegrityError` upon rescanning/overriding any asset with existing active revisions.
   - **Remediation**: Before setting `revision.status = "ACTIVE"` and `revision.is_current = True`, loop through `asset.revisions` and demote prior active revisions (`old_rev.is_current = False`, `old_rev.status = "REPLACED"`, `old_rev.replaced_at = now`).
2. **MEDIUM Defect**: `rescan_course_file_route` in `src/pwd301/blueprints/instructor/routes.py` checks `elif asset.status == "REJECTED":` instead of `elif asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED":`.
   - **Remediation**: Update the conditional check in line 730 to inspect `asset.virus_scan_status == "INFECTED"`.

**Verdict**: **REQUEST_CHANGES**

---

## 5. Verification Method

### 5.1 Commands to Reproduce Findings

1. **Run Challenger Stress Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_challenger_stress.py -v
   ```
   **Result**: 15/15 tests run, demonstrating all Range behaviors and capturing the `IntegrityError` under `test_multiple_revisions_quarantined_fallback_and_rescan`.

2. **Run Python Repro of Multi-Revision Rescan Crash**:
   ```powershell
   .venv\Scripts\python.exe -c "
   from pwd301 import create_app
   from pwd301.extensions import db
   from pwd301.models.identity import User, Role
   from pwd301.models.course import Course
   from pwd301.models.file_import import FileAsset, FileRevision, FileBlob
   from pwd301.services.file_service import rescan_file_asset, get_file_quarantine_root, get_file_storage_root
   import uuid, hashlib

   app = create_app('testing')
   with app.app_context():
       db.create_all()
       user = User(email='inst@test.com', display_name='Inst', password_hash=b'12345678901234567890123456789012')
       role = Role(code='INSTRUCTOR', name='Instructor')
       user.roles.append(role)
       db.session.add_all([user, role])
       db.session.flush()
       course = Course(course_code='C1', title='Course', owner_instructor_id=user.id)
       db.session.add(course)
       db.session.flush()

       asset = FileAsset(course_id=course.id, created_by_user_id=user.id, asset_type='RESOURCE', display_name='doc.pdf', status='ACTIVE')
       db.session.add(asset)
       db.session.flush()

       storage_root = get_file_storage_root()
       b_path = storage_root / 'blobs/11/22/fake'
       b_path.parent.mkdir(parents=True, exist_ok=True)
       b_path.write_bytes(b'rev1')
       blob1 = FileBlob(sha256=hashlib.sha256(b'rev1').digest(), size_bytes=4, detected_mime_type='text/plain', storage_key='blobs/11/22/fake', status='PRESENT', reference_count=1)
       db.session.add(blob1)
       db.session.flush()

       rev1 = FileRevision(file_asset_id=asset.id, revision_no=1, is_current=True, original_filename='doc.pdf', detected_mime_type='text/plain', size_bytes=4, status='ACTIVE', blob_id=blob1.id, uploaded_by_user_id=user.id)
       db.session.add(rev1)
       db.session.flush()

       q_path = get_file_quarantine_root() / 'q2.pdf'
       q_path.write_bytes(b'%PDF-1.4 clean rev2')
       rev2 = FileRevision(file_asset_id=asset.id, revision_no=2, is_current=False, original_filename='doc.pdf', detected_mime_type='application/pdf', size_bytes=19, status='QUARANTINED', quarantine_key='quarantine/q2.pdf', uploaded_by_user_id=user.id)
       db.session.add(rev2)
       db.session.commit()

       rescan_file_asset(user, asset.id, session=db.session)
   "
   ```
   **Output**:
   ```
   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: file_revisions.file_asset_id
   [SQL: UPDATE file_revisions SET is_current=?, blob_id=?, status=?, security_checks_completed_at=?, activated_at=? WHERE file_revisions.id = ?]
   ```

3. **Run Full Combined Milestone 1 Test Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/test_m1_challenger_stress.py -v
   ```
