# 21 — ASSUMPTIONS AND DATABASE ARCHITECTURE DECISIONS

Tài liệu này phân biệt rõ:

- **CONFIRMED BUSINESS RULE** — User đã xác nhận qua Plan Mode.
- **DERIVED DATABASE DESIGN** — lựa chọn kỹ thuật để thực hiện business rule.
- **ASSUMPTION** — chi tiết chưa được business rule khóa; chọn default an toàn để tiếp tục.
- **RECOMMENDATION** — vận hành/tối ưu có thể thay đổi mà không đổi nghiệp vụ.

Không một ADR kỹ thuật nào dưới đây được hiểu là tự ý thay đổi business rule đã khóa.

---

## ADR-DB-001 — BIGINT internal key + UUID public identifier

**Classification:** DERIVED DATABASE DESIGN

**Context**

SQL Server, Flask/SQLAlchemy, một server self-host; dữ liệu có nhiều FK và query relational. Không có nhu cầu distributed-ID generator.

**Decision**

- PK nội bộ: `BIGINT IDENTITY`.
- Entity có exposure qua API/URL quan trọng: thêm `public_id UNIQUEIDENTIFIER`, mặc định `NEWSEQUENTIALID()`.
- API không dựa vào sequential integer như authorization mechanism; authorization vẫn kiểm tra resource ownership.

**Alternatives considered**

- UUID làm PK cho mọi table.
- INT PK.
- Snowflake/distributed ID.

**Why selected**

BIGINT đơn giản, index/FK nhỏ hơn UUID, đủ scale; public UUID giảm accidental enumeration nhưng không thay authorization.

**Consequences**

Có hai định danh ở entity công khai; mapping API phải thống nhất.

**Future trigger to reconsider**

Sharding/multi-region write hoặc scale vượt BIGINT thực tế.

---

## ADR-DB-002 — Timestamps là UTC `DATETIME2(3)`

**Classification:** DERIVED DATABASE DESIGN

**Context**

Assessment timer, retention 30 ngày, audit và job retry cần clock nhất quán.

**Decision**

SQL Server lưu UTC bằng `DATETIME2(3)`; application convert timezone để hiển thị. Server time là authority cho assessment.

**Alternatives considered**

- Local Vietnam time trong DB.
- `DATETIMEOFFSET` cho mọi field.

**Why selected**

UTC đơn giản cho so sánh/retention; timezone hiển thị là concern application.

**Consequences**

Code phải không dùng naive local datetime cho quyết định nghiệp vụ.

**Future trigger to reconsider**

Nếu business cần giữ offset gốc của sự kiện theo pháp lý.

---

## ADR-DB-003 — SQL-backed session + auth/token version để revoke tức thì

**Classification:** DERIVED DATABASE DESIGN

**Context**

Web dùng Flask-Login/session; REST dùng JWT; suspend phải revoke mọi session/JWT ngay.

**Decision**

- Persist server-side auth session metadata trong `auth_sessions`.
- `users.auth_version`/token grant version tham gia validate session/JWT.
- Suspend/password/security revocation tăng version + revoke grants/sessions trong transaction.

**Alternatives considered**

- Pure cookie session không persistent.
- Stateless JWT tới expiry.
- Global Redis-only revocation.

**Why selected**

Đáp ứng immediate revocation mà không yêu cầu Redis bắt buộc cho correctness.

**Consequences**

Mỗi authenticated request cần check lightweight session/version hoặc cached representation có invalidation.

**Future trigger to reconsider**

Scale session validation đủ lớn để cần dedicated distributed session store.

---

## ADR-DB-004 — Một logical Enrollment, nhiều EnrollmentPeriod

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business rule: chỉ một logical Enrollment/User-Course; re-enroll dùng lại Enrollment, restart từ đầu; vẫn phải giữ leave/rejoin history và purge detail theo từng lượt.

**Decision**

- `enrollments` là identity User-Course lâu dài.
- `enrollment_periods` đại diện mỗi giai đoạn học active/left của cùng Enrollment.
- `enrollment_events` ghi lifecycle facts.
- LessonProgress/Attempt liên kết period để purge đúng lượt.

**Alternatives considered**

- Tạo Enrollment mới cho mỗi lần học.
- Reset/overwrite toàn bộ một Enrollment không period.

**Why selected**

Giữ đúng “cùng logical Enrollment” nhưng không rewrite history và cho phép retention 30 ngày chính xác.

**Consequences**

Schema thêm một table period nhưng tránh event-sourcing toàn hệ thống.

**Future trigger to reconsider**

