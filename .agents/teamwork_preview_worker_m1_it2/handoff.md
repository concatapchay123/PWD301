# Handoff Report: Milestone 1 Iteration 2 Remediation
**Author**: Worker M1 Iteration 2 (`teamwork_preview_worker_m1_it2`)  
**Working Directory**: `e:\PWD301\.agents\teamwork_preview_worker_m1_it2`  
**Date**: 2026-09-14T06:01:00Z  
**Target Milestone**: Milestone 1 (R1: File Upload, Virus Scanning & Secure Access Remediation)  
**Handoff Type**: Hard (Remediation Complete)  
**Verdict**: **READY_FOR_AUDIT**

---

## 1. Observation

### 1.1 Baseline Defects Observed
1. **Defect 1 (CRITICAL - Multi-Revision Unique Partial Index Violation)**:
   - File: `src/pwd301/services/file_service.py` lines 1329–1335 (`rescan_file_asset`) and lines 1480–1486 (`quarantine_override`).
   - Observations:
     - When activating a revision upon successful clean rescan or admin override, code set:
       ```python
       revision.blob_id = blob.id
       revision.status = "ACTIVE"
       revision.is_current = True
       revision.rejection_reason = None
       revision.security_checks_completed_at = now
       revision.activated_at = now
       asset.status = "ACTIVE"
       ```
     - Database schema in `src/pwd301/models/file_import.py` defines filtered partial unique constraints:
       - `ux_file_revisions_active` (`UNIQUE(file_asset_id) WHERE status='ACTIVE'`)
       - `uq_file_revisions_current` (`UNIQUE(file_asset_id) WHERE is_current=1`)
     - In multi-revision assets (e.g., Rev 1 is `ACTIVE` and `is_current=True`, Rev 2 was uploaded but quarantined), rescanning or overriding Rev 2 attempted to activate Rev 2 without demoting Rev 1, causing a fatal DB crash:
       ```
       sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: file_revisions.file_asset_id
       [SQL: UPDATE file_revisions SET is_current=?, blob_id=?, status=?, security_checks_completed_at=?, activated_at=? WHERE file_revisions.id = ?]
       ```

2. **Defect 2 (MEDIUM - Flash Message Status Mismatch in `rescan_course_file_route`)**:
   - File: `src/pwd301/blueprints/instructor/routes.py` line 730 (`rescan_course_file_route`).
   - Observations:
     - The route conditionally branched on:
       ```python
       elif asset.status == "REJECTED":
           flash(f"Cảnh báo: Tệp tin '{asset.display_name}' bị phát hiện mã độc và đã bị cách ly!", "danger")
       ```
     - However, `FileAsset.status` constraint `ck_file_assets_2` only permits values `('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')`. `FileAsset.status` is never set to `"REJECTED"`; instead, the rejected status resides on `FileRevision.status == "REJECTED"`, and `FileAsset.virus_scan_status` computes `"INFECTED"`.
     - Because `asset.status == "REJECTED"` never evaluated to True, detecting malware upon rescan misleadingly flashed an `info` message stating: `"Đã kích hoạt quét lại 'malware.bin'. Trạng thái: PENDING."` instead of the danger alert.

3. **Defect 3 (MEDIUM - Concurrency Race Condition in Asynchronous Background Job Enqueueing)**:
   - File: `src/pwd301/services/file_service.py` line 584 (`store_file_stream`) and line 845 (`add_file_revision`).
   - Observations:
     - When scanner timed out or errored, `enqueue_background_job` was called with default `run_async=True`.
     - This immediately submitted an asynchronous task to `_WORKER_EXECUTOR` before the calling session committed the database transaction (`sess.commit()`).
     - In test sandboxes and concurrent executions, this triggered race conditions:
       ```
       sqlalchemy.orm.exc.ObjectDeletedError: Instance '<FileAsset>' has been deleted, or its row is otherwise not present.
       ```
       as well as SQLite database file locking hangs during consecutive test execution.

---

## 2. Logic Chain

1. **Remediation for Defect 1 (`file_service.py`)**:
   - Prior to activating `revision` (`revision.status = "ACTIVE"` and `revision.is_current = True`) in both `rescan_file_asset` and `quarantine_override`, iterate over all revisions in `asset.revisions`:
     ```python
     for rev in asset.revisions:
         if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
             rev.is_current = False
             rev.status = "REPLACED"
             rev.replaced_at = now
     ```
   - This ensures that exactly one revision remains `ACTIVE` and `is_current=True` per asset, strictly preserving the partial unique indexes `ux_file_revisions_active` and `uq_file_revisions_current`.

