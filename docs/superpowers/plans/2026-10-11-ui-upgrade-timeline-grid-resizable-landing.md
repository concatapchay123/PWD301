# Implementation Plan: Comprehensive UI Modernization, Timeline Tree, Resizable Sidebar & Course Landing System

**Goal:** Implement 6 core UI/UX modernizations for PWD301:
1. 4-column responsive grid across course views.
2. Removal of isolated recommendation banner; merging 4 AI-recommended courses directly into the 4-column catalog with prominent glowing "Đề xuất" tag.
3. Continuous vertical timeline tree with neon green circular nodes for lesson outline + smooth scroll to active lesson (matching reference image `Giao diện lộ trình học Ethical Hacking.png`).
4. Hierarchical neon cyan/teal timeline tree for documents/resources with folder nodes, lesson sub-nodes, and elbow connectors to file download cards (matching reference image `Giao diện Timeline Tài liệu Neon Xanh.png`).
5. Draggable resizable sidebar splitter (260px - 520px) with `localStorage` persistence and quick collapse/expand toggle.
6. Course Landing / Overview page for students (conditional routing: not enrolled -> landing page; enrolled -> learning console) + Full Canvas Block Editor for instructors with rich blocks & live student preview.

---

## Architecture Breakdown

### 1. Catalog & Recommendations (Items 1 & 2)
- Target: `frontend/assets/js/views/student.js`, `src/pwd301/services/recommendation_service.py` (or recommendation route).
- Grid updated to `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6`.
- Remove `#catalog-recommendations-banner`.
- When rendering courses in `#catalog-courses-grid`, fetch top 4 recommendations from `/api/ai/recommendations?limit=4`.
- Prepend/highlight these 4 courses with:
  - Badge: `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 flex items-center gap-1 shadow-sm"><span class="material-symbols-outlined text-[12px]">auto_awesome</span>Đề xuất</span>`
  - Card style: Glowing border / neon accent (`border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/30`).
  - Explanation tooltip or subtitle based on student skills/major.

### 2. Timeline Tree for Lesson Outline (Item 3)
- Target: `frontend/assets/js/views/student.js` (around `renderCourseConsole` and outline tree).
- Continuous vertical spine: `before:absolute before:left-[19px] before:top-4 before:bottom-4 before:w-[2px] before:bg-slate-700/60`.
- Chapter Node: Outer ring `w-7 h-7 rounded-full border-2 border-emerald-500 flex items-center justify-center bg-slate-900 shadow-[0_0_10px_rgba(16,185,129,0.4)]` with inner dot `w-2.5 h-2.5 rounded-full bg-emerald-400`.
- Lesson Nodes on Timeline:
  - Active (`ĐANG HỌC`): `w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] ring-4 ring-emerald-500/20`, capsule highlight `bg-emerald-950/40 border border-emerald-500/40 text-emerald-200`, status pill `ĐANG HỌC`.
  - Locked: `w-2.5 h-2.5 rounded-full bg-slate-600`, lock icon, "Khóa" pill.
  - Completed: `w-3 h-3 rounded-full bg-emerald-500`, check icon, "Đã xong" pill.
- Smooth scroll to active lesson element (`scrollIntoView({ behavior: 'smooth', block: 'center' })`).

### 3. Timeline Tree for Documents/Resources (Item 4)
- Target: `frontend/assets/js/views/student.js` (resources tab in `renderCourseConsole`).
- Neon Teal/Cyan theme matching `Giao diện Timeline Tài liệu Neon Xanh.png`:
  - Chapter Node: Glowing teal circular badge with folder icon (`w-8 h-8 rounded-full border-2 border-emerald-500/80 bg-slate-900 flex items-center justify-center text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.35)]`), chapter title, file count badge (`3 tệp`), collapse chevron.
  - Sub-branch line connecting down to lessons.
  - Lesson sub-node: Rounded badge with file document icon (`w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300`), lesson title, file count badge.
  - Elbow connector (`border-l-2 border-b-2 border-slate-700/70 rounded-bl-xl`) leading to File Cards:
    - PDF badge (Crimson Red `PDF`), file name, file size (`25.5 MB`), download action button (`text-slate-400 hover:text-white`).

### 4. Resizable Splitter for Course Console (Item 5)
- Target: `frontend/assets/js/views/student.js` (layout of `renderCourseConsole`).
- Structure:
  - Container with `flex flex-row relative h-[calc(100vh-...)]`.
  - Sidebar element `#course-console-sidebar` with inline width initialized from `localStorage.getItem('pwd301_sidebar_width') || '360px'`.
  - Splitter element `#course-console-splitter`: `w-2 hover:w-2.5 bg-slate-800/80 hover:bg-emerald-500/60 cursor-col-resize select-none transition-colors z-20 flex items-center justify-center group`.
  - Quick toggle button on splitter.
  - Mouse/touch drag handlers with bounds `260px <= width <= 520px`.
  - On mouseup, save to `localStorage.setItem('pwd301_sidebar_width', currentWidth + 'px')`.

### 5. Course Landing Page & Full Canvas Block Editor (Item 6)
- Target:
  - Route in `frontend/assets/js/router.js`: `#/student/courses/intro?id=...` -> `StudentView.renderCourseOverview`.
  - Conditional navigation from catalog/dashboard:
    - Check enrollment: if enrolled -> `#/student/courses/detail?id=...`
    - if not enrolled -> `#/student/courses/intro?id=...`
  - `StudentView.renderCourseOverview`:
    - Full Course Landing view: Hero section with video trailer embed/poster, Course Stats (duration, lectures, level, certificate), Dynamic Blocks rendered from course data/JSON, Syllabus roadmap preview, Instructor profile card, FAQ accordion, Sticky CTA "Ghi danh ngay" / "Vào học".
  - `InstructorView`:
    - In `renderCourseManage`: Add "Giới thiệu môn học" (Course Landing Editor) tab.
    - Full Canvas Block Editor:
      - Add Block (Hero, Rich Text, Media, Highlights, Syllabus Preview, Instructor Bio, FAQ, CTA).
      - Reorder blocks (Up / Down / Drag).
      - Rich Text inline editing / toolbar.
      - "Xem trước như học viên" (Live Student Preview Modal).
      - Save changes to course description JSON envelope.
