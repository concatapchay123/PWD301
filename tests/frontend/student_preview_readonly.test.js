const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8');

test('preview mini quiz gives local feedback without writing learner progress or completion', async () => {
  const start = source.indexOf('checkQuizBtn.onclick = async () => {');
  const end = source.indexOf('\n              };', start) + '\n              };'.length;
  const classList = { add() {}, remove() {} };
  const explanation = { classList, innerHTML: '' };
  const card = { querySelector: selector => selector.includes(':checked') ? { value: 'true' } : explanation, querySelectorAll: () => [] };
  const banner = { innerHTML: '' };
  const writes = [];
  const context = {
    isPreview: true, checkQuizBtn: { classList }, resetQuizBtn: { classList }, nextQuizBtn: null,
    lesson: { quiz: [{ type: 'TRUE_FALSE', correct_value: true }] },
    quizSection: { querySelector: () => card, querySelectorAll: () => [card] },
    totalQuizSlides: 1, quizPassingPercent: 80, currentQuizSlide: 0, hasPassedQuiz: false,
    activeItem: { id: 'lesson' }, hasVideo: true, setLessonCompleted: () => writes.push('local-completion'),
    updateQuizSlideView() {}, UI: { escapeHtml: String, showToast() {} },
    document: { getElementById: id => id === 'cisco-quiz-score-banner' ? banner : { dataset: { lessonId: 'lesson' } } },
    ApiClient: {
      recordLessonProgress: async () => { writes.push('progress'); },
      completeLessonMiniQuiz: async () => { writes.push('quiz'); return { is_completed: true }; },
    },
  };
  vm.runInNewContext(source.slice(start, end), context);
  await context.checkQuizBtn.onclick();
  assert.deepEqual(writes, []);
  assert.match(explanation.innerHTML, /Chính xác/);
  assert.match(banner.innerHTML, /Xem thử/);
});

test('preview revision opt-in cannot change a learners active revision', async () => {
  const start = source.indexOf('optInBtn.onclick = async () => {');
  const end = source.indexOf('\n            };', start) + '\n            };'.length;
  const writes = [];
  const context = { isPreview: true, optInBtn: {}, activeItem: { id: 'lesson' },
    UI: { showToast() {} }, ApiClient: { optInLessonRevision: async () => { writes.push('revision'); return {}; } },
    StudentView: { renderCourseConsole: async () => {} }, container: {}, courseId: 'course', lesson: {},
  };
  vm.runInNewContext(source.slice(start, end), context);
  await context.optInBtn.onclick();
  assert.deepEqual(writes, []);
});

function resolveResourceVideo(isPreview, scanStatus) {
  const start = source.indexOf('// Multi-tier Video Detection:');
  const end = source.indexOf('lesson.video_url = activeVideoUrl;', start) + 'lesson.video_url = activeVideoUrl;'.length;
  const lesson = { resources: [{ asset_id: 'asset', mime_type: 'video/mp4', scan_status: scanStatus, file_url: '/student/files/asset/download' }] };
  vm.runInNewContext(source.slice(start, end), { lesson, isPreview });
  return lesson.video_url;
}

test('uploaded reviewer video uses authenticated stream and pending video stays hidden', () => {
  assert.equal(resolveResourceVideo(true, 'CLEAN'), '/api/files/asset/stream');
  assert.equal(resolveResourceVideo(true, 'PENDING'), null);
});

test('student video detection never falls back to a raw file download', () => {
  assert.equal(resolveResourceVideo(false, 'CLEAN'), null);
});
