/**
 * Frontend Unit Test for TASK-139
 * Verifies UI.formatRelativeTime behavior and Topbar responsive menu structure
 */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const uiCode = fs.readFileSync('frontend/assets/js/ui.js', 'utf8');

const sandbox = {
  window: {},
  document: {
    createElement: () => ({ style: {}, classList: { add: () => {}, remove: () => {} } }),
    addEventListener: () => {}
  },
  console,
  Date,
  Math,
  isNaN,
  Number,
  String
};
vm.createContext(sandbox);
vm.runInContext(uiCode + '; this.UI = UI;', sandbox);
const UI = sandbox.UI;

console.log('--- RUNNING TASK-139 FRONTEND TESTS ---');

// 1. Test formatRelativeTime
const now = Date.now();

// Test 1: Just now (<60s)
const justNow = new Date(now - 15 * 1000).toISOString();
assert.strictEqual(UI.formatRelativeTime(justNow), 'Vừa xong', 'Should be Vừa xong');

// Test 2: 18 minutes ago (User scenario) - With Z
const eighteenMinsWithZ = new Date(now - 18 * 60 * 1000).toISOString();
assert.strictEqual(UI.formatRelativeTime(eighteenMinsWithZ), '18 phút trước', 'Should be 18 phút trước');

// Test 3: 18 minutes ago - WITHOUT Z (naive ISO string from database)
const eighteenMinsNaive = eighteenMinsWithZ.replace('Z', '');
assert.strictEqual(UI.formatRelativeTime(eighteenMinsNaive), '18 phút trước', 'Naive string should also parse as UTC and return 18 phút trước');

// Test 4: 2 hours ago
const twoHoursAgo = new Date(now - 2 * 3600 * 1000).toISOString();
assert.strictEqual(UI.formatRelativeTime(twoHoursAgo), '2 giờ trước', 'Should be 2 giờ trước');

// Test 5: 1 day ago (Yesterday)
const yesterday = new Date(now - 26 * 3600 * 1000).toISOString();
assert.strictEqual(UI.formatRelativeTime(yesterday), 'Hôm qua', 'Should be Hôm qua');

// Test 6: 4 days ago
const fourDaysAgo = new Date(now - 4 * 24 * 3600 * 1000).toISOString();
assert.strictEqual(UI.formatRelativeTime(fourDaysAgo), '4 ngày trước', 'Should be 4 ngày trước');

console.log('✓ All 6 UI.formatRelativeTime assertions passed successfully!');

// 2. Test Router topbar responsive rules in HTML & CSS
const indexHtml = fs.readFileSync('frontend/index.html', 'utf8');
assert(indexHtml.includes('topbar-admin-extra'), 'index.html must include .topbar-admin-extra CSS rule');
assert(indexHtml.includes('topbar-admin-more-btn'), 'index.html must include .topbar-admin-more-btn CSS rule');
assert(indexHtml.includes('@media (max-width: 1849px)'), 'index.html must define max-width: 1849px breakpoint');
assert(indexHtml.includes('@media (min-width: 1850px)'), 'index.html must define min-width: 1850px breakpoint');
assert(indexHtml.includes('hidden lg:flex items-center justify-center absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2'), 'Desktop nav container must use lg breakpoint and dead-center absolute position');

console.log('✓ All 5 Topbar HTML/CSS layout assertions passed successfully!');

// 3. Test router.js implementation
const routerCode = fs.readFileSync('frontend/assets/js/router.js', 'utf8');
assert(routerCode.includes('closeAdminMoreDropdown'), 'router.js must define closeAdminMoreDropdown method');
assert(routerCode.includes('topbar-admin-more-dropdown'), 'router.js must support topbar-admin-more-dropdown');
assert(routerCode.includes('topbar-admin-extra'), 'router.js must assign topbar-admin-extra to secondary tabs');

console.log('✓ All 3 router.js navigation assertions passed successfully!');

console.log('--- ALL FRONTEND TESTS PASSED (14/14) ---');
