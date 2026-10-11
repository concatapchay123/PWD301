# Pham vi review ban VPS

OCR 1.12.12 delegate preview/rule da chay tren Linux. CLI chi chon file/resolve rules; ket luan review do agent lap. Git 2.39.5 trong container co canh bao thap hon 2.41; khong coi day la cong OCR tu dong da pass.

Danh sach nay ghi snapshot cua preview, khong chung nhan cac thay doi TASK-089/090 dang dien ra. Khi agent kia hoan tat phai review diff cuoi va chay lai verifier.

| File | Trang thai | Pham vi |
|---|---|---|
| `.dockerignore` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `.gitignore` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `Dockerfile` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_course_learning.sql` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/006_files_import.sql` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `frontend/assets/js/api.js` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `frontend/assets/js/components/video-armor.js` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `frontend/assets/js/router.js` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `frontend/assets/js/ui.js` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `frontend/assets/js/views/admin.js` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `frontend/assets/js/views/auth.js` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `frontend/assets/js/views/instructor-exams.js` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `frontend/assets/js/views/instructor.js` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `frontend/assets/js/views/student.js` | PARTIAL | Da review playback/VPS; phan preview TASK-090 cho tich hop |
| `pyproject.toml` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/verify.ps1` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/verify.sh` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/__init__.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/blueprints/admin/routes.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/blueprints/api_files/routes.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/blueprints/api_lessons/routes.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/blueprints/auth/routes.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/blueprints/core/routes.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/blueprints/instructor/routes.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/blueprints/student/routes.py` | PARTIAL | Da review playback/VPS; phan preview TASK-090 cho tich hop |
| `src/pwd301/config.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/models/__init__.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/models/assessment.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/models/file_import.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/seeds/baseline.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/assessment_service.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/services/attempt_service.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/services/authorization_service.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/services/background_job_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/course_service.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/services/file_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/lesson_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/operations_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/result_pdf_service.py` | PENDING | TASK-089/090 dang sua; cho ban tich hop |
| `src/pwd301/services/scanner_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/storage_adapter.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/video_drm_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/youtube_validator_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `tests/conftest.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `deploy/Caddyfile` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `deploy/compose.production.yml` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `deploy/compose.staging.yml` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `migrations/versions/b2storage20261009_blob_storage_location.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `migrations/versions/blobdefaultrepair20261009_sqlserver_blob_default.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `migrations/versions/playback20261009_durable_playback.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `migrations/versions/receiptretention20261009_playback_cleanup_index.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/backup_archive.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/bootstrap_release.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/deploy_preflight.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/deployment_urls.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/restore_drill.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/scanner_probe.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/seed_readiness_staging.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `scripts/storage_maintenance.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/models/playback.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/backup_archive_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/backup_cipher.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/playback_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |
| `src/pwd301/services/storage_maintenance_service.py` | SCOPED REVIEW | Phan VPS da doc/review boi root va agent domain; chua la release approval |

## Finding da khac phuc trong review/kiem chung

- Raw video ticket/download bypass: chan hoc vien tai service chung.
- Heartbeat terminal/rate/frontier/sequence: regression va race tren Express.
- Readiness DEPENDENCY DOWN bi tong hop HEALTHY: fail-closed.
- Scanner vuot gioi han tra PASS: ERROR, real ClamAV probe da kiem chung.
- EMAIL dedupe key cua job da ket thuc: giai phong lease, giu lich su/UUID; regression SQLite va Express.
- Worker cleanup co handler nhung thieu lich: durable CLEANUP luc startup va moi 30 phut.
- Backup volume SQL UID khong ghi duoc: permissions init, backup/restore drill thuc te.
- Migration downgrade default/FK: revision repair moi; Express round-trip da chay.
- Development telemetry ghi de RAM production: dung psutil/cgroup, regression.
- Signing DRM ngoai context co default secret: fail-closed.
- Auth demo va TLS badge: demo an theo runtime flag; badge theo protocol.

## Finding con mo

- HLS noi bo van transcode dong bo khi playlist chua co. Da co process lock, atomic publication va timeout; hai process + FFmpeg decrypt thuc te da dat. Crash/SIGKILL cleanup va long-transcode/soak van chua kiem chung truoc release.
- Heartbeat den cham/stall: regression da tai hien cong 19 giay cho 10 giay chuyen dong; da gioi han credit theo wall-clock va chuyen dong hop le, unit 23 passed; SQL rerun 24 passed gom race hai worker.
- B2 that, YouTube metadata/playback that va workload dai chua chay vi thieu moi truong/key.
- TASK-089/090 dang thay doi va con frontend/lint/type errors; khong tinh la baseline de bo qua gate.
