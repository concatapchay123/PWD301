# PWD301 — Deployment, Operations & Demonstration Guide

This document provides complete instructions for orchestrating, deploying, operating, and presenting the **PWD301 Online Course Management Platform** in Docker containerized environments.

Canonical specification references:
- [`docs/system/PWD301_SYSTEM_SPECIFICATION/operations/01_DOCKER_AND_ENVIRONMENT.md`](system/PWD301_SYSTEM_SPECIFICATION/operations/01_DOCKER_AND_ENVIRONMENT.md)
- [`docs/system/PWD301_SYSTEM_SPECIFICATION/operations/02_CONFIGURATION.md`](system/PWD301_SYSTEM_SPECIFICATION/operations/02_CONFIGURATION.md)
- [`docs/system/PWD301_SYSTEM_SPECIFICATION/operations/06_SYSTEM_HEALTH.md`](system/PWD301_SYSTEM_SPECIFICATION/operations/06_SYSTEM_HEALTH.md)

---

## 1. Architecture Overview

The PWD301 platform orchestrates three primary container services within an isolated bridge network (`pwd301_net`):

```
                       +---------------------------------------------------+
                       |              Docker Host Network                  |
                       +---------------------------------------------------+
                                                 |
                                     Port 5000:5000 (HTTP / WSGI)
                                                 v
                     +-------------------------------------------------------+
                     |                     web service                       |
                     |  - Image: pwd301-web (multi-stage Python 3.12-slim)   |
                     |  - WSGI: Gunicorn (4 sync workers, bind 0.0.0.0:5000) |
                     |  - User: appuser:appgroup (UID 10001 / non-root)     |
                     |  - MS ODBC Driver 18 for SQL Server (TLS encrypted)   |
                     +-------------------------------------------------------+
                                  |                             |
                       Port 1433  |                             | Port 3310
                      (TCP / TLS) |                             | (TCP ClamD)
                                  v                             v
       +------------------------------------+  +------------------------------------+
       |             db service             |  |           clamav service           |
       |  - Image: mssql/server:2022-latest |  |  - Image: clamav/clamav:latest     |
       |  - DB: PWD301                      |  |  - Port: 3310 (ClamD stream scan)  |
       |  - Collation: Vietnamese_100_CI_AS |  |  - Fail-closed security architecture|
       |  - Volume: sqldata                 |  |  - Volume: clamav_defs             |
       +------------------------------------+  +------------------------------------+
```

### Storage Volumes

| Volume Name (Compose / Named) | Mount Path in Container | Service | Purpose |
|-------------------------------|-------------------------|---------|---------|
| `sqldata` (`pwd301_sqldata`) | `/var/opt/mssql` | `db` | Persistent SQL Server MDF/LDF data files |
| `clamav_defs` (`pwd301_clamav_defs`) | `/var/lib/clamav` | `clamav` | Persistent ClamAV virus signature definitions |
| `storage_data` (`pwd301_storage_data`) | `/app/storage` | `web` | Active clean uploaded file assets and blobs |
| `quarantine_data` (`pwd301_quarantine_data`) | `/app/quarantine` | `web` | Isolated quarantine store for unscanned/infected files |
| `backup_data` (`pwd301_backup_data`) | `/app/backups` | `web` | Database and asset disaster recovery backups |
| `export_data` (`pwd301_export_data`) | `/app/exports` | `web` | Data exports (gradebooks, audit logs, reports) |


---

## 2. Prerequisites

- **Docker Engine**: Version 24.0.0 or higher.
- **Docker Compose**: Version v2.20.0 or higher.
- **Hardware Recommendations**:
  - Minimum 4 GB RAM (Microsoft SQL Server requires >= 2 GB RAM).
  - Minimum 10 GB available disk space.
  - 2+ CPU cores.

---

## 3. 1-Command Startup

To build images, initialize database volumes, apply migrations, seed baseline & demonstration datasets, and start all services in the background:

```bash
docker compose up --build -d
```

To stream real-time logs across all services:

```bash
docker compose logs -f web
```

To stop all services while preserving database and volume data:

```bash
docker compose down
```

To stop and purge all containers, networks, and persistent data volumes:

```bash
docker compose down -v
```

---

## 4. Automated Container Bootstrap Lifecycle

When the `web` container starts, `scripts/docker-entrypoint.sh` orchestrates an automated 4-stage bootstrap pipeline before handing execution over to the production Gunicorn WSGI server:

```
[Entrypoint Stage 1] wait_for_db.py
   ├── Probes Microsoft SQL Server TCP port 1433 with exponential backoff (up to 30 retries)
   └── Connects to master database and auto-creates database PWD301 if it does not exist
          │
[Entrypoint Stage 2] flask db upgrade
   └── Executes Alembic migration revisions up to head on PWD301 database
          │
[Entrypoint Stage 3] flask seed baseline
   └── Seeds canonical system roles (STUDENT, INSTRUCTOR, ADMIN) and root administrator
          │
[Entrypoint Stage 4] flask seed demo (conditional: SEED_DEMO_DATA=true)
   └── Populates complete demo accounts, courses, lessons, question bank, attempts & audit logs
          │
[Entrypoint Stage 5] exec gunicorn wsgi:app
   └── Boots production WSGI server under non-root appuser (UID 10001)
```

---

## 5. Health Check & Readiness Endpoints

The application exposes standard monitoring endpoints compliant with ADR-002 Zero PK Leakage:

### 5.1 Liveness Probe (`/health`)

Checks if the Flask HTTP process is running and responding:

