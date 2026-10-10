# Báo cáo triển khai và kiểm chứng VPS — TASK-088

**Trạng thái: NOT_DEPLOY_READY.** Báo cáo ngày 10/10/2026 (UTC+7). Đây là bản triển khai đang kiểm chứng, không phải nghiệm thu production. TASK-089/090 đang thay đổi cùng workspace; theo chỉ đạo của chủ dự án, chờ agent đó hoàn tất rồi kiểm chứng bản tích hợp. Không reset, ghi đè hoặc sửa thay phần việc của agent đó.

## A. Phạm vi và nguồn sự thật

Đã triển khai phần tiến độ backend, player hiện có, offload tài liệu, scanner, artifact production, staging riêng và recovery. Chưa đổi DNS, mở production, chuyển/xóa tài liệu thật hoặc push Git.

Nguồn đối chiếu: `AGENTS.md`, `README.md`, `tasks/CURRENT.md`, System Specification (start-here, business catalog, lesson/progress và invariants), Database Architecture canonical, intent bản quyền và kế hoạch `docs/superpowers/plans/2026-10-09-vps-readiness.md`. Ngoại lệ được chủ dự án phê duyệt: YouTube giữ nhận diện theo API chính thức, không che iframe; watermark nội dung chỉ áp dụng HLS nội bộ; B2 không được tuyên bố miễn phí tải vô hạn; tài nguyên theo cấu hình VPS 8 GB.

Baseline HEAD: `6ebbaaa6d5e43160020c8efb6fec9f245cf4ea6e`, nhánh `codex/vps-readiness`. Worktree hiện có thay đổi TASK-088/089/090 chưa commit; tag candidate không phải bằng chứng image chỉ chứa code của HEAD này.

## B. Quyết định tái sử dụng

KEEP: Flask/session/JWT envelope, SQL Server/Alembic, lesson service, custom player, VideoArmor cho HLS, scanner, storage adapter, background jobs, backup/audit và guard restore. Không thêm Redis, queue framework, microservice hoặc thư viện player.

SIMPLIFY NOW: một Promise loader YouTube, lifecycle controller chung, storage backend `local|s3`, tách quyền tải khỏi physical path, health fail-closed. REMOVE NOW: overlay che YouTube, secret DRM mặc định, fallback scanner trả sạch khi vượt giới hạn, metadata UI giả và demo credentials production.

## C. Thay đổi theo nhóm file

| File/nhóm | Kết quả triển khai |
|---|---|
| `models/playback.py`, `services/playback_service.py`, lesson service và Web/JWT lesson routes | Phiên/receipt bền vững, sequence/retry, khóa SQL Server, một phiên cộng thời gian, trusted duration, frontier/resume; heartbeat đến chậm chỉ cộng phần chuyển động hợp lệ và thời gian server |
| `frontend/assets/js/views/student.js`, `api.js`, `components/video-armor.js`, `ui.js` | Player chính thức, controls ngoài iframe, lifecycle, tốc độ thực, pause/error/visibility heartbeat, tải tài liệu bằng ticket; giữ phần TASK-090 của agent khác |
| `services/youtube_validator_service.py`, `background_job_service.py` | Host/link chuẩn hóa, Data API backend, retry 429/5xx; lịch kiểm tra video khi có key, thông báo không trùng; EMAIL dedupe terminal và worker heartbeat |
| `services/storage_adapter.py`, `file_service.py`, `storage_maintenance_service.py`, `models/file_import.py`, file routes | S3 fail-closed, size/SHA streaming, activation sau xác minh, local cleanup sau commit, ticket 60 giây kiểm tra quyền/scan/revision; staging migration checkpoint |
| `services/scanner_service.py`, `video_drm_service.py` | Vượt giới hạn scanner trả ERROR; HLS khóa xuyên process, tạo tạm và publish playlist cuối; timeout bounded, secret fail-closed |
| `backup_archive_service.py`, `backup_cipher.py`, operations service, backup scripts | Backup Express checksum/manifest; cloud archive mã hóa, xác minh stream/receipt và retention; restore drill DB riêng |
| `Dockerfile`, `.dockerignore`, `requirements.txt`, `requirements.lock`, `deploy/*`, `.env.production.example` | Dependency/image pin, UID 10001, source không bind mount, private network, Caddy, caps/log rotation, release một lần, backup timer mẫu |
| `config.py`, app init, auth/core routes, operations service | Production secrets/cookies, scanner/cache budgets, runtime-config không lộ secret, public readiness chỉ metadata an toàn, telemetry OS/container thật |
| `frontend/assets/js/views/auth.js`, helper VPS trong admin/student | Không render demo credentials mặc định/production; TLS badge theo protocol; worker/backup/dashboard phản ánh dữ liệu thực |
| 4 migration `b2storage…`, `playback…`, `receiptretention…`, `blobdefaultrepair…` | Metadata storage, 3 bảng playback, receipt index, repair default/FK rollback; head `blobdefaultrepair20261009` |
| Canonical database docs/DDL, spec/intent/AGENTS/README | Đồng bộ kiến trúc đã phê duyệt, 76 bảng canonical; không tạo DDL thứ hai |
| `scripts/verify.*`, `test_database_guard.py`, preflight/seed/scanner/restore scripts, tests liên quan | Destructive fixture yêu cầu disposable; verifier Linux không PASS khi thiếu Node; regression, concurrency và operational probes |

