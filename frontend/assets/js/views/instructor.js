/**
 * PWD301 LMS - Instructor Views Layer
 * Implements:
 * 1. Instructor Dashboard & KPIs
 * 2. Course Management Hub (Settings, Interactive Lesson Authoring Studio, Student Roster)
 * 3. Question Bank Hub & Subject Inspector (Bloom 6-level taxonomy, curriculum modules, Gemini AI drafting)
 * 4. PWD301 Split-View 50/50 Exam Authoring Studio (3-step workflow, raw syntax parser, validation modal)
 * 4. Academic Matrix & Blooms Taxonomy Management
 * 5. Fullscreen Low-Tech Lesson Authoring Studio
 * 6. PWD301 Exam Builder & Quality Gate Engine
 */

class InstructorView {
  // =========================================================================
  // 1. Instructor Dashboard
  // =========================================================================
  static async renderDashboard(container) {
    container.innerHTML = `
      <div class="py-4 sm:py-6 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
        <!-- Hero Header (Warm Surface Card) -->
        <div class="bg-white dark:bg-[#202020] rounded-2xl p-6 sm:p-8 text-[#222120] dark:text-[#EDEDEB] shadow-subtle flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border border-[#E8E6DF] dark:border-[#2E2D2B]">
          <div class="space-y-2">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F4F1EA] dark:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs font-semibold">
              <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
              Dành cho giảng viên
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#222120] dark:text-[#EDEDEB]">Trang chủ Giảng viên</h1>
            <p class="text-[#5C5B57] dark:text-[#9E9D99] text-sm max-w-xl">Quản lý khóa học, bài giảng và đề thi của bạn.</p>
          </div>
          <div class="flex items-center gap-3 shrink-0">
            <button type="button" id="quick-create-course-btn" class="px-4 sm:px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-sm transition-colors shadow-xs flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">add_circle</span>
              Tạo khóa học mới
            </button>
            <a href="#/instructor/exams" class="px-4 sm:px-5 py-2.5 rounded-xl bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] font-bold text-sm transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px] text-[#8F8E8A] dark:text-[#9E9D99]">quiz</span>
              Soạn đề thi
            </a>
          </div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Khóa học phụ trách</span>
              <span class="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-100/50 dark:border-blue-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">auto_stories</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-courses">
              <span class="inline-block w-12 h-7 bg-[#F4F1EA] dark:bg-[#262524] rounded-lg animate-pulse"></span>
            </div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1" id="ins-kpi-courses-sub">Đang xây dựng & mở lớp</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Tổng sinh viên</span>
              <span class="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-100/50 dark:border-emerald-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">groups</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-students">
              <span class="inline-block w-12 h-7 bg-[#F4F1EA] dark:bg-[#262524] rounded-lg animate-pulse"></span>
            </div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Học viên đang theo học</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Bài giảng & Giáo trình</span>
              <span class="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-100/50 dark:border-indigo-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">menu_book</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-lessons">
              <span class="inline-block w-12 h-7 bg-[#F4F1EA] dark:bg-[#262524] rounded-lg animate-pulse"></span>
            </div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Bài giảng đã xuất bản</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Kỳ thi & Đánh giá</span>
              <span class="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border border-purple-100/50 dark:border-purple-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">assignment</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-assessments">
              <span class="inline-block w-12 h-7 bg-[#F4F1EA] dark:bg-[#262524] rounded-lg animate-pulse"></span>
            </div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Đề thi & Bài kiểm tra đã phát hành</div>
          </div>
        </div>

        <!-- Recent Courses Table Section -->
        <div class="space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] flex items-center gap-2">
                <span class="material-symbols-outlined text-primary dark:text-blue-400 text-[20px]">table_chart</span>
                Danh sách khóa học quản lý
              </h2>
            </div>
            <a href="#/instructor/courses" class="text-xs font-semibold text-primary dark:text-blue-400 hover:underline">Xem đầy đủ</a>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl shadow-xs overflow-hidden" id="ins-courses-table-box">
            <div class="p-8 text-center text-[#8F8E8A] dark:text-[#6D6C68]">
              <span class="inline-block animate-spin text-xl mb-2">⏳</span>
              <p class="text-sm">Đang tải danh sách khóa học...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('quick-create-course-btn').onclick = () => {
      InstructorView.openCreateCourseModal();
    };

    const loadDashboardData = async () => {
      try {
        const res = await ApiClient.getInstructorDashboard({ scope: 'assigned' });
        const analytics = (res && res.data) ? res.data : (res || {});

        const courses = analytics.courses || [];
        const totalStudents = analytics.total_students ?? 0;
        const totalLessons = courses.reduce((acc, c) => acc + (c.lessons?.length || 0), 0);
        const totalAssessments = analytics.total_assessments !== undefined
          ? analytics.total_assessments
          : (courses.reduce((acc, c) => acc + (c.assessments?.length || 0), 0));

        document.getElementById('ins-kpi-courses').textContent = analytics.managed_courses_count ?? courses.length;
        document.getElementById('ins-kpi-students').textContent = totalStudents;
        document.getElementById('ins-kpi-lessons').textContent = totalLessons;
        const kpiAss = document.getElementById('ins-kpi-assessments');
        if (kpiAss) kpiAss.textContent = totalAssessments;

        const subKpi = document.getElementById('ins-kpi-courses-sub');
        if (subKpi) {
          subKpi.textContent = 'Khóa học được phân công & quản lý';
        }

        const tableBox = document.getElementById('ins-courses-table-box');
        if (courses.length === 0) {
          tableBox.innerHTML = `
            <div class="text-center py-12 p-6">
              <span class="material-symbols-outlined text-4xl text-[#8F8E8A] dark:text-[#6D6C68] mb-2">menu_book</span>
              <p class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB]">Bạn chưa được phân công hoặc chưa tạo khóa học nào</p>
              <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1 mb-4">Bắt đầu bằng việc tạo một khóa học mới với mã môn và giáo trình chuẩn.</p>
              <button type="button" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors" onclick="InstructorView.openCreateCourseModal()">
                Tạo khóa học ngay
              </button>
            </div>
          `;
        } else {
          tableBox.innerHTML = `
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs sm:text-sm">
                <thead class="bg-[#F4F1EA] dark:bg-[#262524] border-b border-[#E8E6DF] dark:border-[#2E2D2B] text-[#8F8E8A] dark:text-[#9E9D99] uppercase tracking-wider text-[11px] font-bold">
                  <tr>
                    <th class="px-5 py-3.5">Mã môn</th>
                    <th class="px-5 py-3.5">Tên khóa học</th>
                    <th class="px-5 py-3.5">Danh mục</th>
                    <th class="px-5 py-3.5">Trạng thái</th>
                    <th class="px-5 py-3.5">Sĩ số</th>
                    <th class="px-5 py-3.5 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E8E6DF] dark:divide-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB] font-medium">
                  ${courses.map(c => `
                    <tr class="hover:bg-[#FAF9F5] dark:hover:bg-[#262524]/60 transition-colors">
                      <td class="px-5 py-3.5 font-mono font-bold text-primary dark:text-blue-400">${UI.escapeHtml(c.course_code)}</td>
                      <td class="px-5 py-3.5 font-bold text-[#222120] dark:text-[#EDEDEB] max-w-xs truncate">${UI.escapeHtml(c.title)}</td>
                      <td class="px-5 py-3.5 text-[#5C5B57] dark:text-[#9E9D99]">${UI.escapeHtml(c.category || 'Công nghệ')}</td>
                      <td class="px-5 py-3.5">${UI.statusBadge(c.status)}</td>
                      <td class="px-5 py-3.5 font-semibold text-[#222120] dark:text-[#EDEDEB]">${c.enrolled_count ?? c.enrollments_count ?? 0} sinh viên</td>
                      <td class="px-5 py-3.5 text-right">
                        <a href="#/instructor/courses/manage?id=${c.course_id || c.id}" class="px-3 py-1.5 rounded-lg bg-[#F4F1EA] dark:bg-[#262524] text-[#222120] dark:text-[#EDEDEB] hover:bg-primary hover:text-white dark:hover:bg-primary dark:hover:text-white border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs font-bold transition-colors shadow-2xs">
                          Quản lý
                        </a>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          `;
        }
      } catch (e) {
        console.warn('Instructor dashboard load error:', e);
        const tableBox = document.getElementById('ins-courses-table-box');
        if (tableBox) {
          tableBox.innerHTML = `
            <div class="p-8 text-center text-rose-500 font-bold text-xs">
              Lỗi tải dữ liệu bảng điều khiển: ${UI.escapeHtml(e.message || 'Không thể kết nối máy chủ')}
            </div>
          `;
        }
        if (typeof UI !== 'undefined' && typeof UI.showToast === 'function') {
          UI.showToast('Không thể tải dữ liệu bảng điều khiển giảng viên.', 'error');
        }
      }
    };

    const btnDashAssigned = document.getElementById('btn-dash-scope-assigned');
    const btnDashAll = document.getElementById('btn-dash-scope-all');
    if (btnDashAssigned) {
      btnDashAssigned.onclick = () => {
        if (dashScope !== 'assigned') loadDashboardData('assigned');
      };
    }
    if (btnDashAll) {
      btnDashAll.onclick = () => {
        if (dashScope !== 'all') loadDashboardData('all');
      };
    }

    await loadDashboardData('assigned');
  }

  // =========================================================================
  // 2. Courses Table & Create Course Modal
  // =========================================================================
  static async renderCourses(container) {
    container.innerHTML = `
      <div class="py-4 sm:py-6 lg:py-8 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
        
        <!-- Header Banner (Warm Surface Card) -->
        <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-6 sm:p-8 shadow-subtle flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div class="space-y-1.5">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F4F1EA] dark:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs font-semibold">
              <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              KHÓA HỌC PHỤ TRÁCH
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-[#222120] dark:text-[#EDEDEB] tracking-tight">
              Khóa học của tôi
            </h1>
            <p class="text-xs sm:text-sm text-[#5C5B57] dark:text-[#9E9D99] max-w-2xl">
              Quản lý bài giảng, giáo trình và bài kiểm tra cho các học phần bạn giảng dạy.
            </p>
          </div>

          <div class="flex items-center gap-3 shrink-0">
            <button
              type="button"
              id="btn-add-course"
              class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-[18px]">add_circle</span>
              <span>Tạo khóa học mới</span>
            </button>
          </div>
        </div>

        <!-- Search & Filter Bar -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div class="relative flex-1 max-w-md">
            <span class="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8F8E8A] dark:text-[#6D6C68] text-[19px]">search</span>
            <input
              type="text"
              id="courses-filter-search"
              class="w-full h-11 pl-10 pr-4 rounded-xl bg-white dark:bg-[#202020] text-xs text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] border border-[#E8E6DF] dark:border-[#2E2D2B] focus:outline-none focus:border-primary shadow-2xs"
              placeholder="Tìm kiếm theo mã môn hoặc tên khóa học..."
            />
          </div>

          <div class="flex items-center gap-2.5">
            <div class="relative">
              <select
                id="courses-filter-status"
                class="h-11 pl-3.5 pr-9 rounded-xl bg-white dark:bg-[#202020] text-xs font-semibold text-[#5C5B57] dark:text-[#EDEDEB] border border-[#E8E6DF] dark:border-[#2E2D2B] focus:outline-none focus:border-primary shadow-2xs cursor-pointer appearance-none bg-none"
              >
                <option value="ALL" selected>Tất cả trạng thái</option>
                <option value="PUBLISHED">Đang mở (Published)</option>
                <option value="APPROVED">Đã duyệt (Approved)</option>
                <option value="DRAFT">Bản nháp (Draft)</option>
                <option value="SUBMITTED_FOR_REVIEW">Chờ duyệt (In Review)</option>
              </select>
              <span class="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#8F8E8A] dark:text-[#6D6C68] text-[18px]">expand_more</span>
            </div>

            <button
              type="button"
              id="btn-refresh-courses"
              class="h-11 w-11 rounded-xl bg-white dark:bg-[#202020] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99] flex items-center justify-center transition-colors shadow-2xs"
              title="Làm mới danh sách và đặt lại bộ lọc"
            >
              <span class="material-symbols-outlined text-[19px]">refresh</span>
            </button>
          </div>
        </div>

        <!-- Clean Course Cards Grid -->
        <div id="ins-courses-cards-box" class="min-h-[360px]">
          <div class="p-16 text-center text-[#8F8E8A] dark:text-[#6D6C68]">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-xs">Đang tải danh mục khóa học...</p>
          </div>
        </div>

      </div>
    `;

    document.getElementById('btn-add-course').onclick = () => {
      InstructorView.openCreateCourseModal();
    };

    let allCourses = [];
    let coursesScope = 'assigned';

    const updateTabsUI = () => {
      const tabAssigned = document.getElementById('tab-scope-assigned');
      const tabAll = document.getElementById('tab-scope-all');
      if (!tabAssigned || !tabAll) return;

      if (coursesScope === 'assigned') {
        tabAssigned.className = 'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-2xs bg-white dark:bg-[#202020] text-primary dark:text-blue-400 border border-[#E8E6DF] dark:border-[#2E2D2B]';
        tabAll.className = 'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB]';
      } else {
        tabAll.className = 'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-2xs bg-white dark:bg-[#202020] text-primary dark:text-blue-400 border border-[#E8E6DF] dark:border-[#2E2D2B]';
        tabAssigned.className = 'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB]';
      }
    };

    const renderCards = (coursesToDisplay) => {
      const box = document.getElementById('ins-courses-cards-box');
      if (!box) return;

      if (coursesToDisplay.length === 0) {
        box.innerHTML = `
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-12 text-center shadow-xs">
            <span class="material-symbols-outlined text-4xl text-[#8F8E8A] dark:text-[#6D6C68] mb-2">auto_stories</span>
            <p class="font-bold text-[#222120] dark:text-[#EDEDEB] text-sm">Chưa có khóa học nào</p>
            <p class="text-xs mt-1 text-[#5C5B57] dark:text-[#9E9D99] max-w-sm mx-auto">Bắt đầu bằng việc tạo một khóa học mới hoặc thay đổi từ khóa tìm kiếm.</p>
            <button
              type="button"
              onclick="InstructorView.openCreateCourseModal()"
              class="mt-4 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Tạo khóa học ngay</span>
            </button>
          </div>
        `;
        return;
      }

      box.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          ${coursesToDisplay.map(c => {
            const cId = c.course_id || c.id;
            const lessonCount = (c.lessons || []).length;
            const studentCount = c.enrollments_count ?? c.enrolled_count ?? 0;
            return `
              <div
                class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs hover:border-primary/40 hover:shadow-subtle transition-all flex flex-col justify-between gap-4 group cursor-pointer"
                onclick="window.location.hash = '#/instructor/courses/manage?id=${cId}'"
              >
                <div class="space-y-3">
                  <!-- Course Thumbnail Image -->
                  <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 border border-[#E8E6DF] dark:border-[#2E2D2B]">
                    ${c.thumbnail_url ? `
                      <img src="${UI.escapeHtml(c.thumbnail_url)}" alt="${UI.escapeHtml(c.title)}" class="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300" onerror="this.remove()" />
                    ` : `
                      <div class="w-full h-full flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 gap-1 p-4">
                        <span class="material-symbols-outlined text-[28px]">image</span>
                        <span class="text-[11px] font-semibold">Chưa có ảnh bìa</span>
                      </div>
                    `}
                  </div>

                  <!-- Top Row: Code & Status & Instructor -->
                  <div class="flex items-center justify-between gap-2 flex-wrap">
                    <span class="font-mono font-extrabold text-primary text-xs px-2.5 py-1 rounded-lg bg-primary-subtle border border-primary/20">
                      ${UI.escapeHtml(c.course_code)}
                    </span>
                    <div class="flex items-center gap-1.5 flex-wrap">
                      ${c.instructor_name ? `
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-[#F4F1EA] dark:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] text-[11px] font-semibold border border-[#E8E6DF] dark:border-[#2E2D2B]" title="Giảng viên phụ trách">
                          <span class="material-symbols-outlined text-[13px]">school</span>
                          <span>${UI.escapeHtml(c.instructor_name)}</span>
                        </span>
                      ` : ''}
                      ${UI.statusBadge(c.status)}
                    </div>
                  </div>

                  <!-- Course Title -->
                  <h3 class="text-base font-bold text-[#222120] dark:text-[#EDEDEB] leading-snug line-clamp-2 group-hover:text-primary transition-colors" title="${UI.escapeHtml(c.title)}">
                    ${UI.escapeHtml(c.title)}
                  </h3>

                  <!-- Category / Description -->
                  <p class="text-xs text-[#5C5B57] dark:text-[#9E9D99] line-clamp-2 leading-relaxed">
                    ${UI.escapeHtml(c.description || c.category || 'Chưa có mô tả chi tiết.')}
                  </p>
                </div>

                <div class="space-y-3 pt-3 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
                  <!-- Meta Stats -->
                  <div class="flex items-center justify-between text-xs text-[#8F8E8A] dark:text-[#9E9D99]">
                    <span class="flex items-center gap-1">
                      <span class="material-symbols-outlined text-[16px] text-primary">menu_book</span>
                      <span>${lessonCount} bài học</span>
                    </span>
                    <span class="flex items-center gap-1">
                      <span class="material-symbols-outlined text-[16px] text-emerald-600">groups</span>
                      <span>${studentCount} sinh viên</span>
                    </span>
                  </div>

                  <!-- Action Button -->
                  <a
                    href="#/instructor/courses/manage?id=${cId}"
                    class="w-full py-2.5 px-4 rounded-xl bg-[#F4F1EA] hover:bg-primary hover:text-white dark:bg-[#262524] dark:hover:bg-primary dark:hover:text-white text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all flex items-center justify-center gap-2 border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs"
                    onclick="event.stopPropagation()"
                  >
                    <span>Mở khóa học</span>
                    <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </a>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    };

    const getFilteredCourses = () => {
      const searchVal = (document.getElementById('courses-filter-search')?.value || '').toLowerCase().trim();
      const statusVal = document.getElementById('courses-filter-status')?.value || 'ALL';

      return allCourses.filter(c => {
        const matchesSearch = !searchVal || 
          c.course_code.toLowerCase().includes(searchVal) || 
          c.title.toLowerCase().includes(searchVal) ||
          (c.instructor_name && c.instructor_name.toLowerCase().includes(searchVal)) ||
          (c.category && c.category.toLowerCase().includes(searchVal));

        const matchesStatus = statusVal === 'ALL' || c.status === statusVal;
        return matchesSearch && matchesStatus;
      });
    };

    const loadData = async () => {
      try {
        const res = await ApiClient.getInstructorCourses({ scope: 'assigned' });
        const resData = (res && res.data) ? res.data : (res || {});
        allCourses = Array.isArray(resData.courses)
          ? resData.courses
          : (Array.isArray(res?.courses) ? res.courses : []);

        renderCards(getFilteredCourses());
      } catch (e) {
        const box = document.getElementById('ins-courses-cards-box');
        if (box) {
          box.innerHTML = `
            <div class="col-span-full p-8 rounded-2xl bg-white dark:bg-[#18181b] border border-rose-200 dark:border-rose-900/50 text-center space-y-3 shadow-sm">
              <span class="material-symbols-outlined text-3xl text-rose-500">sync_problem</span>
              <p class="text-sm font-bold text-slate-900 dark:text-white">Không thể tải danh sách khóa học</p>
              <p class="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">${UI.escapeHtml(e.message || 'Lỗi kết nối máy chủ.')}</p>
              <button type="button" class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-1 cursor-pointer" onclick="UI.refreshCurrentRoute()">
                <span class="material-symbols-outlined text-[14px]">refresh</span>
                <span>Thử lại</span>
              </button>
            </div>
          `;
        }
      }
    };

    document.getElementById('courses-filter-search').oninput = () => renderCards(getFilteredCourses());
    document.getElementById('courses-filter-status').onchange = () => renderCards(getFilteredCourses());
    document.getElementById('btn-refresh-courses').onclick = () => {
      const searchInput = document.getElementById('courses-filter-search');
      const statusSelect = document.getElementById('courses-filter-status');
      if (searchInput) searchInput.value = '';
      if (statusSelect) statusSelect.value = 'ALL';
      renderCards(allCourses);
      loadData(coursesScope);
      if (typeof UI !== 'undefined' && typeof UI.showToast === 'function') {
        UI.showToast('Đã làm mới danh sách và đặt lại bộ lọc.', 'info');
      }
    };

    await loadData('assigned');
  }

  static openCreateCourseModal() {
    const formHtml = `
      <form id="create-course-modal-form" class="space-y-4">
        <!-- Lưu ý quan trọng cho Giảng viên khi tạo khóa học mới -->
        <div class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-900 dark:text-amber-300 text-xs flex items-start gap-2.5">
          <span class="material-symbols-outlined text-amber-600 dark:text-amber-400 text-lg shrink-0 mt-0.5">info</span>
          <div class="leading-relaxed">
            <strong class="font-bold">Lưu ý quan trọng cho Giảng viên:</strong><br/>
            Hãy hoàn tất bài giảng, tài liệu và đề thi trước khi gửi duyệt khóa học.
          </div>
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
            Tên khóa học đầy đủ *
          </label>
          <input
            type="text"
            name="title"
            required
            placeholder="VD: Lập trình Web Cao cấp & REST API"
            class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
              Mã khóa học *
            </label>
            <input
              type="text"
              name="course_code"
              required
              placeholder="VD: PWD301, CS101"
              class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm font-mono uppercase text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
            />
          </div>

          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
              Danh mục đào tạo
            </label>
            <input
              type="text"
              name="category"
              list="academic-categories-list"
              placeholder="VD: Khoa học máy tính & CNTT"
              class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
            />
            <datalist id="academic-categories-list">
              <option value="Khoa học máy tính & CNTT"></option>
              <option value="Phát triển Web & Di động"></option>
              <option value="Trí tuệ nhân tạo & Dữ liệu"></option>
              <option value="Thiết kế Đồ họa & UI/UX"></option>
              <option value="Quản trị Kinh doanh"></option>
              <option value="Kỹ thuật Phần mềm"></option>
            </datalist>
          </div>
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
            Mô tả tóm tắt (Tùy chọn)
          </label>
          <textarea
            name="description"
            rows="2"
            placeholder="Tóm tắt ngắn gọn nội dung môn học..."
            class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary resize-none"
          ></textarea>
        </div>
      </form>
    `;

    const footerHtml = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-colors" onclick="UI.closeModal()">
        Hủy bỏ
      </button>
      <button type="button" id="submit-create-course-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs">
        Tạo khóa học
      </button>
    `;

    UI.openModal({
      title: 'Tạo khóa học mới',
      bodyHtml: formHtml,
      footerHtml: footerHtml,
      size: 'md'
    });

    document.getElementById('submit-create-course-btn').onclick = async () => {
      const form = document.getElementById('create-course-modal-form');
      if (!form) return;

      const code = form.course_code.value.trim().toUpperCase();
      const title = form.title.value.trim();
      const desc = form.description.value.trim();
      const cat = form.category.value.trim() || 'Khoa học máy tính & CNTT';

      if (!code || !title) {
        UI.showToast('Vui lòng nhập đầy đủ Tên khóa học và Mã khóa học.', 'warning');
        return;
      }

      const btn = document.getElementById('submit-create-course-btn');
      btn.disabled = true;
      btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang tạo...';

      try {
        const res = await ApiClient.createCourse({
          course_code: code,
          title: title,
          description: desc,
          category: cat,
          difficulty: 'INTERMEDIATE',
          capacity: null
        });
        UI.closeModal();
        UI.showToast(`Đã tạo khóa học ${code} thành công!`, 'success');
        window.location.hash = `#/instructor/courses/manage?id=${res.course_id || res.id}`;
      } catch (err) {
        UI.showToast(err.message || 'Lỗi khi tạo khóa học.', 'error');
        btn.disabled = false;
        btn.innerHTML = 'Tạo khóa học';
      }
    };
  }

  // Helper to parse lesson raw data into modular vertical blocks for low-tech instructors
  static parseLessonToBlocks(lesson) {
    if (!lesson) return [{ id: 'blk_' + Math.random().toString(36).slice(2, 9), type: 'text', content: '' }];
    const blocks = [];
    const rawMd = lesson.markdown_content || '';

    // 1. Extract video URLs from rawMd or lesson.video_urls
    let videoUrls = Array.isArray(lesson.video_urls) ? [...lesson.video_urls] : [];
    const ytMatch = rawMd.match(/<!--\s*video_urls?:\s*(\[.*?\])\s*-->/);
    if (ytMatch) {
      try {
        const parsed = JSON.parse(ytMatch[1]);
        if (Array.isArray(parsed)) {
          parsed.forEach(u => { if (!videoUrls.includes(u)) videoUrls.push(u); });
        }
      } catch (_) {}
    }
    const singleYt = rawMd.match(/<!--\s*video_url:\s*(\S+?)\s*-->/);
    if (singleYt && !videoUrls.includes(singleYt[1])) {
      videoUrls.push(singleYt[1]);
    }

    // 2. Extract quizzes from rawMd or lesson.quiz
    let quizzes = Array.isArray(lesson.quiz) ? [...lesson.quiz] : [];
    let quizPassingPercent = lesson.quiz_passing_percent || 80;
    const quizMatch = rawMd.match(/<!--\s*mini_quiz:\s*(.+?)\s*-->/s);
    if (quizMatch) {
      try {
        const parsedQ = JSON.parse(quizMatch[1]);
        if (Array.isArray(parsedQ) && quizzes.length === 0) quizzes = parsedQ;
      } catch (_) {}
    }
    const passingMatch = rawMd.match(/<!--\s*mini_quiz_passing:\s*(\d+)\s*-->/);
    if (passingMatch) {
      quizPassingPercent = parseInt(passingMatch[1], 10) || 80;
    }
    lesson.quiz_passing_percent = quizPassingPercent;

    // 3. Clean markdown text
    const cleanMd = rawMd
      .replace(/<!--\s*video_urls?:.*?-->\s*/gs, '')
      .replace(/<!--\s*video_url:\s*\S+?\s*-->\s*/gs, '')
      .replace(/<!--\s*mini_quiz:.*?-->\s*/gs, '')
      .replace(/<!--\s*mini_quiz_passing:\s*\d+\s*-->\s*/gs, '')
      .trim();

    if (cleanMd) {
      blocks.push({
        id: 'blk_' + Math.random().toString(36).slice(2, 9),
        type: 'text',
        content: cleanMd
      });
    }

    // Extract video resources and document resources
    const attachedResources = Array.isArray(lesson.resources) ? lesson.resources : [];
    const videoFiles = [];
    const docFiles = [];
    attachedResources.forEach(res => {
      const fn = res.filename || res.title || 'Tài liệu';
      const mime = (res.mime_type || '').toLowerCase();
      const isVideo = mime.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/i.test(fn);
      if (isVideo) {
        videoFiles.push({
          resource_id: res.resource_id,
          asset_id: res.asset_id,
          title: fn,
          filename: fn,
          file_url: res.file_url,
          file_size_bytes: res.file_size_bytes
        });
      } else {
        docFiles.push({
          resource_id: res.resource_id,
          asset_id: res.asset_id,
          title: fn,
          filename: fn,
          file_url: res.file_url,
          file_size_bytes: res.file_size_bytes
        });
      }
    });

    // Add Video blocks
    if (videoUrls.length > 0 || videoFiles.length > 0) {
      blocks.push({
        id: 'blk_' + Math.random().toString(36).slice(2, 9),
        type: 'video',
        videoType: 'YOUTUBE',
        url: videoUrls[0] || '',
        files: videoFiles,
        title: 'Video bài giảng'
      });
      for (let i = 1; i < videoUrls.length; i++) {
        blocks.push({
          id: 'blk_' + Math.random().toString(36).slice(2, 9),
          type: 'video',
          videoType: 'YOUTUBE',
          url: videoUrls[i],
          files: [],
          title: `Video bài giảng ${i + 1}`
        });
      }
    }

    if (docFiles.length > 0) {
      blocks.push({
        id: 'blk_' + Math.random().toString(36).slice(2, 9),
        type: 'document',
        title: 'Tài liệu học tập đính kèm',
        files: docFiles
      });
    }

    // Add Quiz blocks
    quizzes.forEach(q => {
      const qType = q.type || q.q_type || 'MULTIPLE_CHOICE';
      blocks.push({
        id: 'blk_' + Math.random().toString(36).slice(2, 9),
        type: 'quiz',
        q_type: qType,
        question: q.question || q.prompt || '',
        image_url: q.image_url || q.question_image_url || '',
        option_images: Array.isArray(q.option_images) ? q.option_images : [],
        options: Array.isArray(q.options) && q.options.length ? q.options : (Array.isArray(q.choices) ? q.choices : ['', '', '', '']),
        correct_index: q.correct_index ?? q.answer_index ?? 0,
        blank_answer: q.blank_answer || (q.blanks?.[0]?.accepted_answers?.[0] || ''),
        pairs: Array.isArray(q.pairs) && q.pairs.length ? q.pairs : [
          { left: '', right: '' },
          { left: '', right: '' }
        ],
        explanation: q.explanation || '',
        passing_percent: quizPassingPercent
      });
    });

    // If completely empty, provide one default text block
    if (blocks.length === 0) {
      blocks.push({
        id: 'blk_' + Math.random().toString(36).slice(2, 9),
        type: 'text',
        content: ''
      });
    }

    return blocks;
  }

  // Helper to serialize blocks into API payload
  static serializeBlocksToPayload(blocks, meta = {}) {
    const textChunks = [];
    const videoUrls = [];
    const quizzes = [];
    const resources = [];

    blocks.forEach(b => {
      if (b.type === 'text') {
        if (b.content && b.content.trim()) textChunks.push(b.content.trim());
      } else if (b.type === 'video') {
        const u = (b.url || '').trim();
        if (u) videoUrls.push(u);
        if (Array.isArray(b.files)) {
          b.files.forEach(f => resources.push(f));
        }
      } else if (b.type === 'document') {
        if (Array.isArray(b.files)) {
          b.files.forEach(f => resources.push(f));
        }
      } else if (b.type === 'quiz') {
        if (b.question && b.question.trim()) {
          const qType = b.q_type || 'MULTIPLE_CHOICE';
          const qObj = {
            question: b.question.trim(),
            type: qType,
            explanation: (b.explanation || '').trim(),
            image_url: b.image_url || b.question_image_url || '',
            question_image_url: b.image_url || b.question_image_url || ''
          };
          if (qType === 'MULTIPLE_CHOICE') {
            qObj.options = (b.options || ['', '', '', '']).map(opt => String(opt || '').trim());
            qObj.correct_index = Number(b.correct_index || 0);
            if (Array.isArray(b.option_images)) qObj.option_images = b.option_images;
          } else if (qType === 'FILL_BLANK') {
            const ans = (b.blank_answer || '').trim();
            qObj.blanks = [{ accepted_answers: ans ? [ans] : [] }];
            qObj.blank_answer = ans;
          } else if (qType === 'MATCHING') {
            qObj.pairs = Array.isArray(b.pairs) ? b.pairs.filter(p => p.left && p.right) : [];
          }
          quizzes.push(qObj);
        }
      }
    });

    let finalMd = textChunks.join('\n\n');
    if (!finalMd.trim()) {
      finalMd = `# ${meta.title || 'Bài giảng'}\n\n${meta.summary || 'Nội dung bài học.'}`;
    }
    if (quizzes.length > 0) {
      finalMd += '\n\n<!-- mini_quiz: ' + JSON.stringify(quizzes) + ' -->';
      const passingPercent = meta.quiz_passing_percent || 80;
      finalMd += '\n<!-- mini_quiz_passing: ' + passingPercent + ' -->';
    }

    return {
      title: (meta.title || 'Bài giảng').trim(),
      summary: (meta.summary || '').trim(),
      markdown_content: finalMd,
      video_urls: videoUrls,
      quiz: quizzes,
      quiz_passing_percent: meta.quiz_passing_percent || 80,
      resources: resources,
      status: 'DRAFT'
    };
  }

  // -------------------------------------------------------------------------
  // Microsoft Word Ribbon Toolbar Event Wireup
  // -------------------------------------------------------------------------
  static wireWordRibbon(container) {
    if (!container) return;

    container.querySelectorAll('.word-ribbon-toolbar').forEach(toolbar => {
      const card = toolbar.closest('.curriculum-block-card');
      const canvas = card ? card.querySelector('.word-editor-canvas') : null;
      const textarea = card ? card.querySelector('.block-text-textarea') : null;
      if (!canvas) return;

      const syncContent = () => {
        if (textarea) textarea.value = canvas.innerHTML;
      };

      canvas.addEventListener('input', syncContent);
      canvas.addEventListener('blur', syncContent);

      const exec = (cmd, val = null) => {
        canvas.focus();
        try {
          document.execCommand(cmd, false, val);
          syncContent();
        } catch (e) {
          console.warn('execCommand error:', cmd, e);
        }
      };

      // 1. Clipboard
      toolbar.querySelector('.btn-word-paste')?.addEventListener('click', async () => {
        canvas.focus();
        try {
          if (navigator.clipboard && navigator.clipboard.readText) {
            const text = await navigator.clipboard.readText();
            document.execCommand('insertText', false, text);
          } else {
            exec('paste');
          }
        } catch {
          exec('paste');
        }
        syncContent();
      });

      toolbar.querySelector('.btn-word-cut')?.addEventListener('click', () => exec('cut'));
      toolbar.querySelector('.btn-word-copy')?.addEventListener('click', () => exec('copy'));

      toolbar.querySelector('.btn-word-format-painter')?.addEventListener('click', () => {
        UI.showToast('Format Painter: Bôi đen đoạn cần áp dụng định dạng.', 'info');
      });

      // 2. Font
      toolbar.querySelector('.word-font-family')?.addEventListener('change', (e) => {
        exec('fontName', e.target.value);
      });

      toolbar.querySelector('.word-font-size')?.addEventListener('change', (e) => {
        exec('fontSize', e.target.value);
      });

      toolbar.querySelector('.btn-word-grow-font')?.addEventListener('click', () => {
        const sizeSelect = toolbar.querySelector('.word-font-size');
        if (sizeSelect && sizeSelect.selectedIndex < sizeSelect.options.length - 1) {
          sizeSelect.selectedIndex++;
          exec('fontSize', sizeSelect.value);
        }
      });

      toolbar.querySelector('.btn-word-shrink-font')?.addEventListener('click', () => {
        const sizeSelect = toolbar.querySelector('.word-font-size');
        if (sizeSelect && sizeSelect.selectedIndex > 0) {
          sizeSelect.selectedIndex--;
          exec('fontSize', sizeSelect.value);
        }
      });

      toolbar.querySelector('.btn-word-change-case')?.addEventListener('click', () => {
        const sel = window.getSelection();
        if (sel && sel.toString()) {
          const text = sel.toString();
          const isUpper = text === text.toUpperCase();
          const newText = isUpper ? text.toLowerCase() : text.toUpperCase();
          exec('insertText', newText);
        }
      });

      toolbar.querySelector('.btn-word-clear-formatting')?.addEventListener('click', () => {
        exec('removeFormat');
      });

      // 3. Styles
      toolbar.querySelector('.word-styles-select')?.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'p-nospace') {
          exec('formatBlock', 'p');
          const sel = window.getSelection();
          if (sel?.anchorNode?.parentElement) {
            sel.anchorNode.parentElement.style.marginBottom = '0px';
          }
        } else {
          exec('formatBlock', val);
        }
      });

      // 4. Font Styles
      toolbar.querySelector('.btn-word-bold')?.addEventListener('click', () => exec('bold'));
      toolbar.querySelector('.btn-word-italic')?.addEventListener('click', () => exec('italic'));
      toolbar.querySelector('.btn-word-underline')?.addEventListener('click', () => exec('underline'));
      toolbar.querySelector('.btn-word-strike')?.addEventListener('click', () => exec('strikeThrough'));
      toolbar.querySelector('.btn-word-subscript')?.addEventListener('click', () => exec('subscript'));
      toolbar.querySelector('.btn-word-superscript')?.addEventListener('click', () => exec('superscript'));

      toolbar.querySelector('.word-highlight-color')?.addEventListener('input', (e) => {
        exec('hiliteColor', e.target.value);
      });

      toolbar.querySelector('.word-font-color')?.addEventListener('input', (e) => {
        exec('foreColor', e.target.value);
      });

      // 5. Paragraph
      toolbar.querySelector('.btn-word-bullets')?.addEventListener('click', () => exec('insertUnorderedList'));
      toolbar.querySelector('.btn-word-numbering')?.addEventListener('click', () => exec('insertOrderedList'));
      toolbar.querySelector('.btn-word-decrease-indent')?.addEventListener('click', () => exec('outdent'));
      toolbar.querySelector('.btn-word-increase-indent')?.addEventListener('click', () => exec('indent'));
      toolbar.querySelector('.btn-word-align-left')?.addEventListener('click', () => exec('justifyLeft'));
      toolbar.querySelector('.btn-word-align-center')?.addEventListener('click', () => exec('justifyCenter'));
      toolbar.querySelector('.btn-word-align-right')?.addEventListener('click', () => exec('justifyRight'));
      toolbar.querySelector('.btn-word-align-justify')?.addEventListener('click', () => exec('justifyFull'));

      toolbar.querySelector('.btn-word-line-spacing')?.addEventListener('click', () => {
        const currentLH = canvas.style.lineHeight || '1.6';
        const nextLH = currentLH === '1.6' ? '2.0' : (currentLH === '2.0' ? '1.2' : '1.6');
        canvas.style.lineHeight = nextLH;
        UI.showToast(`Giãn dòng: ${nextLH}`, 'info');
      });

      // 6. Editing
      toolbar.querySelector('.btn-word-find')?.addEventListener('click', async () => {
        const query = await UI.prompt('Tìm kiếm văn bản', 'Nhập từ hoặc cụm từ cần tìm:', '', 'Từ khóa...');
        if (query && window.find) {
          window.find(query);
        }
      });

      toolbar.querySelector('.btn-word-replace')?.addEventListener('click', async () => {
        const query = await UI.prompt('Thay thế văn bản', 'Nhập từ khóa cần thay thế:', '', 'Tìm từ...');
        if (!query) return;
        const replaceWith = await UI.prompt('Thay thế bằng', `Thay "${query}" bằng:`, '', 'Nội dung mới...');
        if (replaceWith !== null) {
          const html = canvas.innerHTML;
          canvas.innerHTML = html.replaceAll(query, replaceWith);
          syncContent();
          UI.showToast('Đã thay thế tất cả.', 'success');
        }
      });

      toolbar.querySelector('.btn-word-select-all')?.addEventListener('click', () => exec('selectAll'));
    });
  }


  // =========================================================================
  // 3.0. Single-Page Curriculum Studio Implementation (Low-Tech Optimized)
  // =========================================================================
  static openCoursePreview(course, initialLessonId = null) {
    let preview = null;
    UI.openModal({
      title: 'Xem trước giáo trình',
      bodyHtml: '<div id="instructor-course-tree-preview"></div>',
      size: 'xl',
      onClose: () => preview?.querySelectorAll('video').forEach(video => video.pause()),
    });
    preview = document.getElementById('instructor-course-tree-preview');
    window.AdminView.renderReviewerCoursePreview(preview, course, initialLessonId);
  }

  static async initSinglePageCurriculumStudio(container, course, changesetStatus, initialLessonId = null, initialUnitId = null, assessments = null) {
    const cId = course.course_id || course.id;
    const treeContainer = container.querySelector('#tree-units-container');
    const editorContainer = container.querySelector('#curriculum-editor-pane');
    const statsBadge = container.querySelector('#tree-stats-badge');
    const btnTreeAddUnit = container.querySelector('#btn-tree-add-unit');
    const btnTreeAddLesson = container.querySelector('#btn-tree-add-lesson');

    if (!treeContainer || !editorContainer) return;

    if (!assessments || !Array.isArray(assessments)) {
      try {
        const asmRes = await ApiClient.getCourseAssessments(cId).catch(() => ({ assessments: [] }));
        assessments = asmRes.assessments || asmRes.items || (Array.isArray(asmRes) ? asmRes : []);
      } catch (e) {
        assessments = [];
      }
    }

    const isLocked = (changesetStatus && changesetStatus.status === 'PENDING') || course.status === 'SUBMITTED_FOR_REVIEW';

    // Normalize units and lessons
    let currentUnits = (course.learning_units || []).map(u => ({
      ...u,
      lessons: Array.isArray(u.lessons) ? [...u.lessons] : []
    }));

    // If units don't have lessons array populated, distribute course.lessons by learning_unit_id
    if (Array.isArray(course.lessons) && course.lessons.length > 0) {
      const unitMap = new Map();
      currentUnits.forEach(u => unitMap.set(String(u.learning_unit_id || u.id), u));
      course.lessons.forEach(l => {
        const targetUnit = unitMap.get(String(l.learning_unit_id));
        if (targetUnit) {
          if (!targetUnit.lessons.some(existing => String(existing.lesson_id || existing.id) === String(l.lesson_id || l.id))) {
            targetUnit.lessons.push(l);
          }
        }
      });
    }

    let activeLessonId = initialLessonId || null;
    let activeUnitId = initialUnitId || null;
    let activeBlocks = [];
    let activeLessonMeta = { title: '', duration: 15, summary: '', status: 'DRAFT' };
    let isSaving = false;
    let activeQuizQuestionIndex = 0;

    // Helper to find unit containing a lesson
    const findUnitForLesson = (lessonId) => {
      for (const u of currentUnits) {
        if (u.lessons && u.lessons.some(l => String(l.lesson_id || l.id) === String(lessonId))) {
          return u.learning_unit_id || u.id;
        }
      }
      return null;
    };

    if (!activeLessonId && currentUnits.length > 0) {
      for (const u of currentUnits) {
        if (u.lessons && u.lessons.length > 0) {
          activeLessonId = u.lessons[0].lesson_id || u.lessons[0].id;
          activeUnitId = u.learning_unit_id || u.id;
          break;
        }
      }
      if (!activeUnitId && currentUnits.length > 0) {
        activeUnitId = currentUnits[0].learning_unit_id || currentUnits[0].id;
      }
    } else if (activeLessonId && !activeUnitId) {
      activeUnitId = findUnitForLesson(activeLessonId);
    }

    // Refresh tree stats badge
    const updateTreeStats = () => {
      let totalL = 0;
      currentUnits.forEach(u => { totalL += (u.lessons?.length || 0); });
      if (statsBadge) {
        statsBadge.textContent = `${currentUnits.length} Chương • ${totalL} Bài giảng`;
      }
    };

    // Scrape values from current block inputs into activeBlocks array
    const scrapeBlocksFromDom = () => {
      const titleInput = editorContainer.querySelector('#input-lesson-title');
      const summaryInput = editorContainer.querySelector('#input-lesson-summary');

      if (titleInput) activeLessonMeta.title = titleInput.value.trim();
      if (summaryInput) activeLessonMeta.summary = summaryInput.value.trim();

      const blockCards = editorContainer.querySelectorAll('.curriculum-block-card');
      blockCards.forEach((card, idx) => {
        if (idx >= activeBlocks.length) return;
        const block = activeBlocks[idx];
        if (block.type === 'text') {
          const canvas = card.querySelector('.word-editor-canvas');
          if (canvas) {
            block.content = canvas.innerHTML;
            const textarea = card.querySelector('.block-text-textarea');
            if (textarea) textarea.value = canvas.innerHTML;
          } else {
            const textarea = card.querySelector('.block-text-textarea');
            if (textarea) block.content = textarea.value;
          }
        } else if (block.type === 'video') {
          const urlInput = card.querySelector('.block-video-url');
          if (urlInput) block.url = urlInput.value.trim();
          block.videoType = block.videoType || 'YOUTUBE';
        } else if (block.type === 'quiz') {
          const qInput = card.querySelector('.block-quiz-question');
          if (qInput) block.question = qInput.value.trim();
          const activeType = card.dataset.activeQtype || card.querySelector('[data-active-qtype]')?.dataset.activeQtype || block.q_type || 'MULTIPLE_CHOICE';
          block.q_type = activeType;

          if (activeType === 'MULTIPLE_CHOICE') {
            const optInputs = card.querySelectorAll('.block-quiz-opt-text');
            block.options = Array.from(optInputs).map(i => i.value.trim());
            const checkedRadio = card.querySelector('input[type="radio"]:checked');
            if (checkedRadio) block.correct_index = parseInt(checkedRadio.value, 10) || 0;
          } else if (activeType === 'FILL_BLANK') {
            const blankInput = card.querySelector('.block-quiz-blank-answer');
            if (blankInput) block.blank_answer = blankInput.value.trim();
          } else if (activeType === 'MATCHING') {
            const pairRows = card.querySelectorAll('.block-quiz-pair-row');
            block.pairs = Array.from(pairRows).map(row => {
              const leftInput = row.querySelector('.block-quiz-pair-left');
              const rightInput = row.querySelector('.block-quiz-pair-right');
              return {
                left: leftInput ? leftInput.value.trim() : '',
                right: rightInput ? rightInput.value.trim() : ''
              };
            });
          }

          const expInput = card.querySelector('.block-quiz-explanation');
          if (expInput) block.explanation = expInput.value.trim();

          const passingInput = card.querySelector('.block-quiz-passing-percent');
          if (passingInput) {
            const pVal = parseInt(passingInput.value, 10);
            if (!isNaN(pVal) && pVal >= 50 && pVal <= 100) {
              block.passing_percent = pVal;
              activeLessonMeta.quiz_passing_percent = pVal;
            }
          }
        }
      });
    };

    // Render tree function
    const renderTree = () => {
      updateTreeStats();
      if (currentUnits.length === 0) {
        treeContainer.innerHTML = `
          <div class="text-center py-8 px-4 bg-[#FAF9F5] dark:bg-[#18181b] rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B]">
            <span class="material-symbols-outlined text-3xl text-[#8F8E8A] dark:text-[#6D6C68] mb-1">folder_open</span>
            <p class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Chưa có Chương bài học nào</p>
            <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-1 mb-3">Tạo Chương đầu tiên để bắt đầu xây dựng giáo trình.</p>
            <button
              type="button"
              id="btn-tree-create-first-unit"
              class="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1 cursor-pointer ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}"
              ${isLocked ? 'disabled' : ''}
            >
              <span class="material-symbols-outlined text-[15px]">add</span>
              <span>Thêm Chương đầu tiên</span>
            </button>
          </div>
        `;
        treeContainer.querySelector('#btn-tree-create-first-unit')?.addEventListener('click', handleAddUnit);
        return;
      }

      treeContainer.innerHTML = currentUnits.map((unit, uIdx) => {
        const uId = unit.learning_unit_id || unit.id;
        const uLessons = unit.lessons || [];
        const isUnitActive = String(activeUnitId) === String(uId);

        // Find assessment linked to this chapter
        const uExam = assessments.find(a => (a.learning_unit_id && String(a.learning_unit_id) === String(uId)) || (a.description && a.description.includes('unit_id: ' + uId)) || (a.title && a.title.toLowerCase().includes('chương ' + (uIdx + 1))));

        return `
          <div
            class="unit-tree-node rounded-xl border ${isUnitActive ? 'border-primary/40 bg-primary/[0.02]' : 'border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#18181b]'} overflow-hidden transition-all shadow-2xs"
            data-unit-id="${uId}"
            data-unit-idx="${uIdx}"
            draggable="${!isLocked ? 'true' : 'false'}"
          >
            <!-- Unit Header -->
            <div class="p-3 bg-[#FAF9F5] dark:bg-[#202020] border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between gap-2">
              <div class="flex items-center gap-1.5 min-w-0">
                ${!isLocked ? `
                  <span class="material-symbols-outlined text-[16px] text-[#8F8E8A] dark:text-[#6D6C68] hover:text-primary cursor-grab active:cursor-grabbing shrink-0 drag-handle-unit select-none" title="Kéo thả để sắp xếp thứ tự Chương">drag_indicator</span>
                ` : ''}
                <span class="w-6 h-6 rounded-lg bg-primary/10 text-primary font-bold text-[11px] flex items-center justify-center shrink-0">
                  ${uIdx + 1}
                </span>
                <span class="font-bold text-xs text-[#222120] dark:text-[#EDEDEB] truncate" title="${UI.escapeHtml(unit.title)}">
                  ${UI.escapeHtml(unit.title)}
                </span>
                <span class="text-[10px] text-[#8F8E8A] dark:text-[#6D6C68] shrink-0 font-medium">(${uLessons.length})</span>
              </div>

              <!-- Unit Controls -->
              <div class="flex items-center gap-0.5 shrink-0" onclick="event.stopPropagation()">
                ${!isLocked ? `
                  <button type="button" class="btn-unit-move-up p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99] transition-colors cursor-pointer" data-idx="${uIdx}" title="Di chuyển lên" ${uIdx === 0 ? 'disabled style="opacity: 0.3;"' : ''}>
                    <span class="material-symbols-outlined text-[15px]">arrow_upward</span>
                  </button>
                  <button type="button" class="btn-unit-move-down p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99] transition-colors cursor-pointer" data-idx="${uIdx}" title="Di chuyển xuống" ${uIdx === currentUnits.length - 1 ? 'disabled style="opacity: 0.3;"' : ''}>
                    <span class="material-symbols-outlined text-[15px]">arrow_downward</span>
                  </button>
                  <button type="button" class="btn-rename-unit p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99] transition-colors cursor-pointer" data-unit-id="${uId}" title="Đổi tên Chương">
                    <span class="material-symbols-outlined text-[15px]">edit</span>
                  </button>
                  <button type="button" class="btn-delete-unit p-1 rounded hover:bg-rose-100 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-400 transition-colors cursor-pointer" data-unit-id="${uId}" title="Xóa Chương">
                    <span class="material-symbols-outlined text-[15px]">delete</span>
                  </button>
                ` : ''}
              </div>
            </div>

            <!-- Lessons List -->
            <div class="p-1.5 space-y-1 unit-lessons-dropzone" data-unit-id="${uId}">
              ${uLessons.length === 0 ? `
                <div class="py-2.5 px-3 text-center text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] italic border border-dashed border-transparent rounded-lg empty-lesson-placeholder">
                  Chưa có bài giảng trong chương này. Kéo thả bài vào đây hoặc tạo mới.
                </div>
              ` : uLessons.map((l, lIdx) => {
                const lId = l.lesson_id || l.id;
                const isSelected = String(lId) === String(activeLessonId);
                let badgeClass = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
                let badgeText = 'Nháp';
                if (l.status === 'PUBLISHED') {
                  badgeClass = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300';
                  badgeText = 'Đã xuất bản';
                } else if (l.status === 'MODIFIED') {
                  badgeClass = 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300';
                  badgeText = 'Đã sửa';
                }

                return `
                  <div
                    class="lesson-tree-item p-2 rounded-lg flex items-center justify-between gap-2 cursor-pointer transition-all ${isSelected ? 'bg-primary/10 border border-primary text-primary font-bold shadow-2xs' : 'hover:bg-[#FAF9F5] dark:hover:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] border border-transparent'}"
                    data-lesson-id="${lId}"
                    data-unit-id="${uId}"
                    data-lesson-idx="${lIdx}"
                    draggable="${!isLocked ? 'true' : 'false'}"
                  >
                    <div class="flex items-center gap-1.5 min-w-0 flex-1">
                      ${!isLocked ? `
                        <span class="material-symbols-outlined text-[15px] text-[#8F8E8A] dark:text-[#6D6C68] hover:text-primary cursor-grab active:cursor-grabbing shrink-0 drag-handle-lesson select-none" title="Kéo thả bài giảng">drag_indicator</span>
                      ` : ''}
                      <span class="material-symbols-outlined text-[16px] shrink-0 ${isSelected ? 'text-primary' : 'text-[#8F8E8A] dark:text-[#6D6C68]'}">
                        description
                      </span>
                      <div class="min-w-0 flex-1">
                        <div class="text-xs truncate lesson-item-title ${isSelected ? 'font-bold' : 'font-medium'}">${UI.escapeHtml(l.title)}</div>
                        <div class="flex items-center gap-1.5 text-[10px] text-[#8F8E8A] dark:text-[#6D6C68] font-normal">
                          <span class="px-1.5 py-0.2 rounded text-[9px] font-bold ${badgeClass}">${badgeText}</span>
                        </div>
                      </div>
                    </div>

                    ${!isLocked ? `
                      <div class="flex items-center gap-0.5 shrink-0" onclick="event.stopPropagation()">
                        <button type="button" class="btn-lesson-move-up p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-[#222120] transition-colors cursor-pointer" data-unit-id="${uId}" data-lesson-idx="${lIdx}" title="Di chuyển lên" ${lIdx === 0 ? 'disabled style="opacity: 0.2;"' : ''}>
                          <span class="material-symbols-outlined text-[14px]">expand_less</span>
                        </button>
                        <button type="button" class="btn-lesson-move-down p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-[#222120] transition-colors cursor-pointer" data-unit-id="${uId}" data-lesson-idx="${lIdx}" title="Di chuyển xuống" ${lIdx === uLessons.length - 1 ? 'disabled style="opacity: 0.2;"' : ''}>
                          <span class="material-symbols-outlined text-[14px]">expand_more</span>
                        </button>
                        <button type="button" class="btn-lesson-delete p-1 rounded hover:bg-rose-100 dark:hover:bg-rose-950/40 text-rose-500 hover:text-rose-700 transition-colors cursor-pointer" data-lesson-id="${lId}" title="Xóa bài giảng">
                          <span class="material-symbols-outlined text-[14px]">close</span>
                        </button>
                      </div>
                    ` : ''}
                  </div>
                `;
              }).join('')}

              ${!isLocked ? `
                <button
                  type="button"
                  class="btn-unit-quick-add-lesson w-full py-1.5 px-2.5 rounded-lg border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] hover:border-primary/50 text-[11px] font-semibold text-[#8F8E8A] hover:text-primary dark:text-[#9E9D99] flex items-center justify-center gap-1 transition-colors mt-1 cursor-pointer"
                  data-unit-id="${uId}"
                >
                  <span class="material-symbols-outlined text-[14px]">add</span>
                  <span>Thêm bài giảng</span>
                </button>
              ` : ''}

              <!-- Chapter Assessment Slot -->
              ${uExam ? (() => {
                const qCount = Number(uExam.questions_count ?? uExam.question_count ?? (uExam.questions ? uExam.questions.length : 0));
                const asmId = uExam.assessment_id || uExam.id;
                return `
                  <div class="mt-2 pt-2 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
                    <div class="p-2.5 rounded-xl border border-purple-200 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/20 flex flex-col gap-2">
                      <div class="flex items-center justify-between gap-1.5">
                        <div class="flex items-center gap-1.5 min-w-0">
                          <span class="w-6 h-6 rounded-lg bg-purple-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-[15px]">quiz</span>
                          </span>
                          <div class="min-w-0">
                            <div class="text-[11px] font-bold text-purple-950 dark:text-purple-200 truncate" title="${UI.escapeHtml(uExam.title)}">
                              ${UI.escapeHtml(uExam.title)}
                            </div>
                            <div class="text-[10px] text-purple-700/80 dark:text-purple-300/80">
                              Bài kiểm tra Chương • ${qCount} câu • ${uExam.time_limit_minutes || 45}p
                            </div>
                          </div>
                        </div>
                        ${UI.statusBadge(uExam.status)}
                      </div>
                      <div class="flex items-center justify-end gap-1.5 pt-1 border-t border-purple-100 dark:border-purple-900/40">
                        <button
                          type="button"
                          class="btn-asm-results px-2 py-1 rounded-md bg-white dark:bg-[#202020] hover:bg-purple-100 dark:hover:bg-purple-900/40 text-purple-800 dark:text-purple-200 text-[10px] font-bold transition-colors border border-purple-200 dark:border-purple-800 flex items-center gap-1 cursor-pointer"
                          data-asm-id="${asmId}"
                          data-asm-title="${UI.escapeHtml(uExam.title)}"
                        >
                          <span class="material-symbols-outlined text-[13px] text-primary">bar_chart</span>
                          <span>Bảng điểm</span>
                        </button>
                        <a
                          href="#/instructor/exams?course_id=${cId}&assessment_id=${asmId}"
                          class="px-2 py-1 rounded-md bg-purple-600 hover:bg-purple-700 text-white text-[10px] font-bold transition-colors flex items-center gap-1"
                        >
                          <span class="material-symbols-outlined text-[13px]">edit_note</span>
                          <span>Sửa đề</span>
                        </a>
                      </div>
                    </div>
                  </div>
                `;
              })() : (!isLocked ? `
                <div class="mt-2 pt-2 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
                  <a
                    href="#/instructor/exams?course_id=${cId}&unit_id=${uId}&unit_title=${encodeURIComponent(unit.title)}"
                    class="w-full py-1.5 px-2.5 rounded-lg border border-dashed border-purple-300 dark:border-purple-800 hover:border-purple-500 bg-purple-50/30 dark:bg-purple-950/20 text-[11px] font-bold text-purple-700 dark:text-purple-300 flex items-center justify-center gap-1 transition-colors cursor-pointer"
                  >
                    <span class="material-symbols-outlined text-[14px]">quiz</span>
                    <span>+ Tạo bài kiểm tra</span>
                  </a>
                </div>
              ` : '')}
            </div>
          </div>
        `;
      }).join('');

      // Dedicated Final Test Block at bottom of tree
      const finalExam = assessments.find(a => a.assessment_type === 'FINAL_EXAM' || /final|kết thúc môn|thi hết môn/i.test(a.title) || (!a.learning_unit_id && !(a.description && a.description.includes('unit_id:'))));
      if (finalExam) {
        const fCount = Number(finalExam.questions_count ?? finalExam.question_count ?? (finalExam.questions ? finalExam.questions.length : 0));
        const fId = finalExam.assessment_id || finalExam.id;
        treeContainer.innerHTML += `
          <div class="mt-3 p-3 rounded-xl border border-amber-300 dark:border-amber-700/80 bg-amber-50/40 dark:bg-amber-950/20 shadow-2xs space-y-2">
            <div class="flex items-center justify-between gap-1.5">
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-6 h-6 rounded-lg bg-amber-500 text-white font-black text-xs flex items-center justify-center shrink-0 shadow-xs">
                  <span class="material-symbols-outlined text-[16px]">military_tech</span>
                </span>
                <div class="min-w-0">
                  <div class="flex items-center gap-1.5">
                    <span class="text-[10px] font-black uppercase tracking-wider text-amber-800 dark:text-amber-300">Final Test</span>
                    ${UI.statusBadge(finalExam.status)}
                  </div>
                  <div class="text-xs font-bold text-slate-900 dark:text-white truncate" title="${UI.escapeHtml(finalExam.title)}">
                    ${UI.escapeHtml(finalExam.title)}
                  </div>
                </div>
              </div>
            </div>
            <div class="text-[10px] text-slate-600 dark:text-slate-300 flex items-center gap-2">
              <span>${fCount} câu hỏi</span>
              <span>•</span>
              <span>${finalExam.time_limit_minutes || 60} phút</span>
              <span>•</span>
              <span>${finalExam.total_points || 10}đ</span>
            </div>
            <div class="flex items-center justify-end gap-1.5 pt-1.5 border-t border-amber-200 dark:border-amber-900/60">
              <button
                type="button"
                class="btn-asm-results px-2 py-1 rounded-md bg-white dark:bg-[#202020] hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-900 dark:text-amber-200 text-[10px] font-bold transition-colors border border-amber-200 dark:border-amber-800 flex items-center gap-1 cursor-pointer"
                data-asm-id="${fId}"
                data-asm-title="${UI.escapeHtml(finalExam.title)}"
              >
                <span class="material-symbols-outlined text-[13px] text-primary">bar_chart</span>
                <span>Bảng điểm</span>
              </button>
              <a
                href="#/instructor/exams?course_id=${cId}&assessment_id=${fId}"
                class="px-2 py-1 rounded-md bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold transition-colors flex items-center gap-1"
              >
                <span class="material-symbols-outlined text-[13px]">edit_note</span>
                <span>Sửa đề thi</span>
              </a>
            </div>
          </div>
        `;
      } else if (!isLocked) {
        treeContainer.innerHTML += `
          <div class="mt-3 p-3 rounded-xl border border-dashed border-amber-300 dark:border-amber-800 bg-amber-50/20 dark:bg-amber-950/10 text-center space-y-1.5">
            <div class="flex items-center justify-center gap-1 text-amber-800 dark:text-amber-300 text-xs font-bold">
              <span class="material-symbols-outlined text-[16px]">military_tech</span>
              <span>Final Test (Bài thi kết thúc môn)</span>
            </div>
            <p class="text-[10px] text-slate-500 dark:text-slate-400">Đánh giá toàn khóa học khi sinh viên hoàn thành đủ bài học.</p>
            <a
              href="#/instructor/exams?course_id=${cId}&is_final=1"
              class="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-[11px] font-bold transition-all shadow-xs cursor-pointer mt-1"
            >
              <span class="material-symbols-outlined text-[13px]">add</span>
              <span>Thiết lập Final Test</span>
            </a>
          </div>
        `;
      }

      // Wire tree click listeners
      treeContainer.querySelectorAll('.lesson-tree-item').forEach(item => {
        item.addEventListener('click', () => {
          const lId = item.dataset.lessonId;
          const uId = item.dataset.unitId;
          selectLesson(lId, uId);
        });
      });

      treeContainer.querySelectorAll('.btn-rename-unit').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const uId = btn.dataset.unitId;
          const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(uId));
          if (!unit) return;
          const title = await UI.prompt('Đổi tên Chương', `Tên mới cho "${unit.title}":`, unit.title, 'Tên Chương bài học', 1, 'Lưu tên Chương', { maxLength: 200 });
          if (!title || !title.trim() || title.trim() === unit.title) return;
          try {
            const res = await ApiClient.updateLearningUnit(uId, { title: title.trim() });
            if (res && (res.pending_approval || res.status === 202)) {
              unit.pending_title = title.trim();
              renderTree();
              UI.showToast(res.message || 'Yêu cầu đổi tên Chương đã được gửi tới Quản trị viên để xét duyệt.', 'info');
            } else {
              unit.title = title.trim();
              renderTree();
              UI.showToast('Đã đổi tên Chương thành công!', 'success');
            }
          } catch (err) {
            UI.showToast(err.message || 'Lỗi đổi tên Chương.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-delete-unit').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const uId = btn.dataset.unitId;
          const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(uId));
          if (!unit) return;
          const conf = await UI.confirm(
            'Xóa Chương bài học',
            `Bạn có chắc chắn muốn xóa Chương "${unit.title}" và toàn bộ các bài giảng bên trong?`,
            'Xóa Chương'
          );
          if (!conf) return;
          try {
            const res = await ApiClient.deleteLearningUnit(uId);
            if (res && (res.pending_approval || res.status === 202)) {
              unit.pending_delete = true;
              renderTree();
              UI.showToast(res.message || 'Yêu cầu xóa Chương đã được gửi tới Quản trị viên để xét duyệt.', 'info');
            } else {
              currentUnits = currentUnits.filter(u => String(u.learning_unit_id || u.id) !== String(uId));
              if (String(activeUnitId) === String(uId)) {
                activeUnitId = currentUnits[0]?.learning_unit_id || currentUnits[0]?.id || null;
                activeLessonId = null;
              }
              renderTree();
              if (!activeLessonId) renderEmptyEditor();
              UI.showToast('Đã xóa Chương bài học.', 'success');
            }
          } catch (err) {
            UI.showToast(err.message || 'Lỗi xóa Chương.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-unit-move-up').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx <= 0) return;
          const snapshot = JSON.parse(JSON.stringify(currentUnits));
          const temp = currentUnits[idx];
          currentUnits[idx] = currentUnits[idx - 1];
          currentUnits[idx - 1] = temp;
          const orderedIds = currentUnits.map(u => u.learning_unit_id || u.id);
          try {
            const res = await ApiClient.reorderLearningUnits(cId, orderedIds);
            renderTree();
            if (res && (res.pending_approval || res.status === 202)) {
              UI.showToast(res.message || 'Yêu cầu thay đổi thứ tự Chương đã được gửi tới Quản trị viên để xét duyệt.', 'info');
            } else {
              UI.showToast('Đã thay đổi thứ tự Chương.', 'success');
            }
          } catch (err) {
            currentUnits = snapshot;
            renderTree();
            UI.showToast(err.message || 'Lỗi sắp xếp Chương.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-unit-move-down').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx >= currentUnits.length - 1) return;
          const snapshot = JSON.parse(JSON.stringify(currentUnits));
          const temp = currentUnits[idx];
          currentUnits[idx] = currentUnits[idx + 1];
          currentUnits[idx + 1] = temp;
          const orderedIds = currentUnits.map(u => u.learning_unit_id || u.id);
          try {
            const res = await ApiClient.reorderLearningUnits(cId, orderedIds);
            renderTree();
            if (res && (res.pending_approval || res.status === 202)) {
              UI.showToast(res.message || 'Yêu cầu thay đổi thứ tự Chương đã được gửi tới Quản trị viên để xét duyệt.', 'info');
            } else {
              UI.showToast('Đã thay đổi thứ tự Chương.', 'success');
            }
          } catch (err) {
            currentUnits = snapshot;
            renderTree();
            UI.showToast(err.message || 'Lỗi sắp xếp Chương.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-lesson-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const lId = btn.dataset.lessonId;
          const conf = await UI.confirm('Xóa bài giảng', 'Xác nhận xóa bài giảng này? Nội dung sẽ bị xóa khỏi giáo trình.', 'Xóa bài giảng');
          if (!conf) return;
          try {
            const res = await ApiClient.deleteLesson(cId, lId);
            if (res && res.is_staged_delete) {
              currentUnits.forEach(u => {
                const targetL = u.lessons?.find(l => String(l.lesson_id || l.id) === String(lId));
                if (targetL) targetL.is_staged_delete = true;
              });
              renderTree();
              UI.showToast(res.message || 'Đã đánh dấu xóa bài giảng trong bản nháp cập nhật.', 'info');
              return;
            }
            currentUnits.forEach(u => {
              if (u.lessons) u.lessons = u.lessons.filter(l => String(l.lesson_id || l.id) !== String(lId));
            });
            if (String(activeLessonId) === String(lId)) {
              activeLessonId = null;
              renderEmptyEditor();
            }
            renderTree();
            UI.showToast('Đã xóa bài giảng thành công.', 'success');
          } catch (err) {
            UI.showToast(err.message || 'Lỗi xóa bài giảng.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-lesson-move-up').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const uId = btn.dataset.unitId;
          const lIdx = parseInt(btn.dataset.lessonIdx, 10);
          const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(uId));
          if (!unit || !unit.lessons || lIdx <= 0) return;
          const snapshot = JSON.parse(JSON.stringify(currentUnits));
          const temp = unit.lessons[lIdx];
          unit.lessons[lIdx] = unit.lessons[lIdx - 1];
          unit.lessons[lIdx - 1] = temp;
          const orderedIds = unit.lessons.map(l => l.lesson_id || l.id);
          try {
            await ApiClient.reorderLessons(cId, orderedIds);
            renderTree();
            UI.showToast('Đã di chuyển bài giảng lên.', 'success');
          } catch (err) {
            currentUnits = snapshot;
            renderTree();
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-lesson-move-down').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const uId = btn.dataset.unitId;
          const lIdx = parseInt(btn.dataset.lessonIdx, 10);
          const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(uId));
          if (!unit || !unit.lessons || lIdx >= unit.lessons.length - 1) return;
          const snapshot = JSON.parse(JSON.stringify(currentUnits));
          const temp = unit.lessons[lIdx];
          unit.lessons[lIdx] = unit.lessons[lIdx + 1];
          unit.lessons[lIdx + 1] = temp;
          const orderedIds = unit.lessons.map(l => l.lesson_id || l.id);
          try {
            await ApiClient.reorderLessons(cId, orderedIds);
            renderTree();
            UI.showToast('Đã di chuyển bài giảng xuống.', 'success');
          } catch (err) {
            currentUnits = snapshot;
            renderTree();
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
          }
        });
      });

      treeContainer.querySelectorAll('.btn-unit-quick-add-lesson').forEach(btn => {
        btn.addEventListener('click', () => {
          const uId = btn.dataset.unitId;
          handleCreateLessonInUnit(uId);
        });
      });

      // Native HTML5 Drag and Drop for Chapters & Lessons
      if (!isLocked) {
        setupTreeDragAndDrop();
      }
    };

    // Setup Drag and Drop listeners for units and lessons
    function setupTreeDragAndDrop() {
      // 1. Chapter Drag & Drop
      treeContainer.querySelectorAll('.unit-tree-node').forEach(unitNode => {
        unitNode.addEventListener('dragstart', (e) => {
          // If dragging initiated from within a lesson, let the lesson handler deal with it
          if (e.target.closest('.lesson-tree-item')) return;
          const unitIdx = parseInt(unitNode.dataset.unitIdx, 10);
          const unitId = unitNode.dataset.unitId;
          e.dataTransfer.setData('application/json', JSON.stringify({ type: 'unit', unitIdx, unitId }));
          e.dataTransfer.effectAllowed = 'move';
          unitNode.classList.add('opacity-50', 'ring-2', 'ring-primary');
        });

        unitNode.addEventListener('dragend', () => {
          unitNode.classList.remove('opacity-50', 'ring-2', 'ring-primary');
          treeContainer.querySelectorAll('.unit-tree-node').forEach(n => {
            n.classList.remove('border-primary', 'bg-primary/5', 'ring-2');
          });
        });

        unitNode.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
        });

        unitNode.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          unitNode.classList.remove('border-primary', 'bg-primary/5', 'ring-2');

          let payload = null;
          try {
            payload = JSON.parse(e.dataTransfer.getData('application/json'));
          } catch {
            return;
          }
          if (!payload) return;

          // Dropping a chapter onto another chapter
          if (payload.type === 'unit') {
            const fromIdx = payload.unitIdx;
            const toIdx = parseInt(unitNode.dataset.unitIdx, 10);
            if (isNaN(fromIdx) || isNaN(toIdx) || fromIdx === toIdx) return;
            const snapshot = JSON.parse(JSON.stringify(currentUnits));
            const [movedUnit] = currentUnits.splice(fromIdx, 1);
            currentUnits.splice(toIdx, 0, movedUnit);
            const orderedIds = currentUnits.map(u => u.learning_unit_id || u.id);
            try {
              await ApiClient.reorderLearningUnits(cId, orderedIds);
              renderTree();
              UI.showToast('Đã di chuyển vị trí Chương.', 'success');
            } catch (err) {
              currentUnits = snapshot;
              renderTree();
              UI.showToast(err.message || 'Lỗi sắp xếp Chương.', 'error');
            }
            return;
          }

          // Dropping a lesson directly onto a chapter container
          if (payload.type === 'lesson') {
            const targetUnitId = unitNode.dataset.unitId;
            const srcUnitId = payload.sourceUnitId;
            const lessonId = payload.lessonId;
            if (String(targetUnitId) === String(srcUnitId)) return;

            const srcUnit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(srcUnitId));
            const dstUnit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(targetUnitId));
            if (!srcUnit || !dstUnit) return;

            const movedIdx = (srcUnit.lessons || []).findIndex(l => String(l.lesson_id || l.id) === String(lessonId));
            if (movedIdx === -1) return;

            const snapshot = JSON.parse(JSON.stringify(currentUnits));
            const [movedLesson] = srcUnit.lessons.splice(movedIdx, 1);
            movedLesson.learning_unit_id = targetUnitId;
            if (!dstUnit.lessons) dstUnit.lessons = [];
            dstUnit.lessons.push(movedLesson);

            try {
              await ApiClient.updateLesson(lessonId, { learning_unit_id: targetUnitId });
              renderTree();
              UI.showToast('Đã chuyển bài giảng vào Chương mới.', 'success');
            } catch (err) {
              currentUnits = snapshot;
              renderTree();
              UI.showToast(err.message || 'Lỗi chuyển bài giảng sang Chương mới.', 'error');
            }
          }
        });
      });

      // 2. Lesson Drag & Drop
      treeContainer.querySelectorAll('.lesson-tree-item').forEach(lessonItem => {
        lessonItem.addEventListener('dragstart', (e) => {
          e.stopPropagation();
          const lessonId = lessonItem.dataset.lessonId;
          const unitId = lessonItem.dataset.unitId;
          const lessonIdx = parseInt(lessonItem.dataset.lessonIdx, 10);
          e.dataTransfer.setData('application/json', JSON.stringify({
            type: 'lesson',
            lessonId,
            sourceUnitId: unitId,
            lessonIdx
          }));
          e.dataTransfer.effectAllowed = 'move';
          lessonItem.classList.add('opacity-40', 'border-primary');
        });

        lessonItem.addEventListener('dragend', () => {
          lessonItem.classList.remove('opacity-40', 'border-primary');
          treeContainer.querySelectorAll('.lesson-tree-item').forEach(l => {
            l.classList.remove('border-t-2', 'border-b-2', 'border-primary');
          });
        });

        lessonItem.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.stopPropagation();
          e.dataTransfer.dropEffect = 'move';
          lessonItem.classList.add('border-b-2', 'border-primary');
        });

        lessonItem.addEventListener('dragleave', () => {
          lessonItem.classList.remove('border-b-2', 'border-primary');
        });

        lessonItem.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          lessonItem.classList.remove('border-b-2', 'border-primary');

          let payload = null;
          try {
            payload = JSON.parse(e.dataTransfer.getData('application/json'));
          } catch {
            return;
          }
          if (!payload || payload.type !== 'lesson') return;

          const targetUnitId = lessonItem.dataset.unitId;
          const targetLessonIdx = parseInt(lessonItem.dataset.lessonIdx, 10);
          const srcUnitId = payload.sourceUnitId;
          const srcLessonIdx = payload.lessonIdx;
          const srcLessonId = payload.lessonId;

          // Reordering within the SAME unit
          if (String(srcUnitId) === String(targetUnitId)) {
            const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(srcUnitId));
            if (!unit || !unit.lessons || srcLessonIdx === targetLessonIdx) return;
            const snapshot = JSON.parse(JSON.stringify(currentUnits));
            const [movedLesson] = unit.lessons.splice(srcLessonIdx, 1);
            unit.lessons.splice(targetLessonIdx, 0, movedLesson);
            const orderedIds = unit.lessons.map(l => l.lesson_id || l.id);
            try {
              await ApiClient.reorderLessons(cId, orderedIds);
              renderTree();
              UI.showToast('Đã di chuyển thứ tự bài giảng.', 'success');
            } catch (err) {
              currentUnits = snapshot;
              renderTree();
              UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
            }
            return;
          }

          // Moving to a DIFFERENT unit at a specific index
          const srcUnit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(srcUnitId));
          const dstUnit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(targetUnitId));
          if (!srcUnit || !dstUnit) return;

          const movedIdx = (srcUnit.lessons || []).findIndex(l => String(l.lesson_id || l.id) === String(srcLessonId));
          if (movedIdx === -1) return;

          const snapshot = JSON.parse(JSON.stringify(currentUnits));
          const [movedLesson] = srcUnit.lessons.splice(movedIdx, 1);
          movedLesson.learning_unit_id = targetUnitId;
          if (!dstUnit.lessons) dstUnit.lessons = [];
          dstUnit.lessons.splice(targetLessonIdx, 0, movedLesson);

          try {
            await ApiClient.updateLesson(srcLessonId, { learning_unit_id: targetUnitId });
            const orderedIds = dstUnit.lessons.map(l => l.lesson_id || l.id);
            await ApiClient.reorderLessons(cId, orderedIds);
            renderTree();
            UI.showToast('Đã chuyển bài giảng sang Chương mới.', 'success');
          } catch (err) {
            currentUnits = snapshot;
            renderTree();
            UI.showToast(err.message || 'Lỗi chuyển bài giảng sang Chương mới.', 'error');
          }
        });
      });
    }

    // Handler to create a new Learning Unit
    const handleAddUnit = async () => {
      if (isLocked) {
        UI.showToast('Khóa học đang chờ duyệt. Không thể thêm chương mới.', 'warning');
        return;
      }
      const title = await UI.prompt('Thêm Chương mới', 'Đặt tên cho Chương bài học:', '', 'Ví dụ: Chương 1: Giới thiệu căn bản', 1, 'Tạo Chương', { maxLength: 200 });
      if (!title || !title.trim()) return;
      try {
        const created = await ApiClient.createLearningUnit(cId, { title: title.trim() });
        if (created && (created.pending_approval || created.status === 202)) {
          UI.showToast(created.message || 'Yêu cầu tạo Chương mới đã gửi Quản trị viên để xét duyệt.', 'info');
          return;
        }
        const newUnit = {
          learning_unit_id: created.learning_unit_id || created.id,
          id: created.learning_unit_id || created.id,
          title: title.trim(),
          lessons: []
        };
        currentUnits.push(newUnit);
        if (!activeUnitId) activeUnitId = newUnit.id;
        renderTree();
        UI.showToast('Đã tạo Chương mới thành công!', 'success');
      } catch (err) {
        UI.showToast(err.message || 'Lỗi tạo Chương mới.', 'error');
      }
    };

    // Handler to create a new lesson in a specific unit
    const handleCreateLessonInUnit = async (targetUnitId) => {
      if (isLocked) {
        UI.showToast('Khóa học đang chờ duyệt. Không thể thêm bài giảng mới.', 'warning');
        return;
      }
      const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(targetUnitId));
      if (!unit) return;
      const nextIdx = (unit.lessons?.length || 0) + 1;
      const defaultTitle = `Bài ${nextIdx}: Bài giảng mới`;
      const title = await UI.prompt('Thêm bài giảng mới', `Đặt tiêu đề bài giảng trong "${unit.title}":`, defaultTitle, 'Tiêu đề bài giảng', 1, 'Tạo bài giảng', { maxLength: 200 });
      if (!title || !title.trim()) return;

      try {
        const created = await ApiClient.createLesson(cId, {
          title: title.trim(),
          learning_unit_id: targetUnitId,
          markdown_content: `# ${title.trim()}\n\nNội dung bài học.`,
          status: 'DRAFT'
        });
        const lId = created.lesson_id || created.id;
        const newLessonObj = {
          lesson_id: lId,
          id: lId,
          title: title.trim(),
          status: 'DRAFT',
          learning_unit_id: targetUnitId
        };
        if (!unit.lessons) unit.lessons = [];
        unit.lessons.push(newLessonObj);
        await selectLesson(lId, targetUnitId);
        UI.showToast('Đã tạo bài giảng mới! Thầy/Cô hãy soạn nội dung ở cột bên phải.', 'success');
      } catch (err) {
        UI.showToast(err.message || 'Lỗi tạo bài giảng mới.', 'error');
      }
    };

    // Global add lesson button (uses active unit or first unit)
    const handleAddLessonGlobal = async () => {
      if (currentUnits.length === 0) {
        UI.showToast('Vui lòng tạo ít nhất một Chương trước khi thêm bài giảng.', 'info');
        await handleAddUnit();
        return;
      }
      const targetUnitId = activeUnitId || currentUnits[0].learning_unit_id || currentUnits[0].id;
      await handleCreateLessonInUnit(targetUnitId);
    };

    // Render empty state for editor
    const renderEmptyEditor = () => {
      editorContainer.innerHTML = `
        <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-12 text-center shadow-xs space-y-4">
          <div class="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
            <span class="material-symbols-outlined text-3xl">edit_document</span>
          </div>
          <div class="space-y-1">
            <h3 class="text-base font-bold text-[#222120] dark:text-[#EDEDEB]">Chưa chọn bài giảng</h3>
            <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] max-w-md mx-auto">
              Vui lòng chọn một bài giảng ở cột Cấu trúc bên trái để xem và chỉnh sửa, hoặc bấm nút bên dưới để tạo bài giảng mới.
            </p>
          </div>
          <div class="pt-2">
            <button
              type="button"
              id="btn-editor-create-lesson"
              class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1.5 cursor-pointer ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}"
              ${isLocked ? 'disabled' : ''}
            >
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Thêm bài giảng mới</span>
            </button>
          </div>
        </div>
      `;
      editorContainer.querySelector('#btn-editor-create-lesson')?.addEventListener('click', handleAddLessonGlobal);
    };

    let selectLessonGen = 0;
    let isEditorDirty = false;

    // Select and load lesson into editor
    const selectLesson = async (lessonId, unitId) => {
      if (activeLessonId && String(activeLessonId) !== String(lessonId) && isEditorDirty) {
        const leave = await UI.confirm(
          'Thay đổi chưa lưu',
          'Bài giảng hiện tại có thay đổi chưa lưu. Bạn có muốn bỏ qua và chuyển sang bài học khác?',
          'Bỏ thay đổi'
        );
        if (!leave) return;
      }
      isEditorDirty = false;
      const currentGen = ++selectLessonGen;
      activeLessonId = lessonId;
      activeUnitId = unitId;
      renderTree();

      editorContainer.innerHTML = `
        <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-12 text-center shadow-xs">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">Đang nạp dữ liệu bài giảng...</p>
        </div>
      `;

      try {
        const lessonData = await ApiClient.getLesson(lessonId);
        if (currentGen !== selectLessonGen || String(activeLessonId) !== String(lessonId)) {
          return;
        }
        if (!lessonData) {
          renderEmptyEditor();
          return;
        }

        activeLessonMeta = {
          title: lessonData.title || 'Bài giảng',
          summary: lessonData.summary || '',
          status: lessonData.status || 'DRAFT'
        };
        activeBlocks = InstructorView.parseLessonToBlocks(lessonData);
        renderEditor();
        isEditorDirty = false;
      } catch (err) {
        if (currentGen !== selectLessonGen || String(activeLessonId) !== String(lessonId)) {
          return;
        }
        editorContainer.innerHTML = `
          <div class="bg-white dark:bg-[#202020] border border-rose-300 dark:border-rose-900 rounded-2xl p-8 text-center space-y-3">
            <span class="material-symbols-outlined text-3xl text-rose-500">error</span>
            <p class="text-xs font-bold text-rose-600">Không thể tải nội dung bài giảng: ${UI.escapeHtml(err.message || '')}</p>
          </div>
        `;
      }
    };

    // Render single block card HTML
    const renderBlockHtml = (block, idx) => {
      const bId = block.id;
      let typeLabel = 'Nội dung bài học';
      let typeIcon = 'subject';
      let iconColor = 'text-primary bg-primary/10';

      if (block.type === 'video') {
        typeLabel = 'Video bài giảng';
        typeIcon = 'play_circle';
        iconColor = 'text-rose-600 bg-rose-50 dark:bg-rose-950/40';
      } else if (block.type === 'document') {
        typeLabel = 'Tài liệu đính kèm';
        typeIcon = 'description';
        iconColor = 'text-blue-600 bg-blue-50 dark:bg-blue-950/40';
      } else if (block.type === 'quiz') {
        typeLabel = 'Câu hỏi tương tác';
        typeIcon = 'quiz';
        iconColor = 'text-purple-600 bg-purple-50 dark:bg-purple-950/40';
      }

      let bodyHtml = '';
      if (block.type === 'text') {
        bodyHtml = `
          <div class="space-y-0 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] overflow-hidden bg-white dark:bg-[#1E1E1E]">
            <!-- Microsoft Word Standard Ribbon Toolbar (2 Rows) -->
            <div class="word-ribbon-toolbar bg-[#F8F9FA] dark:bg-[#252526] border-b border-[#E8E6DF] dark:border-[#2E2D2B] p-2 space-y-1.5 select-none" data-block-id="${bId}">
              <!-- Row 1: Clipboard, Font family, Font size, Scale, Case, Clear format, Styles -->
              <div class="flex flex-wrap items-center gap-1.5 text-xs text-[#222120] dark:text-[#EDEDEB]">
                <!-- Group 1: Clipboard -->
                <div class="flex items-center gap-0.5 pr-1.5 border-r border-[#E8E6DF] dark:border-[#3E3D3A]" title="Clipboard (Bộ nhớ tạm)">
                  <button type="button" class="btn-word-paste p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] transition-colors cursor-pointer flex items-center gap-1 text-[11px] font-medium" title="Dán (Paste)">
                    <span class="material-symbols-outlined text-[16px] text-primary">content_paste</span>
                    <span class="hidden sm:inline">Dán</span>
                  </button>
                  <button type="button" class="btn-word-cut p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] transition-colors cursor-pointer" title="Cắt (Cut)">
                    <span class="material-symbols-outlined text-[16px]">content_cut</span>
                  </button>
                  <button type="button" class="btn-word-copy p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] transition-colors cursor-pointer" title="Sao chép (Copy)">
                    <span class="material-symbols-outlined text-[16px]">content_copy</span>
                  </button>
                  <button type="button" class="btn-word-format-painter p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] transition-colors cursor-pointer" title="Sao chép định dạng (Format Painter)">
                    <span class="material-symbols-outlined text-[16px] text-amber-600">format_paint</span>
                  </button>
                </div>

                <!-- Group 2: Font Family & Size -->
                <div class="flex items-center gap-1 pr-1.5 border-r border-[#E8E6DF] dark:border-[#3E3D3A]">
                  <select class="word-font-family px-2 py-1 rounded border border-[#CED4DA] dark:border-[#4E4D4A] bg-white dark:bg-[#1E1E1E] text-xs outline-none focus:border-primary cursor-pointer" title="Phông chữ (Font)">
                    <option value="Aptos, sans-serif" selected>Aptos (Body)</option>
                    <option value="Inter, sans-serif">Inter</option>
                    <option value="Arial, sans-serif">Arial</option>
                    <option value="'Times New Roman', serif">Times New Roman</option>
                    <option value="'Segoe UI', sans-serif">Segoe UI</option>
                    <option value="Roboto, sans-serif">Roboto</option>
                    <option value="Tahoma, sans-serif">Tahoma</option>
                    <option value="'Courier New', monospace">Courier New</option>
                  </select>

                  <select class="word-font-size px-2 py-1 rounded border border-[#CED4DA] dark:border-[#4E4D4A] bg-white dark:bg-[#1E1E1E] text-xs outline-none focus:border-primary cursor-pointer w-14" title="Cỡ chữ (Font Size)">
                    <option value="1">10</option>
                    <option value="2">11</option>
                    <option value="3" selected>12</option>
                    <option value="4">14</option>
                    <option value="5">18</option>
                    <option value="6">24</option>
                    <option value="7">36</option>
                  </select>

                  <button type="button" class="btn-word-grow-font p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Tăng cỡ chữ (Grow Font)">
                    <span class="material-symbols-outlined text-[16px]">format_size</span>
                  </button>
                  <button type="button" class="btn-word-shrink-font p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Giảm cỡ chữ (Shrink Font)">
                    <span class="material-symbols-outlined text-[14px]">text_decrease</span>
                  </button>
                  <button type="button" class="btn-word-change-case p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer font-bold text-[12px]" title="Đổi kiểu chữ hoa/thường (Change Case)">
                    Aa
                  </button>
                  <button type="button" class="btn-word-clear-formatting p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Xóa toàn bộ định dạng chữ (Clear All Formatting)">
                    <span class="material-symbols-outlined text-[16px] text-rose-500">format_clear</span>
                  </button>
                </div>

                <!-- Group 3: Styles (Kiểu văn bản) -->
                <div class="flex items-center gap-1">
                  <span class="text-[10px] uppercase font-bold text-[#8F8E8A] hidden md:inline">Styles:</span>
                  <select class="word-styles-select px-2 py-1 rounded border border-[#CED4DA] dark:border-[#4E4D4A] bg-white dark:bg-[#1E1E1E] text-xs outline-none focus:border-primary cursor-pointer" title="Kiểu định dạng nhanh">
                    <option value="p">Normal (Văn bản thông thường)</option>
                    <option value="h1">Heading 1 (Tiêu đề 1)</option>
                    <option value="h2">Heading 2 (Tiêu đề 2)</option>
                    <option value="h3">Heading 3 (Tiêu đề 3)</option>
                    <option value="h4">Title (Tiêu đề chính)</option>
                    <option value="blockquote">Subtitle (Trích dẫn / Phụ)</option>
                  </select>
                </div>
              </div>

              <!-- Row 2: Font style (B, I, U, S, sub, sup, color, highlight), Paragraph, Editing -->
              <div class="flex flex-wrap items-center gap-1.5 pt-1 border-t border-[#E8E6DF]/60 dark:border-[#3E3D3A]/60 text-xs text-[#222120] dark:text-[#EDEDEB]">
                <!-- Font decorations -->
                <div class="flex items-center gap-0.5 pr-1.5 border-r border-[#E8E6DF] dark:border-[#3E3D3A]">
                  <button type="button" class="btn-word-bold p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer font-bold text-[13px] w-7 text-center" title="In đậm (Bold - Ctrl+B)"><b>B</b></button>
                  <button type="button" class="btn-word-italic p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer italic text-[13px] w-7 text-center font-serif" title="In nghiêng (Italic - Ctrl+I)"><i>I</i></button>
                  <button type="button" class="btn-word-underline p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer underline text-[13px] w-7 text-center" title="Gạch chân (Underline - Ctrl+U)"><u>U</u></button>
                  <button type="button" class="btn-word-strike p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer line-through text-[13px] w-7 text-center" title="Gạch ngang (Strikethrough)">S</button>
                  <button type="button" class="btn-word-subscript p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer text-[11px]" title="Chỉ số dưới (Subscript - H₂O)">x₂</button>
                  <button type="button" class="btn-word-superscript p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer text-[11px]" title="Chỉ số trên (Superscript - x²)">x²</button>

                  <!-- Highlight & Font Color -->
                  <div class="flex items-center gap-1 pl-1">
                    <label class="p-1 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer flex items-center" title="Tô màu nền chữ (Highlight Color)">
                      <span class="material-symbols-outlined text-[16px] text-yellow-500">border_color</span>
                      <input type="color" class="word-highlight-color sr-only" value="#ffff00" />
                    </label>
                    <label class="p-1 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer flex items-center" title="Màu chữ (Font Color)">
                      <span class="material-symbols-outlined text-[16px] text-rose-500">format_color_text</span>
                      <input type="color" class="word-font-color sr-only" value="#111827" />
                    </label>
                  </div>
                </div>

                <!-- Paragraph formatting -->
                <div class="flex items-center gap-0.5 pr-1.5 border-r border-[#E8E6DF] dark:border-[#3E3D3A]">
                  <button type="button" class="btn-word-bullets p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Danh sách dấu đầu dòng (Bullets)">
                    <span class="material-symbols-outlined text-[16px]">format_list_bulleted</span>
                  </button>
                  <button type="button" class="btn-word-numbering p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Danh sách đánh số (Numbering)">
                    <span class="material-symbols-outlined text-[16px]">format_list_numbered</span>
                  </button>
                  <button type="button" class="btn-word-decrease-indent p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Giảm thụt lề (Decrease Indent)">
                    <span class="material-symbols-outlined text-[16px]">format_indent_decrease</span>
                  </button>
                  <button type="button" class="btn-word-increase-indent p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Tăng thụt lề (Increase Indent)">
                    <span class="material-symbols-outlined text-[16px]">format_indent_increase</span>
                  </button>
                  <button type="button" class="btn-word-align-left p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Căn trái (Align Left)">
                    <span class="material-symbols-outlined text-[16px]">format_align_left</span>
                  </button>
                  <button type="button" class="btn-word-align-center p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Căn giữa (Center)">
                    <span class="material-symbols-outlined text-[16px]">format_align_center</span>
                  </button>
                  <button type="button" class="btn-word-align-right p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Căn phải (Align Right)">
                    <span class="material-symbols-outlined text-[16px]">format_align_right</span>
                  </button>
                  <button type="button" class="btn-word-align-justify p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Căn đều hai bên (Justify)">
                    <span class="material-symbols-outlined text-[16px]">format_align_justify</span>
                  </button>
                  <button type="button" class="btn-word-line-spacing p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer" title="Giãn dòng đoạn văn (Line Spacing)">
                    <span class="material-symbols-outlined text-[16px]">format_line_spacing</span>
                  </button>
                </div>

                <!-- Editing (Find, Replace, Select All) -->
                <div class="flex items-center gap-0.5">
                  <button type="button" class="btn-word-find p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer flex items-center gap-0.5 text-[11px]" title="Tìm kiếm (Find)">
                    <span class="material-symbols-outlined text-[15px]">search</span>
                    <span class="hidden lg:inline">Find</span>
                  </button>
                  <button type="button" class="btn-word-replace p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer flex items-center gap-0.5 text-[11px]" title="Thay thế (Replace)">
                    <span class="material-symbols-outlined text-[15px]">find_replace</span>
                    <span class="hidden lg:inline">Replace</span>
                  </button>
                  <button type="button" class="btn-word-select-all p-1.5 rounded hover:bg-[#E9ECEF] dark:hover:bg-[#333333] cursor-pointer flex items-center gap-0.5 text-[11px]" title="Chọn tất cả (Select All)">
                    <span class="material-symbols-outlined text-[15px]">select_all</span>
                    <span class="hidden lg:inline">Select</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- ContentEditable Canvas (Microsoft Word Document Area) -->
            <div
              class="word-editor-canvas min-h-[260px] p-4 sm:p-5 bg-white dark:bg-[#1E1E1E] text-xs sm:text-sm text-[#222120] dark:text-[#EDEDEB] focus:outline-none font-sans leading-relaxed overflow-y-auto max-h-[550px] space-y-2"
              contenteditable="${!isLocked}"
              data-placeholder="Nhập nội dung bài học..."
            >${block.content || '<p>Nhập nội dung bài học tại đây...</p>'}</div>
            <textarea class="block-text-textarea hidden sr-only">${UI.escapeHtml(block.content || '')}</textarea>
          </div>
        `;
      } else if (block.type === 'video') {
        const vFiles = Array.isArray(block.files) ? block.files : [];
        let ytEmbed = '';
        if (block.url && (block.url.includes('youtube.com') || block.url.includes('youtu.be') || block.url.includes('vimeo.com'))) {
          let videoId = '';
          const match = block.url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
          if (match) videoId = match[1];
          if (videoId) {
            ytEmbed = `
              <div class="mt-2.5 aspect-video rounded-xl overflow-hidden bg-black max-w-lg border border-[#E8E6DF] dark:border-[#2E2D2B]">
                <iframe class="w-full h-full" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>
              </div>
            `;
          }
        }
        bodyHtml = `
          <div class="space-y-4">
            <!-- 1. Thanh ngang trên: Nhập đường dẫn YouTube / Vimeo -->
            <div class="p-3.5 bg-white dark:bg-[#1E1E1E] rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] space-y-2">
              <label class="flex items-center gap-1.5 text-xs font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                <span class="material-symbols-outlined text-[16px] text-rose-500">smart_display</span>
                <span>Đường dẫn YouTube / Vimeo bài giảng:</span>
              </label>
              <div class="flex items-center gap-2">
                <input
                  type="url"
                  class="block-video-url flex-1 px-3.5 py-2 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#252525] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value="${UI.escapeHtml(block.url || '')}"
                  ${isLocked ? 'disabled' : ''}
                />
              </div>
              ${ytEmbed}
            </div>

            <!-- 2. Khu vực lớn bên dưới: Tải video từ máy tính (< 1 GB) -->
            <div class="space-y-3">
              <div class="flex items-center justify-between text-xs font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                <span class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px] text-primary">upload_file</span>
                  <span>Tệp video tải lên từ máy tính (&lt; 1 GB):</span>
                </span>
                <span class="text-[11px] font-semibold text-[#8F8E8A] dark:text-[#6D6C68]">Tối đa 2 video / bài học</span>
              </div>

              <!-- Danh sách video đã tải lên trong bài -->
              ${vFiles.length > 0 ? `
                <div class="space-y-3">
                  ${vFiles.map((vf, vfIdx) => {
                    const vfSize = vf.file_size_bytes ? `${(vf.file_size_bytes / (1024 * 1024)).toFixed(1)} MB` : '';
                    return `
                      <div class="p-3.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#1E1E1E] space-y-2.5">
                        <div class="flex items-center justify-between gap-3 text-xs">
                          <div class="flex items-center gap-2 min-w-0">
                            <span class="w-7 h-7 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                              <span class="material-symbols-outlined text-[16px]">videocam</span>
                            </span>
                            <span class="font-bold text-[#222120] dark:text-[#EDEDEB] truncate">${UI.escapeHtml(vf.filename || vf.title || 'Video bài giảng')}</span>
                            ${vfSize ? `<span class="text-[10px] text-[#8F8E8A] font-mono">(${vfSize})</span>` : ''}
                          </div>
                          ${!isLocked ? `
                            <button
                              type="button"
                              class="btn-delete-video-file p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                              data-file-idx="${vfIdx}"
                              data-resource-id="${vf.resource_id || ''}"
                              title="Xóa video này"
                            >
                              <span class="material-symbols-outlined text-[16px]">delete</span>
                            </button>
                          ` : ''}
                        </div>
                        ${vf.file_url ? `
                          <div class="max-w-lg aspect-video rounded-xl overflow-hidden bg-black border border-[#E8E6DF] dark:border-[#2E2D2B]">
                            <video src="${UI.escapeHtml(vf.file_url)}" controls class="w-full h-full object-contain"></video>
                          </div>
                        ` : ''}
                      </div>
                    `;
                  }).join('')}
                </div>
              ` : ''}

              <!-- Vùng kéo thả tệp video (Drag & Drop Zone) -->
              ${!isLocked ? `
                <div class="video-dropzone border-2 border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] hover:border-primary/60 dark:hover:border-primary/60 rounded-2xl p-5 text-center cursor-pointer transition-all bg-[#FAF9F5] dark:bg-[#1E1E1E] group">
                  <input
                    type="file"
                    class="block-video-file-input sr-only"
                    accept="video/mp4,video/webm,video/quicktime,video/x-matroska,.mp4,.webm,.mov,.mkv"
                    multiple
                  />
                  <div class="w-10 h-10 mx-auto rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                    <span class="material-symbols-outlined text-[22px]">cloud_upload</span>
                  </div>
                  <p class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Kéo & thả video vào đây hoặc bấm để chọn tệp từ máy tính</p>
                  <p class="text-[11px] text-[#8F8E8A] dark:text-[#9E9D99] mt-0.5">Hỗ trợ MP4, WebM, MOV, MKV (Dung lượng &lt; 1 GB, có thể chọn nhiều tệp cùng lúc)</p>
                </div>

                <!-- Thanh tiến trình tải video lên -->
                <div class="video-upload-progress hidden p-3 bg-white dark:bg-[#202020] rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] space-y-1.5">
                  <div class="flex items-center justify-between text-xs font-semibold text-[#222120] dark:text-[#EDEDEB]">
                    <span class="progress-file-name truncate">Đang tải video lên máy chủ...</span>
                    <span class="progress-file-percent text-primary font-mono">0%</span>
                  </div>
                  <div class="w-full bg-[#E8E6DF] dark:bg-[#3E3D3A] h-2 rounded-full overflow-hidden">
                    <div class="progress-bar-inner bg-primary h-full transition-all duration-150" style="width: 0%"></div>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        `;
      } else if (block.type === 'document') {
        const files = Array.isArray(block.files) ? block.files : [];
        bodyHtml = `
          <div class="space-y-3">
            <div class="space-y-2">
              ${files.length === 0 ? `
                <div class="p-3 text-center text-xs text-[#8F8E8A] italic bg-[#FAF9F5] dark:bg-[#1E1E1E] rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B]">
                  Chưa có tệp đính kèm nào.
                </div>
              ` : files.map((f, fIdx) => `
                <div class="p-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#1E1E1E] flex items-center justify-between gap-3 text-xs">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="material-symbols-outlined text-[18px] text-primary shrink-0">attachment</span>
                    <span class="font-semibold text-[#222120] dark:text-[#EDEDEB] truncate">${UI.escapeHtml(f.filename || f.title || 'Tài liệu')}</span>
                    ${f.file_size_bytes ? `<span class="text-[10px] text-[#8F8E8A]">(${Math.round(f.file_size_bytes / 1024)} KB)</span>` : ''}
                  </div>
                  <div class="flex items-center gap-1 shrink-0">
                    ${f.file_url ? `
                      <a href="${UI.escapeHtml(f.file_url)}" target="_blank" class="p-1 rounded text-primary hover:bg-primary/10 transition-colors" title="Tải xuống / Xem">
                        <span class="material-symbols-outlined text-[16px]">download</span>
                      </a>
                    ` : ''}
                    ${!isLocked ? `
                      <button type="button" class="btn-delete-doc-file p-1 rounded text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer" data-file-idx="${fIdx}" data-resource-id="${f.resource_id || ''}" title="Xóa tài liệu">
                        <span class="material-symbols-outlined text-[16px]">close</span>
                      </button>
                    ` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
            ${!isLocked ? `
              <label class="inline-flex cursor-pointer items-center gap-2 px-3.5 py-2 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] hover:border-primary bg-white dark:bg-[#1E1E1E] text-xs font-bold text-[#222120] dark:text-[#EDEDEB] transition-colors shadow-2xs">
                <span class="material-symbols-outlined text-[16px] text-primary">upload_file</span>
                <span>Tải tệp đính kèm (PDF, DOCX, ZIP)</span>
                <input type="file" class="block-file-input sr-only" accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip" />
              </label>
            ` : ''}
          </div>
        `;
      } else if (block.type === 'quiz') {
        const qType = block.q_type || 'MULTIPLE_CHOICE';
        const options = Array.isArray(block.options) && block.options.length ? block.options : ['', '', '', ''];
        const optionImages = Array.isArray(block.option_images) ? block.option_images : [];
        const correctIdx = Number(block.correct_index || 0);
        const blankAnswer = block.blank_answer || '';
        const pairs = Array.isArray(block.pairs) && block.pairs.length ? block.pairs : [
          { left: '', right: '' },
          { left: '', right: '' }
        ];
        const qImg = block.image_url || block.question_image_url || '';

        // Calculate quiz index among all quiz blocks
        const allQuizBlocks = activeBlocks.filter(b => b.type === 'quiz');
        const qIdxInQuizzes = allQuizBlocks.indexOf(block);
        const totalQuizzes = allQuizBlocks.length;

        bodyHtml = `
          <div class="space-y-4" data-active-qtype="${qType}">
            <!-- Question Stepper Bar (Pagination like Student View) -->
            ${totalQuizzes > 1 ? `
              <div class="flex items-center justify-between gap-2 p-2 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/80 dark:border-purple-900/60 text-xs select-none">
                <div class="flex items-center gap-1.5 overflow-x-auto py-0.5">
                  <span class="text-[11px] font-bold text-purple-900 dark:text-purple-300 pr-1 shrink-0">Chuyển câu:</span>
                  ${allQuizBlocks.map((qb, i) => `
                    <button
                      type="button"
                      class="btn-quiz-jump-step px-2.5 py-1 rounded-lg font-mono font-bold text-xs transition-all cursor-pointer ${qb === block ? 'bg-purple-600 text-white shadow-xs' : 'bg-white dark:bg-[#1E1E1E] text-slate-700 dark:text-slate-300 border border-purple-200 dark:border-purple-800 hover:bg-purple-100/50'}"
                      data-target-block-id="${qb.id}"
                      title="Chuyển đến Câu ${i + 1}"
                    >
                      Câu ${i + 1}
                    </button>
                  `).join('')}
                </div>
                <span class="text-[11px] font-bold text-purple-700 dark:text-purple-300 shrink-0 font-mono">
                  ${qIdxInQuizzes + 1} / ${totalQuizzes} câu
                </span>
              </div>
            ` : ''}

            <!-- Segmented Control for Question Type -->
            <div class="flex items-center justify-between gap-2 p-1.5 bg-[#FAF9F5] dark:bg-[#181818] rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B]">
              <span class="text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99] px-2 uppercase tracking-wider">Thể loại:</span>
              <div class="flex items-center gap-1">
                <button
                  type="button"
                  class="btn-quiz-type-select px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${qType === 'MULTIPLE_CHOICE' ? 'bg-primary text-white shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#E8E6DF]/50 dark:hover:bg-[#2A2928]'}"
                  data-qtype-select="MULTIPLE_CHOICE"
                  ${isLocked ? 'disabled' : ''}
                >
                  Trắc nghiệm
                </button>
                <button
                  type="button"
                  class="btn-quiz-type-select px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${qType === 'FILL_BLANK' ? 'bg-primary text-white shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#E8E6DF]/50 dark:hover:bg-[#2A2928]'}"
                  data-qtype-select="FILL_BLANK"
                  ${isLocked ? 'disabled' : ''}
                >
                  Điền khuyết
                </button>
                <button
                  type="button"
                  class="btn-quiz-type-select px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${qType === 'MATCHING' ? 'bg-primary text-white shadow-xs' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#E8E6DF]/50 dark:hover:bg-[#2A2928]'}"
                  data-qtype-select="MATCHING"
                  ${isLocked ? 'disabled' : ''}
                >
                  Nối từ
                </button>
              </div>
            </div>

            <!-- Question Prompt & Image Attachment -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="block text-xs font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                  ${qType === 'FILL_BLANK' ? 'Nội dung câu hỏi điền khuyết (dùng [___] làm chỗ trống):' : (qType === 'MATCHING' ? 'Lời dẫn bài tập nối từ:' : 'Nội dung câu hỏi trắc nghiệm:')} <span class="text-rose-500">*</span>
                </label>
                ${!isLocked ? `
                  <label class="cursor-pointer text-[11px] font-bold text-primary hover:underline flex items-center gap-1" title="Dán ảnh (Ctrl+V) hoặc chọn ảnh từ máy">
                    <span class="material-symbols-outlined text-[15px]">add_photo_alternate</span>
                    <span>${qImg ? 'Đổi ảnh câu hỏi' : 'Thêm ảnh câu hỏi'}</span>
                    <input type="file" class="block-quiz-question-file sr-only" accept="image/*" />
                  </label>
                ` : ''}
              </div>

              <div class="relative">
                <textarea
                  rows="2"
                  class="block-quiz-question w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#1E1E1E] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all font-medium resize-y"
                  placeholder="${qType === 'FILL_BLANK' ? 'Ví dụ: Thủ đô của Việt Nam là [___]. (Có thể ấn Ctrl+V để dán ảnh vào đây)' : (qType === 'MATCHING' ? 'Nối các khái niệm ở cột trái với ý nghĩa phù hợp ở cột phải:' : 'Ví dụ: Đâu là ngôn ngữ đánh dấu siêu văn bản? (Có thể ấn Ctrl+V để dán ảnh vào đây)')}"
                  ${isLocked ? 'disabled' : ''}
                >${UI.escapeHtml(block.question || '')}</textarea>
              </div>

              <!-- Question Image Preview -->
              ${qImg ? `
                <div class="relative inline-block border border-purple-200 dark:border-purple-800 rounded-xl overflow-hidden bg-slate-50 dark:bg-slate-900 group">
                  <img src="${UI.escapeHtml(qImg)}" alt="Ảnh câu hỏi" class="max-h-48 max-w-full rounded-xl object-contain block" />
                  ${!isLocked ? `
                    <button type="button" class="btn-remove-quiz-img absolute top-1.5 right-1.5 p-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white shadow-xs cursor-pointer" title="Xóa ảnh này">
                      <span class="material-symbols-outlined text-[14px]">delete</span>
                    </button>
                  ` : ''}
                </div>
              ` : `
                <div class="text-[11px] text-[#8F8E8A] flex items-center gap-1">
                  <span class="material-symbols-outlined text-[14px]">content_paste</span>
                  <span>Mẹo: Thầy/Cô có thể copy ảnh rồi nhấn <strong>Ctrl + V</strong> trực tiếp vào ô câu hỏi để chèn ảnh minh họa.</span>
                </div>
              `}
            </div>

            <!-- Specific Type Body -->
            ${qType === 'MULTIPLE_CHOICE' ? `
              <div class="space-y-2.5">
                <label class="block text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                  Các phương án lựa chọn (Chọn nút tròn để chỉ định đáp án đúng, có thể đính kèm ảnh cho từng đáp án):
                </label>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 quiz-options-container">
                  ${options.map((opt, oIdx) => {
                    const optImg = optionImages[oIdx] || '';
                    return `
                      <div class="flex flex-col gap-1.5 p-2 rounded-xl border ${correctIdx === oIdx ? 'border-primary bg-primary/5' : 'border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#1E1E1E]'} transition-all" data-opt-idx="${oIdx}">
                        <div class="flex items-center gap-2">
                          <input
                            type="radio"
                            name="quiz_correct_${bId}"
                            value="${oIdx}"
                            ${correctIdx === oIdx ? 'checked' : ''}
                            class="w-4 h-4 ml-1 text-primary cursor-pointer shrink-0"
                            ${isLocked ? 'disabled' : ''}
                            title="Chọn làm đáp án đúng"
                          />
                          <span class="text-xs font-bold text-[#5C5B57] dark:text-[#9E9D99] w-4 text-center shrink-0">${String.fromCharCode(65 + oIdx)}</span>
                          <input
                            type="text"
                            class="block-quiz-opt-text flex-1 px-2.5 py-1.5 rounded-lg border-0 bg-transparent text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:ring-0"
                            placeholder="Phương án ${String.fromCharCode(65 + oIdx)} (Ctrl+V để dán ảnh)"
                            value="${UI.escapeHtml(opt || '')}"
                            ${isLocked ? 'disabled' : ''}
                          />
                          ${!isLocked ? `
                            <label class="cursor-pointer p-1 text-[#8F8E8A] hover:text-primary transition-colors" title="Thêm ảnh cho phương án này">
                              <span class="material-symbols-outlined text-[16px]">image</span>
                              <input type="file" class="block-quiz-opt-file sr-only" accept="image/*" data-opt-idx="${oIdx}" />
                            </label>
                          ` : ''}
                        </div>
                        ${optImg ? `
                          <div class="relative inline-block self-start ml-8 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                            <img src="${UI.escapeHtml(optImg)}" alt="Ảnh đáp án ${String.fromCharCode(65 + oIdx)}" class="h-16 object-contain block bg-slate-50 dark:bg-slate-900" />
                            ${!isLocked ? `
                              <button type="button" class="btn-remove-opt-img absolute top-0.5 right-0.5 p-0.5 rounded bg-rose-600 text-white cursor-pointer" data-opt-idx="${oIdx}" title="Xóa ảnh">
                                <span class="material-symbols-outlined text-[12px]">close</span>
                              </button>
                            ` : ''}
                          </div>
                        ` : ''}
                      </div>
                    `;
                  }).join('')}
                </div>
              </div>
            ` : ''}

            ${qType === 'FILL_BLANK' ? `
              <div class="space-y-2.5 p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20">
                <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-800 dark:text-emerald-300">
                  <span class="material-symbols-outlined text-[18px] text-emerald-600">edit_note</span>
                  <span>Đáp án chính xác cho vị trí [___]: <span class="text-rose-500">*</span></span>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    type="text"
                    class="block-quiz-blank-answer flex-1 px-3.5 py-2 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-white dark:bg-[#1E1E1E] text-xs font-bold text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-emerald-600 shadow-2xs"
                    placeholder="Nhập từ hoặc cụm từ cần điền (Ví dụ: Hà Nội)"
                    value="${UI.escapeHtml(blankAnswer)}"
                    ${isLocked ? 'disabled' : ''}
                  />
                </div>
                <p class="text-[11px] text-emerald-700 dark:text-emerald-400 leading-relaxed">
                  Lưu ý: Học sinh sẽ thấy câu hỏi và tự gõ câu trả lời vào ô trống tương ứng. Hệ thống sẽ đối chiếu không phân biệt chữ hoa/thường.
                </p>
              </div>
            ` : ''}

            ${qType === 'MATCHING' ? `
              <div class="space-y-3 p-3.5 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/40 dark:bg-amber-950/20">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-1.5 text-xs font-bold text-amber-800 dark:text-amber-300">
                    <span class="material-symbols-outlined text-[18px] text-amber-600">join_inner</span>
                    <span>Các cặp nối từ tương ứng (Vế A ghép đúng với Vế B):</span>
                  </div>
                  ${!isLocked ? `
                    <button type="button" class="btn-add-quiz-pair px-2 py-1 rounded-lg bg-amber-100 hover:bg-amber-200 dark:bg-amber-900/60 dark:hover:bg-amber-900 text-[11px] font-bold text-amber-900 dark:text-amber-200 flex items-center gap-1 cursor-pointer transition-colors">
                      <span class="material-symbols-outlined text-[14px]">add</span>
                      <span>Thêm cặp ghép</span>
                    </button>
                  ` : ''}
                </div>
                <div class="space-y-2 quiz-pairs-container">
                  ${pairs.map((p, pIdx) => `
                    <div class="flex items-center gap-2 block-quiz-pair-row bg-white dark:bg-[#1E1E1E] p-2 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B]" data-pair-idx="${pIdx}">
                      <span class="w-5 h-5 rounded-md bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 font-bold text-[11px] flex items-center justify-center shrink-0">${pIdx + 1}</span>
                      <input
                        type="text"
                        class="block-quiz-pair-left flex-1 px-2.5 py-1.5 rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#252525] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
                        placeholder="Vế A (Khái niệm ${pIdx + 1})"
                        value="${UI.escapeHtml(p.left || '')}"
                        ${isLocked ? 'disabled' : ''}
                      />
                      <span class="material-symbols-outlined text-[16px] text-amber-500 shrink-0">arrow_forward</span>
                      <input
                        type="text"
                        class="block-quiz-pair-right flex-1 px-2.5 py-1.5 rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#252525] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
                        placeholder="Vế B (Ý nghĩa ${pIdx + 1})"
                        value="${UI.escapeHtml(p.right || '')}"
                        ${isLocked ? 'disabled' : ''}
                      />
                      ${!isLocked && pairs.length > 2 ? `
                        <button type="button" class="btn-remove-quiz-pair p-1 text-rose-500 hover:bg-rose-100 rounded cursor-pointer" data-pair-idx="${pIdx}" title="Xóa cặp này">
                          <span class="material-symbols-outlined text-[15px]">close</span>
                        </button>
                      ` : ''}
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            <!-- Explanation -->
            <div class="space-y-1">
              <label class="block text-[11px] font-semibold text-[#8F8E8A] dark:text-[#6D6C68]">
                Giải thích ngắn khi học viên trả lời (tùy chọn):
              </label>
              <input
                type="text"
                class="block-quiz-explanation w-full px-3 py-2 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#1E1E1E] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
                placeholder="VD: Kiến thức này được đề cập trong bài giảng."
                value="${UI.escapeHtml(block.explanation || '')}"
                ${isLocked ? 'disabled' : ''}
              />
            </div>

            <!-- Quiz Passing Threshold & Action Buttons (Save Question) -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
              <div class="flex items-center gap-2 text-xs">
                <span class="material-symbols-outlined text-[17px] text-purple-600">verified</span>
                <label class="font-bold text-purple-950 dark:text-purple-200 shrink-0">
                  Tỷ lệ đạt (%):
                </label>
                <input
                  type="number"
                  min="50"
                  max="100"
                  step="5"
                  class="block-quiz-passing-percent w-16 px-2 py-1 rounded-lg border border-purple-300 dark:border-purple-800 bg-white dark:bg-[#1E1E1E] text-xs font-bold text-center text-purple-900 dark:text-purple-100 outline-none focus:border-purple-500"
                  value="${block.passing_percent || activeLessonMeta.quiz_passing_percent || 80}"
                  ${isLocked ? 'disabled' : ''}
                />
              </div>

              ${!isLocked ? `
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="btn-save-single-quiz px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                    data-block-idx="${idx}"
                    title="Lưu lại câu hỏi vừa tạo vào bài giảng"
                  >
                    <span class="material-symbols-outlined text-[16px]">save</span>
                    <span>Lưu câu hỏi</span>
                  </button>
                </div>
              ` : ''}
            </div>
          </div>
        `;
      }

      return `
        <div class="curriculum-block-card rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] p-4 sm:p-5 shadow-xs space-y-3 transition-all" data-block-id="${bId}" data-block-idx="${idx}" data-active-qtype="${block.type === 'quiz' ? (block.q_type || 'MULTIPLE_CHOICE') : ''}">
          <!-- Block Header -->
          <div class="flex items-center justify-between pb-2 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div class="flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg ${iconColor} flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-[17px]">${typeIcon}</span>
              </span>
              <span class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">
                ${typeLabel}
              </span>
            </div>

            <!-- Block Controls -->
            <div class="flex items-center gap-1 shrink-0">
              ${!isLocked ? `
                <button type="button" class="btn-block-move-up p-1.5 rounded-lg hover:bg-[#F4F1EA] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] transition-colors cursor-pointer" data-idx="${idx}" title="Di chuyển lên" ${idx === 0 ? 'disabled style="opacity: 0.3;"' : ''}>
                  <span class="material-symbols-outlined text-[16px]">arrow_upward</span>
                </button>
                <button type="button" class="btn-block-move-down p-1.5 rounded-lg hover:bg-[#F4F1EA] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] transition-colors cursor-pointer" data-idx="${idx}" title="Di chuyển xuống" ${idx === activeBlocks.length - 1 ? 'disabled style="opacity: 0.3;"' : ''}>
                  <span class="material-symbols-outlined text-[16px]">arrow_downward</span>
                </button>
                <button type="button" class="btn-block-delete p-1.5 rounded-lg hover:bg-rose-100 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-400 transition-colors cursor-pointer" data-idx="${idx}" title="Xóa nội dung">
                  <span class="material-symbols-outlined text-[16px]">delete</span>
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Block Body -->
          ${bodyHtml}
        </div>
      `;
    };

    // Render full editor pane
    const renderEditor = () => {
      const activeUnit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(activeUnitId));
      let badgeClass = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
      let badgeText = 'Bản nháp';
      if (activeLessonMeta.status === 'PUBLISHED') {
        badgeClass = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300';
        badgeText = 'Đã xuất bản';
      } else if (activeLessonMeta.status === 'MODIFIED') {
        badgeClass = 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300';
        badgeText = 'Đã sửa';
      }

      editorContainer.innerHTML = `
        <div class="space-y-5" id="curriculum-active-editor-root">
          <!-- Top Action Bar -->
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-primary truncate">
                  ${activeUnit ? UI.escapeHtml(activeUnit.title) : 'Chương bài học'}
                </span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
                  ${badgeText}
                </span>
              </div>
              <h2 class="text-base sm:text-lg font-extrabold text-[#222120] dark:text-[#EDEDEB] tracking-tight">
                Chỉnh sửa bài giảng
              </h2>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-2.5 shrink-0">
              <button
                type="button"
                id="btn-preview-lesson"
                class="px-4 py-2 rounded-xl bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center gap-1.5 transition-colors cursor-pointer"
                title="Xem trước giao diện bài học"
              >
                <span class="material-symbols-outlined text-[16px] text-primary">visibility</span>
                <span>Xem trước</span>
              </button>
              ${!isLocked ? `
                <button
                  type="button"
                  id="btn-save-lesson"
                  class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                  title="Lưu lại bài giảng (Phím tắt: Ctrl+S)"
                >
                  <span class="material-symbols-outlined text-[16px]">save</span>
                  <span id="save-btn-text">Lưu bài giảng</span>
                </button>
              ` : `
                <span class="px-3.5 py-2 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 text-xs font-bold border border-blue-200 dark:border-blue-800 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">lock</span>
                  <span>Đang khóa xét duyệt</span>
                </span>
              `}
            </div>
          </div>

          ${isLocked ? `
            <div class="rounded-xl border border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/40 p-4 text-xs text-blue-800 dark:text-blue-200 flex items-center gap-2.5">
              <span class="material-symbols-outlined text-[20px] text-blue-600 shrink-0">lock</span>
              <span>Khóa học đang trong đợt xét duyệt. Chế độ chỉ đọc (Read-only). Vui lòng rút lại yêu cầu hoặc chờ Quản trị viên duyệt xong để chỉnh sửa.</span>
            </div>
          ` : ''}

          <!-- Metadata Card -->
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs space-y-4">
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
                Tiêu đề bài giảng <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                id="input-lesson-title"
                value="${UI.escapeHtml(activeLessonMeta.title || '')}"
                class="w-full px-4 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#1E1E1E] text-sm font-bold text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all"
                placeholder="Nhập tiêu đề bài giảng..."
                ${isLocked ? 'disabled' : ''}
              />
            </div>

            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
                Tóm tắt nội dung bài học
              </label>
              <textarea
                id="input-lesson-summary"
                rows="2"
                class="w-full px-3.5 py-2 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#1E1E1E] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all resize-none"
                placeholder="Mô tả tóm tắt mục tiêu hoặc kiến thức cốt lõi..."
                ${isLocked ? 'disabled' : ''}
              >${UI.escapeHtml(activeLessonMeta.summary || '')}</textarea>
            </div>
          </div>

          <!-- Vertical Blocks List -->
          <div class="space-y-4" id="blocks-list-container">
            ${activeBlocks.map((b, idx) => renderBlockHtml(b, idx)).join('')}
          </div>

          <!-- Add Block Toolbar -->
          ${!isLocked ? `
            <div class="p-4 sm:p-5 rounded-2xl bg-[#FAF9F5] dark:bg-[#18181b] border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs space-y-3">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold uppercase tracking-wider text-[#222120] dark:text-[#EDEDEB]">Thêm nội dung:</span>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <button
                  type="button"
                  id="btn-add-block-text"
                  class="py-2.5 px-3 rounded-xl bg-white dark:bg-[#202020] hover:bg-primary/5 hover:border-primary border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[17px] text-primary">subject</span>
                  <span>Bài học</span>
                </button>
                <button
                  type="button"
                  id="btn-add-block-video"
                  class="py-2.5 px-3 rounded-xl bg-white dark:bg-[#202020] hover:bg-rose-50 hover:border-rose-300 dark:hover:bg-rose-950/40 border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[17px] text-rose-600">play_circle</span>
                  <span>Video</span>
                </button>
                <button
                  type="button"
                  id="btn-add-block-doc"
                  class="py-2.5 px-3 rounded-xl bg-white dark:bg-[#202020] hover:bg-blue-50 hover:border-blue-300 dark:hover:bg-blue-950/40 border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[17px] text-blue-600">description</span>
                  <span>Tài liệu</span>
                </button>
                <button
                  type="button"
                  id="btn-add-block-quiz"
                  class="py-2.5 px-3 rounded-xl bg-white dark:bg-[#202020] hover:bg-purple-50 hover:border-purple-300 dark:hover:bg-purple-950/40 border border-[#E8E6DF] dark:border-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[17px] text-purple-600">quiz</span>
                  <span>Câu hỏi</span>
                </button>
              </div>
            </div>
          ` : ''}

          <!-- Bottom Save Shortcut Bar -->
          ${!isLocked ? `
            <div class="pt-2 flex items-center justify-between">
              <span class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]">
                Nhấn <strong>Ctrl + S</strong> bất cứ lúc nào để lưu bài giảng.
              </span>
              <button
                type="button"
                id="btn-save-lesson-bottom"
                class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                <span class="material-symbols-outlined text-[16px]">save</span>
                <span>Lưu bài giảng</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;

      wireEditorListeners();
    };

    // Wire listeners for editor pane
    const wireEditorListeners = () => {
      // Save buttons
      const saveBtn = editorContainer.querySelector('#btn-save-lesson');
      const saveBtnBottom = editorContainer.querySelector('#btn-save-lesson-bottom');
      const handleSave = async () => {
        if (isSaving || isLocked) return;
        scrapeBlocksFromDom();
        if (!activeLessonMeta.title) {
          UI.showToast('Vui lòng nhập tiêu đề bài giảng.', 'warning');
          return;
        }

        isSaving = true;
        const textSpan = editorContainer.querySelector('#save-btn-text');
        if (textSpan) textSpan.textContent = 'Đang lưu...';
        if (saveBtn) saveBtn.disabled = true;
        if (saveBtnBottom) saveBtnBottom.disabled = true;

        try {
          const targetLessonId = activeLessonId;
          const targetUnitId = activeUnitId;
          const targetGen = selectLessonGen;
          const payload = InstructorView.serializeBlocksToPayload(activeBlocks, activeLessonMeta);
          const res = await ApiClient.updateLesson(targetLessonId, payload);

          const newLessonId = res?.lesson?.lesson_id || res?.lesson_id || res?.id;
          const resolvedId = newLessonId || targetLessonId;
          if (newLessonId && String(newLessonId) !== String(targetLessonId)) {
            if (String(activeLessonId) === String(targetLessonId) && selectLessonGen === targetGen) {
              activeLessonId = newLessonId;
              activeLessonMeta.status = res?.lesson?.status || res?.status || 'DRAFT';
            }
            const treeItem = treeContainer.querySelector(`.lesson-tree-item[data-lesson-id="${targetLessonId}"]`);
            if (treeItem) {
              treeItem.setAttribute('data-lesson-id', newLessonId);
              treeItem.dataset.lessonId = newLessonId;
            }
            const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(targetUnitId));
            if (unit && unit.lessons) {
              const l = unit.lessons.find(item => String(item.lesson_id || item.id) === String(targetLessonId));
              if (l) {
                l.lesson_id = newLessonId;
                l.id = newLessonId;
                l.status = res?.lesson?.status || res?.status || 'DRAFT';
              }
            }
          }

          // Update memory state and tree DOM title for resolvedId
          const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(targetUnitId));
          if (unit && unit.lessons) {
            const l = unit.lessons.find(item => String(item.lesson_id || item.id) === String(resolvedId));
            if (l) {
              l.title = activeLessonMeta.title;
              if (l.status === 'PUBLISHED') l.status = 'MODIFIED';
            }
          }

          const treeItem = treeContainer.querySelector(`.lesson-tree-item[data-lesson-id="${resolvedId}"]`);
          if (treeItem) {
            const titleEl = treeItem.querySelector('.lesson-item-title');
            if (titleEl) titleEl.textContent = activeLessonMeta.title;
          }

          if (selectLessonGen === targetGen && String(activeLessonId) === String(resolvedId)) {
            isEditorDirty = false;
          }

          if (res && (res.pending_approval || res.status === 202)) {
            UI.showToast(res.message || 'Thay đổi đã được gửi duyệt tới Quản trị viên.', 'info');
          } else {
            UI.showToast(res?.message || 'Đã lưu bài giảng thành công!', 'success');
          }
        } catch (err) {
          UI.showToast(err.message || 'Lỗi khi lưu bài giảng.', 'error');
        } finally {
          isSaving = false;
          if (textSpan) textSpan.textContent = 'Lưu bài giảng';
          if (saveBtn) saveBtn.disabled = false;
          if (saveBtnBottom) saveBtnBottom.disabled = false;
        }
      };

      if (saveBtn) saveBtn.onclick = handleSave;
      if (saveBtnBottom) saveBtnBottom.onclick = handleSave;

      // Add Block buttons
      const addTextBtn = editorContainer.querySelector('#btn-add-block-text');
      const addVidBtn = editorContainer.querySelector('#btn-add-block-video');
      const addDocBtn = editorContainer.querySelector('#btn-add-block-doc');
      const addQuizBtn = editorContainer.querySelector('#btn-add-block-quiz');

      if (addTextBtn) {
        addTextBtn.onclick = () => {
          scrapeBlocksFromDom();
          activeBlocks.push({
            id: 'blk_' + Math.random().toString(36).slice(2, 9),
            type: 'text',
            content: ''
          });
          renderEditor();
        };
      }
      if (addVidBtn) {
        addVidBtn.onclick = () => {
          scrapeBlocksFromDom();
          activeBlocks.push({
            id: 'blk_' + Math.random().toString(36).slice(2, 9),
            type: 'video',
            videoType: 'YOUTUBE',
            url: ''
          });
          renderEditor();
        };
      }
      if (addDocBtn) {
        addDocBtn.onclick = () => {
          scrapeBlocksFromDom();
          activeBlocks.push({
            id: 'blk_' + Math.random().toString(36).slice(2, 9),
            type: 'document',
            title: 'Tài liệu đính kèm',
            files: []
          });
          renderEditor();
        };
      }
      if (addQuizBtn) {
        addQuizBtn.onclick = () => {
          scrapeBlocksFromDom();
          activeBlocks.push({
            id: 'blk_' + Math.random().toString(36).slice(2, 9),
            type: 'quiz',
            q_type: 'MULTIPLE_CHOICE',
            question: '',
            options: ['', '', '', ''],
            correct_index: 0,
            blank_answer: '',
            pairs: [
              { left: '', right: '' },
              { left: '', right: '' }
            ],
            explanation: ''
          });
          renderEditor();
        };
      }

      // Quiz type selection and pair management
      editorContainer.querySelectorAll('.btn-quiz-type-select').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const card = btn.closest('.curriculum-block-card');
          const bIdx = parseInt(card.dataset.blockIdx, 10);
          const newType = btn.dataset.qtypeSelect;
          scrapeBlocksFromDom();
          if (activeBlocks[bIdx]) {
            activeBlocks[bIdx].q_type = newType;
            renderEditor();
          }
        };
      });

      editorContainer.querySelectorAll('.btn-add-quiz-pair').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const card = btn.closest('.curriculum-block-card');
          const bIdx = parseInt(card.dataset.blockIdx, 10);
          scrapeBlocksFromDom();
          if (activeBlocks[bIdx]) {
            if (!activeBlocks[bIdx].pairs) activeBlocks[bIdx].pairs = [];
            activeBlocks[bIdx].pairs.push({ left: '', right: '' });
            renderEditor();
          }
        };
      });

      editorContainer.querySelectorAll('.btn-remove-quiz-pair').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const card = btn.closest('.curriculum-block-card');
          const bIdx = parseInt(card.dataset.blockIdx, 10);
          const pIdx = parseInt(btn.dataset.pairIdx, 10);
          scrapeBlocksFromDom();
          if (activeBlocks[bIdx] && activeBlocks[bIdx].pairs) {
            activeBlocks[bIdx].pairs.splice(pIdx, 1);
            renderEditor();
          }
        };
      });

      // Reorder and delete blocks
      editorContainer.querySelectorAll('.btn-block-move-up').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx <= 0) return;
          scrapeBlocksFromDom();
          const temp = activeBlocks[idx];
          activeBlocks[idx] = activeBlocks[idx - 1];
          activeBlocks[idx - 1] = temp;
          renderEditor();
        };
      });

      editorContainer.querySelectorAll('.btn-block-move-down').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx >= activeBlocks.length - 1) return;
          scrapeBlocksFromDom();
          const temp = activeBlocks[idx];
          activeBlocks[idx] = activeBlocks[idx + 1];
          activeBlocks[idx + 1] = temp;
          renderEditor();
        };
      });

      editorContainer.querySelectorAll('.btn-block-delete').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          const conf = await UI.confirm('Xóa nội dung', 'Xác nhận xóa phần nội dung này?', 'Xóa');
          if (!conf) return;
          scrapeBlocksFromDom();
          const targetLessonId = activeLessonId;
          const targetBlock = activeBlocks[idx];
          if (targetBlock && Array.isArray(targetBlock.files) && targetBlock.files.length > 0) {
            for (const f of targetBlock.files) {
              const rId = f.resource_id || f.id || f.asset_id;
              if (rId) {
                try {
                  const res = await ApiClient.detachLessonResource(cId, targetLessonId, rId);
                  if (res && (res.pending_approval || res.status === 202)) {
                    UI.showToast(res.message || 'Yêu cầu gỡ tệp đính kèm đã gửi Quản trị viên để xét duyệt.', 'info');
                  }
                } catch (e) {
                  console.warn('Could not detach resource on block delete:', e);
                }
              }
            }
          }
          if (String(activeLessonId) === String(targetLessonId)) {
            activeBlocks.splice(idx, 1);
            isEditorDirty = true;
            renderEditor();
          }
        };
      });

      // Document file upload inputs
      editorContainer.querySelectorAll('.curriculum-block-card').forEach((card, bIdx) => {
        const fileInput = card.querySelector('.block-file-input');
        const cardBlockId = activeBlocks[bIdx]?.id;
        const targetLessonId = activeLessonId;
        const uploadGen = selectLessonGen;
        if (fileInput) {
          fileInput.onchange = async (e) => {
            const file = e.target.files?.[0];
            e.target.value = '';
            if (!file) return;
            scrapeBlocksFromDom();
            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);

            try {
              UI.showToast('Đang tải lên tài liệu...', 'info');
              const res = await ApiClient.attachLessonResource(cId, targetLessonId, formData);
              if (res && (res.pending_approval || res.status === 202)) {
                UI.showToast(res.message || 'Tài liệu đã được gửi yêu cầu phê duyệt đính kèm (chờ Quản trị viên duyệt).', 'info');
                return;
              }
              if (selectLessonGen === uploadGen && String(activeLessonId) === String(targetLessonId)) {
                const targetBlock = activeBlocks.find(b => b.id === cardBlockId) || activeBlocks[bIdx];
                if (targetBlock) {
                  if (!targetBlock.files) targetBlock.files = [];
                  targetBlock.files.push({
                    resource_id: res.resource_id || res.asset_id,
                    title: file.name,
                    filename: file.name,
                    file_url: res.file_url || '',
                    file_size_bytes: file.size
                  });
                  renderEditor();
                }
              }
              UI.showToast('Đã tải tài liệu thành công!', 'success');
            } catch (err) {
              UI.showToast(err.message || 'Lỗi tải lên tài liệu.', 'error');
            }
          };
        }

        // Delete single file inside document block
        card.querySelectorAll('.btn-delete-doc-file').forEach(delBtn => {
          delBtn.onclick = async () => {
            const fIdx = parseInt(delBtn.dataset.fileIdx, 10);
            const rId = delBtn.dataset.resourceId;
            const targetGen = selectLessonGen;
            scrapeBlocksFromDom();
            try {
              if (rId) {
                const res = await ApiClient.detachLessonResource(cId, targetLessonId, rId);
                if (res && (res.pending_approval || res.status === 202)) {
                  UI.showToast(res.message || 'Yêu cầu gỡ tệp đính kèm đã được gửi tới Quản trị viên để xét duyệt.', 'info');
                  if (selectLessonGen === targetGen && String(activeLessonId) === String(targetLessonId)) {
                    const targetBlock = activeBlocks.find(b => b.id === cardBlockId) || activeBlocks[bIdx];
                    if (targetBlock?.files && targetBlock.files[fIdx]) {
                      targetBlock.files[fIdx].pending_delete = true;
                    }
                    renderEditor();
                  }
                  return;
                }
              }
              if (selectLessonGen === targetGen && String(activeLessonId) === String(targetLessonId)) {
                const targetBlock = activeBlocks.find(b => b.id === cardBlockId) || activeBlocks[bIdx];
                if (targetBlock?.files) {
                  targetBlock.files.splice(fIdx, 1);
                }
                renderEditor();
              }
              UI.showToast('Đã xóa tệp đính kèm.', 'success');
            } catch (err) {
              UI.showToast(err.message || 'Lỗi xóa tệp đính kèm.', 'error');
            }
          };
        });

        // Video URL input live preview update
        const videoUrlInput = card.querySelector('.block-video-url');
        if (videoUrlInput) {
          videoUrlInput.onchange = () => {
            scrapeBlocksFromDom();
            renderEditor();
          };
        }

        // Video file upload & dropzone handlers
        const videoFileInput = card.querySelector('.block-video-file-input');
        const videoDropzone = card.querySelector('.video-dropzone');
        const uploadProgress = card.querySelector('.video-upload-progress');
        const progressFileName = card.querySelector('.progress-file-name');
        const progressFilePercent = card.querySelector('.progress-file-percent');
        const progressBarInner = card.querySelector('.progress-bar-inner');

        const handleUploadVideoFiles = async (filesList) => {
          const files = Array.from(filesList || []);
          if (!files.length) return;

          // Fail-closed video size constraint: < 1 GB (1024 * 1024 * 1024 bytes)
          const MAX_VIDEO_SIZE = 1024 * 1024 * 1024;
          for (const f of files) {
            if (f.size >= MAX_VIDEO_SIZE) {
              UI.showToast(`Tệp "${f.name}" vượt quá giới hạn 1 GB. Vui lòng chọn video nhỏ hơn 1 GB.`, 'warning');
              return;
            }
          }

          scrapeBlocksFromDom();
          if (uploadProgress) uploadProgress.classList.remove('hidden');

          let successCount = 0;
          for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (progressFileName) progressFileName.textContent = `Đang tải: ${file.name} (${i + 1}/${files.length})`;
            const initialPct = Math.round(((i + 0.3) / files.length) * 100);
            if (progressFilePercent) progressFilePercent.textContent = `${initialPct}%`;
            if (progressBarInner) progressBarInner.style.width = `${initialPct}%`;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);

            try {
              const res = await ApiClient.attachLessonResource(cId, targetLessonId, formData);
              if (String(activeLessonId) === String(targetLessonId)) {
                const targetBlock = activeBlocks.find(b => b.id === cardBlockId) || activeBlocks[bIdx];
                if (targetBlock) {
                  if (!targetBlock.files) targetBlock.files = [];
                  targetBlock.files.push({
                    resource_id: res.resource_id || res.asset_id,
                    title: file.name,
                    filename: file.name,
                    file_url: res.file_url || '',
                    file_size_bytes: file.size
                  });
                }
              }
              successCount++;
              const donePct = Math.round(((i + 1) / files.length) * 100);
              if (progressFilePercent) progressFilePercent.textContent = `${donePct}%`;
              if (progressBarInner) progressBarInner.style.width = `${donePct}%`;
            } catch (err) {
              UI.showToast(`Lỗi tải video "${file.name}": ${err.message || 'Không thể tải lên.'}`, 'error');
            }
          }

          if (uploadProgress) uploadProgress.classList.add('hidden');
          if (successCount > 0 && String(activeLessonId) === String(targetLessonId)) {
            renderEditor();
            UI.showToast(`Đã tải lên ${successCount} video thành công!`, 'success');
          }
        };

        if (videoDropzone && videoFileInput) {
          videoDropzone.onclick = (e) => {
            if (e.target !== videoFileInput) {
              videoFileInput.click();
            }
          };

          videoDropzone.ondragover = (e) => {
            e.preventDefault();
            e.stopPropagation();
            videoDropzone.classList.add('border-primary', 'bg-rose-50/50', 'dark:bg-rose-950/20');
          };

          videoDropzone.ondragleave = (e) => {
            e.preventDefault();
            e.stopPropagation();
            videoDropzone.classList.remove('border-primary', 'bg-rose-50/50', 'dark:bg-rose-950/20');
          };

          videoDropzone.ondrop = (e) => {
            e.preventDefault();
            e.stopPropagation();
            videoDropzone.classList.remove('border-primary', 'bg-rose-50/50', 'dark:bg-rose-950/20');
            const dtFiles = e.dataTransfer?.files;
            if (dtFiles && dtFiles.length > 0) {
              handleUploadVideoFiles(dtFiles);
            }
          };

          videoFileInput.onchange = (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
              handleUploadVideoFiles(files);
            }
            e.target.value = '';
          };
        }

        // Delete single video file inside video block
        card.querySelectorAll('.btn-delete-video-file').forEach(delBtn => {
          delBtn.onclick = async () => {
            const fIdx = parseInt(delBtn.dataset.fileIdx, 10);
            const rId = delBtn.dataset.resourceId;
            const conf = await UI.confirm('Xóa video', 'Xác nhận xóa video này khỏi bài giảng?', 'Xóa');
            if (!conf) return;
            scrapeBlocksFromDom();
            try {
              if (rId) {
                await ApiClient.detachLessonResource(cId, activeLessonId, rId);
              }
              if (activeBlocks[bIdx]?.files) {
                activeBlocks[bIdx].files.splice(fIdx, 1);
              }
              renderEditor();
              UI.showToast('Đã xóa video bài giảng.', 'success');
            } catch (err) {
              UI.showToast(err.message || 'Lỗi xóa video bài giảng.', 'error');
            }
          };
        });
      });

      // Preview Lesson Button
      const prevBtn = editorContainer.querySelector('#btn-preview-lesson');
      if (prevBtn) {
        prevBtn.onclick = () => {
          scrapeBlocksFromDom();
          const payload = InstructorView.serializeBlocksToPayload(activeBlocks, activeLessonMeta);
          const selectedId = activeLessonId || 'local-preview';
          const existingLessons = course.lessons || [];
          const selectedLesson = existingLessons.find(lesson => String(lesson.lesson_id || lesson.id) === String(selectedId));
          const previewLesson = { ...selectedLesson, ...payload, lesson_id: selectedId, learning_unit_id: activeUnitId };
          const previewLessons = existingLessons.map(lesson => String(lesson.lesson_id || lesson.id) === String(selectedId) ? previewLesson : lesson);
          if (!selectedLesson) previewLessons.push(previewLesson);
          InstructorView.openCoursePreview({ ...course, lessons: previewLessons }, selectedId);
        };
      }

      // Single Quiz Save button
      editorContainer.querySelectorAll('.btn-save-single-quiz').forEach(btn => {
        btn.onclick = async (e) => {
          e.stopPropagation();
          await handleSave();
        };
      });

      // Jump Step for Quiz Questions
      editorContainer.querySelectorAll('.btn-quiz-jump-step').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const targetId = btn.dataset.targetBlockId;
          const targetCard = editorContainer.querySelector(`.curriculum-block-card[data-block-id="${targetId}"]`);
          if (targetCard) {
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetCard.classList.add('ring-2', 'ring-purple-500');
            setTimeout(() => targetCard.classList.remove('ring-2', 'ring-purple-500'), 1500);
          }
        };
      });

      // Quiz Image Upload & Paste (Ctrl+V) Handlers
      editorContainer.querySelectorAll('.curriculum-block-card').forEach((card, bIdx) => {
        const qTextarea = card.querySelector('.block-quiz-question');
        const qFileInput = card.querySelector('.block-quiz-question-file');
        const btnRemoveQImg = card.querySelector('.btn-remove-quiz-img');

        if (qFileInput) {
          qFileInput.onchange = (e) => {
            const file = e.target.files?.[0];
            e.target.value = '';
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (re) => {
              scrapeBlocksFromDom();
              if (activeBlocks[bIdx]) {
                activeBlocks[bIdx].image_url = re.target.result;
                renderEditor();
              }
            };
            reader.readAsDataURL(file);
          };
        }

        if (qTextarea) {
          qTextarea.addEventListener('paste', (e) => {
            const items = e.clipboardData?.items;
            if (!items) return;
            for (let i = 0; i < items.length; i++) {
              if (items[i].type.indexOf('image') !== -1) {
                const file = items[i].getAsFile();
                if (file) {
                  e.preventDefault();
                  const reader = new FileReader();
                  reader.onload = (re) => {
                    scrapeBlocksFromDom();
                    if (activeBlocks[bIdx]) {
                      activeBlocks[bIdx].image_url = re.target.result;
                      renderEditor();
                      UI.showToast('Đã dán ảnh minh họa vào câu hỏi!', 'success');
                    }
                  };
                  reader.readAsDataURL(file);
                  break;
                }
              }
            }
          });
        }

        if (btnRemoveQImg) {
          btnRemoveQImg.onclick = (e) => {
            e.stopPropagation();
            scrapeBlocksFromDom();
            if (activeBlocks[bIdx]) {
              activeBlocks[bIdx].image_url = '';
              activeBlocks[bIdx].question_image_url = '';
              renderEditor();
            }
          };
        }

        card.querySelectorAll('.block-quiz-opt-file').forEach(fileIn => {
          fileIn.onchange = (e) => {
            const oIdx = parseInt(fileIn.dataset.optIdx, 10);
            const file = e.target.files?.[0];
            e.target.value = '';
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (re) => {
              scrapeBlocksFromDom();
              if (activeBlocks[bIdx]) {
                if (!activeBlocks[bIdx].option_images) activeBlocks[bIdx].option_images = [];
                activeBlocks[bIdx].option_images[oIdx] = re.target.result;
                renderEditor();
              }
            };
            reader.readAsDataURL(file);
          };
        });

        card.querySelectorAll('.block-quiz-opt-text').forEach((optInput, oIdx) => {
          optInput.addEventListener('paste', (e) => {
            const items = e.clipboardData?.items;
            if (!items) return;
            for (let i = 0; i < items.length; i++) {
              if (items[i].type.indexOf('image') !== -1) {
                const file = items[i].getAsFile();
                if (file) {
                  e.preventDefault();
                  const reader = new FileReader();
                  reader.onload = (re) => {
                    scrapeBlocksFromDom();
                    if (activeBlocks[bIdx]) {
                      if (!activeBlocks[bIdx].option_images) activeBlocks[bIdx].option_images = [];
                      activeBlocks[bIdx].option_images[oIdx] = re.target.result;
                      renderEditor();
                      UI.showToast(`Đã dán ảnh cho phương án ${String.fromCharCode(65 + oIdx)}!`, 'success');
                    }
                  };
                  reader.readAsDataURL(file);
                  break;
                }
              }
            }
          });
        });

        card.querySelectorAll('.btn-remove-opt-img').forEach(btn => {
          btn.onclick = (e) => {
            e.stopPropagation();
            const oIdx = parseInt(btn.dataset.optIdx, 10);
            scrapeBlocksFromDom();
            if (activeBlocks[bIdx] && activeBlocks[bIdx].option_images) {
              activeBlocks[bIdx].option_images[oIdx] = '';
              renderEditor();
            }
          };
        });
      });
      // Track unsaved modifications to prevent losing work
      editorContainer.addEventListener('input', () => { isEditorDirty = true; }, { passive: true });
      editorContainer.addEventListener('change', () => { isEditorDirty = true; }, { passive: true });

      // Activate Microsoft Word Standard Ribbon Toolbar
      InstructorView.wireWordRibbon(editorContainer);
    };

    // Keyboard shortcut: Ctrl + S to save lesson
    const handleGlobalKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        const activeRoot = document.getElementById('curriculum-active-editor-root');
        if (activeRoot) {
          e.preventDefault();
          const saveBtn = activeRoot.querySelector('#btn-save-lesson');
          if (saveBtn) saveBtn.click();
        }
      }
    };
    window.removeEventListener('keydown', window._curriculumStudioKeyHandler);
    window._curriculumStudioKeyHandler = handleGlobalKeyDown;
    window.addEventListener('keydown', window._curriculumStudioKeyHandler);

    // Initial button bindings
    if (btnTreeAddUnit) btnTreeAddUnit.onclick = handleAddUnit;
    if (btnTreeAddLesson) btnTreeAddLesson.onclick = handleAddLessonGlobal;

    // Resizable sidebar for Curriculum Tree
    const setupSidebarResizer = () => {
      const treePane = document.getElementById('curriculum-tree-pane');
      const resizer = document.getElementById('curriculum-sidebar-resizer');
      if (!treePane || !resizer) return;

      const savedWidth = typeof localStorage !== 'undefined' ? localStorage.getItem('pwd301_curriculum_sidebar_width') : null;
      if (savedWidth) {
        const num = parseInt(savedWidth, 10);
        if (num >= 260 && num <= 650) {
          treePane.style.width = `${num}px`;
          treePane.classList.remove('lg:w-80');
        }
      }

      let isResizing = false;
      let startX = 0;
      let startWidth = 0;

      resizer.onmousedown = (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = treePane.getBoundingClientRect().width;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';

        const onMouseMove = (moveEvent) => {
          if (!isResizing) return;
          const delta = moveEvent.clientX - startX;
          const newWidth = Math.min(650, Math.max(260, startWidth + delta));
          treePane.style.width = `${newWidth}px`;
          treePane.classList.remove('lg:w-80');
        };

        const onMouseUp = () => {
          if (!isResizing) return;
          isResizing = false;
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const finalWidth = Math.round(treePane.getBoundingClientRect().width);
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('pwd301_curriculum_sidebar_width', String(finalWidth));
          }
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        };

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      };
    };
    setupSidebarResizer();

    // Initial rendering
    renderTree();
    if (activeLessonId) {
      await selectLesson(activeLessonId, activeUnitId);
    } else {
      renderEmptyEditor();
    }
  }

  // =========================================================================
  // 3. Single-Page Curriculum Studio & Enterprise Course Management Dossier
  // =========================================================================
  static async renderCourseManage(container, courseId, initialTab = 'curriculum', initialLessonId = null, initialUnitId = null) {
    if (!courseId || courseId === 'undefined' || courseId === 'null' || !String(courseId).trim()) {
      container.innerHTML = `
        <div class="py-4 sm:py-6 lg:py-8 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
          <div class="flex items-center justify-between text-xs text-[#5C5B57] dark:text-[#9E9D99] font-medium">
            <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Danh sách khóa học</span>
            </a>
          </div>
          <div class="p-8 sm:p-12 rounded-2xl bg-white dark:bg-[#18181b] border border-slate-200/80 dark:border-slate-800 text-center space-y-4 shadow-sm">
            <div class="w-14 h-14 rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
              <span class="material-symbols-outlined text-[28px]">search_off</span>
            </div>
            <div class="space-y-1">
              <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">Chưa chọn khóa học để quản lý</h2>
              <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
                Đường dẫn không chứa mã định danh khóa học hợp lệ. Vui lòng chọn một khóa học từ danh sách phân công của bạn.
              </p>
            </div>
            <div class="pt-2 flex flex-wrap items-center justify-center gap-3">
              <a href="#/instructor/courses" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer">
                <span class="material-symbols-outlined text-[16px]">menu_book</span>
                <span>Danh sách khóa học</span>
              </a>
              <a href="#/instructor/dashboard" class="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer">
                <span class="material-symbols-outlined text-[16px]">dashboard</span>
                <span>Bảng điều khiển</span>
              </a>
            </div>
          </div>
        </div>
      `;
      return;
    }

    const existingRoot = container.querySelector('#course-manage-root');
    const keepCurrentCourseVisible = existingRoot?.dataset.courseId === String(courseId);
    if (!keepCurrentCourseVisible) container.innerHTML = `
      <div class="py-4 sm:py-6 lg:py-8 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans" id="course-manage-root">
        <div class="text-center py-24 text-[#8F8E8A] dark:text-[#6D6C68]">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs">Đang tải giáo án khóa học...</p>
        </div>
      </div>
    `;

    try {
      const [course, assessmentsData, changesetStatus] = await Promise.all([
        ApiClient.getCourseDetail(courseId),
        ApiClient.getCourseAssessments(courseId).catch(() => ({ assessments: [] })),
        ApiClient.getCourseChangesetStatus(courseId).catch(() => null)
      ]);

      if (!course) return;

      const cId = course.course_id || course.id;
      const lessons = course.lessons || [];
      const learningUnits = course.learning_units || [];
      const assessments = assessmentsData.assessments || assessmentsData.items || course.assessments || [];
      const isFrozen = course.status === 'SUBMITTED_FOR_REVIEW';
      const isPending = Boolean(changesetStatus && changesetStatus.status === 'PENDING');

      container.innerHTML = `
        <div class="py-4 sm:py-6 lg:py-8 space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans pb-20" id="course-manage-root" data-course-id="${UI.escapeHtml(cId)}">
          
          <!-- Top Breadcrumb & Navigation -->
          <div class="flex items-center justify-between text-xs text-[#5C5B57] dark:text-[#9E9D99] font-medium">
            <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Danh sách khóa học</span>
            </a>
            <div class="flex items-center gap-2">
              <a
                href="#/student/courses/${cId}"
                class="px-3 py-1.5 rounded-lg bg-[#F4F1EA] dark:bg-[#262524] hover:bg-[#ECE8DF] text-[#222120] dark:text-[#EDEDEB] text-xs font-semibold flex items-center gap-1.5 transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B]"
                title="Xem khóa học dưới góc nhìn Học viên"
              >
                <span class="material-symbols-outlined text-[15px] text-primary">visibility</span>
                <span>Góc nhìn Học viên</span>
              </a>
              <button
                type="button"
                id="btn-open-course-settings"
                class="px-3 py-1.5 rounded-lg bg-[#F4F1EA] dark:bg-[#262524] hover:bg-[#ECE8DF] text-[#222120] dark:text-[#EDEDEB] text-xs font-semibold flex items-center gap-1.5 transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B]"
                title="Cài đặt & Học vụ (Thông tin, Chuẩn đầu ra, Danh sách sinh viên)"
              >
                <span class="material-symbols-outlined text-[15px] text-[#8F8E8A] dark:text-[#9E9D99]">settings</span>
                <span>Cài đặt & Học vụ</span>
              </button>
            </div>
          </div>

          <!-- Rejection Banner: Previous Review Rejection -->
          ${course.status === 'DRAFT' && course.last_rejection ? `
            <div class="rounded-2xl border border-rose-300 dark:border-rose-700/60 bg-rose-50 dark:bg-rose-950/40 p-4 sm:p-5 flex items-start gap-4 shadow-xs">
              <div class="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0 border border-rose-500/20 mt-0.5">
                <span class="material-symbols-outlined text-2xl">error</span>
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-bold text-rose-900 dark:text-rose-200 flex items-center gap-2">
                  <span>Khóa học đã bị Quản trị viên từ chối phê duyệt</span>
                  ${course.last_rejection.rejected_at ? `<span class="text-xs font-normal text-rose-600 dark:text-rose-400">(${UI.formatDate(course.last_rejection.rejected_at)})</span>` : ''}
                </h4>
                <p class="text-xs text-rose-800 dark:text-rose-300 mt-1 font-medium bg-white/60 dark:bg-black/20 p-2.5 rounded-lg border border-rose-200/60 dark:border-rose-800/40">
                  <strong>Lý do từ chối:</strong> ${UI.escapeHtml(course.last_rejection.reason || 'Không có lý do cụ thể.')}
                </p>
                <p class="text-[11px] text-rose-700 dark:text-rose-400 mt-1.5">
                  Thầy/Cô vui lòng cập nhật nội dung giáo trình theo yêu cầu và nộp xét duyệt lại khi hoàn tất.
                </p>
              </div>
            </div>
          ` : ''}

          <!-- Freeze Banner: Course Submitted for Review -->
          ${course.status === 'SUBMITTED_FOR_REVIEW' ? `
            <div class="rounded-2xl border border-sky-300 dark:border-sky-700/60 bg-sky-50 dark:bg-sky-950/40 p-4 sm:p-5 flex items-start gap-4 shadow-xs">
              <div class="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center shrink-0 border border-sky-500/20 mt-0.5">
                <span class="material-symbols-outlined text-2xl">pending_actions</span>
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-bold text-sky-900 dark:text-sky-200">
                  Khóa học đang trong quá trình xét duyệt của Quản trị viên
                </h4>
                <p class="text-xs text-sky-800 dark:text-sky-300 mt-1">
                  Mọi thao tác chỉnh sửa nội dung bài giảng, chương mục và bài thi tạm thời bị đóng băng. Nếu cần chỉnh sửa thêm, Thầy/Cô vui lòng bấm <strong>"Rút lại xét duyệt"</strong> phía trên.
                </p>
              </div>
            </div>
          ` : ''}

          <!-- Course Header Banner (Warm Surface Card) -->
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-6 sm:p-8 shadow-subtle space-y-4">
            <div
              class="relative aspect-video max-h-72 w-full overflow-hidden rounded-xl border ${!course.thumbnail_url ? 'border-amber-400/80 dark:border-amber-600/80 border-dashed bg-amber-50/40 dark:bg-amber-950/20' : 'border-indigo-200 dark:border-indigo-800 bg-indigo-100 dark:bg-indigo-950'} flex flex-col items-center justify-center p-6 text-center group cursor-pointer"
              onclick="document.getElementById('course-thumbnail-input')?.click()"
              title="${course.thumbnail_url ? 'Bấm để đổi ảnh bìa' : 'Bấm để tải ảnh bìa môn học'}"
            >
              ${course.thumbnail_url ? `
                <img src="${UI.escapeHtml(course.thumbnail_url)}" alt="Ảnh đại diện khóa học" class="absolute inset-0 h-full w-full object-cover object-center" onerror="this.remove()" />
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span class="px-4 py-2 rounded-xl bg-black/70 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm">
                    <span class="material-symbols-outlined text-[16px]">photo_camera</span>
                    Đổi ảnh bìa môn học
                  </span>
                </div>
              ` : `
                <span class="absolute -right-8 -top-12 h-44 w-44 rounded-full border-[28px] border-amber-200/40 dark:border-amber-900/30" aria-hidden="true"></span>
                <div class="w-12 h-12 rounded-2xl bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center justify-center mb-2.5 border border-amber-500/30 group-hover:scale-105 transition-transform z-10">
                  <span class="material-symbols-outlined text-2xl">add_photo_alternate</span>
                </div>
                <h4 class="text-sm font-bold text-amber-950 dark:text-amber-200 z-10">Khóa học này chưa có ảnh bìa đại diện</h4>
                <p class="text-xs text-amber-900/80 dark:text-amber-300/80 mt-1 max-w-md z-10">
                  Khóa học bắt buộc phải có ảnh bìa để được duyệt xuất bản. Nhấp vào đây để tải ảnh bìa (PNG, JPEG, WebP).
                </p>
                <div class="mt-3.5 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1.5 z-10 pointer-events-none">
                  <span class="material-symbols-outlined text-[16px]">upload</span>
                  <span>Tải ảnh bìa ngay</span>
                </div>
              `}
            </div>
            <div class="flex items-center justify-between flex-wrap gap-2">
              <label class="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                <span class="material-symbols-outlined text-base">add_photo_alternate</span>
                <span>${course.thumbnail_url ? 'Đổi Ảnh Đại Diện Khóa Học' : 'Tải Ảnh Đại Diện Khóa Học'}</span>
                <input id="course-thumbnail-input" type="file" accept="image/png,image/jpeg,image/webp" class="sr-only" />
              </label>
              ${!course.thumbnail_url ? `
                <span class="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1">
                  <span class="material-symbols-outlined text-[15px]">info</span>
                  Cần có ảnh bìa trước khi gửi duyệt xuất bản
                </span>
              ` : ''}
            </div>
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="font-mono font-extrabold text-primary text-xs px-2.5 py-0.5 rounded-md bg-primary-subtle border border-primary/20">
                    ${UI.escapeHtml(course.course_code)}
                  </span>
                  ${UI.statusBadge(course.status)}
                  <span class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">•</span>
                  <span class="text-xs font-medium text-[#5C5B57] dark:text-[#9E9D99]">
                    ${UI.escapeHtml(course.category || 'Công nghệ')}
                  </span>
                </div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-[#222120] dark:text-[#EDEDEB] tracking-tight">
                  ${UI.escapeHtml(course.title)}
                </h1>
              </div>

              <!-- Quick Status Actions -->
              <div class="flex items-center gap-2 shrink-0">
                ${course.status === 'DRAFT' ? `
                  <button
                    type="button"
                    id="btn-submit-review"
                    class="px-4 py-2 rounded-xl ${course.thumbnail_url ? 'bg-amber-600 hover:bg-amber-700 text-white cursor-pointer' : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed border border-slate-300 dark:border-slate-700'} text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
                    ${!course.thumbnail_url ? 'title="Vui lòng tải ảnh bìa khóa học trước khi gửi duyệt xuất bản"' : ''}
                  >
                    <span class="material-symbols-outlined text-[16px]">send</span>
                    <span>Gửi duyệt xuất bản</span>
                  </button>
                ` : ''}
                ${course.status === 'SUBMITTED_FOR_REVIEW' ? `
                  <button
                    type="button"
                    id="btn-cancel-submit-review"
                    class="px-4 py-2 rounded-xl bg-slate-600 hover:bg-slate-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                    title="Rút lại yêu cầu xét duyệt để mở khóa quyền chỉnh sửa khóa học"
                  >
                    <span class="material-symbols-outlined text-[16px]">undo</span>
                    <span>Rút lại xét duyệt</span>
                  </button>
                ` : ''}
                ${course.status === 'APPROVED' || window.app?.currentRole === 'ADMIN' ? `
                  <button
                    type="button"
                    id="btn-publish-direct"
                    class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                  >
                    <span class="material-symbols-outlined text-[16px]">rocket_launch</span>
                    <span>Xuất bản ngay</span>
                  </button>
                ` : ''}
                ${course.status === 'PUBLISHED' ? (
                  changesetStatus && changesetStatus.status === 'PENDING' ? `
                    <button
                      type="button"
                      disabled
                      class="px-4 py-2 rounded-xl bg-amber-500/20 text-amber-700 dark:text-amber-300 text-xs font-bold flex items-center gap-1.5 cursor-not-allowed border border-amber-300 dark:border-amber-700"
                    >
                      <span class="material-symbols-outlined text-[16px]">lock_clock</span>
                      <span>Đợt cập nhật đang chờ duyệt</span>
                    </button>
                    <button
                      type="button"
                      id="btn-view-changeset-diff"
                      class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-[#202020] hover:bg-slate-200 dark:hover:bg-[#282828] text-slate-800 dark:text-slate-200 text-xs font-bold border border-slate-200 dark:border-[#2E2D2B] transition-colors flex items-center gap-1.5 cursor-pointer"
                      title="Xem đối chiếu các thay đổi giữa bản gốc và bản nháp"
                    >
                      <span class="material-symbols-outlined text-[16px]">difference</span>
                      <span>Xem thay đổi</span>
                    </button>
                    <button
                      type="button"
                      id="btn-retract-changeset"
                      class="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                      title="Rút lại đợt cập nhật để tiếp tục chỉnh sửa"
                    >
                      <span class="material-symbols-outlined text-[16px]">undo</span>
                      <span>Rút lại yêu cầu</span>
                    </button>
                  ` : changesetStatus && changesetStatus.status === 'REJECTED' ? `
                    <button
                      type="button"
                      id="btn-view-changeset-diff"
                      class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-[#202020] hover:bg-slate-200 dark:hover:bg-[#282828] text-slate-800 dark:text-slate-200 text-xs font-bold border border-slate-200 dark:border-[#2E2D2B] transition-colors flex items-center gap-1.5 cursor-pointer"
                      title="Xem đối chiếu các thay đổi"
                    >
                      <span class="material-symbols-outlined text-[16px]">difference</span>
                      <span>Xem thay đổi</span>
                    </button>
                    <button
                      type="button"
                      id="btn-submit-changeset-again"
                      class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                      title="Gửi đợt cập nhật sau khi hoàn thiện"
                    >
                      <span class="material-symbols-outlined text-[16px]">send</span>
                      <span>Gửi duyệt đợt cập nhật</span>
                    </button>
                    <button
                      type="button"
                      id="btn-discard-changeset-rejected"
                      class="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                      title="Hủy bỏ bản nháp đã bị từ chối"
                    >
                      <span class="material-symbols-outlined text-[18px]">delete_sweep</span>
                    </button>
                  ` : changesetStatus && (changesetStatus.has_changes || changesetStatus.changes_count > 0) ? `
                    <button
                      type="button"
                      id="btn-view-changeset-diff"
                      class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-[#202020] hover:bg-slate-200 dark:hover:bg-[#282828] text-slate-800 dark:text-slate-200 text-xs font-bold border border-slate-200 dark:border-[#2E2D2B] transition-colors flex items-center gap-1.5 cursor-pointer"
                      title="Xem đối chiếu các thay đổi giữa bản gốc và bản nháp"
                    >
                      <span class="material-symbols-outlined text-[16px] text-primary">difference</span>
                      <span>Xem thay đổi</span>
                      <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-primary/10 text-primary font-black">${changesetStatus.changes_count || 1}</span>
                    </button>
                    <button
                      type="button"
                      id="btn-submit-course-changeset"
                      class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                      title="Gộp và gửi xét duyệt toàn bộ cập nhật giáo trình môn học"
                    >
                      <span class="material-symbols-outlined text-[16px]">playlist_add_check</span>
                      <span>Gửi duyệt đợt cập nhật</span>
                    </button>
                    <button
                      type="button"
                      id="btn-discard-changeset"
                      class="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                      title="Hủy bỏ toàn bộ bản nháp"
                    >
                      <span class="material-symbols-outlined text-[18px]">delete_sweep</span>
                    </button>
                  ` : `
                    <button
                      type="button"
                      id="btn-submit-course-changeset"
                      class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-[#202020] text-slate-400 dark:text-slate-500 text-xs font-bold border border-slate-200 dark:border-[#2E2D2B] flex items-center gap-1.5 cursor-not-allowed"
                      disabled
                      title="Chưa có thay đổi nào trong bản nháp"
                    >
                      <span class="material-symbols-outlined text-[16px]">playlist_add_check</span>
                      <span>Gửi duyệt đợt cập nhật</span>
                    </button>
                  `
                ) : ''}
              </div>
            </div>

            <p class="text-xs sm:text-sm text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed max-w-3xl">
              ${UI.escapeHtml(course.description || 'Chưa có mô tả chi tiết cho môn học này.')}
            </p>
          </div>

          <!-- SECTION 1: SOẠN GIÁO TRÌNH TRỰC QUAN (SINGLE-PAGE CURRICULUM STUDIO) -->
          <div class="space-y-4" id="curriculum-studio-section">
            <div class="flex items-center justify-between flex-wrap gap-3">
              <div class="flex items-center gap-2.5">
                <span class="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center material-symbols-outlined text-[20px]">menu_book</span>
                <div>
                  <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB]">
                    Soạn thảo Giáo trình (Single-Page Studio)
                  </h2>
                  <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">Cột trái chọn bài học • Cột phải soạn nội dung bài giảng</p>
                </div>
              </div>
            </div>

            <!-- Flexible Studio Layout with Resizable Sidebar -->
            <div class="flex flex-col lg:flex-row gap-0 items-start relative w-full" id="single-page-curriculum-studio">
              <!-- Left Column: Cây Giáo trình (Outline Tree) -->
              <aside class="w-full lg:shrink-0 space-y-4" id="curriculum-tree-pane" style="width: 360px;">
                <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs space-y-4">
                  <div class="flex items-center justify-between pb-3 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
                    <div class="flex items-center gap-2">
                      <span class="material-symbols-outlined text-[18px] text-primary">account_tree</span>
                      <span class="text-xs font-bold uppercase tracking-wider text-[#222120] dark:text-[#EDEDEB]">Cấu trúc bài giảng</span>
                    </div>
                    <span class="text-[11px] font-semibold text-[#8F8E8A] dark:text-[#6D6C68]" id="tree-stats-badge">
                      ${learningUnits.length} Chương
                    </span>
                  </div>

                  <!-- Add Chapter Button (Only Thêm Chương per user request) -->
                  <div class="flex items-center">
                    <button
                      type="button"
                      id="btn-tree-add-unit"
                      class="w-full py-2.5 px-3 rounded-xl bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-center gap-1.5 transition-colors ${isPending || isFrozen ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
                      ${isPending || isFrozen ? 'disabled' : ''}
                      title="Thêm một Chương bài học mới"
                    >
                      <span class="material-symbols-outlined text-[16px] text-primary">create_new_folder</span>
                      <span>Thêm Chương</span>
                    </button>
                  </div>

                  <!-- Tree Content Container -->
                  <div id="tree-units-container" class="space-y-3.5 max-h-[720px] overflow-y-auto pr-1">
                    <!-- Populated dynamically -->
                  </div>
                </div>
              </aside>

              <!-- Resizer Handle (desktop only) -->
              <div
                id="curriculum-sidebar-resizer"
                class="hidden lg:flex w-4 hover:w-4 items-center justify-center cursor-col-resize select-none shrink-0 group py-4 transition-all z-10 self-stretch"
                title="Kéo để tùy chỉnh độ rộng menu Cấu trúc bài giảng"
              >
                <div class="w-1.5 h-16 rounded-full bg-[#E8E6DF] dark:bg-[#2E2D2B] group-hover:bg-primary transition-all"></div>
              </div>

              <!-- Right Column: Trình Soạn Thảo Khối Dọc (Modular Vertical Block Editor) -->
              <main class="flex-1 min-w-0 w-full" id="curriculum-editor-pane">
                <!-- Populated dynamically based on selected lesson -->
              </main>
            </div>
          </div>

        </div>
      `;

      // Bind Settings Modal Button
      container.querySelector('#btn-create-learning-unit')?.addEventListener('click', async () => {
        const title = await UI.prompt('Thêm Chương mới', 'Đặt tên cho Chương bài học chứa tối đa 10 Bài giảng.', '', 'Ví dụ: Tổng quan khóa học', 1, 'Tạo Chương', { maxLength: 200 });
        if (!title) return;
        try {
          const unit = await ApiClient.createLearningUnit(cId, { title: title.trim() });
          if (unit && unit.pending_approval) {
            UI.showToast(unit.message || 'Yêu cầu tạo Chương mới đã gửi Quản trị viên để xét duyệt.', 'info');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(document.getElementById('app-viewport') || container, cId, 'curriculum'));
            return;
          }
          UI.showToast('Đã tạo Bài học mới (bản nháp). Thầy/Cô có thể tạo các bài giảng bên trong và bấm "Gửi" khi hoàn tất.', 'success');
          UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(document.getElementById('app-viewport') || container, cId, 'curriculum'));
        } catch (error) {
          UI.showToast(error.message || 'Không tạo được Chương bài học.', 'error');
        }
      });
      container.querySelectorAll('.btn-rename-learning-unit').forEach(button => {
        button.addEventListener('click', async () => {
          const unit = learningUnits.find(item => item.learning_unit_id === button.dataset.unitId);
          if (!unit) return;
          const title = await UI.prompt('Đổi tên Bài học', `Tên mới cho "${unit.title}":`, unit.title, 'Tên Bài học', 1, 'Lưu Tên Bài Học', { maxLength: 200 });
          if (!title || title.trim() === unit.title) return;
          try {
            const response = await ApiClient.updateLearningUnit(unit.learning_unit_id, { title: title.trim() });
            UI.showToast(response.pending_approval ? 'Tên Bài học đã gửi Admin xét duyệt.' : 'Đã đổi tên Bài học.', response.pending_approval ? 'info' : 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(document.getElementById('app-viewport') || container, cId, initialTab));
          } catch (error) {
            UI.showToast(error.message || 'Không đổi được tên Bài học.', 'error');
          }
        });
      });
      
      // Initialize Single-Page Curriculum Studio
      await InstructorView.initSinglePageCurriculumStudio(
        container,
        course,
        changesetStatus,
        initialLessonId,
        initialUnitId,
        assessments
      );

container.querySelector('#course-thumbnail-input')?.addEventListener('change', async event => {
        const file = event.target.files?.[0];
        event.target.value = '';
        if (!file) return;
        if (isFrozen) {
          UI.showToast('Khóa học đang chờ Quản trị viên xét duyệt. Không thể thay đổi ảnh bìa.', 'warning');
          return;
        }
        if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
          UI.showToast('Chọn ảnh PNG, JPEG hoặc WebP.', 'warning');
          return;
        }
        try {
          const croppedFile = await UI.cropImage(file, { aspectRatio: 16 / 9, title: 'Tùy chỉnh vùng hiển thị ảnh bìa khóa học' });
          if (!croppedFile) return;
          const uploaded = await ApiClient.uploadCourseFile(cId, croppedFile, croppedFile.name, 'COURSE_IMAGE');
          await ApiClient.updateCourse(cId, { thumbnail_file_asset_id: uploaded.asset_id });
          UI.showToast('Đã cập nhật ảnh đại diện khóa học.', 'success');
          UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(document.getElementById('app-viewport') || container, cId, initialTab));
        } catch (error) {
          UI.showToast(error.message || 'Không cập nhật được ảnh đại diện.', 'error');
        }
      });

      document.getElementById('btn-open-course-settings').onclick = async () => {
        await InstructorView.openCourseSettingsModal(course, initialTab === 'curriculum' ? 'settings' : initialTab);
      };

      if (initialTab !== 'curriculum') {
        InstructorView.openCourseSettingsModal(course, initialTab);
      }

      // Bind Submit Review
      const submitRevBtn = document.getElementById('btn-submit-review');
      if (submitRevBtn) {
        submitRevBtn.onclick = async () => {
          if (!course.thumbnail_url) {
            UI.showToast('Khóa học bắt buộc phải có ảnh bìa đại diện trước khi gửi xét duyệt xuất bản!', 'warning');
            document.getElementById('course-thumbnail-input')?.click();
            return;
          }
          const conf = await UI.confirm(
            'Gửi duyệt khóa học',
            'Lưu ý: Thầy/Cô hãy đảm bảo đã tạo hoàn thiện tất cả bài giảng và đề thi (không xuất bản lắt nhắt). Xác nhận gửi khóa học này đến Ban Quản trị xét duyệt xuất bản?',
            'Gửi xét duyệt'
          );
          if (!conf) return;
          try {
            await ApiClient.submitCourseForReview(cId, 'Giảng viên đề xuất duyệt xuất bản.');
            UI.showToast('Đã gửi yêu cầu xét duyệt thành công.', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi gửi xét duyệt.', 'error');
          }
        };
      }

      // Bind Cancel Submit Review
      const cancelRevBtn = document.getElementById('btn-cancel-submit-review');
      if (cancelRevBtn) {
        cancelRevBtn.onclick = async () => {
          const conf = await UI.confirm(
            'Rút lại yêu cầu xét duyệt',
            'Khóa học sẽ quay về trạng thái Nháp (DRAFT) để Thầy/Cô tiếp tục chỉnh sửa giáo trình. Xác nhận rút lại yêu cầu?',
            'Rút lại xét duyệt'
          );
          if (!conf) return;
          try {
            await ApiClient.cancelSubmitCourse(cId);
            UI.showToast('Đã rút lại yêu cầu xét duyệt. Khóa học đã mở khóa để chỉnh sửa.', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi khi rút lại xét duyệt.', 'error');
          }
        };
      }

      // Bind Direct Publish
      const pubBtn = document.getElementById('btn-publish-direct');
      if (pubBtn) {
        pubBtn.onclick = async () => {
          const conf = await UI.confirm(
            'Xuất bản khóa học',
            'Lưu ý: Chỉ xuất bản khi toàn bộ giáo án, bài giảng và đề thi đã hoàn tất đầy đủ. Khóa học sẽ được công khai cho toàn bộ sinh viên ghi danh. Xác nhận xuất bản?',
            'Xuất bản'
          );
          if (!conf) return;
          try {
            await ApiClient.publishCourse(cId);
            UI.showToast('Khóa học đã được xuất bản chính thức thành công!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi xuất bản khóa học.', 'error');
          }
        };
      }

      // Bind Course Changeset Actions
      const openSubmitChangesetModal = () => {
        const todayStr = new Date().toLocaleDateString('vi-VN');
        const defaultTitle = `Đợt cập nhật giáo trình (${todayStr})`;
        const bodyHtml = `
          <form id="submit-changeset-form" class="space-y-4">
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
                Tên đợt cập nhật <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="version_title"
                value="${UI.escapeHtml(defaultTitle)}"
                required
                class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary"
              />
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">
                Tóm tắt thay đổi (Ghi chú cho Quản trị viên)
              </label>
              <textarea
                name="summary"
                rows="3"
                placeholder="VD: Bổ sung 2 bài thực hành, sắp xếp lại chương 1..."
                class="w-full px-3.5 py-2.5 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary resize-none"
              ></textarea>
            </div>
            <p class="text-[11px] text-slate-500 dark:text-slate-400">
              Hệ thống sẽ gom toàn bộ thay đổi giáo trình (bài học mới, nội dung chỉnh sửa, thứ tự) thành 1 đợt xét duyệt duy nhất.
            </p>
          </form>
        `;
        const footerHtml = `
          <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-colors" onclick="UI.closeModal()">
            Hủy bỏ
          </button>
          <button type="button" id="btn-confirm-submit-changeset" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs">
            Gửi Quản trị viên
          </button>
        `;
        UI.openModal({
          title: 'Gửi duyệt cập nhật giáo trình',
          bodyHtml,
          footerHtml,
          size: 'md'
        });
        document.getElementById('btn-confirm-submit-changeset').onclick = async () => {
          const form = document.getElementById('submit-changeset-form');
          if (!form) return;
          const vTitle = form.version_title.value.trim();
          const vSummary = form.summary.value.trim();
          if (!vTitle) {
            UI.showToast('Vui lòng nhập tên đợt cập nhật.', 'warning');
            return;
          }
          const btn = document.getElementById('btn-confirm-submit-changeset');
          btn.disabled = true;
          btn.innerHTML = '⏳ Đang gửi...';
          try {
            await ApiClient.submitCourseChangeset(cId, {
              version_title: vTitle,
              summary: vSummary
            });
            UI.closeModal();
            UI.showToast('Đã gửi đợt cập nhật giáo trình tới Quản trị viên!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (err) {
            btn.disabled = false;
            btn.innerHTML = 'Gửi Quản trị viên';
            UI.showToast(err.message || 'Lỗi gửi đợt cập nhật.', 'error');
          }
        };
      };

      const submitCsBtn = document.getElementById('btn-submit-course-changeset');
      if (submitCsBtn) submitCsBtn.onclick = openSubmitChangesetModal;

      const submitCsBarBtn = document.getElementById('btn-submit-course-changeset-bar');
      if (submitCsBarBtn) submitCsBarBtn.onclick = openSubmitChangesetModal;

      const submitCsAgainBtn = document.getElementById('btn-submit-changeset-again');
      if (submitCsAgainBtn) submitCsAgainBtn.onclick = openSubmitChangesetModal;

      const viewDiffBtn = document.getElementById('btn-view-changeset-diff');
      if (viewDiffBtn) {
        viewDiffBtn.onclick = async () => {
          try {
            const diff = await ApiClient.getCourseChangesetDiff(cId);
            const totalChanges = diff.total_changes_count || (
              (diff.curriculum_structure?.length || 0) +
              (diff.content_blocks?.length || 0) +
              (diff.interactive_quizzes?.length || 0) +
              ((diff.assessments || []).filter(a => a.change_type !== 'UNCHANGED').length) +
              (diff.governance_rules?.is_changed ? 1 : 0)
            );

            const bodyHtml = `
              <div class="space-y-4 text-xs font-sans">
                <!-- Summary Header -->
                <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1">
                  <div class="flex items-center justify-between gap-2">
                    <span class="font-bold text-sm text-slate-900 dark:text-slate-100">${UI.escapeHtml(diff.version_title || 'Đợt Cập Nhật Giáo Trình')}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                      ${totalChanges} thay đổi được ghi nhận
                    </span>
                  </div>
                  <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">${UI.escapeHtml(diff.summary || 'Chi tiết các thay đổi theo 5 phân nhóm học vụ so với giáo trình hiện tại.')}</p>
                </div>

                <!-- 5-Category Deep Changeset Diff Tree -->
                <div class="max-h-[520px] overflow-y-auto pr-1">
                  ${UI.renderCategorizedDiffHtml(diff)}
                </div>
              </div>
            `;
            UI.openModal({
              title: 'Đối chiếu thay đổi giáo trình (5 Phân Nhóm Học Vụ)',
              bodyHtml,
              size: 'lg'
            });
          } catch (err) {
            UI.showToast(err.message || 'Không tải được bản đối chiếu thay đổi.', 'error');
          }
        };
      }

      const retractCsBtn = document.getElementById('btn-retract-changeset');
      if (retractCsBtn) {
        retractCsBtn.onclick = async () => {
          const conf = await UI.confirm(
            'Rút lại đợt cập nhật',
            'Xác nhận rút lại đợt cập nhật đang chờ duyệt? Bạn sẽ có thể tiếp tục chỉnh sửa trước khi gửi lại.',
            'Rút lại'
          );
          if (!conf) return;
          try {
            await ApiClient.retractCourseChangeset(cId);
            UI.showToast('Đã rút lại đợt cập nhật giáo trình thành công.', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (err) {
            UI.showToast(err.message || 'Lỗi rút lại đợt cập nhật.', 'error');
          }
        };
      }

      const bindDiscardBtn = (btnId) => {
        const discardBtn = document.getElementById(btnId);
        if (discardBtn) {
          discardBtn.onclick = async () => {
            const conf = await UI.confirm(
              'Hủy bỏ bản nháp cập nhật',
              'Hành động này sẽ hủy bỏ các thay đổi đang nháp/chờ duyệt và khôi phục trạng thái ban đầu của khóa học. Xác nhận hủy bỏ?',
              'Hủy bỏ bản nháp'
            );
            if (!conf) return;
            try {
              await ApiClient.discardCourseChangeset(cId);
              UI.showToast('Đã hủy bỏ bản nháp cập nhật giáo trình.', 'info');
              UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
            } catch (err) {
              UI.showToast(err.message || 'Lỗi hủy bỏ bản nháp.', 'error');
            }
          };
        }
      };
      bindDiscardBtn('btn-discard-changeset');
      bindDiscardBtn('btn-discard-changeset-rejected');

      // Auto-poll when changeset is PENDING to reactively update view without manual F5
      if (changesetStatus.status === 'PENDING') {
        if (window._courseChangesetPollInterval) clearInterval(window._courseChangesetPollInterval);
        window._courseChangesetPollInterval = setInterval(async () => {
          if (!window.location.hash.includes(`/instructor/courses/manage?id=${cId}`)) {
            clearInterval(window._courseChangesetPollInterval);
            return;
          }
          try {
            const latestStatus = await ApiClient.getCourseChangesetStatus(cId);
            if (latestStatus && latestStatus.status !== 'PENDING') {
              clearInterval(window._courseChangesetPollInterval);
              if (latestStatus.status === 'NONE') {
                UI.showToast('Quản trị viên đã phê duyệt đợt cập nhật giáo trình của bạn!', 'success');
              } else if (latestStatus.status === 'REJECTED') {
                UI.showToast('Quản trị viên đã yêu cầu chỉnh sửa đợt cập nhật của bạn.', 'warning');
              }
              UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
            }
          } catch (e) {
            console.warn('Silent changeset poll error:', e);
          }
        }, 5000);
      }

      // Bind Delete Learning Unit
      container.querySelectorAll('.btn-delete-learning-unit').forEach(button => {
        button.addEventListener('click', async (e) => {
          e.stopPropagation();
          const unitId = button.dataset.unitId;
          const unit = learningUnits.find(item => item.learning_unit_id === unitId);
          if (!unit) return;
          const conf = await UI.confirm(
            'Xóa Bài học',
            `Bạn có chắc chắn muốn xóa bài học "${unit.title}" và toàn bộ lesson bên trong? Thao tác không thể hoàn tác.`,
            'Xóa vĩnh viễn'
          );
          if (!conf) return;
          try {
            await ApiClient.deleteLearningUnit(unitId);
            UI.showToast('Đã xóa bài học thành công.', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
          } catch (error) {
            UI.showToast(error.message || 'Không thể xóa bài học.', 'error');
          }
        });
      });

      // Bind Submit Learning Unit (Gửi duyệt Chương/Bài học mới)
      container.querySelectorAll('.btn-submit-learning-unit').forEach(button => {
        button.addEventListener('click', async (e) => {
          e.stopPropagation();
          const unitId = button.dataset.unitId;
          const unitTitle = button.dataset.unitTitle || 'Bài học này';
          const conf = await UI.confirm(
            'Gửi duyệt bài học',
            `Xác nhận gửi bài học "${unitTitle}" và toàn bộ các bài giảng bên trong tới Quản trị viên để xét duyệt xuất bản?`,
            'Gửi xét duyệt'
          );
          if (!conf) return;
          try {
            const res = await ApiClient.submitLearningUnit(unitId, cId);
            UI.showToast(res.message || 'Đã gửi yêu cầu xét duyệt bài học thành công.', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (error) {
            UI.showToast(error.message || 'Không thể gửi yêu cầu xét duyệt.', 'error');
          }
        });
      });

      // Bind Move Learning Unit Up
      container.querySelectorAll('.btn-move-unit-up').forEach(btn => {
        btn.onclick = async (e) => {
          e.stopPropagation();
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx <= 0 || idx >= learningUnits.length) return;
          const reordered = [...learningUnits];
          const temp = reordered[idx];
          reordered[idx] = reordered[idx - 1];
          reordered[idx - 1] = temp;
          const orderedIds = reordered.map(u => u.learning_unit_id);
          try {
            await ApiClient.reorderLearningUnits(cId, orderedIds);
            UI.showToast('Đã di chuyển bài học lên!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài học.', 'error');
          }
        };
      });

      // Bind Move Learning Unit Down
      container.querySelectorAll('.btn-move-unit-down').forEach(btn => {
        btn.onclick = async (e) => {
          e.stopPropagation();
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx < 0 || idx >= learningUnits.length - 1) return;
          const reordered = [...learningUnits];
          const temp = reordered[idx];
          reordered[idx] = reordered[idx + 1];
          reordered[idx + 1] = temp;
          const orderedIds = reordered.map(u => u.learning_unit_id);
          try {
            await ApiClient.reorderLearningUnits(cId, orderedIds);
            UI.showToast('Đã di chuyển bài học xuống!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài học.', 'error');
          }
        };
      });

      // Bind Drag & Drop Reordering for Learning Units
      let draggedUnitIdx = null;
      container.querySelectorAll('.unit-row-card').forEach(card => {
        card.addEventListener('dragstart', (e) => {
          if (e.target.closest('button') || e.target.closest('a')) {
            e.preventDefault();
            return;
          }
          draggedUnitIdx = parseInt(card.dataset.idx, 10);
          card.classList.add('opacity-40');
          e.dataTransfer.effectAllowed = 'move';
        });
        card.addEventListener('dragend', () => {
          card.classList.remove('opacity-40');
        });
        card.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
        });
        card.addEventListener('drop', async (e) => {
          e.preventDefault();
          const targetIdx = parseInt(card.dataset.idx, 10);
          if (draggedUnitIdx === null || draggedUnitIdx === targetIdx) return;
          const reordered = [...learningUnits];
          const [moved] = reordered.splice(draggedUnitIdx, 1);
          reordered.splice(targetIdx, 0, moved);
          const orderedIds = reordered.map(u => u.learning_unit_id);
          try {
            await ApiClient.reorderLearningUnits(cId, orderedIds);
            UI.showToast('Đã sắp xếp lại thứ tự bài học thành công!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài học.', 'error');
          }
        });
      });

      // Bind Assessment Results Modal
      container.querySelectorAll('.btn-asm-results').forEach(btn => {
        btn.onclick = () => {
          const asmId = btn.dataset.asmId;
          InstructorView.openAssessmentResultsModal(cId, asmId);
        };
      });

      // Bind Publish Assessment
      container.querySelectorAll('.btn-publish-asm').forEach(btn => {
        btn.onclick = async () => {
          const asmId = btn.dataset.asmId;
          const conf = await UI.confirm('Xuất bản bài thi', 'Sinh viên sẽ có thể nhìn thấy và tham gia thi. Xác nhận xuất bản?', 'Xuất bản');
          if (!conf) return;
          try {
            await ApiClient.publishAssessment(asmId);
            UI.showToast('Đã xuất bản đề thi thành công!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, 'curriculum'));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi khi xuất bản bài thi.', 'error');
          }
        };
      });

      container.querySelectorAll('.btn-trash-asm').forEach(btn => {
        btn.onclick = async () => {
          const assessmentId = btn.dataset.asmId;
          const title = btn.dataset.asmTitle || 'bài thi này';
          const confirmed = await UI.confirm(
            'Chuyển bài thi vào thùng rác',
            `Bài thi “${title}” sẽ được gỡ khỏi danh sách đang sử dụng. Lịch sử làm bài vẫn được bảo toàn.`,
            'Chuyển vào thùng rác'
          );
          if (!confirmed) return;
          btn.disabled = true;
          try {
            await ApiClient.trashAssessment(assessmentId, 'Giảng viên yêu cầu lưu trữ bài thi.');
            btn.closest('.assessment-row')?.remove();
            UI.showToast('Đã chuyển bài thi vào thùng rác; lịch sử bài làm được giữ lại.', 'success');
          } catch (error) {
            btn.disabled = false;
            UI.showToast(error.message || 'Không thể chuyển bài thi vào thùng rác.', 'error');
          }
        };
      });

    } catch (err) {
      console.error('[InstructorView.renderCourseManage] Lỗi nạp khóa học:', err);
      container.innerHTML = `
        <div class="py-4 sm:py-6 lg:py-8 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
          <div class="flex items-center justify-between text-xs text-[#5C5B57] dark:text-[#9E9D99] font-medium">
            <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Danh sách khóa học</span>
            </a>
          </div>
          <div class="p-8 sm:p-12 rounded-2xl bg-white dark:bg-[#18181b] border border-rose-200 dark:border-rose-900/50 text-center space-y-4 shadow-sm">
            <div class="w-14 h-14 rounded-2xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto">
              <span class="material-symbols-outlined text-[28px]">error_outline</span>
            </div>
            <div class="space-y-1">
              <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">Không thể nạp dữ liệu khóa học</h2>
              <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
                Khóa học không tồn tại, đã bị gỡ bỏ hoặc bạn không có quyền quản lý khóa học này.
              </p>
              <p class="text-[11px] font-mono text-rose-500/90 dark:text-rose-400/90 pt-1">
                Chi tiết lỗi: ${UI.escapeHtml(err.message || 'Không tìm thấy khóa học.')}
              </p>
            </div>
            <div class="pt-2 flex flex-wrap items-center justify-center gap-3">
              <a href="#/instructor/courses" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer">
                <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                <span>Quay lại danh sách khóa học</span>
              </a>
              <button type="button" class="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer" onclick="window.location.reload()">
                <span class="material-symbols-outlined text-[16px]">refresh</span>
                <span>Tải lại trang</span>
              </button>
            </div>
          </div>
        </div>
      `;
    }
  }

  // =========================================================================
  // 3.0. Course Settings & Academic Governance Modal
  // =========================================================================
  static async openCourseSettingsModal(course, defaultSubTab = 'settings') {
    const cId = course.course_id || course.id;

    // Refresh course from backend to guarantee latest persistent data
    try {
      const freshCourse = await ApiClient.getCourseDetail(cId);
      if (freshCourse) {
        Object.assign(course, freshCourse);
      }
    } catch {
      // Use existing course object if offline or network glitch
    }

    const modalHtml = `
      <div class="space-y-4">
        <!-- Sub-tabs Navigation: Modern Segmented Control -->
        <div class="p-1 rounded-xl bg-[#F4F1EA] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] inline-flex items-center gap-1 w-full sm:w-auto">
          <button
            type="button"
            class="course-modal-subtab flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-bold transition-all bg-white dark:bg-[#1E1E1E] text-primary shadow-xs"
            data-subtab="settings"
          >
            <span class="flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">tune</span>
              <span>Cài đặt chung</span>
            </span>
          </button>
          <button
            type="button"
            class="course-modal-subtab flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-medium text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-white/50 dark:hover:bg-white/5 transition-all"
            data-subtab="academic"
          >
            <span class="flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">verified</span>
              <span>Chuẩn đầu ra & Học vụ</span>
            </span>
          </button>
          <button
            type="button"
            class="course-modal-subtab flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-medium text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-white/50 dark:hover:bg-white/5 transition-all"
            data-subtab="students"
          >
            <span class="flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">groups</span>
              <span>Danh sách sinh viên</span>
            </span>
          </button>
        </div>

        <!-- Sub-tab Content Container -->
        <div id="course-modal-subtab-content" class="pt-1"></div>
      </div>
    `;

    UI.openModal({
      title: `
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
            <span class="material-symbols-outlined text-[17px]">settings</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="font-bold text-[#222120] dark:text-[#EDEDEB]">Cài đặt & Học vụ</span>
            <span class="px-2 py-0.5 rounded-md bg-[#F4F1EA] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99] font-mono text-xs font-bold border border-[#E8E6DF] dark:border-[#383734]">${UI.escapeHtml(course.course_code || '')}</span>
          </div>
        </div>
      `,
      bodyHtml: modalHtml,
      footerHtml: `
        <div class="flex items-center justify-between w-full">
          <div class="text-[11px] text-[#8F8E8A] flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[14px]">shield_check</span>
            <span>Mọi thay đổi học vụ được lưu trữ an toàn</span>
          </div>
          <button type="button" class="px-4 py-2 rounded-xl text-xs font-bold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B]" onclick="UI.closeModal()">
            Đóng
          </button>
        </div>
      `,
      size: 'xl'
    });

    const subtabBtns = document.querySelectorAll('.course-modal-subtab');
    const contentBox = document.getElementById('course-modal-subtab-content');

    const switchSubtab = (tab) => {
      subtabBtns.forEach(btn => {
        if (btn.dataset.subtab === tab) {
          btn.className = 'course-modal-subtab flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-bold transition-all bg-white dark:bg-[#1E1E1E] text-primary shadow-xs';
        } else {
          btn.className = 'course-modal-subtab flex-1 sm:flex-initial px-4 py-2 rounded-lg text-xs font-medium text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-white/50 dark:hover:bg-white/5 transition-all';
        }
      });

      if (tab === 'settings') {
        InstructorView.renderTabSettings(contentBox, course);
      } else if (tab === 'academic') {
        InstructorView.renderTabAcademic(contentBox, course);
      } else if (tab === 'students') {
        InstructorView.renderTabStudents(contentBox, cId);
      }
    };

    subtabBtns.forEach(btn => {
      btn.onclick = () => switchSubtab(btn.dataset.subtab);
    });

    switchSubtab(defaultSubTab === 'curriculum' ? 'settings' : defaultSubTab);
  }

  // =========================================================================
  // 3.1. Tab Curriculum Studio (Interactive Module & Lesson Studio Bar)
  // =========================================================================
  static renderTabCurriculum(tabContainer, course) {
    const lessons = course.lessons || [];
    const cId = course.course_id || course.id;

    tabContainer.innerHTML = `
      <div class="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        <!-- LEFT 8/12: CURRICULUM STUDIO ACCORDION -->
        <div class="xl:col-span-8 space-y-6">
          
          <!-- Module & Lesson Studio Bar -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-primary/20 shadow-sm p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-primary/[0.03] via-white to-white dark:from-primary/[0.05] dark:via-slate-900 dark:to-slate-900">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-[22px]">developer_board</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Quản lý cấu trúc môn học (Curriculum Studio)</h2>
                  <span class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[11px] font-bold">
                    ${lessons.length} Bài giảng
                  </span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Thêm mới, sắp xếp thứ tự và quản lý hiển thị bài giảng theo chuẩn kiểm định.</p>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-2 shrink-0 self-start md:self-auto">
              <a
                href="#/student/lessons/reader?course_id=${cId}&preview=1"
                class="px-4 py-2 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
                title="Xem trước toàn bộ khóa học với cây thư mục bài học (Góc nhìn học viên)"
              >
                <span class="material-symbols-outlined text-[18px] text-primary">visibility</span>
                <span>Xem trước khóa học</span>
              </a>
              <button
                type="button"
                id="btn-open-lesson-studio"
                class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
              >
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>Soạn bài giảng mới</span>
              </button>
            </div>
          </div>

          <!-- Lessons List -->
          <div class="space-y-3" id="curriculum-lessons-list">
            ${lessons.length === 0 ? `
              <div class="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
                <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">menu_book</span>
                <p class="font-bold text-slate-700 dark:text-slate-300 text-sm">Chưa có bài giảng nào trong giáo trình</p>
                <p class="mt-1 mb-4 text-slate-400">Bắt đầu xây dựng đề cương môn học bằng cách soạn bài giảng đầu tiên.</p>
                <button
                  type="button"
                  class="px-5 py-2.5 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center gap-2"
                  onclick="window.location.hash = '#/instructor/courses/${cId}/lessons/new'"
                >
                  <span class="material-symbols-outlined text-[16px]">edit_note</span>
                  <span>Mở Trình Soạn thảo Bài giảng Low-Tech</span>
                </button>
              </div>
            ` : lessons.map((l, idx) => {
              const lId = l.lesson_id || l.id;
              return `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary/40 rounded-2xl p-4 shadow-sm transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group">
                  <div class="flex items-start sm:items-center gap-3.5">
                    <span class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono font-bold flex items-center justify-center text-xs shrink-0">
                      ${idx + 1}
                    </span>
                    <div class="space-y-1">
                      <div class="flex items-center gap-2 flex-wrap">
                        <h3 class="font-bold text-sm text-slate-900 dark:text-white group-hover:text-primary transition-colors ${l.is_staged_delete ? 'line-through opacity-60' : ''}">
                          ${UI.escapeHtml(l.title)}
                        </h3>
                        ${l.is_staged_delete ? `
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300 dark:border-rose-800 shrink-0 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[13px]">delete</span>
                            <span>Đánh dấu xóa</span>
                          </span>
                        ` : l.is_new ? `
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 shrink-0 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[13px]">add_circle</span>
                            <span>Mới tạo</span>
                          </span>
                        ` : (l.is_modified || l.previous_lesson_id) ? `
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 shrink-0 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[13px]">edit_note</span>
                            <span>Đã sửa</span>
                          </span>
                        ` : UI.statusBadge(l.status)}
                      </div>
                      <div class="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                        <span class="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                          <span class="material-symbols-outlined text-[14px]">verified</span>
                          Đã quét sạch ClamAV - An toàn
                        </span>
                        ${l.summary ? `<span>•</span> <span class="truncate max-w-xs text-slate-500">${UI.escapeHtml(l.summary)}</span>` : ''}
                      </div>
                    </div>
                  </div>

                  <!-- Item Actions -->
                  <div class="flex items-center gap-2 self-end sm:self-auto shrink-0">
                    <a
                      href="#/instructor/courses/${cId}/lessons/${lId}/edit"
                      class="px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors flex items-center gap-1"
                      title="Sửa nội dung bài giảng trực quan"
                    >
                      <span class="material-symbols-outlined text-[15px]">edit</span>
                      <span>Soạn nội dung</span>
                    </a>
                    <a
                      href="#/student/lessons/reader?course_id=${cId}&lesson_id=${lId}&preview=1"
                      class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition-colors flex items-center gap-1"
                      title="Xem trước góc nhìn học viên với cây thư mục bài học"
                    >
                      <span class="material-symbols-outlined text-[15px]">visibility</span>
                      <span>Xem thử</span>
                    </a>
                    <button
                      type="button"
                      class="btn-delete-lesson p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-400 hover:text-rose-600 transition-colors"
                      data-lesson-id="${lId}"
                      title="Xóa bài học"
                    >
                      <span class="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>

        </div>

        <!-- RIGHT 4/12: COURSE VAULT, STORAGE & SECURITY WIDGETS -->
        <div class="xl:col-span-4 space-y-6">
          
          <!-- Class Attendance & Health Pill -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px] text-emerald-600">monitor_heart</span>
                <span>Chuyên cần & Tương tác</span>
              </h3>
              <span class="text-xs font-bold text-emerald-600">Tuần 09 / 15</span>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl text-center">
                <span class="text-[11px] text-slate-400 block">Lớp PWD301_L01</span>
                <span class="text-emerald-600 font-extrabold text-base">95.4%</span>
                <span class="text-[10px] text-slate-400 block">Chuyên cần</span>
              </div>
              <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl text-center">
                <span class="text-[11px] text-slate-400 block">Lớp PWD301_L02</span>
                <span class="text-emerald-600 font-extrabold text-base">92.8%</span>
                <span class="text-[10px] text-slate-400 block">Chuyên cần</span>
              </div>
            </div>

            <button
              type="button"
              class="w-full py-2.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
              onclick="UI.showToast('Tính năng gửi thông báo khẩn qua email & SMS đã sẵn sàng.', 'info')"
            >
              <span class="material-symbols-outlined text-[17px] text-primary">campaign</span>
              <span>Gửi thông báo khẩn toàn khóa</span>
            </button>
          </div>

          <!-- Storage Quota & ClamAV Fortress -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px] text-primary">cloud</span>
                <span>Dung lượng lưu trữ giáo trình</span>
              </span>
              <span class="font-bold text-slate-500">128 MB / 5.0 GB</span>
            </div>
            <div class="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div class="h-full bg-primary rounded-full" style="width: 3.2%"></div>
            </div>
            <div class="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 text-[11px] text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px] text-emerald-600">shield</span>
              <span>Toàn bộ tệp tin bài giảng được quét an toàn mã độc tự động bởi ClamAV Daemon.</span>
            </div>
          </div>

        </div>

      </div>
    `;

    document.getElementById('btn-open-lesson-studio').onclick = () => {
      window.location.hash = `#/instructor/courses/${cId}/lessons/new`;
    };

    // Attach delete lesson handlers
    tabContainer.querySelectorAll('.btn-delete-lesson').forEach(btn => {
      btn.onclick = async () => {
        const lId = btn.dataset.lessonId;
        const conf = await UI.confirm('Xóa bài học', 'Bạn có chắc muốn xóa bài giảng này khỏi giáo trình?', 'Xóa');
        if (!conf) return;

        try {
          const res = await ApiClient.deleteLesson(cId, lId);
          if (res && (res.pending_approval || res.status === 'pending_approval')) {
            UI.showToast(res.message || 'Yêu cầu xóa bài giảng đã được gửi tới Ban quản trị để xét duyệt.', 'info');
          } else {
            UI.showToast('Đã xóa bài giảng thành công!', 'success');
          }
          UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(document.getElementById('course-manage-root').parentElement, cId, 'curriculum'));
        } catch (e) {
          UI.showToast(e.message || 'Lỗi xóa bài giảng.', 'error');
        }
      };
    });
  }

  // =========================================================================
  // 3.2. Tab Academic ABET SLO Dossier
  // =========================================================================
  static async renderTabAcademic(tabContainer, course) {
    const cId = course.course_id || course.id;
    let customSLOs = [];
    if (course.learning_objectives !== null && course.learning_objectives !== undefined) {
      if (Array.isArray(course.learning_objectives)) {
        customSLOs = course.learning_objectives.map((item, idx) => {
          if (typeof item === 'object' && item !== null) {
            return {
              title: item.title || item.name || item.code || `SLO-${idx + 1}`,
              description: item.description || item.content || '',
              weight: item.weight || ''
            };
          }
          return { title: `SLO-${idx + 1}`, description: String(item), weight: '' };
        });
      } else if (typeof course.learning_objectives === 'string') {
        try {
          const parsed = JSON.parse(course.learning_objectives);
          if (Array.isArray(parsed)) {
            customSLOs = parsed.map((item, idx) => {
              if (typeof item === 'object' && item !== null) {
                return {
                  title: item.title || item.name || item.code || `SLO-${idx + 1}`,
                  description: item.description || item.content || '',
                  weight: item.weight || ''
                };
              }
              return { title: `SLO-${idx + 1}`, description: String(item), weight: '' };
            });
          }
        } catch {
          customSLOs = course.learning_objectives.split('\n').filter(s => s.trim()).map((s, i) => ({
            title: `SLO-${i + 1}`,
            description: s.trim(),
            weight: ''
          }));
        }
      }
    }
    // Only fall back to default template if the course has never configured any SLOs (null or undefined)
    if ((course.learning_objectives === null || course.learning_objectives === undefined) && customSLOs.length === 0) {
      customSLOs = [
        { title: 'SLO-1 • Phân tích & Giải quyết Vấn đề', description: 'Sinh viên có khả năng phân tích một bài toán kỹ thuật phần mềm phức tạp và áp dụng các nguyên lý máy tính để xác định giải pháp phù hợp.', weight: '30%' },
        { title: 'SLO-2 • Thiết kế Hệ thống & Kiểm thử', description: 'Sinh viên có khả năng thiết kế, cài đặt và đánh giá giải pháp dựa trên máy tính nhằm đáp ứng tập hợp các yêu cầu điện toán xác định theo chuẩn kiến trúc RESTful & CSDL quan hệ.', weight: '50%' },
        { title: 'SLO-3 • Giao tiếp & Tài liệu Kỹ thuật', description: 'Sinh viên có khả năng truyền đạt hiệu quả các luận điểm kỹ thuật trong các ngữ cảnh chuyên môn khác nhau qua báo cáo tài liệu và mã nguồn chuẩn chỉnh.', weight: '20%' }
      ];
    }

    tabContainer.innerHTML = `
      <div class="space-y-6 max-w-[1720px] w-full mx-auto animate-fade-in" id="academic-tab-root">
        
        <!-- TOPBAR: Unified Academic Controls & Single Save Action -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-indigo-600 text-[24px]">school</span>
              <span>Cài đặt & Chuẩn mực Học vụ</span>
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Quản lý Chuẩn đầu ra (SLOs), Đồ thị Môn tiên quyết và Quy chuẩn hoàn thành khóa học tập trung tại một nơi.
            </p>
          </div>
          <div class="flex items-center gap-3 shrink-0">
            <span id="academic-pending-badge" class="hidden px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 flex items-center gap-1.5 shadow-2xs">
              <span class="material-symbols-outlined text-[15px] text-amber-600">hourglass_top</span>
              <span>Đang chờ Admin xét duyệt</span>
            </span>
            <button type="button" id="btn-save-academic-settings" class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer">
              <span class="material-symbols-outlined text-[18px]">save</span>
              <span>Lưu thay đổi học vụ</span>
            </button>
          </div>
        </div>

        <!-- CARD 1: Chuẩn đầu ra (SLO) -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">verified</span>
                <h3 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                  1. Chuẩn đầu ra (Student Learning Outcomes - SLO)
                </h3>
                <!-- Icon dấu chấm hỏi ? có popover giải thích khi rê chuột hoặc bấm -->
                <div class="relative inline-flex items-center" id="slo-help-wrapper">
                  <button
                    type="button"
                    id="btn-slo-help-trigger"
                    class="w-5 h-5 rounded-full bg-slate-100 hover:bg-primary/10 text-slate-500 hover:text-primary dark:bg-slate-800 dark:text-slate-400 dark:hover:text-primary transition-all flex items-center justify-center cursor-pointer shadow-2xs"
                    title="Bấm hoặc rê chuột để xem giải thích Chuẩn đầu ra (SLO)"
                    aria-label="Giải thích Chuẩn đầu ra"
                  >
                    <span class="material-symbols-outlined text-[15px]">help</span>
                  </button>

                  <!-- Micro Popover Giải thích SLO -->
                  <div
                    id="slo-help-popover"
                    class="hidden absolute left-0 top-full mt-2 w-80 sm:w-96 p-4 rounded-xl bg-white dark:bg-[#1E1E1E] border border-slate-200 dark:border-slate-800 shadow-xl z-50 text-xs leading-relaxed space-y-2.5 animate-in fade-in"
                  >
                    <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                      <div class="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                        <span class="material-symbols-outlined text-primary text-[17px]">lightbulb</span>
                        <span>Chuẩn đầu ra (SLO) là gì?</span>
                      </div>
                      <button type="button" id="btn-close-slo-popover" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded cursor-pointer">
                        <span class="material-symbols-outlined text-[14px]">close</span>
                      </button>
                    </div>
                    <div class="space-y-1.5 text-slate-600 dark:text-slate-300">
                      <p>
                        <strong class="text-primary font-semibold">Student Learning Outcomes (SLO):</strong> Bản cam kết năng lực, kiến thức và kỹ năng thực tế mà người học chắc chắn sẽ tự tay làm được sau khi hoàn thành môn học.
                      </p>
                      <div class="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 text-[11px] text-slate-500 dark:text-slate-400 border-l-2 border-primary">
                        <em>Ví dụ: "Tự tay thiết kế và triển khai được hệ thống RESTful API an toàn, có xác thực phân quyền."</em>
                      </div>
                      <p class="text-[11px] text-slate-400 dark:text-slate-500">
                        Giảng viên dựa vào các chuẩn này để xây dựng đề thi công bằng và phục vụ kiểm định chất lượng đào tạo (ABET CAC Criterion 3).
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                Quy định cụ thể những năng lực, kỹ năng thực tế mà sinh viên sẽ làm được sau khóa học. Các chuẩn này được ánh xạ vào ma trận ngân hàng đề thi và hồ sơ kiểm định quốc tế ABET CAC Criterion 3.
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button type="button" id="btn-add-slo" class="px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-2xs">
                <span class="material-symbols-outlined text-[16px] text-primary">add</span>
                <span>Thêm Chuẩn đầu ra</span>
              </button>
            </div>
          </div>

          <!-- Micro-Guide Callout for Instructors -->
          <div class="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 text-xs text-amber-900 dark:text-amber-300 space-y-1">
            <div class="font-bold flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[17px] text-amber-600">lightbulb</span>
              <span>Khuyến nghị sư phạm cho Giảng viên:</span>
            </div>
            <p class="text-[11px] leading-relaxed">
              Hãy đặt tên chuẩn đầu ra rõ ràng, hướng hành động (ví dụ: <em>"Kỹ năng 1: Thiết kế và triển khai CSDL quan hệ 3NF"</em>) thay vì chỉ để mã kỹ thuật cộc lốc. Điều này giúp cả sinh viên, phụ huynh và hội đồng học vụ dễ dàng hiểu được giá trị thực tế của môn học.
            </p>
          </div>

          <div class="space-y-3" id="slo-items-list"></div>
        </div>

        <!-- CARD 2: Course Prerequisites Matrix -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-indigo-600 text-[20px]">account_tree</span>
                <span>2. Danh sách Môn học Tiên quyết (Prerequisites)</span>
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">Quy định điều kiện các môn học sinh viên bắt buộc phải thi đạt trước khi được phép ghi danh vào môn này. (Hệ thống tự động kiểm tra đồ thị phụ thuộc để ngăn ngừa vòng lặp môn học).</p>
            </div>
            <button type="button" id="btn-open-prereq-modal" class="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm shrink-0">
              <span class="material-symbols-outlined text-[16px]">add_link</span>
              <span>Thêm môn tiên quyết</span>
            </button>
          </div>

          <div id="prereqs-table-box" class="space-y-3">
            <div class="p-8 text-center text-slate-400 text-xs">
              <span class="inline-block animate-spin text-lg mb-1">⏳</span>
              <p>Đang kiểm tra danh sách môn học tiên quyết...</p>
            </div>
          </div>
        </div>

        <!-- CARD 3: Course Completion Rules -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
          <div class="pb-4 border-b border-slate-100 dark:border-slate-800">
            <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-emerald-600 text-[20px]">workspace_premium</span>
              <span>3. Điều kiện hoàn thành khóa học</span>
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">Tiêu chuẩn nghiệm thu học vụ tự động để sinh viên được công nhận hoàn thành khóa học và cấp chứng chỉ số.</p>
          </div>

          <form id="completion-rules-form" class="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
            <div class="space-y-2">
              <label class="block font-bold text-slate-700 dark:text-slate-300">Tiến độ bài học tối thiểu (%)</label>
              <input type="number" min="0" max="100" id="rule-min-progress" class="w-full h-10 px-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-slate-900 dark:text-white outline-none focus:border-primary" value="80" />
              <span class="text-[11px] text-slate-400">Sinh viên phải xem và hoàn thành ít nhất tỉ lệ này của các bài học.</span>
            </div>

            <div class="space-y-2">
              <label class="block font-bold text-slate-700 dark:text-slate-300">Điểm khảo thí trung bình tối thiểu (Thang 10)</label>
              <input type="number" step="0.1" min="0" max="10" id="rule-min-score" class="w-full h-10 px-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-slate-900 dark:text-white outline-none focus:border-primary" value="5.0" />
              <span class="text-[11px] text-slate-400">Điểm tổng kết các bài khảo thí bắt buộc phải đạt ngưỡng này trở lên.</span>
            </div>

            <div class="space-y-3 pt-2">
              <label class="flex items-center gap-2.5 cursor-pointer font-bold text-slate-800 dark:text-slate-200">
                <input type="checkbox" id="rule-require-lessons" class="rounded text-primary focus:ring-primary w-4 h-4" checked />
                <span>Bắt buộc hoàn thành 100% bài học tiên quyết</span>
              </label>
              <label class="flex items-center gap-2.5 cursor-pointer font-bold text-slate-800 dark:text-slate-200">
                <input type="checkbox" id="rule-require-assessments" class="rounded text-primary focus:ring-primary w-4 h-4" checked />
                <span>Bắt buộc nộp bài khảo thí chính thức (Midterm/Final)</span>
              </label>
              <label class="flex items-center gap-2.5 cursor-pointer font-bold text-slate-800 dark:text-slate-200">
                <input type="checkbox" id="rule-allow-certificate" class="rounded text-primary focus:ring-primary w-4 h-4" checked />
                <span>Tự động cấp Chứng nhận hoàn thành (Digital Certificate)</span>
              </label>
            </div>
          </form>
        </div>

      </div>
    `;

    // 0. Wire SLO Help Popover (Click & Hover)
    const helpTrigger = document.getElementById('btn-slo-help-trigger');
    const helpPopover = document.getElementById('slo-help-popover');
    const closePopoverBtn = document.getElementById('btn-close-slo-popover');
    let popoverTimeout = null;

    if (helpTrigger && helpPopover) {
      const showPopover = () => {
        if (popoverTimeout) clearTimeout(popoverTimeout);
        helpPopover.classList.remove('hidden');
      };
      const hidePopover = (delay = 200) => {
        if (popoverTimeout) clearTimeout(popoverTimeout);
        popoverTimeout = setTimeout(() => {
          helpPopover.classList.add('hidden');
        }, delay);
      };

      helpTrigger.addEventListener('mouseenter', () => showPopover());
      helpTrigger.addEventListener('mouseleave', () => hidePopover(250));
      helpPopover.addEventListener('mouseenter', () => showPopover());
      helpPopover.addEventListener('mouseleave', () => hidePopover(200));

      helpTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        if (helpPopover.classList.contains('hidden')) {
          showPopover();
        } else {
          helpPopover.classList.add('hidden');
        }
      });

      closePopoverBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        helpPopover.classList.add('hidden');
      });

      const onDocClick = (e) => {
        if (!helpTrigger.contains(e.target) && !helpPopover.contains(e.target)) {
          helpPopover.classList.add('hidden');
        }
      };
      document.addEventListener('click', onDocClick);
    }

    // 1. Render SLOs helper
    const sloContainer = document.getElementById('slo-items-list');
    const colors = ['text-primary', 'text-indigo-600', 'text-purple-600', 'text-emerald-600'];

    const harvestDOMtoSLOs = () => {
      const cards = sloContainer ? sloContainer.querySelectorAll('[data-slo-idx]') : [];
      if (!cards || cards.length === 0) return customSLOs;
      const gathered = [];
      cards.forEach((card, idx) => {
        const titleInput = card.querySelector('.slo-title-input');
        const weightInput = card.querySelector('.slo-weight-input');
        const descInput = card.querySelector('.slo-desc-input');
        const title = (titleInput ? titleInput.value : '').trim() || `SLO-${idx + 1}`;
        const weight = (weightInput ? weightInput.value : '').trim();
        const description = (descInput ? descInput.value : '').trim();
        gathered.push({ title, description, weight });
      });
      customSLOs = gathered;
      return gathered;
    };

    const renderSLOList = () => {
      if (!sloContainer) return;
      if (customSLOs.length === 0) {
        sloContainer.innerHTML = `
          <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
            Chưa có chuẩn đầu ra nào được thiết lập. Nhấp "+ Thêm Chuẩn đầu ra" để tạo mới.
          </div>
        `;
        return;
      }

      sloContainer.innerHTML = customSLOs.map((slo, idx) => {
        const title = typeof slo === 'object' ? (slo.title || `SLO-${idx + 1}`) : `SLO-${idx + 1}`;
        const text = typeof slo === 'object' ? (slo.description || slo.content || '') : String(slo);
        const weight = typeof slo === 'object' ? (slo.weight || '') : '';

        return `
          <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-2 relative group" data-slo-idx="${idx}">
            <div class="flex items-center justify-between">
              <input type="text" class="slo-title-input font-mono text-xs font-bold ${colors[idx % colors.length]} bg-transparent border-0 border-b border-transparent focus:border-primary outline-none px-1 py-0.5 w-2/3" value="${UI.escapeHtml(title)}" placeholder="VD: SLO-${idx + 1} • Kỹ năng: Lập trình Web và Thiết kế CSDL..." />
              <div class="flex items-center gap-2">
                <input type="text" class="slo-weight-input text-[11px] text-slate-400 bg-transparent border-0 border-b border-transparent focus:border-primary outline-none px-1 w-24 text-right" value="${UI.escapeHtml(weight)}" placeholder="Trọng số 30%" />
                <button type="button" class="btn-del-slo p-1 text-slate-400 hover:text-rose-600 transition-colors" data-idx="${idx}" title="Xóa chuẩn đầu ra">
                  <span class="material-symbols-outlined text-[16px]">delete</span>
                </button>
              </div>
            </div>
            <textarea class="slo-desc-input w-full p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-700 dark:text-slate-300 leading-relaxed outline-none focus:border-primary resize-none" rows="2" placeholder="Mô tả cụ thể: Sau khi học xong, sinh viên có thể tự tay làm được những gì...">${UI.escapeHtml(text)}</textarea>
          </div>
        `;
      }).join('');

      sloContainer.querySelectorAll('.btn-del-slo').forEach(btn => {
        btn.onclick = () => {
          harvestDOMtoSLOs();
          const idx = parseInt(btn.dataset.idx, 10);
          customSLOs.splice(idx, 1);
          renderSLOList();
        };
      });

      sloContainer.querySelectorAll('.slo-title-input').forEach((inp, i) => {
        inp.oninput = (e) => {
          if (typeof customSLOs[i] !== 'object') customSLOs[i] = { title: '', description: '' };
          customSLOs[i].title = e.target.value;
        };
      });

      sloContainer.querySelectorAll('.slo-weight-input').forEach((inp, i) => {
        inp.oninput = (e) => {
          if (typeof customSLOs[i] !== 'object') customSLOs[i] = { title: '', description: '' };
          customSLOs[i].weight = e.target.value;
        };
      });

      sloContainer.querySelectorAll('.slo-desc-input').forEach((inp, i) => {
        inp.oninput = (e) => {
          if (typeof customSLOs[i] !== 'object') customSLOs[i] = { title: '', description: '' };
          customSLOs[i].description = e.target.value;
        };
      });
    };

    renderSLOList();

    const addSloBtn = document.getElementById('btn-add-slo');
    if (addSloBtn) {
      addSloBtn.onclick = () => {
        harvestDOMtoSLOs();
        customSLOs.push({
          title: `SLO-${customSLOs.length + 1} • Tiêu chuẩn Năng lực Mới`,
          description: '',
          weight: '20%'
        });
        renderSLOList();
      };
    }

    // 2. Prerequisites List with Staging State
    const prereqBox = document.getElementById('prereqs-table-box');
    let stagedPrerequisites = [];

    const renderPrerequisitesTable = () => {
      if (!prereqBox) return;

      if (stagedPrerequisites.length === 0) {
        prereqBox.innerHTML = `
          <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-xs space-y-1">
            <span class="material-symbols-outlined text-slate-300 dark:text-slate-600 text-3xl">task_alt</span>
            <p class="font-semibold text-slate-600 dark:text-slate-300">Không có điều kiện tiên quyết</p>
            <p class="text-[11px] text-slate-400">Sinh viên có thể trực tiếp ghi danh môn học này mà không cần hoàn thành học phần trước.</p>
          </div>
        `;
      } else {
        prereqBox.innerHTML = `
          <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table class="w-full text-left border-collapse text-xs">
              <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th class="p-3">Mã & Tên môn tiên quyết</th>
                  <th class="p-3">Điểm GPA tối thiểu</th>
                  <th class="p-3">Trạng thái phê duyệt</th>
                  <th class="p-3 text-right">Tác vụ</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                ${stagedPrerequisites.map((p, idx) => {
                  const isDeleted = !!p.is_deleted;
                  const isNew = !!p.is_new;
                  const targetId = p.course_id || p.prerequisite_course_id || p.id;
                  let rowCls = 'hover:bg-slate-50/50 dark:hover:bg-slate-800/40';
                  let statusBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300">Đã phê duyệt</span>`;
                  if (isDeleted) {
                    rowCls = 'bg-rose-50/40 dark:bg-rose-950/20 opacity-60 line-through';
                    statusBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300">Chờ gỡ bỏ</span>`;
                  } else if (isNew) {
                    statusBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-300">Mới thêm (Chờ lưu)</span>`;
                  } else if (p.approval_status === 'PENDING_APPROVAL') {
                    statusBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300">Chờ GV khác phê duyệt</span>`;
                  } else if (p.approval_status === 'REJECTED') {
                    statusBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300">Bị từ chối</span>`;
                  }

                  return `
                    <tr class="${rowCls}">
                      <td class="p-3">
                        <span class="font-mono font-bold text-primary">${UI.escapeHtml(p.course_code || p.prerequisite_course_code || 'PREREQ')}</span>
                        <span class="text-slate-800 dark:text-slate-200 ml-1.5">${UI.escapeHtml(p.title || p.prerequisite_course_title || 'Môn học tiên quyết')}</span>
                      </td>
                      <td class="p-3">
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          ${p.min_grade_point ? `≥ ${p.min_grade_point}` : '≥ 5.0 (C)'}
                        </span>
                      </td>
                      <td class="p-3">
                        ${statusBadge}
                      </td>
                      <td class="p-3 text-right">
                        ${isDeleted ? `
                          <button type="button" class="btn-undo-del-prereq px-2.5 py-1 rounded-lg text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 transition font-bold" data-prereq-idx="${idx}">
                            Hoàn tác
                          </button>
                        ` : `
                          <button type="button" class="btn-del-prereq px-2.5 py-1 rounded-lg text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition font-bold" data-prereq-idx="${idx}" data-prereq-id="${targetId}">
                            Gỡ bỏ
                          </button>
                        `}
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        `;
      }

      // Attach delete & undo handlers
      prereqBox.querySelectorAll('.btn-del-prereq').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.prereqIdx, 10);
          if (stagedPrerequisites[idx]) {
            if (stagedPrerequisites[idx].is_new) {
              stagedPrerequisites.splice(idx, 1);
            } else {
              stagedPrerequisites[idx].is_deleted = true;
            }
            renderPrerequisitesTable();
          }
        };
      });

      prereqBox.querySelectorAll('.btn-undo-del-prereq').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.prereqIdx, 10);
          if (stagedPrerequisites[idx]) {
            stagedPrerequisites[idx].is_deleted = false;
            renderPrerequisitesTable();
          }
        };
      });
      // End of renderPrerequisitesTable
    };


    const loadPrerequisites = async () => {
      try {
        const res = await ApiClient.getCoursePrerequisites(cId);
        const list = (res && res.prerequisites) ? res.prerequisites : (Array.isArray(res) ? res : []);
        stagedPrerequisites = list.map(item => ({
          ...item,
          course_id: item.course_id || item.prerequisite_course_id || item.id,
          is_new: false,
          is_deleted: false,
        }));
        renderPrerequisitesTable();
      } catch (err) {
        prereqBox.innerHTML = `<div class="p-4 text-center text-rose-500 text-xs">Lỗi nạp điều kiện tiên quyết: ${UI.escapeHtml(err.message || err)}</div>`;
      }
    };

    await loadPrerequisites();

    // Open Prerequisite Modal with Staging
    const openPrereqBtn = document.getElementById('btn-open-prereq-modal');
    if (openPrereqBtn) {
      openPrereqBtn.onclick = async () => {
        let myCourses = [];
        let catalogCourses = [];
        try {
          const [cRes, catRes] = await Promise.allSettled([
            ApiClient.getInstructorCourses(),
            ApiClient.getCatalogCourses()
          ]);
          myCourses = (cRes.status === 'fulfilled' && cRes.value) ? (cRes.value.courses || (Array.isArray(cRes.value) ? cRes.value : [])) : [];
          catalogCourses = (catRes.status === 'fulfilled' && catRes.value) ? (catRes.value.courses || catRes.value.items || (Array.isArray(catRes.value) ? catRes.value : [])) : [];
        } catch {
          myCourses = [];
          catalogCourses = [];
        }

        const map = new Map();
        for (const c of [...myCourses, ...catalogCourses]) {
          const key = c.course_id || c.id;
          const status = c.status || 'PUBLISHED';
          if (key && key !== cId && status === 'PUBLISHED' && !map.has(key)) {
            map.set(key, c);
          }
        }
        const candidateCourses = Array.from(map.values()).sort((a, b) => {
          const aMine = myCourses.some(mc => (mc.course_id || mc.id) === (a.course_id || a.id));
          const bMine = myCourses.some(mc => (mc.course_id || mc.id) === (b.course_id || b.id));
          if (aMine && !bMine) return -1;
          if (!aMine && bMine) return 1;
          return (a.title || '').localeCompare(b.title || '');
        });

        const modalHtml = `
          <div class="space-y-4">
            <div class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">Chọn môn học bắt buộc tiên quyết</label>
              <select id="modal-prereq-select" class="w-full h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-xs text-slate-900 dark:text-white outline-none focus:border-primary">
                ${candidateCourses.map(c => {
                  const isMine = myCourses.some(mc => (mc.course_id || mc.id) === (c.course_id || c.id));
                  const badge = isMine ? '★ [Môn của bạn - Dùng được ngay]' : '[Giảng viên khác - Cần gửi xét duyệt]';
                  return `<option value="${c.course_id || c.id}" data-code="${UI.escapeHtml(c.course_code || '')}" data-title="${UI.escapeHtml(c.title || '')}">${c.course_code || 'MÔN'} - ${UI.escapeHtml(c.title)} ${badge}</option>`;
                }).join('')}
              </select>
              <p class="text-[11px] text-slate-400 mt-1">Lưu ý: Môn học của giảng viên khác sẽ tự động gửi yêu cầu xin duyệt đến giảng viên phụ trách khi bấm Lưu thay đổi học vụ.</p>
            </div>

            <div class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">Điểm GPA tối thiểu yêu cầu (Thang 4 hoặc 10)</label>
              <input type="number" step="0.1" min="0" max="10" id="modal-prereq-min-grade" class="w-full h-10 px-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-xs text-slate-900 dark:text-white outline-none focus:border-primary" value="5.0" />
            </div>

            <div class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">Lý do học thuật / Căn cứ đề cương</label>
              <input type="text" id="modal-prereq-reason" class="w-full h-10 px-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white outline-none focus:border-primary" placeholder="VD: Bắt buộc nắm vững kiến thức Lập trình cơ sở..." value="Yêu cầu tiên quyết chuẩn hóa theo đề cương đào tạo" />
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <button type="button" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold cursor-pointer" onclick="UI.closeModal()">Hủy</button>
              <button type="button" id="modal-prereq-submit-btn" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm cursor-pointer">Thêm vào danh sách</button>
            </div>
          </div>
        `;

        UI.openModal({
          title: 'Thiết lập Môn học Tiên quyết',
          bodyHtml: modalHtml,
          size: 'md'
        });

        const subBtn = document.getElementById('modal-prereq-submit-btn');
        if (subBtn) {
          subBtn.onclick = () => {
            const selectEl = document.getElementById('modal-prereq-select');
            const prereqCourseId = selectEl?.value;
            const selectedOpt = selectEl?.selectedOptions?.[0];
            const courseCode = selectedOpt?.dataset?.code || 'PREREQ';
            const courseTitle = selectedOpt?.dataset?.title || 'Môn tiên quyết';
            const minGrade = parseFloat(document.getElementById('modal-prereq-min-grade')?.value || '5.0');
            const reason = document.getElementById('modal-prereq-reason')?.value || '';

            if (!prereqCourseId) {
              UI.showToast('Vui lòng chọn môn học tiên quyết.', 'warning');
              return;
            }

            // Check if already in staged
            const existing = stagedPrerequisites.find(p => (p.course_id || p.prerequisite_course_id || p.id) === prereqCourseId);
            if (existing) {
              if (existing.is_deleted) {
                existing.is_deleted = false;
                existing.min_grade_point = minGrade;
                existing.reason = reason;
                UI.closeModal();
                renderPrerequisitesTable();
                UI.showToast('Đã khôi phục môn tiên quyết vào danh sách.', 'info');
                return;
              }
              UI.showToast('Môn học này đã có trong danh sách tiên quyết.', 'warning');
              return;
            }

            stagedPrerequisites.push({
              course_id: prereqCourseId,
              prerequisite_course_id: prereqCourseId,
              course_code: courseCode,
              title: courseTitle,
              min_grade_point: minGrade,
              reason: reason,
              is_new: true,
              is_deleted: false,
            });

            UI.closeModal();
            renderPrerequisitesTable();
            UI.showToast('Đã thêm môn tiên quyết vào danh sách tạm. Nhấp "Lưu thay đổi học vụ" để áp dụng.', 'info');
          };
        }
      };
    }

    // 3. Load Completion Rules
    const loadCompletionRules = async () => {
      try {
        const rule = await ApiClient.getCourseCompletionRules(cId);
        if (rule) {
          const pEl = document.getElementById('rule-min-progress');
          const sEl = document.getElementById('rule-min-score');
          const lEl = document.getElementById('rule-require-lessons');
          const aEl = document.getElementById('rule-require-assessments');
          const cEl = document.getElementById('rule-allow-certificate');

          if (pEl && rule.minimum_progress_percent !== undefined) pEl.value = rule.minimum_progress_percent;
          if (sEl && rule.minimum_grade_score !== undefined) sEl.value = rule.minimum_grade_score;
          if (lEl && rule.require_all_required_lessons !== undefined) lEl.checked = !!rule.require_all_required_lessons;
          if (aEl && rule.require_required_assessments !== undefined) aEl.checked = !!rule.require_required_assessments;
          if (cEl && rule.allow_certificate !== undefined) cEl.checked = !!rule.allow_certificate;
        }
      } catch (err) {
        console.warn('Could not load completion rules:', err);
      }
    };

    await loadCompletionRules();

    // 4. UNIFIED SAVE ACTION: Lưu Toàn Bộ Cài Đặt & Học Vụ
    const saveAcademicBtn = document.getElementById('btn-save-academic-settings');
    const pendingBadge = document.getElementById('academic-pending-badge');

    if (saveAcademicBtn) {
      saveAcademicBtn.onclick = async () => {
        try {
          saveAcademicBtn.disabled = true;
          saveAcademicBtn.innerHTML = `<span class="inline-block animate-spin text-[14px]">⏳</span> <span>Đang lưu...</span>`;

          let hasPendingApproval = false;

          // 4.1. Save SLOs
          const toSaveSLOs = harvestDOMtoSLOs();
          const sloRes = await ApiClient.updateCourse(cId, { learning_objectives: toSaveSLOs });
          course.learning_objectives = toSaveSLOs;
          customSLOs = [...toSaveSLOs];
          if (sloRes && (sloRes.pending_approval || sloRes.status === 'pending_approval')) {
            hasPendingApproval = true;
          }

          // 4.2. Save Completion Rules
          const rulesPayload = {
            minimum_progress_percent: parseFloat(document.getElementById('rule-min-progress')?.value || '80'),
            minimum_grade_score: parseFloat(document.getElementById('rule-min-score')?.value || '5.0'),
            completion_grace_days: 14,
            require_all_required_lessons: Boolean(document.getElementById('rule-require-lessons')?.checked),
            require_required_assessments: Boolean(document.getElementById('rule-require-assessments')?.checked),
            allow_certificate: Boolean(document.getElementById('rule-allow-certificate')?.checked),
          };
          await ApiClient.updateCourseCompletionRules(cId, rulesPayload);

          const prereqErrors = [];

          // 4.3. Sync Staged Prerequisites
          const toDelete = stagedPrerequisites.filter(p => p.is_deleted && !p.is_new);
          for (const item of toDelete) {
            const pId = item.course_id || item.prerequisite_course_id || item.id;
            try {
              const delRes = await ApiClient.deleteCoursePrerequisite(cId, pId);
              if (delRes && (delRes.pending_approval || delRes.status === 'pending_approval')) {
                hasPendingApproval = true;
              }
            } catch (delErr) {
              console.warn('Failed to delete prereq:', pId, delErr);
              prereqErrors.push(`Xóa môn ${item.course_code || pId}: ${delErr.message || delErr}`);
            }
          }

          const toAdd = stagedPrerequisites.filter(p => p.is_new && !p.is_deleted);
          for (const item of toAdd) {
            const pId = item.course_id || item.prerequisite_course_id || item.id;
            try {
              const addRes = await ApiClient.addCoursePrerequisite(cId, {
                prerequisite_course_id: pId,
                min_grade_point: item.min_grade_point || 5.0,
                reason: item.reason || 'Yêu cầu chuẩn hóa đề cương'
              });
              if (addRes && (addRes.status === 'pending_approval' || addRes.pending_approval)) {
                hasPendingApproval = true;
              }
            } catch (addErr) {
              console.warn('Failed to add prereq:', pId, addErr);
              prereqErrors.push(`Thêm môn ${item.course_code || pId}: ${addErr.message || addErr}`);
            }
          }

          // 4.4. Refresh state
          await loadPrerequisites();

          if (prereqErrors.length > 0) {
            UI.showToast(`Lưu học vụ hoàn tất một phần. Có lỗi môn tiên quyết: ${prereqErrors.join('; ')}`, 'warning');
          } else if (hasPendingApproval) {
            if (pendingBadge) pendingBadge.classList.remove('hidden');
            UI.showToast('Khóa học đã ban hành: Một số thay đổi học vụ đã được gửi tới Quản trị viên để xét duyệt!', 'info');
          } else {
            UI.showToast('Đã lưu toàn bộ Cài đặt & Chuẩn mực Học vụ thành công!', 'success');
          }
        } catch (err) {
          UI.showToast('Lỗi lưu cài đặt học vụ: ' + (err.message || err), 'error');
        } finally {
          saveAcademicBtn.disabled = false;
          saveAcademicBtn.innerHTML = `<span class="material-symbols-outlined text-[18px]">save</span><span>Lưu thay đổi học vụ</span>`;
        }
      };
    }
  }

  // =========================================================================
  // 3.3. Tab Student Roster Management
  // =========================================================================
  static async renderTabStudents(tabContainer, courseId) {
    tabContainer.innerHTML = `
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden" id="students-roster-box">
        <div class="p-16 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs">Đang tải danh sách học viên ghi danh...</p>
        </div>
      </div>
    `;

    try {
      const res = await ApiClient.listCourseStudents(courseId);
      const items = res.items || [];
      const box = document.getElementById('students-roster-box');

      if (items.length === 0) {
        box.innerHTML = `
          <div class="p-16 text-center text-slate-400 text-xs">
            <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">group_off</span>
            <p class="font-bold text-slate-700 dark:text-slate-300 text-sm">Chưa có sinh viên nào ghi danh</p>
            <p class="mt-1 text-slate-400">Sinh viên sẽ xuất hiện tại đây sau khi ghi danh khóa học.</p>
          </div>
        `;
        return;
      }

      box.innerHTML = `
        <table class="w-full text-left text-sm border-collapse">
          <thead class="bg-slate-50/70 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
            <tr>
              <th class="px-5 py-3.5">Học viên</th>
              <th class="px-5 py-3.5">Email</th>
              <th class="px-5 py-3.5">Trạng thái</th>
              <th class="px-5 py-3.5">Tiến độ bài học</th>
              <th class="px-5 py-3.5">Chuyên cần</th>
              <th class="px-5 py-3.5">Ngày ghi danh</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs">
            ${items.map(s => `
              <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-7 h-7 rounded-lg bg-primary/10 text-primary font-bold flex items-center justify-center text-xs">
                      ${UI.escapeHtml((s.student_name || 'H').substring(0, 1).toUpperCase())}
                    </div>
                    <span class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(s.student_name || 'Học viên')}</span>
                  </div>
                </td>
                <td class="px-5 py-3.5 font-mono text-[11px] text-slate-500">${UI.escapeHtml(s.student_email || '')}</td>
                <td class="px-5 py-3.5">${UI.statusBadge(s.status)}</td>
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-2">
                    <div class="w-24 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div class="h-full bg-primary rounded-full" style="width: ${Math.round(s.current_progress_percent || 0)}%"></div>
                    </div>
                    <span class="font-bold text-primary">${Math.round(s.current_progress_percent || 0)}%</span>
                  </div>
                </td>
                <td class="px-5 py-3.5 font-bold text-emerald-600">95.0%</td>
                <td class="px-5 py-3.5 text-slate-400">${UI.formatDate(s.enrolled_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (e) {
      document.getElementById('students-roster-box').innerHTML = `
        <div class="p-8 text-center text-rose-500 font-bold">Lỗi nạp danh sách: ${UI.escapeHtml(e.message)}</div>
      `;
    }
  }

  // =========================================================================
  // 3.4. Tab Assessments
  // =========================================================================
  static async renderTabAssessment(tabContainer, course) {
    const cId = course.course_id || course.id;
    tabContainer.innerHTML = `
      <div class="space-y-6 max-w-[1720px] w-full mx-auto">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-base font-bold text-slate-900 dark:text-white">Kỳ thi & Bài kiểm tra đánh giá</h2>
            <p class="text-xs text-slate-500 mt-0.5">Danh sách các bài Quiz, Giữa kỳ và Cuối kỳ của khóa học.</p>
          </div>
          <a
            href="#/instructor/exams?course_id=${cId}"
            class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-[16px]">add_circle</span>
            <span>Soạn đề thi mới</span>
          </a>
        </div>

        <div id="course-assessments-list-box" class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm divide-y divide-slate-100 dark:divide-slate-800">
          <div class="py-8 text-center text-slate-400">
            <span class="inline-block animate-spin text-xl mb-2">⏳</span>
            <p class="text-xs">Đang tải danh sách kỳ thi...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const res = await ApiClient.getCourseAssessments(cId);
      const assessments = res.items || res.assessments || (Array.isArray(res) ? res : []);
      const listBox = document.getElementById('course-assessments-list-box');

      if (!listBox) return;

      if (assessments.length === 0) {
        listBox.innerHTML = `
          <div class="py-12 text-center text-slate-400">
            <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">quiz</span>
            <p class="text-sm font-semibold text-slate-700 dark:text-slate-300">Chưa có đề thi/bài kiểm tra nào trong khóa học này.</p>
            <p class="text-xs text-slate-400 mt-1">Hãy tạo bài kiểm tra hoặc soạn đề thi tự động chuẩn PWD301 LMS.</p>
            <a href="#/instructor/exams?course_id=${cId}" class="inline-flex items-center gap-1.5 px-4 py-2 mt-4 rounded-xl bg-primary text-white text-xs font-bold shadow-sm">
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Tạo đề thi ngay</span>
            </a>
          </div>
        `;
        return;
      }

      listBox.innerHTML = assessments.map(a => {
        const qCount = a.questions_count !== undefined ? a.questions_count : (a.questions ? a.questions.length : 0);
        const isPub = a.status === 'PUBLISHED';
        return `
          <div class="py-4 flex items-center justify-between gap-4 first:pt-0 last:pb-0">
            <div class="flex items-center gap-3">
              <span class="w-10 h-10 rounded-xl ${isPub ? 'bg-indigo-50 dark:bg-indigo-950/40 text-primary' : 'bg-amber-50 dark:bg-amber-950/40 text-amber-600'} flex items-center justify-center material-symbols-outlined text-[20px]">quiz</span>
              <div>
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(a.title || 'Bài kiểm tra')}</h3>
                <div class="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                  <span>${a.duration_minutes || 60} phút</span>
                  <span>•</span>
                  <span>${qCount} câu hỏi</span>
                  <span>•</span>
                  <span class="${isPub ? 'text-emerald-600' : 'text-amber-600'} font-semibold">${isPub ? 'Đã xuất bản (PUBLISHED)' : (a.status || 'Bản nháp')}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              ${!isPub ? `
                <button
                  type="button"
                  class="btn-publish-assessment px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-xs"
                  data-asm-id="${a.assessment_id || a.id}"
                >
                  <span class="material-symbols-outlined text-[15px]">publish</span>
                  <span>Xuất bản</span>
                </button>
              ` : ''}
              <a
                href="#/instructor/courses/${cId}/assessments/${a.assessment_id || a.id}/results"
                class="px-3.5 py-1.5 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[15px]">bar_chart</span>
                <span>Bảng điểm & Bài nộp</span>
              </a>
              <a
                href="#/instructor/exams/edit?id=${a.assessment_id || a.id}&course_id=${cId}"
                class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors inline-flex items-center gap-1"
                title="Chỉnh sửa cấu hình và danh sách câu hỏi đề thi"
              >
                <span class="material-symbols-outlined text-[15px]">edit</span>
                <span>Chỉnh sửa</span>
              </a>
            </div>
          </div>
        `;
      }).join('');

      listBox.querySelectorAll('.btn-publish-assessment').forEach(btn => {
        btn.onclick = async () => {
          const asmId = btn.dataset.asmId;
          const conf = await UI.confirm('Xuất bản đề thi', 'Bạn có chắc chắn muốn xuất bản đề thi này để sinh viên có thể bắt đầu làm bài?', 'Xuất bản');
          if (!conf) return;
          try {
            btn.disabled = true;
            btn.textContent = 'Đang xuất bản...';
            await ApiClient.publishAssessment(asmId);
            UI.showToast('Đã xuất bản đề thi thành công!', 'success');
            UI.refreshCurrentRoute(() => InstructorView.renderTabAssessment(tabContainer, course));
          } catch (pubErr) {
            UI.showToast('Lỗi xuất bản đề thi: ' + (pubErr.message || pubErr), 'error');
            btn.disabled = false;
            btn.textContent = 'Xuất bản';
          }
        };
      });
    } catch (err) {
      const listBox = document.getElementById('course-assessments-list-box');
      if (listBox) {
        listBox.innerHTML = `<div class="p-4 text-center text-rose-500 text-xs">Lỗi nạp danh sách kỳ thi: ${UI.escapeHtml(err.message)}</div>`;
      }
    }
  }

  static openAssessmentResultsModal(arg1, arg2) {
    let assessmentId = arg1;
    let courseId = null;
    const isIdPattern = (v) => typeof v === 'string' && (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v) || /^\d+$/.test(v));
    if (isIdPattern(arg1) && isIdPattern(arg2)) {
      courseId = arg1;
      assessmentId = arg2;
    } else if (arg2 && isIdPattern(arg2)) {
      assessmentId = arg2;
    } else {
      assessmentId = arg1;
    }
    const targetUrl = courseId
      ? `#/instructor/courses/${courseId}/assessments/${assessmentId}/results`
      : `#/instructor/assessments/${assessmentId}/results`;
    window.location.hash = targetUrl;
  }

  static async renderAssessmentResultsPage(container, assessmentId, courseId = null, page = 1) {
    const backUrl = courseId
      ? `#/instructor/courses/${courseId}/manage?tab=exams`
      : '#/instructor/exams';
    const backText = courseId ? 'Quay lại Quản lý Khóa học' : 'Quay lại Soạn đề thi';

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in py-4 sm:py-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10">
        <!-- Breadcrumb & Back navigation -->
        <div class="flex items-center justify-between gap-4">
          <a href="${backUrl}" class="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-primary transition-colors">
            <span class="material-symbols-outlined text-base">arrow_back</span>
            <span>${backText}</span>
          </a>
        </div>

        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
              <span class="material-symbols-outlined text-primary text-2xl">assessment</span>
              Bảng điểm & Kết quả Khảo thí Trắc nghiệm
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1" id="asm-results-title">Đang tải dữ liệu bài nộp...</p>
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              id="export-gradebook-pdf-btn"
              class="px-4 py-2.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-xs transition cursor-pointer"
            >
              <span class="material-symbols-outlined text-[18px]">picture_as_pdf</span>
              <span>Xuất bảng điểm PDF</span>
            </button>
          </div>
        </div>

        <!-- Dynamic Results Content Container -->
        <div class="space-y-6" id="asm-results-content">
          <div class="py-16 text-center text-slate-400">
            <span class="inline-block animate-spin text-3xl mb-2">⏳</span>
            <p class="text-xs font-semibold">Đang tổng hợp điểm số và báo cáo vi phạm thí sinh...</p>
          </div>
        </div>
      </div>
    `;

    const exportPdfBtn = document.getElementById('export-gradebook-pdf-btn');
    if (exportPdfBtn) {
      exportPdfBtn.onclick = async () => {
        const originalContent = exportPdfBtn.innerHTML;
        try {
          exportPdfBtn.classList.add('opacity-70', 'pointer-events-none');
          exportPdfBtn.innerHTML = '<span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span> <span>Đang tạo PDF...</span>';
          const pdfUrl = `/instructor/assessments/${encodeURIComponent(assessmentId)}/gradebook.pdf`;
          const res = await fetch(pdfUrl, {
            headers: { 'Accept': 'application/pdf' },
            credentials: 'same-origin'
          });
          if (!res.ok) {
            let errMsg = 'Không thể xuất bảng điểm PDF.';
            try {
              const errJson = await res.json();
              if (errJson.error?.message) errMsg = errJson.error.message;
              else if (errJson.message) errMsg = errJson.message;
            } catch (_) {}
            throw new Error(errMsg);
          }
          const blob = await res.blob();
          let filename = `bang_diem_mon_thi_${assessmentId}.pdf`;
          const disposition = res.headers.get('Content-Disposition') || '';
          const fnMatch = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
          if (fnMatch) {
            filename = decodeURIComponent(fnMatch[1] || fnMatch[2]);
          }
          const blobUrl = window.URL.createObjectURL(blob);
          const tempA = document.createElement('a');
          tempA.href = blobUrl;
          tempA.download = filename;
          document.body.appendChild(tempA);
          tempA.click();
          setTimeout(() => {
            document.body.removeChild(tempA);
            window.URL.revokeObjectURL(blobUrl);
          }, 1000);
          UI.showToast('Đã tải xuống bảng điểm lớp (PDF) thành công!', 'success');
        } catch (err) {
          UI.showToast(err.message || 'Lỗi xuất tệp PDF.', 'error');
        } finally {
          exportPdfBtn.classList.remove('opacity-70', 'pointer-events-none');
          exportPdfBtn.innerHTML = originalContent;
        }
      };
    }

    try {
      const data = await ApiClient.getAssessmentAttempts(assessmentId, page);
      const attempts = data.attempts || [];
      const releasedAttempts = attempts.filter(att => att.score_status === 'RELEASED');
      const currentPage = Number(data.page || 1);
      const totalPages = Number(data.pages || 1);
      const titleEl = document.getElementById('asm-results-title');
      if (titleEl) {
        titleEl.textContent = `Đề thi: ${data.assessment_title || 'Khảo thí trắc nghiệm'} • Tổng cộng ${data.total ?? attempts.length} bài nộp`;
      }

      const contentEl = document.getElementById('asm-results-content');
      if (!contentEl) return;

      if (attempts.length === 0) {
        contentEl.innerHTML = `
          <div class="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8">
            <span class="material-symbols-outlined text-5xl text-slate-300 dark:text-slate-600 mb-2">assignment_late</span>
            <p class="text-sm font-bold text-slate-700 dark:text-slate-300">Chưa có sinh viên nào nộp bài</p>
            <p class="text-xs text-slate-400 mt-1">Bài thi này chưa ghi nhận lượt làm bài hoặc nộp bài hoàn tất nào.</p>
          </div>
        `;
        return;
      }

      const totalSubmissions = attempts.length;
      const passedCount = releasedAttempts.filter(a => a.is_passed === true || a.passed === true).length;
      const passRate = releasedAttempts.length > 0 ? Math.round((passedCount / releasedAttempts.length) * 100) : 0;
      const avgScore = releasedAttempts.length > 0
        ? (releasedAttempts.reduce((acc, a) => acc + Number(a.percentage ?? a.percent_score ?? 0), 0) / releasedAttempts.length).toFixed(1)
        : '—';

      contentEl.innerHTML = `
        <!-- Stats Row -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <span class="text-xs text-slate-500 font-medium">Tổng số bài nộp</span>
            <div class="text-2xl font-black text-slate-900 dark:text-white mt-1">${totalSubmissions}</div>
          </div>
          <div class="bg-emerald-50/50 dark:bg-emerald-950/20 p-5 rounded-2xl border border-emerald-200 dark:border-emerald-800 shadow-xs">
            <span class="text-xs text-emerald-600 font-medium">Tỷ lệ đạt</span>
            <div class="text-2xl font-black text-emerald-700 dark:text-emerald-400 mt-1">${passRate}% <span class="text-xs font-normal text-emerald-600">(${passedCount}/${totalSubmissions})</span></div>
          </div>
          <div class="bg-indigo-50/50 dark:bg-indigo-950/20 p-5 rounded-2xl border border-indigo-200 dark:border-indigo-800 shadow-xs">
            <span class="text-xs text-indigo-600 font-medium">Điểm trung bình</span>
            <div class="text-2xl font-black text-indigo-700 dark:text-indigo-400 mt-1">${avgScore}%</div>
          </div>
        </div>

        <!-- Table of Attempts with Vi phạm column -->
        <div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/80 text-slate-500 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th class="px-5 py-3.5">Thí sinh</th>
                <th class="px-5 py-3.5">Thời gian nộp</th>
                <th class="px-5 py-3.5">Điểm số</th>
                <th class="px-5 py-3.5">Tỷ lệ</th>
                <th class="px-5 py-3.5">Kết quả</th>
                <th class="px-5 py-3.5 text-center text-rose-600 dark:text-rose-400">Vi phạm</th>
                <th class="px-5 py-3.5 text-right">Chi tiết bài làm</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              ${attempts.map(att => {
                const released = att.score_status === 'RELEASED';
                const passed = released && (att.is_passed === true || att.passed === true);
                const submittedDate = att.submitted_at ? new Date(att.submitted_at).toLocaleString('vi-VN') : 'Đang làm';
                const pct = released ? (att.percentage ?? att.percent_score ?? '—') : '—';
                const vCount = att.violations_count ?? att.violation_count ?? 0;
                return `
                  <tr class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td class="px-5 py-3.5">
                      <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(att.student_name || 'Học viên')}</div>
                      <div class="text-[11px] text-slate-400">${UI.escapeHtml(att.student_email || '')}</div>
                    </td>
                    <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300 font-mono">${submittedDate}</td>
                    <td class="px-5 py-3.5 font-mono font-bold text-slate-900 dark:text-white">${released ? `${att.raw_score} / ${att.max_possible_points}` : 'Chờ chấm'}</td>
                    <td class="px-5 py-3.5 font-bold ${released ? (passed ? 'text-emerald-600' : 'text-rose-600') : 'text-amber-600'}">${released ? `${pct}%` : 'Chờ chấm'}</td>
                    <td class="px-5 py-3.5">
                      <span class="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold ${!released ? 'bg-amber-100 text-amber-800 border border-amber-200' : passed ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800'}">
                        ${!released ? 'CHỜ CHẤM' : passed ? 'ĐẠT' : 'KHÔNG ĐẠT'}
                      </span>
                    </td>
                    <td class="px-5 py-3.5 text-center">
                      ${vCount > 0 ? `
                        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-100 text-rose-700 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-300 dark:border-rose-800 shadow-2xs">
                          <span class="material-symbols-outlined text-[13px]">warning</span>
                          <span>${vCount} lần</span>
                        </span>
                      ` : `
                        <span class="text-xs font-semibold text-slate-400">0</span>
                      `}
                    </td>
                    <td class="px-5 py-3.5 text-right">
                      <button
                        type="button"
                        class="px-3 py-1.5 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors inline-flex items-center gap-1 cursor-pointer"
                        onclick="InstructorView.openAttemptDetailModal('${att.attempt_id}')"
                      >
                        <span class="material-symbols-outlined text-[14px]">visibility</span>
                        <span>Đối chiếu bài làm</span>
                      </button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
        ${totalPages > 1 ? `
          <div class="flex items-center justify-between text-xs">
            <span class="text-slate-500">Trang ${currentPage}/${totalPages}</span>
            <div class="flex gap-2">
              <button type="button" id="asm-results-prev" class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 ${currentPage <= 1 ? 'opacity-50' : ''}" ${currentPage <= 1 ? 'disabled' : ''}>Trang trước</button>
              <button type="button" id="asm-results-next" class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 ${currentPage >= totalPages ? 'opacity-50' : ''}" ${currentPage >= totalPages ? 'disabled' : ''}>Trang sau</button>
            </div>
          </div>
        ` : ''}
      `;
      const previousButton = document.getElementById('asm-results-prev');
      const nextButton = document.getElementById('asm-results-next');
      if (previousButton) previousButton.onclick = () => InstructorView.renderAssessmentResultsPage(container, assessmentId, courseId, currentPage - 1);
      if (nextButton) nextButton.onclick = () => InstructorView.renderAssessmentResultsPage(container, assessmentId, courseId, currentPage + 1);
    } catch (err) {
      const contentEl = document.getElementById('asm-results-content');
      if (contentEl) {
        contentEl.innerHTML = `
          <div class="p-8 text-center space-y-3 text-rose-600">
            <p class="text-sm font-semibold">Không thể tải kết quả khảo thí.</p>
            <p class="text-xs">${UI.escapeHtml(err.message || 'Lỗi hệ thống')}</p>
            <div class="flex justify-center gap-2">
              <a href="${backUrl}" class="px-4 py-2 rounded-xl border border-slate-300 text-xs font-semibold">Quay lại</a>
              <button type="button" id="retry-assessment-results-btn" class="px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold">Thử lại</button>
            </div>
          </div>
        `;
        document.getElementById('retry-assessment-results-btn')?.addEventListener(
          'click',
          () => InstructorView.renderAssessmentResultsPage(container, assessmentId, courseId, page),
        );
      }
    }
  }

  static async openAttemptDetailModal(attemptId, accessReason = '') {
    const modalId = 'modal-attempt-detail';
    const previousFocus = document.activeElement;
    let modal = document.getElementById(modalId);
    if (!modal) {
      modal = document.createElement('div');
      modal.id = modalId;
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-labelledby', 'modal-att-title');
      modal.className = 'fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden" tabindex="-1">
        <div class="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 id="modal-att-title" class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">fact_check</span>
              Chi tiết câu trả lời & Đối chiếu đáp án
            </h3>
            <p class="text-xs text-slate-500 mt-0.5" id="modal-att-student">Đang nạp bài làm...</p>
          </div>
          <button type="button" aria-label="Đóng chi tiết bài làm" class="attempt-detail-close w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <div class="p-6 overflow-y-auto space-y-6" id="modal-att-content">
          <div class="py-12 text-center text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-xs">Đang tải từng câu hỏi của bài thi...</p>
          </div>
        </div>
      </div>
    `;

    const closeModal = () => {
      document.removeEventListener('keydown', onKeyDown);
      modal.remove();
      if (previousFocus && typeof previousFocus.focus === 'function') previousFocus.focus();
    };
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeModal();
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = Array.from(modal.querySelectorAll('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'));
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    modal.querySelector('.attempt-detail-close')?.addEventListener('click', closeModal);
    modal.addEventListener('click', event => {
      if (event.target === modal) closeModal();
    });
    modal.querySelector('[tabindex="-1"]')?.focus();

    try {
      const [data, appealRes, focusRes] = await Promise.all([
        ApiClient.getInstructorAttemptResult(attemptId, accessReason),
        ApiClient.getAttemptAppeal(attemptId).catch(() => ({ appeal: null })),
        ApiClient.getInstructorAttemptFocusEvents(attemptId).catch(() => null)
      ]);

      const appeal = appealRes?.appeal;
      const studentEl = document.getElementById('modal-att-student');
      if (studentEl) {
        studentEl.textContent = `Thí sinh: ${data.student_name || 'Học viên'} • Điểm: ${data.total_awarded_points ?? 0} / ${data.total_possible_points ?? 0} (${data.percent_score ?? 0}%)`;
      }

      const contentEl = document.getElementById('modal-att-content');
      if (!contentEl) return;

      let appealBannerHtml = '';
      if (appeal) {
        const isPending = appeal.status === 'PENDING';
        const isApproved = appeal.status === 'APPROVED';
        const borderCls = isApproved ? 'border-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/30' : isPending ? 'border-amber-300 bg-amber-50/60 dark:bg-amber-950/30' : 'border-rose-300 bg-rose-50/60 dark:bg-rose-950/30';
        appealBannerHtml = `
          <div class="p-4 rounded-xl border ${borderCls} space-y-3 mb-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined ${isApproved ? 'text-emerald-600' : isPending ? 'text-amber-600' : 'text-rose-600'}">gavel</span>
                <h4 class="font-bold text-xs uppercase tracking-wider text-slate-800 dark:text-slate-200">Đơn yêu cầu phúc khảo bài thi</h4>
              </div>
              <span class="px-2 py-0.5 rounded text-xs font-bold ${isApproved ? 'bg-emerald-100 text-emerald-800' : isPending ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'}">
                ${isApproved ? 'ĐÃ DUYỆT' : isPending ? 'CHỜ XÉT DUYỆT' : 'ĐÃ BÁC BỎ'}
              </span>
            </div>
            <div class="space-y-1 text-xs text-slate-700 dark:text-slate-300">
              <div><strong>Lý do:</strong> ${UI.escapeHtml(appeal.reason || '')}</div>
              <div><strong>Giải trình thí sinh:</strong> <span class="italic">${UI.escapeHtml(appeal.note || 'Không có')}</span></div>
              <div class="text-[11px] text-slate-400">Gửi lúc: ${UI.formatDateTime(appeal.created_at)}</div>
              ${appeal.reviewer_note ? `
                <div class="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 font-medium">
                  <strong>Kết luận:</strong> ${UI.escapeHtml(appeal.reviewer_note)}
                  ${appeal.score_delta !== undefined && appeal.score_delta !== null ? ` (Điều chỉnh: ${appeal.score_delta > 0 ? '+' : ''}${appeal.score_delta}đ)` : ''}
                </div>
              ` : ''}
            </div>

            ${isPending ? `
              <div class="pt-2 flex items-center justify-end gap-2 border-t border-amber-200 dark:border-amber-800">
                <button type="button" id="reject-appeal-btn" class="px-3 py-1.5 rounded-lg border border-rose-300 text-rose-700 dark:text-rose-300 text-xs font-bold hover:bg-rose-50 transition">
                  Bác bỏ đơn
                </button>
                <button type="button" id="approve-appeal-btn" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center gap-1 shadow-sm">
                  <span class="material-symbols-outlined text-[15px]">edit_note</span>
                  <span>Duyệt & Điều chỉnh điểm</span>
                </button>
              </div>
            ` : ''}

          </div>
        `;
      }

      const questions = data.questions || [];
      const focusEvents = focusRes?.events || [];
      const knownSeconds = focusEvents.reduce((sum, event) => sum + (event.duration_seconds || 0), 0);
      const focusBannerHtml = focusRes === null
        ? '<div class="rounded-2xl border border-amber-300 bg-amber-50 dark:bg-amber-950/30 p-4 text-xs font-semibold text-amber-800 dark:text-amber-200 mb-6 flex items-center gap-2"><span class="material-symbols-outlined text-base">warning</span><span>Không tải được dữ liệu giám sát phòng thi. Vui lòng thử lại.</span></div>'
        : `<section class="rounded-2xl border ${focusEvents.length > 0 ? 'border-rose-300 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20' : 'border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/30 dark:bg-emerald-950/20'} p-5 text-xs mb-6 shadow-xs space-y-3">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <h4 class="font-extrabold text-sm flex items-center gap-2 ${focusEvents.length > 0 ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}">
                <span class="material-symbols-outlined text-[18px]">${focusEvents.length > 0 ? 'gavel' : 'verified_user'}</span>
                <span>Kết quả giám sát: ${focusEvents.length} lần vi phạm</span>
              </h4>
              <span class="px-2.5 py-0.5 rounded-full font-bold text-[11px] ${focusEvents.length > 0 ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200 border border-rose-300 dark:border-rose-700' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200 border border-emerald-300'}">
                Tổng thời gian vi phạm: ${knownSeconds} giây
              </span>
            </div>
            ${focusEvents.length ? `
              <ul class="space-y-2 pt-2 border-t border-rose-200/80 dark:border-rose-900/40">
                ${focusEvents.map(event => {
                  const errorLabelMap = {
                    FULLSCREEN_EXIT: 'Thoát toàn màn hình',
                    SCREENSHOT_ATTEMPT: 'Chụp màn hình',
                    TAB_HIDDEN: 'Rời khỏi tab thi',
                    WINDOW_BLUR: 'Mất tiêu điểm / Chuyển cửa sổ'
                  };
                  const errorIconMap = {
                    FULLSCREEN_EXIT: 'fullscreen_exit',
                    SCREENSHOT_ATTEMPT: 'screenshot',
                    TAB_HIDDEN: 'tab',
                    WINDOW_BLUR: 'visibility_off'
                  };
                  const label = errorLabelMap[event.event_type] || event.event_type;
                  const icon = errorIconMap[event.event_type] || 'warning';
                  const timeFormatted = event.started_at ? new Date(event.started_at).toLocaleTimeString('vi-VN') : '';
                  const durationText = event.duration_seconds === null ? 'Chưa xác định thời lượng' : `${event.duration_seconds} giây`;
                  return `
                    <li class="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-rose-200 dark:border-rose-900/50 flex flex-wrap items-center justify-between gap-2">
                      <div class="flex items-center gap-2">
                        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
                          <span class="material-symbols-outlined text-[14px]">${icon}</span>
                          <span>${UI.escapeHtml(label)}</span>
                        </span>
                        ${timeFormatted ? `<span class="text-[11px] text-slate-500 font-mono">Lúc ${timeFormatted}</span>` : ''}
                      </div>
                      <div class="text-xs font-mono font-bold text-rose-600 dark:text-rose-400">
                        Thời gian vi phạm: ${durationText}
                      </div>
                    </li>
                  `;
                }).join('')}
              </ul>
            ` : '<p class="text-emerald-700 dark:text-emerald-300 font-medium text-xs">Thí sinh làm bài nghiêm túc, không ghi nhận hành vi vi phạm nào.</p>'}
          </section>`;
      if (questions.length === 0) {
        contentEl.innerHTML = appealBannerHtml + focusBannerHtml + `<div class="text-center py-8 text-slate-400 text-xs">Không có dữ liệu câu hỏi.</div>`;
      } else {
        contentEl.innerHTML = appealBannerHtml + focusBannerHtml + questions.map((q, idx) => {
        const isEssay = q.question_type === 'ESSAY';
        const canGradeEssay = isEssay && ['PENDING', 'MANUAL_GRADED'].includes(q.grading_status);
        const isCorr = q.is_correct;
        const cardTone = canGradeEssay && q.grading_status === 'PENDING'
          ? 'border-amber-200 dark:border-amber-900/50 bg-amber-50/20'
          : isCorr
            ? 'border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/20'
            : 'border-rose-200 dark:border-rose-900/50 bg-rose-50/20';
        const choices = q.choices || [];
        return `
          <div class="p-4 rounded-xl border ${cardTone} space-y-3">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-2">
                <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${isCorr ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300'}">
                  ${idx + 1}
                </span>
                <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  ${UI.escapeHtml(q.question_type || 'QUESTION')}
                </span>
              </div>
              <div class="text-xs font-bold font-mono ${isCorr ? 'text-emerald-600' : 'text-rose-600'}">
                ${q.awarded_points ?? 0} / ${q.points_assigned ?? 0} điểm
              </div>
            </div>

            <div class="text-sm font-semibold text-slate-900 dark:text-white pl-8">
              ${UI.escapeHtml(q.stem || q.content || '')}
            </div>

            <!-- Choices list or student answer -->
            <div class="space-y-1.5 pl-8 text-xs">
              ${choices.length > 0 ? choices.map(c => {
                const isSelected = c.is_selected;
                const isCorrectChoice = c.is_correct;
                let choiceCls = 'bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300';
                if (isSelected && isCorrectChoice) {
                  choiceCls = 'bg-emerald-100 dark:bg-emerald-950/60 border-emerald-300 text-emerald-900 dark:text-emerald-200 font-bold';
                } else if (isSelected && !isCorrectChoice) {
                  choiceCls = 'bg-rose-100 dark:bg-rose-950/60 border-rose-300 text-rose-900 dark:text-rose-200 font-bold';
                } else if (!isSelected && isCorrectChoice) {
                  choiceCls = 'bg-emerald-50 dark:bg-emerald-950/30 border-dashed border-emerald-400 text-emerald-800 dark:text-emerald-300';
                }

                return `
                  <div class="p-2.5 rounded-lg border ${choiceCls} flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span class="material-symbols-outlined text-[16px] ${isSelected ? (isCorrectChoice ? 'text-emerald-600' : 'text-rose-600') : 'text-slate-400'}">
                        ${isSelected ? (isCorrectChoice ? 'check_circle' : 'cancel') : 'radio_button_unchecked'}
                      </span>
                      <span>${UI.escapeHtml(UI.cleanChoiceText(c.content || ''))}</span>
                    </div>
                    <div class="flex items-center gap-1.5 shrink-0 text-[11px]">
                      ${isSelected ? '<span class="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-[10px]">Đã chọn</span>' : ''}
                      ${isCorrectChoice ? '<span class="px-1.5 py-0.5 rounded bg-emerald-200 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200 text-[10px] font-bold">Đáp án đúng</span>' : ''}
                    </div>
                  </div>
                `;
              }).join('') : (
                q.student_answer_text ? `
                  <div class="p-3 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <span class="text-[11px] text-slate-500 font-semibold block mb-1">Câu trả lời của thí sinh:</span>
                    <span class="font-mono text-slate-900 dark:text-white">${UI.escapeHtml(UI.cleanChoiceText(q.student_answer_text))}</span>
                  </div>
                ` : ''
              )}
            </div>

            ${q.explanation ? `
              <div class="mt-2 pl-8 pt-2 border-t border-slate-200 dark:border-slate-800/60 text-xs text-slate-500 dark:text-slate-400 flex items-start gap-1.5">
                <span class="material-symbols-outlined text-[15px] text-amber-500 shrink-0 mt-0.5">lightbulb</span>
                <span><em>Giải thích:</em> ${UI.escapeHtml(q.explanation)}</span>
              </div>
            ` : ''}

            ${canGradeEssay ? `
              <div class="pl-8 pt-3 border-t border-amber-200 dark:border-amber-900/50 space-y-3" data-essay-grading="${UI.escapeHtml(q.attempt_question_id)}">
                <div class="flex items-center gap-2 text-xs font-bold text-amber-800 dark:text-amber-200">
                  <span class="material-symbols-outlined text-[16px]">edit_note</span>
                  <span>${q.grading_status === 'PENDING' ? 'Lưu điểm tự luận' : 'Cập nhật điểm tự luận'}</span>
                </div>
                <div class="space-y-1.5">
                  <label class="block text-[11px] font-bold text-slate-700 dark:text-slate-300" for="essay-score-${UI.escapeHtml(q.attempt_question_id)}">
                    Điểm tự luận (0–${q.points_assigned})
                  </label>
                  <input
                    id="essay-score-${UI.escapeHtml(q.attempt_question_id)}"
                    data-essay-score
                    type="number"
                    min="0"
                    max="${q.points_assigned}"
                    step="0.25"
                    value="${q.awarded_points ?? 0}"
                    class="c-input w-full"
                    aria-describedby="essay-reason-${UI.escapeHtml(q.attempt_question_id)}"
                  />
                </div>
                <div class="space-y-1.5">
                  <label class="block text-[11px] font-bold text-slate-700 dark:text-slate-300" for="essay-reason-${UI.escapeHtml(q.attempt_question_id)}">
                    Căn cứ chấm <span class="text-rose-500">(Bắt buộc)</span>
                  </label>
                  <textarea
                    id="essay-reason-${UI.escapeHtml(q.attempt_question_id)}"
                    data-essay-reason
                    rows="2"
                    class="c-input w-full resize-y"
                    placeholder="Nêu ngắn gọn căn cứ cho số điểm này"
                  >${UI.escapeHtml(q.feedback || '')}</textarea>
                </div>
                <div class="flex justify-end">
                  <button
                    type="button"
                    data-essay-grade
                    data-attempt-question-id="${UI.escapeHtml(q.attempt_question_id)}"
                    data-max-points="${q.points_assigned}"
                    data-row-version="${UI.escapeHtml(q.row_version || '')}"
                    class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors"
                  >
                    Lưu điểm tự luận
                  </button>
                </div>
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
      }

      contentEl.querySelectorAll('[data-essay-grade]').forEach(button => {
        button.addEventListener('click', async () => {
          const panel = button.closest('[data-essay-grading]');
          const scoreInput = panel?.querySelector('[data-essay-score]');
          const reasonInput = panel?.querySelector('[data-essay-reason]');
          const score = Number(scoreInput?.value);
          const maxPoints = Number(button.dataset.maxPoints);
          const reason = reasonInput?.value.trim() || '';
          if (!Number.isFinite(score) || score < 0 || score > maxPoints) {
            UI.showToast(`Điểm phải nằm trong khoảng 0 đến ${maxPoints}.`, 'warning');
            scoreInput?.focus();
            return;
          }
          if (!reason) {
            UI.showToast('Vui lòng nhập căn cứ chấm trước khi lưu.', 'warning');
            reasonInput?.focus();
            return;
          }

          button.disabled = true;
          try {
            await ApiClient.gradeInstructorAttemptQuestion(
              attemptId,
              button.dataset.attemptQuestionId,
              score,
              reason,
              button.dataset.rowVersion || null,
            );
            UI.showToast('Đã lưu điểm tự luận và cập nhật kết quả.', 'success');
            closeModal();
            await InstructorView.openAttemptDetailModal(attemptId, accessReason);
          } catch (error) {
            button.disabled = false;
            UI.showToast(error.message || 'Không thể lưu điểm tự luận.', 'error');
          }
        });
      });

      // Event handlers for appeal review
      const approveBtn = document.getElementById('approve-appeal-btn');
      if (approveBtn) {
        approveBtn.onclick = () => {
          UI.openModal({
            title: `
              <span class="material-symbols-outlined text-emerald-600 text-[20px]">verified</span>
              <span>Duyệt Phúc Khảo & Điều Chỉnh Điểm Số</span>
            `,
            bodyHtml: `
              <div class="space-y-3.5 text-xs text-slate-700 dark:text-slate-300">
                <div class="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 space-y-1">
                  <div class="font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">info</span>
                    <span>Cập nhật điểm:</span>
                  </div>
                  <p class="text-[11px] leading-relaxed">
                    Hệ thống sẽ tính lại kết quả học tập và lưu lịch sử thay đổi điểm.
                  </p>
                </div>

                <div class="space-y-1">
                  <label class="block font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                    Điểm số cộng thêm (Score Delta) <span class="text-rose-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.25"
                    id="appeal-delta-input"
                    value="1.0"
                    placeholder="VD: 1.0 (hoặc -0.5 nếu trừ điểm)"
                    class="c-input"
                  />
                </div>

                <div class="space-y-1">
                  <label class="block font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                    Ghi chú kết luận & Căn cứ phê duyệt <span class="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="appeal-reviewer-note"
                    rows="3"
                    class="c-input resize-none"
                    placeholder="VD: Chấp thuận phúc khảo câu 3 do lỗi chính tả trong đề gốc, cộng thêm 1.0 điểm..."
                  ></textarea>
                </div>
              </div>
            `,
            footerHtml: `
              <div class="flex items-center justify-end gap-2 w-full">
                <button type="button" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100" onclick="UI.closeModal()">
                  Hủy
                </button>
                <button type="button" id="confirm-approve-appeal-btn" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                  <span class="material-symbols-outlined text-[16px]">save</span>
                  <span>Lưu & Cập nhật điểm</span>
                </button>
              </div>
            `
          });

          const confirmApproveBtn = document.getElementById('confirm-approve-appeal-btn');
          if (confirmApproveBtn) {
            confirmApproveBtn.onclick = async () => {
              const deltaVal = parseFloat(document.getElementById('appeal-delta-input')?.value || '0');
              const noteVal = (document.getElementById('appeal-reviewer-note')?.value || '').trim();
              if (!noteVal) {
                UI.showToast('Vui lòng nhập căn cứ kết luận của Giảng viên.', 'warning');
                return;
              }

              confirmApproveBtn.disabled = true;
              confirmApproveBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang lưu...';

              try {
                await ApiClient.reviewAttemptAppeal(attemptId, {
                  decision: 'APPROVED',
                  score_delta: deltaVal,
                  reviewer_note: noteVal
                });
                UI.closeModal();
                UI.showToast('Đã phê duyệt phúc khảo và cập nhật điểm thành công.', 'success');
                InstructorView.openAttemptDetailModal(attemptId);
              } catch (err) {
                UI.showToast(err.message || 'Lỗi cập nhật phúc khảo.', 'error');
                confirmApproveBtn.disabled = false;
                confirmApproveBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">save</span><span>Lưu & Cập nhật điểm</span>';
              }
            };
          }
        };
      }

      const rejectBtn = document.getElementById('reject-appeal-btn');
      if (rejectBtn) {
        rejectBtn.onclick = () => {
          UI.openModal({
            title: `
              <span class="material-symbols-outlined text-rose-600 text-[20px]">cancel</span>
              <span>Bác Bỏ Đơn Yêu Cầu Phúc Khảo</span>
            `,
            bodyHtml: `
              <div class="space-y-3.5 text-xs text-slate-700 dark:text-slate-300">
                <p class="text-slate-600 dark:text-slate-400">
                  Vui lòng cung cấp lý do bác bỏ để giải trình rõ ràng cho thí sinh về kết quả chấm điểm ban đầu.
                </p>

                <div class="space-y-1">
                  <label class="block font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                    Lý do bác bỏ đơn <span class="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="reject-appeal-note"
                    rows="3"
                    class="c-input resize-none"
                    placeholder="VD: Sau khi đối chiếu đáp án, câu trả lời của thí sinh chưa thỏa mãn điều kiện theo đề bài..."
                  ></textarea>
                </div>
              </div>
            `,
            footerHtml: `
              <div class="flex items-center justify-end gap-2 w-full">
                <button type="button" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100" onclick="UI.closeModal()">
                  Hủy
                </button>
                <button type="button" id="confirm-reject-appeal-btn" class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                  <span class="material-symbols-outlined text-[16px]">block</span>
                  <span>Xác nhận bác bỏ</span>
                </button>
              </div>
            `
          });

          const confirmRejectBtn = document.getElementById('confirm-reject-appeal-btn');
          if (confirmRejectBtn) {
            confirmRejectBtn.onclick = async () => {
              const noteVal = (document.getElementById('reject-appeal-note')?.value || '').trim();
              if (!noteVal) {
                UI.showToast('Vui lòng nhập lý do bác bỏ đơn.', 'warning');
                return;
              }

              confirmRejectBtn.disabled = true;
              confirmRejectBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang xử lý...';

              try {
                await ApiClient.reviewAttemptAppeal(attemptId, {
                  decision: 'REJECTED',
                  reviewer_note: noteVal
                });
                UI.closeModal();
                UI.showToast('Đã bác bỏ đơn phúc khảo.', 'info');
                InstructorView.openAttemptDetailModal(attemptId);
              } catch (err) {
                UI.showToast(err.message || 'Lỗi xử lý bác bỏ.', 'error');
                confirmRejectBtn.disabled = false;
                confirmRejectBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">block</span><span>Xác nhận bác bỏ</span>';
              }
            };
          }
        };
      }
    } catch (err) {
      const errEl = document.getElementById('modal-att-content');
      if (errEl) {
        const reasonRequired = err?.status === 400 && /reason is required/i.test(err.message || '');
        if (reasonRequired) {
          errEl.innerHTML = `
            <div class="p-6 space-y-4 text-sm text-slate-700 dark:text-slate-300">
              <p>Để xem dữ liệu chi tiết của thí sinh, vui lòng ghi rõ lý do truy cập.</p>
              <div class="space-y-2">
                <label for="attempt-detail-reason" class="block text-xs font-bold text-slate-800 dark:text-slate-200">Lý do truy cập</label>
                <textarea id="attempt-detail-reason" rows="3" class="c-input resize-none" placeholder="VD: Đối chiếu bài làm theo yêu cầu chấm phúc khảo"></textarea>
                <p id="attempt-detail-reason-error" class="text-xs text-rose-600 hidden">Vui lòng nhập lý do truy cập.</p>
              </div>
              <button type="button" id="attempt-detail-reason-submit" class="w-full px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold">Tiếp tục</button>
            </div>
          `;
          const reasonInput = document.getElementById('attempt-detail-reason');
          const reasonError = document.getElementById('attempt-detail-reason-error');
          const submitReason = document.getElementById('attempt-detail-reason-submit');
          reasonInput?.focus();
          submitReason?.addEventListener('click', () => {
            const reason = (reasonInput?.value || '').trim();
            if (!reason) {
              reasonError?.classList.remove('hidden');
              reasonInput?.focus();
              return;
            }
            InstructorView.openAttemptDetailModal(attemptId, reason);
          });
          return;
        }
        errEl.innerHTML = `<div class="p-6 text-center text-rose-500 text-xs">Lỗi nạp bài làm. Vui lòng thử lại.</div>`;
      }
    }
  }

  // =========================================================================
  // 3.5. Tab Course Settings & Instructor Contact Info
  // =========================================================================
  static renderTabSettings(tabContainer, course) {
    const cId = course.course_id || course.id;
    const contactInfo = course.contact_info || {};
    const defaultEmail = contactInfo.email || course.instructor_email || '';
    const defaultPhone = contactInfo.phone || '';
    const defaultGroup = contactInfo.group || '';
    const defaultOfficeHours = contactInfo.office_hours || '';

    tabContainer.innerHTML = `
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-2xs space-y-5 max-w-4xl mx-auto animate-fade-in">
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">edit_note</span>
          <span>Cập nhật thông tin khóa học</span>
        </h2>
        
        <form id="edit-course-form" class="space-y-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Tên khóa học</label>
            <input type="text" name="title" value="${UI.escapeHtml(course.title)}" required class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary" />
          </div>

          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Mô tả tóm tắt</label>
            <textarea name="description" rows="3" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary resize-none">${UI.escapeHtml(course.description || '')}</textarea>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Danh mục</label>
              <input type="text" name="category" list="academic-categories-list-settings" value="${UI.escapeHtml(course.category || 'Khoa học máy tính & CNTT')}" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary" />
              <datalist id="academic-categories-list-settings">
                <option value="Khoa học máy tính & CNTT (Computer Science)"></option>
                <option value="Phát triển Web & Ứng dụng Di động"></option>
                <option value="Trí tuệ nhân tạo & Khoa học Dữ liệu"></option>
                <option value="An toàn thông tin & Mạng máy tính"></option>
                <option value="Kỹ thuật Phần mềm (Software Engineering)"></option>
                <option value="Quản trị Kinh doanh & Khởi nghiệp"></option>
                <option value="Tài chính - Ngân hàng & Fintech"></option>
                <option value="Marketing & Thương mại Điện tử"></option>
                <option value="Ngôn ngữ học & Ngoại ngữ ứng dụng"></option>
                <option value="Thiết kế Đồ họa & Sáng tạo Số"></option>
                <option value="Luật học & Pháp lý doanh nghiệp"></option>
                <option value="Y Dược & Khoa học Sức khỏe"></option>
                <option value="Sư phạm & Giáo dục học"></option>
                <option value="Khoa học Xã hội & Nhân văn"></option>
                <option value="Khoa học Tự nhiên & Môi trường"></option>
              </datalist>
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Sĩ số sinh viên thực tế</label>
              <div class="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">groups</span>
                <span>${course.enrolled_count ?? course.enrollments_count ?? 0} sinh viên đang theo học</span>
              </div>
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Sĩ số tối đa</label>
              <div class="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px] text-emerald-500">all_inclusive</span>
                <span>Không giới hạn (Theo quy định hệ thống)</span>
              </div>
            </div>
          </div>

          <!-- Section: Thông tin liên hệ Giảng viên -->
          <div class="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[20px]">contact_phone</span>
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                Thông tin liên hệ & Kênh trao đổi học tập (Hiển thị sang Học sinh)
              </h3>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Email liên hệ <span class="text-rose-500 font-bold">* (Bắt buộc)</span>
                </label>
                <input
                  type="email"
                  name="contact_email"
                  value="${UI.escapeHtml(defaultEmail)}"
                  required
                  placeholder="VD: giangvien@pwd301.edu.vn"
                  class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary font-mono text-xs"
                />
              </div>

              <div class="space-y-1">
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Số điện thoại liên hệ <span class="text-slate-400 font-normal">(Không bắt buộc)</span>
                </label>
                <input
                  type="tel"
                  name="contact_phone"
                  value="${UI.escapeHtml(defaultPhone)}"
                  placeholder="VD: 0912 345 678"
                  class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary text-xs"
                />
              </div>
            </div>

            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Link Group trao đổi học tập (Zalo, MS Teams, Telegram...) <span class="text-slate-400 font-normal">(Không bắt buộc)</span>
              </label>
              <input
                type="url"
                name="contact_group"
                value="${UI.escapeHtml(defaultGroup)}"
                placeholder="VD: https://zalo.me/g/... hoặc https://teams.microsoft.com/..."
                class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary text-xs"
              />
            </div>

            <div class="space-y-1">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Giờ tiếp sinh viên / Văn phòng <span class="text-slate-400 font-normal">(Không bắt buộc)</span>
              </label>
              <input
                type="text"
                name="contact_office_hours"
                value="${UI.escapeHtml(defaultOfficeHours)}"
                placeholder="VD: Thứ 3 & Thứ 5 (14:00 - 16:30) tại P.302 hoặc qua Teams"
                class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary text-xs"
              />
            </div>
          </div>

          <div class="pt-4 flex justify-end">
            <button type="submit" id="save-course-settings-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm">
              Lưu thay đổi
            </button>
          </div>
        </form>

        <!-- Danger Zone: Course Archival / Trash -->
        <div class="border-t border-rose-100 dark:border-rose-950/40 pt-6 mt-6">
          <div class="rounded-2xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 class="text-sm font-bold text-rose-800 dark:text-rose-400 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">delete_forever</span>
                Xóa / Lưu trữ khóa học
              </h3>
              <p class="text-xs text-rose-600 dark:text-rose-400/80 mt-1 max-w-md">
                Chuyển khóa học vào thùng rác lưu trữ (Soft Delete). Khóa học sẽ không còn xuất hiện trong danh mục công khai và sinh viên không thể ghi danh mới.
              </p>
            </div>
            <button
              type="button"
              id="trash-course-btn"
              class="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors shadow-sm shrink-0 flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-[16px]">delete</span>
              Xóa khóa học
            </button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('edit-course-form').onsubmit = async (e) => {
      e.preventDefault();
      const form = e.target;
      const btn = document.getElementById('save-course-settings-btn');
      const cEmail = form.contact_email?.value.trim();

      if (!cEmail) {
        UI.showToast('Vui lòng nhập Email liên hệ của Giảng viên (Bắt buộc).', 'warning');
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang lưu...';

      const contactData = {
        email: cEmail,
        phone: form.contact_phone?.value.trim() || '',
        group: form.contact_group?.value.trim() || '',
        office_hours: form.contact_office_hours?.value.trim() || ''
      };

      // Si so toi da luon la khong gioi han theo quy dinh he thong
      const capacityVal = null;

      try {
        await ApiClient.updateCourse(cId, {
          title: form.title.value.trim(),
          description: form.description.value.trim(),
          category: form.category.value.trim(),
          contact_info: contactData,
          capacity: capacityVal
        });
        course.contact_info = contactData;
        if (capacityVal !== undefined) course.capacity = capacityVal;
        UI.showToast('Đã lưu thông tin khóa học & liên hệ thành công!', 'success');
      } catch (err) {
        UI.showToast(err.message || 'Lỗi cập nhật.', 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = 'Lưu thay đổi';
      }
    };

    document.getElementById('trash-course-btn').onclick = async () => {
      const confirmed = await UI.confirm(
        'Xóa / lưu trữ khóa học',
        `Bạn có chắc chắn muốn xóa/lưu trữ khóa học "${UI.escapeHtml(course.title)}" (${UI.escapeHtml(course.course_code || '')})?<br><br>Khóa học sẽ được chuyển vào thùng rác.`,
        'Chuyển vào thùng rác',
        'Hủy bỏ',
        true
      );
      if (!confirmed) return;

      const trashBtn = document.getElementById('trash-course-btn');
      trashBtn.disabled = true;
      trashBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang xóa...';

      try {
        await ApiClient.trashCourse(cId, 'Giảng viên yêu cầu xóa khóa học từ màn hình quản lý');
        UI.showToast('Đã chuyển khóa học vào thùng rác thành công!', 'success');
        window.location.hash = '#/instructor/courses';
      } catch (err) {
        UI.showToast(err.message || 'Lỗi khi xóa khóa học.', 'error');
        trashBtn.disabled = false;
        trashBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">delete</span> Xóa khóa học';
      }
    };
  }

  // =========================================================================
  // 3.7. Dedicated Fullscreen Low-Tech Lesson Authoring Studio
  // =========================================================================
  static isActiveLessonStudio(root) {
    return Boolean(root?.isConnected && document.getElementById('lesson-studio-root') === root);
  }

  static async uploadLessonFiles(files, uploadOne) {
    const uploaded = [];
    const pending = [];
    const failed = [];
    for (const file of files) {
      try {
        const result = await uploadOne(file);
        if (result?.pending_approval) pending.push({ file, ...result });
        else uploaded.push(result);
      } catch (error) {
        failed.push({ file, error });
      }
    }
    return { uploaded, pending, failed };
  }

  static getVideoCount(links, resources) {
    const uploaded = (resources || []).filter(resource =>
      /\.(mp4|webm|mkv|mov)$/i.test(resource?.filename || resource?.title || '')
    ).length;
    return (links || []).length + uploaded;
  }

  static canAddLessonVideo(links, resources, parentAvailable = 7) {
    return InstructorView.getRemainingVideoSlots(links, resources, parentAvailable) > 0;
  }

  static getRemainingVideoSlots(links, resources, parentAvailable = 7) {
    return Math.max(0, Math.min(2 - InstructorView.getVideoCount(links, resources), parentAvailable));
  }

  static filterVideoUploadBatch(files, remainingSlots) {
    const validExts = /\.(mp4|webm|mkv|mov)$/i;
    const valid = [];
    const oversized = [];
    const invalidType = [];
    for (const file of (files || [])) {
      const name = file?.name || '';
      const type = file?.type || '';
      const size = Number(file?.size || 0);
      if (!validExts.test(name) && !type.startsWith('video/')) {
        invalidType.push(file);
      } else if (size >= 1000000000) {
        oversized.push(file);
      } else {
        valid.push(file);
      }
    }
    const accepted = valid.slice(0, remainingSlots);
    const overflow = valid.slice(remainingSlots);
    return { accepted, overflow, oversized, invalidType };
  }

  static moveVideoItem(list, fromIndex, toIndex) {
    if (!Array.isArray(list) || fromIndex === toIndex || fromIndex < 0 || toIndex < 0 || fromIndex >= list.length || toIndex >= list.length) {
      return Array.isArray(list) ? [...list] : [];
    }
    const result = [...list];
    const [item] = result.splice(fromIndex, 1);
    result.splice(toIndex, 0, item);
    return result;
  }

  static lessonSaveOutcome(response, publish) {
    if (response?.pending_approval || response?.status === 'PENDING_APPROVAL' || response?.status === 202) return 'pending';
    if (response?.status === 'PUBLISHED') return 'published';
    return publish ? 'published' : 'saved';
  }

  static shouldAutosaveLesson(currentVersion, savedVersion) {
    return currentVersion !== savedVersion;
  }

  static renderLessonChildNavigator(unit, courseId, currentLessonId = null) {
    if (!unit) {
      return `
        <nav aria-label="Lesson trong Bài học" class="rounded-2xl border border-[#E8E6DF] dark:border-[#526881] bg-[#FAF9F5] dark:bg-[#1B2A3D] p-4 space-y-3 lg:sticky lg:top-24">
          <div class="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#E8E6DF] dark:border-[#526881]">
            <div>
              <h2 class="text-sm font-bold text-[#222120] dark:text-[#F0F5FA]">Chương bài giảng</h2>
              <span class="text-[11px] font-medium text-[#5C5B57] dark:text-[#C6D2E1]">0/10 Lesson</span>
            </div>
          </div>
          <div class="p-3 text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68] bg-white/50 dark:bg-[#202020]/50 rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B]">
            Chưa có bài giảng nào trong chương này
          </div>
          <button
            type="button"
            id="btn-nav-add-lesson"
            class="btn-nav-add-lesson w-full py-2 px-3 rounded-xl border border-dashed border-primary/40 hover:border-primary bg-primary/5 hover:bg-primary/10 text-primary text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs mt-1 cursor-pointer"
            data-learning-unit-id=""
            data-unit-id=""
            title="Thêm bài học mới"
          >
            <span class="material-symbols-outlined text-[16px]">add</span>
            <span>Thêm bài học mới</span>
          </button>
        </nav>
      `;
    }
    const unitId = encodeURIComponent(unit.learning_unit_id || '');
    const coursePath = `#/instructor/courses/${encodeURIComponent(courseId)}/lessons`;
    const lessons = [...(unit.lessons || [])].sort((a, b) => (a.position || 0) - (b.position || 0));
    const count = unit.lesson_count ?? lessons.length;
    return `
      <nav aria-label="Lesson trong Bài học" class="rounded-2xl border border-[#E8E6DF] dark:border-[#526881] bg-[#FAF9F5] dark:bg-[#1B2A3D] p-4 space-y-3 lg:sticky lg:top-24">
        <div class="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#E8E6DF] dark:border-[#526881]">
          <div>
            <h2 class="text-sm font-bold text-[#222120] dark:text-[#F0F5FA]">${UI.escapeHtml(unit.title)}</h2>
            <span class="text-[11px] font-medium text-[#5C5B57] dark:text-[#C6D2E1]">${count}/10 Lesson</span>
          </div>
        </div>
        <div class="flex flex-col gap-2" id="nav-lessons-sortable-list">
          ${lessons.length === 0 ? `
            <div class="p-3 text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68] bg-white/50 dark:bg-[#202020]/50 rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B]">
              Chưa có bài giảng nào trong chương này
            </div>
          ` : ''}
          ${lessons.map((lesson, idx) => {
            const current = lesson.lesson_id === currentLessonId;
            return `
              <div
                class="nav-lesson-item group/item flex items-center justify-between gap-2 rounded-xl border p-2.5 transition-all select-none ${
                  current
                    ? 'border-primary bg-primary-subtle text-primary dark:text-[#93C5FD] dark:bg-[#2D4058] shadow-2xs'
                    : 'border-[#E8E6DF] dark:border-[#526881] bg-white dark:bg-[#223248] text-[#222120] dark:text-[#F0F5FA] hover:border-primary'
                }"
                draggable="true"
                data-lesson-id="${lesson.lesson_id}"
                data-idx="${idx}"
              >
                <div class="flex items-center gap-2 min-w-0 flex-1">
                  <span class="nav-drag-handle cursor-grab active:cursor-grabbing text-[#8F8E8A] group-hover/item:text-primary transition-colors shrink-0" title="Kéo thả để đổi thứ tự bài học">
                    <span class="material-symbols-outlined text-[16px]">drag_indicator</span>
                  </span>
                  <span class="w-5 h-5 rounded-md font-mono text-[10px] font-bold flex items-center justify-center shrink-0 ${
                    current ? 'bg-primary text-white' : 'bg-[#FAF9F5] dark:bg-[#1B2A3D] text-[#5C5B57] dark:text-[#C6D2E1] border border-[#E8E6DF] dark:border-[#526881]'
                  }">
                    ${idx + 1}
                  </span>
                  <a
                    href="${coursePath}/${encodeURIComponent(lesson.lesson_id)}/edit"
                    ${current ? 'aria-current="page"' : ''}
                    class="nav-lesson-link text-xs font-semibold truncate flex-1 hover:underline cursor-pointer block"
                    title="${UI.escapeHtml(lesson.title)}"
                  >
                    ${UI.escapeHtml(lesson.title)}
                  </a>
                </div>
                <button
                  type="button"
                  class="btn-nav-delete-lesson p-1 rounded-lg text-[#8F8E8A] hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors shrink-0 cursor-pointer"
                  data-lesson-id="${lesson.lesson_id}"
                  data-lesson-title="${UI.escapeHtml(lesson.title)}"
                  title="Xóa bài học này"
                >
                  <span class="material-symbols-outlined text-[15px]">delete</span>
                </button>
              </div>
            `;
          }).join('')}
          ${(!currentLessonId || currentLessonId === 'new') ? `
            <div
              id="nav-draft-lesson-item"
              class="nav-lesson-item group/item flex items-center justify-between gap-2 rounded-xl border p-2.5 transition-all select-none border-primary bg-primary-subtle text-primary dark:text-[#93C5FD] dark:bg-[#2D4058] shadow-2xs ring-1 ring-primary/30"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="w-5 h-5 rounded-md font-mono text-[10px] font-bold flex items-center justify-center shrink-0 bg-primary text-white">
                  ${lessons.length + 1}
                </span>
                <span
                  id="nav-draft-lesson-title"
                  class="text-xs font-bold text-primary truncate flex-1 block"
                  title="Bài giảng mới (Bản nháp)"
                >
                  Bài giảng ${lessons.length + 1}
                </span>
                <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40 shrink-0">
                  Bản nháp
                </span>
              </div>
            </div>
          ` : ''}
        </div>
        ${count < 10 ? `
          <button
            type="button"
            id="btn-nav-add-lesson"
            class="btn-nav-add-lesson w-full py-2 px-3 rounded-xl border border-dashed border-primary/40 hover:border-primary bg-primary/5 hover:bg-primary/10 text-primary text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-2xs mt-1 cursor-pointer"
            data-learning-unit-id="${unitId}"
            data-unit-id="${unitId}"
            title="Thêm bài học mới"
          >
            <span class="material-symbols-outlined text-[16px]">add</span>
            <span>Thêm bài học mới</span>
          </button>
        ` : ''}
      </nav>
    `;
  }

  static async renderLessonAuthoringStudio(container, courseId, lessonId = null, initialUnitId = null) {
    return InstructorView.renderCourseManage(container, courseId, 'curriculum', lessonId, initialUnitId);
  }

  // =========================================================================
  // 5. PWD301 Exam Authoring Studio (Delegated to instructor-exams.js)
  // =========================================================================
  static renderExams(container) {
    if (typeof InstructorView.renderExamsHub === 'function') {
      return InstructorView.renderExamsHub(container);
    }
  }

  // =========================================================================
  // 6. Dedicated Prerequisite Approval Center for Instructors (TASK-084)
  // =========================================================================
  static async renderPrerequisiteApprovalRequests(container) {
    if (!container) return;
    container.innerHTML = `
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs">Đang tải danh sách yêu cầu môn tiên quyết...</p>
        </div>
      </div>
    `;

    let activeFilter = 'ALL'; // ALL, PENDING, APPROVED, REJECTED
    let allRequests = [];

    const fetchAndRender = async () => {
      try {
        const res = await ApiClient.getInstructorIncomingPrerequisiteRequests();
        allRequests = (res && res.incoming) ? res.incoming : (Array.isArray(res) ? res : []);
        renderUI();
      } catch (err) {
        container.innerHTML = `
          <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
            <div class="p-6 rounded-2xl bg-rose-50/80 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs">
              <p class="font-bold">Lỗi tải danh sách yêu cầu:</p>
              <p class="mt-1">${UI.escapeHtml(err.message || String(err))}</p>
            </div>
          </div>
        `;
      }
    };

    const renderUI = () => {
      const filtered = allRequests.filter(r => {
        if (activeFilter === 'ALL') return true;
        if (activeFilter === 'PENDING') return r.approval_status === 'PENDING_APPROVAL' || r.approval_status === 'PENDING';
        if (activeFilter === 'APPROVED') return r.approval_status === 'APPROVED';
        if (activeFilter === 'REJECTED') return r.approval_status === 'REJECTED';
        return true;
      });

      const pendingCount = allRequests.filter(r => r.approval_status === 'PENDING_APPROVAL' || r.approval_status === 'PENDING').length;
      const approvedCount = allRequests.filter(r => r.approval_status === 'APPROVED').length;
      const rejectedCount = allRequests.filter(r => r.approval_status === 'REJECTED').length;

      container.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6 animate-fadeIn">
          <!-- Header Banner -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
            <div class="space-y-1">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold shadow-2xs">
                  <span class="material-symbols-outlined text-[20px]">account_tree</span>
                </div>
                <h1 class="text-xl font-black text-slate-900 dark:text-white tracking-tight">Xét duyệt Yêu cầu Môn Tiên quyết</h1>
              </div>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                Quản lý các yêu cầu từ đồng nghiệp xin liên kết học phần do Thầy/Cô phụ trách làm điều kiện tiên quyết cho chương trình đào tạo của họ.
              </p>
            </div>
            <button type="button" id="btn-refresh-prereq-requests" class="px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-bold transition flex items-center gap-1.5 self-start sm:self-auto cursor-pointer shadow-2xs">
              <span class="material-symbols-outlined text-[16px]">refresh</span>
              <span>Làm mới</span>
            </button>
          </div>

          <!-- Filter Pills -->
          <div class="flex flex-wrap items-center gap-2">
            <button type="button" class="btn-filter-prereq px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${activeFilter === 'ALL' ? 'bg-indigo-600 text-white shadow-2xs' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'}" data-filter="ALL">
              Tất cả (${allRequests.length})
            </button>
            <button type="button" class="btn-filter-prereq px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${activeFilter === 'PENDING' ? 'bg-amber-600 text-white shadow-2xs' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'}" data-filter="PENDING">
              Chờ phê duyệt ${pendingCount > 0 ? `(${pendingCount})` : ''}
            </button>
            <button type="button" class="btn-filter-prereq px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${activeFilter === 'APPROVED' ? 'bg-emerald-600 text-white shadow-2xs' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'}" data-filter="APPROVED">
              Đã chấp thuận (${approvedCount})
            </button>
            <button type="button" class="btn-filter-prereq px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${activeFilter === 'REJECTED' ? 'bg-rose-600 text-white shadow-2xs' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'}" data-filter="REJECTED">
              Đã từ chối (${rejectedCount})
            </button>
          </div>

          <!-- Main Table or Empty State -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden">
            ${filtered.length === 0 ? `
              <div class="p-12 text-center text-slate-400 space-y-2">
                <span class="material-symbols-outlined text-4xl text-slate-300 dark:text-slate-600">inbox</span>
                <p class="font-bold text-slate-600 dark:text-slate-300 text-sm">Không có yêu cầu nào trong mục này</p>
                <p class="text-xs text-slate-400">Các yêu cầu xin liên kết môn học từ giảng viên khác sẽ hiển thị tại đây để bạn phê duyệt.</p>
              </div>
            ` : `
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs">
                  <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th class="p-3.5">Học phần của bạn</th>
                      <th class="p-3.5">Khóa học & Giảng viên đề xuất</th>
                      <th class="p-3.5">Lý do / Căn cứ</th>
                      <th class="p-3.5">Thời gian & Trạng thái</th>
                      <th class="p-3.5 text-right">Tác vụ</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                    ${filtered.map(r => {
                      const isPending = r.approval_status === 'PENDING_APPROVAL' || r.approval_status === 'PENDING';
                      const isApproved = r.approval_status === 'APPROVED';
                      const isRejected = r.approval_status === 'REJECTED';

                      let badgeHtml = '';
                      if (isPending) {
                        badgeHtml = `<span class="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300">Chờ duyệt</span>`;
                      } else if (isApproved) {
                        badgeHtml = `<span class="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300">Đã chấp thuận</span>`;
                      } else {
                        badgeHtml = `<span class="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300">Đã từ chối</span>`;
                      }

                      return `
                        <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                          <td class="p-3.5">
                            <div class="space-y-0.5">
                              <span class="font-mono font-bold text-indigo-600 dark:text-indigo-400">${UI.escapeHtml(r.prerequisite_course_code || 'MÔN')}</span>
                              <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(r.prerequisite_course_title || 'Khóa học của bạn')}</div>
                            </div>
                          </td>
                          <td class="p-3.5">
                            <div class="space-y-0.5">
                              <span class="font-mono font-bold text-slate-700 dark:text-slate-300">${UI.escapeHtml(r.requesting_course_code || '')}</span>
                              <div class="text-slate-800 dark:text-slate-200">${UI.escapeHtml(r.requesting_course_title || 'Khóa học')}</div>
                              <div class="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                                <span class="material-symbols-outlined text-[13px]">person</span>
                                <span>${UI.escapeHtml(r.requesting_instructor_name || 'Giảng viên')}</span>
                                ${r.requesting_instructor_email ? `(${UI.escapeHtml(r.requesting_instructor_email)})` : ''}
                              </div>
                            </div>
                          </td>
                          <td class="p-3.5 max-w-xs">
                            <p class="text-slate-600 dark:text-slate-400 line-clamp-2 italic">
                              "${UI.escapeHtml(r.review_note || 'Yêu cầu chuẩn hóa theo chương trình đào tạo')}"
                            </p>
                          </td>
                          <td class="p-3.5 whitespace-nowrap">
                            <div class="space-y-1">
                              <div>${badgeHtml}</div>
                              <div class="text-[11px] text-slate-400">
                                ${r.requested_at ? new Date(r.requested_at).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : 'Vừa xong'}
                              </div>
                            </div>
                          </td>
                          <td class="p-3.5 text-right whitespace-nowrap">
                            ${isPending ? `
                              <div class="flex items-center justify-end gap-1.5">
                                <button type="button" class="btn-act-approve px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition cursor-pointer shadow-2xs" data-req-cid="${r.requesting_course_id}" data-prereq-cid="${r.prerequisite_course_id}">
                                  Chấp thuận
                                </button>
                                <button type="button" class="btn-act-reject px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 hover:border-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-slate-700 dark:text-slate-300 hover:text-rose-600 font-bold text-xs transition cursor-pointer" data-req-cid="${r.requesting_course_id}" data-prereq-cid="${r.prerequisite_course_id}">
                                  Từ chối
                                </button>
                              </div>
                            ` : `
                              <span class="text-[11px] text-slate-400 font-semibold italic">Đã hoàn tất xử lý</span>
                            `}
                          </td>
                        </tr>
                      `;
                    }).join('')}
                  </tbody>
                </table>
              </div>
            `}
          </div>
        </div>
      `;

      // Wire filters
      container.querySelectorAll('.btn-filter-prereq').forEach(btn => {
        btn.onclick = () => {
          activeFilter = btn.dataset.filter;
          renderUI();
        };
      });

      // Wire refresh
      document.getElementById('btn-refresh-prereq-requests')?.addEventListener('click', fetchAndRender);

      // Wire approve
      container.querySelectorAll('.btn-act-approve').forEach(btn => {
        btn.onclick = async () => {
          const reqCid = btn.dataset.reqCid;
          const prereqCid = btn.dataset.prereqCid;
          try {
            btn.disabled = true;
            btn.textContent = 'Đang duyệt...';
            await ApiClient.reviewInstructorIncomingPrerequisiteRequest(reqCid, prereqCid, { action: 'APPROVE', note: 'Đồng ý liên kết môn tiên quyết.' });
            UI.showToast('Đã phê duyệt yêu cầu môn tiên quyết thành công!', 'success');
            if (window.AppRouter && AppRouter.fetchInstructorPendingCounts) {
              AppRouter.fetchInstructorPendingCounts();
            }
            await fetchAndRender();
          } catch (err) {
            UI.showToast('Lỗi phê duyệt: ' + (err.message || err), 'error');
            btn.disabled = false;
            btn.textContent = 'Chấp thuận';
          }
        };
      });

      // Wire reject
      container.querySelectorAll('.btn-act-reject').forEach(btn => {
        btn.onclick = async () => {
          const reqCid = btn.dataset.reqCid;
          const prereqCid = btn.dataset.prereqCid;
          const reason = prompt('Vui lòng nhập lý do từ chối yêu cầu môn tiên quyết này:');
          if (reason === null) return;
          try {
            btn.disabled = true;
            btn.textContent = 'Đang xử lý...';
            await ApiClient.reviewInstructorIncomingPrerequisiteRequest(reqCid, prereqCid, { action: 'REJECT', note: reason || 'Chưa phù hợp với mục tiêu đào tạo.' });
            UI.showToast('Đã từ chối yêu cầu liên kết môn tiên quyết.', 'info');
            if (window.AppRouter && AppRouter.fetchInstructorPendingCounts) {
              AppRouter.fetchInstructorPendingCounts();
            }
            await fetchAndRender();
          } catch (err) {
            UI.showToast('Lỗi từ chối: ' + (err.message || err), 'error');
            btn.disabled = false;
            btn.textContent = 'Từ chối';
          }
        };
      });
    };

    await fetchAndRender();
  }

}

window.InstructorView = InstructorView;
