# Master Test Plan — Iteration 09: File Uploads, ClamAV Fail-Closed Scanning & YouTube 16:9 Player

## 1. Executive Summary & Iteration Target
- **Iteration ID:** `IT09`
- **Target Subsystem:** File Storage Engine, ClamAV Antivirus Daemon Integration, 50MB Non-Archive Attachment Policy, YouTube Standard 16:9 Responsive Player, Cover Poster Shield.
- **Focus Area:** File validation, security containment, media streaming integrity, and responsive video player UX:
  1. Strict 50MB Non-Archive Attachment Policy: Rejection of `.zip`, `.rar`, `.7z` with canonical Vietnamese message.
  2. Strict 50MB Attachment Ceiling: Rejection of non-video files exceeding 50,000,000 bytes.
  3. ClamAV Fail-Closed Quarantine Defense: EICAR malware detection and complete denial of student download for infected/quarantined files.
  4. Clean Learning Document Attachment Upload & Student Document Hub Access.
  5. YouTube Player Standard 16:9 Viewport: 100% width, 100% height, zero crop, uncropped aspect ratio.
  6. Cover Poster Shield & Custom Control Bar: Concealment of YouTube native controls/red play button prior to play interaction.
- **Execution Mode:** Real Google Chrome (Playwright `channel="chrome"`), REST API Envelopes, ClamAV Scanning on `localhost:3310`.

---

## 2. Multi-Agent Role Allocation
- **AGENT 01 (QA Orchestrator):** Test orchestration, file lifecycle verification, virus scan verification.
- **AGENT 02 (Frontend & UI/UX QA):** 16:9 viewport verification, Cover Poster Shield transition, custom control bar state.
- **AGENT 03 (Backend & API QA):** Multipart file upload endpoints, boundary validation, status codes (400, 403, 423), ClamAV daemon socket protocol.
- **AGENT 04 (Database QA):** `FileAsset.virus_scan_status`, `LessonResource`, referential integrity.
- **AGENT 05 (Security & RBAC QA):** Fail-closed file download security, anti-malware isolation, quarantine traversal prevention.
- **AGENT 08 (Independent Auditor):** Verification of empirical evidence, annotated screenshots, and false-positive elimination.

---

## 3. Test Cases Inventory
1. `TC-IT09-001`: Strict Non-Archive Attachment Policy (Rejection of .zip, .rar, .7z with Canonical Message)
2. `TC-IT09-002`: Strict 50MB Attachment Ceiling Enforcement
3. `TC-IT09-003`: ClamAV Fail-Closed Quarantine Defense (Malware Containment & Student Block)
4. `TC-IT09-004`: Clean Learning Document Upload & Student Document Hub Access
5. `TC-IT09-005`: YouTube Player Standard 16:9 Viewport & Aspect Ratio Verification
6. `TC-IT09-006`: Cover Poster Shield & Custom Control Bar Interaction

---

## 4. Test Environment & Accounts
- **Host:** `http://localhost:5000`
- **Antivirus:** ClamAV Daemon on `localhost:3310`
- **Accounts:**
  - Instructor: `instructor1@pwd301.local` / `Password123!`
  - Student: `student1@pwd301.local` / `Password123!`
