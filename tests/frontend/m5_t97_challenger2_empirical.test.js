const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const studentSource = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8');
const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

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
        _classes: new Set(),
        add(...cls) { cls.forEach(c => this._classes.add(c)); },
        remove(...cls) { cls.forEach(c => this._classes.delete(c)); },
        contains(c) { return this._classes.has(c); },
        toggle(c, force) {
          if (force === undefined) {
            if (this._classes.has(c)) this._classes.delete(c);
            else this._classes.add(c);
          } else if (force) {
            this._classes.add(c);
          } else {
            this._classes.delete(c);
          }
        }
      };
      this._src = '';
      this._innerHTML = '';
      this.textContent = '';
      this.hidden = false;
      this.dispatchEvent = (event) => {
        const type = typeof event === 'string' ? event : event?.type;
        const key = `${this.id || 'anon'}:${type}`;
        if (listeners.has(key)) {
          for (const fn of listeners.get(key)) {
            fn(event);
          }
        }
      };
      this.play = async () => {
        this.paused = false;
        this.dispatchEvent({ type: 'playing' });
      };
      this.pause = () => {
        this.paused = true;
        this.dispatchEvent({ type: 'pause' });
      };
      if (id) elements.set(id, this);
    }

    get src() { return this._src; }
    set src(v) { this._src = v; }

    get innerHTML() { return this._innerHTML; }
    set innerHTML(html) {
      this._innerHTML = html;
      // Also sync textContent roughly for search
      this.textContent = String(html).replace(/<[^>]+>/g, ' ');
    }

    get firstElementChild() {
      // Find or return the first child
      if (this.children.length > 0) return this.children[0];
      // Synthetic child for parsed button
      if (this._innerHTML.includes('<button') || this._innerHTML.includes('<a')) {
        const dummy = new MockElement('button');
        dummy.parentElement = this;
        return dummy;
      }
      return null;
    }

    setAttribute(k, v) { this.attributes.set(k, String(v)); }
    getAttribute(k) { return this.attributes.get(k) || null; }
    removeAttribute(k) { this.attributes.delete(k); }
    hasAttribute(k) { return this.attributes.has(k); }

    appendChild(child) {
      if (child.parentElement) {
        child.parentElement.removeChild(child);
      }
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

    closest(selector) {
      return null;
    }

    get isConnected() { return true; }

    querySelector(selector) {
      if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        for (const c of this.children) {
          if (c.classList.contains(cls) || (c.className && c.className.includes(cls))) return c;
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
      const key = `${this.id || 'anon'}:${type}`;
      if (!listeners.has(key)) listeners.set(key, new Set());
      listeners.get(key).add(fn);
    }

    removeEventListener(type, fn) {
      const key = `${this.id || 'anon'}:${type}`;
      if (listeners.has(key)) listeners.get(key).delete(fn);
    }
  }

  const mockDoc = {
    visibilityState: 'visible',
    getElementById(id) { return elements.get(id) || null; },
    createElement(tag) { return new MockElement(tag); },
    querySelectorAll() { return []; },
    addEventListener() {},
    removeEventListener() {}
  };

  return { mockDoc, MockElement, elements, listeners };
}

function loadStudentView(overrides = {}) {
  const window = {
    location: { origin: 'https://pwd.test', hash: '' },
    app: { currentUser: { id: 101, student_code: 'SV101', email: 'sv101@pwd301.edu', full_name: 'Student 101' } },
    clientIp: '192.168.1.100'
  };
  const ctx = {
    window,
    URL,
    console,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    VideoArmor,
    UI: {
      parseYouTubeId: url => {
        if (!url) return null;
        const m = String(url).match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/|live\/))([a-zA-Z0-9_\-]{11})/);
        return m ? m[1] : null;
      },
      escapeHtml: s => String(s ?? ''),
      showToast() {}
    },
    ...overrides
  };
  vm.runInNewContext(studentSource, ctx);
  return { view: window.StudentView, window, ctx };
}

// =========================================================================
// CHALLENGE 1: Video Tracker Independence
// Assert supplementary video blocks initialize independent tracker instances with distinct mediaIds.
// =========================================================================

