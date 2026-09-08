# Domain Model

## 1. Domain boundaries

### Identity & access

`users` is the account identity. Roles are normalized through `user_roles`. Browser sessions and REST JWT grants are separate because their lifecycles differ. `auth_version` is the fast global revocation guard.

### Course & learning

A Course has one optional current Instructor owner, ordered Lessons, prerequisites and completion rules. Enrollment is a logical long-lived User-Course relationship. Enrollment periods segment re-enrollment and retention.

### Question Bank

A Question is stable identity inside one Course. Historical educational content lives in QuestionRevision. Choices and accepted short answers are children of a revision, never mutable shared rows.

### Assessment structure

An Assessment owns policy/timing. Static questions, blueprint rules and a materialized candidate pool describe the structure. Question content itself remains in the Question Bank so future starters can receive the latest approved revision.

### Attempt & grading

Attempt is the boundary at which mutable course/question content becomes immutable Student evidence. Current answer rows optimize resume. Answer events preserve detailed changes only for the configured retention window.

### Regrading

QuestionCorrection describes why a new revision affects prior grading. RegradeJob/RegradeItem make large corrections resumable. Current grade/result tables are paired with append histories.

### File & import

File bytes are deduplicated; logical assets/revisions define application lifecycle. Import is a draft staging domain and never bypasses Question Bank approval.

### AI/RAG

Conversation/message content is ephemeral. AIRequest and source usage persist minimal operational trace. KnowledgeDocument/Version/Chunk hold source/index metadata, not authorization-free knowledge.

### Notification, audit, operations

NotificationEvent is fan-out; Notification and EmailDelivery are separate delivery channels. AuditEvent is the durable append-only security/business trail. BackgroundJob is only common queue mechanics.

## 2. Table inventory

### Identity

- `users` — Tài khoản duy nhất cho Student/Instructor/Admin; email là định danh đăng nhập duy nhất.
- `roles` — Danh mục ba role hệ thống.
- `user_roles` — Quan hệ nhiều-nhiều User ↔ Role và nguồn gán quyền.
- `auth_sessions` — Session phía server cho web/Jinja/AJAX; cho phép revoke tức thì và theo dõi re-auth.
- `jwt_token_grants` — Theo dõi JWT/refresh grant cho REST API và revoke có kiểm soát.
- `user_security_tokens` — Token dùng một lần cho verify email, đổi email, reset password.
- `instructor_applications` — Yêu cầu Student trở thành Instructor; Admin duyệt/từ chối.
- `security_events` — Sự kiện bảo mật/abuse cần giữ dù raw AI chat hoặc session đã cleanup.
### Course

- `courses` — Course chính; có thể tạm không có Instructor owner; code và title đều unique.
- `course_prerequisites` — Quan hệ N-N Course yêu cầu Course khác hoàn thành trước.
- `course_completion_rules` — Cấu hình điều kiện hoàn thành Course theo mô hình đơn giản, không EAV.
- `course_change_requests` — Staging tối thiểu cho thay đổi material của Course đã published để Admin duyệt trước khi áp dụng.
- `lessons` — Lesson thuộc Course, có thứ tự, nội dung Markdown và ngưỡng hoàn thành tự động.
- `enrollments` — Một logical Enrollment duy nhất cho mỗi Student-Course; re-enroll tái sử dụng row và mở period mới.
- `enrollment_periods` — Phân đoạn các lần học bên dưới cùng logical Enrollment để reset khi re-enroll và purge đúng period.
- `enrollment_events` — Lịch sử nhỏ, append-only cho enroll/leave/re-enroll/completion/purge.
- `lesson_progress` — Source of truth cho tiến độ Lesson trong từng enrollment period.
- `course_completion_summaries` — Compact historical summary giữ sau detail purge và làm bằng chứng prerequisite.
### Question

- `questions` — Identity ổn định của một Question trong đúng một Course; nội dung nằm ở revision.
- `question_revisions` — Phiên bản nội dung/loại/đáp án semantics của Question. Choices/accepted answers thuộc revision.
- `question_revision_choices` — Choices immutable theo từng QuestionRevision; correct flag không bao giờ gửi trong Student attempt payload.
- `question_revision_accepted_answers` — Đáp án chấp nhận cho SHORT_ANSWER theo revision.
- `question_provenance` — Nguồn gốc Question/Revision: manual, import, AI-generated, duplicate; giữ traceability không phụ thuộc source record sống mãi.
### Assessment

