const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
const source = fs.readFileSync(filename, 'utf8');

test('studio navigator shows sibling lessons and marks the current lesson', () => {
  const window = {};
  vm.runInNewContext(source, { window, document: {}, UI: { escapeHtml: value => String(value).replaceAll('<', '&lt;') } }, { filename });
  const unit = {
    learning_unit_id: 'unit-1', title: 'Bài học 1', lesson_count: 2,
    lessons: [
      { lesson_id: 'lesson-1', title: 'Mở đầu', position: 1 },
      { lesson_id: 'lesson-2', title: '<Nội dung>', position: 2 },
    ],
  };
  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'lesson-2');
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-1\/edit"/);
  assert.match(html, /aria-current="page"/);
  assert.match(html, /&lt;Nội dung>/);
  assert.match(html, /data-learning-unit-id="unit-1"/);
  assert.match(html, /2\/10 Lesson/);
});

test('studio navigator hides add action when the parent has ten lessons', () => {
  const window = {};
  vm.runInNewContext(source, { window, document: {}, UI: { escapeHtml: value => String(value) } }, { filename });
  const unit = {
    learning_unit_id: 'unit-1', title: 'Đầy', lesson_count: 10,
    lessons: Array.from({ length: 10 }, (_, index) => ({ lesson_id: `lesson-${index}`, title: `Lesson ${index + 1}`, position: index + 1 })),
  };
  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'lesson-0');
  assert.doesNotMatch(html, /Thêm Lesson/);
  assert.match(html, /10\/10 Lesson/);
});
