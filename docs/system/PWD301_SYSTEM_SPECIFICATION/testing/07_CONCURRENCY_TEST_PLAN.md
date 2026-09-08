# Concurrency Test Plan

Run real concurrent transactions for: two enrolls for last seat; lesson reorder stale editor; simultaneous Question edits; publish vs edit; two Attempt starts/attempt-limit; two lease acquires; heartbeat vs takeover; stale offline answer vs newer answer; two submits; simultaneous manual grades; two corrections/regrade retries; FileAsset active revision swap; KnowledgeVersion active swap. Assert one valid final state and no silent overwrite.
