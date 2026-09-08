# Request / Response Contracts

## Standard success
Resource responses expose public UUID/GUID, allowed fields, lifecycle status, timestamps and optional `row_version` token for optimistic concurrency. Internal IDs, storage keys, password/token material and hidden correct-answer metadata are omitted.

## Pagination
`{ "items": [...], "page": 1, "page_size": 50, "total": 123 }` or a cursor form when query cost warrants it. Filters/sort are server allow-listed.

## Attempt answer save
Request contains `lease_token`, `client_change_id` UUID, monotonically increasing `client_sequence`, and answer payload specific to question type. Response returns server accepted sequence/version and `saved_at`.

## AI answer
Returns answer text, source references/version identifiers authorized for the actor, insufficiency/out-of-scope status when applicable, and no raw protected context.
