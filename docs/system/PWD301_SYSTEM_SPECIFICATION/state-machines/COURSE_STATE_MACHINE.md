# Course state machine

See the [replacement contract](../implementation/WORKFLOW_SUPERSESSION.md).

```mermaid
stateDiagram-v2
    [*] --> NeverApprovedDraft
    NeverApprovedDraft --> InitialPending: submit
    InitialPending --> NeverApprovedDraft: reject or withdraw
    InitialPending --> ApprovedBaseline: Admin approves
    ApprovedBaseline --> StagingDraft: explicit instructor save
    StagingDraft --> FrozenSubmission: submit aggregate
    FrozenSubmission --> ApprovedBaseline: approve exact version atomically
    FrozenSubmission --> StagingDraft: withdraw or reject with complete successor
    StagingDraft --> ApprovedBaseline: discard proposal
    ApprovedBaseline --> Archived: archive if dependencies permit
    Archived --> ApprovedBaseline: restore
```

Approved baseline includes APPROVED, PUBLISHED and historically approved courses.
Legacy published courses missing approved_at remain review-required. Course
baseline status and aggregate status are separate; no transition resets prior
approval to free authoring. Pending submissions freeze all instructor mutators.
