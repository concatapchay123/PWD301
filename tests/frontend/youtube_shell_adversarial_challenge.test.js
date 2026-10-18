const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

function createMockEnvironment() {
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
      this.className = '';
      this.classList = {
        add: (...classes) => { for (const c of classes) { if (!this.className.includes(c)) this.className += ' ' + c; } },
        remove: (...classes) => { for (const c of classes) { this.className = this.className.replace(c, '').trim(); } },
        toggle: (c, force) => {
          const has = this.className.includes(c);
          if (force === true || (force === undefined && !has)) this.classList.add(c);
          else if (force === false || (force === undefined && has)) this.classList.remove(c);
        },
        contains: (c) => this.className.includes(c)
      };
      if (id) elements.set(id, this);
    }
    setAttribute(k, v) { this.attributes.set(k, String(v)); }
    getAttribute(k) { return this.attributes.get(k) || null; }
    removeAttribute(k) { this.attributes.delete(k); }
    appendChild(child) {
      child.parentElement = this;
      this.children.push(child);
      if (child.id) elements.set(child.id, child);
      return child;
    }
    addEventListener(type, fn) {
      const key = `${this.id}:${type}`;
      if (!listeners.has(key)) listeners.set(key, []);
      listeners.get(key).push(fn);
    }
    dispatchEvent(event) {
      const key = `${this.id}:${event.type}`;
      const fns = listeners.get(key) || [];
      for (const fn of fns) fn(event);
    }
    click() {
      this.dispatchEvent({ type: 'click', target: this, preventDefault: () => {} });
    }
    querySelector(selector) {
      if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
      return null;
    }
  }

  const mockDocument = {
    getElementById: (id) => elements.get(id) || null,
    createElement: (tag) => new MockElement(tag),
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  const timerIds = new Set();
  const mockWindow = {
    document: mockDocument,
    location: { hash: '#/student/courses/c1/lessons/l1' },
    app: { currentUser: { id: 101, student_code: 'SV101', email: 'stu@example.com' } },
    setInterval: (fn, ms) => { const id = setInterval(fn, ms); timerIds.add(id); return id; },
    clearInterval: (id) => { timerIds.delete(id); clearInterval(id); },
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    clearTimeout: (id) => clearTimeout(id)
  };

  const context = vm.createContext({
    window: mockWindow,
    document: mockDocument,
    global: mockWindow,
    setInterval: mockWindow.setInterval,
    clearInterval: mockWindow.clearInterval,
    setTimeout: mockWindow.setTimeout,
    clearTimeout: mockWindow.clearTimeout,
    UI: {
      parseYouTubeId: (url) => {
        const m = String(url).match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/))([\w-]{11})/);
        return m ? m[1] : null;
      },
      escapeHtml: (s) => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
    },
    ApiClient: {
      startLessonPlayback: async () => ({ session_id: 'sess-1', next_sequence: 1, frontier_seconds: 0 }),
      recordPlaybackHeartbeat: async () => ({ status: 'ACTIVE', frontier_seconds: 10 })
    },
    console
  });

  const studentJsCode = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');
  vm.runInNewContext(studentJsCode, context);

  return { StudentView: context.window.StudentView, mockDocument, MockElement, elements, listeners };
}

