const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

class FakeClassList {
  values = new Set();
  add(v) { this.values.add(v); }
  remove(v) { this.values.delete(v); }
  contains(v) { return this.values.has(v); }
  toggle(v, force) {
    const add = force === undefined ? !this.values.has(v) : Boolean(force);
    if (add) this.values.add(v); else this.values.delete(v);
    return add;
  }
}

class FakeElement {
  attributes = new Map();
  childNodes = [];
  classList = new FakeClassList();
  dataset = {};
  style = {};
  _innerHTML = '';

  get innerHTML() { return this._innerHTML; }
  set innerHTML(val) {
    this._innerHTML = String(val);
    this.childNodes = this._innerHTML ? [{ innerHTML: this._innerHTML, parentElement: this }] : [];
  }

  constructor(id = '') { this.id = id; }
  setAttribute(k, v) { this.attributes.set(k, String(v)); }
  getAttribute(k) { return this.attributes.get(k) || null; }
  removeAttribute(k) { this.attributes.delete(k); }
  remove() {
    if (!this.parentElement) return;
    this.parentElement.childNodes = this.parentElement.childNodes.filter(c => c !== this);
    this.parentElement = null;
  }
  querySelector() { return null; }
  querySelectorAll() { return []; }
  addEventListener() {}
  removeEventListener() {}
}

function createTestRouter(currentRole = 'STUDENT') {
  const viewport = new FakeElement('app-viewport');
  const elements = new Map([
    ['app-viewport', viewport],
    ['app-sidebar', new FakeElement('app-sidebar')],
    ['app-topbar', new FakeElement('app-topbar')],
    ['top-micro-loader', new FakeElement('top-micro-loader')],
    ['top-micro-loader-bar', new FakeElement('top-micro-loader-bar')],
    ['topbar-navigation-items', new FakeElement('topbar-navigation-items')],
    ['mobile-nav-links', new FakeElement('mobile-nav-links')],
    ['topbar-user-name', new FakeElement('topbar-user-name')],
    ['topbar-avatar-initials', new FakeElement('topbar-avatar-initials')],
    ['topbar-role-badge', new FakeElement('topbar-role-badge')],
    ['topbar-role-dropdown', new FakeElement('topbar-role-dropdown')],
    ['topbar-notification-badge', new FakeElement('topbar-notification-badge')],
    ['topbar-notification-list', new FakeElement('topbar-notification-list')],
    ['topbar-notification-dropdown', new FakeElement('topbar-notification-dropdown')],
  ]);
  const document = {
    body: new FakeElement('body'),
    createElement: () => new FakeElement(),
    getElementById: id => elements.get(id) || null,
    querySelector: sel => {
      if (sel.startsWith('#')) return elements.get(sel.slice(1)) || null;
      return null;
    },
    querySelectorAll: () => [],
    addEventListener: () => {},
  };
  const window = {
    location: { hash: '#/student/courses' },
    history: {
      pushState: () => {},
      replaceState: () => {},
    },
    addEventListener: () => {},
    matchMedia: () => ({ matches: false, addEventListener: () => {} }),
    setInterval: () => 123,
    clearInterval: () => {},
  };
  const sandbox = {
    URLSearchParams,
    document,
    setTimeout,
    setInterval: window.setInterval,
    clearInterval: window.clearInterval,
    window,
    UI: { closeDrawer() {}, closeModal() {}, startMicroLoading() {}, stopMicroLoading() {}, escapeHtml: s => String(s) },
    ApiClient: {
      getNotifications: async () => ({ notifications: [], unread_count: 0 }),
      markNotificationRead: async (id) => ({ success: true, id }),
      markAllNotificationsRead: async (cat, role) => ({ success: true, count: 0 }),
    },
    console,
  };
  const routerPath = path.resolve(__dirname, '../../frontend/assets/js/router.js');
  vm.runInNewContext(fs.readFileSync(routerPath, 'utf8'), sandbox, { filename: routerPath });
  const router = new sandbox.window.AppRouter();
  router.currentUser = {
    id: 'user-1',
    display_name: 'Nguyen Van A',
    email: 'user@example.com',
    primary_role: currentRole,
    role_codes: [currentRole],
  };
  router.currentRole = currentRole;
  return { router, elements, window, document, sandbox };
}

test('isFocusRoute hides topbar during exams but keeps it visible on results', () => {
  const { router } = createTestRouter();

  // Fullscreen exam / attempt routes
  assert.equal(router.isFocusRoute('#/student/exams/attempt-123'), true);
  assert.equal(router.isFocusRoute('#/student/exams/attempt-123?q=2'), true);
  assert.equal(router.isFocusRoute('#/student/assessments/attempt-xyz'), true);
  assert.equal(router.isFocusRoute('#/student/exams/waiting-room?id=1'), true);

  // Results route must NOT be focus mode (topbar remains visible)
  assert.equal(router.isFocusRoute('#/student/exams/attempt-123/results'), false);
  assert.equal(router.isFocusRoute('#/student/exams/results?id=123'), false);
  assert.equal(router.isFocusRoute('#/student/courses'), false);
  assert.equal(router.isFocusRoute('#/instructor/courses'), false);
  assert.equal(router.isFocusRoute('#/admin/operations'), false);
});

