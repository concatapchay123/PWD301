const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const studentSource = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8');

function loadStudentView(overrides = {}) {
  const window = {
    location: { origin: 'https://pwd.test', hash: '' },
    app: { currentUser: { id: 1, name: 'Student 1', role: 'STUDENT' } }
  };
  const ctx = {
    window,
    URL,
    console,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    UI: {
      parseYouTubeId: url => {
        if (!url) return null;
        const m = String(url).match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/|live\/))([a-zA-Z0-9_\-]{11})/);
        return m ? m[1] : null;
      },
      escapeHtml: s => String(s ?? ''),
      showToast() {}
    },
    document: {
      visibilityState: 'visible',
      getElementById: () => null,
      createElement: () => ({ remove() {}, appendChild() {} }),
      addEventListener() {},
      removeEventListener() {}
    },
    ...overrides
  };
  vm.runInNewContext(studentSource, ctx);
  return { view: ctx.window.StudentView, window: ctx.window, ctx };
}

function fakePlayerDOM(type = 'youtube') {
  const elements = new Map();
  const events = new Map();
  const element = (id, attrs = {}) => {
    const el = {
      id,
      style: {},
      textContent: '',
      tagName: 'DIV',
      isConnected: true,
      classList: {
        _classes: new Set(),
        add(c) { this._classes.add(c); },
        remove(c) { this._classes.delete(c); },
        contains(c) { return this._classes.has(c); },
        toggle(c, force) { if (force !== undefined) { if (force) this.add(c); else this.remove(c); } else { if (this.contains(c)) this.remove(c); else this.add(c); } }
      },
      getAttribute: name => attrs[name] || '',
      setAttribute(name, val) { attrs[name] = String(val); },
      removeAttribute(name) { delete attrs[name]; },
      querySelector: () => null,
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 500, height: 10 }),
      addEventListener(name, fn) { events.set(`${id}:${name}`, fn); },
      removeEventListener(name) { events.delete(`${id}:${name}`); }
    };
    elements.set(id, el);
    return el;
  };

  element('p-container', { 'data-player-type': type, 'data-yt-id': 'abcdefghijk' });
  for (const id of [
    'p-yt', 'p-play-btn', 'p-big-play', 'p-speed-btn', 'p-volume', 'p-status', 'p-retry',
    'p-time', 'p-lock-indicator', 'p-progress-track', 'p-buffered-bar', 'p-watched-bar',
    'p-played-bar', 'p-shield', 'p-mute-btn', 'p-fullscreen-btn', 'p-progress-retry'
  ]) {
    element(id);
  }

  const document = {
    visibilityState: 'visible',
    fullscreenElement: null,
    getElementById: id => elements.get(id),
    addEventListener(name, fn) { events.set(`doc:${name}`, fn); },
    removeEventListener(name) { events.delete(`doc:${name}`); }
  };
  return { document, elements, events };
}

// =========================================================================
// OBJECTIVE 1: Challenge Supplementary Video URL Normalization in student.js
// =========================================================================

test('CHALLENGE 1.1: Empty and falsy video_urls handling in normalization', () => {
  const snippetStart = studentSource.indexOf('// Security Invariant: Students get 403 Forbidden from /api/files/<assetId>/stream. Resolve to HLS.');
  const snippetEnd = studentSource.indexOf('lesson.video_url = activeVideoUrl;', snippetStart) + 'lesson.video_url = activeVideoUrl;'.length;
  const code = studentSource.slice(snippetStart, snippetEnd);

  // Case 1: video_urls is empty array
  {
    const lesson = { video_urls: [], video_url: null };
    const course = { public_id: 'c1' };
    const expectedLessonId = 'l1';
    let activeVideoUrl = null;
    const isPreview = false;
    const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };
    vm.runInNewContext(code, ctx);
    assert.deepEqual(ctx.lesson.video_urls, []);
    assert.equal(ctx.lesson.video_url, null);
  }

  // Case 2: video_urls is null or undefined
  {
    const lesson = { video_urls: null, video_url: null };
    const course = { public_id: 'c1' };
    const expectedLessonId = 'l1';
    let activeVideoUrl = null;
    const isPreview = false;
    const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };
    assert.doesNotThrow(() => vm.runInNewContext(code, ctx));
    assert.equal(ctx.lesson.video_urls, null);
  }

  // Case 3: video_urls has empty strings and falsy values
  {
    const lesson = { video_urls: ['', null, undefined, false, 0], video_url: '' };
    const course = { public_id: 'c1' };
    const expectedLessonId = 'l1';
    let activeVideoUrl = '';
    const isPreview = false;
    const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };
    assert.doesNotThrow(() => vm.runInNewContext(code, ctx));
    assert.deepEqual(ctx.lesson.video_urls, ['', null, undefined, false, 0]);
  }
});

