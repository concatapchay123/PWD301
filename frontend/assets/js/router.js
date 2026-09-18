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
      this.currentUser = await ApiClient.getCurrentUser();
      if (this.currentUser) {
        this.currentRole = this.currentUser.primary_role || (this.currentUser.role_codes && this.currentUser.role_codes[0]) || 'STUDENT';
      } else {
        this.currentRole = 'STUDENT';
      }
    } catch {
      this.currentUser = null;
    }
    this.updateUserUI();
    this.refreshNotificationBadge();
    return this.currentUser;
  }

  parseHash() {
    const raw = window.location.hash || '';
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

  async handleRoute() {
    if (typeof UI !== 'undefined' && typeof UI.startMicroLoading === 'function') {
      UI.startMicroLoading();
    }

    try {
      const { path, query } = this.parseHash();

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
          this.updateUserUI();
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
          this.updateUserUI();
        }
      }

      // Show Shell (Topbar + Dynamic Navigation) for authenticated views
      this.toggleShell(true);
      this.renderDynamicSidebar();
      this.updateTopbarBreadcrumb(path);

      // Clean up lingering modal overlays from previous views while preserving permanent shells
      if (typeof UI !== 'undefined') {
        if (typeof UI.closeModal === 'function') UI.closeModal();
        if (typeof UI.closeDrawer === 'function') UI.closeDrawer();
      }
      document.querySelectorAll('body > .fixed.inset-0:not(#app-drawer-backdrop):not(#modal-container)').forEach(m => m.remove());

      // Fullscreen Focus Mode toggle for Exams & Dedicated Studios
      const isFocusRoute = path.includes('/attempt') || path.includes('/waiting-room') || path.includes('/lessons/new') || (path.includes('/lessons/') && path.includes('/edit')) || path.includes('/instructor/exams');
      if (isFocusRoute) {
        document.body.classList.add('fullscreen-focus-mode');
      } else {
        document.body.classList.remove('fullscreen-focus-mode');
      }

      // Anti-Cheat & Exam Integrity: Conceal Floating AI Tutor during active exam attempts & waiting room
      const isExamActive = path.includes('/attempt') || path.includes('/waiting-room');
      const floatingAi = document.getElementById('floating-ai-container');
      if (floatingAi) {
        if (isExamActive) {
          floatingAi.classList.add('hidden');
          if (window.FloatingAITutor && typeof window.FloatingAITutor.close === 'function') {
            window.FloatingAITutor.close();
          }
        } else {
          floatingAi.classList.remove('hidden');
        }
      }

      // Route Dispatcher
      await this.dispatchRoute(path, query);
    } finally {
      if (typeof UI !== 'undefined' && typeof UI.stopMicroLoading === 'function') {
        UI.stopMicroLoading();
      }
    }
  }

  redirectToRoleHome() {
    if (this.currentRole === 'ADMIN') {
      window.location.hash = '#/admin/governance';
    } else if (this.currentRole === 'INSTRUCTOR') {
      window.location.hash = '#/instructor/dashboard';
    } else {
      window.location.hash = '#/student/dashboard';
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

  async dispatchRoute(path, query) {
    if (!this.viewport) return;

    // --- Student Routes ---
    if (path === '#/student/dashboard') {
      await StudentView.renderDashboard(this.viewport);
    } else if (path === '#/student/catalog') {
      await StudentView.renderCatalog(this.viewport);
    } else if (path === '#/student/courses') {
      await StudentView.renderMyLearning(this.viewport);
    } else if (path === '#/student/courses/detail' || (path.startsWith('#/student/courses/') && !path.includes('/lessons/'))) {
      const courseId = query.id || path.replace('#/student/courses/', '');
      await StudentView.renderCourseDetail(this.viewport, courseId, query.tab || 'syllabus');
    } else if (path === '#/student/lessons/reader' || (path.startsWith('#/student/courses/') && path.includes('/lessons/'))) {
      let cId = query.course_id;
      let lId = query.lesson_id;
      const m = path.match(/#\/student\/courses\/([^/]+)\/lessons\/([^/]+)/);
      if (m) {
        cId = m[1];
        lId = m[2];
      }
      await StudentView.renderLessonReader(this.viewport, cId, lId);
    } else if (path === '#/student/assessments') {
      await StudentView.renderAssessmentsList(this.viewport);
    } else if (path === '#/student/assessments/waiting-room' || path.endsWith('/waiting-room')) {
      const aId = query.id || path.replace('#/student/assessments/', '').replace('/waiting-room', '');
      await StudentView.renderWaitingRoom(this.viewport, aId);
    } else if (path === '#/student/assessments/attempt' || (path.startsWith('#/student/assessments/attempts/') && !path.endsWith('/results'))) {
      const attId = query.id || path.replace('#/student/assessments/attempts/', '');
      await StudentView.renderAttemptConsole(this.viewport, attId);
    } else if (path === '#/student/assessments/results' || path.endsWith('/results')) {
      const attId = query.id || path.replace('#/student/assessments/attempts/', '').replace('/results', '');
      await StudentView.renderAttemptResults(this.viewport, attId);
    } else if (path === '#/student/ai-assistant') {
      window.location.hash = '#/student/dashboard';
    } else if (path === '#/student/become-instructor') {
      await StudentView.renderBecomeInstructor(this.viewport);
    }

    // --- Instructor Routes ---
    else if (path === '#/instructor/dashboard') {
      await InstructorView.renderDashboard(this.viewport);
    } else if (path === '#/instructor/courses') {
      await InstructorView.renderCourses(this.viewport);
    } else if (path === '#/instructor/courses/manage') {
      await InstructorView.renderCourseManage(this.viewport, query.id, query.tab || 'curriculum');
    } else if (path.startsWith('#/instructor/courses/') && path.endsWith('/manage')) {
      const parts = path.split('/');
      const courseId = parts[3];
      await InstructorView.renderCourseManage(this.viewport, courseId, query.tab || 'curriculum');
    } else if (path.startsWith('#/instructor/courses/') && path.includes('/lessons/new')) {
      const parts = path.split('/');
      const courseId = parts[3];
      await InstructorView.renderLessonAuthoringStudio(this.viewport, courseId, null);
    } else if (path.startsWith('#/instructor/courses/') && path.includes('/lessons/') && path.endsWith('/edit')) {
      const parts = path.split('/');
      const courseId = parts[3];
      const lessonId = parts[5];
      await InstructorView.renderLessonAuthoringStudio(this.viewport, courseId, lessonId);
    } else if (path === '#/instructor/questions/studio' || (path === '#/instructor/questions' && query.studio)) {
      await InstructorView.renderExtendedQuestionStudio(this.viewport, query.course);
    } else if (path === '#/instructor/questions') {
      await InstructorView.renderQuestions(this.viewport, query.course);
    } else if (path === '#/instructor/exams') {
      InstructorView.renderExams(this.viewport);
    }

    // --- Admin Routes ---
    else if (path === '#/admin/governance') {
      await AdminView.renderGovernance(this.viewport, query.tab || 'users');
    } else if (path === '#/admin/operations') {
      await AdminView.renderOperations(this.viewport);
    }

    // Fallback
    else {
      this.redirectToRoleHome();
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
      menu = [
        { label: 'Bàn điều hành', path: '#/admin/governance', icon: 'admin_panel_settings' },
        { label: 'Người dùng', path: '#/admin/governance?tab=users', icon: 'manage_accounts' },
        { label: 'Duyệt khóa học', path: '#/admin/governance?tab=courses', icon: 'rule' },
        { label: 'Hồ sơ giảng viên', path: '#/admin/governance?tab=applications', icon: 'badge' },
        { label: 'Vận hành hệ thống', path: '#/admin/operations', icon: 'monitoring' },
      ];
    } else if (role === 'INSTRUCTOR') {
      menu = [
        { label: 'Bàn làm việc', path: '#/instructor/dashboard', icon: 'dashboard' },
        { label: 'Khóa học', path: '#/instructor/courses', icon: 'auto_stories' },
        { label: 'Ngân hàng câu hỏi', path: '#/instructor/questions', icon: 'database' },
        { label: 'Soạn đề thi', path: '#/instructor/exams', icon: 'assignment_add' },
      ];
    } else {
      menu = [
        { label: 'Bàn làm việc', path: '#/student/dashboard', icon: 'dashboard' },
        { label: 'Khám phá Khóa học', path: '#/student/catalog', icon: 'explore' },
        { label: 'Khóa học của tôi', path: '#/student/courses', icon: 'school' },
        { label: 'Bài kiểm tra', path: '#/student/assessments', icon: 'quiz' },
        { label: 'Đăng ký Giảng viên', path: '#/student/become-instructor', icon: 'badge' },
      ];
    }

    // 1. Populate Desktop Topbar Navigation Items (Warm Editorial Pill Tabs)
    const topNav = document.getElementById('topbar-navigation-items');
    if (topNav) {
      topNav.innerHTML = menu.map(m => {
        const isPathActive = path === m.path || (m.path.includes('?') && window.location.hash.startsWith(m.path));
        return `
          <a
            href="${m.path}"
            class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              isPathActive
                ? 'bg-[#FFFFFF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] font-bold shadow-2xs'
                : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#FAF9F5] dark:hover:bg-[#262524] hover:text-[#222120] dark:hover:text-[#EDEDEB]'
            }"
          >
            <span class="material-symbols-outlined text-[16px]">${m.icon}</span>
            <span>${m.label}</span>
          </a>
        `;
      }).join('');
    }

    // 2. Populate Mobile Drawer Navigation Items
    const mobileNav = document.getElementById('mobile-navigation-items');
    if (mobileNav) {
      mobileNav.innerHTML = menu.map(m => {
        const isPathActive = path === m.path || (m.path.includes('?') && window.location.hash.startsWith(m.path));
        return `
          <a
            href="${m.path}"
            class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              isPathActive
                ? 'bg-[#222120] text-[#FAF9F5] dark:bg-[#EDEDEB] dark:text-[#191919] font-bold'
                : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] hover:text-[#222120] dark:hover:text-[#EDEDEB]'
            }"
          >
            <span class="material-symbols-outlined text-[17px]">${m.icon}</span>
            <span>${m.label}</span>
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
    if (!titleEl) return;

    let title = 'Cổng Học tập Trực tuyến';
    if (path.includes('dashboard')) title = 'Tổng quan Bàn làm việc';
    else if (path.includes('catalog')) title = 'Danh mục Khóa học';
    else if (path.includes('courses')) title = 'Khóa học & Giáo trình';
    else if (path.includes('reader')) title = 'Phòng đọc Bài giảng Học thuật';
    else if (path.includes('waiting-room')) title = 'Phòng chờ Khảo thí';
    else if (path.includes('attempt')) title = 'Bàn làm bài Khảo thí';
    else if (path.includes('results')) title = 'Kết quả & Đối chiếu Bài thi';
    else if (path.includes('ai-assistant')) title = 'Trợ lý AI Học thuật Gemini';
    else if (path.includes('become-instructor')) title = 'Hồ sơ Giảng viên';
    else if (path.includes('questions')) title = 'Ngân hàng Câu hỏi Chuẩn Bloom';
    else if (path.includes('exams')) title = 'Phân hệ Soạn đề thi PWD301 LMS';
    else if (path.includes('governance')) title = 'Quản trị Học vụ';
    else if (path.includes('operations')) title = 'Vận hành & An ninh';

    titleEl.textContent = title;
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

    const roleName = this.currentRole === 'ADMIN' ? 'QUẢN TRỊ VIÊN' : this.currentRole === 'INSTRUCTOR' ? 'GIẢNG VIÊN' : 'HỌC VIÊN';
    if (roleBadge) {
      roleBadge.textContent = roleName;
      roleBadge.className = `px-1.5 py-0.2 rounded text-[8px] font-bold uppercase tracking-wider border ${
        this.currentRole === 'ADMIN'
          ? 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
          : this.currentRole === 'INSTRUCTOR'
          ? 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300'
          : 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
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
    if (avatarBtn && dropdown) {
      avatarBtn.onclick = (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('hidden');
      };
      document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== avatarBtn) {
          dropdown.classList.add('hidden');
        }
      });
    }
  }

  initNotifications() {
    const bellBtn = document.getElementById('topbar-notifications-btn');
    if (bellBtn) {
      bellBtn.onclick = () => {
        if (window.StudentView && typeof StudentView.openNotificationHub === 'function') {
          StudentView.openNotificationHub();
        }
      };
    }
    this.refreshNotificationBadge();
  }

  async refreshNotificationBadge() {
    if (!this.currentUser) return;
    try {
      const res = await ApiClient.getStudentNotifications();
      const badge = document.getElementById('topbar-notifications-badge');
      if (badge && res) {
        const count = res.unread_count || 0;
        if (count > 0) {
          badge.textContent = count > 99 ? '99+' : count;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }
    } catch (e) {
      // ignore
    }
  }
}

window.AppRouter = AppRouter;
