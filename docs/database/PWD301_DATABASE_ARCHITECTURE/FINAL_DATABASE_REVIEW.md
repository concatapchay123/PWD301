# FINAL DATABASE REVIEW

> Completion-pass review cho PWD301 Database Architecture. Kết quả này phản ánh artifact sau static QA/repair; runtime SQL Server và Mermaid render được ghi đúng trạng thái, không giả lập.

## 1. Executive verdict

**PASS WITH NON-BLOCKING ENVIRONMENT NOTES — READY AS IMPLEMENTATION BASELINE.**

- Actual SQL table count: **71**.
- Data Dictionary table count: **71**.
- ERD entity coverage: **71/71**.
- SQL files: **12**.
- Mermaid diagrams: **10**.
- Foreign keys: **156**.
- Named constraints: **476**.
- Explicit indexes: **108**.
- Critical triggers: **12**.
- Broad `ON DELETE CASCADE`: **0**.
- Blocking business-rule contradictions: **0**.

## 2. Final quality gates

| Category | Status | Evidence / finding | Resolution |
|---|---|---|---|
| Database Architecture | PASS | Normalized relational schema; no EAV/CQRS/event-sourcing overreach | Keep conventional relational model |
| SQL Server compatibility | PASS WITH NOTE | Static DDL review passes; no PostgreSQL/MySQL syntax hazards detected | Runtime execution not available in this environment |
| ERD ↔ Data Dictionary ↔ DDL | PASS | 71 SQL tables = 71 documented tables = 71 ERD entities | No unexplained discrepancy |
| Data Dictionary | PASS | Every SQL table documented once; column set/nullability reconciled | Updated affected dictionaries during repair |
| Business-rule traceability | PASS | Major AUTH/COURSE/ENROLL/QBANK/ASSESS/ATTEMPT/REGRADE/FILE/AI/AUDIT rules mapped | Service/transaction/worker enforcement named where DB alone is inappropriate |
| Assessment integrity | PASS | Timing lock after publish; structure/points lock after first start; correction remains allowed | Trigger + service transaction design aligned |
| Attempt snapshot | PASS | Question/choice/order/points stable per attempt | Historical evidence never rewritten |
| Single-tab lease | PASS | Expiring lease/heartbeat/takeover; no long-lived DB lock | Conditional update + same Attempt ID |
| Regrading | PASS | Background, resumable, idempotent; score history retained | Purged enrollment periods excluded |
| Enrollment retention | PASS | >30-day no-rejoin detail purge + compact summary | Prerequisite/completion history preserved |
| File security | PASS | Quarantine, fail-closed scan, dedup, two-phase replacement, private delivery | Official video limit **<1 GB** |
| AI/RAG | PASS | Authorized/published/active source filtering; invalidation/versioning modeled | Archived/deleted content excluded |
| Audit | PASS | Append-only trigger; actor/context/target/reason/correlation metadata | No secret/token persistence requirement |
| Performance/indexing | PASS WITH NOTE | Hot-path indexes, filtered uniqueness, DB pagination modeled | Execution-plan/load tuning remains deployment work |
| Migration/seed readiness | PASS | Ordered DDL/Alembic strategy + idempotent role/demo seed guidance | No production credentials/secrets seeded |
| Documentation completeness | PASS | README, manifest, ERD, dictionaries, lifecycle, security, traceability, test plan present | Cross-links statically checked |
| Artifact/package integrity | PASS | Final ZIP recreated after document finalization and integrity-tested | See packaging section |

## 3. Completion-pass substantive changes

