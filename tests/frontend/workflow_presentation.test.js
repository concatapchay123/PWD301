const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const escapeHtml = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
function loadStudent(extra = {}) {
  const window = { addEventListener() {}, app: { currentUser: { full_name: 'Learner' } } };
  const context = { window, console, UI: { escapeHtml, cleanChoiceText: String, formatDateTime: () => '', showToast() {}, renderMath() {} }, requestAnimationFrame: fn => fn(), localStorage: { getItem: () => null }, document: { getElementById: () => null, querySelectorAll: () => [], createElementNS: () => ({ setAttribute() {} }) }, ...extra };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8'), context);
  return { view: window.StudentView, context };
}

test('waiting room distinguishes resume, closed, exhausted and actual prerequisite lock', () => {
  const { view } = loadStudent();
  assert.equal(view.getWaitingRoomState({ can_start: false, can_resume: true, active_attempt_id: 'active' }), 'RESUME');
  assert.equal(view.getWaitingRoomState({ can_start: false, start_block_reason: 'CLOSED', is_closed: true }), 'CLOSED');
  assert.equal(view.getWaitingRoomState({ can_start: false, start_block_reason: 'EXHAUSTED', is_attempt_limit_reached: true }), 'EXHAUSTED');
  assert.equal(view.getWaitingRoomState({ can_start: false, start_block_reason: 'PREREQUISITE', is_locked: true }), 'LOCKED_PREREQUISITE');
});

test('earned score presentation keeps zero and does not replace an unreleased score', () => {
  const { view } = loadStudent();
  assert.equal(view.getAssessmentScoreLabel({ display_score: { is_released: true, score_out_of_10: 0 } }), '0 / 10');
  assert.equal(view.getAssessmentScoreLabel({ display_score: { is_released: true, score_out_of_10: 7.5 } }), '7.5 / 10');
  assert.equal(view.getAssessmentScoreLabel({ display_score: { is_released: false, score_out_of_10: null } }), 'Chưa công bố');
  assert.equal(view.getAssessmentScoreLabel({ display_score: null }), 'Chưa có điểm');
});

test('shared matching renderer supplies SVG, stable controls and independent duplicate-label cards', () => {
  const { view } = loadStudent();
  const html = view.renderMatchingBoard({ pairs: [{ key: '0', left: '<Left>', options: [{ key: 'a', text: 'Same' }] }, { key: '1', left: 'Second', options: [{ key: 'b', text: 'Same' }] }], rights: [{ text: 'Same' }, { text: 'Same' }], attributes: 'data-test-board="1"' });
  assert.match(html, /matching-board-svg/);
  assert.match(html, /data-left-key="0"/);
  assert.match(html, /data-right-pos="0"/);
  assert.match(html, /data-right-pos="1"/);
  assert.match(html, /&lt;Left>/);
  assert.match(html, /<select/);
  assert.doesNotMatch(html, /is_correct|data-correct|Đáp án đúng/);
});

test('matching restores per-group saved keys through selected option text', () => {
  const { view } = loadStudent();
  const list = () => ({ add() {}, remove() {} });
  const left = { dataset: { leftKey: '1' }, classList: list() };
  const right = { dataset: { rightPos: '0', rightText: 'Visible answer' }, classList: list() };
  const select = { dataset: { groupIndex: '1' }, value: 'group-specific-uuid', options: [{ value: 'group-specific-uuid', dataset: { answerText: 'Visible answer' }, textContent: 'Visible answer' }] };
  const counter = { textContent: '' };
  const svg = { innerHTML: '', appendChild() {} };
  const board = {
    getBoundingClientRect: () => ({ left: 0, top: 0 }),
    querySelector(selector) {
      if (selector === '.matching-board-svg') return svg;
      if (selector === '.matching-board-counter') return counter;
      if (selector.includes('.matching-card-left[')) return left;
      if (selector.includes('.matching-card-right[')) return right;
      return null;
    },
    querySelectorAll(selector) {
      if (selector.includes('select.')) return [select];
      if (selector === '.matching-card-left') return [left];
      if (selector === '.matching-card-right') return [right];
      if (selector === '.matching-card-left, .matching-card-right') return [left, right];
      return [];
    }
  };
  view.setupMatchingBoard(board, () => {});
  assert.equal(counter.textContent, '1/1 đã nối');
});

test('matching callbacks preserve the physical right card for duplicate answer labels', () => {
  const { view } = loadStudent();
  const card = dataset => ({ dataset, classList: { add() {}, remove() {} }, setAttribute() {} });
  const lefts = [card({ leftKey: '0' }), card({ leftKey: '1' })];
  const rights = [card({ rightPos: '0', rightText: 'Same' }), card({ rightPos: '1', rightText: 'Same' })];
  const board = {
    getBoundingClientRect: () => ({ left: 0, top: 0 }),
    querySelector(selector) {
      if (selector === '.matching-board-svg') return { innerHTML: '', appendChild() {} };
      if (selector.includes('.matching-card-left[')) return lefts.find(item => selector.includes(`"${item.dataset.leftKey}"`));
      if (selector.includes('.matching-card-right[')) return rights.find(item => selector.includes(`"${item.dataset.rightPos}"`));
      return null;
    },
    querySelectorAll(selector) {
      if (selector === '.matching-card-left') return lefts;
      if (selector === '.matching-card-right') return rights;
      if (selector === '.matching-card-left, .matching-card-right') return [...lefts, ...rights];
      return [];
    }
  };
  const calls = [];
  view.setupMatchingBoard(board, (...args) => calls.push(args));
  lefts[0].onclick(); rights[1].onclick();
  lefts[1].onclick(); rights[0].onclick();
  assert.deepEqual(calls, [['0', 'Same', '1'], ['1', 'Same', '0']]);
});

