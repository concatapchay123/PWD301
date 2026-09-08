/**
 * PWD301 — Public / Guest Views
 * Functional Minimalism — Academic SaaS LMS
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};
  window.PWD.views = window.PWD.views || {};

  const publicViews = {
    // 1. Public Course Catalog
    catalog() {
      const courses = window.PWD.store.state.courses.filter(c => c.status !== 'draft');
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Khám phá Khóa học',
          subtitle: 'Danh mục các chương trình đào tạo trực tuyến công khai tại PWD301',
          primaryAction: `<a href="#/public/login" class="btn btn-primary btn-sm">Đăng nhập</a>`
        })}

        <div class="row g-3 mb-4 align-items-center">
          <div class="col-md-5">
            <div class="catalog-search-wrap">
              <span class="text-slate-400 me-2">${cmp.icon('search')}</span>
              <input type="text" id="public-search" class="catalog-search-input border-0 w-100" placeholder="Tìm kiếm theo mã môn hoặc tên khóa học..." oninput="PWD.views.public.handleCatalogFilter()">
            </div>
          </div>
          <div class="col-md-4">
            <select id="public-category-filter" class="form-select" onchange="PWD.views.public.handleCatalogFilter()">
              <option value="all">Tất cả danh mục</option>
              <option value="Phát triển Web">Phát triển Web</option>
              <option value="Frontend">Frontend</option>
              <option value="Dữ liệu">Dữ liệu</option>
              <option value="Bảo mật">Bảo mật</option>
              <option value="Hệ thống">Hệ thống</option>
              <option value="AI / ML">AI / ML</option>
            </select>
          </div>
          <div class="col-md-3 text-md-end d-none d-md-block">
            <span class="text-caption text-muted">Hiển thị: <strong>${courses.length}</strong> khóa học</span>
          </div>
        </div>

        <div class="row g-4" id="public-course-grid">
          ${courses.map(course => cmp.renderCourseCard(course, { targetLink: `#/public/course/${course.id}` })).join('')}
        </div>
      `;
    },

    renderCourseCard(course) {
      const cmp = window.PWD.components;
      return cmp.renderCourseCard(course, { targetLink: `#/public/course/${course.id}` });
    },

    handleCatalogFilter() {
      const query = (document.getElementById('public-search')?.value || '').toLowerCase().trim();
      const cat = document.getElementById('public-category-filter')?.value || 'all';

      const cards = document.querySelectorAll('#public-course-grid > div');
      cards.forEach(card => {
        const qData = (card.getAttribute('data-query') || card.getAttribute('data-title') || '').toLowerCase();
        const code = (card.getAttribute('data-code') || '').toLowerCase();
        const category = card.getAttribute('data-category') || '';

        const matchesQuery = !query || qData.includes(query) || code.includes(query);
        const matchesCat = cat === 'all' || category === cat;

        card.style.display = (matchesQuery && matchesCat) ? 'block' : 'none';
      });
    },

    // 2. Public Course Detail
    courseDetail(params) {
      const course = window.PWD.store.state.courses.find(c => c.id === params.id);
      const cmp = window.PWD.components;

      if (!course) {
        return cmp.emptyState('Không tìm thấy khóa học', 'Khóa học này không tồn tại hoặc đã bị gỡ bỏ.', `<a href="#/public/catalog" class="btn btn-secondary btn-sm">Quay lại danh mục</a>`);
      }

      const lessons = window.PWD.store.state.lessons.filter(l => l.courseId === course.id);

      return `
        ${cmp.pageHeader({
          title: course.title,
          subtitle: `Mã môn học: ${course.code} • Phân môn: ${course.category}`,
          breadcrumbs: [
            { label: 'Khám phá khóa học', href: '#/public/catalog' },
            { label: course.code, href: `#/public/course/${course.id}` }
          ],
          primaryAction: `<a href="#/public/login" class="btn btn-primary btn-sm">Đăng nhập để ghi danh</a>`
        })}

        <div class="row g-4">
          <div class="col-lg-8">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="sub-title m-0">Giới thiệu khóa học</h5>
              </div>
              <div class="card-body">
                <p style="font-size: var(--font-body); line-height: 1.6;">${course.description}</p>
                <div class="alert-card alert-card-info mt-3">
                  <span style="flex-shrink:0;">${cmp.icon('checkCircle')}</span>
                  <div>
                    <strong>Điều kiện hoàn thành môn:</strong>
                    <div class="text-caption mt-1">${course.completionRule}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Khung chương trình đào tạo</h5>
                <span class="text-caption text-muted">${lessons.length} bài học</span>
              </div>
              <div class="card-body p-0">
                <ul class="list-group list-group-flush">
                  ${lessons.length === 0 ? `<li class="list-group-item p-4 text-muted text-center">Nội dung bài giảng đang được cập nhật.</li>` : ''}
                  ${lessons.map((les, idx) => `
                    <li class="list-group-item d-flex justify-content-between align-items-center px-4 py-3">
                      <div>
                        <span class="text-caption text-muted me-2">${idx + 1}.</span>
                        <span class="fw-medium">${les.title}</span>
                      </div>
                      <span class="text-caption text-muted">${les.duration}</span>
                    </li>
                  `).join('')}
                </ul>
              </div>
            </div>
          </div>

          <div class="col-lg-4">
            <div class="card">
              <div class="card-header">
                <h5 class="sub-title m-0">Thông tin tổng quan</h5>
              </div>
              <div class="card-body">
                <div class="mb-3">
                  <div class="text-caption text-muted">Giảng viên phụ trách</div>
                  <div class="fw-medium">${course.instructorName}</div>
                </div>
                <div class="mb-3">
                  <div class="text-caption text-muted">Chỉ tiêu ghi danh</div>
                  <div class="fw-medium">${course.enrolledCount} / ${course.capacity} sinh viên</div>
                </div>
                <div class="mb-3">
                  <div class="text-caption text-muted">Môn học tiên quyết</div>
                  <div class="fw-medium">
                    ${course.prerequisites && course.prerequisites.length > 0 
                      ? course.prerequisites.map(pId => {
                          const p = window.PWD.store.state.courses.find(c => c.id === pId);
                          return `<span class="badge badge-warning me-1">${p ? p.code : pId}</span>`;
                        }).join('')
                      : '<span class="text-muted">Không có</span>'
                    }
                  </div>
                </div>
                <div class="border-top border-slate-200 pt-3">
                  <button onclick="PWD.app.switchPerspective('student'); PWD.router.navigate('#/student/course/${course.id}')" class="btn btn-secondary btn-sm w-100">
                    Chuyển sang Sinh viên để thử ghi danh
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 3. Login View
    login() {
      const cmp = window.PWD.components;

      return `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 70vh;">
          <div class="card" style="width: 100%; max-width: 440px;">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <div class="topbar-brand-mark mx-auto mb-2" style="width: 36px; height: 36px; font-size: 16px;">P3</div>
                <h4 class="page-title mb-1">Đăng nhập PWD301</h4>
                <p class="text-caption text-muted m-0">Hệ thống Quản lý Khóa học Trực tuyến</p>
              </div>

              <!-- Quick Demo Persona Switcher -->
              <div class="p-3 bg-slate-50 border border-slate-200 rounded mb-4">
                <div class="text-caption fw-semibold text-slate-700 mb-2">Truy cập nhanh tài khoản demo:</div>
                <div class="d-grid gap-2">
                  <button type="button" class="btn btn-secondary btn-sm text-start d-flex justify-content-between" onclick="PWD.views.public.doQuickLogin('student')">
                    <span><strong>Sinh viên:</strong> Nguyễn Minh Anh</span>
                    <span class="text-muted">→</span>
                  </button>
                  <button type="button" class="btn btn-secondary btn-sm text-start d-flex justify-content-between" onclick="PWD.views.public.doQuickLogin('instructor')">
                    <span><strong>Giảng viên:</strong> Trần Hoàng Nam</span>
                    <span class="text-muted">→</span>
                  </button>
                  <button type="button" class="btn btn-secondary btn-sm text-start d-flex justify-content-between" onclick="PWD.views.public.doQuickLogin('admin')">
                    <span><strong>Quản trị viên:</strong> Lê Thu Hà</span>
                    <span class="text-muted">→</span>
                  </button>
                </div>
              </div>

              <form onsubmit="event.preventDefault(); PWD.views.public.handleFormLogin();">
                <div class="form-group mb-3">
                  <label class="form-label">Địa chỉ email</label>
                  <input type="email" id="login-email" class="form-control form-control-sm" placeholder="nhap@email.com" value="student@demo.local">
                </div>
                <div class="form-group mb-3">
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <label class="form-label m-0">Mật khẩu</label>
                    <a href="#/public/forgot-password" class="text-caption text-decoration-none">Quên mật khẩu?</a>
                  </div>
                  <input type="password" id="login-password" class="form-control form-control-sm" placeholder="••••••••" value="demo1234">
                </div>
                <button type="submit" class="btn btn-primary btn-sm w-100">Đăng nhập</button>
              </form>

              <div class="text-center mt-3 pt-3 border-top border-slate-200">
                <span class="text-caption text-muted">Chưa có tài khoản?</span>
                <a href="#/public/register" class="text-caption fw-semibold ms-1">Đăng ký mới</a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    doQuickLogin(role) {
      window.PWD.app.switchPerspective(role);
      window.PWD.components.showToast(`Đã chuyển sang góc nhìn demo: ${role.toUpperCase()}`, 'success');
      if (role === 'student') window.PWD.router.navigate('#/student/dashboard');
      else if (role === 'instructor') window.PWD.router.navigate('#/instructor/dashboard');
      else if (role === 'admin') window.PWD.router.navigate('#/admin/dashboard');
    },

    handleFormLogin() {
      const email = document.getElementById('login-email')?.value.trim() || '';
      if (email.includes('instructor')) this.doQuickLogin('instructor');
      else if (email.includes('admin')) this.doQuickLogin('admin');
      else this.doQuickLogin('student');
    },

    // 4. Register View
    register() {
      return `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 70vh;">
          <div class="card" style="width: 100%; max-width: 440px;">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <div class="topbar-brand-mark mx-auto mb-2" style="width: 36px; height: 36px; font-size: 16px;">P3</div>
                <h4 class="page-title mb-1">Đăng ký tài khoản</h4>
                <p class="text-caption text-muted m-0">Tạo tài khoản học viên PWD301</p>
              </div>

              <form onsubmit="event.preventDefault(); PWD.views.public.handleRegisterSubmit();">
                <div class="form-group mb-3">
                  <label class="form-label">Họ và tên <span class="required">*</span></label>
                  <input type="text" id="reg-name" class="form-control form-control-sm" placeholder="Nguyễn Văn A" required>
                </div>
                <div class="form-group mb-3">
                  <label class="form-label">Email học viên <span class="required">*</span></label>
                  <input type="email" id="reg-email" class="form-control form-control-sm" placeholder="student@demo.local" required>
                </div>
                <div class="form-group mb-4">
                  <label class="form-label">Mật khẩu <span class="required">*</span></label>
                  <input type="password" id="reg-pwd" class="form-control form-control-sm" placeholder="Tối thiểu 8 ký tự" required>
                </div>
                <button type="submit" class="btn btn-primary btn-sm w-100">Đăng ký tài khoản</button>
              </form>

              <div class="text-center mt-3 pt-3 border-top border-slate-200">
                <span class="text-caption text-muted">Đã có tài khoản?</span>
                <a href="#/public/login" class="text-caption fw-semibold ms-1">Đăng nhập</a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    handleRegisterSubmit() {
      window.PWD.components.showToast('Đăng ký tài khoản demo thành công! Tự động chuyển về giao diện Sinh viên.', 'success');
      this.doQuickLogin('student');
    },

    // 5. Forgot Password View
    forgotPassword() {
      return `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 70vh;">
          <div class="card" style="width: 100%; max-width: 440px;">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <h4 class="page-title mb-1">Khôi phục mật khẩu</h4>
                <p class="text-caption text-muted m-0">Nhập email để nhận liên kết đặt lại mật khẩu</p>
              </div>

              <form onsubmit="event.preventDefault(); PWD.components.showToast('Mô phỏng: Liên kết khôi phục đã được gửi vào hòm thư!', 'info'); PWD.router.navigate('#/public/login');">
                <div class="form-group mb-4">
                  <label class="form-label">Email đăng ký</label>
                  <input type="email" class="form-control form-control-sm" placeholder="student@demo.local" required>
                </div>
                <button type="submit" class="btn btn-primary btn-sm w-100 mb-2">Gửi liên kết khôi phục</button>
                <a href="#/public/login" class="btn btn-secondary btn-sm w-100">Quay lại đăng nhập</a>
              </form>
            </div>
          </div>
        </div>
      `;
    }
  };

  window.PWD.views.public = publicViews;
})();