test('checkPathActive correctly matches hierarchical sub-routes for topbar navigation', () => {
  const { router } = createTestRouter();

  // Student assessment subpaths
  assert.equal(router.checkPathActive('#/student/assessments', '#/student/assessments'), true);
  assert.equal(router.checkPathActive('#/student/assessments/attempt-123', '#/student/assessments'), true);

  // Instructor course subpaths
  assert.equal(router.checkPathActive('#/instructor/courses/manage?id=1', '#/instructor/courses'), true);
  assert.equal(router.checkPathActive('#/instructor/courses/new', '#/instructor/courses'), true);

  // Instructor exam subpaths
  assert.equal(router.checkPathActive('#/instructor/exams/editor', '#/instructor/exams'), true);
  assert.equal(router.checkPathActive('#/instructor/exams?category=tech', '#/instructor/exams'), true);

  // Admin operational subpaths
  assert.equal(router.checkPathActive('#/admin/courses/review?id=1', '#/admin/governance?tab=courses'), true);
  assert.equal(router.checkPathActive('#/admin/operations/telemetry', '#/admin/operations'), true);

  // Cross-role or unrelated should not match
  assert.equal(router.checkPathActive('#/student/courses', '#/student/assessments'), false);
  assert.equal(router.checkPathActive('#/instructor/exams', '#/instructor/courses'), false);
});

test('renderDynamicTopbar does not include Question Bank for INSTRUCTOR role', () => {
  const { router, elements } = createTestRouter('INSTRUCTOR');
  router.renderDynamicTopbar();

  const navLinks = elements.get('topbar-navigation-items');
  assert.ok(!navLinks.innerHTML.includes('#/instructor/questions'), 'Instructor topbar must NOT include Question Bank link');
  assert.ok(!navLinks.innerHTML.includes('Ngân hàng câu hỏi'), 'Must NOT contain Vietnamese label for question bank');
  assert.ok(navLinks.innerHTML.includes('#/instructor/courses'), 'Must include Courses link');
  assert.ok(navLinks.innerHTML.includes('#/instructor/exams'), 'Must include Exams link');
});

test('renderDynamicTopbar renders role-specific navigation for STUDENT and ADMIN', () => {
  // Student
  const student = createTestRouter('STUDENT');
  student.router.renderDynamicTopbar();
  const studentLinks = student.elements.get('topbar-navigation-items').innerHTML;
  assert.ok(studentLinks.includes('#/student/courses'));
  assert.ok(studentLinks.includes('#/student/catalog'));
  assert.ok(studentLinks.includes('#/student/assessments'));

  // Admin
  const admin = createTestRouter('ADMIN');
  admin.router.renderDynamicTopbar();
  const adminLinks = admin.elements.get('topbar-navigation-items').innerHTML;
  assert.ok(adminLinks.includes('#/admin/governance'));
  assert.ok(adminLinks.includes('tab=courses'));
  assert.ok(adminLinks.includes('tab=applications'));
  assert.ok(adminLinks.includes('#/admin/operations'));
});

test('updateUserUI configures settings link tailored to the current role', () => {
  // Student settings
  const student = createTestRouter('STUDENT');
  student.router.updateUserUI();
  const studentDropdown = student.elements.get('topbar-role-dropdown');
  assert.ok(studentDropdown.innerHTML.includes('#/student/settings'));

  // Instructor settings
  const instructor = createTestRouter('INSTRUCTOR');
  instructor.router.updateUserUI();
  const instructorDropdown = instructor.elements.get('topbar-role-dropdown');
  assert.ok(instructorDropdown.innerHTML.includes('#/instructor/settings'));

  // Admin settings -> Security tab in Governance
  const admin = createTestRouter('ADMIN');
  admin.router.updateUserUI();
  const adminDropdown = admin.elements.get('topbar-role-dropdown');
  assert.ok(adminDropdown.innerHTML.includes('#/admin/governance?tab=security'));
});

test('ApiClient exposes markNotificationRead and markAllNotificationsRead', () => {
  const apiPath = path.resolve(__dirname, '../../frontend/assets/js/api.js');
  const sandbox = {
    window: {},
    fetch: async (url, opts) => ({
      ok: true,
      status: 200,
      json: async () => ({ success: true, url, method: opts?.method }),
    }),
    sessionStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
    console,
  };
  vm.runInNewContext(fs.readFileSync(apiPath, 'utf8'), sandbox, { filename: apiPath });
  const ApiClient = sandbox.window.ApiClient;

  assert.equal(typeof ApiClient.markNotificationRead, 'function');
  assert.equal(typeof ApiClient.markAllNotificationsRead, 'function');
});