test('CHALLENGE 1.2: Invalid and malformed URLs in video_urls normalization', () => {
  const snippetStart = studentSource.indexOf('// Security Invariant: Students get 403 Forbidden from /api/files/<assetId>/stream. Resolve to HLS.');
  const snippetEnd = studentSource.indexOf('lesson.video_url = activeVideoUrl;', snippetStart) + 'lesson.video_url = activeVideoUrl;'.length;
  const code = studentSource.slice(snippetStart, snippetEnd);

  const testUrls = [
    '/api/files//stream',                  // missing assetId
    '/api/files/not-a-valid-stream',        // missing /stream suffix
    '/api/files/uuid-1234/something_else',  // wrong suffix
    'https://example.com/api/files/',       // no assetId
    '/api/files/special%20char#1/stream',   // special chars in asset ID
    null,                                   // null item
    12345                                   // non-string
  ];

  const lesson = { video_urls: [...testUrls], video_url: null };
  const course = { public_id: 'course-uuid-99' };
  const expectedLessonId = 'lesson-uuid-88';
  let activeVideoUrl = null;
  const isPreview = false;
  const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };

  assert.doesNotThrow(() => vm.runInNewContext(code, ctx));

  assert.equal(ctx.lesson.video_urls[0], '/api/files//stream');
  assert.equal(ctx.lesson.video_urls[1], '/api/files/not-a-valid-stream');
  assert.equal(ctx.lesson.video_urls[2], '/api/files/uuid-1234/something_else');
  assert.equal(
    ctx.lesson.video_urls[4],
    `/student/courses/course-uuid-99/lessons/lesson-uuid-88/video/${encodeURIComponent('special%20char#1')}/playlist.m3u8`
  );
  assert.equal(ctx.lesson.video_urls[5], null);
  assert.equal(ctx.lesson.video_urls[6], 12345);
});

test('CHALLENGE 1.3: Mixed URL normalization (YouTube, HLS, raw files, external)', () => {
  const snippetStart = studentSource.indexOf('// Security Invariant: Students get 403 Forbidden from /api/files/<assetId>/stream. Resolve to HLS.');
  const snippetEnd = studentSource.indexOf('lesson.video_url = activeVideoUrl;', snippetStart) + 'lesson.video_url = activeVideoUrl;'.length;
  const code = studentSource.slice(snippetStart, snippetEnd);

  const mixedUrls = [
    'https://youtu.be/abcdefghijk',
    '/api/files/asset-uuid-1/stream',
    '/student/courses/c1/lessons/l1/video/asset-uuid-2/playlist.m3u8',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
  ];

  const lesson = {
    video_urls: [...mixedUrls],
    video_url: '/api/files/asset-uuid-primary/stream'
  };
  const course = { public_id: 'course-alpha' };
  const expectedLessonId = 'lesson-beta';
  let activeVideoUrl = lesson.video_url;
  const isPreview = false;
  const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };

  vm.runInNewContext(code, ctx);

  assert.equal(
    ctx.lesson.video_url,
    '/student/courses/course-alpha/lessons/lesson-beta/video/asset-uuid-primary/playlist.m3u8'
  );
  assert.equal(ctx.lesson.video_urls[0], 'https://youtu.be/abcdefghijk');
  assert.equal(
    ctx.lesson.video_urls[1],
    '/student/courses/course-alpha/lessons/lesson-beta/video/asset-uuid-1/playlist.m3u8'
  );
  assert.equal(
    ctx.lesson.video_urls[2],
    '/student/courses/c1/lessons/l1/video/asset-uuid-2/playlist.m3u8'
  );
  assert.equal(
    ctx.lesson.video_urls[3],
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
  );
});