- `assessments` — Định nghĩa bài đánh giá dùng chung engine; timing khóa ngay sau publish, structure/points khóa khi Student đầu tiên start.
- `assessment_sections` — Nhóm câu tùy chọn trong Assessment; hỗ trợ structure rõ nhưng không bắt buộc.
- `assessment_question_assignments` — Câu tĩnh được đưa trực tiếp vào Assessment; thường luôn xuất hiện.
- `assessment_blueprints` — Ma trận chọn câu tự động cho Assessment.
- `assessment_blueprint_rules` — Một dòng điều kiện ma trận: lesson/difficulty/type/count/points.
- `assessment_question_pool` — Pool candidate đã materialize/curate để randomize ổn định; ngăn pool tự thay đổi âm thầm sau first start.
### Attempt

- `assessment_attempts` — Một lượt làm bài cụ thể của Student, chứa timer authoritative, lease tab, submit idempotency và lifecycle.
- `attempt_questions` — Snapshot đầy đủ của câu mà Student thực sự thấy; không đổi khi QuestionRevision tương lai thay đổi.
- `attempt_choice_snapshots` — Snapshot lựa chọn đúng thứ tự Student thấy, không lưu is_correct.
- `attempt_answers` — Trạng thái answer hiện hành của từng AttemptQuestion; source of truth để resume nhanh.
- `attempt_answer_choices` — Lựa chọn hiện hành cho câu choice; junction AttemptAnswer ↔ AttemptChoiceSnapshot.
- `attempt_answer_events` — Log chi tiết từng thay đổi answer đã gửi/được chấp nhận, phục vụ resume/debug và retention 30 ngày.
- `attempt_question_grades` — Điểm hiện hành của từng AttemptQuestion, gồm auto/manual/full-credit correction.
- `attempt_question_grade_history` — Append-only lịch sử thay đổi điểm từng câu.
- `assessment_results` — Kết quả hiện hành của một Attempt; final score pending nếu còn Essay chưa chấm.
- `assessment_result_history` — Append-only lịch sử điểm tổng cũ/mới để Student xem lý do thay đổi.
- `question_corrections` — Business event khi Question đã dùng được chỉnh; phân biệt answer-only và content/choices để worker áp dụng policy đúng.
- `regrade_jobs` — Job chấm lại lớn, resumable/idempotent cho một correction.
- `regrade_items` — Per-attempt progress/idempotency cho regrade job.
### Files

- `file_blobs` — Đại diện file vật lý deduplicated theo SHA-256; nhiều logical assets/revisions có thể dùng chung.
- `file_assets` — Logical file identity trong LMS; lifecycle độc lập với blob vật lý, hỗ trợ replacement/recovery.
- `file_revisions` — Một lần upload/replacement của FileAsset; luôn quarantine trước khi active.
- `file_scan_results` — Kết quả từng bước validation/malware/parser security cho FileRevision.
- `lesson_resources` — Liên kết Lesson với logical FileAsset; quyền truy cập đi qua Lesson/Course.
- `question_revision_resources` — Ảnh/tệp đính kèm QuestionRevision, đặc biệt image extracted từ DOCX.
- `document_import_jobs` — Import DOCX/PDF → draft Assessment với confidence/review; không auto publish.
- `import_questions` — Intermediate parsed question record, chưa là Question Bank cho tới Instructor approve.
- `import_duplicate_candidates` — Cảnh báo duplicate/near-duplicate trong import hoặc Question Bank; không auto merge.
- `import_question_resources` — Ảnh extracted gắn với parsed question trước approval.
### Ai

- `ai_conversations` — Phiên chat ngắn hạn; raw conversation tự xóa sau 5 phút inactivity.
- `ai_messages` — Raw user/assistant messages tạm thời trong conversation 5 phút.
- `ai_requests` — Metadata mỗi AI/backend routing request; giữ usage/security mà không cần raw prompt lâu dài.
- `ai_generated_question_drafts` — Draft câu hỏi do AI tạo; không vào Question Bank trước Instructor review.
- `knowledge_documents` — Logical source eligible for RAG metadata; authorization remains LMS source entity, not vector index.
- `knowledge_versions` — Process/activation state cho một version RAG; old version chỉ dùng nếu still valid/authorized.
- `knowledge_chunks` — Metadata chunk; embedding/vector payload nằm vector store riêng để không phụ thuộc SQL Server vector feature.
- `ai_source_usages` — Records source version/chunk metadata used by an AI answer/request without retaining raw conversation.
### Notification

