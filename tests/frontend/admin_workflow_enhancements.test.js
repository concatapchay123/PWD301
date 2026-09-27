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

test('course review actions are available only for the canonical submitted state', () => {
  const AdminView = loadView('../../frontend/assets/js/views/admin.js', 'AdminView');

  assert.equal(AdminView.canReviewCourse({ status: 'SUBMITTED_FOR_REVIEW' }), true);
  assert.equal(AdminView.canReviewCourse({ status: 'PENDING' }), false);
  assert.equal(AdminView.canReviewCourse({ status: 'APPROVED' }), false);
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

test('operations view keeps service health without requesting or polling hardware telemetry', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8');
  const renderStart = source.indexOf('static async renderOperations(container)');
  const renderEnd = source.indexOf('static openCreateBackupModal(', renderStart);
  const operationsSource = source.slice(renderStart, renderEnd);

  assert.notEqual(renderStart, -1);
  assert.notEqual(renderEnd, -1);
  assert.doesNotMatch(source, /getAdminTelemetry|pollTelemetry|telem-(?:cpu|ram|disk|node|net)|refresh-telemetry/i);
  assert.doesNotMatch(operationsSource, /getAdminTelemetry|pollTelemetry|telem-(?:cpu|ram|disk|node|net)|refresh-telemetry/i);
  assert.match(operationsSource, /getAdminHealth\(\)/);
  assert.match(operationsSource, /loadHealthMatrix/);
});

test('shared dialogs and shell overlays use blur while toast stays outside the backdrop system', () => {
  const uiSource = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8');
  const shellSource = fs.readFileSync(path.resolve(__dirname, '../../frontend/index.html'), 'utf8');

  assert.match(uiSource, /modalLayer\.className\s*=\s*['"][^'"]*backdrop-blur-(?:sm|md|lg)/);
  assert.match(uiSource, /confirmLayer\.className\s*=\s*['"][^'"]*backdrop-blur-(?:sm|md|lg)/);
  assert.match(uiSource, /backdrop\.className\s*=\s*['"][^'"]*backdrop-blur-(?:sm|md|lg)/);
  assert.match(shellSource, /id="mobile-nav-backdrop"[^>]*backdrop-blur-(?:sm|md|lg)/);
  assert.match(shellSource, /id="app-drawer-backdrop"[^>]*backdrop-blur-(?:sm|md|lg)/);
  assert.doesNotMatch(uiSource.match(/static showToast\([\s\S]*?static dismissToast\(/)?.[0] || '', /backdrop-blur/);
});

test('interactive SPA modules do not invoke native browser dialogs', () => {
  const files = [
    '../../frontend/assets/js/controllers.js',
    '../../frontend/assets/js/views/admin.js',
    '../../frontend/assets/js/views/student.js',
    '../../frontend/assets/js/views/instructor.js',
    '../../frontend/assets/js/views/instructor-exams.js',
  ];

  for (const relativePath of files) {
    const source = fs.readFileSync(path.resolve(__dirname, relativePath), 'utf8');
    assert.doesNotMatch(source, /(?<![\w$.])(?:window\s*\.\s*)?(?:alert|confirm|prompt)\s*\(/, relativePath);
  }
});

test('shared UI exposes an informational dialog that uses the shared modal layer', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/ui.js'), 'utf8');

  assert.match(source, /static alert\(/);
  assert.match(source, /static alert\([\s\S]*?UI\.openModal\(/);
  assert.match(source, /UI\.escapeHtml\(message\)/);
});

test('light and dark theme tokens separate canvas, card, raised surface, and border roles', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/index.html'), 'utf8');

  for (const token of ['surface-canvas', 'surface-card', 'surface-raised', 'border-subtle', 'dark-canvas', 'dark-card', 'dark-raised', 'dark-border']) {
    assert.match(source, new RegExp(`"${token}": "#[0-9A-Fa-f]{6}"`), `${token} should have a concrete palette value`);
  }
  assert.match(source, /bg-surface-canvas dark:bg-dark-canvas/);
  assert.match(source, /bg-surface-card dark:bg-dark-card/);
  assert.match(source, /"primary-contrast": "#FDFBF7"/);
  assert.doesNotMatch(source, /"primary-contrast": "#FFFFFF"/);
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
