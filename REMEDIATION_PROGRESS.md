# Data Synchronization Remediation Progress

**Status: IN_PROGRESS — baseline and revalidation; no system completion claim.**

Audit snapshot: 926fce6727c5dbdcf428b37ac143e8b46ac305e6.
Current HEAD: 6fbe22dff1516d3fc0555c80bdfdb5e70f8f996f. Existing dirty working tree is preserved; no reset, checkout, staging or commit performed.

ChatGPT Project connection verified against current HEAD and dirty state. C2C task: c2c_a731; PLAN iteration 0 received and read on 2026-10-07. Phase 0 requires current-source revalidation of all 57 findings before production edits. First implementation unit: SYNC-042 account-scoped ExamStore isolation; test first, preserve existing dirty changes, independently reviewed by ChatGPT after execution.

Baseline frontend: node --test --test-reporter=tap over all tests/frontend/*.test.js: 115 passed, 0 failed, 0 skipped, exit 0. Existing tests alone are not persistence proof.
Backend pytest not yet run: tests/conftest.py contains SQL Server destructive cleanup. Use explicitly isolated SQLite/test target before any backend run. No database migration, backup or restore executed.

| Finding | Severity | Root Cause | Current Status | Fix Status | Tests | Evidence |
|---|---|---|---|---|---|---|
| SYNC-001 | P1 | G13 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-002 | P0 | G09 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-003 | P1 | G09 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-004 | P0 | G04 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-005 | P0 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-006 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-007 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-008 | P2 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-009 | P0 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-010 | P0 | G03 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-011 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-012 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-013 | P1 | G05 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-014 | P1 | G05 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-015 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-016 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-017 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-018 | P2 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-019 | P2 | G15 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-020 | P2 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-021 | P2 | G15 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-022 | P1 | G12 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-023 | P1 | G12 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-024 | P2 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-025 | P1 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-026 | P1 | G03 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-027 | P0 | G07 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-028 | P1 | G06 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-029 | P0 | G07 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-030 | P1 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-031 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-032 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-033 | P2 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-034 | P2 | G07 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-035 | P2 | G03 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-036 | P1 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-037 | P2 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-038 | P2 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-039 | P2 | G08 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-040 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-041 | P0 | G03 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-042 | P0 | G08 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-043 | P1 | G08 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-044 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-045 | P1 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-046 | P2 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-047 | P1 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-048 | P1 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-049 | P2 | G04 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-050 | P2 | G14 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-051 | P2 | G03 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-052 | P2 | G02 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-053 | P2 | G11 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-054 | P2 | G01 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-055 | P2 | G12 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-056 | P1 | G10 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
| SYNC-057 | P2 | G11 | NEEDS REVALIDATION | NOT_FIXED | Not yet executed for this finding | Audit is historical; current source/test evidence required |
