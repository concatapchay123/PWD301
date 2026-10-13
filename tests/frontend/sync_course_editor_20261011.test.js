const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8');

test('lesson draft acknowledgement replaces route identity and keeps departure guard aligned', () => {
  const oldHash = '#/instructor/courses/manage?id=course&tab=curriculum&lesson_id=published';
  const window = { location: { hash: oldHash }, app: { beforeRouteLeave: { routeHash: oldHash } }, history: { replaceState(_state, _title, hash) { window.location.hash = hash; } } };
  vm.runInNewContext(source, { window, URLSearchParams });
  window.InstructorView.replaceLessonEditorRoute('course', 'published', 'draft');
  assert.equal(window.location.hash, '#/instructor/courses/manage?id=course&tab=curriculum&lesson_id=draft');
  assert.equal(window.app.beforeRouteLeave.routeHash, window.location.hash);
  window.InstructorView.replaceLessonEditorRoute('course', 'published', 'stale-draft');
  assert.equal(window.location.hash, '#/instructor/courses/manage?id=course&tab=curriculum&lesson_id=draft');
});

test('lesson draft acknowledgement cannot change another course route', () => {
  const window = { location: { hash: '#/instructor/courses/manage?id=other&lesson_id=published' }, history: { replaceState() { assert.fail('wrong course route changed'); } } };
  vm.runInNewContext(source, { window, URLSearchParams });
  window.InstructorView.replaceLessonEditorRoute('course', 'published', 'draft');
});

function selectionHarness() {
  const initialHash = '#/instructor/courses/manage?id=course&tab=curriculum&lesson_id=A';
  let replacements = 0;
  const window = { location: { hash: initialHash }, app: { beforeRouteLeave: { routeHash: initialHash } }, history: { replaceState(_state, _title, hash) { replacements++; window.location.hash = hash; } } };
  const context = { window, URLSearchParams, cId: 'course', activeLessonId: 'A', activeUnitId: 'unit', isEditorDirty: false, selectLessonGen: 0,
    activeLessonMeta: {}, activeBlocks: [], editorContainer: { innerHTML: '' }, renderTree() {}, renderEmptyEditor() {}, renderEditor() {},
    UI: { confirm: async () => false, escapeHtml: String }, ApiClient: { getLesson: async () => ({ title: 'Second lesson', status: 'DRAFT' }) } };
  vm.createContext(context);
  vm.runInContext(source, context);
  context.InstructorView = window.InstructorView;
  context.InstructorView.parseLessonToBlocks = () => [];
  const start = source.indexOf('    const selectLesson = async');
  const end = source.indexOf('    // Render single block card HTML', start);
  vm.runInContext(source.slice(start, end) + '\nthis.selectLessonForTest = selectLesson;', context);
  return { context, window, replacements: () => replacements };
}

test('successful tree selection replaces the lesson route for F5 without growing history', async () => {
  const h = selectionHarness();
  await h.context.selectLessonForTest('B', 'unit');
  assert.equal(new URLSearchParams(h.window.location.hash.split('?')[1]).get('lesson_id'), 'B');
  assert.equal(h.replacements(), 1);
  assert.equal(h.window.app.beforeRouteLeave.routeHash, h.window.location.hash);
});

test('cancelled or failed lesson selection retains the last successful URL', async () => {
  const h = selectionHarness();
  h.context.isEditorDirty = true;
  await h.context.selectLessonForTest('B', 'unit');
  assert.equal(h.context.activeLessonId, 'A');
  h.context.isEditorDirty = false;
  h.context.ApiClient.getLesson = async () => { throw new Error('Unavailable'); };
  await h.context.selectLessonForTest('B', 'unit');
  assert.equal(new URLSearchParams(h.window.location.hash.split('?')[1]).get('lesson_id'), 'A');
  assert.equal(h.replacements(), 0);
});

