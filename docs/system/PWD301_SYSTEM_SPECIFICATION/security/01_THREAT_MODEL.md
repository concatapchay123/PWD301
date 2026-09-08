# Threat Model

| Threat | Asset | Attack | Prevention | Detection | Test |
|---|---|---|---|---|---|
| Broken authentication | account/session | guessing, fixation | adaptive hash, generic errors, rotation, rate limits | security events | SEC-AUTH-01 |
| CSRF | cookie-auth writes | forged browser mutation | Flask-WTF/CSRF on web/AJAX | rejected-CSRF metrics | SEC-WEB-01 |
| XSS | users/session | malicious Markdown/AI output | sanitize rendered Markdown/AI HTML; CSP; escape templates | CSP/report/log | SEC-WEB-02 |
| IDOR | course/student/attempt | guess another public ID | object-level authorization every request | denied-access security event threshold | SEC-AUTHZ-01 |
| Privilege escalation | Admin/Instructor | forged role/owner fields | server role relations; allow-listed DTOs | audit/security events | SEC-AUTHZ-02 |
| SQL injection | DB | crafted query input | SQLAlchemy parameterization; allow-listed sort/filter | error/security monitoring | SEC-DB-01 |
| Mass assignment | grades/roles/state | privileged JSON fields | explicit request schemas | validation logs | SEC-API-01 |
| Replay/duplicate | submit/jobs/email | resend request | idempotency keys + unique boundaries | duplicate metrics | SEC-CONC-01 |
| Attempt takeover | active exam | second tab steals lease | expiring tokenized lease + conditional update | lease conflict | SEC-CONC-02 |
| Malicious upload | server/students | malware/macro/polyglot | quarantine, allowlist, ClamAV, fail closed | scan/security event | SEC-FILE-01 |
| Decompression bomb | CPU/RAM/disk | crafted Office/PDF | entry/uncompressed/ratio/time/memory limits | parser failure alert | SEC-FILE-02 |
| Path traversal/direct storage | file bytes | crafted filename/storage URL | generated storage key; app authorization route | denied/file anomaly | SEC-FILE-03 |
| Prompt injection | AI tools/data | document instructs model | data-not-instruction boundary; no direct SQL; allow-listed tools | prompt-abuse event | SEC-AI-01 |
| RAG leakage | course/student data | unauthorized chunks | authorization filter before retrieval; metadata policy | source-usage trace | SEC-AI-02 |
| Draft/archive leakage | content | stale index | publication/status filter + immediate invalidation | RAG QA | SEC-AI-03 |
| Cross-user AI leakage | personalized context | shared cache | no shared personalized cache | cache audit | SEC-AI-04 |
| Audit tampering | integrity | update/delete log | append-only DB control + restricted DB account | integrity review | SEC-AUDIT-01 |
| Sensitive log leakage | credentials/answers | excessive logging | redaction/schema logging | log review | SEC-LOG-01 |
| Export leakage | grade data | public/long-lived file | authorized generation, private storage, expiry | export audit | SEC-EXPORT-01 |
| Soft-delete leakage | historical data | query misses status | default scoped queries + authorization/status check | negative tests | SEC-DATA-01 |
