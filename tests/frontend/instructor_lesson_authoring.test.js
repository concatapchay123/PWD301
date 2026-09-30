const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
const source = fs.readFileSync(filename, 'utf8');

function setupContext(extra = {}) {
  const window = {};
  const context = {
    window,
    document: {
      getElementById: () => null,
      querySelectorAll: () => [],
      querySelector: () => null,
      addEventListener: () => {}
    },
    UI: {
      escapeHtml: val => String(val ?? '').replaceAll('<', '&lt;').replaceAll('>', '&gt;'),
      statusBadge: status => `<span class="badge">${status}</span>`,
      renderMarkdown: md => md
    },
    ...extra
  };
  vm.runInNewContext(source, context, { filename });
  return { window, context };
}

test('renderLessonChildNavigator renders dynamic draft placeholder when on new lesson route (currentLessonId is null)', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-1',
    title: 'Chương 1: Khởi động',
    lesson_count: 2,
    lessons: [
      { lesson_id: 'lesson-1', title: 'Bài 1: Giới thiệu', position: 1 },
      { lesson_id: 'lesson-2', title: 'Bài 2: Cài đặt', position: 2 }
    ]
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', null);
  assert.match(html, /id="nav-draft-lesson-item"/, 'Must render draft placeholder item');
  assert.match(html, /id="nav-draft-lesson-title"/, 'Must render draft title element');
  assert.match(html, /Bài giảng 3/, 'Draft placeholder must display index 3 (2 existing + 1)');
  assert.match(html, /Bản nháp/, 'Draft placeholder must display "Bản nháp" badge');
});

test('renderLessonChildNavigator does not render draft placeholder when viewing existing lesson', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-1',
    title: 'Chương 1: Khởi động',
    lesson_count: 2,
    lessons: [
      { lesson_id: 'lesson-1', title: 'Bài 1: Giới thiệu', position: 1 },
      { lesson_id: 'lesson-2', title: 'Bài 2: Cài đặt', position: 2 }
    ]
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'lesson-1');
  assert.doesNotMatch(html, /id="nav-draft-lesson-item"/, 'Must NOT render draft placeholder when editing existing lesson');
  assert.match(html, /aria-current="page"/, 'Must mark active lesson');
});

test('renderLessonChildNavigator sets data-learning-unit-id cleanly without string prefix', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-clean-uuid',
    title: 'Chương Chuẩn',
    lesson_count: 1,
    lessons: [
      { lesson_id: 'lesson-1', title: 'Bài 1', position: 1 }
    ]
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'lesson-1');
  assert.match(html, /data-learning-unit-id="unit-clean-uuid"/, 'Must not contain learning_unit_id= prefix');
  assert.doesNotMatch(html, /data-learning-unit-id="learning_unit_id=/, 'Must not have prefix');
});

test('instructor.js contains separate save draft button and publish button', () => {
  assert.ok(source.includes('id="studio-save-draft-btn"'), 'Includes studio-save-draft-btn');
  assert.ok(source.includes('Lưu nháp'), 'Includes Lưu nháp label');
  assert.ok(source.includes('id="studio-save-btn"'), 'Includes studio-save-btn');
  assert.ok(source.includes('Xuất bản'), 'Includes Xuất bản label');
});

test('instructor.js displays chapter selector without class hidden in studio', () => {
  assert.ok(source.includes('id="studio-learning-unit-select"'), 'Includes studio-learning-unit-select');
  assert.ok(!source.includes('id="studio-learning-unit-select" class="hidden"'), 'Does not hide chapter select');
  assert.ok(source.includes('Thuộc Chương:'), 'Includes Chapter label');
});
