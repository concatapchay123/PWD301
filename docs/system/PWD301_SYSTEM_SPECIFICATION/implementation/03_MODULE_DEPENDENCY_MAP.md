# Module Dependency Map

```text
auth/users → policies
courses/learning → questions → assessments → attempts/grading → regrading
files → imports → questions/assessments
notifications/audit ← domain services
ai → policy + courses/learning + knowledge metadata
workers → domain services (not direct ad-hoc DB mutation)
admin → explicit governed service APIs
```

Avoid circular imports through service interfaces/application context. AI/file adapters depend on domain policy, never the reverse.