2. **Remediation for Defect 2 (`instructor/routes.py`)**:
   - In `rescan_course_file_route`, updated line 730 condition from:
     `elif asset.status == "REJECTED":`
     to:
     `elif asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED":`
   - When a rescan detects malware, `asset.virus_scan_status` evaluates to `"INFECTED"`, correctly triggering the danger flash message: `"Cảnh báo: Tệp tin '...' bị phát hiện mã độc và đã bị cách ly!"`.

3. **Remediation for Defect 3 (`file_service.py`)**:
   - In both `store_file_stream` and `add_file_revision`, passed `run_async=False` to `enqueue_background_job`:
     ```python
     enqueue_background_job(
         job_type="FILE_SCAN",
         payload={"asset_id": asset.id, "user_id": actor.id},
         run_async=False,
         session=sess,
     )
     ```
   - The job is securely committed in `background_jobs` with status `"QUEUED"`. Workers can claim and process it deterministically without uncoordinated thread dispatch racing with the caller's active database transaction or test fixture teardown.

4. **Test Suite Enhancements (`tests/test_m1_challenger_stress.py`)**:
   - Updated `test_multiple_revisions_quarantined_fallback_and_rescan` from asserting an `IntegrityError` reproduction to verifying genuine success: `rev2` becomes `ACTIVE` and current, while `rev1` is demoted to `REPLACED` and `is_current=False`.
   - Added `test_multiple_revisions_quarantine_override_demotes_prior_revision` verifying that admin quarantine override on multi-revision files correctly demotes prior active revisions and satisfies uniqueness constraints.
   - Added `test_instructor_rescan_infected_file_flashes_danger_alert` verifying that rescanning an infected file displays the danger alert banner in the UI and does not show `"Trạng thái: PENDING"`.

---

## 3. Caveats

- **External Worker Daemon in Production**: With `run_async=False`, jobs are enqueued into the persistent database table `background_jobs`. In production deployments, background jobs are consumed by the dedicated worker loop (`run_worker_loop()`) or a Celery/systemd daemon.
- No other caveats.

---

## 4. Conclusion

All 3 defects reported by Challenger 2 have been remediated with minimal, genuine code changes:
- Defect 1 (CRITICAL): Resolved by demoting prior active/current revisions before activating any revision in `rescan_file_asset` and `quarantine_override`.
- Defect 2 (MEDIUM): Resolved by inspecting `asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED"` in `rescan_course_file_route`.
- Defect 3 (MEDIUM): Resolved by passing `run_async=False` in `enqueue_background_job` during `store_file_stream` and `add_file_revision`.
- Test Pass Rate: 100% across all Milestone 1 and file test suites (108/108 tests passing).
- Static Analysis: 0 errors in `ruff check` and `mypy`.

---

## 5. Verification Method

### 5.1 Project Verification Commands & Actual Results

1. **Challenger Stress Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_challenger_stress.py -v
   ```
   **Result**: 17/17 passed in 4.97s (including multi-revision rescan, multi-revision override, and danger flash alert tests).

2. **Adversarial Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_adversarial.py -v
   ```
   **Result**: 24/24 passed in 7.52s.

3. **Milestone 1 File Access & Management Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py -v
   ```
   **Result**: 14/14 passed in 3.69s with zero race conditions or database locks.

4. **Full Combined File Subsystem Test Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_file_access.py tests/test_files.py tests/test_m1_challenger_stress.py tests/test_m1_adversarial.py tests/api/test_file_api.py tests/security/test_file_authorization_idor.py tests/unit/test_file_service.py tests/security/test_quarantine_fail_closed.py tests/api/test_scan_api.py -v
   ```
   **Result**: 108/108 passed in 29.46s (100% pass rate).

5. **Static Analysis & Lint Check**:
   ```powershell
   .venv\Scripts\ruff.exe check src/pwd301 tests/test_m1_challenger_stress.py
   .venv\Scripts\ruff.exe format --check src/pwd301 tests/test_m1_challenger_stress.py
   ```
   **Result**: "All checks passed!", 89 files already formatted.

6. **Type Checking**:
   ```powershell
   .venv\Scripts\mypy.exe src/pwd301
   ```
   **Result**: "Success: no issues found in 85 source files".
