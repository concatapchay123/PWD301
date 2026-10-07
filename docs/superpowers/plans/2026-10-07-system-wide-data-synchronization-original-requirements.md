# GOAL: SYSTEM-WIDE DATA SYNCHRONIZATION REMEDIATION

You are operating as a **Senior Principal Full-Stack Engineer, Software Architect, Database Engineer, Reliability Engineer, and QA Engineer**.

Your goal is to **systematically remediate the confirmed defects documented in `SYSTEM_DATA_SYNCHRONIZATION_AUDIT.md` and bring the project to a stable, persistence-safe, regression-tested state**.

This is an IMPLEMENTATION task.

Unlike the previous audit, you ARE allowed to modify source code.

However, you must follow all safety, verification, architectural, and sequencing constraints below.

---

# 1. PRIMARY SOURCE OF TRUTH

Before modifying anything, read the COMPLETE file:

`SYSTEM_DATA_SYNCHRONIZATION_AUDIT.md`

Do not rely only on its Executive Summary.

Read:

- every SYNC finding
- Global Root Causes
- Admin Audit
- Instructor Audit
- Student Audit
- API Contract Mismatches
- Cross-role Synchronization
- Root Cause Dependency Map
- Severity Matrix
- Recommended Fix Strategy
- Recommended Fix Order
- Regression Testing Plan
- Final Assessment

The audit contains:

- 57 finding groups
- 9 P0
- 27 P1
- 21 P2
- 15 root-cause categories
- multiple cross-module architectural patterns

Treat the audit as the initial remediation backlog.

However:

> DO NOT blindly assume every finding is still valid.

The audit was generated against repository snapshot:

`926fce6727c5dbdcf428b37ac143e8b46ac305e6`

First determine the CURRENT repository HEAD.

If current HEAD differs from the audited snapshot:

1. identify relevant code changes;
2. revalidate affected findings;
3. mark each finding as:
   - STILL VALID
   - PARTIALLY FIXED
   - ALREADY FIXED
   - OBSOLETE
   - NEEDS REVALIDATION

Never overwrite a newer correct implementation merely to match the old audit.

---

# 2. FINAL OBJECTIVE

The remediation is considered successful only when:

1. successful Create/Update/Delete operations immediately reconcile the current UI;
2. F5 does not cause legitimately saved changes to disappear;
3. F5 does not become necessary for ordinary same-user mutations;
4. failed persistence cannot masquerade as successful persistence;
5. frontend state and authoritative server state agree;
6. partial transaction failures cannot silently leave inconsistent domain state;
7. draft/live identities are handled correctly;
8. async responses cannot update the wrong entity/account;
9. persisted data survives:
   - UI rerender
   - F5
   - navigation
   - logout/login where applicable;
10. cross-role state becomes correct after the intended workflow;
11. all relevant P0 and P1 findings are either:
   - fixed and verified, or
   - explicitly BLOCKED with concrete technical evidence;
12. P2 findings are addressed unless fixing them introduces greater architectural risk;
13. no regression is introduced into authentication, authorization, history, snapshots, file security, assessment scoring, or persisted domain data.

---

# 3. NON-NEGOTIABLE SAFETY RULES

You may edit project source code.

You MUST NOT:

- destroy production data;
- run destructive commands against a production database;
- run irreversible migrations against an unidentified database;
- DROP production tables;
- truncate production data;
- reset the real database;
- fabricate backup success;
- disable authorization to make tests pass;
- bypass validation to make tests pass;
- weaken CSRF/session/JWT security;
- remove audit/history mechanisms;
- delete tests because they fail;
- comment out broken features;
- hide errors with empty catch blocks;
- replace proper synchronization with `window.location.reload()`;
- add F5/reload as the solution;
- mark a finding fixed merely because code compiles;
- claim success when verification was skipped.

If database migration is required:

1. inspect target identity first;
2. verify environment;
3. use an isolated/disposable database or safe copy where possible;
4. verify upgrade;
5. verify resulting schema;
6. test application compatibility;
7. test downgrade/rollback strategy where applicable.

