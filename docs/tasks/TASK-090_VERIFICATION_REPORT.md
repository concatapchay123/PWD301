# TASK-090 — Báo cáo triển khai và kiểm chứng

**Status: COMPLETED — native PDF iframe đã được chủ dự án kiểm chứng trực tiếp trong Edge.** Full verifier hiện tại PASS. Ngày kiểm chứng: 10/10/2026 (UTC+7). Branch `codex/vps-readiness`, HEAD đầu phiên và cuối phiên `6ebbaaa6d5e43160020c8efb6fec9f245cf4ea6e`. Không commit/push/deploy, đổi DNS hoặc sửa dữ liệu thật. Dirty changes TASK-088/089 được giữ lại. Baseline và evidence: `.superpowers/task-090/` (ignored). Không công bố tệp thông tin kết nối.

Goal resumed audit: Edge Profile 1 đã kết nối qua extension. Chủ dự án xác nhận PDF control hiển thị bình thường, PDF trong modal của PWD301 hiển thị và cuộn được đến trang 2. Cổng native PDF đạt bằng kiểm chứng trực tiếp của chủ dự án; ảnh/AX tự động không đọc được native viewer. Không thay mã sản phẩm hoặc nới quyền/CSP để xử lý giới hạn công cụ.

## A. Scope và nguồn sự thật

Thực hiện handoff TASK-090 đầy đủ: assessment review, PDF cá nhân/lớp, preview instructor/admin, reviewer video streaming và course/change-request approval. Chỉ đạo thực hiện của chủ dự án thay thế wording chờ approval cũ trong hai kế hoạch ngày 09/10.

Đã đọc AGENTS local/global, CURRENT TASK-090/089, task template, README liên quan; System Specification start-here, business rule catalog, invariants, assessment/attempt/grading/course/lesson/file authorization và frontend flows; canonical Database Architecture, DDL và concurrency/migration contracts; hai kế hoạch assessment/admin ngày 09/10; VPS_READINESS_REPORT và CODE_REVIEW. Không tạo schema thứ hai hoặc phục hồi legacy frontend.

| Nhóm | Ban đầu đã tái hiện | Trạng thái hiện tại | Evidence |
|---|---|---|---|
| A Review | NEVER dùng None; disclosure/UI cần regression | VERIFIED API/SQL/browser, giữ historical snapshot | Policy tests; năm policy trong browser |
| B PDF | Builder có sẵn nhưng layout/long/missing/Unicode chưa chứng minh | VERIFIED PDF thật và render 6 trang | PDF tests, geometry, ảnh từng trang, PDF qua UI |
| C Preview | Một phần renderer; 3 frontend regressions | VERIFIED tree/video/Markdown/quiz/read-only/responsive; native iframe PDF đạt bằng xác nhận trực tiếp của chủ dự án trong Edge | Browser desktop/mobile, bốn quiz modes; DB progress/playback = 0 |
| D Stream | Alias thiếu quyền/revision/full headers | VERIFIED Range/auth/scan và phát video thực | API/SQL security tests; browser video readyState 4, thời gian tăng |
| E Approval | Transaction/audit/retry/concurrency chưa chứng minh | VERIFIED API/SQL/browser; sửa stale DOM queue và resource diff | SQL 46 passed; approval/rejection UI; audit/status DB proof |
| TASK-088 | Historical evidence không phải release proof | Regression PASS; provider/load/cloud recovery vẫn thuộc TASK-088 | Full verifier, SQL playback/migration/grade/revision |

## B. Reuse decisions

KEEP Flask auth/session/JWT/CSRF/envelopes, object authorization, scan/materialization, Werkzeug conditional delivery, ReportLab Unicode fonts, existing course changesets, resource services, mandatory audit và SQL row locks. REUSE một renderer read-only cho instructor/admin và một saved-payload loader cho queue/diff/review. Nhu cầu loader được chứng minh bằng invalid-payload regression. Không thêm player/queue/PDF framework hoặc hạ tầng mới.

Native PDF chỉ nhúng blob sau HTTP authorization, Content-Type application/pdf và magic %PDF-; không điều hướng iframe không sandbox tới URL tùy ý. Text/HTML vẫn sandbox. Blob URL thu hồi khi đóng. Các transaction có caller session do caller commit.

## C. Per-file changes

Một phần dirty diff đã tồn tại trước phiên; không nhận toàn bộ diff làm việc mới.

