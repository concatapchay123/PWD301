# Historical Notification Disposition Approval Packet

Date: 2026-10-06
Scope: read-only SQL Server inspection for the notification audit
Status: **OPEN — approval required; no historical row was changed**

## Purpose

This packet records the exact historical notification rows that cannot be safely
reassigned, merged, deleted or rewritten from the current database alone. It is
an approval input, not a repair script. The notification and audit tables are
append-only for this decision; no owner approval was inferred from the audit
request.

SMTP/inbox delivery is **OUT OF SCOPE** for this cycle. The email rows below are
included only as stored database evidence; no external delivery was attempted.

## Read-only evidence query

The live `PWD301` SQL Server database was inspected through the `pwd301_db`
container using `sqlcmd` with `SELECT` statements only. The selection windows
were:

- `LESSON_CHANGE_REQUEST`: `2026-09-28 03:10:04` through
  `2026-09-28 03:16:28.999` UTC.
- `COURSE_CHANGE_APPROVED`: `2026-09-28 05:44:15` through
  `2026-09-28 05:44:22.999` UTC, plus `2026-09-29 02:09:31` through
  `2026-09-29 02:09:31.999` UTC.

The query joined `notification_events`, `notifications`, `users` and
`email_deliveries`; it did not issue `INSERT`, `UPDATE` or `DELETE`.

The direct verification output was:

```text
scoped_events  distinct_event_keys  linked_notifications  linked_emails
17             17                   17                    17
duplicate_event_key_groups: 0
orphan_event_rows: 0
```

The selected event IDs were `50002` through `50014`, `60002` through `60004`
and `90006`.

## Exact rows in scope

| Group | Event IDs | Notification IDs | Email IDs | Recipient | Stored event type | Count |
|---|---:|---:|---:|---|---|---:|
| A | 50002–50014 | 60002–60014 | 10002–10014 | user 1 (`admin@pwd301.local`) | `LESSON_CHANGE_REQUEST` | 13 |
| B | 60002–60004, 90006 | 70002–70004, 100006 | 20002–20004, 50006 | user 2 (`instructor1@pwd301.local`) | `COURSE_CHANGE_APPROVED` | 4 |
| **Total** | 17 events | 17 notifications | 17 email rows | — | — | **17** |

Each row has one linked notification and one linked email-delivery row. The
event keys are unique. Therefore the evidence supports **17 repeated-copy
records**, not a proven 17-row duplicate-delivery incident.

## Business-identity assessment

### Group A — 13 lesson-change copies

- All 13 rows have the same recipient, role, title and body.
- The body names course `CS101` and lesson `Bài 1: Tổng quan về Kiến trúc Web & HTTP Protocol`.
- The stored event payload contains only the generic action URL
  `#/admin/governance?tab=courses`.
- `target_id`, `correlation_id` and a durable change-request identity are not
  available in the event/notification record.
- The exact event window contains no matching current
  `course_change_requests` row.
- Current CS101 has internal course ID `70013` and public ID
  `5DA5CFBC-28A5-4DB8-A478-F634676F2C67`; the matching lesson title exists in
  more than one current/historical lesson row, including lesson IDs `80046`
  and `90018`.
- Current requests for those lesson rows occur at different times and cannot be
  joined deterministically to the 13 historical events.

Disposition: **ambiguous — owner mapping required**.

### Group B — 4 course-approved copies

- All four rows have the same recipient, role, title and body.
- The title/body names the same lesson, but do not contain a request ID,
  course public ID, lesson public ID or correlation ID.
- The action URL contains the stale UUID
  `cf547469-d8b8-43ef-882c-721048826232`, which is absent from the current
  `courses` table.
- Current course `CS101` has a different public ID, and the current database
  contains multiple lesson-change candidates at later timestamps.
- The exact historical windows do not contain a safely joinable request row.

Disposition: **ambiguous — owner mapping required**.

## Outbox evidence

All 17 linked `email_deliveries` rows preserve a recipient snapshot, template
code, random dedupe UUID and `PENDING` status. `subject`, `body_text`,
`course_change_request_id`, target-resource and correlation fields do not add a
safe business identity. These rows must not be treated as inbox-delivery proof.

## Approval decision required

An authorized business/data owner must choose one disposition for each group or
each explicitly listed row:

1. **Retain unchanged as historical evidence** — recommended default while
   identity is unresolved.
2. **Annotate through an approved append-only disposition record** — only after
   the owner supplies the exact business identity and reason.
3. **Repair in a disposable rehearsal first, then approve a production change**
   — requires exact old/new values, affected IDs, rollback plan, audit entry and
   a post-change count/consistency check.

No option authorizes deleting or merging these rows merely because their copy is
identical. A repair must be rejected if the proposed mapping relies only on
title text, recipient, timestamp proximity or the stale action URL.

## Acceptance gate

This gate is **not passed** until the owner records, for all 17 rows or an
explicit group-level decision:

- business event identity (`course_change_request_id`, file/revision ID or an
  explicitly approved legacy identity);
- intended action (`retain`, `annotate`, `repair`, or `do not change`);
- owner/approver and approval timestamp;
- disposable rehearsal result before any live mutation;
- exact post-change verification, if a change is eventually authorized.

Current safe conclusion: **preserve all 17 rows unchanged**. No repair,
deletion, merge or reassignment was performed in this audit continuation.