Do NOT mutate an unidentified live database.

---

# 4. DO NOT REWRITE THE STACK

The existing application is:

- Flask
- SQLAlchemy
- SQL Server
- Vanilla JavaScript SPA

Do not migrate the project to:

- React
- Vue
- Next.js
- Redux
- TanStack Query
- Redis
- WebSocket

unless the existing architecture makes the requirement impossible and you have strong evidence.

The audit explicitly supports targeted remediation.

Prefer fixing the current architecture.

Reuse existing:

- serializers
- API client
- ordered queues
- authorization
- ROWVERSION/concurrency mechanisms
- sessions/JWT
- audit/history
- domain snapshots
- file security checks

where they are correct.

---

# 5. ROOT-CAUSE-FIRST RULE

Do NOT treat all 57 findings as 57 unrelated bugs.

First map them into the audit root causes:

- G01 Representation/API contract does not roundtrip
- G02 Acknowledgement not reconciled with authoritative state
- G03 Async callback/response identity race
- G04 Transaction ownership fragmented
- G05 Draft manifest does not preserve complete intent
- G06 Editing lease enforcement gaps
- G07 Local sequence/event not connected to durable sequence
- G08 Local durability/account scoping
- G09 Operational success lacks real execution evidence
- G10 Authority incorrectly depends on frontend
- G11 Cache/refetch invalidation problems
- G12 Routing/scope lacks persisted identity
- G13 Runtime schema incompatible with code
- G14 Read failure treated as empty data
- G15 Dirty workflow lacks checkpoint/recovery

Fix shared causes whenever a safe reusable solution can eliminate multiple findings.

Avoid 10 separate patches when one correct contract normalization fixes all 10.

---

# 6. IMPLEMENTATION ORDER

Follow this order unless concrete dependency analysis proves a different order safer.

## PHASE 0 — BASELINE & SAFETY

Before changing code:

1. Read repository instructions including `AGENTS.md`.
2. Check git status.
3. Record current HEAD.
4. Preserve all existing user modifications.
5. Do not overwrite unrelated uncommitted work.
6. Identify test commands.
7. Identify backend/frontend startup paths.
8. Identify database configuration without leaking secrets.
9. Map current migration head.
10. Run safe baseline tests.

Create:

`REMEDIATION_PROGRESS.md`

Track every finding:

| Finding | Severity | Root Cause | Current Status | Fix Status | Tests | Evidence |
|---|---|---|---|---|---|---|

Do not use this progress document as a substitute for actual testing.

---

# 7. PHASE 1 — DATA LOSS PREVENTION

Prioritize the audit findings:

- SYNC-002
- SYNC-004
- SYNC-005
- SYNC-009
- SYNC-010
- SYNC-027
- SYNC-029
- SYNC-041
- SYNC-042

These have priority because they can cause:

- lost user intent;
- partial persistence;
- wrong-entity updates;
- cross-account contamination;
- unreliable recovery;
- lost answer state.

For every P0:

### Step A
Create or identify a deterministic regression test reproducing the defect.

### Step B
Confirm the test fails for the expected reason.

### Step C
Implement the smallest architecturally correct fix.

### Step D
Run the focused regression test.

### Step E
Run adjacent tests.

### Step F
Inspect persisted state where applicable.

### Step G
Mark the finding fixed only after evidence exists.

Never convert a data-loss problem into a hidden error.

---

# 8. PHASE 2 — DATABASE PERSISTENCE & TRANSACTION SAFETY

Address:

- SYNC-001
- SYNC-004
- related transaction/persistence findings

Investigate:

- migration 0012
- migration 0013
- Alembic head
- deployed/runtime schema
- ORM compatibility
- SQL constraints
- nested commits
- helper-owned commits
- rollback boundaries

For composite business operations:

> ONE outer transaction should own the business action whenever atomicity is required.

Inner helpers should not independently commit if that makes rollback impossible.

Prefer:

`outer transaction → helpers flush → final validation → commit`

over:

`helper commit → helper commit → later operation fails → rollback cannot undo earlier commits`

Add fault-path tests.

Verify partial failure cannot leave falsely successful state.

---

# 9. PHASE 3 — API CONTRACT & ACKNOWLEDGEMENT

Address contract-related findings including:

- SYNC-006
- SYNC-007
- SYNC-008
- SYNC-015
- SYNC-016
- SYNC-024
- SYNC-025
- SYNC-032
- SYNC-040
- SYNC-044
- SYNC-045
- SYNC-046
- SYNC-047
- SYNC-048
- SYNC-054

Normalize:

Frontend representation
↔ API request
↔ Backend DTO/validation
↔ ORM/domain model
↔ serializer
↔ frontend representation

The following invariant must hold:

> deserialize(serialize(valid_state)) must preserve meaningful persisted state.

Test explicit:

- false
- true
- null
- empty string
- zero
- arrays
- enum values
- nested objects
- IDs
- URLs
- resource references

Do NOT use truthiness such as:

`value || default`

where `false`, `0`, or `null` are meaningful domain values.

---

# 10. HTTP OUTCOME SEMANTICS

The UI must distinguish:

- APPLIED
- PENDING APPROVAL
- PARTIAL
- REJECTED
- FAILED

HTTP 202 MUST NOT be treated as:

> live mutation already applied.

A fulfilled Promise MUST NOT automatically mean business success.

Check:

- HTTP status
- API success field
- domain state
- returned authoritative representation

Do not show success toast until success semantics are actually satisfied.

---

# 11. PHASE 4 — FRONTEND SYNCHRONIZATION

Address:

- stale UI
- optimistic mutation without rollback
- wrong draft/live identity
- late async responses
- missing authoritative reconciliation
- disappearing unsaved form input
- resource/order persistence
- wrong entity IDs

Required rule:

> SAME-USER successful mutation must reconcile immediately without F5.

That does NOT require WebSocket.

Use the existing architecture appropriately:

- consume server response;
- update authoritative local representation;
- or refetch the affected entity;
- rollback optimistic state on failure.

Do NOT solve this using:

`location.reload()`

or:

`window.location.reload()`.

---

# 12. ASYNC IDENTITY FENCING

For asynchronous entity loads/mutations:

Never depend on mutable global/current IDs after an `await`.

Bad conceptual pattern:

currentLesson = A
request A

currentLesson = B
request B

response A arrives
apply response to currentLesson B

Correct pattern must bind operations to immutable identity/generation.

Use appropriate mechanisms such as:

- captured entity ID
- request generation/token
- cancellation/obsolete-response check
- scoped callback identity

Any response from entity A must never mutate entity B.

Test deliberately reversed response ordering.

---

# 13. DRAFT IDENTITY

When backend creates a draft/clone/new entity:

The frontend must consume the returned persisted identity.

Example:

Save live lesson
→ backend creates working draft ID D
→ response returns D
→ subsequent saves/reads must target D where workflow requires D

Never continue operating on the old live ID merely because the UI still holds it.

---

# 14. LESSON ROUNDTRIP

Explicitly regression-test:

- YouTube URLs
- document resources
- resource detach
- lesson clone
- lesson move
- block ordering
- text blocks
- quiz blocks
- persisted IDs

For each:

LOAD
→ parse
→ edit/no-op
→ serialize
→ save
→ fresh GET
→ compare meaningful state

A no-op load/save must not destroy information.

---

# 15. PHASE 5 — DRAFT / COURSE MANIFEST CONSISTENCY

Fix draft/live workflows so that one new changeset does not silently discard unrelated pending user intent.

Preserve required categories including where applicable:

- additions
- edits
- moves
- deletes
- resources
- metadata
- governance changes

Do not cancel previous intent unless:

1. it is intentionally superseded;
2. its intent is represented in the replacement;
3. recovery/history remains available.

Approval must promote the intended draft state.

Deleted draft resources must not magically reappear.

---

# 16. PHASE 6 — LOCAL STORAGE / ACCOUNT SCOPE

