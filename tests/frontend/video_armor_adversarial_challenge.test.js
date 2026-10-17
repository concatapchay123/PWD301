const assert = require('node:assert/strict');
const test = require('node:test');

// Mock browser environment for VideoArmor adversarial challenge
function createMockArmorDOM() {
  const listeners = new Map();
  let observerCallback = null;

  class MockElement {
    constructor(tagName = 'div', className = '') {
      this.tagName = tagName.toUpperCase();
      this.className = className;
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.attributes = new Map();
      this._textContent = '';
      this._paused = false;
      this.hidden = false;
      this.isConnected = true;
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
      if (observerCallback) {
        observerCallback([{
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
        if (observerCallback) {
          observerCallback([{
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
      return null;
    }
    querySelectorAll(selector) {
      const results = [];
      for (const c of this.children) {
        if (selector === 'video, audio' && (c.tagName === 'VIDEO' || c.tagName === 'AUDIO')) {
          results.push(c);
        }
        if (c.tagName.toLowerCase() === selector.toLowerCase() ||
            (c.className && c.className.includes(selector.replace('.', '')))) {
          results.push(c);
        }
        results.push(...c.querySelectorAll(selector));
      }
      return results;
    }
    pause() {
      this._paused = true;
    }
    closest(selector) {
      return null;
    }
    addEventListener(type, fn) {
      if (!this._listeners) this._listeners = new Map();
      if (!this._listeners.has(type)) this._listeners.set(type, []);
      this._listeners.get(type).push(fn);
    }
    removeEventListener(type, fn) {
      if (!this._listeners || !this._listeners.has(type)) return;
      this._listeners.set(type, this._listeners.get(type).filter(f => f !== fn));
    }
    dispatchEvent(event) {
      if (!this._listeners || !this._listeners.has(event.type)) return;
      for (const fn of this._listeners.get(event.type)) fn(event);
    }
  }

  class MockMutationObserver {
    constructor(cb) {
      this.callback = cb;
      observerCallback = cb;
    }
    observe(target, options) {
      this.target = target;
      this.options = options;
    }
    disconnect() {
      if (observerCallback === this.callback) {
        observerCallback = null;
      }
    }
    trigger(mutations = []) {
      this.callback(mutations);
    }
  }

  const mockDocument = {
    createElement: (tag) => new MockElement(tag),
    addEventListener: (type, fn) => {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
    removeEventListener: () => {},
    dispatchEvent: (event) => {
      const fns = listeners.get(event.type) || [];
      for (const fn of fns) fn(event);
    },
    visibilityState: 'visible'
  };

  const mockWindow = {
    document: mockDocument,
    MutationObserver: MockMutationObserver,
    getComputedStyle: (el) => el.style,
    addEventListener: mockDocument.addEventListener,
    removeEventListener: () => {},
    dispatchEvent: mockDocument.dispatchEvent,
    setInterval: () => 1,
    clearInterval: () => {}
  };

  return { mockDocument, mockWindow, MockElement, MockMutationObserver };
}

function loadVideoArmor(env) {
  global.document = env.mockDocument;
  global.window = env.mockWindow;
  global.MutationObserver = env.mockWindow.MutationObserver;
  try {
    Object.defineProperty(global, 'navigator', {
      value: { clipboard: { writeText: async () => {} } },
      configurable: true,
      writable: true
    });
  } catch (_) {}
  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');
  return VideoArmor;
}

test('Challenge 3.1: VideoArmor mounts forensic DOM node with student identity', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  const armor = VideoArmor.mount(container, {
    student: {
      student_code: 'SV20261017',
      email: 'student_chal@example.edu',
      display_name: 'Nguyen Van Challenger'
    },
    ip: '192.168.1.100'
  });

  const watermarkEl = container.querySelector('.video-armor-watermark');
  assert.ok(watermarkEl, 'Watermark DOM element must be present in player container');
  assert.equal(watermarkEl.getAttribute('data-armor-guard'), 'watermark');

  // Verify text content contains forensic credentials
  const text = watermarkEl.textContent;
  assert.ok(text.includes('SV20261017'), 'Watermark must contain student code');
  assert.ok(text.includes('student_chal@example.edu'), 'Watermark must contain student email');
  assert.ok(text.includes('192.168.1.100'), 'Watermark must contain student IP');
});

test('Challenge 3.2: VideoArmor zero-visible-pixel guarantee and disabled jumping timer', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  const armor = VideoArmor.mount(container, {
    student: { student_code: 'SV999', email: 'test@test.edu' }
  });

  const watermarkEl = container.querySelector('.video-armor-watermark');
  assert.ok(watermarkEl);

  // 1. Invisible Box Dimensions
  assert.equal(watermarkEl.style.width, '1px', 'Width must be 1px minimal footprint');
  assert.equal(watermarkEl.style.height, '1px', 'Height must be 1px minimal footprint');
  assert.equal(watermarkEl.style.overflow, 'hidden', 'Overflow must be hidden');

  // 2. Invisible Typography
  assert.equal(watermarkEl.style.fontSize, '0px', 'Font size must be 0px');
  assert.equal(watermarkEl.style.lineHeight, '0', 'Line height must be 0');
  assert.equal(watermarkEl.style.color, 'transparent', 'Text color must be transparent');

  // 3. Invisible Styling
  assert.equal(watermarkEl.style.backgroundColor, 'transparent', 'Background must be transparent');
  assert.equal(watermarkEl.style.border, 'none', 'Border must be none');
  assert.equal(watermarkEl.style.boxShadow, 'none', 'Box shadow must be none');

  // 4. Alpha Opacity Below 8-bit Quantum
  const opacityVal = Number(watermarkEl.style.opacity);
  assert.ok(opacityVal <= 0.001, 'Opacity must be <= 0.001');
  const alpha8Bit = Math.round(opacityVal * 255);
  assert.equal(alpha8Bit, 0, 'Alpha channel in 8-bit sRGB rounds to exactly 0 (zero visible pixels)');

  // 5. Disabled Jumping Timer (no floating animated artifacts)
  assert.equal(armor.repositionTimer, null, 'Jumping interval timer must be disabled/null');
});

test('Challenge 3.3: Anti-tamper observer triggers blackout upon DOM removal', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  const video = new env.MockElement('video');
  container.appendChild(video);

  let violationReported = null;
  const armor = VideoArmor.mount(container, {
    student: { student_code: 'SV_ATTACKER' },
    onSecurityViolation: (reason) => { violationReported = reason; }
  });

  assert.equal(armor.isBlackedOut, false);
  const watermarkEl = container.querySelector('.video-armor-watermark');
  assert.ok(watermarkEl);

  // Attack: Malicious user removes watermark element from DOM
  container.removeChild(watermarkEl);

  // Assert anti-tamper detected removal and triggered blackout
  assert.equal(armor.isBlackedOut, true, 'Blackout must trigger when watermark is removed');
  assert.equal(video._paused, true, 'Video media must be paused upon blackout');

  const blackoutCard = container.querySelector('.video-armor-blackout');
  assert.ok(blackoutCard, 'Blackout card overlay must be mounted in container');
  assert.equal(blackoutCard.getAttribute('data-armor-blackout'), 'true');
});

test('Challenge 3.4: Anti-tamper observer triggers blackout upon CSS tampering', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const tamperingScenarios = [
    {
      name: 'Setting hidden attribute',
      apply: (el) => { el.hidden = true; }
    },
    {
      name: 'Setting display to none',
      apply: (el) => { el.style.display = 'none'; }
    },
    {
      name: 'Setting visibility to hidden',
      apply: (el) => { el.style.visibility = 'hidden'; }
    },
    {
      name: 'Setting visibility to collapse',
      apply: (el) => { el.style.visibility = 'collapse'; }
    },
    {
      name: 'Setting opacity to 0',
      apply: (el) => { el.style.opacity = '0'; }
    }
  ];

  for (const scenario of tamperingScenarios) {
    const container = new env.MockElement('div', 'player-container');
    const armor = VideoArmor.mount(container, {
      student: { student_code: 'SV_CSS_HACK' }
    });

    const watermarkEl = container.querySelector('.video-armor-watermark');
    assert.ok(watermarkEl);
    assert.equal(armor.isBlackedOut, false);

    // Apply CSS attack
    scenario.apply(watermarkEl);

    // Notify observer of attribute/style mutation
    armor._inspectMutations([{
      type: 'attributes',
      attributeName: 'style',
      target: watermarkEl
    }]);

    assert.equal(
      armor.isBlackedOut,
      true,
      `Blackout must trigger when tampering via: ${scenario.name}`
    );
  }
});

test('Challenge 3.5: Anti-tamper triggers blackout upon DOM re-parenting attack', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  const outsideDiv = new env.MockElement('div', 'outside-wrapper');

  const armor = VideoArmor.mount(container, {
    student: { student_code: 'SV_REPARENT' }
  });

  const watermarkEl = container.querySelector('.video-armor-watermark');
  assert.ok(watermarkEl);
  assert.equal(armor.isBlackedOut, false);

  // Attack: Move watermark element to an outside container
  outsideDiv.appendChild(watermarkEl);

  armor._inspectMutations([{
    type: 'childList',
    target: container
  }]);

  assert.equal(
    armor.isBlackedOut,
    true,
    'Blackout must trigger if watermark element parent is not the player container'
  );
});

test('Challenge 3.6: VideoArmor intercepts all DevTools & View Source shortcut keys', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const devtoolsKeys = [
    { name: 'F12 key', event: { key: 'F12', keyCode: 123 } },
    { name: 'Ctrl+Shift+I', event: { key: 'I', keyCode: 73, ctrlKey: true, shiftKey: true } },
    { name: 'Ctrl+Shift+J', event: { key: 'J', keyCode: 74, ctrlKey: true, shiftKey: true } },
    { name: 'Ctrl+Shift+C', event: { key: 'C', keyCode: 67, ctrlKey: true, shiftKey: true } },
    { name: 'Ctrl+U', event: { key: 'u', keyCode: 85, ctrlKey: true } },
    { name: 'Cmd+Option+I (macOS)', event: { key: 'i', keyCode: 73, metaKey: true, altKey: true } },
    { name: 'Cmd+Option+J (macOS)', event: { key: 'j', keyCode: 74, metaKey: true, altKey: true } },
    { name: 'Cmd+Option+C (macOS)', event: { key: 'c', keyCode: 67, metaKey: true, altKey: true } },
    { name: 'Cmd+Option+U (macOS)', event: { key: 'u', keyCode: 85, metaKey: true, altKey: true } }
  ];

  for (const shortcut of devtoolsKeys) {
    const container = new env.MockElement('div', 'player-container');
    let reportedReason = null;
    const armor = VideoArmor.mount(container, {
      student: { student_code: 'DEV_ATTACKER' },
      onSecurityViolation: (reason) => { reportedReason = reason; }
    });

    let defaultPrevented = false;
    let stopPropagated = false;
    const keyEvent = {
      type: 'keydown',
      ...shortcut.event,
      preventDefault: () => { defaultPrevented = true; },
      stopPropagation: () => { stopPropagated = true; }
    };

    env.mockWindow.dispatchEvent(keyEvent);

    assert.equal(armor.isBlackedOut, true, `${shortcut.name} must trigger Blackout Shield`);
    assert.equal(reportedReason, 'DEVTOOLS_DETECTED', `${shortcut.name} must report DEVTOOLS_DETECTED`);
    assert.equal(defaultPrevented, true, `${shortcut.name} must prevent browser default action`);

    const blackoutCard = container.querySelector('.video-armor-blackout');
    assert.ok(blackoutCard, 'Blackout card overlay must be present');
    const reasonEl = blackoutCard.querySelector('.video-armor-reason');
    assert.ok(reasonEl);
    assert.equal(reasonEl.textContent, 'PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN');

    armor.destroy();
  }
});

test('Challenge 3.7: VideoArmor intercepts Screen Capture shortcuts and wipes clipboard', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  let clipboardCleared = false;
  Object.defineProperty(global, 'navigator', {
    value: {
      clipboard: {
        writeText: (val) => {
          if (val === '') clipboardCleared = true;
          return Promise.resolve();
        }
      }
    },
    configurable: true,
    writable: true
  });

  const captureKeys = [
    { name: 'PrintScreen', event: { key: 'PrintScreen', keyCode: 44 } },
    { name: 'Win+Shift+S', event: { key: 's', keyCode: 83, metaKey: true, shiftKey: true } },
    { name: 'Meta+Shift+S', event: { key: 'S', keyCode: 83, metaKey: true, shiftKey: true } },
    { name: 'Cmd+Shift+4 (macOS)', event: { key: '4', keyCode: 52, metaKey: true, shiftKey: true } }
  ];

  for (const capture of captureKeys) {
    clipboardCleared = false;
    const container = new env.MockElement('div', 'player-container');
    let reportedReason = null;
    const armor = VideoArmor.mount(container, {
      student: { student_code: 'CAPTURE_ATTACKER' },
      onSecurityViolation: (reason) => { reportedReason = reason; }
    });

    let defaultPrevented = false;
    const keyEvent = {
      type: 'keyup',
      ...capture.event,
      preventDefault: () => { defaultPrevented = true; }
    };

    env.mockWindow.dispatchEvent(keyEvent);

    assert.equal(armor.isBlackedOut, true, `${capture.name} must trigger Blackout Shield`);
    assert.equal(reportedReason, 'SCREEN_CAPTURE_ATTEMPT', `${capture.name} must report SCREEN_CAPTURE_ATTEMPT`);
    assert.equal(clipboardCleared, true, `${capture.name} must wipe clipboard content`);

    const blackoutCard = container.querySelector('.video-armor-blackout');
    const reasonEl = blackoutCard.querySelector('.video-armor-reason');
    assert.equal(reasonEl.textContent, 'PHÁT HIỆN THAO TÁC CHỤP / QUAY MÀN HÌNH');

    armor.destroy();
  }
});

test('Challenge 3.8: VideoArmor blocks Context Menu (Inspect Element) and triggers Blackout', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  let reportedReason = null;
  const armor = VideoArmor.mount(container, {
    student: { student_code: 'RIGHT_CLICK_USER' },
    onSecurityViolation: (reason) => { reportedReason = reason; }
  });

  let defaultPrevented = false;
  container.dispatchEvent({
    type: 'contextmenu',
    preventDefault: () => { defaultPrevented = true; },
    stopPropagation: () => {}
  });

  assert.equal(armor.isBlackedOut, true, 'Right click context menu must trigger Blackout Shield');
  assert.equal(reportedReason, 'CONTEXT_MENU_BLOCKED', 'Violation reason must be CONTEXT_MENU_BLOCKED');
  assert.equal(defaultPrevented, true, 'contextmenu event default must be prevented');

  const blackoutCard = container.querySelector('.video-armor-blackout');
  const reasonEl = blackoutCard.querySelector('.video-armor-reason');
  assert.equal(reasonEl.textContent, 'PHÁT HIỆN THAO TÁC CHUỘT PHẢI MÃ NGUỒN');

  armor.destroy();
});

test('Challenge 3.9: VideoArmor automatic DevTools timing delta detection bouncer', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  let reportedReason = null;
  const armor = VideoArmor.mount(container, {
    student: { student_code: 'DEBUGGER_PAUSE_USER' },
    onSecurityViolation: (reason) => { reportedReason = reason; }
  });

  // Mock Date.now to simulate a 150ms execution delay caused by DevTools debugger pause
  const originalNow = Date.now;
  let callCount = 0;
  Date.now = () => {
    callCount++;
    return callCount === 1 ? 1000 : 1150; // delta = 150ms > 100ms
  };

  try {
    armor._checkDevTools();
    assert.equal(armor.isBlackedOut, true, 'Debugger timing delta > 100ms must trigger Blackout Shield');
    assert.equal(reportedReason, 'DEVTOOLS_DETECTED', 'Violation reason must be DEVTOOLS_DETECTED');
  } finally {
    Date.now = originalNow;
    armor.destroy();
  }
});

