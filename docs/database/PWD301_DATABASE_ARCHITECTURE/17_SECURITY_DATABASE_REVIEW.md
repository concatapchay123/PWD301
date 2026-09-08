# Security Database Review

## Scope

This is a schema/threat review, not a source-code penetration test. The database must support authorization, but route/service code remains responsible for deciding whether the authenticated actor may perform a specific operation.

## Threat review

| Threat | Risk | Schema support | Required application control | Status |
|---|---|---|---|---|
| IDOR on Course/Lesson/Assessment | Instructor changes URL to another Course | ownership and Course FK chains | deny-by-default object ownership check | PASS design |
| IDOR on Student data | Instructor queries Student in other Course | Attempt/Enrollment → Course relationship | verify current Course owner before read | PASS design |
| Role-only authorization | any Instructor edits any Course | owner field + role tables | check both role and ownership | PASS design |
| Privilege escalation through role rows | invalid ADMIN-only set | unique junction only partially helps | role service maintains cumulative valid set | PASS WITH SERVICE |
| Suspended session remains valid | unauthorized continued access | status/auth_version/session/JWT grants | auth middleware checks every request | PASS design |
| JWT replay after global revoke | old signed JWT used | token grant + auth_version | validate grant/version/jti/claims | PASS design |
| Email-change takeover | unverified new email becomes login | one-time hashed token | switch email only after verification | PASS design |
| Session theft persistence | long-lived cookie | server-side session revoke/expiry | Secure/HttpOnly/SameSite cookie, rotate login session | PASS design |
| CSRF browser writes | forged session request | DB not direct | Flask-WTF/CSRF on browser/Jinja/AJAX writes | APP LAYER |
| Mass assignment | user sets owner/status/score fields | sensitive columns explicit | DTO/allowlist request fields; no ORM `**json` bulk assignment | APP LAYER |
| Correct-answer leakage | Student API receives `is_correct` | correct flags separated from AttemptChoiceSnapshot | dedicated Student serializer excludes answer key/explanation until allowed | PASS design |
| Historical content rewrite | edit used Question in place | revision model + critical triggers | create/activate new revision | PASS |
| Assessment rules changed after Students start | unfair exam | first-start marker + triggers | service/UI precheck | PASS |
| Browser clock cheating | extended timer | deadline stored server-side | all save/submit compares server time | PASS |
| Double submit | duplicate result | unique/terminal attempt state | idempotent submit transaction | PASS |
| Two active tabs | conflicting answers | expiring lease fields | lease token on every answer write | PASS |
| Stale offline answer overwrites newer | data loss | change UUID + sequence/version | conditional update | PASS |
| Student changes selected Choice ID to another question | tampered payload | snapshot FKs | verify choice parent matches AttemptQuestion | PASS WITH SERVICE |
| Regrade after detail purge | references deleted data | period `detail_purged_at` | target query excludes/skip item | PASS |
| Regrade double application | score corruption | unique job+attempt | item state claim + atomic history/current update | PASS |
| File path guessing | unauthorized download | storage key private, logical reference tables | app route auth, no public storage path | PASS |
| MIME spoof | malicious file disguised | scan/validation result model | extension+magic+server MIME+allowlist | PASS design |
| Malware scanner unavailable | unsafe pass-through | scan ERROR/PASS model | fail closed activation | PASS |
| ZIP/Office decompression bomb | resource exhaustion | processing result/job model | parser size/entry/ratio/time/memory limits | PASS WITH SERVICE/CONTAINER |
| Macro-enabled Office | code execution risk | file metadata/status | reject `.docm/.pptm`; format allowlist | PASS |
| Shared blob deleted from one Lesson | data loss | FileBlob separated from FileAsset | ref check + recovery before physical delete | PASS |
| XSS from Markdown/import/AI output | session theft/data access | DB stores source, not trusted HTML | sanitize rendered Markdown/AI HTML, CSP, no unsafe `\|safe` | APP LAYER |
| RAG cross-course leakage | Student retrieves inaccessible content | KnowledgeDocument Course scope/status | authorization prefilter before vector result reaches Gemini | PASS design |
| RAG uses archived/deleted content | stale unauthorized output | invalidated status/current version | invalidate immediately and filter active only | PASS |
| RAG prompt injection in documents | model follows document command | DB marks source/provenance only | treat retrieved chunks as untrusted data; tool policy independent | APP/AI GATEWAY |
| Personalized AI cache leak | Student B receives A response | no SQL shared personalized cache | shared cache only generic; auth-scope-aware runtime policy | PASS design |
| Raw AI chat retention leak | stored private conversation | explicit expiry index | purge >5min inactivity | PASS |
| AI source provenance lost after chat purge | impossible debug | AIRequest + SourceUsage metadata | no raw content needed | PASS |
| Audit tampering | Admin edits history | append-only trigger/table policy | application principal INSERT/SELECT only | PASS |
| Audit secret leakage | password/JWT in JSON | flexible JSON could allow it | central redaction allowlist; never serialize secrets | PASS WITH APP |
| Sensitive action succeeds but audit fails | no accountability | same SQL transaction possible | audit insert required before commit | PASS |
| Course cascade removes attempts | historical destruction | NO ACTION default | explicit delete service | PASS |
| Soft-deleted content leaks in list/API | hidden data exposed | status/deleted columns | default ORM query scopes + permission checks | PASS WITH APP |
| Archived Course visible to AI | violates AI rule | Knowledge invalidation state | archive transaction invalidates RAG | PASS |
| Grade export public exposure | PII leak | export owner/course/expiry/file asset | private download, short expiry, audit export | PASS |
| SQL injection | arbitrary DB read/write | ORM schema no direct protection | SQLAlchemy bound parameters; no string-concatenated SQL | APP LAYER |
| Excessive DB account privilege | app compromise → schema/backup admin | schema can work least privilege | separate migration/runtime/backup principals | DEPLOYMENT |
| Backup contains secrets/PII unprotected | offline leak | metadata only here | encrypt/protect backup destination; restore access control | DEPLOYMENT |
| Docker/worker compromise | file/parser escapes | DB not enough | non-root containers, no Docker socket, resource limits | DEPLOYMENT |

