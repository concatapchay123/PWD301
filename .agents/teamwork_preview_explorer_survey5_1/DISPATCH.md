# Explorer Survey 5.1: Core App Shell & Design System
Assigned to teamwork_preview_explorer_survey5_1

## 2026-09-16T05:18:05Z

You are teamwork_preview_explorer_survey5_1.
Your working directory is: E:\PWD301\.agents\teamwork_preview_explorer_survey5_1
Your parent is: teamwork_preview_orchestrator_5 (Conversation ID: 4946890a-b666-4014-a18b-0a588b75fb4e).

CRITICAL CONSTRAINTS:
- Read E:\PWD301\.agents\ORIGINAL_REQUEST.md (specifically the master prompt at header ## 2026-09-16T05:16:14Z).
- You are a READ-ONLY explorer. Do NOT modify or write source code files. Write only to your working directory (.agents/teamwork_preview_explorer_survey5_1/).
- Apply mandatory skills: Superpowers, Task Observer, Ponytail, Full Output Enforcement, Impeccable. Remember the completion reporting syntax: "Đã dùng x skill gồm: ...".

TASK OBJECTIVE:
Map and analyze Objective R1 (Core App Shell & Design System):
1. Investigate frontend-preview/app.css, frontend-preview/components.js, and existing Flask layout src/pwd301/templates/base.html and static assets in src/pwd301/static/.
2. Detail how Tailwind CSS CDN, Plus Jakarta Sans, Inter, JetBrains Mono, and Material Symbols Outlined are used and how to integrate them cleanly into base.html without FOUC.
3. Analyze the Topbar requirements: notification counter, timezone selector, i18n language toggle, switch-role dropdown. How are current user context, notifications, and preferences passed from Flask session / context processors?
4. Analyze the dynamic 276px Sidebar across Student, Instructor, and Admin roles: active state highlighting, role switching, icons, layout collapse/expand.
5. Analyze the Toast Feedback system (toast-container) and Modal popups in frontend-preview vs existing flash messages in Flask.
6. Check existing JS scripts (app_shell.js, theme.js, motion.js) to ensure no JavaScript conflicts, and map out needed client-side utilities.
7. Document concrete integration recommendations, exact template changes required, CSS/JS asset layout, and potential risks.

Deliverable:
Write a comprehensive report to E:\PWD301\.agents\teamwork_preview_explorer_survey5_1\handoff.md with:
- Observation (verified facts, file paths, line numbers)
- Logic Chain (analysis and architectural blueprint)
- Caveats & Risks
- Concrete Implementation Plan for Milestone 1
- Verification Plan
When finished, send a message to your parent with your summary and handoff path.
