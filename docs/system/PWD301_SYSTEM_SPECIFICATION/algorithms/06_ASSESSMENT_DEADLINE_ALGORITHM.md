# Assessment Deadline Algorithm

```text
assert published and now >= open_at and now < close_at
started_at = server_now
deadline_at = min(started_at + time_limit, close_at)
```

If no time limit, deadline is close_at (or configured non-timed behavior when close may be absent for practice). A Student starting near close only gets remaining time. Save/submit validity compares server time to persisted `deadline_at`; browser countdown is display only. Timing configuration is immutable after publish.