test('CHALLENGE 1.4: Single-lesson preview mode isolation (isPreview === true)', () => {
  const snippetStart = studentSource.indexOf('// Security Invariant: Students get 403 Forbidden from /api/files/<assetId>/stream. Resolve to HLS.');
  const snippetEnd = studentSource.indexOf('lesson.video_url = activeVideoUrl;', snippetStart) + 'lesson.video_url = activeVideoUrl;'.length;
  const code = studentSource.slice(snippetStart, snippetEnd);

  const lesson = {
    video_urls: ['/api/files/asset-uuid-supp/stream'],
    video_url: '/api/files/asset-uuid-main/stream'
  };
  const course = { public_id: 'course-preview' };
  const expectedLessonId = 'lesson-preview';
  let activeVideoUrl = lesson.video_url;
  const isPreview = true;
  const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };

  vm.runInNewContext(code, ctx);

  // In preview mode, raw file streams MUST NOT be converted to /student/courses/.../playlist.m3u8
  assert.equal(ctx.lesson.video_url, '/api/files/asset-uuid-main/stream');
  assert.equal(ctx.lesson.video_urls[0], '/api/files/asset-uuid-supp/stream');
});

test('CHALLENGE 1.5: Missing course or lesson identifiers degrades safely', () => {
  const snippetStart = studentSource.indexOf('// Security Invariant: Students get 403 Forbidden from /api/files/<assetId>/stream. Resolve to HLS.');
  const snippetEnd = studentSource.indexOf('lesson.video_url = activeVideoUrl;', snippetStart) + 'lesson.video_url = activeVideoUrl;'.length;
  const code = studentSource.slice(snippetStart, snippetEnd);

  const lesson = {
    video_urls: ['/api/files/asset-uuid-1/stream'],
    video_url: '/api/files/asset-uuid-main/stream'
  };
  const course = null;
  const expectedLessonId = null;
  let activeVideoUrl = lesson.video_url;
  const isPreview = false;
  const ctx = { lesson, course, expectedLessonId, activeVideoUrl, isPreview };

  assert.doesNotThrow(() => vm.runInNewContext(code, ctx));
  assert.equal(ctx.lesson.video_url, '/api/files/asset-uuid-main/stream');
  assert.equal(ctx.lesson.video_urls[0], '/api/files/asset-uuid-1/stream');
});

// =========================================================================
// OBJECTIVE 2: Challenge Silent Scrub Pacing & Heartbeat Packet Retry Logic
// =========================================================================

test('CHALLENGE 2.1: Seeking beyond frontier is strictly prevented during active learning', async t => {
  const dom = fakePlayerDOM('youtube');
  let currentPos = 10;
  let seekTarget = null;
  const driver = {
    getCurrentTime: () => currentPos,
    getDuration: () => 100,
    getPlaybackRate: () => 1,
    seekTo: val => { seekTarget = val; currentPos = val; },
    destroy() {}
  };

  let callbacks;
  const { view } = loadStudentView({
    ...dom,
    ApiClient: {
      startLessonPlayback: async () => ({ session_id: 's-test', next_sequence: 1, duration: 100, frontier: 30 })
    }
  });

  view.ensureYouTubeAPI = async () => ({
    Player: class {
      constructor(_, config) {
        callbacks = config.events;
        return driver;
      }
    }
  });

  const ctrl = view.setupCustomVideoPlayer('p', {
    lessonId: 'l-test',
    isCompleted: false
  });
  t.after(() => ctrl.destroy());

  await new Promise(resolve => setImmediate(resolve));
  callbacks.onReady();

  // Set confirmed frontier to 30s
  ctrl.applyConfirmed({ frontier: 30, duration: 100 });

  // 1. Progress track click at 80% (targets 80s, but frontier is 30s)
  const progressTrack = dom.elements.get('p-progress-track');
  progressTrack.onclick({ clientX: 400, stopPropagation() {} }); // 400/500 = 80% of 100s = 80s
  assert.equal(seekTarget, 30, 'Forward seek beyond frontier (80s) must be clamped to frontier (30s)');

  // 2. Backward seek to 15s (within frontier) should succeed
  progressTrack.onclick({ clientX: 75, stopPropagation() {} }); // 75/500 = 15% of 100s = 15s
  assert.equal(seekTarget, 15, 'Backward seek to 15s must be allowed');

  // 3. ArrowRight keyboard navigation (+5s from current 15s -> 20s) should succeed
  currentPos = 15;
  const keydownFn = dom.events.get('p-container:keydown');
  keydownFn({ key: 'ArrowRight', preventDefault() {} });
  assert.equal(seekTarget, 20, 'Seek forward within frontier (20s) must be allowed');

  // 4. ArrowRight keyboard navigation from 28s (+5s -> 33s) must be clamped to 30s
  currentPos = 28;
  keydownFn({ key: 'ArrowRight', preventDefault() {} });
  assert.equal(seekTarget, 30, 'Seek forward beyond frontier (33s) must be clamped to frontier (30s)');

  // 5. ArrowLeft keyboard navigation to negative time must be clamped to 0s
  currentPos = 2;
  keydownFn({ key: 'ArrowLeft', preventDefault() {} });
  assert.equal(seekTarget, 0, 'Seek backward below 0 must be clamped to 0s');
});

