const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function load(file, overrides = {}) {
  const window = {};
  const context = { window, console: { warn() {}, error() {}, info() {} }, ...overrides };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js', file), 'utf8'), context);
  return context;
}

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test('settings preferences save reads retained inputs after router moves the page', async () => {
  const button = {};
  const inputs = {
    '#pref-email-course': { checked: false },
    '#pref-email-assessment': { checked: true },
    '#pref-email-grade': { checked: false },
    '#pref-email-marketing': { checked: true },
    '#btn-save-preferences': button,
  };
  let moved = false;
  let submitted;
  const container = { innerHTML: '', querySelector: selector => moved ? null : inputs[selector] || null, querySelectorAll: () => [] };
  const ctx = load('views/student.js', {
    document: { getElementById: () => null, querySelector: () => null },
    UI: { escapeHtml: value => String(value || ''), showToast() {} },
    ApiClient: { getProfile: async () => ({ profile: { id: 'a' } }), getPreferences: async () => ({}), updatePreferences: async value => { submitted = value; } },
  });
  await ctx.window.StudentView.renderSettings(container);
  moved = true;
  await button.onclick();
  assert.deepEqual(JSON.parse(JSON.stringify(submitted)), {
    email_course: false, email_assessment: true, email_grade: false, email_marketing: true,
  });
});

test('attempt departure retries failed answers and blocks unconfirmed data loss', async () => {
  const ctx = load('views/student.js', { UI: { confirm: async () => false } });
  const failed = new Set(['question']);
  const payloads = new Map([['question', { answer_text: 'Unacknowledged' }]]);
  let retries = 0;
  const allowed = await ctx.window.StudentView.prepareAttemptDeparture(
    async () => {}, new Set(), failed, payloads,
    async () => { retries++; throw new Error('offline'); }
  );
  assert.equal(retries, 1);
  assert.equal(allowed, false);
});

test('departure drains saves queued while the initial request is pending', async () => {
  const ctx = load('views/student.js', { UI: { confirm: async () => false } });
  const first = deferred();
  const second = deferred();
  const pending = new Set([first.promise]);
  let finished = false;
  const leaving = ctx.window.StudentView.prepareAttemptDeparture(
    async () => {}, pending, new Set(), new Map(), async () => {}
  ).then(result => { finished = true; return result; });
  await Promise.resolve();
  await Promise.resolve();
  pending.add(second.promise);
  first.promise.then(() => pending.delete(first.promise));
  second.promise.then(() => pending.delete(second.promise));
  first.resolve();
  await new Promise(done => setImmediate(done));
  assert.equal(finished, false);
  second.resolve();
  assert.equal(await leaving, true);
});

test('router waits for attempt departure before replacing content', async () => {
  const flight = deferred();
  const ctx = load('router.js', {
    document: { getElementById: () => null },
    UI: {},
  });
  ctx.window.location = { hash: '#/student/dashboard' };
  ctx.window.history = { replaceState() {} };
  const router = Object.create(ctx.window.AppRouter.prototype);
  router.beforeRouteLeave = { routeHash: '#/student/assessments/attempt?id=a', leave: () => flight.promise };
  let rendered = false;
  router.renderRoute = async () => { rendered = true; };
  const pending = router.handleRoute();
  await Promise.resolve();
  assert.equal(rendered, false);
  flight.resolve(true);
  await pending;
  assert.equal(rendered, true);
});

test('settings displays authoritative avatar instead of an older local choice', async () => {
  const container = { innerHTML: '', querySelector: () => null, querySelectorAll: () => [] };
  const ctx = load('views/student.js', {
    document: { getElementById: () => null, querySelector: () => null },
    UI: { escapeHtml: value => String(value || ''), showToast() {} },
    ApiClient: { getProfile: async () => ({ profile: { id: 'a', avatar_url: 'https://example.com/server.svg' } }), getPreferences: async () => ({}) },
  });
  ctx.window.StudentView.getStoredRandomAvatarUrl = () => 'https://example.com/local.svg';
  await ctx.window.StudentView.renderSettings(container);
  assert.match(container.innerHTML, /https:\/\/example.com\/server.svg/);
  assert.doesNotMatch(container.innerHTML, /https:\/\/example.com\/local.svg/);
});