test('hidden detail results still render released total and suppress answer content', async () => {
  const data = { score_status: 'RELEASED', allow_student_view_results: false, raw_score: 7.5, max_score: 10, passed: true, questions: [{ content: 'Question', choices: [{ content: 'PRIVATE ANSWER', is_selected: true, is_correct: true }], explanation: 'PRIVATE EXPLANATION' }] };
  const { view } = loadStudent({ ApiClient: { getAttemptResult: async () => data, getAttemptAppeal: async () => ({}) } });
  const container = { innerHTML: '', querySelector: () => null, querySelectorAll: () => [] };
  await view.renderAttemptResults(container, 'attempt');
  assert.match(container.innerHTML, /7\.5/);
  assert.doesNotMatch(container.innerHTML, /PRIVATE ANSWER|PRIVATE EXPLANATION/);
});

test('Admin review API carries the exact displayed review version and request identity', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/api.js'), 'utf8'), { window, console });
  const calls = [];
  window.ApiClient.request = async (url, options) => { calls.push({ url, ...options }); return {}; };
  await window.ApiClient.reviewCourse('course', 'APPROVE', '', 'initial-version');
  await window.ApiClient.approveCourseChangeset('request', '', 'submitted-version');
  await window.ApiClient.rejectCourseChangeset('request', 'Needs revision', 'submitted-version');
  assert.equal(calls[0].body.review_version, 'initial-version');
  assert.equal(calls[1].body.request_id, 'request');
  assert.equal(calls[1].body.review_version, 'submitted-version');
  assert.equal(calls[2].body.review_version, 'submitted-version');
});

test('withdraw APIs carry the displayed sealed submission identity', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/api.js'), 'utf8'), { window, console });
  const calls = [];
  window.ApiClient.request = async (url, options) => { calls.push({ url, ...options }); return {}; };
  await window.ApiClient.cancelSubmitCourse('course', 'initial-version');
  await window.ApiClient.retractCourseChangeset('course', { request_id: 'request', review_version: 'update-version' });
  assert.equal(calls[0].body?.review_version, 'initial-version');
  assert.equal(calls[1].body?.request_id, 'request');
  assert.equal(calls[1].body?.review_version, 'update-version');
});

test('instructor course reads never substitute the published catalog after a draft read fails', async () => {
  const window = { location: { hash: '#/instructor/courses/edit?id=course' } };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/api.js'), 'utf8'), { window, console });
  const calls = [];
  window.ApiClient.request = async url => { calls.push(url); if (url.startsWith('/instructor')) throw new Error('Draft unavailable'); return { title: 'Published baseline' }; };
  await assert.rejects(window.ApiClient.getCourseDetail('course'), /Draft unavailable/);
  assert.deepEqual(calls, ['/instructor/courses/course']);
});

test('prerequisite edits preserve unchanged requirements and stage additions/removals', () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8'), { window, console });
  const initial = [{ prerequisite_course_id: 'a', min_grade_point: 5 }, { prerequisite_course_id: 'b', min_grade_point: 6 }];
  const selected = [{ prerequisite_course_id: 'a', min_grade_point: 7 }, { prerequisite_course_id: 'c', min_grade_point: 5 }];
  const edits = window.InstructorView.getPrerequisiteEdits(initial, selected);
  assert.deepEqual(Array.from(edits.remove), ['b']);
  assert.deepEqual(JSON.parse(JSON.stringify(edits.add)), [{ prerequisite_course_id: 'c' }]);
  assert.equal(window.InstructorView.getPrerequisiteEdits(initial, initial).add.length, 0);
});

test('lesson completion UI follows server acknowledgement and preview cannot write completion', async () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8').replaceAll('\r\n', '\n');
  const start = source.indexOf('const checkAndUnlockLesson = async () => {');
  const end = source.indexOf('\n          };', start) + '\n          };'.length;
  for (const [preview, response, expected] of [[false, { is_completed: false }, 0], [false, { is_completed: true }, 1], [true, { is_completed: true }, 0]]) {
    let completed = 0, writes = 0;
    const context = { isPreview: preview, isCompleted: false, trackedLessonId: 'lesson', renderBottomNav() {}, isLessonRequirementsMet: () => true,
      setLessonCompleted: () => { completed++; }, console, UI: { showToast() {} },
      ApiClient: { recordLessonProgress: async () => { writes++; return response; } } };
    vm.runInNewContext(source.slice(start, end) + '\nthis.confirmCompletion = checkAndUnlockLesson;', context);
    await context.confirmCompletion();
    assert.equal(completed, expected);
    assert.equal(writes, preview ? 0 : 1);
  }
});

test('an active resumable final test stays in the active section at its attempt limit', () => {
  const { view } = loadStudent();
  const active = { id: 'active', is_open: true, can_resume: true, is_attempt_limit_reached: true };
  const done = { id: 'done', is_open: true, is_completed: true, is_attempt_limit_reached: true };
  const upcoming = { id: 'future', is_open: false };
  const result = view.partitionAssessments([active, done, upcoming]);
  assert.equal(result.active[0], active);
  assert.equal(result.completed[0], done);
  assert.equal(result.upcoming[0], upcoming);
});
