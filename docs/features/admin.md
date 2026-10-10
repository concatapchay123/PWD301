# Admin

Canonical references:

- [`business/15_AUDIT_AND_ADMIN_ACTIONS.md`](../system/PWD301_SYSTEM_SPECIFICATION/business/15_AUDIT_AND_ADMIN_ACTIONS.md)
- [`api/12_ADMIN_API.md`](../system/PWD301_SYSTEM_SPECIFICATION/api/12_ADMIN_API.md)
- [`authorization/04_ADMIN_PERMISSION_RULES.md`](../system/PWD301_SYSTEM_SPECIFICATION/authorization/04_ADMIN_PERMISSION_RULES.md)
- [`frontend/04_ADMIN_UI_FLOWS.md`](../system/PWD301_SYSTEM_SPECIFICATION/frontend/04_ADMIN_UI_FLOWS.md)

## Canonical Change Review & Diff Governance (TASK-089)
- **3-Category Visual Diff Engine**: Admin reviews changes categorized into:
  1. `Khóa học` (Course Metadata): 100% of writable fields compared, changed fields highlighted with strike-through red original and green proposed values, unchanged fields collapsed by default.
  2. `Bài học` (Lesson Content & Media): title, summary, markdown diff with line/word additions/removals, videos, attachments.
  3. `Khung giáo trình` (Curriculum Changeset): added, modified, deleted lesson hierarchy.
- **Review Action Standards**:
  - Queue Table: `[Xem]` (inspect detail) placed first, `[Duyệt]` (quick approve with confirmation modal) placed second.
  - Detail View: `[Từ chối]` (reason prompt >= 5 chars + confirm modal) and `[Phê duyệt]` (confirm modal before apply).
- **Class Gradebook PDF**: Admins can export official class gradebook PDFs via `/admin/assessments/<id>/gradebook.pdf`.

Implementation must also consult relevant tests/acceptance criteria and the canonical database architecture before persistence changes.
