const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/auth.js');

function createMockElement(id = '', tagName = 'div') {
  const classListSet = new Set();
  const listeners = {};
  return {
    id,
    tagName: tagName.toUpperCase(),
    type: 'text',
    value: '',
    checked: false,
    classList: {
      add: (...cls) => cls.forEach(c => classListSet.add(c)),
      remove: (...cls) => cls.forEach(c => classListSet.delete(c)),
      contains: (c) => classListSet.has(c),
      get length() { return classListSet.size; }
    },
    addEventListener: (type, handler) => {
      listeners[type] = listeners[type] || [];
      listeners[type].push(handler);
    },
    removeEventListener: (type, handler) => {
      if (!listeners[type]) return;
      listeners[type] = listeners[type].filter(h => h !== handler);
    },
    dispatchEvent: (type, eventObj = {}) => {
      if (!listeners[type]) return;
      listeners[type].forEach(h => h(eventObj));
    },
    _listeners: listeners,
  };
}

function createMockEnvironment() {
  const elements = new Map();
  const docListeners = {};

  const document = {
    getElementById: (id) => {
      if (!elements.has(id)) {
        elements.set(id, createMockElement(id));
      }
      return elements.get(id);
    },
    querySelector: (sel) => null,
    querySelectorAll: (sel) => [],
    addEventListener: (type, handler) => {
      docListeners[type] = docListeners[type] || [];
      docListeners[type].push(handler);
    },
    removeEventListener: (type, handler) => {
      if (!docListeners[type]) return;
      docListeners[type] = docListeners[type].filter(h => h !== handler);
    },
    _docListeners: docListeners,
    _elements: elements,
  };

  const window = {
    document,
    ApiClient: {},
    UI: { showToast: () => {} },
  };

  return { window, document };
}

function loadFreshAuthView() {
  const source = fs.readFileSync(sourcePath, 'utf8');
  const env = createMockEnvironment();
  vm.runInNewContext(source, { window: env.window, document: env.document }, { filename: sourcePath });
  return { window: env.window, document: env.document, AuthView: env.window.AuthView };
}

test('AuthView.render includes Caps Lock warning containers in login and register forms', () => {
  const { AuthView } = loadFreshAuthView();
  const html = AuthView.render();

  // Login password Caps Lock warning
  assert.match(html, /id="login-capslock-warning"/);
  // Login email Caps Lock warning
  assert.match(html, /id="login-email-capslock-warning"/);
  // Register password Caps Lock warning
  assert.match(html, /id="register-capslock-warning"/);
  // Register confirm password Caps Lock warning
  assert.match(html, /id="register-confirm-capslock-warning"/);

  // Checks for accessibility and content
  assert.match(html, /keyboard_capslock/);
  assert.match(html, /Đang bật Caps Lock/);
  assert.match(html, /role="alert"/);
  assert.match(html, /aria-live="polite"/);
});

test('AuthView.checkCapsLock returns true if event modifier is active', () => {
  const { AuthView } = loadFreshAuthView();

  assert.equal(typeof AuthView.checkCapsLock, 'function');
  assert.equal(AuthView.checkCapsLock({ getModifierState: (mod) => mod === 'CapsLock' }), true);
  assert.equal(AuthView.checkCapsLock({ getModifierState: (mod) => false }), false);
  assert.equal(AuthView.checkCapsLock(null), false);
  assert.equal(AuthView.checkCapsLock({}), false);
  assert.equal(AuthView.checkCapsLock({ getModifierState: 'not-a-fn' }), false);
});

test('AuthView.setupCapsLockWarning toggles hidden class on CapsLock events', () => {
  const { AuthView } = loadFreshAuthView();

  const input = createMockElement('login-password', 'input');
  const warning = createMockElement('login-capslock-warning', 'div');
  warning.classList.add('hidden');

  const handler = AuthView.setupCapsLockWarning(input, warning);
  assert.ok(handler && typeof handler.cleanup === 'function');

  // Trigger keydown with CapsLock ON
  input.dispatchEvent('keydown', {
    getModifierState: (key) => key === 'CapsLock',
  });
  assert.equal(warning.classList.contains('hidden'), false, 'Warning should be visible when CapsLock is on');

  // Trigger keydown with CapsLock OFF
  input.dispatchEvent('keydown', {
    getModifierState: (key) => false,
  });
  assert.equal(warning.classList.contains('hidden'), true, 'Warning should be hidden when CapsLock is off');

  // Trigger keyup with CapsLock ON
  input.dispatchEvent('keyup', {
    getModifierState: (key) => key === 'CapsLock',
  });
  assert.equal(warning.classList.contains('hidden'), false);

  // Trigger blur
  input.dispatchEvent('blur', {});
  assert.equal(warning.classList.contains('hidden'), true, 'Warning should be hidden on blur');

  // Trigger focus when CapsLock was remembered as active
  input.dispatchEvent('focus', {});
  assert.equal(warning.classList.contains('hidden'), false, 'Warning should be restored on focus when active');

  // Trigger click with CapsLock ON
  input.dispatchEvent('click', {
    getModifierState: (key) => key === 'CapsLock',
  });
  assert.equal(warning.classList.contains('hidden'), false);

  // Trigger click with CapsLock OFF
  AuthView.isCapsLockActive = false;
  input.dispatchEvent('click', {
    getModifierState: (key) => false,
  });
  assert.equal(warning.classList.contains('hidden'), true);

  // Cleanup removes listeners
  handler.cleanup();
  assert.equal(input._listeners.keydown.length, 0);
  assert.equal(input._listeners.keyup.length, 0);
  assert.equal(input._listeners.click.length, 0);
  assert.equal(input._listeners.focus.length, 0);
  assert.equal(input._listeners.blur.length, 0);
});

