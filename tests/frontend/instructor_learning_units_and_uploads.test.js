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

test('renderLessonChildNavigator renders drag handles, delete button, and add lesson action', () => {
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
  assert.match(html, /Chương 1: Khởi động/);
  assert.match(html, /2\/10 Lesson/);
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-1\/edit"/);
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-2\/edit"/);
  assert.match(html, /aria-current="page"/);
  assert.match(html, /btn-nav-delete-lesson/);
  assert.match(html, /nav-drag-handle/);
  assert.match(html, /\+ Thêm bài học mới/);
  assert.match(html, /data-lesson-id="lesson-1"/);
  assert.match(html, /data-lesson-id="lesson-2"/);
});

test('renderLessonChildNavigator hides add lesson button when unit has 10 lessons', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-max',
    title: 'Chương Đầy',
    lesson_count: 10,
    lessons: Array.from({ length: 10 }, (_, i) => ({
      lesson_id: `l-${i}`,
      title: `Bài ${i + 1}`,
      position: i + 1
    }))
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'l-0');
  assert.doesNotMatch(html, /Thêm Lesson/);
  assert.doesNotMatch(html, /\+ Thêm bài học mới/);
  assert.match(html, /10\/10 Lesson/);
});

test('instructor.js contains Learning Unit reordering and delete actions', () => {
  assert.ok(source.includes('btn-move-unit-up'), 'Includes btn-move-unit-up');
  assert.ok(source.includes('btn-move-unit-down'), 'Includes btn-move-unit-down');
  assert.ok(source.includes('btn-delete-learning-unit'), 'Includes btn-delete-learning-unit');
  assert.ok(source.includes('unit-row-card'), 'Includes unit-row-card');
  assert.ok(source.includes('unit-drag-handle'), 'Includes unit-drag-handle');
});

test('instructor.js does not contain global course-lessons-order details', () => {
  assert.ok(!source.includes('id="course-lessons-order"'), 'Removed global course-lessons-order details');
  assert.ok(!source.includes('Sắp xếp Lesson trong khóa học'), 'Removed global lessons order text');
});

test('instructor.js includes explicit delete buttons for video and document uploads', () => {
  assert.ok(source.includes('Xóa video'), 'Includes Xóa video label');
  assert.ok(source.includes('Xóa tài liệu'), 'Includes Xóa tài liệu label');
  assert.ok(source.includes('btn-choose-doc-file'), 'Includes btn-choose-doc-file button');
  assert.ok(source.includes('btn-delete-preview-video'), 'Includes btn-delete-preview-video');
});

test('instructor.js includes cover photo reminder banner and badges', () => {
  assert.ok(source.includes('Khóa học này chưa có ảnh bìa đại diện'), 'Includes cover photo reminder text');
  assert.ok(source.includes('Chưa có ảnh bìa'), 'Includes badge text in course list');
});
