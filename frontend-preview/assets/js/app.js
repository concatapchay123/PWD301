/**
 * PWD301 — Online Course Management Platform
 * Application Shell Controller & Master Route Registry
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  class AppController {
    constructor() {
      this.store = window.PWD.store;
      this.router = window.PWD.router;
      this.components = window.PWD.components;
      this._lastToggleTime = 0;
    }

    init() {
      this.initTheme();
      this.initSidebarState();
      this.initNotifications();
      this.initAIChat();
      this.registerAllRoutes();
      this.renderSidebar();
      this.updatePerspectiveUI();
      this.router.init('router-outlet');
      this.bindEvents();
    }

    initSidebarState() {
      try {
        if (localStorage.getItem('pwd301_sidebar_collapsed') === 'true') {
          document.documentElement.classList.add('sidebar-collapsed');
          document.body.classList.add('sidebar-collapsed');
        }
      } catch (e) {}
    }

    toggleSidebar(e) {
      const now = Date.now();
      if (now - (this._lastToggleTime || 0) < 200) {
        if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
        return;
      }
      this._lastToggleTime = now;
      if (e && typeof e.stopPropagation === 'function') {
        e.stopPropagation();
      }
      const isCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
      const nextState = !isCollapsed;
      if (nextState) {
        document.documentElement.classList.add('sidebar-collapsed');
        document.body.classList.add('sidebar-collapsed');
        try { localStorage.setItem('pwd301_sidebar_collapsed', 'true'); } catch (err) {}
      } else {
        document.documentElement.classList.remove('sidebar-collapsed');
        document.body.classList.remove('sidebar-collapsed');
        try { localStorage.setItem('pwd301_sidebar_collapsed', 'false'); } catch (err) {}
      }
      const topbarToggleBtn = document.getElementById('sidebar-toggle-btn');
      if (topbarToggleBtn) {
        topbarToggleBtn.setAttribute('aria-expanded', String(!nextState));
        topbarToggleBtn.setAttribute('title', nextState ? 'Mở rộng menu (Ctrl+B)' : 'Thu gọn menu (Ctrl+B)');
        topbarToggleBtn.setAttribute('aria-label', nextState ? 'Mở rộng menu' : 'Thu gọn menu');
      }
    }

    bindEvents() {
      // Perspective dropdown change
      const select = document.getElementById('perspective-select');
      if (select) {
        select.addEventListener('change', (e) => {
          this.switchPerspective(e.target.value);
        });
      }

      // Allow clicking topbar brand wrapper in collapsed state to expand sidebar (TikTok style)
      const brandWrapper = document.querySelector('.topbar-brand-wrapper');
      if (brandWrapper && !brandWrapper._boundToggle) {
        brandWrapper._boundToggle = true;
        brandWrapper.addEventListener('click', (e) => {
          if (e.target.closest('#sidebar-toggle-btn')) {
            return;
          }
          if (document.documentElement.classList.contains('sidebar-collapsed')) {
            e.preventDefault();
            e.stopPropagation();
            this.toggleSidebar(e);
          }
        });
      }

      // Sidebar toggle button click listener
      const topbarToggleBtn = document.getElementById('sidebar-toggle-btn');
      if (topbarToggleBtn && !topbarToggleBtn._boundToggle) {
        topbarToggleBtn._boundToggle = true;
        topbarToggleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.toggleSidebar(e);
        });
      }

      // Keyboard shortcut: Ctrl + B (or Cmd + B on Mac)
      if (!this._boundKeyboard) {
        this._boundKeyboard = true;
        document.addEventListener('keydown', (e) => {
          if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
            const target = e.target;
            const isInput = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
            if (!isInput) {
              e.preventDefault();
              this.toggleSidebar(e);
            }
          }
        });
      }
    }

    switchPerspective(role) {
      this.store.setPerspective(role);
      this.renderSidebar();
      this.updatePerspectiveUI();

      // Navigate to default view for the perspective
      if (role === 'public') this.router.navigate('#/public/catalog');
      else if (role === 'student') this.router.navigate('#/student/dashboard');
      else if (role === 'instructor') this.router.navigate('#/instructor/dashboard');
      else if (role === 'admin') this.router.navigate('#/admin/dashboard');
    }

    updatePerspectiveUI() {
      const p = this.store.getPerspective();
      const badge = document.getElementById('demo-perspective-badge');
      if (badge) {
        let label = 'PUBLIC / KHÁCH';
        if (p === 'student') label = 'SINH VIÊN (Nguyễn Minh Anh)';
        else if (p === 'instructor') label = 'GIẢNG VIÊN (Trần Hoàng Nam)';
        else if (p === 'admin') label = 'QUẢN TRỊ VIÊN (Lê Thu Hà)';
        badge.textContent = label;
      }

      // Update Topbar avatar & name
      const user = this.store.getCurrentUser();
      const nameEl = document.getElementById('topbar-user-name');
      const avatarEl = document.getElementById('topbar-user-avatar');
      
      if (nameEl) {
        nameEl.textContent = user ? user.name : 'Khách vãng lai';
      }
      if (avatarEl) {
        avatarEl.textContent = user ? user.avatar : 'G';
      }

      // Update selector dropdown in topbar
      const select = document.getElementById('perspective-select');
      if (select) select.value = p;
    }

    renderSidebar() {
      const p = this.store.getPerspective();
      const sidebarContainer = document.getElementById('sidebar-nav-container');
      const offcanvasContainer = document.getElementById('offcanvas-nav-container');
      const cmp = this.components;

      let navHtml = '';

      if (p === 'public') {
        navHtml = `
          <div class="sidebar-section-label">Dành cho Khách</div>
          <li class="sidebar-item">
            <a href="#/public/catalog" class="sidebar-link">
              ${cmp.icon('book')} <span>Khám phá khóa học</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/public/login" class="sidebar-link">
              ${cmp.icon('user')} <span>Đăng nhập</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/public/register" class="sidebar-link">
              ${cmp.icon('graduation')} <span>Đăng ký tài khoản</span>
            </a>
          </li>
        `;
      } else if (p === 'student') {
        navHtml = `
          <div class="sidebar-section-label">Học tập</div>
          <li class="sidebar-item">
            <a href="#/student/dashboard" class="sidebar-link" title="Tổng quan" data-nav-label="Tổng quan">
              ${cmp.icon('activity')} <span>Tổng quan</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/my-learning" class="sidebar-link" title="Khóa học của tôi" data-nav-label="Khóa học của tôi">
              ${cmp.icon('book')} <span>Khóa học của tôi</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/catalog" class="sidebar-link" title="Khám phá khóa học" data-nav-label="Khám phá khóa học">
              ${cmp.icon('search')} <span>Khám phá khóa học</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/assessments" class="sidebar-link" title="Bài kiểm tra" data-nav-label="Bài kiểm tra">
              ${cmp.icon('clock')} <span>Bài kiểm tra</span>
            </a>
          </li>

          <div class="sidebar-section-label">Hỗ trợ & Tiện ích</div>
          <li class="sidebar-item">
            <a href="#/student/ai-assistant" class="sidebar-link" title="Trợ lý AI" data-nav-label="Trợ lý AI">
              ${cmp.icon('sparkles')} <span>Trợ lý AI</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/recommendations" class="sidebar-link" title="Gợi ý học tập" data-nav-label="Gợi ý học tập">
              ${cmp.icon('graduation')} <span>Gợi ý học tập</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/notifications" class="sidebar-link" title="Thông báo" data-nav-label="Thông báo">
              ${cmp.icon('bell')} <span>Thông báo</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/student/profile" class="sidebar-link" title="Hồ sơ cá nhân" data-nav-label="Hồ sơ cá nhân">
              ${cmp.icon('settings')} <span>Hồ sơ cá nhân</span>
            </a>
          </li>
        `;
      } else if (p === 'instructor') {
        navHtml = `
          <div class="sidebar-section-label">Giảng dạy</div>
          <li class="sidebar-item">
            <a href="#/instructor/dashboard" class="sidebar-link">
              ${cmp.icon('activity')} <span>Tổng quan giảng viên</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/courses" class="sidebar-link">
              ${cmp.icon('book')} <span>Khóa học của tôi</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/questions" class="sidebar-link">
              ${cmp.icon('database')} <span>Ngân hàng câu hỏi</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/assessments" class="sidebar-link">
              ${cmp.icon('clock')} <span>Bài kiểm tra & Đề thi</span>
            </a>
          </li>

          <div class="sidebar-section-label">Công cụ Soạn đề</div>
          <li class="sidebar-item">
            <a href="#/instructor/import" class="sidebar-link">
              ${cmp.icon('upload')} <span>Import DOCX/PDF</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/ai-generator" class="sidebar-link">
              ${cmp.icon('sparkles')} <span>AI sinh câu hỏi</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/grading-queue" class="sidebar-link">
              ${cmp.icon('edit')} <span>Hàng đợi chấm luận</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/export" class="sidebar-link">
              ${cmp.icon('download')} <span>Xuất bảng điểm</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/instructor/profile" class="sidebar-link">
              ${cmp.icon('settings')} <span>Hồ sơ giảng viên</span>
            </a>
          </li>
        `;
      } else if (p === 'admin') {
        navHtml = `
          <div class="sidebar-section-label">Quản trị & Vận hành</div>
          <li class="sidebar-item">
            <a href="#/admin/dashboard" class="sidebar-link">
              ${cmp.icon('activity')} <span>Tổng quan hệ thống</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/users" class="sidebar-link">
              ${cmp.icon('users')} <span>Quản lý người dùng</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/instructor-approvals" class="sidebar-link">
              ${cmp.icon('graduation')} <span>Duyệt giảng viên</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/role-management" class="sidebar-link">
              ${cmp.icon('user')} <span>Phân quyền (RBAC)</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/course-review" class="sidebar-link">
              ${cmp.icon('book')} <span>Duyệt khóa học</span>
            </a>
          </li>

          <div class="sidebar-section-label">Bảo mật & Kiểm toán</div>
          <li class="sidebar-item">
            <a href="#/admin/security-center" class="sidebar-link">
              ${cmp.icon('shield')} <span>Trung tâm bảo mật</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/security-events" class="sidebar-link">
              ${cmp.icon('alertTriangle')} <span>Sự kiện an ninh</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/ai-security" class="sidebar-link">
              ${cmp.icon('sparkles')} <span>An toàn AI</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/audit-log" class="sidebar-link">
              ${cmp.icon('fileText')} <span>Nhật ký Audit Log</span>
            </a>
          </li>

          <div class="sidebar-section-label">Hạ tầng & Dữ liệu</div>
          <li class="sidebar-item">
            <a href="#/admin/storage" class="sidebar-link">
              ${cmp.icon('database')} <span>Giám sát lưu trữ</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/jobs" class="sidebar-link">
              ${cmp.icon('clock')} <span>Tiến trình nền (Jobs)</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/system-health" class="sidebar-link">
              ${cmp.icon('server')} <span>Sức khỏe dịch vụ</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/backup-history" class="sidebar-link">
              ${cmp.icon('refresh')} <span>Sao lưu & Phục hồi</span>
            </a>
          </li>
          <li class="sidebar-item">
            <a href="#/admin/settings" class="sidebar-link">
              ${cmp.icon('settings')} <span>Cài đặt hệ thống</span>
            </a>
          </li>
        `;
      }

      if (sidebarContainer) sidebarContainer.innerHTML = `<ul class="sidebar-nav-list">${navHtml}</ul>`;
      if (offcanvasContainer) offcanvasContainer.innerHTML = `<ul class="sidebar-nav-list">${navHtml}</ul>`;
    }

    registerAllRoutes() {
      const v = window.PWD.views;

      // Public Routes
      this.router.register('/public/catalog', () => v.public.catalog());
      this.router.register('/public/course/:id', (params) => v.public.courseDetail(params));
      this.router.register('/public/login', () => v.public.login());
      this.router.register('/public/register', () => v.public.register());
      this.router.register('/public/forgot-password', () => v.public.forgotPassword());

      // Student Routes
      this.router.register('/student/dashboard', () => v.student.dashboard());
      this.router.register('/student/catalog', () => v.student.catalog());
      this.router.register('/student/course/:id', (params) => v.student.courseDetail(params));
      this.router.register('/student/my-learning', () => v.student.myLearning());
      this.router.register('/student/course-dashboard/:id', (params) => v.student.courseDashboard(params));
      this.router.register('/student/lesson/:id', (params) => v.student.lessonReader(params));
      this.router.register('/student/lesson-resources/:id', (params) => v.student.lessonResources(params));
      this.router.register('/student/progress/:id', (params) => v.student.progress(params));
      this.router.register('/student/assessments', () => v.student.assessments());
      this.router.register('/student/assessment-detail/:id', (params) => v.student.assessmentDetail(params));
      this.router.register('/student/attempt/:id', (params) => v.student.attempt(params));
      this.router.register('/student/attempt-submitted/:id', (params) => v.student.submitted(params));
      this.router.register('/student/result/:id', (params) => v.student.result(params));
      this.router.register('/student/score-history/:id', (params) => v.student.scoreHistory(params));
      this.router.register('/student/ai-assistant', () => v.student.aiAssistant());
      this.router.register('/student/recommendations', () => v.student.recommendations());
      this.router.register('/student/notifications', () => v.student.notifications());
      this.router.register('/student/profile', () => v.student.profile());

      // Instructor Routes
      this.router.register('/instructor/dashboard', () => v.instructor.dashboard());
      this.router.register('/instructor/courses', () => v.instructor.courses());
      this.router.register('/instructor/course-editor/:id', (params) => v.instructor.courseEditor(params));
      this.router.register('/instructor/curriculum/:id', (params) => v.instructor.curriculum(params));
      this.router.register('/instructor/lesson-editor/:id', (params) => v.instructor.lessonEditor(params));
      this.router.register('/instructor/resources/:id', (params) => v.instructor.resources(params));
      this.router.register('/instructor/questions', () => v.instructor.questions());
      this.router.register('/instructor/question-editor/:id', (params) => v.instructor.questionEditor(params));
      this.router.register('/instructor/question-history/:id', (params) => v.instructor.questionHistory(params));
      this.router.register('/instructor/assessments', () => v.instructor.assessments());
      this.router.register('/instructor/assessment-builder/:id', (params) => v.instructor.assessmentBuilder(params));
      this.router.register('/instructor/question-picker/:id', (params) => v.instructor.questionPicker(params));
      this.router.register('/instructor/blueprint-builder/:id', (params) => v.instructor.blueprintBuilder(params));
      this.router.register('/instructor/publish-validation/:id', (params) => v.instructor.publishValidation(params));
      this.router.register('/instructor/import', () => v.instructor.import());
      this.router.register('/instructor/import-review', () => v.instructor.importReview());
      this.router.register('/instructor/ai-generator', () => v.instructor.aiGenerator());
      this.router.register('/instructor/ai-draft-review', () => v.instructor.aiDraftReview());
      this.router.register('/instructor/monitoring/:id', (params) => v.instructor.monitoring(params));
      this.router.register('/instructor/grading-queue', () => v.instructor.gradingQueue());
      this.router.register('/instructor/grade-editor/:id', (params) => v.instructor.gradeEditor(params));
      this.router.register('/instructor/regrade-status/:id', (params) => v.instructor.regradeStatus(params));
      this.router.register('/instructor/analytics-assessment/:id', (params) => v.instructor.analyticsAssessment(params));
      this.router.register('/instructor/analytics-students/:id', (params) => v.instructor.analyticsStudents(params));
      this.router.register('/instructor/export', () => v.instructor.export());
      this.router.register('/instructor/profile', () => v.instructor.profile());

      // Admin Routes
      this.router.register('/admin/dashboard', () => v.admin.dashboard());
      this.router.register('/admin/users', () => v.admin.users());
      this.router.register('/admin/user-detail/:id', (params) => v.admin.userDetail(params));
      this.router.register('/admin/instructor-approvals', () => v.admin.instructorApprovals());
      this.router.register('/admin/role-management', () => v.admin.roleManagement());
      this.router.register('/admin/course-review', () => v.admin.courseReview());
      this.router.register('/admin/course-reassignment', () => v.admin.courseReassignment());
      this.router.register('/admin/security-center', () => v.admin.securityCenter());
      this.router.register('/admin/security-events', () => v.admin.securityEvents());
      this.router.register('/admin/ai-security', () => v.admin.aiSecurity());
      this.router.register('/admin/audit-log', () => v.admin.auditLog());
      this.router.register('/admin/audit-detail/:id', (params) => v.admin.auditDetail(params));
      this.router.register('/admin/storage', () => v.admin.storage());
      this.router.register('/admin/scanner-status', () => v.admin.scannerStatus());
      this.router.register('/admin/jobs', () => v.admin.jobs());
      this.router.register('/admin/system-health', () => v.admin.systemHealth());
      this.router.register('/admin/backup-history', () => v.admin.backupHistory());
      this.router.register('/admin/alerts', () => v.admin.alerts());
      this.router.register('/admin/settings', () => v.admin.settings());
      this.router.register('/admin/profile', () => v.admin.profile());
    }


    // ==========================================
    // THEME MANAGEMENT (Dark / Light Mode)
    // ==========================================
    initTheme() {
      const savedTheme = localStorage.getItem('pwd301_theme');
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = savedTheme || (prefersDark ? 'dark' : 'light');
      this.applyTheme(theme, false);
    }

    applyTheme(theme, showFeedback = true) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('pwd301_theme', theme);

      const themeIconEl = document.getElementById('theme-icon');
      const themeBtnEl = document.getElementById('theme-toggle-btn');
      if (themeIconEl && this.components) {
        themeIconEl.innerHTML = theme === 'dark' ? this.components.icon('sun') : this.components.icon('moon');
      }
      if (themeBtnEl) {
        themeBtnEl.title = theme === 'dark' ? 'Chuyển sang chế độ Sáng' : 'Chuyển sang chế độ Tối';
        themeBtnEl.setAttribute('aria-label', themeBtnEl.title);
      }

      if (showFeedback && this.components) {
        this.components.showToast(theme === 'dark' ? 'Đã bật Chế độ Tối' : 'Đã bật Chế độ Sáng', 'info');
      }
    }

    toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      this.applyTheme(next, true);
    }

    // ==========================================
    // NOTIFICATION BELL & DROPDOWN MANAGEMENT
    // ==========================================
    initNotifications() {
      const bellIconEl = document.getElementById('notif-bell-icon');
      if (bellIconEl && this.components) {
        bellIconEl.innerHTML = this.components.icon('bell');
      }
      this.updateNotificationBadge();
      this.renderNotificationList();

      // Close dropdown when clicking outside
      document.addEventListener('click', (e) => {
        const notifWrapper = document.getElementById('topbar-notif-wrapper');
        const notifDropdown = document.getElementById('notif-dropdown');
        if (notifDropdown && !notifDropdown.classList.contains('d-none')) {
          if (notifWrapper && !notifWrapper.contains(e.target)) {
            this.closeNotifications();
          }
        }
      });
    }

    updateNotificationBadge() {
      const notifs = this.store.state.notifications || [];
      const unreadCount = notifs.filter(n => !n.read).length;
      const badgeEl = document.getElementById('notif-badge');
      const headerBadgeEl = document.getElementById('notif-header-badge');

      if (badgeEl) {
        if (unreadCount > 0) {
          badgeEl.textContent = unreadCount > 9 ? '9+' : unreadCount;
          badgeEl.classList.remove('d-none');
        } else {
          badgeEl.classList.add('d-none');
        }
      }

      if (headerBadgeEl) {
        headerBadgeEl.textContent = `${unreadCount} mới`;
        if (unreadCount === 0) {
          headerBadgeEl.className = 'badge badge-neutral';
        } else {
          headerBadgeEl.className = 'badge badge-info';
        }
      }
    }

    renderNotificationList() {
      const container = document.getElementById('notif-list-container');
      if (!container) return;

      const notifs = this.store.state.notifications || [];
      if (notifs.length === 0) {
        container.innerHTML = `<div class="p-4 text-center text-caption text-muted">Không có thông báo nào</div>`;
        return;
      }

      container.innerHTML = notifs.map(n => `
        <div class="notif-item ${n.read ? 'read' : 'unread'}" onclick="PWD.app.clickNotificationItem('${n.id}', event)">
          <div class="notif-item-indicator"></div>
          <div class="flex-grow-1" style="min-width: 0;">
            <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
              <span class="notif-item-title">${n.title}</span>
              <span class="notif-item-time">${n.time}</span>
            </div>
            <p class="notif-item-body">${n.body}</p>
          </div>
        </div>
      `).join('');
    }

    toggleNotifications(e) {
      if (e) e.stopPropagation();
      const dropdown = document.getElementById('notif-dropdown');
      if (!dropdown) return;

      const isOpen = !dropdown.classList.contains('d-none');
      if (isOpen) {
        this.closeNotifications();
      } else {
        dropdown.classList.remove('d-none');
        this.renderNotificationList();
      }
    }

    closeNotifications() {
      const dropdown = document.getElementById('notif-dropdown');
      if (dropdown) dropdown.classList.add('d-none');
    }

    markAllNotificationsRead(e) {
      if (e) e.stopPropagation();
      const notifs = this.store.state.notifications || [];
      notifs.forEach(n => n.read = true);
      this.store.persist();
      this.updateNotificationBadge();
      this.renderNotificationList();
      this.components.showToast('Đã đánh dấu đọc tất cả thông báo.', 'info');
      if (window.location.hash.includes('notifications')) {
        this.router.handleRouting();
      }
    }

    clickNotificationItem(id, e) {
      if (e) e.stopPropagation();
      const notifs = this.store.state.notifications || [];
      const item = notifs.find(n => n.id === id);
      if (item) {
        item.read = true;
        this.store.persist();
        this.updateNotificationBadge();
        this.renderNotificationList();

        if (item.type === 'assessment') {
          this.closeNotifications();
          this.router.navigate('#/student/assessment-detail/a1');
        } else if (item.type === 'grade') {
          this.closeNotifications();
          this.router.navigate('#/student/result/att_completed_01');
        } else if (item.type === 'course') {
          this.closeNotifications();
          this.router.navigate('#/student/course/c4');
        }
      }
    }

    // ==========================================
    // FLOATING AI CHATBOT MANAGEMENT
    // ==========================================
    initAIChat() {
      const fabIcon = document.getElementById('ai-fab-icon');
      if (fabIcon && this.components) {
        fabIcon.innerHTML = this.components.icon('sparkles');
      }
    }

    toggleAIChat() {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      const icon = document.getElementById('ai-fab-icon');
      if (!win) return;

      const isHidden = win.classList.contains('d-none');
      if (isHidden) {
        if (window.PWD.motion && typeof window.PWD.motion.openAIChat === 'function') {
          window.PWD.motion.openAIChat(win);
        } else {
          win.classList.remove('d-none');
        }
        if (launcher) launcher.classList.add('active');
        if (icon && this.components) icon.innerHTML = this.components.icon('x');

        setTimeout(() => {
          const input = document.getElementById('ai-floating-input');
          if (input) input.focus();
        }, 150);
      } else {
        if (window.PWD.motion && typeof window.PWD.motion.closeAIChat === 'function') {
          window.PWD.motion.closeAIChat(win);
        } else {
          win.classList.add('d-none');
        }
        if (launcher) launcher.classList.remove('active');
        if (icon && this.components) icon.innerHTML = this.components.icon('sparkles');
      }
    }

    openAIChat(starterQuestion = '') {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      const icon = document.getElementById('ai-fab-icon');
      if (!win) return;

      if (window.PWD.motion && typeof window.PWD.motion.openAIChat === 'function') {
        window.PWD.motion.openAIChat(win);
      } else {
        win.classList.remove('d-none');
      }
      if (launcher) launcher.classList.add('active');
      if (icon && this.components) icon.innerHTML = this.components.icon('x');

      if (starterQuestion) {
        this.selectQuickPrompt(starterQuestion);
      } else {
        setTimeout(() => {
          const input = document.getElementById('ai-floating-input');
          if (input) input.focus();
        }, 150);
      }
    }

    closeAIChat() {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      const icon = document.getElementById('ai-fab-icon');
      if (window.PWD.motion && typeof window.PWD.motion.closeAIChat === 'function') {
        window.PWD.motion.closeAIChat(win);
      } else if (win) {
        win.classList.add('d-none');
      }
      if (launcher) launcher.classList.remove('active');
      if (icon && this.components) icon.innerHTML = this.components.icon('sparkles');
    }

    selectQuickPrompt(promptText) {
      const input = document.getElementById('ai-floating-input');
      if (input) {
        input.value = promptText;
        this.sendFloatingAIMessage();
      }
    }

    sendFloatingAIMessage() {
      const input = document.getElementById('ai-floating-input');
      const text = (input?.value || '').trim();
      if (!text) return;

      const msgContainer = document.getElementById('ai-floating-messages');
      if (!msgContainer) return;

      // 1. Append user message
      const userMsg = document.createElement('div');
      userMsg.className = 'ai-chat-msg ai-msg-user';
      userMsg.innerHTML = `
        <div class="ai-msg-avatar">MA</div>
        <div class="ai-msg-content">${this.escapeHtml(text)}</div>
      `;
      msgContainer.appendChild(userMsg);
      input.value = '';
      msgContainer.scrollTop = msgContainer.scrollHeight;

      // 2. Typing indicator
      const typingIndicator = document.createElement('div');
      typingIndicator.id = 'ai-typing-indicator';
      typingIndicator.className = 'ai-chat-msg ai-msg-bot';
      typingIndicator.innerHTML = `
        <div class="ai-msg-avatar">${this.components.icon('sparkles')}</div>
        <div class="ai-msg-content">
          <div class="ai-typing-indicator">
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
          </div>
        </div>
      `;
      msgContainer.appendChild(typingIndicator);
      msgContainer.scrollTop = msgContainer.scrollHeight;

      // 3. Simulated AI answer
      setTimeout(() => {
        const indicator = document.getElementById('ai-typing-indicator');
        if (indicator) indicator.remove();

        let answer = '';
        let citation = 'Bài giảng PWD301 & Tài liệu thực hành';

        const lower = text.toLowerCase();
        if (lower.includes('bán hàng') || lower.includes('lập trình cho') || lower.includes('viết web')) {
          answer = `Chào bạn! Trợ lý Bạch Tuộc AI là trợ lý học tập và hướng dẫn sử dụng hệ thống PWD301. Hệ thống không hỗ trợ lập trình gia công, xây dựng website thương mại hoặc viết mã nguồn dự án ngoài theo yêu cầu cá nhân. Bạn có thể tham khảo các khóa học Lập trình Web trên hệ thống để tự trang bị kiến thức nhé!`;
          citation = 'Quy chế Trợ lý Học tập PWD301 & Chính sách Phạm vi AI';
        } else if (lower.includes('khóa học') || lower.includes('môn học')) {
          answer = `Hệ thống PWD301 cung cấp nhiều khóa học chuyên sâu từ cơ bản đến nâng cao: Lập trình Web với Python & Flask, Kiến trúc Cơ sở Dữ liệu SQL Server, Thiết kế Giao diện Frontend, và An toàn Thông tin Ứng dụng Web. Bạn có thể truy cập mục <strong>Khóa học</strong> trên thanh điều hướng để xem chi tiết!`;
          citation = 'Danh mục Khóa học PWD301 Online Course Platform';
        } else if (lower.includes('đăng ký')) {
          answer = `Để đăng ký khóa học: 1. Vào trang <strong>Khóa học</strong>; 2. Chọn môn học bạn quan tâm để xem thông tin chi tiết; 3. Nhấn nút <strong>Đăng ký học</strong>. Nếu khóa học có điều kiện tiên quyết, bạn cần hoàn thành môn học trước đó để được xét duyệt.`;
          citation = 'Hướng dẫn Học viên: Quy trình Đăng ký Môn học';
        } else if (lower.includes('thi') || lower.includes('kiểm tra') || lower.includes('điểm') || lower.includes('nộp bài')) {
          answer = `Để làm bài kiểm tra: Bạn vào mục <strong>Bài kiểm tra</strong> trong bảng điều khiển học viên, chọn đề thi được giao và nhấn <strong>Bắt đầu làm bài</strong>. Sau khi hoàn thành, nhấn <strong>Nộp bài</strong> để hệ thống tự động chấm điểm và ghi nhận bảng điểm ngay lập tức.`;
          citation = 'Quy chế Thi & Đánh giá Kết quả Học tập';
        } else if (lower.includes('giảng viên') || lower.includes('ứng tuyển') || lower.includes('nộp đơn')) {
          answer = `Để trở thành Giảng viên trên PWD301: Học viên truy cập trang <strong>Trở thành Giảng viên</strong> từ menu hồ sơ, điền minh chứng chuyên môn (kinh nghiệm giảng dạy, chứng chỉ, hợp đồng/thu nhập) và gửi đơn. Quản trị viên (Admin) sẽ xét duyệt và cấp quyền trong 24-48 giờ.`;
          citation = 'Quy trình Tự ứng cử & Xét duyệt Giảng viên';
        } else {
          answer = `Chào bạn! Ở trang chính, Trợ lý Bạch Tuộc AI sẵn sàng hỗ trợ giải đáp về hệ thống PWD301, danh mục khóa học và hướng dẫn sử dụng các tính năng nền tảng. Bạn cần hỗ trợ thêm thông tin gì về hệ thống không?`;
          citation = 'Trung tâm Hỗ trợ Học tập & Hướng dẫn Nền tảng PWD301';
        }

        const botMsg = document.createElement('div');
        botMsg.className = 'ai-chat-msg ai-msg-bot';
        botMsg.innerHTML = `
          <div class="ai-msg-avatar">${this.components.icon('sparkles')}</div>
          <div class="ai-msg-content">
            <div>${answer}</div>
            <div class="ai-citation-badge">📖 <strong>Nguồn:</strong> ${citation}</div>
          </div>
        `;
        msgContainer.appendChild(botMsg);
        msgContainer.scrollTop = msgContainer.scrollHeight;
      }, 600);
    }

    escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  }

  window.PWD.app = new AppController();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.PWD.app.init();
    });
  } else {
    window.PWD.app.init();
  }
})();
