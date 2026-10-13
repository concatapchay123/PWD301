const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

function load(file, additions = {}) {
  const window = { location: { hash: '#/admin' } };
  vm.runInNewContext(fs.readFileSync(`frontend/assets/js/${file}`, 'utf8'), { window, console, ...additions });
  return window;
}

for (const status of ['ACTIVE', 'SUSPENDED']) {
  test(`user row connects ${status} account state action to its existing workflow`, async () => {
    const button = { dataset: { userId: 'owned-user', userName: 'Owned user' } };
    const selector = status === 'SUSPENDED' ? '.unsuspend-user-btn' : '.suspend-user-btn';
    const tbody = { innerHTML: '', querySelectorAll: value => value === selector ? [button] : [] };
    const elements = { 'users-box': {}, 'admin-users-tbody': tbody, 'btn-sync-users': {}, 'btn-sync-optimistic': {} };
    const window = load('views/admin.js', {
      document: { getElementById: id => elements[id] || null },
      UI: { escapeHtml: value => String(value || ''), formatDate: () => '' },
      ApiClient: { getAdminUsers: async () => ({ users: [{ user_id: 'owned-user', display_name: 'Owned user', email: 'owned@example.invalid', roles: ['STUDENT'], status }] }) },
    });
    window.app = { currentUser: { is_primary_admin: true } };
    let target;
    window.AdminView.openSuspendModal = (...args) => { target = ['suspend', ...args]; };
    window.AdminView.unsuspendUser = async (...args) => { target = ['unsuspend', ...args]; };
    assert.equal(await window.AdminView.renderTabUsers({}), true);
    assert.ok(tbody.innerHTML.includes(selector.slice(1)));
    await button.onclick();
    assert.deepEqual(target, [status === 'SUSPENDED' ? 'unsuspend' : 'suspend', 'owned-user', 'Owned user']);
  });
}

for (const blocked of ['delegated', 'primary-target', 'self']) {
  test(`user row disables suspension for ${blocked}`, async () => {
    const button = { dataset: { userId: 'owned-user', userName: 'Owned user' } };
    const tbody = { innerHTML: '', querySelectorAll: value => value === '.suspend-user-btn' ? [button] : [] };
    const elements = { 'users-box': {}, 'admin-users-tbody': tbody, 'btn-sync-users': {}, 'btn-sync-optimistic': {} };
    const window = load('views/admin.js', {
      document: { getElementById: id => elements[id] || null },
      UI: { escapeHtml: value => String(value || ''), formatDate: () => '', showToast() {} },
      ApiClient: { getAdminUsers: async () => ({ users: [{ user_id: 'owned-user', email: 'owned@example.invalid', roles: ['ADMIN'], status: 'ACTIVE', is_primary_admin: blocked === 'primary-target' }] }) },
    });
    window.app = { currentUser: { id: blocked === 'self' ? 'owned-user' : 'actor', is_primary_admin: blocked !== 'delegated' } };
    let calls = 0;
    window.AdminView.openSuspendModal = () => { calls++; };
    await window.AdminView.renderTabUsers({});
    assert.match(tbody.innerHTML.match(/<button[^>]*suspend-user-btn[^>]*>/)[0], /disabled/);
    await button.onclick();
    assert.equal(calls, 0);
  });
}

test('suspension forwards explicit confirmation phrase', async () => {
  const { ApiClient } = load('api.js');
  let sent;
  ApiClient.request = async (_url, options) => { sent = options.body; };
  await ApiClient.suspendUser('owner', 'Reason', 'Password', 'CONFIRM_USER_SUSPEND');
  assert.equal(sent.confirmation_phrase, 'CONFIRM_USER_SUSPEND');
});

test('suspension modal blocks missing phrase then sends exact phrase', async () => {
  const elements = {
    'confirm-suspend-btn': {}, 'suspend-reason': { value: 'Detailed reason' },
    'suspend-password': { value: 'Password' }, 'suspend-confirm-phrase': { value: '' },
  };
  const calls = [];
  const { AdminView } = load('views/admin.js', {
    document: { getElementById: id => elements[id] || null },
    UI: { escapeHtml: x => x, openModal() {}, closeModal() {}, showToast() {}, refreshCurrentRoute() {} },
    ApiClient: { suspendUser: async (...args) => calls.push(args) },
  });
  AdminView.openSuspendModal('owner', 'Name');
  await elements['confirm-suspend-btn'].onclick();
  assert.equal(calls.length, 0);
  elements['suspend-confirm-phrase'].value = 'CONFIRM_USER_SUSPEND';
  await elements['confirm-suspend-btn'].onclick();
  assert.equal(calls[0][3], 'CONFIRM_USER_SUSPEND');
});

test('review list network failure preserves prior rows and presents unavailable state', async () => {
  const container = { innerHTML: '<div>Prior course row</div>', querySelector: selector => selector === '#courses-review-box' ? {} : null,
    insertAdjacentHTML(_position, markup) { this.notice = markup; } };
  const { AdminView } = load('views/admin.js', {
    document: { getElementById: () => null },
    UI: { escapeHtml: x => x },
    ApiClient: { getPendingCourses: async () => { throw new Error('network down'); }, getAdminChangeRequests: async () => ({ change_requests: [] }) },
  });
  await AdminView.renderTabCoursesReview(container);
  assert.match(container.innerHTML, /Prior course row/);
  assert.match(container.notice || container.innerHTML, /Không tải được/);
  assert.equal(container.innerHTML, '<div>Prior course row</div>');
});

test('user refresh cannot report success when the authoritative read failed', async () => {
  const toasts = [];
  const { AdminView } = load('views/admin.js', { UI: { showToast: (...args) => toasts.push(args) } });
  AdminView.renderTabUsers = async () => false;
  assert.equal(await AdminView.refreshUsers({}), false);
  assert.equal(toasts.some(([, status]) => status === 'success'), false);
  AdminView.renderTabUsers = async () => true;
  assert.equal(await AdminView.refreshUsers({}), true);
  assert.equal(toasts.some(([, status]) => status === 'success'), true);
});

test('recovered review queue removes the stale unavailable notice', async () => {
  let noticeRemoved = false;
  const box = { innerHTML: '', querySelectorAll: () => [] };
  const container = {
    innerHTML: '',
    querySelector: selector => selector === '#courses-review-box' ? box
      : selector === '#admin-review-load-error' ? { remove() { noticeRemoved = true; } } : null,
  };
  const { AdminView } = load('views/admin.js', {
    document: { getElementById: () => null },
    UI: { escapeHtml: x => x },
    ApiClient: { getPendingCourses: async () => ({ courses: [] }), getAdminChangeRequests: async () => ({ change_requests: [] }) },
  });
  await AdminView.renderTabCoursesReview(container);
  assert.match(box.innerHTML, /Khóa học chờ duyệt/);
  assert.equal(noticeRemoved, true);
});

test('exact review detail fetch does not rely on active queue membership', async () => {
  const requested = [];
  const { AdminView } = load('views/admin.js', {
    UI: { escapeHtml: x => x },
    ApiClient: { getAdminChangeRequest: async id => { requested.push(id); return { change_requests: [{ id, status: 'APPROVED' }] }; } },
  });
  let displayed;
  AdminView.renderChangeRequestReviewDetail = (_container, request) => { displayed = request; };
  await AdminView.renderChangeRequestReviewPage({ innerHTML: '' }, 'older-request');
  assert.equal(requested[0], 'older-request');
  assert.equal(displayed.status, 'APPROVED');
});
