/**
 * PWD301 LMS - Single Page Application (SPA) Master Router & Shell Controller
 * Warm Editorial Edition - Minimalist Instant Navigation, Role-based Menus,
 * Micro-Progress Transitions, Focus Fullscreen Exam Mode.
 */

class AppRouter {
  static get instance() {
    return window.app || null;
  }

  constructor() {
    this.currentUser = null;
    this.currentRole = 'STUDENT';
    this.viewport = document.getElementById('app-viewport');
    this.sidebar = document.getElementById('app-sidebar');
    this.topbar = document.getElementById('app-topbar');
    this.adminNavBadges = {
      courses: 0,
      applications: 0
    };
  }

  async init() {
    // 1. Initial auth state check
    await this.refreshCurrentUser();

    // 2. Setup hash change listener
    window.addEventListener('hashchange', () => this.handleRoute());

    // 3. Setup global theme listener
    this.initThemeToggle();

    // 4. Setup Notifications Bell & Badge Polling
    this.initNotifications();

    // 4.2 Initial Admin Navigation Badges (Pending approvals)
    if (this.currentRole === 'ADMIN') {
      this.fetchAdminPendingCounts();
    }

    // 4.5 Setup Mobile Navigation Drawer
    this.initMobileNav();

    // 5. Setup Floating AI Tutor
    if (window.FloatingAITutor) {
      FloatingAITutor.init();
    }

    // 6. Initial route resolution
    await this.handleRoute();
  }

