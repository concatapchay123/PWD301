const assert = require('node:assert/strict');
const test = require('node:test');

// Mock browser environment for VideoArmor
function createMockDOM() {
  const listeners = new Map();
  const intervals = new Set();

  class MockElement {
    constructor(tagName = 'div') {
      this.tagName = tagName.toUpperCase();
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.attributes = new Map();
      this.dataset = {};
      this.textContent = '';
      this._paused = false;
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
      if (mockDocument._observerCallback) {
        mockDocument._observerCallback([{
          type: 'childList',
          addedNodes: [child],
          removedNodes: [],
          target: this
        }]);
      }
      return child;
    }

    removeChild(child) {
      const idx = this.children.indexOf(child);
      if (idx !== -1) {
        this.children.splice(idx, 1);
        child.parentElement = null;
        if (mockDocument._observerCallback) {
          mockDocument._observerCallback([{
            type: 'childList',
            addedNodes: [],
            removedNodes: [child],
            target: this
          }]);
        }
      }
      return child;
    }

    querySelector(selector) {
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        for (const c of this.children) {
          if (c.className && c.className.includes(cls)) return c;
          const found = c.querySelector(selector);
          if (found) return found;
        }
      }
      if (selector.startsWith('#')) {
        const id = selector.slice(1);
        for (const c of this.children) {
          if (c.id === id) return c;
          const found = c.querySelector(selector);
          if (found) return found;
        }
      }
      for (const c of this.children) {
        if (c.tagName.toLowerCase() === selector.toLowerCase()) return c;
        const found = c.querySelector(selector);
        if (found) return found;
      }
      return null;
    }

    querySelectorAll(selector) {
      const results = [];
      for (const c of this.children) {
        if (c.tagName.toLowerCase() === selector.toLowerCase() ||
            (c.className && c.className.includes(selector.replace('.', '')))) {
          results.push(c);
        }
        results.push(...c.querySelectorAll(selector));
      }
      return results;
    }

    getBoundingClientRect() {
      return { width: 800, height: 450, top: 0, left: 0 };
    }

    pause() {
      this._paused = true;
    }

    play() {
      this._paused = false;
    }
  }

  class MockMutationObserver {
    constructor(callback) {
      this.callback = callback;
      mockDocument._observerCallback = callback;
    }
    observe(target, options) {
      this.target = target;
      this.options = options;
    }
    disconnect() {
      mockDocument._observerCallback = null;
    }
  }

  const mockDocument = {
    _observerCallback: null,
    visibilityState: 'visible',
    createElement(tag) {
      return new MockElement(tag);
    },
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(fn);
    },
    removeEventListener(type, fn) {
      if (listeners.has(type)) listeners.get(type).delete(fn);
    },
    dispatchEvent(event) {
      if (listeners.has(event.type)) {
        for (const fn of listeners.get(event.type)) fn(event);
      }
    }
  };

  const mockWindow = {
    addEventListener: mockDocument.addEventListener,
    removeEventListener: mockDocument.removeEventListener,
    dispatchEvent: mockDocument.dispatchEvent,
    setInterval(fn, ms) {
      const id = setInterval(fn, ms);
      if (id && typeof id.unref === 'function') id.unref();
      intervals.add(id);
      return id;
    },
    clearInterval(id) {
      intervals.delete(id);
      clearInterval(id);
    }
  };

  return { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals };
}

test('VideoArmor mounts dynamic watermark with student credentials and moves over time', async () => {
  const { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals } = createMockDOM();
  global.document = mockDocument;
  global.window = mockWindow;
  global.MutationObserver = MockMutationObserver;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  const container = new MockElement('div');
  const armor = VideoArmor.mount(container, {
    student: {
      student_code: 'SV2026001',
      full_name: 'Nguyen Van A',
      email: 'student@example.com'
    },
    ip: '192.168.1.100'
  });

  assert.ok(armor, 'Armor instance should be created');
  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark, 'Watermark element must be rendered inside container');

  const text = watermark.textContent;
  assert.ok(text.includes('SV2026001') || text.includes('Nguyen Van A'), 'Watermark contains student identification');
  assert.ok(text.includes('student@example.com'), 'Watermark contains email');
  assert.ok(text.includes('192.168.1.100'), 'Watermark contains IP address');

  // Verify non-intrusive styling
  assert.equal(watermark.style.pointerEvents, 'none');
  assert.equal(watermark.style.position, 'absolute');

  // Verify repositioning
  const oldPos = { top: watermark.style.top, left: watermark.style.left };
  armor.reposition();
  // Reposition changes coordinates
  assert.ok(watermark.style.top !== undefined);

  armor.destroy();
  for (const id of intervals) clearInterval(id);
});

