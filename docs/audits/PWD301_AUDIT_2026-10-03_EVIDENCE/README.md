# Bằng chứng audit ngày 03/10/2026

Hai báo cáo ở thư mục cha là deliverables chính. Đây là artifact kiểm tra, không phải mã sản phẩm hay chứng nhận release.

## Baseline

`baseline-head.txt` lưu HEAD; `baseline-status.txt` lưu danh sách thay đổi đã có. Audit không reset/commit/push/sửa source có sẵn. Source dirty là phiên bản được kiểm tra.

## Browser đã quan sát

Browser: Edge, phiên giảng viên đang mở ở `http://127.0.0.1:5000/`.

1. Trang quản lý môn: `#/instructor/courses/manage?id=7f8753c7-5788-4b04-9c06-edeedfbbd915`.
2. Click nút Bảng điểm & Bài nộp.
3. Hash trở thành `#/instructor/courses/7f8753c7-5788-4b04-9c06-edeedfbbd915/assessments/649eb226-0712-4f35-96d1-407b1e2dc55a/results`.
4. Visible text: “Lỗi tải kết quả: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.”
5. Reload; CDP Network responseReceived xác nhận `GET http://127.0.0.1:5000/student/attempt/` status404. Không ghi cookie/header/session token vào artifact.
6. Tab GET endpoint JSON attempts trực tiếp bị browser client block. Không coi client block là backend error.

Nguồn lỗi: generic student suffix branch chạy trước instructor branches; malformed attempt ID chứa # nên phần sau thành URL fragment. `router-reproduction.cjs` chạy source dispatcher bằng VM và stub views, 3 instructor cases fail, 2 student cases pass.

## Lệnh và log

- `node --test` với toàn bộ 26 test files frontend: `frontend-tests.txt`, 81 passed.
- `node docs/audits/PWD301_AUDIT_2026-10-03_EVIDENCE/router-reproduction.cjs`: `router-reproduction.txt`, 3 fail/2 pass, exit1 có chủ đích để chứng minh bug.
- Backend 103 tests: `backend-targeted-tests.txt`; suite course IDOR/RBAC, lesson authoring, scan, operations/security, unit user/file.
- Backend 11 tests: `backend-additional-tests.txt`; health six services, student recommendations, file API.
- Backend 23 tests: `backend-malware-tests.txt`; M1 file access + malware scan service.
- Grading 58 tests: unit grading, grading API, grading IDOR, assessment regrading traceability; command và kết quả được ghi trong audit. Không lưu riêng full console log của lượt này.
- `backend-reproduction.py`/`.json`: SQLite fake identities; UUID/numeric governance, Admin no-reason edit, no-op nonowner metadata.
- `gradebook-reproduction.py`/`.txt`: SQLite test fixtures; pending omission, grading empty, invalid Decimal500, Admin detail without reason, objective manual rewrite, hidden/released payload contracts.
- Full pytest: `pytest-full.txt`, với `TEST_DATABASE_URL=sqlite:///:memory:` và `-p no:cacheprovider`; kết quả cuối ghi trong báo cáo chính.
- Static fresh: repo check PASS; Ruff PASS; format265; mypy88 files clean (unused module config note). Audit không sửa lỗi sản phẩm.
- OCR review: exit1 vì chưa cấu hình endpoint LLM; không có output review được công cụ chứng nhận.

Các log pytest chọn lọc có thể trùng ca với full suite; không cộng thành tổng unique tests. Pytest logs trong PowerShell có thể chứa định dạng NativeCommandError của stderr; kết luận lấy từ pytest summary và exit code.

## SQL Server đọc trực tiếp

`docker ps`: web, db, ClamAV healthy tại thời điểm đọc. `docker exec pwd301_web flask db current` và `flask db heads` đều `a1b2c3d4e5f8 (head)`.

Query đọc metadata bằng SQLAlchemy bind parameters:

```sql
SELECT COUNT(*) FROM sys.columns
WHERE object_id=OBJECT_ID(:table) AND name=:column
```

Parameters table=`users`, column=`avatar_url`; output `avatar_column_count=1`. Không in connection string và không ghi SQL schema/data.

## Timestamp reproduction

Node với `TZ=Asia/Bangkok`, input UTC-naive `2026-10-03T03:57:15.761206`:

- `new Date(raw).toLocaleString('en-GB')` → `03/10/2026, 03:57:15`.
- `new Date(raw+'Z').toLocaleString('en-GB')` → `03/10/2026, 10:57:15`.

Đây là repro parser, không phải test tất cả UTC serializer production.

## Nhật ký tiến trình/giới hạn

Đọc reports và baseline → phân loại historical IDs → tái hiện browser/network → kiểm tra độc lập backend/governance và grading → chạy existing suites → thêm repro không sửa source → tạo báo cáo lỗi+giải pháp → kiểm tra tài liệu/evidence.

Không đã chạy mọi role/UI flow; không release/pentest; không chạy SQL Server race/upgrade/downgrade/restore; không dùng live test fixture cleanup. Scripts trong thư mục này đặt `TEST_DATABASE_URL` in-memory, dùng app testing và fake data. Nếu chạy lại, giữ nguyên sandbox setting. Không mang các script này vào pipeline live.

## Đóng kiểm tra

Full pytest: 1540 passed in 1027.04s, exit0. Node: 81 passed. Router regression repro sau di chuyển artifact: 2 passed, 3 failed, exit1. Repo contract sau tạo báo cáo: PASS. Link hai báo cáo đã kiểm tra tồn tại. Git status các file có sẵn khớp baseline (diff_count=0); chỉ thêm docs/audits artifacts. Files báo cáo đã kiểm tra UTF-8 và coverage15 historical/24 findings/21 scenarios; không commit/push.