  initMobileNav() {
    const btn = document.getElementById('topbar-mobile-menu-btn');
    const drawer = document.getElementById('mobile-nav-drawer');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const closeBtn = document.getElementById('mobile-nav-close-btn');

    if (!btn || !drawer || !backdrop) return;

    const open = () => {
      drawer.classList.remove('hidden');
      backdrop.classList.remove('hidden');
    };

    const close = () => {
      drawer.classList.add('hidden');
      backdrop.classList.add('hidden');
    };

    btn.onclick = open;
    if (closeBtn) closeBtn.onclick = close;
    backdrop.onclick = close;

    document.getElementById('mobile-navigation-items')?.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        close();
      }
    });
  }

  async refreshCurrentUser() {
    try {
      const prevUserId = this.currentUser?.id;
      this.currentUser = await ApiClient.getCurrentUser();
      if (this.currentUser) {
        this.currentRole = this.currentUser.primary_role || (this.currentUser.role_codes && this.currentUser.role_codes[0]) || 'STUDENT';
        if (prevUserId && prevUserId !== this.currentUser.id) {
          this.notificationsCache = null;
        }
        this.loadCachedNotifications();
      } else {
        this.currentRole = 'STUDENT';
        this.notificationsCache = null;
      }
    } catch {
      this.currentUser = null;
      this.notificationsCache = null;
    }
    this.updateUserUI();
    this.refreshNotificationBadge();
    return this.currentUser;
  }

  parseHash(rawHash = window.location.hash || '') {
    const raw = rawHash;
    const qIdx = raw.indexOf('?');
    const path = qIdx !== -1 ? raw.substring(0, qIdx) : raw;
    const query = {};

    if (qIdx !== -1) {
      const searchStr = raw.substring(qIdx + 1);
      const params = new URLSearchParams(searchStr);
      for (const [key, value] of params.entries()) {
        query[key] = value;
      }
    }

    return { path: path || '#/', query };
  }

  handleRoute() {
    if (this._isRouting) {
      this._rerouteRequested = true;
      return this._routingPromise;
    }
    this._isRouting = true;

    if (typeof UI !== 'undefined' && typeof UI.startMicroLoading === 'function') {
      UI.startMicroLoading();
    }

    this._routingPromise = (async () => {
      try {
        let routeHash;
        do {
          this._rerouteRequested = false;
          routeHash = window.location.hash || '#/';
          await this.renderRoute(routeHash);
        } while (
          this._rerouteRequested
          || (window.location.hash || '#/') !== routeHash
        );
      } finally {
        this._isRouting = false;
        this._routingPromise = null;
        if (typeof UI !== 'undefined' && typeof UI.stopMicroLoading === 'function') {
          UI.stopMicroLoading();
        }
      }
    })();

    return this._routingPromise;
  }

  createRouteStagingViewport() {
    const stagingViewport = document.createElement('div');
    stagingViewport.className = 'route-render-stage';
    stagingViewport.setAttribute('aria-hidden', 'true');
    stagingViewport.inert = true;
    Object.assign(stagingViewport.style, {
      position: 'absolute',
      inset: '0',
      width: '100%',
      visibility: 'hidden',
      pointerEvents: 'none',
    });
    this.viewport.prepend(stagingViewport);
    this.viewport.setAttribute('aria-busy', 'true');
    return stagingViewport;
  }

  commitRouteStagingViewport(stagingViewport, path) {
    const renderedContent = Array.from(stagingViewport.childNodes);
    stagingViewport.remove();
    this.viewport.replaceChildren(...renderedContent);
    this.viewport.removeAttribute('aria-busy');
    this.applyRouteChrome(path);
  }

  applyRouteChrome(path) {
    if (this._needsUserUiRefresh) {
      this.updateUserUI();
      this._needsUserUiRefresh = false;
    }
    this.toggleShell(true);
    this.renderDynamicSidebar();
    this.updateTopbarBreadcrumb(path);

    if (typeof UI !== 'undefined') {
      if (typeof UI.closeModal === 'function') UI.closeModal();
      if (typeof UI.closeDrawer === 'function') UI.closeDrawer();
    }
    document.querySelectorAll('body > .fixed.inset-0:not(#app-drawer-backdrop):not(#modal-container)').forEach(m => m.remove());

    const isFocusRoute = path.includes('/attempt')
      || path.includes('/waiting-room')
      || path.includes('/lessons/new')
      || (path.includes('/lessons/') && path.includes('/edit'))
      || path.includes('/instructor/exams');
    document.body.classList.toggle('fullscreen-focus-mode', isFocusRoute);

    const isExamActive = path.includes('/attempt') || path.includes('/waiting-room');
    const floatingAi = document.getElementById('floating-ai-container');
    if (!floatingAi) return;
    floatingAi.classList.toggle('hidden', isExamActive);
    if (isExamActive && window.FloatingAITutor && typeof window.FloatingAITutor.close === 'function') {
      window.FloatingAITutor.close();
    }
  }

  async renderRoute(routeHash) {
    if (!this.viewport) return;
    const { path, query } = this.parseHash(routeHash);

    // Auth Guard: If not logged in and not on auth path, redirect to auth
    if (!this.currentUser && path !== '#/auth' && path !== '#/login') {
      await this.refreshCurrentUser();
      if (!this.currentUser) {
        this.toggleShell(false);
        this.renderAuth();
        return;
      }
    }

    // If logged in and on #/auth or #/login, redirect to role home
    if (this.currentUser && (path === '#/auth' || path === '#/login' || path === '#/' || path === '')) {
      this.redirectToRoleHome();
      return;
    }

    // Role Permission Guard with Automatic Multi-Role Perspective Switching
    const userRoles = (this.currentUser && (this.currentUser.role_codes || [this.currentUser.primary_role || 'STUDENT'])) || ['STUDENT'];
    const hasAdminRole = userRoles.includes('ADMIN');
    const hasInstructorRole = userRoles.includes('INSTRUCTOR') || hasAdminRole;

    if (path.startsWith('#/admin')) {
      if (!hasAdminRole) {
        UI.showToast('Bạn không có quyền truy cập khu vực Quản trị viên.', 'warning');
        this.redirectToRoleHome();
        return;
      }
      if (this.currentRole !== 'ADMIN') {
        try {
          await ApiClient.switchRole('ADMIN');
        } catch (err) {
          console.warn('Auto switchRole to ADMIN error:', err);
        }
        this.currentRole = 'ADMIN';
        this._needsUserUiRefresh = true;
      }
    } else if (path.startsWith('#/instructor')) {
      if (!hasInstructorRole) {
        UI.showToast('Bạn không có quyền truy cập khu vực Giảng viên.', 'warning');
        this.redirectToRoleHome();
        return;
      }
      if (this.currentRole !== 'INSTRUCTOR' && this.currentRole !== 'ADMIN') {
        try {
          await ApiClient.switchRole('INSTRUCTOR');
        } catch (err) {
          console.warn('Auto switchRole to INSTRUCTOR error:', err);
        }
        this.currentRole = 'INSTRUCTOR';
        this._needsUserUiRefresh = true;
      }
    }

    // Route Dispatcher
    const stagingViewport = this.createRouteStagingViewport();
    try {
      await this.dispatchRoute(path, query, stagingViewport);
      if ((window.location.hash || '#/') === routeHash) {
        if (stagingViewport.childNodes.length > 0) {
          this.commitRouteStagingViewport(stagingViewport, path);
        } else {
          stagingViewport.remove();
          this.viewport.removeAttribute('aria-busy');
        }
      } else {
        stagingViewport.remove();
        this._rerouteRequested = true;
      }
    } catch (error) {
      stagingViewport.remove();
      this.viewport.removeAttribute('aria-busy');
      throw error;
    }
  }

  redirectToRoleHome() {
    let target = '#/student/dashboard';
    if (this.currentRole === 'ADMIN') {
      target = '#/admin/governance';
    } else if (this.currentRole === 'INSTRUCTOR') {
      target = '#/instructor/dashboard';
    }
    if (window.location.hash === target) {
      this.handleRoute();
    } else {
      window.location.hash = target;
    }
  }

  toggleShell(visible) {
    if (this.topbar) this.topbar.style.display = visible ? 'flex' : 'none';
    if (this.sidebar) this.sidebar.style.display = 'none';
  }

  renderAuth() {
    if (!this.viewport) return;
    this.viewport.innerHTML = AuthView.render();
    AuthView.attachEvents();
  }

  async dispatchRoute(path, query, viewport = this.viewport) {
    if (!viewport) return;

    // --- Student Routes ---
    if (path === '#/student/dashboard') {
      await StudentView.renderDashboard(viewport);
    } else if (path === '#/student/catalog') {
      await StudentView.renderCatalog(viewport);
    } else if (path === '#/student/courses') {
      await StudentView.renderMyLearning(viewport);
    } else if (path === '#/student/courses/detail' || (path.startsWith('#/student/courses/') && !path.includes('/lessons/'))) {
      const courseId = query.id || path.replace('#/student/courses/', '');
      await StudentView.renderCourseDetail(viewport, courseId, query.tab || 'syllabus');
    } else if (path === '#/student/lessons/reader' || (path.startsWith('#/student/courses/') && path.includes('/lessons/'))) {
      let cId = query.course_id;
      let lId = query.lesson_id;
      const m = path.match(/#\/student\/courses\/([^/]+)\/lessons\/([^/]+)/);
      if (m) {
        cId = m[1];
        lId = m[2];
      }
      await StudentView.renderLessonReader(viewport, cId, lId);
    } else if (path === '#/student/assessments') {
      await StudentView.renderAssessmentsList(viewport);
    } else if (path === '#/student/assessments/waiting-room' || path.endsWith('/waiting-room')) {
      const aId = query.id || path.replace('#/student/assessments/', '').replace('/waiting-room', '');
      await StudentView.renderWaitingRoom(viewport, aId);
    } else if (path === '#/student/assessments/attempt' || (path.startsWith('#/student/assessments/attempts/') && !path.endsWith('/results'))) {
      const attId = query.id || path.replace('#/student/assessments/attempts/', '');
      await StudentView.renderAttemptConsole(viewport, attId);
    } else if (path === '#/student/assessments/results' || path.endsWith('/results')) {
      const attId = query.id || path.replace('#/student/assessments/attempts/', '').replace('/results', '');
      await StudentView.renderAttemptResults(viewport, attId);
    } else if (path === '#/student/ai-assistant') {
      window.location.hash = '#/student/dashboard';
    } else if (path === '#/student/become-instructor') {
      await StudentView.renderBecomeInstructor(viewport);
    } else if (path === '#/student/settings' || path === '#/settings') {
      await StudentView.renderSettings(viewport);
    }

    // --- Instructor Routes ---
    else if (path === '#/instructor/dashboard') {
      await InstructorView.renderDashboard(viewport);
    } else if (path === '#/instructor/courses') {
      await InstructorView.renderCourses(viewport);
    } else if (path === '#/instructor/courses/manage') {
      await InstructorView.renderCourseManage(viewport, query.id, query.tab || 'curriculum');
    } else if (path.startsWith('#/instructor/courses/') && path.endsWith('/manage')) {
      const parts = path.split('/');
      const courseId = parts[3];
      await InstructorView.renderCourseManage(viewport, courseId, query.tab || 'curriculum');
    } else if (path.startsWith('#/instructor/courses/') && path.includes('/lessons/new')) {
      const parts = path.split('/');
      const courseId = parts[3];
      await InstructorView.renderLessonAuthoringStudio(viewport, courseId, null);
    } else if (path.startsWith('#/instructor/courses/') && path.includes('/lessons/') && path.endsWith('/edit')) {
      const parts = path.split('/');
      const courseId = parts[3];
      const lessonId = parts[5];
      await InstructorView.renderLessonAuthoringStudio(viewport, courseId, lessonId);
    } else if (path === '#/instructor/questions/studio' || (path === '#/instructor/questions' && query.studio)) {
      await InstructorView.renderExtendedQuestionStudio(viewport, query.course);
    } else if (path === '#/instructor/questions') {
      await InstructorView.renderQuestions(viewport, query.course);
    } else if (path === '#/instructor/exams' || path === '#/instructor/exams/hub') {
      await InstructorView.renderExamsHub(viewport, query);
    } else if (path === '#/instructor/exams/editor') {
      InstructorView.renderExamEditor(viewport);
    } else if (path === '#/instructor/exams/interactive') {
      InstructorView.renderExamInteractive(viewport);
    } else if (path === '#/instructor/exams/excel') {
      InstructorView.renderExamExcel(viewport);
    } else if (path === '#/instructor/exams/moodle') {
      InstructorView.renderExamMoodle(viewport);
    } else if (path === '#/instructor/exams/matrix') {
      InstructorView.renderExamMatrix(viewport);
    } else if (path === '#/instructor/exams/settings') {
      InstructorView.renderExamSettings(viewport);
    }

    // --- Admin Routes ---
    else if (path === '#/admin/governance') {
      await AdminView.renderGovernance(viewport, query.tab || 'users');
    } else if (path === '#/admin/operations') {
      await AdminView.renderOperations(viewport);
    }

    // Fallback
    else {
      this.redirectToRoleHome();
    }
  }

  // =========================================================================
  // Top Navigation Bar & Mobile Drawer Menus (Warm Editorial Pill Tabs)
  // =========================================================================
  updateAdminNavBadges(badges = {}) {
    this.adminNavBadges = { ...this.adminNavBadges, ...badges };
    this.renderDynamicSidebar();
  }

  async fetchAdminPendingCounts() {
    if (this.currentRole !== 'ADMIN') return;
    try {
      const [coursesRes, crRes, appsRes] = await Promise.allSettled([
        ApiClient.getPendingCourses(),
        ApiClient.getAdminChangeRequests('PENDING'),
        ApiClient.getAdminInstructorApplications('PENDING')
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

      this.adminNavBadges.courses = pendingCoursesCount + pendingCrCount;
      this.adminNavBadges.applications = pendingAppsCount;
      this.renderDynamicSidebar();
    } catch (err) {
      console.warn('Silent admin pending badge fetch warning:', err);
    }
  }

  // =========================================================================
  // Top Navigation Bar & Mobile Drawer Menus (Warm Editorial Pill Tabs)
  // =========================================================================
  renderDynamicSidebar() {
    const role = this.currentRole;
    const { path } = this.parseHash();

    let menu = [];

    if (role === 'ADMIN') {
      const subRole = this.currentUser?.admin_sub_role || 'ADMIN_PRIMARY';
      if (subRole === 'ADMIN_COURSE_REVIEW') {
        menu = [
          { label: 'Điều hành học vụ', path: '#/admin/governance', icon: 'manage_accounts', badge: 0 },
          { label: 'Duyệt khóa học', path: '#/admin/governance?tab=courses', icon: 'fact_check', badge: this.adminNavBadges?.courses || 0 },
        ];
      } else if (subRole === 'ADMIN_INSTRUCTOR_REVIEW') {
        menu = [
          { label: 'Điều hành học vụ', path: '#/admin/governance', icon: 'manage_accounts', badge: 0 },
          { label: 'Duyệt giảng viên', path: '#/admin/governance?tab=applications', icon: 'badge', badge: this.adminNavBadges?.applications || 0 },
        ];
      } else if (subRole === 'ADMIN_TEACHING_ASSIGNMENT') {
        menu = [
          { label: 'Điều hành học vụ', path: '#/admin/governance', icon: 'manage_accounts', badge: 0 },
          { label: 'Phân công giảng dạy', path: '#/admin/governance?tab=reassign', icon: 'swap_horiz', badge: 0 },
        ];
      } else if (subRole === 'ADMIN_SYSTEM_MONITORING') {
        menu = [
          { label: 'Vận hành hệ thống', path: '#/admin/operations', icon: 'monitoring', badge: 0 },
        ];
      } else {
        // ADMIN_PRIMARY / Super Admin
        menu = [
          { label: 'Người dùng & Phân quyền', path: '#/admin/governance', icon: 'manage_accounts', badge: 0 },
          { label: 'Duyệt khóa học', path: '#/admin/governance?tab=courses', icon: 'fact_check', badge: this.adminNavBadges?.courses || 0 },
          { label: 'Duyệt giảng viên', path: '#/admin/governance?tab=applications', icon: 'badge', badge: this.adminNavBadges?.applications || 0 },
          { label: 'Phân công giảng dạy', path: '#/admin/governance?tab=reassign', icon: 'swap_horiz', badge: 0 },
          { label: 'An toàn & Kiểm toán', path: '#/admin/governance?tab=security', icon: 'policy', badge: 0 },
          { label: 'Vận hành hệ thống', path: '#/admin/operations', icon: 'monitoring', badge: 0 },
        ];
      }
    } else if (role === 'INSTRUCTOR') {
      menu = [
        { label: 'Trang chủ', path: '#/instructor/dashboard', icon: 'home' },
        { label: 'Khóa học', path: '#/instructor/courses', icon: 'auto_stories' },
        { label: 'Soạn đề thi', path: '#/instructor/exams', icon: 'assignment_add' },
      ];
    } else {
      menu = [
        { label: 'Trang chủ', path: '#/student/dashboard', icon: 'home' },
        { label: 'Khám phá Khóa học', path: '#/student/catalog', icon: 'explore' },
        { label: 'Khóa học của tôi', path: '#/student/courses', icon: 'school' },
        { label: 'Bài kiểm tra', path: '#/student/assessments', icon: 'quiz' },
        { label: 'Đăng ký Giảng viên', path: '#/student/become-instructor', icon: 'badge' },
        { label: 'Cài đặt', path: '#/student/settings', icon: 'settings' },
      ];
    }

    // 1. Populate Desktop Topbar Navigation Items (Warm Editorial Pill Tabs)
    const topNav = document.getElementById('topbar-navigation-items');
    const currentFullHash = window.location.hash || '#/';
    if (topNav) {
      topNav.innerHTML = menu.map(m => {
        const isPathActive = m.path.includes('?')
          ? (currentFullHash === m.path || currentFullHash.startsWith(m.path + '&'))
          : (m.path === '#/admin/governance'
            ? (currentFullHash === m.path || currentFullHash === m.path + '/' || currentFullHash === m.path + '?tab=users')
            : (currentFullHash === m.path || currentFullHash === m.path + '/' || (!currentFullHash.includes('?') && currentFullHash.startsWith(m.path))));
        const badgeNum = Number(m.badge) || 0;
        return `
          <a
            href="${m.path}"
            class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              isPathActive
                ? 'bg-[#FFFFFF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] font-bold shadow-2xs'
                : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#FAF9F5] dark:hover:bg-[#262524] hover:text-[#222120] dark:hover:text-[#EDEDEB]'
            }"
            ${badgeNum > 0 ? `title="${m.label} (${badgeNum} việc cần xử lý)"` : ''}
          >
            <span class="material-symbols-outlined text-[16px]">${m.icon}</span>
            <span class="inline-flex items-center">
              <span>${m.label}</span>
              ${badgeNum > 0 ? `
                <sup class="ml-0.5 -top-1.5 text-[11px] font-black text-amber-600 dark:text-amber-400 select-none leading-none tracking-tight">${badgeNum > 99 ? '99+' : badgeNum}</sup>
              ` : ''}
            </span>
          </a>
        `;
      }).join('');
    }

    // 2. Populate Mobile Drawer Navigation Items
    const mobileNav = document.getElementById('mobile-navigation-items');
    if (mobileNav) {
      mobileNav.innerHTML = menu.map(m => {
        const isPathActive = m.path.includes('?')
          ? (currentFullHash === m.path || currentFullHash.startsWith(m.path + '&'))
          : (m.path === '#/admin/governance'
            ? (currentFullHash === m.path || currentFullHash === m.path + '/' || currentFullHash === m.path + '?tab=users')
            : (currentFullHash === m.path || currentFullHash === m.path + '/' || (!currentFullHash.includes('?') && currentFullHash.startsWith(m.path))));
        const badgeNum = Number(m.badge) || 0;
        return `
          <a
            href="${m.path}"
            class="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              isPathActive
                ? 'bg-[#222120] text-[#FAF9F5] dark:bg-[#EDEDEB] dark:text-[#191919] font-bold'
                : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] hover:text-[#222120] dark:hover:text-[#EDEDEB]'
            }"
          >
            <div class="flex items-center gap-2.5">
              <span class="material-symbols-outlined text-[17px]">${m.icon}</span>
              <span class="inline-flex items-center">
                <span>${m.label}</span>
                ${badgeNum > 0 ? `
                  <sup class="ml-0.5 -top-1.5 text-[11px] font-black text-amber-600 dark:text-amber-400 select-none leading-none tracking-tight">${badgeNum > 99 ? '99+' : badgeNum}</sup>
                ` : ''}
              </span>
            </div>
            ${badgeNum > 0 ? `
              <span class="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">${badgeNum} chờ</span>
            ` : ''}
          </a>
        `;
      }).join('');
    }

    // 3. Fallback compatibility for sidebar container
    const navBox = document.getElementById('sidebar-navigation-items');
    if (navBox && mobileNav) {
      navBox.innerHTML = mobileNav.innerHTML;
    }
  }

  updateTopbarBreadcrumb(path) {
    const titleEl = document.getElementById('topbar-page-title');
    if (titleEl) {
      titleEl.textContent = '';
      titleEl.style.display = 'none';
    }
  }

  // =========================================================================
  // Topbar Profile, Avatar & Multi-Role Switcher Dropdown
  // =========================================================================
  updateUserUI() {
    const user = this.currentUser;
    const nameEl = document.getElementById('topbar-user-name');
    const avatarInitials = document.getElementById('topbar-avatar-initials');
    const roleBadge = document.getElementById('topbar-role-badge');
    const roleDropdown = document.getElementById('topbar-role-dropdown');

    if (!user) return;

    const displayName = user.display_name || user.email;
    if (nameEl) nameEl.textContent = displayName;

    const initials = displayName.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
    if (avatarInitials) avatarInitials.textContent = initials || 'US';

    const roleName = this.currentRole === 'ADMIN'
      ? (user.admin_sub_role_label ? user.admin_sub_role_label.toUpperCase() : 'QUẢN TRỊ VIÊN')
      : this.currentRole === 'INSTRUCTOR' ? 'GIẢNG VIÊN' : 'HỌC VIÊN';
    if (roleBadge) {
      roleBadge.textContent = roleName;
      roleBadge.className = `px-1.5 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider border leading-none ${
        this.currentRole === 'ADMIN'
          ? 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
          : this.currentRole === 'INSTRUCTOR'
          ? 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300'
          : 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
      }`;
    }

    if (avatarInitials) {
      avatarInitials.textContent = initials || 'US';
      avatarInitials.className = `w-7 h-7 rounded-full font-bold flex items-center justify-center text-[11px] shadow-xs transition-all border ${
        this.currentRole === 'ADMIN'
          ? 'bg-rose-900 text-rose-100 border-rose-400/50'
          : this.currentRole === 'INSTRUCTOR'
          ? 'bg-blue-900 text-blue-100 border-blue-400/50'
          : 'bg-[#222120] dark:bg-[#2A2928] text-[#FAF9F5] dark:text-[#EDEDEB] border-[#E8E6DF] dark:border-[#3E3D3A]'
      }`;
    }

    // Build Role Switcher buttons
    const userRoles = user.role_codes || [user.primary_role || 'STUDENT'];
    const canSwitchToInstructor = userRoles.includes('INSTRUCTOR') || userRoles.includes('ADMIN');
    const canSwitchToAdmin = userRoles.includes('ADMIN');

    if (roleDropdown) {
      roleDropdown.innerHTML = `
        <div class="px-3 py-2 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
          <div class="font-bold text-xs text-[#222120] dark:text-[#EDEDEB] truncate">${displayName}</div>
          <div class="text-[11px] text-[#8F8E8A] truncate">${user.email}</div>
        </div>

        ${(canSwitchToInstructor || canSwitchToAdmin) ? `
          <div class="p-1.5 border-b border-[#E8E6DF] dark:border-[#2E2D2B] space-y-0.5">
            <div class="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-[#8F8E8A]">Chuyển góc nhìn</div>
            
            <button type="button" class="switch-role-action w-full flex items-center justify-between px-2 py-1.5 rounded-md text-xs font-semibold ${this.currentRole === 'STUDENT' ? 'bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB]' : 'hover:bg-[#FAF9F5] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99]'}" data-target-role="STUDENT">
              <span class="flex items-center gap-2"><span class="material-symbols-outlined text-[15px]">school</span> Học viên</span>
              ${this.currentRole === 'STUDENT' ? '<span class="material-symbols-outlined text-[14px]">check</span>' : ''}
            </button>

            ${canSwitchToInstructor ? `
              <button type="button" class="switch-role-action w-full flex items-center justify-between px-2 py-1.5 rounded-md text-xs font-semibold ${this.currentRole === 'INSTRUCTOR' ? 'bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB]' : 'hover:bg-[#FAF9F5] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99]'}" data-target-role="INSTRUCTOR">
                <span class="flex items-center gap-2"><span class="material-symbols-outlined text-[15px]">person_apron</span> Giảng viên</span>
                ${this.currentRole === 'INSTRUCTOR' ? '<span class="material-symbols-outlined text-[14px]">check</span>' : ''}
              </button>
            ` : ''}

            ${canSwitchToAdmin ? `
              <button type="button" class="switch-role-action w-full flex items-center justify-between px-2 py-1.5 rounded-md text-xs font-semibold ${this.currentRole === 'ADMIN' ? 'bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB]' : 'hover:bg-[#FAF9F5] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99]'}" data-target-role="ADMIN">
                <span class="flex items-center gap-2"><span class="material-symbols-outlined text-[15px]">admin_panel_settings</span> Quản trị viên</span>
                ${this.currentRole === 'ADMIN' ? '<span class="material-symbols-outlined text-[14px]">check</span>' : ''}
              </button>
            ` : ''}
          </div>
        ` : ''}
        ${!canSwitchToInstructor ? `
          <div class="p-1.5 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
            <a
              href="#/student/become-instructor"
              class="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs font-semibold text-primary dark:text-blue-400 hover:bg-[#FAF9F5] dark:hover:bg-[#262524] transition-colors"
              onclick="document.getElementById('topbar-role-dropdown')?.classList.add('hidden')"
            >
              <span class="material-symbols-outlined text-[16px]">badge</span>
              <span>Đăng ký làm Giảng viên</span>
            </a>
          </div>
        ` : ''}

        <div class="p-1.5 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
          <a
            href="#/student/settings"
            class="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#FAF9F5] dark:hover:bg-[#262524] hover:text-[#222120] dark:hover:text-[#EDEDEB] transition-colors"
            onclick="document.getElementById('topbar-role-dropdown')?.classList.add('hidden')"
          >
            <span class="material-symbols-outlined text-[16px]">settings</span>
            <span>Cài đặt tài khoản</span>
          </a>
        </div>

        <div class="p-1">
          <button type="button" id="topbar-logout-btn" class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors">
            <span class="material-symbols-outlined text-[15px]">logout</span>
            <span>Đăng xuất tài khoản</span>
          </button>
        </div>
      `;

      // Handle role switch buttons
      roleDropdown.querySelectorAll('.switch-role-action').forEach(btn => {
        btn.onclick = async () => {
          const target = btn.dataset.targetRole;
          if (target === this.currentRole) return;
          try {
            await ApiClient.switchRole(target);
            this.currentRole = target;
            if (target === 'ADMIN') {
              this.fetchAdminPendingCounts();
            }
            UI.showToast(`Đã chuyển sang góc nhìn ${target === 'ADMIN' ? 'Quản trị viên' : target === 'INSTRUCTOR' ? 'Giảng viên' : 'Học viên'}!`, 'info');
            this.updateUserUI();
            this.redirectToRoleHome();
            roleDropdown.classList.add('hidden');
          } catch (err) {
            UI.showToast(err.message || 'Không thể chuyển đổi vai trò.', 'error');
          }
        };
      });

      // Handle Logout
      const logoutBtn = document.getElementById('topbar-logout-btn');
      if (logoutBtn) {
        logoutBtn.onclick = async () => {
          roleDropdown.classList.add('hidden');
          this.closeNotificationsDropdown();
          if (this.currentUser && this.currentUser.id) {
            try { sessionStorage.removeItem(`pwd301_notifs_${this.currentUser.id}`); } catch {}
          }
          this.notificationsCache = null;
          this.currentUser = null;
          this.currentRole = null;
          this.toggleShell(false);
          await ApiClient.logout();
          this.renderAuth();
          UI.showToast('Đã đăng xuất tài khoản an toàn.', 'info');
        };
      }
    }
  }

  initThemeToggle() {
    const btn = document.getElementById('topbar-theme-toggle');
    const icon = document.getElementById('theme-toggle-icon');

    const updateThemeIcon = () => {
      const isDark = document.documentElement.classList.contains('dark');
      if (icon) icon.textContent = isDark ? 'light_mode' : 'dark_mode';
    };

    if (btn) {
      btn.onclick = () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeIcon();
      };
    }

    updateThemeIcon();

    // Setup Avatar Dropdown Toggle
    const avatarBtn = document.getElementById('topbar-avatar-btn');
    const dropdown = document.getElementById('topbar-role-dropdown');
    const chevron = document.getElementById('topbar-avatar-chevron');
    if (avatarBtn && dropdown) {
      avatarBtn.onclick = (e) => {
        e.stopPropagation();
        this.closeNotificationsDropdown();
        const isHidden = dropdown.classList.toggle('hidden');
        if (chevron) {
          chevron.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
        }
      };
      document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !avatarBtn.contains(e.target)) {
          dropdown.classList.add('hidden');
          if (chevron) chevron.style.transform = 'rotate(0deg)';
        }
      });
    }
  }

  // =========================================================================
  // 4. Instant Notification Dropdown & Cache Management (0ms SWR)
  // =========================================================================

  loadCachedNotifications() {
    if (!this.currentUser || !this.currentUser.id) return;
    try {
      const raw = sessionStorage.getItem(`pwd301_notifs_${this.currentUser.id}`);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.items)) {
          this.notificationsCache = parsed;
          this.updateBadgeFromCache();
        }
      }
    } catch {
      // Ignore sessionStorage errors
    }
  }

  saveCachedNotifications() {
    if (!this.currentUser || !this.currentUser.id || !this.notificationsCache) return;
    try {
      sessionStorage.setItem(`pwd301_notifs_${this.currentUser.id}`, JSON.stringify(this.notificationsCache));
    } catch {
      // Ignore quota errors
    }
  }

  updateBadgeFromCache() {
    const badge = document.getElementById('topbar-notifications-badge');
    if (!badge || !this.notificationsCache) return;
    const count = this.notificationsCache.unread_count ?? (this.notificationsCache.items || []).filter(i => !i.is_read && !i.read).length;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }

  initNotifications() {
    this.activeNotificationTab = 'ALL';
    const bellBtn = document.getElementById('topbar-notifications-btn');
    const dropdown = document.getElementById('topbar-notifications-dropdown');

    if (bellBtn && dropdown) {
      bellBtn.onclick = (e) => {
        e.stopPropagation();
        this.toggleNotificationsDropdown();
      };

      // Click outside to dismiss dropdown
      document.addEventListener('click', (e) => {
        const wrapper = document.getElementById('topbar-notifications-wrapper');
        if (wrapper && !wrapper.contains(e.target)) {
          this.closeNotificationsDropdown();
        }
      });

      // Escape key to dismiss
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !dropdown.classList.contains('hidden')) {
          this.closeNotificationsDropdown();
        }
      });
    }

    // Initial load from cache or background fetch
    this.loadCachedNotifications();
    this.refreshNotificationBadge(true);
  }

  toggleNotificationsDropdown() {
    const dropdown = document.getElementById('topbar-notifications-dropdown');
    if (!dropdown) return;
    if (dropdown.classList.contains('hidden')) {
      this.openNotificationsDropdown();
    } else {
      this.closeNotificationsDropdown();
    }
  }

  openNotificationsDropdown() {
    const dropdown = document.getElementById('topbar-notifications-dropdown');
    const bellBtn = document.getElementById('topbar-notifications-btn');
    const roleDropdown = document.getElementById('topbar-role-dropdown');

    if (roleDropdown) roleDropdown.classList.add('hidden');

    if (dropdown) {
      dropdown.classList.remove('hidden');
      if (bellBtn) bellBtn.setAttribute('aria-expanded', 'true');

      // Instant first paint from cache (0ms delay)
      if (this.notificationsCache && Array.isArray(this.notificationsCache.items)) {
        this.renderNotificationsDropdownContent();
      } else {
        this.renderNotificationsSkeleton();
      }

      // SWR: Silent background revalidation
      this.fetchNotifications(false);
    }
  }

  closeNotificationsDropdown() {
    const dropdown = document.getElementById('topbar-notifications-dropdown');
    const bellBtn = document.getElementById('topbar-notifications-btn');
    if (dropdown && !dropdown.classList.contains('hidden')) {
      dropdown.classList.add('hidden');
      if (bellBtn) bellBtn.setAttribute('aria-expanded', 'false');
    }
  }

  formatRelativeTime(dateStr) {
    if (!dateStr) return '';
    try {
      let s = String(dateStr).trim();
      if (s.includes('T') && !s.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(s)) {
        s += 'Z';
      }
      const date = new Date(s);
      const now = new Date();
      const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
      if (isNaN(diffSec) || diffSec < 0) return 'Vừa xong';
      if (diffSec < 60) return 'Vừa xong';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)} phút trước`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} giờ trước`;
      if (diffSec < 86400 * 2) return 'Hôm qua';
      if (diffSec < 86400 * 7) return `${Math.floor(diffSec / 86400)} ngày trước`;
      return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return '';
    }
  }

  getCategoryMeta(cat) {
    const c = (cat || 'SYSTEM').toUpperCase();
    switch (c) {
      case 'SECURITY':
        return {
          icon: 'security',
          iconColor: 'bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40',
          label: 'Bảo mật',
          badgeColor: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'
        };
      case 'ASSESSMENT':
        return {
          icon: 'quiz',
          iconColor: 'bg-purple-50 text-purple-600 dark:bg-purple-950/50 dark:text-purple-400 border border-purple-200 dark:border-purple-800/40',
          label: 'Khảo thí',
          badgeColor: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300'
        };
      case 'COURSE':
        return {
          icon: 'menu_book',
          iconColor: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40',
          label: 'Khóa học',
          badgeColor: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
        };
      case 'GRADE':
        return {
          icon: 'military_tech',
          iconColor: 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40',
          label: 'Điểm số',
          badgeColor: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
        };
      default:
        return {
          icon: 'campaign',
          iconColor: 'bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40',
          label: 'Hệ thống',
          badgeColor: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
        };
    }
  }

  renderNotificationsSkeleton() {
    const dropdown = document.getElementById('topbar-notifications-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = `
      <div class="p-4 border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between bg-[#FAF9F5] dark:bg-[#242423]">
        <div class="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
        <div class="h-3 w-16 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
      </div>
      <div class="p-3 space-y-3">
        ${[1, 2, 3].map(() => `
          <div class="flex items-start gap-3 p-2 rounded-xl bg-slate-50 dark:bg-[#262524] animate-pulse">
            <div class="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-700 shrink-0"></div>
            <div class="flex-1 space-y-2 py-0.5">
              <div class="h-3 w-3/4 bg-slate-200 dark:bg-slate-700 rounded"></div>
              <div class="h-2.5 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderNotificationsDropdownContent() {
    const dropdown = document.getElementById('topbar-notifications-dropdown');
    if (!dropdown || !this.notificationsCache) return;

    const items = this.notificationsCache.items || [];
    const unreadCount = items.filter(i => !i.is_read && !i.read).length;
    const activeTab = this.activeNotificationTab || 'ALL';

    // Filter items based on active tab
    const filtered = items.filter(item => {
      const isRead = item.is_read ?? item.read ?? false;
      const cat = (item.category || '').toUpperCase();
      if (activeTab === 'UNREAD') return !isRead;
      if (activeTab === 'ASSESSMENT') return cat === 'ASSESSMENT' || cat === 'GRADE';
      if (activeTab === 'COURSE') return cat === 'COURSE';
      if (activeTab === 'SYSTEM') return cat === 'SYSTEM' || cat === 'SECURITY';
      return true;
    });

    const roleName = this.currentRole === 'ADMIN'
      ? 'Quản trị viên'
      : (this.currentRole === 'INSTRUCTOR' ? 'Giảng viên' : 'Học viên');

    dropdown.innerHTML = `
      <!-- Header -->
      <div class="p-3 sm:px-4 sm:py-3 border-b border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#242423] flex items-center justify-between select-none">
        <div class="flex items-center gap-2">
          <span class="font-bold text-sm text-[#222120] dark:text-[#EDEDEB]">Thông báo</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${unreadCount > 0 ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300' : 'bg-[#E8E6DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99]'}">
            ${unreadCount > 0 ? `${unreadCount} mới` : '0 mới'}
          </span>
        </div>
        ${unreadCount > 0 ? `
          <button
            type="button"
            id="notif-dropdown-mark-all"
            class="text-[11px] font-semibold text-primary hover:text-primary-hover hover:underline inline-flex items-center gap-1 transition-colors"
            title="Đánh dấu tất cả thông báo là đã đọc"
          >
            <span class="material-symbols-outlined text-[15px]">done_all</span>
            <span>Đã đọc tất cả</span>
          </button>
        ` : ''}
      </div>

      <!-- Filter Tabs -->
      <div class="flex items-center gap-1 px-3 py-2 border-b border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] overflow-x-auto no-scrollbar text-[11px]">
        <button type="button" class="notif-filter-tab px-2.5 py-1 rounded-lg font-medium transition-all ${activeTab === 'ALL' ? 'bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] font-bold shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]'}" data-tab="ALL">Tất cả</button>
        <button type="button" class="notif-filter-tab px-2.5 py-1 rounded-lg font-medium transition-all ${activeTab === 'UNREAD' ? 'bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] font-bold shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]'}" data-tab="UNREAD">Chưa đọc (${unreadCount})</button>
        <button type="button" class="notif-filter-tab px-2.5 py-1 rounded-lg font-medium transition-all ${activeTab === 'ASSESSMENT' ? 'bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] font-bold shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]'}" data-tab="ASSESSMENT">Khảo thí</button>
        <button type="button" class="notif-filter-tab px-2.5 py-1 rounded-lg font-medium transition-all ${activeTab === 'COURSE' ? 'bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] font-bold shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]'}" data-tab="COURSE">Khóa học</button>
        <button type="button" class="notif-filter-tab px-2.5 py-1 rounded-lg font-medium transition-all ${activeTab === 'SYSTEM' ? 'bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] font-bold shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]'}" data-tab="SYSTEM">Hệ thống</button>
      </div>

      <!-- Notifications List (Scrollable) -->
      <div class="max-h-[360px] sm:max-h-[400px] overflow-y-auto divide-y divide-[#F4F1EA] dark:divide-[#2E2D2B]" id="notif-dropdown-list">
        ${filtered.length === 0 ? `
          <div class="py-12 px-4 text-center text-[#8F8E8A]">
            <span class="material-symbols-outlined text-3xl text-[#D3D0C8] dark:text-[#3E3D3A] mb-1.5 inline-block">notifications_off</span>
            <p class="font-semibold text-xs text-[#5C5B57] dark:text-[#9E9D99]">Không có thông báo nào</p>
            <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-0.5">Bạn đã xem hết các thông báo trong mục này.</p>
          </div>
        ` : filtered.map(item => {
          const isRead = item.is_read ?? item.read ?? false;
          const meta = this.getCategoryMeta(item.category);
          const relTime = this.formatRelativeTime(item.created_at);
          const targetUrl = item.action_url || item.target_url || '';

          return `
            <div
              class="notif-dropdown-item p-3 sm:p-3.5 hover:bg-[#FAF9F5] dark:hover:bg-[#262524] transition-colors cursor-pointer flex items-start gap-3 relative ${isRead ? 'opacity-70 bg-[#FFFFFF] dark:bg-[#202020]' : 'bg-primary/[0.02] dark:bg-primary/[0.04]'}"
              data-id="${item.id}"
              data-link="${targetUrl ? (window.UI ? UI.escapeHtml(targetUrl) : targetUrl) : ''}"
            >
              <!-- Category Icon -->
              <div class="w-8 h-8 rounded-xl ${meta.iconColor} flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                <span class="material-symbols-outlined text-[17px]">${meta.icon}</span>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0 space-y-1">
                <div class="flex items-center justify-between gap-1.5">
                  <span class="text-[10px] font-bold uppercase tracking-wider ${meta.badgeColor} px-1.5 py-0.2 rounded">
                    ${meta.label}
                  </span>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <span class="text-[10.5px] text-[#8F8E8A] dark:text-[#6D6C68]">${relTime}</span>
                    ${!isRead ? '<span class="w-2 h-2 rounded-full bg-rose-600 ring-2 ring-[#FAF9F5] dark:ring-[#202020] shrink-0" title="Chưa đọc"></span>' : ''}
                  </div>
                </div>

                <div class="text-xs ${isRead ? 'font-medium text-[#222120] dark:text-[#EDEDEB]' : 'font-bold text-[#222120] dark:text-[#EDEDEB]'} leading-snug">
                  ${window.UI ? UI.escapeHtml(item.title || '') : (item.title || '')}
                </div>

                <p class="text-[11.5px] text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed line-clamp-2">
                  ${window.UI ? UI.escapeHtml(item.body || item.message || '') : (item.body || item.message || '')}
                </p>
              </div>
            </div>
          `;
        }).join('')}
      </div>

      <!-- Footer with Role Context -->
      <div class="p-2.5 px-3.5 border-t border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#242423] flex items-center justify-between text-[11px] text-[#8F8E8A] dark:text-[#9E9D99] select-none">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">shield_person</span>
          <span>Góc nhìn: <strong class="text-[#222120] dark:text-[#EDEDEB] font-bold">${roleName}</strong></span>
        </span>
        <button type="button" class="text-primary hover:underline font-semibold" onclick="window.app?.refreshNotificationBadge?.(true)">
          Làm mới
        </button>
      </div>
    `;

    // Hook up tab buttons
    dropdown.querySelectorAll('.notif-filter-tab').forEach(tabBtn => {
      tabBtn.onclick = (e) => {
        e.stopPropagation();
        this.activeNotificationTab = tabBtn.dataset.tab;
        this.renderNotificationsDropdownContent();
      };
    });

    // Hook up mark all read
    const markAllBtn = document.getElementById('notif-dropdown-mark-all');
    if (markAllBtn) {
      markAllBtn.onclick = async (e) => {
        e.stopPropagation();
        await this.handleMarkAllRead();
      };
    }

    // Hook up item clicks
    dropdown.querySelectorAll('.notif-dropdown-item').forEach(itemEl => {
      itemEl.onclick = async (e) => {
        e.stopPropagation();
        const id = itemEl.dataset.id;
        const link = itemEl.dataset.link;
        await this.handleNotificationItemClick(id, link);
      };
    });
  }

  async handleNotificationItemClick(notifId, link) {
    if (!notifId || !this.notificationsCache) return;

    // Optimistic local update
    const item = (this.notificationsCache.items || []).find(i => i.id === notifId);
    if (item && !item.is_read && !item.read) {
      item.is_read = true;
      item.read = true;
      if (typeof this.notificationsCache.unread_count === 'number' && this.notificationsCache.unread_count > 0) {
        this.notificationsCache.unread_count--;
      }
      this.saveCachedNotifications();
      this.updateBadgeFromCache();
      this.renderNotificationsDropdownContent();

      // Silent background API sync
      try {
        await ApiClient.markNotificationRead(notifId);
      } catch (err) {
        console.warn('Silent markNotificationRead failed:', err);
      }
    }

    // Open detailed reading modal so user can fully read notification
    if (item) {
      this.openNotificationModal(item, link);
    } else if (link) {
      this.closeNotificationsDropdown();
      if (window.location.hash === link) {
        this.handleRoute();
      } else {
        window.location.hash = link;
      }
    }
  }

  openNotificationModal(item, link) {
    this.closeNotificationsDropdown();
    if (!item) return;

    const meta = this.getCategoryMeta(item.category);
    const relTime = this.formatRelativeTime(item.created_at);
    const exactTime = window.UI ? UI.formatDateTime(item.created_at) : (item.created_at || '');
    const targetLink = link || item.action_url || item.target_url || '';

    const bodyHtml = `
      <div class="space-y-4 text-xs">
        <div class="flex items-center justify-between pb-3 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-bold uppercase tracking-wider ${meta.badgeColor} px-2 py-0.5 rounded">
              ${meta.label}
            </span>
            <span class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] font-mono">${exactTime} (${relTime})</span>
          </div>
          <span class="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">done_all</span> Đã đọc
          </span>
        </div>

        <div class="space-y-2">
          <h4 class="text-sm sm:text-base font-bold text-[#222120] dark:text-[#EDEDEB] leading-snug">
            ${window.UI ? UI.escapeHtml(item.title || '') : (item.title || '')}
          </h4>
          <div class="p-4 rounded-xl bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB] leading-relaxed text-xs sm:text-sm whitespace-pre-line select-text">
            ${window.UI ? UI.escapeHtml(item.body || item.message || '') : (item.body || item.message || '')}
          </div>
        </div>
      </div>
    `;

    const footerHtml = `
      <div class="flex items-center justify-between w-full">
        <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524]" onclick="UI.closeModal()">
          Đóng
        </button>
        ${targetLink ? `
          <button type="button" id="notif-modal-navigate-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold flex items-center gap-2 shadow-sm transition-all">
            <span>${(targetLink.includes('courses') || targetLink.includes('applications') || targetLink.includes('review') || targetLink.includes('governance')) ? 'Chuyển đến duyệt ngay' : 'Chuyển đến trang liên quan'}</span>
            <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        ` : ''}
      </div>
    `;

    if (window.UI && typeof UI.openModal === 'function') {
      UI.openModal({
        title: 'Chi tiết Thông báo Học vụ',
        bodyHtml,
        footerHtml,
        size: 'md'
      });

      const navBtn = document.getElementById('notif-modal-navigate-btn');
      if (navBtn) {
        navBtn.onclick = () => {
          UI.closeModal();
          if (window.location.hash === targetLink) {
            this.handleRoute();
          } else {
            window.location.hash = targetLink;
          }
        };
      }
    }
  }

  async handleMarkAllRead() {
    if (!this.notificationsCache) return;

    // Optimistic local update
    (this.notificationsCache.items || []).forEach(i => {
      i.is_read = true;
      i.read = true;
    });
    this.notificationsCache.unread_count = 0;
    this.saveCachedNotifications();
    this.updateBadgeFromCache();
    this.renderNotificationsDropdownContent();

    if (typeof UI !== 'undefined' && typeof UI.showToast === 'function') {
      UI.showToast('Đã đánh dấu tất cả thông báo là đã đọc.', 'success');
    }

    // Silent background API sync
    try {
      await ApiClient.markAllNotificationsRead();
    } catch (err) {
      console.warn('markAllNotificationsRead background sync error:', err);
    }
  }

  async fetchNotifications(forceRender = false) {
    if (!this.currentUser) return;
    try {
      const data = await ApiClient.getNotifications();
      if (data && Array.isArray(data.items)) {
        const items = data.items.map(i => ({
          ...i,
          is_read: i.is_read ?? i.read ?? false,
          read: i.is_read ?? i.read ?? false,
        }));
        const unreadCount = data.unread_count ?? items.filter(i => !i.is_read).length;

        this.notificationsCache = {
          items: items,
          unread_count: unreadCount,
          last_fetched: Date.now(),
          user_id: this.currentUser.id,
        };
        this.saveCachedNotifications();
        this.updateBadgeFromCache();

        // If dropdown is currently open or forceRender requested, re-render
        const dropdown = document.getElementById('topbar-notifications-dropdown');
        if (dropdown && !dropdown.classList.contains('hidden') || forceRender) {
          this.renderNotificationsDropdownContent();
        }
      }
    } catch (e) {
      console.warn('fetchNotifications background error:', e);
    }
  }

  async refreshNotificationBadge(forceFetch = false) {
    if (!this.currentUser) return;
    if (this.notificationsCache && !forceFetch) {
      this.updateBadgeFromCache();
      return;
    }
    await this.fetchNotifications(false);
  }
}

window.AppRouter = AppRouter;