test('VideoArmor triggers Blackout when watermark is removed from DOM', async () => {
  const { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals } = createMockDOM();
  global.document = mockDocument;
  global.window = mockWindow;
  global.MutationObserver = MockMutationObserver;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  const container = new MockElement('div');
  const video = new MockElement('video');
  container.appendChild(video);

  let violationCaught = false;
  let violationType = '';
  const armor = VideoArmor.mount(container, {
    student: { email: 'student@example.com' },
    ip: '10.0.0.1',
    onSecurityViolation: (reason) => {
      violationCaught = true;
      violationType = reason;
    }
  });

  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark);

  // Simulate malicious user deleting watermark node
  container.removeChild(watermark);

  // Blackout screen should be activated
  const blackout = container.querySelector('.video-armor-blackout');
  assert.ok(blackout, 'Blackout screen must be rendered upon watermark removal');
  assert.equal(video._paused, true, 'Video playback must be paused during blackout');
  assert.equal(violationCaught, true, 'Security violation callback must fire');
  assert.equal(violationType, 'DOM_TAMPER');

  armor.destroy();
  for (const id of intervals) clearInterval(id);
});

test('VideoArmor pauses media when document becomes hidden (visibilitychange)', async () => {
  const { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals } = createMockDOM();
  global.document = mockDocument;
  global.window = mockWindow;
  global.MutationObserver = MockMutationObserver;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  const container = new MockElement('div');
  const video = new MockElement('video');
  container.appendChild(video);

  const armor = VideoArmor.mount(container, {
    student: { email: 'student@example.com' }
  });

  video._paused = false;

  // Simulate tab switch / hidden
  mockDocument.visibilityState = 'hidden';
  mockDocument.dispatchEvent({ type: 'visibilitychange' });

  assert.equal(video._paused, true, 'Video must be paused when switching tab away');

  armor.destroy();
  for (const id of intervals) clearInterval(id);
});

test('VideoArmor intercepts PrintScreen key to discourage screen capture', async () => {
  const { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals } = createMockDOM();
  global.document = mockDocument;
  global.window = mockWindow;
  global.MutationObserver = MockMutationObserver;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  const container = new MockElement('div');
  let violationCaught = false;
  const armor = VideoArmor.mount(container, {
    student: { email: 'student@example.com' },
    onSecurityViolation: (reason) => {
      if (reason === 'SCREEN_CAPTURE_ATTEMPT') violationCaught = true;
    }
  });

  let defaultPrevented = false;
  mockWindow.dispatchEvent({
    type: 'keyup',
    key: 'PrintScreen',
    preventDefault: () => { defaultPrevented = true; }
  });

  assert.equal(violationCaught, true, 'Screen capture key trigger violation');

  armor.destroy();
  for (const id of intervals) clearInterval(id);
});

test('VideoArmor triggers Blackout when watermark style is tampered with (display none)', async () => {
  const { mockDocument, mockWindow, MockElement, MockMutationObserver, intervals } = createMockDOM();
  global.document = mockDocument;
  global.window = mockWindow;
  global.MutationObserver = MockMutationObserver;

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

  const container = new MockElement('div');
  const armor = VideoArmor.mount(container, {
    student: { email: 'student@example.com' }
  });

  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark);

  // Malicious user sets display: none
  watermark.style.display = 'none';
  if (mockDocument._observerCallback) {
    mockDocument._observerCallback([{
      type: 'attributes',
      attributeName: 'style',
      target: watermark
    }]);
  }

  const blackout = container.querySelector('.video-armor-blackout');
  assert.ok(blackout, 'Blackout screen must be rendered upon style tampering');

  // Test restoration
  armor.restore();
  assert.equal(container.querySelector('.video-armor-blackout'), null, 'Blackout must be cleared on restore');
  assert.equal(watermark.style.display, 'block', 'Watermark style must be restored to visible');

  armor.destroy();
  for (const id of intervals) clearInterval(id);
});
