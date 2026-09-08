# User State Machine

```mermaid
stateDiagram-v2
[*] --> ACTIVE
ACTIVE --> SUSPENDED: admin suspend
SUSPENDED --> ACTIVE: authorized restore
ACTIVE --> DEACTIVATED: account delete/deactivate
SUSPENDED --> DEACTIVATED: deactivate
DEACTIVATED --> ANONYMIZED: retention/privacy action
ANONYMIZED --> [*]
```

## Semantics
Stored status; role set is separate. Suspension invalidates auth immediately.
