# Security Requirements

Security is defense-in-depth: authentication, object authorization, input validation, relational constraints/transactions, output encoding, audit, least privilege and operational monitoring. The application DB login must not be `sa`/db_owner for routine runtime. Migration/backup privileges are separated. Secrets are injected via environment/secret mechanism and excluded from source, images and logs.

High-risk fail-closed paths: suspended auth, required audit for sensitive action, file scan, assessment deadline/lease, RAG authorization.
