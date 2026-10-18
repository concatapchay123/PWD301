# 17-RESIDUAL RISK REGISTER & MITIGATION STRATEGY

## 1. Residual Risk Inventory

| Risk ID | Title | Inherent Risk | Residual Risk | Proposed Mitigation |
|---|---|---|---|---|
| **RISK-01** | DEFECT-AUTH-01 Token Exposure | HIGH | **MEDIUM** | Apply 1-line hotfix to remove token from JSON payload. |
| **RISK-02** | DEFECT-IT10-001 Trash Serialization 403 | MEDIUM | **LOW** | Return lightweight confirmation envelope. |
| **RISK-03** | DEFECT-IT16-001 N+1 Query Cascade | MEDIUM | **LOW** | Add eager-loading selectinload options. |
| **RISK-04** | DEFECT-BOLA-01 Lesson Outline Leak | MEDIUM | **LOW** | Add require_course_viewer check. |
