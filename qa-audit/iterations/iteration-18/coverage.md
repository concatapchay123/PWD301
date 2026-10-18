# Iteration 18 Coverage Analysis: Adversarial Probing & Defect Clustering

**Iteration:** 18  
**Coverage Scope:** Adversarial business logic probing, unenrollment lockdown, video pacing wall-clock clamping, submission idempotency conflict, grading boundaries, cross-instructor IDOR, and anti-leak exam delivery.  

---

## 1. Endpoints & Operations Covered

| Module / Blueprint | Endpoint / Action | Method | Role Exercised | Coverage Status | Verification Type |
|---|---|---|---|---|---|
| `student` | `/student/courses/<id>/leave` | `POST` | Student | **Covered** | Adversarial Unenrollment Rejection (403) |
| `student` | `/student/lessons/<id>/progress` | `POST` | Student | **Covered** | Wall-clock Clamping & Clamped Progress |
| `student` | `/student/attempt/<id>/submit` | `POST` | Student | **Covered** | Idempotency Key Conflict Rejection (409) |
| `instructor` | `/instructor/attempts/<id>/grades/<qid>` | `POST` | Instructor 1 | **Covered** | Out-of-bounds Points Rejection (400) |
| `instructor` | `/instructor/attempts/<id>/grading` | `GET` | Instructor 2 (Non-owner) | **Covered** | Cross-Instructor IDOR Rejection (403) |
| `instructor` | `/instructor/attempts/<id>/grades/<qid>` | `POST` | Instructor 2 (Non-owner) | **Covered** | Cross-Instructor IDOR Write Rejection (403) |
| `student` | `/student/attempt/<id>` | `GET` | Student | **Covered** | Anti-Leak Exam Delivery Suppression |

---

## 2. Invariant & Security Verification

- **Strict Lifetime Enrollment (Rule 10.10):** Confirmed active in code and database.
- **Pacing Engine & Wall-Clock Clamping (Algorithm 04):** Verified fail-closed boundary enforcement.
- **Single Active Editing Lease & Idempotency (Algorithm 07):** Idempotency conflict error strictly prevents replay attacks.
- **Zero-Trust Object-Level Authorization:** Proved isolation between separate instructors.
- **Anti-Leak Delivery Invariant:** Complete suppression of solution indicators during active exams.
