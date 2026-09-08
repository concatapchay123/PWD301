# File Upload Security

Pipeline: metadata/size/type allowlist → generated storage name → quarantine → hash/dedup → malware scan → archive/parser resource checks → processing → safe → activation. Macro Office formats are rejected. Scanner unavailable/failure remains BLOCKED/PENDING. Baseline limits: image ~10 MB, PDF/DOCX 50 MB, PPTX 100 MB, video < 1 GB. Direct storage is private.