test('catalog enrollment failure cannot render false unenrolled actions', async () => {
  const grid = { innerHTML: '', querySelectorAll: () => [] };
  const ctx = load('views/student.js', {
    document: { getElementById: id => id === 'catalog-courses-grid' ? grid : null },
    UI: { escapeHtml: value => String(value || '') },
    ApiClient: { getCatalogCourses: async () => ({ items: [{ id: 'c', title: 'Course' }] }), getStudentEnrollments: async () => { throw new Error('Enrollment unavailable'); }, getRecommendations: async () => [] },
  });
  await ctx.window.StudentView.renderCatalog({ innerHTML: '' });
  assert.match(grid.innerHTML, /Enrollment unavailable/);
  assert.doesNotMatch(grid.innerHTML, /enroll-action-btn/);
});

function routerHarness(method) {
  const flight = deferred();
  const saved = [];
  const ctx = load('router.js', {
    document: { getElementById: () => null },
    UI: { showToast() {} },
    ApiClient: { [method]: () => flight.promise },
  });
  const router = Object.create(ctx.window.AppRouter.prototype);
  Object.assign(router, {
    currentUser: { id: 'owner-A' }, currentRole: 'INSTRUCTOR',
    notificationsCache: { items: [{ id: 'notice-A', is_read: false, read: false }], unread_count: 1 },
    saveCachedNotifications() { saved.push({ owner: this.currentUser.id, items: JSON.parse(JSON.stringify(this.notificationsCache.items)) }); },
    updateBadgeFromCache() {}, renderNotificationsDropdownContent() {},
  });
  return { router, flight, saved };
}

for (const change of ['owner', 'role', 'logout', 'generation']) {
  test(`notification read failure cannot degrade a newer ${change} scope`, async () => {
    const h = routerHarness('getNotifications');
    const pending = h.router.fetchNotifications(false);
    if (change === 'owner') h.router.currentUser = { id: 'owner-B' };
    if (change === 'role') h.router.currentRole = 'STUDENT';
    if (change === 'logout') h.router.currentUser = null;
    if (change === 'generation') h.router._notifFetchGen++;
    h.router.notificationFetchState = { status: 'ready', last_attempt: 42 };
    h.flight.reject(new Error('Old read failure'));
    await pending;
    assert.equal(h.router.notificationFetchState.status, 'ready');
    assert.equal(h.router.notificationFetchState.last_attempt, 42);
  });
}

test('notification read started before user identity hydration cannot apply after logout', async () => {
  const h = routerHarness('getNotifications');
  h.router.currentUser = {};
  const pending = h.router.fetchNotifications(false);
  h.router.currentUser = null;
  h.router.notificationFetchState = { status: 'ready' };
  h.flight.reject(new Error('Old incomplete-identity failure'));
  await pending;
  assert.equal(h.router.notificationFetchState.status, 'ready');
});

for (const [handler, api, args] of [
  ['handleDeleteNotification', 'deleteNotification', ['notice-A']],
  ['handleMarkAllRead', 'markAllNotificationsRead', []],
]) {
  test(`${handler}: failed old-owner mutation cannot overwrite new-owner cache`, async () => {
    const h = routerHarness(api);
    const pending = h.router[handler](...args);
    h.router.currentUser = { id: 'owner-B' };
    h.router.currentRole = 'STUDENT';
    h.router.notificationsCache = { items: [{ id: 'notice-B', is_read: false }], unread_count: 1 };
    h.flight.reject(new Error('network failure'));
    await pending;
    assert.deepEqual(h.router.notificationsCache.items.map(item => item.id), ['notice-B']);
    assert.equal(h.saved.some(snapshot => snapshot.owner === 'owner-B' && snapshot.items.some(item => item.id === 'notice-A')), false);
  });

  test(`${handler}: visible cache changes only after acknowledgement`, async () => {
    const h = routerHarness(api);
    const pending = h.router[handler](...args);
    assert.equal(h.router.notificationsCache.items.length, 1);
    assert.equal(h.router.notificationsCache.unread_count, 1);
    h.flight.resolve({ success: true });
    await pending;
    assert.equal(h.router.notificationsCache.unread_count, 0);
  });
}