## Authentication data rules

Never persist:
- plaintext password;
- raw password reset/email verify token;
- raw session cookie;
- raw bearer access token;
- Gemini API key;
- database password;
- encryption private keys.

Persist only:
- strong password hash;
- SHA-256/cryptographic hash of opaque tokens where lookup is required;
- JWT `jti`, expiry, auth version, revoke state;
- redacted security metadata.

## PII classification

### High sensitivity

- email;
- password hash;
- authentication/session/token metadata;
- individual Student answers/results;
- grade exports;
- IP/security metadata;
- AI raw messages during their short lifetime.

### Moderate sensitivity

- display name/avatar;
- enrollment/progress;
- notifications;
- Course ownership.

### Low/non-PII

- published Course/Lesson educational content;
- generic question content (answer keys remain exam-sensitive);
- aggregate anonymized analytics.

## Application database principals

Recommended separation:

1. **migration principal**
   - DDL/ALTER/index/trigger permissions;
   - used only by controlled migrations.

2. **runtime application principal**
   - only required CRUD/EXECUTE;
   - no `db_owner`;
   - no arbitrary backup/restore;
   - cannot UPDATE/DELETE `audit_events`.

3. **backup principal/job**
   - backup-specific permissions;
   - cannot run normal application mutations.

4. **maintenance/archive principal**
   - tightly controlled path for audit archival/retention maintenance.

The Flask production process must not run as SQL Server `sa`.

## Audit payload policy

Allowed examples:
- changed field names;
- IDs;
- old/new status;
- old/new numeric score;
- reason;
- redacted metadata.

Disallowed:
- password hash;
- raw JWT/session token;
- Gemini key;
- DB connection string;
- whole Student essay unless an investigation has a specific approved need;
- raw AI chat merely to “have more logs”.

## Soft-delete leakage defense

Every repository/query must make deletion state explicit:
- Student/normal Instructor path defaults to active/published scope.
- Admin trash pages explicitly opt into TRASH.
- Historical grading service may reference retired QuestionRevision by ID, not a generic “active only” query.
- RAG has a separate stricter rule: archived Course is excluded even if old Student can still read it in LMS.

## File security boundary

Access decision is based on:
1. authenticated user;
2. logical FileAsset reference;
3. Course/Lesson/Question authorization;
4. current FileRevision security-cleared state;
5. route response headers/content handling.

A SHA-256 hash or opaque storage key is **not** permission.

## AI boundary

Gemini never:
- accepts caller-supplied `user_id` as authority;
- directly queries SQL;
- decides authorization;
- gets unpublished/unauthorized chunks;
- performs destructive admin operations.

Backend tools derive current user from authenticated context and re-check resource permissions.

## Residual risks to validate in implementation

1. Markdown sanitizer configuration and unsafe Jinja `|safe`.
2. SQLAlchemy default scopes for TRASH/ARCHIVED data.
3. session implementation actually uses server-side revocable state.
4. worker/container parser limits for Office/PDF bombs.
5. vector store supports reliable delete/filter/invalidation.
6. runtime secrets never enter logs.
7. exported grade file route cannot be guessed/shared beyond authorization.
8. database principal permissions match the architecture.
