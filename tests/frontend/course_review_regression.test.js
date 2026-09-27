const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('submitted course inspection replaces loading and exposes approval', async () => {
  const modalCalls = [];
  let closed = 0;
  const approveButton = {};
  const elements = { 'modal-approve-course-btn': approveButton };
  const window = {};
  const UI = {
    openModal: options => { modalCalls.push(options); return { isConnected: true }; },
    closeModal: () => { closed += 1; },
    confirm: async () => true,
    showToast: () => {},
    escapeHtml: value => String(value ?? ''),
    renderMarkdown: value => value,
    refreshCurrentRoute: () => {},
  };
  let reviewed = null;
  const ApiClient = {
    getAdminCourseDetail: async () => ({
      course_id: 'course-1', course_code: 'C1', title: 'Course',
      status: 'SUBMITTED_FOR_REVIEW', lessons: [],
    }),
    reviewCourse: async (...args) => { reviewed = args; },
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, ApiClient, console,
    document: { getElementById: id => elements[id] || null },
  }, { filename });

  await window.AdminView.openCourseInspectionModal('course-1');
  assert.equal(modalCalls.length, 2);
  assert.equal(closed, 1, 'loading dialog must be removed before detail opens');
  assert.equal(typeof approveButton.onclick, 'function');
  await approveButton.onclick();
  assert.equal(reviewed?.[1], 'approve');
});
