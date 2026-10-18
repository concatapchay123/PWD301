const assert = require('node:assert/strict');
const test = require('node:test');

// Mock DOM helper for testing Global Security Shield and Course Document Tree Modal
function createMockEnvironment() {
  const windowListeners = new Map();
  const documentListeners = new Map();
  const storage = new Map();

  class MockElement {
    constructor(tagName = 'div', className = '') {
      this.tagName = tagName.toUpperCase();
      this.className = className;
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.attributes = new Map();
      this._textContent = '';
      this.innerHTML_val = '';
      this.isConnected = true;
      this._listeners = new Map();
    }

    get textContent() {
      if (this.children.length > 0) {
        return this.children.map(c => c.textContent).join(' ');
      }
      return this._textContent || '';
    }
    set textContent(val) {
      this._textContent = val;
    }

    get innerHTML() {
      return this.innerHTML_val;
    }
    set innerHTML(html) {
      this.innerHTML_val = html;
      this.children = [];
      // Basic mock parsing of id, class, and tags from html
      const idMatches = [...html.matchAll(/id="([^"]+)"/g)];
      idMatches.forEach(m => {
        const child = new MockElement('div', '');
        child.id = m[1];
        child.parentElement = this;
        this.children.push(child);
      });
      const btnMatches = [...html.matchAll(/class="([^"]*btn-close-modal[^"]*)"/g)];
      btnMatches.forEach(() => {
        const child = new MockElement('button', 'btn-close-modal');
        child.parentElement = this;
        this.children.push(child);
      });
    }

    setAttribute(key, val) {
      this.attributes.set(key, String(val));
    }
    getAttribute(key) {
      return this.attributes.get(key) || null;
    }
    removeAttribute(key) {
      this.attributes.delete(key);
    }

    appendChild(child) {
      child.parentElement = this;
      this.children.push(child);
      return child;
    }

    removeChild(child) {
      const idx = this.children.indexOf(child);
      if (idx !== -1) {
        this.children.splice(idx, 1);
        child.parentElement = null;
      }
      return child;
    }

    remove() {
      if (this.parentElement) {
        this.parentElement.removeChild(this);
      }
    }

    querySelector(selector) {
      if (selector.startsWith('#')) {
        const id = selector.slice(1);
        return this._findChild(el => el.id === id);
      }
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        return this._findChild(el => el.className && el.className.includes(cls));
      }
      return this._findChild(el => el.tagName.toLowerCase() === selector.toLowerCase());
    }

    querySelectorAll(selector) {
      const results = [];
      this._findAllChildren(el => {
        if (selector.startsWith('.')) {
          return el.className && el.className.includes(selector.slice(1));
        }
        if (selector.startsWith('#')) {
          return el.id === selector.slice(1);
        }
        return el.tagName.toLowerCase() === selector.toLowerCase();
      }, results);
      return results;
    }

    _findChild(predicate) {
      for (const child of this.children) {
        if (predicate(child)) return child;
        const found = child._findChild(predicate);
        if (found) return found;
      }
      return null;
    }

    _findAllChildren(predicate, out) {
      for (const child of this.children) {
        if (predicate(child)) out.push(child);
        child._findAllChildren(predicate, out);
      }
    }

    addEventListener(event, fn) {
      if (!this._listeners.has(event)) this._listeners.set(event, []);
      this._listeners.get(event).push(fn);
      this['on' + event] = fn;
    }
    removeEventListener(event, fn) {
      const fns = this._listeners.get(event) || [];
      const idx = fns.indexOf(fn);
      if (idx !== -1) fns.splice(idx, 1);
    }
    dispatchEvent(event) {
      const fns = this._listeners.get(event.type) || [];
      fns.forEach(fn => fn(event));
      if (this['on' + event.type]) this['on' + event.type](event);
    }
  }

  const mockBody = new MockElement('body', '');
  const mockDocument = {
    body: mockBody,
    createElement(tag) {
      return new MockElement(tag);
    },
    getElementById(id) {
      return mockBody._findChild(el => el.id === id) || (mockBody.id === id ? mockBody : null);
    },
    querySelectorAll(sel) {
      return mockBody.querySelectorAll(sel);
    },
    addEventListener(event, fn) {
      if (!documentListeners.has(event)) documentListeners.set(event, []);
      documentListeners.get(event).push(fn);
    },
    removeEventListener(event, fn) {
      const fns = documentListeners.get(event) || [];
      const idx = fns.indexOf(fn);
      if (idx !== -1) fns.splice(idx, 1);
    },
    visibilityState: 'visible'
  };

  const mockSessionStorage = {
    getItem(k) { return storage.get(k) || null; },
    setItem(k, v) { storage.set(k, String(v)); },
    removeItem(k) { storage.delete(k); },
    clear() { storage.clear(); }
  };

  const mockLocalStorage = {
    _data: new Map(),
    getItem(k) { return this._data.get(k) || null; },
    setItem(k, v) { this._data.set(k, String(v)); },
    removeItem(k) { this._data.delete(k); },
    clear() { this._data.clear(); }
  };

  let clipboardText = '';
  const mockNavigator = {
    clipboard: {
      writeText: async (t) => { clipboardText = t; }
    }
  };

  const mockWindow = {
    document: mockDocument,
    sessionStorage: mockSessionStorage,
    localStorage: mockLocalStorage,
    navigator: mockNavigator,
    location: { hash: '#/student/dashboard' },
    addEventListener(event, fn) {
      if (!windowListeners.has(event)) windowListeners.set(event, []);
      windowListeners.get(event).push(fn);
    },
    removeEventListener(event, fn) {
      const fns = windowListeners.get(event) || [];
      const idx = fns.indexOf(fn);
      if (idx !== -1) fns.splice(idx, 1);
    },
    setInterval: (fn) => ({ id: 1, unref: () => {} }),
    clearInterval: () => {},
    ApiClient: {
      logout: async () => ({ revoked: true })
    }
  };

  return {
    mockDocument,
    mockWindow,
    mockBody,
    mockSessionStorage,
    mockLocalStorage,
    windowListeners,
    documentListeners,
    getClipboardText: () => clipboardText
  };
}