test('lesson block roundtrip preserves interleaved order and text boundaries', () => {
  const { window } = load('views/instructor.js');
  const view = window.InstructorView;
  const blocks = [
    { id: 'video-1', type: 'video', url: 'https://youtu.be/abcdefghijk', videoType: 'YOUTUBE', files: [] },
    { id: 'text-1', type: 'text', content: 'First paragraph' },
    { id: 'doc-1', type: 'document', files: [{ resource_id: 'r-1', asset_id: 'a-1', filename: 'notes.pdf' }] },
    { id: 'text-2', type: 'text', content: 'Second paragraph <!-- comment -->' },
  ];
  const payload = view.serializeBlocksToPayload(blocks, { title: 'Lesson' });
  const restored = view.parseLessonToBlocks({ ...payload, resources: [{ resource_id: 'r-1', asset_id: 'a-1', filename: 'notes.pdf', mime_type: 'application/pdf' }] });
  assert.deepEqual(Array.from(restored, block => block.type), ['video', 'text', 'document', 'text']);
  assert.deepEqual(Array.from(restored.filter(block => block.type === 'text'), block => block.content), ['First paragraph', 'Second paragraph <!-- comment -->']);
});

test('lesson manifest cannot resurrect detached resources or stale download URLs', () => {
  const { window } = load('views/instructor.js');
  const view = window.InstructorView;
  const payload = view.serializeBlocksToPayload([
    { id: 'doc-1', type: 'document', files: [{ resource_id: 'gone', asset_id: 'gone-asset', file_url: '/old-private-link' }] },
    { id: 'text-1', type: 'text', content: 'Body' },
  ], { title: 'Lesson' });
  const restored = view.parseLessonToBlocks({ ...payload, resources: [] });
  assert.equal(restored.flatMap(block => block.files || []).length, 0);
  assert.equal(JSON.stringify(restored).includes('/old-private-link'), false);
});

test('exam workflow reports draft storage failure instead of claiming auto-save', () => {
  const draft = { title: 'Unsaved exam', questions: [{ stem: 'Q' }], storageFailed: true, lastSaved: null };
  const ctx = load('views/instructor-exams.js', {
    window: { InstructorView: {}, ExamStore: { getDraft: () => draft, canVisitStep: () => true } },
    UI: { escapeHtml: value => String(value ?? '') },
  });
  const html = ctx.window.InstructorView.renderExamWorkflowHeader(1, '', null, null);
  assert.match(html, /Chưa lưu/);
  assert.doesNotMatch(html, /1 câu • Tự động lưu/);
});

test('exam store persists a current saved timestamp and emits draft failure state', () => {
  const values = new Map();
  const ctx = load('exam-store.js', {
    window: { app: { currentUser: { id: 'I', active_role: 'INSTRUCTOR' } } },
    localStorage: { getItem: key => values.get(key), setItem: (key, val) => values.set(key, val) },
  });
  const result = ctx.window.ExamStore.saveDraft({ title: 'Saved' });
  assert.equal(JSON.parse(values.values().next().value).lastSaved, result.lastSaved);
  assert.ok(result.lastSaved);
});

test('lesson annotations are never shown as user-facing Markdown content', () => {
  const { window } = load('ui.js');
  const rendered = window.UI.renderMarkdown('Visible body\n<!-- PWD301_BLOCKS: [{"type":"text","content":"INTERNAL_LAYOUT_ONLY"}] -->');
  assert.match(rendered, /Visible body/);
  assert.doesNotMatch(rendered, /INTERNAL_LAYOUT_ONLY|PWD301_BLOCKS/);
});

test('018: an empty saved text manifest cannot hide updated authoritative text', () => {
  const { window } = load('views/instructor.js');
  const view = window.InstructorView;
  const payload = view.serializeBlocksToPayload([
    { id: 'text-empty', type: 'text', content: '' },
    { id: 'document', type: 'document', files: [] },
  ], { title: 'Lesson' });
  const restored = view.parseLessonToBlocks({
    ...payload, markdown_content: `Fresh authoritative content\n${payload.markdown_content}`, resources: [],
  });
  assert.equal(restored.some(block => block.type === 'text' && block.content.includes('Fresh authoritative content')), true);
});