Diff cuối và các file dùng chung phải review lại sau TASK-090. Danh sách OCR scope trong `CODE_REVIEW.md` là snapshot, không phải release approval.

## D. Xóa và đơn giản hóa

Loại lớp che/redirect shield YouTube và tham số không còn tác dụng; không phủ watermark lên iframe. Loại scanner path fallback và heuristic PASS cho tệp chưa thực sự quét. Không seed demo production hoặc dùng secret startup mặc định. Không dùng hostname/RAM máy phát triển làm telemetry production. Không đánh đồng viewed-most với hoàn thành lesson.

## E. Debt và điểm cần kiểm chứng tiếp

| Mục | Trigger / owner / risk / safeguard / điểm review |
|---|---|
| HLS tạo đồng bộ lần đầu | Trigger: tải HLS nội bộ đồng thời hoặc video dài; owner: TASK-088; risk: latency/temporary files sau SIGKILL; guard: per-output process lock, timeout và atomic publication; review trước G3/G7, chưa có crash/soak dài |
| Backup diagnostic/manual retention | Trigger: đĩa tăng; owner: vận hành; risk: giữ bằng chứng làm đầy đĩa; guard: budget/alert, không tự xóa bản recovery duy nhất; review trong soak và runbook VPS |
| Provider và workload thật | Trigger: nhận staging credentials/host; owner: triển khai; risk: mock không đại diện quota/egress/playback; guard: cổng G3/G4/G6/G7 bị chặn; kiểm chứng trước release |

## F. Kiểm chứng đã chạy

Evidence nằm trong `.superpowers/vps-readiness/` được Git ignore. Không đưa env, token hoặc URL ký vào báo cáo.

| Kiểm chứng | Kết quả / giới hạn |
|---|---|
| Backend toàn bộ, `pytest-current-all.log` | Snapshot trước các sửa cuối: 1726 passed, 3 failed, 5 skipped, 23 phút. Health failure đã sửa và chạy test riêng; 2 lỗi PDF/review thuộc bản tích hợp đang thay đổi. Không tính toàn suite pass |
| VPS scoped, `vps-scoped-final.log` | 127 passed, không skipped; chạy trước một số hardening cuối |
| Public readiness/API, `readiness-api-final.log` | 28 passed; public body không lộ path/error dependency chi tiết |
| Express thật, `sql-final-all.log` | 26 passed, 67 giây: migration base round-trip, FK/trigger/ROWVERSION, playback worker race và dedupe. DB disposable riêng |
| Heartbeat delayed retry | 3 regression mới fail đúng 19 thay vì 10 giây; sau sửa unit module 23 passed. Express rerun `playback-delayed-sql.log`: 24 passed, 66,96 giây, gồm race hai worker |
| Hardening cuối | `root-latest.log`: 41 passed, 9,90 giây; worker healthcheck 5 tests fail trước sửa rồi pass, kiểm tra heartbeat thay HTTP Web kế thừa |
| HLS/storage, `hls-storage-final.log` | 27 passed; `hls-live-cross-process.log`: hai process cùng generation thành công, key 16 byte, giải mã FFmpeg thật. Chưa crash/soak |
| Scanner thật, `scanner-live-final.log` | ClamAV 1.4.3: clean PASS, EICAR FAIL, unavailable ERROR, oversized ERROR; unit regression 17 passed |
| YouTube jobs, `youtube-jobs-final.log` | 4 passed; test mô phỏng 429/5xx/network retry, không chứng minh provider thật |
| Backup/restore, `restore-drill.log` | Express backup 10.735.616 byte, checksum/manifest và VERIFYONLY; restore DB mới, DBCC CHECKDB đạt; đối chiếu 20 courses/53 users/20 lessons/50 enrollments. Chưa cloud encryption roundtrip thật |
| Frontend toàn bộ, `frontend-latest.log` | Snapshot 150/154 pass, 4 fail. Auth failure đã sửa; own rerun 34 passed (`frontend-own-final.log`). 3 course-review failures chờ TASK-090 |
| Lint/types | Scoped VPS lint đạt. Full lint và mypy còn lỗi trong file TASK-089/090; không ghi pass hoặc sửa thay agent đó |
| Repository contract | Fresh repo_check PASS, canonical 76 tables, fences/contract đạt |
| Artifact | Build Docker Linux độc lập thành công; container UID 10001, DB Express/ClamAV/proxy private, worker sau dedupe fix không restart. Image candidate chứa dirty worktree |
| TLS/browser | Strict TLS client dùng CA staging riêng, không bypass certificate. IAB HTTP smoke đăng nhập không có demo panel và badge local; HTTP smoke không thay browser HTTPS/đa trình duyệt |
| Readiness runtime | DB/scanner/worker healthy nhưng mail queue suy giảm vì không có SMTP; trả 503, không xóa job để tạo PASS |
| Systemd/preflight | Systemd verifier chưa có; chưa cài timer VPS. Windows preflight không đạt Linux/provider config. Docker host 16 GB không tương đương ngân sách host 8 GB |