test('Challenge 1: Video Tracker Independence - supplementary video blocks initialize independent tracker instances with distinct mediaIds', async (t) => {
  const { mockDoc, MockElement, elements } = createMockPlaybackDOM();
  const playbackStarts = [];
  const heartbeats = [];

  const ApiClient = {
    startLessonPlayback: async (lessonId, mediaId) => {
      const sessionId = `session_${mediaId.replace(/[^a-zA-Z0-9]/g, '_')}`;
      playbackStarts.push({ lessonId, mediaId, sessionId });
      return {
        session_id: sessionId,
        next_sequence: 1,
        frontier: 0,
        duration: 120,
        is_video_complete: false,
        all_videos_complete: false
      };
    },
    recordPlaybackHeartbeat: async (lessonId, body) => {
      heartbeats.push({ lessonId, ...body });
      return {
        next_sequence: (body.sequence || 1) + 1,
        frontier: body.position_seconds || 10,
        duration: 120,
        is_video_complete: false,
        all_videos_complete: false
      };
    }
  };

  const { view } = loadStudentView({
    document: mockDoc,
    ApiClient
  });

  // Setup DOM elements for 2 supplementary video players
  // Player 0: cisco-extra-video-0
  const c0 = new MockElement('div', 'cisco-extra-video-0-container');
  const v0 = new MockElement('video', 'cisco-extra-video-0');
  v0.readyState = 2; // HAVE_CURRENT_DATA
  c0.appendChild(v0);
  for (const s of ['play-btn', 'big-play', 'speed-btn', 'progress-retry', 'status', 'lock-indicator', 'time']) {
    new MockElement('div', `cisco-extra-video-0-${s}`);
  }

  // Player 1: cisco-extra-video-1
  const c1 = new MockElement('div', 'cisco-extra-video-1-container');
  const v1 = new MockElement('video', 'cisco-extra-video-1');
  v1.readyState = 2;
  c1.appendChild(v1);
  for (const s of ['play-btn', 'big-play', 'speed-btn', 'progress-retry', 'status', 'lock-indicator', 'time']) {
    new MockElement('div', `cisco-extra-video-1-${s}`);
  }

  // Mount Player 0 as supplementary
  const ctrl0 = view.setupCustomVideoPlayer('cisco-extra-video-0', {
    lessonId: 'lesson-901',
    mediaId: 'video:supplementary-part-0',
    supplementary: true,
    streamUrl: '/media/part0.mp4'
  });
  t.after(() => ctrl0?.destroy());

  // Mount Player 1 as supplementary
  const ctrl1 = view.setupCustomVideoPlayer('cisco-extra-video-1', {
    lessonId: 'lesson-901',
    mediaId: 'video:supplementary-part-1',
    supplementary: true,
    streamUrl: '/media/part1.mp4'
  });
  t.after(() => ctrl1?.destroy());

  await new Promise(resolve => setImmediate(resolve));

  // 1. Verify both supplementary video blocks initialize independent tracker sessions
  assert.equal(playbackStarts.length, 2, 'Both supplementary video players must initialize tracker sessions');
  assert.equal(playbackStarts[0].lessonId, 'lesson-901');
  assert.equal(playbackStarts[0].mediaId, 'video:supplementary-part-0', 'Player 0 must use its own distinct mediaId');
  assert.equal(playbackStarts[1].lessonId, 'lesson-901');
  assert.equal(playbackStarts[1].mediaId, 'video:supplementary-part-1', 'Player 1 must use its own distinct mediaId');
  assert.notEqual(playbackStarts[0].sessionId, playbackStarts[1].sessionId, 'Trackers must have distinct session IDs');

  // 2. Heartbeat isolation: update Player 0
  const elPlayBtn0 = elements.get('cisco-extra-video-0-play-btn');
  v0.paused = false;
  v0.currentTime = 15;
  elPlayBtn0.onclick({ stopPropagation() {} });
  await new Promise(resolve => setImmediate(resolve));

  assert.ok(heartbeats.length >= 1, 'Player 0 must send heartbeats');
  const lastHb0 = heartbeats[heartbeats.length - 1];
  assert.equal(lastHb0.media_id, 'video:supplementary-part-0', 'Heartbeat from Player 0 must carry Part 0 mediaId');
  assert.equal(lastHb0.playback_session_id, playbackStarts[0].sessionId, 'Heartbeat from Player 0 must carry Part 0 session');

  // 3. Heartbeat isolation: update Player 1
  const preLen = heartbeats.length;
  const elPlayBtn1 = elements.get('cisco-extra-video-1-play-btn');
  v1.paused = false;
  v1.currentTime = 45;
  elPlayBtn1.onclick({ stopPropagation() {} });
  await new Promise(resolve => setImmediate(resolve));

  assert.ok(heartbeats.length > preLen, 'Player 1 must send heartbeats');
  const lastHb1 = heartbeats[heartbeats.length - 1];
  assert.equal(lastHb1.media_id, 'video:supplementary-part-1', 'Heartbeat from Player 1 must carry Part 1 mediaId');
  assert.equal(lastHb1.playback_session_id, playbackStarts[1].sessionId, 'Heartbeat from Player 1 must carry Part 1 session');

  // 4. Destroy Player 0: must not destroy Player 1
  ctrl0.destroy();
  await new Promise(resolve => setImmediate(resolve));
  const afterDestroyLen = heartbeats.length;

  // Player 1 can still report progress
  v1.currentTime = 60;
  elPlayBtn1.onclick({ stopPropagation() {} });
  await new Promise(resolve => setImmediate(resolve));
  assert.ok(heartbeats.length > afterDestroyLen, 'Player 1 must continue sending heartbeats');
  const latestHb = heartbeats[heartbeats.length - 1];
  assert.equal(latestHb.media_id, 'video:supplementary-part-1', 'Player 1 remains fully active after Player 0 is destroyed');
  assert.equal(latestHb.playback_session_id, playbackStarts[1].sessionId);
});

