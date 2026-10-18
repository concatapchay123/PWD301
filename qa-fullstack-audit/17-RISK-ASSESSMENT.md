# 17-RISK ASSESSMENT & THREAT MODELING

## 1. Risk Matrix for Discovered Defects

| Defect ID | Risk Category | Likelihood | Impact | Overall Risk | Mitigation Priority |
|---|---|---|---|---|---|
| **DEFECT-AUTH-01** | Account Takeover / Security | Medium | Critical | **HIGH** | Immediate Patch (P1) |
| **DEFECT-IT10-001** | Instructor Workflow Interruption | High | Moderate | **HIGH** | Next Sprint (P1) |
| **DEFECT-BOLA-01** | Information Disclosure | High | Minor | **MEDIUM** | Next Sprint (P2) |
| **DEFECT-ROUTE-01** | API Routing Ambiguity | Low | Moderate | **MEDIUM** | Next Sprint (P2) |
| **DEFECT-IT16-001** | Performance Degradation | High | Minor | **MEDIUM** | Optimization (P2) |
| **DEFECT-AUTH-02** | Frontend Architectural Debt | Low | Low | **LOW** | Minor Polish (P3) |

---

## 2. Platform Security Threat Analysis
- **Anti-Tamper Resilience:** HIGH. Key interception and automated session revocation successfully mitigate casual cheating and source code inspection.
- **DRM Video Stream Protection:** HIGH. AES-128 segment encryption with 12-hour session keys protects internal course videos from direct scraping.