test('VideoArmor Global Security Shield: install, detect shortcuts, trigger lockdown, and uninstall', async () => {
  const env = createMockEnvironment();
  global.window = env.mockWindow;
  global.document = env.mockDocument;
  global.sessionStorage = env.mockSessionStorage;
  global.localStorage = env.mockLocalStorage;
  global.navigator = env.mockWindow.navigator;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  // 1. Initial State: not installed
  assert.equal(VideoArmor.isGlobalShieldInstalled(), false, 'Shield should initially be inactive');

  // 2. Install Shield with authenticated student
  const student = {
    student_code: 'SV20261018',
    email: 'test_sec@pwd301.local'
  };
  VideoArmor.installGlobalShield(student);
  assert.equal(VideoArmor.isGlobalShieldInstalled(), true, 'Shield must be active after installGlobalShield');

  // 3. Test checkShortcutViolation
  assert.equal(VideoArmor.checkShortcutViolation({ key: 'F12', keyCode: 123 }), 'DEVTOOLS_DETECTED');
  assert.equal(VideoArmor.checkShortcutViolation({ key: 'i', ctrlKey: true, shiftKey: true }), 'DEVTOOLS_DETECTED');
  assert.equal(VideoArmor.checkShortcutViolation({ key: 'u', ctrlKey: true }), 'VIEW_SOURCE_ATTEMPT');
  assert.equal(VideoArmor.checkShortcutViolation({ key: 'PrintScreen', keyCode: 44 }), 'SCREEN_CAPTURE_ATTEMPT');
  assert.equal(VideoArmor.checkShortcutViolation({ key: 's', ctrlKey: true, shiftKey: true }), 'SCREEN_CAPTURE_ATTEMPT');
  assert.equal(VideoArmor.checkShortcutViolation({ key: 'a', ctrlKey: false }), null);

  // 4. Trigger Global Lockdown
  await VideoArmor.triggerGlobalLockdown('DEVTOOLS_DETECTED');

  // Verify Blackout Shield mounted in DOM
  const shield = env.mockDocument.getElementById('global-security-blackout-shield');
  assert.ok(shield, 'Global blackout shield must be created in document.body');
  assert.ok(shield.innerHTML.includes('🛡️ CẢNH BÁO AN NINH HỆ THỐNG'), 'Shield must display official security warning title');
  assert.ok(shield.innerHTML.includes('PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN'), 'Shield must specify detection reason');
  assert.ok(shield.innerHTML.includes('SV20261018'), 'Shield must display forensic watermark identifier');

  // Verify sessionStorage security alert flag set
  assert.ok(env.mockSessionStorage.getItem('pwd301_security_alert'), 'pwd301_security_alert must be set in sessionStorage');

  // 5. Test Uninstall Global Shield
  VideoArmor.uninstallGlobalShield();
  assert.equal(VideoArmor.isGlobalShieldInstalled(), false, 'Shield must be inactive after uninstallGlobalShield');
  assert.equal(env.mockDocument.getElementById('global-security-blackout-shield'), null, 'Shield DOM node must be removed upon uninstall');
});

