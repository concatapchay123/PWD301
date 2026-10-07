# Course State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> REVIEW: submit
    REVIEW --> PUBLISHED: approve
    REVIEW --> DRAFT: reject/change
    PUBLISHED --> ARCHIVED: archive
    ARCHIVED --> PUBLISHED: restore if valid
    DRAFT --> TRASH: delete
    ARCHIVED --> TRASH: delete/recovery workflow
    TRASH --> ARCHIVED: restore

    state "Published Course Working Draft (COURSE_VERSION_CHANGESET)" as Changeset {
        PUBLISHED --> Changeset_DRAFT: instructor edits (isolated draft)
        Changeset_DRAFT --> Changeset_PENDING: submit all changes
        note right of Changeset_PENDING
            FAIL-CLOSED LOCK:
            All instructor mutations locked
            Students view PUBLISHED version
        end note
        Changeset_PENDING --> Changeset_DRAFT: retract submission
        Changeset_PENDING --> PUBLISHED: admin approve (atomic apply)
        Changeset_PENDING --> Changeset_REJECTED: admin reject (with reason)
        Changeset_REJECTED --> Changeset_DRAFT: instructor modifies draft
        Changeset_DRAFT --> PUBLISHED: discard draft
    }
```

## Semantics
- Primary course lifecycle follows DRAFT → REVIEW → PUBLISHED → ARCHIVED/TRASH.
- For published courses, all updates (add/edit/delete/reorder lessons) are staged into an atomic `COURSE_VERSION_CHANGESET`.
- Fragmented or piecemeal approvals are strictly banned.
- When submitted for review (`Changeset_PENDING`), the course is locked fail-closed against instructor mutations until Admin approves or rejects, or instructor retracts.
- Active students continue learning without disruption while changes are staged.

