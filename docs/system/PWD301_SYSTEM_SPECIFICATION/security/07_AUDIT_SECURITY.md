# Audit Security

Important audit is append-only and written with real actor identity/context, target, action, reason, time and correlation ID. Do not store passwords, raw tokens, session secrets or unnecessary Student/AI content. Application runtime should have insert/read permissions needed for audit but no normal update/delete path. Sensitive business mutation and required AuditEvent share a DB transaction so audit persistence failure aborts the mutation.
