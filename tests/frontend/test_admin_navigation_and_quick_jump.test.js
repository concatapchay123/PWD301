const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

test('Admin Topbar includes Duyệt khóa học (tier3) and responsive dropdown items', () => {
  const routerCode = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/router.js'), 'utf8');

  // Verify router.js contains tier3Html in topNav.innerHTML
  assert.match(routerCode, /topNav\.innerHTML\s*=\s*primaryHtml\s*\+\s*tier3Html\s*\+\s*tier2Html\s*\+\s*secondaryHtml\s*\+\s*moreDropdownHtml/);

  // Verify tier3 is mapped to topbar-admin-tier3
  assert.match(routerCode, /renderNavLink\(tier3Item,\s*['"]topbar-admin-tier3['"]\)/);
  assert.match(routerCode, /topbar-admin-tier3-dropdown/);
});

test('Course Review includes Menu Truy Cập Nhanh and Quick Jump buttons', async () => {
  const adminCode = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8');

  // Verify quick nav markup exists in admin.js
  assert.match(adminCode, /id="admin-courses-quick-nav"/);
  assert.match(adminCode, /Menu Truy Cập Nhanh/);
  assert.match(adminCode, /quick-jump-courses-btn/);
  assert.match(adminCode, /quick-jump-changes-btn/);
  assert.match(adminCode, /quick-jump-management-btn/);

  // Verify governance quick hub exists on users tab
  assert.match(adminCode, /id="admin-governance-quick-hub"/);
});