Anything persisted in browser storage must be correctly scoped.

At minimum evaluate keys against:

- user ID
- role
- course/entity ID
- assessment ID
- appropriate draft ID

User A data must never hydrate User B.

Instructor state must never hydrate Student state.

Logout/account switch must invalidate or correctly namespace account-specific memory/cache.

Test:

User A
→ create local draft/cache
→ logout
→ User B login
→ ensure A state cannot appear

---

# 17. PHASE 7 — STUDENT ANSWER / SEQUENCE DURABILITY

Treat assessment answers as high-integrity data.

Test:

- typing
- debounce
- navigation
- F5
- deadline
- submit
- retry
- duplicate request
- reordered request
- stale sequence
- two tabs where relevant

The latest accepted answer must have a durable sequence relationship.

Do not allow older late requests to overwrite newer accepted answers.

Do not rely only on browser event order.

---

# 18. BACKUP / RESTORE

A successful backup must contain actual recoverable database data.

Do not call metadata JSON a database backup.

Do not report:

`SUCCEEDED`

unless the required backup operation actually completed.

For restore verification:

- use an isolated restore target;
- compare schema;
- compare representative row counts/data;
- verify histories/references as appropriate.

Never run restore against the active project database merely to prove a test.

If the environment cannot safely perform a real restore drill:

mark the verification:

`BLOCKED — SAFE RESTORE TARGET REQUIRED`

Do NOT invent success.

---

# 19. READ FAILURE SEMANTICS

A backend/read failure must not silently become:

`[]`

or:

`0 results`

if the real state is UNKNOWN.

Differentiate:

- successfully empty
- unavailable/error
- unauthorized
- stale
- partial

Do not turn infrastructure failure into misleading valid business data.

---

# 20. ROUTING / PERSISTED SCOPE

Do not infer persisted relationships from:

- page title
- label
- URL string only
- UI position

when the relationship should have a durable ID/FK/domain field.

Deep links must rehydrate the intended entity after F5.

Test:

navigate via deep link
→ F5
→ correct editor/entity/scope remains loaded

---

# 21. AUTHORITY RULE

Frontend is not the authority for:

- scoring
- authorization
- persistent roles
- ownership
- deadlines
- sensitive workflow status
- server lifecycle state

Backend must validate authoritative rules.

Frontend may display them but must not be trusted as their enforcement source.

---

# 22. DO NOT ADD REAL-TIME INFRASTRUCTURE PREMATURELY

Same-browser immediate synchronization does not require WebSocket.

Fix:

mutation acknowledgement
→ authoritative state
→ local reconcile/refetch

first.

Only implement cross-browser realtime if an explicit product requirement exists.

Do not add Redis/WebSocket merely because F5 currently changes data.

---

# 23. TEST STRATEGY

For every fixed mutation, evaluate:

ACTION
→ immediate UI
→ API acknowledgement
→ DB/server state
→ fresh GET
→ F5
→ navigation away/back
→ relogin where relevant
→ second role/session where relevant

Test negative outcomes:

- 400
- 401
- 403
- 409
- 500
- timeout
- network failure
- late response
- partial failure

The UI must not claim success for a failed mutation.

---

# 24. ROLE ACCEPTANCE TESTS

## ADMIN

Verify relevant:

- role management
- suspension/session revocation
- notifications
- course approval/rejection
- change approval
- backup
- restore validation
- system settings
- maintenance behavior

## INSTRUCTOR

Verify relevant:

- create/update course
- curriculum
- learning units
- lesson save
- lesson clone
- lesson move
- resources
- YouTube
- academic settings
- prerequisites
- assessments
- question editing
- publishing
- draft/retry
- change submission

## STUDENT

Verify relevant:

- enrollment-dependent flows
- lesson progress
- quiz answers
- answer autosave
- F5 recovery
- assessment submit
- results
- retries
- session/role transitions

---

# 25. CROSS-ROLE ACCEPTANCE

Test workflows such as:

Instructor modifies draft
→ Admin sees correct proposal
→ Admin approves
→ Student obtains correct published representation

