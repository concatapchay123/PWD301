"""Generate System Inventory for PWD301 QA Audit."""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "src")
from backend import create_app
from backend.extensions import db
import backend.models.identity
import backend.models.course
import backend.models.assessment
import backend.models.attempt_regrade
import backend.models.file_import
import backend.models.notification_audit
import backend.models.operations
import backend.models.playback
import backend.models.question_bank
import backend.models.ai_rag

app = create_app("testing")

with app.app_context():
    # 1. Routes
    routes = []
    for rule in app.url_map.iter_rules():
        methods = sorted(list(rule.methods - {"HEAD", "OPTIONS"}))
        routes.append({"rule": rule.rule, "endpoint": rule.endpoint, "methods": methods})
    routes.sort(key=lambda x: (x["rule"], x["endpoint"]))

    # 2. Models
    tables = []
    for tbl_name, table in db.metadata.tables.items():
        tables.append((tbl_name, len(table.columns)))
    tables.sort()

    # 3. Frontend Routes
    frontend_routes = [
        {"path": "#/auth", "role": "ANONYMOUS", "desc": "Login / Registration Form (Email, Password, Roles)"},
        {"path": "#/student/dashboard", "role": "STUDENT", "desc": "Student Learning Dashboard & Enrolled Courses"},
        {"path": "#/student/catalog", "role": "STUDENT", "desc": "Course Catalog & Discovery"},
        {"path": "#/student/courses", "role": "STUDENT", "desc": "My Learning View & Course Progress"},
        {"path": "#/student/courses/:id/intro", "role": "STUDENT", "desc": "Course Overview, Syllabus, Prerequisites"},
        {"path": "#/student/courses/:id", "role": "STUDENT", "desc": "Course Study Console & Outline"},
        {"path": "#/student/courses/:id/lessons/:lesson_id", "role": "STUDENT", "desc": "Interactive Lesson Reader, 16:9 Video & DRM"},
        {"path": "#/student/assessments", "role": "STUDENT", "desc": "Student Assessment Schedule & Exam List"},
        {"path": "#/student/assessments/:id/waiting-room", "role": "STUDENT", "desc": "Exam Waiting Room & Prerequisite Verification"},
        {"path": "#/student/assessments/attempts/:id", "role": "STUDENT", "desc": "Fullscreen Exam Focus Mode & Autosave Leases"},
        {"path": "#/student/assessments/attempts/:id/results", "role": "STUDENT", "desc": "Exam Results, Breakdown & Review"},
        {"path": "#/student/ai-assistant", "role": "STUDENT", "desc": "Octopus AI Assistant RAG Chat"},
        {"path": "#/student/become-instructor", "role": "STUDENT", "desc": "Instructor Application Form & File Upload"},
        {"path": "#/student/settings", "role": "ALL", "desc": "User Profile, Password Change & Preferences"},
        {"path": "#/instructor/dashboard", "role": "INSTRUCTOR", "desc": "Instructor Overview & Course Workload"},
        {"path": "#/instructor/courses", "role": "INSTRUCTOR", "desc": "Instructor Managed Courses List"},
        {"path": "#/instructor/courses/:id/manage", "role": "INSTRUCTOR", "desc": "Single-Page Studio, Curriculum & Staging Draft"},
        {"path": "#/instructor/prerequisites/requests", "role": "INSTRUCTOR", "desc": "Prerequisite Course Linking Approval"},
        {"path": "#/instructor/exams/hub", "role": "INSTRUCTOR", "desc": "Question Bank & Exam Management Hub"},
        {"path": "#/instructor/exams/editor", "role": "INSTRUCTOR", "desc": "Step 2: Manual Question Authoring"},
        {"path": "#/instructor/exams/interactive", "role": "INSTRUCTOR", "desc": "Step 2: Interactive Question Builder"},
        {"path": "#/instructor/exams/excel", "role": "INSTRUCTOR", "desc": "Step 2: Excel Bulk Exam Import (.xlsx)"},
        {"path": "#/instructor/exams/moodle", "role": "INSTRUCTOR", "desc": "Step 2: Moodle XML Exam Import (.xml)"},
        {"path": "#/instructor/exams/matrix", "role": "INSTRUCTOR", "desc": "Step 3: Bloom Taxonomy Matrix & Grading Spec"},
        {"path": "#/instructor/exams/settings", "role": "INSTRUCTOR", "desc": "Step 4: Scheduling, Timing & Publish Controls"},
        {"path": "#/instructor/exams/results", "role": "INSTRUCTOR", "desc": "Assessment Submissions, Grading & PDF Export"},
        {"path": "#/admin/governance", "role": "ADMIN", "desc": "Admin Governance (Users, Courses, Apps, Security)"},
        {"path": "#/admin/courses/review", "role": "ADMIN", "desc": "Initial Course Submission Review Pane"},
        {"path": "#/admin/change-requests/review", "role": "ADMIN", "desc": "Staging Draft Changeset Diff Modal & Approval"},
        {"path": "#/admin/operations", "role": "ADMIN", "desc": "System Telemetry, Backups, Health & Logs"},
    ]

    out_file = Path("qa-audit/02-SYSTEM-INVENTORY.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# SYSTEM INVENTORY & TEST COVERAGE BASELINE\n\n")
        f.write(f"- **Backend HTTP Endpoints:** {len(routes)}\n")
        f.write(f"- **Database Model Tables:** {len(tables)}\n")
        f.write(f"- **Frontend SPA Routes:** {len(frontend_routes)}\n")
        f.write(f"- **Platform Architecture:** Pure Headless REST API + Single-Page Application (SPA)\n\n")

        f.write("## 1. Frontend Route Inventory\n\n")
        f.write("| Route Path | Minimum Role | Functionality & View Description |\n|---|---|---|\n")
        for fr in frontend_routes:
            f.write(f"| `{fr['path']}` | `{fr['role']}` | {fr['desc']} |\n")

        f.write("\n## 2. Database Models & Tables Inventory\n\n")
        f.write("| Table Name | Column Count | Domain |\n|---|---|---|\n")
        for tbl, cols in tables:
            domain = "Identity & RBAC" if any(k in tbl for k in ["user", "role", "session", "auth"]) else (
                "Course & Curriculum" if any(k in tbl for k in ["course", "lesson", "unit", "prereq", "enroll"]) else (
                    "Assessment & Exams" if any(k in tbl for k in ["assess", "attempt", "question", "grade", "choice", "section"]) else (
                        "File & Streaming" if any(k in tbl for k in ["file", "playback", "resource", "asset"]) else (
                            "AI & RAG" if any(k in tbl for k in ["ai", "rag", "vector", "chat"]) else "Operations & Audit"
                        )
                    )
                )
            )
            f.write(f"| `{tbl}` | {cols} cols | {domain} |\n")

        f.write("\n## 3. Backend HTTP API Endpoints Inventory\n\n")
        f.write("| Methods | Route Path | Endpoint Name | Blueprint |\n|---|---|---|---|\n")
        for r in routes:
            bp = r["endpoint"].split(".")[0] if "." in r["endpoint"] else "root"
            methods_str = ", ".join(r["methods"])
            f.write(f"| `{methods_str}` | `{r['rule']}` | `{r['endpoint']}` | `{bp}` |\n")

    print(f"Inventory successfully written to {out_file} with {len(routes)} endpoints, {len(tables)} tables, {len(frontend_routes)} routes.")
