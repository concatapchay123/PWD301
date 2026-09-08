# Import Job State Machine

```mermaid
stateDiagram-v2
[*] --> QUEUED
QUEUED --> PROCESSING
PROCESSING --> REVIEW_REQUIRED: parsed
PROCESSING --> FAILED: unrecoverable
REVIEW_REQUIRED --> COMPLETED: Instructor review/promote
FAILED --> QUEUED: explicit/retryable retry
```

## Semantics
Imported questions remain drafts until Instructor approval.
