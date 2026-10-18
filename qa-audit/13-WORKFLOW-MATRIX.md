# PWD301 BUSINESS WORKFLOW & STATE TRANSITION MATRIX

## 1. Course Authoring & Staging Draft Lifecycle State Machine

```
   [NEW DRAFT]
        │
        ▼
   [INSTRUCTOR EDITING] ──(Auto-save draft without modifying live catalog)
        │
        ▼
   [SUBMITTED_FOR_REVIEW] ──(Course locked for author edits during review)
        │
        ├─────────────────────────────┐
        ▼                             ▼
   [ADMIN APPROVED]              [ADMIN REJECTED]
        │                             │
        ▼                             ▼
   [PUBLISHED / LIVE]            [RETURNED TO DRAFT]
        │
        ▼ (Post-Approval Changes)
   [STAGING DRAFT (COURSE_VERSION_CHANGESET)]
        │ (Continuous auto-save into ONE aggregated pending changeset)
        ▼
   [CHANGESET SUBMITTED] ──(Admin atomic side-by-side diff comparison)
        │
        ├─────────────────────────────┐
        ▼                             ▼
   [CHANGESET MERGED TO LIVE]    [CHANGESET REJECTED]
   (Zero downtime live update)   (Published catalog preserved untouched)
```

---

## 2. Assessment & Single Active Editing Lease Lifecycle

```
   [WAITING ROOM]
        │ (Check schedule, prerequisites, remaining attempt count)
        ▼
   [START ATTEMPT] ──► Generates AttemptSnapshot + Issues LEASE_TOKEN (TTL 120s)
        │
        ▼
   [AUTOSAVE PULSE] ──► Updates answer payload, client_sequence, heartbeat
        │
        ├── [LEASE TAKEOVER ATTEMPT] (Other tab / browser)
        │       │
        │       ├─► If original lease active: REJECT (409 Conflict / ACTIVE_LEASE_EXISTS)
        │       └─► If original lease expired: GRANT takeover & continue same Attempt
        │
        ▼
   [SUBMIT ATTEMPT] ──► Idempotent submission, lease revoked, server grades objective items
        │
        ▼
   [RESULTS & GRADING]
        │
        ├─► Objective items: Immediate score breakdown released
        └─► Subjective/Essay items: Instructor manual grading queue -> Result PDF Export
```

---

## 3. Video Pacing & Realtime Lesson Unlock Flow

```
   [LESSON OPENED]
        │
        ▼
   [PLAYBACK SESSION INITIALIZED] (DRM Token generated, frontier = 0s)
        │
        ▼
   [ACTIVE PLAYBACK & HEARTBEAT] (Frontier advances; forward seek blocked past frontier)
        │
        ├── [FORWARD SEEK ATTEMPT] ──► Snapped back to frontier
        │
        ▼
   [FINAL 5 SECONDS REACHED] (currentTime >= Duration - 5s OR Duration <= 5s)
        │
        ├─► Pacing restrictions UNLOCKED (free scrubbing across last 5s)
        ├─► Video completion flagged (is_video_complete = true)
        ▼
   [VIDEO ENDED EVENT (State 0 / Ended)]
        │
        ▼
   [REALTIME NEXT LESSON UNLOCK] (No F5 Reload!)
        ├─► Next button flips to Emerald Green (`bg-emerald-600 text-white animate-fade-in`)
        └─► Sidebar outline unlocks next lesson dynamically
```
