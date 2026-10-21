# SYSTEM ARCHITECTURE & COMPONENT TAXONOMY

## 1. Overview
PWD301 is a pure headless Enterprise Learning Management System (LMS) with high-stakes online examinations, secure DRM video delivery, Bloom taxonomy assessment matrices, and real-time AI pedagogical assistance (Octopus AI Assistant).

```
+----------------------------------------------------------------------------------------------------+
|                                    CLIENT APPLICATION LAYER                                        |
|  Pure Single-Page Application (SPA) / Vanilla Modern JS + Tailwind CSS + FontAwesome + KaTeX       |
|  Routes: #/auth, #/student/*, #/instructor/*, #/admin/*                                           |
+----------------------------------------------------------------------------------------------------+
                                             |
                   HTTP / REST / Server-Sent Events (SSE)
                                             |
+----------------------------------------------------------------------------------------------------+
|                                    APPLICATION SERVER LAYER                                        |
|  Flask 3.x WSGI Application running on Gunicorn (Port 5000)                                       |
|  - Auth & Session Management (Session Cookies + CSRF + AuthVersion multi-device revocation)        |
|  - RBAC: Student, Instructor, Admin (Primary, Audit, System Monitoring)                             |
|  - Single Active Editing Lease Engine (Algorithm 07)                                               |
|  - Video Pacing & DRM Token Minting (12h TTL, HLS fail-closed, YouTube standard 16:9)              |
|  - ClamAV Integration: Fail-closed virus scanner, 50MB non-archive attachment enforcement          |
|  - Octopus AI Assistant: Gemini Flash API (maxOutputTokens=4096, RAG retrieval with auth scoping)   |
+----------------------------------------------------------------------------------------------------+
                                             |
                  SQLAlchemy 2.x ORM / pyodbc (ODBC Driver 18)
                                             |
+----------------------------------------------------------------------------------------------------+
|                                      DATA PERSISTENCE LAYER                                        |
|  Microsoft SQL Server 2022 (Docker container 'pwd301_db', Port 1433)                               |
|  - 78 Relational Tables across 6 Core Domains                                                      |
|  - BIGINT PKs, UUID/GUID public identifiers, UTC DATETIME2(3), ROWVERSION concurrency tokens      |
+----------------------------------------------------------------------------------------------------+
```

## 2. Key Non-Negotiable Architectural Invariants
1. **Pure Headless Backend**: All endpoints strictly serve standardized JSON envelopes:
   ```json
   {
     "success": true,
     "data": { ... },
     "error": null
   }
   ```
2. **Multi-Device Concurrent Logout**: When user logs in on Device B while active on Device A, Device A receives real-time SSE `auth:concurrent_session_revoked`, both devices display a full-screen blackout modal ("CẢNH BÁO AN NINH HỆ THỐNG"), sessions are revoked, and users are redirected to `#/auth/login`.
3. **Single Active Editing Lease**: Only one active editing lease controls an attempt at any time; takeover requires lease expiry/loss and continues the same attempt.
4. **Strict 50MB Non-Archive Policy**: Maximum 50 MB for lesson attachments. Archive files (.zip, .rar, .7z, etc.) are strictly rejected with: *"Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"*.
5. **Fail-Closed Virus Scanning**: Unscanned or quarantined files are inaccessible.
6. **YouTube Standard 16:9 Viewport**: Responsive 100% width/height without distortion across all 4 touchpoints.
7. **Pacing Engine & 5-Second Seek Unlock**: Anti-forward seek restriction is strictly enforced from 00:00 up to (Duration - 5s). At <= 5s, the system unlocks video completion and allows free scrubbing.
8. **Realtime Next-Lesson Unlock**: Video end + miniquiz passing dynamically lights up the "Tiếp theo" button without requiring F5 reload.
9. **Two-Tier Broadcast RBAC**: Only Primary Admin may broadcast any category; System Monitoring Admin is strictly locked to `SYSTEM` broadcasts; other admins have broadcast UI hidden and API blocked.
10. **Global Anti-Tamper Lockdown**: Unauthorized DevTools opening (F12, Ctrl+Shift+I, etc.) overlays the Blackout Shield, revokes the session on server, and redirects to login.
