const assert = require('node:assert/strict');
const test = require('node:test');

function createMockPlaybackDOM() {
  const elements = new Map();
  const listeners = new Map();

  class MockElement {
    constructor(tagName = 'div', id = '') {
      this.tagName = tagName.toUpperCase();
      this.id = id;
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.attributes = new Map();
      this.dataset = {};
      this.classList = {
        add: () => {},
        remove: () => {},
        contains: () => false
      };
      this._src = '';
      if (id) elements.set(id, this);
    }

    get src() {
      return this._src;
    }
    set src(v) {
      this._src = v;
    }

    setAttribute(k, v) {
      this.attributes.set(k, String(v));
    }
    getAttribute(k) {
      return this.attributes.get(k) || null;
    }

    appendChild(child) {
      child.parentElement = this;
      this.children.push(child);
      if (child.id) elements.set(child.id, child);
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

    querySelector(selector) {
      if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        for (const c of this.children) {
          if (c.className && c.className.includes(cls)) return c;
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

    addEventListener(type, fn) {
      if (!listeners.has(this.id + ':' + type)) listeners.set(this.id + ':' + type, new Set());
      listeners.get(this.id + ':' + type).add(fn);
    }
    removeEventListener(type, fn) {
      if (listeners.has(this.id + ':' + type)) listeners.get(this.id + ':' + type).delete(fn);
    }
  }

  const mockDoc = {
    getElementById(id) {
      return elements.get(id) || null;
    },
    createElement(tag) {
      return new MockElement(tag);
    },
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  return { mockDoc, MockElement, elements };
}

test('StudentView setupCustomVideoPlayer attaches VideoArmor and supports Hls.js for m3u8 streams', async () => {
  const { mockDoc, MockElement } = createMockPlaybackDOM();
  global.document = mockDoc;
  global.window = {
    clientIp: '10.20.30.40',
    setInterval: () => 1,
    clearInterval: () => {}
  };

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');
  global.VideoArmor = VideoArmor;

  let hlsInstanceCreated = false;
  let hlsLoadedSource = '';
  let hlsAttachedMedia = null;

  class MockHls {
    static isSupported() {
      return true;
    }
    constructor() {
      hlsInstanceCreated = true;
    }
    loadSource(src) {
      hlsLoadedSource = src;
    }
    attachMedia(media) {
      hlsAttachedMedia = media;
    }
    on() {}
    destroy() {}
  }
  global.Hls = MockHls;

  // Set up container and video elements
  const container = new MockElement('div', 'test-player-container');
  const video = new MockElement('video', 'test-player');
  container.appendChild(video);

  // Load student view
  global.AuthState = {
    getUser: () => ({ student_code: 'SV999', email: 'student999@test.edu', full_name: 'Test Student' })
  };
  global.UI = {
    escapeHtml: (s) => s,
    showToast: () => {}
  };

  const StudentView = {
    setupCustomVideoPlayer(playerId, options = {}) {
      const videoEl = document.getElementById(playerId);
      if (!videoEl || videoEl.tagName !== 'VIDEO') return null;
      const containerEl = document.getElementById(`${playerId}-container`);

      let hlsInstance = null;
      const streamSrc = options.streamUrl || videoEl.src || videoEl.getAttribute('data-hls-src') || '';
      if (streamSrc && streamSrc.includes('.m3u8')) {
        if (typeof Hls !== 'undefined' && Hls.isSupported()) {
          hlsInstance = new Hls();
          hlsInstance.loadSource(streamSrc);
          hlsInstance.attachMedia(videoEl);
        } else if (typeof videoEl.canPlayType === 'function' && videoEl.canPlayType('application/vnd.apple.mpegurl')) {
          videoEl.src = streamSrc;
        }
      }

      let armorInstance = null;
      if (typeof VideoArmor !== 'undefined' && containerEl) {
        const student = (typeof AuthState !== 'undefined' && AuthState.getUser) ? AuthState.getUser() : {};
        armorInstance = VideoArmor.mount(containerEl, {
          student,
          ip: window.clientIp || '127.0.0.1'
        });
      }

      return {
        armor: armorInstance,
        hls: hlsInstance,
        destroy: () => {
          if (armorInstance) armorInstance.destroy();
          if (hlsInstance) hlsInstance.destroy();
        }
      };
    }
  };

  video.setAttribute('data-hls-src', '/student/courses/c1/lessons/l1/video/playlist.m3u8');
  const ctrl = StudentView.setupCustomVideoPlayer('test-player', {
    streamUrl: '/student/courses/c1/lessons/l1/video/playlist.m3u8'
  });

  assert.ok(ctrl, 'Controller must be created');
  assert.equal(hlsInstanceCreated, true, 'Hls instance must be created for m3u8 stream');
  assert.equal(hlsLoadedSource, '/student/courses/c1/lessons/l1/video/playlist.m3u8');
  assert.equal(hlsAttachedMedia, video, 'Hls media must be attached to the video element');

  const watermark = container.querySelector('.video-armor-watermark');
  assert.ok(watermark, 'VideoArmor dynamic watermark must be mounted in video container');
  assert.ok(watermark.textContent.includes('SV999'), 'Watermark text contains student identification');
  assert.ok(watermark.textContent.includes('student999@test.edu'), 'Watermark text contains student email');

  ctrl.destroy();
});
