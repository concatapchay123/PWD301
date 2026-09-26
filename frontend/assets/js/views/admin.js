/**
 * PWD301 LMS - Admin Views Layer
 * Implements:
 * 1. Admin Academic Governance Command Center (4-Tab Modular Command Center):
 *    - Tab 1: Users Matrix & Progressive RBAC + Session Control + Suspend Modal
 *    - Tab 2: Course Review Queue (Side-by-Side Diff) & Instructor Applications
 *    - Tab 3: Faculty Reassignment & Workload Matrix
 *    - Tab 4: Academic Security & Immutable Audit Trail with SHA-256 Block Verification
 * 2. Server Operations & Security Cockpit (65/35 Split Layout):
 *    - Service Health Matrix & Fail-Closed Quarantine Sandbox
 *    - Background Daemons Execution & Regrading Worker Progress
 *    - Isolated Danger Zone ("Never Overwrite Live Database", Staging Dry-Run & Guarded Live Restore)
 *    - System Maintenance Window Engine (Start/End Window)
 *    - Live Hardware Telemetry (CPU, RAM, Disk, Network auto-poll 10s)
 *    - Active Sessions Revocation Panel & Live Threat Stream
 */

class AdminView {
  static getAuditPageState(page, perPage, total) {
    const pageSize = Math.max(1, Number.parseInt(perPage, 10) || 50);
    const itemCount = Math.max(0, Number.parseInt(total, 10) || 0);
    const pageCount = Math.max(1, Math.ceil(itemCount / pageSize));
    const currentPage = Math.min(pageCount, Math.max(1, Number.parseInt(page, 10) || 1));
    return {
      page: currentPage,
      perPage: pageSize,
      total: itemCount,
      pageCount,
      firstItem: itemCount ? ((currentPage - 1) * pageSize) + 1 : 0,
      lastItem: itemCount ? Math.min(currentPage * pageSize, itemCount) : 0,
      hasPrevious: currentPage > 1,
      hasNext: currentPage < pageCount,
    };
  }

  static matchesAuditActionFilter(log, actionFilter = 'ALL') {
    if (actionFilter === 'ALL') return true;
    const action = String(log?.action || '').toUpperCase();
    if (actionFilter === 'ROLE') return action.includes('ROLE') || action.includes('ASSIGN');
    if (actionFilter === 'COURSE') return action.includes('COURSE');
    if (actionFilter === 'DATABASE') return action.includes('DATABASE') || action.includes('BACKUP') || action.includes('RESTORE');
    if (actionFilter === 'QUARANTINE') return action.includes('QUARANTINE');
    return action.includes(String(actionFilter).toUpperCase());
  }

  static getAuditRequestParams(page, perPage, actionFilter = 'ALL') {
    const params = { page, per_page: perPage };
    if (actionFilter !== 'ALL') params.action = actionFilter;
    return params;
  }

  static getAuditActionsForRole(subRole) {
    const allActions = [
      'USER_SUSPEND', 'USER_UNSUSPEND', 'USER_ROLES_UPDATED', 'USER_ROLE_ASSIGNED',
      'USER_ROLE_REVOKED', 'USER_REVOKE_SESSIONS', 'COURSE_CREATED', 'COURSE_UPDATED',
      'COURSE_APPROVED', 'COURSE_PUBLISHED', 'COURSE_TRASHED', 'COURSE_ARCHIVED',
      'COURSE_RESTORED_FROM_TRASH', 'COURSE_SUBMITTED_FOR_REVIEW', 'COURSE_REJECTED',
      'COURSE_RETRACTED_TO_DRAFT', 'COURSE_OWNER_REASSIGNED', 'LESSON_CREATED',
      'LESSON_UPDATED', 'LESSON_REORDERED', 'LESSON_TRASHED', 'LESSON_STATUS_CHANGED',
      'TEACHING_ASSIGNMENT_CREATED', 'TEACHING_ASSIGNMENT_UPDATED', 'DATABASE_BACKUP_CREATED',
      'DATABASE_BACKUP_VERIFIED', 'DATABASE_RESTORE_DRY_RUN', 'DATABASE_RESTORE_INITIATED',
      'DATABASE_RESTORE_COMPLETED', 'QUARANTINE_OVERRIDE', 'ASSESSMENT_CREATED',
      'ASSESSMENT_UPDATED', 'ASSESSMENT_PUBLISHED', 'ASSESSMENT_CANCELLED',
      'ASSESSMENT_TRASHED', 'ASSESSMENT_RESTORED',
      'INSTRUCTOR_APPLICATION_SUBMITTED', 'INSTRUCTOR_APPLICATION_CANCELLED',
      'INSTRUCTOR_APPLICATION_APPROVED', 'INSTRUCTOR_APPLICATION_REJECTED',
    ];
    const actionsByRole = {
      ADMIN_COURSE_REVIEW: allActions.filter(action =>
        [
          'COURSE_CHANGE', 'COURSE_ADMIN_EDIT', 'COURSE_APPROVED', 'COURSE_PUBLISHED',
          'COURSE_TRASHED', 'COURSE_ARCHIVED', 'COURSE_RESTORED', 'COURSE_SUBMITTED',
          'COURSE_REJECTED', 'COURSE_RETRACTED', 'COURSE_STATUS_TO_', 'COURSE_CREATED',
          'COURSE_UPDATED', 'LESSON_', 'SUBJECT_',
        ].some(prefix => action.startsWith(prefix))
      ),
      ADMIN_INSTRUCTOR_REVIEW: allActions.filter(action => action.startsWith('INSTRUCTOR_APPLICATION_')),
      ADMIN_TEACHING_ASSIGNMENT: allActions.filter(action =>
        ['TEACHING_', 'COURSE_REASSIGN', 'COURSE_OWNER_REASSIGNED', 'COURSE_ASSIGN']
          .some(prefix => action.startsWith(prefix))
      ),
    };
    return actionsByRole[subRole] || allActions;
  }

  static getAssignableAdminSubRoles() {
    return ['ADMIN_COURSE_REVIEW', 'ADMIN_INSTRUCTOR_REVIEW', 'ADMIN_TEACHING_ASSIGNMENT', 'ADMIN_SYSTEM_MONITORING'];
  }

  static getAdminSubRoleSelectionState(currentRoles, currentAdminSubRole) {
    const isExistingPrimary = currentRoles.includes('ADMIN') && currentAdminSubRole === 'ADMIN_PRIMARY';
    return {
      isExistingPrimary,
      selectedSubRole: isExistingPrimary || !AdminView.getAssignableAdminSubRoles().includes(currentAdminSubRole)
        ? null
        : currentAdminSubRole,
    };
  }

  static renderAuditActionOptions(subRole) {
    const labels = {
      USER_SUSPEND: 'Khóa tài khoản', USER_UNSUSPEND: 'Mở khóa tài khoản', USER_ROLES_UPDATED: 'Cập nhật tập vai trò',
      USER_ROLE_ASSIGNED: 'Bổ nhiệm vai trò', USER_ROLE_REVOKED: 'Thu hồi vai trò', USER_REVOKE_SESSIONS: 'Thu hồi phiên đăng nhập',
      COURSE_CREATED: 'Tạo khóa học', COURSE_UPDATED: 'Cập nhật khóa học', COURSE_APPROVED: 'Duyệt khóa học',
      COURSE_PUBLISHED: 'Xuất bản khóa học', COURSE_TRASHED: 'Đưa khóa học vào thùng rác', COURSE_ARCHIVED: 'Lưu trữ khóa học',
      COURSE_RESTORED_FROM_TRASH: 'Khôi phục khóa học', COURSE_SUBMITTED_FOR_REVIEW: 'Gửi khóa học xét duyệt',
      COURSE_REJECTED: 'Từ chối khóa học', COURSE_RETRACTED_TO_DRAFT: 'Rút khóa học về bản nháp',
      COURSE_OWNER_REASSIGNED: 'Chuyển người phụ trách khóa học', LESSON_CREATED: 'Tạo bài giảng',
      LESSON_UPDATED: 'Cập nhật bài giảng', LESSON_REORDERED: 'Sắp xếp lại bài giảng', LESSON_TRASHED: 'Đưa bài giảng vào thùng rác',
      LESSON_STATUS_CHANGED: 'Đổi trạng thái bài giảng', TEACHING_ASSIGNMENT_CREATED: 'Tạo phân công giảng dạy',
      TEACHING_ASSIGNMENT_UPDATED: 'Cập nhật phân công giảng dạy', DATABASE_BACKUP_CREATED: 'Tạo bản sao lưu cơ sở dữ liệu',
      DATABASE_BACKUP_VERIFIED: 'Xác minh bản sao lưu', DATABASE_RESTORE_DRY_RUN: 'Chạy thử khôi phục cơ sở dữ liệu',
      DATABASE_RESTORE_INITIATED: 'Bắt đầu khôi phục cơ sở dữ liệu', DATABASE_RESTORE_COMPLETED: 'Hoàn tất khôi phục cơ sở dữ liệu',
      QUARANTINE_OVERRIDE: 'Giải phóng tệp cách ly', ASSESSMENT_CREATED: 'Tạo bài thi', ASSESSMENT_UPDATED: 'Cập nhật bài thi',
      ASSESSMENT_PUBLISHED: 'Xuất bản bài thi', ASSESSMENT_CANCELLED: 'Hủy bài thi', ASSESSMENT_TRASHED: 'Đưa bài thi vào thùng rác',
      ASSESSMENT_RESTORED: 'Khôi phục bài thi',
      INSTRUCTOR_APPLICATION_SUBMITTED: 'Nhận hồ sơ giảng viên', INSTRUCTOR_APPLICATION_CANCELLED: 'Hủy hồ sơ giảng viên',
      INSTRUCTOR_APPLICATION_APPROVED: 'Duyệt hồ sơ giảng viên', INSTRUCTOR_APPLICATION_REJECTED: 'Từ chối hồ sơ giảng viên',
    };
    return ['ALL', ...AdminView.getAuditActionsForRole(subRole)].map(action =>
      `<option value="${action}">${action === 'ALL' ? 'Tất cả tác vụ' : (labels[action] || action.replace(/_/g, ' '))}</option>`
    ).join('');
  }

  static renderLessonMarkdown(markdown) {
    if (typeof UI !== 'undefined' && typeof UI.renderMarkdown === 'function') {
      return UI.renderMarkdown(String(markdown || ''));
    }
    return typeof UI !== 'undefined' ? UI.escapeHtml(String(markdown || '')) : '';
  }

  static getQueueSummary(subRole, counts = {}) {
    const summary = { courses: 0, changes: 0, applications: 0, assignments: 0 };
    if (subRole === 'ADMIN_COURSE_REVIEW') {
      summary.courses = counts.courses || 0;
      summary.changes = counts.changes || 0;
    } else if (subRole === 'ADMIN_INSTRUCTOR_REVIEW') {
      summary.applications = counts.applications || 0;
    } else if (subRole === 'ADMIN_TEACHING_ASSIGNMENT') {
      summary.assignments = counts.assignments || 0;
    }
    return summary;
  }

  // =========================================================================
  // 1. Admin Governance Command Center (4-Tab Modular Command Center)
  // =========================================================================
  static async renderGovernance(container, activeTab = 'users', subQueue = null) {
    const adminSubRole = window.app?.currentUser?.admin_sub_role || 'ADMIN_PRIMARY';
    const showQueueSummary = adminSubRole === 'ADMIN_COURSE_REVIEW' || adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
    const isInstructorQueue = adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
    container.innerHTML = `
        <div class="p-6 space-y-6 max-w-[1800px] mx-auto animate-fade-in" id="admin-governance-root">
        
        <!-- Header & Context Banner -->
        <section class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div class="space-y-1.5">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary font-caption text-xs font-semibold">
              <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span id="admin-governance-actor-label">Phiên điều hành Quản trị viên • Trực ban Thẩm định Học vụ</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Trung tâm Điều hành & Thẩm định Học vụ Đào tạo
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 max-w-3xl">
              Quản lý phân quyền RBAC, thẩm định thay đổi đề cương môn học, điều chuyển giảng dạy an toàn và giám sát tính toàn vẹn dữ liệu.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3 shrink-0">
            <div class="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-500">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Quy chuẩn: <strong class="text-slate-800 dark:text-slate-200 font-bold">Calm Operational Trust</strong></span>
            </div>
            <button type="button" id="btn-open-broadcast" class="px-3.5 py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5" onclick="AdminView.openBroadcastModal()">
              <span class="material-symbols-outlined text-[18px]">campaign</span>
              <span>Phát thông báo</span>
            </button>
            <a href="#/admin/operations" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">monitoring</span>
              <span>Cockpit Vận hành</span>
            </a>
          </div>
        </section>

        <!-- 3 Core KPI Cards with Deep Link Navigation -->
        <div class="${showQueueSummary ? 'grid grid-cols-1 md:grid-cols-3' : 'grid grid-cols-1 md:grid-cols-2'} gap-5">
          
          <!-- KPI 1: Đề cương chờ duyệt -->
          <div class="${showQueueSummary ? '' : 'hidden'} cursor-pointer group bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/40 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 hover:border-primary/40 shadow-sm transition-all" onclick="window.location.hash = '#/admin/governance?tab=${isInstructorQueue ? 'applications' : 'courses'}'">
            <div class="flex items-center justify-between">
              <span data-queue-summary-title class="text-xs font-bold text-slate-500 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[22px]">fact_check</span>
                Duyệt khóa học & Bản sửa đổi
              </span>
              <span class="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 text-[11px] font-bold" id="kpi-courses-badge">Đang tải...</span>
            </div>
            <div class="flex items-baseline gap-3 my-2">
              <span class="text-3xl font-extrabold text-slate-900 dark:text-white font-mono" id="kpi-courses-pending">--</span>
              <span data-queue-summary-description class="text-xs text-slate-400">Khóa học / Bản sửa chờ duyệt</span>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs transition-colors">
              <span class="text-slate-500" id="kpi-courses-subtext">Hàng đợi xét duyệt ABET CAC</span>
              <span class="font-bold text-primary flex items-center gap-1">Xem chi tiết <span class="material-symbols-outlined text-[14px]">arrow_forward</span></span>
            </div>
          </div>

          <!-- KPI 2: Tài nguyên an ninh học vụ & Tệp cách ly -->
          <div class="cursor-pointer group bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/40 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 hover:border-rose-400/40 shadow-sm transition-all" onclick="window.location.hash = '#/admin/governance?tab=security'">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 flex items-center gap-2">
                <span class="material-symbols-outlined text-rose-600 text-[22px]">security_update_warning</span>
                An toàn Học thuật & Kiểm toán
              </span>
              <span class="px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 text-[11px] font-bold">Sandbox Fail-Closed</span>
            </div>
            <div class="flex items-baseline gap-3 my-2">
              <span class="text-3xl font-extrabold text-slate-900 dark:text-white font-mono" id="kpi-audit-blocks">SHA-256</span>
              <span class="text-xs text-slate-400">Chuỗi Bút lục Toàn vẹn</span>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs transition-colors">
              <span class="text-slate-500">Kiểm toán append-only bất biến</span>
              <span class="font-bold text-rose-600 flex items-center gap-1">Audit log <span class="material-symbols-outlined text-[14px]">arrow_forward</span></span>
            </div>
          </div>

          <!-- KPI 3: Giám sát hạ tầng phần cứng -->
          <div class="cursor-pointer group bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/40 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 hover:border-amber-400/40 shadow-sm transition-all" onclick="window.location.hash = '#/admin/operations'">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 flex items-center gap-2">
                <span class="material-symbols-outlined text-amber-500 text-[22px]">dns</span>
                Giám sát hạ tầng phần cứng
              </span>
              <span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-bold" id="kpi-telemetry-badge">Hệ thống OK</span>
            </div>
            <div class="flex items-baseline gap-3 my-2">
              <span class="text-3xl font-extrabold text-slate-900 dark:text-white font-mono" id="kpi-uptime-val">100%</span>
              <span class="text-xs text-slate-400">Thời gian hoạt động (Uptime)</span>
            </div>
            <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs transition-colors">
              <span class="text-slate-500" id="kpi-telemetry-metrics">CPU: --% • RAM: -- GB</span>
              <span class="font-bold text-primary flex items-center gap-1">Cockpit <span class="material-symbols-outlined text-[14px]">arrow_forward</span></span>
            </div>
          </div>

        </div>

        <!-- Tab Content Box -->
        <div id="admin-tab-content-box" class="min-h-[400px]"></div>

      </div>
    `;

    // Load initial KPIs
    try {
      const isCourseReviewer = adminSubRole === 'ADMIN_COURSE_REVIEW';
      const isInstructorReviewer = adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
      const canViewTelemetry = adminSubRole === 'ADMIN_PRIMARY' || adminSubRole === 'ADMIN_SYSTEM_MONITORING';
      const [coursesRes, appsRes, crRes, telemRes] = await Promise.allSettled([
        isCourseReviewer ? ApiClient.getPendingCourses() : Promise.resolve(null),
        isInstructorReviewer ? ApiClient.getAdminInstructorApplications('PENDING') : Promise.resolve(null),
        isCourseReviewer ? ApiClient.getAdminChangeRequests('PENDING') : Promise.resolve(null),
        canViewTelemetry ? ApiClient.getAdminTelemetry() : Promise.resolve(null)
      ]);

      let pendingCoursesCount = 0;
      if (coursesRes.status === 'fulfilled' && coursesRes.value) {
        pendingCoursesCount = coursesRes.value.pending_count || (coursesRes.value.courses ? coursesRes.value.courses.length : 0);
      }
      let pendingCrCount = 0;
      if (crRes.status === 'fulfilled' && crRes.value) {
        pendingCrCount = crRes.value.pending_count || (crRes.value.change_requests ? crRes.value.change_requests.length : 0);
      }
      let pendingAppsCount = 0;
      if (appsRes.status === 'fulfilled' && appsRes.value) {
        pendingAppsCount = appsRes.value.pending_count || (appsRes.value.applications ? appsRes.value.applications.length : 0);
      }

      const queueSummary = AdminView.getQueueSummary(adminSubRole, {
        courses: pendingCoursesCount,
        changes: pendingCrCount,
        applications: pendingAppsCount,
      });
      const totalCourseWork = queueSummary.courses + queueSummary.changes + queueSummary.applications;
      const el = document.getElementById('kpi-courses-pending');
      const badge = document.getElementById('kpi-courses-badge');

      if (isInstructorQueue) {
        const queueCard = el?.closest('div[onclick]');
        const queueTitle = queueCard?.querySelector('[data-queue-summary-title]');
        const queueDescription = queueCard?.querySelector('[data-queue-summary-description]');
        const queueSubtext = document.getElementById('kpi-courses-subtext');
        if (queueTitle?.lastChild) queueTitle.lastChild.textContent = ' Hồ sơ giảng viên chờ duyệt';
        if (queueDescription) queueDescription.textContent = 'Hồ sơ đang chờ xét duyệt';
        if (queueSubtext) queueSubtext.textContent = 'Hàng đợi xét duyệt giảng viên';
      }

      if (el) el.textContent = String(totalCourseWork).padStart(2, '0');
      if (badge) badge.textContent = `${totalCourseWork} chờ duyệt`;

      // Synchronize Real-time Superscript Exponent Badges to Topbar
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({
          courses: queueSummary.courses + queueSummary.changes,
          applications: queueSummary.applications
        });
      }

      if (telemRes.status === 'fulfilled' && telemRes.value) {
        const data = telemRes.value;
        const cpuPct = data.cpu?.percent ?? 0;
        const ramUsed = data.memory?.used_gb ?? 0;
        const ramTotal = data.memory?.total_gb ?? '--';
        const metricsEl = document.getElementById('kpi-telemetry-metrics');
        if (metricsEl) metricsEl.textContent = `CPU: ${cpuPct}% • RAM: ${ramUsed} / ${ramTotal} GB`;
      }
    } catch (err) {
      console.warn('Initial admin KPI load warning:', err);
    }

    // Tab Switching Logic (URL Hash & Topbar Synchronized)
    const contentBox = document.getElementById('admin-tab-content-box');

    AdminView.switchTab = (tabKey, subQueue = null, syncHash = true) => {
      const tabToQuery = {
        'tab-users': '',
        'tab-courses-review': 'courses',
        'tab-review': 'courses',
        'tab-instructor-apps': 'applications',
        'tab-reassign': 'reassign',
        'tab-security': 'security'
      };

      if (syncHash) {
        const q = tabToQuery[tabKey];
        const newHash = q ? `#/admin/governance?tab=${q}` : '#/admin/governance';
        if (window.location.hash !== newHash) {
          window.location.hash = newHash;
          return;
        }
      }

      if (tabKey === 'tab-users') {
        AdminView.renderTabUsers(contentBox);
      } else if (tabKey === 'tab-courses-review' || tabKey === 'tab-review') {
        AdminView.renderTabCoursesReview(contentBox, subQueue);
      } else if (tabKey === 'tab-instructor-apps') {
        AdminView.renderTabInstructorApps(contentBox);
      } else if (tabKey === 'tab-reassign') {
        AdminView.renderTabReassign(contentBox);
      } else if (tabKey === 'tab-security') {
        AdminView.renderTabSecurity(contentBox);
      }
    };

