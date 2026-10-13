# Atomic Admin role removal runtime — 2026-10-13

Status: named SYNC-049 acceptance verified; whole-system IN_PROGRESS.

## A. Scope and authority

Historical SYNC-049 requires one batch request, atomic role persistence and authoritative UI refresh after success/failure. Inspected cumulative role rules, mandatory STUDENT baseline, protected primary administrator, current native revoke modal, API wrapper, Admin route transaction and user role services. Original audit and unrelated work preserved.

## B. Reuse decisions

Existing implementation meets this requirement: `ApiClient.removeRoles` submits one POST with `action:remove` and the selected `roles`; existing Admin route invokes role operations with `commit=False`, commits once and rolls back validation/authorization failures. Native modal refreshes the current route in finally. No new product abstraction or source repair needed.

## C. Per-file changes

Evidence report, closure ledger, progress and change manifest only. Native ignored runner creates a unique owned disposable account through existing registration/assignment services, grants permitted ADMIN_SYSTEM_MONITORING plus cumulative roles and operates through actual password login and UI. No existing human account's roles changed. No product source, test source, configuration, model or migration edited in this increment.

## D. Deletion/simplification

Keep existing atomic batch transaction and UI refresh; avoid replacing them with another exact-role-set API. The older closure description incorrectly attributed this native path to `set_user_roles`; current code actually uses caller-owned per-role services inside one transaction. This report corrects that trace without changing the working implementation.

## E. Deferred debt

No optional debt added. Native target is a subordinate administrator, not the protected primary administrator. This does not certify every role/target combination or all concurrent authorization changes; existing broader role policy tests remain separately scoped.

## F. Actual verification

Native Edge **three checks passed**, clean terminal exit0 (`browser-admin-batch-roles-20261013.log`, `browser-admin-batch-roles-evidence.json`):

1. Real wrapper batch `[ADMIN,STUDENT]`: ADMIN removal runs first, forbidden baseline removal fails. Actual error response; independent SQL retains ADMIN/INSTRUCTOR/STUDENT and the exact original auth_version, demonstrating whole-transaction rollback.
2. Native revoke select-all selects ADMIN/INSTRUCTOR; short reason gets real400. The finally refresh sends actual user-list GET. Visible role metadata and independent SQL keep the original roles. Retry can reopen the current authoritative modal.
3. Native valid select-all sends exactly one POST containing both roles and no singular `role` field. Real server200 commits only STUDENT while ACK is held; modal remains pending until ACK. Following native refresh and F5 show only persisted STUDENT, confirmed independently in SQL. Exactly one valid mutation request.

Existing exact API regression also passes freshly on guarded migrated SQL Server: **1 passed, zero skipped/failed**,3.33s, terminal exit0 (`sqlserver-admin-batch-role-20261013.log`). This exercises atomic assignment, rollback and successful composite removal. Counts are separate evidence, not a whole-suite result.

Disposable guard enabled; actual DB_NAME/migration head checked before destructive pytest fixtures. Native runner checks owned browser baseline and creates a unique fixture; SQL runner uses a separate already-guarded testing target. No fake role API responses or service mutations used. Current source was unchanged by these checks.

Fresh OCR delegate preview/rules retrieved for native Admin/API and backend route/service files. Host review confirms one batch payload, commit=False composition, explicit rollback, protected role validation, reason requirements, native finally refresh and no unintended live account access. Repository/diff checks run after report updates; original audit diff is empty.

## G. Remaining work

Remaining audit/runtime/provider gates continue independently. Prior aggregate evidence predates the mini-quiz serializer repair; this increment does not claim a new full current-source aggregate. No commit, push, deployment, live migration or restore performed.
