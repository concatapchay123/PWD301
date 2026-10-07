# Course Management

## Confirmed rules
- Course code and title are globally unique.
- Course normally has one Instructor owner but owner may be temporarily null.
- Admin can reassign; prior owner loses current Student detail access.
- Course updates on published courses are staged into an isolated working draft changeset (COURSE_VERSION_CHANGESET). All additions, edits, reordering, and deletions are bundled together into a single atomic change request submitted to Admin. Piecemeal or fragmented per-lesson approvals are strictly forbidden. While a changeset is pending Admin review (PENDING), all instructor mutations are locked fail-closed (409 Conflict). Admin reviews the consolidated side-by-side text diff and executes atomic approve or reject.
- Course referenced as prerequisite by an active Course cannot be archived/deleted until dependency resolved.
- Course with students is hidden/archived rather than destructive-history deletion.

## Primary persistence
`courses`, `course_prerequisites`, `course_change_requests`, `audit_events`, `notification_events`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
