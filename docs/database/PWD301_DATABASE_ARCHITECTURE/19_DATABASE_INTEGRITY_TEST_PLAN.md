# 19 — DATABASE INTEGRITY TEST PLAN

> Mục tiêu: chứng minh schema + service transaction + worker + permission layer bảo toàn dữ liệu trước lỗi nghiệp vụ, retry, race condition, retention và thao tác phá hoại.
>
> Database engine mục tiêu: **Microsoft SQL Server**. ORM/migration mục tiêu: Flask-SQLAlchemy + Alembic/Flask-Migrate.

---

## 1. Phạm vi và nguyên tắc

Test plan này không chỉ kiểm tra CRUD. Mỗi test quan trọng phải chứng minh ít nhất một trong các thuộc tính:

- **Correctness** — dữ liệu cuối cùng đúng theo business rule.
- **Historical integrity** — không rewrite những gì Student thực sự thấy/chọn.
- **Idempotency** — retry không tạo duplicate hoặc cộng/trừ điểm hai lần.
- **Concurrency safety** — hai request đồng thời không phá invariant.
- **Authorization support** — schema có đủ ownership/relationship để service kiểm tra object-level permission.
- **Retention safety** — cleanup không phá prerequisite, summary, audit hoặc dữ liệu còn phải chấm lại.
- **Recoverability** — soft-delete/recovery hoạt động đúng.
- **Fail closed** — lỗi audit/file scan/timing không vô tình mở quyền hoặc phát hành dữ liệu chưa an toàn.

### 1.1 Môi trường test

Tối thiểu có:

1. SQL Server test container/database riêng.
2. Migration chạy từ database rỗng đến head.
3. Seed role `STUDENT`, `INSTRUCTOR`, `ADMIN`.
4. Test service sử dụng transaction thật, không mock database cho integration test.
5. Worker test có thể chạy synchronous/test mode nhưng phải dùng cùng idempotency logic production.
6. Clock/time provider có thể cố định thời gian trong test để kiểm tra deadline.

### 1.2 Quy ước mức test

| Mức | Ý nghĩa |
|---|---|
| `DB` | Constraint/index/trigger/FK trực tiếp trên SQL Server |
| `MODEL` | SQLAlchemy mapping và validation cơ bản |
| `SERVICE` | Nghiệp vụ + transaction boundary |
| `CONCURRENCY` | Hai hoặc nhiều transaction song song |
| `WORKER` | Job retry/resume/idempotency |
| `AUTHZ` | Permission/object ownership |
| `RETENTION` | Cleanup/purge/archive/anonymization |
| `MIGRATION` | Upgrade/downgrade/constraint rollout |

---

## 2. Identity / Authentication / Role

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| AUTH-T001 | DB | Tạo hai User cùng normalized email | Unique constraint từ chối record thứ hai |
| AUTH-T002 | SERVICE | Đổi email sang email chưa verify | `users.email` cũ vẫn active; token pending giữ email mới |
| AUTH-T003 | SERVICE | Verify email token hợp lệ một lần | Email đổi atomically; token consumed; audit/notification nếu policy yêu cầu |
| AUTH-T004 | SERVICE | Reuse email verification token | Bị từ chối; không đổi dữ liệu |
| AUTH-T005 | DB/SERVICE | Gán role `INSTRUCTOR` nhưng thiếu `STUDENT` | Service tự gán bộ role hợp lệ hoặc từ chối; không để tổ hợp role bất hợp lệ |
| AUTH-T006 | DB/SERVICE | Gán `ADMIN` | Kết quả cuối phải có `ADMIN+INSTRUCTOR+STUDENT` |
| AUTH-T007 | SERVICE | Student → Instructor | Cùng `users.id`; Enrollment/Attempt cũ không đổi owner |
| AUTH-T008 | SERVICE | Suspend User đang login web | Mọi `auth_sessions` active bị revoke/invalid; request tiếp theo bị block |
| AUTH-T009 | SERVICE | Suspend User còn JWT | Token cũ bị invalid theo auth/token version hoặc revocation grant |
| AUTH-T010 | SERVICE | Unsuspend User | Không tự phục hồi session/token cũ; user phải authenticate lại |
| AUTH-T011 | AUTHZ | Student gọi API Admin | 403; không mutation |
| AUTH-T012 | AUTHZ | Instructor sửa Course của Instructor khác | 403; object ownership được kiểm tra |
| AUTH-T013 | SERVICE | Sensitive Admin action thiếu re-auth | Bị từ chối |
| AUTH-T014 | SERVICE | Re-auth đúng nhưng confirmation phrase sai | Bị từ chối |
| AUTH-T015 | SERVICE | Re-auth + phrase đúng nhưng thiếu reason | Bị từ chối |
| AUTH-T016 | SERVICE | Audit insert fail trong sensitive action | Toàn transaction rollback; target không đổi |