- `notification_events` — Business event fan-out source for in-app notification/email; dedupe retries via event_key.
- `notifications` — In-app notification per recipient với read/unread và retention.
- `notification_preferences` — User preferences cho optional email categories; mandatory security email không disable.
- `email_deliveries` — Outbox/retry record cho email; primary business transaction không rollback do external send fail.
- `audit_events` — Append-only authoritative audit cho hành động Admin/Instructor quan trọng và score/security-sensitive actions.
### Operations

- `background_jobs` — Generic persistence cho queue/retry common mechanics; complex domain progress stays in regrade/import/version tables.
- `system_alerts` — Admin-facing alerts for suspicious/operational conditions.
- `backup_runs` — Metadata của backup tự động hằng ngày/manual và restore drills; không chứa backup bytes.
- `grade_exports` — Sensitive CSV/Excel export request/file lifecycle với giới hạn kích thước và expiry.
- `analytics_snapshots` — Derived/cache metrics cho Dashboard; source of truth vẫn normalized learning/assessment data.
- `system_health_snapshots` — Short-retention health metadata cho Admin Dashboard (DB/worker/ClamAV/Gemini/storage).

## 3. Relationship summary

- User N-N Role through `user_roles`.
- User 1-N Course as current owner, but Course owner may be NULL.
- Course N-N Course through `course_prerequisites`.
- Course 1-N Lesson.
- User N-N Course logically through `enrollments`; `enrollment_periods` segment lifecycle beneath one logical relationship.
- EnrollmentPeriod 1-N LessonProgress and AssessmentAttempt.
- Course 1-N Question; optional Lesson 1-N Question.
- Question 1-N QuestionRevision; Revision 1-N Choice / AcceptedAnswer.
- Course 1-N Assessment.
- Assessment N-N Question through static assignments and pool candidates.
- Assessment 1-N Attempt.
- Attempt 1-N AttemptQuestion; AttemptQuestion 1-N ChoiceSnapshot; AttemptQuestion 1-1 current Answer and current Grade.
- Correction 1-1 logical RegradeJob; RegradeJob 1-N RegradeItem.
- FileBlob 1-N FileRevision; FileAsset 1-N FileRevision; Lesson/QuestionRevision references FileAsset.
- Course/Lesson source 1-N KnowledgeDocument/Version/Chunk.
- AIRequest N-N source chunks through `ai_source_usages`.
- NotificationEvent 1-N Notifications/EmailDeliveries.
- BackgroundJob can be referenced by complex domain jobs, but business state remains in domain tables.

## 4. Source of truth classification

### Source-of-truth tables

- `users`, roles and auth grants;
- `courses`, `lessons`, prerequisites and completion rules;
- `enrollments`, `enrollment_periods`, `lesson_progress`, completion summaries;
- `questions`, `question_revisions`, revision answer structures;
- `assessments` and structure tables;
- `assessment_attempts`, attempt snapshots, current answers;
- current grades/results plus their histories;
- file assets/revisions and scan result;
- knowledge source/version activation metadata;
- notifications/audit/business delivery state.

### Immutable snapshots

- `attempt_questions`;
- `attempt_choice_snapshots`;
- grade/result history rows;
- AuditEvent;
- EnrollmentEvent.

### Short-retention detail

- `attempt_answer_events`;
- raw `ai_messages`;
- import diagnostics/draft data after promotion;
- health snapshots.

### Derived/cache

- `enrollments.current_progress_percent`;
- Question usage counters;
- `analytics_snapshots`;
- file blob reference count;
- health snapshots.

## 5. Domain rules that are intentionally not represented by a separate table

- Role hierarchy: enforced by service on `user_roles`; no generic permission/EAV table is needed in MVP.
- Rate limiting: runtime Redis/in-memory limiter is preferable; SQL only persists abuse/security events.
- Recommendation result: calculated by backend rules on current progress/prerequisites; no durable recommendation table is required unless product later needs history.
- Shared AI response cache: prefer short-lived Redis/in-memory cache; do not persist personalized responses in SQL.
- Live open/closed Assessment state: derived from `status`, `open_at`, `close_at` and server time, avoiding redundant mutable state.