test('AuthView.setupCapsLockWarning safely handles null or missing arguments', () => {
  const { AuthView } = loadFreshAuthView();

  assert.equal(AuthView.setupCapsLockWarning(null, null), null);
  assert.equal(AuthView.setupCapsLockWarning(createMockElement('input'), null), null);
  assert.equal(AuthView.setupCapsLockWarning(null, createMockElement('warning')), null);
});

test('AuthView.attachEvents wires up Caps Lock warnings to all input targets', () => {
  const { AuthView, document } = loadFreshAuthView();

  AuthView.attachEvents();

  const loginPass = document.getElementById('login-password');
  const loginPassWarn = document.getElementById('login-capslock-warning');
  loginPassWarn.classList.add('hidden');

  const loginEmail = document.getElementById('login-email');
  const loginEmailWarn = document.getElementById('login-email-capslock-warning');
  loginEmailWarn.classList.add('hidden');

  // Verify listeners were attached to login-password
  assert.ok(loginPass._listeners.keydown && loginPass._listeners.keydown.length > 0);
  assert.ok(loginPass._listeners.keyup && loginPass._listeners.keyup.length > 0);
  assert.ok(loginPass._listeners.click && loginPass._listeners.click.length > 0);

  // Verify listeners were attached to login-email
  assert.ok(loginEmail._listeners.keydown && loginEmail._listeners.keydown.length > 0);

  // Test CapsLock trigger on login-password
  loginPass.dispatchEvent('keydown', {
    getModifierState: (k) => k === 'CapsLock'
  });
  assert.equal(loginPassWarn.classList.contains('hidden'), false);

  // Test CapsLock off on login-password
  loginPass.dispatchEvent('keyup', {
    getModifierState: (k) => false
  });
  assert.equal(loginPassWarn.classList.contains('hidden'), true);

  // Test CapsLock trigger on login-email
  loginEmail.dispatchEvent('keydown', {
    getModifierState: (k) => k === 'CapsLock'
  });
  assert.equal(loginEmailWarn.classList.contains('hidden'), false);
});

test('Global document key listeners sync AuthView.isCapsLockActive', () => {
  const { AuthView, document } = loadFreshAuthView();

  AuthView.attachEvents();

  assert.ok(document._docListeners.keydown && document._docListeners.keydown.length > 0);
  assert.ok(document._docListeners.keyup && document._docListeners.keyup.length > 0);

  // Simulate global CapsLock activation
  document._docListeners.keydown.forEach(fn => fn({
    getModifierState: (k) => k === 'CapsLock'
  }));
  assert.equal(AuthView.isCapsLockActive, true);

  // Simulate global CapsLock deactivation
  document._docListeners.keyup.forEach(fn => fn({
    getModifierState: (k) => false
  }));
  assert.equal(AuthView.isCapsLockActive, false);
});

test('Controllers.initAuth binds Caps Lock warning when elements are present', () => {
  const { AuthView, window } = loadFreshAuthView();
  const controllersPath = path.resolve(__dirname, '../../frontend/assets/js/controllers.js');
  const controllersSource = fs.readFileSync(controllersPath, 'utf8');
  vm.runInNewContext(controllersSource, { window, document: window.document }, { filename: controllersPath });

  const passInput = createMockElement('login-password', 'input');
  passInput.type = 'password';
  const passWarn = createMockElement('login-capslock-warning', 'div');
  passWarn.classList.add('hidden');

  const container = {
    querySelector: (sel) => {
      if (sel === 'input[type="password"]') return passInput;
      if (sel === '#login-capslock-warning') return passWarn;
      return null;
    }
  };

  window.Controllers.initAuth(container);

  assert.ok(passInput._listeners.keydown && passInput._listeners.keydown.length > 0);

  // Trigger CapsLock
  passInput.dispatchEvent('keydown', {
    getModifierState: (k) => k === 'CapsLock'
  });
  assert.equal(passWarn.classList.contains('hidden'), false);
});
