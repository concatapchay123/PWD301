# Decision Inventory & Consistency Pass

## 1. Purpose

Tài liệu này là bước kiểm tra trước schema. Nó phân biệt:

- **CONFIRMED BUSINESS RULE**: quyết định đã được người dùng khóa trong 16 vòng Plan Mode + vòng cuối.
- **SUPERSEDED**: quyết định cũ đã được thay thế rõ ràng bởi quyết định mới.
- **DERIVED DATABASE DESIGN**: thiết kế DB cần thiết để thực thi rule, nhưng không phải business rule mới.
- **ASSUMPTION**: default an toàn cho phần Plan Mode chưa quyết định; được ghi thêm trong ADR.
- **RECOMMENDATION**: hướng triển khai nên dùng nhưng không làm thay đổi business behavior.

## 2. Confirmed decision inventory

### Identity / authentication

- Web/Jinja/AJAX dùng Flask-Login với session phía server; REST API dùng JWT.
- JWT không được lưu trong `localStorage`/`sessionStorage` của website.
- Email là login identifier duy nhất, unique; đổi email phải verify email mới trước.
- User có nhiều role theo đúng tổ hợp: `STUDENT`; `STUDENT+INSTRUCTOR`; `STUDENT+INSTRUCTOR+ADMIN`.
- Upgrade role dùng cùng User, giữ learning history.
- Suspend phải chặn ngay session/JWT hiện hành.
- Sensitive Admin action cần password re-authentication + typed confirmation phrase; destructive/high-risk action còn cần reason.
- Admin không impersonate User; chỉ có safe preview.

### Course / learning

- Course code unique và title unique toàn hệ thống.
- Course bình thường có một Instructor owner, nhưng có thể tạm `NULL` để Admin reassign.
- Prerequisite bắt buộc; cycle bị chặn.
- Course đang là prerequisite của active Course khác không được archive/delete trước khi giải quyết dependency.
- Course completion rule configurable.
- Lesson completion cần cả minimum time và evidence viewed most content.
- Lesson reorder áp dụng mọi người nhưng không xóa completion.
- Material lesson rewrite không bắt Student đã complete học lại.
- Lesson mới thêm không làm giảm progress Student đang học; với cohort hiện tại nó là `Xem thêm`.
- Student chỉ có một logical Enrollment cho Course; re-enroll dùng lại Enrollment nhưng mở learning period mới và restart từ đầu.
- Prior completed Course vẫn thỏa prerequisite khi Student học lại.
- Leave Course >30 ngày không rejoin: detailed learning data có thể purge; compact completion/prerequisite summary giữ.
- Period đã purge không tham gia future automatic regrading.

### Question Bank / correction

- Question thuộc đúng một Course; Lesson optional.
- Unused Question có thể edit in-place; used Question important edit tạo `QuestionRevision`.
- Choice và accepted answer thuộc revision.
- Revision từng Student thấy hoặc dùng grading giữ lâu dài.
- Sau khi có Student trả lời, question type không được đổi; muốn type khác phải tạo Question mới.
- Points thuộc Assessment-question relation, không thuộc Question.
- Multiple-choice exact selection: không partial credit.
- Short answer có nhiều accepted answers; mặc định trim + case-insensitive, có exact mode.
- Essay manual grade trong MVP.
- Duplicate Question tạo identity mới độc lập.
- Student chưa start luôn nhận latest valid QuestionRevision.
- Student đã start giữ snapshot cũ.
- Correct-answer-only change: automatic regrade eligible submitted attempts, giữ old/new score.
- Content/choices change: attempts đã start trước thời điểm Save được full credit câu đó; historical snapshot không rewrite.
- Submitted attempts trước content/choice change cũng được full credit theo rule đã khóa.

### Assessment / attempt

- Assessment type: practice/quiz/midterm/final/placement.
- Có open/close/time limit; close là hard boundary; server time authoritative.
- **Timing không được sửa sau Publish.**
- Attempt limit và scoring policy configurable.
- Có random subset, blueprint/matrix, fixed questions, shuffle question/choice.
- Score release và answer/explanation visibility configurable.
- Assessment có Essay thì final result pending đến manual grading xong.
- Manual grade có thể sửa nhưng phải giữ old/new/actor/time/reason.
- Practice có thể optional; Assessment có passing threshold.
- Cancel active Assessment không xóa attempts/history.
- **Sau Student đầu tiên start: không add/remove question, không đổi points.**
- Chỉ tab đầu tiên được edit; lease stale cho phép tab mới takeover cùng Attempt.
- Choice save ngay + periodic reconciliation; text answer debounce 1–2s.
- Offline browser giữ pending changes; server chỉ công nhận save thành công trước deadline.
- Time expiry server finalizes saved answers.
- Submit idempotent.
- Nếu Instructor sửa content/answer khi Student đang làm: Student vẫn thấy snapshot cũ; grading/correction policy mới áp dụng theo rule.

### Files / import

