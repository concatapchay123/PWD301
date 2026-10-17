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
      this.textContent = '';
      this._paused = false;
      this.hidden = false;
      this.isConnected = true;
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
    setInterval: () => 1,
    clearInterval: () => {}
  };

  return { mockDocument, mockWindow, MockElement, MockMutationObserver };
}

function loadVideoArmor(env) {
  global.document = env.mockDocument;
  global.window = env.mockWindow;
  global.MutationObserver = env.mockWindow.MutationObserver;
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