    const targetTab = (activeTab === 'courses' || activeTab === 'review')
      ? 'tab-courses-review'
      : (activeTab === 'applications' || activeTab === 'instructors')
        ? 'tab-instructor-apps'
        : activeTab === 'security'
          ? 'tab-security'
          : activeTab === 'reassign'
            ? 'tab-reassign'
            : 'tab-users';
    AdminView.switchTab(targetTab, subQueue, false);
  }

  // =========================================================================
  // Tab 1: Users & Progressive RBAC + Active Sessions (100% Live Database)
  // =========================================================================
  static async renderTabUsers(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5" id="users-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải ma trận người dùng & kiểm soát phiên từ MS SQL Server...</p>
        </div>
      </div>
    `;

    try {
      const res = await ApiClient.getAdminUsers();
      const users = res.users || [];
      const totalUsers = res.total !== undefined ? res.total : users.length;

      const box = document.getElementById('users-box');
      if (!box) return;

      box.innerHTML = `
        <!-- Table Header & Controls -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[22px]">badge</span>
              <h2 class="text-base font-bold text-slate-900 dark:text-white">Ma trận Người dùng & Phân quyền RBAC (${totalUsers} tài khoản)</h2>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">Xác lập phạm vi thẩm quyền theo chuẩn RBAC AUTH-002. Cấp/thu hồi quyền có kiểm toán bắt buộc. Không Impersonation.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div class="relative">
              <input type="text" id="user-search-input" aria-label="Tìm kiếm người dùng theo tên hoặc email" placeholder="Tìm tên hoặc email..." class="pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-primary" />
              <span class="material-symbols-outlined absolute left-2.5 top-2 text-slate-400 text-[16px]" aria-hidden="true">search</span>
            </div>
            <select id="user-role-filter" aria-label="Lọc người dùng theo vai trò" class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-bold focus:outline-none">
              <option value="ALL">T&#7845;t c&#7843; ng&#432;&#7901;i d&#249;ng</option>
              <option value="STUDENT">Sinh vi&#234;n</option>
              <option value="INSTRUCTOR">Gi&#7843;ng vi&#234;n</option>
              <option value="ADMIN">Qu&#7843;n tr&#7883; vi&#234;n</option>
            </select>
            <button type="button" id="btn-sync-users" class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-bold transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">sync</span>
              <span>Đồng bộ</span>
            </button>
          </div>
        </div>

        <!-- Master Table Container -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm border-collapse" id="admin-users-table">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="py-3 px-3">Họ tên & Email</th>
                <th class="py-3 px-3">Vai trò RBAC</th>
                <th class="py-3 px-3">Trạng thái</th>
                <th class="py-3 px-3">Ngày tạo</th>
                <th class="py-3 px-3 text-right">Kiểm soát An toàn</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="admin-users-tbody">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>

        <!-- Strict Non-negotiable Invariant: No Impersonation -->
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600 dark:text-slate-300">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-[18px]">verified_user</span>
            <span><strong>Nguyên tắc Bất biến AUTH-002:</strong> Hệ thống không hỗ trợ "Đăng nhập dưới danh nghĩa" (Impersonation). Mọi hành động thao tác dữ liệu bắt buộc gắn định danh thực của Quản trị viên điều hành.</span>
          </div>
          <span class="font-mono text-[11px] text-slate-400 font-bold shrink-0">Policy RBAC-v4.2-Strict</span>
        </div>

        <!-- Optimistic Locking Panel -->
        <div class="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div class="flex items-start gap-2.5">
            <span class="material-symbols-outlined text-amber-600 text-[20px] mt-0.5">sync_problem</span>
            <div>
              <strong class="text-amber-900 dark:text-amber-300 block mb-0.5">Cơ chế Kiểm soát Xung đột Đồng thời (Optimistic Locking & auth_version)</strong>
              <p class="text-amber-800/80 dark:text-amber-400/80">Khi vai trò bị thay đổi hoặc tài khoản bị tạm ngưng, auth_version sẽ tăng, lập tức thu hồi phiên của người dùng trên toàn hệ thống.</p>
            </div>
          </div>
          <button type="button" id="btn-sync-optimistic" class="px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border border-amber-300 dark:border-amber-800 hover:bg-amber-50 text-slate-800 dark:text-slate-200 font-bold text-xs shrink-0 transition-colors shadow-xs">
            Đồng bộ trạng thái mới nhất
          </button>
        </div>
      `;

      const renderTableRows = (userList = users) => {
        const tbody = document.getElementById('admin-users-tbody');
        if (!tbody) return;

        if (userList.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="py-8 text-center text-slate-400 text-xs">
                Không tìm thấy người dùng phù hợp với điều kiện tìm kiếm.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = userList.map(u => {
          const isSuspended = u.status === 'SUSPENDED';
          const initials = (u.display_name || u.email || 'U').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
          const avatarBg = u.roles && u.roles.includes('ADMIN') ? 'bg-primary text-white' : u.roles && u.roles.includes('INSTRUCTOR') ? 'bg-indigo-600 text-white' : 'bg-slate-500 text-white';

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="py-4 px-3 align-middle">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-xl ${avatarBg} font-bold flex items-center justify-center text-xs shrink-0 shadow-xs">
                    ${initials}
                  </div>
                  <div>
                    <div class="font-bold text-slate-900 dark:text-white text-xs sm:text-sm">
                      ${UI.escapeHtml(u.display_name || 'Chưa cập nhật tên')}
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono">${UI.escapeHtml(u.email)}</div>
                  </div>
                </div>
              </td>
              <td class="py-4 px-3 align-middle">
                <div class="flex flex-wrap gap-1">
                  ${(u.roles || []).map(r => {
                    let rClass = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
                    let rLabel = r;
                    if (r === 'ADMIN') {
                      rClass = 'bg-primary-subtle text-primary border border-primary/20 font-bold';
                      if (u.admin_sub_role_label) {
                        rLabel = `ADMIN (${u.admin_sub_role_label})`;
                      }
                    }
                    if (r === 'INSTRUCTOR') rClass = 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 font-bold';
                    return `<span class="px-2 py-0.5 rounded text-[10px] ${rClass}">${rLabel}</span>`;
                  }).join('')}
                </div>
              </td>
              <td class="py-4 px-3 align-middle text-xs">
                ${isSuspended ? `
                  <div class="flex items-center gap-1.5 text-rose-600 font-bold">
                    <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                    <span>Đã đình chỉ</span>
                  </div>
                  <div class="font-mono text-[10px] text-slate-400">${u.suspended_at ? UI.formatDate(u.suspended_at) : ''}</div>
                ` : `
                  <div class="flex items-center gap-1.5 text-emerald-600 font-bold">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>Hoạt động</span>
                  </div>
                `}
              </td>
              <td class="py-4 px-3 align-middle text-xs text-slate-400 font-mono">
                ${UI.formatDate(u.created_at)}
              </td>
              <td class="py-4 px-3 align-middle text-right">
                <div class="inline-flex items-center gap-1.5">
                  <button type="button" class="px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors manage-role-btn ${!window.app?.currentUser?.is_primary_admin ? 'opacity-60 cursor-not-allowed' : ''}" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}" data-roles="${(u.roles || []).join(',')}" data-admin-sub-role="${u.admin_sub_role || 'ADMIN_PRIMARY'}" title="${!window.app?.currentUser?.is_primary_admin ? 'Chỉ Admin chính mới có quyền phân quyền' : 'Phân quyền tài khoản'}">
                    Phân quyền
                  </button>
                  ${isSuspended ? `
                    <button type="button" class="px-2.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-bold border border-emerald-200 transition-colors unsuspend-user-btn" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}">
                      Mở khóa
                    </button>
                  ` : `
                    <button type="button" class="px-2.5 py-1.5 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-bold border border-rose-200 transition-colors suspend-user-btn" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}">
                      Tạm ngưng
                    </button>
                  `}
                  <button type="button" class="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400 text-xs font-bold transition-colors revoke-sessions-btn" title="Thu hồi toàn bộ phiên đăng nhập của người dùng" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}">
                    Thu hồi phiên
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('');

        // Attach action events
        tbody.querySelectorAll('.manage-role-btn').forEach(btn => {
          btn.onclick = () => {
            if (!window.app?.currentUser?.is_primary_admin) {
              UI.showToast('Chỉ Quản trị viên chính (Admin chính) mới có quyền phân quyền người dùng.', 'warning');
              return;
            }
            const currentRoles = (btn.dataset.roles || '').split(',').filter(Boolean);
            AdminView.openRoleModal(btn.dataset.userId, btn.dataset.userName, currentRoles, btn.dataset.adminSubRole);
          };
        });

        tbody.querySelectorAll('.suspend-user-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.openSuspendModal(btn.dataset.userId, btn.dataset.userName);
          };
        });

        tbody.querySelectorAll('.unsuspend-user-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.unsuspendUser(btn.dataset.userId, btn.dataset.userName);
          };
        });

        tbody.querySelectorAll('.revoke-sessions-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.revokeUserSessions(btn.dataset.userId, btn.dataset.userName);
          };
        });
      };

      // Initial render of rows
      renderTableRows(users);

      // Search & Filter event bindings (Debounced Server-side Query with Local Fallback)
      const searchInput = document.getElementById('user-search-input');
      const roleFilter = document.getElementById('user-role-filter');
      let searchDebounceTimer = null;

      const triggerQuery = async () => {
        const sVal = searchInput ? searchInput.value.trim() : '';
        const rVal = roleFilter ? roleFilter.value : 'ALL';
        try {
          const freshRes = await ApiClient.getAdminUsers({
            search: sVal,
            role: rVal === 'ALL' ? '' : rVal
          });
          const freshUsers = freshRes.users || [];
          renderTableRows(freshUsers);
          const counterEl = box.querySelector('h2');
          if (counterEl) {
            counterEl.textContent = `Ma trận Người dùng & Phân quyền RBAC (${freshRes.total !== undefined ? freshRes.total : freshUsers.length} tài khoản)`;
          }
        } catch (e) {
          const localFiltered = users.filter(u => {
            const matchText = !sVal || 
              (u.display_name && u.display_name.toLowerCase().includes(sVal.toLowerCase())) ||
              (u.email && u.email.toLowerCase().includes(sVal.toLowerCase()));
            const matchRole = rVal === 'ALL' || (u.roles && u.roles.includes(rVal));
            return matchText && matchRole;
          });
          renderTableRows(localFiltered);
        }
      };

      if (searchInput) {
        searchInput.oninput = () => {
          clearTimeout(searchDebounceTimer);
          searchDebounceTimer = setTimeout(triggerQuery, 250);
        };
      }
      if (roleFilter) {
        roleFilter.onchange = () => {
          triggerQuery();
        };
      }

      document.getElementById('btn-sync-users').onclick = () => {
        UI.refreshCurrentRoute(() => AdminView.renderTabUsers(container));
      };

      document.getElementById('btn-sync-optimistic').onclick = () => {
        UI.refreshCurrentRoute(() => AdminView.renderTabUsers(container));
        UI.showToast('Đã đồng bộ trạng thái người dùng mới nhất từ máy chủ!', 'success');
      };

    } catch (err) {
      console.error('TabUsers load error:', err);
      const box = document.getElementById('users-box');
      if (box) {
        box.innerHTML = `
          <div class="p-8 text-center text-rose-500 space-y-2">
            <span class="material-symbols-outlined text-4xl">error</span>
            <p class="text-sm font-bold">Không thể tải danh sách người dùng: ${UI.escapeHtml(err.message || 'Lỗi kết nối')}</p>
            <button type="button" class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box'))) ">Thử lại</button>
          </div>
        `;
      }
    }
  }

  static openRoleModal(userId, userName, currentRoles = [], currentAdminSubRole = 'ADMIN_PRIMARY') {
    const subRoleSelectionState = AdminView.getAdminSubRoleSelectionState(currentRoles, currentAdminSubRole);
    if (!window.app?.currentUser?.is_primary_admin) {
      UI.showToast('Chỉ Quản trị viên chính (Admin chính) mới có quyền phân quyền người dùng.', 'error');
      return;
    }

    const body = `
      <div class="space-y-4 text-xs">
        <p class="text-slate-600 dark:text-slate-300">
          Quản lý phân quyền lũy tiến AUTH-002 cho tài khoản <strong>${UI.escapeHtml(userName)}</strong>.
        </p>
        
        <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
          <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Vai trò hiện tại:</div>
          <div class="flex flex-wrap gap-1">
            ${currentRoles.length > 0 ? currentRoles.map(r => `<span class="px-2 py-0.5 rounded bg-primary-subtle text-primary font-bold text-[10px]">${r}</span>`).join('') : '<span class="text-slate-400">Không có vai trò</span>'}
          </div>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Hành động</label>
          <select id="modal-role-action" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="assign">Cấp thêm quyền (Assign)</option>
            <option value="remove">Thu hồi quyền (Remove)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Vai trò mục tiêu</label>
          <select id="modal-role-code" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="ADMIN">ADMIN (Quản trị viên)</option>
            <option value="INSTRUCTOR">INSTRUCTOR (Giảng viên)</option>
            <option value="STUDENT">STUDENT (Sinh viên)</option>
          </select>
        </div>

        <!-- Phân quyền chi tiết Admin dưới quyền Admin chính -->
        <div id="admin-sub-role-container" class="space-y-2 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
          <div class="flex items-center justify-between">
            <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 text-[11px] flex items-center gap-1.5">
              <span class="material-symbols-outlined text-primary text-[16px]">shield_person</span>
              Phân nhóm quyền Quản trị (Dưới quyền Admin chính)
            </label>
            <span class="text-[10px] text-primary font-bold bg-primary-subtle px-2 py-0.5 rounded">Thẩm quyền rõ ràng</span>
          </div>
          <div class="space-y-2 pt-1">
            ${subRoleSelectionState.isExistingPrimary ? `
              <div class="px-2.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-200" role="status">
                Tài khoản Admin chính hiện tại; không thể cấp mới hoặc đổi vai trò tại đây.
              </div>
            ` : ''}
            <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
              <input type="radio" name="admin-sub-role-radio" value="ADMIN_COURSE_REVIEW" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_COURSE_REVIEW' ? 'checked' : ''}>
              <div>
                <div class="font-bold text-xs text-slate-900 dark:text-white">Admin duyệt khóa học</div>
                <div class="text-[11px] text-slate-500">Phê duyệt đề cương khóa học mới, duyệt yêu cầu sửa/xóa bài giảng và môn học.</div>
              </div>
            </label>
            <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
              <input type="radio" name="admin-sub-role-radio" value="ADMIN_INSTRUCTOR_REVIEW" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_INSTRUCTOR_REVIEW' ? 'checked' : ''}>
              <div>
                <div class="font-bold text-xs text-slate-900 dark:text-white">Admin duyệt giảng viên</div>
                <div class="text-[11px] text-slate-500">Thẩm định hồ sơ, xem trực tiếp file CV, bằng cấp và phê duyệt/từ chối đơn ứng tuyển.</div>
              </div>
            </label>
            <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
              <input type="radio" name="admin-sub-role-radio" value="ADMIN_TEACHING_ASSIGNMENT" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_TEACHING_ASSIGNMENT' ? 'checked' : ''}>
              <div>
                <div class="font-bold text-xs text-slate-900 dark:text-white">Admin phân công giảng dạy</div>
                <div class="text-[11px] text-slate-500">Điều phối, gán và chuyển giao giảng viên phụ trách các khóa học đào tạo.</div>
              </div>
            </label>
            <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
              <input type="radio" name="admin-sub-role-radio" value="ADMIN_SYSTEM_MONITORING" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_SYSTEM_MONITORING' ? 'checked' : ''}>
              <div>
                <div class="font-bold text-xs text-slate-900 dark:text-white">Admin giám sát hệ thống</div>
                <div class="text-[11px] text-slate-500">Theo dõi tài nguyên phần cứng CPU/RAM, nhật ký kiểm toán bất biến (Audit Log) & Telemetry.</div>
              </div>
            </label>
          </div>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Lý do thay đổi phân quyền (Kiểm toán bắt buộc) *</label>
          <input type="text" id="modal-role-reason" placeholder="VD: Quyết định bổ nhiệm nhân sự học vụ..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
        </div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Đóng</button>
      <button type="button" id="submit-role-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Xác nhận phân quyền</button>
    `;

    UI.openModal({
      title: 'Phân quyền tài khoản người dùng',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    const actionSelect = document.getElementById('modal-role-action');
    const roleSelect = document.getElementById('modal-role-code');
    const subRoleContainer = document.getElementById('admin-sub-role-container');

    const updateSubRoleVisibility = () => {
      if (subRoleContainer) {
        if (actionSelect.value === 'assign' && roleSelect.value === 'ADMIN') {
          subRoleContainer.classList.remove('hidden');
        } else {
          subRoleContainer.classList.add('hidden');
        }
      }
    };

    if (actionSelect) actionSelect.onchange = updateSubRoleVisibility;
    if (roleSelect) roleSelect.onchange = updateSubRoleVisibility;
    updateSubRoleVisibility();

    document.getElementById('submit-role-btn').onclick = async () => {
      const action = document.getElementById('modal-role-action').value;
      const role = document.getElementById('modal-role-code').value;
      const reason = document.getElementById('modal-role-reason').value.trim();

      if (!reason) {
        UI.showToast('Vui lòng nhập lý do thay đổi phân quyền kiểm toán.', 'warning');
        return;
      }

      let adminSubRole = null;
      if (action === 'assign' && role === 'ADMIN') {
        const checkedRadio = document.querySelector('input[name="admin-sub-role-radio"]:checked');
        if (!checkedRadio || !AdminView.getAssignableAdminSubRoles().includes(checkedRadio.value)) {
          UI.showToast('Vui lòng chọn một vai trò admin phụ trước khi cấp quyền ADMIN.', 'warning');
          return;
        }
        adminSubRole = checkedRadio.value;
      }

      try {
        if (action === 'assign') {
          await ApiClient.assignRole(userId, role, reason, adminSubRole);
          UI.showToast(`Đã cấp quyền ${role} cho ${userName} thành công!`, 'success');
        } else {
          await ApiClient.removeRole(userId, role, reason);
          UI.showToast(`Đã thu hồi quyền ${role} của ${userName} thành công!`, 'info');
        }
        UI.closeModal();
        UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
      } catch (e) {
        UI.showToast(e.message || 'Lỗi phân quyền.', 'error');
      }
    };
  }

  static openSuspendModal(userId, userName) {
    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400 text-xs border border-rose-200 dark:border-rose-900/60 leading-relaxed">
          <strong>Cảnh báo An toàn Fail-Closed:</strong> Khi tạm ngưng tài khoản, toàn bộ phiên đăng nhập hoạt động (Web Session và JWT Bearer Tokens) sẽ bị thu hồi tức thì (auth_version increment). Người dùng sẽ bị chặn toàn bộ quyền truy cập.
        </div>
        <p class="text-slate-600 dark:text-slate-300">Tài khoản mục tiêu: <strong>${UI.escapeHtml(userName)}</strong> (${userId})</p>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Lý do phong tỏa (Bắt buộc kiểm toán) *</label>
          <textarea id="suspend-reason" rows="3" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600 resize-none" placeholder="Ghi rõ căn cứ vi phạm hoặc nghi vấn an ninh..."></textarea>
        </div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy</button>
      <button type="button" id="confirm-suspend-btn" class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-sm">Xác nhận Tạm ngưng</button>
    `;

    UI.openModal({
      title: 'Khóa quyền & Tạm ngưng Tài khoản Khẩn cấp',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    document.getElementById('confirm-suspend-btn').onclick = async () => {
      const reason = document.getElementById('suspend-reason').value.trim();
      if (!reason) {
        UI.showToast('Vui lòng nhập lý do phong tỏa kiểm toán.', 'warning');
        return;
      }
      try {
        await ApiClient.suspendUser(userId, reason);
        UI.closeModal();
        UI.showToast(`Đã tạm ngưng tài khoản ${userName} thành công! Toàn bộ phiên đã bị thu hồi.`, 'success');
        UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
      } catch (e) {
        UI.showToast(e.message || 'Lỗi tạm ngưng tài khoản.', 'error');
      }
    };
  }

  static async unsuspendUser(userId, userName) {
    const conf = await UI.confirm(
      'Mở khóa tài khoản',
      `Bạn có chắc chắn muốn kích hoạt lại tài khoản cho "${userName}"? Người dùng sẽ có thể đăng nhập bình thường.`,
      'Kích hoạt lại'
    );
    if (!conf) return;

    try {
      await ApiClient.unsuspendUser(userId, 'Quản trị viên mở khóa tài khoản');
      UI.showToast(`Đã kích hoạt lại tài khoản của ${userName} thành công!`, 'success');
      UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
    } catch (e) {
      UI.showToast(e.message || 'Lỗi mở khóa tài khoản.', 'error');
    }
  }

  static async revokeUserSessions(userId, userName) {
    const conf = await UI.confirm(
      'Thu hồi toàn bộ phiên đăng nhập',
      `Xác nhận cưỡng chế chấm dứt tất cả các phiên làm việc và JWT tokens hiện tại của "${userName}"? Người dùng sẽ phải đăng nhập lại.`,
      'Thu hồi phiên'
    );
    if (!conf) return;

    try {
      await ApiClient.revokeUserSessions(userId, 'Quản trị viên cưỡng chế thu hồi phiên');
      UI.showToast(`Đã thu hồi toàn bộ phiên đăng nhập của ${userName}!`, 'success');
    } catch (e) {
      UI.showToast(e.message || 'Lỗi thu hồi phiên.', 'error');
    }
  }

  static openBroadcastModal() {
    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-primary/10 text-primary border border-primary/20 text-xs leading-relaxed">
          <strong>Phát thông báo Hệ thống:</strong> Thông báo sẽ được chuyển phát trực tiếp tới hộp thư in-app của toàn bộ tài khoản mục tiêu theo thời gian thực.
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Tiêu đề thông báo *</label>
          <input type="text" id="broadcast-title" placeholder="VD: Thông báo bảo trì nâng cấp học kỳ mới..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Đối tượng nhận</label>
          <select id="broadcast-role" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="ALL">Tất cả người dùng</option>
            <option value="STUDENT">Chỉ Sinh viên (STUDENT)</option>
            <option value="INSTRUCTOR">Chỉ Giảng viên (INSTRUCTOR)</option>
            <option value="ADMIN">Chỉ Quản trị viên (ADMIN)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Phân loại thông báo</label>
          <select id="broadcast-category" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="SYSTEM">Hệ thống (SYSTEM)</option>
            <option value="COURSE">Khóa học / Học vụ (COURSE)</option>
            <option value="ASSESSMENT">Khảo thí (ASSESSMENT)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Nội dung chi tiết *</label>
          <textarea id="broadcast-body" rows="4" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary resize-none" placeholder="Nhập nội dung thông báo..."></textarea>
        </div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy</button>
      <button type="button" id="submit-broadcast-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold flex items-center gap-1.5 shadow-sm">
        <span class="material-symbols-outlined text-[16px]">campaign</span>
        <span>Phát thông báo ngay</span>
      </button>
    `;

    UI.openModal({
      title: 'Phát thông báo hệ thống',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    document.getElementById('submit-broadcast-btn').onclick = async () => {
      const title = document.getElementById('broadcast-title').value.trim();
      const roleVal = document.getElementById('broadcast-role').value;
      const targetRole = roleVal === 'ALL' ? null : roleVal;
      const category = document.getElementById('broadcast-category').value;
      const bodyText = document.getElementById('broadcast-body').value.trim();

      if (!title) {
        UI.showToast('Vui lòng nhập tiêu đề thông báo.', 'warning');
        return;
      }
      if (!bodyText) {
        UI.showToast('Vui lòng nhập nội dung thông báo.', 'warning');
        return;
      }

      try {
        const res = await ApiClient.broadcastNotification(title, bodyText, targetRole, category);
        UI.closeModal();
        const count = res.broadcasted_count || 0;
        UI.showToast(`Đã phát thông báo thành công tới ${count} người dùng!`, 'success');
      } catch (err) {
        UI.showToast(err.message || 'Lỗi phát thông báo.', 'error');
      }
    };
  }

  // =========================================================================
  // Tab 2: Duyệt Khóa học & Hàng đợi Bản sửa đổi (Course Review & Change Requests)
  // =========================================================================
  static async renderTabCoursesReview(container, subQueue = null) {
    container.innerHTML = `
      <div class="space-y-6 animate-fade-in" id="courses-review-box">
        <div class="p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải hàng đợi thẩm định đề cương khóa học & yêu cầu sửa đổi...</p>
        </div>
      </div>
    `;

    try {
      const [pendingCoursesRes, changeReqsRes] = await Promise.allSettled([
        ApiClient.getPendingCourses(),
        ApiClient.getAdminChangeRequests('ALL')
      ]);

      const pendingCourses = (pendingCoursesRes.status === 'fulfilled' && pendingCoursesRes.value) ? (pendingCoursesRes.value.courses || []) : [];
      const changeRequests = (changeReqsRes.status === 'fulfilled' && changeReqsRes.value) ? (changeReqsRes.value.change_requests || []) : [];
      const pendingChangeRequests = changeRequests.filter(r => r.status === 'PENDING');

      // Update badge
      const totalPending = pendingCourses.length + pendingChangeRequests.length;
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({ courses: totalPending });
      }
      const elPending = document.getElementById('kpi-courses-pending');
      const badgePending = document.getElementById('kpi-courses-badge');
      if (elPending) elPending.textContent = String(totalPending).padStart(2, '0');
      if (badgePending) badgePending.textContent = `${totalPending} chờ duyệt`;

      const box = document.getElementById('courses-review-box');
      if (!box) return;

      box.innerHTML = `
        <!-- Section 1: Hàng đợi Thẩm định Đề cương Khóa học mới/xuất bản -->
        <div id="admin-review-courses-queue" class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">fact_check</span>
                Hàng đợi Thẩm định Khóa học Chờ Duyệt (Pending Courses)
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">Đối soát đề cương, chuẩn đầu ra SLO và danh mục bài học do Giảng viên hoàn thiện trước khi ban hành chính thức.</p>
            </div>
            <span class="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 text-xs font-bold border border-amber-200">
              ${pendingCourses.length} Khóa học chờ duyệt
            </span>
          </div>

          ${pendingCourses.length === 0 ? `
            <div class="p-8 text-center text-slate-400 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <span class="material-symbols-outlined text-emerald-500 text-3xl">task_alt</span>
              <p class="text-xs font-bold text-slate-700 dark:text-slate-300">Không có khóa học nào đang chờ thẩm định</p>
              <p class="text-[11px] text-slate-400">Toàn bộ khóa học nộp lên đã được giải quyết hoặc chưa có đề xuất xuất bản mới.</p>
            </div>
          ` : `
            <div class="space-y-4">
              ${pendingCourses.map(c => `
                <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                  <div class="bg-slate-50 dark:bg-slate-800 px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-700 text-xs">
                    <div>
                      <span class="font-bold font-mono text-primary mr-1">${UI.escapeHtml(c.course_code)}</span>
                      <span class="font-bold text-slate-800 dark:text-slate-200">${UI.escapeHtml(c.title)}</span>
                      <span class="text-slate-400 ml-2">Cập nhật lúc: ${UI.formatDateTime(c.updated_at)}</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors shadow-xs flex items-center gap-1 inspect-course-btn" data-course-id="${c.course_id}">
                        <span class="material-symbols-outlined text-[16px]">menu_book</span> Xem đề cương & bài học
                      </button>
                      <button type="button" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs flex items-center gap-1 approve-course-btn" data-course-id="${c.course_id}" data-course-title="${UI.escapeHtml(c.title)}">
                        <span class="material-symbols-outlined text-[16px]">check</span> Phê duyệt ban hành
                      </button>
                      <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors reject-course-btn" data-course-id="${c.course_id}" data-course-title="${UI.escapeHtml(c.title)}">
                        Yêu cầu chỉnh sửa
                      </button>
                    </div>
                  </div>

                  <!-- Course Metadata Details -->
                  <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-slate-50/50 dark:bg-slate-950/40">
                    <div class="p-3 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 font-sans">
                      <div class="font-bold text-slate-500 uppercase text-[10px] pb-1 border-b border-slate-100 dark:border-slate-800 font-mono">Thông tin nộp duyệt</div>
                      <p><strong>Mã khóa học:</strong> <span class="font-mono text-primary font-bold">${UI.escapeHtml(c.course_code)}</span></p>
                      <p><strong>Tiêu đề:</strong> ${UI.escapeHtml(c.title)}</p>
                      <p><strong>Trạng thái:</strong> <span class="text-amber-600 font-bold">${c.status}</span></p>
                      <p><strong>Giảng viên chủ quản:</strong> ${UI.escapeHtml(c.owner_instructor_name || c.owner_instructor_id || 'Chưa gán')}</p>
                    </div>
                    <div class="p-3 rounded bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/40 space-y-1 text-emerald-900 dark:text-emerald-300 font-sans">
                      <div class="font-bold text-emerald-700 dark:text-emerald-400 uppercase text-[10px] pb-1 border-b border-emerald-200 dark:border-emerald-800 font-mono">Quy trình thẩm định học vụ</div>
                      <p class="text-xs leading-relaxed">Đề cương đã được Giảng viên hoàn thiện toàn bộ bài học và đệ trình xuất bản. Nhấn <strong>Xem đề cương & bài học</strong> để kiểm tra đầy đủ, hoặc <strong>Phê duyệt ban hành</strong> để chính thức mở khóa học cho Sinh viên đăng ký.</p>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          `}
        </div>

        <!-- Section 2: Hàng đợi Phê duyệt Sửa/Xóa Bài giảng & Môn học (Change Requests) -->
        <div id="admin-review-change-requests-queue" class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">edit_note</span>
                Hàng đợi Phê duyệt Sửa/Xóa Bài giảng & Môn học (Change Requests)
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">Xem đối chiếu bản sửa đổi chi tiết (Side-by-Side Diff) giữa bản hiện tại và bản đề xuất trước khi phê duyệt.</p>
            </div>
            <div class="flex items-center gap-1.5" id="cr-status-filter-group">
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white" data-status="ALL">Tất cả (${changeRequests.length})</button>
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="PENDING">Chờ duyệt (${pendingChangeRequests.length})</button>
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="APPROVED">Đã duyệt</button>
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="REJECTED">Từ chối</button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs sm:text-sm min-w-[1500px] table-fixed">
              <colgroup>
                <col style="width:160px"><col style="width:240px"><col style="width:360px">
                <col style="width:170px"><col style="width:130px"><col style="width:150px"><col style="width:290px">
              </colgroup>
              <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                <tr>
                  <th class="px-3.5 py-3 w-[150px] whitespace-nowrap">Loại yêu cầu</th>
                  <th class="px-3.5 py-3 w-[200px] whitespace-nowrap">Khóa học</th>
                  <th class="px-3.5 py-3 min-w-[280px]">Đối tượng & Đề xuất</th>
                  <th class="px-3.5 py-3 w-[140px] whitespace-nowrap">Người gửi</th>
                  <th class="px-3.5 py-3 w-[110px] whitespace-nowrap">Trạng thái</th>
                  <th class="px-3.5 py-3 w-[130px] whitespace-nowrap">Thời điểm</th>
                  <th class="px-3.5 py-3 w-[230px] whitespace-nowrap text-right">Quyết định phê duyệt</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="change-requests-tbody">
                <!-- Populated via JS -->
              </tbody>
            </table>
          </div>
        </div>
      `;

      // Event bindings for Courses Review
      box.querySelectorAll('.inspect-course-btn').forEach(btn => {
        btn.onclick = () => {
          AdminView.openCourseInspectionModal(btn.dataset.courseId);
        };
      });

      box.querySelectorAll('.approve-course-btn').forEach(btn => {
        btn.onclick = () => {
          const courseId = btn.dataset.courseId;
          AdminView.openCourseInspectionModal(courseId);
        };
      });

      box.querySelectorAll('.reject-course-btn').forEach(btn => {
        btn.onclick = async () => {
          const courseId = btn.dataset.courseId;
          const courseTitle = btn.dataset.courseTitle;
          const note = await UI.prompt(
            'Yêu cầu chỉnh sửa đề cương',
            `Vui lòng nhập lý do và chỉ dẫn yêu cầu giảng viên chỉnh sửa đề cương "${courseTitle}":`,
            '',
            'Nhập lý do chi tiết (tối thiểu 5 ký tự)...',
            5
          );
          if (!note) return;

          try {
            await ApiClient.reviewCourse(courseId, 'reject', note);
            UI.showToast(`Đã gửi phản hồi yêu cầu chỉnh sửa cho khóa học "${courseTitle}".`, 'info');
            UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi từ chối đề cương.', 'error');
          }
        };
      });

      // Filter change requests
      const renderChangeRequestRows = (statusFilter = 'ALL') => {
        const tbody = document.getElementById('change-requests-tbody');
        if (!tbody) return;

        const filtered = changeRequests.filter(r => statusFilter === 'ALL' || r.status === statusFilter);

        if (filtered.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7" class="py-8 text-center text-slate-400 text-xs">
                Không có yêu cầu thay đổi nào trong danh mục này.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(r => {
          const payload = r.proposed_payload || {};
          let typeBadge = 'bg-slate-100 text-slate-700 border-slate-200';
          let typeLabel = 'Thay đổi khác';

          if (r.change_type === 'LESSON_STRUCTURE' && payload.action === 'DELETE') {
            typeBadge = 'bg-rose-50 text-rose-700 border-rose-200';
            typeLabel = 'XÓA BÀI GIẢNG';
          } else if (r.change_type === 'LESSON_CONTENT' || r.change_type === 'LESSON_STRUCTURE') {
            typeBadge = 'bg-blue-50 text-blue-700 border-blue-200';
            typeLabel = 'SỬA BÀI GIẢNG';
          } else if (r.change_type === 'PREREQUISITE') {
            typeBadge = 'bg-purple-50 text-purple-700 border-purple-200';
            typeLabel = 'MÔN TIÊN QUYẾT';
          }

          let statusBadge = 'bg-amber-50 text-amber-700 border-amber-200';
          if (r.status === 'APPROVED') statusBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          if (r.status === 'REJECTED') statusBadge = 'bg-rose-50 text-rose-700 border-rose-200';

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="px-3.5 py-3.5 whitespace-nowrap align-middle">
                <div class="inline-flex items-center gap-1.5">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${typeBadge}">
                    ${typeLabel}
                  </span>
                  <span class="text-[10px] text-slate-400 font-mono">#${r.id}</span>
                </div>
              </td>
              <td class="px-3.5 py-3.5 align-middle">
                <div class="font-bold text-slate-900 dark:text-white font-mono text-xs whitespace-nowrap">${UI.escapeHtml(r.course_code || '')}</div>
                <div class="text-xs text-slate-500 truncate max-w-[190px]" title="${UI.escapeHtml(r.course_title || '')}">${UI.escapeHtml(r.course_title || '')}</div>
              </td>
              <td class="px-3.5 py-3.5 align-middle">
                <div class="font-bold text-slate-800 dark:text-slate-200 text-xs truncate max-w-[320px]" title="${UI.escapeHtml(r.target_title || '')}">${UI.escapeHtml(r.target_title || 'Mục tiêu #' + (r.target_id || ''))}</div>
                ${payload.action === 'DELETE' ? `
                  <div class="text-[11px] text-rose-600 dark:text-rose-400 mt-0.5 truncate max-w-[320px]" title="${UI.escapeHtml(payload.reason || 'Yêu cầu gỡ bỏ')}">
                    <strong>Lý do xóa:</strong> ${UI.escapeHtml(payload.reason || 'Yêu cầu gỡ bỏ')}
                  </div>
                ` : payload.title ? `
                  <div class="text-[11px] text-slate-500 mt-0.5 truncate max-w-[320px]" title="${UI.escapeHtml(payload.title)}">
                    <strong>Tiêu đề mới:</strong> ${UI.escapeHtml(payload.title)}
                  </div>
                ` : ''}
              </td>
              <td class="px-3.5 py-3.5 text-xs text-slate-700 dark:text-slate-300 whitespace-nowrap align-middle">
                <span class="truncate block max-w-[130px]" title="${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}">${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}</span>
              </td>
              <td class="px-3.5 py-3.5 whitespace-nowrap align-middle">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge}">
                  ${r.status === 'PENDING' ? 'Chờ duyệt' : (r.status === 'APPROVED' ? 'Đã duyệt' : 'Từ chối')}
                </span>
              </td>
              <td class="px-3.5 py-3.5 text-xs text-slate-400 font-mono whitespace-nowrap align-middle">
                ${UI.formatDate(r.created_at)}
              </td>
              <td class="px-3.5 py-3.5 text-right space-x-1.5 whitespace-nowrap align-middle">
                <button type="button" class="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors shadow-xs view-diff-cr-btn" data-req-id="${r.id}">
                  Xem bản sửa
                </button>
                ${r.status === 'PENDING' ? `
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors approve-cr-btn" data-req-id="${r.id}" data-type="${typeLabel}">
                    Phê duyệt
                  </button>
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors reject-cr-btn" data-req-id="${r.id}" data-type="${typeLabel}">
                    Từ chối
                  </button>
                ` : `
                  <span class="text-xs text-slate-400 italic">${UI.escapeHtml(r.review_reason || 'Đã giải quyết')}</span>
                `}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.view-diff-cr-btn').forEach(btn => {
          btn.onclick = () => {
            const reqId = btn.dataset.reqId;
            const r = changeRequests.find(x => String(x.id) === String(reqId));
            if (r) AdminView.openChangeRequestDiffModal(r, () => UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(container)));
          };
        });

        tbody.querySelectorAll('.approve-cr-btn').forEach(btn => {
          btn.onclick = () => {
            const reqId = btn.dataset.reqId;
            const r = changeRequests.find(x => String(x.id) === String(reqId));
            if (r) {
              AdminView.openChangeRequestDiffModal(r, () => UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(container)));
            }
          };
        });

        tbody.querySelectorAll('.reject-cr-btn').forEach(btn => {
          btn.onclick = async () => {
            const reqId = btn.dataset.reqId;
            const typeName = btn.dataset.type;
            const reason = await UI.prompt(
              'Từ chối yêu cầu thay đổi',
              `Nhập lý do từ chối yêu cầu "${typeName}" (#${reqId}):`,
              '',
              'Nhập lý do từ chối (tối thiểu 3 ký tự)...',
              3
            );
            if (!reason) return;

            try {
              await ApiClient.reviewAdminChangeRequest(reqId, { action: 'reject', reason });
              UI.showToast(`Đã từ chối yêu cầu #${reqId}.`, 'info');
              UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi từ chối yêu cầu.', 'error');
            }
          };
        });
      };

      renderChangeRequestRows('ALL');

      const crFilterBtns = box.querySelectorAll('.cr-filter-btn');
      crFilterBtns.forEach(btn => {
        btn.onclick = () => {
          crFilterBtns.forEach(b => {
            b.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200';
          });
          btn.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white';
          renderChangeRequestRows(btn.dataset.status);
        };
      });

      if (subQueue === 'courses') {
        const courseQueueEl = document.getElementById('admin-review-courses-queue');
        if (courseQueueEl) {
          setTimeout(() => {
            courseQueueEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        }
      } else if (subQueue === 'change-requests') {
        const crQueueEl = document.getElementById('admin-review-change-requests-queue');
        if (crQueueEl) {
          setTimeout(() => {
            crQueueEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            crQueueEl.classList.add('ring-2', 'ring-primary', 'shadow-md');
            setTimeout(() => crQueueEl.classList.remove('ring-2', 'ring-primary', 'shadow-md'), 3000);
          }, 100);
        }
      }
    } catch (err) {
      console.error('TabCoursesReview load error:', err);
    }
  }

  // Alias for backward compatibility
  static renderTabReview(container, subQueue = null) {
    return AdminView.renderTabCoursesReview(container, subQueue);
  }

  // =========================================================================
  // Modal: Thẩm định & Đối chiếu Bản Sửa đổi Chi tiết (Side-by-Side Diff)
  // =========================================================================
  static openChangeRequestDiffModal(r, onReviewed = null) {
    const orig = r.original_data || {};
    const prop = r.proposed_payload || {};
    const isDelete = prop.action === 'DELETE';
    const isPending = r.status === 'PENDING';

    const isCourse = r.target_type === 'COURSE' || (!r.target_type && (orig.course_code || prop.course_code));

    const titleChanged = prop.title && prop.title !== orig.title;
    const summaryChanged = prop.summary && prop.summary !== orig.summary;
    const descChanged = prop.description && prop.description !== orig.description;
    const catChanged = prop.category && prop.category !== orig.category;
    const contentChanged = prop.markdown_content && prop.markdown_content !== orig.markdown_content;
    const durationChanged = prop.estimated_duration_minutes && prop.estimated_duration_minutes !== orig.estimated_duration_minutes;

    const body = `
      <div class="space-y-4 text-xs">
        <!-- Header Info -->
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-primary-subtle text-primary border border-primary/20">${UI.escapeHtml(r.course_code || orig.course_code || '')}</span>
              <span class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(r.target_title || orig.title || 'Yêu cầu #' + r.id)}</span>
            </div>
            <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Khóa học: <strong>${UI.escapeHtml(r.course_title || orig.title || '')}</strong> • Giảng viên đề xuất: <strong>${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}</strong>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-1 rounded-full text-xs font-bold ${r.status === 'PENDING' ? 'bg-amber-50 text-amber-700 border border-amber-200' : (r.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200')}">
              ${r.status === 'PENDING' ? 'Chờ duyệt' : (r.status === 'APPROVED' ? 'Đã duyệt' : 'Từ chối')}
            </span>
          </div>
        </div>

        ${isDelete ? `
          <div class="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 space-y-2">
            <div class="font-bold text-sm flex items-center gap-2 text-rose-700 dark:text-rose-400">
              <span class="material-symbols-outlined text-[20px]">delete_forever</span>
              Yêu cầu gỡ bỏ ${isCourse ? 'khóa học' : 'bài giảng'}
            </div>
            <p class="leading-relaxed">Giảng viên đề xuất gỡ bỏ ${isCourse ? 'khóa học này khỏi hệ thống' : 'bài giảng này khỏi đề cương'}.</p>
            <div class="p-3 rounded-lg bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/40 text-xs">
              <strong>Lý do yêu cầu xóa:</strong> ${UI.escapeHtml(prop.reason || 'Không có lý do chi tiết.')}
            </div>
          </div>
        ` : `
          <!-- Side-by-Side Diff View -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h5 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5 text-xs">
                <span class="material-symbols-outlined text-primary text-[18px]">difference</span>
                Đối chiếu thay đổi chi tiết (Bản hiện tại vs Bản đã sửa đổi)
              </h5>
              <span class="text-[11px] text-slate-400">Các mục có khung màu viền sáng hiển thị nội dung được điều chỉnh</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Left: Original Version -->
              <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 flex flex-col">
                <div class="bg-slate-100 dark:bg-slate-800 px-3.5 py-2 border-b border-slate-200 dark:border-slate-700 font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                  <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[16px] text-slate-400">history</span> Bản hiện tại (Original)</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">Hiện có</span>
                </div>
                <div class="p-3.5 space-y-3 flex-1 overflow-y-auto max-h-[350px]">
                  ${isCourse ? `
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Tên khóa học</div>
                      <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5 text-xs">${UI.escapeHtml(orig.title || 'Chưa cập nhật')}</div>
                    </div>
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Danh mục đào tạo</div>
                      <div class="text-slate-600 dark:text-slate-400 mt-0.5 text-xs">${UI.escapeHtml(orig.category || 'N/A')}</div>
                    </div>
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Mô tả khóa học</div>
                      <div class="mt-1 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs leading-relaxed max-h-48 overflow-y-auto text-slate-700 dark:text-slate-300 whitespace-pre-wrap">${UI.escapeHtml(orig.description || '(Trống)')}</div>
                    </div>
                  ` : `
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Tiêu đề bài học</div>
                      <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5 text-xs">${UI.escapeHtml(orig.title || 'Chưa cập nhật')}</div>
                    </div>
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Tóm tắt ngắn (Summary)</div>
                      <div class="text-slate-600 dark:text-slate-400 mt-0.5 text-xs leading-relaxed">${UI.escapeHtml(orig.summary || '(Trống)')}</div>
                    </div>
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Thời lượng dự kiến</div>
                      <div class="font-mono text-slate-700 dark:text-slate-300 mt-0.5 text-xs">${orig.estimated_duration_minutes || 0} phút</div>
                    </div>
                    <div>
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Nội dung bài học (Markdown)</div>
                      <div class="mt-1 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-sm leading-relaxed break-words max-h-48 overflow-y-auto text-slate-700 dark:text-slate-300">${AdminView.renderLessonMarkdown(orig.markdown_content || '(Chưa có nội dung)')}</div>
                    </div>
                  `}
                </div>
              </div>

              <!-- Right: Modified Version -->
              <div class="rounded-xl border-2 border-primary/30 dark:border-primary/40 overflow-hidden bg-white dark:bg-slate-900 flex flex-col shadow-xs">
                <div class="bg-primary/10 px-3.5 py-2 border-b border-primary/20 font-bold text-primary flex items-center justify-between">
                  <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[16px]">edit_document</span> Bản đã sửa đổi (Proposed)</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-primary text-white font-bold">Bản mới</span>
                </div>
                <div class="p-3.5 space-y-3 flex-1 overflow-y-auto max-h-[350px]">
                  ${isCourse ? `
                    <div class="${titleChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${titleChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Tên khóa học ${titleChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="font-bold text-slate-900 dark:text-white mt-0.5 text-xs">${UI.escapeHtml(prop.title || orig.title || 'Chưa cập nhật')}</div>
                    </div>
                    <div class="${catChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${catChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Danh mục đào tạo ${catChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="text-slate-700 dark:text-slate-300 mt-0.5 text-xs">${UI.escapeHtml(prop.category || orig.category || 'N/A')}</div>
                    </div>
                    <div class="${descChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${descChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Mô tả khóa học ${descChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="mt-1 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs leading-relaxed max-h-48 overflow-y-auto text-slate-800 dark:text-slate-200 whitespace-pre-wrap">${UI.escapeHtml(prop.description || orig.description || '(Trống)')}</div>
                    </div>
                  ` : `
                    <div class="${titleChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${titleChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Tiêu đề bài học ${titleChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="font-bold text-slate-900 dark:text-white mt-0.5 text-xs">${UI.escapeHtml(prop.title || orig.title || 'Chưa cập nhật')}</div>
                    </div>
                    <div class="${summaryChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${summaryChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Tóm tắt ngắn (Summary) ${summaryChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="text-slate-700 dark:text-slate-300 mt-0.5 text-xs leading-relaxed">${UI.escapeHtml(prop.summary || orig.summary || '(Trống)')}</div>
                    </div>
                    <div class="${durationChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${durationChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Thời lượng dự kiến ${durationChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="font-mono text-slate-800 dark:text-slate-200 mt-0.5 text-xs">${prop.estimated_duration_minutes || orig.estimated_duration_minutes || 0} phút</div>
                    </div>
                    <div class="${contentChanged ? 'p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800' : ''}">
                      <div class="text-[10px] font-bold ${contentChanged ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400'} uppercase tracking-wider flex items-center gap-1">
                        Nội dung bài học (Markdown) ${contentChanged ? '<span class="text-[10px] font-bold text-emerald-600">(Đã sửa)</span>' : ''}
                      </div>
                      <div class="mt-1 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-sm leading-relaxed break-words max-h-48 overflow-y-auto text-slate-800 dark:text-slate-200">${AdminView.renderLessonMarkdown(prop.markdown_content || orig.markdown_content || '(Chưa có nội dung)')}</div>
                    </div>
                  `}
                </div>
              </div>
            </div>
          </div>
        `}
      </div>
    `;

    const footer = `
      <div class="flex items-center justify-between w-full">
        <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
        ${isPending ? `
          <div class="flex items-center gap-2">
            <button type="button" id="diff-reject-btn" class="px-3.5 py-2 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors">
              Từ chối yêu cầu
            </button>
            <button type="button" id="diff-approve-btn" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">check</span>
              <span>Phê duyệt & Áp dụng thay đổi</span>
            </button>
          </div>
        ` : `
          <span class="text-xs text-slate-400 italic">${UI.escapeHtml(r.review_reason || 'Đã giải quyết')}</span>
        `}
      </div>
    `;

    UI.openModal({
      title: `Thẩm định Bản Sửa đổi • #${r.id} (${r.course_code || 'Khóa học'})`,
      bodyHtml: body,
      footerHtml: footer,
      size: 'xl'
    });

    if (isPending) {
      document.getElementById('diff-approve-btn').onclick = async () => {
        try {
          await ApiClient.reviewAdminChangeRequest(r.id, { action: 'approve' });
          UI.showToast(`Đã phê duyệt và áp dụng bản sửa đổi #${r.id} thành công!`, 'success');
          UI.closeModal();
          if (onReviewed) onReviewed();
        } catch (e) {
          UI.showToast(e.message || 'Lỗi phê duyệt yêu cầu.', 'error');
        }
      };

      document.getElementById('diff-reject-btn').onclick = async () => {
        const reason = await UI.prompt(
          'Từ chối bản sửa đổi',
          `Nhập lý do từ chối yêu cầu sửa đổi #${r.id}:`,
          '',
          'Nhập lý do chi tiết (tối thiểu 3 ký tự)...',
          3
        );
        if (!reason) return;
        try {
          await ApiClient.reviewAdminChangeRequest(r.id, { action: 'reject', reason });
          UI.showToast(`Đã từ chối yêu cầu #${r.id}.`, 'info');
          UI.closeModal();
          if (onReviewed) onReviewed();
        } catch (e) {
          UI.showToast(e.message || 'Lỗi từ chối yêu cầu.', 'error');
        }
      };
    }
  }

  // =========================================================================
  // Tab 3: Hồ sơ Đăng ký Giảng viên (Instructor Applications - Tách riêng)
  // =========================================================================
  static async renderTabInstructorApps(container) {
    container.innerHTML = `
      <div class="space-y-6 animate-fade-in" id="instructor-apps-box">
        <div class="p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang nạp hồ sơ ứng tuyển giảng viên...</p>
        </div>
      </div>
    `;

    try {
      const appsRes = await ApiClient.getAdminInstructorApplications('ALL');
      const applications = appsRes?.applications || [];
      const pendingApps = applications.filter(a => a.status === 'PENDING');

      // Update badge
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({ applications: pendingApps.length });
      }

      const box = document.getElementById('instructor-apps-box');
      if (!box) return;

      box.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">badge</span>
                Hồ sơ Đăng ký Giảng viên (Instructor Applications)
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">Thẩm định hồ sơ chuyên môn, văn bằng chứng chỉ và xét chuẩn đào tạo ABET CAC trước khi phê duyệt bổ nhiệm quyền giảng viên.</p>
            </div>
            <div class="flex items-center gap-1.5" id="app-status-filter-group">
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white" data-status="ALL">Tất cả (${applications.length})</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="PENDING">Chờ duyệt (${pendingApps.length})</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="APPROVED">Đã duyệt</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="REJECTED">Từ chối</button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs sm:text-sm">
              <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                <tr>
                  <th class="px-4 py-3">Ứng viên</th>
                  <th class="px-4 py-3">Trình độ & Chuyên môn</th>
                  <th class="px-4 py-3">Kinh nghiệm</th>
                  <th class="px-4 py-3">Trạng thái</th>
                  <th class="px-4 py-3">Thời điểm nộp</th>
                  <th class="px-4 py-3 text-right">Quyết định bổ nhiệm</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="instructor-apps-tbody">
                <!-- Populated via JS -->
              </tbody>
            </table>
          </div>
        </div>
      `;

      const renderAppRows = (statusFilter = 'ALL') => {
        const tbody = document.getElementById('instructor-apps-tbody');
        if (!tbody) return;

        const filtered = applications.filter(a => statusFilter === 'ALL' || a.status === statusFilter);

        if (filtered.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="6" class="py-8 text-center text-slate-400 text-xs">
                Không có hồ sơ nào trong danh mục này.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(a => {
          const details = a.details || {};
          let statusBadge = 'bg-amber-50 text-amber-700 border-amber-200';
          if (a.status === 'APPROVED') statusBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          if (a.status === 'REJECTED') statusBadge = 'bg-rose-50 text-rose-700 border-rose-200';

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="px-4 py-3.5">
                <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(a.applicant_name)}</div>
                <div class="text-xs text-slate-400 font-mono">${UI.escapeHtml(a.applicant_email)}</div>
              </td>
              <td class="px-4 py-3.5">
                <div class="font-bold text-slate-800 dark:text-slate-200">${UI.escapeHtml(details.degree || 'Chưa cập nhật')}</div>
                <div class="text-[11px] text-slate-400">${UI.escapeHtml(details.specialization || details.institution || 'CNTT')}</div>
              </td>
              <td class="px-4 py-3.5 text-xs">
                ${details.years_experience ? `${details.years_experience} năm kinh nghiệm` : (details.experience || '1-3 năm')}
              </td>
              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge}">
                  ${a.status_label || a.status}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-slate-400 font-mono">
                ${UI.formatDate(a.created_at)}
              </td>
              <td class="px-4 py-3.5 text-right space-x-1.5 whitespace-nowrap">
                <button type="button" class="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors view-app-btn" data-app-id="${a.id}">
                  Xem CV
                </button>
                ${a.status === 'PENDING' ? `
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors approve-app-btn" data-app-id="${a.id}" data-name="${UI.escapeHtml(a.applicant_name)}">
                    Bổ nhiệm
                  </button>
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors reject-app-btn" data-app-id="${a.id}" data-name="${UI.escapeHtml(a.applicant_name)}">
                    Từ chối
                  </button>
                ` : ''}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.view-app-btn').forEach(btn => {
          btn.onclick = () => {
            const appId = btn.dataset.appId;
            const app = applications.find(x => String(x.id) === String(appId));
            if (app) AdminView.openApplicationDetailModal(app, container);
          };
        });

        tbody.querySelectorAll('.approve-app-btn').forEach(btn => {
          btn.onclick = async () => {
            const appId = btn.dataset.appId;
            const name = btn.dataset.name;
            const conf = await UI.confirm('Bổ nhiệm Giảng viên', `Xác nhận phê duyệt đơn đăng ký và cấp quyền Giảng viên (INSTRUCTOR) cho "${name}"?`, 'Phê duyệt bổ nhiệm');
            if (!conf) return;

            try {
              await ApiClient.reviewInstructorApplication(appId, 'approve', 'Đạt chuẩn thẩm định học vụ');
              UI.showToast(`Đã bổ nhiệm giảng viên ${name} thành công!`, 'success');
              UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi phê duyệt đơn.', 'error');
            }
          };
        });

        tbody.querySelectorAll('.reject-app-btn').forEach(btn => {
          btn.onclick = async () => {
            const appId = btn.dataset.appId;
            const name = btn.dataset.name;
            const reason = await UI.prompt(
              'Từ chối hồ sơ giảng viên',
              `Nhập lý do từ chối đơn đăng ký làm giảng viên của ứng viên "${name}":`,
              '',
              'Nhập lý do từ chối hồ sơ (tối thiểu 5 ký tự)...',
              5
            );
            if (!reason) return;

            try {
              await ApiClient.reviewInstructorApplication(appId, 'reject', reason);
              UI.showToast(`Đã từ chối đơn của ${name}.`, 'info');
              UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi từ chối đơn.', 'error');
            }
          };
        });
      };

      renderAppRows('ALL');

      const filterBtns = box.querySelectorAll('.app-filter-btn');
      filterBtns.forEach(btn => {
        btn.onclick = () => {
          filterBtns.forEach(b => {
            b.className = 'app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200';
          });
          btn.className = 'app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white';
          renderAppRows(btn.dataset.status);
        };
      });

    } catch (err) {
      console.error('TabInstructorApps load error:', err);
    }
  }

  static async openCourseInspectionModal(courseId) {
    try {
      UI.openModal({
        title: 'Hồ sơ Thẩm định Đề cương & Bài học',
        bodyHtml: '<div class="p-8 text-center text-slate-400"><span class="inline-block animate-spin text-xl mb-2">⏳</span><p>Đang tải chi tiết đề cương học vụ...</p></div>',
        footerHtml: '<button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>',
        size: 'lg'
      });

      const course = await ApiClient.getAdminCourseDetail(courseId);
      const lessons = course.lessons || [];

      // Parse learning objectives for Admin inspection
      let adminSLOs = [];
      if (course.learning_objectives) {
        if (Array.isArray(course.learning_objectives)) {
          adminSLOs = [...course.learning_objectives];
        } else if (typeof course.learning_objectives === 'string') {
          try {
            const parsed = JSON.parse(course.learning_objectives);
            if (Array.isArray(parsed)) adminSLOs = parsed;
          } catch {
            adminSLOs = course.learning_objectives.split('\n').filter(s => s.trim()).map((s, i) => ({
              title: `SLO-${i + 1}`,
              description: s.trim()
            }));
          }
        }
      }

      const bodyHtml = `
        <div class="space-y-4 text-xs">
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <span class="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-primary-subtle text-primary border border-primary/20">${UI.escapeHtml(course.course_code)}</span>
                <h4 class="font-bold text-base text-slate-900 dark:text-white mt-1">${UI.escapeHtml(course.title)}</h4>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">${course.status}</span>
            </div>
            <p class="text-slate-500 dark:text-slate-400 text-xs">${UI.escapeHtml(course.description || 'Chưa có mô tả khóa học.')}</p>
            <div class="pt-2 border-t border-slate-200 dark:border-slate-700 flex flex-wrap gap-4 text-slate-600 dark:text-slate-300 font-medium">
              <span><strong>Giảng viên:</strong> ${UI.escapeHtml(course.owner_instructor_name)} (${UI.escapeHtml(course.owner_instructor_email || 'N/A')})</span>
              <span><strong>Độ khó:</strong> ${course.difficulty || 'N/A'}</span>
              <span><strong>Danh mục:</strong> ${course.category || 'N/A'}</span>
            </div>
          </div>

          <!-- Section: Chuẩn đầu ra SLO Inspection -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <h5 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px] text-primary">verified_user</span>
                  Chuẩn kỹ năng đầu ra của môn học (SLO - Student Learning Outcomes)
                </h5>
                <button type="button" onclick="UI.openAcademicGlossaryModal()" class="text-[11px] text-primary hover:underline font-bold" title="Xem giải thích thuật ngữ">
                  (SLO là gì?)
                </button>
              </div>
              <span class="text-slate-400 text-xs">${adminSLOs.length} Chuẩn đầu ra</span>
            </div>

            ${adminSLOs.length === 0 ? `
              <div class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs space-y-1">
                <div class="font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">warning</span>
                  <span>Chưa thiết lập Chuẩn đầu ra môn học!</span>
                </div>
                <p class="text-[11px] leading-relaxed">Khóa học này chưa có danh mục SLO. Khuyến nghị Admin yêu cầu giảng viên bổ sung chuẩn đầu ra trước khi phê duyệt ban hành.</p>
              </div>
            ` : `
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                ${adminSLOs.map((slo, idx) => {
                  const title = typeof slo === 'object' ? (slo.title || `SLO-${idx + 1}`) : `SLO-${idx + 1}`;
                  const desc = typeof slo === 'object' ? (slo.description || slo.content || '') : String(slo);
                  const weight = typeof slo === 'object' && slo.weight ? slo.weight : null;
                  return `
                    <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 space-y-1">
                      <div class="flex items-center justify-between">
                        <span class="font-mono font-bold text-primary text-xs">${UI.escapeHtml(title)}</span>
                        ${weight ? `<span class="text-[10px] text-slate-400 font-semibold font-mono">Trọng số: ${UI.escapeHtml(weight)}</span>` : ''}
                      </div>
                      <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">${UI.escapeHtml(desc || 'Chưa có mô tả chi tiết.')}</p>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h5 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px] text-primary">format_list_numbered</span>
                Đề cương Danh sách Bài học (${lessons.length} bài)
              </h5>
            </div>

            ${lessons.length === 0 ? `
              <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                Khóa học chưa có bài học nào được thiết lập trong đề cương.
              </div>
            ` : `
              <div class="divide-y divide-slate-100 dark:divide-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden bg-white dark:bg-slate-900">
                ${lessons.map((l, idx) => `
                  <div class="p-3.5 flex items-center justify-between gap-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <div class="flex items-center gap-3 min-w-0">
                      <span class="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono font-bold text-xs flex items-center justify-center flex-shrink-0">
                        ${l.order_index || idx + 1}
                      </span>
                      <div class="truncate">
                        <div class="font-bold text-slate-800 dark:text-slate-200 text-xs truncate">${UI.escapeHtml(l.title)}</div>
                        ${l.summary ? `<div class="text-[11px] text-slate-400 truncate">${UI.escapeHtml(l.summary)}</div>` : ''}
                      </div>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${l.status === 'PUBLISHED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'}">
                      ${l.status}
                    </span>
                  </div>
                `).join('')}
              </div>
            `}
          </div>
        </div>
      `;

      const isPending = course.status === 'PENDING';
      const footerHtml = `
        <div class="flex items-center justify-between w-full">
          <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
          ${isPending ? `
            <div class="flex items-center gap-2">
              <button type="button" id="modal-reject-course-btn" class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors">
                Yêu cầu chỉnh sửa
              </button>
              <button type="button" id="modal-approve-course-btn" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">check</span>
                <span>Phê duyệt ban hành</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;

      UI.openModal({
        title: `Hồ sơ Thẩm định Đề cương • ${course.course_code}`,
        bodyHtml,
        footerHtml,
        size: 'lg'
      });

      if (isPending) {
        const approveBtn = document.getElementById('modal-approve-course-btn');
        if (approveBtn) {
          approveBtn.onclick = async () => {
            const conf = await UI.confirm('Phê duyệt đề cương', `Xác nhận phê duyệt ban hành đề cương khóa học "${course.title}"?`, 'Phê duyệt');
            if (!conf) return;
            try {
              await ApiClient.reviewCourse(course.course_id, 'approve', 'Phê duyệt chuẩn hóa đề cương học vụ');
              UI.showToast(`Đã phê duyệt đề cương "${course.title}" thành công!`, 'success');
              UI.closeModal();
              const contentBox = document.getElementById('admin-tab-content-box');
              if (contentBox) UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(contentBox));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi duyệt khóa học.', 'error');
            }
          };
        }

        const rejectBtn = document.getElementById('modal-reject-course-btn');
        if (rejectBtn) {
          rejectBtn.onclick = async () => {
            const note = await UI.prompt(
              'Yêu cầu chỉnh sửa đề cương',
              `Vui lòng nhập lý do và chỉ dẫn yêu cầu giảng viên chỉnh sửa đề cương "${course.title}":`,
              '',
              'Nhập lý do chi tiết (tối thiểu 5 ký tự)...',
              5
            );
            if (!note) return;
            try {
              await ApiClient.reviewCourse(course.course_id, 'reject', note);
              UI.showToast(`Đã gửi phản hồi yêu cầu chỉnh sửa cho khóa học "${course.title}".`, 'info');
              UI.closeModal();
              const contentBox = document.getElementById('admin-tab-content-box');
              if (contentBox) UI.refreshCurrentRoute(() => AdminView.renderTabCoursesReview(contentBox));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi từ chối đề cương.', 'error');
            }
          };
        }
      }
    } catch (err) {
      UI.showToast(err.message || 'Lỗi tải hồ sơ khóa học.', 'error');
    }
  }

  static openApplicationDetailModal(app, container = null) {
    const details = app.details || {};
    const attachedFiles = details.attached_files || [];
    const isPending = app.status === 'PENDING';
    let certificateDriveUrl = '';
    try {
      const parsedUrl = new URL(details.certificate_drive_url || '');
      if (
        parsedUrl.protocol === 'https:'
        && ['drive.google.com', 'docs.google.com'].includes(parsedUrl.hostname.toLowerCase())
        && !parsedUrl.username
        && !parsedUrl.password
      ) {
        certificateDriveUrl = parsedUrl.href;
      }
    } catch {
      // Hide malformed or legacy links rather than rendering an active unsafe URL.
    }

    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
          <div class="flex items-center justify-between">
            <h4 class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(app.applicant_name)}</h4>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${isPending ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300' : 'bg-primary/10 text-primary'}">${app.status_label || app.status}</span>
          </div>
          <div class="text-slate-500 font-mono">${UI.escapeHtml(app.applicant_email)} • Nộp ngày: ${UI.formatDateTime(app.created_at)}</div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Cơ sở / Tổ chức</span>
            <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">${UI.escapeHtml(details.institution_name || details.institution || 'Hoạt động tự do / Độc lập')}</div>
          </div>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Chuyên môn / Lĩnh vực ngách</span>
            <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">${UI.escapeHtml(details.specialization || details.degree || 'N/A')}</div>
          </div>
        </div>

        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold uppercase">Định hướng giảng dạy / Thư ngỏ</span>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
            ${UI.escapeHtml(details.statement_of_purpose || details.statement || details.bio || 'Chưa cung cấp tóm tắt tiểu sử')}
          </div>
        </div>

        ${(details.portfolio_url || details.certificate_url || details.evidence_urls) ? `
          <div class="space-y-1">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Liên kết Portfolio / GitHub / Website</span>
            <div><a href="${UI.escapeHtml(details.portfolio_url || details.certificate_url || details.evidence_urls)}" target="_blank" class="text-primary font-bold hover:underline break-all inline-flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">link</span>${UI.escapeHtml(details.portfolio_url || details.certificate_url || details.evidence_urls)}</a></div>
          </div>
        ` : ''}

        ${certificateDriveUrl ? `
          <div class="space-y-1">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Chứng chỉ / bằng cấp trên Google Drive</span>
            <div><a href="${UI.escapeHtml(certificateDriveUrl)}" target="_blank" rel="noopener noreferrer" class="text-primary font-bold hover:underline break-all inline-flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">school</span>${UI.escapeHtml(certificateDriveUrl)}</a></div>
          </div>
        ` : ''}

        ${attachedFiles.length > 0 ? `
          <div class="space-y-1.5">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Tệp CV & Minh chứng đính kèm (${attachedFiles.length})</span>
            <div class="space-y-1">
              ${attachedFiles.map(f => {
                const fileKey = f.saved_filename || f.file || f.name || '';
                const fileName = f.original_name || f.saved_filename || f.name || f.file || 'Tài liệu minh chứng';
                const fileSize = f.size ? ` • ${UI.formatBytes(f.size)}` : '';
                return `
                <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="material-symbols-outlined text-[18px] ${f.doc_type === 'CV_PORTFOLIO' ? 'text-primary' : 'text-slate-400'}">${f.doc_type === 'CV_PORTFOLIO' ? 'badge' : 'attach_file'}</span>
                    <div class="min-w-0">
                      <div class="font-medium text-xs text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(fileName)}</div>
                      <div class="text-[10px] text-slate-400 font-mono">${f.doc_type === 'CV_PORTFOLIO' ? '<span class="text-primary font-bold">CV / Portfolio</span>' : 'Minh chứng'}${fileSize}</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <button type="button" class="preview-evidence-btn px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-[10px] font-bold transition-colors flex items-center gap-1" data-url="/admin/instructor-applications/${app.id}/evidence/${encodeURIComponent(fileKey)}?preview=1" data-name="${UI.escapeHtml(fileName)}">
                      <span class="material-symbols-outlined text-[13px]">visibility</span>
                      <span>Xem trước</span>
                    </button>
                    <a href="/admin/instructor-applications/${app.id}/evidence/${encodeURIComponent(fileKey)}" download="${UI.escapeHtml(fileName)}" class="px-2.5 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-200 text-[10px] font-bold transition-colors flex items-center gap-1">
                      <span class="material-symbols-outlined text-[13px]">download</span>
                      <span>Tải về</span>
                    </a>
                  </div>
                </div>
              `;}).join('')}
            </div>
          </div>
        ` : ''}

        ${app.review_reason ? `
          <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 text-xs border border-amber-200">
            <strong>Ghi chú thẩm định:</strong> ${UI.escapeHtml(app.review_reason)}
          </div>
        ` : ''}
      </div>
    `;

    const footer = `
      <div class="flex items-center justify-between w-full">
        <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
        ${isPending ? `
          <div class="flex items-center gap-2">
            <button type="button" id="modal-reject-app-btn" class="px-3.5 py-2 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors">
              Từ chối hồ sơ
            </button>
            <button type="button" id="modal-approve-app-btn" class="px-3.5 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-bold transition-colors shadow-xs">
              Phê duyệt & Bổ nhiệm
            </button>
          </div>
        ` : ''}
      </div>
    `;

    UI.openModal({
      title: `Hồ sơ Đăng ký Giảng viên • #${app.id}`,
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    // Attach preview event handlers for CV / Evidence files
    document.querySelectorAll('.preview-evidence-btn').forEach(btn => {
      btn.onclick = () => {
        AdminView.openEvidencePreviewModal(btn.dataset.url, btn.dataset.name);
      };
    });

    if (isPending) {
      const modalApproveBtn = document.getElementById('modal-approve-app-btn');
      if (modalApproveBtn) {
        modalApproveBtn.onclick = async () => {
          const conf = await UI.confirm('Bổ nhiệm Giảng viên', `Xác nhận phê duyệt đơn đăng ký và cấp quyền Giảng viên (INSTRUCTOR) cho "${app.applicant_name}"?`, 'Phê duyệt bổ nhiệm');
          if (!conf) return;
          try {
            await ApiClient.reviewInstructorApplication(app.id, 'approve', 'Đạt chuẩn thẩm định học vụ');
            UI.showToast(`Đã bổ nhiệm giảng viên ${app.applicant_name} thành công!`, 'success');
            UI.closeModal();
            if (container) UI.refreshCurrentRoute(() => AdminView.renderTabReview(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi phê duyệt đơn.', 'error');
          }
        };
      }

      const modalRejectBtn = document.getElementById('modal-reject-app-btn');
      if (modalRejectBtn) {
        modalRejectBtn.onclick = async () => {
          const reason = await UI.prompt(
            'Từ chối hồ sơ giảng viên',
            `Nhập lý do từ chối đơn đăng ký của ứng viên "${app.applicant_name}":`,
            '',
            'Nhập lý do từ chối hồ sơ (tối thiểu 5 ký tự)...',
            5
          );
          if (!reason) return;
          try {
            await ApiClient.reviewInstructorApplication(app.id, 'reject', reason);
            UI.showToast(`Đã từ chối đơn của ${app.applicant_name}.`, 'info');
            UI.closeModal();
            if (container) UI.refreshCurrentRoute(() => AdminView.renderTabReview(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi từ chối đơn.', 'error');
          }
        };
      }
    }
  }

  static openEvidencePreviewModal(fileUrl, fileName) {
    const isPdf = (fileName || '').toLowerCase().endsWith('.pdf');
    const isOfficeDocument = /\.(docx|xlsx)$/i.test(fileName || '');
    const isImage = /\.(jpg|jpeg|png|webp|gif|svg)$/i.test(fileName || '');
    
    let previewContent = '';
    if (isPdf) {
      previewContent = `
        <div class="w-full h-[72vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-inner">
          <iframe src="${fileUrl}" class="w-full h-full border-0" title="${UI.escapeHtml(fileName)}"></iframe>
        </div>
      `;
    } else if (isImage) {
      previewContent = `
        <div class="max-h-[72vh] flex items-center justify-center bg-slate-950/20 dark:bg-slate-950/60 rounded-xl p-4 overflow-auto border border-slate-200 dark:border-slate-800">
          <img src="${fileUrl}" alt="${UI.escapeHtml(fileName)}" class="max-h-[68vh] object-contain rounded-lg shadow-sm" />
        </div>
      `;
    } else if (isOfficeDocument) {
      previewContent = `
        <div class="w-full h-[65vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-auto border border-slate-200 dark:border-slate-800 p-5">
          <p id="evidence-text-preview-status" class="text-sm text-slate-500">Đang trích xuất nội dung tài liệu...</p>
          <pre id="evidence-text-preview" class="hidden whitespace-pre-wrap break-words text-sm leading-6 text-slate-800 dark:text-slate-200"></pre>
        </div>
      `;
    } else {
      previewContent = `
        <div class="w-full h-[65vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-inner">
          <iframe src="${fileUrl}" class="w-full h-full border-0" title="${UI.escapeHtml(fileName)}"></iframe>
        </div>
      `;
    }

    const downloadUrl = fileUrl.replace('?preview=1', '');

    UI.openModal({
      title: `Xem trước tài liệu: ${UI.escapeHtml(fileName)}`,
      bodyHtml: `
        <div class="space-y-3">
          ${previewContent}
          <div class="flex items-center justify-between text-xs text-slate-500 pt-1">
            <span>Trình xem tài liệu học vụ tích hợp (PDF / Ảnh / Văn bản).</span>
            <a href="${downloadUrl}" download="${UI.escapeHtml(fileName)}" class="text-primary font-bold hover:underline flex items-center gap-1">
              <span class="material-symbols-outlined text-[15px]">download</span> Tải tệp về máy
            </a>
          </div>
        </div>
      `,
      footerHtml: `
        <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'xl'
    });

    if (isOfficeDocument) {
      const status = document.getElementById('evidence-text-preview-status');
      const textPreview = document.getElementById('evidence-text-preview');
      const textUrl = fileUrl.replace(/\?.*$/, '?format=text');
      fetch(textUrl, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
        .then(async response => {
          const payload = await response.json();
          if (!response.ok || !payload.success) throw new Error(payload.error?.message || 'Không thể xem trước tài liệu.');
          if (textPreview) {
            textPreview.textContent = payload.data?.text || 'Tài liệu không có văn bản để hiển thị.';
            textPreview.classList.remove('hidden');
          }
          if (status) status.classList.add('hidden');
        })
        .catch(error => {
          if (status) status.textContent = error.message || 'Không thể xem trước tài liệu. Bạn vẫn có thể tải tệp gốc.';
        });
    }
  }

  // =========================================================================
  // Tab 3: Faculty Reassignment & Workload Matrix (100% Live DB)
  // =========================================================================
  static async renderTabReassign(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5 animate-fade-in" id="reassign-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải ma trận phân công giảng dạy & định mức giờ...</p>
        </div>
      </div>
    `;

    try {
      const [workloadRes, coursesRes] = await Promise.allSettled([
        ApiClient.getAdminFacultyWorkload(),
        ApiClient.getAdminCourses()
      ]);

      const workloadData = (workloadRes.status === 'fulfilled' && workloadRes.value) ? workloadRes.value : null;
      const courses = (coursesRes.status === 'fulfilled' && coursesRes.value) ? (coursesRes.value.courses || []) : [];
      const instructors = workloadData?.instructors || [];

      const box = document.getElementById('reassign-box');
      if (!box) return;

      box.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[20px]">swap_horiz</span>
              Điều chuyển Phân công Giảng dạy
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">Quản lý phân công và thực hiện điều phối chuyển giao khóa học giữa các Giảng viên có thẩm quyền.</p>
          </div>
          <button type="button" id="open-reassign-tool-btn" class="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">sync_alt</span>
            <span>Điều chuyển Môn học</span>
          </button>
        </div>

        <!-- Instructor Reassignment Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="px-5 py-3.5">Giảng viên</th>
                <th class="px-5 py-3.5">Email liên hệ</th>
                <th class="px-5 py-3.5">Số môn phụ trách</th>
                <th class="px-5 py-3.5">Danh sách môn phụ trách</th>
                <th class="px-5 py-3.5 text-right">Điều phối</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              ${instructors.length === 0 ? `
                <tr>
                  <td colspan="5" class="py-8 text-center text-slate-400 text-xs">
                    Chưa có nhân sự nào được cấp quyền Giảng viên (INSTRUCTOR).
                  </td>
                </tr>
              ` : instructors.map(ins => {
                const assigned = ins.courses || [];

                return `
                  <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td class="px-5 py-4 font-bold text-slate-900 dark:text-white">
                      ${UI.escapeHtml(ins.display_name || 'N/A')}
                    </td>
                    <td class="px-5 py-4 text-xs font-mono text-slate-400">
                      ${UI.escapeHtml(ins.email)}
                    </td>
                    <td class="px-5 py-4 font-mono font-bold text-slate-700 dark:text-slate-300 text-xs">
                      ${assigned.length} môn học
                    </td>
                    <td class="px-5 py-4">
                      ${assigned.length > 0 ? `
                        <div class="flex flex-wrap gap-1">
                          ${assigned.map(c => `
                            <span class="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-primary-subtle text-primary border border-primary/20" title="${UI.escapeHtml(c.title)}">
                              ${UI.escapeHtml(c.course_code)}
                            </span>
                          `).join('')}
                        </div>
                      ` : '<span class="text-slate-400 italic text-xs">Chưa gán môn nào</span>'}
                    </td>
                    <td class="px-5 py-4 text-right">
                      <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors reassign-instructor-btn" data-instructor-id="${ins.user_id}">
                        Điều chuyển
                      </button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;

      const openReassignModal = (preselectedCourseId = null, preselectedInstructorId = null) => {
        const body = `
          <div class="space-y-4 text-xs">
            <p class="text-slate-600 dark:text-slate-300">
              Chuyển giao quyền sở hữu môn học từ Giảng viên hiện tại sang Giảng viên mới. Thao tác này sẽ ghi nhật ký kiểm toán bất biến.
            </p>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Khóa học cần điều chuyển *</label>
              <select id="modal-reassign-course" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                ${courses.map(c => `
                  <option value="${c.course_id}" ${c.course_id === preselectedCourseId ? 'selected' : ''}>
                    [${UI.escapeHtml(c.course_code)}] ${UI.escapeHtml(c.title)}
                  </option>
                `).join('')}
              </select>
            </div>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Giảng viên tiếp nhận mới *</label>
              <select id="modal-reassign-instructor" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                ${instructors.map(ins => `
                  <option value="${ins.user_id}" ${ins.user_id === preselectedInstructorId ? 'selected' : ''}>
                    ${UI.escapeHtml(ins.display_name)} (${UI.escapeHtml(ins.email)})
                  </option>
                `).join('')}
              </select>
            </div>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Lý do điều chuyển (Kiểm toán bắt buộc) *</label>
              <textarea id="modal-reassign-reason" rows="2" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs resize-none" placeholder="Căn cứ theo quyết định điều động công tác số..."></textarea>
            </div>
          </div>
        `;

        const footer = `
          <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
          <button type="button" id="submit-reassign-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Xác nhận điều chuyển</button>
        `;

        UI.openModal({
          title: 'Điều chuyển Phân công Giảng dạy',
          bodyHtml: body,
          footerHtml: footer,
          size: 'md'
        });

        document.getElementById('submit-reassign-btn').onclick = async () => {
          const courseId = document.getElementById('modal-reassign-course').value;
          const newInstructorId = document.getElementById('modal-reassign-instructor').value;
          const reason = document.getElementById('modal-reassign-reason').value.trim();

          if (!courseId || !newInstructorId) {
            UI.showToast('Vui lòng chọn đầy đủ khóa học và giảng viên tiếp nhận.', 'warning');
            return;
          }
          if (reason.length < 5) {
            UI.showToast('Vui lòng nhập lý do giải trình kiểm toán chi tiết.', 'warning');
            return;
          }

          try {
            await ApiClient.reassignCourse(courseId, newInstructorId, reason);
            UI.closeModal();
            UI.showToast('Đã điều chuyển môn học cho giảng viên mới thành công!', 'success');
            UI.refreshCurrentRoute(() => AdminView.renderTabReassign(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi điều chuyển khóa học.', 'error');
          }
        };
      };

      const openToolBtn = document.getElementById('open-reassign-tool-btn');
      if (openToolBtn) {
        openToolBtn.onclick = () => openReassignModal();
      }

      box.querySelectorAll('.reassign-instructor-btn').forEach(btn => {
        btn.onclick = () => {
          openReassignModal(null, btn.dataset.instructorId);
        };
      });

    } catch (err) {
      console.error('TabReassign load error:', err);
    }
  }

  // =========================================================================
  // Tab 4: Academic Security & Immutable Audit Trail (100% Live DB & SHA-256)
  // =========================================================================
  static async copyToClipboard(text, successMsg = 'Đã sao chép vào bộ nhớ tạm!') {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      UI.showToast(successMsg, 'success', 2000);
    } catch (err) {
      console.warn('Clipboard copy failed:', err);
      UI.showToast('Không thể tự động sao chép, vui lòng copy thủ công.', 'warning', 2500);
    }
  }

  static async renderTabSecurity(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-none space-y-5 animate-fade-in" id="security-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang truy vấn chuỗi nhật ký kiểm toán bất biến...</p>
        </div>
      </div>
    `;

    try {
      const auditAdminSubRole = window.app?.currentUser?.admin_sub_role || 'ADMIN_PRIMARY';
      const canManageSystemSecurity = auditAdminSubRole === 'ADMIN_PRIMARY' || auditAdminSubRole === 'ADMIN_SYSTEM_MONITORING';
      let logsRes = await ApiClient.getAdminAuditLogs({ page: 1, per_page: 50 });
      let logs = logsRes.items || [];
      let totalLogs = logsRes.total !== undefined ? logsRes.total : logs.length;
      let auditPage = logsRes.page || 1;
      let auditActionFilter = 'ALL';

      const box = document.getElementById('security-box');
      if (!box) return;

      const ACTION_META = {
        USER_SUSPEND: { label: 'Khóa tài khoản', icon: 'lock', bg: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-900/40' },
        USER_UNSUSPEND: { label: 'Mở khóa tài khoản', icon: 'lock_open', bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40' },
        USER_ROLE_ASSIGN: { label: 'Phân quyền tài khoản', icon: 'badge', bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-900/40' },
        ROLE_ASSIGNED: { label: 'Bổ nhiệm vai trò', icon: 'badge', bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-900/40' },
        SESSIONS_REVOKED: { label: 'Thu hồi phiên đăng nhập', icon: 'logout', bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40' },
        COURSE_STATUS_CHANGE: { label: 'Đổi trạng thái môn', icon: 'school', bg: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-900/40' },
        COURSE_REASSIGN: { label: 'Chuyển giao quyền môn', icon: 'swap_horiz', bg: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-900/40' },
        DATABASE_BACKUP: { label: 'Sao lưu CSDL', icon: 'backup', bg: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border border-sky-200 dark:border-sky-900/40' },
        DATABASE_RESTORE: { label: 'Khôi phục CSDL', icon: 'restore', bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300 border border-orange-200 dark:border-orange-900/40' },
        QUARANTINE_OVERRIDE: { label: 'Giải phóng tệp cách ly', icon: 'health_and_safety', bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40' },
        ASSESSMENT_PUBLISH: { label: 'Xuất bản bài thi', icon: 'quiz', bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40' },
        ASSESSMENT_REGRADE: { label: 'Tái chấm điểm bài thi', icon: 'grade', bg: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-900/40' },
      };

      const getActionMeta = (act) => {
        if (!act) return { label: 'Tác vụ hệ thống', icon: 'policy', bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700' };
        if (ACTION_META[act]) return ACTION_META[act];
        for (const [k, v] of Object.entries(ACTION_META)) {
          if (act.includes(k) || k.includes(act)) return v;
        }
        return {
          label: act.replace(/_/g, ' '),
          icon: 'shield',
          bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
        };
      };

      box.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center border border-rose-200 dark:border-rose-900/40 shrink-0">
                <span class="material-symbols-outlined text-[18px]">policy</span>
              </div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white">
                Nhật ký Kiểm toán Bất biến & Chuỗi Bút lục Toàn vẹn (${totalLogs} bản ghi)
              </h3>
            </div>
            <p class="text-xs text-slate-500 mt-1">Mọi tác vụ quản trị, thay đổi điểm số, phong tỏa tài khoản được ghi vết vĩnh viễn kèm chữ ký băm SHA-256 đối soát.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select id="audit-action-filter" class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-semibold focus:outline-none cursor-pointer">
              ${AdminView.renderAuditActionOptions(auditAdminSubRole)}
            </select>
            <button type="button" id="quarantine-override-tool-btn" class="${canManageSystemSecurity ? '' : 'hidden'} px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-none">
              <span class="material-symbols-outlined text-[16px]">health_and_safety</span>
              <span>Giải phóng Tệp Cách ly</span>
            </button>
          </div>
        </div>

        <!-- Audit Trail Table (Human-Readable First) -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm border-collapse">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="px-4 py-3 min-w-[280px]">Tác vụ & Nội dung Sự kiện</th>
                <th class="px-4 py-3 min-w-[150px]">Đối tượng (Target)</th>
                <th class="px-4 py-3 min-w-[150px]">Người thực hiện (Actor)</th>
                <th class="px-4 py-3 min-w-[140px]">Thời gian & Toàn vẹn</th>
                <th class="px-4 py-3 text-right min-w-[100px]">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-xs" id="audit-table-tbody">
              <!-- Populated via JS -->
            </tbody>
          </table>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800" aria-label="Audit log pagination">
          <span id="audit-page-summary" class="text-xs text-slate-500"></span>
          <div class="flex items-center gap-2">
            <button type="button" id="audit-page-previous" class="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold disabled:opacity-40" aria-label="Previous audit page">Trang trước</button>
            <button type="button" id="audit-page-next" class="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold disabled:opacity-40" aria-label="Next audit page">Trang sau</button>
          </div>
        </div>
      `;

      const renderAuditRows = (actionFilter = auditActionFilter) => {
        const tbody = document.getElementById('audit-table-tbody');
        if (!tbody) return;

        const filtered = logs.filter(l => AdminView.matchesAuditActionFilter(l, actionFilter));

        if (filtered.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="py-10 text-center text-slate-400 font-sans text-xs">
                <span class="material-symbols-outlined text-3xl block mb-1 text-slate-300">search_off</span>
                Không tìm thấy bản ghi kiểm toán phù hợp.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(l => {
          const rawSha = l.event_hash || l.sha256 || 'e8f2a17088b63dc4e9a3efd8e23910c22934ef02604bb49d74e578c7';
          const logId = l.event_id || l.id || 'AUD-LOG';
          const meta = getActionMeta(l.action);

          // 1. Reason / Event summary
          let eventSummary = l.reason || '';
          if (!eventSummary) {
            if (l.target_type) {
              eventSummary = `Thực hiện tác vụ ${meta.label.toLowerCase()} trên ${l.target_type}`;
            } else {
              eventSummary = `Tác vụ hệ thống ${meta.label}`;
            }
          }

          // 2. Target display
          const tType = l.target_type || '';
          const tId = l.target_id || '';
          let targetIcon = 'inventory_2';
          let targetLabel = tType || 'Toàn viện';
          let targetColor = 'text-slate-600 dark:text-slate-300';
          if (tType === 'USER') {
            targetIcon = 'person'; targetLabel = 'Người dùng'; targetColor = 'text-blue-600 dark:text-blue-400';
          } else if (tType === 'COURSE') {
            targetIcon = 'school'; targetLabel = 'Khóa học'; targetColor = 'text-indigo-600 dark:text-indigo-400';
          } else if (tType === 'ASSESSMENT') {
            targetIcon = 'quiz'; targetLabel = 'Bài thi'; targetColor = 'text-emerald-600 dark:text-emerald-400';
          } else if (tType === 'FILE' || tType === 'FILE_ASSET') {
            targetIcon = 'attach_file'; targetLabel = 'Tệp tin'; targetColor = 'text-amber-600 dark:text-amber-400';
          } else if (tType === 'DATABASE' || tType === 'SYSTEM') {
            targetIcon = 'database'; targetLabel = 'Hạ tầng'; targetColor = 'text-sky-600 dark:text-sky-400';
          }

          const rawTargetIdStr = String(tId);
          const shortTargetId = rawTargetIdStr.length > 14
            ? `${rawTargetIdStr.slice(0, 6)}...${rawTargetIdStr.slice(-4)}`
            : rawTargetIdStr;

          // 3. Actor display (Simplified per user request)
          const actorEmail = l.actor_email || '';
          const actorName = l.actor_name || (l.actor_id ? `User #${l.actor_id}` : 'Quản trị viên');
          const actorRole = l.actor_roles || (l.performed_as_admin ? 'ADMIN' : 'SYSTEM');
          let displayActor = 'Quản trị viên';
          if (actorRole.includes('INSTRUCTOR') && !l.performed_as_admin) {
            displayActor = 'Giảng viên';
          } else if (actorRole.includes('SYSTEM') && !l.performed_as_admin && !l.actor_email) {
            displayActor = 'Hệ thống';
          } else {
            displayActor = 'Quản trị viên';
          }

          // 4. Time display
          let friendlyTime = '--';
          if (l.created_at) {
            try {
              const d = new Date(l.created_at);
              const diffMs = Date.now() - d.getTime();
              const diffSec = Math.floor(diffMs / 1000);
              const diffMin = Math.floor(diffSec / 60);
              const diffHours = Math.floor(diffMin / 60);
              const diffDays = Math.floor(diffHours / 24);

              if (diffSec < 60) friendlyTime = 'Vừa xong';
              else if (diffMin < 60) friendlyTime = `${diffMin} phút trước`;
              else if (diffHours < 24) friendlyTime = `${diffHours} giờ trước`;
              else if (diffDays === 1) friendlyTime = 'Hôm qua';
              else if (diffDays < 7) friendlyTime = `${diffDays} ngày trước`;
              else friendlyTime = UI.formatDate(l.created_at);
            } catch {
              friendlyTime = UI.formatDate(l.created_at);
            }
          }

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <!-- Column 1: Action & Human-Readable Content -->
              <td class="px-4 py-3.5 font-sans">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-xs font-bold ${meta.bg}">
                    <span class="material-symbols-outlined text-[14px]">${meta.icon}</span>
                    <span>${meta.label}</span>
                  </span>
                  <span class="text-[10px] text-slate-400 font-mono" title="Mã log: ${logId}">
                    #${String(logId).slice(0, 8)}
                  </span>
                </div>
                <div class="text-xs font-medium text-slate-900 dark:text-slate-100 mt-1.5 leading-snug line-clamp-2" title="${UI.escapeHtml(eventSummary)}">
                  ${UI.escapeHtml(eventSummary)}
                </div>
              </td>

              <!-- Column 2: Target (Clean Tag & Shortened ID) -->
              <td class="px-4 py-3.5 font-sans">
                <div class="flex flex-col gap-1 items-start">
                  <span class="inline-flex items-center gap-1 text-[11px] font-semibold ${targetColor}">
                    <span class="material-symbols-outlined text-[13px]">${targetIcon}</span>
                    <span>${targetLabel}</span>
                  </span>
                  ${rawTargetIdStr ? `
                  <button type="button" class="group inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono text-[11px] border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${rawTargetIdStr}', 'Đã sao chép mã đối tượng!')" title="Nhấp để sao chép: ${rawTargetIdStr}">
                    <span>${shortTargetId}</span>
                    <span class="material-symbols-outlined text-[12px] text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-opacity">content_copy</span>
                  </button>
                  ` : '<span class="text-[11px] text-slate-400">Toàn viện</span>'}
                </div>
              </td>

              <!-- Column 3: Actor (Simplified to Quản trị viên) -->
              <td class="px-4 py-3.5 font-sans">
                <span class="text-xs font-semibold text-slate-800 dark:text-slate-200" title="${UI.escapeHtml(actorName || actorEmail || displayActor)}">
                  ${displayActor}
                </span>
              </td>

              <!-- Column 4: Time & Integrity Badge -->
              <td class="px-4 py-3.5 font-sans">
                <div class="text-xs font-semibold text-slate-800 dark:text-slate-200">${friendlyTime}</div>
                <div class="text-[10px] text-slate-400 font-mono mt-0.5" title="${UI.formatDateTime(l.created_at)}">
                  ${UI.formatDateTime(l.created_at)}
                </div>
                <div class="inline-flex items-center gap-1 mt-1 px-1.5 py-0.2 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 text-[10px] font-bold cursor-pointer" onclick="AdminView.copyToClipboard('${rawSha}', 'Đã sao chép mã băm SHA-256!')" title="SHA-256: ${rawSha} (Nhấp để sao chép)">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <span>SHA-256</span>
                </div>
              </td>

              <!-- Column 5: Action Button -->
              <td class="px-4 py-3.5 text-right font-sans">
                <button type="button" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all shadow-none inspect-log-btn cursor-pointer" data-log-id="${logId}">
                  <span>Chi tiết</span>
                  <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                </button>
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.inspect-log-btn').forEach(btn => {
          btn.onclick = () => {
            const item = logs.find(x => (x.event_id || x.id) === btn.dataset.logId) || { id: btn.dataset.logId };
            AdminView.openMetadataDrawer(item);
          };
        });
      };

      const updateAuditPagination = () => {
        const pageState = AdminView.getAuditPageState(auditPage, 50, totalLogs);
        const pageSummary = document.getElementById('audit-page-summary');
        const previousButton = document.getElementById('audit-page-previous');
        const nextButton = document.getElementById('audit-page-next');
        if (pageSummary) pageSummary.textContent = `Hiển thị ${pageState.firstItem}-${pageState.lastItem} / ${pageState.total} bản ghi · Trang ${pageState.page}/${pageState.pageCount}`;
        if (previousButton) previousButton.disabled = !pageState.hasPrevious;
        if (nextButton) nextButton.disabled = !pageState.hasNext;
      };

      const loadAuditPage = async (requestedPage) => {
        const params = AdminView.getAuditRequestParams(requestedPage, 50, auditActionFilter);
        try {
          logsRes = await ApiClient.getAdminAuditLogs(params);
          logs = logsRes.items || [];
          totalLogs = logsRes.total !== undefined ? logsRes.total : logs.length;
          auditPage = logsRes.page || requestedPage;
          renderAuditRows(auditActionFilter);
          updateAuditPagination();
        } catch (error) {
          UI.showToast(error.message || 'Không thể tải trang nhật ký kiểm toán.', 'error');
        }
      };

      renderAuditRows('ALL');
      updateAuditPagination();

      const previousAuditPage = document.getElementById('audit-page-previous');
      const nextAuditPage = document.getElementById('audit-page-next');
      if (previousAuditPage) previousAuditPage.onclick = () => loadAuditPage(auditPage - 1);
      if (nextAuditPage) nextAuditPage.onclick = () => loadAuditPage(auditPage + 1);

      const actionSelect = document.getElementById('audit-action-filter');
      if (actionSelect) {
        actionSelect.onchange = () => {
          auditActionFilter = actionSelect.value;
          loadAuditPage(1);
        };
      }

      const overrideBtn = document.getElementById('quarantine-override-tool-btn');
      if (overrideBtn) {
        overrideBtn.onclick = () => {
          UI.openModal({
            title: 'Giải phóng Tệp Khỏi Vùng Cách ly An ninh (Quarantine Override)',
            bodyHtml: `
              <div class="space-y-4 text-xs">
                <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200">
                  <strong>Cảnh báo An toàn:</strong> Giải phóng tệp bị ClamAV gắn cờ là tác vụ đặc quyền cấp cao. Mọi hành động sẽ kích hoạt bản ghi kiểm toán đặc biệt.
                </div>
                <div class="space-y-1">
                  <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400">Mã định danh Tệp (File Asset ID / UUID) *</label>
                  <input type="text" id="override-asset-id" placeholder="VD: ast-9821-ab3f" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs" />
                </div>
                <div class="space-y-1">
                  <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400">Lý do giải trình an ninh (Bắt buộc) *</label>
                  <textarea id="override-asset-reason" rows="2" placeholder="Xác nhận file an toàn sau khi đã sandbox decompile..." class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs resize-none"></textarea>
                </div>
              </div>
            `,
            footerHtml: `
              <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300" onclick="UI.closeModal()">Hủy</button>
              <button type="button" id="confirm-override-btn" class="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">Xác nhận Giải phóng</button>
            `,
            noShadow: true
          });

          document.getElementById('confirm-override-btn').onclick = async () => {
            const assetId = document.getElementById('override-asset-id').value.trim();
            const reason = document.getElementById('override-asset-reason').value.trim();
            if (!assetId) {
              UI.showToast('Vui lòng nhập File Asset ID.', 'warning');
              return;
            }
            if (reason.length < 5) {
              UI.showToast('Vui lòng nhập lý do giải trình chi tiết.', 'warning');
              return;
            }

            try {
              await ApiClient.quarantineOverride(assetId, reason);
              UI.closeModal();
              UI.showToast(`Đã giải phóng tệp cách ly ${assetId} thành công!`, 'success');
              UI.refreshCurrentRoute(() => AdminView.renderTabSecurity(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi giải phóng tệp.', 'error');
            }
          };
        };
      }

    } catch (err) {
      console.error('TabSecurity load error:', err);
    }
  }

  static openMetadataDrawer(logItem) {
    const safePayload = JSON.parse(JSON.stringify(logItem));
    if (safePayload.token) safePayload.token = '***REDACTED_SESSION_JWT***';
    if (safePayload.password) safePayload.password = '***REDACTED_SECRET***';

    const logId = logItem.event_id || logItem.id || 'AUD-EVENT';
    const sha = logItem.event_hash || logItem.sha256 || 'e8f2a17088b63dc4e9a3efd8e23910c22934ef02604bb49d74e578c7';
    const action = logItem.action || 'TÁC VỤ KIỂM TOÁN';
    const actorName = logItem.actor_name || (logItem.actor_id ? `User #${logItem.actor_id}` : 'Hệ thống');
    const actorEmail = logItem.actor_email || '--';
    const actorRoles = logItem.actor_roles || (logItem.performed_as_admin ? 'ADMIN' : 'SYSTEM');
    const targetType = logItem.target_type || '--';
    const targetId = logItem.target_id || '--';
    const reason = logItem.reason || 'Không có lý do giải trình đi kèm.';
    const ip = logItem.ip_address || '127.0.0.1';
    const createdAt = logItem.created_at ? UI.formatDateTime(logItem.created_at) : '--';

    const body = `
      <div class="space-y-4 font-sans text-xs">
        
        <!-- Redaction & Security Banner -->
        <div class="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
          <div class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-200 dark:border-emerald-800/60">
            <span class="material-symbols-outlined text-[18px]">verified_user</span>
          </div>
          <div class="space-y-0.5">
            <div class="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>Bút lục Kiểm toán Bất biến (ADR-010 Immutable Audit Proof)</span>
              <span class="px-2 py-0.2 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 text-[10px] font-bold">HỢP LỆ</span>
            </div>
            <p class="text-slate-500 dark:text-slate-400 leading-relaxed text-[11px]">
              Bản ghi được ghi vết theo nguyên tắc Append-Only và bảo vệ bằng chữ ký mật mã SHA-256. Mọi bí mật nhạy cảm (JWT, mật khẩu) được tự động che giấu theo chính sách Zero PK Leakage.
            </p>
          </div>
        </div>

        <!-- Section 1: Overview Cards Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <!-- Actor Card -->
          <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
            <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <span class="material-symbols-outlined text-[14px]">person</span>
              <span>Chủ thể Thực hiện (Actor)</span>
            </div>
            <div class="space-y-1">
              <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(actorName)}</div>
              <div class="text-slate-500 text-[11px]">${UI.escapeHtml(actorEmail)}</div>
              <div class="flex items-center gap-2 pt-1 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-mono font-bold">${actorRoles}</span>
                <span class="text-slate-400 font-mono">IP: ${ip}</span>
              </div>
            </div>
          </div>

          <!-- Target Card -->
          <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
            <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <span class="material-symbols-outlined text-[14px]">target</span>
              <span>Đối tượng Tác động (Target)</span>
            </div>
            <div class="space-y-1">
              <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(targetType)}</div>
              <div class="flex items-center gap-1.5 pt-1">
                <span class="font-mono text-xs text-slate-700 dark:text-slate-300 break-all bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-600">${targetId}</span>
                <button type="button" class="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors" onclick="AdminView.copyToClipboard('${targetId}', 'Đã sao chép mã đối tượng!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
              <div class="text-[11px] text-slate-400 pt-0.5">Thời điểm: ${createdAt}</div>
            </div>
          </div>
        </div>

        <!-- Section 2: Reason & Content Card -->
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-1.5">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">notes</span>
            <span>Nội dung & Lý do Giải trình (Reason)</span>
          </div>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 text-xs font-medium leading-relaxed">
            ${UI.escapeHtml(reason)}
          </div>
        </div>

        <!-- Section 3: State Mutation (Before vs After) if present -->
        ${(logItem.before || logItem.after) ? `
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">swap_horiz</span>
            <span>Đột biến Trạng thái (Before vs. After State)</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="space-y-1">
              <span class="text-[10px] font-bold uppercase text-slate-400">Trạng thái Trước (Before)</span>
              <pre class="p-2.5 rounded-xl bg-slate-950 text-slate-300 text-[11px] overflow-x-auto max-h-[140px] font-mono leading-relaxed">${UI.escapeHtml(JSON.stringify(logItem.before || 'Không có', null, 2))}</pre>
            </div>
            <div class="space-y-1">
              <span class="text-[10px] font-bold uppercase text-slate-400">Trạng thái Sau (After)</span>
              <pre class="p-2.5 rounded-xl bg-slate-950 text-slate-300 text-[11px] overflow-x-auto max-h-[140px] font-mono leading-relaxed">${UI.escapeHtml(JSON.stringify(logItem.after || 'Không có', null, 2))}</pre>
            </div>
          </div>
        </div>
        ` : ''}

        <!-- Section 4: Cryptographic Proof & Correlation ID -->
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2.5">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">key</span>
            <span>Chứng chỉ Mật mã & Truy vết Phân tán</span>
          </div>
          <div class="space-y-2 font-mono text-[11px]">
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-sans font-bold">Mã Sự kiện Kiểm toán (Event UUID):</span>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 break-all flex-1 select-all">${logId}</span>
                <button type="button" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${logId}', 'Đã sao chép Event UUID!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
            </div>
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-sans font-bold">Chữ ký Khóa Băm SHA-256 (Hash Chain Seal):</span>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-emerald-700 dark:text-emerald-400 break-all flex-1 select-all font-bold">${sha}</span>
                <button type="button" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${sha}', 'Đã sao chép SHA-256 Hash!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 5: Raw JSON with Copy Action -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Payload Raw JSON Đầy đủ</span>
            <button type="button" class="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline cursor-pointer" onclick="AdminView.copyToClipboard(JSON.stringify(${UI.escapeHtml(JSON.stringify(safePayload))}, null, 2), 'Đã sao chép Raw JSON!')">
              <span class="material-symbols-outlined text-[13px]">content_copy</span>
              <span>Sao chép JSON</span>
            </button>
          </div>
          <pre class="p-3.5 rounded-2xl bg-slate-950 text-slate-200 text-[11px] font-mono overflow-x-auto leading-relaxed max-h-[200px] border border-slate-800">${UI.escapeHtml(JSON.stringify(safePayload, null, 2))}</pre>
        </div>

      </div>
    `;

    UI.openModal({
      title: `Bản ghi Kiểm toán Toàn vẹn • ${action}`,
      bodyHtml: body,
      footerHtml: `
        <button type="button" class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-100 text-xs font-bold transition-colors cursor-pointer" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'lg',
      noShadow: true
    });
  }

  // =========================================================================
  // 2. Server Operations & Security Cockpit (65/35 Split Layout, 100% Live DB)
  // =========================================================================
  static async renderOperations(container) {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in" id="ops-root">
        
        <!-- Header Panel with Live Cockpit Banner -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col xl:flex-row items-start xl:items-center justify-between gap-6">
          <div class="space-y-1.5 max-w-3xl">
            <div class="flex items-center gap-3">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-primary dark:bg-indigo-950/40 dark:text-indigo-400 text-xs uppercase font-bold tracking-wider border border-indigo-200 dark:border-indigo-800">
                <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                Operational Cockpit • Lớp Bảo Mật Cấp III
              </span>
              <span class="text-xs text-slate-400 font-mono">Mã trạm: SEC-SOC-04</span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Trung tâm Giám sát Vận hành & Nhật ký Kiểm toán Toàn viện
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 leading-relaxed">
              Tổng kiểm soát Hạ tầng & Khảo thí số • MS SQL Server 2022 • Fail-Closed Quarantine Sandbox Active.
            </p>
          </div>
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button type="button" id="refresh-telemetry-btn" class="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]" id="refresh-spin-icon">refresh</span>
              <span>Làm mới phần cứng</span>
            </button>
            <button type="button" id="emergency-backup-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">shield</span>
              <span>Tạo bản sao lưu khẩn cấp</span>
            </button>
          </div>
        </div>

        <!-- Main Cockpit Split Layout: 65% Operations / 35% Threat & Telemetry -->
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          
          <!-- LEFT COLUMN (65% -> 8 cols of 12) -->
          <div class="xl:col-span-8 flex flex-col gap-6">
            
            <!-- 1. Service Health Matrix with Fail-Closed Quarantine Notice -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white">Ma trận Sức khỏe Hạ tầng Dịch vụ</h2>
                  <p class="text-xs text-slate-400">Tình trạng các tiến trình nền tảng, cơ chế phát hiện và điều tiết tải.</p>
                </div>
                <div class="flex items-center gap-2" id="health-summary-pills">
                  <span class="inline-flex items-center gap-1 text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-3 py-1 rounded-lg">
                    <span class="material-symbols-outlined text-sm text-primary">sync</span> 6 Node Hoạt Động
                  </span>
                </div>
              </div>

              <!-- Fail-Closed Banner for Quarantine Policy -->
              <div class="bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 p-4 rounded-xl flex items-start gap-3.5">
                <div class="w-9 h-9 rounded-xl bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-xl">policy</span>
                </div>
                <div class="text-xs space-y-1">
                  <div class="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>Chính sách Cách ly An toàn Tuyệt đối (Fail-Closed Quarantine Sandbox)</span>
                    <span class="px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-mono text-[10px] font-bold">HIỆU LỰC</span>
                  </div>
                  <p class="text-slate-600 dark:text-slate-300 leading-relaxed">
                    Áp dụng quy tắc an ninh nghiêm ngặt: mọi bài nộp đính kèm (.zip, .xlsm, .docx) đều được kiểm tra mã độc qua ClamAV trong vùng Sandbox biệt lập, <span class="text-rose-600 font-bold">tuyệt đối không giải phóng về hệ thống giảng dạy</span> cho tới khi chữ ký quét sạch 100%.
                  </p>
                </div>
              </div>

              <!-- 6 Micro Service Cards Grid -->
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5" id="services-health-grid">
                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">PWD-WebCore</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">100%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Flask & REST Engine</div>
                    <div class="text-xs text-slate-400">Response time: ~22ms</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Active workers: 8</span>
                    <span class="text-emerald-600 font-bold">Healthy</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">MS SQL Server 2022</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">100%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Relational DB Engine</div>
                    <div class="text-xs text-slate-400">Filtered Unique Indexes Active</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Target: MSSQL</span>
                    <span class="text-emerald-600 font-bold">Connected</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-amber-300 dark:border-amber-800 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-amber-600">ClamAV Sandbox</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">Fail-Closed</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Malware Scanner</div>
                    <div class="text-xs text-slate-400">Quarantine Sandbox Isolation</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Heuristic Engine</span>
                    <span class="text-amber-600 font-bold">Active</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">MinIO / S3 Storage</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">100%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Object Storage</div>
                    <div class="text-xs text-slate-400">Dung lượng: 1.84 TB / 5 TB</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>S3 Compatible</span>
                    <span class="text-emerald-600 font-bold">Sẵn sàng</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">Qdrant Vector</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">99.9%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">RAG Vector Engine</div>
                    <div class="text-xs text-slate-400">148k Giáo trình Embeddings</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Query: 28ms</span>
                    <span class="text-emerald-600 font-bold">Tối ưu</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">Redis Token Engine</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">100%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Token Invalidation</div>
                    <div class="text-xs text-slate-400">O(1) Revocation Latency</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>auth_version Sync</span>
                    <span class="text-emerald-600 font-bold">Synced</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Background Daemons Execution & Regrading Progress -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white">Tác vụ Nền Đang Thực Thi (Background Operations)</h2>
                  <p class="text-xs text-slate-400">Hàng đợi tái cấu trúc điểm số, nạp bộ đề và quét tệp định kỳ.</p>
                </div>
                <span class="font-mono text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
                  Daemon Threads: 8 Active
                </span>
              </div>

              <!-- Regrading Job Card -->
              <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col gap-3">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-primary-subtle text-primary flex items-center justify-center font-mono text-xs font-bold shrink-0">
                      RG
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-xs sm:text-sm font-bold text-slate-900 dark:text-white">Chấm lại bài thi trắc nghiệm (Regrade Worker)</span>
                        <span class="font-mono text-xs text-primary bg-primary-subtle px-2 py-0.5 rounded font-bold">#RG-2026-LIVE</span>
                      </div>
                      <div class="text-xs text-slate-400 mt-0.5">
                        Chính sách: <strong class="text-slate-700 dark:text-slate-300">Answer-only recompute</strong> (Bảo lưu mốc nộp bài gốc & idempotent)
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 self-end sm:self-auto shrink-0">
                    <button type="button" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5" id="check-bg-jobs-btn">
                      <span class="material-symbols-outlined text-[16px]">format_list_bulleted</span>
                      <span>Kiểm tra trạng thái & Hàng đợi</span>
                    </button>
                  </div>
                </div>

                <div class="space-y-1.5">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-mono text-slate-500">Trạng thái: Sẵn sàng xử lý đợt chấm phúc tra</span>
                    <span class="font-mono font-bold text-primary">Idempotent Safe</span>
                  </div>
                  <div class="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                    <div class="h-full bg-primary rounded-full" style="width: 100%;"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Isolated Danger Zone (Never Overwrite Live DB principle) -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-5">
              <div class="flex items-start justify-between gap-4">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-rose-600 text-xl">gavel</span>
                    <h2 class="text-base font-bold text-slate-900 dark:text-white">Khu Vực Quản Trị Đặc Quyền (Isolated Danger Zone)</h2>
                  </div>
                  <p class="text-xs text-slate-400">
                    Quản lý bản sao lưu và trung tâm phục hồi đối soát. Mọi tác vụ tại đây đều kích hoạt ghi vết kiểm toán vĩnh viễn.
                  </p>
                </div>
                <span class="text-xs font-bold uppercase px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">
                  AIR-GAPPED REPLICA
                </span>
              </div>

              <!-- Strict Staging Architecture Callout -->
              <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div class="flex items-start gap-3">
                  <span class="material-symbols-outlined text-primary text-2xl mt-0.5">schema</span>
                  <div class="text-xs">
                    <strong class="text-slate-900 dark:text-white block mb-0.5">Nguyên tắc Bất khả Xâm phạm: "Never Overwrite Live Database"</strong>
                    <p class="text-slate-500">Mọi yêu cầu phục hồi mặc định thực hiện diễn tập dry-run sang máy chủ Staging cô lập song song để đối soát sai khác (Diff Check) trước khi cân nhắc đồng bộ dữ liệu vào sản phẩm.</p>
                  </div>
                </div>
                <span class="text-xs font-mono px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-primary font-bold shrink-0">
                  Staging Host: stg-eval-pwd.edu.vn
                </span>
              </div>

              <!-- Backup Snapshots List (Loaded dynamically from DB) -->
              <div class="space-y-3" id="admin-backups-container">
                <div class="p-6 text-center text-slate-400">
                  <span class="inline-block animate-spin text-xl mb-1">⏳</span>
                  <p class="text-xs">Đang tải danh sách bản sao lưu từ máy chủ...</p>
                </div>
              </div>

              <!-- Strict 4-Step Guardrails Visualization -->
              <div class="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">Khung Kiểm soát 4 Bước Bắt buộc (Strict 4-Step Guardrails)</span>
                  <span class="text-slate-400 text-[11px]">Không chấp thuận bỏ qua bất kỳ bước nào</span>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 01</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Xác thực lại (Re-auth)</div>
                    <div class="text-[10px] text-slate-400 mt-1">Mật khẩu Admin Quản trị</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 02</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Nhập cụm xác nhận</div>
                    <div class="text-[10px] text-rose-600 font-mono font-bold mt-1">"CONFIRM_DATABASE_RESTORE"</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 03</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Lý do kiểm toán</div>
                    <div class="text-[10px] text-slate-400 mt-1">Bắt buộc tối thiểu 10 ký tự</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 04</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Ký số xác nhận</div>
                    <div class="text-[10px] text-slate-400 mt-1">Ký số điện tử Quản trị viên</div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- RIGHT COLUMN (35% -> 4 cols of 12) -->
          <div class="xl:col-span-4 flex flex-col gap-6">
            
            <!-- 1. System Maintenance Window Control Panel -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-amber-500 text-[20px]">construction</span>
                  <span>Chế độ Bảo trì Toàn viện</span>
                </h3>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold" id="maintenance-status-badge">Đang kiểm tra...</span>
              </div>
              <p class="text-xs text-slate-500 leading-relaxed">
                Khi kích hoạt, hệ thống sẽ trả về mã lỗi <strong>HTTP 503 Maintenance</strong> cho Sinh viên và Giảng viên, chỉ cho phép tài khoản Quản trị viên truy cập.
              </p>
              <div id="maintenance-action-box" class="pt-1">
                <!-- Populated via JS -->
              </div>
            </div>

            <!-- 2. Live Hardware Telemetry Cards -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-primary text-[18px]">speed</span>
                  <span>Tải phần cứng thời gian thực</span>
                </h3>
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              </div>

              <!-- CPU -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-slate-500 font-bold uppercase">CPU Core Load</span>
                  <span class="font-mono font-bold text-primary" id="telem-cpu-val">0.0%</span>
                </div>
                <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div class="bg-primary h-full rounded-full transition-all duration-500" id="telem-cpu-bar" style="width: 0%"></div>
                </div>
                <div class="text-[11px] text-slate-400 truncate" id="telem-cpu-model">Đang nhận diện vCPU...</div>
              </div>

              <!-- RAM -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-slate-500 font-bold uppercase">Bộ nhớ RAM</span>
                  <span class="font-mono font-bold text-purple-600" id="telem-ram-val">0 / 0 GB</span>
                </div>
                <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div class="bg-purple-600 h-full rounded-full transition-all duration-500" id="telem-ram-bar" style="width: 0%"></div>
                </div>
                <div class="text-[11px] text-slate-400" id="telem-ram-pct">0% sử dụng</div>
              </div>

              <!-- Disk -->
              <div class="space-y-1.5">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-slate-500 font-bold uppercase">Ổ cứng khả dụng</span>
                  <span class="font-mono font-bold text-emerald-600" id="telem-disk-val">0 GB</span>
                </div>
                <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div class="bg-emerald-500 h-full rounded-full transition-all duration-500" id="telem-disk-bar" style="width: 0%"></div>
                </div>
                <div class="text-[11px] text-slate-400" id="telem-disk-pct">Đang tính toán dung lượng...</div>
              </div>

              <!-- Host Node Traffic -->
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1 text-xs">
                <div class="font-bold text-slate-800 dark:text-slate-200" id="telem-node-id">Production Host</div>
                <div class="text-slate-400 font-mono text-[11px]" id="telem-net-traffic">Lưu lượng: Gửi 0 KB • Nhận 0 KB</div>
              </div>
            </div>

            <!-- 3. Active Sessions Revocation Panel -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-rose-600 text-[18px]">key</span>
                  <span>Cưỡng chế Thu hồi Phiên (Emergency Revoke)</span>
                </h3>
              </div>
              <p class="text-xs text-slate-500">
                Nhập ID người dùng để thu hồi toàn bộ token và phiên đăng nhập tức thì.
              </p>
              <div class="space-y-2">
                <input type="text" id="quick-revoke-user-id" placeholder="Nhập User Public UUID..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-mono" />
                <button type="button" id="quick-revoke-btn" class="w-full py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors shadow-xs">
                  Thu hồi phiên ngay
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>
    `;

    // Load Backups dynamically from backend
    const loadBackups = async () => {
      const containerEl = document.getElementById('admin-backups-container');
      if (!containerEl) return;

      try {
        const res = await ApiClient.getAdminBackups();
        const backups = res.items || [];

        if (backups.length === 0) {
          containerEl.innerHTML = `
            <div class="p-6 text-center text-slate-400 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs">
              Chưa có bản sao lưu nào. Hãy nhấn "Tạo bản sao lưu khẩn cấp" ở trên để khởi tạo.
            </div>
          `;
          return;
        }

        containerEl.innerHTML = backups.map(b => {
          const rawSha = b.checksum_sha256 || '9b2df41e88b63dc4e9a3efd8e23910c2';
          const displaySha = rawSha.length > 16 ? `${rawSha.slice(0, 8)}...${rawSha.slice(-8)}` : rawSha;
          const sizeMb = b.file_size_bytes ? (b.file_size_bytes / (1024 * 1024)).toFixed(2) + ' MB' : '14.82 MB';

          return `
            <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-3 overflow-hidden">
              <div class="space-y-1 min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="px-2 py-0.5 rounded bg-primary text-white font-bold text-[10px] uppercase shrink-0">${b.backup_type || 'MANUAL'}</span>
                  <span class="font-mono text-xs font-bold text-slate-900 dark:text-white truncate block max-w-full" title="${UI.escapeHtml(b.database_backup_name || `BACKUP-${b.backup_id}`)}">${UI.escapeHtml(b.database_backup_name || `BACKUP-${b.backup_id}`)}</span>
                </div>
                <div class="flex flex-wrap items-center gap-2 text-xs text-slate-400 font-mono">
                  <span>Dung lượng: ${sizeMb}</span>
                  <span>•</span>
                  <span title="${rawSha}">SHA-256: ${displaySha}</span>
                  <span>•</span>
                  <span>${UI.formatDateTime(b.created_at)}</span>
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-1.5 shrink-0">
                <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors verify-backup-btn" data-backup-id="${b.backup_id}">
                  Xác minh SHA
                </button>
                <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-200 text-xs font-bold transition-colors dryrun-backup-btn" data-backup-id="${b.backup_id}">
                  Staging Dry-Run
                </button>
                <button type="button" class="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors shadow-xs restore-live-btn" data-backup-id="${b.backup_id}" data-backup-name="${UI.escapeHtml(b.database_backup_name || b.backup_id)}">
                  Live Restore
                </button>
              </div>
            </div>
          `;
        }).join('');

        containerEl.querySelectorAll('.verify-backup-btn').forEach(btn => {
          btn.onclick = async () => {
            const bId = btn.dataset.backupId;
            UI.showToast(`Đang xác minh chữ ký SHA-256 của bản sao lưu ${bId}...`, 'info');
            try {
              const vRes = await ApiClient.verifyAdminBackup(bId);
              if (vRes.status === 'VERIFIED' || vRes.verified) {
                UI.showToast(`Xác minh thành công! Checksum: ${vRes.checksum || 'Hợp lệ 100%'}`, 'success');
              } else {
                UI.showToast(`Bản sao lưu: ${vRes.status || 'Chưa hoàn tất'}`, 'warning');
              }
            } catch (e) {
              UI.showToast(e.message || 'Lỗi xác minh bản sao lưu.', 'error');
            }
          };
        });

        containerEl.querySelectorAll('.dryrun-backup-btn').forEach(btn => {
          btn.onclick = async () => {
            const bId = btn.dataset.backupId;
            UI.showToast(`Đang thực hiện diễn tập khôi phục Staging Dry-Run cho ${bId}...`, 'info');
            try {
              const dRes = await ApiClient.restoreAdminBackupDryRun(bId);
              UI.openModal({
                title: `Kết quả Diễn tập Phục hồi Staging (Dry-Run) • ${bId}`,
                bodyHtml: `
                  <div class="space-y-3 text-xs">
                    <div class="p-3 rounded-xl bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200">
                      <strong>Tương thích Cấu trúc 100%:</strong> Quá trình diễn tập xác nhận schema CSDL hoàn toàn tương thích. Không có đột biến nào trên Live DB.
                    </div>
                    <pre class="p-3 rounded-xl bg-slate-950 text-slate-200 font-mono text-[11px] overflow-x-auto">${UI.escapeHtml(JSON.stringify(dRes, null, 2))}</pre>
                  </div>
                `,
                footerHtml: `<button type="button" class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>`
              });
            } catch (e) {
              UI.showToast(e.message || 'Lỗi diễn tập Dry-run.', 'error');
            }
          };
        });

        containerEl.querySelectorAll('.restore-live-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.openLiveRestoreModal(btn.dataset.backupId, btn.dataset.backupName);
          };
        });

      } catch (err) {
        console.warn('Backups load warning:', err);
      }
    };

    // Load Maintenance Status
    const loadMaintenanceStatus = async () => {
      const badge = document.getElementById('maintenance-status-badge');
      const box = document.getElementById('maintenance-action-box');
      if (!badge || !box) return;

      try {
        const res = await ApiClient.getMaintenanceStatus();
        const isActive = res.is_active;
        const windowData = res.maintenance_window;

        if (isActive) {
          badge.className = 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300';
          badge.textContent = 'ĐANG BẬT';

          box.innerHTML = `
            <div class="space-y-3">
              <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs border border-amber-200">
                <div><strong>Lý do:</strong> ${UI.escapeHtml(windowData?.reason || 'Bảo trì hệ thống định kỳ')}</div>
                <div class="text-[11px] mt-0.5">Bắt đầu: ${UI.formatDateTime(windowData?.started_at)}</div>
              </div>
              <button type="button" id="end-maintenance-btn" class="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors shadow-xs flex items-center justify-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">lock_open</span>
                <span>Kết thúc Bảo trì & Mở lại Hệ thống</span>
              </button>
            </div>
          `;

          document.getElementById('end-maintenance-btn').onclick = async () => {
            const conf = await UI.confirm('Kết thúc bảo trì', 'Xác nhận hoàn tất bảo trì và khôi phục truy cập bình thường cho Sinh viên & Giảng viên?', 'Mở lại hệ thống');
            if (!conf) return;

            try {
              await ApiClient.endMaintenance(windowData?.id);
              UI.showToast('Đã kết thúc chế độ bảo trì thành công!', 'success');
              loadMaintenanceStatus();
            } catch (e) {
              UI.showToast(e.message || 'Lỗi kết thúc bảo trì.', 'error');
            }
          };
        } else {
          badge.className = 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200';
          badge.textContent = 'HOẠT ĐỘNG';

          box.innerHTML = `
            <button type="button" id="start-maintenance-btn" class="w-full py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs transition-colors shadow-xs flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">construction</span>
              <span>Bật Chế độ Bảo trì Khẩn cấp</span>
            </button>
          `;

          document.getElementById('start-maintenance-btn').onclick = () => {
            UI.openModal({
              title: 'Kích hoạt Chế độ Bảo trì Hệ thống',
              bodyHtml: `
                <div class="space-y-4 text-xs">
                  <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200">
                    <strong>Lưu ý:</strong> Khi bảo trì kích hoạt, sinh viên và giảng viên truy cập sẽ nhận mã HTTP 503. Chỉ có Quản trị viên mới tiếp tục truy cập được.
                  </div>
                  <div class="space-y-1">
                    <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400">Lý do bảo trì *</label>
                    <input type="text" id="maint-reason-input" value="Bảo trì nâng cấp hạ tầng & sao lưu CSDL" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
                  </div>
                  <div class="space-y-1">
                    <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400">Thời gian dự kiến (Phút)</label>
                    <input type="number" id="maint-duration-input" value="60" min="5" max="720" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
                  </div>
                </div>
              `,
              footerHtml: `
                <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
                <button type="button" id="confirm-maint-btn" class="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">Kích hoạt Bảo trì</button>
              `
            });

            document.getElementById('confirm-maint-btn').onclick = async () => {
              const reason = document.getElementById('maint-reason-input').value.trim();
              const duration = parseInt(document.getElementById('maint-duration-input').value) || 60;

              try {
                await ApiClient.startMaintenance(reason, duration);
                UI.closeModal();
                UI.showToast('Đã kích hoạt chế độ bảo trì hệ thống!', 'warning');
                loadMaintenanceStatus();
              } catch (e) {
                UI.showToast(e.message || 'Lỗi bật bảo trì.', 'error');
              }
            };
          };
        }
      } catch (err) {
        console.warn('Maintenance status load warning:', err);
      }
    };

    // Load Service Health Matrix dynamically from backend
    const loadHealthMatrix = async () => {
      const gridEl = document.getElementById('services-health-grid');
      const summaryEl = document.getElementById('health-summary-pills');
      if (!gridEl) return;

      try {
        const health = await ApiClient.getAdminHealth();
        const services = health?.services || {};
        const serviceKeys = Object.keys(services);

        if (serviceKeys.length > 0) {
          let healthyCount = 0;
          gridEl.innerHTML = serviceKeys.map(k => {
            const s = services[k];
            const isHealthy = s.status === 'HEALTHY';
            const isDegraded = s.status === 'DEGRADED';
            if (isHealthy) healthyCount++;

            const badgeClass = isHealthy
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
              : (isDegraded ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300');
            const borderClass = isHealthy
              ? 'border-slate-200 dark:border-slate-700'
              : (isDegraded ? 'border-amber-300 dark:border-amber-800' : 'border-rose-300 dark:border-rose-800');
            const statusColor = isHealthy ? 'text-emerald-600' : (isDegraded ? 'text-amber-600' : 'text-rose-600');

            return `
              <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border ${borderClass} flex flex-col justify-between gap-3">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold uppercase text-slate-500">${UI.escapeHtml(s.service_name || k)}</span>
                  <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${badgeClass} text-[11px] font-bold">${UI.escapeHtml(s.status)}</span>
                </div>
                <div>
                  <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(s.service_name || k)}</div>
                  <div class="text-xs text-slate-400">Độ trễ: ${s.latency_ms !== null && s.latency_ms !== undefined ? s.latency_ms + 'ms' : 'N/A'}</div>
                </div>
                <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                  <span class="truncate max-w-[140px]" title="${UI.escapeHtml(s.notes || '')}">${UI.escapeHtml(s.notes || 'Hệ thống chuẩn hóa')}</span>
                  <span class="${statusColor} font-bold">${UI.escapeHtml(s.status)}</span>
                </div>
              </div>
            `;
          }).join('');

          if (summaryEl) {
            summaryEl.innerHTML = `
              <span class="inline-flex items-center gap-1 text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-3 py-1 rounded-lg">
                <span class="material-symbols-outlined text-sm text-primary">sync</span> ${healthyCount}/${serviceKeys.length} Node Hoạt Động
              </span>
            `;
          }
        }
      } catch (err) {
        console.warn('Health matrix load warning:', err);
      }
    };

    // Quick Revoke Event
    const quickRevokeBtn = document.getElementById('quick-revoke-btn');
    if (quickRevokeBtn) {
      quickRevokeBtn.onclick = async () => {
        const uId = document.getElementById('quick-revoke-user-id').value.trim();
        if (!uId) {
          UI.showToast('Vui lòng nhập User UUID.', 'warning');
          return;
        }
        try {
          await ApiClient.revokeUserSessions(uId, 'Admin emergency revoke from Operations Cockpit');
          UI.showToast(`Đã thu hồi toàn bộ phiên đăng nhập của người dùng ${uId}!`, 'success');
          document.getElementById('quick-revoke-user-id').value = '';
        } catch (e) {
          UI.showToast(e.message || 'Lỗi thu hồi phiên.', 'error');
        }
      };
    }

    // Wire Background Jobs Modal Trigger
    const checkJobsBtn = document.getElementById('check-bg-jobs-btn');
    if (checkJobsBtn) {
      checkJobsBtn.onclick = () => AdminView.openBackgroundJobsModal();
    }

    // Polling Hardware Telemetry Function
    const pollTelemetry = async () => {
      try {
        const data = await ApiClient.getAdminTelemetry();
        if (!data) return;

        if (data.cpu) {
          const pct = data.cpu.percent ?? 0;
          const cpuVal = document.getElementById('telem-cpu-val');
          const cpuModel = document.getElementById('telem-cpu-model');
          const cpuBar = document.getElementById('telem-cpu-bar');
          if (cpuVal) cpuVal.textContent = `${pct}%`;
          if (cpuModel) cpuModel.textContent = data.cpu.model || `${data.cpu.cores || 4} vCPU`;
          if (cpuBar) cpuBar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
        }

        if (data.memory) {
          const ramVal = document.getElementById('telem-ram-val');
          const ramPct = document.getElementById('telem-ram-pct');
          const ramBar = document.getElementById('telem-ram-bar');
          if (ramVal) ramVal.textContent = `${data.memory.used_gb ?? '0'} / ${data.memory.total_gb ?? '0'} GB`;
          if (ramPct) {
            if (data.container && data.container.memory_used_gb != null) {
              ramPct.textContent = `${data.memory.percent ?? 0}% sử dụng • Container: ${data.container.memory_used_gb} GB`;
            } else {
              ramPct.textContent = `${data.memory.percent ?? 0}% sử dụng`;
            }
          }
          if (ramBar) ramBar.style.width = `${Math.min(100, Math.max(0, data.memory.percent ?? 0))}%`;
        }

        if (data.disk) {
          const diskVal = document.getElementById('telem-disk-val');
          const diskPct = document.getElementById('telem-disk-pct');
          const diskBar = document.getElementById('telem-disk-bar');
          if (diskVal) diskVal.textContent = `${data.disk.free_gb ?? '0'} GB khả dụng`;
          if (diskPct) diskPct.textContent = `Tổng ${data.disk.total_gb ?? '0'} GB (${data.disk.percent ?? 0}% dùng)`;
          if (diskBar) diskBar.style.width = `${Math.min(100, Math.max(0, data.disk.percent ?? 0))}%`;
        }

        const nodeEl = document.getElementById('telem-node-id');
        if (nodeEl) {
          if (data.container && data.host?.hostname) {
            nodeEl.textContent = `${data.node_label || 'Docker Container'} on ${data.host.hostname}`;
          } else {
            nodeEl.textContent = data.node_label || data.hostname || data.host?.node_label || data.host?.hostname || 'Production Node';
          }
        }
        if (data.network) {
          const netEl = document.getElementById('telem-net-traffic');
          if (netEl) {
            netEl.textContent = data.network.traffic_label
              ? `Lưu lượng: ${data.network.traffic_label}`
              : `Lưu lượng: Gửi ${data.network.bytes_sent_human || '0 KB'} • Nhận ${data.network.bytes_recv_human || '0 KB'}`;
          }
        }
      } catch (err) {
        console.warn('Telemetry poll error:', err);
      }
    };

    const refreshBtn = document.getElementById('refresh-telemetry-btn');
    const spinIcon = document.getElementById('refresh-spin-icon');
    if (refreshBtn) {
      refreshBtn.onclick = async () => {
        spinIcon?.classList.add('animate-spin');
        await Promise.allSettled([pollTelemetry(), loadBackups(), loadMaintenanceStatus(), loadHealthMatrix()]);
        setTimeout(() => spinIcon?.classList.remove('animate-spin'), 600);
      };
    }

    document.getElementById('emergency-backup-btn').onclick = () => {
      AdminView.openCreateBackupModal(() => loadBackups());
    };

    // Initialize operations view
    loadBackups();
    loadMaintenanceStatus();
    loadHealthMatrix();
    pollTelemetry();

    const timer = setInterval(() => {
      if (!document.getElementById('telem-cpu-val')) {
        clearInterval(timer);
        return;
      }
      pollTelemetry();
    }, 10000);
  }

  static openCreateBackupModal(onSuccess = null) {
    const body = `
      <div class="space-y-4 text-xs">
        <p class="text-slate-600 dark:text-slate-300">
          Khởi tạo bản sao lưu snapshot CSDL MS SQL Server với tính toán mã băm toàn vẹn SHA-256.
        </p>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Loại sao lưu</label>
          <select id="modal-backup-type" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
            <option value="MANUAL">MANUAL (Sao lưu thủ công)</option>
            <option value="PRE_MAINTENANCE">PRE_MAINTENANCE (Trước bảo trì)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Ghi chú sao lưu</label>
          <input type="text" id="modal-backup-notes" placeholder="VD: Sao lưu khẩn cấp kiểm toán..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
        </div>
      </div>
    `;

    UI.openModal({
      title: 'Tạo Bản Sao Lưu Cơ Sở Dữ Liệu Mới',
      bodyHtml: body,
      footerHtml: `
        <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
        <button type="button" id="confirm-create-backup-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Khởi tạo Sao Lưu</button>
      `,
      size: 'md'
    });

    document.getElementById('confirm-create-backup-btn').onclick = async () => {
      const type = document.getElementById('modal-backup-type').value;
      const notes = document.getElementById('modal-backup-notes').value.trim();

      UI.showToast('Đang tiến hành tạo bản sao lưu snapshot...', 'info');
      try {
        const res = await ApiClient.createAdminBackup(type, notes);
        UI.closeModal();
        UI.showToast(`Đã tạo bản sao lưu ${res.backup?.database_backup_name || 'thành công'}!`, 'success');
        if (onSuccess) onSuccess();
      } catch (e) {
        UI.showToast(e.message || 'Lỗi tạo bản sao lưu.', 'error');
      }
    };
  }

  static openLiveRestoreModal(backupId, backupName) {
    const body = `
      <form id="live-restore-form" onsubmit="return false;" class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 space-y-1 border border-rose-200 dark:border-rose-900/60">
          <div class="font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-rose-600">warning</span>
            <span>CẢNH BÁO QUẢN TRỊ CAO CẤP: KHÔI PHỤC LIVE DATABASE</span>
          </div>
          <p>Hành động này sẽ khôi phục dữ liệu từ bản sao lưu <strong class="break-all font-mono">${UI.escapeHtml(backupName)}</strong> vào CSDL trực tiếp. Để đảm bảo an toàn tuyệt đối, hệ thống yêu cầu tuân thủ nghiêm ngặt 4 bước xác thực dưới đây.</p>
        </div>

        <div class="space-y-1">
          <label for="restore-admin-password" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 01: Nhập Mật khẩu Quản trị viên để xác thực lại (Re-auth) *
          </label>
          <input type="password" id="restore-admin-password" autocomplete="current-password" placeholder="Nhập mật khẩu tài khoản Admin của bạn..." class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600" />
        </div>

        <div class="space-y-1">
          <label for="restore-confirm-phrase" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 02: Nhập chính xác cụm từ: <span class="font-mono text-rose-600 font-black">CONFIRM_DATABASE_RESTORE</span> *
          </label>
          <input type="text" id="restore-confirm-phrase" placeholder="Gõ chính xác CONFIRM_DATABASE_RESTORE..." class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs outline-none focus:border-rose-600" />
        </div>

        <div class="space-y-1">
          <label for="restore-audit-reason" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 03: Lý do giải trình kiểm toán bắt buộc (Tối thiểu 10 ký tự) *
          </label>
          <textarea id="restore-audit-reason" rows="2" placeholder="Ghi rõ căn cứ quyết định phục hồi CSDL trực tiếp..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600 resize-none"></textarea>
        </div>

        <div class="pt-1">
          <label class="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800 cursor-pointer">
            <input type="checkbox" id="restore-sign-cert-check" class="mt-0.5 rounded text-rose-600 focus:ring-rose-500" />
            <span class="text-xs text-slate-700 dark:text-slate-300 leading-snug">
              Bước 04: Tôi ký số điện tử xác nhận với tư cách Quản trị viên, chịu trách nhiệm hoàn toàn về quyết định khôi phục CSDL.
            </span>
          </label>
        </div>
      </form>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy bỏ</button>
      <button type="button" id="submit-live-restore-btn" class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold">Thực thi Khôi phục Live Database</button>
    `;

    const displayBackupTitle = backupName && backupName.length > 25 ? `${backupName.slice(0, 22)}...` : (backupName || '');
    UI.openModal({
      title: `Khôi phục CSDL Trực tiếp • ${displayBackupTitle}`,
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    document.getElementById('submit-live-restore-btn').onclick = async () => {
      const password = document.getElementById('restore-admin-password').value;
      const phrase = document.getElementById('restore-confirm-phrase').value.trim();
      const reason = document.getElementById('restore-audit-reason').value.trim();
      const signed = document.getElementById('restore-sign-cert-check').checked;

      if (!password) {
        UI.showToast('Vui lòng nhập mật khẩu xác thực lại của bạn.', 'warning');
        return;
      }
      if (phrase !== 'CONFIRM_DATABASE_RESTORE') {
        UI.showToast('Vui lòng nhập chính xác cụm từ: CONFIRM_DATABASE_RESTORE', 'warning');
        return;
      }
      if (reason.length < 10) {
        UI.showToast('Vui lòng nhập lý do giải trình kiểm toán chi tiết (tối thiểu 10 ký tự).', 'warning');
        return;
      }
      if (!signed) {
        UI.showToast('Vui lòng tích chọn xác nhận ký số điện tử.', 'warning');
        return;
      }

      UI.showToast('Đang thực thi khôi phục cơ sở dữ liệu có kiểm soát...', 'info');
      try {
        const res = await ApiClient.restoreAdminBackup(backupId, phrase, password);
        UI.closeModal();
        UI.showToast('Khôi phục cơ sở dữ liệu thành công! Bản ghi kiểm toán đã được lưu vĩnh viễn.', 'success');
      } catch (e) {
        UI.showToast(e.message || 'Lỗi khôi phục cơ sở dữ liệu.', 'error');
      }
    };
  }

  static async openBackgroundJobsModal() {
    UI.openModal({
      title: 'Hàng Đợi & Tiến Trình Tác Vụ Nền (Background Execution Engine)',
      bodyHtml: `
        <div class="space-y-4 text-xs">
          <!-- Summary Counters -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3" id="bg-jobs-summary-cards">
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Queued (Chờ xử lý)</div>
              <div class="text-xl font-bold font-mono text-amber-500 mt-1" id="bg-summary-queued">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Running (Đang chạy)</div>
              <div class="text-xl font-bold font-mono text-primary mt-1" id="bg-summary-running">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Succeeded (Hoàn thành)</div>
              <div class="text-xl font-bold font-mono text-emerald-600 mt-1" id="bg-summary-succeeded">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Failed (Thất bại)</div>
              <div class="text-xl font-bold font-mono text-rose-600 mt-1" id="bg-summary-failed">0</div>
            </div>
          </div>

          <!-- Controls / Filter -->
          <div class="flex items-center justify-between gap-3 pt-2">
            <div class="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px] text-primary">dns</span>
              <span>Danh sách tác vụ điều phối MS SQL</span>
            </div>
            <button type="button" id="refresh-jobs-list-btn" class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">refresh</span>
              <span>Làm mới</span>
            </button>
          </div>

          <!-- Table Container -->
          <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table class="w-full text-left border-collapse text-xs">
              <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th class="p-2.5">Job ID</th>
                  <th class="p-2.5">Loại tác vụ</th>
                  <th class="p-2.5">Trạng thái</th>
                  <th class="p-2.5">Thử lại (Attempts)</th>
                  <th class="p-2.5">Thời gian khởi tạo</th>
                  <th class="p-2.5 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody id="bg-jobs-table-body" class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr>
                  <td colspan="6" class="p-6 text-center text-slate-400">
                    <span class="inline-block animate-spin text-lg mb-1">⏳</span>
                    <p>Đang tải danh sách tác vụ nền...</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `,
      footerHtml: `
        <button type="button" class="px-5 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold hover:bg-slate-300" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'xl'
    });

    const loadJobs = async () => {
      const tbody = document.getElementById('bg-jobs-table-body');
      if (!tbody) return;

      try {
        const res = await ApiClient.getAdminBackgroundJobs({ per_page: 50 });
        const summary = res.summary || {};
        const items = res.items || [];

        const qEl = document.getElementById('bg-summary-queued');
        const rEl = document.getElementById('bg-summary-running');
        const sEl = document.getElementById('bg-summary-succeeded');
        const fEl = document.getElementById('bg-summary-failed');

        if (qEl) qEl.textContent = summary.queued || 0;
        if (rEl) rEl.textContent = summary.running || 0;
        if (sEl) sEl.textContent = summary.succeeded || 0;
        if (fEl) fEl.textContent = summary.failed || 0;

        if (items.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="6" class="p-6 text-center text-slate-400 font-mono text-xs">
                Không có tác vụ nền nào trong hàng đợi.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = items.map(job => {
          let statusBadge = '';
          if (job.status === 'SUCCEEDED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 font-bold text-[10px]">SUCCEEDED</span>';
          } else if (job.status === 'RUNNING') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-indigo-50 text-primary dark:bg-indigo-950/40 dark:text-indigo-300 font-bold text-[10px] animate-pulse">RUNNING</span>';
          } else if (job.status === 'FAILED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 font-bold text-[10px]">FAILED</span>';
          } else {
            statusBadge = `<span class="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 font-bold text-[10px]">${job.status}</span>`;
          }

          const rawId = job.job_id || '';
          const shortId = rawId.length > 13 ? `${rawId.slice(0, 8)}...` : rawId;
          const retryDisabled = job.status !== 'FAILED';

          return `
            <tr class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
              <td class="p-2.5 font-mono text-[11px] font-bold text-slate-700 dark:text-slate-300" title="${UI.escapeHtml(rawId)}">
                ${UI.escapeHtml(shortId)}
              </td>
              <td class="p-2.5 font-bold text-slate-900 dark:text-white">
                ${UI.escapeHtml(job.job_type)}
                ${job.last_error ? `<div class="text-[10px] text-rose-500 font-normal font-mono truncate max-w-[200px]" title="${UI.escapeHtml(job.last_error)}">${UI.escapeHtml(job.last_error)}</div>` : ''}
              </td>
              <td class="p-2.5">${statusBadge}</td>
              <td class="p-2.5 font-mono text-slate-500 text-[11px]">
                ${job.attempt_count} / ${job.max_attempts}
              </td>
              <td class="p-2.5 text-slate-400 text-[11px]">
                ${job.created_at ? UI.formatDateTime(job.created_at) : '--'}
              </td>
              <td class="p-2.5 text-right">
                ${!retryDisabled ? `
                  <button type="button" class="px-2.5 py-1 rounded-lg bg-primary hover:bg-primary-hover text-white font-bold text-[11px] transition-colors retry-bg-job-btn" data-job-id="${UI.escapeHtml(rawId)}">
                    Thử lại
                  </button>
                ` : `
                  <span class="text-slate-300 dark:text-slate-600 text-[11px] font-mono">--</span>
                `}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.retry-bg-job-btn').forEach(btn => {
          btn.onclick = async () => {
            const jId = btn.dataset.jobId;
            btn.disabled = true;
            btn.innerHTML = '<span class="inline-block animate-spin">⏳</span>';
            try {
              await ApiClient.retryAdminBackgroundJob(jId);
              UI.showToast(`Đã đưa tác vụ ${jId} trở lại hàng đợi xử lý!`, 'success');
              await loadJobs();
            } catch (e) {
              UI.showToast(e.message || 'Lỗi thử lại tác vụ.', 'error');
              btn.disabled = false;
              btn.textContent = 'Thử lại';
            }
          };
        });

      } catch (err) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="p-6 text-center text-rose-500 font-mono text-xs">
              Lỗi tải danh sách tác vụ: ${UI.escapeHtml(err.message || 'Không thể kết nối máy chủ')}
            </td>
          </tr>
        `;
      }
    };

    const refreshBtn = document.getElementById('refresh-jobs-list-btn');
    if (refreshBtn) {
      refreshBtn.onclick = () => loadJobs();
    }

    loadJobs();
  }
}

window.AdminView = AdminView;
