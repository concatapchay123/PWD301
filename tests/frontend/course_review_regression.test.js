const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('change request review uses a full page with before and after content', async () => {
  const elements = { 'diff-approve-btn': {}, 'diff-reject-btn': {} };
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/change-requests/review?id=7' } };
  let reviewed = null;
  const UI = {
    openModal: () => { throw new Error('Review must not open a modal'); },
    escapeHtml: value => String(value ?? ''),
    renderMarkdown: value => String(value ?? ''),
    showToast: () => {},
    confirm: async () => true,
    refreshCurrentRoute: () => {},
  };
  const ApiClient = {
    getAdminChangeRequests: async () => ({ change_requests: [{
      id: 7, status: 'PENDING', target_type: 'LESSON', course_code: 'C1',
      course_title: 'Course', target_title: 'Lesson', requested_by_name: 'Teacher',
      original_data: { title: 'Before', markdown_content: 'Old content' },
      proposed_payload: { title: 'After', markdown_content: 'New content' },
    }] }),
    reviewAdminChangeRequest: async (...args) => { reviewed = args; },
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, ApiClient, console,
    document: { getElementById: id => elements[id] || null },
  }, { filename });
  await window.AdminView.renderChangeRequestReviewPage(container, '7');
  assert.match(container.innerHTML, /Old content/);
  assert.match(container.innerHTML, /New content/);
  assert.equal(typeof elements['diff-approve-btn'].onclick, 'function');
  await elements['diff-approve-btn'].onclick();
  assert.equal(reviewed[0], 7);
  assert.equal(window.location.hash, '#/admin/governance?tab=courses');
});

test('pending Admin queue offers inspection and confirmed quick approval', async () => {
  const tbody = { innerHTML: '', querySelectorAll: () => [] };
  const box = {
    innerHTML: '',
    querySelector: selector => selector === '#change-requests-tbody' ? tbody : null,
    querySelectorAll: () => [],
  };
  const UI = {
    escapeHtml: value => String(value ?? ''),
    formatDate: value => String(value ?? ''),
    formatDateTime: value => String(value ?? ''),
  };
  const ApiClient = {
    getPendingCourses: async () => ({ courses: [] }),
    getAdminChangeRequests: async () => ({ change_requests: [{
      id: 7, status: 'PENDING', change_type: 'LESSON_CONTENT',
      target_type: 'LESSON', course_code: 'C1', course_title: 'Course',
      target_title: 'Lesson', requested_by_name: 'Teacher',
      proposed_payload: { title: 'Changed Lesson' }, created_at: 'today',
    }] }),
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  const window = {};
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, ApiClient, console,
    document: { getElementById: id => id === 'courses-review-box' ? box : id === 'change-requests-tbody' ? tbody : null },
  }, { filename });
  await window.AdminView.renderTabCoursesReview({ innerHTML: '', querySelector: () => box });
  assert.match(tbody.innerHTML, />Xem</);
  assert.match(tbody.innerHTML, /quick-pass-cr-btn/);
  assert.match(tbody.innerHTML, />Duyệt</);
  assert.doesNotMatch(tbody.innerHTML, /approve-cr-btn|reject-cr-btn/);
});

test('course queue renders into its route container while the previous route still exists', async () => {
  const oldBox = { innerHTML: 'Previous route', querySelector: () => null, querySelectorAll: () => [] };
  const newBox = { innerHTML: '', querySelector: () => null, querySelectorAll: () => [] };
  const container = { innerHTML: '', querySelector: () => newBox };
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
    window, console, UI: { escapeHtml: String, formatDate: String, formatDateTime: String },
    ApiClient: { getPendingCourses: async () => ({ courses: [] }), getAdminChangeRequests: async () => ({ change_requests: [] }) },
    document: { getElementById: id => id === 'courses-review-box' ? oldBox : null },
  });
  await window.AdminView.renderTabCoursesReview(container);
  assert.match(newBox.innerHTML, /Khóa học chờ duyệt/);
  assert.equal(oldBox.innerHTML, 'Previous route');
});

