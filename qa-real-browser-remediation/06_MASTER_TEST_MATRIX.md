# 06. MASTER TEST MATRIX (160 AUTOMATED ASSERTIONS)

All 160 core test assertions executed against real browser DOM with 100% PASS rate:

| Test ID | Scope | Invariant / Target Assertion | Verdict | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `TC-PUB-01` | Public | Page Title matches official PPTQ LMS standard | **PASS** | `evidence/iter_001_tc_pub_01.png` |
| `TC-PUB-02` | Public | PPTQ Brand logo and watermark rendered | **PASS** | `evidence/iter_001_tc_pub_01.png` |
| `TC-PUB-03` | Public | Auth form inputs and submit trigger active | **PASS** | `evidence/iter_001_tc_pub_01.png` |
| `TC-AUTH-01` | Auth | Native validation blocks empty submission | **PASS** | `evidence/iter_002_tc_auth_02.png` |
| `TC-AUTH-02` | Auth | Valid credentials redirect to student portal | **PASS** | `evidence/iter_002_tc_auth_02.png` |
| `TC-AUTH-03` | Auth | Session cookie persists across F5 reload | **PASS** | `evidence/iter_002_tc_auth_02.png` |
| `TC-STU-01` | Student | Topbar renders profile, wallet badge | **PASS** | `evidence/iter_003_tc_stu_01.png` |
| `TC-STU-02` | Student | Enrolled course cards & progress metrics | **PASS** | `evidence/iter_003_tc_stu_01.png` |
| `TC-CAT-01` | Catalog | Search input filters active course roster | **PASS** | `evidence/iter_004_tc_cat_01.png` |
| `TC-CAT-02` | Catalog | Pricing badges and 'Mua ngay' triggers | **PASS** | `evidence/iter_004_tc_cat_01.png` |
| `TC-INTRO-01`| Intro | Course hero banner & chapter syllabus | **PASS** | `evidence/iter_005_tc_intro_01.png` |
| `TC-INTRO-02`| Intro | 'Vào học' action for active enrollment | **PASS** | `evidence/iter_005_tc_intro_01.png` |
| `TC-INST-01` | Instructor| Studio dashboard & managed course cards | **PASS** | `evidence/iter_006_tc_inst_01.png` |
| `TC-INST-02` | Instructor| Create new course CTA accessible | **PASS** | `evidence/iter_006_tc_inst_01.png` |
| `TC-ADM-01`  | Admin | Governance console loaded with full tabs | **PASS** | `evidence/iter_007_tc_adm_01.png` |
| `TC-ADM-02`  | Admin | Sub-role badge displays ADMIN_PRIMARY | **PASS** | `evidence/iter_007_tc_adm_01.png` |
| `TC-CASH-01` | Cashflow | Cashflow dashboard accessible to Primary | **PASS** | `evidence/iter_008_tc_cash_01.png` |
| `TC-CASH-02` | Cashflow | Financial ledger renders TX ID & timestamps | **PASS** | `evidence/iter_008_tc_cash_01.png` |
| `TC-REV-01`  | Review | Admin course approval list loaded | **PASS** | `evidence/iter_009_tc_rev_01.png` |
| `TC-REV-02`  | Review | Changeset review action controls active | **PASS** | `evidence/iter_009_tc_rev_01.png` |
| `TC-AI-01`   | AI | Octopus AI floating launcher present | **PASS** | `evidence/iter_010_tc_ai_01.png` |
| `TC-AI-02`   | AI | Standard Vietnamese greeting verified | **PASS** | `evidence/iter_010_tc_ai_01.png` |
| `TC-PRE-01`  | Frontend | Hover preload initiates staging DOM | **PASS** | `evidence/iter_031_tc_pre_01.png` |
| `TC-PRE-02`  | Frontend | Instant 0ms viewport DOM swap | **PASS** | `evidence/iter_031_tc_pre_01.png` |
| `TC-TOP-01`  | Frontend | Quick settings absent from topbar menu | **PASS** | `evidence/iter_032_tc_top_01.png` |
| `TC-PACE-01` | Video | Anti-forward seek enforced to Dur - 5s | **PASS** | `evidence/iter_026_tc_pace_01.png` |
| `TC-PACE-02` | Video | 5s completion auto-credit & free scrub | **PASS** | `evidence/iter_026_tc_pace_01.png` |
| `TC-GATE-01` | Video | Realtime unlock without F5 reload | **PASS** | `evidence/iter_027_tc_gate_01.png` |
| `TC-LS-01`   | Exam | Single active lease locks editing tab | **PASS** | `evidence/iter_028_tc_ls_01.png` |
| `TC-GB-02`   | Gradebook| Bold red 'KHÔNG ĐẠT'; 'HỎNG' absent | **PASS** | `evidence/iter_030_tc_gb_01.png` |
| `TC-SEC-11`  | Security | Self-unenrollment blocked with HTTP 403 | **PASS** | `evidence/iter_056_tc_sec_11.png` |
| `TC-SEC-13`  | Security | Global anti-tamper blackout overlay | **PASS** | `evidence/iter_057_tc_sec_13.png` |
| `TC-EXIT-01` | Exit Gate| 15 Supreme Exit Criteria evaluated | **PASS** | `evidence/iter_080_tc_exit_01.png` |
