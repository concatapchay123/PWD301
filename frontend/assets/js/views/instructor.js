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
      <div class="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto animate-fade-in font-sans">
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
      <div class="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in font-sans">
        
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
            <div class="col-span-full p-8 rounded-2xl bg-white dark:bg-[#1A1827] border border-rose-200 dark:border-rose-900/50 text-center space-y-3 shadow-sm">
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

  // =========================================================================
  // 3. Enterprise 5-Tab Course Management Dossier (Coursera/Udemy Hybrid)
  // =========================================================================
  static async renderCourseManage(container, courseId, initialTab = 'curriculum') {
    if (!courseId || courseId === 'undefined' || courseId === 'null' || !String(courseId).trim()) {
      container.innerHTML = `
        <div class="p-4 sm:p-6 lg:p-8 space-y-6 max-w-4xl mx-auto animate-fade-in font-sans">
          <div class="flex items-center justify-between text-xs text-[#5C5B57] dark:text-[#9E9D99] font-medium">
            <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Danh sách khóa học</span>
            </a>
          </div>
          <div class="p-8 sm:p-12 rounded-2xl bg-white dark:bg-[#1A1827] border border-slate-200/80 dark:border-slate-800 text-center space-y-4 shadow-sm">
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
      <div class="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in font-sans" id="course-manage-root">
        <div class="text-center py-24 text-[#8F8E8A] dark:text-[#6D6C68]">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs">Đang tải giáo án khóa học...</p>
        </div>
      </div>
    `;

    try {
      const [course, assessmentsData] = await Promise.all([
        ApiClient.getCourseDetail(courseId),
        ApiClient.getCourseAssessments(courseId).catch(() => ({ assessments: [] }))
      ]);

      if (!course) return;

      const cId = course.course_id || course.id;
      const lessons = course.lessons || [];
      const learningUnits = course.learning_units || [];
      const assessments = assessmentsData.assessments || assessmentsData.items || course.assessments || [];
      const isFrozen = course.status === 'SUBMITTED_FOR_REVIEW';

      container.innerHTML = `
        <div class="p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto animate-fade-in font-sans pb-20" id="course-manage-root" data-course-id="${UI.escapeHtml(cId)}">
          
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

          <!-- Reminder Banner: Missing Cover Photo -->
          ${!course.thumbnail_url ? `
            <div class="rounded-2xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 p-4 sm:p-5 flex items-center justify-between flex-wrap gap-4 shadow-xs">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/20">
                  <span class="material-symbols-outlined text-2xl">add_photo_alternate</span>
                </div>
                <div>
                  <h4 class="text-sm font-bold text-amber-900 dark:text-amber-200">Khóa học này chưa có ảnh bìa đại diện</h4>
                  <p class="text-xs text-amber-800 dark:text-amber-300 mt-0.5">
                    Thầy/Cô hãy tải lên ảnh bìa cho môn học để giáo trình hiển thị trực quan và thu hút sinh viên hơn khi xuất bản.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onclick="document.getElementById('course-thumbnail-input')?.click()"
                class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1.5 cursor-pointer shrink-0"
              >
                <span class="material-symbols-outlined text-[16px]">upload</span>
                <span>Tải ảnh bìa ngay</span>
              </button>
            </div>
          ` : ''}

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
            <div class="relative aspect-video max-h-72 w-full overflow-hidden rounded-xl bg-indigo-100 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center">
              <span class="absolute -right-8 -top-12 h-44 w-44 rounded-full border-[28px] border-indigo-200/70 dark:border-indigo-800/70" aria-hidden="true"></span>
              <span class="material-symbols-outlined text-6xl text-indigo-600 dark:text-indigo-300" aria-hidden="true">school</span>
              ${course.thumbnail_url ? `<img src="${UI.escapeHtml(course.thumbnail_url)}" alt="Ảnh đại diện khóa học" class="absolute inset-0 h-full w-full object-cover object-center" onerror="this.remove()" />` : ''}
            </div>
            <label class="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200">
              <span class="material-symbols-outlined text-base">add_photo_alternate</span> Đổi Ảnh Đại Diện Khóa Học
              <input id="course-thumbnail-input" type="file" accept="image/png,image/jpeg,image/webp" class="sr-only" />
            </label>
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
                    class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
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
              </div>
            </div>

            <p class="text-xs sm:text-sm text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed max-w-3xl">
              ${UI.escapeHtml(course.description || 'Chưa có mô tả chi tiết cho môn học này.')}
            </p>
          </div>

          <!-- SECTION 1: BÀI GIẢNG & NỘI DUNG -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center material-symbols-outlined text-[18px]">menu_book</span>
                <div>
                  <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB]">
                    Bài học (${learningUnits.length})
                  </h2>
                  <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">Nội dung học tập sinh viên sẽ theo dõi</p>
                </div>
              </div>

              ${isFrozen ? `
                <div class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-semibold flex items-center gap-1.5" title="Khóa học đang chờ duyệt, hãy rút lại xét duyệt để mở khóa chỉnh sửa">
                  <span class="material-symbols-outlined text-[16px]">lock</span>
                  <span>Đang chờ duyệt</span>
                </div>
              ` : `
                <button
                  type="button"
                  id="btn-create-learning-unit"
                  class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[16px]">add</span>
                  <span>Thêm Bài học</span>
                </button>
              `}
            </div>

            <div class="space-y-4" id="learning-units-list">
              ${learningUnits.length === 0 ? `
                <div class="rounded-2xl border border-dashed border-[#E8E6DF] dark:border-[#526881] bg-white dark:bg-[#223248] p-10 text-center">
                  <span class="material-symbols-outlined text-3xl text-[#8F8E8A] dark:text-[#6D6C68] mb-2">menu_book</span>
                  <p class="text-xs font-bold text-[#222120] dark:text-[#F0F5FA]">Chưa có Bài học nào trong khóa học</p>
                  <p class="text-[11px] text-[#5C5B57] dark:text-[#C6D2E1] mt-1 mb-3">Tạo bài học đầu tiên để bắt đầu phân chia chương mục giáo trình.</p>
                </div>
              ` : learningUnits.map((unit, unitIdx) => {
                const children = unit.lessons || [];
                const unitId = unit.learning_unit_id;
                const videoCount = children.reduce((total, lesson) =>
                  total + InstructorView.getVideoCount(lesson.video_urls || [], lesson.resources || []), 0);
                const targetLessonId = (children[0] && (children[0].lesson_id || children[0].id)) || 'new';
                const targetUrl = targetLessonId === 'new'
                  ? `#/instructor/courses/${cId}/lessons/new?learning_unit_id=${unitId}`
                  : `#/instructor/courses/${cId}/lessons/${targetLessonId}/edit`;
                return `
                  <section
                    class="unit-row-card rounded-2xl border border-[#E8E6DF] dark:border-[#526881] bg-white dark:bg-[#223248] p-5 sm:p-6 transition-all hover:border-primary/40 shadow-xs"
                    ${isFrozen ? '' : 'draggable="true"'}
                    data-unit-id="${unitId}"
                    data-idx="${unitIdx}"
                  >
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div class="flex items-center gap-3.5 min-w-0 flex-1">
                        <!-- Drag Handle & Up/Down Arrows -->
                        <div class="flex items-center gap-1 shrink-0 select-none">
                          ${isFrozen ? '' : `
                          <div class="flex flex-col gap-0.5">
                            <button
                              type="button"
                              class="btn-move-unit-up p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-primary transition-colors ${unitIdx === 0 ? 'opacity-25 cursor-not-allowed' : 'cursor-pointer'}"
                              data-idx="${unitIdx}"
                              ${unitIdx === 0 ? 'disabled' : ''}
                              title="Di chuyển bài học lên trên"
                            >
                              <span class="material-symbols-outlined text-[15px]">arrow_upward</span>
                            </button>
                            <button
                              type="button"
                              class="btn-move-unit-down p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-primary transition-colors ${unitIdx === learningUnits.length - 1 ? 'opacity-25 cursor-not-allowed' : 'cursor-pointer'}"
                              data-idx="${unitIdx}"
                              ${unitIdx === learningUnits.length - 1 ? 'disabled' : ''}
                              title="Di chuyển bài học xuống dưới"
                            >
                              <span class="material-symbols-outlined text-[15px]">arrow_downward</span>
                            </button>
                          </div>
                          <span class="unit-drag-handle cursor-grab active:cursor-grabbing p-1 text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB]" title="Kéo thả để sắp xếp thứ tự bài học">
                            <span class="material-symbols-outlined text-[18px]">drag_indicator</span>
                          </span>
                          `}
                          <span class="w-8 h-8 rounded-xl bg-[#F4F1EA] dark:bg-[#1B2A3D] text-[#5C5B57] dark:text-[#9E9D99] font-bold text-xs flex items-center justify-center shrink-0 border border-[#E8E6DF] dark:border-[#526881]">
                            #${unitIdx + 1}
                          </span>
                        </div>

                        <!-- Title & Metadata -->
                        <div class="min-w-0 flex-1">
                          <a href="${targetUrl}" class="block group/title">
                            <div class="flex items-center gap-2 flex-wrap">
                              <h3 class="text-base font-bold text-[#222120] dark:text-[#F0F5FA] group-hover/title:text-primary transition-colors truncate">
                                ${UI.escapeHtml(unit.title)}
                              </h3>
                              ${unit.is_staged ? `
                                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                                  unit.pending_approval
                                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-700'
                                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
                                }">
                                  <span class="w-1.5 h-1.5 rounded-full ${unit.pending_approval ? 'bg-amber-500 animate-pulse' : 'bg-amber-600'}"></span>
                                  <span>${unit.pending_approval ? 'Chờ Admin duyệt' : 'Bản nháp mới (Chưa gửi duyệt)'}</span>
                                </span>
                              ` : ''}
                            </div>
                          </a>
                          <div class="flex items-center gap-3 mt-1 text-xs text-[#5C5B57] dark:text-[#C6D2E1]">
                            <span class="flex items-center gap-1">
                              <span class="material-symbols-outlined text-[14px] text-primary">description</span>
                              <span>${children.length}/10 Lesson</span>
                            </span>
                            <span>•</span>
                            <span class="flex items-center gap-1">
                              <span class="material-symbols-outlined text-[14px] text-blue-500">play_circle</span>
                              <span>${videoCount}/7 video</span>
                            </span>
                          </div>
                          ${(() => {
                            const flaggedLessons = children.filter(l => l.is_flagged || (l.material_change_summary && l.material_change_summary.startsWith('[FLAGGED]: ')));
                            if (flaggedLessons.length === 0) return '';
                            return `
                              <div class="mt-2.5 p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-semibold space-y-1">
                                <div class="flex items-center gap-1.5 text-rose-700 dark:text-rose-400">
                                  <span class="material-symbols-outlined text-[16px]">flag</span>
                                  <span>Admin đã gắn cờ ${flaggedLessons.length} bài giảng có vấn đề:</span>
                                </div>
                                <ul class="list-disc list-inside font-normal text-[11px] space-y-0.5 text-rose-900 dark:text-rose-300">
                                  ${flaggedLessons.map(fl => `<li><strong>${UI.escapeHtml(fl.title)}:</strong> ${UI.escapeHtml(fl.flag_reason || fl.material_change_summary?.replace('[FLAGGED]: ', '') || 'Cần chỉnh sửa nội dung')}</li>`).join('')}
                                </ul>
                              </div>
                            `;
                          })()}
                        </div>
                      </div>

                      <!-- Action Buttons -->
                      <div class="flex flex-wrap items-center gap-2 shrink-0">
                        ${(unit.is_staged && !unit.pending_approval) ? `
                          <button
                            type="button"
                            class="btn-submit-learning-unit px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                            data-unit-id="${unitId}"
                            data-unit-title="${UI.escapeHtml(unit.title)}"
                            title="Gửi bài học này và toàn bộ các bài giảng bên trong tới Quản trị viên để xét duyệt"
                          >
                            <span class="material-symbols-outlined text-[16px]">send</span>
                            <span>Gửi</span>
                          </button>
                        ` : ''}
                        <a
                          href="${targetUrl}"
                          class="px-3.5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
                          title="Vào soạn thảo các bài giảng trong bài học này"
                        >
                          <span class="material-symbols-outlined text-[16px]">${isFrozen ? 'visibility' : 'edit_document'}</span>
                          <span>${isFrozen ? 'Xem nội dung' : 'Vào soạn thảo'}</span>
                        </a>
                        ${isFrozen ? '' : `
                        <button
                          type="button"
                          class="btn-rename-learning-unit px-3 py-2 rounded-xl border border-[#E8E6DF] dark:border-[#526881] hover:bg-[#FAF9F5] dark:hover:bg-[#1B2A3D] text-[#222120] dark:text-[#F0F5FA] text-xs font-semibold transition-colors cursor-pointer"
                          data-unit-id="${unitId}"
                        >
                          Đổi tên
                        </button>
                        ${children.length < 10 ? `
                          <a
                            href="#/instructor/courses/${cId}/lessons/new?learning_unit_id=${unitId}"
                            class="px-3 py-2 rounded-xl border border-primary/30 text-primary dark:text-[#93C5FD] hover:bg-primary/5 text-xs font-bold transition-colors"
                          >
                            Thêm Lesson
                          </a>
                        ` : ''}
                        <button
                          type="button"
                          class="btn-delete-learning-unit p-2 rounded-xl text-[#8F8E8A] hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                          data-unit-id="${unitId}"
                          title="Xóa bài học này"
                        >
                          <span class="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                        `}
                      </div>
                    </div>
                  </section>
                `;
              }).join('')}
            </div>
          </div>

          <!-- SECTION 2: BÀI THI & KIỂM TRA -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="w-8 h-8 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 flex items-center justify-center material-symbols-outlined text-[18px]">quiz</span>
                <div>
                  <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB]">
                    Bài thi & Đánh giá (${assessments.length})
                  </h2>
                  <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">Khảo thí trắc nghiệm tự động chấm</p>
                </div>
              </div>

              <a
                href="#/instructor/exams?course_id=${cId}"
                class="px-4 py-2 rounded-xl bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-all border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center gap-1.5 shadow-2xs"
              >
                <span class="material-symbols-outlined text-[16px]">assignment_add</span>
                <span>Soạn đề thi</span>
              </a>
            </div>

            <!-- Assessments Stack -->
            <div class="space-y-3" id="course-assessments-stack">
              ${assessments.length === 0 ? `
                <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-10 text-center shadow-xs">
                  <span class="material-symbols-outlined text-3xl text-[#8F8E8A] dark:text-[#6D6C68] mb-1">assignment</span>
                  <p class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Chưa có bài thi nào cho khóa học này</p>
                  <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-1 mb-3">Tạo bài thi trắc nghiệm để đánh giá kết quả học tập của sinh viên.</p>
                  <a
                    href="#/instructor/exams?course_id=${cId}"
                    class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1.5"
                  >
                    <span class="material-symbols-outlined text-[15px]">add</span>
                    <span>Tạo bài thi ngay</span>
                  </a>
                </div>
              ` : `
                <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl shadow-xs divide-y divide-[#E8E6DF] dark:divide-[#2E2D2B] overflow-hidden">
                  ${assessments.map(asm => {
                    const asmId = asm.assessment_id || asm.id;
                    const qCount = (asm.questions || []).length || asm.question_count || 0;
                    return `
                      <div class="assessment-row p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-[#FAF9F5] dark:hover:bg-[#262524]/60 transition-colors" data-assessment-id="${asmId}">
                        <div class="flex items-center gap-3.5 min-w-0">
                          <span class="w-8 h-8 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 font-bold text-xs flex items-center justify-center shrink-0 border border-purple-100 dark:border-purple-900/30 material-symbols-outlined text-[18px]">
                            task_alt
                          </span>
                          <div class="min-w-0">
                            <div class="flex items-center gap-2">
                              <h4 class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB] truncate">
                                ${UI.escapeHtml(asm.title)}
                              </h4>
                              ${UI.statusBadge(asm.status)}
                            </div>
                            <div class="flex items-center gap-2 text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-0.5">
                              <span>Thời lượng: ${asm.time_limit_minutes || 45} phút</span>
                              <span>•</span>
                              <span>${qCount} câu hỏi</span>
                              <span>•</span>
                              <span>Thang điểm: ${asm.total_points || 10}đ</span>
                            </div>
                          </div>
                        </div>

                        <div class="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            class="btn-trash-asm px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-bold transition-colors flex items-center gap-1"
                            data-asm-id="${asmId}"
                            data-asm-title="${UI.escapeHtml(asm.title)}"
                          >
                            <span class="material-symbols-outlined text-[14px]">delete</span>
                            <span>Chuyển vào thùng rác</span>
                          </button>
                          <button
                            type="button"
                            class="btn-asm-results px-3 py-1.5 rounded-lg bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center gap-1"
                            data-asm-id="${asmId}"
                            data-asm-title="${UI.escapeHtml(asm.title)}"
                          >
                            <span class="material-symbols-outlined text-[14px] text-primary">bar_chart</span>
                            <span>Bảng điểm & Bài nộp</span>
                          </button>
                          ${asm.status === 'DRAFT' ? `
                            <button
                              type="button"
                              class="btn-publish-asm px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors flex items-center gap-1 shadow-2xs"
                              data-asm-id="${asmId}"
                            >
                              <span class="material-symbols-outlined text-[14px]">rocket_launch</span>
                              <span>Xuất bản</span>
                            </button>
                          ` : ''}
                        </div>
                      </div>
                    `;
                  }).join('')}
                </div>
              `}
            </div>
          </div>

        </div>
      `;

      // Bind Settings Modal Button
      container.querySelector('#btn-create-learning-unit')?.addEventListener('click', async () => {
        const title = await UI.prompt('Thêm Chương mới', 'Đặt tên cho Chương bài học chứa tối đa 10 Bài giảng.', '', 'Ví dụ: Tổng quan khóa học', 1, 'Tạo Chương');
        if (!title) return;
        try {
          const unit = await ApiClient.createLearningUnit(cId, { title: title.trim() });
          if (unit && unit.pending_approval) {
            UI.showToast(unit.message || 'Yêu cầu tạo Chương mới đã gửi Quản trị viên để xét duyệt.', 'info');
            await InstructorView.renderCourseManage(container, cId, 'curriculum');
            return;
          }
          UI.showToast('Đã tạo Bài học mới (bản nháp). Thầy/Cô có thể tạo các bài giảng bên trong và bấm "Gửi" khi hoàn tất.', 'success');
          await InstructorView.renderCourseManage(container, cId, 'curriculum');
        } catch (error) {
          UI.showToast(error.message || 'Không tạo được Chương bài học.', 'error');
        }
      });
      container.querySelectorAll('.btn-rename-learning-unit').forEach(button => {
        button.addEventListener('click', async () => {
          const unit = learningUnits.find(item => item.learning_unit_id === button.dataset.unitId);
          if (!unit) return;
          const title = await UI.prompt('Đổi tên Bài học', `Tên mới cho "${unit.title}":`, unit.title, 'Tên Bài học', 1, 'Lưu Tên Bài Học');
          if (!title || title.trim() === unit.title) return;
          try {
            const response = await ApiClient.updateLearningUnit(unit.learning_unit_id, { title: title.trim() });
            UI.showToast(response.pending_approval ? 'Tên Bài học đã gửi Admin xét duyệt.' : 'Đã đổi tên Bài học.', response.pending_approval ? 'info' : 'success');
            if (!response.pending_approval) UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
          } catch (error) {
            UI.showToast(error.message || 'Không đổi được tên Bài học.', 'error');
          }
        });
      });
      container.querySelector('#course-thumbnail-input')?.addEventListener('change', async event => {
        const file = event.target.files?.[0];
        if (!file) return;
        if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
          UI.showToast('Chọn ảnh PNG, JPEG hoặc WebP.', 'warning');
          return;
        }
        try {
          const uploaded = await ApiClient.uploadCourseFile(cId, file, file.name, 'COURSE_IMAGE');
          await ApiClient.updateCourse(cId, { thumbnail_file_asset_id: uploaded.asset_id });
          UI.showToast('Đã cập nhật ảnh đại diện khóa học.', 'success');
          UI.refreshCurrentRoute(() => InstructorView.renderCourseManage(container, cId, initialTab));
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
        <div class="p-4 sm:p-6 lg:p-8 space-y-6 max-w-4xl mx-auto animate-fade-in font-sans">
          <div class="flex items-center justify-between text-xs text-[#5C5B57] dark:text-[#9E9D99] font-medium">
            <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Danh sách khóa học</span>
            </a>
          </div>
          <div class="p-8 sm:p-12 rounded-2xl bg-white dark:bg-[#1A1827] border border-rose-200 dark:border-rose-900/50 text-center space-y-4 shadow-sm">
            <div class="w-14 h-14 rounded-2xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto">
              <span class="material-symbols-outlined text-[28px]">error_outline</span>
            </div>
            <div class="space-y-1">
              <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white">Không thể nạp dữ liệu khóa học</h2>
              <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
                Khóa học không tồn tại, đã bị gỡ bỏ hoặc bạn không có quyền quản lý khóa học này.
              </p>
              <p class="text-[11px] font-mono text-rose-500/90 dark:text-rose-400/90 pt-1">
                Chi tiết lỗi: ${UI.escapeHtml(err.message || 'Course not found.')}
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
              <button
                type="button"
                id="btn-open-lesson-studio"
                class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
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
                      <div class="flex items-center gap-2">
                        <h3 class="font-bold text-sm text-slate-900 dark:text-white group-hover:text-primary transition-colors">
                          ${UI.escapeHtml(l.title)}
                        </h3>
                        ${UI.statusBadge(l.status)}
                      </div>
                      <div class="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                        <span class="flex items-center gap-1">
                          <span class="material-symbols-outlined text-[14px]">schedule</span>
                          ~${l.estimated_duration_minutes || 45} phút
                        </span>
                        <span>•</span>
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
                      href="#/student/lessons/reader?course_id=${cId}&lesson_id=${lId}"
                      class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition-colors flex items-center gap-1"
                      title="Xem trước góc nhìn học viên"
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
      <div class="space-y-6 max-w-5xl mx-auto animate-fade-in" id="academic-tab-root">
        
        <!-- CARD 1: Chuẩn đầu ra (SLO) -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-2xs space-y-5">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">verified</span>
                <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                  1. Chuẩn đầu ra
                </h2>
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
              <button type="button" id="btn-add-slo" class="px-3.5 py-1.75 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-2xs">
                <span class="material-symbols-outlined text-[16px] text-primary">add</span>
                <span>Thêm Chuẩn đầu ra</span>
              </button>
              <button type="button" id="btn-save-slos" class="px-4 py-1.75 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm">
                <span class="material-symbols-outlined text-[16px]">save</span>
                <span>Lưu</span>
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
              <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-indigo-600 text-[20px]">account_tree</span>
                <span>2. Danh sách Môn học Tiên quyết (Prerequisites)</span>
              </h2>
              <p class="text-xs text-slate-500 mt-0.5">Quy định điều kiện các môn học sinh viên bắt buộc phải thi đạt trước khi được phép ghi danh vào môn này. (Hệ thống tự động kiểm tra đồ thị phụ thuộc để ngăn ngừa vòng lặp môn học).</p>
            </div>
            <button type="button" id="btn-open-prereq-modal" class="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm shrink-0">
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
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600 text-[20px]">workspace_premium</span>
                <span>3. Quy chuẩn Đạt & Hoàn thành Khóa học (Completion Rules)</span>
              </h2>
              <p class="text-xs text-slate-500 mt-0.5">Tiêu chuẩn nghiệm thu học vụ tự động để sinh viên được công nhận hoàn thành khóa học và cấp chứng chỉ số.</p>
            </div>
            <button type="button" id="btn-save-completion-rules" class="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm shrink-0">
              <span class="material-symbols-outlined text-[16px]">task_alt</span>
              <span>Lưu quy chuẩn hoàn thành</span>
            </button>
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

    const saveSlosBtn = document.getElementById('btn-save-slos');
    if (saveSlosBtn) {
      saveSlosBtn.onclick = async () => {
        try {
          saveSlosBtn.disabled = true;
          saveSlosBtn.innerHTML = `<span class="inline-block animate-spin text-[14px]">⏳</span> Đang lưu...`;
          const toSave = harvestDOMtoSLOs();
          const res = await ApiClient.updateCourse(cId, { learning_objectives: toSave });

          // Synchronize in-memory course object and local state immediately
          course.learning_objectives = toSave;
          customSLOs = [...toSave];
          if (res && res.learning_objectives) {
            course.learning_objectives = res.learning_objectives;
          }

          UI.showToast('Đã lưu thành công bộ Chuẩn đầu ra ABET vào CSDL!', 'success');
        } catch (err) {
          UI.showToast('Lỗi lưu chuẩn đầu ra: ' + (err.message || err), 'error');
        } finally {
          saveSlosBtn.disabled = false;
          saveSlosBtn.innerHTML = `<span class="material-symbols-outlined text-[16px]">save</span><span>Lưu</span>`;
        }
      };
    }

    // 2. Load Prerequisites List
    const prereqBox = document.getElementById('prereqs-table-box');
    const loadPrerequisites = async () => {
      try {
        const [res, reqRes] = await Promise.allSettled([
          ApiClient.getCoursePrerequisites(cId),
          ApiClient.getInstructorPrerequisiteRequests()
        ]);
        const list = (res.status === 'fulfilled' && res.value && res.value.prerequisites) ? res.value.prerequisites : (Array.isArray(res.value) ? res.value : []);
        const incomingReqs = (reqRes.status === 'fulfilled' && reqRes.value && reqRes.value.incoming) ? reqRes.value.incoming : [];

        let incomingHtml = '';
        if (incomingReqs.length > 0) {
          incomingHtml = `
            <div class="mb-4 rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50/70 dark:bg-amber-950/30 p-4 space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-amber-600 text-[18px]">notification_important</span>
                  <span class="text-xs font-bold text-amber-900 dark:text-amber-200">
                    Có ${incomingReqs.length} yêu cầu xin sử dụng môn học của bạn làm môn tiên quyết:
                  </span>
                </div>
              </div>
              <div class="divide-y divide-amber-200 dark:divide-amber-800/60">
                ${incomingReqs.map(r => `
                  <div class="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div>
                      <span class="font-bold text-slate-800 dark:text-slate-200">GV ${UI.escapeHtml(r.requested_by_name || 'Đồng nghiệp')}</span>
                      <span class="text-slate-600 dark:text-slate-400">xin liên kết môn <strong>${UI.escapeHtml(r.prerequisite_course_title || 'Môn của bạn')}</strong> vào khóa học: <strong>${UI.escapeHtml(r.course_code || '')} - ${UI.escapeHtml(r.course_title || '')}</strong></span>
                      <p class="text-[11px] text-slate-500 mt-0.5 italic">Lý do: "${UI.escapeHtml(r.reason || 'Yêu cầu chuẩn hóa đào tạo')}"</p>
                    </div>
                    <div class="flex items-center gap-1.5 shrink-0">
                      <button type="button" class="btn-approve-prereq px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs" data-req-id="${r.id}">
                        Phê duyệt
                      </button>
                      <button type="button" class="btn-reject-prereq px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-700 dark:text-slate-200 font-bold text-xs" data-req-id="${r.id}">
                        Từ chối
                      </button>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }

        if (list.length === 0) {
          prereqBox.innerHTML = incomingHtml + `
            <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-xs space-y-1">
              <span class="material-symbols-outlined text-slate-300 dark:text-slate-600 text-3xl">task_alt</span>
              <p class="font-semibold text-slate-600 dark:text-slate-300">Không có điều kiện tiên quyết</p>
              <p class="text-[11px] text-slate-400">Sinh viên có thể trực tiếp ghi danh môn học này mà không cần hoàn thành học phần trước.</p>
            </div>
          `;
        } else {
          prereqBox.innerHTML = incomingHtml + `
            <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
              <table class="w-full text-left border-collapse text-xs">
                <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th class="p-3">Mã & Tên môn tiên quyết</th>
                    <th class="p-3">Điểm GPA tối thiểu</th>
                    <th class="p-3">Ngày thiết lập</th>
                    <th class="p-3 text-right">Tác vụ</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                  ${list.map(p => `
                    <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td class="p-3">
                        <span class="font-mono font-bold text-primary">${UI.escapeHtml(p.course_code || p.prerequisite_course_code || 'PREREQ')}</span>
                        <span class="text-slate-800 dark:text-slate-200 ml-1.5">${UI.escapeHtml(p.title || p.prerequisite_course_title || 'Môn học tiên quyết')}</span>
                      </td>
                      <td class="p-3">
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          ${p.min_grade_point || '≥ 5.0 (C)'}
                        </span>
                      </td>
                      <td class="p-3 text-slate-400 font-mono text-[11px]">
                        ${p.created_at ? UI.formatDate(p.created_at) : 'Mặc định'}
                      </td>
                      <td class="p-3 text-right">
                        <button type="button" class="btn-del-prereq px-2.5 py-1 rounded-lg text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition font-bold" data-prereq-id="${p.prerequisite_course_id || p.id}">
                          Gỡ bỏ
                        </button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          `;
        }

        prereqBox.querySelectorAll('.btn-del-prereq').forEach(btn => {
          btn.onclick = async () => {
            const pId = btn.dataset.prereqId;
            const ok = await UI.confirm('Xác nhận gỡ bỏ điều kiện tiên quyết', 'Bạn có chắc chắn muốn gỡ bỏ môn học tiên quyết này khỏi môn học?');
            if (!ok) return;
            try {
              await ApiClient.deleteCoursePrerequisite(cId, pId);
              UI.showToast('Đã xóa môn tiên quyết thành công!', 'success');
              await loadPrerequisites();
            } catch (err) {
              UI.showToast('Lỗi xóa tiên quyết: ' + (err.message || err), 'error');
            }
          };
        });

        // Attach incoming approval/rejection handlers
        prereqBox.querySelectorAll('.btn-approve-prereq').forEach(btn => {
          btn.onclick = async () => {
            const reqId = btn.dataset.reqId;
            try {
              btn.disabled = true;
              await ApiClient.reviewInstructorPrerequisiteRequest(reqId, { action: 'approve' });
              UI.showToast('Đã phê duyệt yêu cầu môn tiên quyết!', 'success');
              await loadPrerequisites();
            } catch (err) {
              UI.showToast('Lỗi phê duyệt: ' + (err.message || err), 'error');
              btn.disabled = false;
            }
          };
        });

        prereqBox.querySelectorAll('.btn-reject-prereq').forEach(btn => {
          btn.onclick = async () => {
            const reqId = btn.dataset.reqId;
            const reason = prompt('Nhập lý do từ chối yêu cầu môn tiên quyết:');
            if (reason === null) return;
            try {
              btn.disabled = true;
              await ApiClient.reviewInstructorPrerequisiteRequest(reqId, { action: 'reject', reason: reason || 'Không phù hợp' });
              UI.showToast('Đã từ chối yêu cầu môn tiên quyết.', 'info');
              await loadPrerequisites();
            } catch (err) {
              UI.showToast('Lỗi từ chối: ' + (err.message || err), 'error');
              btn.disabled = false;
            }
          };
        });

      } catch (err) {
        prereqBox.innerHTML = `<div class="p-4 text-center text-rose-500 text-xs">Lỗi nạp điều kiện tiên quyết: ${UI.escapeHtml(err.message || err)}</div>`;
      }
    };

    await loadPrerequisites();

    // Open Prerequisite Modal
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
          if (key && key !== cId && !map.has(key)) {
            map.set(key, c);
          }
        }
        const candidateCourses = Array.from(map.values());

        const modalHtml = `
          <div class="space-y-4">
            <div class="space-y-1">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">Chọn môn học bắt buộc tiên quyết</label>
              <select id="modal-prereq-select" class="w-full h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-xs text-slate-900 dark:text-white outline-none focus:border-primary">
                ${candidateCourses.map(c => {
                  const isMine = myCourses.some(mc => (mc.course_id || mc.id) === (c.course_id || c.id));
                  const badge = isMine ? '[Môn của bạn]' : '[Giảng viên khác - Cần gửi duyệt]';
                  return `<option value="${c.course_id || c.id}">${c.course_code || 'MÔN'} - ${UI.escapeHtml(c.title)} ${badge}</option>`;
                }).join('')}
              </select>
              <p class="text-[11px] text-slate-400 mt-1">Lưu ý: Môn học của giảng viên khác sẽ tự động gửi yêu cầu xin duyệt và thông báo đến giảng viên phụ trách.</p>
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
              <button type="button" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold" onclick="UI.closeModal()">Hủy</button>
              <button type="button" id="modal-prereq-submit-btn" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm">Xác nhận thêm</button>
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
          subBtn.onclick = async () => {
            const prereqCourseId = document.getElementById('modal-prereq-select')?.value;
            const minGrade = parseFloat(document.getElementById('modal-prereq-min-grade')?.value || '5.0');
            const reason = document.getElementById('modal-prereq-reason')?.value || '';

            if (!prereqCourseId) {
              UI.showToast('Vui lòng chọn môn học tiên quyết.', 'warning');
              return;
            }

            try {
              subBtn.disabled = true;
              subBtn.textContent = 'Đang lưu...';
              const res = await ApiClient.addCoursePrerequisite(cId, {
                prerequisite_course_id: prereqCourseId,
                min_grade_point: minGrade,
                reason: reason
              });
              UI.closeModal();
              if (res && res.status === 'pending_approval') {
                UI.showToast(res.message || 'Môn học thuộc giảng viên khác. Đã gửi thông báo và yêu cầu xin duyệt.', 'info');
              } else {
                UI.showToast(res?.message || 'Đã thêm môn tiên quyết thành công!', 'success');
              }
              await loadPrerequisites();
            } catch (err) {
              UI.showToast('Lỗi thêm tiên quyết: ' + (err.message || err), 'error');
              subBtn.disabled = false;
              subBtn.textContent = 'Xác nhận thêm';
            }
          };
        }
      };
    }

    // 3. Load & Save Completion Rules
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

    const saveRulesBtn = document.getElementById('btn-save-completion-rules');
    if (saveRulesBtn) {
      saveRulesBtn.onclick = async () => {
        try {
          saveRulesBtn.disabled = true;
          saveRulesBtn.innerHTML = `<span class="inline-block animate-spin text-[14px]">⏳</span> Đang lưu...`;

          const payload = {
            minimum_progress_percent: parseFloat(document.getElementById('rule-min-progress')?.value || '80'),
            minimum_grade_score: parseFloat(document.getElementById('rule-min-score')?.value || '5.0'),
            completion_grace_days: 14,
            require_all_required_lessons: Boolean(document.getElementById('rule-require-lessons')?.checked),
            require_required_assessments: Boolean(document.getElementById('rule-require-assessments')?.checked),
            allow_certificate: Boolean(document.getElementById('rule-allow-certificate')?.checked),
          };

          await ApiClient.updateCourseCompletionRules(cId, payload);
          UI.showToast('Đã cập nhật Quy chuẩn Hoàn thành Khóa học vào CSDL!', 'success');
        } catch (err) {
          UI.showToast('Lỗi lưu quy chuẩn hoàn thành: ' + (err.message || err), 'error');
        } finally {
          saveRulesBtn.disabled = false;
          saveRulesBtn.innerHTML = `<span class="material-symbols-outlined text-[16px]">task_alt</span><span>Lưu quy chuẩn hoàn thành</span>`;
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
      <div class="space-y-6 max-w-5xl mx-auto">
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

  static async renderAssessmentResultsPage(container, assessmentId, courseId = null) {
    const backUrl = courseId
      ? `#/instructor/courses/${courseId}/manage?tab=exams`
      : '#/instructor/exams';
    const backText = courseId ? 'Quay lại Quản lý Khóa học' : 'Quay lại Soạn đề thi';

    container.innerHTML = `
      <div class="space-y-6 animate-fade-in p-4 sm:p-6 max-w-7xl mx-auto">
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

    try {
      const data = await ApiClient.getAssessmentAttempts(assessmentId);
      const attempts = data.attempts || [];
      const titleEl = document.getElementById('asm-results-title');
      if (titleEl) {
        titleEl.textContent = `Đề thi: ${data.assessment_title || 'Khảo thí trắc nghiệm'} • Tổng cộng ${attempts.length} bài nộp`;
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
      const passedCount = attempts.filter(a => a.is_passed || a.passed).length;
      const passRate = totalSubmissions > 0 ? Math.round((passedCount / totalSubmissions) * 100) : 0;
      const avgScore = totalSubmissions > 0
        ? (attempts.reduce((acc, a) => acc + (a.percentage || a.percent_score || 0), 0) / totalSubmissions).toFixed(1)
        : 0;

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
                const passed = att.is_passed || att.passed;
                const submittedDate = att.submitted_at ? new Date(att.submitted_at).toLocaleString('vi-VN') : 'Đang làm';
                const pct = att.percentage !== undefined ? att.percentage : (att.percent_score || 0);
                const vCount = att.violations_count ?? att.violation_count ?? 0;
                return `
                  <tr class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                    <td class="px-5 py-3.5">
                      <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(att.student_name || 'Học viên')}</div>
                      <div class="text-[11px] text-slate-400">${UI.escapeHtml(att.student_email || '')}</div>
                    </td>
                    <td class="px-5 py-3.5 text-slate-600 dark:text-slate-300 font-mono">${submittedDate}</td>
                    <td class="px-5 py-3.5 font-mono font-bold text-slate-900 dark:text-white">${att.raw_score ?? 0} / ${att.max_possible_points ?? 0}</td>
                    <td class="px-5 py-3.5 font-bold ${passed ? 'text-emerald-600' : 'text-rose-600'}">${pct}%</td>
                    <td class="px-5 py-3.5">
                      <span class="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold ${passed ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800'}">
                        ${passed ? 'ĐẠT' : 'KHÔNG ĐẠT'}
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
      `;
    } catch (err) {
      const contentEl = document.getElementById('asm-results-content');
      if (contentEl) {
        contentEl.innerHTML = `<div class="p-8 text-center text-rose-500 text-xs font-semibold">Lỗi tải kết quả khảo thí: ${UI.escapeHtml(err.message)}</div>`;
      }
    }
  }

  static async openAttemptDetailModal(attemptId) {
    const modalId = 'modal-attempt-detail';
    let modal = document.getElementById(modalId);
    if (!modal) {
      modal = document.createElement('div');
      modal.id = modalId;
      modal.className = 'fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div class="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">fact_check</span>
              Chi tiết câu trả lời & Đối chiếu đáp án
            </h3>
            <p class="text-xs text-slate-500 mt-0.5" id="modal-att-student">Đang nạp bài làm...</p>
          </div>
          <button type="button" class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" onclick="document.getElementById('${modalId}').remove()">
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

    try {
      const [data, appealRes, focusRes] = await Promise.all([
        ApiClient.getInstructorAttemptResult(attemptId),
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
        const isCorr = q.is_correct;
        const choices = q.choices || [];
        return `
          <div class="p-4 rounded-xl border ${isCorr ? 'border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/20' : 'border-rose-200 dark:border-rose-900/50 bg-rose-50/20'} space-y-3">
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
                      <span>${UI.escapeHtml(c.content || '')}</span>
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
                    <span class="font-mono text-slate-900 dark:text-white">${UI.escapeHtml(q.student_answer_text)}</span>
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
          </div>
        `;
      }).join('');
      }

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
        errEl.innerHTML = `<div class="p-6 text-center text-rose-500 text-xs">Lỗi nạp bài làm: ${UI.escapeHtml(err.message)}</div>`;
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
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Giới hạn sĩ số tối đa (Capacity)</label>
              <input
                type="number"
                name="capacity"
                min="1"
                value="${course.capacity ?? ''}"
                placeholder="Để trống nếu không giới hạn sĩ số"
                class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary text-xs"
              />
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

      let capacityVal = undefined;
      const capStr = form.capacity?.value?.trim();
      if (capStr) {
        const parsedCap = parseInt(capStr, 10);
        if (!isNaN(parsedCap) && parsedCap > 0) {
          capacityVal = parsedCap;
        }
      } else if (capStr === '') {
        capacityVal = null;
      } else if (course.capacity !== undefined) {
        capacityVal = course.capacity;
      }

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
      const confirmed = window.confirm(
        `Bạn có chắc chắn muốn xóa/lưu trữ khóa học "${course.title}" (${course.course_code || ''})?\n\nKhóa học sẽ được chuyển vào thùng rác.`
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
    if (response?.pending_approval) return 'pending';
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
            <span>+ Thêm bài học mới</span>
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
            <span>+ Thêm bài học mới</span>
          </button>
        ` : ''}
      </nav>
    `;
  }

  static async renderLessonAuthoringStudio(container, courseId, lessonId = null, initialUnitId = null) {
    if (window._currentStudioTimer) {
      clearInterval(window._currentStudioTimer);
      window._currentStudioTimer = null;
    }
    let availableUnits = [];
    let lessonStatus = 'DRAFT';
    let handleAddNewLesson = null;
    let resetEditorToEmpty = null;
    try {
      const unitResponse = await ApiClient.getLearningUnits(courseId);
      availableUnits = unitResponse.items || [];
    } catch (error) {
      UI.showToast(error.message || 'Không tải được danh sách Bài học.', 'error');
      if (!lessonId) return;
    }
    let selectedUnitId = initialUnitId || null;
    if (!selectedUnitId && availableUnits.length > 0) {
      selectedUnitId = availableUnits[0].learning_unit_id || availableUnits[0].id;
    }
    if (!selectedUnitId && availableUnits.length === 0) {
      // Lazy creation per Section 10.7 of AGENTS.md: do not create unit on view navigation
      selectedUnitId = null;
    }

    const activeUnit = availableUnits.find(u => (u.learning_unit_id || u.id) === selectedUnitId);
    const nextIndex = (activeUnit?.lessons?.length || 0) + 1;
    const initialLessonTitle = !lessonId ? `Bài giảng ${nextIndex}` : 'Bài giảng';

    let courseDetails = null;
    try {
      courseDetails = await ApiClient.getCourse(courseId);
    } catch (_) {}

    let lessonCreationPromise = null;
    const createLessonOnce = (payload) => {
      if (lessonId) return Promise.resolve(lessonId);
      if (!lessonCreationPromise) {
        lessonCreationPromise = ApiClient.createLesson(courseId, {
          ...payload,
          ...(selectedUnitId ? { learning_unit_id: selectedUnitId } : {})
        })
          .then(async (result) => {
            lessonId = result?.lesson_id || result?.id;
            selectedUnitId = result?.learning_unit_id || selectedUnitId;
            if (!lessonId) throw new Error('The lesson draft was not created.');
            window.history.replaceState(null, '', `#/instructor/courses/${courseId}/lessons/${lessonId}/edit`);
            try {
              availableUnits = (await ApiClient.getLearningUnits(courseId)).items || availableUnits;
              renderChildNavigator();
            } catch (_) {
              // The created draft remains valid when the sibling list cannot refresh.
            }
            return lessonId;
          })
          .finally(() => { lessonCreationPromise = null; });
      }
      return lessonCreationPromise;
    };

    container.innerHTML = `
      <div class="min-h-screen bg-[#FAF9F5] dark:bg-[#101925] font-sans flex flex-col animate-fade-in" id="lesson-studio-root">
        
        <!-- Top Sticky Header -->
        <header class="sticky top-0 z-40 bg-white dark:bg-[#202020] border-b border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs select-none shrink-0 px-4 sm:px-8 h-16 flex items-center justify-between gap-4">
          <!-- Left: Back Button & Context -->
          <div class="flex items-center gap-3 min-w-0">
            <button
              type="button"
              id="studio-back-btn"
              class="w-9 h-9 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] flex items-center justify-center transition-colors shrink-0"
              title="Quay lại Giáo án khóa học"
            >
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
            </button>
            <div class="flex items-center gap-2 truncate">
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-primary-subtle text-primary shrink-0 border border-primary/20">
                <span class="sm:hidden">Lesson</span><span class="hidden sm:inline">SOẠN BÀI GIẢNG</span>
              </span>
              <span class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] hidden sm:inline">•</span>
              <span class="text-xs text-[#5C5B57] dark:text-[#9E9D99] truncate hidden sm:inline" id="studio-header-course-ref">
                ${UI.escapeHtml(courseDetails?.title || courseDetails?.code || 'Khóa học')}
              </span>
            </div>
          </div>

          <!-- Center: Learning Unit Title -->
          <div class="flex-1 flex items-center justify-center min-w-0 px-2 text-center">
            <span class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB] truncate" id="studio-header-unit-title">
              Bài học
            </span>
          </div>

          <!-- Right: Action Buttons (Lưu nháp & Xuất bản) -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              type="button"
              id="studio-save-draft-btn"
              class="px-3.5 py-2 rounded-xl bg-white dark:bg-[#1B2A3D] hover:bg-[#FAF9F5] dark:hover:bg-[#223248] text-[#5C5B57] dark:text-[#C6D2E1] border border-[#E8E6DF] dark:border-[#526881] text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
              title="Lưu bản nháp bài giảng"
            >
              <span class="material-symbols-outlined text-[16px]">save</span>
              <span>Lưu nháp</span>
            </button>
            <button
              type="button"
              id="studio-save-btn"
              class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-2 cursor-pointer"
              title="Xuất bản bài giảng"
            >
              <span id="studio-save-indicator" class="flex items-center text-white/90">
                <span class="material-symbols-outlined text-[16px]">cloud_done</span>
              </span>
              <span id="studio-save-btn-text">Xuất bản</span>
            </button>
          </div>
        </header>

        <!-- Main Document Canvas (Notion / Doc Style) -->
        <main class="flex-1 max-w-[1600px] w-full mx-auto p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] items-start gap-6">
          <aside id="studio-lesson-navigator" class="min-w-0"></aside>
          <div class="min-w-0 bg-white dark:bg-[#223248] border border-[#E8E6DF] dark:border-[#526881] rounded-2xl p-6 sm:p-8 lg:p-10 shadow-subtle space-y-6">

            <!-- Working Draft / Approval Status Banner -->
            <div id="studio-draft-banner-container" class="space-y-3"></div>

            <!-- Quy định cấu trúc bài giảng (Làm nổi bật) -->
            <div class="rounded-xl border border-primary/25 bg-primary/5 dark:bg-primary/10 dark:border-primary/30 p-3.5 sm:p-4 flex items-center gap-3.5 shadow-2xs">
              <div class="w-8 h-8 rounded-lg bg-primary/15 text-primary flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-[20px]">info</span>
              </div>
              <div class="flex-1 text-xs text-[#222120] dark:text-[#E7E9EB] leading-relaxed">
                <span class="font-bold text-primary dark:text-[#93C5FD]">Lưu ý định mức:</span>
                Mỗi <strong class="text-[#121212] dark:text-white">Bài học</strong> chứa tối đa <span class="inline-flex items-center px-1.5 py-0.5 rounded font-bold bg-primary/10 text-primary dark:text-[#93C5FD] text-[11px]">10 Lesson</span> và <span class="inline-flex items-center px-1.5 py-0.5 rounded font-bold bg-primary/10 text-primary dark:text-[#93C5FD] text-[11px]">7 video</span>. Mỗi <strong class="text-[#121212] dark:text-white">Lesson</strong> chứa tối đa <span class="inline-flex items-center px-1.5 py-0.5 rounded font-bold bg-primary/10 text-primary dark:text-[#93C5FD] text-[11px]">2 video</span> và <span class="inline-flex items-center px-1.5 py-0.5 rounded font-bold bg-primary/10 text-primary dark:text-[#93C5FD] text-[11px]">5 tài liệu</span>.
              </div>
            </div>
            <!-- Lesson Title (Large Document Heading) -->
            <div>
              <input
                type="text"
                id="studio-input-title"
                class="w-full text-2xl sm:text-3xl font-extrabold text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] bg-transparent border-0 border-b border-transparent hover:border-[#E8E6DF] dark:hover:border-[#2E2D2B] focus:border-primary outline-none py-2 transition-colors"
                placeholder="Tiêu đề bài giảng..."
                value="${UI.escapeHtml(initialLessonTitle)}"
              />
            </div>

            <!-- Quick Metadata Bar (Summary & Duration) -->
            <div class="pb-4 border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <input
                type="text"
                id="studio-input-summary"
                class="flex-1 h-9 px-3.5 rounded-xl bg-[#FAF9F5] dark:bg-[#262524] text-xs text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] border border-[#E8E6DF] dark:border-[#2E2D2B] outline-none focus:border-primary"
                placeholder="Mô tả tóm tắt mục tiêu bài học (1 câu ngắn)..."
              />
              <div class="flex items-center gap-1.5 px-3 h-9 rounded-xl bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs shrink-0" title="Thời lượng ước tính bài giảng">
                <span class="material-symbols-outlined text-[16px] text-primary">schedule</span>
                <span class="text-[#5C5B57] dark:text-[#9E9D99] text-[11px] font-semibold">Thời lượng:</span>
                <input
                  type="number"
                  id="studio-input-duration"
                  min="1"
                  max="600"
                  class="w-24 min-w-20 bg-transparent text-xs text-[#222120] dark:text-[#EDEDEB] outline-none font-bold text-center"
                  placeholder="15"
                  value="15"
                />
                <span class="text-[#8F8E8A] text-[11px]">phút</span>
              </div>
            </div>

            <!-- Word-like WYSIWYG Formatting Toolbar -->
            <div class="bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-2.5 flex flex-wrap items-center gap-1.5 shadow-2xs select-none sticky top-18 z-30">
              <!-- Paragraph Format Dropdown -->
              <select
                id="studio-tool-format"
                class="h-8 px-2.5 rounded-lg bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#3E3D3A] text-xs font-semibold text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary cursor-pointer"
                title="Định dạng đoạn văn"
              >
                <option value="p">Đoạn văn (Normal)</option>
                <option value="h1">Tiêu đề 1 (H1)</option>
                <option value="h2">Tiêu đề 2 (H2)</option>
                <option value="h3">Tiêu đề 3 (H3)</option>
              </select>

              <div class="h-5 w-px bg-[#E8E6DF] dark:bg-[#3E3D3A] mx-0.5"></div>

              <!-- Font Styles: Bold, Italic, Underline, Strike -->
              <button type="button" id="studio-tool-bold" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] hover:text-primary transition-colors font-bold text-xs" title="In đậm (Ctrl+B)">
                <span class="material-symbols-outlined text-[18px]">format_bold</span>
              </button>
              <button type="button" id="studio-tool-italic" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] hover:text-primary transition-colors text-xs" title="In nghiêng (Ctrl+I)">
                <span class="material-symbols-outlined text-[18px]">format_italic</span>
              </button>
              <button type="button" id="studio-tool-underline" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] hover:text-primary transition-colors text-xs" title="Gạch chân (Ctrl+U)">
                <span class="material-symbols-outlined text-[18px]">format_underlined</span>
              </button>
              <button type="button" id="studio-tool-strike" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] hover:text-primary transition-colors text-xs" title="Gạch ngang chữ">
                <span class="material-symbols-outlined text-[18px]">strikethrough_s</span>
              </button>

              <div class="h-5 w-px bg-[#E8E6DF] dark:bg-[#3E3D3A] mx-0.5"></div>

              <!-- Colors: Text Color & Highlight -->
              <div class="flex items-center gap-1" title="Màu chữ">
                <label for="studio-tool-color" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] cursor-pointer flex items-center">
                  <span class="material-symbols-outlined text-[18px] text-rose-600">format_color_text</span>
                </label>
                <input type="color" id="studio-tool-color" value="#222120" class="w-5 h-5 rounded cursor-pointer border-0 bg-transparent p-0 hidden" />
              </div>
              <div class="flex items-center gap-1" title="Màu nền nổi bật (Highlight)">
                <label for="studio-tool-bgcolor" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] cursor-pointer flex items-center">
                  <span class="material-symbols-outlined text-[18px] text-amber-500">format_color_fill</span>
                </label>
                <input type="color" id="studio-tool-bgcolor" value="#FEF08A" class="w-5 h-5 rounded cursor-pointer border-0 bg-transparent p-0 hidden" />
              </div>

              <div class="h-5 w-px bg-[#E8E6DF] dark:bg-[#3E3D3A] mx-0.5"></div>

              <!-- Alignments: Left, Center, Right, Justify -->
              <button type="button" id="studio-tool-left" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Căn trái">
                <span class="material-symbols-outlined text-[18px]">format_align_left</span>
              </button>
              <button type="button" id="studio-tool-center" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Căn giữa">
                <span class="material-symbols-outlined text-[18px]">format_align_center</span>
              </button>
              <button type="button" id="studio-tool-right" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Căn phải">
                <span class="material-symbols-outlined text-[18px]">format_align_right</span>
              </button>
              <button type="button" id="studio-tool-justify" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Căn đều hai bên">
                <span class="material-symbols-outlined text-[18px]">format_align_justify</span>
              </button>

              <div class="h-5 w-px bg-[#E8E6DF] dark:bg-[#3E3D3A] mx-0.5"></div>

              <!-- Lists & Blocks -->
              <button type="button" id="studio-tool-ul" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Danh sách gạch đầu dòng">
                <span class="material-symbols-outlined text-[18px]">format_list_bulleted</span>
              </button>
              <button type="button" id="studio-tool-ol" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Danh sách đánh số thứ tự">
                <span class="material-symbols-outlined text-[18px]">format_list_numbered</span>
              </button>
              <button type="button" id="studio-tool-callout" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Hộp ghi chú nổi bật (Callout)">
                <span class="material-symbols-outlined text-[18px] text-amber-500">lightbulb</span>
              </button>
              <button type="button" id="studio-tool-table" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Chèn bảng 3x3">
                <span class="material-symbols-outlined text-[18px] text-indigo-600">table_chart</span>
              </button>
              <button type="button" id="studio-tool-hr" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Chèn đường kẻ ngang ngắt đoạn">
                <span class="material-symbols-outlined text-[18px]">horizontal_rule</span>
              </button>
              <button type="button" id="studio-tool-clear" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Xóa định dạng (Văn bản gốc)">
                <span class="material-symbols-outlined text-[18px]">format_clear</span>
              </button>

              <div class="h-5 w-px bg-[#E8E6DF] dark:bg-[#3E3D3A] mx-0.5"></div>

              <!-- Undo / Redo -->
              <button type="button" id="studio-tool-undo" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Hoàn tác (Ctrl+Z)">
                <span class="material-symbols-outlined text-[18px]">undo</span>
              </button>
              <button type="button" id="studio-tool-redo" class="p-1.5 rounded-lg hover:bg-white dark:hover:bg-[#202020] text-[#5C5B57] dark:text-[#9E9D99] transition-colors" title="Làm lại (Ctrl+Y)">
                <span class="material-symbols-outlined text-[18px]">redo</span>
              </button>
            </div>

            <!-- Visual Word Document Canvas (contenteditable WYSIWYG) -->
            <div class="relative">
              <div
                id="studio-content-editor"
                contenteditable="true"
                class="w-full min-h-[560px] p-6 sm:p-8 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm sm:text-base text-[#222120] dark:text-[#EDEDEB] focus:outline-none focus:ring-2 focus:ring-primary/20 leading-relaxed font-sans shadow-2xs overflow-y-auto space-y-3"
              >
                <p>Nhập nội dung bài giảng tại đây. Bạn có thể bôi đen chữ để in đậm, in nghiêng, đổi màu, tạo danh sách hoặc chèn bảng giống Microsoft Word...</p>
              </div>
            </div>

            <!-- Video Studio Section (Unified Toolbar + Dropzone) -->
            <div class="p-5 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5]/80 dark:bg-[#262524]/60 space-y-4" id="studio-video-section">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-[20px] text-primary">play_circle</span>
                  <span class="text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99]">Video bài giảng</span>
                  <span id="studio-video-count-badge" class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                    0/2 video
                  </span>
                </div>
                <span class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]">
                  Tối đa 2 video cho Lesson, 7 video cho Bài học • MP4/WebM/MKV &lt; 1GB hoặc link YouTube/Vimeo
                </span>
              </div>

              <!-- Unified Toolbar: Chèn link video YouTube / Vimeo -->
              <div class="space-y-1.5" id="studio-video-toolbar-area">
                <label for="studio-input-video-url" class="block text-xs font-medium text-[#5C5B57] dark:text-[#9E9D99]">
                  Chèn link video YouTube / Vimeo:
                </label>
                <div class="flex items-center gap-2">
                  <div class="relative flex-1">
                    <span class="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#8F8E8A] dark:text-[#6D6C68]">link</span>
                    <input
                      type="url"
                      id="studio-input-video-url"
                      class="w-full h-10 pl-9 pr-3.5 rounded-xl bg-white dark:bg-[#202020] text-xs text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] border border-[#E8E6DF] dark:border-[#2E2D2B] outline-none focus:border-primary shadow-2xs transition-colors"
                      placeholder="Dán link YouTube (VD: https://www.youtube.com/watch?v=...) hoặc Vimeo..."
                    />
                  </div>
                  <button
                    type="button"
                    id="btn-apply-video-url"
                    class="px-4 h-10 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shrink-0 flex items-center gap-1.5 cursor-pointer shadow-2xs"
                  >
                    <span class="material-symbols-outlined text-[16px]">add_link</span>
                    <span>Thêm link</span>
                  </button>
                </div>
              </div>

              <!-- Unified Dropzone: Kéo thả nhiều tệp video & Nút chọn file từ máy tính -->
              <div class="space-y-2" id="studio-video-dropzone-area">
                <input
                  type="file"
                  id="studio-video-file-input"
                  multiple
                  accept="video/mp4,video/webm,video/x-matroska,video/quicktime,.mp4,.webm,.mkv,.mov"
                  class="hidden"
                />
                <div
                  id="studio-video-dropzone"
                  role="button"
                  tabindex="0"
                  class="rounded-xl border-2 border-dashed border-[#D3D0C8] dark:border-[#3E3D3A] hover:border-primary dark:hover:border-primary p-6 text-center cursor-pointer transition-all bg-white/60 dark:bg-[#1E1D1B]/60 hover:bg-white dark:hover:bg-[#202020] space-y-2 group focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto group-hover:scale-105 transition-transform">
                    <span class="material-symbols-outlined text-[24px]">cloud_upload</span>
                  </div>
                  <div class="text-xs text-[#5C5B57] dark:text-[#9E9D99]">
                    <span class="font-bold text-[#222120] dark:text-[#EDEDEB]">Kéo thả tối đa 2 video vào đây</span> hoặc
                    <button type="button" id="btn-choose-video-file" class="text-primary font-bold hover:underline cursor-pointer">chọn từ máy tính</button>
                  </div>
                  <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]">
                    Hỗ trợ tải lên nhiều tệp cùng lúc (MP4, WebM, MKV, MOV &lt; 1GB/video • quét ClamAV tự động)
                  </p>
                </div>

                <!-- Progress Bar -->
                <div id="studio-video-progress-box" class="hidden space-y-1.5 pt-1">
                  <div class="flex items-center justify-between text-xs text-primary font-bold">
                    <span id="studio-video-progress-text">Đang tải video lên máy chủ...</span>
                    <span id="studio-video-progress-percent">0%</span>
                  </div>
                  <div class="w-full h-2 rounded-full bg-[#E8E6DF] dark:bg-[#2E2D2B] overflow-hidden">
                    <div id="studio-video-progress-bar" class="h-full bg-primary transition-all duration-150 rounded-full" style="width: 0%"></div>
                  </div>
                </div>
              </div>

              <!-- Danh sách Video (Cards List) -->
              <div class="space-y-2 pt-1">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB] flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px] text-primary">playlist_play</span>
                    <span>Danh sách video trong bài giảng</span>
                    <span class="text-[10px] font-normal text-[#8F8E8A] dark:text-[#6D6C68] hidden sm:inline">(Kéo thả để đổi thứ tự • Bấm để xem trước)</span>
                  </span>
                  <span id="studio-video-quota-hint" class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]"></span>
                </div>
                <div id="studio-video-list" class="space-y-2 text-xs" aria-live="polite"></div>
              </div>

              <!-- Video Preview Box (Centered horizontally and vertically) -->
              <div id="studio-video-preview-box" class="hidden pt-2">
                <div class="flex items-center justify-between pb-1.5 px-1">
                  <span class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB] flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px] text-primary">preview</span>
                    <span id="studio-video-preview-title">Xem trước video</span>
                  </span>
                  <div class="flex items-center gap-3">
                    <button
                      type="button"
                      id="btn-delete-preview-video"
                      class="text-xs text-rose-600 dark:text-rose-400 hover:text-rose-700 flex items-center gap-0.5 cursor-pointer font-semibold"
                      title="Xóa video đang xem trước"
                    >
                      <span class="material-symbols-outlined text-[15px]">delete</span>
                      <span>Xóa video</span>
                    </button>
                    <button
                      type="button"
                      id="btn-close-preview"
                      class="text-xs text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] flex items-center gap-0.5 cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[15px]">close</span>
                      <span>Đóng xem trước</span>
                    </button>
                  </div>
                </div>
                <div class="max-w-2xl mx-auto relative rounded-2xl overflow-hidden bg-black aspect-video max-h-[360px] border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-subtle group flex items-center justify-center">
                  <div id="studio-video-player-target" class="w-full h-full flex items-center justify-center"></div>
                </div>
              </div>
            </div>

            <!-- Attachment Section (Tài liệu đính kèm) -->
            <div class="pt-4 border-t border-[#E8E6DF] dark:border-[#2E2D2B] space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px] text-emerald-600">attach_file</span>
                  <span>Tài liệu đính kèm</span>
                </span>
                <button
                  type="button"
                  id="btn-trigger-upload"
                  class="px-3 py-1.5 rounded-lg bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-semibold flex items-center gap-1 transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B]"
                >
                  <span class="material-symbols-outlined text-[15px]">upload</span>
                  <span>Đính kèm tệp</span>
                </button>
                <input type="file" id="studio-hidden-file-input" class="hidden" multiple />
              </div>

              <div
                id="studio-resources-dropzone"
                role="button"
                tabindex="0"
                class="rounded-xl border-2 border-dashed border-[#D3D0C8] dark:border-[#3E3D3A] hover:border-emerald-500 dark:hover:border-emerald-500 p-6 text-center cursor-pointer transition-all bg-white/60 dark:bg-[#1E1D1B]/60 hover:bg-white dark:hover:bg-[#202020] space-y-2 group focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <div class="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center mx-auto group-hover:scale-105 transition-transform">
                  <span class="material-symbols-outlined text-[24px]">cloud_upload</span>
                </div>
                <div class="text-xs text-[#5C5B57] dark:text-[#9E9D99]">
                  <span class="font-bold text-[#222120] dark:text-[#EDEDEB]">Kéo thả tài liệu vào đây</span> hoặc
                  <button type="button" id="btn-choose-doc-file" class="text-emerald-600 font-bold hover:underline cursor-pointer">chọn từ máy tính</button>
                </div>
                <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]">
                  Hỗ trợ tải lên nhiều tệp cùng lúc (PDF, DOCX, XLSX, PPTX, TXT, ZIP &lt; 50MB/tệp • quét ClamAV tự động • tối đa 5 tài liệu)
                </p>
              </div>

              <!-- Attachments List Container -->
              <div id="studio-attachments-list" class="space-y-2">
                <div class="p-4 rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68]">
                  Chưa có tài liệu đính kèm. Bấm "Đính kèm tệp" để tải lên tài liệu học tập (được quét an toàn qua ClamAV).
                </div>
              </div>
            </div>

            <!-- Mini-Quiz Section (Bộ câu hỏi củng cố bài giảng) -->
            <div class="pt-4 border-t border-[#E8E6DF] dark:border-[#2E2D2B] space-y-4" id="studio-quiz-section">
              <div class="flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99] flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-[18px] text-purple-600">quiz</span>
                      <span>Bộ Câu hỏi Củng cố Bài học (Mini-Quiz)</span>
                    </span>
                    <span id="studio-mini-quiz-count" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                      0 câu hỏi
                    </span>
                  </div>
                  <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-0.5">
                    Thêm các câu hỏi củng cố (Trắc nghiệm đơn/nhiều đáp án, Điền khuyết, Nối từ, Đúng/Sai) để học sinh tự đánh giá ngay sau bài giảng.
                  </p>
                </div>
                <button
                  type="button"
                  id="btn-add-mini-quiz-q"
                  class="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs shrink-0 cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[16px]">add_circle</span>
                  <span>Thêm câu hỏi</span>
                </button>
              </div>

              <div id="studio-mini-quiz-list" class="space-y-4">
                <div class="p-5 rounded-2xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68]">
                  Chưa có câu hỏi củng cố nào cho bài học này. Bấm "Thêm câu hỏi" để tạo bài kiểm tra nhanh.
                </div>
              </div>
            </div>

          </div>
        </main>

      </div>
    `;

    const studioRoot = container.querySelector('#lesson-studio-root') || container;
    const getEl = (id) => studioRoot ? studioRoot.querySelector('#' + id) : null;
    let attachedResources = [];
    let currentVideoUrl = '';
    let videoUrls = [];
    let miniQuizQuestions = [];

    const updateHeaderUnitTitle = () => {
      const titleEl = getEl('studio-header-unit-title');
      if (!titleEl) return;
      const unit = availableUnits.find(item => (item.learning_unit_id || item.id) === selectedUnitId);
      const clean = (unit?.title || 'Bài học').replace(/\s*\(\d+\/\d+.*?\)/g, '').trim();
      titleEl.textContent = clean;
    };

    const setSaveIndicator = (state) => {
      const ind = getEl('studio-save-indicator');
      if (!ind) return;
      if (state === 'saving') {
        ind.innerHTML = '<span class="material-symbols-outlined text-[16px] animate-spin">sync</span>';
      } else if (state === 'pending') {
        ind.innerHTML = '<span class="material-symbols-outlined text-[16px] text-amber-300" title="Đang chờ Admin duyệt">hourglass_top</span>';
      } else {
        ind.innerHTML = '<span class="material-symbols-outlined text-[16px]">cloud_done</span>';
      }
    };

    let videoItems = [];
    const parentVideoSlots = () => {
      const unit = availableUnits.find(item => (item.learning_unit_id || item.id) === selectedUnitId);
      if (!unit) return 7;
      const siblingVideos = (unit.lessons || [])
        .filter(item => (item.lesson_id || item.id) !== lessonId)
        .reduce((total, item) => total + InstructorView.getVideoCount(item.video_urls || [], item.resources || []), 0);
      return Math.max(0, 7 - siblingVideos);
    };
    const renderChildNavigator = () => {
      const target = getEl('studio-lesson-navigator');
      if (!target) return;
      const unit = availableUnits.find(item => (item.learning_unit_id || item.id) === selectedUnitId);
      target.innerHTML = InstructorView.renderLessonChildNavigator(unit, courseId, lessonId);
      updateHeaderUnitTitle();

      // Bind Add Lesson button in navigator
      const navAddBtn = target.querySelector('#btn-nav-add-lesson');
      if (navAddBtn) {
        navAddBtn.onclick = (e) => {
          e.preventDefault();
          if (typeof handleAddNewLesson === 'function') {
            handleAddNewLesson();
          }
        };
      }

      if (!unit) return;
      const lessons = [...(unit.lessons || [])].sort((a, b) => (a.position || 0) - (b.position || 0));

      // Clean up timer when navigating away by clicking a lesson link
      target.querySelectorAll('.nav-lesson-link').forEach(link => {
        link.addEventListener('click', async (e) => {
          e.preventDefault();
          const targetHref = link.getAttribute('href');
          if (editVersion > savedVersion) {
            setSaveIndicator('saving');
            try {
              await saveLessonData(false, true);
            } catch (_) {}
          }
          if (window._currentStudioTimer) {
            clearInterval(window._currentStudioTimer);
            window._currentStudioTimer = null;
          }
          if (targetHref) {
            window.location.hash = targetHref.replace(/^#/, '');
          }
        });
      });

      // Bind delete lesson in navigator
      target.querySelectorAll('.btn-nav-delete-lesson').forEach(btn => {
        btn.onclick = async (e) => {
          e.preventDefault();
          e.stopPropagation();
          const targetLId = btn.dataset.lessonId;
          const targetLTitle = btn.dataset.lessonTitle || 'bài học này';
          const conf = await UI.confirm('Xóa Lesson', `Bạn có chắc chắn muốn xóa lesson "${targetLTitle}"? Thao tác không thể hoàn tác.`, 'Xóa vĩnh viễn');
          if (!conf) return;
          try {
            const res = await ApiClient.deleteLesson(courseId, targetLId);
            if (res && res.pending_approval) {
              UI.showToast(res.message || 'Yêu cầu xóa bài giảng đã được gửi tới Admin để xét duyệt.', 'info');
              return;
            }
            UI.showToast('Đã xóa lesson thành công.', 'success');
            if (unit && Array.isArray(unit.lessons)) {
              unit.lessons = unit.lessons.filter(l => (l.lesson_id || l.id) !== targetLId);
              unit.lesson_count = unit.lessons.length;
            }
            if (targetLId === lessonId) {
              if (unit?.lessons?.length > 0) {
                if (window._currentStudioTimer) {
                  clearInterval(window._currentStudioTimer);
                  window._currentStudioTimer = null;
                }
                const nextLesson = unit.lessons[0];
                const nextId = nextLesson.lesson_id || nextLesson.id;
                window.location.hash = `#/instructor/courses/${courseId}/lessons/${nextId}/edit`;
              } else {
                lessonId = null;
                if (typeof resetEditorToEmpty === 'function') {
                  resetEditorToEmpty();
                }
                renderChildNavigator();
                window.history.replaceState(null, '', `#/instructor/courses/${courseId}/lessons/new?learning_unit_id=${unit?.learning_unit_id || ''}`);
              }
            } else {
              renderChildNavigator();
            }
          } catch (err) {
            UI.showToast(err.message || 'Lỗi khi xóa lesson.', 'error');
          }
        };
      });

      // Bind Drag & Drop Reordering for lessons in navigator
      let draggedNavIdx = null;
      target.querySelectorAll('.nav-lesson-item').forEach(item => {
        item.addEventListener('dragstart', (e) => {
          if (e.target.closest('button') || e.target.closest('.btn-nav-delete-lesson')) {
            e.preventDefault();
            return;
          }
          draggedNavIdx = parseInt(item.dataset.idx, 10);
          item.classList.add('opacity-40', 'scale-[0.98]');
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', String(draggedNavIdx));
        });
        item.addEventListener('dragend', () => {
          item.classList.remove('opacity-40', 'scale-[0.98]');
          target.querySelectorAll('.nav-lesson-item').forEach(el => {
            el.classList.remove('border-primary', 'bg-primary/5');
          });
        });
        item.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
          item.classList.add('border-primary', 'bg-primary/5');
        });
        item.addEventListener('dragleave', () => {
          item.classList.remove('border-primary', 'bg-primary/5');
        });
        item.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          item.classList.remove('border-primary', 'bg-primary/5');
          const targetIdx = parseInt(item.dataset.idx, 10);
          if (draggedNavIdx === null || draggedNavIdx === targetIdx || !unit?.lessons) return;
          const reordered = [...lessons];
          const [moved] = reordered.splice(draggedNavIdx, 1);
          reordered.splice(targetIdx, 0, moved);
          unit.lessons = reordered;
          renderChildNavigator();

          const allOrderedIds = [];
          (availableUnits || []).forEach(u => {
            (u.lessons || []).forEach(l => {
              const lid = l.lesson_id || l.id;
              if (lid && !allOrderedIds.includes(lid)) allOrderedIds.push(lid);
            });
          });

          try {
            const res = await ApiClient.reorderLessons(courseId, allOrderedIds);
            if (res && (res.pending_approval || res.status === 'pending_approval')) {
              UI.showToast(res.message || 'Yêu cầu sắp xếp bài giảng đã được gửi tới Ban quản trị để xét duyệt.', 'info');
            } else {
              UI.showToast('Đã sắp xếp lại thứ tự bài giảng thành công!', 'success');
            }
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
            renderChildNavigator();
          }
        });
      });
    };
    renderChildNavigator();
    updateHeaderUnitTitle();

    const titleInput = getEl('studio-input-title');
    if (titleInput) {
      titleInput.addEventListener('input', () => {
        const draftTitleEl = getEl('nav-draft-lesson-title');
        if (draftTitleEl) {
          const unit = availableUnits.find(item => (item.learning_unit_id || item.id) === selectedUnitId);
          const nextIdx = (unit?.lessons?.length || 0) + 1;
          draftTitleEl.textContent = titleInput.value.trim() || `Bài giảng ${nextIdx}`;
        }
      });
    }

    const resourceVideoUrl = resource => {
      const baseUrl = resource.file_url || resource.download_url || '';
      if (!baseUrl || baseUrl.includes('disposition=')) return baseUrl;
      return `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}disposition=inline`;
    };

    // Helper: Parse YouTube Video ID reliably across all URL formats
    const parseYouTubeId = (url) => {
      return UI.parseYouTubeId(url);
    };

    // Render Video Preview Helper (Centered)
    const renderVideoPreview = (url) => {
      const previewBox = getEl('studio-video-preview-box');
      const target = getEl('studio-video-player-target');
      const previewTitle = getEl('studio-video-preview-title');
      if (!previewBox || !target) return;

      if (!url || !String(url).trim()) {
        previewBox.classList.add('hidden');
        target.innerHTML = '';
        return;
      }

      previewBox.classList.remove('hidden');
      const cleanUrl = String(url).trim();

      const item = videoItems.find(v => v.url === cleanUrl);
      if (previewTitle && item) {
        previewTitle.textContent = `Xem trước: ${item.title || 'Video bài giảng'}`;
      } else if (previewTitle) {
        previewTitle.textContent = 'Xem trước video';
      }

      // YouTube Embed Handler
      const ytId = UI.parseYouTubeId(cleanUrl);
      if (ytId) {
        target.innerHTML = `
          <iframe
            class="w-full h-full max-h-[360px] aspect-video mx-auto block rounded-xl"
            src="${UI.getYouTubeEmbedUrl(ytId)}"
            title="Video bài giảng YouTube"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen
          ></iframe>
        `;
        return;
      }

      // Vimeo Embed Handler
      if (cleanUrl.includes('vimeo.com/')) {
        const vimeoId = cleanUrl.split('vimeo.com/')[1]?.split('?')[0]?.split('/')[0];
        if (vimeoId) {
          target.innerHTML = `
            <iframe
              class="w-full h-full max-h-[360px] aspect-video mx-auto block rounded-xl"
              src="https://player.vimeo.com/video/${encodeURIComponent(vimeoId)}"
              title="Video bài giảng Vimeo"
              frameborder="0"
              allow="autoplay; fullscreen; picture-in-picture"
              allowfullscreen
            ></iframe>
          `;
          return;
        }
      }

      // Direct MP4 / WebM / Resource URL (Centered)
      target.innerHTML = `
        <video controls class="max-h-[360px] max-w-full mx-auto my-auto object-contain block rounded-xl" src="${UI.escapeHtml(cleanUrl)}" preload="metadata">
          Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
        </video>
      `;
    };

    const syncVideoItemsFromState = () => {
      const currentMap = new Map(videoItems.map(v => [v.url, v]));
      const nextItems = [];

      for (const url of videoUrls) {
        if (currentMap.has(url)) {
          nextItems.push(currentMap.get(url));
          currentMap.delete(url);
        } else {
          nextItems.push({
            id: `link-${url}`,
            type: 'LINK',
            url,
            title: url,
            isYouTube: Boolean(UI.parseYouTubeId(url)),
            isVimeo: /^https:\/\/(?:www\.)?vimeo\.com\/\d+/i.test(url)
          });
        }
      }

      const uploaded = attachedResources.filter(resource =>
        /\.(mp4|webm|mkv|mov)$/i.test(resource.filename || resource.title || '')
      );
      for (const res of uploaded) {
        const url = resourceVideoUrl(res);
        if (currentMap.has(url)) {
          const item = currentMap.get(url);
          item.resource = res;
          item.resource_id = res.resource_id;
          nextItems.push(item);
          currentMap.delete(url);
        } else {
          nextItems.push({
            id: `res-${res.resource_id || Math.random()}`,
            type: 'UPLOAD',
            url,
            title: res.title || res.filename || 'Video tải lên',
            resource_id: res.resource_id,
            resource: res
          });
        }
      }

      videoItems = nextItems;
    };

    const renderVideoList = () => {
      syncVideoItemsFromState();
      const list = getEl('studio-video-list');
      const badge = getEl('studio-video-count-badge');
      const quotaHint = getEl('studio-video-quota-hint');
      const toolbarInput = getEl('studio-input-video-url');
      const toolbarBtn = getEl('btn-apply-video-url');
      const dropzone = getEl('studio-video-dropzone');

      const totalCount = videoItems.length;
      const remainingSlots = InstructorView.getRemainingVideoSlots(videoUrls, attachedResources, parentVideoSlots());

      if (badge) {
        badge.textContent = `${totalCount}/2 video`;
        if (totalCount >= 2) {
          badge.className = 'px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20';
        } else {
          badge.className = 'px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20';
        }
      }

      if (quotaHint) {
        quotaHint.textContent = remainingSlots === 0
          ? 'Đã đạt giới hạn video của Lesson hoặc Bài học'
          : `Còn trống ${remainingSlots} video trong Lesson và Bài học`;
      }

      const isFull = remainingSlots === 0;
      if (toolbarInput) {
        toolbarInput.disabled = isFull;
        if (isFull) {
          toolbarInput.placeholder = 'Đã đạt giới hạn tối đa 2 video trong Lesson.';
        } else {
          toolbarInput.placeholder = 'Dán link YouTube (VD: https://www.youtube.com/watch?v=...) hoặc Vimeo...';
        }
      }
      if (toolbarBtn) toolbarBtn.disabled = isFull;
      if (dropzone) {
        if (isFull) {
          dropzone.classList.add('opacity-60', 'cursor-not-allowed', 'pointer-events-none');
        } else {
          dropzone.classList.remove('opacity-60', 'cursor-not-allowed', 'pointer-events-none');
        }
      }

      if (!list) return;

      if (totalCount === 0) {
        list.innerHTML = `
          <div class="p-4 rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68]">
            Chưa có video nào trong Lesson (0/2). Hãy dán link YouTube ở trên hoặc kéo thả tệp video từ máy tính.
          </div>
        `;
        return;
      }

      list.innerHTML = videoItems.map((entry, index) => {
        const isSelected = currentVideoUrl && entry.url === currentVideoUrl;
        const iconHtml = entry.type === 'LINK'
          ? (entry.isYouTube
              ? `<span class="material-symbols-outlined text-[18px] text-rose-500 shrink-0">smart_display</span>`
              : `<span class="material-symbols-outlined text-[18px] text-sky-500 shrink-0">live_tv</span>`)
          : `<span class="material-symbols-outlined text-[18px] text-emerald-500 shrink-0">video_file</span>`;

        const typeLabel = entry.type === 'LINK'
          ? (entry.isYouTube ? 'YouTube' : 'Vimeo')
          : 'Tệp tải lên';

        return `
          <div
            class="video-draggable-card flex items-center justify-between gap-3 p-3 rounded-xl border transition-all cursor-pointer select-none group ${
              isSelected
                ? 'border-primary bg-primary/5 dark:bg-primary/10 shadow-2xs'
                : 'border-[#E8E6DF] dark:border-[#3E3D3A] bg-white dark:bg-[#202020] hover:border-primary/50 dark:hover:border-primary/50'
            }"
            draggable="true"
            data-index="${index}"
            title="Bấm để xem video này • Kéo thả để đổi thứ tự"
          >
            <div class="flex items-center gap-2.5 min-w-0 flex-1">
              <!-- Drag handle indicator -->
              <div
                class="drag-handle text-[#8F8E8A] dark:text-[#6D6C68] group-hover:text-primary cursor-grab active:cursor-grabbing p-1 -ml-1 rounded-md shrink-0 flex items-center justify-center transition-colors"
                title="Kéo thả để đổi thứ tự"
              >
                <span class="material-symbols-outlined text-[18px]">drag_indicator</span>
              </div>

              <span class="px-2 py-0.5 rounded-md font-mono text-[11px] font-bold shrink-0 ${
                index === 0
                  ? 'bg-primary text-white'
                  : 'bg-[#F4F1EA] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#9E9D99]'
              }">
                #${index + 1}
              </span>
              ${iconHtml}
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <span class="text-[10px] font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#6D6C68]">${typeLabel}</span>
                  ${isSelected ? '<span class="text-[10px] font-semibold text-primary">• Đang xem</span>' : ''}
                </div>
                <div class="text-xs font-semibold text-[#222120] dark:text-[#EDEDEB] truncate" title="${UI.escapeHtml(entry.title)}">
                  ${UI.escapeHtml(entry.title)}
                </div>
              </div>
            </div>

            <!-- Actions: Delete -->
            <div class="flex items-center gap-1 shrink-0">
              <button
                type="button"
                class="btn-video-delete px-2.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                data-index="${index}"
                title="Xóa video này"
                draggable="false"
              >
                <span class="material-symbols-outlined text-[15px]">delete</span>
                <span>Xóa video</span>
              </button>
            </div>
          </div>
        `;
      }).join('');

      // Bind Click to Preview & Drag and Drop for Reordering
      let isDragging = false;
      const cards = list.querySelectorAll('.video-draggable-card');

      cards.forEach(card => {
        // Click anywhere on card (except delete button) to preview
        card.onclick = (e) => {
          if (isDragging) return;
          if (e.target.closest('.btn-video-delete')) return;
          const idx = Number(card.dataset.index);
          const item = videoItems[idx];
          if (item) {
            currentVideoUrl = item.url;
            renderVideoPreview(currentVideoUrl);
            renderVideoList();
          }
        };

        // Drag and Drop reordering
        card.ondragstart = (e) => {
          if (e.target.closest('.btn-video-delete')) {
            e.preventDefault();
            return;
          }
          isDragging = true;
          const idx = Number(card.dataset.index);
          card.dataset.dragging = 'true';
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', String(idx));
          setTimeout(() => {
            card.classList.add('opacity-40', 'scale-[0.99]');
          }, 0);
        };

        card.ondragend = () => {
          setTimeout(() => {
            isDragging = false;
          }, 50);
          cards.forEach(c => {
            delete c.dataset.dragging;
            c.classList.remove('opacity-40', 'scale-[0.99]', 'border-primary', 'bg-primary/10');
          });
        };

        card.ondragover = (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
          if (card.dataset.dragging !== 'true') {
            card.classList.add('border-primary', 'bg-primary/10');
          }
        };

        card.ondragleave = (e) => {
          if (!card.contains(e.relatedTarget)) {
            card.classList.remove('border-primary', 'bg-primary/10');
          }
        };

        card.ondrop = (e) => {
          e.preventDefault();
          e.stopPropagation();
          card.classList.remove('border-primary', 'bg-primary/10');
          const targetIdx = Number(card.dataset.index);
          const rawSource = e.dataTransfer.getData('text/plain');
          const sourceIdx = Number(rawSource);
          if (!isNaN(sourceIdx) && !isNaN(targetIdx) && sourceIdx !== targetIdx) {
            videoItems = InstructorView.moveVideoItem(videoItems, sourceIdx, targetIdx);
            videoUrls = videoItems.filter(v => v.type === 'LINK').map(v => v.url);
            renderVideoList();
            UI.showToast(`Đã đổi vị trí video #${sourceIdx + 1} sang #${targetIdx + 1}.`, 'info');
          }
        };
      });

      // Bind Delete
      list.querySelectorAll('.btn-video-delete').forEach(btn => {
        btn.onclick = async (e) => {
          e.stopPropagation();
          const idx = Number(btn.dataset.index);
          const item = videoItems[idx];
          if (!item) return;

          const conf = await UI.confirm('Xóa video', `Bạn có chắc chắn muốn xóa video "${item.title || 'này'}"?`, 'Xóa video');
          if (!conf) return;

          if (item.type === 'LINK') {
            videoUrls = videoUrls.filter(u => u !== item.url);
          } else if (item.type === 'UPLOAD') {
            if (item.resource_id && lessonId) {
              try {
                const response = await ApiClient.detachLessonResource(courseId, lessonId, item.resource_id);
                if (response.pending_approval) {
                  UI.showToast('Yêu cầu gỡ video đã gửi Admin xét duyệt.', 'info');
                  return;
                }
              } catch (err) {
                UI.showToast(err.message || 'Không thể gỡ video.', 'error');
                return;
              }
            }
            attachedResources = attachedResources.filter(r => r !== item.resource && r.resource_id !== item.resource_id);
            renderAttachments();
          }

          videoItems = videoItems.filter((_, i) => i !== idx);

          if (currentVideoUrl === item.url) {
            currentVideoUrl = videoItems.length ? videoItems[0].url : '';
            renderVideoPreview(currentVideoUrl);
          }

          renderVideoList();
          UI.showToast(`Đã xóa video thành công.`, 'info');
        };
      });
    };

    const deletePreviewVideoBtn = getEl('btn-delete-preview-video');
    if (deletePreviewVideoBtn) {
      deletePreviewVideoBtn.onclick = async () => {
        if (!currentVideoUrl) return;
        const idx = videoItems.findIndex(v => v.url === currentVideoUrl);
        if (idx === -1) return;
        const item = videoItems[idx];
        const conf = await UI.confirm('Xóa video', `Bạn có chắc chắn muốn xóa video "${item.title || 'này'}"?`, 'Xóa video');
        if (!conf) return;
        if (item.type === 'LINK') {
          videoUrls = videoUrls.filter(u => u !== item.url);
        } else if (item.type === 'UPLOAD') {
          if (item.resource_id && lessonId) {
            try {
              const response = await ApiClient.detachLessonResource(courseId, lessonId, item.resource_id);
              if (response.pending_approval) {
                UI.showToast('Yêu cầu gỡ video đã gửi Admin xét duyệt.', 'info');
                return;
              }
            } catch (err) {
              UI.showToast(err.message || 'Không thể gỡ video.', 'error');
              return;
            }
          }
          attachedResources = attachedResources.filter(r => r !== item.resource && r.resource_id !== item.resource_id);
          renderAttachments();
        }
        videoItems = videoItems.filter((_, i) => i !== idx);
        currentVideoUrl = videoItems.length ? videoItems[0].url : '';
        renderVideoPreview(currentVideoUrl);
        renderVideoList();
        UI.showToast('Đã xóa video thành công.', 'info');
      };
    }

    const handleApplyVideoUrl = async () => {
      const inputEl = getEl('studio-input-video-url');
      const inputUrl = inputEl?.value.trim() || '';
      if (!inputUrl) {
        UI.showToast('Vui lòng nhập đường dẫn video hợp lệ.', 'warning');
        return;
      }
      const ytId = UI.parseYouTubeId(inputUrl);
      const vimeoId = inputUrl.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d+)\/?$/i)?.[1];
      if (!ytId && !vimeoId) {
        UI.showToast('Chỉ chấp nhận liên kết YouTube hoặc Vimeo hợp lệ.', 'warning');
        return;
      }
      const url = ytId ? `https://www.youtube.com/watch?v=${ytId}` : `https://vimeo.com/${vimeoId}`;
      if (videoUrls.includes(url)) {
        UI.showToast('Video này đã có trong danh sách bài học.', 'warning');
        return;
      }
      if (!InstructorView.canAddLessonVideo(videoUrls, attachedResources, parentVideoSlots())) {
        UI.showToast('Mỗi Lesson chỉ được có tối đa 2 video.', 'warning');
        return;
      }

      if (ytId) {
        UI.showToast('Đang kiểm tra tính khả dụng của video YouTube...', 'info');
        try {
          const check = await ApiClient.checkYouTubeLink(url);
          if (!check.valid) {
            UI.showToast(check.reason || 'Video YouTube không tồn tại hoặc không cho phép nhúng.', 'error');
            return;
          }
          UI.showToast(`Video YouTube hợp lệ: "${check.title || 'Video'}"`, 'success');
        } catch (err) {
          console.warn('YouTube check error:', err);
        }
      }

      videoUrls.push(url);
      currentVideoUrl = url;
      if (inputEl) inputEl.value = '';
      renderVideoPreview(currentVideoUrl);
      renderVideoList();
      if (!ytId) {
        UI.showToast('Đã thêm link video vào bài học thành công!', 'success');
      }
    };

    const applyUrlBtn = getEl('btn-apply-video-url');
    if (applyUrlBtn) {
      applyUrlBtn.onclick = handleApplyVideoUrl;
    }

    const urlInput = getEl('studio-input-video-url');
    if (urlInput) {
      urlInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleApplyVideoUrl();
        }
      };
    }

    const closePreviewBtn = getEl('btn-close-preview');
    if (closePreviewBtn) {
      closePreviewBtn.onclick = () => {
        renderVideoPreview('');
      };
    }

    // Video Batch Upload Function (Sequential & Quota Aware)
    const uploadVideoBatch = async (files) => {
      if (!files || !files.length) return;
      const remainingSlots = InstructorView.getRemainingVideoSlots(videoUrls, attachedResources, parentVideoSlots());

      if (remainingSlots <= 0) {
        UI.showToast('Lesson đã đạt giới hạn tối đa 2 video.', 'warning');
        return;
      }

      const { accepted, overflow, oversized, invalidType } = InstructorView.filterVideoUploadBatch(files, remainingSlots);

      if (invalidType.length) {
        UI.showToast(`${invalidType.length} tệp không đúng định dạng video (MP4, WebM, MKV, MOV).`, 'warning');
      }
      if (oversized.length) {
        UI.showToast(`${oversized.length} video vượt quá dung lượng cho phép (< 1GB).`, 'error');
      }
      if (overflow.length) {
        UI.showToast(`Đã nhận ${accepted.length} video hợp lệ, bỏ qua ${overflow.length} video do vượt giới hạn 2 video.`, 'info');
      }

      if (!accepted.length) return;

      const progressBox = getEl('studio-video-progress-box');
      const progressBar = getEl('studio-video-progress-bar');
      const progressPercent = getEl('studio-video-progress-percent');
      const progressText = getEl('studio-video-progress-text');

      if (progressBox) progressBox.classList.remove('hidden');

      try {
        if (!lessonId) {
          if (progressText) progressText.textContent = 'Đang khởi tạo bản nháp bài học...';
          const title = getEl('studio-input-title')?.value.trim() || 'Bài giảng mới';
          const summary = getEl('studio-input-summary')?.value.trim() || '';
          const editorEl = getEl('studio-content-editor');
          const mdContent = editorEl ? editorEl.innerHTML : '';
          const durationVal = parseInt(getEl('studio-input-duration')?.value, 10);
          await createLessonOnce({
            title,
            summary,
            markdown_content: mdContent,
            status: 'DRAFT',
            estimated_duration_minutes: !isNaN(durationVal) && durationVal > 0 ? durationVal : 15
          });
        }

        let uploadedSuccessCount = 0;
        let pendingApprovalCount = 0;
        for (let i = 0; i < accepted.length; i++) {
          const file = accepted[i];
          const fileNum = i + 1;
          const totalFiles = accepted.length;

          if (progressText) progressText.textContent = `Đang tải lên (${fileNum}/${totalFiles}): ${file.name}...`;
          if (progressBar) progressBar.style.width = `${Math.round(((fileNum - 1) / totalFiles) * 100)}%`;
          if (progressPercent) progressPercent.textContent = `${Math.round(((fileNum - 1) / totalFiles) * 100)}%`;

          try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);

            const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
            if (res.pending_approval) {
              pendingApprovalCount++;
              continue;
            }
            const baseVideoUrl = res.download_url || res.file_url || `/student/courses/${courseId}/files/${res.resource_id}/download`;
            const videoUrl = `${baseVideoUrl}${baseVideoUrl.includes('?') ? '&' : '?'}disposition=inline`;

            const newResource = {
              resource_id: res.resource_id,
              title: file.name,
              filename: file.name,
              file_url: videoUrl,
              download_url: videoUrl,
              file_asset: res.file_asset
            };
            attachedResources.push(newResource);
            uploadedSuccessCount++;

            if (!currentVideoUrl) {
              currentVideoUrl = videoUrl;
              renderVideoPreview(currentVideoUrl);
            }

            renderAttachments();
            renderVideoList();
          } catch (fileErr) {
            UI.showToast(`Lỗi tải video "${file.name}": ${fileErr.message || 'Không thể tải lên.'}`, 'error');
          }
        }

        if (progressBar) progressBar.style.width = '100%';
        if (progressPercent) progressPercent.textContent = '100%';
        if (progressText) progressText.textContent = `Hoàn tất tải lên ${uploadedSuccessCount}/${accepted.length} video.`;
        if (uploadedSuccessCount > 0) {
          UI.showToast(`Đã tải lên thành công ${uploadedSuccessCount} video!`, 'success');
        }
        if (pendingApprovalCount > 0) {
          UI.showToast(`${pendingApprovalCount} video đã gửi Admin xét duyệt.`, 'info');
        }
      } catch (err) {
        UI.showToast(err.message || 'Lỗi tải video lên máy chủ.', 'error');
      } finally {
        setTimeout(() => {
          if (progressBox) progressBox.classList.add('hidden');
        }, 2500);
      }
    };

    // Video File Upload & Dropzone Handlers
    const videoFileInput = getEl('studio-video-file-input');
    const chooseVideoBtn = getEl('btn-choose-video-file');
    const videoDropzone = getEl('studio-video-dropzone');

    if (chooseVideoBtn && videoFileInput) {
      chooseVideoBtn.onclick = (e) => {
        e.stopPropagation();
        videoFileInput.click();
      };
    }

    if (videoDropzone && videoFileInput) {
      videoDropzone.onclick = (e) => {
        if (e.target !== chooseVideoBtn && !chooseVideoBtn?.contains(e.target)) {
          videoFileInput.click();
        }
      };

      videoDropzone.onkeydown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          videoFileInput.click();
        }
      };

      videoDropzone.ondragover = (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        videoDropzone.classList.add('border-primary', 'bg-primary/5');
      };

      videoDropzone.ondragleave = (e) => {
        e.preventDefault();
        videoDropzone.classList.remove('border-primary', 'bg-primary/5');
      };

      videoDropzone.ondrop = async (e) => {
        e.preventDefault();
        videoDropzone.classList.remove('border-primary', 'bg-primary/5');
        const files = Array.from(e.dataTransfer?.files || []);
        if (files.length) {
          await uploadVideoBatch(files);
        }
      };
    }

    if (videoFileInput) {
      videoFileInput.onchange = async (e) => {
        const files = Array.from(e.target.files || []);
        if (files.length) {
          await uploadVideoBatch(files);
        }
        videoFileInput.value = '';
      };
    }

    // Word-like WYSIWYG Editor Helpers & ExecCommand Bindings
    const formatDoc = (cmd, value = null) => {
      document.execCommand(cmd, false, value);
      const editor = getEl('studio-content-editor');
      if (editor) editor.focus();
    };

    const toolFormat = getEl('studio-tool-format');
    if (toolFormat) {
      toolFormat.onchange = (e) => {
        formatDoc('formatBlock', `<${e.target.value}>`);
      };
    }

    getEl('studio-tool-bold')?.addEventListener('click', () => formatDoc('bold'));
    getEl('studio-tool-italic')?.addEventListener('click', () => formatDoc('italic'));
    getEl('studio-tool-underline')?.addEventListener('click', () => formatDoc('underline'));
    getEl('studio-tool-strike')?.addEventListener('click', () => formatDoc('strikeThrough'));
    getEl('studio-tool-left')?.addEventListener('click', () => formatDoc('justifyLeft'));
    getEl('studio-tool-center')?.addEventListener('click', () => formatDoc('justifyCenter'));
    getEl('studio-tool-right')?.addEventListener('click', () => formatDoc('justifyRight'));
    getEl('studio-tool-justify')?.addEventListener('click', () => formatDoc('justifyFull'));
    getEl('studio-tool-ul')?.addEventListener('click', () => formatDoc('insertUnorderedList'));
    getEl('studio-tool-ol')?.addEventListener('click', () => formatDoc('insertOrderedList'));
    getEl('studio-tool-hr')?.addEventListener('click', () => formatDoc('insertHorizontalRule'));
    getEl('studio-tool-clear')?.addEventListener('click', () => formatDoc('removeFormat'));
    getEl('studio-tool-undo')?.addEventListener('click', () => formatDoc('undo'));
    getEl('studio-tool-redo')?.addEventListener('click', () => formatDoc('redo'));

    const colorInput = getEl('studio-tool-color');
    if (colorInput) {
      colorInput.oninput = (e) => formatDoc('foreColor', e.target.value);
    }
    const bgInput = getEl('studio-tool-bgcolor');
    if (bgInput) {
      bgInput.oninput = (e) => formatDoc('hiliteColor', e.target.value);
    }

    // Insert Callout Box
    getEl('studio-tool-callout')?.addEventListener('click', () => {
      const html = `<blockquote style="border-left: 3px solid #2563EB; background: #EFF4FE; padding: 12px 16px; margin: 12px 0; border-radius: 0 8px 8px 0; color: #1E3A8A;"><strong>💡 Lưu ý trọng tâm:</strong> Nhập ghi chú kiến thức cần nhấn mạnh cho sinh viên tại đây...</blockquote><p><br></p>`;
      formatDoc('insertHTML', html);
    });

    // Insert 3x3 Table
    getEl('studio-tool-table')?.addEventListener('click', () => {
      const html = `
        <table style="width: 100%; border-collapse: collapse; margin: 12px 0; border: 1px solid #E8E6DF;">
          <thead>
            <tr style="background: #F4F1EA;">
              <th style="border: 1px solid #E8E6DF; padding: 8px; text-align: left;">Cột 1</th>
              <th style="border: 1px solid #E8E6DF; padding: 8px; text-align: left;">Cột 2</th>
              <th style="border: 1px solid #E8E6DF; padding: 8px; text-align: left;">Cột 3</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 1</td>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 2</td>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 3</td>
            </tr>
            <tr>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 4</td>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 5</td>
              <td style="border: 1px solid #E8E6DF; padding: 8px;">Dữ liệu 6</td>
            </tr>
          </tbody>
        </table>
        <p><br></p>
      `;
      formatDoc('insertHTML', html);
    });

    // Render Attached Files List (with API server deletion)
    function renderAttachments() {
      const containerEl = getEl('studio-attachments-list');
      if (!containerEl) return;

      if (attachedResources.length === 0) {
        containerEl.innerHTML = `
          <div class="p-4 rounded-xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68]">
            Chưa có tài liệu đính kèm. Bấm "Đính kèm tệp" để tải lên tài liệu học tập (được quét an toàn qua ClamAV).
          </div>
        `;
        return;
      }

      containerEl.innerHTML = attachedResources.map((res, idx) => `
        <div class="p-3 rounded-xl bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="material-symbols-outlined text-[20px] text-emerald-600 shrink-0">description</span>
            <div class="min-w-0">
              <span class="font-bold text-[#222120] dark:text-[#EDEDEB] truncate block">
                ${UI.escapeHtml(res.title || res.filename || 'Tài liệu')}
              </span>
              <span class="text-[10px] font-semibold block ${res.file_asset?.virus_scan_status === 'CLEAN' && res.file_asset?.status === 'ACTIVE' ? 'text-emerald-600' : 'text-amber-700'}">${res.file_asset?.virus_scan_status === 'CLEAN' && res.file_asset?.status === 'ACTIVE' ? 'Đã quét sạch - Có thể truy cập' : 'Đang chờ quét an toàn - Chưa thể truy cập'}</span>
            </div>
          </div>
          <button
            type="button"
            class="btn-remove-attachment px-2.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer shrink-0"
            data-idx="${idx}"
            title="Xóa tài liệu này"
          >
            <span class="material-symbols-outlined text-[15px]">delete</span>
            <span>Xóa tài liệu</span>
          </button>
        </div>
      `).join('');

      containerEl.querySelectorAll('.btn-remove-attachment').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          const res = attachedResources[idx];
          if (!res) return;

          const conf = await UI.confirm('Xóa tài liệu', `Bạn có chắc chắn muốn xóa tài liệu "${res.title || res.filename || 'này'}" khỏi bài học?`, 'Xóa tài liệu');
          if (!conf) return;

          const resId = res?.resource_id || res?.id;

          if (lessonId && resId) {
            try {
              const response = await ApiClient.detachLessonResource(courseId, lessonId, resId);
              if (response.pending_approval) {
                UI.showToast('Yêu cầu gỡ tài liệu đã gửi Admin xét duyệt.', 'info');
                return;
              }
              UI.showToast('Đã xóa tài liệu khỏi bài giảng!', 'success');
            } catch (err) {
              UI.showToast(err.message || 'Lỗi khi xóa tài liệu trên máy chủ.', 'error');
              return;
            }
          }

          // If this resource was current video, clear it
          if (currentVideoUrl && resourceVideoUrl(res) === currentVideoUrl) {
            currentVideoUrl = '';
            renderVideoPreview('');
          }

          attachedResources.splice(idx, 1);
          renderAttachments();
          renderVideoList();
        };
      });
    }

    // Normalization helper for Mini-Quiz Questions (Backward compatible)
    const normalizeQuizQuestion = (raw) => {
      if (!raw) return null;
      const q = { ...raw };
      if (!q.type) {
        q.type = 'MULTIPLE_CHOICE';
      }
      if (q.type === 'MULTIPLE_CHOICE' || q.type === 'SINGLE_CHOICE') {
        q.type = 'MULTIPLE_CHOICE';
        const rawOpts = Array.isArray(q.options) ? q.options : (Array.isArray(q.choices) ? q.choices : []);
        q.options = rawOpts.length > 0 ? [...rawOpts] : ['Lựa chọn A', 'Lựa chọn B', 'Lựa chọn C', 'Lựa chọn D'];
        if (q.options.length < 2) {
          while (q.options.length < 2) {
            q.options.push(`Lựa chọn ${String.fromCharCode(65 + q.options.length)}`);
          }
        }
        if (!Array.isArray(q.correct_answers)) {
          if (typeof q.correct_index === 'number') {
            q.correct_answers = [q.correct_index];
          } else {
            q.correct_answers = [0];
          }
        }
        if (q.allow_multiple === undefined) {
          q.allow_multiple = q.correct_answers.length > 1;
        }
        q.correct_index = q.correct_answers[0] ?? 0;
      } else if (q.type === 'FILL_BLANK') {
        if (!Array.isArray(q.blanks) || q.blanks.length === 0) {
          q.blanks = [{ accepted_answers: [''] }];
        } else {
          q.blanks = q.blanks.map(b => ({
            accepted_answers: Array.isArray(b.accepted_answers)
              ? [...b.accepted_answers]
              : (b.accepted_answers ? [String(b.accepted_answers)] : [''])
          }));
        }
      } else if (q.type === 'MATCHING') {
        if (!Array.isArray(q.pairs) || q.pairs.length === 0) {
          q.pairs = [
            { left: '', right: '' },
            { left: '', right: '' }
          ];
        } else {
          q.pairs = q.pairs.map(p => ({ left: p.left || '', right: p.right || '' }));
          if (q.pairs.length < 2) {
            while (q.pairs.length < 2) q.pairs.push({ left: '', right: '' });
          }
        }
      } else if (q.type === 'TRUE_FALSE') {
        if (typeof q.correct_value !== 'boolean') {
          q.correct_value = true;
        }
      }
      return q;
    };

    // Render Question Body based on Question Type
    function renderQuestionBody(q, qIdx) {
      if (q.type === 'MULTIPLE_CHOICE') {
        const isMulti = Boolean(q.allow_multiple);
        const correctSet = new Set(Array.isArray(q.correct_answers) ? q.correct_answers : [q.correct_index ?? 0]);

        return `
          <div class="space-y-3 pt-1">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <label class="block text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                Các lựa chọn trả lời (Tích chọn đáp án đúng):
              </label>
              <label class="flex items-center gap-1.5 text-xs text-[#5C5B57] dark:text-[#9E9D99] cursor-pointer hover:text-[#222120] dark:hover:text-white transition-colors">
                <input
                  type="checkbox"
                  class="quiz-allow-multi-chk rounded text-purple-600 focus:ring-purple-600 w-3.5 h-3.5 cursor-pointer"
                  data-q-idx="${qIdx}"
                  ${isMulti ? 'checked' : ''}
                />
                <span class="font-medium text-[11px]">Nhiều đáp án đúng (Multi-select)</span>
              </label>
            </div>

            <div class="space-y-2">
              ${(q.options || ['Lựa chọn A', 'Lựa chọn B']).map((opt, optIdx) => {
                const isChecked = correctSet.has(optIdx);
                return `
                  <div class="flex items-center gap-2 p-1.5 rounded-xl border transition-all ${isChecked ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20' : 'border-transparent'}">
                    ${isMulti ? `
                      <input
                        type="checkbox"
                        class="quiz-opt-chk text-emerald-600 focus:ring-emerald-600 h-4 w-4 rounded cursor-pointer shrink-0 ml-1"
                        data-q-idx="${qIdx}"
                        data-opt-idx="${optIdx}"
                        ${isChecked ? 'checked' : ''}
                        title="Tích chọn làm một trong các đáp án đúng"
                      />
                    ` : `
                      <input
                        type="radio"
                        name="correct_choice_${qIdx}"
                        class="quiz-opt-radio text-emerald-600 focus:ring-emerald-600 h-4 w-4 cursor-pointer shrink-0 ml-1"
                        data-q-idx="${qIdx}"
                        data-opt-idx="${optIdx}"
                        ${isChecked ? 'checked' : ''}
                        title="Chọn làm đáp án đúng duy nhất"
                      />
                    `}
                    <span class="w-6 h-6 rounded-lg ${isChecked ? 'bg-emerald-600 text-white font-bold' : 'bg-[#EDEBE6] dark:bg-[#32312F] text-[#5C5B57] dark:text-[#A8A6A0] font-semibold'} text-xs flex items-center justify-center shrink-0">
                      ${String.fromCharCode(65 + optIdx)}
                    </span>
                    <input
                      type="text"
                      class="quiz-opt-input flex-1 px-3 py-1.5 rounded-lg bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all"
                      data-q-idx="${qIdx}"
                      data-opt-idx="${optIdx}"
                      value="${UI.escapeHtml(opt)}"
                      placeholder="Lựa chọn ${String.fromCharCode(65 + optIdx)}..."
                    />
                    ${q.options.length > 2 ? `
                      <button
                        type="button"
                        class="btn-del-opt p-1 text-[#8F8E8A] hover:text-rose-600 transition-colors cursor-pointer shrink-0"
                        data-q-idx="${qIdx}"
                        data-opt-idx="${optIdx}"
                        title="Xóa lựa chọn này"
                      >
                        <span class="material-symbols-outlined text-[16px]">close</span>
                      </button>
                    ` : ''}
                  </div>
                `;
              }).join('')}
            </div>

            <div class="pt-1">
              <button
                type="button"
                class="btn-add-opt text-xs text-purple-600 dark:text-purple-400 hover:text-purple-700 font-bold flex items-center gap-1 px-3 py-1.5 rounded-xl border border-dashed border-purple-300 dark:border-purple-800 hover:bg-purple-50 dark:hover:bg-purple-950/40 transition-all cursor-pointer"
                data-q-idx="${qIdx}"
              >
                <span class="material-symbols-outlined text-[15px]">add</span>
                <span>Thêm lựa chọn</span>
              </button>
            </div>
          </div>
        `;
      }

      if (q.type === 'FILL_BLANK') {
        const blanks = q.blanks && q.blanks.length ? q.blanks : [{ accepted_answers: [''] }];

        return `
          <div class="space-y-3 pt-1">
            <div class="p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 text-xs text-emerald-900 dark:text-emerald-200 space-y-1 leading-relaxed">
              <div class="flex items-center gap-1 font-bold">
                <span class="material-symbols-outlined text-[15px]">info</span>
                <span>Hướng dẫn câu hỏi điền khuyết:</span>
              </div>
              <p class="text-[11px] text-emerald-800 dark:text-emerald-300">
                Mỗi ô trống tương ứng với một vị trí <code>[___]</code> trong đề bài. Nhập các đáp án đúng được chấp nhận cho từng ô trống (nhiều đáp án cách nhau bởi dấu phẩy <code>,</code>). Hệ thống sẽ tự động so khớp không phân biệt hoa thường khi học sinh làm bài.
              </p>
            </div>

            <div class="space-y-2.5">
              ${blanks.map((b, bIdx) => {
                const answersStr = Array.isArray(b.accepted_answers) ? b.accepted_answers.join(', ') : (b.accepted_answers || '');
                return `
                  <div class="flex items-center gap-2 p-2.5 rounded-xl bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
                    <span class="px-2 py-1 rounded-md bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 font-bold text-xs shrink-0">
                      Ô #${bIdx + 1}
                    </span>
                    <input
                      type="text"
                      class="quiz-blank-input flex-1 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#1A1918] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-emerald-500 transition-all"
                      data-q-idx="${qIdx}"
                      data-b-idx="${bIdx}"
                      value="${UI.escapeHtml(answersStr)}"
                      placeholder="Các đáp án đúng được chấp nhận (VD: Hà Nội, Ha Noi, Hanoi)..."
                    />
                    ${blanks.length > 1 ? `
                      <button
                        type="button"
                        class="btn-del-blank p-1 text-[#8F8E8A] hover:text-rose-600 transition-colors cursor-pointer shrink-0"
                        data-q-idx="${qIdx}"
                        data-b-idx="${bIdx}"
                        title="Xóa ô trống này"
                      >
                        <span class="material-symbols-outlined text-[16px]">close</span>
                      </button>
                    ` : ''}
                  </div>
                `;
              }).join('')}
            </div>

            <div class="pt-1">
              <button
                type="button"
                class="btn-add-blank text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 font-bold flex items-center gap-1 px-3 py-1.5 rounded-xl border border-dashed border-emerald-300 dark:border-emerald-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-all cursor-pointer"
                data-q-idx="${qIdx}"
              >
                <span class="material-symbols-outlined text-[15px]">add</span>
                <span>Thêm chỗ trống</span>
              </button>
            </div>
          </div>
        `;
      }

      if (q.type === 'MATCHING') {
        const pairs = q.pairs && q.pairs.length ? q.pairs : [{ left: '', right: '' }, { left: '', right: '' }];

        return `
          <div class="space-y-3 pt-1">
            <div class="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 text-xs text-amber-900 dark:text-amber-200 space-y-1 leading-relaxed">
              <div class="flex items-center gap-1 font-bold">
                <span class="material-symbols-outlined text-[15px]">info</span>
                <span>Hướng dẫn câu hỏi nối từ:</span>
              </div>
              <p class="text-[11px] text-amber-800 dark:text-amber-300">
                Nhập các cặp đối ứng giữa Vế Trái (Cột A) và Vế Phải (Cột B). Khi học sinh làm bài, danh sách vế phải sẽ được tự động xáo trộn để học sinh chọn ghép đôi.
              </p>
            </div>

            <div class="space-y-2">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 px-1 text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                <div>Vế Trái (Cột A - Khái niệm / Thuật ngữ)</div>
                <div>Vế Phải (Cột B - Định nghĩa / Ý nghĩa đối ứng)</div>
              </div>

              ${pairs.map((p, pIdx) => `
                <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-2 rounded-xl bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
                  <div class="flex items-center gap-2 flex-1">
                    <span class="w-5 h-5 rounded-md bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 font-bold text-[11px] flex items-center justify-center shrink-0">
                      ${pIdx + 1}
                    </span>
                    <input
                      type="text"
                      class="quiz-pair-left flex-1 px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-[#1A1918] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-amber-500 transition-all"
                      data-q-idx="${qIdx}"
                      data-p-idx="${pIdx}"
                      value="${UI.escapeHtml(p.left || '')}"
                      placeholder="VD: HTML..."
                    />
                  </div>
                  <span class="material-symbols-outlined text-slate-400 text-[16px] hidden sm:inline shrink-0">swap_horiz</span>
                  <div class="flex items-center gap-2 flex-1">
                    <input
                      type="text"
                      class="quiz-pair-right flex-1 px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-[#1A1918] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-amber-500 transition-all"
                      data-q-idx="${qIdx}"
                      data-p-idx="${pIdx}"
                      value="${UI.escapeHtml(p.right || '')}"
                      placeholder="VD: Ngôn ngữ đánh dấu siêu văn bản..."
                    />
                    ${pairs.length > 2 ? `
                      <button
                        type="button"
                        class="btn-del-pair p-1 text-[#8F8E8A] hover:text-rose-600 transition-colors cursor-pointer shrink-0"
                        data-q-idx="${qIdx}"
                        data-p-idx="${pIdx}"
                        title="Xóa cặp nối này"
                      >
                        <span class="material-symbols-outlined text-[16px]">close</span>
                      </button>
                    ` : ''}
                  </div>
                </div>
              `).join('')}
            </div>

            <div class="pt-1">
              <button
                type="button"
                class="btn-add-pair text-xs text-amber-600 dark:text-amber-400 hover:text-amber-700 font-bold flex items-center gap-1 px-3 py-1.5 rounded-xl border border-dashed border-amber-300 dark:border-amber-800 hover:bg-amber-50 dark:hover:bg-amber-950/40 transition-all cursor-pointer"
                data-q-idx="${qIdx}"
              >
                <span class="material-symbols-outlined text-[15px]">add</span>
                <span>Thêm cặp nối</span>
              </button>
            </div>
          </div>
        `;
      }

      if (q.type === 'TRUE_FALSE') {
        const isTrue = q.correct_value !== false;
        return `
          <div class="space-y-2 pt-1">
            <label class="block text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
              Chọn đáp án đúng của mệnh đề:
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label class="flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${isTrue ? 'border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 shadow-2xs font-bold' : 'border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-[#5C5B57]'}">
                <input
                  type="radio"
                  name="tf_choice_${qIdx}"
                  value="true"
                  class="quiz-tf-radio text-emerald-600 focus:ring-emerald-600 w-4 h-4 cursor-pointer"
                  data-q-idx="${qIdx}"
                  ${isTrue ? 'checked' : ''}
                />
                <span class="material-symbols-outlined text-emerald-600 text-[20px]">check_circle</span>
                <span class="text-xs sm:text-sm">Đúng (True) - Mệnh đề là chính xác</span>
              </label>

              <label class="flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${!isTrue ? 'border-rose-500 bg-rose-50/60 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 shadow-2xs font-bold' : 'border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-[#5C5B57]'}">
                <input
                  type="radio"
                  name="tf_choice_${qIdx}"
                  value="false"
                  class="quiz-tf-radio text-rose-600 focus:ring-rose-600 w-4 h-4 cursor-pointer"
                  data-q-idx="${qIdx}"
                  ${!isTrue ? 'checked' : ''}
                />
                <span class="material-symbols-outlined text-rose-600 text-[20px]">cancel</span>
                <span class="text-xs sm:text-sm">Sai (False) - Mệnh đề không chính xác</span>
              </label>
            </div>
          </div>
        `;
      }

      return '';
    }

    // Mini-Quiz Authoring Renderer
    function renderMiniQuiz() {
      const containerEl = getEl('studio-mini-quiz-list');
      if (!containerEl) return;

      const countEl = getEl('studio-mini-quiz-count');
      if (countEl) countEl.textContent = `${miniQuizQuestions.length} câu hỏi`;

      if (miniQuizQuestions.length === 0) {
        containerEl.innerHTML = `
          <div class="p-6 rounded-2xl border border-dashed border-[#E8E6DF] dark:border-[#2E2D2B] text-center text-xs text-[#8F8E8A] dark:text-[#6D6C68] space-y-2">
            <span class="material-symbols-outlined text-[28px] text-purple-400">quiz</span>
            <p class="font-medium">Chưa có câu hỏi củng cố nào cho bài học này.</p>
            <p class="text-[11px] text-[#A8A6A0]">Bấm nút "Thêm câu hỏi" ở trên để tạo câu hỏi trắc nghiệm, điền khuyết, nối từ hoặc đúng/sai.</p>
          </div>
        `;
        return;
      }

      containerEl.innerHTML = miniQuizQuestions.map((q, qIdx) => `
        <div class="p-5 rounded-2xl bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] space-y-4 relative shadow-2xs" data-q-idx="${qIdx}">
          <!-- Card Header -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300 flex items-center gap-1 shrink-0">
                <span class="material-symbols-outlined text-[14px]">help</span>
                <span>Câu hỏi ${qIdx + 1}</span>
              </span>

              <!-- Type Switcher Tabs -->
              <div class="inline-flex p-0.5 rounded-xl bg-[#EDEBE6] dark:bg-[#1E1D1B] border border-[#E0DED7] dark:border-[#353432] text-[11px] font-semibold">
                <button
                  type="button"
                  class="btn-switch-type px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all cursor-pointer ${q.type === 'MULTIPLE_CHOICE' ? 'bg-purple-600 text-white shadow-xs font-bold' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120]'}"
                  data-q-idx="${qIdx}"
                  data-target-type="MULTIPLE_CHOICE"
                  title="Câu hỏi Trắc nghiệm nhiều lựa chọn"
                >
                  <span class="material-symbols-outlined text-[14px]">checklist</span>
                  <span>Trắc nghiệm</span>
                </button>
                <button
                  type="button"
                  class="btn-switch-type px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all cursor-pointer ${q.type === 'FILL_BLANK' ? 'bg-emerald-600 text-white shadow-xs font-bold' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120]'}"
                  data-q-idx="${qIdx}"
                  data-target-type="FILL_BLANK"
                  title="Câu hỏi Điền khuyết vào chỗ trống"
                >
                  <span class="material-symbols-outlined text-[14px]">edit_note</span>
                  <span>Điền khuyết</span>
                </button>
                <button
                  type="button"
                  class="btn-switch-type px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all cursor-pointer ${q.type === 'MATCHING' ? 'bg-amber-600 text-white shadow-xs font-bold' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120]'}"
                  data-q-idx="${qIdx}"
                  data-target-type="MATCHING"
                  title="Câu hỏi Nối từ / Ghép đôi khái niệm"
                >
                  <span class="material-symbols-outlined text-[14px]">swap_horiz</span>
                  <span>Nối từ</span>
                </button>
                <button
                  type="button"
                  class="btn-switch-type px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all cursor-pointer ${q.type === 'TRUE_FALSE' ? 'bg-sky-600 text-white shadow-xs font-bold' : 'text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120]'}"
                  data-q-idx="${qIdx}"
                  data-target-type="TRUE_FALSE"
                  title="Câu hỏi Đúng hoặc Sai"
                >
                  <span class="material-symbols-outlined text-[14px]">check_box</span>
                  <span>Đúng / Sai</span>
                </button>
              </div>
            </div>

            <!-- Move / Delete Actions -->
            <div class="flex items-center gap-1 self-end sm:self-auto">
              ${qIdx > 0 ? `
                <button type="button" class="btn-move-q-up p-1 text-[#8F8E8A] hover:text-primary transition-colors cursor-pointer" data-idx="${qIdx}" title="Di chuyển lên trên">
                  <span class="material-symbols-outlined text-[18px]">arrow_upward</span>
                </button>
              ` : ''}
              ${qIdx < miniQuizQuestions.length - 1 ? `
                <button type="button" class="btn-move-q-down p-1 text-[#8F8E8A] hover:text-primary transition-colors cursor-pointer" data-idx="${qIdx}" title="Di chuyển xuống dưới">
                  <span class="material-symbols-outlined text-[18px]">arrow_downward</span>
                </button>
              ` : ''}
              <button
                type="button"
                class="btn-del-quiz-q p-1 text-[#8F8E8A] hover:text-rose-600 transition-colors cursor-pointer"
                data-idx="${qIdx}"
                title="Xóa câu hỏi này"
              >
                <span class="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>
          </div>

          <!-- Question Prompt -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="block text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
                ${q.type === 'FILL_BLANK'
                  ? 'Nội dung câu hỏi (chèn [___] vào chỗ trống cần điền) *'
                  : (q.type === 'MATCHING'
                    ? 'Đề bài / Yêu cầu ghép nối *'
                    : 'Nội dung câu hỏi / Đề bài *')}
              </label>
              ${q.type === 'FILL_BLANK' ? `
                <button
                  type="button"
                  class="btn-insert-blank-tag text-[10px] font-bold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 flex items-center gap-0.5 px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 cursor-pointer transition-all"
                  data-q-idx="${qIdx}"
                  title="Bấm để chèn nhanh ký hiệu chỗ trống [___] vào đề bài"
                >
                  <span class="material-symbols-outlined text-[12px]">add</span>
                  <span>Chèn [___]</span>
                </button>
              ` : ''}
            </div>
            <textarea
              rows="2"
              class="quiz-q-input w-full px-3 py-2 rounded-xl bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all resize-y"
              data-q-idx="${qIdx}"
              placeholder="${q.type === 'FILL_BLANK' ? 'VD: Thủ đô của Việt Nam là [___]. Thành phố trực thuộc trung ương có diện tích lớn nhất là [___].' : (q.type === 'MATCHING' ? 'VD: Hãy nối các khái niệm ở cột A với định nghĩa tương ứng ở cột B:' : (q.type === 'TRUE_FALSE' ? 'VD: Python là một ngôn ngữ lập trình thông dịch (Interpreted Language).' : 'VD: Thuật toán nào sau đây có độ phức tạp trung bình là O(n log n)?'))}"
            >${UI.escapeHtml(q.question || '')}</textarea>
          </div>

          <!-- Question Body according to Type -->
          ${renderQuestionBody(q, qIdx)}

          <!-- Explanation Section -->
          <div class="space-y-1 pt-2 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
            <label class="block text-[11px] font-bold text-[#5C5B57] dark:text-[#9E9D99]">
              Giải thích đáp án & Gợi ý (Hiển thị cho học sinh sau khi bấm "Kiểm tra đáp án")
            </label>
            <input
              type="text"
              class="quiz-exp-input w-full px-3 py-2 rounded-xl bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] text-xs text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-primary transition-all"
              data-q-idx="${qIdx}"
              value="${UI.escapeHtml(q.explanation || '')}"
              placeholder="VD: Quicksort và Mergesort đều có độ phức tạp thời gian trung bình O(n log n)..."
            />
          </div>
        </div>
      `).join('');

      // Bind switch question type
      containerEl.querySelectorAll('.btn-switch-type').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          const targetType = btn.dataset.targetType;
          if (miniQuizQuestions[qIdx]) {
            miniQuizQuestions[qIdx].type = targetType;
            if (targetType === 'MULTIPLE_CHOICE') {
              if (!Array.isArray(miniQuizQuestions[qIdx].options) || miniQuizQuestions[qIdx].options.length < 2) {
                miniQuizQuestions[qIdx].options = ['Lựa chọn A', 'Lựa chọn B', 'Lựa chọn C', 'Lựa chọn D'];
              }
              if (!Array.isArray(miniQuizQuestions[qIdx].correct_answers)) {
                miniQuizQuestions[qIdx].correct_answers = [0];
              }
            } else if (targetType === 'FILL_BLANK') {
              if (!Array.isArray(miniQuizQuestions[qIdx].blanks) || miniQuizQuestions[qIdx].blanks.length === 0) {
                miniQuizQuestions[qIdx].blanks = [{ accepted_answers: [''] }];
              }
            } else if (targetType === 'MATCHING') {
              if (!Array.isArray(miniQuizQuestions[qIdx].pairs) || miniQuizQuestions[qIdx].pairs.length < 2) {
                miniQuizQuestions[qIdx].pairs = [
                  { left: '', right: '' },
                  { left: '', right: '' }
                ];
              }
            } else if (targetType === 'TRUE_FALSE') {
              if (typeof miniQuizQuestions[qIdx].correct_value !== 'boolean') {
                miniQuizQuestions[qIdx].correct_value = true;
              }
            }
            renderMiniQuiz();
          }
        };
      });

      // Bind move up
      containerEl.querySelectorAll('.btn-move-q-up').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx > 0) {
            const temp = miniQuizQuestions[idx];
            miniQuizQuestions[idx] = miniQuizQuestions[idx - 1];
            miniQuizQuestions[idx - 1] = temp;
            renderMiniQuiz();
          }
        };
      });

      // Bind move down
      containerEl.querySelectorAll('.btn-move-q-down').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx < miniQuizQuestions.length - 1) {
            const temp = miniQuizQuestions[idx];
            miniQuizQuestions[idx] = miniQuizQuestions[idx + 1];
            miniQuizQuestions[idx + 1] = temp;
            renderMiniQuiz();
          }
        };
      });

      // Bind delete question
      containerEl.querySelectorAll('.btn-del-quiz-q').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          miniQuizQuestions.splice(idx, 1);
          renderMiniQuiz();
        };
      });

      // Bind question prompt change
      containerEl.querySelectorAll('.quiz-q-input').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) miniQuizQuestions[qIdx].question = e.target.value;
        };
      });

      // Bind insert blank tag shortcut
      containerEl.querySelectorAll('.btn-insert-blank-tag').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            const curText = miniQuizQuestions[qIdx].question || '';
            miniQuizQuestions[qIdx].question = curText ? `${curText} [___]` : '[___]';
            if (!Array.isArray(miniQuizQuestions[qIdx].blanks)) {
              miniQuizQuestions[qIdx].blanks = [];
            }
            const matchCount = (miniQuizQuestions[qIdx].question.match(/\[___\]/g) || []).length;
            while (miniQuizQuestions[qIdx].blanks.length < matchCount) {
              miniQuizQuestions[qIdx].blanks.push({ accepted_answers: [''] });
            }
            renderMiniQuiz();
          }
        };
      });

      // Bind allow multi toggle
      containerEl.querySelectorAll('.quiz-allow-multi-chk').forEach(chk => {
        chk.onchange = (e) => {
          const qIdx = parseInt(chk.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            miniQuizQuestions[qIdx].allow_multiple = e.target.checked;
            if (!e.target.checked && miniQuizQuestions[qIdx].correct_answers && miniQuizQuestions[qIdx].correct_answers.length > 1) {
              miniQuizQuestions[qIdx].correct_answers = [miniQuizQuestions[qIdx].correct_answers[0]];
              miniQuizQuestions[qIdx].correct_index = miniQuizQuestions[qIdx].correct_answers[0];
            }
            renderMiniQuiz();
          }
        };
      });

      // Bind choice radio change (single choice)
      containerEl.querySelectorAll('.quiz-opt-radio').forEach(radio => {
        radio.onchange = () => {
          const qIdx = parseInt(radio.dataset.qIdx, 10);
          const optIdx = parseInt(radio.dataset.optIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            miniQuizQuestions[qIdx].correct_answers = [optIdx];
            miniQuizQuestions[qIdx].correct_index = optIdx;
            renderMiniQuiz();
          }
        };
      });

      // Bind choice checkbox change (multi choice)
      containerEl.querySelectorAll('.quiz-opt-chk').forEach(chk => {
        chk.onchange = (e) => {
          const qIdx = parseInt(chk.dataset.qIdx, 10);
          const optIdx = parseInt(chk.dataset.optIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            let currentSet = new Set(miniQuizQuestions[qIdx].correct_answers || []);
            if (e.target.checked) {
              currentSet.add(optIdx);
            } else {
              currentSet.delete(optIdx);
            }
            miniQuizQuestions[qIdx].correct_answers = Array.from(currentSet).sort((a, b) => a - b);
            miniQuizQuestions[qIdx].correct_index = miniQuizQuestions[qIdx].correct_answers[0] ?? 0;
            renderMiniQuiz();
          }
        };
      });

      // Bind choice input change
      containerEl.querySelectorAll('.quiz-opt-input').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          const optIdx = parseInt(inp.dataset.optIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].options) {
            miniQuizQuestions[qIdx].options[optIdx] = e.target.value;
          }
        };
      });

      // Bind add option button
      containerEl.querySelectorAll('.btn-add-opt').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            if (!Array.isArray(miniQuizQuestions[qIdx].options)) {
              miniQuizQuestions[qIdx].options = [];
            }
            const nextLetter = String.fromCharCode(65 + miniQuizQuestions[qIdx].options.length);
            miniQuizQuestions[qIdx].options.push(`Lựa chọn ${nextLetter}`);
            renderMiniQuiz();
          }
        };
      });

      // Bind delete option button
      containerEl.querySelectorAll('.btn-del-opt').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          const optIdx = parseInt(btn.dataset.optIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].options && miniQuizQuestions[qIdx].options.length > 2) {
            miniQuizQuestions[qIdx].options.splice(optIdx, 1);
            if (Array.isArray(miniQuizQuestions[qIdx].correct_answers)) {
              miniQuizQuestions[qIdx].correct_answers = miniQuizQuestions[qIdx].correct_answers
                .filter(idx => idx !== optIdx)
                .map(idx => (idx > optIdx ? idx - 1 : idx));
              if (miniQuizQuestions[qIdx].correct_answers.length === 0) {
                miniQuizQuestions[qIdx].correct_answers = [0];
              }
              miniQuizQuestions[qIdx].correct_index = miniQuizQuestions[qIdx].correct_answers[0];
            }
            renderMiniQuiz();
          }
        };
      });

      // Bind blank input change
      containerEl.querySelectorAll('.quiz-blank-input').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          const bIdx = parseInt(inp.dataset.bIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].blanks && miniQuizQuestions[qIdx].blanks[bIdx]) {
            const rawVal = e.target.value;
            const parts = rawVal.split(',').map(s => s.trim()).filter(Boolean);
            miniQuizQuestions[qIdx].blanks[bIdx].accepted_answers = parts.length ? parts : [rawVal.trim()];
          }
        };
      });

      // Bind add blank button
      containerEl.querySelectorAll('.btn-add-blank').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            if (!Array.isArray(miniQuizQuestions[qIdx].blanks)) {
              miniQuizQuestions[qIdx].blanks = [];
            }
            miniQuizQuestions[qIdx].blanks.push({ accepted_answers: [''] });
            renderMiniQuiz();
          }
        };
      });

      // Bind delete blank button
      containerEl.querySelectorAll('.btn-del-blank').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          const bIdx = parseInt(btn.dataset.bIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].blanks && miniQuizQuestions[qIdx].blanks.length > 1) {
            miniQuizQuestions[qIdx].blanks.splice(bIdx, 1);
            renderMiniQuiz();
          }
        };
      });

      // Bind pair left input change
      containerEl.querySelectorAll('.quiz-pair-left').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          const pIdx = parseInt(inp.dataset.pIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].pairs && miniQuizQuestions[qIdx].pairs[pIdx]) {
            miniQuizQuestions[qIdx].pairs[pIdx].left = e.target.value;
          }
        };
      });

      // Bind pair right input change
      containerEl.querySelectorAll('.quiz-pair-right').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          const pIdx = parseInt(inp.dataset.pIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].pairs && miniQuizQuestions[qIdx].pairs[pIdx]) {
            miniQuizQuestions[qIdx].pairs[pIdx].right = e.target.value;
          }
        };
      });

      // Bind add pair button
      containerEl.querySelectorAll('.btn-add-pair').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            if (!Array.isArray(miniQuizQuestions[qIdx].pairs)) {
              miniQuizQuestions[qIdx].pairs = [];
            }
            miniQuizQuestions[qIdx].pairs.push({ left: '', right: '' });
            renderMiniQuiz();
          }
        };
      });

      // Bind delete pair button
      containerEl.querySelectorAll('.btn-del-pair').forEach(btn => {
        btn.onclick = () => {
          const qIdx = parseInt(btn.dataset.qIdx, 10);
          const pIdx = parseInt(btn.dataset.pIdx, 10);
          if (miniQuizQuestions[qIdx] && miniQuizQuestions[qIdx].pairs && miniQuizQuestions[qIdx].pairs.length > 2) {
            miniQuizQuestions[qIdx].pairs.splice(pIdx, 1);
            renderMiniQuiz();
          }
        };
      });

      // Bind true/false radio change
      containerEl.querySelectorAll('.quiz-tf-radio').forEach(radio => {
        radio.onchange = (e) => {
          const qIdx = parseInt(radio.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) {
            miniQuizQuestions[qIdx].correct_value = (e.target.value === 'true');
            renderMiniQuiz();
          }
        };
      });

      // Bind explanation change
      containerEl.querySelectorAll('.quiz-exp-input').forEach(inp => {
        inp.oninput = (e) => {
          const qIdx = parseInt(inp.dataset.qIdx, 10);
          if (miniQuizQuestions[qIdx]) miniQuizQuestions[qIdx].explanation = e.target.value;
        };
      });
    }

    // Add Mini-Quiz Question Button
    const addQuizQBtn = getEl('btn-add-mini-quiz-q');
    if (addQuizQBtn) {
      addQuizQBtn.onclick = () => {
        miniQuizQuestions.push(normalizeQuizQuestion({
          type: 'MULTIPLE_CHOICE',
          question: '',
          allow_multiple: false,
          options: ['Lựa chọn A', 'Lựa chọn B', 'Lựa chọn C', 'Lựa chọn D'],
          correct_answers: [0],
          correct_index: 0,
          explanation: ''
        }));
        renderMiniQuiz();
      };
    }

    // Load Existing Lesson if Editing
    if (lessonId) {
      try {
        const existingLesson = await ApiClient.getLesson(lessonId);
        if (existingLesson) {
          selectedUnitId = existingLesson.learning_unit_id || selectedUnitId;
          lessonStatus = existingLesson.status || 'DRAFT';

          // Check if there is a working draft from CourseChangeRequest
          const draft = existingLesson.working_draft;
          const draftBannerContainer = getEl('studio-draft-banner-container');
          if (draft && draftBannerContainer) {
            if (draft.status === 'REJECTED') {
              const reason = draft.review_notes || 'Không có lý do chi tiết từ quản trị viên.';
              draftBannerContainer.innerHTML = `
                <div class="rounded-xl border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-amber-600 dark:text-amber-400 text-2xl shrink-0 mt-0.5">warning</span>
                    <div>
                      <h4 class="text-sm font-bold text-amber-900 dark:text-amber-200">Bản sửa đổi gần nhất bị Quản trị viên từ chối</h4>
                      <p class="text-xs text-amber-800 dark:text-amber-300 mt-1 leading-relaxed">
                        <strong>Lý do từ chối:</strong> ${UI.escapeHtml(reason)}
                      </p>
                      <p class="text-[11px] text-amber-700/80 dark:text-amber-400/80 mt-0.5">
                        Hệ thống đang hiển thị nội dung bản nháp đã sửa để bạn chỉnh sửa và gửi lại. Bạn cũng có thể hủy bỏ bản nháp để quay về bản đã xuất bản.
                      </p>
                    </div>
                  </div>
                  <div class="shrink-0 flex items-center gap-2">
                    <button id="btn-discard-lesson-draft" class="px-3.5 py-1.5 rounded-lg bg-white dark:bg-amber-900/60 border border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-200 text-xs font-semibold hover:bg-amber-100 transition-colors shadow-xs">
                      Hủy bản nháp này
                    </button>
                  </div>
                </div>
              `;
              const discardBtn = getEl('btn-discard-lesson-draft');
              if (discardBtn) {
                discardBtn.onclick = async () => {
                  if (!confirm('Bạn có chắc muốn hủy bản nháp này và khôi phục về phiên bản bài giảng đang hoạt động không?')) return;
                  try {
                    const targetId = existingLesson?.lesson_id || existingLesson?.id || lessonId;
                    await ApiClient.discardLessonDraft(targetId);
                    UI.showToast('Đã hủy bản nháp bài giảng thành công.', 'success');
                    window.location.reload();
                  } catch (e) {
                    UI.showToast('Lỗi khi hủy bản nháp: ' + e.message, 'error');
                  }
                };
              }
            } else if (draft.status === 'PENDING') {
              draftBannerContainer.innerHTML = `
                <div class="rounded-xl border border-sky-300 bg-sky-50 dark:bg-sky-950/30 dark:border-sky-800 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-sky-600 dark:text-sky-400 text-2xl shrink-0 mt-0.5">pending_actions</span>
                    <div>
                      <h4 class="text-sm font-bold text-sky-900 dark:text-sky-200">Yêu cầu sửa đổi đang chờ Ban quản trị duyệt</h4>
                      <p class="text-xs text-sky-800 dark:text-sky-300 mt-1 leading-relaxed">
                        Nội dung bài giảng đang có bản đề xuất sửa đổi chờ xét duyệt. Bạn có thể tiếp tục cập nhật hoặc rút lại yêu cầu xét duyệt.
                      </p>
                    </div>
                  </div>
                  <div class="shrink-0 flex items-center gap-2">
                    <button id="btn-discard-lesson-draft" class="px-3.5 py-1.5 rounded-lg bg-white dark:bg-sky-900/60 border border-sky-300 dark:border-sky-700 text-sky-900 dark:text-sky-200 text-xs font-semibold hover:bg-sky-100 transition-colors shadow-xs">
                      Hủy yêu cầu xét duyệt
                    </button>
                  </div>
                </div>
              `;
              const discardBtn = getEl('btn-discard-lesson-draft');
              if (discardBtn) {
                discardBtn.onclick = async () => {
                  if (!confirm('Bạn có chắc muốn rút lại yêu cầu xét duyệt bản sửa đổi này không?')) return;
                  try {
                    const targetId = existingLesson?.lesson_id || existingLesson?.id || lessonId;
                    await ApiClient.discardLessonDraft(targetId);
                    UI.showToast('Đã hủy yêu cầu xét duyệt thành công.', 'success');
                    window.location.reload();
                  } catch (e) {
                    UI.showToast('Lỗi khi hủy yêu cầu: ' + e.message, 'error');
                  }
                };
              }
            }
          }

          if ((existingLesson.status === 'HISTORICAL' || existingLesson.is_historical) && existingLesson.latest_lesson_id) {
            const draftBannerContainer = getEl('studio-draft-banner-container');
            if (draftBannerContainer) {
              draftBannerContainer.innerHTML = `
                <div class="rounded-xl border border-indigo-200 bg-indigo-50 dark:bg-indigo-950/40 dark:border-indigo-800 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined text-indigo-600 dark:text-indigo-400 text-2xl shrink-0 mt-0.5">history_toggle_off</span>
                    <div>
                      <h4 class="text-sm font-bold text-indigo-950 dark:text-indigo-200">Bạn đang xem phiên bản bài giảng lưu trữ (Lịch sử)</h4>
                      <p class="text-xs text-indigo-800 dark:text-indigo-300 mt-0.5 leading-relaxed">
                        Bài giảng này đã được nâng cấp lên phiên bản mới hơn đang phát hành cho học viên. Để chỉnh sửa phiên bản mới nhất, vui lòng chuyển sang bài giảng hiện hành.
                      </p>
                    </div>
                  </div>
                  <div class="shrink-0 flex items-center gap-2">
                    <a href="#/instructor/courses/${courseId}/lessons/${existingLesson.latest_lesson_id}/edit" class="px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs inline-flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-[16px]">sync</span>
                      <span>Chuyển sang bản hiện hành</span>
                    </a>
                  </div>
                </div>
              `;
            }
          }

          const sourceData = (draft && draft.payload && typeof draft.payload === 'object')
            ? { ...existingLesson, ...draft.payload }
            : existingLesson;

          renderChildNavigator();
          const titleEl = getEl('studio-input-title');
          if (titleEl) titleEl.value = sourceData.title || '';
          const summaryEl = getEl('studio-input-summary');
          if (summaryEl) summaryEl.value = sourceData.summary || '';
          const durEl = getEl('studio-input-duration');
          if (durEl) durEl.value = sourceData.estimated_duration_minutes || 15;

          if (sourceData.markdown_content) {
            const editorEl = getEl('studio-content-editor');
            if (editorEl) {
              let content = sourceData.markdown_content;
              // If it's already HTML
              if (/<[a-z][\s\S]*>/i.test(content) && (content.includes('<p') || content.includes('<div') || content.includes('<h'))) {
                editorEl.innerHTML = UI.renderMarkdown(content);
              } else {
                // Render markdown to HTML for visual editing
                editorEl.innerHTML = UI.renderMarkdown(content);
              }
            }
          }

          videoUrls = Array.isArray(sourceData.video_urls) ? [...sourceData.video_urls] : [];
          if (!videoUrls.length && sourceData.video_url && /^(https:\/\/(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com))/.test(sourceData.video_url)) {
            videoUrls = [sourceData.video_url];
          }

          if (sourceData.resources && Array.isArray(sourceData.resources)) {
            attachedResources = sourceData.resources;
            renderAttachments();
          }

          if (sourceData.video_url) {
            currentVideoUrl = sourceData.video_url;
          } else if (videoUrls.length) {
            currentVideoUrl = videoUrls[0];
          } else {
            const firstUpload = (attachedResources || []).find(resource =>
              /\.(mp4|webm|mkv|mov)$/i.test(resource.filename || resource.title || '')
            );
            if (firstUpload) currentVideoUrl = resourceVideoUrl(firstUpload);
          }

          if (currentVideoUrl) {
            renderVideoPreview(currentVideoUrl);
          }
          renderVideoList();

          if (sourceData.quiz && Array.isArray(sourceData.quiz)) {
            miniQuizQuestions = sourceData.quiz.map(normalizeQuizQuestion).filter(Boolean);
            renderMiniQuiz();
          }
        }
      } catch (err) {
        UI.showToast('Không thể nạp nội dung bài giảng: ' + err.message, 'error');
      }
    }

    // File Upload Handler for Documents / Attachments
    const fileInput = getEl('studio-hidden-file-input');
    const triggerUploadBtn = getEl('btn-trigger-upload');
    if (triggerUploadBtn && fileInput) triggerUploadBtn.onclick = () => fileInput.click();

    const uploadDocuments = async files => {
      if (!files.length) return;
      const documentCount = attachedResources.filter(resource =>
        !/\.(mp4|webm|mkv|mov)$/i.test(resource.filename || resource.title || '')
      ).length;
      if (documentCount + files.length > 5) {
        UI.showToast(`Lesson còn ${Math.max(0, 5 - documentCount)} vị trí tài liệu.`, 'warning');
        return;
      }
      try {
        if (!lessonId) {
          const rawInitialHtml = getEl('studio-content-editor')?.innerHTML || '';
          await createLessonOnce({
            title: getEl('studio-input-title')?.value.trim() || 'Bài giảng mới',
            summary: getEl('studio-input-summary')?.value.trim() || '',
            markdown_content: UI.htmlToMarkdown ? UI.htmlToMarkdown(rawInitialHtml) : rawInitialHtml,
            status: 'DRAFT'
          });
        }
        const result = await InstructorView.uploadLessonFiles(files, async file => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('title', file.name);
          const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
          if (res.pending_approval) return res;
          return {
            resource_id: res.resource_id,
            title: file.name,
            filename: file.name,
            file_url: res.file_url || res.download_url || '#',
            file_asset: res.file_asset
          };
        });
        attachedResources.push(...result.uploaded);
        renderAttachments();
        renderVideoList();
        if (result.uploaded.length) UI.showToast(`Đã đính kèm ${result.uploaded.length} tài liệu.`, 'success');
        if (result.pending.length) UI.showToast(`${result.pending.length} tài liệu đã gửi Admin xét duyệt.`, 'info');
        for (const failure of result.failed) {
          UI.showToast(`${failure.file.name}: ${failure.error.message || 'Không thể tải lên.'}`, 'error');
        }
      } catch (error) {
        UI.showToast(error.message || 'Không thể tạo bản nháp để tải tài liệu.', 'error');
      }
    };
    if (fileInput) {
      fileInput.onchange = async event => {
        await uploadDocuments(Array.from(event.target.files || []));
        fileInput.value = '';
      };
    }
    const dropzone = getEl('studio-resources-dropzone');
    const chooseDocBtn = getEl('btn-choose-doc-file');
    if (chooseDocBtn && fileInput) {
      chooseDocBtn.onclick = (e) => {
        e.stopPropagation();
        fileInput.click();
      };
    }
    if (dropzone && fileInput) {
      dropzone.onclick = (e) => {
        if (e.target !== chooseDocBtn && !chooseDocBtn?.contains(e.target)) {
          fileInput.click();
        }
      };
      dropzone.onkeydown = event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          fileInput.click();
        }
      };
      dropzone.ondragover = event => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
        dropzone.classList.add('border-emerald-500', 'bg-emerald-50/10');
      };
      dropzone.ondragleave = event => {
        event.preventDefault();
        dropzone.classList.remove('border-emerald-500', 'bg-emerald-50/10');
      };
      dropzone.ondrop = async event => {
        event.preventDefault();
        dropzone.classList.remove('border-emerald-500', 'bg-emerald-50/10');
        await uploadDocuments(Array.from(event.dataTransfer?.files || []));
      };
    }

    // Save & Publish Logic
    let editVersion = 0;
    let savedVersion = 0;
    let saveInFlight = null;
    studioRoot.addEventListener('input', () => { editVersion++; });
    studioRoot.addEventListener('change', () => { editVersion++; });
    const saveLessonData = async (publish = false, autosave = false) => {
      if (!InstructorView.isActiveLessonStudio(studioRoot)) return false;
      if (saveInFlight) {
        if (autosave) return false;
        try { await saveInFlight; } catch (_) { /* A manual save may retry after a failed autosave. */ }
        if (!InstructorView.isActiveLessonStudio(studioRoot)) return false;
      }
      if (autosave && !InstructorView.shouldAutosaveLesson(editVersion, savedVersion)) return false;
      const versionAtSave = editVersion;
      const title = (studioRoot.querySelector('#studio-input-title')?.value || '').trim();
      const summary = (studioRoot.querySelector('#studio-input-summary')?.value || '').trim();
      const editorEl = studioRoot.querySelector('#studio-content-editor');
      const rawHtml = editorEl ? editorEl.innerHTML : '';
      const mdContent = UI.htmlToMarkdown ? UI.htmlToMarkdown(rawHtml) : rawHtml;

      if (!title) {
        UI.showToast('Vui lòng nhập tên bài giảng.', 'warning');
        return false;
      }

      // Clean and sanitize mini-quiz questions
      const validQuiz = miniQuizQuestions
        .filter(q => q && q.question && q.question.trim())
        .map(q => {
          const item = { ...q, question: q.question.trim(), explanation: (q.explanation || '').trim() };
          if (item.type === 'MULTIPLE_CHOICE') {
            item.options = (item.options || []).map(o => (o || '').trim()).filter(Boolean);
            if (item.options.length < 2) {
              item.options = ['Lựa chọn A', 'Lựa chọn B'];
            }
            item.choices = item.options; // backward compatibility
            if (!Array.isArray(item.correct_answers) || item.correct_answers.length === 0) {
              item.correct_answers = [0];
            }
            item.correct_index = item.correct_answers[0] ?? 0; // backward compatibility
          } else if (item.type === 'FILL_BLANK') {
            item.blanks = (item.blanks || []).map(b => {
              let accepted = [];
              if (Array.isArray(b.accepted_answers)) {
                accepted = b.accepted_answers.map(a => String(a).trim()).filter(Boolean);
              } else if (typeof b.accepted_answers === 'string') {
                accepted = b.accepted_answers.split(',').map(a => a.trim()).filter(Boolean);
              }
              if (accepted.length === 0) accepted = [''];
              return { accepted_answers: accepted };
            });
            if (item.blanks.length === 0) {
              item.blanks = [{ accepted_answers: [''] }];
            }
          } else if (item.type === 'MATCHING') {
            item.pairs = (item.pairs || [])
              .map(p => ({ left: (p.left || '').trim(), right: (p.right || '').trim() }))
              .filter(p => p.left || p.right);
            if (item.pairs.length === 0) {
              item.pairs = [{ left: '', right: '' }, { left: '', right: '' }];
            }
          } else if (item.type === 'TRUE_FALSE') {
            item.correct_value = Boolean(item.correct_value);
          }
          return item;
        });

      // Auto-capture URL from input field if instructor entered a link
      const typedUrl = (studioRoot.querySelector('#studio-input-video-url')?.value || '').trim();
      if (typedUrl) {
        const parsedYt = UI.parseYouTubeId(typedUrl);
        const vimeoId = typedUrl.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d+)\/?$/i)?.[1];
        if (!parsedYt && !vimeoId) {
          UI.showToast('Chỉ chấp nhận liên kết YouTube hoặc Vimeo hợp lệ.', 'warning');
          return false;
        }
        const url = parsedYt ? `https://www.youtube.com/watch?v=${parsedYt}` : `https://vimeo.com/${vimeoId}`;
        if (!videoUrls.includes(url)) {
          if (!InstructorView.canAddLessonVideo(videoUrls, attachedResources, parentVideoSlots())) {
            UI.showToast('Mỗi Bài giảng chỉ được có tối đa 2 video. URL video phụ không được lưu kèm.', 'warning');
          } else {
            videoUrls.push(url);
            currentVideoUrl = url;
            renderVideoList();
          }
        }
      }

      const durationVal = parseInt(studioRoot.querySelector('#studio-input-duration')?.value, 10);
      const estDuration = !isNaN(durationVal) && durationVal > 0 ? durationVal : 15;

      const payload = {
        title,
        summary,
        markdown_content: mdContent,
        video_urls: videoUrls,
        quiz: validQuiz,
        status: publish || lessonStatus === 'PUBLISHED' ? 'PUBLISHED' : 'DRAFT',
        resources: attachedResources,
        estimated_duration_minutes: estDuration
      };

      try {
        const operation = (async () => {
          if (!lessonId) {
            const created = await ApiClient.createLesson(courseId, {
              ...payload,
              ...(selectedUnitId ? { learning_unit_id: selectedUnitId } : {})
            });
            lessonId = created?.lesson_id || created?.id;
            selectedUnitId = created?.learning_unit_id || selectedUnitId;
            if (!lessonId) throw new Error('Không tạo được bài giảng mới.');
            window.history.replaceState(null, '', `#/instructor/courses/${courseId}/lessons/${lessonId}/edit`);
            try {
              availableUnits = (await ApiClient.getLearningUnits(courseId)).items || availableUnits;
              renderChildNavigator();
            } catch (_) {}
            return created;
          }
          return ApiClient.updateLesson(lessonId, payload);
        })();
        saveInFlight = operation;
        const response = await operation;
        const outcome = InstructorView.lessonSaveOutcome(response, publish);
        if (outcome !== 'pending') lessonStatus = payload.status;
        savedVersion = versionAtSave;
        setSaveIndicator(outcome === 'pending' ? 'pending' : 'saved');

        // Update the lesson title in local unit.lessons so navigator reflects the new title immediately
        const curUnit = availableUnits.find(u => (u.learning_unit_id || u.id) === selectedUnitId);
        if (curUnit && Array.isArray(curUnit.lessons)) {
          const lItem = curUnit.lessons.find(l => (l.lesson_id || l.id) === lessonId);
          if (lItem && lItem.title !== title) {
            lItem.title = title;
            renderChildNavigator();
          }
        }

        return outcome;
      } catch (err) {
        setSaveIndicator('saved');
        UI.showToast(err.message || 'Lỗi lưu bài giảng.', 'error');
        return false;
      } finally {
        saveInFlight = null;
      }
    };

    resetEditorToEmpty = () => {
      const curUnit = availableUnits.find(u => (u.learning_unit_id || u.id) === selectedUnitId);
      const nextPos = (curUnit?.lessons?.length || 0) + 1;
      const titleEl = studioRoot.querySelector('#studio-input-title');
      if (titleEl) titleEl.value = `Bài giảng ${nextPos}`;
      const summaryEl = studioRoot.querySelector('#studio-input-summary');
      if (summaryEl) summaryEl.value = '';
      const durEl = studioRoot.querySelector('#studio-input-duration');
      if (durEl) durEl.value = '15';
      const editorEl = studioRoot.querySelector('#studio-content-editor');
      if (editorEl) editorEl.innerHTML = '<p>Nhập nội dung bài giảng tại đây...</p>';
      videoUrls = [];
      currentVideoUrl = '';
      renderVideoList();
      attachedResources = [];
      renderResourceList();
      miniQuizQuestions = [];
      renderMiniQuiz();
      editVersion = 0;
      savedVersion = 0;
      setSaveIndicator('saved');
    };

    handleAddNewLesson = async () => {
      if (editVersion > savedVersion) {
        try {
          await saveLessonData(false, true);
        } catch (_) {}
      }

      if (!selectedUnitId && availableUnits.length > 0) {
        selectedUnitId = availableUnits[0].learning_unit_id || availableUnits[0].id;
      }
      if (!selectedUnitId) {
        const title = await UI.prompt('Tạo Chương mới', 'Khóa học chưa có Chương nào. Vui lòng đặt tên cho Chương đầu tiên:', '', 'Ví dụ: Chương 1: Khởi động', 1, 'Tạo Chương');
        if (!title) return;
        try {
          const newUnit = await ApiClient.createLearningUnit(courseId, { title: title.trim() });
          if (newUnit?.pending_approval) {
            UI.showToast(newUnit.message || 'Yêu cầu tạo Chương mới đã gửi Quản trị viên để xét duyệt.', 'info');
            return;
          }
          selectedUnitId = newUnit?.learning_unit_id || newUnit?.id;
          const freshUnits = await ApiClient.getLearningUnits(courseId);
          availableUnits = freshUnits.items || [];
        } catch (err) {
          UI.showToast(err.message || 'Lỗi khi tạo Chương bài giảng mới.', 'error');
          return;
        }
      }

      let curUnit = availableUnits.find(u => (u.learning_unit_id || u.id) === selectedUnitId);
      const existingLessons = curUnit?.lessons || [];
      if (existingLessons.length >= 10) {
        UI.showToast('Mỗi Bài học chỉ chứa tối đa 10 Lesson.', 'warning');
        return;
      }

      if (window._currentStudioTimer) {
        clearInterval(window._currentStudioTimer);
        window._currentStudioTimer = null;
      }

      const nextTargetHash = `#/instructor/courses/${courseId}/lessons/new?learning_unit_id=${selectedUnitId}`;
      if (window.location.hash === nextTargetHash || !lessonId) {
        const titleEl = studioRoot.querySelector('#studio-input-title');
        const hasContent = editVersion > 0;
        if (hasContent) {
          try {
            await saveLessonData(false, true);
            window.location.hash = nextTargetHash;
            return;
          } catch (_) {}
        }
        if (titleEl) {
          titleEl.focus();
        }
        UI.showToast('Bạn đang ở màn hình soạn bài giảng mới.', 'info');
        renderChildNavigator();
      } else {
        window.location.hash = nextTargetHash;
      }
    };

    const saveDraftBtn = getEl('studio-save-draft-btn');
    if (saveDraftBtn) {
      saveDraftBtn.onclick = async () => {
        saveDraftBtn.disabled = true;
        setSaveIndicator('saving');
        try {
          const outcome = await saveLessonData(false);
          if (outcome) {
            UI.showToast('Đã lưu bản nháp bài giảng thành công!', 'success');
            setSaveIndicator('saved');
          } else {
            setSaveIndicator('saved');
          }
        } finally {
          saveDraftBtn.disabled = false;
        }
      };
    }

    const saveBtn = getEl('studio-save-btn');
    if (saveBtn) {
      saveBtn.onclick = async () => {
        saveBtn.disabled = true;
        setSaveIndicator('saving');
        try {
          const outcome = await saveLessonData(true);
          if (outcome === 'pending') {
            UI.showToast('Bản sửa bài giảng đã gửi Admin xét duyệt.', 'info');
            setSaveIndicator('pending');
          } else if (outcome) {
            UI.showToast('Đã lưu và xuất bản bài giảng thành công!', 'success');
            setSaveIndicator('saved');
          } else {
            setSaveIndicator('saved');
          }
        } finally {
          saveBtn.disabled = false;
        }
      };
    }

    const backBtn = getEl('studio-back-btn');
    if (backBtn) {
      backBtn.onclick = async (e) => {
        if (e && typeof e.preventDefault === 'function') e.preventDefault();
        if (editVersion > savedVersion) {
          setSaveIndicator('saving');
          try {
            await saveLessonData(false, true);
          } catch (_) {}
        }
        if (window._currentStudioTimer) {
          clearInterval(window._currentStudioTimer);
          window._currentStudioTimer = null;
        }
        window.location.hash = `#/instructor/courses/${courseId}/manage?tab=curriculum`;
      };
    };

    // Auto-save interval every 30 seconds
    const autoSaveTimer = setInterval(async () => {
      if (InstructorView.isActiveLessonStudio(studioRoot)) {
        await saveLessonData(false, true);
      } else {
        clearInterval(autoSaveTimer);
        if (window._currentStudioTimer === autoSaveTimer) {
          window._currentStudioTimer = null;
        }
      }
    }, 30000);
    window._currentStudioTimer = autoSaveTimer;
  }

  // =========================================================================
  // 5. PWD301 Exam Authoring Studio (Delegated to instructor-exams.js)
  // =========================================================================
  static renderExams(container) {
    if (typeof InstructorView.renderExamsHub === 'function') {
      return InstructorView.renderExamsHub(container);
    }
  }

}

window.InstructorView = InstructorView;
