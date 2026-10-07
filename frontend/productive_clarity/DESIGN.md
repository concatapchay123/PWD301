---
name: Productive Clarity
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#4648d4'
  on-secondary: '#ffffff'
  secondary-container: '#6063ee'
  on-secondary-container: '#fffbff'
  tertiary: '#004c76'
  on-tertiary: '#ffffff'
  tertiary-container: '#00659a'
  on-tertiary-container: '#bedfff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#cce5ff'
  tertiary-fixed-dim: '#93ccff'
  on-tertiary-fixed: '#001d31'
  on-tertiary-fixed-variant: '#004b73'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
  surface-canvas: '#F8FAFC'
  surface-card: '#FFFFFF'
  border-subtle: '#E2E8F0'
  text-primary: '#0F172A'
  text-secondary: '#1E293B'
  text-muted: '#64748B'
  success-emerald: '#059669'
  warning-amber: '#D97706'
  danger-rose: '#E11D48'
  info-sky: '#0284C7'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 21px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  gutter-mobile: 1rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

# PWD301 EdTech Design System — Enterprise Clarity

## North Star: "Productive Clarity"
Clean, systematic, and accessible. Built for high-density academic & enterprise learning platforms. Every element earns its place without unnecessary visual noise.

## Colors
- **Primary Brand (`#4F46E5` / `#6366F1`):** Indigo CTA and focused elements.
- **Surface / Background:** `#F8FAFC` slate canvas, pure `#FFFFFF` cards and panels.
- **Border / Divider:** `#E2E8F0` crisp subtle slate dividers.
- **Text:** Slate-900 (`#0F172A`) for bold headers, Slate-800 (`#1E293B`) for high-contrast body, Slate-500 (`#64748B`) for descriptive metadata.
- **Semantics:** Emerald-600 (`#059669`) for Published / Success, Amber-600 (`#D97706`) for Prerequisites & Warnings, Rose-600 (`#E11D48`) for Locked / Errors, Sky-600 (`#0284C7`) for Informational notices.

## Typography
- **Font:** Plus Jakarta Sans, Inter, sans-serif.
- **Borders & Radii:** 10px rounded corners for controls, 14px for cards/modals.

## Invariants & Design Standards (TASK-081 Consensus)
- **Wide Semi-Fluid Layout (`max-w-[1720px]`):** All primary workspaces, dashboards, exam consoles, and studio editors must use `max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10`. Side gutters are reduced to 1/3 of the previous narrow containers (`max-w-4xl`/`max-w-7xl`).
- **Clean Button Labeling (Zero Redundant `+`):** Never include a literal `+` character in button text when an icon (`add`, `add_circle`, `create_new_folder`) is present. Example: `Thêm bài giảng vào chương này`, NOT `+ + Thêm bài giảng vào chương này`.
- **Curriculum Studio Video Block Structure:**
  - *Top bar:* Single-line YouTube/Vimeo input with live embed preview.
  - *Bottom area:* Large dashed dropzone for dragging & dropping or selecting local video files (`.mp4`, `.webm`, `.mov`, `.mkv`), supporting multi-file selection, upload progress bar, HTML5 video preview, and deletion controls.
  - *Constraints:* Video file size strictly `< 1 GB`, maximum 2 videos per lesson, fail-closed antivirus scanning.
- **Academic Result PDF Engine:** Generated via backend `ReportLab` using TrueType Unicode font (`Arial`/`arialbd.ttf`), full student details (`attempt.student`), score summary, pass/fail status badge, and question breakdown table.
- **Attempt Flow Auto-Redirect & Error Resilience:**
  - Visiting an attempt in status `GRADED`, `SUBMITTED`, or `PENDING_GRADING` automatically transitions to `#/student/assessments/results?id=<attempt_id>` without 400 errors.
  - Never render raw technical error text on empty screens. All edge cases must use polite Academic State Cards with icon and navigation buttons.
  - All numerical formatting (e.g. `scorePct`) must be null-safe (`Number.isFinite(...) ? ... : '0.0'`).
