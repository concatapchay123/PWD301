# Autosave and Offline Reconciliation

Each client change has UUID `client_change_id` and monotonically increasing `client_sequence` per AttemptQuestion. Server transaction validates active Attempt, deadline, lease, payload type; inserts dedupe event; updates current answer only if incoming sequence is newer than stored accepted sequence. Duplicate change ID returns original acceptance. A stale offline event arriving after a newer answer is recorded but cannot overwrite current state. Any event received after deadline is rejected/not counted.