| File | Hoàn thiện/kiểm chứng TASK-090 trong phiên |
|---|---|
| services/attempt_service.py | NEVER list rỗng; authoritative answers_visible; restricted disclosure; historical choice fallback |
| views/student.js | Inline đúng/sai/thiếu; hidden questions an toàn; read-only quiz/progress guard; bỏ raw student video fallback |
| views/instructor-exams.js | Giữ AFTER_CLOSE/AFTER_ALL_ATTEMPTS khi sửa cấu hình |
| services/result_pdf_service.py | Unicode bắt buộc, escape, không truncate, split rows/pagination, score canonical, missing data không bịa kết quả |
| blueprints/student/routes.py | PDF có tên course và time limit thật, readable snapshot answers |
| blueprints/instructor/routes.py | Toàn bộ gradebook pages, pending/released status và thống kê; không fallback candidate UUID |
| blueprints/admin/routes.py | Gradebook pages/status; chapter/public file handles; shared payload validation; accurate resource diff; business errors; required audit/transaction; missing DETACH không duyệt |
| views/admin.js | Shared tree/workspace; media cleanup; bốn quiz modes cục bộ; malformed metadata guard; escaped document title/URL; verified PDF blob lifecycle; scoped/awaited route-staging queue |
| views/instructor.js | Shared preview, current editor content, cleanup |
| blueprints/api_files/routes.py | Reviewer owner/course-review quyền trước phục vụ; inline/private/no-store/nosniff/Accept-Ranges; version/Range validation |
| services/lesson_service.py | Course/request lock + refresh; mandatory approval/rejection audit; caller-owned session không commit sớm |
| services/course_service.py | Status row lock/refresh; retry một audit; caller transaction |
| src/pwd301/__init__.py | CSP frame blob: cho PDF bytes đã xác minh; giữ auth/provider/secret guards |
| migrations/versions/reviewpolicy20261010_restricted_assessment_review.py | Migration mới CHECK CORRECT_WRONG_ONLY; downgrade guard khi còn policy này |
| canonical sql/004_assessment.sql và assessment dictionary | Đồng bộ enum với behavior/model; không sửa applied migration |
| System Specification assessment/instructor/admin flows | Policy/PDF/read-only tree/approval contracts |
| tests/api/test_assessment_review_policy.py | Policy disclosure/NEVER |
| tests/api/test_video_preview_stream.py | Real bytes, persisted scan, Range/auth/version/scan denial |
| tests/api/test_admin_change_requests_review.py | Payload shape, object ownership, chapter/public handles, DETACH, audit/retry/rollback |
| tests/integration/test_approval_sqlserver.py | Concurrent reviewers/one audit; downgrade guard giữ data/head |
| tests/api/test_course_api.py | ROWVERSION thật trên MSSQL, không UPDATE timestamp giả |
| tests/api/test_student_backend_completion.py | 10 / 10 theo canonical formatting, PDF thực được kiểm chứng |
| tests/test_result_pdf_formatting.py; test_admin_diff_and_gradebook_pdf.py | Unicode/long/missing/score/PDF và partial resource diff |
| tests/frontend/assessment_review_policy.test.js; student_preview_readonly.test.js; reviewer_course_preview.test.js; course_review_regression.test.js | Policy UI, preview/no writes, quiz/document security/lifecycle, stale route DOM |

Đường dẫn services/blueprints thuộc `src/pwd301/`; views thuộc `frontend/assets/js/views/`. File list này chỉ mô tả task delta trên các file dùng chung, không chứng nhận toàn bộ TASK-088 source diff.

## D. Deletion/simplification

REMOVE NOW: detached answer cluster, raw student-video fallback, text truncation/UUID academic fallback, premature caller-session commits, success giả khi diff lỗi, missing DETACH approval. SIMPLIFY NOW: shared preview/payload validation, scoped queue DOM. KEEP: lease/autosave/submit, SQL locks/ROWVERSION, HLS, durable playback, storage/scanner fail-closed, production guards/telemetry. Không reset/stash/clean toàn worktree.

## E. Debt và giới hạn

