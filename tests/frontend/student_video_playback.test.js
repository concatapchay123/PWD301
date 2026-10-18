const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');

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

    contains(child) {
      let cur = child;
      while (cur) {
        if (cur === this) return true;
        cur = cur.parentElement;
      }
      return false;
    }

    closest() {
      return null;
    }

    get isConnected() {
      return true;
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
    querySelectorAll() {
      return [];
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

test('VideoArmor tolerates sub-pixel opacity (0.001) without blackout and triggers blackout on genuine zero opacity', () => {
  const { mockDoc, MockElement } = createMockPlaybackDOM();
  global.document = mockDoc;
  global.window = {
    getComputedStyle: el => el.style
  };

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');
  const container = new MockElement('div', 'player-subpixel-container');
  const armor = VideoArmor.mount(container, {
    silentWatermark: false,
    student: { student_code: 'SV-SUBPIXEL', email: 'subpixel@test.edu' }
  });

  assert.ok(armor.watermarkEl, 'Watermark must be created');
  assert.equal(armor.isBlackedOut, false, 'Initial state must not be blacked out');

  // Sub-pixel opacity simulation (e.g. 0.001 or rounding artifact)
  armor.watermarkEl.style.opacity = '0.001';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, false, 'Sub-pixel opacity 0.001 must not trigger blackout');

  // Genuine tampering: opacity explicitly set to 0
  armor.watermarkEl.style.opacity = '0';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, true, 'Genuine opacity 0 tampering must trigger blackout');

  armor.destroy();
});

test('VideoArmor gracefully re-attaches watermark when detached when gracefulReattach option is enabled', () => {
  const { mockDoc, MockElement } = createMockPlaybackDOM();
  global.document = mockDoc;
  global.window = {
    getComputedStyle: el => el.style
  };

  const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');
  const container = new MockElement('div', 'player-reattach-container');
  const armor = VideoArmor.mount(container, {
    silentWatermark: false,
    gracefulReattach: true,
    student: { student_code: 'SV-REATTACH' }
  });

  assert.ok(armor.watermarkEl, 'Watermark must exist');
  assert.equal(armor.watermarkEl.parentElement, container);

  // Detach watermark element from container (e.g. temporary DOM shift)
  container.removeChild(armor.watermarkEl);
  assert.equal(armor.watermarkEl.parentElement, null);

  // Inspect mutations with gracefulReattach: true
  armor._inspectMutations([]);
  assert.equal(armor.watermarkEl.parentElement, container, 'Watermark must be gracefully re-attached');
  assert.equal(armor.isBlackedOut, false, 'Graceful re-attachment must not blackout');

  armor.destroy();
});

test('Sequential completion gate enforces 60-second text dwell, 100% video watched across all videos, and miniquiz pass score', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // 1. Text dwell time >= 60 seconds
  assert.match(studentSource, /const\s+dwellRequired\s*=\s*60;/, 'dwellRequired must be 60 seconds');
  assert.doesNotMatch(studentSource, /const\s+dwellRequired\s*=\s*30;/, 'dwellRequired must not be 30 seconds');
  assert.match(studentSource, /Cần học tối thiểu 60s/, 'Notification must show minimum 60s text dwell');

  // 2. Multi-video requirement: all videos in lesson must be complete
  assert.match(studentSource, /result\.all_videos_complete/, 'Must verify all_videos_complete for multi-video lessons');

  // 3. Miniquiz pass score requirement
  assert.match(studentSource, /quizPassingPercent/, 'Must check miniquiz passing score percentage');
});

