# Configuration

## Secrets
`SECRET_KEY`, JWT signing secret/key, DB credentials, Gemini API key, email credentials. Never commit.

## Non-secret / configurable defaults
Environment, public base URL, upload type/size limits, storage quotas/warning thresholds, retention days (confirmed enrollment detail 30 days), AI chat inactivity 5 minutes, lease/heartbeat interval, autosave debounce 1–2 seconds, rate limits, parser time/resource limits, pagination sizes, email retry/timeouts. Thresholds not locked by Plan Mode remain tunable.
