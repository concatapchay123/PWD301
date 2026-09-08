# Acceptance Criteria

## AC-AUTH-001
Given a valid active User, when web login succeeds, then session identifier rotates, Flask-Login identity is established and no JWT is stored in website localStorage.

## AC-AUTH-002
Given a suspended User with active session/JWT, when suspension commits, then subsequent web/API requests are rejected and revocation/audit/notification exist.

## AC-COURSE-001
Given Course A is an active prerequisite of B, when archive/delete A is requested, then mutation is rejected until dependency is resolved.

## AC-ENROLL-001
Given one remaining Course seat and two concurrent eligible enroll requests, when both execute, then at most one new active enrollment period succeeds.

## AC-ENROLL-002
Given Student leaves and re-enrolls within 30 days, then active learning restarts from beginning while prior completion summary remains unchanged.

## AC-RET-001
Given no rejoin for >30 days, cleanup may purge detailed period data, future regrade excludes that period, and prerequisite/completion summary remains.

## AC-LESSON-001
Given lesson completion already true, when lessons reorder or content is materially rewritten, then completion is not cleared.

## AC-QREV-001
Given a Question has been used, when Instructor makes important edit, then a new QuestionRevision is created and old exposed revision remains readable to historical Attempt snapshot.

## AC-ASSESS-001
Given Assessment is published, when timing edit is attempted, then DB/service rejects and original timing remains.

## AC-ASSESS-002
Given first Student has started, when question add/remove or assigned-points change is attempted, then mutation is rejected.

## AC-ATTEMPT-001
Given eligible Student starts Assessment, then exact selected revisions/choices/order/points are persisted once and resume returns identical snapshot.

## AC-ATTEMPT-002
Given tab A owns valid lease, when tab B tries to save, then request is rejected and answer remains unchanged.

## AC-ATTEMPT-003
Given tab A crashes and lease expires, when tab B takes over, then same Attempt/snapshot/answers/deadline continue.

## AC-AUTOSAVE-001
Given newer sequence already saved, when older offline change arrives, then older event cannot overwrite current answer.

## AC-TIMER-001
Given server deadline passed, when an unsent answer arrives, then it is rejected/not counted even if client shows earlier edit time.

## AC-SUBMIT-001
Given two concurrent submit requests with same idempotency semantics, then exactly one logical result exists and both callers observe that result.

## AC-GRADE-001
Given Essay remains ungraded, final result stays pending; after valid manual grade all required grading can finalize.

## AC-REGRADE-001
Given correct-answer-only correction, eligible retained submitted attempts are regraded, old/new history persists and changed Students are notified.

## AC-REGRADE-002
Given content/choice correction after prior starts, historical snapshots stay unchanged and affected earlier attempts receive full-credit correction policy.

## AC-FILE-001
Given scanner unavailable or malware result not PASS, FileRevision cannot become active/downloadable by Student.

## AC-FILE-002
Given identical bytes uploaded twice, logical assets may differ while one physical blob is reused without bypassing security state.

## AC-IMPORT-001
Given ambiguous imported question/no answer key, it remains review-required/no official answer until Instructor explicitly confirms input or AI suggestion.

## AC-AI-001
Given Student asks AI about unauthorized/draft/archived content, retrieval returns no protected chunks and answer does not reveal detailed content.

## AC-AI-002
Given AI conversation inactive for >5 minutes, raw messages/conversation content are purged while permitted minimal security metadata may remain.

## AC-NOTIF-001
Given email provider fails after business commit, primary action remains committed and delivery retries without duplicate logical notification.

## AC-AUDIT-001
Given sensitive Admin mutation requires audit and audit insert fails, the business mutation is rolled back.

## AC-ADMIN-001
Given Admin edits Instructor-owned content, reason is required, AuditEvent exists and Instructor notification is created.

## AC-BACKUP-001
Given restore request without reauth/phrase/reason, restore is refused; no automatic restore overwrites live DB.
