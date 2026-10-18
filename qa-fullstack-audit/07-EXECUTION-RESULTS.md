# 07-EXECUTION RESULTS & METRICS

## Overall Test Execution Telemetry

- **Total Execution Runs:** 20 STLC Iterations completed.
- **Pass Rate:** 96.7% (58 test assertions passed, 2 confirmed defect reproductions).
- **Execution Engine:** Playwright Sync API driving Google Chrome 155 on Windows 11.
- **Host Target:** http://127.0.0.1:5000 (Pure Headless + SPA).

### Visual Evidence Ledger (Annotated Screenshots)
All 19 high-resolution annotated screenshots are available in [qa-fullstack-audit/screenshots-annotated/](file:///e:/PWD301/qa-fullstack-audit/screenshots-annotated/):

1. `IT01_Home_Guest.png` — Verified guest homepage, clean topbar, and 0 logo images.
2. `IT01_Health_Public.png` — Verified /health JSON response.
3. `IT02_Login_Form.png` — Verified login form, inputs, and password visibility toggle.
4. `IT02_Student_Dashboard.png` — Verified authenticated student portal and enrollments.
5. `IT02_Admin_Dashboard.png` — Verified super-admin management console.
6. `IT03_Admin_Dashboard.png` — Verified RBAC boundary enforcement.
7. `IT04_Student_Portal.png` — Verified SPA navigation and course catalog.
8. `IT04_Modal_Open.png` — Verified modal dialog rendering and backdrop dismiss.
9. `IT05_Course_Form.png` — Verified form controls and Vietnamese Unicode handling.
10. `IT06_Course_Studio.png` — Verified instructor authoring studio.
11. `IT08_Staging_Drafts.png` — Verified staging draft changesets.
12. `IT09_YouTube_16x9_Student.png` — Verified YouTube player 16:9 uncropped viewport.
13. `IT11_Assessment_Lease.png` — Verified single active editing lease.
14. `IT12_Exam_AntiLeak.png` — Verified anti-leak exam slot rendering.
15. `IT13_AntiTamper_BlackoutShield.png` — Verified full-screen Blackout Shield overlay.
16. `IT15_Mobile_375x667.png` — Verified responsive mobile layout.
17. `IT15_Tablet_768x1024.png` — Verified responsive tablet layout.
18. `IT15_Desktop_1920x1080.png` — Verified responsive desktop layout.
19. `IT16_Performance_Profile.png` — Verified latency telemetry visualization.
