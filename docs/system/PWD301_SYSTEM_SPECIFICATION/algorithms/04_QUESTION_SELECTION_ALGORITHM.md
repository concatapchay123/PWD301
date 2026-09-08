# Question Selection Algorithm

At Attempt start under transaction: include all mandatory assignments; resolve blueprint rules and eligible pool; verify enough candidates; prefer less-recently-used candidates when multiple satisfy; use cryptographically adequate/non-predictable randomized selection for fairness, not client randomness; materialize exact selected QuestionRevision, assigned points and question order into Attempt snapshot. Shuffle choices when enabled and persist exact order. Never regenerate on resume/takeover.