```bash
curl -i http://localhost:5000/health
```

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "app": "PWD301",
  "version": "1.0.0"
}
```

### 5.2 Deep Readiness Probe (`/health/deep`)

Validates operational connectivity to Microsoft SQL Server (`SELECT 1`), ClamAV antivirus TCP daemon (`PING` -> `PONG`), and available storage capacity:

```bash
curl -i http://localhost:5000/health/deep
```

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "database": "connected",
  "antivirus": "connected",
  "storage": "operational"
}
```

---

## 6. Comprehensive Demonstration Dataset

When `SEED_DEMO_DATA=true` (enabled by default in `docker-compose.yml`), the system seeds a realistic, comprehensive showcase dataset.

### 6.1 Demonstration Accounts

All demonstration accounts are configured with the unified standard password:  
**`Password123!`**

| Email | Display Name | Assigned Roles | Demonstration Purpose |
|-------|--------------|----------------|-----------------------|
| `admin@pwd301.local` | Quản trị viên Hệ thống | `ADMIN`, `INSTRUCTOR`, `STUDENT` | System management, course review/approval, audit inspection |
| `instructor1@pwd301.local` | TS. Nguyễn Văn A | `INSTRUCTOR`, `STUDENT` | Course author (CS101, CS201), manual essay grading |
| `instructor2@pwd301.local` | ThS. Trần Thị B | `INSTRUCTOR`, `STUDENT` | Course author (CS301 submitted for review) |
| `student1@pwd301.local` | Lê Hoàng Nam | `STUDENT` | 100% completed student (active enrollment, perfect exam score) |
| `student2@pwd301.local` | Phạm Minh Tuấn | `STUDENT` | Submitted exam awaiting manual essay evaluation |
| `student3@pwd301.local` | Đỗ Mai Anh | `STUDENT` | Active student in-progress |
| `student4@pwd301.local` | Hoàng Gia Bảo | `STUDENT` | Clean account (0 enrollments) for live registration/enrollment showcase |

### 6.2 Courses & Prerequisite Architecture

1. **CS101: Lập trình Python & Flask Web Nâng Cao**
   - **Status:** `PUBLISHED`
   - **Instructor:** `instructor1@pwd301.local`
   - **Content:** 2 rich Markdown lessons with downloadable PDF study attachment.
   - **Assessment:** Midterm Exam (`PUBLISHED`) with 5 question types.
2. **CS201: Cấu trúc Dữ liệu, Giải thuật & Thiết kế Hệ thống**
   - **Status:** `DRAFT` (authoring stage)
   - **Prerequisite:** Linked to CS101 (demonstrating cycle-free prerequisite validation).
3. **CS301: Trí tuệ Nhân tạo & Xử lý Ngôn ngữ Tự nhiên RAG**
   - **Status:** `SUBMITTED_FOR_REVIEW` (demonstrates Admin review and approval workflow).

### 6.3 Question Bank (Bloom's Taxonomy Coverage)

The CS101 assessment contains 5 distinct question types:
- **`SINGLE_CHOICE`**: Flask routing decorator `@app.route()` (Bloom: *Remember*).
- **`MULTIPLE_CHOICE`**: Idempotent HTTP methods `GET`, `PUT`, `DELETE` (Bloom: *Understand*).
- **`TRUE_FALSE`**: Zero PK Leakage ADR-002 security invariant (Bloom: *Analyze*).
- **`SHORT_ANSWER`**: Database migration tool `Alembic` with normalized matching (Bloom: *Apply*).
- **`ESSAY`**: In-depth architectural analysis of connection pooling and exhaustion (Bloom: *Evaluate*).

### 6.4 Assessment Attempts & Live Grading Scenario

- **Student 1 (`student1@pwd301.local`)**:
  - Completed all lessons (100% progress).
  - Attempt Status: `GRADED`, Score: **20.0 / 20.0 (100%)**, Result: `RELEASED`.
  - Both auto-graded questions and manual essay grade are finalized with instructor feedback.
- **Student 2 (`student2@pwd301.local`)**:
  - Attempt Status: `SUBMITTED`, Objective score: 12.0 / 20.0.
  - Essay Question Status: `PENDING` manual grading.
  - **Live Demonstration Flow:**
    1. Log in as `instructor1@pwd301.local` (`Password123!`).
    2. Open Instructor Assessment Grading view.
    3. Select Student 2's submission.
    4. Review the essay answer, enter awarded points (e.g. `3.5 / 4.0`), provide feedback, and click **Submit Grade**.
    5. Observe score aggregation and automatic notification generation!

---

## 7. Container Test Execution

To run the platform test suite directly inside the running container environment:

```bash
# Run complete test suite (814+ tests)
docker compose exec web pytest

# Run demo seeding and integration tests specifically
docker compose exec web pytest tests/integration/test_demo_seed.py -v

# Run contract and security tests
docker compose exec web pytest tests/contract/ tests/security/
```

---

## 8. Security & Operational Hardening

- **Non-Root Execution:** The web container runs under non-privileged system user `appuser:appgroup` (UID `10001`, GID `10001`). No container process runs as `root`.
- **Fail-Closed Antivirus:** File uploads are directed to an isolated quarantine area. Files are only accessible to students once ClamAV confirms a clean scan verdict (`CLEAN`).
- **Zero PK Leakage (ADR-002):** Internal `BIGINT` auto-increment primary keys are strictly forbidden from appearing in API responses, URLs, session cookies, and client HTML templates; UUID/GUID public identifiers are enforced universally.
- **Session Security:** In production mode, Flask session cookies enforce `SameSite=Lax`, `HttpOnly=True`, and `Secure` (overridable via `SESSION_COOKIE_SECURE=false` for local HTTP demonstrations).
- **Database Backup & Recovery:** SQL Server `.bak` files can be placed in `/var/opt/mssql/backup` for restoration via administrative commands. Restores require explicit administrative confirmation and never overwrite live data automatically.