test('CHALLENGE 2.2: Free seeking is permitted once course/lesson is completed', async t => {
  const dom = fakePlayerDOM('youtube');
  let currentPos = 10;
  let seekTarget = null;
  const driver = {
    getCurrentTime: () => currentPos,
    getDuration: () => 100,
    getPlaybackRate: () => 1,
    seekTo: val => { seekTarget = val; currentPos = val; },
    destroy() {}
  };

  let callbacks;
  const { view } = loadStudentView({
    ...dom,
    ApiClient: {
      startLessonPlayback: async () => ({ session_id: 's-test', next_sequence: 1, duration: 100, frontier: 100 })
    }
  });

  view.ensureYouTubeAPI = async () => ({
    Player: class {
      constructor(_, config) {
        callbacks = config.events;
        return driver;
      }
    }
  });

  const ctrl = view.setupCustomVideoPlayer('p', {
    lessonId: 'l-test',
    isCompleted: true
  });
  t.after(() => ctrl.destroy());

  await new Promise(resolve => setImmediate(resolve));
  callbacks.onReady();

  // Confirm completion and set duration to 100s
  ctrl.applyConfirmed({ frontier: 100, duration: 100, is_completed: true });

  // Progress track click at 85% (85s) - must be allowed because lesson is completed
  const progressTrack = dom.elements.get('p-progress-track');
  progressTrack.onclick({ clientX: 425, stopPropagation() {} }); // 425/500 = 85s
  assert.equal(seekTarget, 85, 'Seek to 85s must be permitted on completed lesson');
});

test('CHALLENGE 2.3: Heartbeat packet retry logic upon consecutive network failures', async t => {
  const calls = [];
  let failCount = 2; // Fail twice, then succeed
  let latestConfirmed = null;

  const ApiClient = {
    startLessonPlayback: async () => ({
      session_id: 'session-persist-1',
      next_sequence: 1,
      frontier: 5,
      duration: 60
    }),
    recordPlaybackHeartbeat: async (lessonId, body) => {
      calls.push(JSON.parse(JSON.stringify(body)));
      if (failCount > 0) {
        failCount--;
        const netErr = new Error('Network timeout / 503 Service Unavailable');
        netErr.status = 503;
        throw netErr;
      }
      return {
        session_id: body.playback_session_id,
        next_sequence: body.sequence + 1,
        frontier: 25,
        duration: 60
      };
    }
  };

  const { view } = loadStudentView({
    ApiClient,
    document: {
      visibilityState: 'visible',
      addEventListener() {},
      removeEventListener() {}
    }
  });

  const tracker = view.createPlaybackTracker('l-persist', 'media-1', {
    onConfirmed: val => { latestConfirmed = val; },
    onError: () => {}
  });
  t.after(() => tracker.destroy());

  await tracker.ready;
  // Clear confirmed result from startLessonPlayback initial call
  latestConfirmed = null;

  // 1. First heartbeat attempt -> fails (failCount becomes 1)
  tracker.update('playing', 10, 1);
  await tracker.flush();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].sequence, 1);
  assert.equal(calls[0].position_seconds, 10);
  assert.equal(latestConfirmed, null, 'Should not confirm upon failure');

  // 2. Second heartbeat attempt -> fails (failCount becomes 0)
  // Even if update was called with a new position, the preserved pending packet must be re-sent
  tracker.update('playing', 15, 1);
  await tracker.flush();
  assert.equal(calls.length, 2);
  assert.equal(calls[1].sequence, 1, 'Retry packet must preserve sequence 1');
  assert.equal(calls[1].position_seconds, 10, 'Retry packet must preserve original captured position');
  assert.equal(latestConfirmed, null);

  // 3. Third heartbeat attempt -> succeeds!
  await tracker.flush();
  assert.equal(calls.length, 3);
  assert.equal(calls[2].sequence, 1, 'Third attempt still retries sequence 1');
  assert.equal(latestConfirmed.next_sequence, 2, 'Confirmed result after success should have next_sequence 2');
  assert.equal(latestConfirmed.frontier, 25);

  // 4. Fourth heartbeat -> now sends sequence 2 with updated position
  tracker.update('playing', 30, 1);
  await tracker.flush();
  assert.equal(calls.length, 4);
  assert.equal(calls[3].sequence, 2, 'Subsequent heartbeat must advance to sequence 2');
  assert.equal(calls[3].position_seconds, 30);
});