test('learning unit review compares the unit title instead of course metadata', () => {
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/change-requests/review?id=8' } };
  const UI = { escapeHtml: value => String(value ?? ''), renderMarkdown: value => String(value ?? '') };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, console, document: { getElementById: () => null },
  }, { filename });
  window.AdminView.renderChangeRequestReviewDetail(container, {
    id: 8, status: 'APPROVED', target_type: 'COURSE', change_type: 'LESSON_STRUCTURE',
    course_title: 'Khóa học C1', target_title: 'Bài học cũ',
    original_data: { title: 'Bài học cũ' },
    proposed_payload: { action: 'UPDATE_LEARNING_UNIT', title: 'Bài học mới' },
  });
  assert.match(container.innerHTML, /Tên Bài học hiện tại/);
  assert.match(container.innerHTML, /Bài học cũ/);
  assert.match(container.innerHTML, /Bài học mới/);
  assert.doesNotMatch(container.innerHTML, /Tên khóa học/);
});

test('lesson review shows status changes and an explicitly cleared summary', () => {
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/change-requests/review?id=9' } };
  const UI = { escapeHtml: value => String(value ?? ''), renderMarkdown: value => String(value ?? '') };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, console, document: { getElementById: () => null },
  }, { filename });
  window.AdminView.renderChangeRequestReviewDetail(container, {
    id: 9, status: 'APPROVED', target_type: 'LESSON', course_title: 'Course',
    original_data: {
      title: 'Lesson', summary: 'Old summary', status: 'PUBLISHED',
      minimum_completion_seconds: 30, viewed_fraction_required: 0.8,
    },
    proposed_payload: {
      summary: '', status: 'HIDDEN',
      minimum_completion_seconds: 90, viewed_fraction_required: 0.9,
    },
  });
  assert.match(container.innerHTML, /PUBLISHED/);
  assert.match(container.innerHTML, /HIDDEN/);
  assert.equal((container.innerHTML.match(/Old summary/g) || []).length, 1);
  assert.match(container.innerHTML, /\(Trống\)/);
  assert.match(container.innerHTML, /30 giây/);
  assert.match(container.innerHTML, /90 giây/);
  assert.match(container.innerHTML, /80%/);
  assert.match(container.innerHTML, /90%/);
});

test('resource review shows the files before and after approval', () => {
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/change-requests/review?id=10' } };
  const UI = { escapeHtml: value => String(value ?? ''), renderMarkdown: value => String(value ?? '') };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, console, document: { getElementById: () => null },
  }, { filename });
  window.AdminView.renderChangeRequestReviewDetail(container, {
    id: 10, status: 'APPROVED', target_type: 'LESSON', course_title: 'Course',
    original_data: { title: 'Lesson', resources: [{ resource_id: 1, title: 'old.pdf' }] },
    proposed_payload: { action: 'RESOURCE_CHANGES', changes: [
      { action: 'ATTACH', asset_id: 2, title: 'new.pdf' },
      { action: 'DETACH', resource_id: 1, title: 'old.pdf' },
    ] },
  });
  assert.match(container.innerHTML, /Tài liệu hiện tại/);
  assert.match(container.innerHTML, /Tài liệu sau khi duyệt/);
  assert.match(container.innerHTML, /old\.pdf/);
  assert.match(container.innerHTML, /new\.pdf/);
});