Nếu business sau này muốn mỗi enrollment attempt là entity độc lập có certificate/billing riêng.

---

## ADR-DB-005 — New Lesson optional cho cohort cũ bằng effective timestamp, không snapshot Course per Student

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business rule: thêm Lesson mới không làm progress Student cũ giảm; Lesson mới là “Xem thêm” cho existing cohort; tránh lưu nhiều Course version.

**Decision**

Lesson có `required_for_periods_starting_at` (hoặc equivalent effective boundary). EnrollmentPeriod bắt đầu trước boundary coi Lesson mới optional cho completion/progress denominator.

**Alternatives considered**

- Snapshot toàn Course/Lesson list cho mỗi Enrollment.
- Recompute mọi Student và làm progress tụt.

**Why selected**

Ít dữ liệu, query được, giữ đúng intent.

**Consequences**

Completion calculation phải dùng period start/effective date, không chỉ current Lesson list.

**Future trigger to reconsider**

Nếu Course versioning/certification pháp lý yêu cầu chương trình học immutable per cohort.

---

## ADR-DB-006 — Assessment mapping giữ Question identity; Attempt resolve latest valid QuestionRevision lúc start

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business rule superseded “published immutable”: Student chưa start luôn nhận latest Question version; Student đã start giữ frozen snapshot. Structure/points lock sau first start.

**Decision**

`assessment_question_assignments`/pool reference `questions.id`. Khi start attempt, transaction resolve `questions.current_revision_id`, tạo `attempt_questions` snapshot và choice snapshots.

**Alternatives considered**

- Assessment pin QuestionRevision lúc publish.
- Assessment tự update FK revision ngoài attempt.

**Why selected**

Phản ánh chính xác rule “latest for not-started” mà không mutate existing attempt.

**Consequences**

Start-attempt transaction phải atomic với Question current revision đọc/snapshot.

**Future trigger to reconsider**

Nếu business quay lại “published assessment pin revision”.

---

## ADR-DB-007 — Course material change dùng staging request thay vì mutate published row trước approval

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business rule: minor edit có thể apply ngay; material edit phải Admin re-approval. Chưa quy định storage representation.

**Decision**

`course_change_requests` giữ proposed material change/diff/payload ở trạng thái review; approved transaction mới apply vào canonical Course/Lesson/requirements.

**Alternatives considered**

- Copy toàn Course version graph.
- Mutate canonical rồi đánh flag “pending approval”.

**Why selected**

Không expose unapproved material change và tránh snapshot toàn Course.

**Consequences**

Payload dùng limited JSON/structured metadata cần schema validation ở service.

**Future trigger to reconsider**

Nếu material edit trở nên phức tạp đến mức cần first-class CourseVersion.

---

## ADR-DB-008 — Limited JSON trên SQL Server

**Classification:** DERIVED DATABASE DESIGN

**Context**

Một số payload audit/diff/AI/job diagnostic có shape biến đổi, nhưng schema không được biến thành generic JSON database.

**Decision**

Core business fields normalized; JSON chỉ dùng cho metadata/payload biến đổi có `ISJSON` check khi phù hợp.

**Alternatives considered**

- EAV.
- JSON cho hầu hết entity.
- Tạo table riêng cho mọi diagnostic property.

**Why selected**

Giữ relational queryability mà không overengineer metadata ít query.

**Consequences**

JSON không được chứa secret/raw token/password; application validate shape.

**Future trigger to reconsider**

Khi một JSON field trở thành query/filter/join thường xuyên → normalize.

---

## ADR-DB-009 — External vector index, SQL giữ RAG source-of-truth metadata

**Classification:** DERIVED DATABASE DESIGN

**Context**

SQL Server là primary DB nhưng vector search technology có thể thay; RAG cần authorization/version/invalidation rõ.

**Decision**

SQL tables giữ KnowledgeDocument/Version/Chunk metadata, source lineage, status và vector key/namespace. Vector embedding/index có thể ở infrastructure phù hợp; SQL vẫn quyết định version nào được phép retrieve.

**Alternatives considered**

- Binary embedding lớn trực tiếp SQL Server core schema.
- Treat vector store as source of truth.

**Why selected**

Tách replaceable search infrastructure khỏi authorization/historical metadata.

**Consequences**

Index worker cần two-phase activate: build external → mark SQL version ACTIVE atomically.

**Future trigger to reconsider**

SQL Server/vector capability được chọn chính thức và đáp ứng performance tốt.

---

## ADR-DB-010 — Generic BackgroundJob chỉ cho cơ chế chung, domain job vẫn có table riêng khi cần

