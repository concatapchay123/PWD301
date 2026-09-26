const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadView(relativePath, globalName, globals = {}) {
  const filename = path.resolve(__dirname, relativePath);
  const window = globals.window || {};
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window,
    document: {},
    console,
    URLSearchParams,
    ...globals,
  }, { filename });
  return window[globalName];
}

test('audit pagination reports bounded page state from API totals', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.deepEqual(
    { ...AdminView.getAuditPageState(2, 50, 130) },
    { page: 2, perPage: 50, total: 130, pageCount: 3, firstItem: 51, lastItem: 100, hasPrevious: true, hasNext: true },
  );
  assert.deepEqual(
    { ...AdminView.getAuditPageState(99, 50, 0) },
    { page: 1, perPage: 50, total: 0, pageCount: 1, firstItem: 0, lastItem: 0, hasPrevious: false, hasNext: false },
  );
});

test('audit action filter matches log categories consistently after each page fetch', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.equal(AdminView.matchesAuditActionFilter({ action: 'USER_ROLE_ASSIGN' }, 'ROLE'), true);
  assert.equal(AdminView.matchesAuditActionFilter({ action: 'COURSE_STATUS_CHANGE' }, 'COURSE'), true);
  assert.equal(AdminView.matchesAuditActionFilter({ action: 'DATABASE_RESTORE' }, 'DATABASE'), true);
  assert.equal(AdminView.matchesAuditActionFilter({ action: 'USER_SUSPEND' }, 'COURSE'), false);
});

test('audit page requests keep page, size, and selected action filter together', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.deepEqual(
    { ...AdminView.getAuditRequestParams(3, 50, 'COURSE_STATUS_CHANGE') },
    { page: 3, per_page: 50, action: 'COURSE_STATUS_CHANGE' },
  );
  assert.deepEqual(
    { ...AdminView.getAuditRequestParams(1, 50, 'ALL') },
    { page: 1, per_page: 50 },
  );
});

test('lesson preview delegates Markdown rendering to the existing safe UI renderer', () => {
  let renderedInput;
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView', {
    UI: { renderMarkdown: value => { renderedInput = value; return '<p>safe preview</p>'; } },
  });

  assert.equal(AdminView.renderLessonMarkdown('## Lesson'), '<p>safe preview</p>');
  assert.equal(renderedInput, '## Lesson');
});

test('review notifications resolve to the matching approval tab and queue', () => {
  const AppRouter = loadView('../../frontend/assets/js/router.js', 'AppRouter');

  assert.equal(
    AppRouter.getNotificationReviewTarget({ category: 'COURSE', action_url: '#/admin/governance?tab=courses' }),
    '#/admin/governance?tab=courses&queue=courses',
  );
  assert.equal(
    AppRouter.getNotificationReviewTarget({ category: 'SYSTEM', action_url: '#/admin/governance?tab=applications' }),
    '#/admin/governance?tab=applications',
  );
});

test('clicking an admin review notification opens its queue directly', async () => {
  const window = { location: { hash: '#/student/dashboard' } };
  const AppRouter = loadView('../../frontend/assets/js/router.js', 'AppRouter', { window });
  let openedModal = false;
  const router = Object.create(AppRouter.prototype);
  router.notificationsCache = {
    items: [{ id: 'notification-1', category: 'COURSE', is_read: true, action_url: '#/admin/governance?tab=courses' }],
  };
  router.closeNotificationsDropdown = () => {};
  router.openNotificationModal = () => { openedModal = true; };
  router.handleRoute = () => {};

  await router.handleNotificationItemClick('notification-1', '#/admin/governance?tab=courses');

  assert.equal(window.location.hash, '#/admin/governance?tab=courses&queue=courses');
  assert.equal(openedModal, false);
});

test('primary-admin summary omits subordinate queues while assigned roles retain their own counts', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');
  const counts = { courses: 4, changes: 3, applications: 6, assignments: 2 };

  assert.deepEqual({ ...AdminView.getQueueSummary('ADMIN_PRIMARY', counts) }, { courses: 0, changes: 0, applications: 0, assignments: 0 });
  assert.deepEqual({ ...AdminView.getQueueSummary('ADMIN_COURSE_REVIEW', counts) }, { courses: 4, changes: 3, applications: 0, assignments: 0 });
  assert.deepEqual({ ...AdminView.getQueueSummary('ADMIN_INSTRUCTOR_REVIEW', counts) }, { courses: 0, changes: 0, applications: 6, assignments: 0 });
});

test('role assignment choices exclude ADMIN_PRIMARY and retain existing primary status', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.deepEqual([...AdminView.getAssignableAdminSubRoles()], [
    'ADMIN_COURSE_REVIEW',
    'ADMIN_INSTRUCTOR_REVIEW',
    'ADMIN_TEACHING_ASSIGNMENT',
    'ADMIN_SYSTEM_MONITORING',
  ]);
  assert.deepEqual(
    { ...AdminView.getAdminSubRoleSelectionState(['ADMIN'], 'ADMIN_PRIMARY') },
    { isExistingPrimary: true, selectedSubRole: null },
  );
});

test('audit action options are limited to each review admin role', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.deepEqual([...AdminView.getAuditActionsForRole('ADMIN_INSTRUCTOR_REVIEW')], [
    'INSTRUCTOR_APPLICATION_SUBMITTED',
    'INSTRUCTOR_APPLICATION_CANCELLED',
    'INSTRUCTOR_APPLICATION_APPROVED',
    'INSTRUCTOR_APPLICATION_REJECTED',
  ]);
  assert.equal(AdminView.getAuditActionsForRole('ADMIN_COURSE_REVIEW').every(action => /^(COURSE_|LESSON_|SUBJECT_)/.test(action)), true);
});

test('audit action filters use canonical actions emitted by the backend', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');
  const actions = AdminView.getAuditActionsForRole('ADMIN_PRIMARY');

  for (const action of [
    'USER_ROLE_ASSIGNED',
    'USER_ROLES_UPDATED',
    'USER_ROLE_REVOKED',
    'USER_REVOKE_SESSIONS',
    'LESSON_TRASHED',
    'DATABASE_BACKUP_CREATED',
    'DATABASE_RESTORE_COMPLETED',
    'ASSESSMENT_PUBLISHED',
  ]) {
    assert.equal(actions.includes(action), true, `${action} should be filterable`);
  }
  for (const action of ['USER_ROLE_ASSIGN', 'SESSIONS_REVOKED', 'LESSON_DELETED', 'ASSESSMENT_PUBLISH']) {
    assert.equal(actions.includes(action), false, `${action} is not a canonical emitted action`);
  }
});
