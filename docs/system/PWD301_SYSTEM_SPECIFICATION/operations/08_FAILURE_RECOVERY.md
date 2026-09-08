# Failure Recovery

Web request failure leaves transactions rolled back. Workers retry idempotently with bounded attempts/timeouts. Scanner outage leaves files blocked. Gemini outage disables only Gemini-dependent behavior; backend-computable features remain. Regrade/import/index jobs resume from persisted item/status. Browser crash is recovered through Attempt lease expiry/takeover. DB restore is manual-confirmed only.