test('CHALLENGE 2.4: Heartbeat session resync on HTTP 400 sequence/session mismatch', async t => {
  const calls = [];
  let syncCount = 0;

  const ApiClient = {
    startLessonPlayback: async () => {
      syncCount++;
      return {
        session_id: `session-new-${syncCount}`,
        next_sequence: 1,
        frontier: 0,
        duration: 100
      };
    },
    recordPlaybackHeartbeat: async (lessonId, body) => {
      calls.push(JSON.parse(JSON.stringify(body)));
      if (body.sequence === 1 && syncCount === 1) {
        const err = new Error('Sequence mismatch: expected sequence 5');
        err.status = 400;
        err.code = 'VALIDATION_ERROR';
        throw err;
      }
      return {
        session_id: body.playback_session_id,
        next_sequence: body.sequence + 1,
        frontier: 10
      };
    }
  };

  const { view } = loadStudentView({
    ApiClient,
    document: {
      visibilityState: 'visible',
      addEventListener() {},
      removeEventListener() {}
    }
  });

  const tracker = view.createPlaybackTracker('l-sync', 'media-sync');
  t.after(() => tracker.destroy());

  await tracker.ready;
  assert.equal(syncCount, 1);

  // Send heartbeat -> server throws 400 sequence mismatch
  tracker.update('playing', 10, 1);
  await tracker.flush();

  await new Promise(resolve => setTimeout(resolve, 50));

  assert.equal(syncCount, 2, 'Playback session must automatically resync upon 400 sequence mismatch');

  tracker.update('playing', 12, 1);
  await tracker.flush();
  assert.equal(calls.at(-1).playback_session_id, 'session-new-2');
  assert.equal(calls.at(-1).sequence, 1);
});

test('CHALLENGE 2.5 (VERIFIED RESOLVED): Clean UI shell invariants and speed-btn DOM structure restored', () => {
  const { view } = loadStudentView({
    UI: {
      parseYouTubeId: url => String(url || '').includes('youtu') ? 'abcdefghijk' : null,
      escapeHtml: s => s
    }
  });

  const ytHtml = view._getEmbedVideoHtml('https://youtu.be/abcdefghijk', 'player-yt', false);
  const hlsHtml = view._getEmbedVideoHtml('/student/courses/c/lessons/l/video/a/playlist.m3u8', 'player-hls', false);

  // Lock indicator must be hidden in both
  assert.match(ytHtml, /id="player-yt-lock-indicator"[^>]*class="hidden"/);
  assert.match(hlsHtml, /id="player-hls-lock-indicator"[^>]*class="hidden"/);

  // Status alert must be hidden in both
  assert.match(ytHtml, /id="player-yt-status"[^>]*class="hidden/);
  assert.match(hlsHtml, /id="player-hls-status"[^>]*class="hidden/);

  // No visible lock text in progress track title in both
  assert.doesNotMatch(ytHtml, /title="[^"]*Khóa tua nhanh/i);
  assert.doesNotMatch(hlsHtml, /title="[^"]*Khóa tua nhanh/i);

  // BUG 1 RESOLUTION VERIFICATION:
  // In BOTH YouTube and Native HLS shells, speed-btn must be properly closed with </button>,
  // progress-retry button must be restored with class="hidden", and lock-indicator/fullscreen-btn
  // must not be engulfed inside speed-btn.
  assert.match(
    ytHtml,
    /<button[^>]*id="player-yt-speed-btn"[^>]*>\s*1\.0x\s*<\/button>/,
    'YouTube player shell speed-btn must be cleanly closed'
  );
  assert.match(
    hlsHtml,
    /<button[^>]*id="player-hls-speed-btn"[^>]*>\s*1\.0x\s*<\/button>/,
    'Native HLS player shell speed-btn must be cleanly closed'
  );
  assert.match(
    ytHtml,
    /<button[^>]*id="player-yt-progress-retry"[^>]*class="[^"]*hidden[^"]*"[^>]*>Thử Lưu Tiến Độ<\/button>/,
    'YouTube player shell must include hidden progress-retry button for backward test compatibility'
  );
  assert.match(
    hlsHtml,
    /<button[^>]*id="player-hls-progress-retry"[^>]*class="[^"]*hidden[^"]*"[^>]*>Thử Lưu Tiến Độ<\/button>/,
    'Native HLS player shell must include hidden progress-retry button for backward test compatibility'
  );
});