| Change | Reason | Files affected | Business impact |
|---|---|---|---|
| Changed historical actor/owner FKs from cascade-style `SET NULL` to `NO ACTION` where multiple paths to `users` could create SQL Server cascade-path risk | SQL Server compatibility + preserve actor history | `002_course_learning.sql`, `003_question_bank.sql`, `004_assessment.sql` + related Data Dictionaries | No business-rule change; User history remains deactivate/anonymize-in-place |
| Made deferred background-job/current-version pointers nullable where bootstrap/circular lifecycle requires it | Avoid impossible insert order and invalid `SET NULL` on NOT NULL columns | `005_attempt_regrade.sql`, `006_files_import.sql`, `007_ai_rag.sql` + related dictionaries | Enables safe two-phase creation/activation |
| Added explicit `PENDING` lifecycle for `file_assets`; ACTIVE requires valid ACTIVE current revision | Prevent logical asset becoming accessible before scanned revision activation | `006_files_import.sql`, `09_DATA_DICTIONARY_FILES_IMPORT.md`, `16_CONCURRENCY_AND_TRANSACTIONS.md` | Strengthens fail-closed file lifecycle |
| Hardened Assessment publish/first-start marker immutability | Prevent bypassing timing/structure/point locks by clearing marker fields | `012_critical_invariant_triggers.sql`, `07_DATA_DICTIONARY_ASSESSMENT.md` | Preserves final mutability rules exactly |
| Kept filtered unique active-version invariants | Guarantee one ACTIVE file revision/asset and one ACTIVE knowledge version/document | `011_indexes.sql` + docs | Stronger DB-level lifecycle integrity |
| Added three missing operational entities to ERD coverage | ERD previously covered 68 of 71 SQL tables | `03_ERD.md` | Documentation reconciliation only |
| Fixed README stale filename/reference and expanded final navigation/SQL manifest | Package entry point needed to be implementation-ready | `README.md` | Documentation only |
| Fixed Markdown table escaping and heading hierarchy issues | Static Markdown QA | Security/Test/Migration/Final Review docs | Documentation only |
| Added final artifact manifest and refreshed non-blocking open issues | Completion/package requirement | `ARTIFACT_MANIFEST.md`, `OPEN_ISSUES.md` | Documentation/QA only |

## 4. SQL Server static QA

Static checks performed across all 12 SQL files:

- 71 unique `CREATE TABLE` statements.
- All FK parent/target tables and referenced columns exist.
- No `ON DELETE SET NULL` references a NOT NULL local column.
- No duplicate named constraint or explicit index name detected.
- All explicit index tables/columns exist.
- `public_id` columns use `UNIQUEIDENTIFIER` + `NEWSEQUENTIALID()` consistently on major public entities.
- No `FLOAT` is used for grade/score DDL.
- No accidental `SERIAL`, `BIGSERIAL`, `BOOLEAN`, `TIMESTAMPTZ`, `JSONB`, `ON CONFLICT`, `ILIKE`, or PostgreSQL enum syntax detected.
- Critical filtered unique indexes verified for active EnrollmentPeriod, FileRevision and KnowledgeVersion.
- 12 critical triggers reference `inserted`/`deleted` set semantics where applicable; audit trigger intentionally blocks UPDATE/DELETE.
- Broad cascading deletion of historical learning/assessment data is absent (`ON DELETE CASCADE` count = 0).

**SQL Server runtime execution: NOT EXECUTED — environment limitation.** `sqlcmd`/SQL Server/Docker runtime was not available, so no claim of executed DDL is made.

## 5. ERD / Data Dictionary / DDL reconciliation

| Set | Count |
|---|---:|
| SQL tables | 71 |
| Data Dictionary tables | 71 |
| ERD entity coverage | 71 |

Set differences after repair:

```text
SQL_TABLES - DICTIONARY_TABLES = ∅
DICTIONARY_TABLES - SQL_TABLES = ∅
SQL_TABLES - ERD_TABLES = ∅
ERD_TABLES - SQL_TABLES = ∅
```

Data Dictionary column names and nullability were also reconciled against DDL. Computed columns and SQL Server `ROWVERSION` were treated according to SQL Server semantics rather than literal `NOT NULL` text parsing.

## 6. Assessment integrity proof

| Scenario | Protection |
|---|---|
| Student starts near close time | `deadline_at = min(start + time_limit, close_at)` by server transaction |
| Timing update after publish | Service block + critical trigger |
| Add/remove/restructure questions after first start | `first_attempt_started_at` marker + structure triggers |
| Change assigned points after first start | Same structure/assignment lock |
| Correct answer changed after submit | New QuestionRevision/Correction → eligible RegradeJob → grade/result history |
| Question text/choices changed while Student active | Existing Attempt snapshot stays frozen; configured full-credit correction applies to eligible attempts |
| Two tabs open | First valid lease owns editing; second blocked/read-only |
| First tab crashes | Lease expiry → takeover of same Attempt; no regenerated questions/order/deadline |
| Offline save arrives after deadline | Rejected/not counted by server-authoritative deadline |
| Old offline change arrives after newer save | Monotonic/change-version reconciliation prevents stale overwrite |
| Two concurrent submits | Terminal-state/idempotency transaction creates one logical result |

The final Assessment rule is **not** “Published Assessment cannot change.” Timing locks after publish; structure/points lock after first Student start; Question correction/versioning remains valid according to the confirmed correction rules.

## 7. Regrading and retention proof

