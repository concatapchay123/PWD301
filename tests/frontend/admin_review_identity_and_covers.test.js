const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadAdmin({ api = {}, elements = {}, extraUI = {} } = {}) {
  const window = { location: { hash: '#/admin/change-requests/review?id=7' } };
  const UI = {
    escapeHtml: value => String(value ?? ''),
    renderMarkdown: value => String(value ?? ''),
    formatDate: String,
    formatDateTime: String,
    showToast() {},
    confirm: async () => true,
    refreshCurrentRoute() {},
    ...extraUI,
  };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8'), {
    window, UI, ApiClient: api, console,
    document: { getElementById: id => elements[id] || null },
  });
  return window;
}

test('course cover review renders the current and proposed cropped images without height clamps', () => {
  const container = { innerHTML: '' };
  const window = loadAdmin();
  window.AdminView.renderChangeRequestReviewDetail(container, {
    id: 7, status: 'APPROVED', target_type: 'COURSE', course_id: 'course-one',
    change_type: 'COURSE_METADATA', course_title: 'Course', original_data: { title: 'Course' },
    proposed_payload: { thumbnail_file_asset_id: 'new-asset' },
    current_cover_url: '/api/files/old-asset/download?disposition=inline',
    proposed_cover_url: '/api/files/new-asset/download?disposition=inline',
  });
  assert.match(container.innerHTML, /src="\/api\/files\/old-asset\/download\?disposition=inline"/);
  assert.match(container.innerHTML, /src="\/api\/files\/new-asset\/download\?disposition=inline"/);
  assert.doesNotMatch(container.innerHTML, /aspect-video max-h-/);
});