test('AuthView renders security alert banner when pwd301_security_alert is present in sessionStorage', () => {
  const env = createMockEnvironment();
  global.window = env.mockWindow;
  global.document = env.mockDocument;
  global.sessionStorage = env.mockSessionStorage;
  global.localStorage = env.mockLocalStorage;

  // Global UI mock
  global.UI = { escapeHtml: s => s };

  const { AuthView } = require('../../frontend/assets/js/views/auth.js');

  // Without alert
  env.mockSessionStorage.removeItem('pwd301_security_alert');
  const normalHtml = AuthView.render();
  assert.equal(normalHtml.includes('id="auth-security-alert-banner"'), false, 'Normal auth view should not render security banner');

  // With alert
  env.mockSessionStorage.setItem('pwd301_security_alert', 'Cảnh báo an ninh: Phiên làm việc đã bị thu hồi do phát hiện hành vi vi phạm chính sách bảo mật hệ thống.');
  const alertHtml = AuthView.render();
  assert.ok(alertHtml.includes('id="auth-security-alert-banner"'), 'Security banner must render when pwd301_security_alert is set');
  assert.ok(alertHtml.includes('🛡️ CẢNH BÁO AN NINH HỆ THỐNG'), 'Banner must display security alert title');
  assert.ok(alertHtml.includes('Phiên làm việc đã bị thu hồi'), 'Banner must display revocation notice');
});

test('InstructorView.openCourseDocumentTreeModal renders hierarchical document tree and close action', () => {
  const env = createMockEnvironment();
  global.window = env.mockWindow;
  global.document = env.mockDocument;
  global.sessionStorage = env.mockSessionStorage;
  global.localStorage = env.mockLocalStorage;
  global.UI = { escapeHtml: s => s };

  // Load InstructorView
  delete require.cache[require.resolve('../../frontend/assets/js/views/instructor.js')];
  require('../../frontend/assets/js/views/instructor.js');
  const InstructorView = global.window.InstructorView;

  const mockCourse = {
    title: 'Lập trình Web PWD301',
    resources: [
      { filename: 'syllabus.pdf', file_size_bytes: 250000, asset_id: 'ast-gen-1' }
    ],
    learning_units: [
      {
        id: 'unit-1',
        title: 'Nhập môn HTML/CSS',
        lessons: [
          {
            id: 'les-1',
            title: 'Cơ bản về DOM',
            blocks: [
              {
                type: 'document',
                files: [
                  { filename: 'dom_guide.docx', file_size_bytes: 520000, asset_id: 'ast-les-1' }
                ]
              }
            ]
          }
        ]
      }
    ]
  };

  const modal = InstructorView.openCourseDocumentTreeModal(mockCourse, mockCourse.learning_units);
  assert.ok(modal, 'openCourseDocumentTreeModal should return modal element');
  assert.equal(modal.id, 'pwd301-course-docs-modal');

  // Verify modal content
  assert.ok(modal.innerHTML.includes('Cây tài liệu: Lập trình Web PWD301'), 'Modal must display course title');
  assert.ok(modal.innerHTML.includes('syllabus.pdf'), 'Modal must display general course resource');
  assert.ok(modal.innerHTML.includes('Nhập môn HTML/CSS'), 'Modal must display chapter unit');
  assert.ok(modal.innerHTML.includes('dom_guide.docx'), 'Modal must display lesson document file');
  assert.ok(modal.innerHTML.includes('2 tệp'), 'Modal must calculate total document count');

  // Verify empty state when course has zero documents
  const emptyCourse = { title: 'Khóa học trống', learning_units: [] };
  const emptyModal = InstructorView.openCourseDocumentTreeModal(emptyCourse, []);
  assert.ok(emptyModal.innerHTML.includes('Chưa có tài liệu đính kèm nào'), 'Empty course should render friendly empty state');
});
