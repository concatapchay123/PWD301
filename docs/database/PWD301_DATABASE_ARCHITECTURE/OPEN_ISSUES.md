# OPEN ISSUES

## Trạng thái

**No blocking business-rule contradictions remain.**

Consistency pass đã reconcile các rule superseded và giữ rule mới nhất đã được User xác nhận. Package có thể dùng làm implementation baseline.

## Non-blocking implementation/deployment notes

| ID | Type | Note | Current safe choice | Revisit trigger |
|---|---|---|---|---|
| NB-001 | Tuning | Exact attempt lease/heartbeat interval chưa khóa bằng business rule. | Dùng cấu hình ngắn có expiry + heartbeat; không giữ DB lock dài. | Load/concurrency test trên server thật. |
| NB-002 | Operations | Exact backup retention, RPO/RTO còn là deployment configuration. | Daily automatic backup + manual backup + periodic restore drill. | Trước production/demo deployment. |
| NB-003 | Infrastructure | Vector search engine cụ thể chưa bị khóa. | SQL Server giữ authorization/provenance/version metadata; vector layer replaceable. | Khi chọn RAG implementation. |
| NB-004 | Verification | SQL Server runtime execution không khả dụng trong environment QA hiện tại. | Static SQL Server compatibility/structure review. | Chạy fresh migration trên SQL Server test instance. |
| NB-005 | Verification | Mermaid CLI/render engine không được cài trong environment QA hiện tại. | Static Mermaid block/entity/reference validation. | CI/local docs build có Mermaid renderer. |
| NB-006 | Product rule default | Leave Course khi còn AssessmentAttempt active chưa được User định nghĩa riêng. | Service tạm block leave cho tới khi attempt terminal để tránh orphan/retention race. | Nếu product cần cho phép leave giữa attempt. |

Các note trên **không thay đổi business behavior đã khóa** và không phải blocker cho packaging.
