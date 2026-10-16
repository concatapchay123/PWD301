# Course Management

## Confirmed rules
- Course code and title are globally unique.
- Course code and title are globally unique.
- Course normally has exactly one Instructor owner; owner is only null when the assigned instructor account is suspended (`SUSPENDED`).
- Admin can assign unassigned courses (`owner_instructor_id IS NULL`) or transfer/swap courses between instructors atomically (`COURSE_OWNER_REASSIGNED`, `COURSE_OWNER_SWAPPED`). Prior owner immediately loses current Student detail access. Two distinct reassignment modes are enforced: (1) Assign unassigned courses, and (2) Transfer or 2-way atomic swap between instructors.
- The [replacement contract](../implementation/WORKFLOW_SUPERSESSION.md) governs direct authoring before first approval, mandatory aggregate staging afterward, frozen submissions, complete withdrawal/rejection restoration and atomic version-bound review. Per-feature approvals are forbidden.
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