---

## 3. Course / Lesson / Enrollment / Prerequisite

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| COURSE-T001 | DB | Trùng `course_code` | Reject |
| COURSE-T002 | DB | Trùng Course title theo policy global unique | Reject |
| COURSE-T003 | SERVICE | Revoke Instructor owner | Course tồn tại; owner có thể `NULL`; Student access không tự mất |
| COURSE-T004 | SERVICE | Reassign Course | Owner mới có quyền; owner cũ mất quyền current student data; audit có history |
| COURSE-T005 | DB | Prerequisite A → A | Reject |
| COURSE-T006 | SERVICE | Tạo A→B, B→C, C→A | Detect cycle trước commit và reject |
| COURSE-T007 | SERVICE | Archive Course A đang prerequisite của active Course B | Block và báo dependency |
| COURSE-T008 | CONCURRENCY | Hai Student cùng chiếm slot cuối của Course capacity | Chỉ một enrollment thành công |
| COURSE-T009 | DB | Hai active Enrollment logic cho cùng User-Course | Unique/invariant ngăn duplicate |
| COURSE-T010 | SERVICE | Student chưa đạt prerequisite enroll | Reject |
| COURSE-T011 | SERVICE | Student đã có completion summary rồi re-enroll prerequisite course | Eligibility cũ vẫn được giữ |
| COURSE-T012 | SERVICE | Leave Course | Enrollment chuyển lifecycle; tạo event/period retention; không hard-delete ngay |
| COURSE-T013 | SERVICE | Re-enroll trong 30 ngày | Cùng logical Enrollment, period/lifecycle mới; progress active reset từ đầu |
| COURSE-T014 | RETENTION | Không rejoin >30 ngày | Detailed learning data của period được purge theo policy; compact summary còn |
| COURSE-T015 | RETENTION | Regrade job chạy sau period đã purge | Period đã purge không được chọn làm regrade target |
| COURSE-T016 | SERVICE | Student leave khi có active AssessmentAttempt | Áp dụng safe assumption trong ADR: block leave tới khi attempt terminal; không orphan attempt |
| COURSE-T017 | SERVICE | Instructor thêm Lesson mới | Existing enrollment baseline không tụt progress; Lesson mới optional/Xem thêm theo effective rule |
| COURSE-T018 | SERVICE | Student đã complete Course, thêm Lesson mới | CourseCompletionSummary vẫn completed |
| COURSE-T019 | SERVICE | Reorder Lessons | Position mới áp dụng; LessonProgress completed không reset |
| COURSE-T020 | SERVICE | Material rewrite Lesson | Student đã completed vẫn completed |
| COURSE-T021 | SERVICE | Delete Lesson đã có history | Hidden/tombstone; historical linkage còn |
| COURSE-T022 | SERVICE | Delete unused Lesson sau recovery | Hard delete allowed khi không dependent history |

---

