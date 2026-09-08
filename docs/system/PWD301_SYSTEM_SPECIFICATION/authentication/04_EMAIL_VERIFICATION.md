# Email Verification

Flow: request new email → normalize and ensure uniqueness → create single-purpose expiring verification token → send email → verify token and current User state → atomically activate new email → invalidate older pending email-change tokens → increment auth/security version if policy requires → audit + notify. Token values are stored hashed, single-use and expiry-limited.