- `QuestionCorrection` identifies answer-only vs content/choice correction and effective revision/cutoff.
- Regrade is background, resumable and idempotent per target item.
- Worker targets retained AttemptQuestion source references efficiently; no historical snapshot is rewritten.
- Score changes preserve previous/current values, actor/reason/time and notify affected Student when applicable.
- When a Student leaves and does not rejoin for >30 days, eligible detailed period data may be purged; that purged period naturally/exlicitly leaves future automatic regrading scope.
- Compact Course completion/prerequisite summary is not cascade-deleted.

## 8. File security proof

- Upload enters quarantine and is inaccessible to Student until required checks pass.
- Scanner failure/unavailability is fail-closed.
- `.docm` / `.pptm` are not allowed.
- Parser workflow carries size/resource/time safeguards for DOCX/PPTX/PDF containers.
- Official video limit throughout active architecture is **<1 GB**.
- Physical blob dedup is separated from logical authorization.
- File replacement is two-phase: old active revision survives if new revision fails scanning/processing.
- One FileAsset can have at most one ACTIVE FileRevision by filtered unique index.
- Private application route is the authorization boundary; storage path itself is never sufficient.

## 9. AI/RAG proof

- Student retrieval is limited to published, authorized content; archived Course content is excluded from AI retrieval by confirmed business rule.
- Deleted/inactivated sources are invalidated immediately for retrieval even if physical recovery bytes remain.
- New KnowledgeVersion becomes current only after successful processing.
- One KnowledgeDocument has at most one ACTIVE KnowledgeVersion by filtered unique index.
- Failed new version may fall back only to a still-valid/authorized prior version.
- AI answer source-version references are retained for traceability.
- Raw AI chat content is TTL-based and removed after 5 minutes inactivity; security/audit metadata remains minimal and separate.
- Personalized AI responses are not shared-cache reused across users.

## 10. Audit and security proof

- Important AuditEvent rows are append-only; UPDATE/DELETE is blocked by trigger.
- Sensitive Admin mutation requires authorization + re-authentication + confirmation phrase + reason at service layer.
- Where required audit and business mutation share the SQL database, they commit atomically; audit persistence failure blocks the sensitive mutation.
- User removal begins with deactivate/anonymize, not destructive cascade through historical records.
- Object-level authorization remains service/permission-layer responsibility; schema provides ownership/resource relationships but does not pretend to replace authorization middleware.

## 11. Markdown and Mermaid QA

Markdown static QA:

- fenced code blocks balanced;
- no unresolved development/draft markers;
- heading hierarchy checked;
- relative Markdown links checked;
- malformed table issue found during pass was repaired;
- superseded historical rules remain explicitly labeled rather than silently removed.

Mermaid:

- 10 Mermaid blocks found;
- block delimiters and diagram headers statically checked;
- ERD entity references reconciled to all 71 SQL tables.

**Mermaid render validation: NOT EXECUTED — Mermaid CLI/render engine unavailable.** No claim of successful graphical rendering is made.

## 12. Migration / seed / backend readiness

- Numeric SQL dependency order documented in `sql/README.md`.
- Alembic migration layout and expand/backfill/contract guidance documented in `20_MIGRATION_STRATEGY.md`.
- Seed strategy includes stable `STUDENT`, `INSTRUCTOR`, `ADMIN` roles and optional development-only demo data.
- Seed guidance explicitly excludes real API keys, tokens, credentials and production PII.
- Schema contract supports SQLAlchemy models, Flask session auth, JWT API, AJAX service endpoints, workers and optimistic concurrency without requiring backend developers to invent new business rules.

## 13. Package inventory and ZIP validation

Final package inventory is authoritative in `ARTIFACT_MANIFEST.md`.

Final packaging validation after the last document update:

- ZIP exists: **PASS**.
- ZIP integrity test: **PASS**.
- Root directory inside archive is `PWD301_DATABASE_ARCHITECTURE/`: **PASS**.
- `README.md`: **PASS**.
- `ARTIFACT_MANIFEST.md`: **PASS**.
- `sql/` and all 12 SQL files: **PASS**.
- No temp/cache/unrelated files included: **PASS**.
- SHA-256 checksum generated separately: **PASS**.

## 14. Remaining notes

There are **no blocking business-rule contradictions**. Remaining items in `OPEN_ISSUES.md` are deployment/runtime tuning or environment verification notes only.

## 15. Final verdict

**PASS WITH NOTES — COMPLETE FOR DATABASE ARCHITECTURE PACKAGING AND READY FOR SQLAlchemy/Alembic BACKEND IMPLEMENTATION.**

The two environment limitations are explicit: SQL Server DDL was not runtime-executed here, and Mermaid diagrams were not renderer-executed here. Both received static QA and are test targets for the implementation/CI environment.