## 4. Question Bank / Revision

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| QBANK-T001 | SERVICE | Sửa Question chưa từng dùng | Có thể update in-place, không bắt buộc tạo revision mới |
| QBANK-T002 | SERVICE | Sửa Question đã dùng | Tạo `question_revisions` mới; revision cũ không mutate |
| QBANK-T003 | DB | Sửa text trực tiếp của revision đã từng dùng/shown | Trigger/guard từ chối |
| QBANK-T004 | DB | Sửa choice thuộc revision đã used | Reject; phải revision mới |
| QBANK-T005 | DB | Sửa accepted short answer của used revision | Reject; phải revision mới |
| QBANK-T006 | DB/SERVICE | Đổi question type sau khi có Student answer | Reject |
| QBANK-T007 | SERVICE | Duplicate Question | Tạo Question identity mới độc lập |
| QBANK-T008 | SERVICE | Delete unused Question | Trash/recovery rồi hard delete nếu không reference |
| QBANK-T009 | SERVICE | Delete Question đã dùng nhưng chưa attempt | Chỉ hard-delete nếu gỡ mọi mapping và không remaining reference |
| QBANK-T010 | SERVICE | Delete Question đã có Student answer | Hide/tombstone Question; revision dùng grading retained |
| QBANK-T011 | RETENTION | Cleanup unused draft revision | Chỉ xóa revision chưa từng shown/graded và không source lineage cần thiết |
| QBANK-T012 | DB | MC choice correct set rỗng | Publish/preflight block |
| QBANK-T013 | SERVICE | MC answer chọn thiếu/nhầm choice | 0 điểm — exact set match only |
| QBANK-T014 | SERVICE | Short answer ` Flask ` vs accepted `flask` default mode | Match sau trim/case fold |
| QBANK-T015 | SERVICE | Short answer exact mode khác case | Không match |

---

## 5. Assessment Structure / Publish

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| ASSESS-T001 | SERVICE | Publish Assessment không có câu | Block |
| ASSESS-T002 | SERVICE | Publish có MC thiếu correct answer | Block |
| ASSESS-T003 | SERVICE | Publish blueprint thiếu candidate | Block + shortage diagnostics |
| ASSESS-T004 | SERVICE | Publish có AI/import draft chưa approved | Block |
| ASSESS-T005 | SERVICE | Publish với `open_at >= close_at` | Block |
| ASSESS-T006 | DB/TRIGGER | Sửa `open_at/close_at/time_limit` sau publish | Reject |
| ASSESS-T007 | SERVICE | Chưa có Student start, sửa structure | Allowed theo lifecycle/preflight |
| ASSESS-T008 | DB/TRIGGER | Sau first start, thêm/xóa assignment/pool/fixed question | Reject |
| ASSESS-T009 | DB/TRIGGER | Sau first start, đổi points mapping | Reject |
| ASSESS-T010 | SERVICE | Question Bank có revision mới trước Student start | Attempt mới resolve latest valid revision |
| ASSESS-T011 | SERVICE | Student đã start trước revision mới | AttemptQuestion snapshot không đổi |
| ASSESS-T012 | SERVICE | Cùng Assessment random 30/100 cho 2 Student | Mỗi attempt lưu exact selected set + order |
| ASSESS-T013 | SERVICE | Shuffle choices | Snapshot order stable qua reload |
| ASSESS-T014 | SERVICE | Mandatory fixed question | Có trong mọi generated attempt |
| ASSESS-T015 | SERVICE | Close 10:00, start 09:40, limit 60m | `deadline_at = 10:00` |
| ASSESS-T016 | SERVICE | Attempt limit reached | Start mới reject |
| ASSESS-T017 | SERVICE | Cancel active Assessment | Attempts/history retained, in-progress → cancellation terminal state |

---

