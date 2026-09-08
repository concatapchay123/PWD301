# Background Jobs

Persist work before execution. Jobs cover malware scan/file processing, DOCX/PDF import, regrading, RAG indexing/invalidation, email delivery, retention cleanup, analytics refresh and backup tracking. Workers claim with bounded lease, update attempts/status, use idempotency/dedupe, exponential/bounded retry, timeout and terminal failure alert. Domain-specific job/item tables are used where rich progress is needed.
