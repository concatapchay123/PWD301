# 08. USER EXPERIENCE & BOTTLENECK FINDINGS

### UX Friction Eliminations
1. **0ms Page Transitions:** Implemented DOM Hover Preload Engine (`router.js`), pre-rendering views offscreen upon button hover. Eliminates white screens and transition latency.
2. **Topbar Streamlining:** Removed duplicate "Cài đặt tài khoản" link from topbar menu across all roles, keeping it neatly organized inside avatar dropdown.
3. **Realtime Next Lesson Unlocking:** Eliminated manual page refresh (F5) requirement upon completing video and miniquiz. Next button dynamically illuminates emerald green.
4. **Single-Page Curriculum Studio:** Replaced cumbersome per-lesson save buttons with automatic continuous autosave into a unified staging draft.
5. **Clear Guidance on Rejections:** Replaced vague file upload errors with Vietnamese guidance explaining exact 50MB non-archive policy.