### Môi trường cô lập

Compose project `pwd301-readiness-20261009`; DB `pwd301_test_readiness`, regression DB `pwd301_test_regression`; volumes riêng. Seed 20 khóa học/50 học viên, chưa có video thật. Loopback SQL 15439, HTTPS 18443, HTTP smoke 18080. Không chạy destructive fixture lên DB hiện tại.

Image candidate lần build cuối: `sha256:a6db42f6b264c8dd762b50968f3a3d02d57f2662f392bfbc040b06f67d25a6aa`, tag tạm `pwd301:readiness-6ebbaaa`; không phải release tag. `tls-current.log` lúc 17:24 UTC ngày 09/10: TLS xác minh CA đạt; `/health/deep` 503 do mail queue DEGRADED; DB/ClamAV/worker healthy. Docker Worker healthcheck healthy, restart 0. `/auth/runtime-config` production trả demo false. Storage đang local, nên cloud_storage HEALTHY trong response này không chứng minh B2.

### Cổng nghiệm thu

| Cổng | Trạng thái | Phần còn thiếu |
|---|---|---|
| G1 Mã | PARTIAL | TASK-090 hoàn tất; full verifier, review diff và smoke thi bản tích hợp |
| G2 Database | PARTIAL | Express core đạt; chạy lại migration/transaction trên artifact tích hợp cuối |
| G3 Video | PARTIAL/BLOCKED | YouTube API key/video thật, Chrome/Edge/Firefox/mobile, internal HLS crash/load |
| G4 Storage | BLOCKED | B2 private staging key/bucket; upload/download/SHA/ticket expiry và migration thật |
| G5 Artifact | PARTIAL | Linux sạch phù hợp VPS 8 GB, secrets/SMTP hợp lệ, readiness HEALTHY, artifact cuối bất biến |
| G6 Recovery | PARTIAL | Local Express drill đạt; cloud encryption/decrypt/restore và timer VPS chưa chạy |
| G7 Tải | NOT RUN | 50 phiên 60 phút + soak 4 giờ, tài liệu/video/provider thật, p95/error/RAM/đĩa |
| G8 Bàn giao | PARTIAL | Có compose/env/migration/tools/runbook/report; cần evidence G1–G7 và release image cuối |

**Không cổng chưa chạy, skipped hoặc blocked nào được tính pass.**

## G. Bước tiếp theo

1. Chờ TASK-090 hoàn tất theo chỉ đạo; chạy full frontend/backend/lint/format/typecheck và review bản tích hợp.
2. Nhập B2 tài liệu + bucket/key backup riêng, YouTube key/video staging và SMTP vào môi trường bí mật, không chat/commit. Không mượn credentials production hoặc chuyển tài liệu thật.
3. Chạy provider E2E, cloud recovery, browser matrix và workload đã chốt trên môi trường host phù hợp 8 GB; lưu output/mốc thời gian.
4. Chỉ sau G1–G8 đạt mới pin/tag release cuối và ghi DEPLOY_READY. Production là đợt riêng có quyền triển khai.