## 6. AssessmentAttempt / Autosave / Lease / Submit

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| ATTEMPT-T001 | CONCURRENCY | Hai request `start` cùng lúc cùng Student+Assessment | Chỉ một attempt number được tạo; request kia nhận existing/consistent result |
| ATTEMPT-T002 | SERVICE | Reload trang | Không regenerate questions/order |
| ATTEMPT-T003 | CONCURRENCY | Tab A và B acquire editing lease đồng thời | Chỉ một thắng |
| ATTEMPT-T004 | SERVICE | Tab B khi A lease còn valid | Block editing + warning |
| ATTEMPT-T005 | SERVICE | A crash, lease hết hạn, B takeover | B nhận lease mới trên cùng attempt |
| ATTEMPT-T006 | SERVICE | Old tab A gửi heartbeat sau B takeover | Reject stale lease token |
| ATTEMPT-T007 | SERVICE | MC answer change | Current answer update + answer event nếu policy bật |
| ATTEMPT-T008 | SERVICE | Same autosave request retry | Không duplicate semantic effect; sequence/idempotency xử lý an toàn |
| ATTEMPT-T009 | SERVICE | Offline old answer đến sau newer answer | Không overwrite newer server version |
| ATTEMPT-T010 | CONCURRENCY | Autosave và submit đồng thời | Final state có answer hợp lệ trước submit/deadline; post-submit save reject |
| ATTEMPT-T011 | SERVICE | Answer tới sau `deadline_at` | Không được tính dù client timestamp trước deadline |
| ATTEMPT-T012 | WORKER/SERVICE | Student offline tới sau deadline | Server finalize bằng answers đã ACK trước deadline |
| ATTEMPT-T013 | CONCURRENCY | Submit hai request cùng lúc | Một terminal result; request khác trả cùng result |
| ATTEMPT-T014 | SERVICE | Retry submit sau network timeout | Trả existing result, không grade lần 2 |
| ATTEMPT-T015 | SERVICE | Student sửa clock máy | Không thay deadline server |
| ATTEMPT-T016 | SERVICE | Assessment có essay | Result `PENDING_GRADING` cho tới manual grade đủ |
| ATTEMPT-T017 | SERVICE | Manual essay grade revision | Old/new grade history + actor/reason/time |
| ATTEMPT-T018 | RETENTION | Autosave events hết retention | Current/final answer/history bắt buộc theo period policy được giữ hoặc purge đúng rule |

---

## 7. Question Correction / Full Credit / Regrading

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| REGRADE-T001 | SERVICE | Chỉ correct answer thay đổi | Tạo correction type ANSWER_ONLY + regrade job |
| REGRADE-T002 | WORKER | Regrade 1.000 attempts | Job chạy background, progress track |
| REGRADE-T003 | WORKER | Worker crash ở item 400 | Resume từ pending; 1–399 không double-apply |
| REGRADE-T004 | SERVICE | Regrade đổi tổng score | Current result đổi; result history lưu old/new/reason/source |
| REGRADE-T005 | SERVICE | Score không đổi | Không gửi notification “đổi điểm” nếu không có delta; vẫn có technical regrade result nếu cần |
| REGRADE-T006 | SERVICE | Question text/choices thay đổi lúc Student đang làm | Frozen snapshot giữ nguyên; question grade policy full-credit theo correction cutoff |
| REGRADE-T007 | SERVICE | Question text/choices thay đổi sau Student submit | Eligible submitted attempt được full credit câu đó |
| REGRADE-T008 | SERVICE | Student start sau correction save | Nhận revision mới và chấm bình thường, không hưởng blanket full-credit cũ |
| REGRADE-T009 | WORKER | Hai correction liên tiếp | Job 2 dùng correction revision/version ordering; không overwrite bằng kết quả stale job 1 |
| REGRADE-T010 | CONCURRENCY | Correction mới trong khi old regrade running | Conditional version check / stale detection; final score phản ánh correction mới nhất |
| REGRADE-T011 | RETENTION | Enrollment period purged trước job selection | Không nằm trong target set |
| REGRADE-T012 | RETENTION/WORKER | Purge cố chạy khi regrade item còn pending | Purge phải skip/defer period hoặc job target phải atomically exclude trước purge |

---

