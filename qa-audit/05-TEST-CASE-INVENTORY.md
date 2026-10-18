# PWD301 MASTER TEST CASE INVENTORY (119 TEST CASES)

| Test ID | Iteration | Test Case Title | Status | Evidence |
|---|---|---|---|---|
| **TC-IT01-001** | Iteration 1 | Environment Health Check & Authentic Telemetry Verification | **PASS** |  |
| **TC-IT01-002** | Iteration 1 | Landing Page Shell & PPTQ Brand Identity Render | **PASS** | IT01_TC02_landing_auth_view.png |
| **TC-IT01-003** | Iteration 1 | Student Login & Learning Dashboard Resolution | **PASS** | IT01_TC03_student_dashboard.png |
| **TC-IT01-004** | Iteration 1 | Course Catalog Navigation & Search Discovery | **PASS** | IT01_TC04_course_catalog.png |
| **TC-IT01-005** | Iteration 1 | Admin Authentication & System Governance Overview | **PASS** | IT01_TC05_admin_governance.png |
| **TC-IT02-001** | Iteration 2 | New Student Registration Flow | **PASS** | IT02_TC01_registration_flow.png |
| **TC-IT02-002** | Iteration 2 | Duplicate Registration Email Conflict | **PASS** | IT02_TC02_duplicate_email_error.png |
| **TC-IT02-003** | Iteration 2 | Password Policy Enforcement (< 8 chars) | **PASS** | IT02_TC03_weak_password_error.png |
| **TC-IT02-004** | Iteration 2 | Authentication Rejection on Wrong Password | **PASS** | IT02_TC04_wrong_password_alert.png |
| **TC-IT02-005** | Iteration 2 | SQL Injection Parameterized Defense Verification | **PASS** | IT02_TC05_sqli_defense_probe.png |
| **TC-IT02-006** | Iteration 2 | Session Revocation & Protected Access Guard | **PASS** | IT02_TC06_session_revocation_guard.png |
| **TC-IT03-001** | Iteration 3 | Student Restricted from Instructor Studio | **PASS** | IT03_TC01_student_blocked_from_instructor.png |
| **TC-IT03-002** | Iteration 3 | Student Restricted from Admin Governance | **PASS** | IT03_TC02_student_blocked_from_admin.png |
| **TC-IT03-003** | Iteration 3 | Strict Lifetime Enrollment Invariant (Leave Course Locked) | **PASS** | IT03_TC03_lifetime_enrollment_locked.png |
| **TC-IT03-004** | Iteration 3 | Backend RBAC API Barrier for Student | **PASS** | IT03_TC04_api_rbac_barrier.png |
| **TC-IT03-005** | Iteration 3 | Instructor Restricted from Admin Governance | **PASS** | IT03_TC05_instructor_blocked_from_admin.png |
| **TC-IT03-006** | Iteration 3 | Primary Admin Multi-Tab Governance Access | **PASS** | IT03_TC06_primary_admin_operations.png |
| **TC-IT04-001** | Iteration 4 | Topbar Brand Identity & PPTQ Logo Render | **PASS** | IT04_TC01_topbar_brand_identity.png |
| **TC-IT04-002** | Iteration 4 | Dynamic Role Navigation Items Render | **PASS** | IT04_TC02_dynamic_nav_items.png |
| **TC-IT04-003** | Iteration 4 | Mobile Drawer Open/Close Interaction | **PASS** | IT04_TC03_mobile_drawer_opened.png |
| **TC-IT04-004** | Iteration 4 | Focus Exam Mode Shell Guard & Anti-Leak Header | **PASS** | IT04_TC04_focus_exam_mode_guard.png |
| **TC-IT04-005** | Iteration 4 | Unknown Route Graceful Fallback (404 Handling) | **PASS** | IT04_TC05_unknown_route_fallback.png |
| **TC-IT04-006** | Iteration 4 | Clean Browser History Stack Navigation Integrity | **PASS** | IT04_TC06_browser_history_stack.png |
| **TC-IT05-001** | Iteration 5 | Vietnamese Unicode Diacritics Storage & Presentation | **PASS** | IT05_TC01_vietnamese_unicode_integrity.png |
| **TC-IT05-002** | Iteration 5 | Client-Side Empty Required Field Validation | **PASS** | IT05_TC02_empty_field_validation.png |
| **TC-IT05-003** | Iteration 5 | Email Format Boundary Validation | **PASS** | IT05_TC03_email_format_boundary.png |
| **TC-IT05-004** | Iteration 5 | Rapid Double-Submit Button Locking Protection | **PASS** | IT05_TC04_double_submit_locking.png |
| **TC-IT05-005** | Iteration 5 | Extreme Input Length Boundary Handling | **PASS** | IT05_TC05_length_boundary_handling.png |
| **TC-IT05-006** | Iteration 5 | Form Input XSS Sanitization & HTML Escape | **PASS** | IT05_TC06_xss_sanitization_defense.png |
| **TC-IT06-001** | Iteration 6 | Idempotent Navigation on Manage Route (Zero Side-Effects) | **PASS** | IT06_TC01_idempotent_navigation.png |
| **TC-IT06-002** | Iteration 6 | UI Course Creation via Instructor Studio Modal | **PASS** | IT06_TC02_ui_course_creation.png |
| **TC-IT06-003** | Iteration 6 | Studio Header Render & Status Badge Verification | **PASS** | IT06_TC03_studio_header_render.png |
| **TC-IT06-004** | Iteration 6 | Learning Unit (Chapter) Creation in Studio | **PASS** | IT06_TC04_chapter_creation.png |
| **TC-IT06-005** | Iteration 6 | Browser Refresh Resilience & Read-After-Write Consistency | **PASS** | IT06_TC05_refresh_resilience.png |
| **TC-IT06-006** | Iteration 6 | Duplicate Course Code Uniqueness Enforcement (409 Conflict) | **PASS** | IT06_TC06_duplicate_code_conflict.png |
| **TC-IT07-001** | Iteration 7 | Standard JSON Success Envelope Verification | **PASS** | IT07_TC01_success_envelope.png |
| **TC-IT07-002** | Iteration 7 | Standard JSON Error Envelope Structure & Correlation ID | **PASS** | IT07_TC02_error_envelope_correlation_id.png |
| **TC-IT07-003** | Iteration 7 | HTTP 400 Bad Request & Field Errors Schema | **PASS** | IT07_TC03_bad_request_validation.png |
| **TC-IT07-004** | Iteration 7 | HTTP 401 Unauthorized Authentication Boundary | **PASS** | IT07_TC04_unauthorized_boundary.png |
| **TC-IT07-005** | Iteration 7 | HTTP 403 Forbidden on Cross-Role Access | **PASS** | IT07_TC05_cross_role_forbidden.png |
| **TC-IT07-006** | Iteration 7 | Pure Headless Invariant (Application/JSON Content-Type, Zero HTML Leakage) | **PASS** | IT07_TC06_pure_headless_contract.png |
| **TC-IT08-001** | Iteration 8 | Pre-Flight Publish Readiness Validation (Fail-Closed Rejection) | **PASS** | IT08_TC01_preflight_rejection.png |
| **TC-IT08-002** | Iteration 8 | Complete Course Submission & Studio Lock | **PASS** | IT08_TC02_course_submitted_locked.png |
| **TC-IT08-003** | Iteration 8 | Admin Governance Queue & Course Inspection Dossier | **PASS** | IT08_TC03_admin_review_queue.png |
| **TC-IT08-004** | Iteration 8 | Admin Course Approval & Publication Transition | **PASS** | IT08_TC04_course_published_catalog.png |
| **TC-IT08-005** | Iteration 8 | Unified Staging Draft Invariant (Post-Publication Isolation) | **PASS** | IT08_TC05_staging_draft_isolation.png |
| **TC-IT08-006** | Iteration 8 | Atomic All-or-Nothing Changeset Diff Modal & Admin Approval | **PASS** | IT08_TC06_changeset_diff_approved.png |
| **TC-IT09-001** | Iteration 9 | Strict Non-Archive Attachment Policy (Rejection of .zip, .rar, .7z) | **PASS** | IT09_TC01_archive_rejection.png |
| **TC-IT09-002** | Iteration 9 | Strict 50MB Attachment Ceiling Enforcement | **PASS** | IT09_TC02_size_ceiling_50mb.png |
| **TC-IT09-003** | Iteration 9 | ClamAV Fail-Closed Quarantine Defense (Malware Containment) | **PASS** | IT09_TC03_clamav_quarantine.png |
| **TC-IT09-004** | Iteration 9 | Clean Learning Document Upload & Access | **PASS** | IT09_TC04_clean_document_attached.png |
| **TC-IT09-005** | Iteration 9 | YouTube Standard 16:9 Full Viewport & Aspect Ratio Verification | **PASS** | IT09_TC05_youtube_16_9_viewport.png |
| **TC-IT09-006** | Iteration 9 | Cover Poster Shield & Custom Control Bar Interaction | **PASS** | IT09_TC06_poster_shield_custom_controls.png |
| **TC-IT10-001** | Iteration 10 | Cascade Attachment Deletion & Document Hub Invariant | **PASS** | IT10_TC01_cascade_attachment_deletion.png |
| **TC-IT10-002** | Iteration 10 | Contiguous Lesson Position Re-Compaction | **PASS** | IT10_TC02_lesson_position_recompaction.png |
| **TC-IT10-003** | Iteration 10 | Multi-Table Transaction Atomicity & Rollback | **PASS** | IT10_TC03_transaction_atomicity_rollback.png |
| **TC-IT10-004** | Iteration 10 | Foreign Key Referential Integrity & Non-Destructive Soft-Delete | **FAIL** | IT10_TC04_foreign_key_soft_delete.png |
| **TC-IT10-005** | Iteration 10 | Append-Only Immutable Audit Trail | **PASS** | IT10_TC05_immutable_audit_trail.png |
| **TC-IT10-006** | Iteration 10 | Learning Unit Soft-Delete & Child Cascading | **PASS** | IT10_TC06_chapter_cascade_soft_delete.png |
| **TC-IT11-001** | Iteration 11 | Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07) | **PASS** | IT11_TC01_Lease_Acquisition_Heartbeat.png |
| **TC-IT11-002** | Iteration 11 | Concurrent Window/Tab Takeover & Lease Fencing (Algorithm 07) | **PASS** | IT11_TC02_Lease_Takeover_Fencing.png |
| **TC-IT11-003** | Iteration 11 | Submission Idempotency Under Concurrent Double-Submit | **PASS** | IT11_TC03_Concurrent_Submit_Idempotency.png |
| **TC-IT11-004** | Iteration 11 | Optimistic Concurrency & Course Changeset Fingerprint Guard | **PASS** | IT11_TC04_Optimistic_Concurrency_Review_Version.png |
| **TC-IT11-005** | Iteration 11 | Concurrent Enrollment Capacity Enforcement | **PASS** | IT11_TC05_Capacity_Enforcement_Row_Lock.png |
| **TC-IT11-006** | Iteration 11 | Active Editing Lease Revocation on Submit | **PASS** | IT11_TC06_Lease_Revocation_On_Submit.png |
| **TC-IT12-001** | Iteration 12 | Prerequisite Cycle Prevention (DAG Invariant Algorithm 03) | **PASS** | IT12_TC01_Prerequisite_Cycle_Prevention.png |
| **TC-IT12-002** | Iteration 12 | Expired Editing Lease Autosave Fencing (Algorithm 07) | **PASS** | IT12_TC02_Expired_Lease_Autosave_Fencing.png |
| **TC-IT12-003** | Iteration 12 | Corrupt & Tampered Lease Token Defense | **PASS** | IT12_TC03_Corrupt_Lease_Token_Defense.png |
| **TC-IT12-004** | Iteration 12 | Out-of-Bounds Sequence Number Fencing (Client Sequencing) | **PASS** | IT12_TC04_Client_Sequencing_Fencing.png |
| **TC-IT12-005** | Iteration 12 | Invalid State Transition Rejection (State Machine Guard) | **PASS** | IT12_TC05_Invalid_State_Transition_Rejection.png |
| **TC-IT12-006** | Iteration 12 | Boundary & Negative Value Validation | **PASS** | IT12_TC06_Boundary_Negative_Value_Validation.png |
| **TC-IT13-001** | Iteration 13 | Anti-Tamper DevTools Shortcut Trap (F12) & Full-Screen Blackout Shield | **PASS** | IT13_TC01_Anti_Tamper_Blackout_Shield.png |
| **TC-IT13-002** | Iteration 13 | View Source & Screen Capture Key Interception (Ctrl+U / PrintScreen) | **PASS** | IT13_TC02_Shortcut_Interception_Rules.png |
| **TC-IT13-003** | Iteration 13 | Right-Click Context Menu Suppression on Authenticated Surfaces | **PASS** | IT13_TC03_ContextMenu_Suppression.png |
| **TC-IT13-004** | Iteration 13 | State-Changing CSRF Token Enforcement (Fail-Closed 400 CSRF_ERROR) | **PASS** | IT13_TC04_CSRF_Token_Enforcement.png |
| **TC-IT13-005** | Iteration 13 | XSS Payload Sanitization & HTML Output Escaping | **PASS** | IT13_TC05_XSS_Sanitization_Defense.png |
| **TC-IT13-006** | Iteration 13 | Sensitive System Secret & Internal Credential Leak Defense | **PASS** | IT13_TC06_Secret_Leak_Defense.png |
| **TC-IT14-001** | Iteration 14 | Browser Console Error Audit on Student Portal Routes | **PASS** | IT14_TC01_Student_Console_Audit.png |
| **TC-IT14-002** | Iteration 14 | Browser Console Error Audit on Instructor Studio Routes | **PASS** | IT14_TC02_Instructor_Console_Audit.png |
| **TC-IT14-003** | Iteration 14 | Browser Console Error Audit on Admin Governance Routes | **PASS** | IT14_TC03_Admin_Console_Audit.png |
| **TC-IT14-004** | Iteration 14 | Network Failure Simulation & Client-Side Error Interception | **PASS** | IT14_TC04_Network_Failure_Interception.png |
| **TC-IT14-005** | Iteration 14 | Delayed Response & High Latency Resilience (Loading State) | **PASS** | IT14_TC05_Latency_Loading_Resilience.png |
| **TC-IT14-006** | Iteration 14 | Offline / Online Connectivity Transition & Auto-Recovery | **PASS** | IT14_TC06_Offline_Online_Transition.png |
| **TC-IT15-001** | Iteration 15 | Mobile Narrow Viewport (320px & 375px) Layout & Drawer Adaptability | **PASS** | IT15_TC01_Mobile_Narrow_Viewport_320_375.png |
| **TC-IT15-002** | Iteration 15 | Tablet Portrait & Landscape Viewports (768px & 1024px) Layout | **PASS** | IT15_TC02_Tablet_Viewport_768_1024.png |
| **TC-IT15-003** | Iteration 15 | Desktop Standard & Ultrawide Viewports (1440px & 1920px) Constraints | **PASS** | IT15_TC03_Desktop_Ultrawide_1440_1920.png |
| **TC-IT15-004** | Iteration 15 | Dark Theme Rendering & Contrast Preservation | **PASS** | IT15_TC04_Dark_Theme_Rendering.png |
| **TC-IT15-005** | Iteration 15 | Light Theme Soft Palette & Pure White / Black Ban Adherence | **PASS** | IT15_TC05_Light_Theme_Palette.png |
| **TC-IT15-006** | Iteration 15 | WCAG AA Color Contrast Ratio Verification on Key Actions | **PASS** | IT15_TC06_WCAG_AA_Contrast_Ratios.png |
| **TC-IT16-001** | Iteration 16 | Core API Response Time Baseline across Critical Endpoints (<= 500ms) | **FAIL** | IT16_TC01_API_Response_Latency.png |
| **TC-IT16-002** | Iteration 16 | Payload Efficiency & JSON Envelope Size Audit (<= 500KB) | **PASS** | IT16_TC02_Payload_Sizes.png |
| **TC-IT16-003** | Iteration 16 | Core Web Vitals: Cumulative Layout Shift (CLS) & Largest Contentful Paint (LCP) | **PASS** | IT16_TC03_Core_Web_Vitals_CLS_LCP.png |
| **TC-IT16-004** | Iteration 16 | Server Resource Utilization & Authentic Telemetry Verification (psutil Rule 10.5) | **PASS** | IT16_TC04_Authentic_Telemetry_psutil.png |
| **TC-IT16-005** | Iteration 16 | Single Page App Memory Leak Indications under Repeated Route Traversal | **PASS** | IT16_TC05_DOM_Memory_Retention.png |
| **TC-IT16-006** | Iteration 16 | Database Multi-Join Relational Query Overhead & Connection Pool Latency | **PASS** | IT16_TC06_Database_Connection_Pool.png |
| **TC-IT17-001** | Iteration 17 | Cascade Attachment Deletion: Trashing Lesson Purges FileAsset from Document Hub | **PASS** | IT17_TC01_Cascade_Attachment_Deletion.png |
| **TC-IT17-002** | Iteration 17 | Cascade LearningUnit Deletion & Curriculum Consistency | **PASS** | IT17_TC02_Cascade_Learning_Unit_Deletion.png |
| **TC-IT17-003** | Iteration 17 | Course Document Tree Hierarchy Verification | **PASS** | IT17_TC03_Document_Tree_Hierarchy.png |
| **TC-IT17-004** | Iteration 17 | Two-Tier Broadcast Notification RBAC Enforcement (Primary vs System Monitoring vs Sub-Admin) | **PASS** | IT17_TC04_Two_Tier_Broadcast_RBAC.png |
| **TC-IT17-005** | Iteration 17 | Event-Driven Notification Delivery into Student Inbox Feed | **PASS** | IT17_TC05_Notification_Delivery.png |
| **TC-IT17-006** | Iteration 17 | Notification Read State & Unread Counter Synchronization | **PASS** | IT17_TC06_Notification_Read_Sync.png |
| **TC-IT18-001** | Iteration 18 | Adversarial Student Self-Unenrollment Prevention (Strict Lifetime Enrollment) | **PASS** | IT18_TC01_Strict_Lifetime_Enrollment_Enforcement.png |
| **TC-IT18-002** | Iteration 18 | Adversarial Video Pacing Engine Enforcement (Anti-Forward Seek & Wall-Clock Clamping) | **PASS** | IT18_TC02_Pacing_Engine_Wall_Clock_Clamping.png |
| **TC-IT18-003** | Iteration 18 | Adversarial Assessment Attempt Double-Submission & Idempotency Conflict Handling | **PASS** | IT18_TC03_Idempotency_Conflict_Replay_Protection.png |
| **TC-IT18-004** | Iteration 18 | Adversarial Manual Grading Boundary Validation (Score Clamping & Non-Negative Enforcement) | **PASS** | IT18_TC04_Manual_Grading_Boundary_Validation.png |
| **TC-IT18-005** | Iteration 18 | Cross-Instructor IDOR on Assessment Attempts (Tenant / Resource Isolation) | **PASS** | IT18_TC05_Cross_Instructor_IDOR_Isolation.png |
| **TC-IT18-006** | Iteration 18 | Anti-Leak Exam Delivery Invariant & In-Flight Quiz Protection | **PASS** | IT18_TC06_Anti_Leak_Delivery_Suppression.png |
| **TC-IT19-001** | Iteration 19 | Re-verify DEFECT-IT10-001: Course Trashing Serialization HTTP 403 | **DEFECT_CONFIRMED** | IT19_TC01_Defect_Course_Trash_403.png |
| **TC-IT19-002** | Iteration 19 | Re-verify DEFECT-IT16-001: N+1 Query Serialization Latency on /instructor/courses | **DEFECT_CONFIRMED** | IT19_TC02_Defect_Course_List_Latency.png |
| **TC-IT19-003** | Iteration 19 | Anti-Tamper Security Lockdown Regression (Rule 10.8 DevTools Trap) | **PASS** | IT19_TC03_Anti_Tamper_Blackout_Shield.png |
| **TC-IT19-004** | Iteration 19 | File Security Regression: 50MB Non-Archive Policy (Rule 10.3) | **PASS** | IT19_TC04_Archive_Attachment_Policy.png |
| **TC-IT19-005** | Iteration 19 | Exam Concurrency Regression: Single Active Editing Lease Takeover & Stale Write Fencing | **PASS** | IT19_TC05_Lease_Takeover_Fencing.png |
| **TC-IT19-006** | Iteration 19 | Two-Tier Broadcast Notification RBAC Governance Regression | **PASS** | IT19_TC06_Broadcast_RBAC_Matrix.png |
| **TC-IT20-001** | Iteration 20 | Platform System Health & Authentic Telemetry Verification (Rule 10.5) | **PASS** | IT20_TC01_System_Health_Telemetry.png |
| **TC-IT20-002** | Iteration 20 | Role-Based User Journey Integrity across Multi-Actor Shells | **PASS** | IT20_TC02_Multi_Role_Shell_Rendering.png |
| **TC-IT20-003** | Iteration 20 | Pure Headless JSON Contract Compliance (Rule 10.1 Anti-Regression) | **PASS** | IT20_TC03_Pure_Headless_JSON_Contract.png |
| **TC-IT20-004** | Iteration 20 | Release Quality Gate Assessment (Iterations 01 to 20 Consolidation) | **PASS** | IT20_TC04_Release_Gate_Metrics.png |
| **TC-IT20-005** | Iteration 20 | Residual Risk Analysis & Technical Debt Ledger Documentation | **PASS** | IT20_TC05_Residual_Risk_Triage.png |
| **TC-IT20-006** | Iteration 20 | Executive Audit Sign-Off & Master Evidence Traceability Index | **PASS** | IT20_TC06_Master_Evidence_Executive_Signoff.png |