# File Management

## Confirmed rules
- Upload enters quarantine and is inaccessible until all required checks pass.
- Malware scanner failure/unavailable is fail-closed.
- Macro-enabled Office is forbidden; parser resource limits apply. Archives (.zip, .rar, .7z, .tar, .gz, .bz2, .xz, .iso) are strictly forbidden with exact rejection message: "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)".
- Baseline sizes: image ~10 MB, non-archive attachments <= 50 MB (50,000,000 bytes) for Word (DOCX/DOC), PDF, Excel (XLSX/XLS), PowerPoint (PPTX/PPT), Text (TXT), AutoCAD (.dwg, .dxf), and 3D models (.obj, .fbx, .stl, .blend, .step, .stp, .gltf, .glb); video < 1 GB (current operational limit, superseding older ~2 GB references).
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