**Classification:** DERIVED DATABASE DESIGN

**Context**

Có scan/import/index/email/retention/analytics/regrade. Một “everything jobs table” sẽ che mất domain state; nhưng duplicate retry mechanics cũng không nên viết lại nhiều lần.

**Decision**

`background_jobs` lưu claim/status/retry/timing chung. Domain phức tạp có table riêng như `regrade_jobs`, `document_import_jobs`, `email_deliveries` và optional FK về generic job.

**Alternatives considered**

- Chỉ generic job payload JSON.
- Mỗi domain tự implement queue fields hoàn toàn.

**Why selected**

Cân bằng maintainability và queryable domain state.

**Consequences**

Worker framework phải rõ ownership giữa generic row và domain row.

**Future trigger to reconsider**

Nếu chuyển sang external durable queue/orchestrator có persistence riêng.

---

## ADR-DB-011 — Trigger chỉ bảo vệ invariant lịch sử/khóa quan trọng

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business service là nơi xử lý logic; nhưng một số mutation tuyệt đối không được bypass bởi admin script/ORM bug.

**Decision**

Trigger cho:

- published assessment timing immutable;
- assessment structure/points lock sau first start;
- used QuestionRevision/choice/accepted answer immutable;
- Question type lock sau answered;
- append-only AuditEvent;
- selected current-version integrity guards.

Không dùng trigger để tính progress/regrade/recommendation.

**Alternatives considered**

- Service-only.
- Trigger-heavy business logic.

**Why selected**

Defense-in-depth cho historical integrity, nhưng tránh hidden domain behavior.

**Consequences**

Migration/backfill phải test trigger interaction.

**Future trigger to reconsider**

Nếu constraint có thể thay trigger bằng declarative DB feature rõ hơn.

---

## ADR-DB-012 — Course leave khi có active AssessmentAttempt

**Classification:** ASSUMPTION

**Context**

Plan Mode chưa khóa cụ thể Student bấm Leave Course trong lúc còn AssessmentAttempt `IN_PROGRESS`.

**Decision**

Safe default: **block leave** cho tới khi active attempt terminal (submitted/expired/cancelled). Không tự cancel bài khi Student bấm leave.

**Alternatives considered**

- Auto-cancel attempt.
- Allow leave và attempt tiếp tục orphaned.

**Why selected**

Ít bất ngờ nhất, không phá grading/timer/history.

**Consequences**

UI phải giải thích lý do và cho Student hoàn tất/đợi hết bài.

**Future trigger to reconsider**

User xác nhận behavior khác cho leave-during-attempt.

---

## ADR-DB-013 — Scoring policy hỗ trợ AVERAGE như một configured option

**Classification:** DERIVED DATABASE DESIGN

**Context**

Business rule cho Instructor chọn first/latest/highest hoặc policy được cấu hình khác.

**Decision**

Reference schema hỗ trợ `FIRST`, `LATEST`, `HIGHEST`, `AVERAGE` như tập policy ban đầu. Không cho arbitrary expression/script.

**Alternatives considered**

- Chỉ ba policy named.
- Custom formula JSON/expression.

**Why selected**

AVERAGE là option thông dụng, vẫn bounded/secure; không mở arbitrary formula engine.

**Consequences**

Course completion/result aggregation service phải xử lý policy enum.

**Future trigger to reconsider**

Khi Instructor cần weighted/custom formula thật sự.

---

## ADR-DB-014 — `ROWVERSION` cho optimistic concurrency, tách khỏi QuestionRevision business version

**Classification:** DERIVED DATABASE DESIGN

**Context**

Course/Lesson/Question/Assessment/File/Knowledge và một số grading row có concurrent editor/job.

**Decision**

Dùng SQL Server `ROWVERSION` làm concurrency token trên mutable hot entities. `QuestionRevision.revision_no` là business historical version, không dùng thay `ROWVERSION`.

**Alternatives considered**

- `updated_at` only.
- Long-held pessimistic row locks.

**Why selected**

Native, reliable conditional update; không giữ lock lâu.

**Consequences**

API edit command phải gửi expected version và trả conflict khi stale.

**Future trigger to reconsider**

Không cần; đây là pattern phù hợp SQL Server trừ khi ORM/tooling thay đổi.

---

## ADR-DB-015 — Filtered unique index cho một ACTIVE FileRevision và KnowledgeVersion

**Classification:** DERIVED DATABASE DESIGN

**Context**

Service transaction cần switch current version, nhưng worker race có thể tạo hai ACTIVE rows nếu chỉ dựa vào code.