and:

Student submits assessment
→ backend persists authoritative result
→ Instructor/Admin views correct persisted result
→ Student F5/relogin retains correct state

Cross-role correctness does NOT necessarily mean instant WebSocket delivery.

It means the authoritative state is correct and refresh/navigation/focus behavior is truthful.

---

# 26. TEST-FIRST FOR HIGH-RISK DEFECTS

For P0 and important P1 findings:

Prefer:

1. create deterministic failing regression test;
2. confirm defect;
3. fix;
4. make test pass.

Do not write meaningless tests that simply reproduce the implementation.

Tests should assert the required business invariant.

---

# 27. PRESERVE CORRECT SYSTEM INVARIANTS

Do not break:

- historical snapshots
- immutable assessment/result evidence
- audit trails
- authorization checks
- file validation
- server deadlines
- UUID identities
- ROWVERSION/concurrency checks
- ordered answer queue semantics
- privacy boundaries

Do not trade correctness in one module for regression in another.

---

# 28. SMALL COMMITS / LOGICAL PATCHES

Work in logical remediation units.

For each unit:

1. findings addressed
2. files changed
3. reason
4. tests added/updated
5. tests run
6. result
7. remaining risk

Avoid giant unrelated refactors.

Do not reformat the entire repository.

Do not rename unrelated files/functions.

---

# 29. DO NOT STOP AT FIRST GREEN TEST

Existing audit already showed frontend tests passing while severe defects still existed.

Therefore:

> Existing tests passing is NOT proof of persistence correctness.

You must add targeted tests for previously uncovered defects.

A finding is not fixed merely because old tests remain green.

---

# 30. REMEDIATION LOOP

For each finding:

```text
READ FINDING
↓
REVALIDATE CURRENT CODE
↓
REPRODUCE / CREATE TEST
↓
IDENTIFY ROOT CAUSE
↓
CHECK SHARED ROOT-CAUSE FIX
↓
IMPLEMENT MINIMAL CORRECT CHANGE
↓
RUN TARGETED TEST
↓
RUN RELATED TESTS
↓
VERIFY AUTHORITATIVE STATE
↓
VERIFY F5 / FRESH READ WHEN APPLICABLE
↓
UPDATE REMEDIATION_PROGRESS.md
↓
NEXT FINDING
```

Do not mark complete before this loop succeeds.

---

# 31. BLOCKER POLICY

If a finding requires something unavailable, such as:

- production credentials
- external mail provider
- real ClamAV infrastructure
- isolated SQL Server restore target
- unavailable browser environment
- missing service

do NOT fake the result.

Mark:

`BLOCKED`

Include:

- exact blocker
- what is already fixed
- what remains unverified
- exact command/test/procedure required to verify it later

Continue fixing other independent findings.

---

# 32. COMPLETION GATES

Do NOT declare the system fixed until all of these are evaluated.

## Gate A — P0

All P0 findings:

`FIXED + VERIFIED`

or legitimate:

`BLOCKED`

No unresolved P0 may be silently ignored.

## Gate B — P1

All P1 findings evaluated and either fixed or explicitly blocked with evidence.

## Gate C — Regression

Relevant automated suites pass.

## Gate D — Persistence

Representative mutations verify:

UI
→ API
→ DB
→ fresh GET
→ F5

## Gate E — Identity

Race tests confirm stale response cannot mutate current entity.

## Gate F — Cross-account

Browser/local storage cannot leak state between users/roles.

## Gate G — Transaction

Fault injection verifies composite actions do not persist partial state unexpectedly.

## Gate H — Migration

Runtime schema compatibility is verified against a safe target.

## Gate I — No reload workaround

Search repository for newly introduced reload/F5 workarounds.

There should be none unless explicitly required for unrelated behavior.

---

# 33. FINAL FULL REGRESSION

After all remediation phases:

Run all safe available:

- frontend tests
- backend tests
- syntax checks
- static checks
- API contract tests
- persistence integration tests
- role tests
- race tests
- browser tests where environment supports them