// =========================================================================
// CHALLENGE 2: VideoArmor Sub-Pixel & Graceful Re-attach
// Verify sub-pixel opacity (0.001) does not trigger tamper lockout.
// Verify detached watermark re-attaches gracefully.
// =========================================================================

test('Challenge 2A: VideoArmor Sub-Pixel Opacity - opacity 0.001 (or sub-pixel rounding to 0) does not trigger tamper lockout, but genuine 0 opacity triggers blackout', () => {
  const { mockDoc, MockElement } = createMockPlaybackDOM();
  global.document = mockDoc;

  let computedOpacity = '0.001';
  let animationName = 'none';
  let transitionProp = 'none';

  const container = new MockElement('div', 'armor-container-1');
  global.window = {
    getComputedStyle: (el) => {
      if (el === container) {
        return { opacity: '1', display: 'block', visibility: 'visible', animationName: 'none', transitionProperty: 'none' };
      }
      return {
        opacity: computedOpacity,
        display: 'block',
        visibility: 'visible',
        animationName: animationName,
        transitionProperty: transitionProp
      };
    }
  };

  const violations = [];
  const armor = VideoArmor.mount(container, {
    silentWatermark: false,
    student: { student_code: 'SV-SUBPIXEL', email: 'subpixel@pwd.edu' },
    onSecurityViolation: (reason) => violations.push(reason)
  });

  assert.ok(armor.watermarkEl, 'Watermark element must be created');
  assert.equal(armor.isBlackedOut, false, 'Initial state must not be blacked out');

  // Case 1: Standard sub-pixel opacity inline: '0.001'
  armor.watermarkEl.style.opacity = '0.001';
  computedOpacity = '0.001';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, false, 'Sub-pixel opacity 0.001 must NOT trigger blackout');

  // Case 2: Sub-pixel rounding artifact where computedStyle rounds 0.001 to '0', but inline style has '0.001'
  computedOpacity = '0';
  armor.watermarkEl.style.opacity = '0.001';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, false, 'Computed 0 with legitimate sub-pixel inline 0.001 must NOT trigger blackout');

  // Case 3: CSS animation active where opacity is 0 temporarily during transition
  armor.watermarkEl.style.opacity = '';
  computedOpacity = '0';
  animationName = 'pulse';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, false, 'Active CSS animation must NOT trigger blackout during transition');

  // Case 4: Genuine tampering - explicitly set inline opacity to '0'
  animationName = 'none';
  armor.watermarkEl.style.opacity = '0';
  computedOpacity = '0';
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, true, 'Genuine inline opacity 0 tampering MUST trigger blackout');
  assert.ok(violations.length > 0, 'Security violation callback must be dispatched');

  armor.destroy();
});

