# Reviewer 2 Handoff Report: Milestone 1 Verification & Adversarial Review
**Author**: Reviewer 2 (`teamwork_preview_reviewer_m1_2`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_reviewer_m1_2`  
**Target Milestone**: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)  
**Date**: 2026-09-13T22:52:00Z  
**Handoff Type**: Hard (Task Complete)  
**Verdict**: **APPROVE**  

---

## 1. Observation

### 1.1 Integrity & Facade Check Observations
- Inspected `src/pwd301/models/file_import.py` (lines 218–313):
  ```python
  def _effective_revision(self) -> Any:
      if self.current_revision is not None:
          return self.current_revision
      if self.revisions:
          return self.revisions[-1]
      return None
  ```
  Properties `original_filename`, `original_file_name`, `file_name`, `size_bytes`, `file_size_bytes`, `mime_type`, `detected_mime_type`, `virus_scan_status`, `is_video`, `is_pdf` dynamically resolve child revisions and scan statuses. There are no hardcoded mock returns, fake values, or dummy facades.
- Inspected `src/pwd301/services/file_service.py` (lines 581–589, 839–847):
  ```python
  sess.flush()
  from pwd301.services.background_job_service import enqueue_background_job
  enqueue_background_job(
      job_type="FILE_SCAN",
      payload={"asset_id": asset.id, "user_id": actor.id},
      session=sess,
  )
  ```
  Real background job enqueueing is invoked when scanner errors occur in `store_file_stream` and `add_file_revision`.
- Inspected `src/pwd301/blueprints/api_files/routes.py` (line 239–242):
  ```python
  @api_file_bp.route("/<asset_id>/quarantine-override", methods=["POST"])
  @jwt_required
  @admin_required
  def quarantine_override_api(asset_id: str) -> tuple[Response, int] | Response:
  ```
  `@admin_required` decorator is genuinely present (resolving DEF-15).
- Inspected `src/pwd301/services/authorization_service.py` (lines 106–115):
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
  Safe GET download allows session cookies; all state-changing `/api/*` endpoints continue rejecting session cookies unconditionally.
- Inspected `src/pwd301/blueprints/instructor/routes.py` (lines 692–748):
  - `download_course_file_route`: Calls `require_course_manager(actor, course_id)`, retrieves file via `get_file_for_download`, and directly streams using `send_file(..., conditional=True)`.
  - `rescan_course_file_route`: POST route invoking `rescan_file_asset`, flashing appropriate alert messages (`ACTIVE`, `REJECTED`, or pending status), and redirecting back to the materials tab.
- Inspected `src/pwd301/blueprints/student/routes.py` (lines 1273–1305):
  ```python
  @student_bp.route("/courses/<course_id>/files/<asset_id>/download", methods=["GET"])
  @student_bp.route("/files/<asset_id>/download", methods=["GET"])
  @student_required
  def download_student_course_file_route(asset_id: str, course_id: str | None = None) -> Any:
      actor = require_authenticated_actor()
      ...
      asset, blob, physical_path = get_file_for_download(
          actor, asset_id, revision_no=revision_no, session=db.session
      )
      if course_id is not None:
          course = _resolve_course(course_id, session=db.session)
          if course is None or course.id != asset.course_id:
              raise ResourceNotFoundError("File asset not found for the specified course.")
  ```
- Inspected `src/pwd301/services/file_service.py` (lines 1016–1050):
  ```python
  if revision is not None:
      if revision.status == "REJECTED":
          raise FileInfectedError("File revision is rejected due to malware detection.")
      if revision.status == "QUARANTINED":
          raise FileSecurityQuarantineError("File revision is quarantined pending security clearance.")
      for scan in revision.scan_results:
          if scan.status == "FAIL":
              raise FileInfectedError("File security verification detected malware.")
          elif scan.status == "ERROR":
              raise FileSecurityQuarantineError("File security verification error.")
  ...
  if asset.status != "ACTIVE":
      raise FileSecurityQuarantineError(f"File asset is not accessible (status: {asset.status}).")
  if revision is None or revision.status not in ("ACTIVE", "REPLACED"):
      raise FileSecurityQuarantineError("File revision is quarantined or not approved for access.")
  ```

### 1.2 Automated Tool Execution Results
- **Command**: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/security/test_file_authorization_idor.py -v`
  **Output**: `24 passed in 6.69s` (Exit code: 0).
- **Command**: `.venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v`
  **Output**: `43 passed in 10.70s` (Exit code: 0).
- **Command**: `.venv\Scripts\mypy.exe src/pwd301`
  **Output**: `Success: no issues found in 85 source files` (Exit code: 0).
- **Command**: `.venv\Scripts\ruff.exe check src/pwd301/models/file_import.py src/pwd301/services/file_service.py src/pwd301/services/authorization_service.py src/pwd301/blueprints/api_files/routes.py src/pwd301/blueprints/instructor/routes.py src/pwd301/blueprints/student/routes.py tests/test_m1_file_access.py tests/security/test_file_authorization_idor.py`
  **Output**: `All checks passed!` (Exit code: 0).

---

## 2. Logic Chain

1. **Integrity Validation (Observation 1.1)**:
   - Evaluated all additions against forbidden integrity patterns: no hardcoded outputs in production code, no mock shortcuts, no facades. The logic directly queries and writes to SQLAlchemy models (`FileAsset`, `FileRevision`, `FileScanResult`, `BackgroundJob`).
   - The test suites do not rely on pre-baked fixtures or hardcoded mock returns; tests create actual assets, run real background job dispatch logic, and test against real database transactions.

2. **Fail-Closed Security Invariant Analysis (Observation 1.1)**:
   - When a student or instructor requests a file via `/student/courses/<cid>/files/<fid>/download`, `/student/files/<fid>/download`, `/instructor/.../download`, or `/api/files/<fid>/download`, `get_file_for_download` is invoked *prior* to preparing any file stream or calling `send_file`.
   - If the file revision or asset status is `QUARANTINED`, `PENDING`, `REJECTED`, or has scan results with `FAIL` or `ERROR`, `FileSecurityQuarantineError` or `FileInfectedError` is raised.
   - In `src/pwd301/__init__.py` line 271, `FileSecurityQuarantineError` is explicitly mapped to `("FILE_QUARANTINED", 403)`.
   - Zero bytes are transmitted to the client, preserving strict fail-closed file access.

3. **Unauthorized Actor Matrix (Observation 1.1 & Test Verification)**:
   - **Unauthenticated**: Blocked by `@instructor_required` or `@student_required` with 401 Unauthorized / redirect to login; or in API routes via `require_authenticated_actor` returning 401.
   - **Unenrolled Student**: In `get_file_for_download`, `Enrollment.status == "ACTIVE"` is queried. If non-existent or inactive, `FileAccessDeniedError("You are not actively enrolled in this course.")` is raised, yielding HTTP 403 Forbidden.
   - **Wrong Course Manager**: In `download_course_file_route`, `require_course_manager(actor, course_id)` enforces course ownership. In `get_file_for_download`, `course.owner_instructor_id == actor.id` is verified for `asset.course_id`. In `rescan_file_asset`, `require_course_manager(actor, asset.course_id)` is enforced. Cross-tenant or foreign instructor access is blocked with HTTP 403 Forbidden.

4. **DEF-15 Resolution (Observation 1.1 & Test Verification)**:
   - `/api/files/<asset_id>/quarantine-override` now has both `@jwt_required` and `@admin_required`.
   - Tests confirm non-admin instructors receive HTTP 403 Forbidden (`Access denied: insufficient role permissions.`), while administrators succeed (HTTP 200).

5. **Test and Static Coverage Verification (Observation 1.2)**:
   - All 24 targeted tests and 43 full file subsystem tests executed independently and passed with 100% success.
   - Mypy verified 85 source files with zero type issues.

---

## 3. Caveats

1. **Reverse Proxy Acceleration (`X-Accel-Redirect` / `X-Sendfile`)**: In the current Flask implementation, `send_file(..., conditional=True)` handles range requests and streaming directly in Python. In high-throughput production environments with Nginx/Caddy, offloading file streaming to web server internal redirects can reduce Python worker thread saturation.
2. **Course ID / Asset ID Consistency in Instructor Route**: In `download_course_file_route`, `require_course_manager(actor, course_id)` is called followed by `get_file_for_download(actor, asset_id)`. If an instructor owns both Course 1 and Course 2, but requests `/instructor/courses/<course_1_id>/files/<asset_2_id>/download`, the file streams because the instructor owns Course 2 as well. Unlike `student/routes.py`, it does not raise a 404 for route-course mismatch. This is a minor URL hygiene observation, not a security vulnerability.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 1 satisfies all functional, architectural, and security requirements:
- Clean files display accurate scan status badges (`CLEAN`), sizes in MB, and original filenames in instructor and student templates.
- Stuck pending scans are automatically queued for background scanning and can be rescanned on-demand via an authenticated Web UI action.
- Web session downloads function cleanly for authorized actors without 403 errors, while maintaining anti-CSRF protections on mutating API routes.
- Fail-closed security invariants and IDOR protections are strictly enforced.
- DEF-15 is resolved with `@admin_required`.
- Zero regressions across the entire file testing suite.

---

## 5. Verification Method

To independently verify this assessment:

1. **Run Target M1 & IDOR Test Suites**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/security/test_file_authorization_idor.py -v
   ```
   *Expected*: 24 passed in < 10 seconds.

2. **Run Full File Subsystem Test Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py -v
   ```
   *Expected*: 43 passed in < 15 seconds.

3. **Run Type Checking**:
   ```powershell
   .venv\Scripts\mypy.exe src/pwd301
   ```
   *Expected*: `Success: no issues found in 85 source files`.

4. **Verify Invalidation Conditions**:
   - The review conclusion would be invalidated if any quarantined file streamed bytes to a student, if a non-admin could invoke `quarantine-override`, or if session cookies could authenticate a state-changing API request (`POST /api/files/...`).
