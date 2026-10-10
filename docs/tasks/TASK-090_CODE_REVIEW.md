# TASK-090 — Open Code Review coverage

Review date: 10/10/2026. Mode: **OCR delegate** (CLI deterministic selection/rules; host agent reviews code). This is not an external OCR LLM run or a whole TASK-088 release audit.

## Execution and scope

- Windows OCR 1.12.12 launcher failed and its binary was blocked by Application Control. Protection was not bypassed.
- Same package/version ran in `node:22.14.0-bookworm`, workspace mounted read-only. `ocr delegate preview --format json` and `ocr delegate rule --format json` exited 0.
- Evidence: `.superpowers/task-090/ocr-release-preview.json`, `ocr-final-rules.json`; earlier RED/GREEN logs remain in the same evidence directory.
- Preview: 152 dirty files, 68 reviewable, 84 excluded by CLI rules. Git 2.39.5 compatibility warning is disclosed; local Git workspace/status/diff checks corroborate scope.
- Applied Python/JavaScript rule groups: null/boundary handling, error semantics, resource cleanup, object authorization, untrusted data, SQL concurrency/transaction ownership, async lifecycle and disclosure.
- Review covers TASK-090 delta and required downstream call paths. Preexisting TASK-088 files have an explicit skip disposition below; regression tests do not constitute a source review of their entire diff.

## Confirmed findings and disposition

| Finding | Source location in current file | Root cause / correction | Evidence |
|---|---|---|---|
| Hidden-review crash and answer disclosure | attempt_service.py:2985 and result serializer | Explicit visibility gate, NEVER empty list, selected-only restricted feedback | assessment RED/GREEN, four policy API tests, browser policies |
| Invalid applied SQL policy CHECK | new reviewpolicy migration, downgrade:23 | Model policy was absent from applied schema; new migration, guarded rollback, canonical DDL | sql-policy-red.log, SQL migration/review policy and downgrade tests |
| Premature commits and duplicate lifecycle audit | course_service.py:987; lesson_service.py:2365/2383 | Caller-owned transaction, locked refreshed course/request and mandatory audit | course-race RED logs, concurrent live SQL tests |
| Reviewer stream authorization/header/version gaps | api_files/routes.py download/stream handler | Owner/course-review restriction before serving, positive revision, Range/headers | video-red.log, persisted scan and SQL byte tests |
| PDF truncation/missing-data/pagination | result_pdf_service.py; instructor/admin PDF routes | Escape/Unicode/row splits; preserve complete data and pending status; all result pages | pdf RED/GREEN, actual six-page inspection, 101-row export test |
| Document title XSS / executable URL | admin.js:1970 | Escape title and URL, reject executable URLs; PDF native frame receives verified blob only | document-title-red.log, document-title-green.log, PDF HTML/auth rejection test |
| Malformed quiz crash | admin.js:1858/1875/1902 | Filter non-object questions, safely refuse malformed nested answer metadata | quiz-malformed-red.log, quiz-malformed-green.log |
| Empty queue during route staging | admin.js:1464 and governance switch | Global ID lookup saw previous route; container-scoped query and await render | queue-staging-red.log/green.log; actual approval/rejection refresh |
| False resource removal diff | admin/routes.py:1452 | Absent field was treated as empty list; inherit unchanged resources and apply explicit attach/detach proposal | resource-diff RED/GREEN; browser title-only diff is one change |
| Malformed saved-resource success/crash | admin/routes.py:1434 | Shared JSON object/changes-list validation across queue/diff/review; no exception-to-success fallback | resource-shape RED/GREEN; current live SQL coverage |

These findings were fixed and regression-tested. No unresolved blocking code finding is asserted from speculative inputs. The native PDF iframe browser gate was completed in connected Edge on 10/10/2026: the project owner directly confirmed PDF display and scrolling to page 2 in the application's modal. Browser-tool screenshots show an empty region even for a standalone PDF without application CSP; they are not claimed as visual proof. This tool limitation is tracked separately from code-review findings.

## UI detector triage

Impeccable context and detector actually ran. Detector exit 2: 54 warnings across entire incumbent files. Two warnings within student result review (lines 6511/6520 at scan time) matched sanitizer regular expressions `<img[^>` rather than rendered images. Other warnings were outside the TASK-090 preview/result edits. They are not represented as a passing detector or silently fixed by a broad redesign. Later scoped fixes were checked manually against craft floor; detector was not looped.

## Additional manual review

Test files excluded by CLI were reviewed manually for meaningful assertions and safe fixtures: policy, video, approval, SQL concurrency/downgrade, ROWVERSION, PDF formatting/pagination, frontend preview/read-only/security and route staging. No xfail/skip was added to suppress a product failure. SQL-only tests have explicit environment skips in the SQLite suite and separately execute on the verified disposable MSSQL database.

Approved simplification classifications: existing auth/storage/playback/security contracts KEEP; premature commits/silent success/raw fallback REMOVE NOW; shared preview/payload parsing and container DOM SIMPLIFY NOW. Provider/load/cloud recovery remain TASK-088 debt with NOT_DEPLOY_READY safeguard.

## Per-reviewable-file disposition

The following checklist uses each `(path, status)` returned by OCR. `Reviewed TASK-090` means the task delta and its relevant callers were reviewed; mixed preexisting TASK-088 delta remains owned by its release audit. `Skipped` is an explicit scope exclusion, not a passing review.

| Path | OCR status | Disposition |
|---|---|---|
| `.dockerignore` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `.gitignore` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `Dockerfile` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/004_assessment.sql` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/006_files_import.sql` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/api.js` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/components/video-armor.js` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/router.js` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/ui.js` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/views/admin.js` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `frontend/assets/js/views/auth.js` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `frontend/assets/js/views/instructor-exams.js` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `frontend/assets/js/views/instructor.js` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `frontend/assets/js/views/student.js` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `pyproject.toml` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/repo_check.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/verify.ps1` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/verify.sh` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/__init__.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/blueprints/admin/routes.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/blueprints/api_files/routes.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/blueprints/api_lessons/routes.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/blueprints/auth/routes.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/blueprints/core/routes.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/blueprints/instructor/routes.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/blueprints/student/routes.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/config.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/models/__init__.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/models/assessment.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/models/file_import.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/seeds/baseline.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/assessment_service.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/services/attempt_service.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/services/authorization_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/background_job_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/course_service.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/services/file_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/lesson_service.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/services/operations_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/result_pdf_service.py` | modified | Reviewed TASK-090; mixed baseline excluded from release claim |
| `src/pwd301/services/scanner_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/storage_adapter.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/video_drm_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/youtube_validator_service.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `tests/conftest.py` | modified | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `deploy/Caddyfile` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `deploy/compose.production.yml` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `deploy/compose.staging.yml` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `migrations/versions/b2storage20261009_blob_storage_location.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `migrations/versions/blobdefaultrepair20261009_sqlserver_blob_default.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `migrations/versions/playback20261009_durable_playback.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `migrations/versions/receiptretention20261009_playback_cleanup_index.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `migrations/versions/reviewpolicy20261010_restricted_assessment_review.py` | added | Reviewed TASK-090; mixed baseline excluded from release claim |
| `scripts/backup_archive.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/bootstrap_release.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/deploy_preflight.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/deployment_urls.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/restore_drill.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/scanner_probe.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/seed_readiness_staging.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/storage_maintenance.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `scripts/worker_healthcheck.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/models/playback.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/backup_archive_service.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/backup_cipher.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/playback_service.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
| `src/pwd301/services/storage_maintenance_service.py` | added | Skipped: preexisting TASK-088/configuration delta; preserved, separate VPS review owns it |
