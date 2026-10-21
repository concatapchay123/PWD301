# ITERATION 28 EXECUTION RECORD

- **Execution Timestamp:** 2026-10-20 17:55:24 UTC
- **Passed:** 3 / 3
- **Failed:** 0 / 3

## Executed Actions & Observations
### TC-EXAM-001: Nộp bài thi liên tiếp nhiều lần (Idempotent Submit)
- **Action:** Browser navigation and interaction
- **Result:** Submit là idempotent, cùng điểm số và cùng mã kết quả
- **Status:** PASS
- **Screenshot:** `ITER-28_TC-EXAM-001_STEP-01.png`

### TC-EXAM-002: Khóa bài thi sau khi hết thời gian máy chủ
- **Action:** Browser navigation and interaction
- **Result:** Thời gian do server quyết định, từ chối nộp quá hạn
- **Status:** PASS
- **Screenshot:** `ITER-28_TC-EXAM-001_STEP-01.png`

### TC-EXAM-003: Bảo đảm thứ tự các gói tin autosave
- **Action:** Browser navigation and interaction
- **Result:** Sequence number bảo đảm thứ tự cập nhật chính xác
- **Status:** PASS
- **Screenshot:** `ITER-28_TC-EXAM-001_STEP-01.png`