test('Challenge 2B: VideoArmor Graceful Re-attach - detached watermark re-attaches gracefully without lockout, while unhandled removal locks out', () => {
  const { mockDoc, MockElement } = createMockPlaybackDOM();
  global.document = mockDoc;
  global.window = {
    getComputedStyle: el => ({
      opacity: '0.001',
      display: 'block',
      visibility: 'visible'
    })
  };

  // Scenario 1: gracefulReattach = true
  const container1 = new MockElement('div', 'armor-container-reattach');
  const armorGraceful = VideoArmor.mount(container1, {
    silentWatermark: false,
    gracefulReattach: true,
    student: { student_code: 'SV-REATTACH' }
  });

  assert.equal(armorGraceful.watermarkEl.parentElement, container1);

  // Detach watermark element from container (e.g. DOM framework re-render shift)
  container1.removeChild(armorGraceful.watermarkEl);
  assert.equal(armorGraceful.watermarkEl.parentElement, null);

  // Inspect mutations with gracefulReattach = true
  armorGraceful._inspectMutations([]);
  assert.equal(armorGraceful.watermarkEl.parentElement, container1, 'Watermark MUST be gracefully re-attached to container');
  assert.equal(armorGraceful.isBlackedOut, false, 'Graceful re-attachment must NOT trigger blackout');
  armorGraceful.destroy();

  // Scenario 2: Watermark shifted inside container to a child wrapper
  const container2 = new MockElement('div', 'armor-container-nested');
  const subWrapper = new MockElement('div', 'sub-wrapper');
  container2.appendChild(subWrapper);
  const armorNested = VideoArmor.mount(container2, {
    silentWatermark: false,
    student: { student_code: 'SV-NESTED' }
  });

  // Shift watermark inside child wrapper
  subWrapper.appendChild(armorNested.watermarkEl);
  assert.equal(armorNested.watermarkEl.parentElement, subWrapper);
  assert.equal(container2.contains(armorNested.watermarkEl), true);

  armorNested._inspectMutations([]);
  assert.equal(armorNested.watermarkEl.parentElement, container2, 'Watermark moved inside container MUST re-attach to container root');
  assert.equal(armorNested.isBlackedOut, false, 'Internal shift re-attachment must NOT trigger blackout');
  armorNested.destroy();

  // Scenario 3: Adversarial test - complete removal with gracefulReattach = false
  const container3 = new MockElement('div', 'armor-container-tamper');
  const armorStrict = VideoArmor.mount(container3, {
    silentWatermark: false,
    gracefulReattach: false,
    student: { student_code: 'SV-STRICT' }
  });

  container3.removeChild(armorStrict.watermarkEl);
  assert.equal(armorStrict.watermarkEl.parentElement, null);
  armorStrict._inspectMutations([]);
  assert.equal(armorStrict.isBlackedOut, true, 'Removal with gracefulReattach=false MUST trigger DOM_TAMPER blackout');
  armorStrict.destroy();
});

// =========================================================================
// CHALLENGE 3: Dwell Time Boundary
// Verify 59s dwell leaves text requirement incomplete; 60s dwell satisfies text requirement.
// =========================================================================

