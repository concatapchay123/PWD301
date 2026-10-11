const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function harness() {
  const buttons = [0, 1].map(index => ({ dataset: { lessonIndex: String(index) }, setAttribute() {} }));
  let paused = 0;
  const workspace = { innerHTML: '', querySelectorAll: selector => selector === 'video' ? [{ pause: () => paused++ }] : [] };
  const container = { innerHTML: '', querySelector: () => workspace, querySelectorAll: () => buttons };
  const window = {};
  const UI = {
    escapeHtml: value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;'),
    renderMarkdown: value => `<p>${value}</p>`,
    parseYouTubeId: () => 'abcdefghijk',
    getYouTubeEmbedUrl: () => 'https://www.youtube.com/embed/abcdefghijk?enablejsapi=1',
  };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
    window, UI, console, document: { getElementById: () => null },
    ApiClient: new Proxy({}, { get: () => () => { throw new Error('Preview must not write or fetch progress'); } }),
  });
  return { view: window.AdminView, container, workspace, buttons, paused: () => paused };
}

test('reviewer tree switches content instantly and pauses removed media without progress writes', () => {
  const h = harness();
  h.view.renderReviewerCoursePreview(h.container, { learning_units: [{ id: 'u1', title: 'Chapter A' }], lessons: [
    { lesson_id: 'l1', learning_unit_id: 'u1', title: 'First', markdown_content: 'First text', resources: [
      { asset_id: 'safe-video', filename: 'lecture.mp4', mime_type: 'video/mp4', scan_status: 'CLEAN', file_url: '/student/files/safe-video/download' },
      { asset_id: 'unsafe-video', filename: 'unsafe.mp4', mime_type: 'video/mp4', scan_status: 'PENDING' },
    ] },
    { lesson_id: 'l2', title: 'Second', markdown_content: 'Second text' },
  ] });
  assert.match(h.container.innerHTML, /Chapter A/);
  assert.match(h.workspace.innerHTML, /\/api\/files\/safe-video\/stream/);
  assert.doesNotMatch(h.workspace.innerHTML, /student\/files|unsafe-video/);
  h.buttons[1].onclick();
  assert.match(h.workspace.innerHTML, /Second text/);
  assert.doesNotMatch(h.workspace.innerHTML, /First text/);
  assert.ok(h.paused() >= 1);
});

test('reviewer parses canonical video and quiz metadata with local answer feedback', () => {
  const h = harness();
  h.view.renderReviewerCoursePreview(h.container, { lessons: [{ title: 'Media', video_urls: ['https://youtu.be/abcdefghijk'],
    markdown_content: 'Read this<!-- mini_quiz: [{"question":"2 + 2?","options":["3","4"],"correct_index":1}] -->',
  }] });
  assert.match(h.workspace.innerHTML, /youtube.com\/embed/);
  assert.match(h.workspace.innerHTML, /2 \+ 2\?/);
  assert.match(h.workspace.innerHTML, /Kiểm tra đáp án/);
  assert.doesNotMatch(h.workspace.innerHTML, /mini_quiz:/);
});

test('reviewer quiz handles canonical formats and exact multiple-choice sets locally', () => {
  const h = harness();
  const multi = { type: 'MULTIPLE_CHOICE', options: ['A', 'B', 'C'], correct_indices: [0, 2] };
  assert.match(h.view.reviewerQuizInputs(multi, 'multi'), /type="checkbox"/);
  assert.equal(h.view.gradeReviewerQuiz(multi, ['0']), false);
  assert.equal(h.view.gradeReviewerQuiz(multi, ['2', '0']), true);
  const blank = { type: 'FILL_BLANK', blanks: [{ accepted_answers: ['Hà Nội', 'Hanoi'] }] };
  assert.match(h.view.reviewerQuizInputs(blank, 'blank'), /type="text"/);
  assert.equal(h.view.gradeReviewerQuiz(blank, ['  HÀ NỘI ']), true);
  assert.equal(h.view.gradeReviewerQuiz(blank, ['']), false);
  const matching = { type: 'MATCHING', pairs: [{ left: 'One', right: '1' }, { left: 'Two', right: '2' }] };
  assert.match(h.view.reviewerQuizInputs(matching, 'match'), /One/);
  assert.equal(h.view.gradeReviewerQuiz(matching, ['1', '2']), true);
  assert.equal(h.view.gradeReviewerQuiz(matching, ['2', '1']), false);
  assert.equal(h.view.gradeReviewerQuiz({ type: 'TRUE_FALSE', correct_value: false }, ['false']), true);
  assert.equal(h.view.gradeReviewerQuiz({ type: 'TRUE_FALSE', correct_value: true }, ['false']), false);
  assert.equal(h.view.gradeReviewerQuiz({ options: ['A'] }, ['0']), null);
});

test('reviewer hides internal passing metadata and escapes quiz answers', () => {
  const h = harness();
  h.view.renderReviewerCoursePreview(h.container, { lessons: [{ title: 'Quiz', markdown_content: 'Read<!-- mini_quiz_passing: 80 -->', quiz: [{ type: 'FILL_BLANK', question: 'Fill', blanks: [{ accepted_answers: ['<script>secret</script>'] }] }] }] });
  assert.doesNotMatch(h.workspace.innerHTML, /mini_quiz_passing|<script>|secret/);
});

test('reviewer tree identifies video quiz and text lessons with contextual icons', () => {
  const h = harness();
  h.view.renderReviewerCoursePreview(h.container, { lessons: [
    { title: 'Video', resources: [{ mime_type: 'video/mp4', asset_id: 'video' }] },
    { title: 'Quiz', markdown_content: '<!-- mini_quiz: [] -->' },
    { title: 'Text', markdown_content: 'Read this' },
  ] });
  assert.match(h.container.innerHTML, />videocam<\/span>/);
  assert.match(h.container.innerHTML, />quiz<\/span>/);
  assert.match(h.container.innerHTML, />article<\/span>/);
});

