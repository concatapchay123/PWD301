# Security Audit

Audit the current task/domain against canonical security requirements and threat model.

Check authentication, object authorization/IDOR, CSRF, XSS, injection, mass assignment, secret/log leakage, file access/upload risks, replay/idempotency, race conditions, soft-delete leakage and AI/RAG authorization where relevant.

For every finding provide: severity, evidence, realistic exploit/impact, smallest safe remediation and required regression/security tests. Do not introduce speculative enterprise infrastructure when a local control is sufficient.