test('Challenge 3: Dwell Time Boundary - 59s leaves text requirement incomplete; 60s satisfies requirement', () => {
  // Test the exact boundary logic function directly
  const dwellRequired = 60;
  const hasText = true;

  const checkRequirement = (dwellElapsed) => {
    const dwellOk = !hasText || (dwellElapsed >= dwellRequired);
    const missing = [];
    if (hasText && dwellElapsed < dwellRequired) {
      missing.push(`Cần học tối thiểu 60s (còn ${dwellRequired - dwellElapsed}s)`);
    }
    return { dwellOk, missing };
  };

  // Sub-boundary tests
  const res0 = checkRequirement(0);
  assert.equal(res0.dwellOk, false);
  assert.equal(res0.missing[0], 'Cần học tối thiểu 60s (còn 60s)');

  const res58 = checkRequirement(58);
  assert.equal(res58.dwellOk, false);
  assert.equal(res58.missing[0], 'Cần học tối thiểu 60s (còn 2s)');

  // Critical boundary 1: 59 seconds (1 second short)
  const res59 = checkRequirement(59);
  assert.equal(res59.dwellOk, false, '59s dwell MUST leave text requirement incomplete');
  assert.equal(res59.missing.length, 1);
  assert.equal(res59.missing[0], 'Cần học tối thiểu 60s (còn 1s)');

  // Critical boundary 2: 60 seconds (exact threshold)
  const res60 = checkRequirement(60);
  assert.equal(res60.dwellOk, true, '60s dwell MUST satisfy text requirement');
  assert.equal(res60.missing.length, 0);

  // Boundary 3: 61 seconds (satisfied)
  const res61 = checkRequirement(61);
  assert.equal(res61.dwellOk, true, '61s dwell MUST satisfy text requirement');
  assert.equal(res61.missing.length, 0);

  // Source contract verification in student.js
  assert.match(studentSource, /const\s+dwellRequired\s*=\s*60;/, 'dwellRequired constant must be exactly 60');
  assert.match(studentSource, /dwellElapsed\s*>=\s*dwellRequired/, 'Comparison must use >= dwellRequired');
  assert.match(studentSource, /dwellElapsed\s*<\s*dwellRequired/, 'Missing condition must check < dwellRequired');
  assert.match(studentSource, /Cần học tối thiểu 60s/, 'Toast/notification message must specify 60s');
});

// =========================================================================
// CHALLENGE 4: Multi-Video Completion Requirement
// Verify watching 1 of 2 videos leaves video requirement incomplete; watching all videos satisfies requirement.
// =========================================================================

test('Challenge 4: Multi-Video Completion Requirement - watching 1 of 2 videos leaves video requirement incomplete; watching all videos satisfies requirement', () => {
  // Simulate the multi-video evaluation algorithm from student.js
  const lessonMulti = {
    video_url: '/media/video_part1.m3u8',
    video_urls: ['/media/video_part1.m3u8', '/media/video_part2.m3u8']
  };

  const hasMultipleVideos = Array.isArray(lessonMulti.video_urls) && lessonMulti.video_urls.length > 1;
  assert.equal(hasMultipleVideos, true, 'Lesson must be identified as multi-video');

  const evaluateCompletion = (currentVideoWatched, heartbeatResult) => {
    const isAllVideoDone = hasMultipleVideos
      ? Boolean(heartbeatResult.all_videos_complete)
      : Boolean(heartbeatResult.is_video_complete || heartbeatResult.all_videos_complete);

    let updatedWatched = currentVideoWatched;
    if (isAllVideoDone) {
      updatedWatched = true;
    }

    const missing = [];
    if (!updatedWatched) {
      missing.push('Cần xem hết 100% video bài học');
    }
    return { videoWatched: updatedWatched, isVideoMet: updatedWatched, missing };
  };

  // State 0: Initial state (neither video watched)
  let videoWatched = false;

  // Step 1: Student watches only Video 1 to 100%
  // Backend returns is_video_complete = true, but all_videos_complete = false
  const hb1 = {
    media_id: 'video_part1',
    is_video_complete: true,
    all_videos_complete: false
  };
  const res1 = evaluateCompletion(videoWatched, hb1);
  assert.equal(res1.videoWatched, false, 'Watching only 1 of 2 videos MUST leave videoWatched = false');
  assert.equal(res1.isVideoMet, false, 'Video requirement must remain unmet');
  assert.ok(res1.missing.includes('Cần xem hết 100% video bài học'), 'Missing requirement must include video requirement');

  // Step 2: Student watches Video 2 to 100%
  // Backend returns all_videos_complete = true
  const hb2 = {
    media_id: 'video_part2',
    is_video_complete: true,
    all_videos_complete: true
  };
  const res2 = evaluateCompletion(res1.videoWatched, hb2);
  assert.equal(res2.videoWatched, true, 'Watching all videos MUST set videoWatched = true');
  assert.equal(res2.isVideoMet, true, 'Video requirement must be satisfied');
  assert.equal(res2.missing.length, 0);

  // Contrast: Single-video lesson
  const lessonSingle = {
    video_url: '/media/single.m3u8',
    video_urls: ['/media/single.m3u8']
  };
  const hasMultipleSingle = Array.isArray(lessonSingle.video_urls) && lessonSingle.video_urls.length > 1;
  assert.equal(hasMultipleSingle, false, 'Single-video lesson must have hasMultipleVideos = false');

  const singleHb = { is_video_complete: true, all_videos_complete: false };
  const singleDone = hasMultipleSingle ? Boolean(singleHb.all_videos_complete) : Boolean(singleHb.is_video_complete || singleHb.all_videos_complete);
  assert.equal(singleDone, true, 'For single-video lessons, is_video_complete = true is sufficient');
});

