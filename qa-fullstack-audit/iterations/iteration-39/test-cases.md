# ITERATION 39 TEST CASES

| Test ID | Requirement | Target Role | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-ARMOR-001` | REQ-SEC-03 | `STUDENT` | Không bị khóa màn hình và không bị đăng xuất | Zoom thoải mái không kích hoạt cảnh báo an ninh | **PASS** |
| `TC-ARMOR-002` | REQ-SEC-04 | `STUDENT` | Cho phép chuột phải tự do, không cảnh báo | Chuột phải hoạt động bình thường trên màn hình học tập | **PASS** |
| `TC-ARMOR-003` | REQ-SEC-05 | `STUDENT` | Phủ Blackout Shield ngay lập tức và thu hồi phiên trên server | Blackout Shield xuất hiện tức thì và gọi POST /auth/logout | **PASS** |
