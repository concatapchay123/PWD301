# Secret Management

Secrets must be outside Git and Docker image, injected by environment/secret store. Rotate DB/JWT/Gemini/email credentials without code changes. Logs/config diagnostics print only presence/source labels, never values. Separate development secrets from production. Compromised signing/Flask secret triggers explicit revocation/rotation procedure.