test('course review page exposes rejection feedback and returns to the queue', async () => {
  const elements = { 'modal-reject-course-btn': {} };
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/courses/review?id=course-1' } };
  let promptOptions = null;
  const UI = {
    openModal: () => { throw new Error('Course review should use the page'); },
    prompt: async (...args) => {
      promptOptions = args;
      return 'Cần bổ sung mục tiêu học tập';
    },
    showToast: () => {},
    escapeHtml: value => String(value ?? ''),
    renderMarkdown: value => value,
  };
  let reviewed = null;
  const ApiClient = {
    getAdminCourseDetail: async () => ({
      course_id: 'course-1', course_code: 'C1', title: 'Course',
      status: 'SUBMITTED_FOR_REVIEW', lessons: [
        { lesson_id: 'lesson-1', title: 'First lesson', status: 'DRAFT', markdown_content: '# Full lesson text', resources: [] },
      ],
    }),
    reviewCourse: async (...args) => { reviewed = args; },
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, ApiClient, console,
    document: { getElementById: id => elements[id] || null },
  }, { filename });

  await window.AdminView.renderCourseReviewPage(container, 'course-1');
  assert.match(container.innerHTML, /Full lesson text/);
  assert.equal(typeof elements['modal-reject-course-btn'].onclick, 'function');
  await elements['modal-reject-course-btn'].onclick();
  assert.equal(promptOptions?.[5], 'Gửi Yêu Cầu');
  assert.equal(reviewed?.[1], 'reject');
  assert.equal(reviewed?.[2], 'Cần bổ sung mục tiêu học tập');
  assert.equal(window.location.hash, '#/admin/governance?tab=courses');
});

test('course review opens as a full page with approval after inspection', async () => {
  const elements = { 'modal-approve-course-btn': {} };
  const container = { innerHTML: '' };
  const window = { location: { hash: '#/admin/courses/review?id=course-1' } };
  const UI = {
    openModal: () => { throw new Error('Course review should use the page'); },
    confirm: async () => true,
    showToast: () => {},
    escapeHtml: value => String(value ?? ''),
    renderMarkdown: value => value,
  };
  const ApiClient = {
    getAdminCourseDetail: async () => ({
      course_id: 'course-1', course_code: 'C1', title: 'Course',
      status: 'SUBMITTED_FOR_REVIEW', lessons: [
        { lesson_id: 'lesson-1', title: 'First lesson', status: 'DRAFT', markdown_content: '# Full lesson text', resources: [] },
      ],
    }),
    reviewCourse: async () => ({}),
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/admin.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, UI, ApiClient, console,
    document: { getElementById: id => elements[id] || null },
  }, { filename });

  await window.AdminView.renderCourseReviewPage(container, 'course-1');
  assert.match(container.innerHTML, /Course/);
  assert.match(container.innerHTML, /Duyệt Khóa Học/);
  assert.match(container.innerHTML, /Full lesson text/);
  assert.equal(typeof elements['modal-approve-course-btn'].onclick, 'function');
  await elements['modal-approve-course-btn'].onclick();
  assert.equal(window.location.hash, '#/admin/governance?tab=courses');
});

test('change approval cancellation and server errors preserve the inspected request', async () => {
  const elements = { 'diff-approve-btn': {}, 'diff-reject-btn': {} };
  const window = { location: { hash: '#/admin/change-requests/review?id=7' } };
  let confirmed = false;
  let writes = 0;
  const errors = [];
  const UI = { escapeHtml: String, renderMarkdown: String, confirm: async () => confirmed,
    showToast: message => errors.push(message), refreshCurrentRoute: () => { throw new Error('Must not refresh on failure'); } };
  const ApiClient = { reviewAdminChangeRequest: async () => { writes++; throw new Error('Request already resolved'); } };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
    window, UI, ApiClient, document: { getElementById: id => elements[id] || null }, console,
  });
  window.AdminView.renderChangeRequestReviewDetail({ innerHTML: '' }, {
    id: 7, target_type: 'LESSON', status: 'PENDING', original_data: {}, proposed_payload: { title: 'New' },
  });
  await elements['diff-approve-btn'].onclick();
  assert.equal(writes, 0);
  confirmed = true;
  await elements['diff-approve-btn'].onclick();
  assert.equal(writes, 1);
  assert.equal(window.location.hash, '#/admin/change-requests/review?id=7');
  assert.match(errors[0], /Request already resolved/);
});
