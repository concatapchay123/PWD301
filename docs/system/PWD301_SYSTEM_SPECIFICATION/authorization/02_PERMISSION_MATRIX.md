# Permission Matrix

Legend: ✓ allowed when object conditions pass; R reason required; — denied.

| Resource / Action | Student | Instructor owner/current manager | Other Instructor | Admin | Conditions |
|---|---:|---:|---:|---:|---|
| Course catalog view | ✓ | ✓ | ✓ | ✓ | Published/discoverable visibility |
| Course draft view | — | ✓ | — | ✓ | Owner/current manager or Admin |
| Course create | — | ✓ | ✓ | ✓ | Instructor role |
| Course update | — | ✓ | — | ✓ R | Admin override audited + reason + notify owner |
| Course publish request | — | ✓ | — | ✓ | Material change follows approval |
| Course archive/delete | — | ✓ | — | ✓ R | Prerequisite dependency/history rules |
| Lesson manage/reorder | — | ✓ | — | ✓ R | Same Course authorization |
| Enroll/leave self | ✓ | ✓ | ✓ | ✓ | As Student identity; prerequisite/capacity rules |
| Student progress view | Own | Managed Course | — | ✓ R for individual detail | Aggregate may be broader |
| Question Bank view/manage | — | ✓ | — | ✓ R | Question belongs managed Course |
| Assessment create/edit | — | ✓ | — | ✓ R | Timing/structure/point lock rules |
| Assessment attempt start | ✓ | ✓ | ✓ | ✓ | User enrolled/eligible; acts as self |
| Attempt view | Own | Managed Course final/detail policy | — | ✓ R | Active answers protect correct-answer data |
| Attempt answer save/submit | Own only | Own only | Own only | Own only | Valid lease/deadline |
| Essay grade | — | ✓ | — | ✓ R | Managed Course; grade history |
| Grade export | — | ✓ | — | ✓ | Managed Course; sensitive export |
| File resource download | Authorized learner | Managed Course | — | ✓ | App route authorization + safe active revision |
| File upload/manage | — | ✓ | — | ✓ R | Quota + security pipeline |
| Import/AI question review | — | ✓ | — | ✓ R | Managed Course |
| Student AI | Own authorized scope | Own-as-student | Own-as-student | Own-as-student | AI tools cannot bypass permissions |
| Instructor AI on Course | — | ✓ | — | ✓ | Current course authorization |
| Notification read | Own | Own | Own | Own | Recipient only |
| Audit read | — | Limited own relevant history if exposed | — | ✓ | Sensitive audit permission |
| User role/suspend | — | — | — | ✓ R | Sensitive action; reauth/audit/notify |
| Backup trigger/restore | — | — | — | ✓ R | Restore: reauth + phrase + reason + audit |
