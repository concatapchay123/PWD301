# MASTER DEFECT REGISTRY & REMEDIATION LEDGER — 100% REMEDIATED & VERIFIED

## Defect Remediation & Quality Audit Summary
- **Total Defects Identified During QA & Remediation Campaigns:** 11
- **Critical (P0) Blockers:** 1 (`DEFECT-07` - Grade Appeal 500 Error) — **RESOLVED & VERIFIED**
- **High Priority (P1) Defects:** 3 (`DEFECT-01`, `DEFECT-06`, `DEFECT-08`) — **RESOLVED & VERIFIED**
- **Medium Priority (P2) Inconsistencies:** 3 (`DEFECT-02`, `DEFECT-09`, `BUG-QA-002`) — **RESOLVED & VERIFIED**
- **Low Priority (P3) Schema / Routing Items:** 4 (`DEFECT-03`, `DEFECT-04`, `DEFECT-05`, `BUG-QA-001`) — **RESOLVED & VERIFIED**
- **Total Open Defects:** **0**
- **Defect Remediation Rate:** **100.0%**
- **Post-Remediation Regression Status:** 100.0% Pass Rate across all 50 Iterations

---

## Complete Defect Resolution Ledger

| Defect ID | Severity | Category | Description | Root Cause | Fix Applied | Verification Status |
|---|---|---|---|---|---|---|
| [DEFECT-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-01.md) | High (P1) | REST API Envelope | Missing `"success": false` & `"data": null` on 401/403 responses | Decorator returned dictionary omitting mandatory top-level envelope fields | Standardized `authorization_service.py` error envelopes for all roles | **RESOLVED & VERIFIED** (Pass across Iterations 01, 03, 13) |
| [DEFECT-02](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-02.md) | Medium (P2) | REST API Schema | Missing standardized JSON envelope wrapping on 200 OK responses | Endpoints returned raw dictionaries directly at root without wrapper | Global `after_request` interceptor in `src/pwd301/__init__.py` + route wrappers | **RESOLVED & VERIFIED** (Pass across Iterations 01-50) |
| [DEFECT-03](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-03.md) | Low (P3) | Routing / Alias | Missing canonical `/student/courses` endpoint (returned 404) | Only `/student/enrollments` was registered | Added canonical `@student_bp.route("/courses")` alias | **RESOLVED & VERIFIED** (Pass in Iteration 03, 08, 27) |
| [DEFECT-04](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-04.md) | Low (P3) | REST API Envelope | Missing `"data": null` on 409 Conflict concurrent login response | 409 response dictionary omitted `"data": null` field | Added `"data": None` to 409 response in `auth/routes.py` | **RESOLVED & VERIFIED** (Pass in Iteration 02, 35) |
| [DEFECT-05](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-05.md) | Low (P3) | REST API Envelope | Malformed 429 Rate Limit error response envelope | Rate limit handlers returned raw error object | Standardized 429 responses with `"success": false, "data": null` | **RESOLVED & VERIFIED** (Pass in Iteration 02, 13, 32) |
| [BUG-QA-001](file:///e:/PWD301/qa-fullstack-audit/defects/BUG-QA-001.md) | Low (P3) | REST API Envelope | `/admin/telemetry` 401 unauthenticated response lacked `"data": null` | JWT auth service error helper omitted `"data": null` | Standardized `jwt_auth_service.py` error payloads across all endpoints | **RESOLVED & VERIFIED** (Pass in Iteration 01, 16, 40) |
| [BUG-QA-002](file:///e:/PWD301/qa-fullstack-audit/defects/BUG-QA-002.md) | Medium (P2) | HTTP Method | Method Not Allowed (405) on HTTP `PUT /api/courses/<id>` | Route decorator registered only `methods=["PATCH"]` | Extended decorator to `methods=["PATCH", "PUT"]` in `api_courses/routes.py` | **RESOLVED & VERIFIED** (Pass in Iteration 06, 07, 32) |
| **DEFECT-06** | High (P1) | Course State Isolation | Khóa học đã bị xóa (TRASH) vẫn hiển thị trong tài khoản học viên | `enrollment_service.py` & `analytics_service.py` thiếu điều kiện lọc `Course.status != 'TRASH'` và `Course.deleted_at.is_(None)` | Bổ sung filter CSDL loại bỏ 100% khóa học đã xóa khỏi danh sách học viên, overview và khảo thí | **RESOLVED & VERIFIED** (Pass in Iteration 21: `TC-REM-001`) |
| **DEFECT-07** | Critical (P0) | Assessment Appeal | Lỗi 500 khi nộp đơn phúc khảo và thiếu tính năng đính kèm minh chứng | `submit_attempt_appeal_route` truy cập sai trường `.score` thay vì `.raw_score` gây `AttributeError`; CSDL thiếu cột lưu minh chứng | Sửa logic lấy điểm, bổ sung cột `evidence_filename` / `evidence_url` và route đính kèm multipart file <= 10MB | **RESOLVED & VERIFIED** (Pass in Iteration 22: `TC-REM-002`, `TC-REM-003`) |
| **DEFECT-08** | High (P1) | Exam Proctoring / Armor | Phóng to/thu nhỏ trình duyệt (zoom) bị nhận diện nhầm thành DevTools gây khóa màn hình hoặc logout | `video-armor.js` sử dụng chênh lệch `outerWidth - innerWidth > 160`; `student.js` bật `watchFullscreen` kích hoạt overlay khóa | Xóa hoàn toàn phép so sánh kích thước cửa sổ khỏi `video-armor.js`; vô hiệu hóa overlay khóa khi zoom trình duyệt | **RESOLVED & VERIFIED** (Pass in Iteration 23: `TC-REM-004`, Iteration 39: `TC-ARMOR-001`) |
| **DEFECT-09** | Medium (P2) | AI Tutor Persona | Phát ngôn của trợ lý AI chưa chuẩn hóa theo 3 mẫu phát ngôn bất biến | System instruction, classifier và UI có các câu chào / từ chối dài dòng cũ | Đồng bộ 100% 3 mẫu phát ngôn chuẩn mực của "Bạch Tuột, trợ lí AI của hệ thống PPTQ" trên backend & frontend | **RESOLVED & VERIFIED** (Pass in Iteration 24: `TC-REM-005` - `TC-REM-008`, Iteration 38: `TC-AI-003`) |
