# Glossary and Terminology

| Term | Meaning |
|---|---|
| Enrollment | Stable logical Student-Course relationship reused across leave/re-enroll. |
| EnrollmentPeriod | One active learning period/session of an Enrollment; detailed retention is period-scoped. |
| Completion Summary | Compact durable history used for prior completion/prerequisite integrity after detail purge. |
| Question | Stable bank identity. |
| QuestionRevision | Immutable historical content/answer version once used. |
| Assessment | Configured exam/practice container. |
| AssessmentQuestion assignment/pool | Relationship holding assessment-specific points/selection rules. |
| Attempt | One Student execution of an Assessment. |
| Attempt snapshot | Frozen exact questions/choices/order/points shown to that Student. |
| Lease | Expiring right of one browser tab/session instance to edit an Attempt. |
| Correction | Approved change to Question content/correct answer producing revision/regrade policy. |
| Regrade | Background recalculation of eligible historical grades after correction. |
| FileBlob | Deduplicated physical bytes metadata. |
| FileAsset | Logical resource identity exposed to business domain. |
| FileRevision | Version of FileAsset passing quarantine/security lifecycle. |
| KnowledgeVersion | RAG-indexable version tied to authorized source revision. |
| AuditEvent | Append-only record of important Admin/Instructor/security actions. |
| Derived cache | Recomputable value (e.g., progress/analytics); never sole historical source. |
| Server authoritative | Server/DB time and state decide validity, not client claims. |
| Object-level authorization | Permission check against concrete resource ownership/enrollment/course relationship. |
