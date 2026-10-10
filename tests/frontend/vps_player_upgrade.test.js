const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');
function load(overrides = {}) {
  const window = { location: { origin: 'https://pwd.test' } };
  const ctx = { window, URL, console, setTimeout, clearTimeout, setInterval, clearInterval, UI: { parseYouTubeId: () => 'abcdefghijk', escapeHtml: s => s, showToast() {} }, ...overrides };
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/student.js', 'utf8'), ctx);
  return { view: window.StudentView, window, ctx };
}
test('YouTube shell leaves iframe unobscured and places controls outside video aspect box', () => {
  const { view } = load();
  const html = view._getEmbedVideoHtml('https://youtu.be/abcdefghijk', 'p');
  assert.doesNotMatch(html, /-shield|scale-105|pointer-events-none[^>]*>\s*<div id="p-yt"/);
  assert.match(html, /aria-label="Âm lượng"/);
});
test('shared YouTube loader rejects on timeout and permits a later retry', async () => {
  const scripts = new Map(); let timeout;
  const document = { getElementById: id => scripts.get(id), createElement: () => ({ remove() { scripts.delete(this.id); } }), head: { appendChild(el) { scripts.set(el.id, el); } } };
  const { view, window } = load({ document, setTimeout: fn => { timeout = fn; return 1; }, clearTimeout() {} });
  assert.equal(typeof view.ensureYouTubeAPI, 'function');
  const first = view.ensureYouTubeAPI();
  assert.equal(view.ensureYouTubeAPI(), first);
  timeout();
  await assert.rejects(first, /YouTube/);
  const next = view.ensureYouTubeAPI();
  window.YT = { Player: class {} };
  window.onYouTubeIframeAPIReady();
  assert.equal(await next, window.YT);
});
test('playback session preserves exact failed heartbeat for retry and ignores updates after destroy', async () => {
  const calls = []; let fail = true; let started;
  const ApiClient = { startLessonPlayback: async () => ({ session_id: 's', next_sequence: 1, frontier: 12, duration: 60 }), recordPlaybackHeartbeat: async (_, body) => { calls.push(JSON.parse(JSON.stringify(body))); if (fail) { fail = false; throw Error('offline'); } return { next_sequence: body.sequence + 1, frontier: 22 }; } };
  const { view } = load({ ApiClient, document: { visibilityState: 'visible', addEventListener() {}, removeEventListener() {} } });
  assert.equal(typeof view.createPlaybackTracker, 'function');
  const tracker = view.createPlaybackTracker('l', 'youtube:abcdefghijk', { onConfirmed: value => { started = value; } });
  await tracker.ready;
  tracker.update('playing', 12, 1);
  await tracker.flush();
  tracker.update('playing', 22, 1);
  await tracker.flush();
  assert.deepEqual(calls[0], calls[1]);
  assert.equal(started.frontier, 22);
  tracker.destroy();
});
const uiSource = fs.readFileSync('frontend/assets/js/ui.js', 'utf8');
test('YouTube parser rejects lookalike hosts while accepting watch shorts and live', () => {
  const window = {}; vm.runInNewContext(uiSource, { window, URL });
  assert.equal(window.UI.parseYouTubeId('https://evil.test/youtube.com/watch?v=abcdefghijk'), null);
  assert.equal(window.UI.parseYouTubeId('https://youtube.com.evil.test/watch?v=abcdefghijk'), null);
  for (const url of ['https://youtu.be/abcdefghijk', 'https://www.youtube.com/watch?v=abcdefghijk', 'https://youtube.com/shorts/abcdefghijk', 'https://youtube.com/live/abcdefghijk']) assert.equal(window.UI.parseYouTubeId(url), 'abcdefghijk');
  assert.doesNotMatch(window.UI.getYouTubeEmbedUrl('abcdefghijk'), /modestbranding/);
});
test('API sends canonical playback contracts and download ticket without fetching the file', async () => {
  const window = {}; const requests = [];
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, document: { querySelector: () => null } });
  window.ApiClient.request = async (url, options) => { requests.push({ url, options }); return { url: 'https://b2.test/object' }; };
  assert.equal(typeof window.ApiClient.startLessonPlayback, 'function');
  await window.ApiClient.startLessonPlayback('l', 'youtube:abcdefghijk');
  await window.ApiClient.recordPlaybackHeartbeat('l', { sequence: 1 });
  await window.ApiClient.getFileDownloadTicket('a');
  assert.equal(requests[0].url, '/student/lessons/l/playback-sessions');
  assert.equal(requests[0].options.body.media_id, 'youtube:abcdefghijk');
  assert.equal(requests[2].url, '/api/files/a/download-ticket');
});
function fakePlayerDOM(type = 'youtube') {
  const elements = new Map(), events = new Map();
  const element = (id, attrs = {}) => {
    const el = { id, style: {}, textContent: '', tagName: 'DIV', isConnected: true, classList: { add() {}, remove() {} }, getAttribute: name => attrs[name] || '', querySelector: () => null,
      addEventListener(name, fn) { events.set(`${id}:${name}`, fn); }, removeEventListener(name) { events.delete(`${id}:${name}`); } };
    elements.set(id, el); return el;
  };
  element('p-container', { 'data-player-type': type, 'data-yt-id': 'abcdefghijk' });
  for (const id of ['p-yt', 'p-play-btn', 'p-speed-btn', 'p-volume', 'p-status', 'p-retry', 'p-time', 'p-lock-indicator']) element(id);
  const document = { visibilityState: 'visible', getElementById: id => elements.get(id), addEventListener(name, fn) { events.set(`doc:${name}`, fn); }, removeEventListener(name) { events.delete(`doc:${name}`); } };
  return { document, elements, events };
}
test('disposing while YouTube loader is pending prevents late player creation', async () => {
  const dom = fakePlayerDOM(); const { view } = load(dom);
  let resolve, creations = 0;
  view.ensureYouTubeAPI = () => new Promise(r => { resolve = r; });
  const ctrl = view.setupCustomVideoPlayer('p'); ctrl.destroy();
  resolve({ Player: class { constructor() { creations++; } } });
  await Promise.resolve();
  assert.equal(creations, 0);
  assert.equal(dom.events.size, 0);
  assert.equal(dom.elements.get('p-play-btn').onclick, null);
});
test('YouTube requests only supported speed and displays rate confirmed by driver', async t => {
  const dom = fakePlayerDOM(); const { view } = load(dom);
  let callbacks, requested, actualRate = 1;
  const driver = { getPlaybackRate: () => actualRate, getAvailablePlaybackRates: () => [1, 1.5], setPlaybackRate: rate => { requested = rate; }, getCurrentTime: () => 0, getDuration: () => 60, destroy() {} };
  view.ensureYouTubeAPI = async () => ({ Player: class { constructor(_, config) { callbacks = config.events; return driver; } } });
  const ctrl = view.setupCustomVideoPlayer('p', { preview: true }); t.after(() => ctrl.destroy());
  await new Promise(resolve => setImmediate(resolve)); callbacks.onReady();
  dom.elements.get('p-speed-btn').onclick({ stopPropagation() {} });
  try {
  assert.equal(requested, 1.5);
  assert.equal(dom.elements.get('p-speed-btn').textContent, '1x');
  actualRate = 1.5; callbacks.onPlaybackRateChange();
  assert.equal(dom.elements.get('p-speed-btn').textContent, '1.5x');
  callbacks.onStateChange({ data: 0 });
  assert.notEqual(dom.elements.get('p-lock-indicator').textContent, 'Đã mở khóa tua');
  } finally { ctrl.destroy(); }
});
test('pausing during an in-flight heartbeat queues the terminal paused state', async t => {
  let complete; const calls = [];
  const ApiClient = { startLessonPlayback: async () => ({ session_id: 's', next_sequence: 1 }), recordPlaybackHeartbeat: async (_, body) => { calls.push({ ...body }); if (calls.length === 1) return new Promise(resolve => { complete = resolve; }); return { next_sequence: 3 }; } };
  const { view } = load({ ApiClient, document: { addEventListener() {}, removeEventListener() {}, visibilityState: 'visible' } });
  const tracker = view.createPlaybackTracker('l', 'youtube:abcdefghijk');
  t.after(() => tracker.destroy());
  await tracker.ready; tracker.update('playing', 0, 1); const first = tracker.flush();
  await new Promise(resolve => setImmediate(resolve)); tracker.update('paused', 5, 1); tracker.flush();
  complete({ next_sequence: 2 }); await first; await new Promise(resolve => setImmediate(resolve));
  try {
  assert.equal(calls.length, 2);
  assert.equal(calls[1].state, 'paused'); assert.equal(calls[1].sequence, 2);
  } finally { tracker.destroy(); }
});
test('tracker releases its timer and stops when its lesson leaves the page', async t => {
  let tick, cleared = false, alive = true; const calls = [];
  const { view } = load({ setInterval: fn => { tick = fn; return 8; }, clearInterval: id => { cleared = id === 8; }, document: { addEventListener() {}, removeEventListener() {}, visibilityState: 'visible' }, ApiClient: { startLessonPlayback: async () => ({ session_id: 's', next_sequence: 1 }), recordPlaybackHeartbeat: async (_, body) => { calls.push(body); return { next_sequence: 2 }; } } });
  const tracker = view.createPlaybackTracker('l', 'content:l', { isAlive: () => alive }); t.after(() => tracker.destroy());
  await tracker.ready; tracker.update('playing', 0, 1); alive = false; tick();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(cleared, true); assert.equal(calls[0].state, 'paused');
});
test('YouTube detects a forward jump and seeks back to the confirmed frontier', async t => {
  const dom = fakePlayerDOM(); let tick, callbacks, current = 0, time = 0, target;
  class Clock extends Date { static now() { return time; } }
  const { view } = load({ ...dom, Date: Clock, setInterval: fn => { tick = fn; return 1; }, clearInterval() {} });
  const driver = { getCurrentTime: () => current, getDuration: () => 60, getPlaybackRate: () => 1, seekTo: value => { target = value; current = value; }, destroy() {} };
  view.ensureYouTubeAPI = async () => ({ Player: class { constructor(_, config) { callbacks = config.events; return driver; } } });
  const ctrl = view.setupCustomVideoPlayer('p', { preview: true }); t.after(() => ctrl.destroy());
  await new Promise(resolve => setImmediate(resolve)); callbacks.onReady(); callbacks.onStateChange({ data: 1 });
  time = 250; current = 30; tick();
  assert.equal(target, 0);
});
test('both player shells provide an explicit progress retry action', () => {
  const { view } = load({ UI: { parseYouTubeId: url => url.includes('youtu') ? 'abcdefghijk' : null, escapeHtml: s => s } });
  for (const url of ['https://youtu.be/abcdefghijk', '/course/lesson/video/playlist.m3u8']) {
    assert.match(view._getEmbedVideoHtml(url, 'p'), /id="p-progress-retry"[^>]*>Thử Lưu Tiến Độ/);
  }
});
test('native player reports load failure and disposes event handlers', t => {
  const dom = fakePlayerDOM('native');
  const video = { tagName: 'VIDEO', src: '/lesson/video/playlist.m3u8', currentTime: 0, playbackRate: 1, paused: true, style: {}, getAttribute: () => '', canPlayType: () => 'probably', pause() {}, addEventListener(name, fn) { dom.events.set(`video:${name}`, fn); }, removeEventListener(name) { dom.events.delete(`video:${name}`); } };
  dom.elements.set('p', video);
  const { view } = load(dom); const ctrl = view.setupCustomVideoPlayer('p', { preview: true }); t.after(() => ctrl.destroy());
  dom.events.get('video:error')();
  assert.match(dom.elements.get('p-status').textContent, /Không thể tải video/);
  ctrl.destroy(); assert.equal(dom.events.size, 0);
});
test('ended video flush uses a backend-supported paused terminal state', async t => {
  const dom = fakePlayerDOM(); let callbacks; const calls = [];
  const ApiClient = { startLessonPlayback: async () => ({ session_id: 's', next_sequence: 1, duration: 100, frontier: 0 }), recordPlaybackHeartbeat: async (_, body) => { calls.push({ ...body }); return { next_sequence: body.sequence + 1, frontier: 0, duration: 100 }; } };
  const { view } = load({ ...dom, ApiClient });
  view.ensureYouTubeAPI = async () => ({ Player: class { constructor(_, config) { callbacks = config.events; return { getCurrentTime: () => 100, getDuration: () => 100, getPlaybackRate: () => 1, destroy() {} }; } } });
  const ctrl = view.setupCustomVideoPlayer('p', { lessonId: 'l' }); t.after(() => ctrl.destroy());
  await new Promise(resolve => setImmediate(resolve)); callbacks.onReady(); await new Promise(resolve => setImmediate(resolve));
  callbacks.onStateChange({ data: 0 }); await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls.at(-1).state, 'paused');
});
test('server seek_required reconciles an already resumed player', async t => {
  const dom = fakePlayerDOM(); let callbacks, seek;
  const { view } = load(dom);
  view.ensureYouTubeAPI = async () => ({ Player: class { constructor(_, config) { callbacks = config.events; return { getCurrentTime: () => 30, getDuration: () => 100, getPlaybackRate: () => 1, seekTo: value => { seek = value; }, destroy() {} }; } } });
  const ctrl = view.setupCustomVideoPlayer('p', { preview: true }); t.after(() => ctrl.destroy());
  await new Promise(resolve => setImmediate(resolve)); callbacks.onReady();
  ctrl.applyConfirmed({ frontier: 20, duration: 100 });
  ctrl.applyConfirmed({ frontier: 10, duration: 100, seek_required: true });
  assert.equal(seek, 10);
});
test('confirmed playback rate change flushes old motion before resetting the new rate interval', async t => {
  const dom = fakePlayerDOM(); let callbacks, rate = 1, position = 0; const calls = [];
  const ApiClient = { startLessonPlayback: async () => ({ session_id: 's', next_sequence: 1, duration: 100, frontier: 0 }), recordPlaybackHeartbeat: async (_, body) => { calls.push({ ...body }); return { next_sequence: body.sequence + 1, frontier: body.position_seconds, duration: 100 }; } };
  const { view } = load({ ...dom, ApiClient });
  const driver = { getCurrentTime: () => position, getDuration: () => 100, getPlaybackRate: () => rate, pauseVideo: () => callbacks.onStateChange({ data: 2 }), playVideo: () => callbacks.onStateChange({ data: 1 }), seekTo: value => { position = value; }, destroy() {} };
  view.ensureYouTubeAPI = async () => ({ Player: class { constructor(_, config) { callbacks = config.events; return driver; } } });
  const ctrl = view.setupCustomVideoPlayer('p', { lessonId: 'l' }); t.after(() => ctrl.destroy());
  await new Promise(resolve => setImmediate(resolve)); callbacks.onReady(); await new Promise(resolve => setImmediate(resolve));
  callbacks.onStateChange({ data: 1 }); await new Promise(resolve => setImmediate(resolve));
  position = 10; rate = 2; callbacks.onPlaybackRateChange(); await new Promise(resolve => setImmediate(resolve));
  assert.ok(calls.some(call => call.state === 'playing' && call.position_seconds === 10 && call.playback_rate === 1));
  assert.ok(calls.some(call => call.state === 'paused' && call.playback_rate === 2));
  assert.equal(calls.at(-1).state, 'playing'); assert.equal(calls.at(-1).playback_rate, 2);
});
