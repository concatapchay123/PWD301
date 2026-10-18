# Iteration 15 Test Plan: Responsive Design Across Viewports, WCAG AA Contrast & Theming

**Iteration:** 15  
**Domain:** Responsive Design (320px to 1920px), WCAG AA Contrast, Dark & Light Themes  
**Auditor Lead:** AGENT 02 — Frontend & UI/UX QA (Impeccable Audit & Adapt Playbook)  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Objective:** Empirically verify multi-viewport responsiveness from mobile narrow (320px) to desktop ultrawide (1920px), assert zero horizontal scroll overflow, test Dark and Light theme rendering, and calculate WCAG AA color contrast ratios on primary user interface elements.

---

## 1. Scope & Design Invariants (Rule 2 & Impeccable Contract)

1. **Multi-Viewport Responsiveness:**
   - Mobile Narrow ($320\text{px} \times 568\text{px}$, $375\text{px} \times 667\text{px}$): Mobile navigation drawer/hamburger, zero horizontal scrollbar (`scrollWidth <= innerWidth`), full-width CTA buttons.
   - Tablet ($768\text{px} \times 1024\text{px}$, $1024\text{px} \times 768\text{px}$): Responsive grid wrapping (2-column on portrait, 3-column on landscape).
   - Desktop & Ultrawide ($1440\text{px} \times 900\text{px}$, $1920\text{px} \times 1080\text{px}$): Max-width centering container (`max-w-7xl` or equivalent) preventing text stretch.
2. **Theming & Invariant Colors (Rule 2.2):**
   - Prohibition on Pure Black (`#000000`) and Pure White (`#ffffff`); soft darks (`#0f172a`, `#18181b`, `#242424`) and warm off-whites (`#f8fafc`, `#f4f4f5`, `#e7e9eb`).
   - Seamless dark/light theme switching without broken text contrast.
3. **WCAG AA Contrast Standards:**
   - Body text contrast $\ge 4.5:1$.
   - Large text and primary UI components / CTA buttons contrast $\ge 3.0:1$.

---

## 2. Test Execution Schedule (6 Test Cases)

- **TC-IT15-001:** Mobile Narrow Viewport (320px & 375px) Layout & Drawer Adaptability
- **TC-IT15-002:** Tablet Portrait & Landscape Viewports (768px & 1024px) Layout
- **TC-IT15-003:** Desktop Standard & Ultrawide Viewports (1440px & 1920px) Constraints
- **TC-IT15-004:** Dark Theme Rendering & Contrast Preservation
- **TC-IT15-005:** Light Theme Soft Palette & Pure White / Black Ban Adherence
- **TC-IT15-006:** WCAG AA Color Contrast Ratio Verification on Key Actions
