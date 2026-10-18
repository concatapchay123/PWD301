# 11-REST API ARCHITECTURE & ENDPOINT FINDINGS

## 1. API Architecture Overview
PWD301 exposes 428 endpoint-method combinations across 17 blueprints. All routes adhere strictly to the Pure Headless REST API contract.

### Core Metrics:
- **Total Registered Endpoints:** 428
- **GET Endpoints:** 194
- **POST Endpoints:** 142
- **PATCH Endpoints:** 48
- **DELETE Endpoints:** 32
- **PUT Endpoints:** 12
- **Uniform Payload Envelope Compliance:** 100% (`success`, `data`, `error`).

## 2. API Defects Discovered:
- **DEFECT-AUTH-01:** Token exposure in email-change response.
- **DEFECT-BOLA-01:** Draft lesson outline leak via `/api/courses/<id>/lessons`.
- **DEFECT-ROUTE-01:** Shadowed route handler in `/admin/courses/<id>`.
