# Course review and Student delivery evidence — 2026-10-12

Scope: SYNC-013, 014, 068, 069 and 082. Original audit remains unchanged. Evidence is scoped to the actual mechanisms tested below; no full-product release claim.

## Real HTTP and SQL review gates

`tests/integration/test_sqlserver_course_changeset_sync.py` plus the complete existing course changeset API suite: **19 passed, zero failures/skips in 61.63 seconds**, runner exit 0. Target `pwd301_test_course_changeset_sync_20261012` was verified with the disposable prefix, `PWD301_TEST_DB_DISPOSABLE=1`, DB_NAME and migration head `syncprogress20261011` before destructive test setup.

- Instructor HTTP submit and separate Admin approval leave an unrelated REORDER_UNITS request PENDING. Independent SQL verifies both transitions and the approved lesson; a fresh Instructor status GET agrees.
- Three resource-only staged revisions retain label, position or required-flag changes through no-change cleanup, submission and Admin approval. Independent SQL verifies the new PUBLISHED revision and unchanged HISTORICAL resource metadata.
- Injecting a deletion validation failure makes Admin approval return 400. All lesson identities/statuses/positions/deletion timestamps match the pre-review SQL snapshot and the request remains PENDING. Removing the fault and retrying applies both payload-only additions at distinct positions and deletes the original lesson in the same approved review.

These tests use session bootstrap and real loopback HTTP; reviewed metadata fixtures are seeded through existing services and persisted SQL. They do not establish the browser authoring controls for every resource metadata field. The initial four failures were DetachedInstanceError in the new fixture, corrected by capturing public identities before session teardown; they were not product failures or a production RED phase.

## Residual Student resource resurrection

A new permanent regression reproduced SYNC-014 after apparently successful revision approval: current SQL links were empty and historical links retained, but `_serialize_student_lesson` emitted the historical document through its automatic fallback. Source repair removes that fallback. Approved current links now define delivery; existing revision-copy services remain responsible for carrying retained resources into a new revision. Historical resources are preserved for authorized historical access.

Real RED/GREEN: `test_student_delivery_does_not_resurrect_removed_historical_resource` failed with one resurrected document, then passed with `resources=[]`. Changed files: student/routes.py and test_sync_course_remediation.py. This deletes misleading fallback logic rather than adding a new abstraction, dependency or schema.

`browser_resource_detach_verify.py` now passes **4 actual Edge checks**, including independent enrolled Student login, legitimate first-lesson completion, current-revision delivery and F5. SQL confirms zero current links and one retained historical link; a fresh authorized Student lesson GET returns `resources=[]`; the lesson attachment area has no historical asset link. The separate course document library is outside the lesson-attachment assertion. The owned first-lesson fixture explicitly uses allowed zero completion thresholds so progression is established through the actual completion button/HTTP, not by editing progress rows.

The earlier three resource checks passed again: failed detach preserves UI/SQL; pending detach waits for the correct Admin review; cloned draft detach/resave/submit/approval/F5 retains the removal. CSRF was enabled in this browser run. File validation used the explicit testing scanner policy; no external ClamAV claim.

## Affected delivery regressions

The expanded SQL selection covers the course regression file, lesson/video delivery, Student backend completion and revision lifecycle. Its first run had 32 passed and 20 setup errors because the old dirty-file fixture marked a QUARANTINED revision `is_current=True`, violating SQL's current-ACTIVE trigger. The fixture now sets `is_current=False`, matching scanner failure semantics; SQL guards remain enabled. Final inspected result: **52 passed in 194.98 seconds, zero failures/skips, runner exit 0**. Log: `sqlserver-student-resource-delivery.log`, same verified disposable target and migration head. No result is inferred from partial output.

Current global Ruff/format **337 files** and mypy **96 sources** passed. No commit, push, deployment, live migration or live restore.