- Upload vào quarantine; Student không access trước toàn bộ security check.
- Malware scanner unavailable/error = fail-closed.
- `.docm/.pptm` và macro-enabled Office bị từ chối.
- Archive/Office/PDF parser có size/entry/ratio/time/memory/resource limits.
- Initial limits: image ~10MB; PDF 50MB; DOCX 50MB; PPTX 100MB; **video <1GB**.
- SHA-256 dedup physical file; nhiều logical refs dùng chung blob.
- Replacement chỉ active sau check; old version recovery ~30 ngày.
- Direct storage path private; download qua authorized app route.
- Course/Instructor quota; low disk cảnh báo rồi block upload.
- DOCX priority; scanned PDF OCR không thuộc MVP.
- Import tạo draft, confidence/diagnostics, ambiguous review.
- No answer key => chưa có official answer; AI chỉ gợi ý, Instructor xác nhận.
- AI-generated/imported question không vào Question Bank trước approval.
- Images extracted, scanned, reattached; broken image forces review.
- Duplicate chỉ flag, không auto merge.

### AI / RAG

- AI scope chỉ LMS; mixed prompt chỉ trả phần in-scope.
- Student AI chỉ lấy published content được authorized; inaccessible Course có thể biết tồn tại/recommend nhưng không đọc chi tiết.
- Draft/review và archived Course không được RAG retrieve.
- Student AI chỉ đọc dữ liệu của chính Student; Instructor/Admin theo permission.
- Gemini nhận minimum necessary data.
- Recommendation do backend rules tính; Gemini chỉ explain.
- Retrieved/uploaded docs luôn là untrusted data, không phải instruction.
- Evidence không đủ thì phải nói không đủ.
- Backend-computable query bypass Gemini; Gemini fail không làm core backend chết.
- AI chat raw content xóa sau 5 phút inactivity; user message reset timer; security metadata tối thiểu có thể giữ.
- Shared cache chỉ generic non-personalized; personalized response không reuse/shared cache.
- Content update invalidates old searchable version; new version active sau processing success.
- Delete source stops retrieval immediately.
- New published content auto indexing.
- Last valid old version chỉ dùng nếu vẫn authorized/valid.
- AI answer metadata ghi source version/revision.

### Notification / audit / operations

- In-app notifications + important email.
- Optional email preferences, security email mandatory.
- Email failure không rollback business action; retry + dedupe.
- Assessment reminders.
- Instructor chỉ xem Student ở current managed Course; reassignment mất current access.
- Answer change history không phải routine Instructor view.
- Admin aggregate rộng; individual detail requires reason.
- Score change history old/new/reason/actor/time; Student được thấy reason.
- Instructors có grade export cho own Course; file export sensitive/short-lived.
- Audit important records append-only; correction là event mới.
- Required audit failure blocks sensitive/destructive action.
- Daily automatic backup + manual backup; restore drill định kỳ.
- Service restart có thể tự động; DB restore luôn explicit Admin confirmation.
- Large lists server-side pagination/filter/sort.
- Heavy analytics/progress có cache/derived values nhưng source of truth normalized.
- Large regrade background, resumable/idempotent.
- Concurrent edits use optimistic concurrency.
- External/API/parser operations có timeout/resource limits.

## 3. Superseded decisions

### SUPERSEDED-001 — Published Assessment fully immutable

Old idea: published Assessment is completely immutable.

Final rule:
- timing immutable immediately after publish;
- structure and points immutable after first Student starts;
- Question identity mapping remains, but Student who has not started resolves the latest approved QuestionRevision;
- active/historical attempts preserve frozen snapshot;
- answer/content corrections follow regrade/full-credit rules.

Therefore schema **must not pin a fixed QuestionRevision on `assessment_question_assignments`**. The revision is resolved into `attempt_questions` at start.

### SUPERSEDED-002 — Hard delete used Question

Old preference allowed hard-delete of used Question.

Final rule: Question that a Student answered is removed from active bank but minimal Question + historical revisions required for grading/regrading/audit are retained.

### SUPERSEDED-003 — Keep all former enrollment attempts forever

General historical-integrity rules are narrowed by the later 30-day former-enrollment retention rule. After leave >30 days without rejoin, detailed Attempt/answers may be purged and those purged attempts are not future regrade targets. Compact completion/prerequisite summary survives.

### SUPERSEDED-004 — Video under ~2GB in handoff draft

The confirmed Plan Mode Round 6 limit is **video under 1GB**. Reference DDL/documentation uses the 1GB policy. The value remains configuration, not a SQL CHECK on file content format.

## 4. Reconciled rules

### Latest question vs frozen attempt

There is no conflict:
- Assessment maps to Question identity.
- Attempt start resolves `questions.current_revision_id`.
- Attempt stores rendered content/choice/order snapshot.
- Later answer-only correction can grade against a newer approved revision without rewriting the snapshot.
- Content/choice correction awards full credit to eligible attempts started before its effective time.

### Re-enrollment without “many Enrollment rows”

`enrollments` is one logical User-Course record. `enrollment_periods` are lifecycle/retention segments beneath it, not separate logical enrollments. This permits restart and 30-day purge without overwriting historical facts.

### New Lesson without Course snapshots

`lessons.required_for_periods_starting_at` marks when a Lesson becomes required. Existing periods started earlier treat it as optional “Xem thêm”; new periods after the effective time include it. No per-Student Course snapshot is needed.

## 5. Open issues

No business blocker remains for initial ERD. Unspecified technical choices are recorded as ADR/ASSUMPTION in `21_ASSUMPTIONS_AND_DECISIONS.md`.