## 8. File / Blob / Quarantine / Replacement

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| FILE-T001 | SERVICE | Upload `.docm`/`.pptm` | Reject trước publish/use |
| FILE-T002 | SERVICE | Client MIME giả | Detected MIME/signature quyết định policy |
| FILE-T003 | SERVICE | Image >10MB / PDF-DOCX >50MB / PPTX >100MB / video >=1GB | Reject theo configured limits |
| FILE-T004 | WORKER | ClamAV unavailable | Revision vẫn blocked/pending; không SAFE |
| FILE-T005 | WORKER | Malware detected | REJECTED + security event; Student không access |
| FILE-T006 | WORKER | DOCX/PPTX decompression bomb | Abort theo uncompressed/resource/time limits |
| FILE-T007 | DB | Hai `ACTIVE` revisions cho cùng FileAsset | Filtered unique index reject |
| FILE-T008 | SERVICE | Hai upload content hash giống nhau | Có thể dùng chung `file_blobs`; logical authorization độc lập |
| FILE-T009 | SERVICE | Delete một logical ref của shared blob | Blob không xóa nếu còn ref khác |
| FILE-T010 | SERVICE | Replace file bằng revision mới chưa scan xong | Old revision vẫn current/active |
| FILE-T011 | SERVICE | Replacement scan fail | Old revision tiếp tục active; new rejected |
| FILE-T012 | SERVICE | Replacement scan pass | Current pointer switch atomically; old → recovery |
| FILE-T013 | RETENTION | Recovery hết hạn nhưng blob còn referenced | Không physical delete |
| FILE-T014 | AUTHZ | Student biết storage key nhưng không authorized course | Download route deny; storage path không public |
| FILE-T015 | SERVICE | Low disk critical | Upload new blocked; system alert generated |

---

## 9. DOCX/PDF Import / AI Question Draft

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| IMPORT-T001 | WORKER | 100 questions, 92 confident, 8 ambiguous | 92 draft-ready; 8 flagged review |
| IMPORT-T002 | SERVICE | No answer key | Official answer remains unknown |
| IMPORT-T003 | SERVICE | AI suggest answer | Suggestion not official until Instructor confirms |
| IMPORT-T004 | SERVICE | Instructor confirms suggestion | Official answer created; AI provenance retained |
| IMPORT-T005 | SERVICE | Broken extracted image | Related import question `review_required`; not silently ready |
| IMPORT-T006 | SERVICE | Duplicate within import | Candidate warning only; no auto-merge |
| IMPORT-T007 | SERVICE | Near duplicate existing Question Bank | Warning only; Instructor decides |
| IMPORT-T008 | SERVICE | Import completes | Creates draft assessment/question drafts, never auto-publish |
| IMPORT-T009 | WORKER | Parser timeout | Job fail safely; no partially active data |
| IMPORT-T010 | CONCURRENCY | Course owner changed while import running | Finalization re-checks current permission/ownership before attaching/publishing |

---

## 10. AI / RAG / Chat retention

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| AI-T001 | AUTHZ | Student asks content from inaccessible Course | May recommend course metadata; no detailed chunks retrieved |
| AI-T002 | AUTHZ | Draft/review Course content exists in index candidate | Retrieval filter excludes it |
| AI-T003 | AUTHZ | Student requests peer score | Deny; only own data |
| AI-T004 | SERVICE | Backend-answerable progress query | No Gemini call required |
| AI-T005 | SERVICE | Gemini unavailable | Backend-only feature still returns |
| AI-T006 | SERVICE | Retrieved document contains prompt-injection text | Treated as data; no authorization/tool elevation |
| AI-T007 | RETENTION | Last user message >5 minutes | Raw `ai_messages`/conversation content cleanup; minimal security event may remain |
| AI-T008 | RETENTION | User sends message at minute 4 | Inactivity expiry reset from latest user message |
| AI-T009 | SERVICE | Personalized response cache request | Not shared/reused across users |
| AI-T010 | SERVICE | Generic nonpersonalized cache | May reuse only within safe key/version policy |
| AI-T011 | SERVICE | Source document updated | Old searchable version invalidated; new not active until processing succeeds |
| AI-T012 | SERVICE | Source document deleted while indexing | Retrieval disabled immediately; pending/new version cannot activate |
| AI-T013 | SERVICE | Course archived | Knowledge document excluded even if old ACTIVE vector data physically exists |
| AI-T014 | DB | Two ACTIVE knowledge versions same document | Filtered unique index rejects |
| AI-T015 | SERVICE | New version processing fails | Old version only remains usable if source still authorized/valid |
| AI-T016 | SERVICE | AI answer produced | Source version/chunk provenance recorded without storing unnecessary private prompt forever |

