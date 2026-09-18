# Forensic Audit Report: Milestone 1 Iteration 2
**Auditor**: Forensic Auditor (`teamwork_preview_auditor_m1_it2`)  
**Target Work Product**: Worker M1 Iteration 2 changes in `src/pwd301/services/file_service.py`, `src/pwd301/blueprints/instructor/routes.py`, and `tests/test_m1_challenger_stress.py`  
**Profile**: General Project (Development Mode per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## 1. Observation

### 1.1 Revision Demotion Inspection in `src/pwd301/services/file_service.py`
1. In `rescan_file_asset` (lines 1331–1336):
   ```python
   for rev in asset.revisions:
       if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
           rev.is_current = False
           rev.status = "REPLACED"
           rev.replaced_at = now
   ```
   Immediately followed by (lines 1337–1343):
   ```python
   revision.blob_id = blob.id
   revision.status = "ACTIVE"
   revision.is_current = True
   revision.rejection_reason = None
   revision.security_checks_completed_at = now
   revision.activated_at = now
   asset.status = "ACTIVE"
   ```
2. In `quarantine_override` (lines 1488–1493):
   ```python
   for rev in asset.revisions:
       if rev.id != revision.id and (rev.is_current or rev.status == "ACTIVE"):
           rev.is_current = False
           rev.status = "REPLACED"
           rev.replaced_at = now
   ```
   Followed by promoting `revision` (`revision.status = "ACTIVE"`, `revision.is_current = True`).

### 1.2 Status Checking Inspection in `src/pwd301/blueprints/instructor/routes.py`
In `rescan_course_file_route` (lines 725–739):
```python
if asset.status == "ACTIVE":
    flash(
        f"Tệp tin '{asset.display_name}' đã được quét an toàn và kích hoạt thành công!",
        "success",
    )
elif asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED":
    flash(
        f"Cảnh báo: Tệp tin '{asset.display_name}' bị phát hiện mã độc và đã bị cách ly!",
        "danger",
    )
else:
    flash(
        f"Đã kích hoạt quét lại '{asset.display_name}'. Trạng thái: {asset.status}.",
        "info",
    )
```
Inspection of `FileAsset.virus_scan_status` in `src/pwd301/models/file_import.py` (lines 275–296) confirms that when the effective revision has `status == "REJECTED"`, `virus_scan_status` evaluates to `"INFECTED"`. Thus, the alert message correctly triggers with category `"danger"`.

### 1.3 Asynchronous Job Enqueueing Inspection in `src/pwd301/services/file_service.py`
In `store_file_stream` (lines 581–589) and `add_file_revision` (lines 843–851):
```python
sess.flush()
from pwd301.services.background_job_service import enqueue_background_job

enqueue_background_job(
    job_type="FILE_SCAN",
    payload={"asset_id": asset.id, "user_id": actor.id},
    run_async=False,
    session=sess,
)

sess.commit()
```
Passing `run_async=False` prevents spawning uncoordinated background worker threads before `sess.commit()`, eliminating thread race conditions against active DB transactions and SQLite locking issues.

### 1.4 Static Analysis Execution Output
- `ruff check src/pwd301`:
  ```
  All checks passed!
  ```
- `ruff format --check src/pwd301`:
  ```
  85 files already formatted
  ```
- `mypy src/pwd301`:
  ```
  Success: no issues found in 85 source files
  ```

### 1.5 Automated Test Suite Execution Output
- `pytest tests/test_m1_challenger_stress.py tests/test_m1_file_access.py -v`:
  ```
  ============================= 29 passed in 8.00s ==============================
  ```
- Full file security & API regression suite:
  `pytest tests/test_m1_adversarial.py tests/test_files.py tests/security/test_quarantine_fail_closed.py tests/api/test_scan_api.py -v`:
  ```
  ============================= 50 passed in 14.48s =============================
  ```
- Total test coverage executed by Auditor: **79 / 79 tests passed** (100% pass rate).

---

## 2. Logic Chain

1. **Adherence to Integrity Mode (Development Mode)**:
   - `ORIGINAL_REQUEST.md` lines 8 and 42 specify `Integrity mode: development`.
   - In Development Mode, strict prohibitions include: (a) hardcoded test results, (b) dummy/facade implementations, (c) fabricated outputs.
   - Analysis of git diff across `file_service.py` and `instructor/routes.py` revealed zero hardcoded constants, zero mock outputs, and zero conditional bypasses.

2. **Genuine Revision Demotion Logic**:
   - The database schema enforces partial unique constraints:
     - `ux_file_revisions_active`: exactly one revision per asset can have `status='ACTIVE'`.
     - `uq_file_revisions_current`: exactly one revision per asset can have `is_current=1`.
   - By iterating over `asset.revisions` and setting `rev.is_current = False`, `rev.status = "REPLACED"`, and `rev.replaced_at = now` for all other revisions before activating `revision`, the logic genuinely satisfies both partial unique indexes at the ORM and relational database level.

3. **Genuine Route Status Checking**:
   - `FileAsset.status` is constrained to `('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')` and never stores `"REJECTED"`.
   - Worker it2 updated the flash condition to inspect `asset.virus_scan_status == "INFECTED" or asset.status == "REJECTED"`.
   - Because `FileAsset.virus_scan_status` dynamically inspects `rev_status == "REJECTED"`, this allows `rescan_course_file_route` to detect malware authentically and flash the warning banner.

4. **Empirical Independent Verification**:
   - Both unit, integration, adversarial, and stress tests were executed directly in the project environment.
   - All 79 tests passed cleanly without assertion errors, database integrity violations, or lock hangs.

---

## 3. Caveats

- No caveats. All changes are minimal, targeted, and fully verified against the source code, schema constraints, static analyzers, and test suite.

---

## 4. Conclusion

The changes implemented by Worker M1 it2 for Milestone 1 are authentic, well-structured, minimal, and fully compliant with project invariants:
- Zero hardcoded test values or bypass facades.
- Genuine multi-revision lifecycle state transitions.
- Fully verified via static linters (`ruff`, `mypy`) and automated tests (`pytest`).
- **Final Verdict**: **CLEAN**.

---

## 5. Verification Method

To independently reproduce the forensic verification:

1. **Verify Static Analysis**:
   ```powershell
   .venv\Scripts\ruff.exe check src/pwd301
   .venv\Scripts\ruff.exe format --check src/pwd301
   .venv\Scripts\mypy.exe src/pwd301
   ```

2. **Run Targeted Milestone 1 Challenger & File Access Tests**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_challenger_stress.py tests/test_m1_file_access.py -v
   ```

3. **Run Full Regression File Security Suite**:
   ```powershell
   .venv\Scripts\pytest.exe tests/test_m1_adversarial.py tests/test_files.py tests/security/test_quarantine_fail_closed.py tests/api/test_scan_api.py -v
   ```
