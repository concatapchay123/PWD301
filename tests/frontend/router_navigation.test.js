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
  return { router, viewport, window, document };
}

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

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