---

## 11. Notification / Email / Audit

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| NOTIF-T001 | SERVICE | Score changed by regrade | In-app notification created with reason/source |
| NOTIF-T002 | WORKER | Email send timeout then retry | One logical delivery; retry count increments; no duplicate business action |
| NOTIF-T003 | DB/SERVICE | User tries disable mandatory SECURITY email | Reject/force enabled |
| NOTIF-T004 | SERVICE | Email failure after Instructor approval | Approval remains committed; delivery retry later |
| AUDIT-T001 | DB | `UPDATE audit_events` | Trigger/permission rejects |
| AUDIT-T002 | DB | `DELETE audit_events` | Reject |
| AUDIT-T003 | SERVICE | Correct wrong audit fact | New corrective event; original remains |
| AUDIT-T004 | SERVICE | Admin edits Instructor content | reason required + audit + Instructor notification |
| AUDIT-T005 | SERVICE | Admin detailed Student view without reason | Reject/require reason per policy |
| AUDIT-T006 | SECURITY | Attempt to log password/JWT/raw secret | Sanitization/redaction test ensures not persisted |
| AUDIT-T007 | CONCURRENCY | Business mutation + audit in same transaction fails at audit insert | Business mutation rollback |

---

## 12. Delete / Restore / Anonymization

| ID | Mức | Scenario | Kết quả bắt buộc |
|---|---|---|---|
| DELETE-T001 | SERVICE | Delete Course with Student history | Hidden/trash/archive semantics; attempts/results not cascade-deleted |
| DELETE-T002 | SERVICE | Delete unused Course after recovery | Hard delete allowed if no protected dependency |
| DELETE-T003 | SERVICE | Restore within recovery | Record/linkage restored consistently |
| DELETE-T004 | SERVICE | Restore document while Course archived | File may restore physically/logically but RAG remains non-retrievable while Course archived |
| DELETE-T005 | SERVICE | User delete request | First deactivate; PII anonymize only according policy; history FK remains valid |
| DELETE-T006 | RETENTION | Audit old | Never delete; may archive storage |
| DELETE-T007 | DB | Parent delete with historical child | `NO ACTION`/service guard prevents cascade loss |
| DELETE-T008 | SERVICE | Hard-delete Question revision that was graded | Reject |

---

## 13. Migration tests

| ID | Scenario | Kết quả bắt buộc |
|---|---|---|
| MIG-T001 | Fresh `alembic upgrade head` | Tạo toàn schema không lỗi |
| MIG-T002 | Run migrations twice | Lần hai no-op, không duplicate object |
| MIG-T003 | Seed roles twice | Idempotent |
| MIG-T004 | Create data then upgrade new nullable column | Data cũ giữ nguyên |
| MIG-T005 | Backfill → enforce NOT NULL | Constraint chỉ bật sau khi data hợp lệ |
| MIG-T006 | Add large index | Có kế hoạch maintenance/lock phù hợp; test staging |
| MIG-T007 | Trigger creation order | Bảng/index tồn tại trước trigger |
| MIG-T008 | Cross-domain FK script | Không circular bootstrap failure |
| MIG-T009 | Downgrade destructive migration | Chỉ chạy trong dev/test; production rollback dùng forward-fix/backup plan |

---

## 14. Performance / query plan tests

Các query sau phải được đo trên seed dữ liệu đủ lớn (ví dụ 10k Question, 100k Attempt/Answer, 1M audit/event rows nếu có thể generate):

