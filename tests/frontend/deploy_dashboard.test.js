const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('empty student dashboard hides course hero until enrollment is confirmed', async () => {
  const window = {};
  const document = { getElementById: () => null };
  const ApiClient = { getStudentDashboard: async () => ({ enrollments: [], upcoming_assessments: [], recent_results: [] }) };
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/student.js', 'utf8'), { window, document, ApiClient, console });
  const container = { innerHTML: '' };
  await window.StudentView.renderDashboard(container);
  assert.match(container.innerHTML, /class="[^"]*hidden[^"]*" id="dashboard-hero-continue-card"/);
  assert.doesNotMatch(container.innerHTML, /Còn khoảng 45 phút học|Bạn có bài kiểm tra sắp tới/);
});
