# Submission Idempotency

Client supplies stable idempotency key. Transaction locks/conditionally updates Attempt terminal state. If result already exists for same key/Attempt, return it. If same key maps to different semantic payload, return conflict. First successful submit freezes current accepted answers, grades objective questions, creates one AssessmentResult/pending result and sets terminal timestamp/status. Concurrent submit requests converge to one logical result.
