# Storage Management

Apply per-Course/per-Instructor quotas; Admin can raise limits. Warn before critical free-space threshold; block new uploads when critically low rather than risking disk exhaustion. Physical blobs deduplicate and delete only when no logical references remain and recovery window expires. Secure exports and old file revisions have explicit cleanup.