Re-run searches for the patterns identified by the audit.

Re-read the entire original finding list and verify NONE were accidentally skipped.

---

# 34. FINAL REPORT

Create:

`SYSTEM_DATA_SYNCHRONIZATION_REMEDIATION_REPORT.md`

It must contain:

# 1. Executive Summary

# 2. Original Repository Snapshot

# 3. Remediation Repository Snapshot

# 4. Files Changed

# 5. Root Causes Fixed

# 6. P0 Results

# 7. P1 Results

# 8. P2 Results

# 9. Database/Migration Changes

# 10. Frontend Synchronization Changes

# 11. API Contract Changes

# 12. Transaction Changes

# 13. Race Condition Fixes

# 14. Draft/Persistence Fixes

# 15. Admin Verification

# 16. Instructor Verification

# 17. Student Verification

# 18. Cross-role Verification

# 19. Tests Added

# 20. Tests Executed

# 21. Passed Tests

# 22. Failed Tests

# 23. Blocked Verification

# 24. Remaining Risks

# 25. Finding-by-Finding Status Matrix

Use:

| Bug ID | Severity | Before | Root Cause | Fix | Verification | Final Status |
|---|---|---|---|---|---|---|

Valid final statuses:

- FIXED_VERIFIED
- FIXED_PARTIALLY_VERIFIED
- BLOCKED
- ALREADY_FIXED
- OBSOLETE
- NOT_FIXED

Never hide NOT_FIXED items.

---

# 35. FINAL NUMERIC SUMMARY

Report:

```text
Total original findings: 57

FIXED_VERIFIED:
FIXED_PARTIALLY_VERIFIED:
ALREADY_FIXED:
OBSOLETE:
BLOCKED:
NOT_FIXED:

P0 remaining:
P1 remaining:
P2 remaining:
```

Also report:

```text
Tests added:
Tests passed:
Tests failed:
Tests skipped:
```

Do not convert skipped tests into passes.

---

# 36. FINAL SYSTEM STATUS

Choose exactly one:

`CRITICAL`

`UNSTABLE`

`PARTIALLY STABLE`

`STABLE WITH BLOCKED EXTERNAL VERIFICATION`

`STABLE`

Only use `STABLE` if there is sufficient evidence.

---

# 37. MOST IMPORTANT ENGINEERING PRINCIPLE

Do not optimize for:

> making the UI look fixed.

Optimize for:

> preserving user intent and ensuring the authoritative persisted state is correct.

The correct invariant is:

```text
USER INTENT
↓
VALID REQUEST
↓
AUTHORIZED BACKEND ACTION
↓
ATOMIC / CORRECT PERSISTENCE
↓
AUTHORITATIVE RESPONSE
↓
FRONTEND RECONCILIATION
↓
F5
↓
SAME CORRECT STATE
```

If F5 changes a successful operation back to an older state, the operation is NOT fixed.

If the UI changes but persistence does not, it is NOT fixed.

If persistence succeeds but the current UI remains stale until F5, it is NOT fully fixed.

If a partial failure is presented as full success, it is NOT fixed.

---

# 38. AUTONOMY

Continue autonomously through independent remediation work.

Do not stop after fixing one bug.

Do not stop after fixing one role.

Do not stop because existing tests pass.

Do not stop after P0 if P1/P2 remain safely actionable.

When a specific risky operation requires external authorization or an unavailable safe environment:

- mark only that verification BLOCKED;
- continue with all independent safe work.

---

# FINAL GOAL

Remediate the system so that Admin, Instructor, and Student workflows are backed by truthful, authoritative persistence and correct immediate UI synchronization.

Prioritize:

DATA SAFETY
→ DATABASE INTEGRITY
→ TRANSACTION CORRECTNESS
→ API CONTRACT
→ IDENTITY/RACE SAFETY
→ FRONTEND SYNCHRONIZATION
→ CROSS-ROLE CONSISTENCY
→ UX

Do not use reload/F5 as a fix.

Do not claim success without evidence.

Read the original audit again before declaring completion.