| Mục | Trigger/owner | Risk/safeguard | Review point |
|---|---|---|---|
| Native viewer automation | Browser tooling owner | Edge hiển thị PDF cho người dùng nhưng ảnh/AX của công cụ trống; giữ evidence riêng và không gọi ảnh đó là proof | Khi công cụ hỗ trợ native PDF |
| Policy downgrade | Authorized policy owner cần downgrade | Không tự đổi dữ liệu; guard giữ head/data và dừng exit 1 | Trước downgrade |
| Provider/readiness TASK-088 | Agent VPS/release owner | B2/YouTube thật, cloud recovery, tải 8 GB chưa được chứng nhận. NOT_DEPLOY_READY | Trước release |
| Legacy UI warnings | UI owner sửa vùng tương ứng | Không tự redesign vùng ngoài task; review triage riêng | Khi vùng đó được chỉnh sửa |

## F. Verification thực tế

Full verifier: disposable memory SQLite (`TEST_DATABASE_URL=sqlite:///:memory:`, acknowledgment 1). SQL: database riêng `pwd301_test_task090`; wrapper xác minh DB_NAME, disposable guard, other sessions = 0 trước mỗi lượt. Browser: `pwd301_test_browser090.sqlite`, localhost 15090, synthetic data; scan PASS fixture không chứng minh ClamAV thật. Không chạy destructive fixture trên development/production DB.

Lệnh aggregate: `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1`. Bypass chỉ trong process, không thay policy hệ thống. PowerShell 5 có quoting lỗi; verifier dùng PowerShell 7.

| Gate | Kết quả thật | Evidence trong .superpowers/task-090/ |
|---|---|---|
| Baseline Ruff/mypy | 12/8 errors được tái hiện | lint-before.log, mypy-before.log |
| Ruff/format hiện tại | PASS; 323 files formatted | Terminal và verifier mới |
| Verifier snapshot trước sửa cuối | Exit 0; 1791 backend passed, 7 skipped; full frontend snapshot pass | full-verifier-final.log |
| Verifier source mới nhất | Exit 0, PASS; 1796 backend passed, 8 SQL-only skipped; 1023.65 s | full-verifier-release.log |
| Full frontend source mới nhất | 177 passed, 0 failed, 0 skipped | full-verifier-release.log |
| Verifier obsolete bị hủy khi source đổi | INTERRUPTED, không tính pass | full-verifier-integrated.log |
| SQL policy/approval/course/video hiện tại | 46 passed, 160.39 s, không skipped | sql-release.log |
| SQL migration/playback/grade/revision/concurrency | 7 passed, 16.56 s | sql-all-gates-final.log |
| Downgrade giữ restricted row/head | 1 passed; cũng nằm trong SQL 46 hiện tại | sql-downgrade-guard.log |
| CSP/security | 37 passed, 19.10 s | pdf-csp-security.log |
| Resource diff/shape | 16 passed, 11.66 s sau RED | resource-diff-red.log, resource-shape-red.log, resource-shape-green.log |
| Frontend queue | 9 passed sau RED | queue-staging-red.log, queue-staging-green.log |
| Frontend preview/quiz/security | 11 passed sau RED | tree-icons-green.log; document-title/quiz-malformed RED logs |
| git diff --check | Exit 0; CRLF warnings không phải whitespace errors | Terminal output |

Không cộng các lượt overlap thành tổng giả. SQL-only skipped không tính pass; được chạy riêng trên MSSQL. SQLite không chứng minh locking/migration.

Browser student: IMMEDIATE có đúng/sai/thiếu/explanation; restricted không missed/explanation; NEVER/blocked policies không crash. Chờ đúng result ID trước screenshot. Instructor/admin: tree, instant switching, Markdown, bốn quiz types; real video duration 2 s, readyState 4, paused false và thời gian tăng; mobile 390 px không horizontal overflow, desktop 1366 px. Approval/rejection thật qua UI: initial APPROVED/DRAFT, request APPROVED/REJECTED; queue/badge refresh từ backend sau quyết định, không F5.

Computed UI metrics ở preview cuối: button padding 8px 16px; chữ phụ rgb(158,157,153) trên rgb(24,24,27) đạt contrast 6.53:1; tree labels rgb(232,230,223) trên rgb(32,32,32) đạt 13.05:1. Evidence screenshot: browser-preview-final.png. Không dùng screenshot bị crop ngang để chứng minh bố cục desktop.

DB proof sau browser: lesson_progress = 0; playback_sessions = 0; các audit COURSE_APPROVED, COURSE_REJECTED, COURSE_CHANGE_APPROVED, COURSE_CHANGE_REJECTED tồn tại. Extra courses/lessons do fixture chủ động tạo, không do preview. Evidence: browser-db-proof-final.log và browser-*.png.