test('malformed optional quiz metadata cannot crash reviewer preview or claim correctness', () => {
  const h = harness();
  assert.doesNotThrow(() => h.view.renderReviewerCoursePreview(h.container, {
    lessons: [{ title: 'Malformed metadata', markdown_content: '<!-- mini_quiz: [null, 5, {"question":"Valid question","options":["A"]}] -->' }],
  }));
  assert.match(h.workspace.innerHTML, /Valid question/);
  assert.doesNotThrow(() => h.view.reviewerQuizInputs({ type: 'MATCHING', pairs: [null] }, 'quiz'));
  assert.equal(h.view.gradeReviewerQuiz({ type: 'MATCHING', pairs: [null] }, ['A']), null);
  assert.equal(h.view.gradeReviewerQuiz({ type: 'FILL_BLANK', blanks: [null] }, ['A']), null);
});

test('resource proposal preview neither mutates originals nor retains detached resources', () => {
  const h = harness();
  const original = { resources: [{ resource_id: 'r1', asset_id: 'old', title: 'old.pdf' }] };
  const proposal = { action: 'RESOURCE_CHANGES', changes: [
    { action: 'DETACH', resource_id: 'r1' }, { action: 'ATTACH', asset_id: 'new', title: 'new.pdf' },
  ] };
  const merged = h.view.reviewerProposedLesson(original, proposal);
  assert.deepEqual(original.resources.map(r => r.title), ['old.pdf']);
  assert.deepEqual(Array.from(merged.resources, r => r.title), ['new.pdf']);
});

test('instructor preview reuses reviewer rendering and cleans media on close', () => {
  let options;
  let rendered;
  let paused = false;
  const preview = { querySelectorAll: () => [{ pause: () => { paused = true; } }] };
  const window = { AdminView: { renderReviewerCoursePreview: (...args) => { rendered = args; } } };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8'), {
    window, UI: { openModal: value => { options = value; } }, document: { getElementById: () => preview },
  });
  window.InstructorView.openCoursePreview({ lessons: [{ lesson_id: 'draft-local', title: 'Unsaved lesson' }] }, 'draft-local');
  assert.equal(rendered[2], 'draft-local');
  assert.equal(rendered[1].lessons[0].title, 'Unsaved lesson');
  options.onClose();
  assert.equal(paused, true);
});

test('document preview rejects executable URLs and escapes file URLs', () => {
  const modals = [];
  const window = {};
  const UI = { escapeHtml: value => String(value).replaceAll('"', '&quot;').replaceAll('<', '&lt;'),
    openModal: options => modals.push(options), showToast: () => {} };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), { window, UI });
  window.AdminView.openDocumentPreviewModal('text.txt', 'javascript:alert(1)', 'text/plain');
  assert.equal(modals.length, 0);
  window.AdminView.openDocumentPreviewModal('<img src=x onerror=alert(1)>text.txt', '/api/files/x/download?name=" onload="alert(1)', 'text/plain');
  assert.doesNotMatch(modals[0].bodyHtml, /name=" onload="/);
  assert.match(modals[0].bodyHtml, /sandbox/);
  assert.doesNotMatch(modals[0].title, /<img/);
});

test('native PDF preview verifies bytes before embedding and releases its URL', async () => {
  let options;
  const frame = { src: '', isConnected: true };
  const message = { textContent: '' };
  const revoked = [];
  const window = {};
  const UI = { escapeHtml: String, openModal: value => { options = value; }, showToast() {} };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
    window, UI, console, Blob, URL: { createObjectURL: () => 'blob:verified-pdf', revokeObjectURL: value => revoked.push(value) },
    fetch: async () => ({ ok: true, headers: { get: () => 'application/pdf' }, blob: async () => new Blob(['%PDF-1.7 test'], { type: 'application/pdf' }) }),
    document: { getElementById: id => id === 'reviewer-pdf-frame' ? frame : id === 'reviewer-pdf-message' ? message : null },
  });
  await window.AdminView.openDocumentPreviewModal('test.pdf', '/api/files/x/download', 'application/pdf');
  assert.equal(frame.src, 'blob:verified-pdf');
  assert.doesNotMatch(options.bodyHtml, /iframe sandbox/);
  assert.match(options.bodyHtml, /reviewer-pdf-message/);
  options.onClose();
  assert.deepEqual(revoked, ['blob:verified-pdf']);
});

test('native PDF preview never embeds HTML or a failed authorization response', async () => {
  for (const response of [
    { ok: false, headers: { get: () => 'application/pdf' } },
    { ok: true, headers: { get: () => 'text/html' } },
    { ok: true, headers: { get: () => 'application/pdf' }, blob: async () => new Blob(['<script>alert(1)</script>']) },
  ]) {
    const frame = { src: '', isConnected: true };
    const message = { textContent: '' };
    const window = {};
    vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
      window, Blob, URL: { createObjectURL: () => { throw new Error('Untrusted bytes embedded'); } },
      UI: { escapeHtml: String, openModal() {} }, fetch: async () => response,
      document: { getElementById: id => id === 'reviewer-pdf-frame' ? frame : message },
    });
    await window.AdminView.openDocumentPreviewModal('document.pdf', '/api/files/x/download', 'application/pdf');
    assert.equal(frame.src, '');
    assert.match(message.textContent, /Không thể xem/);
  }
});
