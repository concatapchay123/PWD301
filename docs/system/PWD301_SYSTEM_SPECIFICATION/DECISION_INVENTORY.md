# Decision Inventory and Consistency Pass

## Confirmed baseline
- Flask/Python + SQL Server + Docker; server-rendered Jinja/Bootstrap UI with AJAX/Fetch.
- Browser auth uses Flask-Login/session; REST API uses JWT. Website AJAX never stores JWT in localStorage.
- Cumulative roles: STUDENT; INSTRUCTOR+STUDENT; ADMIN+INSTRUCTOR+STUDENT.
- Course/Lesson/Enrollment, QuestionRevision, Assessment/Attempt snapshots, file quarantine, AI/RAG authorization, audit, retention and jobs follow the locked Plan Mode rules.

## Superseded rules
| Older wording | Current authoritative rule |
|---|---|
| Video around 2 GB | **Video upload limit is < 1 GB.** |
| Published Assessment is fully immutable | Timing locks after publish; structure and assigned points lock after first Student starts; Question content/correct-answer corrections still use QuestionRevision/regrade rules. |
| Delete all Student history after leave | After 30 days without rejoin, detailed learning data may purge and stops future regrading; compact completion/prerequisite/history summary remains. |
| Hard-delete answered Questions | Remove from active bank but preserve minimal Question/revisions required for historical integrity. |

## Reconciled semantics
- `QuestionRevision` business versioning and SQL Server `ROWVERSION` optimistic concurrency are separate concepts.
- Archived Course may remain LMS-accessible to eligible historical learners, but archived Course is excluded from AI/RAG retrieval.
- Attempt snapshot preserves what the Student saw; grading may later change without rewriting that evidence.
- User removal is deactivate/anonymize-first; historical FKs are not broad-cascaded.

## Open business contradictions
None blocking. Exact operational thresholds not explicitly locked (lesson minimum time/view threshold, lease duration, rate limits, storage warning percentages) are documented as configurable defaults rather than confirmed business rules.
