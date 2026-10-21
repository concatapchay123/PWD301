"""Generate Comprehensive System Inventory for PWD301 Full-Stack QA Audit."""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "src")
from pwd301 import create_app
from pwd301.extensions import db
import pwd301.models.identity
import pwd301.models.course
import pwd301.models.assessment
import pwd301.models.attempt_regrade
import pwd301.models.file_import
import pwd301.models.notification_audit
import pwd301.models.operations
import pwd301.models.playback
import pwd301.models.question_bank
import pwd301.models.ai_rag

app = create_app("testing")

with app.app_context():
    # 1. Routes
    routes = []
    for rule in app.url_map.iter_rules():
        methods = sorted(list(rule.methods - {"HEAD", "OPTIONS"}))
        blueprint = rule.endpoint.split(".")[0] if "." in rule.endpoint else "core"
        routes.append({"rule": rule.rule, "endpoint": rule.endpoint, "methods": methods, "blueprint": blueprint})
    routes.sort(key=lambda x: (x["blueprint"], x["rule"], x["endpoint"]))

    # 2. Models
    tables = []
    for tbl_name, table in db.metadata.tables.items():
        cols = [c.name for c in table.columns]
        tables.append((tbl_name, cols))
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

    out_file = Path("qa-fullstack-audit/03-SYSTEM-INVENTORY.md")
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
        f.write("| Table Name | Column Count | Domain | Sample Columns |\n|---|---|---|---|\n")
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
            sample_cols = ", ".join(cols[:4]) + ("..." if len(cols) > 4 else "")
            f.write(f"| `{tbl}` | {len(cols)} cols | {domain} | {sample_cols} |\n")

        f.write("\n## 3. Backend HTTP API Endpoints Inventory\n\n")
        f.write("| Blueprint | Methods | Route Path | Endpoint Name |\n|---|---|---|---|\n")
        for r in routes:
            f.write(f"| `{r['blueprint']}` | `{', '.join(r['methods'])}` | `{r['rule']}` | `{r['endpoint']}` |\n")

print(f"System inventory generated at {out_file} with {len(routes)} routes and {len(tables)} tables.")
