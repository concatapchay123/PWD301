# Attempt Lease Algorithm

Acquire uses conditional update: if no active lease, same tab owner, or `lease_expires_at <= now`, set owner/session, random lease token, heartbeat and new expiry. Second tab while lease valid gets `LEASE_CONFLICT`. Heartbeat validates token+owner+nonterminal attempt then extends expiry. Takeover is allowed only after stale expiry and keeps same Attempt/snapshot/deadline. Save requires current token. No DB transaction/row lock is held between requests. Lease duration is a **CONFIGURABLE DEFAULT** tuned by heartbeat/network tests.