test('late lesson GET cannot replace the newest selected route', async () => {
  const h = selectionHarness();
  const delayed = flight();
  h.context.ApiClient.getLesson = id => id === 'B' ? delayed.promise : Promise.resolve({ title: 'Newest lesson', status: 'DRAFT' });
  const first = h.context.selectLessonForTest('B', 'unit');
  await h.context.selectLessonForTest('C', 'unit');
  delayed.resolve({ title: 'Late lesson', status: 'DRAFT' });
  await first;
  assert.equal(h.context.activeLessonMeta.title, 'Newest lesson');
  assert.equal(new URLSearchParams(h.window.location.hash.split('?')[1]).get('lesson_id'), 'C');
  assert.equal(h.replacements(), 1);
});

test('video URL blur refreshes preview without replacing the clicked editor controls', () => {
  const input = {};
  const preview = { innerHTML: '' };
  let editorReplacements = 0;
  const context = {
    card: { querySelector: selector => selector === '.block-video-url' ? input : preview },
    bIdx: 0,
    activeBlocks: [{ type: 'video', url: 'https://youtu.be/dQw4w9WgXcQ' }],
    isEditorDirty: false,
    scrapeBlocksFromDom() {},
    renderEditor() { editorReplacements++; },
    renderBlockHtml() { return '<div class="block-video-preview">new preview</div>'; },
    document: { createElement: () => ({ content: { querySelector: () => ({ innerHTML: 'new preview' }) } }) },
  };
  const start = source.indexOf('        const videoUrlInput = card.querySelector');
  const end = source.indexOf('        // Video file upload & dropzone handlers', start);
  vm.runInNewContext(source.slice(start, end), context);
  input.onchange();
  assert.equal(editorReplacements, 0);
  assert.equal(preview.innerHTML, 'new preview');
  assert.equal(context.isEditorDirty, true);
});
function flight() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
function harness() {
  const save = {}, del = { dataset: { idx: '0', fileIdx: '0', resourceId: 'file-A' } };
  const videoDel = { dataset: { fileIdx: '0', resourceId: 'file-A' } };
  const card = { querySelector: () => null, querySelectorAll: selector => selector === '.btn-delete-video-file' ? [videoDel] : [] };
  const updates = flight(), detach = flight(), confirm = flight(), calls = [];
  const ctx = { console, FormData, isSaving: false, isLocked: false, activeLessonId: 'A', activeUnitId: 'unit', selectLessonGen: 1,
    activeLessonMeta: { title: 'Title A' }, activeBlocks: [{ id: 'block-A', type: 'video', files: [{ resource_id: 'file-A' }] }],
    isEditorDirty: true, cId: 'course', currentUnits: [{ id: 'unit', lessons: [{ id: 'A', title: 'Title A' }] }],
    course: { lessons: [] }, scrapeBlocksFromDom() {}, renderEditor() {},
    UI: { showToast() {}, confirm: () => confirm.promise },
    ApiClient: { updateLesson: (...args) => { calls.push(['save', ...args]); return updates.promise; },
      detachLessonResource: (...args) => { calls.push(['detach', ...args]); return detach.promise; } },
    InstructorView: { serializeBlocksToPayload: (blocks, meta) => JSON.parse(JSON.stringify({ ...meta, blocks })) },
    treeContainer: { querySelector: () => null },
    editorContainer: { querySelector: selector => selector === '#btn-save-lesson' ? save : null,
      querySelectorAll: selector => selector === '.btn-block-delete' ? [del] : selector === '.curriculum-block-card' ? [card] : [] },
  };
  vm.createContext(ctx);
  function wire(from, to) { vm.runInContext(source.slice(source.indexOf(from), source.indexOf(to, source.indexOf(from))), ctx); }
  return { ctx, save, del, videoDel, updates, detach, confirm, calls, wire };
}

test('019: structural block additions mark the editor dirty', () => {
  const h = harness();
  const add = {};
  h.ctx.isEditorDirty = false;
  h.ctx.editorContainer.querySelector = selector => selector === '#btn-add-block-text' ? add : null;
  h.wire('      // Add Block buttons', '      // Reorder and delete blocks');
  add.onclick();
  assert.equal(h.ctx.isEditorDirty, true);
});