PDF current builder: attempt long 2 trang, gradebook long 2 trang, hai missing cases 1 trang mỗi loại. Đã xem trực quan cả 6 trang; outside_margins = []; tiếng Việt, phần kết text dài, repeated table header được giữ. PDF tải thật qua UI và render: tên course/assessment đọc được, selected choice content, 0 / 10, Có giám sát nâng cao, Thành phố Hồ Chí Minh. Fixture threshold 0 giải thích kết quả đạt ở điểm 0, không phải rule sửa trong PDF. Evidence: pdf-geometry.json, pdf-*.pdf/png, browser-student-result.pdf/png.

Native iframe PDF — VERIFIED_MANUAL_OWNER, 10/10/2026: Edge Profile 1 kết nối qua extension; mở reviewer course preview, chuyển bài và mở tài liệu qua HTTP authorization rồi verified PDF blob. Chủ dự án xác nhận trực tiếp: (1) PDF control tại localhost:15091 hiển thị bình thường; (2) PDF trong modal PWD301 hiển thị; (3) đặt chuột trong PDF và cuộn được đến trang 2. Trả lời ban đầu “không chuyển trang được” được làm rõ bằng thao tác cuộn thành công, không bỏ qua thất bại này.

Giới hạn công cụ: screenshot/AX của modal, HTTP inline và control PDF không có application CSP đều trả vùng trống. CDP frame tree xác nhận iframe có MIME application/pdf và URL blob đúng. Không kết luận viewer hỏng từ ảnh trống; không dùng các ảnh browser-edge-pdf-modal.png, browser-edge-pdf-inline.png, browser-edge-pdf-control.png làm proof nội dung PDF. Thử điều khiển native viewer bằng công cụ timeout/không đổi AX. Download-event mới trên Edge timeout, không tính là pass; lần tải thật qua UI và PDF render trước đó vẫn là evidence đã ghi ở trên. Lượt này không sửa source sản phẩm, không thay CSP hoặc thêm thư viện viewer.

Audit chốt: đọc lại yêu cầu gốc A–E, báo cáo/review và logs full-verifier-release, sql-release, sql-all-gates-final, browser-db-proof-final, pdf-geometry. Source/test/check files không có mtime mới hơn verifier đã kết thúc; không coi kiểm tra mtime là thay thế tests. Repo check và git diff --check chạy lại exit 0. Full suite không chạy lại trong lượt chỉ đóng cổng browser; số liệu là output thật đã chạy trước đó trong cùng phiên goal. Không cộng overlap SQL, không tính skipped là pass.

Open Code Review chạy delegate mode thật: CLI selection/rules, host review diff/downstream; không external OCR LLM endpoint. Windows Application Control chặn binary; không bypass. CLI 1.12.12 chạy trong Linux read-only container exit 0, có Git 2.39.5 compatibility warning. Coverage/finding: TASK-090_CODE_REVIEW.md. Impeccable context/detect chạy thật; detect exit 2 với 54 warnings trên toàn file, không gọi PASS. Hai warnings trong student result là regex sanitizer <img[^> (false positive); phần còn lại legacy ngoài scope. Các sửa cuối được kiểm tra thủ công theo craft floor, không lặp detector.

## G. Remaining gates và TASK-088

TASK-090 COMPLETED. Verifier source hiện tại đã kết thúc PASS; toàn bộ frontend PASS. Tám SQL-only skips đã có lượt thực thi riêng trên MSSQL (SQL 46 và SQL all-gates 7, không cộng các lượt overlap). Native PDF trong trang đã được chủ dự án xác nhận hiển thị và cuộn đến trang 2 trong Edge; automated native-viewer capture/control vẫn là giới hạn công cụ, không phải gate PASS tự động. Agent VPS revalidate shared app CSP/routes/views, file authorization, course/lesson/attempt services và migration head reviewpolicy20261010. Regression này không thay thế B2/YouTube thật, cloud recovery hoặc workload 8 GB. **Không tuyên bố DEPLOY_READY.**

Đã dùng 7 skill gồm: superpowers (using-superpowers, systematic-debugging, test-driven-development, writing-plans, executing-plans, verification-before-completion, dispatching-parallel-agents), task-observer, ponytail, full-output-enforcement, open-code-review (delegate), impeccable, pdf.
