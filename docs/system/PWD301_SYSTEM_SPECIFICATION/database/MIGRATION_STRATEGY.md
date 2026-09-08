# 20 — MIGRATION STRATEGY

## 1. Bối cảnh

Tại thời điểm thiết kế database architecture này, nguồn cung cấp không kèm một repository/schema production đang chạy cần bảo toàn. Vì vậy reference DDL được thiết kế như **greenfield target schema** cho PWD301, nhưng migration workflow vẫn phải theo Flask-Migrate/Alembic và tuyệt đối không dựa vào `db.create_all()` trong production.

> Classification: **ASSUMPTION — greenfield initial schema**. Nếu repository sau này cho thấy đã có dữ liệu/schema thật, áp dụng mục 8 “existing-schema adoption” trước khi migration.

---

## 2. Nguyên tắc migration

1. **Alembic revision là source of deployment order**; các file canonical tại `../../../database/PWD301_DATABASE_ARCHITECTURE/sql/*.sql` là reference architecture, không thay thế migration history.
2. Mỗi migration phải nhỏ, có thể review, có mục đích rõ.
3. Thay đổi phá dữ liệu phải tách thành nhiều bước: `expand → backfill → validate → constrain → cleanup`.
4. Không đổi tên/xóa cột production và thêm replacement trong cùng một bước nếu có data.
5. Không làm data backfill nặng trong request web.
6. Index lớn cần lên kế hoạch maintenance window nếu dữ liệu thật đã lớn.
7. Schema migration và application deploy phải tương thích theo rolling/forward-safe pattern ở mức hợp lý, dù project chạy một server.
8. Mọi migration release phải có backup/restore point trước thao tác phá hủy.
9. Không rollback database tự động bằng restore backup khi app deploy lỗi; Admin phải xác nhận restore theo business rule.

---

## 3. Initial migration layout đề xuất

Có thể map reference SQL thành Alembic revisions theo domain:

```text
migrations/versions/
  0001_identity_auth.py
  0002_course_learning.py
  0003_question_bank.py
  0004_assessment_structure.py
  0005_attempt_grading_regrade.py
  0006_files_import.py
  0007_ai_rag.py
  0008_notification_audit.py
  0009_operations.py
  0010_cross_domain_constraints.py
  0011_indexes.py
  0012_critical_invariant_triggers.py
  0013_seed_system_roles.py
```

Không bắt buộc giữ đúng 13 revision; mục tiêu là reviewability và dependency order.

---

## 4. Execution order

### Phase 1 — Core tables

1. Identity/Auth
2. Course/Learning
3. Question Bank
4. Assessment Structure
5. Attempt/Grading/Regrade
6. Files/Import
7. AI/RAG
8. Notification/Audit
9. Operations

### Phase 2 — Cross-domain pointers

Các pointer gây vòng dependency được thêm sau khi cả hai phía đã tồn tại, ví dụ:

- current avatar/file revision;
- current QuestionRevision;
- current EnrollmentPeriod;
- current FileRevision;
- current KnowledgeVersion;
- BackgroundJob links;
- correction/regrade lineage.

Reference: `../../../database/PWD301_DATABASE_ARCHITECTURE/sql/010_cross_domain_constraints.sql`.

### Phase 3 — Index

Tạo nonclustered/filtered indexes sau tables/FKs.

Reference: `../../../database/PWD301_DATABASE_ARCHITECTURE/sql/011_indexes.sql`.

### Phase 4 — Critical invariant triggers

Tạo trigger sau khi schema hoàn chỉnh.

Reference: `../../../database/PWD301_DATABASE_ARCHITECTURE/sql/012_critical_invariant_triggers.sql`.

---

## 5. Seed strategy

Seed bắt buộc, idempotent:

### Roles

```text
STUDENT
INSTRUCTOR
ADMIN
```

Role seed dùng stable code, không phụ thuộc ID cụ thể.

### Demo data

Seed demo có thể gồm:

- 1 Admin;
- 2 Instructor;
- 5–20 Student;
- Course/Lesson;
- Question Bank;
- Assessment draft/published;
- sample Enrollment/Attempt.

Không seed:

- real password plaintext;
- real API key;
- real email credential;
- malware sample;
- production PII.

Password seed chỉ dùng hash của demo password đã document riêng cho development.

---

## 6. Expand / Backfill / Contract patterns

## 6.1 Thêm field bắt buộc

Không:

```text
ALTER TABLE ... ADD new_col NOT NULL
```

nếu table đã có rows mà không có safe default.

Làm:

1. add nullable;
2. deploy app ghi cả field mới;
3. backfill;
4. validate `NULL = 0 rows`;
5. add `NOT NULL`;
6. bỏ fallback cũ sau release sau.

## 6.2 Đổi enum/state

Vì schema dùng constrained VARCHAR:

1. mở CHECK cho cả old + new state;
2. deploy code hiểu cả hai;
3. migrate data;
4. thu hẹp CHECK nếu cần.

## 6.3 Đổi relationship

Ví dụ chuyển từ một FK cũ sang junction table:

1. tạo junction mới;
2. backfill;
3. dual read/write nếu cần;
4. validate row counts;
5. switch application;
6. remove legacy FK sau khi ổn định.

---

## 7. Migration cho các feature nhạy cảm

## 7.1 QuestionRevision rollout

Nếu legacy schema có `questions.content` + choices trực tiếp:

