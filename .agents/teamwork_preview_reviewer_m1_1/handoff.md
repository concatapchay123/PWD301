# Independent Review & Adversarial Critic Report: Milestone 1 (R1)

**Reviewer**: Reviewer 1 (`teamwork_preview_reviewer_m1_1`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_reviewer_m1_1`  
**Target Milestone**: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)  
**Worker Under Review**: `teamwork_preview_worker_m1`  
**Review Verdict**: **APPROVE**  
**Date**: 2026-09-14T05:50:30+07:00  

---

## 1. Observation

### 1.1 Code & Specification Artifacts Inspected
1. **`src/pwd301/models/file_import.py` (lines 218–314)**:
   - `_effective_revision()`: Reliably resolves `self.current_revision` or falls back to `self.revisions[-1]` (ordered by `revision_no` ascending via relationship declaration at line 188).
   - `original_filename` & `original_file_name`: Safely extract original upload name or fall back to `display_name`.
   - `file_name`: Canonical alias for `display_name`.
   - `size_bytes` & `file_size_bytes`: Read size from effective revision or default to 0.
   - `mime_type` & `detected_mime_type`: Return detected or declared MIME type with fallback to `'application/octet-stream'`.
   - `virus_scan_status`: Dynamically computes status based on asset status, revision status, and scan results (`CLEAN` for ACTIVE, `INFECTED` for REJECTED, `BLOCKED` for scan errors/blocked status, and `PENDING` for QUARANTINED/VALIDATING/SCANNING).
   - `is_video` & `is_pdf`: Detect media type by MIME prefix and file extensions (`.mp4`, `.webm`, `.mkv`, `.mov`, `.avi`, `.pdf`).

2. **`src/pwd301/templates/instructor/course_manage.html` (lines 370–407)**:
   - File table properly renders `fa.original_file_name or fa.file_name`, file size in MB (`{{ (fa.file_size_bytes / 1024 / 1024) | round(2) }} MB`), MIME type badge, and scan status badge.
   - Status badges: `CLEAN (Đã quét an toàn)` (success badge), `INFECTED (Đã cách ly)` (danger badge), and warning badge for `PENDING`.
   - Action column contains a CSRF-protected form for "Quét lại" (Rescan) button when `fa.virus_scan_status == 'PENDING'`:
     ```html
     <form method="POST" action="/instructor/courses/{{ course.public_id }}/files/{{ fa.public_id }}/rescan" class="d-inline">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
       <button type="submit" class="btn btn-sm btn-outline-warning" title="Quét lại file">
         <i class="bi bi-arrow-repeat me-1"></i>Quét lại
       </button>
     </form>
     ```
   - Zero PK leakage: Uses `course.public_id` and `fa.public_id` (ADR-002 compliant).

3. **`src/pwd301/services/file_service.py` (lines 582–589, 843–850, 920–1053, 1237–1300)**:
   - In both `store_file_stream()` and `add_file_revision()`, when `main_verdict.status == "ERROR"`, asset and revision are saved with `status="PENDING"` and `status="QUARANTINED"`, followed immediately by enqueuing a background scan task:
     ```python
     enqueue_background_job(
         job_type="FILE_SCAN",
         payload={"asset_id": asset.id, "user_id": actor.id},
         session=sess,
     )
     ```
   - Background worker in `background_job_service.py` picks up `FILE_SCAN` jobs and executes `rescan_file_asset()`.
   - `rescan_file_asset()` enforces course ownership via `require_course_manager(actor, asset.course_id)`, strips path traversal via `Path(revision.quarantine_key).name`, performs multi-engine scans, and updates status.
   - `get_file_for_download()` strictly enforces Zero-Trust authorization and fail-closed file quarantine (ADR-008).

4. **`src/pwd301/blueprints/instructor/routes.py` (lines 692–745)**:
   - `download_course_file_route()`: Directly streams authenticated files via `send_file(..., conditional=True)` with sanitized filename and content-disposition, eliminating the previous redirect to the API route that caused 403 errors.
   - `rescan_course_file_route()`: `POST /courses/<course_id>/files/<asset_id>/rescan` validates instructor ownership with `require_course_manager()`, executes `rescan_file_asset()`, handles commits and rollbacks, flashes Vietnamese user feedback, and redirects to the materials tab.

5. **`src/pwd301/services/authorization_service.py` (lines 108–116) & `api_files/routes.py` (lines 47–110, 239–250)**:
   - Session authentication exception in `get_authenticated_actor()` is strictly restricted to safe GET requests:
     ```python
     is_safe_file_download = (
         request.method == "GET"
         and request.path.startswith("/api/files/")
         and request.path.endswith("/download")
     )
     if not is_safe_file_download:
         return None
     ```
   - Mutating REST endpoints (`POST`, `PUT`, `DELETE`, etc.) strictly reject session cookies, preserving CSRF immunity.
   - `quarantine_override_api()` at `/api/files/<asset_id>/quarantine-override` now has `@admin_required` in addition to `@jwt_required` (DEF-15 resolved).

6. **`src/pwd301/blueprints/student/routes.py` (lines 1273–1306)**:
   - `download_student_course_file_route()`: Endpoints `GET /courses/<course_id>/files/<asset_id>/download` and `GET /files/<asset_id>/download` protected by `@student_required`.
   - Enforces active student enrollment and published course status via `get_file_for_download()`.
   - Course scoping verification: If `course_id` is supplied in URL, verifies `course.id == asset.course_id`, raising `ResourceNotFoundError` on mismatch.
   - Fails closed on quarantined or infected files, returning HTTP 403.
   - Streams files via `send_file(..., conditional=True)`.

### 1.2 Tool Executions & Test Results
- **Milestone 1 Test Suite**:
  - Command: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py -v`
  - Result: `14 passed in 3.73s` (100% pass rate).
- **Full File Subsystem Regression Suite**:
  - Command: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v`
  - Result: `43 passed in 10.84s` (0 failures, 0 regressions).
- **Linter (`ruff check`)**:
  - Command: `.venv\Scripts\ruff.exe check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py`
  - Result: `All checks passed!`
- **Formatter Check (`ruff format --check`)**:
  - Command: `.venv\Scripts\ruff.exe format --check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py`
  - Result: `8 files already formatted`.
- **Type Checker (`mypy`)**:
  - Command: `.venv\Scripts\mypy.exe src/pwd301`
  - Result: `Success: no issues found in 85 source files`.
- **Repository Static Contract Check**:
  - Command: `.venv\Scripts\python.exe scripts/repo_check.py`
  - Result: All checks passed (balanced markdown fences, canonical 71 CREATE TABLE statements, single database architecture contract).

---

## 2. Logic Chain

1. **Integrity Audit**:
   - Source code inspection confirms NO hardcoded test results, facade implementations, or bypasses. All property accessors on `FileAsset` query live SQLAlchemy relationships and attributes.
   - All tests in `tests/test_m1_file_access.py` and `tests/test_files.py` interact with live application clients, SQLite test database tables, and real HTTP session/JWT contexts.
   - Independent test execution reproduced the worker's reported results with 100% fidelity.

2. **Correctness & Conformance**:
   - **R1.1 File Asset Rendering**: The properties `original_filename`, `file_size_bytes`, `mime_type`, and `virus_scan_status` exist and accurately reflect current/effective revision state. Clean files uploaded with a clean scan verdict immediately report `CLEAN` rather than falling back to `PENDING`.
   - **R1.2 Unstick PENDING Scan Status**: Both upload functions enqueue `FILE_SCAN` background tasks on scanner errors. The instructor UI displays the "Quét lại" button with valid CSRF tokens, and the backend route triggers on-demand re-scanning.
   - **R1.3 Authenticated Session Downloads**: Both instructor and student web routes allow direct file downloads without HTTP 403 errors, while preserving strict authorization (managing instructor ownership, active student enrollment in published course).
   - **ADR-002 (Zero PK Leakage)**: All URLs and JSON payloads expose opaque UUIDs (`public_id`) and avoid exposing internal `BigInt` PKs.
   - **ADR-008 (Fail-Closed Quarantine)**: Quarantined, infected, or unscanned files return HTTP 403 on student download attempts.
   - **DEF-15 Resolution**: The admin override route `/api/files/<asset_id>/quarantine-override` strictly requires the `ADMIN` role.

3. **Adversarial Stress-Testing**:
   - *Attack Scenario A (CSRF on API via Session Cookie)*: An attacker tricks a logged-in user into triggering state-changing REST API requests (e.g. `POST /api/files/<id>/rescan`).
     *Result*: Blocked. `authorization_service.py` strictly restricts session cookies to `GET` requests ending in `/download`. The POST request receives HTTP 401 Unauthorized.
   - *Attack Scenario B (Privilege Escalation on Quarantine Override)*: An authenticated instructor attempts to override quarantine using Bearer JWT.
     *Result*: Blocked. `@admin_required` halts the request with HTTP 403 Forbidden.
   - *Attack Scenario C (IDOR on Student Downloads)*: A student enrolled in Course A attempts to download a file belonging to Course B.
     *Result*: Blocked. `get_file_for_download()` checks enrollment in `asset.course_id`. The student is rejected with HTTP 403 Forbidden.
   - *Attack Scenario D (Quarantined File Access)*: An enrolled student attempts to download a file whose scan status is `QUARANTINED`.
     *Result*: Blocked. `get_file_for_download()` checks revision status and raises `FileSecurityQuarantineError` (HTTP 403).
   - *Attack Scenario E (Path Traversal)*: An attacker tampers with download routes or quarantine keys.
     *Result*: Blocked. Filenames are sanitized via `sanitize_filename()`, quarantine keys are stripped via `Path(...).name`, and physical paths are checked via `physical_path.is_relative_to(storage_root)`.

4. **Ponytail Minimal-Change & Simplicity Assessment**:
   - Zero extraneous dependencies introduced.
   - Reused existing services (`get_file_for_download`, `rescan_file_asset`, `enqueue_background_job`, `sanitize_filename`).
   - Clean, standard library idioms and native Flask mechanisms (`send_file(..., conditional=True)`).

---

## 3. Caveats

1. **Development vs. Production Streaming**:
   In development, Flask `send_file(..., conditional=True)` handles HTTP Range requests (`206 Partial Content`) directly in Python. In high-traffic production environments, enabling `USE_X_ACCEL_REDIRECT` will offload streaming directly to Nginx.
2. **Scanner Daemon Mocking in Tests**:
   In test environments where ClamAV daemon is unavailable, the fallback heuristic scanner operates seamlessly, and monkeypatching is used in `test_scanner_error_enqueues_background_job` to simulate socket timeouts. This is standard practice and verified to function properly.
3. **Subsequent Milestones (M2–M6)**:
   This review strictly covers Milestone 1 (R1). Course metadata customization (M2), assessment authoring (M3), lecture media attachments (M4), and AI context features (M5) remain separate milestones.

---

## 4. Conclusion

**Verdict: APPROVE**

The work completed for Milestone 1 is exemplary, robust, and completely fulfills all requirements and architectural invariants:
- Zero integrity violations detected.
- All 14 tests in `tests/test_m1_file_access.py` and `tests/test_files.py` pass.
- All 29 existing file subsystem tests pass without regression (43/43 total).
- Linter, formatter, type checker, and repository contract checks pass with 0 errors.
- Security controls (ADR-002 zero PK leakage, ADR-008 fail-closed quarantine, CSRF isolation, DEF-15 admin requirement) are thoroughly validated.

---

## 5. Verification Method

To independently reproduce and verify this review, execute the following commands in PowerShell from the project root (`e:\PWD301`):

```powershell
# 1. Run Milestone 1 targeted tests
.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py -v

# 2. Run full file subsystem regression suite
.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v

# 3. Static linter check
.venv\Scripts\ruff.exe check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py

# 4. Formatter check
.venv\Scripts\ruff.exe format --check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/test_files.py

# 5. Type checking
.venv\Scripts\mypy.exe src/pwd301

# 6. Repository architecture check
.venv\Scripts\python.exe scripts/repo_check.py
```