test('Challenge 2.1: YouTube HTML shell structural invariants and pointer-events protection', () => {
  const { StudentView } = createMockEnvironment();
  const html = StudentView._getEmbedVideoHtml('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'yt-test-player');

  // 1. Player container markers
  assert.match(html, /id="yt-test-player-container"/, 'Player container must exist');
  assert.match(html, /data-custom-player="true"/, 'Must flag custom player');
  assert.match(html, /data-player-type="youtube"/, 'Must identify as youtube player');
  assert.match(html, /data-yt-id="dQw4w9WgXcQ"/, 'Must extract correct YouTube video ID');

  // 2. Viewport container
  assert.match(html, /id="yt-test-player-viewport"/, 'Viewport element must exist');
  assert.match(html, /class="[^"]*aspect-video[^"]*overflow-hidden[^"]*"/, 'Viewport must have aspect-video and overflow-hidden');

  // 3. Iframe host scaling & pointer-events isolation
  assert.match(html, /pointer-events-none/, 'Wrapper must have pointer-events-none class');
  assert.match(html, /pointer-events:\s*none;?/, 'Wrapper must have pointer-events: none inline style');
  assert.match(html, /inset:\s*0/, 'Wrapper must have standard inset: 0 for 16:9 uncropped viewport');
  assert.match(html, /width:\s*100%/, 'Wrapper must have width 100%');
  assert.match(html, /height:\s*100%/, 'Wrapper must have height 100%');
  assert.doesNotMatch(html, /top:\s*-22%/, 'Wrapper must eliminate -22% top crop');

  // 4. Transparent Click Shield Overlay
  assert.match(html, /id="yt-test-player-shield"/, 'Transparent click shield overlay must exist');
  assert.match(html, /z-index:\s*10/, 'Shield must have z-index 10 above iframe wrapper');
  assert.match(html, /cursor:\s*pointer/, 'Shield must show pointer cursor for user interaction');
  assert.match(html, /inset:\s*0|top:\s*0/, 'Shield must cover entire viewport area');

  // 4b. Poster/Backdrop Shield (z-index 15, bg-slate-950)
  assert.match(html, /id="yt-test-player-poster-shield"/, 'Poster backdrop shield must exist');
  assert.match(html, /z-index:\s*15/, 'Poster shield must have z-index 15 above iframe wrapper and below big play');
  assert.match(html, /bg-slate-950/, 'Poster shield must have dark background');

  // 5. Big Play Button
  assert.match(html, /id="yt-test-player-big-play"/, 'Big play button must exist');
  assert.match(html, /aria-label="Phát video"/, 'Big play button must have accessible label');

  // 6. Custom controls isolated from YouTube iframe
  assert.match(html, /id="yt-test-player-controls"/, 'Custom controls container must exist');
  assert.match(html, /aria-label="Âm lượng"/, 'Volume control must have accessible label');
});

test('Challenge 2.2: Transparent shield intercepts click events and controls driver play/pause', async () => {
  const { StudentView, MockElement, elements } = createMockEnvironment();

  const container = new MockElement('div', 'yt-chal-container');
  container.setAttribute('data-custom-player', 'true');
  container.setAttribute('data-player-type', 'youtube');
  container.setAttribute('data-yt-id', 'dQw4w9WgXcQ');

  const viewport = new MockElement('div', 'yt-chal-viewport');
  const ytHost = new MockElement('div', 'yt-chal-yt');
  const shield = new MockElement('div', 'yt-chal-shield');
  const bigPlay = new MockElement('button', 'yt-chal-big-play');
  const playBtn = new MockElement('button', 'yt-chal-play-btn');
  const statusEl = new MockElement('p', 'yt-chal-status');
  const progressTrack = new MockElement('div', 'yt-chal-progress-track');
  const bufferedBar = new MockElement('div', 'yt-chal-buffered-bar');
  const watchedBar = new MockElement('div', 'yt-chal-watched-bar');
  const playedBar = new MockElement('div', 'yt-chal-played-bar');
  const timeEl = new MockElement('span', 'yt-chal-time');
  const speedBtn = new MockElement('button', 'yt-chal-speed-btn');
  const lockIndicator = new MockElement('span', 'yt-chal-lock-indicator');
  const volumeSlider = new MockElement('input', 'yt-chal-volume');
  const muteBtn = new MockElement('button', 'yt-chal-mute-btn');
  const fullscreenBtn = new MockElement('button', 'yt-chal-fullscreen-btn');
  const retryBtn = new MockElement('button', 'yt-chal-retry');
  const progressRetry = new MockElement('button', 'yt-chal-progress-retry');

  viewport.appendChild(ytHost);
  viewport.appendChild(shield);
  viewport.appendChild(bigPlay);
  container.appendChild(viewport);
  container.appendChild(playBtn);
  container.appendChild(statusEl);
  container.appendChild(progressTrack);
  container.appendChild(bufferedBar);
  container.appendChild(watchedBar);
  container.appendChild(playedBar);
  container.appendChild(timeEl);
  container.appendChild(speedBtn);
  container.appendChild(lockIndicator);
  container.appendChild(volumeSlider);
  container.appendChild(muteBtn);
  container.appendChild(fullscreenBtn);
  container.appendChild(retryBtn);
  container.appendChild(progressRetry);

  let playCalled = 0;
  let pauseCalled = 0;
  let currentState = 2; // PAUSED

  const mockDriver = {
    getPlayerState: () => currentState,
    playVideo: () => {
      playCalled++;
      currentState = 1; // PLAYING
    },
    pauseVideo: () => {
      pauseCalled++;
      currentState = 2; // PAUSED
    },
    getCurrentTime: () => 15,
    getDuration: () => 120,
    getVideoLoadedFraction: () => 0.5,
    seekTo: () => {},
    isMuted: () => false,
    mute: () => {},
    unMute: () => {},
    setVolume: () => {},
    setPlaybackRate: () => {}
  };

  // Mock global YT.Player
  global.YT = {
    Player: function(id, config) {
      setTimeout(() => {
        if (config.events && config.events.onReady) {
          config.events.onReady({ target: mockDriver });
        }
      }, 0);
      return mockDriver;
    },
    PlayerState: {
      PLAYING: 1,
      PAUSED: 2,
      ENDED: 0,
      BUFFERING: 3,
      CUED: 5
    }
  };

  const handle = StudentView.setupCustomVideoPlayer('yt-chal', {
    youtube: true,
    lessonId: 'l1',
    courseId: 'c1'
  });

  // Give event loop a tick to initialize driver
  await new Promise(r => setTimeout(r, 20));

  // 1. Click on shield while paused: must trigger play
  shield.click();
  assert.equal(playCalled, 1, 'Clicking shield while paused must trigger driver.playVideo()');

  // 2. Click on shield while playing: must trigger pause
  shield.click();
  assert.equal(pauseCalled, 1, 'Clicking shield while playing must trigger driver.pauseVideo()');

  // 3. Click on big play button: must trigger play
  bigPlay.click();
  assert.equal(playCalled, 2, 'Clicking big play button must trigger driver.playVideo()');

  // 4. Click on control bar play button: must trigger pause
  playBtn.click();
  assert.equal(pauseCalled, 2, 'Clicking play button must trigger driver.pauseVideo()');

  if (handle && handle.dispose) handle.dispose();
});

test('Challenge 2.3: Crop geometry analysis across responsive viewports eliminates header & footer', () => {
  // Test matrix of representative viewports:
  const testViewports = [
    { name: '1080p FHD', width: 1920, height: 1080 },
    { name: '720p HD', width: 1280, height: 720 },
    { name: '480p SD', width: 854, height: 480 },
    { name: '360p Mobile Land', width: 640, height: 360 },
    { name: 'Mobile Port 390x844 (aspect-video: 390x219.375)', width: 390, height: 390 * 9 / 16 },
    { name: 'Tablet 4:3 1024x768 (aspect-video: 1024x576)', width: 1024, height: 1024 * 9 / 16 },
    { name: '4K UHD', width: 3840, height: 2160 }
  ];

  // YouTube UI dimensions (standard desktop and mobile web player):
  // Header bar (title, channel icon, share button): typically 48px to 60px height.
  // Footer logo watermark: typically 32px to 40px height.
  const MAX_YT_HEADER_HEIGHT = 60;
  const MAX_YT_FOOTER_HEIGHT = 40;

  for (const vp of testViewports) {
    const H = vp.height;
    // top = -14%, height = 128%
    const topCroppedPixels = 0.14 * H;
    const bottomCroppedPixels = (1.28 - 1.00 - 0.14) * H; // exactly 0.14 * H

    assert.ok(
      topCroppedPixels >= 30,
      `[${vp.name}] Top crop (${topCroppedPixels.toFixed(1)}px) must be substantial enough to eliminate YouTube header`
    );
    assert.ok(
      bottomCroppedPixels >= 30,
      `[${vp.name}] Bottom crop (${bottomCroppedPixels.toFixed(1)}px) must be substantial enough to eliminate YouTube bottom logo`
    );

    if (H >= 360) {
      assert.ok(
        topCroppedPixels >= 50,
        `[${vp.name}] Top crop (${topCroppedPixels.toFixed(1)}px) exceeds typical 50px header`
      );
      assert.ok(
        bottomCroppedPixels >= 50,
        `[${vp.name}] Bottom crop (${bottomCroppedPixels.toFixed(1)}px) exceeds typical 40px footer`
      );
    }
  }
});

test('Challenge 2.4: Poster shield behavior, pending play queueing, and secure YT.Player configuration', async () => {
  const { StudentView, MockElement } = createMockEnvironment();

  const container = new MockElement('div', 'p-container');
  container.setAttribute('data-custom-player', 'true');
  container.setAttribute('data-player-type', 'youtube');
  container.setAttribute('data-yt-id', 'test1234567');

  const viewport = new MockElement('div', 'p-viewport');
  const ytHost = new MockElement('div', 'p-yt');
  const shield = new MockElement('div', 'p-shield');
  const posterShield = new MockElement('div', 'p-poster-shield');
  const bigPlay = new MockElement('button', 'p-big-play');
  const playBtn = new MockElement('button', 'p-play-btn');
  const statusEl = new MockElement('p', 'p-status');

  viewport.appendChild(ytHost);
  viewport.appendChild(shield);
  viewport.appendChild(posterShield);
  viewport.appendChild(bigPlay);
  container.appendChild(viewport);
  container.appendChild(playBtn);
  container.appendChild(statusEl);

  let playCalled = 0;
  let pauseCalled = 0;
  let playerConfig = null;
  let onStateChangeFn = null;
  let onReadyFn = null;

  const mockDriver = {
    getPlayerState: () => 2,
    playVideo: () => { playCalled++; },
    pauseVideo: () => { pauseCalled++; },
    getCurrentTime: () => 0,
    getDuration: () => 100,
    getVideoLoadedFraction: () => 0,
    seekTo: () => {},
    isMuted: () => false,
    mute: () => {},
    unMute: () => {},
    setVolume: () => {},
    setPlaybackRate: () => {}
  };

  // Mock global YT.Player that captures config
  global.YT = {
    Player: function(id, config) {
      playerConfig = config;
      onStateChangeFn = config.events?.onStateChange;
      onReadyFn = config.events?.onReady;
      return mockDriver;
    }
  };

  // 1. Click big play BEFORE onReady fires -> should queue pending play
  const handle = StudentView.setupCustomVideoPlayer('p', { youtube: true });
  assert.equal(playCalled, 0, 'playVideo should not be called before YT is ready');

  bigPlay.click();
  assert.equal(playCalled, 0, 'Clicking before ready queues pending play without crashing');

  // Allow event loop tick for async ensureYouTubeAPI and new YT.Player instantiation
  await new Promise(r => setTimeout(r, 20));

  // Trigger onReady -> queued play should now be executed
  onReadyFn?.();
  assert.equal(playCalled, 1, 'Pending play action executed immediately upon onReady');

  // Verify secure YT.Player configuration
  assert.equal(playerConfig.host, 'https://www.youtube-nocookie.com', 'Must use youtube-nocookie.com host');
  assert.equal(playerConfig.playerVars?.origin, undefined, 'Origin parameter must be omitted to prevent Error 153');
  assert.equal(playerConfig.playerVars?.modestbranding, 1, 'Must include modestbranding: 1');
  assert.equal(playerConfig.playerVars?.iv_load_policy, 3, 'Must include iv_load_policy: 3');
  assert.equal(playerConfig.playerVars?.disablekb, 1, 'Must include disablekb: 1');
  assert.equal(playerConfig.playerVars?.fs, 0, 'Must include fs: 0');

  // 2. Trigger onStateChange with 1 (PLAYING) -> poster shield must be hidden
  onStateChangeFn?.({ data: 1 });
  assert.ok(posterShield.classList.contains('opacity-0'), 'Poster shield must have opacity-0 when playing');
  assert.ok(posterShield.classList.contains('pointer-events-none'), 'Poster shield must have pointer-events-none when playing');

  // 3. Trigger onStateChange with 2 (PAUSED) -> poster shield must NOT be shown again
  onStateChangeFn?.({ data: 2 });
  assert.ok(posterShield.classList.contains('opacity-0'), 'Poster shield must remain hidden with opacity-0 when paused');

  if (handle && handle.dispose) handle.dispose();
});

test('Challenge 2.5: Course Hero Trailer embeds Clean Player Shell v3 with autoplay muted loop and Zero-Button Ambient Invariant', () => {
  const fs = require('node:fs');
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // 1. Initial Hero Box Autoplay Muted & Loop inside Clean Player Shell v3
  assert.match(studentSource, /id="hero-trailer-clean-shell"/, 'Must contain #hero-trailer-clean-shell in initial render');
  assert.match(studentSource, /inset:\s*0;\s*width:\s*100%;\s*height:\s*100%/, 'Hero trailer must have standard 16:9 uncropped viewport style');
  assert.doesNotMatch(studentSource, /top:\s*-22%/, 'Hero trailer must eliminate -22% top crop');
  assert.match(studentSource, /https:\/\/www\.youtube-nocookie\.com\/embed\/\$\{ytHeroId\}\?autoplay=1&mute=1&loop=1/, 'Hero trailer embed URL must enforce autoplay, mute, and loop');

  // 2. Zero-Button Ambient Hero Trailer Invariant
  assert.doesNotMatch(studentSource, /id="btn-trailer-toggle-mute"/, 'Must eliminate #btn-trailer-toggle-mute button');
  assert.doesNotMatch(studentSource, /id="btn-hero-video-expand"/, 'Must eliminate #btn-hero-video-expand button');
  assert.doesNotMatch(studentSource, /id="btn-play-hero-trailer"/, 'Must eliminate #btn-play-hero-trailer button');
  assert.doesNotMatch(studentSource, /openTrailerLightbox/, 'Must eliminate openTrailerLightbox modal logic');
});

test('Challenge 2.6: Teacher Reviewer Course Preview renders Clean Player Shell v3 without native YouTube UI', () => {
  const fs = require('node:fs');
  const adminSource = fs.readFileSync('frontend/assets/js/views/admin.js', 'utf8');

  // 1. Helper _getCleanYouTubeShellHtml
  assert.match(adminSource, /_getCleanYouTubeShellHtml\(id,/, 'AdminView must contain _getCleanYouTubeShellHtml');
  assert.match(adminSource, /inset:\s*0;\s*width:\s*100%;\s*height:\s*100%/, 'Reviewer shell must use standard 16:9 uncropped style');
  assert.doesNotMatch(adminSource, /top:\s*-22%/, 'Reviewer shell must not crop top by -22%');
  assert.match(adminSource, /id="\$\{playerId\}-poster-shield"/, 'Reviewer shell must contain poster-shield');
  assert.match(adminSource, /id="\$\{playerId\}-shield"/, 'Reviewer shell must contain click-shield');
  assert.match(adminSource, /id="\$\{playerId\}-big-play"/, 'Reviewer shell must contain big-play');
  assert.match(adminSource, /id="\$\{playerId\}-controls"/, 'Reviewer shell must contain custom controls');

  // 2. Controller setupReviewerVideoPlayer
  assert.match(adminSource, /setupReviewerVideoPlayer\(playerId\)/, 'AdminView must contain setupReviewerVideoPlayer');
  assert.match(adminSource, /AdminView\.setupReviewerVideoPlayer\(`reviewer-player-\${index}-\${yIdx}`\)/, 'renderLesson must initialize setupReviewerVideoPlayer');
});