**Decision**

- `UNIQUE(file_asset_id) WHERE status='ACTIVE'`
- `UNIQUE(knowledge_document_id) WHERE status='ACTIVE'`

Current pointer vẫn tồn tại để read nhanh; activation transaction cập nhật status + pointer atomically.

**Alternatives considered**

- Service-only invariant.
- Không lưu ACTIVE status, chỉ current pointer.

**Why selected**

Defense-in-depth và giúp query pending/invalidated lifecycle rõ.

**Consequences**

Activation order phải chuyển old ACTIVE → inactive trước khi new → ACTIVE trong cùng transaction.

**Future trigger to reconsider**

Nếu lifecycle model bỏ ACTIVE status và dùng pointer làm sole truth.

---

## ADR-DB-016 — Progress/analytics là derived cache, không phải source of truth

**Classification:** CONFIRMED BUSINESS RULE + DERIVED DATABASE DESIGN

**Context**

Plan Mode đã khóa progress có thể cache để đọc nhanh nhưng LessonProgress/AssessmentResult là nguồn thật.

**Decision**

`enrollments.current_progress_percent`/analytics snapshots là derived values. Recompute service có thể rebuild từ canonical learning/assessment data còn trong retention + completion summary.

**Alternatives considered**

- Tính toàn bộ live mỗi request.
- Chỉ lưu progress field và tin nó tuyệt đối.

**Why selected**

Hiệu năng tốt nhưng recoverable.

**Consequences**

Mutation học tập phải invalidate/recompute cache; Student không được submit progress percent trực tiếp.

**Future trigger to reconsider**

Nếu dataset quá nhỏ có thể bỏ cache mà không đổi business behavior.

---

## ADR-DB-017 — 30-day detailed retention gắn EnrollmentPeriod; compact summary giữ lâu dài

**Classification:** CONFIRMED BUSINESS RULE + DERIVED DATABASE DESIGN

**Context**

Sau leave >30 ngày không rejoin, detailed data có thể purge và không còn future automatic regrade, nhưng completion/prerequisite/final summary phải giữ.

**Decision**

Retention worker đánh dấu/purge period detail; `course_completion_summaries` + enrollment lifecycle fact tồn tại lâu dài. Regrade query chỉ chọn period đủ retention eligibility.

**Alternatives considered**

- Giữ mọi attempt mãi.
- Purge mọi thứ cả completion evidence.

**Why selected**

Đúng business rule và bảo toàn prerequisite.

**Consequences**

Analytics lịch sử chi tiết giảm sau purge; documentation/report phải biết retention boundary.

**Future trigger to reconsider**

Nếu trường/luật yêu cầu retention dài hơn.

---

## ADR-DB-018 — Video limit là policy cấu hình dưới 1 GB, không hard-code bằng SQL CHECK theo MIME

**Classification:** CONFIRMED BUSINESS RULE + DERIVED DATABASE DESIGN

**Context**

Round 6 xác nhận video dưới 1 GB; file type được xác định sau server-side detection.

**Decision**

Upload service/config enforce: image ~10MB, PDF/DOCX ~50MB, PPTX ~100MB, video **<1GB**. Database chỉ check `size_bytes > 0` và lưu detected MIME/status.

**Alternatives considered**

- SQL CHECK theo filename/MIME.

**Why selected**

SQL row không nên tin client extension/MIME và policy size cần configurable.

**Consequences**

Upload tests bắt buộc verify service limit; DB không thể tự nhận file bytes format.

**Future trigger to reconsider**

Nếu size policy trở thành per-tenant plan stored relationally.

---

# Open assumptions summary

| ID | Assumption | Current safe behavior | Business impact |
|---|---|---|---|
| A-001 | Leave Course trong active attempt | Block leave đến terminal | Nhỏ; tránh orphan/cancel ngầm |
| A-002 | SQL Server isolation configuration | Khuyến nghị `READ_COMMITTED_SNAPSHOT` sau concurrency test | Operational, không đổi nghiệp vụ |
| A-003 | Vector storage engine | External/replaceable; SQL metadata authoritative | Infrastructure choice |
| A-004 | Exact backup retention/RPO/RTO numbers | Daily backup required; concrete retention configurable | Operational |
| A-005 | Exact lease duration/heartbeat interval | Configurable short lease; DB stores expiry/heartbeat | UX/operations, không đổi single-tab rule |

Không có OPEN ISSUE nào buộc phải dừng ERD. Nếu các assumption trên được User xác nhận khác trong tương lai, cập nhật ADR + migration/service rule tương ứng.