1. Course Catalog search/filter/pagination.
2. Question Bank multi-filter + search + usage.
3. Enrollment list theo Course/status.
4. Student attempt list.
5. Pending essay grading.
6. Notification unread list.
7. Audit list theo time/actor/target/action.
8. Regrade target lookup theo `question_id/revision/correction cutoff`.
9. Retention scan `left/retention_until`.
10. File recovery cleanup.
11. Knowledge indexing pending queue.
12. Instructor dashboard aggregate/cache read.

Acceptance guideline cho project:

- không scan toàn bộ bảng do thiếu index ở query nóng;
- pagination phải server-side;
- query plan phải dùng index hợp lý khi selectivity đủ;
- tránh N+1 ở ORM;
- write path autosave không bị quá nhiều secondary index không cần thiết.

---

## 15. Race-condition harness bắt buộc

Dùng ít nhất 2 connection/transaction độc lập và barrier để ép interleaving:

### RACE-001 — Enrollment capacity last slot

```text
T1 read capacity available
T2 read capacity available
T1 enroll
T2 enroll
COMMIT both attempt
```

Expected: chỉ một thành công.

### RACE-002 — Attempt lease

```text
Tab A acquire
Tab B acquire concurrently
```

Expected: đúng một owner token.

### RACE-003 — Double submit

```text
POST submit A
POST submit B
```

Expected: một `assessment_results` logical result và cùng response semantic.

### RACE-004 — Concurrent Question edit

Hai editor gửi cùng `row_version`; transaction đầu commit, transaction sau nhận stale conflict.

### RACE-005 — Correction vs regrade

Correction 2 được commit khi Job correction 1 đang chạy; Job 1 không được ghi score dựa trên version stale sau Job 2.

### RACE-006 — File activation

Hai worker cố activate hai file revisions cùng asset; filtered unique index + transaction chỉ cho một ACTIVE.

### RACE-007 — Knowledge activation

Hai index jobs hoàn tất gần đồng thời; chỉ một ACTIVE version/document.

---

## 16. Data-integrity scenario checklist cuối

Mỗi scenario phải PASS trước production/demo candidate:

- [ ] Instructor sửa correct answer sau Student submit.
- [ ] Instructor sửa text/choices khi Student đang làm.
- [ ] Hai tab cùng mở attempt.
- [ ] Tab A crash, tab B takeover.
- [ ] Student offline tới sau deadline.
- [ ] Student retry submit.
- [ ] Instructor bị revoke role.
- [ ] Course mất owner.
- [ ] Student leave Course.
- [ ] Student rejoin trong 30 ngày nhưng restart từ đầu.
- [ ] Student không rejoin >30 ngày và detailed purge.
- [ ] Regrade sau detailed purge không chọn period đã purge.
- [ ] Question delete sau khi đã dùng.
- [ ] Assessment delete sau khi có attempts.
- [ ] User anonymize.
- [ ] File malware scan fail.
- [ ] File replacement scan fail.
- [ ] Course archived.
- [ ] RAG indexing đồng thời Course archive/delete.
- [ ] AI chat inactivity >5 phút.
- [ ] Admin edit Instructor Course.
- [ ] Audit insert fail trong sensitive action.
- [ ] Concurrent Instructor edits.
- [ ] Blueprint shortage.
- [ ] Timing edit attempt sau publish.
- [ ] Assessment add/remove question sau first start.
- [ ] Assessment points edit sau first start.
- [ ] Storage dedup shared blob delete.
- [ ] Account suspend giữa active attempt.
- [ ] Role revoke giữa active Instructor edit.

---

## 17. Exit criteria

Database integrity test suite được xem là đạt khi:

1. tất cả DB constraints/triggers quan trọng có negative test;
2. tất cả transaction pseudocode trong `16_CONCURRENCY_AND_TRANSACTIONS.md` có integration test tương ứng;
3. race-condition tests chạy lặp nhiều lần không tạo invariant violation;
4. worker retry test chứng minh idempotency;
5. retention test chứng minh không phá completion/prerequisite summary;
6. security test chứng minh soft-deleted/archived/unauthorized data không bị query nhầm;
7. migration fresh install PASS;
8. test report lưu cùng release candidate.
