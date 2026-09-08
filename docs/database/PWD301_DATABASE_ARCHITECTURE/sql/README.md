# SQL Server Reference DDL

Các file trong thư mục này là **reference architecture DDL** cho Microsoft SQL Server. Production schema nên được triển khai qua Flask-Migrate/Alembic và giữ cùng invariants với DDL này.

## Execution order

1. `001_identity.sql`
2. `002_course_learning.sql`
3. `003_question_bank.sql`
4. `004_assessment.sql`
5. `005_attempt_regrade.sql`
6. `006_files_import.sql`
7. `007_ai_rag.sql`
8. `008_notification_audit.sql`
9. `009_operations.sql`
10. `010_cross_domain_constraints.sql`
11. `011_indexes.sql`
12. `012_critical_invariant_triggers.sql`

## Notes

- Timestamps sử dụng UTC `DATETIME2(3)`.
- Internal keys dùng `BIGINT IDENTITY`.
- Public IDs dùng `UNIQUEIDENTIFIER` ở entity phù hợp.
- SQL Server `ROWVERSION` dùng cho optimistic concurrency; không phải business revision number.
- JSON metadata dùng `NVARCHAR(MAX)` và `ISJSON` khi applicable.
- `ON DELETE CASCADE` chỉ dùng với disposable child data; historical learning/assessment data được application-managed.
- Các cross-domain current pointers được tạo sau domain tables để tránh circular bootstrap dependency.
- Filtered unique indexes đảm bảo tối đa một ACTIVE `file_revision`/asset và một ACTIVE `knowledge_version`/document.
- Trigger chỉ bảo vệ critical immutable/history invariants, không thay service-layer business logic.

## Verification

Reference DDL cần được:

1. chạy trên SQL Server test database;
2. chạy migration fresh install;
3. chạy `19_DATABASE_INTEGRITY_TEST_PLAN.md`;
4. kiểm tra execution plans với seed/load data;
5. điều chỉnh index dựa trên workload thật trước production.