test('an explicit proposed cover removal never falls back to the current image', () => {
  const container = { innerHTML: '' };
  const window = loadAdmin();
  window.AdminView.renderChangeRequestReviewDetail(container, {
    id: 7, status: 'APPROVED', target_type: 'COURSE', course_id: 'course-one',
    change_type: 'COURSE_METADATA', course_title: 'Course', original_data: { title: 'Course' },
    proposed_payload: { thumbnail_file_asset_id: null },
    current_cover_url: '/api/files/old-asset/download?disposition=inline',
    proposed_cover_url: null,
  });
  assert.match(container.innerHTML, /Ảnh bìa đề xuất/);
  assert.match(container.innerHTML, /Không có ảnh bìa/);
  assert.equal((container.innerHTML.match(/src="\/api\/files\/old-asset/g) || []).length, 1);
});

test('initial course review preserves the full 16:9 cover and sends its displayed version', async () => {
  const elements = { 'modal-approve-course-btn': {} };
  let reviewed;
  const window = loadAdmin({ elements, api: {
    getAdminCourseDetail: async () => ({
      course_id: 'course-one', course_code: 'C1', title: 'Course', status: 'SUBMITTED_FOR_REVIEW',
      thumbnail_url: '/api/courses/course-one/thumbnail', review_version: 'course-v1', lessons: [],
    }),
    reviewCourse: async (...args) => { reviewed = args; },
  } });
  const container = { innerHTML: '' };
  await window.AdminView.renderCourseReviewPage(container, 'course-one');
  assert.match(container.innerHTML, /src="\/api\/courses\/course-one\/thumbnail"/);
  assert.doesNotMatch(container.innerHTML, /aspect-video max-h-/);
  await elements['modal-approve-course-btn'].onclick();
  assert.deepEqual(Array.from(reviewed), ['course-one', 'approve', 'Đã kiểm tra nội dung và duyệt khóa học', 'course-v1']);
});

test('request approval sends the exact displayed request and version', async () => {
  const elements = { 'diff-approve-btn': {}, 'diff-reject-btn': {} };
  let reviewed;
  const window = loadAdmin({ elements, api: {
    reviewAdminChangeRequest: async (...args) => { reviewed = args; },
  } });
  window.AdminView.renderChangeRequestReviewDetail({ innerHTML: '' }, {
    id: 7, request_id: 7, review_version: 'request-v1', status: 'PENDING', target_type: 'COURSE',
    change_type: 'COURSE_METADATA', original_data: { title: 'Course' }, proposed_payload: { title: 'Updated' },
  });
  await elements['diff-approve-btn'].onclick();
  assert.equal(reviewed[0], 7);
  assert.deepEqual(JSON.parse(JSON.stringify(reviewed[1])), {
    action: 'approve', request_id: 7, review_version: 'request-v1',
  });
});

test('stale approval keeps the displayed review and requires fresh inspection', async () => {
  const elements = { 'diff-approve-btn': {}, 'diff-reject-btn': {} };
  const messages = [];
  let calls = 0;
  const window = loadAdmin({ elements, extraUI: { showToast: message => messages.push(message) }, api: {
    reviewAdminChangeRequest: async () => { calls += 1; throw Object.assign(new Error('Changed'), { status: 409 }); },
  } });
  window.AdminView.renderChangeRequestReviewDetail({ innerHTML: '' }, {
    id: 7, request_id: 7, review_version: 'old-version', status: 'PENDING', target_type: 'COURSE',
    change_type: 'COURSE_METADATA', original_data: {}, proposed_payload: { title: 'Updated' },
  });
  await elements['diff-approve-btn'].onclick();
  assert.equal(calls, 1);
  assert.equal(window.location.hash, '#/admin/change-requests/review?id=7');
  assert.ok(messages.some(message => /tải lại|Tải lại/.test(message)));
  assert.equal(elements['diff-approve-btn'].disabled, true);
  assert.equal(elements['diff-reject-btn'].disabled, true);
});

test('quick aggregate approval sends its displayed identity without dropping sibling queue rows', async () => {
  const button = { dataset: { reqId: '7' }, closest: () => null };
  const tbody = { innerHTML: '', querySelectorAll: selector => selector === '.quick-pass-cr-btn' ? [button] : [] };
  const box = { innerHTML: '', querySelectorAll: () => [], querySelector: () => null };
  const container = { innerHTML: '', querySelector: selector => selector === '#courses-review-box' ? box : null };
  let approved;
  const window = loadAdmin({ elements: { 'change-requests-tbody': tbody }, api: {
    getPendingCourses: async () => ({ courses: [] }),
    getAdminChangeRequests: async () => ({ change_requests: [
      { id: 7, request_id: 7, review_version: 'aggregate-v1', status: 'PENDING', course_id: 'same-course',
        course_title: 'Course', change_type: 'COURSE_VERSION_CHANGESET', proposed_payload: { action: 'COURSE_VERSION_CHANGESET' } },
      { id: 8, request_id: 8, review_version: 'legacy-v1', status: 'PENDING', course_id: 'same-course',
        course_title: 'Course', change_type: 'COURSE_METADATA', proposed_payload: { title: 'Legacy proposal' } },
    ] }),
    approveCourseChangeset: async (...args) => { approved = args; },
  } });
  await window.AdminView.renderTabCoursesReview(container);
  assert.ok(tbody.innerHTML.includes('data-req-id="7"'));
  assert.ok(tbody.innerHTML.includes('data-req-id="8"'));
  await button.onclick({ stopPropagation() {} });
  assert.deepEqual(Array.from(approved), [7, 'Phê duyệt đợt cập nhật giáo trình.', 'aggregate-v1']);
  assert.ok(tbody.innerHTML.includes('data-req-id="8"'));
});

test('categorized review shows both 16:9 covers and an explicit proposed removal', () => {
  const context = { window: {}, document: {}, console };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8'), context);
  const html = context.window.UI.renderCategorizedDiffHtml({
    governance_rules: {
      is_changed: true,
      current_cover_url: '/api/files/current/download?disposition=inline',
      proposed_cover_url: '/api/files/proposed/download?disposition=inline',
    },
  });
  assert.ok(html.includes('src="/api/files/current/download?disposition=inline"'));
  assert.ok(html.includes('src="/api/files/proposed/download?disposition=inline"'));
  assert.equal((html.match(/aspect-video/g) || []).length, 2);
  const removalHtml = context.window.UI.renderCategorizedDiffHtml({
    governance_rules: { is_changed: true, current_cover_url: '/current.jpg', proposed_cover_url: null },
  });
  assert.ok(removalHtml.includes('Ảnh bìa đề xuất'));
  assert.ok(removalHtml.includes('Không có ảnh bìa'));
});

test('governance review displays canonical proposed thresholds including zero and false', () => {
  const context = { window: {}, document: {}, console };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8'), context);
  const html = context.window.UI.renderCategorizedDiffHtml({ total_changes_count: 1, governance_rules: {
    is_changed: true,
    current: { minimum_grade_score: 5, minimum_progress_percent: 80, require_all_required_lessons: true, require_required_assessments: true },
    proposed: { minimum_grade_score: 0, minimum_progress_percent: 0, require_all_required_lessons: false, require_required_assessments: false },
  } });
  assert.match(html, /5\/10[^]*0\/10/);
  assert.match(html, /80%[^]*0%/);
  assert.match(html, /Có[^]*Không/);
});

test('processed review history fetches explicit statuses while pending badges remain accurate', async () => {
  const buttons = ['PENDING', 'REJECTED', 'APPLIED'].map(status => ({ dataset: { status } }));
  const tbody = { innerHTML: '', querySelectorAll: () => [] };
  const box = { innerHTML: '', querySelectorAll: selector => selector === '.cr-filter-btn' ? buttons : [] };
  const container = { innerHTML: '', querySelector: selector => selector === '#courses-review-box' ? box : null };
  const requests = [], badges = [];
  const window = loadAdmin({ elements: { 'change-requests-tbody': tbody }, api: {
    getPendingCourses: async () => ({ courses: [] }),
    getAdminChangeRequests: async status => {
      requests.push(status);
      return { change_requests: [{ id: status === 'ALL' ? 7 : 8, status: status === 'ALL' ? 'PENDING' : status,
        course_title: 'Course', target_title: status === 'ALL' ? 'Pending proposal' : 'Processed proposal',
        change_type: 'COURSE_METADATA', proposed_payload: {}, review_reason: status === 'REJECTED' ? 'Please revise objectives' : null }] };
    },
  } });
  window.app = { updateAdminNavBadges: value => badges.push(value.courses) };
  await window.AdminView.renderTabCoursesReview(container);
  assert.ok(box.innerHTML.includes('Lịch Sử Xét Duyệt'));
  await buttons[1].onclick();
  assert.deepEqual(requests, ['ALL', 'REJECTED']);
  assert.ok(tbody.innerHTML.includes('Please revise objectives'));
  assert.ok(tbody.innerHTML.includes('Từ chối'));
  assert.ok(!tbody.innerHTML.includes('quick-pass-cr-btn'));
  await buttons[2].onclick();
  assert.ok(tbody.innerHTML.includes('Đã áp dụng'));
  assert.ok(!tbody.innerHTML.includes('Từ chối'));
  await buttons[0].onclick();
  assert.ok(tbody.innerHTML.includes('Pending proposal'));
  assert.ok(badges.every(count => count === 1));
});

test('categorized diff renders question changes, standalone files, prerequisites, and metadata', () => {
  const context = { window: {}, document: {}, console };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8'), context);
  const diff = {
    total_changes_count: 4,
    question_changes: [
      { change_type: 'ADDED', question_type: 'MULTIPLE_CHOICE', content: 'What is 2 + 2?', explanation: 'Basic math' },
    ],
    file_changes: [
      { change_type: 'ADDED', file_name: 'Reference_Guide.pdf', file_size_bytes: 20480, scan_status: 'CLEAN' },
    ],
    prerequisite_changes: [
      { change_type: 'ADDED', course_code: 'CS101', title: 'Intro to CS' },
    ],
    metadata_changes: [
      { field: 'description', old_value: 'Old desc', new_value: 'New desc' },
    ],
    governance_rules: { is_changed: true },
  };
  const html = context.window.UI.renderCategorizedDiffHtml(diff);
  assert.ok(html.includes('Ngân hàng Câu hỏi'));
  assert.ok(html.includes('What is 2 + 2?'));
  assert.ok(html.includes('Tài liệu &amp; Tệp đính kèm') || html.includes('Tài liệu & Tệp đính kèm'));
  assert.ok(html.includes('Reference_Guide.pdf'));
  assert.ok(html.includes('Môn học Tiên quyết'));
  assert.ok(html.includes('[CS101]'));
  assert.ok(html.includes('Intro to CS'));
  assert.ok(html.includes('Thông tin Khóa học'));
  assert.ok(html.includes('New desc'));
  assert.ok(!html.includes('Chưa phát hiện thay đổi nào so với giáo trình hiện tại'));
});

test('categorized diff with only question changes renders without false empty state', () => {
  const context = { window: {}, document: {}, console };
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8'), context);
  const diff = {
    question_changes: [
      { change_type: 'MODIFIED', question_type: 'ESSAY', content: 'Explain recursion' },
    ],
  };
  const html = context.window.UI.renderCategorizedDiffHtml(diff);
  assert.ok(html.includes('Ngân hàng Câu hỏi'));
  assert.ok(html.includes('Explain recursion'));
  assert.ok(!html.includes('Chưa phát hiện thay đổi nào so với giáo trình hiện tại'));
});