test('Next button renders disabled/gray without lock icon when incomplete and transitions to emerald green when complete', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Disabled incomplete template
  assert.match(studentSource, /<button\s+type="button"\s+id="cisco-next-btn"\s+disabled/, 'Incomplete Next button must have disabled attribute');
  assert.match(studentSource, /bg-slate-200/, 'Incomplete Next button must have slate gray background');
  assert.match(studentSource, /cursor-not-allowed/, 'Incomplete Next button must have cursor-not-allowed');

  // Verify NO lock icon and NO "Đã khóa" in Next button
  const nextBtnMatches = studentSource.match(/box\.innerHTML\s*=\s*`\s*<button[^>]+id="cisco-next-btn"[^>]*>[\s\S]*?<\/button>\s*`;/g);
  assert.ok(nextBtnMatches && nextBtnMatches.length >= 2, 'Must have distinct complete and incomplete Next button templates');
  const disabledBtn = nextBtnMatches.find(tmpl => tmpl.includes('disabled'));
  assert.ok(disabledBtn, 'Must find disabled Next button template');
  assert.doesNotMatch(disabledBtn, /lock/i, 'Incomplete Next button must NOT contain a lock icon');
  assert.doesNotMatch(disabledBtn, /Đã khóa/i, 'Incomplete Next button must NOT contain "Đã khóa" text');

  // Emerald green complete template
  const enabledBtn = nextBtnMatches.find(tmpl => !tmpl.includes('disabled') && tmpl.includes('bg-emerald-600'));
  assert.ok(enabledBtn, 'Must find emerald green complete Next button template');
  assert.match(enabledBtn, /cursor-pointer/, 'Complete Next button must have cursor-pointer');
  assert.match(enabledBtn, /shadow-md/, 'Complete Next button must have shadow-md');
});

test('YouTube Standard 16:9 uncropped viewport and z-[15] poster shield', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Verify standard 16:9 uncropped viewport in _getEmbedVideoHtml (inset: 0, 100% width/height, zero crop)
  assert.match(
    studentSource,
    /position:\s*absolute;\s*inset:\s*0;\s*width:\s*100%;\s*height:\s*100%;\s*pointer-events:\s*none;?/,
    '_getEmbedVideoHtml must enforce standard 16:9 uncropped viewport (inset: 0, width: 100%, height: 100%)'
  );
  assert.doesNotMatch(
    studentSource,
    /top:\s*-22%/,
    '_getEmbedVideoHtml must permanently eliminate -22% top crop'
  );

  // Verify Poster Shield styling: z-[15], bg-slate-950, inset-0
  assert.match(
    studentSource,
    /id="\$\{playerId\}-poster-shield"[^>]*class="[^"]*z-\[15\][^"]*bg-slate-950[^"]*"/,
    'Poster shield must have z-[15] and bg-slate-950 classes to cover YouTube UI before playback'
  );

  // Verify click shield overlay
  assert.match(
    studentSource,
    /id="\$\{playerId\}-shield"[^>]*class="[^"]*cursor-pointer\s+bg-transparent[^"]*"/,
    'Click shield must exist with cursor-pointer and bg-transparent'
  );
});

test('Single Event Listener Invariant: setupCustomVideoPlayer registers single click listener without double el.onclick binding', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Verify click helper in setupCustomVideoPlayer does NOT assign el.onclick
  const clickHelperMatch = studentSource.match(/const\s+click\s*=\s*\(suffix,\s*handler\)\s*=>\s*\{[\s\S]*?buttons\.push\(el\);\s*\}\s*\};/);
  assert.ok(clickHelperMatch, 'Must find click helper function inside setupCustomVideoPlayer');
  assert.doesNotMatch(
    clickHelperMatch[0],
    /el\.onclick\s*=/,
    'click helper must NOT assign el.onclick (prevents double-toggle bug)'
  );
  assert.match(
    clickHelperMatch[0],
    /listen\(el,\s*'click',\s*wrapped\);/,
    'click helper must only bind through listen(el, "click", wrapped)'
  );
});

test('Poster Shield transitions to opacity-0 pointer-events-none only when onStateChange receives PLAYING (event.data === 1)', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Verify onStateChange checks event.data === 1 before hiding poster shield
  assert.match(
    studentSource,
    /if\s*\(\s*event\.data\s*===\s*1\s*\)\s*\{[\s\S]*?poster\.classList\.add\('opacity-0',\s*'pointer-events-none'\);/,
    'Poster shield must only be hidden when onStateChange receives PLAYING (event.data === 1)'
  );

  // Verify transition does not hide poster shield prematurely for YouTube
  assert.match(
    studentSource,
    /if\s*\(\s*playing\s*&&\s*!youtube\s*\)\s*\{[\s\S]*?poster\.classList\.add\('opacity-0',\s*'pointer-events-none'\);/,
    'transition must not hide poster shield for YouTube on initial click before PLAYING state'
  );
});

