# Concurrency Control

| Operation | Race | Protection |
|---|---|---|
| Email uniqueness/change | two Users activate same normalized email | unique DB constraint + activation transaction |
| Course capacity | last seat concurrent enroll | serialize/lock capacity decision + active enrollment uniqueness |
| Lesson reorder | two stale order edits | ROWVERSION + transaction updating complete ordered set |
| Question edit | concurrent revision/edit | ROWVERSION on mutable root + revision transaction |
| Assessment publish/edit | stale config/publish | ROWVERSION + publish state validation |
| Attempt start | two starts/attempt limit | attempt-number uniqueness + locked count/transaction |
| Attempt lease | two tabs acquire | conditional UPDATE on expiry/owner + random token |
| Answer save | concurrent/offline events | valid lease + client_change_id unique + monotonic client sequence |
| Submit | duplicate/concurrent submit | idempotency key + terminal/result uniqueness/serialized transition |
| Manual grade | concurrent graders | ROWVERSION + append history |
| Correction | competing edits | ROWVERSION/revision sequencing + correction transaction |
| Regrade | retry/multiple workers | unique job+attempt item + conditional claim/status |
| File activation | two revisions active | filtered unique index + transactional current swap |
| Knowledge activation | two versions active | filtered unique index + transactional activation/invalidation |

QuestionRevision is business history; ROWVERSION is optimistic concurrency and must not be conflated. No long-lived database locks are kept for the duration of an Assessment Attempt.