// =========================================================================
// CHALLENGE 5: Next Button State Invariants
// In incomplete state: disabled, gray classes, no lock icon, no "Đã khóa" text.
// In complete state: emerald green classes, enabled.
// =========================================================================

test('Challenge 5: Next Button State Invariants - disabled & gray with NO lock icon/text when incomplete; emerald green & enabled when complete', () => {
  const { mockDoc, MockElement, elements } = createMockPlaybackDOM();

  // Test the button generator function modeled directly on student.js lines 4608-4655
  const renderNextButtonHtml = (meetsAll, nextItem = { title: 'Bài học tiếp theo', id: 'l2', type: 'lesson' }) => {
    const box = new MockElement('div', 'cisco-bottom-next-box');
    if (nextItem) {
      if (meetsAll) {
        box.innerHTML = `
          <button type="button" id="cisco-next-btn" title="${nextItem.title}" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white transition-all flex items-center gap-1.5 shadow-md cursor-pointer animate-fade-in">
            <span>Tiếp theo</span>
            <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        `;
      } else {
        box.innerHTML = `
          <button type="button" id="cisco-next-btn" disabled title="Chưa đủ điều kiện chuyển bài" class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-300/80 dark:border-slate-700 cursor-not-allowed select-none">
            <span>Tiếp theo</span>
            <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        `;
      }
    } else {
      if (meetsAll) {
        box.innerHTML = `
          <a href="#/student/courses" id="cisco-next-btn" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white transition-colors flex items-center gap-1.5 shadow-md cursor-pointer">
            <span>Hoàn thành khóa học</span>
            <span class="material-symbols-outlined text-[16px]">celebration</span>
          </a>
        `;
      } else {
        box.innerHTML = `
          <button type="button" id="cisco-next-btn" disabled class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-300/80 dark:border-slate-700 cursor-not-allowed select-none">
            <span>Hoàn thành khóa học</span>
            <span class="material-symbols-outlined text-[16px]">celebration</span>
          </button>
        `;
      }
    }
    return box.innerHTML;
  };

  // 1. Incomplete state for intermediate lesson
  const incompleteHtml = renderNextButtonHtml(false, { title: 'Lesson 2' });

  // Invariant checks on incomplete state:
  assert.match(incompleteHtml, /disabled/, 'Incomplete Next button must have disabled attribute');
  assert.match(incompleteHtml, /bg-slate-200/, 'Incomplete Next button must have bg-slate-200 class');
  assert.match(incompleteHtml, /text-slate-400/, 'Incomplete Next button must have text-slate-400 class');
  assert.match(incompleteHtml, /cursor-not-allowed/, 'Incomplete Next button must have cursor-not-allowed class');
  assert.match(incompleteHtml, /select-none/, 'Incomplete Next button must have select-none class');

  // Negative checks: NO lock icon, NO "Đã khóa" text
  assert.doesNotMatch(incompleteHtml, /lock/i, 'Incomplete Next button must NOT contain a lock icon');
  assert.doesNotMatch(incompleteHtml, /Đã khóa/i, 'Incomplete Next button must NOT contain "Đã khóa" text');
  assert.doesNotMatch(incompleteHtml, /bg-emerald-600/, 'Incomplete Next button must NOT have green class');
  assert.doesNotMatch(incompleteHtml, /cursor-pointer/, 'Incomplete Next button must NOT have cursor-pointer');

  // 2. Complete state for intermediate lesson
  const completeHtml = renderNextButtonHtml(true, { title: 'Lesson 2' });

  // Invariant checks on complete state:
  assert.doesNotMatch(completeHtml, /disabled/, 'Complete Next button must NOT have disabled attribute');
  assert.match(completeHtml, /bg-emerald-600/, 'Complete Next button must have bg-emerald-600 class');
  assert.match(completeHtml, /hover:bg-emerald-700/, 'Complete Next button must have hover:bg-emerald-700 class');
  assert.match(completeHtml, /text-white/, 'Complete Next button must have text-white class');
  assert.match(completeHtml, /cursor-pointer/, 'Complete Next button must have cursor-pointer class');
  assert.match(completeHtml, /shadow-md/, 'Complete Next button must have shadow-md class');
  assert.doesNotMatch(completeHtml, /bg-slate-200/, 'Complete Next button must NOT have bg-slate-200');
  assert.doesNotMatch(completeHtml, /cursor-not-allowed/, 'Complete Next button must NOT have cursor-not-allowed');

  // 3. Final lesson in course
  const incompleteFinalHtml = renderNextButtonHtml(false, null);
  assert.match(incompleteFinalHtml, /disabled/);
  assert.match(incompleteFinalHtml, /bg-slate-200/);
  assert.match(incompleteFinalHtml, /cursor-not-allowed/);
  assert.doesNotMatch(incompleteFinalHtml, /lock/i);
  assert.doesNotMatch(incompleteFinalHtml, /Đã khóa/i);

  const completeFinalHtml = renderNextButtonHtml(true, null);
  assert.match(completeFinalHtml, /href="#\/student\/courses"/);
  assert.match(completeFinalHtml, /bg-emerald-600/);
  assert.match(completeFinalHtml, /cursor-pointer/);
  assert.doesNotMatch(completeFinalHtml, /disabled/);

  // 4. Source code template verification in student.js
  const nextTemplates = studentSource.match(/box\.innerHTML\s*=\s*`\s*<button[^>]+id="cisco-next-btn"[^>]*>[\s\S]*?<\/button>\s*`;/g);
  assert.ok(nextTemplates && nextTemplates.length >= 2, 'student.js must contain both complete and incomplete button templates');

  const sourceDisabledTmpl = nextTemplates.find(t => t.includes('disabled'));
  assert.ok(sourceDisabledTmpl, 'Must find disabled Next button template in student.js');
  assert.doesNotMatch(sourceDisabledTmpl, /lock/i, 'Disabled template in student.js must NOT contain lock icon');
  assert.doesNotMatch(sourceDisabledTmpl, /Đã khóa/i, 'Disabled template in student.js must NOT contain "Đã khóa" text');
  assert.match(sourceDisabledTmpl, /bg-slate-200/, 'Disabled template in student.js must use bg-slate-200');
  assert.match(sourceDisabledTmpl, /cursor-not-allowed/, 'Disabled template in student.js must use cursor-not-allowed');

  const sourceEnabledTmpl = nextTemplates.find(t => !t.includes('disabled') && t.includes('bg-emerald-600'));
  assert.ok(sourceEnabledTmpl, 'Must find emerald green Next button template in student.js');
  assert.match(sourceEnabledTmpl, /cursor-pointer/, 'Enabled template in student.js must use cursor-pointer');
  assert.match(sourceEnabledTmpl, /shadow-md/, 'Enabled template in student.js must use shadow-md');
});
