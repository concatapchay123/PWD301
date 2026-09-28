const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('exam method screen keeps file rules behind optional help', () => {
  const window = {
    InstructorView: {},
    ExamStore: {
      getDraft: () => ({}),
      hasDraft: () => false,
    },
    location: { hash: '#/instructor/exams' },
  };
  const context = {
    window,
    document: { getElementById: () => null },
    ApiClient: { getInstructorCourses: async () => ({ courses: [] }) },
    UI: { escapeHtml: value => String(value ?? '') },
    console,
    URLSearchParams,
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), context, { filename });
  window.InstructorView.renderExamWorkflowHeader = () => '';
  window.InstructorView.bindExamWorkflowHeaderEvents = () => {};

  const container = { innerHTML: '', querySelectorAll: () => [] };
  window.InstructorView.renderExamsHub(container);

  assert.match(container.innerHTML, /<details[^>]*>\s*<summary[^>]*>Hướng dẫn định dạng tệp/);
  assert.match(container.innerHTML, /data-exam-method="interactive"/);
  assert.match(container.innerHTML, /id="btn-hub-quick-sample"/);
  assert.doesNotMatch(container.innerHTML, /Công nghệ Parser thông minh/);
});
