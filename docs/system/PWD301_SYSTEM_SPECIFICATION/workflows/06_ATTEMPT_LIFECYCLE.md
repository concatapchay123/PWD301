# Attempt Lifecycle

Eligibility/start transaction → snapshot materialization → in-progress + lease → save/resume/offline reconciliation → submit or server expiration → objective grading → pending manual grading if essay → graded/final result. Cancellation uses explicit terminal state. Lease takeover does not create new Attempt.
