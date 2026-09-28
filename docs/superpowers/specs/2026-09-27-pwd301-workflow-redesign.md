# PWD301 workflow and interface repair

## Objective

Resolve the defects listed in the attached goal objective across exams, notifications, course review, course imagery, lesson authoring, and the shared interface. Preserve the existing session-authenticated SPA, JSON API, SQL Server model, historical assessment evidence, and file quarantine rules.

## Confirmed decisions

- In a monitored exam, leaving the tab or exiting requested fullscreen is recorded and shown as a warning. Instructors can review the observations. The browser does not block operating-system gestures or reliably observe screenshots, so the product must not claim those capabilities or assign a screenshot count.
- The goal objective authorizes the full set of repairs. The external course-authoring HTML is a layout reference, not a source of application behavior or code.
- Existing changes in `frontend/assets/js/views/instructor.js` and `tests/frontend/lesson_studio_isolation.test.js` are in progress and must be preserved.

## Capabilities

### Exam flow

The waiting room is a dedicated route with one primary action, the exam title, opening state/countdown, duration, remaining attempts, and a short accurate rules summary. Exam settings choose whether monitoring and fullscreen are requested and which exam interface is used. Monitoring uses browser visibility/focus/fullscreen events, deduplicates adjacent signals, records leave duration and event counts on the server, and never automatically submits for a monitoring event. The instructor sees recorded events for attempts in courses they manage. Attempt submission waits for pending answer saves, offers recovery when a save fails, reuses a stable idempotency key on retry, and handles a committed submission even if grading/result loading is delayed.

### Exam authoring

The first method-selection step must be complete before any later route opens. Later steps are reachable only after the preceding step is complete, including direct hash navigation. Back navigation to completed steps remains available. The interactive editor should provide clear add/edit/remove question actions and inline validation. The workflow keeps the shared instructor topbar; its stepper is part of page content.

### Notifications and language

Every confirmation, toast, and notification names the resource and action actually being performed. Review queue actions refresh after success, hide completed requests from the pending queue, and display a clear rejection reason. User-facing headings and action labels use plain Vietnamese; the academic safety/audit UI entry is removed while backend safeguards and audit records remain.

### Course review and imagery

Course approval opens a dedicated admin detail route with course information, lessons, resources and approval controls. Permission is checked server-side. Instructors can upload a scanned, same-course image and set it as the course thumbnail. The thumbnail is served through an authorized route. Courses without one receive an attractive, accessible CSS fallback.

### Lesson structure

Add a parent learning unit (user-facing `Bài học`) above existing `Lesson` records. Existing lesson IDs, progress, question links, file links, and history remain stable. Existing lessons are backfilled into one-child units. A unit has at most 10 active lessons and 7 videos total; each child lesson has at most 2 videos and 5 documents. Count both uploaded videos and external links. Enforce caps in the service layer under a transaction, then reflect remaining capacity in the authoring studio. The studio uses a wider editing canvas, a child-lesson navigator, and the existing project visual language.

### Shared interface

Use a coherent dark palette with distinct canvas, surface, raised dialog, border, primary text, and muted text values. Dialogs and toasts have visible separation and WCAG AA body-text contrast. Preserve the role topbar across all ordinary routes. Improve table widths and responsive overflow where the affected queues currently waste space. Expand random-avatar choices beyond robot-only designs.

## Verification

- Write a failing regression test before each behavioral code change, then run it green.
- Run affected Python unit/API tests and Node frontend tests, then repository lint/static checks and the aggregate verification script when feasible.
- Check migration upgrade/downgrade on the available database engine; report SQL Server checks as unverified if unavailable.
- Inspect changed screens at desktop and mobile widths in both themes. Run the Impeccable detector and a line-level security/logic review.

## Constraints

- No new Jinja templates or independent preview frontend.
- No JWT in browser storage, direct file paths, private IDs, or unsafe unscanned file delivery.
- Exam deadlines and editing leases remain server authoritative; submitted answers and score history remain immutable.
- Do not reset current student completion during lesson grouping.
