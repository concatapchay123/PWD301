# File Management

## Confirmed rules
- Upload enters quarantine and is inaccessible until all required checks pass.
- Malware scanner failure/unavailable is fail-closed.
- Macro-enabled Office is forbidden; parser resource/decompression limits apply.
- Baseline sizes: image ~10 MB, PDF 50 MB, DOCX 50 MB, PPTX 100 MB, video < 1 GB.
- Blob dedup and logical asset/revision separation preserve references.
- Replacement activates only after checks; old revision recoverable ~30 days.

## Primary persistence
`file_blobs`, `file_assets`, `file_revisions`, `file_scan_results`, `lesson_resources`, `question_revision_resources`.

## Implementation obligations
- Validate state and object authorization before mutation.
- Use service-owned transaction boundaries; do not rely on UI validation.
- Emit audit/notification/job side effects only according to documented event policy.
- Preserve historical evidence instead of rewriting past records.

## Failure semantics
State violations return a stable conflict/state error; authorization failures disclose no protected details; required-audit sensitive mutations roll back.

## Tests
Trace to `../testing/03_BUSINESS_RULE_TEST_MATRIX.md`, domain-specific integration tests and `../testing/11_END_TO_END_SCENARIOS.md`.
