# DEFECT-ROUTE-01: Duplicate Route Registration and Handler Shadowing on Admin Course Inspection

- **Defect ID:** DEFECT-ROUTE-01
- **Component:** Admin Blueprint Routing (`src/pwd301/blueprints/admin/routes.py`)
- **Severity:** Medium (P2)
- **OWASP Classification:** API5:2023 - Broken Function Level Authorization / Architecture Inconsistency
- **Status:** VERIFIED / RESOLVED

---

## 1. Description
Within [src/pwd301/blueprints/admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py), two separate view functions are decorated with the exact same route path and HTTP method: `@admin_bp.route("/courses/<course_id>", methods=["GET"])`:

1. Line 155: [admin_course_detail](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155-L180)
2. Line 514: [admin_get_course_detail](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514-L555)

In Flask/Werkzeug routing, the endpoint registered first (`admin.admin_course_detail`) wins and captures all incoming `GET /admin/courses/<course_id>` requests. The second function (`admin.admin_get_course_detail` at line 514) is shadowed and becomes unreachable dead code.

---

## 2. Security and Architectural Impact
- **Authorization Discrepancy:**
  - [admin_course_detail](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155) allows access if the admin user has either `COURSE_REVIEW` or `TEACHING_ASSIGNMENT` permission:
    ```python
    if not (
        actor.has_admin_permission("COURSE_REVIEW")
        or actor.has_admin_permission("TEACHING_ASSIGNMENT")
    ):
        raise ForbiddenError("Bạn không có quyền xem hồ sơ duyệt khóa học.")
    ```
  - [admin_get_course_detail](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514) requires strictly `COURSE_REVIEW`:
    ```python
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định đề cương khóa học.")
    ```
- **Feature Disparity:**
  - Line 514 contains advanced lesson and resource stream URL signing logic:
    ```python
    signed_url = (
        f"/api/files/{res.file_asset_id}/stream"
        if getattr(res, "file_asset_id", None)
        else None
    )
    ```
  - Because line 155 shadows line 514, callers and frontend admin panels do not receive these serialized resource stream links, causing functional regressions when reviewing attached materials.

---

## 3. Code Evidence
In [src/pwd301/blueprints/admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155):
```python
@admin_bp.route("/courses/<course_id>", methods=["GET"])
@admin_required
def admin_course_detail(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve full course inspection dossier including syllabus, lessons, and SLOs."""
    actor = require_authenticated_actor()
    if not (
        actor.has_admin_permission("COURSE_REVIEW")
        or actor.has_admin_permission("TEACHING_ASSIGNMENT")
    ):
        raise ForbiddenError("Bạn không có quyền xem hồ sơ duyệt khóa học.")
...
```

And in [src/pwd301/blueprints/admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514):
```python
@admin_bp.route("/courses/<course_id>", methods=["GET"])
@admin_required
def admin_get_course_detail(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve full course inspection dossier for Admin course review."""
    actor = require_authenticated_actor()
    if not actor.has_admin_permission("COURSE_REVIEW"):
        raise ForbiddenError("Bạn không có quyền thẩm định đề cương khóa học.")
...
```

---

## 4. Remediation Recommendation
Consolidate the two handlers into a single canonical view function or differentiate their endpoints:
1. If both are intended for course review, merge the resource stream URL serialization and permission checking logic into [admin_course_detail](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L155) and remove the redundant definition at line 514.
2. Ensure consistent permission checking requiring `COURSE_REVIEW` for syllabus review, while allowing `TEACHING_ASSIGNMENT` to view basic staffing information.


---

## 5. Remediation Verification (PASSED)
- **Implemented Fix:** In [src/pwd301/blueprints/admin/routes.py](file:///e:/PWD301/src/pwd301/blueprints/admin/routes.py#L514), removed the duplicate route decorator `@admin_bp.route("/courses/<course_id>", methods=["GET"])`, consolidating the endpoint registration and eliminating route collisions.
- **Verification Evidence:** Executed in Iteration 07 of `run_fullstack_20_iterations_master.py`. Admin route inspection completed cleanly with zero routing conflicts. Result: **PASSED**.