test('019: lesson departure and unload preserve unsaved edits', async () => {
  const listeners = {};
  const window = { app: {}, location: { hash: '#/instructor/courses/manage?id=course' },
    addEventListener: (type, handler) => { listeners[type] = handler; }, removeEventListener() {} };
  vm.runInNewContext(source, { window, document: {}, UI: { confirm: async () => false } });
  let dirty = true;
  window.InstructorView.installLessonDepartureGuard({ isConnected: true }, () => dirty);
  assert.equal(await window.app.beforeRouteLeave.leave(), false);
  let prevented = false;
  listeners.beforeunload({ preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  dirty = false;
  assert.equal(await window.app.beforeRouteLeave.leave(), true);
});

test('save response uses submitted title and preserves later edits', async () => {
  const h = harness(); h.wire('      const saveBtn = editorContainer', '      // Add Block buttons');
  const pending = h.save.onclick();
  h.ctx.activeLessonMeta.title = 'Unsaved later title';
  h.updates.resolve({ status: 'DRAFT' }); await pending;
  assert.equal(h.ctx.currentUnits[0].lessons[0].title, 'Title A');
  assert.equal(h.ctx.isEditorDirty, true);
});

test('new lesson revision acknowledgement rebinds resource controls while retaining later edits', async () => {
  const h = harness();
  h.ctx.InstructorView.replaceLessonEditorRoute = () => {};
  h.ctx.activeBlocks[0].files[0].asset_id = 'asset-A';
  let rendered = 0;
  h.ctx.renderEditor = () => { rendered++; };
  h.wire('      const saveBtn = editorContainer', '      // Add Block buttons');
  const pending = h.save.onclick();
  h.ctx.activeLessonMeta.title = 'Later edit';
  h.updates.resolve({ lesson: { lesson_id: 'draft-A', status: 'DRAFT', resources: [{ asset_id: 'asset-A', resource_id: 'draft-file-A' }] } });
  await pending;
  assert.equal(h.ctx.activeBlocks[0].files[0].resource_id, 'draft-file-A');
  assert.equal(h.ctx.activeLessonMeta.title, 'Later edit');
  assert.equal(h.ctx.isEditorDirty, true);
  assert.equal(rendered, 1);
});

for (const outcome of ['failure', 'pending']) {
  test(`block deletion retains block on ${outcome}`, async () => {
    const h = harness(); h.wire("      editorContainer.querySelectorAll('.btn-block-delete')", '      // Document file upload inputs');
    const pending = h.del.onclick(); h.confirm.resolve(true); await Promise.resolve();
    if (outcome === 'failure') h.detach.reject(new Error('detach failed'));
    else h.detach.resolve({ pending_approval: true });
    await pending; assert.equal(h.ctx.activeBlocks.length, 1);
  });
}

test('block confirmation cannot delete another lesson', async () => {
  const h = harness(); h.wire("      editorContainer.querySelectorAll('.btn-block-delete')", '      // Document file upload inputs');
  const pending = h.del.onclick();
  h.ctx.activeLessonId = 'B'; h.ctx.selectLessonGen = 2; h.ctx.activeBlocks = [{ id: 'block-B', files: [{ resource_id: 'file-B' }] }];
  h.confirm.resolve(true); await Promise.resolve(); h.detach.resolve({ success: true }); await pending;
  assert.equal(h.calls.length, 0); assert.equal(h.ctx.activeBlocks[0].id, 'block-B');
});

test('video confirmation cannot target newly selected lesson', async () => {
  const h = harness(); h.wire('      // Document file upload inputs', '      // Preview Lesson Button');
  const pending = h.videoDel.onclick();
  h.ctx.activeLessonId = 'B'; h.ctx.selectLessonGen = 2; h.ctx.activeBlocks = [{ id: 'block-B', files: [{ resource_id: 'file-B' }] }];
  h.confirm.resolve(true); await Promise.resolve(); h.detach.resolve({ success: true }); await pending;
  assert.equal(h.calls.length, 0); assert.equal(h.ctx.activeBlocks[0].files.length, 1);
});

test('video pending detach retains authoritative file', async () => {
  const h = harness(); h.wire('      // Document file upload inputs', '      // Preview Lesson Button');
  const pending = h.videoDel.onclick(); h.confirm.resolve(true); await Promise.resolve(); h.detach.resolve({ pending_approval: true }); await pending;
  assert.equal(h.ctx.activeBlocks[0].files.length, 1);
});

for (const kind of ['question-file', 'question-paste', 'option-file', 'option-paste']) {
  function imageHarness() {
    const h = harness(), readers = [], handlers = {};
    const questionFile = {}, optionFile = { dataset: { optIdx: '0' } };
    const questionText = { addEventListener: (event, handler) => { handlers.questionPaste = handler; } };
    const optionText = { addEventListener: (event, handler) => { handlers.optionPaste = handler; } };
    const card = {
      querySelector: selector => ({ '.block-quiz-question': questionText, '.block-quiz-question-file': questionFile }[selector] || null),
      querySelectorAll: selector => selector === '.block-quiz-opt-file' ? [optionFile] : selector === '.block-quiz-opt-text' ? [optionText] : [],
    };
    let scrapes = 0, renders = 0;
    h.ctx.scrapeBlocksFromDom = () => { scrapes++; };
    h.ctx.renderEditor = () => { renders++; };
    h.ctx.FileReader = class { constructor() { readers.push(this); } readAsDataURL() {} };
    h.ctx.editorContainer.querySelectorAll = selector => selector === '.curriculum-block-card' ? [card] : [];
    h.ctx.activeBlocks = [{ id: 'block-A', type: 'quiz', options: ['First', 'Second'] }];
    h.ctx.isEditorDirty = false;
    h.wire('      // Quiz Image Upload & Paste', '      // Activate Microsoft Word Standard Ribbon Toolbar');
    function start() {
      const event = { target: { files: [{}] }, preventDefault() {}, clipboardData: { items: [{ type: 'image/png', getAsFile: () => ({}) }] } };
      if (kind === 'question-file') questionFile.onchange(event);
      if (kind === 'option-file') optionFile.onchange(event);
      if (kind === 'question-paste') handlers.questionPaste(event);
      if (kind === 'option-paste') handlers.optionPaste(event);
      scrapes = 0; renders = 0;
    }
    return { ...h, start, readers, counts: () => ({ scrapes, renders }) };
  }

  test(`026: ${kind} read cannot mutate a newly selected lesson`, () => {
    const h = imageHarness(); h.start();
    h.ctx.activeLessonId = 'B'; h.ctx.selectLessonGen = 2;
    h.ctx.activeBlocks = [{ id: 'block-B', type: 'quiz', options: ['Other'] }];
    h.readers[0].onload({ target: { result: 'data:image/png;base64,AAA' } });
    assert.equal(h.ctx.activeBlocks[0].image_url, undefined);
    assert.equal(h.ctx.activeBlocks[0].option_images, undefined);
    assert.equal(h.ctx.isEditorDirty, false);
    assert.deepEqual(h.counts(), { scrapes: 0, renders: 0 });
  });

  test(`026: ${kind} read follows the original block after reordering`, () => {
    const h = imageHarness(), target = h.ctx.activeBlocks[0]; h.start();
    h.ctx.activeBlocks.unshift({ id: 'unrelated', type: 'text' });
    h.readers[0].onload({ target: { result: 'data:image/png;base64,AAA' } });
    assert.equal(kind.startsWith('question') ? target.image_url : target.option_images?.[0], 'data:image/png;base64,AAA');
    assert.equal(h.ctx.activeBlocks[0].image_url, undefined);
    assert.equal(h.ctx.activeBlocks[0].option_images, undefined);
    assert.equal(h.ctx.isEditorDirty, true);
  });

  if (kind.startsWith('option')) {
    test(`026: ${kind} read is discarded if choices change while reading`, () => {
      const h = imageHarness(); h.start();
      h.ctx.activeBlocks[0].options.splice(0, 1);
      h.readers[0].onload({ target: { result: 'data:image/png;base64,AAA' } });
      assert.equal(h.ctx.activeBlocks[0].option_images, undefined);
      assert.equal(h.ctx.isEditorDirty, false);
      assert.equal(h.counts().renders, 0);
    });
  }
}