test('Challenge 3.10: Blackout Shield overlay UI validation and complete restore flow', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);

  const container = new env.MockElement('div', 'player-container');
  const video = new env.MockElement('video');
  container.appendChild(video);

  let restored = false;
  const armor = VideoArmor.mount(container, {
    student: {
      student_code: 'SV_RESTORATION',
      full_name: 'Tran Van Hoc',
      email: 'restore@student.edu'
    },
    ip: '114.119.130.1',
    onRestore: () => { restored = true; }
  });

  video._paused = false;

  // Trigger blackout
  armor.triggerBlackout('DEVTOOLS_DETECTED');

  assert.equal(armor.isBlackedOut, true);
  assert.equal(video._paused, true, 'All playing media must be paused upon blackout');

  const blackout = container.querySelector('.video-armor-blackout');
  assert.ok(blackout, 'Blackout overlay must exist');
  assert.equal(blackout.getAttribute('data-armor-blackout'), 'true');

  const card = container.querySelector('.video-armor-blackout-card');
  assert.ok(card, 'Warning card must exist');
  assert.ok(card.textContent.includes('🛡️ CẢNH BÁO AN NINH BẢN QUYỀN'), 'Must display red security warning title');

  const badge = container.querySelector('.video-armor-badge');
  assert.ok(badge, 'Forensic watermark badge must be rendered inside warning card');
  assert.ok(badge.textContent.includes('SV_RESTORATION'));
  assert.ok(badge.textContent.includes('restore@student.edu'));

  const restoreBtn = container.querySelector('.video-armor-restore-btn');
  assert.ok(restoreBtn, 'Restore button must be present in card');
  assert.equal(restoreBtn.textContent, 'Khôi phục và Tiếp tục học');

  // Click restore button to recover session
  restoreBtn.dispatchEvent({ type: 'click' });

  assert.equal(armor.isBlackedOut, false, 'isBlackedOut must be reset to false after restore');
  assert.equal(container.querySelector('.video-armor-blackout'), null, 'Blackout overlay must be removed from container');
  assert.equal(restored, true, 'onRestore callback must fire');

  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark, 'Watermark element must remain intact');
  assert.equal(watermark.style.opacity, '0.001', 'Watermark opacity must be reset to non-visible quantum');

  armor.destroy();
});

test('Challenge 3.11: ExamStore integration with VideoArmor', () => {
  const env = createMockArmorDOM();
  const VideoArmor = loadVideoArmor(env);
  global.VideoArmor = VideoArmor;

  const { ExamStore } = require('../../frontend/assets/js/exam-store.js');
  const container = new env.MockElement('div', 'exam-console');

  const armor = ExamStore.attachArmor(container, {
    student: { student_code: 'EXAM_CANDIDATE' },
    ip: '10.10.10.1'
  });

  assert.ok(armor, 'ExamStore.attachArmor must return VideoArmor instance');
  assert.equal(armor.options.globalProtection, true, 'Exam armor must enforce globalProtection');

  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark, 'Forensic watermark must be mounted on exam container');
  assert.ok(watermark.textContent.includes('EXAM_CANDIDATE'));

  armor.destroy();
});
