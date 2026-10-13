const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync('frontend/assets/js/views/instructor-exams.js', 'utf8');

function proceed(mode, chapter = 'unit', lesson = 'lesson', selectedMode = null) {
  const patches = [], errors = [];
  const window = { ExamStore: { saveDraft(patch) { patches.push(patch); } }, location: { hash: '#/instructor/exams/matrix' } };
  const context = {
    window, currentAcademicMode: mode, currentUnitId: 'unit',
    draft: { academicMode: mode, learningUnitId: 'unit' },
    questions: [{ stem: 'Retained question' }],
    courseSelect: { value: 'course' }, chapterSelect: { value: chapter }, lessonSelect: { value: lesson },
    document: { querySelector() { return selectedMode ? { value: selectedMode } : null; } },
    UI: { showToast(message) { errors.push(message); } },
  };
  const start = source.indexOf('    const onProceedToSettings = () => {');
  const end = source.indexOf("    document.getElementById('btn-matrix-proceed')", start);
  vm.runInNewContext(source.slice(start, end) + '\nthis.proceed = onProceedToSettings;', context);
  context.proceed();
  return { window, patches, errors };
}

test('matrix progression preserves contextual chapter mode and exact selected chapter', () => {
  const result = proceed('chapter_linked');
  assert.equal(result.patches[0].academicMode, 'chapter_linked');
  assert.equal(result.patches[0].learningUnitId, 'unit');
  assert.equal(result.patches[0].lessonId, '');
});

test('chapter mode requires a selected chapter before acknowledging matrix completion', () => {
  const result = proceed('chapter_linked', '');
  assert.equal(result.patches.length, 0);
  assert.equal(result.window.location.hash, '#/instructor/exams/matrix');
  assert.equal(result.errors.length, 1);
});

test('explicit independent choice clears linkage and lesson mode still requires a lesson', () => {
  const independent = proceed('chapter_linked', 'unit', 'lesson', 'independent');
  assert.equal(independent.patches[0].academicMode, 'independent');
  assert.equal(independent.patches[0].learningUnitId, '');
  assert.equal(independent.patches[0].lessonId, '');
  const missing = proceed('lesson_linked', 'unit', '', 'lesson_linked');
  assert.equal(missing.patches.length, 0);
});

test('matrix progression does not silently replace contextual final exam mode', () => {
  const result = proceed('course_final');
  assert.equal(result.patches[0].academicMode, 'course_final');
  assert.equal(result.patches[0].learningUnitId, '');
  assert.equal(result.patches[0].lessonId, '');
});
