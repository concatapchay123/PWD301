# Forensic Audit Report: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)

**Auditor**: Forensic Auditor M1 (`teamwork_preview_auditor_m1`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_auditor_m1`  
**Date**: 2026-09-14T05:51:00Z  
**Target Milestone**: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)  
**Handoff Type**: Hard (Audit Complete)  
**Profile**: General Project  
**Integrity Mode**: Development (from `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## Forensic Audit Report

**Work Product**: Milestone 1 Changes:
- `src/pwd301/models/file_import.py`
- `src/pwd301/services/file_service.py`
- `src/pwd301/services/authorization_service.py`
- `src/pwd301/blueprints/api_files/routes.py`
- `src/pwd301/blueprints/instructor/routes.py`
- `src/pwd301/blueprints/student/routes.py`
- `src/pwd301/templates/instructor/course_manage.html`
- `tests/test_m1_file_access.py`
- `tests/test_files.py`

**Verdict**: **CLEAN**

### Phase Results
- **Hardcoded Test Results Check**: **PASS** — Zero hardcoded test return strings, literals matching test users, or canned test assertions found in `src/`.
- **Facade Implementation Check**: **PASS** — All models, properties, routes, and services implement genuine application logic with real SQL queries, filesystem I/O, and streaming.
- **Fabricated Verification Output Check**: **PASS** — Workspace was scanned for pre-populated logs, cached test artifacts, or fake attestation files; none existed.
- **Dynamic Property Calculation**: **PASS** — `FileAsset` properties (`original_filename`, `size_bytes`, `mime_type`, `virus_scan_status`, `is_video`, `is_pdf`) dynamically derive from effective child `FileRevision` and `FileScanResult` entities.
- **Secure File Streaming & Authorization**: **PASS** — `download_course_file_route` and `download_student_course_file_route` perform zero-trust role/enrollment verification and stream physical bytes with `send_file(..., conditional=True)`.
- **Background Job Enqueueing & Rescan**: **PASS** — Genuine `FILE_SCAN` job persistence in `background_jobs` table upon scanner errors; `rescan_file_asset` genuinely rescans bytes, recalculates hashes, migrates quarantined blobs, and activates revisions.
- **Automated Verification & Regression Check**: **PASS** — 14/14 Milestone 1 tests pass, 43/43 file subsystem tests pass, Ruff check passes (0 violations), Ruff format passes, Mypy typecheck passes (0 errors across 85 files).

---

## 1. Observation

### 1.1 Source Code and Git Diff Analysis
1. **`src/pwd301/models/file_import.py` (lines 218–315)**:
   - Added `_effective_revision()` method returning `self.current_revision or (self.revisions[-1] if self.revisions else None)`.
   - Added dynamic properties:
     - `original_filename` / `original_file_name`: Reads `rev.original_filename` or falls back to `self.display_name`.
     - `file_name`: Returns `self.display_name`.
     - `size_bytes` / `file_size_bytes`: Reads `rev.size_bytes` or returns `0`.
     - `mime_type` / `detected_mime_type`: Reads `rev.detected_mime_type or rev.declared_mime_type or 'application/octet-stream'`.
     - `virus_scan_status`: Inspects `self.status`, `rev.status`, and `rev.scan_results` status flags (`ERROR` -> `'BLOCKED'`, `'ACTIVE'` -> `'CLEAN'`, `'REJECTED'` -> `'INFECTED'`, `'PENDING'` / `'QUARANTINED'` -> `'PENDING'`).
     - `is_video`: Validates `video/` MIME type prefix and `.mp4`, `.webm`, `.mkv`, `.mov`, `.avi` extensions.
     - `is_pdf`: Validates `application/pdf` MIME type and `.pdf` extension.
   - Observation: No hardcoded return values. All properties query real relational attributes.

2. **`src/pwd301/services/file_service.py` (lines 581–589, 841–850, 1237–1340)**:
   - In `store_file_stream` and `add_file_revision`: On scanner error/timeout, `enqueue_background_job(job_type="FILE_SCAN", payload={"asset_id": asset.id, "user_id": actor.id}, session=sess)` is invoked, persisting a background job to database.
   - In `rescan_file_asset`: Genuinely locates the physical file in quarantine root or storage root, executes `scan_file_all_engines` and `scan_blob_file`, verifies sha256 checksums, moves files on disk, updates `FileBlob` and `FileRevision` statuses, and transitions `FileAsset.status` from `'PENDING'` to `'ACTIVE'` (or `'REJECTED'`).

3. **`src/pwd301/services/authorization_service.py` (lines 106–116)**:
   - In `get_authenticated_actor()`:
     ```python
     if has_request_context() and (request.path == "/api" or request.path.startswith("/api/")):
         is_safe_file_download = (
             request.method == "GET"
             and request.path.startswith("/api/files/")
             and request.path.endswith("/download")
         )
         if not is_safe_file_download:
             return None
     ```
   - Observation: Only safe, idempotent GET requests to `/api/files/<asset_id>/download` allow web session cookies. All mutating (`POST`, `PUT`, `DELETE`) and all other `/api/*` requests strictly reject session authentication, maintaining complete anti-CSRF isolation.

4. **`src/pwd301/blueprints/api_files/routes.py` (line 241)**:
   - Decorated `quarantine_override_api` with `@admin_required` (resolving DEF-15).

5. **`src/pwd301/blueprints/instructor/routes.py` (lines 693–749)**:
   - Replaced redirect in `download_course_file_route` with direct streaming: calls `require_course_manager(actor, course_id)`, calls `get_file_for_download`, sanitizes filename, and streams via `send_file(physical_path, mimetype=blob.detected_mime_type, as_attachment=(disposition == 'attachment'), download_name=clean_filename, conditional=True)`.
   - Added `rescan_course_file_route` (`POST /courses/<course_id>/files/<asset_id>/rescan`): Enforces course manager permissions, calls `rescan_file_asset`, commits transaction, flashes user alert, and redirects to materials tab.

6. **`src/pwd301/blueprints/student/routes.py` (lines 1273–1305)**:
   - Added `download_student_course_file_route` (`GET /courses/<course_id>/files/<asset_id>/download` and `GET /files/<asset_id>/download`): Decorated with `@student_required`, calls `get_file_for_download`, checks course ownership matching, and streams file via `send_file(..., conditional=True)`.

7. **`src/pwd301/templates/instructor/course_manage.html` (lines 370–405)**:
   - Correctly renders `fa.original_file_name or fa.file_name`, file size in MB, MIME type badge, and scan status badges (`CLEAN (Đã quét an toàn)`, `INFECTED (Đã cách ly)`, `PENDING`).
   - Renders a CSRF-protected "Quét lại" form button when `fa.virus_scan_status == 'PENDING'`.

### 1.2 Automated Tool Execution & Verifications
- **Pytest Target M1 Suite**:
  - Command: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py -v`
  - Output: `14 passed in 3.73s`
- **Pytest All File Subsystems Suite**:
  - Command: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v`
  - Output: `43 passed in 10.76s` (0 failures, 0 regressions)
- **Ruff Linter Check**:
  - Command: `.venv\Scripts\ruff.exe check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py`
  - Output: `All checks passed!`
- **Ruff Format Check**:
  - Command: `.venv\Scripts\ruff.exe format --check ...`
  - Output: `8 files already formatted`
- **Mypy Static Type Checker**:
  - Command: `.venv\Scripts\mypy.exe src/pwd301`
  - Output: `Success: no issues found in 85 source files`

### 1.3 Independent Adversarial Stress Tests
Three independent scripts were executed directly in Python:
1. **Adversarial Test 1 (Dynamic FileAsset Properties)**:
   - Initial state (no revision): Fallback to display name, size 0, octet-stream MIME, PENDING status.
   - Adding active PDF revision: Properties updated to revision name, 1000 bytes, application/pdf, is_pdf=True, is_video=False, CLEAN status.
   - Adding rejected video revision: Properties fell back to revisions[-1], size 5MB, is_video=True, INFECTED status.
   - Adding scan error result: Status transitioned to BLOCKED.
   - Result: `PASSED`
2. **Adversarial Test 2 (Streaming & Authorization)**:
   - Unauthenticated download rejected (HTTP 302/401/403).
   - Instructor download succeeded with matching payload bytes (`FORENSIC_INTEGRITY_CHECK_RANDOM_PAYLOAD_1234567890`).
   - Unenrolled student download rejected (HTTP 403).
   - Enrolled student download succeeded with matching payload bytes.
   - Unpublishing course resulted in immediate HTTP 403 rejection for enrolled student.
   - Quarantined file resulted in HTTP 403 fail-closed rejection for enrolled student.
   - Result: `ALL 6 SUBTESTS PASSED`
3. **Adversarial Test 3 (Background Job Enqueueing & Rescan File Asset)**:
   - Enqueued background job created genuine row in `BackgroundJob` table with valid JSON payload.
   - Calling `rescan_file_asset` on quarantined file located physical file, scanned it, migrated bytes to storage blob, marked revision and asset ACTIVE, and deleted quarantine copy.
   - Result: `ALL PASSED`

---

## 2. Logic Chain

1. **Premise**: An integrity violation occurs if code hardcodes outputs to pass tests, stubs interfaces with empty or fixed returns, bypasses security authorization checks, or falsifies scan statuses.
2. **Observation**:
   - `FileAsset` properties read directly from `_effective_revision()`. When the underlying revision or scan results change, the properties immediately return the new values without any hardcoded mapping.
   - Both Web UI streaming endpoints (`download_course_file_route` and `download_student_course_file_route`) call `get_file_for_download`, which executes a zero-trust multi-factor authorization check (role validation, course ownership for instructor, active enrollment and published course status for student, fail-closed quarantine and infected checks).
   - In the adversarial test, when an unenrolled student or a student accessing a quarantined file attempts download, the system returns HTTP 403. When authorized, exact disk bytes are streamed.
   - In `authorization_service.py`, session authentication is only permitted for safe GET download requests; all mutating routes return `None` when bearer JWT is missing, preserving CSRF isolation.
   - In `file_service.py`, `enqueue_background_job` inserts real jobs into the database and `rescan_file_asset` genuinely hashes and moves files on the local disk.
   - Static analysis tools (`ruff`, `mypy`) confirm standard compliance and absence of unused imports or type errors.
   - Regression testing across all 43 file subsystem tests yielded 100% passing tests with 0 failures.
3. **Conclusion**: The implementation is authentic, complete, resilient, and adheres strictly to the System Specification and non-negotiable invariants.

---

## 3. Caveats

- In production behind Nginx, `send_file(..., conditional=True)` can be configured with `USE_X_ACCEL_REDIRECT` for zero-copy kernel offloading. In development, Flask's internal range request handling performs correctly.
- Background worker execution relies on periodic job polling or asynchronous dispatch. In the test environment, jobs are processed synchronously or via immediate runner.

---

## 4. Conclusion

**Verdict: CLEAN**

Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation) contains zero integrity violations, zero cheating patterns, and zero hardcoded test facades. All requirements in `ORIGINAL_REQUEST.md` §R1 are satisfied with genuine, robust code. The work product is approved.

---

## 5. Verification Method

To independently reproduce this forensic audit:

1. **Run Unit and Integration Tests**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py -v
   ```
   *Expected*: 14 passed.

2. **Run Full File Subsystem Regression Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v
   ```
   *Expected*: 43 passed.

3. **Run Static Linters and Type Checking**:
   ```powershell
   .venv\Scripts\ruff.exe check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py
   .venv\Scripts\ruff.exe format --check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py
   .venv\Scripts\mypy.exe src/pwd301
   ```
   *Expected*: 0 violations, 85 source files verified.

4. **Verify Zero Cheating Strings**:
   ```powershell
   git grep -i "test_m1" src/
   git grep -i "syllabi" src/
   ```
   *Expected*: 0 matches.