test('CHALLENGE 1.6 (VERIFIED RESOLVED): setupCustomVideoPlayer preserves preview isolation when options.preview is true', async t => {
  const dom = fakePlayerDOM('native');
  const attrs = {};
  const video = {
    id: 'p',
    tagName: 'VIDEO',
    src: '/api/files/asset-preview-id/stream',
    currentTime: 0,
    playbackRate: 1,
    duration: 60,
    readyState: 1,
    paused: true,
    style: {},
    classList: { add() {}, remove() {} },
    getAttribute: attr => attrs[attr] || '',
    setAttribute: (attr, val) => { attrs[attr] = val; },
    removeAttribute: attr => { delete attrs[attr]; },
    canPlayType: () => 'probably',
    pause() {},
    load() {},
    addEventListener(name, fn) { dom.events.set(`video:${name}`, fn); },
    removeEventListener(name) { dom.events.delete(`video:${name}`); }
  };
  dom.elements.set('p', video);

  const { view } = loadStudentView({
    ...dom,
    window: {
      location: {
        origin: 'https://pwd.test',
        hash: '#student/courses?id=course-preview-uuid&preview=1'
      }
    }
  });

  // 1. Preview mode (preview: true) -> MUST NOT rewrite to student HLS route
  const ctrlPreview = view.setupCustomVideoPlayer('p', {
    streamUrl: '/api/files/asset-preview-id/stream',
    lessonId: 'lesson-preview-id',
    preview: true // PREVIEW MODE
  });
  t.after(() => ctrlPreview?.destroy());

  const previewHlsSrc = video.getAttribute('data-hls-src');
  assert.equal(
    previewHlsSrc,
    '',
    'Preview mode must NOT set student HLS route on data-hls-src'
  );
  assert.equal(
    video.src,
    '/api/files/asset-preview-id/stream',
    'Preview mode must preserve original direct stream URL on video.src'
  );

  // 2. Non-preview student mode -> MUST rewrite to student HLS route
  const studentAttrs = {};
  const studentVideo = {
    ...video,
    id: 'p-student',
    getAttribute: attr => studentAttrs[attr] || '',
    setAttribute: (attr, val) => { studentAttrs[attr] = val; },
    removeAttribute: attr => { delete studentAttrs[attr]; }
  };
  dom.elements.set('p-student', studentVideo);
  dom.elements.set('p-student-container', {
    getAttribute: name => name === 'data-player-type' ? 'native' : '',
    classList: { add() {}, remove() {}, contains: () => false },
    addEventListener() {},
    removeEventListener() {}
  });

  const ctrlStudent = view.setupCustomVideoPlayer('p-student', {
    streamUrl: '/api/files/asset-student-id/stream',
    courseId: 'course-student-uuid',
    lessonId: 'lesson-student-id',
    preview: false
  });
  t.after(() => ctrlStudent?.destroy());

  const studentHlsSrc = studentVideo.getAttribute('data-hls-src');
  assert.equal(
    studentHlsSrc,
    '/student/courses/course-student-uuid/lessons/lesson-student-id/video/asset-student-id/playlist.m3u8',
    'Non-preview student mode must correctly resolve /api/files/ to student HLS playlist.m3u8'
  );
});