1. tạo `question_revisions`;
2. tạo choice/accepted answer revision tables;
3. tạo revision `1` từ Question hiện tại;
4. set `questions.current_revision_id`;
5. map Assessment/Attempt theo source identity;
6. chỉ sau validate mới bỏ legacy mutable fields.

Không xóa old question data trước khi reconciliation hoàn tất.

## 7.2 Attempt snapshot rollout

Nếu legacy attempt chỉ giữ `question_id/answer`:

1. tạo snapshot tables;
2. backfill snapshot từ revision khả dụng;
3. đánh dấu confidence/provenance nếu exact historical rendered content không thể tái tạo;
4. không giả vờ historical snapshot chính xác nếu legacy system không lưu.

## 7.3 EnrollmentPeriod rollout

Nếu legacy có một Enrollment đơn:

1. mỗi Enrollment hiện tại tạo một period số 1;
2. map LessonProgress/Attempt vào period nếu xác định được;
3. set `current_period_id` cho active enrollment;
4. tạo summary từ completion/result hiện tại;
5. validate one active period/enrollment.

## 7.4 File blob dedup rollout

Không dedup bằng filename. Chỉ sau khi SHA-256 được tính và file bytes đã xác nhận.

1. create FileBlob by hash;
2. attach revisions;
3. verify reference count query;
4. chỉ xóa legacy physical duplicate sau recovery/verification.

## 7.5 RAG version rollout

1. create KnowledgeDocument/Version metadata;
2. index source current content;
3. activate version only after full processing;
4. then enable retrieval from new index.

---

## 8. Existing-schema adoption — nếu repository sau này có schema/data

Trước migration:

1. export current Alembic heads/history;
2. dump INFORMATION_SCHEMA tables/columns/FKs/indexes;
3. count rows mỗi table;
4. identify orphan FKs / duplicate emails / duplicate Course codes;
5. map old model → target model;
6. classify every target field:
   - direct copy;
   - transform;
   - derived;
   - unavailable historical fact;
7. create dry-run migration trên database copy;
8. compare counts/checksums;
9. run integrity scenarios;
10. only then production apply.

### Không được làm

- tự động drop table không nhận diện;
- silently merge duplicate Question;
- fabricate missing historical snapshots;
- truncate audit/history để “migration dễ hơn”.

---

## 9. Constraint rollout strategy

Một số constraint có thể phát hiện legacy data xấu. Thứ tự:

1. query violations;
2. report/repair data;
3. add constraint;
4. run negative test.

Đặc biệt:

- unique normalized email;
- Course code/title unique;
- active Enrollment uniqueness;
- one ACTIVE FileRevision;
- one ACTIVE KnowledgeVersion;
- QuestionRevision immutability;
- Assessment timing/structure/points locking.

---

## 10. Index rollout

### Fresh database

Index có thể tạo trong initial migration.

### Existing large database

Trước index:

- đo row count;
- estimate lock/write impact;
- loại duplicate/redundant index;
- tạo theo priority query-hot path;
- update statistics;
- kiểm tra execution plan sau deploy.

Không tạo index cho mọi column chỉ vì có filter UI.

---

## 11. Trigger migration

Trigger chỉ dùng cho invariant khó chấp nhận bị bypass, không dùng làm hidden business service.

Khi deploy trigger:

1. test với ORM-generated SQL;
2. test multi-row UPDATE/DELETE;
3. test migration/backfill path;
4. maintenance migration cần session/context-specific bypass chỉ nếu được thiết kế/audit rõ — mặc định **không có bypass runtime**.

---

## 12. Transaction isolation / SQL Server notes

- Dùng transaction ngắn.
- Không giữ database lock suốt thời gian Student làm bài.
- Lease là dữ liệu thời hạn + conditional update.
- Capacity/start-attempt hot race dùng transaction/appropriate locking hoặc serializable section nhỏ theo pseudocode.
- Khuyến nghị bật `READ_COMMITTED_SNAPSHOT` sau khi load/concurrency test để giảm reader-writer blocking, nhưng đây là **ADR/DB configuration**, không phải business rule.

---

## 13. Release checklist cho mỗi migration

### Before

- [ ] Migration reviewed.
- [ ] Backup metadata fresh.
- [ ] Backup restore test gần đây hợp lệ.
- [ ] Staging upgrade PASS.
- [ ] Estimated lock/data rewrite documented.
- [ ] App version compatibility checked.

### During

- [ ] Maintenance/log correlation ID.
- [ ] Migration output captured.
- [ ] Disk free-space checked.
- [ ] No manual ad-hoc schema edits ngoài migration.

### After

- [ ] `alembic current` đúng head.
- [ ] FK/check/index count expected.
- [ ] Smoke tests.
- [ ] Critical integrity tests.
- [ ] Background workers healthy.
- [ ] No unexpected long locks/errors.

---

## 14. Rollback philosophy

### Development/test

Có thể dùng Alembic downgrade khi migration thực sự reversible.

### Production-like deployment

Ưu tiên:

1. stop/disable bad app path;
2. forward-fix schema/app;
3. restore DB từ backup **chỉ khi Admin xác nhận** và đã đánh giá data loss window.

Không tự động restore backup chỉ vì healthcheck fail.

---

## 15. Migration acceptance criteria

Migration strategy đạt khi:

- fresh install tạo đúng target schema;
- seed idempotent;
- reference DDL và Alembic models không lệch;
- cross-domain FK order không circular-fail;
- historical data không bị cascade/drop ngầm;
- rollback/forward-fix plan tồn tại;
- migration tests trong `19_DATABASE_INTEGRITY_TEST_PLAN.md` PASS.
