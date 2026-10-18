# Iteration 15: Test Case Specifications

**Domain:** Responsive Design (320px to 1920px), WCAG AA Contrast, Dark & Light Themes  

---

### TC-IT15-001: Mobile Narrow Viewport (320px & 375px) Layout & Drawer Adaptability
- **Target Invariant:** Rule 2.2 (Mobile Touch & Layout Constraints).
- **Preconditions:** Real Google Chrome logged in as `student1@pwd301.local`.
- **Test Steps:**
  1. Set viewport to $320\text{px} \times 568\text{px}$.
  2. Measure `document.documentElement.scrollWidth` vs `window.innerWidth` (must be $\le$).
  3. Verify mobile navigation trigger (hamburger/menu button) is visible and operable.
  4. Resize to $375\text{px} \times 667\text{px}$ and verify dashboard card elements stack cleanly.
- **Pass Criteria:** Zero horizontal scroll overflow (`scrollWidth <= innerWidth`), clean vertical single-column stacking, mobile navigation accessible.

---

### TC-IT15-002: Tablet Portrait & Landscape Viewports (768px & 1024px) Layout
- **Target Invariant:** Responsive multi-column layout on medium viewports.
- **Preconditions:** Real Google Chrome on course catalog or dashboard.
- **Test Steps:**
  1. Set viewport to $768\text{px} \times 1024\text{px}$ (Tablet Portrait).
  2. Inspect grid layout (verifying 2-column or responsive flow).
  3. Set viewport to $1024\text{px} \times 768\text{px}$ (Tablet Landscape).
  4. Inspect grid layout (verifying multi-column card presentation).
  5. Assert zero horizontal overflow.
- **Pass Criteria:** Zero horizontal overflow, grid cleanly scales from 2 to 3 columns.

---

### TC-IT15-003: Desktop Standard & Ultrawide Viewports (1440px & 1920px) Constraints
- **Target Invariant:** Large screen readability & max-width container constraints.
- **Preconditions:** Real Google Chrome on desktop view.
- **Test Steps:**
  1. Set viewport to $1440\text{px} \times 900\text{px}$.
  2. Set viewport to $1920\text{px} \times 1080\text{px}$ (Full HD / Ultrawide).
  3. Assert main content area is constrained by container (e.g. `max-w-7xl` $\approx 1280\text{px}$ to $1440\text{px}$) rather than stretching edge-to-edge.
- **Pass Criteria:** Content centered with max-width container; typography line lengths comfortable for reading.

---

### TC-IT15-004: Dark Theme Rendering & Contrast Preservation
- **Target Invariant:** Dark Mode Design Tokens & WCAG Contrast.
- **Preconditions:** Authenticated student view.
- **Test Steps:**
  1. Toggle dark mode by adding class `'dark'` to `document.documentElement`.
  2. Inspect computed styles on background (verifying dark slate/zinc hues) and text (verifying light slate/zinc hues).
  3. Assert text color is not dark-on-dark.
- **Pass Criteria:** Dark mode active, background is dark slate/zinc, text is high-contrast light.

---

### TC-IT15-005: Light Theme Soft Palette & Pure White / Black Ban Adherence
- **Target Invariant:** Rule 2.2 (Ban on Pure `#000000` & `#ffffff`).
- **Preconditions:** Authenticated student view in Light mode.
- **Test Steps:**
  1. Ensure light mode active (remove class `'dark'`).
  2. Inspect computed background and text colors of primary card containers.
  3. Verify background avoids glaring harsh whites and text uses deep soft charcoal/slate rather than pure `#000000`.
- **Pass Criteria:** Soft color palette adhering to Rule 2.2 invariants.

---

### TC-IT15-006: WCAG AA Color Contrast Ratio Verification on Key Actions
- **Target Invariant:** WCAG 2.1 AA Contrast ($\ge 4.5:1$ normal text, $\ge 3:1$ large/UI).
- **Preconditions:** Authenticated view containing Primary CTA button (e.g. `btn-primary`, login submit, or dashboard action).
- **Test Steps:**
  1. Extract foreground color (`color`) and background color (`backgroundColor`) of Primary CTA button.
  2. Calculate luminance and relative contrast ratio: $CR = \frac{L_1 + 0.05}{L_2 + 0.05}$.
  3. Assert $CR \ge 3.0:1$ for buttons/large elements and $\ge 4.5:1$ for body text.
- **Pass Criteria:** Contrast ratio passes WCAG AA requirements with empirical numeric score.
