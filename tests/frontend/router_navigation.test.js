const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

class FakeClassList {
  values = new Set();

  add(value) {
    this.values.add(value);
  }

  remove(value) {
    this.values.delete(value);
  }

  contains(value) {
    return this.values.has(value);
  }

  toggle(value, force) {
    const shouldAdd = force === undefined ? !this.values.has(value) : Boolean(force);
    if (shouldAdd) this.values.add(value);
    else this.values.delete(value);
    return shouldAdd;
  }
}

class FakeElement {
  attributes = new Map();
  childNodes = [];
  classList = new FakeClassList();
  dataset = {};
  inert = false;
  style = {};
  _innerHTML = '';

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(value) {
    this._innerHTML = String(value);
    this.childNodes = this._innerHTML ? [{ innerHTML: this._innerHTML, parentElement: this }] : [];
  }

  constructor(id = '') {
    this.id = id;
  }

  prepend(child) {
    child.parentElement = this;
    this.childNodes.unshift(child);
  }

  replaceChildren(...children) {
    this.childNodes = children;
    for (const child of children) child.parentElement = this;
    this._innerHTML = children.map(child => child.innerHTML || '').join('');
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  getAttribute(name) {
    return this.attributes.get(name) || null;
  }

  removeAttribute(name) {
    this.attributes.delete(name);
  }

  remove() {
    if (!this.parentElement) return;
    this.parentElement.childNodes = this.parentElement.childNodes.filter(child => child !== this);
    this.parentElement = null;
  }

  querySelector() {
    return null;
  }

  querySelectorAll() {
    return [];
  }
}

function createRouter() {
  const viewport = new FakeElement('app-viewport');
  viewport.innerHTML = 'current screen';
  const elements = new Map([
    ['app-viewport', viewport],
    ['app-sidebar', new FakeElement('app-sidebar')],
    ['app-topbar', new FakeElement('app-topbar')],
    ['top-micro-loader', new FakeElement('top-micro-loader')],
    ['top-micro-loader-bar', new FakeElement('top-micro-loader-bar')],
    ['topbar-notifications-dropdown', new FakeElement('topbar-notifications-dropdown')],
  ]);
  const document = {
    body: new FakeElement('body'),
    createElement: () => new FakeElement(),
    getElementById: id => elements.get(id) || null,
    querySelectorAll: () => [],
  };
  const window = { location: { hash: '#/student/courses' } };
  const sandbox = {
    URLSearchParams,
    document,
    setTimeout,
    window,
    UI: { closeDrawer() {}, closeModal() {}, startMicroLoading() {}, stopMicroLoading() {} },
    ApiClient: {},
    console,
  };
  const routerPath = path.resolve(__dirname, '../../frontend/assets/js/router.js');
  vm.runInNewContext(fs.readFileSync(routerPath, 'utf8'), sandbox, { filename: routerPath });
  const router = new sandbox.window.AppRouter();
  router.currentUser = { primary_role: 'STUDENT', role_codes: ['STUDENT'] };
  router.currentRole = 'STUDENT';
  router.renderDynamicSidebar = () => {};
  router.toggleShell = () => {};
  router.updateTopbarBreadcrumb = () => {};
  return { router, viewport, window, document, sandbox };
}

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

for (const authHash of ['#/auth', '#/login']) {
  test(`unauthenticated ${authHash} settles on the login screen without a role-home redirect`, async () => {
    const { router, viewport, window, sandbox } = createRouter();
    router.currentUser = null;
    window.location.hash = authHash;
    window.history = { replaceState: (_state, _title, hash) => { window.location.hash = hash; } };
    const shellStates = [];
    router.toggleShell = visible => shellStates.push(visible);
    let attached = 0;
    sandbox.AuthView = { render: () => 'login screen', attachEvents: () => { attached += 1; } };
    router.redirectToRoleHome = () => assert.fail('an unauthenticated auth route must not enter the role-home fallback');

    await router.handleRoute();

    assert.equal(viewport.innerHTML, 'login screen');
    assert.equal(window.location.hash, '#/auth');
    assert.ok(attached > 0);
    assert.ok(shellStates.length > 0 && shellStates.every(visible => visible === false));
    assert.equal(router._isRouting, false);
  });
}

test('expired session on a protected route reaches auth without repeated session requests', async () => {
  const { router, viewport, window, sandbox } = createRouter();
  router.currentUser = null;
  window.history = { replaceState: (_state, _title, hash) => { window.location.hash = hash; } };
  sandbox.AuthView = { render: () => 'login screen', attachEvents() {} };
  let sessionRequests = 0;
  router.refreshCurrentUser = async () => { sessionRequests += 1; };
  router.redirectToRoleHome = () => assert.fail('auth must remain stable after an expired session');

  await router.handleRoute();

  assert.equal(viewport.innerHTML, 'login screen');
  assert.equal(window.location.hash, '#/auth');
  assert.equal(sessionRequests, 1);
  assert.equal(router._isRouting, false);
});

test('notification action labels match the destination task', () => {
  const { window } = createRouter();
  const label = window.AppRouter.getNotificationActionLabel;
  assert.equal(label({ event_type: 'COURSE_SUBMITTED_FOR_REVIEW' }), 'Xem Khóa Học');
  assert.equal(label({ event_type: 'INSTRUCTOR_APPLICATION_SUBMITTED' }), 'Xem Hồ Sơ');
  assert.equal(label({ event_type: 'COURSE_APPROVED' }), 'Xem Khóa Học');
  assert.equal(label({ event_type: 'COURSE_CHANGE_REJECTED' }), 'Xem Khóa Học');
  assert.equal(label({ event_type: 'LESSON_CHANGE_REQUEST' }), 'Xem Yêu Cầu');
});

test('notification transport failure renders an explicit degraded state', async () => {
  const { router, document } = createRouter();
  await router.fetchNotifications(true);

  const dropdown = document.getElementById('topbar-notifications-dropdown');
  assert.equal(router.notificationFetchState.status, 'degraded');
  assert.match(dropdown.innerHTML, /Không thể tải thông báo/);
  assert.doesNotMatch(dropdown.innerHTML, /Không có thông báo nào/);
});

test('does not render a cached empty state while notification revalidation is pending', async () => {
  const { router, document, sandbox } = createRouter();
  const request = deferred();
  sandbox.ApiClient.getNotifications = async () => request.promise;
  router.notificationsCache = {
    items: [],
    unread_count: 0,
    last_fetched: Date.now() - 60_000,
  };
  router.notificationFetchState = { status: 'ready' };

  router.openNotificationsDropdown();

  const dropdown = document.getElementById('topbar-notifications-dropdown');
  assert.match(dropdown.innerHTML, /animate-pulse/);
  assert.doesNotMatch(dropdown.innerHTML, /Không có thông báo nào/);

  request.resolve({
    items: [{
      id: 'notification-1',
      title: 'Server notice',
      body: 'A notification arrived.',
      category: 'SYSTEM',
      target_role: 'STUDENT',
      created_at: new Date().toISOString(),
      is_read: false,
    }],
    unread_count: 1,
  });
  await new Promise(resolve => setTimeout(resolve, 0));

  assert.equal(router.notificationFetchState.status, 'ready');
  assert.match(dropdown.innerHTML, /Server notice/);
});

test('keeps the current screen visible until the next route has finished rendering', async () => {
  const { router, viewport, window, document } = createRouter();
  const request = deferred();
  let navRenders = 0;
  router.renderDynamicSidebar = () => { navRenders += 1; };
  window.location.hash = '#/student/courses/detail?id=course-1';
  document.body.classList.add('fullscreen-focus-mode');
  router.dispatchRoute = async (path, _query, stagingViewport = viewport) => {
    assert.equal(stagingViewport.getAttribute('aria-hidden'), 'true');
    stagingViewport.innerHTML = 'loading destination';
    await request.promise;
    stagingViewport.innerHTML = 'destination ready';
  };

  const navigation = router.handleRoute();
  await Promise.resolve();
  assert.equal(viewport.innerHTML, 'current screen');
  assert.equal(viewport.attributes.get('aria-busy'), 'true');
  assert.equal(navRenders, 0);
  assert.equal(document.body.classList.contains('fullscreen-focus-mode'), true);

  request.resolve();
  await navigation;
  assert.equal(viewport.innerHTML, 'destination ready');
  assert.equal(viewport.attributes.has('aria-busy'), false);
  assert.equal(navRenders, 1);
  assert.equal(document.body.classList.contains('fullscreen-focus-mode'), false);
});

test('keeps the current screen visible while refreshing the same route', async () => {
  const { router, viewport, window } = createRouter();
  const request = deferred();
  router.currentUser = { primary_role: 'INSTRUCTOR', role_codes: ['INSTRUCTOR'] };
  router.currentRole = 'INSTRUCTOR';
  window.location.hash = '#/instructor/courses/manage?id=course-1&tab=curriculum';
  router.dispatchRoute = async (_path, _query, stagingViewport = viewport) => {
    stagingViewport.innerHTML = 'refreshed course loading';
    await request.promise;
    stagingViewport.innerHTML = 'refreshed course ready';
  };

  const refresh = router.handleRoute();
  await Promise.resolve();
  assert.equal(viewport.innerHTML, 'current screen');

  request.resolve();
  await refresh;
  assert.equal(viewport.innerHTML, 'refreshed course ready');
});

test('direct navigation cannot skip unfinished exam authoring steps', async () => {
  const { router, window, viewport } = createRouter();
  router.currentUser = { primary_role: 'INSTRUCTOR', role_codes: ['INSTRUCTOR'] };
  router.currentRole = 'INSTRUCTOR';
  window.ExamStore = { canVisitStep: step => step <= 1 };
  window.location.hash = '#/instructor/exams/settings';
  let dispatched = false;
  router.dispatchRoute = async () => { dispatched = true; };

  await router.renderRoute(window.location.hash);
  assert.equal(dispatched, false);
  assert.equal(window.location.hash, '#/instructor/exams');
  assert.equal(viewport.innerHTML, 'current screen');
});

test('renders the newest route when another navigation arrives during a pending render', async () => {
  const { router, viewport, window } = createRouter();
  const firstRequest = deferred();
  const secondRequest = deferred();
  const renderedPaths = [];
  router.dispatchRoute = async (path, _query, stagingViewport = viewport) => {
    renderedPaths.push(path);
    stagingViewport.innerHTML = `loading ${path}`;
    await (path === '#/student/courses' ? firstRequest.promise : secondRequest.promise);
    stagingViewport.innerHTML = `ready ${path}`;
  };

  const navigation = router.handleRoute();
  await Promise.resolve();
  window.location.hash = '#/student/courses/detail?id=course-2';
  router.handleRoute();
  firstRequest.resolve();
  await new Promise(resolve => setImmediate(resolve));

  assert.equal(viewport.innerHTML, 'current screen');
  assert.equal(renderedPaths.join('|'), '#/student/courses|#/student/courses/detail');
  secondRequest.resolve();
  await navigation;
  assert.equal(viewport.innerHTML, 'ready #/student/courses/detail');
});
