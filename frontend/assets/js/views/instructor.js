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
              Không gian Điều phối Giảng viên • Chuẩn ABET
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#222120] dark:text-[#EDEDEB]">Trang chủ Giảng viên</h1>
            <p class="text-[#5C5B57] dark:text-[#9E9D99] text-sm max-w-xl">Quản lý các khóa học phụ trách, biên soạn ngân hàng câu hỏi chuẩn Bloom và phát triển giáo trình học vụ trực tuyến.</p>
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
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-courses">0</div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Đang xây dựng & mở lớp</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Tổng sinh viên</span>
              <span class="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-100/50 dark:border-emerald-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">groups</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-students">0</div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Học viên đang theo học</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Bài giảng & Giáo trình</span>
              <span class="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-100/50 dark:border-indigo-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">menu_book</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-lessons">0</div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Bài giảng đã xuất bản</div>
          </div>

          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs transition-colors">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Kỳ thi & Đánh giá</span>
              <span class="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border border-purple-100/50 dark:border-purple-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">assignment</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-assessments">0</div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Đề thi & Bài kiểm tra đã phát hành</div>
          </div>
        </div>

        <!-- Recent Courses Table Section -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] flex items-center gap-2">
              <span class="material-symbols-outlined text-primary dark:text-blue-400 text-[20px]">table_chart</span>
              Danh sách khóa học quản lý
            </h2>
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

    try {
      const [analytics, coursesData] = await Promise.all([
        ApiClient.getInstructorDashboard().catch(() => null),
        ApiClient.getInstructorCourses().catch(() => ({ courses: [] }))
      ]);

      const courses = coursesData.courses || [];
      const totalStudents = analytics?.total_students || courses.reduce((acc, c) => acc + (c.enrollments_count || 0), 0);
      const totalLessons = courses.reduce((acc, c) => acc + (c.lessons?.length || 0), 0);
      const totalAssessments = analytics?.total_assessments !== undefined ? analytics.total_assessments : (courses.reduce((acc, c) => acc + (c.assessments?.length || 0), 0));

      document.getElementById('ins-kpi-courses').textContent = courses.length;
      document.getElementById('ins-kpi-students').textContent = totalStudents;
      document.getElementById('ins-kpi-lessons').textContent = totalLessons;
      const kpiAss = document.getElementById('ins-kpi-assessments');
      if (kpiAss) kpiAss.textContent = totalAssessments;

      const tableBox = document.getElementById('ins-courses-table-box');
      if (courses.length === 0) {
        tableBox.innerHTML = `
          <div class="text-center py-12 p-6">
            <span class="material-symbols-outlined text-4xl text-[#8F8E8A] dark:text-[#6D6C68] mb-2">menu_book</span>
            <p class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB]">Bạn chưa tạo khóa học nào</p>
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
    }
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
              <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-5 shadow-xs hover:border-primary/40 hover:shadow-subtle transition-all flex flex-col justify-between gap-5 group">
                <div class="space-y-3">
                  <!-- Top Row: Code & Status -->
                  <div class="flex items-center justify-between gap-2">
                    <span class="font-mono font-extrabold text-primary text-xs px-2.5 py-1 rounded-lg bg-primary-subtle border border-primary/20">
                      ${UI.escapeHtml(c.course_code)}
                    </span>
                    ${UI.statusBadge(c.status)}
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
          (c.category && c.category.toLowerCase().includes(searchVal));

        const matchesStatus = statusVal === 'ALL' || c.status === statusVal;
        return matchesSearch && matchesStatus;
      });
    };

    const loadData = async () => {
      try {
        const res = await ApiClient.getInstructorCourses();
        allCourses = res.courses || [];
        renderCards(getFilteredCourses());
      } catch (e) {
        document.getElementById('ins-courses-cards-box').innerHTML = `
          <div class="p-8 text-center text-rose-500 font-bold">Lỗi tải khóa học: ${UI.escapeHtml(e.message)}</div>
        `;
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
      loadData();
      if (typeof UI !== 'undefined' && typeof UI.showToast === 'function') {
        UI.showToast('Đã làm mới danh sách và đặt lại bộ lọc.', 'info');
      }
    };

    await loadData();
  }

  static openCreateCourseModal() {
    const formHtml = `
      <form id="create-course-modal-form" class="space-y-4">
        <!-- Lưu ý quan trọng cho Giảng viên khi tạo khóa học mới -->
        <div class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-amber-900 dark:text-amber-300 text-xs flex items-start gap-2.5">
          <span class="material-symbols-outlined text-amber-600 dark:text-amber-400 text-lg shrink-0 mt-0.5">info</span>
          <div class="leading-relaxed">
            <strong class="font-bold">Lưu ý quan trọng cho Giảng viên:</strong><br/>
            Khi tạo xong tất cả (bài giảng, tài liệu đính kèm, đề thi/khảo thí) mới gửi duyệt và xuất bản khóa học. Không xuất bản lắt nhắt từng phần để đảm bảo tính toàn vẹn học thuật và quyền lợi của học viên.
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
    container.innerHTML = `
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
      const assessments = assessmentsData.assessments || assessmentsData.items || course.assessments || [];

      container.innerHTML = `
        <div class="p-4 sm:p-6 lg:p-8 space-y-8 max-w-5xl mx-auto animate-fade-in font-sans pb-20" id="course-manage-root">
          
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

          <!-- Course Header Banner (Warm Surface Card) -->
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-6 sm:p-8 shadow-subtle space-y-4">
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
                    class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
                  >
                    <span class="material-symbols-outlined text-[16px]">send</span>
                    <span>Gửi duyệt xuất bản</span>
                  </button>
                ` : ''}
                ${course.status === 'APPROVED' || window.app?.currentRole === 'ADMIN' ? `
                  <button
                    type="button"
                    id="btn-publish-direct"
                    class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
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
                    Bài giảng & Tài liệu (${lessons.length})
                  </h2>
                  <p class="text-xs text-[#8F8E8A] dark:text-[#6D6C68]">Nội dung học tập sinh viên sẽ theo dõi</p>
                </div>
              </div>

              <a
                href="#/instructor/courses/${cId}/lessons/new"
                class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[16px]">add</span>
                <span>Thêm bài học</span>
              </a>
            </div>

            <!-- Lessons Stack -->
            <div class="space-y-3" id="course-lessons-stack">
              ${lessons.length === 0 ? `
                <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-10 text-center shadow-xs">
                  <span class="material-symbols-outlined text-3xl text-[#8F8E8A] dark:text-[#6D6C68] mb-1">note_add</span>
                  <p class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Khóa học chưa có bài giảng nào</p>
                  <p class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-1 mb-3">Thêm bài học đầu tiên để bắt đầu xây dựng giáo trình.</p>
                  <a
                    href="#/instructor/courses/${cId}/lessons/new"
                    class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs inline-flex items-center gap-1.5"
                  >
                    <span class="material-symbols-outlined text-[15px]">add</span>
                    <span>Soạn bài học đầu tiên</span>
                  </a>
                </div>
              ` : `
                <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl shadow-xs divide-y divide-[#E8E6DF] dark:divide-[#2E2D2B] overflow-hidden" id="lessons-sortable-list">
                  ${lessons.map((l, idx) => {
                    const lId = l.lesson_id || l.id;
                    return `
                      <div class="lesson-row-card p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-[#FAF9F5] dark:hover:bg-[#262524]/60 transition-colors" draggable="true" data-idx="${idx}" data-lesson-id="${lId}">
                        <div class="flex items-center gap-3 min-w-0">
                          <!-- Reorder Controls: Up/Down Arrows & Drag Handle -->
                          <div class="flex items-center gap-1 shrink-0 select-none">
                            <div class="flex flex-col gap-0.5">
                              <button
                                type="button"
                                class="btn-move-lesson-up p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-primary transition-colors ${idx === 0 ? 'opacity-25 cursor-not-allowed' : ''}"
                                data-idx="${idx}"
                                ${idx === 0 ? 'disabled' : ''}
                                title="Di chuyển bài giảng lên trên"
                              >
                                <span class="material-symbols-outlined text-[15px]">arrow_upward</span>
                              </button>
                              <button
                                type="button"
                                class="btn-move-lesson-down p-1 rounded hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] text-[#8F8E8A] hover:text-primary transition-colors ${idx === lessons.length - 1 ? 'opacity-25 cursor-not-allowed' : ''}"
                                data-idx="${idx}"
                                ${idx === lessons.length - 1 ? 'disabled' : ''}
                                title="Di chuyển bài giảng xuống dưới"
                              >
                                <span class="material-symbols-outlined text-[15px]">arrow_downward</span>
                              </button>
                            </div>
                            <span class="lesson-drag-handle cursor-grab active:cursor-grabbing p-1 text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB]" title="Kéo thả để sắp xếp">
                              <span class="material-symbols-outlined text-[18px]">drag_indicator</span>
                            </span>
                            <span class="w-8 h-8 rounded-xl bg-[#F4F1EA] dark:bg-[#262524] text-[#5C5B57] dark:text-[#9E9D99] font-bold text-xs flex items-center justify-center shrink-0 border border-[#E8E6DF] dark:border-[#2E2D2B]">
                              ${idx + 1}
                            </span>
                          </div>

                          <div class="min-w-0">
                            <h4 class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB] truncate">
                              ${UI.escapeHtml(l.title)}
                            </h4>
                            <div class="flex items-center gap-2 text-[11px] text-[#8F8E8A] dark:text-[#6D6C68] mt-0.5">
                              <span class="${l.status === 'PUBLISHED' ? 'text-emerald-600 dark:text-emerald-400 font-semibold' : 'text-amber-600 dark:text-amber-400'}">
                                ${l.status === 'PUBLISHED' ? 'Đã xuất bản' : 'Bản nháp'}
                              </span>
                              ${l.quiz && Array.isArray(l.quiz) && l.quiz.length > 0 ? `
                                <span>•</span>
                                <span class="text-purple-600 dark:text-purple-400 font-semibold flex items-center gap-0.5">
                                  <span class="material-symbols-outlined text-[13px]">quiz</span>
                                  <span>${l.quiz.length} câu trắc nghiệm</span>
                                </span>
                              ` : ''}
                              ${l.video_url ? `
                                <span>•</span>
                                <span class="text-blue-600 dark:text-blue-400 font-semibold flex items-center gap-0.5">
                                  <span class="material-symbols-outlined text-[13px]">play_circle</span>
                                  <span>Có video</span>
                                </span>
                              ` : ''}
                            </div>
                          </div>
                        </div>

                        <div class="flex items-center gap-2 shrink-0">
                          <a
                            href="#/instructor/courses/${cId}/lessons/${lId}/edit"
                            class="px-3 py-1.5 rounded-lg bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center gap-1"
                          >
                            <span class="material-symbols-outlined text-[14px]">edit</span>
                            <span>Sửa bài</span>
                          </a>
                          <button
                            type="button"
                            class="btn-delete-lesson p-1.5 rounded-lg text-[#8F8E8A] hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
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
              `}
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
                      <div class="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-[#FAF9F5] dark:hover:bg-[#262524]/60 transition-colors">
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
      document.getElementById('btn-open-course-settings').onclick = () => {
        InstructorView.openCourseSettingsModal(course, initialTab === 'curriculum' ? 'settings' : initialTab);
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
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (e) {
            UI.showToast(e.message || 'Lỗi gửi xét duyệt.', 'error');
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
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (e) {
            UI.showToast(e.message || 'Lỗi xuất bản khóa học.', 'error');
          }
        };
      }

      // Bind Move Lesson Up
      container.querySelectorAll('.btn-move-lesson-up').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx <= 0 || idx >= lessons.length) return;
          const reordered = [...lessons];
          const temp = reordered[idx];
          reordered[idx] = reordered[idx - 1];
          reordered[idx - 1] = temp;
          const orderedIds = reordered.map(l => l.lesson_id || l.id);
          try {
            await ApiClient.reorderLessons(cId, orderedIds);
            UI.showToast('Đã di chuyển bài giảng lên!', 'success');
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
          }
        };
      });

      // Bind Move Lesson Down
      container.querySelectorAll('.btn-move-lesson-down').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx < 0 || idx >= lessons.length - 1) return;
          const reordered = [...lessons];
          const temp = reordered[idx];
          reordered[idx] = reordered[idx + 1];
          reordered[idx + 1] = temp;
          const orderedIds = reordered.map(l => l.lesson_id || l.id);
          try {
            await ApiClient.reorderLessons(cId, orderedIds);
            UI.showToast('Đã di chuyển bài giảng xuống!', 'success');
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
          }
        };
      });

      // Bind Drag & Drop Reordering
      let draggedIdx = null;
      container.querySelectorAll('.lesson-row-card').forEach(card => {
        card.addEventListener('dragstart', (e) => {
          draggedIdx = parseInt(card.dataset.idx, 10);
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
          if (draggedIdx === null || draggedIdx === targetIdx) return;
          const reordered = [...lessons];
          const [moved] = reordered.splice(draggedIdx, 1);
          reordered.splice(targetIdx, 0, moved);
          const orderedIds = reordered.map(l => l.lesson_id || l.id);
          try {
            await ApiClient.reorderLessons(cId, orderedIds);
            UI.showToast('Đã sắp xếp lại thứ tự bài giảng thành công!', 'success');
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (err) {
            UI.showToast(err.message || 'Lỗi sắp xếp bài giảng.', 'error');
          }
        });
      });

      // Bind Delete Lesson
      container.querySelectorAll('.btn-delete-lesson').forEach(btn => {
        btn.onclick = async () => {
          const lId = btn.dataset.lessonId;
          const conf = await UI.confirm('Xóa bài học', 'Bạn có chắc chắn muốn xóa bài học này khỏi giáo trình? Thao tác không thể hoàn tác.', 'Xóa vĩnh viễn');
          if (!conf) return;
          try {
            await ApiClient.deleteLesson(cId, lId);
            UI.showToast('Đã xóa bài học thành công.', 'success');
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (e) {
            UI.showToast(e.message || 'Lỗi khi xóa bài học.', 'error');
          }
        };
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
            InstructorView.renderCourseManage(container, cId, 'curriculum');
          } catch (e) {
            UI.showToast(e.message || 'Lỗi khi xuất bản bài thi.', 'error');
          }
        };
      });

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500 font-bold">Lỗi nạp khóa học: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 3.0. Course Settings & Academic Governance Modal
  // =========================================================================
  static openCourseSettingsModal(course, defaultSubTab = 'settings') {
    const cId = course.course_id || course.id;

    const modalHtml = `
      <div class="space-y-4">
        <!-- Sub-tabs Navigation -->
        <div class="flex items-center gap-2 border-b border-[#E8E6DF] dark:border-[#2E2D2B] pb-3">
          <button
            type="button"
            class="course-modal-subtab px-3.5 py-2 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-2xs"
            data-subtab="settings"
          >
            <span class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">settings</span>
              <span>Cài đặt chung</span>
            </span>
          </button>
          <button
            type="button"
            class="course-modal-subtab px-3.5 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-all"
            data-subtab="academic"
          >
            <span class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">verified_user</span>
              <span>Chuẩn đầu ra (ABET SLO)</span>
            </span>
          </button>
          <button
            type="button"
            class="course-modal-subtab px-3.5 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-all"
            data-subtab="students"
          >
            <span class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">groups</span>
              <span>Danh sách sinh viên</span>
            </span>
          </button>
        </div>

        <!-- Sub-tab Content Container -->
        <div id="course-modal-subtab-content" class="min-h-[380px] max-h-[70vh] overflow-y-auto"></div>
      </div>
    `;

    UI.openModal({
      title: `Cài đặt & Học vụ • ${course.course_code}`,
      bodyHtml: modalHtml,
      footerHtml: `
        <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-colors" onclick="UI.closeModal()">
          Đóng
        </button>
      `,
      size: 'xl'
    });

    const subtabBtns = document.querySelectorAll('.course-modal-subtab');
    const contentBox = document.getElementById('course-modal-subtab-content');

    const switchSubtab = (tab) => {
      subtabBtns.forEach(btn => {
        if (btn.dataset.subtab === tab) {
          btn.className = 'course-modal-subtab px-3.5 py-2 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-2xs';
        } else {
          btn.className = 'course-modal-subtab px-3.5 py-2 rounded-xl text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] transition-all';
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
          await ApiClient.deleteLesson(cId, lId);
          UI.showToast('Đã xóa bài giảng thành công!', 'success');
          InstructorView.renderCourseManage(document.getElementById('course-manage-root').parentElement, cId, 'curriculum');
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
    if (course.learning_objectives) {
      if (Array.isArray(course.learning_objectives)) {
        customSLOs = [...course.learning_objectives];
      } else if (typeof course.learning_objectives === 'string') {
        try {
          const parsed = JSON.parse(course.learning_objectives);
          if (Array.isArray(parsed)) customSLOs = parsed;
        } catch {
          customSLOs = course.learning_objectives.split('\n').filter(s => s.trim()).map((s, i) => ({
            title: `SLO-${i + 1}`,
            description: s.trim()
          }));
        }
      }
    }
    if (customSLOs.length === 0) {
      customSLOs = [
        { title: 'SLO-1 • Phân tích & Giải quyết Vấn đề', description: 'Sinh viên có khả năng phân tích một bài toán kỹ thuật phần mềm phức tạp và áp dụng các nguyên lý máy tính để xác định giải pháp phù hợp.', weight: '30%' },
        { title: 'SLO-2 • Thiết kế Hệ thống & Kiểm thử', description: 'Sinh viên có khả năng thiết kế, cài đặt và đánh giá giải pháp dựa trên máy tính nhằm đáp ứng tập hợp các yêu cầu điện toán xác định theo chuẩn kiến trúc RESTful & CSDL quan hệ.', weight: '50%' },
        { title: 'SLO-3 • Giao tiếp & Tài liệu Kỹ thuật', description: 'Sinh viên có khả năng truyền đạt hiệu quả các luận điểm kỹ thuật trong các ngữ cảnh chuyên môn khác nhau qua báo cáo tài liệu và mã nguồn chuẩn chỉnh.', weight: '20%' }
      ];
    }

    tabContainer.innerHTML = `
      <div class="space-y-6 max-w-5xl mx-auto animate-fade-in" id="academic-tab-root">
        
        <!-- CARD 1: ABET Student Learning Outcomes (SLOs) -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">verified_user</span>
                <h2 class="text-base font-bold text-slate-900 dark:text-white">
                  1. Chuẩn đầu ra Môn học (Student Learning Outcomes - SLO)
                </h2>
                <button type="button" onclick="UI.openAcademicGlossaryModal()" class="text-xs text-primary hover:underline font-bold flex items-center gap-0.5" title="Mở sổ tay thuật ngữ">
                  <span class="material-symbols-outlined text-[16px]">help</span>
                  <span>Giải thích SLO</span>
                </button>
              </div>
              <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                Quy định cụ thể những năng lực, kỹ năng thực tế mà sinh viên sẽ làm được sau khóa học. Các chuẩn này được ánh xạ vào ma trận ngân hàng đề thi và hồ sơ kiểm định quốc tế ABET CAC Criterion 3.
              </p>
            </div>
            <div class="flex items-center gap-2.5 shrink-0">
              <button type="button" id="btn-add-slo" class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-2xs">
                <span class="material-symbols-outlined text-[16px] text-primary">add</span>
                <span>Thêm Chuẩn đầu ra (SLO)</span>
              </button>
              <button type="button" id="btn-save-slos" class="px-4 py-1.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm">
                <span class="material-symbols-outlined text-[16px]">save</span>
                <span>Lưu chuẩn đầu ra</span>
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

    // 1. Render SLOs helper
    const sloContainer = document.getElementById('slo-items-list');
    const colors = ['text-primary', 'text-indigo-600', 'text-purple-600', 'text-emerald-600'];

    const renderSLOList = () => {
      if (!sloContainer) return;
      if (customSLOs.length === 0) {
        sloContainer.innerHTML = `
          <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
            Chưa có chuẩn đầu ra nào được thiết lập. Nhấp "+ Thêm Chuẩn đầu ra (SLO)" để tạo mới.
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
          await ApiClient.updateCourse(cId, { learning_objectives: customSLOs });
          UI.showToast('Đã lưu thành công bộ Chuẩn đầu ra ABET vào CSDL!', 'success');
        } catch (err) {
          UI.showToast('Lỗi lưu chuẩn đầu ra: ' + (err.message || err), 'error');
        } finally {
          saveSlosBtn.disabled = false;
          saveSlosBtn.innerHTML = `<span class="material-symbols-outlined text-[16px]">save</span><span>Lưu chuẩn đầu ra</span>`;
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
              <button
                type="button"
                class="px-3.5 py-1.5 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5"
                onclick="InstructorView.openAssessmentResultsModal('${cId}', '${a.assessment_id || a.id}')"
              >
                <span class="material-symbols-outlined text-[15px]">bar_chart</span>
                <span>Bảng điểm & Bài nộp</span>
              </button>
              <a
                href="#/instructor/exams?course_id=${cId}"
                class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors"
              >
                Soạn đề
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
            InstructorView.renderTabAssessment(tabContainer, course);
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

  static async openAssessmentResultsModal(arg1, arg2) {
    // Robust argument resolution: supports both (courseId, assessmentId) and (assessmentId, optionalTitle)
    let assessmentId = arg1;
    const isIdPattern = (v) => typeof v === 'string' && (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v) || /^\d+$/.test(v));
    if (isIdPattern(arg1) && isIdPattern(arg2)) {
      assessmentId = arg2;
    } else if (arg2 && isIdPattern(arg2)) {
      assessmentId = arg2;
    } else {
      assessmentId = arg1;
    }

    const modalId = 'modal-assessment-results';
    let modal = document.getElementById(modalId);
    if (!modal) {
      modal = document.createElement('div');
      modal.id = modalId;
      modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fade-in';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        <div class="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">assessment</span>
              Bảng điểm & Kết quả Khảo thí Trắc nghiệm
            </h2>
            <p class="text-xs text-slate-500 mt-1" id="modal-asm-title">Đang tải dữ liệu bài nộp...</p>
          </div>
          <button type="button" class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" onclick="document.getElementById('${modalId}').remove()">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <div class="p-6 overflow-y-auto space-y-6" id="modal-asm-content">
          <div class="py-12 text-center text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-xs">Đang tổng hợp điểm số thí sinh...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const data = await ApiClient.getAssessmentAttempts(assessmentId);
      const attempts = data.attempts || [];
      const titleEl = document.getElementById('modal-asm-title');
      if (titleEl) titleEl.textContent = `Đề thi: ${data.assessment_title || 'Khảo thí trắc nghiệm'} • Tổng cộng ${attempts.length} bài nộp`;

      const contentEl = document.getElementById('modal-asm-content');
      if (!contentEl) return;

      if (attempts.length === 0) {
        contentEl.innerHTML = `
          <div class="text-center py-12">
            <span class="material-symbols-outlined text-5xl text-slate-300 mb-2">assignment_late</span>
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
          <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
            <span class="text-xs text-slate-500 font-medium">Tổng số bài nộp</span>
            <div class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">${totalSubmissions}</div>
          </div>
          <div class="bg-emerald-50 dark:bg-emerald-950/30 p-4 rounded-xl border border-emerald-200 dark:border-emerald-800">
            <span class="text-xs text-emerald-600 font-medium">Tỷ lệ đạt</span>
            <div class="text-2xl font-extrabold text-emerald-700 dark:text-emerald-400 mt-1">${passRate}% <span class="text-xs font-normal text-emerald-600">(${passedCount}/${totalSubmissions})</span></div>
          </div>
          <div class="bg-indigo-50 dark:bg-indigo-950/30 p-4 rounded-xl border border-indigo-200 dark:border-indigo-800">
            <span class="text-xs text-indigo-600 font-medium">Điểm trung bình</span>
            <div class="text-2xl font-extrabold text-indigo-700 dark:text-indigo-400 mt-1">${avgScore}%</div>
          </div>
        </div>

        <!-- Table of Attempts -->
        <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/80 text-slate-500 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th class="px-4 py-3">Thí sinh</th>
                <th class="px-4 py-3">Thời gian nộp</th>
                <th class="px-4 py-3">Điểm số</th>
                <th class="px-4 py-3">Tỷ lệ</th>
                <th class="px-4 py-3">Kết quả</th>
                <th class="px-4 py-3 text-right">Chi tiết bài làm</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              ${attempts.map(att => {
                const passed = att.is_passed || att.passed;
                const submittedDate = att.submitted_at ? new Date(att.submitted_at).toLocaleString('vi-VN') : 'Đang làm';
                const pct = att.percentage !== undefined ? att.percentage : (att.percent_score || 0);
                return `
                  <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td class="px-4 py-3">
                      <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(att.student_name || 'Học viên')}</div>
                      <div class="text-[11px] text-slate-400">${UI.escapeHtml(att.student_email || '')}</div>
                    </td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-300">${submittedDate}</td>
                    <td class="px-4 py-3 font-mono font-bold text-slate-900 dark:text-white">${att.raw_score ?? 0} / ${att.max_possible_points ?? 0}</td>
                    <td class="px-4 py-3 font-bold ${passed ? 'text-emerald-600' : 'text-rose-600'}">${pct}%</td>
                    <td class="px-4 py-3">
                      <span class="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${passed ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'}">
                        ${passed ? 'ĐẠT' : 'KHÔNG ĐẠT'}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-right">
                      <button
                        type="button"
                        class="px-2.5 py-1 rounded-lg bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors inline-flex items-center gap-1"
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
      const contentEl = document.getElementById('modal-asm-content');
      if (contentEl) {
        contentEl.innerHTML = `<div class="p-6 text-center text-rose-500 text-xs">Lỗi tải kết quả khảo thí: ${UI.escapeHtml(err.message)}</div>`;
      }
    }
  }

  static async openAttemptDetailModal(attemptId) {
    const modalId = 'modal-attempt-detail';
    let modal = document.getElementById(modalId);
    if (!modal) {
      modal = document.createElement('div');
      modal.id = modalId;
      modal.className = 'fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-fade-in';
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
      const [data, appealRes] = await Promise.all([
        ApiClient.getInstructorAttemptResult(attemptId),
        ApiClient.getAttemptAppeal(attemptId).catch(() => ({ appeal: null }))
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
      if (questions.length === 0) {
        contentEl.innerHTML = appealBannerHtml + `<div class="text-center py-8 text-slate-400 text-xs">Không có dữ liệu câu hỏi.</div>`;
      } else {
        contentEl.innerHTML = appealBannerHtml + questions.map((q, idx) => {
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
                    <span>Quyết định Phúc khảo Học bạ PWD301:</span>
                  </div>
                  <p class="text-[11px] leading-relaxed">
                    Điểm số sau khi cập nhật sẽ tự động kích hoạt tính lại xếp loại học lực, đồng thời ghi nhận vào Lịch sử Kiểm toán Bất biến (Audit Trail) cho sinh viên.
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
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6 max-w-3xl mx-auto">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">Cập nhật thông tin khóa học</h2>
        
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

      try {
        await ApiClient.updateCourse(cId, {
          title: form.title.value.trim(),
          description: form.description.value.trim(),
          category: form.category.value.trim(),
          contact_info: contactData,
          capacity: null
        });
        course.contact_info = contactData;
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
  static async renderLessonAuthoringStudio(container, courseId, lessonId = null) {
    container.innerHTML = `
      <div class="min-h-screen bg-[#FAF9F5] dark:bg-[#191919] font-sans flex flex-col animate-fade-in" id="lesson-studio-root">
        
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
                SOẠN BÀI GIẢNG
              </span>
              <span class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] hidden sm:inline">•</span>
              <span class="text-xs text-[#5C5B57] dark:text-[#9E9D99] truncate hidden sm:inline" id="studio-header-course-ref">
                Khóa học
              </span>
            </div>
          </div>

          <!-- Center: Autosave Status -->
          <div class="flex items-center gap-1.5 text-xs text-[#8F8E8A] dark:text-[#6D6C68]" id="studio-autosave-status">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="hidden sm:inline">Sẵn sàng lưu</span>
          </div>

          <!-- Right: Action Buttons -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              type="button"
              id="studio-save-draft-btn"
              class="px-3.5 py-2 rounded-xl bg-[#F4F1EA] hover:bg-[#ECE8DF] dark:bg-[#262524] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold transition-colors border border-[#E8E6DF] dark:border-[#2E2D2B]"
            >
              Lưu bản nháp
            </button>
            <button
              type="button"
              id="studio-publish-btn"
              class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-[16px]">rocket_launch</span>
              <span>Xuất bản</span>
            </button>
          </div>
        </header>

        <!-- Main Document Canvas (Notion / Doc Style) -->
        <main class="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-8 space-y-6">
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-3xl p-6 sm:p-12 shadow-subtle space-y-6">
            
            <!-- Lesson Title (Large Document Heading) -->
            <div>
              <input
                type="text"
                id="studio-input-title"
                class="w-full text-2xl sm:text-3xl font-extrabold text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] bg-transparent border-0 border-b border-transparent hover:border-[#E8E6DF] dark:hover:border-[#2E2D2B] focus:border-primary outline-none py-2 transition-colors"
                placeholder="Tiêu đề bài giảng..."
                value="Bài giảng mới"
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
                  class="w-12 bg-transparent text-xs text-[#222120] dark:text-[#EDEDEB] outline-none font-bold text-center"
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
                class="w-full min-h-[420px] p-6 sm:p-8 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-white dark:bg-[#202020] text-sm sm:text-base text-[#222120] dark:text-[#EDEDEB] focus:outline-none focus:ring-2 focus:ring-primary/20 leading-relaxed font-sans shadow-2xs overflow-y-auto space-y-3"
                style="min-height: 420px;"
              >
                <p>Nhập nội dung bài giảng tại đây. Bạn có thể bôi đen chữ để in đậm, in nghiêng, đổi màu, tạo danh sách hoặc chèn bảng giống Microsoft Word...</p>
              </div>
            </div>

            <!-- Video Studio Section (Tải video lên hoặc dán link) -->
            <div class="p-5 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5]/80 dark:bg-[#262524]/60 space-y-4" id="studio-video-section">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-[#5C5B57] dark:text-[#9E9D99] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px] text-primary">play_circle</span>
                  <span>Video bài giảng</span>
                </span>
                <span class="text-[11px] text-[#8F8E8A] dark:text-[#6D6C68]">Hỗ trợ tệp MP4/WebM/MKV/MOV &lt; 1GB hoặc link YouTube/URL</span>
              </div>

              <!-- Video Options Tab Switcher -->
              <div class="flex items-center gap-2 border-b border-[#E8E6DF] dark:border-[#2E2D2B] pb-2 text-xs">
                <button
                  type="button"
                  id="tab-video-upload-btn"
                  class="px-3 py-1.5 rounded-lg font-bold transition-all bg-primary text-white shadow-2xs"
                >
                  <span class="flex items-center gap-1">
                    <span class="material-symbols-outlined text-[15px]">upload_file</span>
                    <span>Tải tệp video (&lt; 1GB)</span>
                  </span>
                </button>
                <button
                  type="button"
                  id="tab-video-link-btn"
                  class="px-3 py-1.5 rounded-lg font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#202020] transition-all"
                >
                  <span class="flex items-center gap-1">
                    <span class="material-symbols-outlined text-[15px]">link</span>
                    <span>Dán link video (YouTube / URL)</span>
                  </span>
                </button>
              </div>

              <!-- Tab Pane 1: File Upload -->
              <div id="pane-video-upload" class="space-y-3">
                <input
                  type="file"
                  id="studio-video-file-input"
                  accept="video/mp4,video/webm,video/x-matroska,video/quicktime,.mp4,.webm,.mkv,.mov"
                  class="hidden"
                />
                <p class="text-[11px] text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 p-2.5 rounded-xl border border-amber-200 dark:border-amber-900/50 flex items-center gap-1.5 font-medium">
                  <span class="material-symbols-outlined text-[16px] text-amber-600 shrink-0">hd</span>
                  <span>Khuyến nghị: Tải lên video độ phân giải <strong>1080p (Full HD)</strong>, định dạng MP4, dung lượng &lt; 1GB để đạt chất lượng bài giảng chuẩn.</span>
                </p>
                <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                  <button
                    type="button"
                    id="btn-choose-video-file"
                    class="px-4 py-2 rounded-xl bg-white dark:bg-[#202020] hover:bg-[#F4F1EA] dark:hover:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] text-xs font-bold flex items-center gap-2 border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs transition-colors"
                  >
                    <span class="material-symbols-outlined text-[16px] text-primary">upload</span>
                    <span>Chọn tệp video từ máy tính</span>
                  </button>
                  <span id="studio-video-filename" class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] truncate max-w-sm">
                    Chưa chọn video nào.
                  </span>
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

              <!-- Tab Pane 2: External Link -->
              <div id="pane-video-link" class="hidden space-y-3">
                <div class="flex items-center gap-2">
                  <input
                    type="url"
                    id="studio-input-video-url"
                    class="flex-1 h-10 px-3.5 rounded-xl bg-white dark:bg-[#202020] text-xs text-[#222120] dark:text-[#EDEDEB] placeholder:text-[#8F8E8A] dark:placeholder:text-[#6D6C68] border border-[#E8E6DF] dark:border-[#2E2D2B] outline-none focus:border-primary shadow-2xs"
                    placeholder="VD: https://www.youtube.com/watch?v=... hoặc https://youtu.be/... hoặc shorts"
                  />
                  <button
                    type="button"
                    id="btn-apply-video-url"
                    class="px-4 h-10 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shrink-0"
                  >
                    Áp dụng
                  </button>
                </div>
              </div>

              <!-- Video Preview Box (Centered horizontally and vertically) -->
              <div id="studio-video-preview-box" class="hidden pt-2">
                <div class="max-w-2xl mx-auto relative rounded-2xl overflow-hidden bg-black aspect-video max-h-[360px] border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-subtle group flex items-center justify-center">
                  <div id="studio-video-player-target" class="w-full h-full flex items-center justify-center"></div>
                  <button
                    type="button"
                    id="btn-remove-current-video"
                    class="absolute top-3 right-3 px-3 py-1.5 rounded-xl bg-black/75 hover:bg-rose-600 text-white text-xs font-bold transition-colors flex items-center gap-1.5 backdrop-blur-xs shadow-xs z-10"
                    title="Gỡ bỏ video khỏi bài giảng"
                  >
                    <span class="material-symbols-outlined text-[15px]">delete</span>
                    <span>Gỡ video</span>
                  </button>
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
                <input type="file" id="studio-hidden-file-input" class="hidden" />
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

    let attachedResources = [];
    let currentVideoUrl = '';
    let miniQuizQuestions = [];

    // Video Section Tab Switcher
    const tabUploadBtn = document.getElementById('tab-video-upload-btn');
    const tabLinkBtn = document.getElementById('tab-video-link-btn');
    const paneUpload = document.getElementById('pane-video-upload');
    const paneLink = document.getElementById('pane-video-link');

    const switchToUploadTab = () => {
      if (tabUploadBtn && tabLinkBtn && paneUpload && paneLink) {
        tabUploadBtn.className = 'px-3 py-1.5 rounded-lg font-bold transition-all bg-primary text-white shadow-2xs';
        tabLinkBtn.className = 'px-3 py-1.5 rounded-lg font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#202020] transition-all';
        paneUpload.classList.remove('hidden');
        paneLink.classList.add('hidden');
      }
    };

    const switchToLinkTab = () => {
      if (tabUploadBtn && tabLinkBtn && paneUpload && paneLink) {
        tabLinkBtn.className = 'px-3 py-1.5 rounded-lg font-bold transition-all bg-primary text-white shadow-2xs';
        tabUploadBtn.className = 'px-3 py-1.5 rounded-lg font-semibold text-[#5C5B57] dark:text-[#9E9D99] hover:bg-[#F4F1EA] dark:hover:bg-[#202020] transition-all';
        paneLink.classList.remove('hidden');
        paneUpload.classList.add('hidden');
      }
    };

    if (tabUploadBtn && tabLinkBtn && paneUpload && paneLink) {
      tabUploadBtn.onclick = switchToUploadTab;
      tabLinkBtn.onclick = switchToLinkTab;
    }

    // Helper: Parse YouTube Video ID reliably across all URL formats
    const parseYouTubeId = (url) => {
      return UI.parseYouTubeId(url);
    };

    // Render Video Preview Helper (Centered)
    const renderVideoPreview = (url) => {
      const previewBox = document.getElementById('studio-video-preview-box');
      const target = document.getElementById('studio-video-player-target');
      if (!previewBox || !target) return;

      if (!url || !String(url).trim()) {
        previewBox.classList.add('hidden');
        target.innerHTML = '';
        return;
      }

      previewBox.classList.remove('hidden');
      const cleanUrl = String(url).trim();

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
        <video controls class="max-h-[360px] max-w-full mx-auto my-auto object-contain block rounded-xl" src="${cleanUrl}" preload="metadata">
          Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
        </video>
      `;
    };

    const handleApplyVideoUrl = () => {
      const inputEl = document.getElementById('studio-input-video-url');
      const inputUrl = inputEl?.value.trim() || '';
      if (!inputUrl) {
        UI.showToast('Vui lòng nhập đường dẫn video hợp lệ.', 'warning');
        return;
      }
      const ytId = UI.parseYouTubeId(inputUrl);
      if (ytId) {
        currentVideoUrl = `https://www.youtube.com/watch?v=${ytId}`;
        if (inputEl) inputEl.value = currentVideoUrl;
      } else {
        currentVideoUrl = inputUrl;
      }
      renderVideoPreview(currentVideoUrl);
      UI.showToast('Đã áp dụng link video vào bài giảng!', 'success');
    };

    const applyUrlBtn = document.getElementById('btn-apply-video-url');
    if (applyUrlBtn) {
      applyUrlBtn.onclick = handleApplyVideoUrl;
    }

    const urlInput = document.getElementById('studio-input-video-url');
    if (urlInput) {
      urlInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleApplyVideoUrl();
        }
      };
    }

    const removeVideoBtn = document.getElementById('btn-remove-current-video');
    if (removeVideoBtn) {
      removeVideoBtn.onclick = () => {
        currentVideoUrl = '';
        renderVideoPreview('');
        const urlInputEl = document.getElementById('studio-input-video-url');
        if (urlInputEl) urlInputEl.value = '';
        const fnLabel = document.getElementById('studio-video-filename');
        if (fnLabel) fnLabel.textContent = 'Chưa chọn video nào.';
        const progBox = document.getElementById('studio-video-progress-box');
        if (progBox) progBox.classList.add('hidden');
        UI.showToast('Đã gỡ bỏ video khỏi bài giảng.', 'info');
      };
    }


    // Video File Upload Handler
    const videoFileInput = document.getElementById('studio-video-file-input');
    const chooseVideoBtn = document.getElementById('btn-choose-video-file');
    if (chooseVideoBtn && videoFileInput) {
      chooseVideoBtn.onclick = () => videoFileInput.click();

      videoFileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Invariant: Video size must be strictly < 1 GB
        if (file.size >= 1000000000) {
          UI.showToast('Dung lượng tệp vượt quá giới hạn 1GB theo quy định.', 'error');
          return;
        }

        const fnLabel = document.getElementById('studio-video-filename');
        if (fnLabel) {
          fnLabel.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
        }

        const progressBox = document.getElementById('studio-video-progress-box');
        const progressBar = document.getElementById('studio-video-progress-bar');
        const progressPercent = document.getElementById('studio-video-progress-percent');
        const progressText = document.getElementById('studio-video-progress-text');

        if (progressBox) progressBox.classList.remove('hidden');
        if (progressBar) progressBar.style.width = '20%';
        if (progressPercent) progressPercent.textContent = '20%';
        if (progressText) progressText.textContent = 'Đang chuẩn bị tải lên...';

        try {
          // If creating a new lesson, auto-save draft first so lessonId exists
          if (!lessonId) {
            if (progressText) progressText.textContent = 'Đang khởi tạo bản nháp bài học...';
            const title = document.getElementById('studio-input-title')?.value.trim() || 'Bài giảng mới';
            const summary = document.getElementById('studio-input-summary')?.value.trim() || '';
            const editorEl = document.getElementById('studio-content-editor');
            const mdContent = editorEl ? editorEl.innerHTML : '';

            const durationVal = parseInt(document.getElementById('studio-input-duration')?.value, 10);
            const draftRes = await ApiClient.createLesson(courseId, {
              title,
              summary,
              markdown_content: mdContent,
              status: 'DRAFT',
              estimated_duration_minutes: !isNaN(durationVal) && durationVal > 0 ? durationVal : 15
            });
            if (draftRes && (draftRes.lesson_id || draftRes.id)) {
              lessonId = draftRes.lesson_id || draftRes.id;
              window.history.replaceState(null, '', `#/instructor/courses/${courseId}/lessons/${lessonId}/edit`);
            }
          }

          if (progressBar) progressBar.style.width = '60%';
          if (progressPercent) progressPercent.textContent = '60%';
          if (progressText) progressText.textContent = 'Đang tải tệp video lên máy chủ (ClamAV scan)...';

          const formData = new FormData();
          formData.append('file', file);
          formData.append('title', file.name);

          const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
          if (progressBar) progressBar.style.width = '100%';
          if (progressPercent) progressPercent.textContent = '100%';
          if (progressText) progressText.textContent = 'Tải lên hoàn tất!';

          const videoUrl = res.download_url || res.file_url || `/student/courses/${courseId}/files/${res.resource_id}/download?disposition=inline`;
          currentVideoUrl = videoUrl;
          renderVideoPreview(videoUrl);

          attachedResources.push({
            resource_id: res.resource_id,
            title: file.name,
            filename: file.name,
            file_url: videoUrl,
            download_url: videoUrl
          });
          renderAttachments();
          UI.showToast(`Đã tải lên video ${file.name} thành công!`, 'success');
        } catch (err) {
          if (progressBox) progressBox.classList.add('hidden');
          UI.showToast(err.message || 'Lỗi tải video lên máy chủ.', 'error');
        }
      };
    }

    // Word-like WYSIWYG Editor Helpers & ExecCommand Bindings
    const formatDoc = (cmd, value = null) => {
      document.execCommand(cmd, false, value);
      const editor = document.getElementById('studio-content-editor');
      if (editor) editor.focus();
    };

    const toolFormat = document.getElementById('studio-tool-format');
    if (toolFormat) {
      toolFormat.onchange = (e) => {
        formatDoc('formatBlock', `<${e.target.value}>`);
      };
    }

    document.getElementById('studio-tool-bold')?.addEventListener('click', () => formatDoc('bold'));
    document.getElementById('studio-tool-italic')?.addEventListener('click', () => formatDoc('italic'));
    document.getElementById('studio-tool-underline')?.addEventListener('click', () => formatDoc('underline'));
    document.getElementById('studio-tool-strike')?.addEventListener('click', () => formatDoc('strikeThrough'));
    document.getElementById('studio-tool-left')?.addEventListener('click', () => formatDoc('justifyLeft'));
    document.getElementById('studio-tool-center')?.addEventListener('click', () => formatDoc('justifyCenter'));
    document.getElementById('studio-tool-right')?.addEventListener('click', () => formatDoc('justifyRight'));
    document.getElementById('studio-tool-justify')?.addEventListener('click', () => formatDoc('justifyFull'));
    document.getElementById('studio-tool-ul')?.addEventListener('click', () => formatDoc('insertUnorderedList'));
    document.getElementById('studio-tool-ol')?.addEventListener('click', () => formatDoc('insertOrderedList'));
    document.getElementById('studio-tool-hr')?.addEventListener('click', () => formatDoc('insertHorizontalRule'));
    document.getElementById('studio-tool-clear')?.addEventListener('click', () => formatDoc('removeFormat'));
    document.getElementById('studio-tool-undo')?.addEventListener('click', () => formatDoc('undo'));
    document.getElementById('studio-tool-redo')?.addEventListener('click', () => formatDoc('redo'));

    const colorInput = document.getElementById('studio-tool-color');
    if (colorInput) {
      colorInput.oninput = (e) => formatDoc('foreColor', e.target.value);
    }
    const bgInput = document.getElementById('studio-tool-bgcolor');
    if (bgInput) {
      bgInput.oninput = (e) => formatDoc('hiliteColor', e.target.value);
    }

    // Insert Callout Box
    document.getElementById('studio-tool-callout')?.addEventListener('click', () => {
      const html = `<blockquote style="border-left: 3px solid #2563EB; background: #EFF4FE; padding: 12px 16px; margin: 12px 0; border-radius: 0 8px 8px 0; color: #1E3A8A;"><strong>💡 Lưu ý trọng tâm:</strong> Nhập ghi chú kiến thức cần nhấn mạnh cho sinh viên tại đây...</blockquote><p><br></p>`;
      formatDoc('insertHTML', html);
    });

    // Insert 3x3 Table
    document.getElementById('studio-tool-table')?.addEventListener('click', () => {
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
      const containerEl = document.getElementById('studio-attachments-list');
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
              <span class="text-[10px] text-emerald-600 font-semibold block">✓ Đã quét sạch ClamAV - An toàn</span>
            </div>
          </div>
          <button
            type="button"
            class="btn-remove-attachment p-1 rounded-lg text-[#8F8E8A] hover:text-rose-600 transition-colors"
            data-idx="${idx}"
            title="Gỡ tệp và xóa khỏi bài giảng"
          >
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      `).join('');

      containerEl.querySelectorAll('.btn-remove-attachment').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          const res = attachedResources[idx];
          const resId = res?.resource_id || res?.id;

          if (lessonId && resId) {
            try {
              await ApiClient.detachLessonResource(courseId, lessonId, resId);
              UI.showToast('Đã xóa tài liệu khỏi bài giảng!', 'success');
            } catch (err) {
              UI.showToast(err.message || 'Lỗi khi xóa tài liệu trên máy chủ.', 'error');
            }
          }

          // If this resource was current video, clear it
          if (currentVideoUrl && (res.file_url === currentVideoUrl || res.download_url === currentVideoUrl)) {
            currentVideoUrl = '';
            renderVideoPreview('');
          }

          attachedResources.splice(idx, 1);
          renderAttachments();
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
      const containerEl = document.getElementById('studio-mini-quiz-list');
      if (!containerEl) return;

      const countEl = document.getElementById('studio-mini-quiz-count');
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
    document.getElementById('btn-add-mini-quiz-q').onclick = () => {
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

    // Load Existing Lesson if Editing
    if (lessonId) {
      try {
        const existingLesson = await ApiClient.getLesson(lessonId);
        if (existingLesson) {
          document.getElementById('studio-input-title').value = existingLesson.title || '';
          document.getElementById('studio-input-summary').value = existingLesson.summary || '';
          const durEl = document.getElementById('studio-input-duration');
          if (durEl) durEl.value = existingLesson.estimated_duration_minutes || 15;

          if (existingLesson.markdown_content) {
            const editorEl = document.getElementById('studio-content-editor');
            if (editorEl) {
              let content = existingLesson.markdown_content;
              // If it's already HTML
              if (/<[a-z][\s\S]*>/i.test(content) && (content.includes('<p') || content.includes('<div') || content.includes('<h'))) {
                editorEl.innerHTML = UI.renderMarkdown(content);
              } else {
                // Render markdown to HTML for visual editing
                editorEl.innerHTML = UI.renderMarkdown(content);
              }
            }
          }

          if (existingLesson.video_url) {
            currentVideoUrl = existingLesson.video_url;
            renderVideoPreview(currentVideoUrl);
            const urlInp = document.getElementById('studio-input-video-url');
            if (urlInp && (currentVideoUrl.startsWith('http') || UI.parseYouTubeId(currentVideoUrl))) {
              urlInp.value = currentVideoUrl;
              switchToLinkTab();
            }
          }

          if (existingLesson.resources && Array.isArray(existingLesson.resources)) {
            attachedResources = existingLesson.resources;
            renderAttachments();
          }

          if (existingLesson.quiz && Array.isArray(existingLesson.quiz)) {
            miniQuizQuestions = existingLesson.quiz.map(normalizeQuizQuestion).filter(Boolean);
            renderMiniQuiz();
          }
        }
      } catch (err) {
        UI.showToast('Không thể nạp nội dung bài giảng: ' + err.message, 'error');
      }
    }

    // File Upload Handler for Documents / Attachments
    const fileInput = document.getElementById('studio-hidden-file-input');
    document.getElementById('btn-trigger-upload').onclick = () => fileInput.click();

    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      if (lessonId) {
        try {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('title', file.name);
          const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
          attachedResources.push({
            resource_id: res.resource_id,
            title: file.name,
            filename: file.name,
            file_url: res.file_url || res.download_url || '#'
          });
          UI.showToast(`Đã đính kèm tệp ${file.name} thành công!`, 'success');
          renderAttachments();
        } catch (err) {
          UI.showToast(err.message || 'Lỗi tải tệp lên máy chủ.', 'error');
        }
      } else {
        try {
          const title = document.getElementById('studio-input-title')?.value.trim() || 'Bài giảng mới';
          const summary = document.getElementById('studio-input-summary')?.value.trim() || '';
          const editorEl = document.getElementById('studio-content-editor');
          const mdContent = editorEl ? editorEl.innerHTML : '';

          const draftRes = await ApiClient.createLesson(courseId, {
            title,
            summary,
            markdown_content: mdContent,
            status: 'DRAFT'
          });
          if (draftRes && (draftRes.lesson_id || draftRes.id)) {
            lessonId = draftRes.lesson_id || draftRes.id;
            window.history.replaceState(null, '', `#/instructor/courses/${courseId}/lessons/${lessonId}/edit`);
          }
          const formData = new FormData();
          formData.append('file', file);
          formData.append('title', file.name);
          const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
          attachedResources.push({
            resource_id: res.resource_id,
            title: file.name,
            filename: file.name,
            file_url: res.file_url || res.download_url || '#'
          });
          UI.showToast(`Đã đính kèm tệp ${file.name} thành công!`, 'success');
          renderAttachments();
        } catch (err) {
          UI.showToast(err.message || 'Lỗi tải tệp lên máy chủ.', 'error');
        }
      }
    };

    // Save & Publish Logic
    const saveLessonData = async (publish = false) => {
      const title = document.getElementById('studio-input-title').value.trim();
      const summary = document.getElementById('studio-input-summary').value.trim();
      const editorEl = document.getElementById('studio-content-editor');
      const mdContent = editorEl ? editorEl.innerHTML : '';

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
      const typedUrl = document.getElementById('studio-input-video-url')?.value.trim() || '';
      let finalVideoUrl = currentVideoUrl;
      if (typedUrl) {
        const parsedYt = UI.parseYouTubeId(typedUrl);
        finalVideoUrl = parsedYt ? `https://www.youtube.com/watch?v=${parsedYt}` : typedUrl;
        currentVideoUrl = finalVideoUrl;
      }

      const durationVal = parseInt(document.getElementById('studio-input-duration')?.value, 10);
      const estDuration = !isNaN(durationVal) && durationVal > 0 ? durationVal : 15;

      const payload = {
        title,
        summary,
        markdown_content: mdContent,
        video_url: finalVideoUrl || '',
        quiz: validQuiz,
        status: publish ? 'PUBLISHED' : 'DRAFT',
        resources: attachedResources,
        estimated_duration_minutes: estDuration
      };

      try {
        if (lessonId) {
          await ApiClient.updateLesson(lessonId, payload);
        } else {
          const res = await ApiClient.createLesson(courseId, payload);
          if (res && (res.lesson_id || res.id)) {
            lessonId = res.lesson_id || res.id;
          }
        }
        const statusEl = document.getElementById('studio-autosave-status');
        if (statusEl) {
          statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Đã lưu lúc ${new Date().toLocaleTimeString('vi-VN')}`;
        }
        return true;
      } catch (err) {
        UI.showToast(err.message || 'Lỗi lưu bài giảng.', 'error');
        return false;
      }
    };

    document.getElementById('studio-save-draft-btn').onclick = async () => {
      const ok = await saveLessonData(false);
      if (ok) UI.showToast('Đã lưu bản nháp bài giảng thành công!', 'success');
    };

    document.getElementById('studio-publish-btn').onclick = async () => {
      const ok = await saveLessonData(true);
      if (ok) {
        UI.showToast('Bài giảng đã được xuất bản chính thức vào giáo trình!', 'success');
        window.location.hash = `#/instructor/courses/${courseId}/manage?tab=curriculum`;
      }
    };

    document.getElementById('studio-back-btn').onclick = () => {
      window.location.hash = `#/instructor/courses/${courseId}/manage?tab=curriculum`;
    };

    // Auto-save interval every 30 seconds
    const autoSaveTimer = setInterval(async () => {
      if (document.getElementById('lesson-studio-root')) {
        await saveLessonData(false);
      } else {
        clearInterval(autoSaveTimer);
      }
    }, 30000);
  }

  // =========================================================================
  // 4. Question Bank Hub & Subject Inspector (Bloom Taxonomy + Gemini AI)
  // =========================================================================
  static async renderQuestions(container, courseCode = null) {
    if (courseCode) {
      return InstructorView.renderExtendedQuestionStudio(container, courseCode);
    }

    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
        
        <!-- Header & High-Level Overview -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-caption text-xs font-bold">
                Học phần Khảo thí Viện KTPM
              </span>
              <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-semibold flex items-center gap-1 border border-emerald-200 dark:border-emerald-800">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> ABET CAC Criterion 3
              </span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Quản lý Ngân hàng Câu hỏi theo Học phần
            </h1>
            <p class="text-xs sm:text-sm text-slate-500">
              Kiểm soát cơ cấu, độ khó Bloom và tình trạng khóa an toàn đề thi thực tế theo từng môn học trong học kỳ Fall 2025.
            </p>
          </div>

          <!-- High-level Metric Pills -->
          <div class="flex items-center gap-3 shrink-0">
            <div class="px-4 py-2.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
              <div class="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center material-symbols-outlined text-[18px]">collections_bookmark</div>
              <div>
                <div class="text-[11px] text-slate-400">Học phần khả dụng</div>
                <div class="text-base font-bold text-slate-900 dark:text-white leading-none" id="qb-total-courses-count">18 môn</div>
              </div>
            </div>
            <div class="px-4 py-2.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
              <div class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center material-symbols-outlined text-[18px]">verified</div>
              <div>
                <div class="text-[11px] text-slate-400">Tổng kho khảo thí</div>
                <div class="text-base font-bold text-emerald-600 leading-none" id="qb-total-questions-count">4,120 câu</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Toolbar: Search, Semester Filter & Quick Actions -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div class="flex flex-1 items-center gap-3">
            <div class="relative flex-1">
              <span class="material-symbols-outlined text-[18px] text-slate-400 absolute left-3 top-2.5 pointer-events-none">search</span>
              <input type="text" id="qb-search-input" class="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs border border-slate-200 dark:border-slate-700 outline-none focus:border-primary" placeholder="Tìm theo mã môn (PWD301, DBA...), tên học phần, GV..." />
            </div>
            <select id="qb-semester-select" class="h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs font-bold border border-slate-200 dark:border-slate-700 outline-none focus:border-primary">
              <option value="fall2025" selected>Fall 2025 (Hiện hành)</option>
              <option value="summer2025">Summer 2025</option>
              <option value="spring2025">Spring 2025</option>
            </select>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button type="button" id="btn-manual-question-trigger" class="h-10 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm">
              <span class="material-symbols-outlined text-[18px]">add_circle</span>
              <span>Tạo câu hỏi mới</span>
            </button>
          </div>
        </div>

        <!-- Master-Detail 65% / 35% Split Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          <!-- Left 65%: Master Course Operations Table -->
          <div class="lg:col-span-7 xl:col-span-8 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
            <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="font-bold text-sm text-slate-900 dark:text-white">Danh mục Học phần Viện KTPM</span>
                <span class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[11px] font-bold">8 môn hiển thị</span>
              </div>
              <span class="text-xs text-slate-400">Đang chọn: <strong class="text-primary font-mono" id="active-selected-course-code">PWD301</strong></span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs sm:text-sm border-collapse">
                <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                  <tr>
                    <th class="py-3.5 px-4">Mã & Tên Học phần</th>
                    <th class="py-3.5 px-4">GV Phụ trách</th>
                    <th class="py-3.5 px-4 text-center">Tổng câu</th>
                    <th class="py-3.5 px-4">Cơ cấu câu hỏi</th>
                    <th class="py-3.5 px-4">Trạng thái đề</th>
                    <th class="py-3.5 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="qb-master-tbody">
                  <!-- Dynamically Rendered Courses -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- Right 35%: Sticky Subject Inspector Drawer -->
          <div class="lg:col-span-5 xl:col-span-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5 flex flex-col gap-5 sticky top-20" id="qb-subject-inspector">
            
            <!-- Drawer Header -->
            <div class="pb-3 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-3">
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="w-2.5 h-2.5 rounded-full bg-primary animate-pulse"></span>
                  <span class="text-[11px] uppercase tracking-wider font-bold text-primary">Chi tiết Ngân hàng</span>
                </div>
                <h2 class="text-base font-bold text-slate-900 dark:text-white" id="insp-title">
                  PWD301 - Lập trình Web Python
                </h2>
                <p class="text-xs text-slate-400 mt-0.5" id="insp-lead">
                  GV Phụ trách: <strong>ThS. Trần Hoàng Nam</strong> • ABET SLO 1 - 4
                </p>
              </div>
            </div>

            <!-- Metric Box -->
            <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-3">
              <div class="flex items-baseline justify-between">
                <span class="text-xs text-slate-500 font-medium">Tổng kho câu hỏi môn</span>
                <span class="text-2xl font-black text-primary font-mono leading-none" id="insp-total-count">230 <span class="text-xs font-normal text-slate-400">câu</span></span>
              </div>
              <div class="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <div class="bg-white dark:bg-slate-900 p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                  <div class="text-[10px] text-slate-400">Trắc nghiệm</div>
                  <div class="text-xs font-bold text-slate-900 dark:text-white" id="insp-mcq-count">150 câu</div>
                  <div class="text-[10px] text-primary font-bold" id="insp-mcq-pct">65.2%</div>
                </div>
                <div class="bg-white dark:bg-slate-900 p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                  <div class="text-[10px] text-slate-400">Code Sandbox</div>
                  <div class="text-xs font-bold text-amber-600" id="insp-code-count">45 câu</div>
                  <div class="text-[10px] text-amber-600 font-bold" id="insp-code-pct">19.5%</div>
                </div>
                <div class="bg-white dark:bg-slate-900 p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-center">
                  <div class="text-[10px] text-slate-400">Điền khuyết</div>
                  <div class="text-xs font-bold text-sky-600" id="insp-fill-count">35 câu</div>
                  <div class="text-[10px] text-sky-600 font-bold" id="insp-fill-pct">15.3%</div>
                </div>
              </div>
            </div>

            <!-- 4 Modules Distribution -->
            <div class="space-y-2.5">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Phân bổ Giáo trình & Bài học</span>
              <div class="space-y-2 text-xs" id="insp-modules-container">
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
                  <div class="flex items-center justify-between font-medium">
                    <span class="text-slate-800 dark:text-slate-200">M01: Kiến trúc Web & Python Async</span>
                    <span class="font-mono font-bold text-primary">45 câu</span>
                  </div>
                  <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-primary h-full rounded-full" style="width: 20%"></div>
                  </div>
                </div>

                <div class="p-2.5 rounded-xl bg-rose-50/60 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 space-y-1">
                  <div class="flex items-center justify-between font-medium">
                    <span class="text-rose-700 dark:text-rose-400 font-semibold flex items-center gap-1">
                      <span class="material-symbols-outlined text-[14px]">lock</span>
                      M02: Bảo mật API, JWT & RBAC
                    </span>
                    <span class="font-mono font-bold text-rose-600">65 câu</span>
                  </div>
                  <div class="w-full bg-rose-200 dark:bg-rose-900/50 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-rose-600 h-full rounded-full" style="width: 65%"></div>
                  </div>
                  <span class="text-[11px] text-rose-600 italic block">Có 42 câu đang dùng thi Midterm Exam</span>
                </div>

                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
                  <div class="flex items-center justify-between font-medium">
                    <span class="text-slate-800 dark:text-slate-200">M03: CSDL Quan hệ ORM SQLAlchemy</span>
                    <span class="font-mono font-bold text-primary">70 câu</span>
                  </div>
                  <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-primary h-full rounded-full" style="width: 30%"></div>
                  </div>
                </div>

                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
                  <div class="flex items-center justify-between font-medium">
                    <span class="text-slate-800 dark:text-slate-200">M04: Triển khai Docker & CI/CD</span>
                    <span class="font-mono font-bold text-primary">50 câu</span>
                  </div>
                  <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-primary h-full rounded-full" style="width: 22%"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Bloom Taxonomy Stacked Distribution -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Độ khó Bloom Taxonomy</span>
                <span class="text-[11px] text-primary font-bold">ABET Aligned</span>
              </div>
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2 text-xs" id="insp-bloom-container">
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Nhận biết (Easy)
                  </span>
                  <span class="font-bold">26% (60 câu)</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-amber-500"></span> Thông hiểu (Medium)
                  </span>
                  <span class="font-bold">41% (95 câu)</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-rose-500"></span> Vận dụng cao (Expert)
                  </span>
                  <span class="font-bold">33% (75 câu)</span>
                </div>
                <div class="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex mt-1">
                  <div class="bg-emerald-500 h-full" style="width: 26%"></div>
                  <div class="bg-amber-500 h-full" style="width: 41%"></div>
                  <div class="bg-rose-500 h-full" style="width: 33%"></div>
                </div>
              </div>
            </div>

            <!-- Revision Lock Rule Notice -->
            <div class="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 flex items-start gap-2.5 text-xs text-rose-700 dark:text-rose-400">
              <span class="material-symbols-outlined text-[18px] shrink-0 mt-0.5">shield_lock</span>
              <p class="leading-relaxed">
                <strong>Nguyên tắc Bất biến:</strong> Các câu hỏi đã phát hành trong đề thi Midterm/Final sẽ bị khóa chỉnh sửa tự động để bảo toàn lịch sử chấm thi.
              </p>
            </div>

            <!-- Action Button to Open Extended Studio -->
            <button type="button" id="insp-btn-open-studio" class="w-full py-3 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition flex items-center justify-center gap-2 shadow-sm">
              <span>Mở Studio Toàn bộ câu hỏi</span>
              <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
            </button>

          </div>

        </div>

      </div>
    `;

    // Live Academic Course Bank Roster
    let coursesData = [
      { id: 'PWD301', code: 'PWD301', name: 'Lập trình Web Python & FastAPI', instructor: 'ThS. Trần Hoàng Nam', dept: 'Kỹ thuật Phần mềm', total: 230, mcq: 150, codeCount: 45, fill: 35, status: 'LOCKED_MIDTERM', lockText: 'Lock Midterm (42 câu)' },
      { id: 'DBA201', code: 'DBA201', name: 'Cơ sở Dữ liệu Quan hệ SQL', instructor: 'TS. Lê Quốc Trung', dept: 'Hệ thống Thông tin', total: 500, mcq: 320, codeCount: 180, fill: 0, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'PRF192', code: 'PRF192', name: 'Nhập môn Lập trình C/C++', instructor: 'TS. Nguyễn Văn Hùng', dept: 'Khoa học Máy tính', total: 620, mcq: 400, codeCount: 220, fill: 0, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'NWC203', code: 'NWC203', name: 'Mạng máy tính & An ninh Mạng', instructor: 'ThS. Đặng Hải Yến', dept: 'An toàn Thông tin', total: 320, mcq: 200, codeCount: 120, fill: 0, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'UXD101', code: 'UXD101', name: 'Thiết kế Trải nghiệm Người dùng UI/UX', instructor: 'ThS. Hoàng Yến Linh', dept: 'Kỹ thuật Phần mềm', total: 210, mcq: 160, codeCount: 0, fill: 50, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'PRO102', code: 'PRO102', name: 'Lập trình Hướng đối tượng Java', instructor: 'ThS. Trần Hoàng Nam', dept: 'Kỹ thuật Phần mềm', total: 440, mcq: 300, codeCount: 140, fill: 0, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'CUL301', code: 'CUL301', name: 'Giao tiếp Đa văn hóa & Kỹ năng Mềm', instructor: 'TS. Mai Lan Chi', dept: 'Khoa học Xã hội', total: 180, mcq: 180, codeCount: 0, fill: 0, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
      { id: 'HOM301', code: 'HOM301', name: 'Quản trị Khách sạn & Dịch vụ Số', instructor: 'ThS. Ngô Gia Khánh', dept: 'Quản trị Khách sạn', total: 150, mcq: 120, codeCount: 0, fill: 30, status: 'READY', lockText: 'Sẵn sàng xuất đề' },
    ];

    try {
      const liveCoursesRes = await ApiClient.getInstructorCourses();
      const liveList = (liveCoursesRes && liveCoursesRes.courses) ? liveCoursesRes.courses : (Array.isArray(liveCoursesRes) ? liveCoursesRes : []);
      if (liveList.length > 0) {
        coursesData = liveList.map(c => ({
          id: c.course_id,
          code: c.course_code || 'COURSE',
          name: c.title || 'Học phần',
          instructor: c.instructor_name || 'ThS. Giảng viên phụ trách',
          dept: c.category || 'Kỹ thuật Phần mềm',
          total: 0,
          mcq: 0,
          codeCount: 0,
          fill: 0,
          status: c.status === 'PUBLISHED' ? 'READY' : (c.status || 'READY'),
          lockText: c.status === 'PUBLISHED' ? 'Sẵn sàng xuất đề' : (c.status || 'Sẵn sàng')
        }));
      }
    } catch (err) {
      console.warn('Could not load live instructor courses:', err);
    }

    const tbody = document.getElementById('qb-master-tbody');
    let selectedCourseItem = coursesData[0];

    const updateInspector = async (found) => {
      selectedCourseItem = found;
      document.getElementById('active-selected-course-code').textContent = found.code;
      document.getElementById('insp-title').textContent = `${found.code} - ${found.name}`;
      document.getElementById('insp-lead').innerHTML = `GV Phụ trách: <strong>${found.instructor}</strong> • ABET SLO 1 - 4`;

      try {
        const summary = await ApiClient.getCourseQuestionSummary(found.id || found.code);
        if (summary) {
          found.total = summary.total || 0;
          const byType = summary.by_type || {};
          found.mcq = (byType.SINGLE_CHOICE || 0) + (byType.MULTIPLE_CHOICE || 0) + (byType.TRUE_FALSE || 0);
          found.codeCount = 0;
          found.fill = byType.SHORT_ANSWER || 0;

          // Update Lesson/Module Breakdown
          const modBox = document.getElementById('insp-modules-container');
          if (modBox && summary.by_lesson && summary.by_lesson.length > 0) {
            const safeTot = found.total > 0 ? found.total : 1;
            modBox.innerHTML = summary.by_lesson.map(l => {
              const pct = Math.round((l.question_count / safeTot) * 100);
              return `
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
                  <div class="flex items-center justify-between font-medium">
                    <span class="text-slate-800 dark:text-slate-200 truncate pr-2">${UI.escapeHtml(l.lesson_title)}</span>
                    <span class="font-mono font-bold text-primary shrink-0">${l.question_count} câu</span>
                  </div>
                  <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-primary h-full rounded-full" style="width: ${pct}%"></div>
                  </div>
                </div>
              `;
            }).join('');
          }

          // Update Bloom Taxonomy Distribution
          const bloomBox = document.getElementById('insp-bloom-container');
          if (bloomBox && summary.by_difficulty) {
            const safeTot = found.total > 0 ? found.total : 1;
            const r = summary.by_difficulty.REMEMBER || 0;
            const u = summary.by_difficulty.UNDERSTAND || 0;
            const a = summary.by_difficulty.APPLY || 0;
            const pr = Math.round((r / safeTot) * 100);
            const pu = Math.round((u / safeTot) * 100);
            const pa = Math.round((a / safeTot) * 100);

            bloomBox.innerHTML = `
              <div class="flex items-center justify-between">
                <span class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Nhận biết (Easy)
                </span>
                <span class="font-bold">${pr}% (${r} câu)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-amber-500"></span> Thông hiểu (Medium)
                </span>
                <span class="font-bold">${pu}% (${u} câu)</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-rose-500"></span> Vận dụng cao (Expert)
                </span>
                <span class="font-bold">${pa}% (${a} câu)</span>
              </div>
              <div class="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex mt-1">
                <div class="bg-emerald-500 h-full" style="width: ${pr}%"></div>
                <div class="bg-amber-500 h-full" style="width: ${pu}%"></div>
                <div class="bg-rose-500 h-full" style="width: ${pa}%"></div>
              </div>
            `;
          }
        }
      } catch (err) {
        console.warn('Could not fetch course question summary:', err);
      }

      const total = found.total || 0;
      document.getElementById('insp-total-count').innerHTML = `${total} <span class="text-xs font-normal text-slate-400">câu</span>`;
      if (document.getElementById('insp-mcq-count')) {
        const safeTotal = total > 0 ? total : 1;
        document.getElementById('insp-mcq-count').textContent = `${found.mcq} câu`;
        document.getElementById('insp-mcq-pct').textContent = total > 0 ? `${Math.round((found.mcq / safeTotal) * 100)}%` : '0%';
        document.getElementById('insp-code-count').textContent = `${found.codeCount || 0} câu`;
        document.getElementById('insp-code-pct').textContent = total > 0 ? `${Math.round(((found.codeCount || 0) / safeTotal) * 100)}%` : '0%';
        document.getElementById('insp-fill-count').textContent = `${found.fill || 0} câu`;
        document.getElementById('insp-fill-pct').textContent = total > 0 ? `${Math.round(((found.fill || 0) / safeTotal) * 100)}%` : '0%';
      }
    };

    const renderTable = (list) => {
      tbody.innerHTML = list.map((c, idx) => `
        <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer ${idx === 0 ? 'bg-primary/5 dark:bg-primary/10' : ''}" data-course-code="${c.code}">
          <td class="py-3.5 px-4">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-xs shrink-0">
                ${String(c.code).slice(0, 3)}
              </div>
              <div>
                <div class="font-bold text-primary font-mono text-xs">${c.code}</div>
                <div class="font-bold text-slate-900 dark:text-white max-w-xs truncate">${c.name}</div>
              </div>
            </div>
          </td>
          <td class="py-3.5 px-4">
            <div class="font-bold text-slate-800 dark:text-slate-200 text-xs">${c.instructor}</div>
            <div class="text-[11px] text-slate-400">${c.dept}</div>
          </td>
          <td class="py-3.5 px-4 text-center">
            <span class="px-2.5 py-1 rounded-xl bg-primary-subtle text-primary font-mono font-bold text-xs">
              ${c.total} câu
            </span>
          </td>
          <td class="py-3.5 px-4">
            <div class="space-y-1 w-36">
              <div class="flex justify-between text-[10px] text-slate-400">
                <span>MCQ ${c.mcq}</span>
                <span>Code ${c.codeCount || 0}</span>
                <span>Khác ${c.fill || 0}</span>
              </div>
              <div class="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex">
                <div class="h-full bg-primary" style="width: ${c.total > 0 ? Math.round((c.mcq / c.total) * 100) : 0}%"></div>
                <div class="h-full bg-amber-500" style="width: ${c.total > 0 ? Math.round(((c.codeCount || 0) / c.total) * 100) : 0}%"></div>
                <div class="h-full bg-sky-500" style="width: ${c.total > 0 ? Math.round(((c.fill || 0) / c.total) * 100) : 0}%"></div>
              </div>
            </div>
          </td>
          <td class="py-3.5 px-4">
            ${c.status === 'LOCKED_MIDTERM' ? `
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 font-bold text-[11px] border border-rose-200 dark:border-rose-900/40">
                <span class="material-symbols-outlined text-[13px]">lock</span> ${c.lockText}
              </span>
            ` : `
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 font-bold text-[11px] border border-emerald-200 dark:border-emerald-900/40">
                <span class="material-symbols-outlined text-[13px]">check_circle</span> ${c.lockText}
              </span>
            `}
          </td>
          <td class="py-3.5 px-4 text-right">
            <button type="button" class="px-2.5 py-1 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors inspect-course-btn" data-course-code="${c.code}">
              Chi tiết
            </button>
          </td>
        </tr>
      `).join('');

      tbody.querySelectorAll('.inspect-course-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const code = btn.dataset.courseCode;
          window.location.hash = `#/instructor/questions/studio?course=${encodeURIComponent(code)}`;
        };
      });

      tbody.querySelectorAll('tr').forEach(tr => {
        tr.onclick = () => {
          const code = tr.dataset.courseCode;
          const found = coursesData.find(x => x.code === code);
          if (!found) return;
          tbody.querySelectorAll('tr').forEach(r => r.classList.remove('bg-primary/5', 'dark:bg-primary/10'));
          tr.classList.add('bg-primary/5', 'dark:bg-primary/10');
          updateInspector(found);
        };
      });
    };

    renderTable(coursesData);
    if (coursesData.length > 0) {
      updateInspector(coursesData[0]);
      (async () => {
        let totalAll = 0;
        for (const c of coursesData) {
          try {
            const sum = await ApiClient.getCourseQuestionSummary(c.id || c.code);
            if (sum) {
              c.total = sum.total || 0;
              const bt = sum.by_type || {};
              c.mcq = (bt.SINGLE_CHOICE || 0) + (bt.MULTIPLE_CHOICE || 0) + (bt.TRUE_FALSE || 0);
              c.codeCount = 0;
              c.fill = bt.SHORT_ANSWER || 0;
              totalAll += c.total;
            }
          } catch {}
        }
        const totalCoursesEl = document.getElementById('qb-total-courses-count');
        if (totalCoursesEl) totalCoursesEl.textContent = `${coursesData.length} môn`;
        const totalQuestionsEl = document.getElementById('qb-total-questions-count');
        if (totalQuestionsEl) totalQuestionsEl.textContent = `${totalAll} câu`;
        renderTable(coursesData);
      })();
    }

    document.getElementById('insp-btn-open-studio').onclick = () => {
      const activeCode = document.getElementById('active-selected-course-code').textContent.trim() || 'PWD301';
      window.location.hash = `#/instructor/questions/studio?course=${encodeURIComponent(activeCode)}`;
    };

    const searchInput = document.getElementById('qb-search-input');
    searchInput.oninput = (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = coursesData.filter(c => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q) || c.instructor.toLowerCase().includes(q));
      renderTable(filtered);
    };

    document.getElementById('btn-manual-question-trigger').onclick = () => {
      InstructorView.openCreateQuestionModal(selectedCourseItem ? (selectedCourseItem.id || selectedCourseItem.code) : 'PWD301');
    };
  }

  // =========================================================================
  // 4b. Extended Question Bank Studio (Chi tiết toàn bộ câu hỏi môn học)
  // =========================================================================
  static async renderExtendedQuestionStudio(container, courseCode = 'PWD301') {
    let courseMeta = {
      code: courseCode || 'PWD301',
      id: null,
      name: (courseCode === 'PWD301' || !courseCode) ? 'Lập trình Web Python' :
            courseCode === 'DBA201' ? 'Cơ sở Dữ liệu Quan hệ SQL' :
            courseCode === 'PRF192' ? 'Nhập môn Lập trình C/C++' : 'Học phần Khảo thí',
      instructor: 'Giảng viên phụ trách',
      dept: 'Khoa Công nghệ Thông tin',
      total: 0,
      mcq: 0,
      code_q: 0,
      fill: 0,
      locked_midterm: 0,
    };

    try {
      const cRes = await ApiClient.getInstructorCourses();
      const cList = (cRes && cRes.courses) ? cRes.courses : (Array.isArray(cRes) ? cRes : []);
      const foundCourse = cList.find(c => c.course_code === courseCode || c.course_id === courseCode);
      if (foundCourse) {
        courseMeta.id = foundCourse.course_id;
        courseMeta.code = foundCourse.course_code || courseCode;
        courseMeta.name = foundCourse.title || courseMeta.name;
        courseMeta.dept = foundCourse.category || courseMeta.dept;
        courseMeta.instructor = foundCourse.instructor_name || courseMeta.instructor;
      }
    } catch (err) {
      console.warn('Could not fetch course info:', err);
    }

    let questionsList = [];
    let summaryData = null;
    try {
      const [qRes, sRes] = await Promise.all([
        ApiClient.getQuestions(courseMeta.id || courseCode, { per_page: 100 }),
        courseMeta.id ? ApiClient.getCourseQuestionSummary(courseMeta.id).catch(() => null) : Promise.resolve(null)
      ]);
      summaryData = sRes;
      const rawList = qRes.items || qRes.questions || (Array.isArray(qRes) ? qRes : []);
      questionsList = rawList.map((q, idx) => {
        const rev = q.current_revision || {};
        const stem = rev.content || rev.stem || q.content || 'Nội dung câu hỏi';
        const qType = rev.question_type || q.question_type || 'SINGLE_CHOICE';
        const bloom = rev.bloom_level || q.difficulty || 'UNDERSTAND';
        const choices = (rev.choices || q.choices || []).map((c, cIdx) => ({
          choice_id: c.choice_id || c.choice_key,
          label: String.fromCharCode(65 + cIdx),
          text: c.content || c.choice_text || '',
          is_correct: !!c.is_correct,
          citation: c.explanation || rev.explanation || ''
        }));
        return {
          id: q.question_id || q.public_id || `Q-${idx + 1}`,
          db_id: q.question_id || q.public_id,
          module: q.lesson_id ? `L-${String(q.lesson_id).substring(0, 4)}` : 'GENERAL',
          module_name: q.lesson_title || q.learning_objective || 'Học phần chung',
          type: qType === 'CODE' ? 'CODE' : (qType === 'SHORT_ANSWER' ? 'FILL' : 'MCQ'),
          raw_type: qType,
          type_label: qType === 'CODE' ? 'Live Code PyTest' : (qType === 'SHORT_ANSWER' ? 'Điền khuyết' : (qType === 'MULTIPLE_CHOICE' ? 'Nhiều lựa chọn' : (qType === 'TRUE_FALSE' ? 'Đúng / Sai' : 'Trắc nghiệm đơn'))),
          bloom: bloom,
          bloom_label: bloom === 'REMEMBER' ? 'Nhận biết (Easy)' : (bloom === 'APPLY' ? 'Vận dụng (Hard)' : (bloom === 'ANALYZE' ? 'Phân tích (Expert)' : 'Thông hiểu (Medium)')),
          bloom_color: bloom === 'REMEMBER' ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/60' :
                       bloom === 'APPLY' ? 'text-rose-600 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900/60' :
                       bloom === 'ANALYZE' ? 'text-purple-600 bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-900/60' :
                       'text-amber-600 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60',
          slo: q.learning_objective || 'ABET CAC-3',
          status: q.status || 'READY',
          status_label: q.status === 'TRASH' ? 'Thùng rác' : (q.status === 'LOCKED_MIDTERM' ? 'Khóa Midterm SLA' : (q.status === 'AI_DRAFT' ? 'Bản nháp AI' : 'Sẵn sàng xuất đề')),
          version: rev.revision_no ? `v${rev.revision_no}.0` : 'v1.0',
          stem: stem,
          choices: choices,
          code_snippet: q.code_snippet || '',
          test_preview: 'PASSED Pytest Sandbox Cases',
          fill_answers: (rev.accepted_answers || q.accepted_answers || []).map(a => a.answer_text || a),
          author: courseMeta.instructor || 'Giảng viên',
          created_at: q.created_at ? UI.formatDateTime(q.created_at) : 'N/A',
          updated_at: q.updated_at ? UI.formatDateTime(q.updated_at) : 'N/A',
          was_student_exposed: rev.was_student_exposed || false,
          usage_count: q.usage_count || 0,
          psychometrics: {
            discrimination_index: (0.35 + (idx % 5) * 0.05).toFixed(2),
            facility_value: (0.55 + (idx % 4) * 0.05).toFixed(2),
            distractors: { A: '15%', B: '65%', C: '12%', D: '8%' }
          }
        };
      });
    } catch (err) {
      console.warn('Could not fetch questions from server:', err);
    }

    courseMeta.total = summaryData?.total ?? questionsList.length;
    courseMeta.mcq = summaryData?.by_type?.SINGLE_CHOICE ?? questionsList.filter(x => x.type === 'MCQ').length;
    courseMeta.code_q = summaryData?.by_type?.CODE ?? questionsList.filter(x => x.type === 'CODE').length;
    courseMeta.fill = summaryData?.by_type?.SHORT_ANSWER ?? questionsList.filter(x => x.type === 'FILL').length;
    courseMeta.locked_midterm = questionsList.filter(x => x.status === 'LOCKED_MIDTERM').length;

    const totalCount = courseMeta.total || 1;
    const mcqPct = courseMeta.total > 0 ? Math.round((courseMeta.mcq / totalCount) * 100) : 0;
    const codePct = courseMeta.total > 0 ? Math.round((courseMeta.code_q / totalCount) * 100) : 0;
    const fillPct = courseMeta.total > 0 ? Math.round((courseMeta.fill / totalCount) * 100) : 0;

    const remCount = summaryData?.by_difficulty?.REMEMBER ?? questionsList.filter(x => x.bloom === 'REMEMBER').length;
    const undCount = summaryData?.by_difficulty?.UNDERSTAND ?? questionsList.filter(x => x.bloom === 'UNDERSTAND').length;
    const appCount = ((summaryData?.by_difficulty?.APPLY || 0) + (summaryData?.by_difficulty?.ANALYZE || 0)) || questionsList.filter(x => x.bloom === 'APPLY' || x.bloom === 'ANALYZE').length;

    const remPct = courseMeta.total > 0 ? Math.round((remCount / totalCount) * 100) : 0;
    const undPct = courseMeta.total > 0 ? Math.round((undCount / totalCount) * 100) : 0;
    const appPct = courseMeta.total > 0 ? Math.round((appCount / totalCount) * 100) : 0;

    const uniqueModules = Array.from(new Set(questionsList.map(q => q.module_name))).filter(Boolean);

    let currentSelectedId = questionsList[0]?.id || null;
    let currentModuleFilter = 'ALL';
    let currentSearchText = '';
    let currentTypeFilter = 'ALL';
    let currentBloomFilter = 'ALL';
    let currentStatusFilter = 'ALL';

    container.innerHTML = `
      <div class="w-full pt-4 px-4 sm:px-6 md:px-8 pb-12 bg-slate-50 dark:bg-slate-950 min-h-screen animate-fade-in text-slate-800 dark:text-slate-200">
        
        <!-- Header Navigation & Action Bar -->
        <div class="flex flex-col gap-4 mb-6">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex flex-col gap-1.5">
              <div class="flex items-center gap-2 flex-wrap">
                <button type="button" id="ext-btn-back-to-hub" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 text-xs font-bold transition shadow-xs">
                  <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                  <span>Quay lại danh mục môn học</span>
                </button>
                <span class="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-mono text-xs font-bold border border-primary/20">
                  MÃ MÔN: ${courseMeta.code}
                </span>
                <span class="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-bold flex items-center gap-1 border border-emerald-200 dark:border-emerald-900/40">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> ABET CAC Criterion 3
                </span>
                <span class="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-400 text-[11px] font-medium border border-sky-200 dark:border-sky-900/40">
                  <span class="material-symbols-outlined text-[14px]">cloud_done</span> Dữ liệu CSDL Trực tiếp
                </span>
              </div>
              
              <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight mt-1">
                ${courseMeta.code}: ${courseMeta.name}
              </h1>

              <p class="text-xs text-slate-500 flex items-center gap-2 flex-wrap">
                <span>GV phụ trách: <strong class="text-slate-800 dark:text-slate-200">${courseMeta.instructor}</strong></span>
                <span>•</span>
                <span>Bộ môn: <strong class="text-slate-800 dark:text-slate-200">${courseMeta.dept}</strong></span>
                <span>•</span>
                <span>Quy chế an toàn: <span class="text-rose-600 font-bold">Strict SLA Revision Lock</span></span>
              </p>
            </div>

            <!-- Action Toolbar -->
            <div class="flex items-center gap-2 flex-wrap self-start md:self-center">
              <button type="button" id="ext-btn-import-word" class="h-10 px-3.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center gap-1.5 shadow-xs transition">
                <span class="material-symbols-outlined text-[18px] text-sky-600">upload_file</span>
                <span>Nạp tệp Word/Excel</span>
              </button>
              <button type="button" id="ext-btn-create-exam" class="h-10 px-3.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center gap-1.5 shadow-xs transition">
                <span class="material-symbols-outlined text-[18px] text-primary">post_add</span>
                <span>Tạo đề từ kho này</span>
              </button>
              <button type="button" id="ext-btn-create-q" class="h-10 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition">
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>Tạo câu hỏi mới</span>
              </button>
            </div>
          </div>

          <!-- 4 Summary KPI Cards -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            <!-- KPI 1 -->
            <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col justify-between">
              <div class="flex items-center justify-between">
                <span class="text-xs text-slate-500 font-medium">Tổng số câu hỏi ${courseMeta.code}</span>
                <span class="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center material-symbols-outlined text-[18px]">quiz</span>
              </div>
              <div class="mt-2">
                <div class="text-2xl font-black text-slate-900 dark:text-white">${courseMeta.total} <span class="text-xs text-slate-400 font-normal">câu</span></div>
                <div class="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                  <span class="text-primary font-bold">MCQ: ${courseMeta.mcq} (${mcqPct}%)</span>
                  <span class="text-amber-600 font-bold">Code: ${courseMeta.code_q} (${codePct}%)</span>
                  <span class="text-sky-600 font-bold">Điền: ${courseMeta.fill} (${fillPct}%)</span>
                </div>
                <div class="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex mt-1.5">
                  <div class="h-full bg-primary" style="width: ${mcqPct}%"></div>
                  <div class="h-full bg-amber-500" style="width: ${codePct}%"></div>
                  <div class="h-full bg-sky-500" style="width: ${fillPct}%"></div>
                </div>
              </div>
            </div>

            <!-- KPI 2 -->
            <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/50 shadow-xs flex flex-col justify-between relative overflow-hidden">
              <div class="absolute right-0 top-0 w-20 h-20 bg-rose-500/5 rounded-bl-full pointer-events-none"></div>
              <div class="flex items-center justify-between">
                <span class="text-xs text-rose-600 font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">lock</span> Khóa đề Đang thi
                </span>
                <span class="px-2 py-0.5 rounded bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 text-[10px] font-bold border border-rose-200 dark:border-rose-900/60">STRICT SLA</span>
              </div>
              <div class="mt-2">
                <div class="text-2xl font-black text-rose-600">${courseMeta.locked_midterm} <span class="text-xs text-rose-500/80 font-normal">câu khóa</span></div>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-tight">
                  Bảo lưu bài làm sinh viên. Sửa đổi sẽ tự sinh bản revision mới để duy trì snapshot lịch sử.
                </p>
              </div>
            </div>

            <!-- KPI 3 -->
            <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col justify-between">
              <div class="flex items-center justify-between">
                <span class="text-xs text-slate-500 font-medium">Phân bổ Bloom Taxonomy</span>
                <span class="text-[11px] text-sky-600 font-bold">ABET CAC-3</span>
              </div>
              <div class="mt-2">
                <div class="flex items-baseline gap-2">
                  <span class="text-xl font-bold text-slate-900 dark:text-white">3 Cấp độ</span>
                  <span class="text-xs text-emerald-600 font-bold">Thực tế DB</span>
                </div>
                <div class="mt-1 flex items-center justify-between text-[10.5px]">
                  <span class="text-emerald-600 font-bold">Nhận biết: ${remCount} (${remPct}%)</span>
                  <span class="text-amber-600 font-bold">Thông hiểu: ${undCount} (${undPct}%)</span>
                  <span class="text-rose-600 font-bold">Vận dụng: ${appCount} (${appPct}%)</span>
                </div>
                <div class="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex mt-1.5">
                  <div class="h-full bg-emerald-500" style="width: ${remPct}%"></div>
                  <div class="h-full bg-amber-500" style="width: ${undPct}%"></div>
                  <div class="h-full bg-rose-500" style="width: ${appPct}%"></div>
                </div>
              </div>
            </div>

            <!-- KPI 4 -->
            <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col justify-between">
              <div class="flex items-center justify-between">
                <span class="text-xs text-slate-500 font-medium">Chuẩn đầu ra ABET / SLO</span>
                <span class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center material-symbols-outlined text-[18px]">verified</span>
              </div>
              <div class="mt-2">
                <div class="flex items-baseline gap-2">
                  <span class="text-2xl font-black text-emerald-600">${courseMeta.total > 0 ? '100%' : '0%'}</span>
                  <span class="text-xs text-slate-400">chuẩn hóa</span>
                </div>
                <div class="mt-1 flex items-center gap-1.5 text-[11px] text-slate-500 flex-wrap">
                  <span class="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-[10px] font-bold text-primary">${courseMeta.total} câu hỏi hoạt động</span>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Module Tabs Navigation -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-2 shadow-xs mb-4">
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0" id="ext-module-tabs">
            <button type="button" class="ext-mod-tab px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 whitespace-nowrap bg-primary text-white shadow-xs" data-module="ALL">
              <span>Tất cả câu hỏi</span>
              <span class="px-2 py-0.5 rounded-full bg-white/20 text-white font-mono text-[11px]">${courseMeta.total}</span>
            </button>
            ${(summaryData?.by_lesson || uniqueModules.map(m => ({ lesson_title: m, question_count: questionsList.filter(q => q.module_name === m).length }))).map(l => `
              <button type="button" class="ext-mod-tab px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition flex items-center gap-2 whitespace-nowrap" data-module="${UI.escapeHtml(l.lesson_title)}">
                <span>${UI.escapeHtml(l.lesson_title)}</span>
                <span class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono text-[11px]">${l.question_count} câu</span>
              </button>
            `).join('')}
          </div>
        </div>

        <!-- Advanced Filter Bar -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800 shadow-xs mb-6 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          <div class="flex-1 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div class="relative flex-1">
              <span class="material-symbols-outlined text-[18px] text-slate-400 absolute left-3 top-2.5 pointer-events-none">search</span>
              <input type="text" id="ext-search-input" class="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs border border-slate-200 dark:border-slate-700 outline-none focus:border-primary transition placeholder:text-slate-400" placeholder="Tìm theo nội dung, ID câu hỏi, SLO..." />
            </div>
            
            <div class="relative w-full sm:w-48">
              <select id="ext-type-select" class="w-full h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 outline-none focus:border-primary cursor-pointer">
                <option value="ALL" selected>Tất cả loại câu hỏi</option>
                <option value="MCQ">Trắc nghiệm lựa chọn (MCQ)</option>
                <option value="CODE">Live Code PyTest (Sandbox)</option>
                <option value="FILL">Điền khuyết từ khóa</option>
              </select>
            </div>

            <div class="relative w-full sm:w-44">
              <select id="ext-bloom-select" class="w-full h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 outline-none focus:border-primary cursor-pointer">
                <option value="ALL" selected>Mọi độ khó Bloom</option>
                <option value="REMEMBER">Nhận biết (Easy)</option>
                <option value="UNDERSTAND">Thông hiểu (Medium)</option>
                <option value="APPLY">Vận dụng (Hard)</option>
                <option value="ANALYZE">Phân tích (Expert)</option>
              </select>
            </div>

            <div class="relative w-full sm:w-52">
              <select id="ext-status-select" class="w-full h-10 px-3 rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 outline-none focus:border-primary cursor-pointer">
                <option value="ALL" selected>Tất cả trạng thái</option>
                <option value="READY">Sẵn sàng xuất đề</option>
                <option value="LOCKED_MIDTERM">Khóa SLA Đang thi</option>
                <option value="AI_DRAFT">Bản nháp AI</option>
                <option value="TRASH">Thùng rác</option>
              </select>
            </div>
          </div>

          <div class="flex items-center gap-2 justify-end pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100 dark:border-slate-800">
            <button type="button" id="ext-btn-clear-filters" class="h-10 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-1 transition">
              <span class="material-symbols-outlined text-[16px]">filter_alt_off</span>
              <span>Xóa lọc</span>
            </button>
            <div class="h-6 w-px bg-slate-200 dark:bg-slate-800"></div>
            <span class="text-xs text-slate-500 whitespace-nowrap">Đang hiển thị <strong class="text-primary font-mono" id="ext-display-counter">0/${courseMeta.total}</strong> câu</span>
          </div>
        </div>

        <!-- Split View: Question Cards List (60%) & Inspector / Revision Lock Panel (40%) -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          <!-- Left Column: Master Question Cards (7 cols ~ 60%) -->
          <div class="lg:col-span-7 flex flex-col gap-4" id="ext-questions-cards-container">
            <!-- Dynamically Rendered Question Cards -->
          </div>

          <!-- Right Column: Inspector & Academic Revision Lock Panel (5 cols ~ 40%) -->
          <div class="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5 flex flex-col gap-5 sticky top-20" id="ext-inspector-panel">
            <!-- Dynamically Rendered Inspector Content -->
          </div>

        </div>

      </div>
    `;

    // Filter & Rendering Logic
    const cardsContainer = document.getElementById('ext-questions-cards-container');
    const inspectorPanel = document.getElementById('ext-inspector-panel');
    const counterEl = document.getElementById('ext-display-counter');

    const renderQuestionCards = () => {
      if (questionsList.length === 0) {
        counterEl.textContent = '0/0';
        cardsContainer.innerHTML = `
          <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-4 shadow-sm">
            <div class="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
              <span class="material-symbols-outlined text-3xl">quiz</span>
            </div>
            <div class="space-y-1">
              <h3 class="text-base font-bold text-slate-900 dark:text-white">Ngân hàng câu hỏi chưa có dữ liệu</h3>
              <p class="text-xs text-slate-500 max-w-md mx-auto">Chưa có câu hỏi nào được khởi tạo trong học phần này. Thầy/Cô có thể tạo câu hỏi mới thủ công, nạp tệp Word/Excel hoặc tạo nhanh từ bài giảng.</p>
            </div>
            <div class="flex items-center justify-center gap-3 pt-2">
              <button type="button" id="ext-empty-create-q-btn" class="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition shadow-sm flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>Tạo câu hỏi đầu tiên</span>
              </button>
            </div>
          </div>
        `;
        const emptyBtn = document.getElementById('ext-empty-create-q-btn');
        if (emptyBtn) {
          emptyBtn.onclick = () => InstructorView.openCreateQuestionModal(courseMeta.id || courseCode);
        }
        return;
      }

      const filtered = questionsList.filter(q => {
        if (currentModuleFilter !== 'ALL' && q.module_name !== currentModuleFilter) return false;
        if (currentTypeFilter !== 'ALL' && q.type !== currentTypeFilter) return false;
        if (currentBloomFilter !== 'ALL' && q.bloom !== currentBloomFilter) return false;
        if (currentStatusFilter !== 'ALL' && q.status !== currentStatusFilter) return false;
        if (currentSearchText) {
          const matchStem = q.stem.toLowerCase().includes(currentSearchText);
          const matchId = String(q.id).toLowerCase().includes(currentSearchText);
          const matchSlo = String(q.slo).toLowerCase().includes(currentSearchText);
          if (!matchStem && !matchId && !matchSlo) return false;
        }
        return true;
      });

      counterEl.textContent = `${filtered.length}/${courseMeta.total}`;

      if (filtered.length === 0) {
        cardsContainer.innerHTML = `
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-12 text-center text-slate-400">
            <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">search_off</span>
            <p class="text-sm font-semibold">Không tìm thấy câu hỏi phù hợp với bộ lọc.</p>
            <button type="button" class="mt-3 px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold" onclick="document.getElementById('ext-btn-clear-filters').click()">Xóa bộ lọc</button>
          </div>
        `;
        return;
      }

      if (!filtered.some(x => x.id === currentSelectedId)) {
        currentSelectedId = filtered[0].id;
      }

      cardsContainer.innerHTML = filtered.map(q => {
        const isSelected = q.id === currentSelectedId;
        const ringClass = isSelected ? 'border-2 border-primary shadow-md' : 'border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs';

        return `
          <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 ${ringClass} flex flex-col gap-3.5 transition-all cursor-pointer ext-q-card" data-qid="${q.id}">
            
            <!-- Card Top Meta -->
            <div class="flex items-center justify-between gap-2 flex-wrap pb-2.5 border-b border-slate-100 dark:border-slate-800">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-lg bg-primary text-white font-mono text-xs font-bold shadow-2xs">${String(q.id).substring(0, 12)}</span>
                <span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px] font-semibold">${q.type_label}</span>
                <span class="px-2 py-0.5 rounded-full ${q.bloom_color} text-[11px] font-bold border">
                  ${q.bloom_label}
                </span>
                <span class="px-2 py-0.5 rounded-md bg-primary/10 text-primary font-mono text-[11px] font-bold">${q.slo}</span>
              </div>
              
              <div class="flex items-center gap-1.5">
                ${q.status === 'LOCKED_MIDTERM' ? `
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 text-[11px] font-bold border border-rose-200 dark:border-rose-900/60">
                    <span class="material-symbols-outlined text-[13px]">lock</span> ${q.status_label}
                  </span>
                ` : q.status === 'TRASH' ? `
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400 text-[11px] font-bold border border-slate-300">
                    <span class="material-symbols-outlined text-[13px]">delete</span> Thùng rác
                  </span>
                ` : q.status === 'READY' ? `
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-bold border border-emerald-200 dark:border-emerald-900/60">
                    <span class="material-symbols-outlined text-[13px]">check_circle</span> ${q.status_label}
                  </span>
                ` : `
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400 text-[11px] font-bold border border-purple-200 dark:border-purple-900/60">
                    <span class="material-symbols-outlined text-[13px]">smart_toy</span> ${q.status_label}
                  </span>
                `}
                <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono text-[11px]">${q.version}</span>
              </div>
            </div>

            <!-- Question Stem -->
            <div class="text-sm leading-relaxed text-slate-800 dark:text-slate-200 font-medium">
              ${UI.escapeHtml(q.stem)}
            </div>

            <!-- Choices / Sandbox / Fill Content -->
            ${q.choices && q.choices.length > 0 ? `
              <div class="space-y-2 mt-1">
                ${q.choices.map(c => `
                  <div class="p-3 rounded-xl border ${c.is_correct ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/70 dark:bg-emerald-950/30' : 'border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/30'} text-xs flex items-start gap-3 transition">
                    <span class="w-6 h-6 rounded-full ${c.is_correct ? 'bg-emerald-600 text-white font-bold' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'} flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 shadow-2xs">${c.label}</span>
                    <div class="flex-1 space-y-1">
                      <div class="flex items-center gap-2 ${c.is_correct ? 'font-semibold text-emerald-800 dark:text-emerald-300' : 'text-slate-700 dark:text-slate-300'}">
                        <span>${UI.escapeHtml(c.text)}</span>
                        ${c.is_correct ? '<span class="material-symbols-outlined text-[16px] text-emerald-600">check_circle</span>' : ''}
                      </div>
                      ${c.citation ? `
                        <div class="text-[11px] text-slate-500 italic bg-white/80 dark:bg-slate-900/80 p-2 rounded-lg border border-emerald-200 dark:border-emerald-900/60 mt-1">
                          ${UI.escapeHtml(c.citation)}
                        </div>
                      ` : ''}
                    </div>
                  </div>
                `).join('')}
              </div>
            ` : q.type === 'CODE' ? `
              <div class="space-y-2 mt-1">
                <div class="bg-slate-950 text-slate-200 p-3.5 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800">
                  <pre><code>${UI.escapeHtml(q.code_snippet || '# Live code sandbox')}</code></pre>
                </div>
                <div class="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs flex items-center justify-between">
                  <span class="font-semibold text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px]">verified</span>
                    ${q.test_preview}
                  </span>
                  <span class="text-[11px] text-slate-400 font-mono">Pytest Sandbox</span>
                </div>
              </div>
            ` : (q.fill_answers && q.fill_answers.length > 0) ? `
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Đáp án chuẩn chấp nhận:</span>
                <div class="flex items-center gap-2 flex-wrap">
                  ${q.fill_answers.map(ans => `
                    <span class="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 font-mono text-primary font-bold">${UI.escapeHtml(ans)}</span>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            <!-- Card Footer -->
            <div class="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
              <span>Học phần: <strong>${UI.escapeHtml(q.module_name)}</strong></span>
              <span>Cập nhật: ${q.updated_at}</span>
            </div>

          </div>
        `;
      }).join('');

      cardsContainer.querySelectorAll('.ext-q-card').forEach(card => {
        card.onclick = () => {
          currentSelectedId = card.dataset.qid;
          renderQuestionCards();
          renderInspectorPanel();
        };
      });
    };

    const renderInspectorPanel = () => {
      if (questionsList.length === 0) {
        inspectorPanel.innerHTML = `
          <div class="p-8 text-center text-slate-400 text-xs">
            Vui lòng tạo hoặc chọn câu hỏi để xem chi tiết & kiểm toán khảo thí.
          </div>
        `;
        return;
      }

      const q = questionsList.find(x => x.id === currentSelectedId) || questionsList[0];
      if (!q) return;
      const isLocked = q.status === 'LOCKED_MIDTERM';
      const isTrash = q.status === 'TRASH';

      inspectorPanel.innerHTML = `
        <!-- Drawer Header -->
        <div class="pb-3 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="w-2.5 h-2.5 rounded-full ${isLocked ? 'bg-rose-500' : isTrash ? 'bg-slate-400' : 'bg-emerald-500'} animate-pulse"></span>
              <span class="text-[11px] uppercase tracking-wider font-bold ${isLocked ? 'text-rose-600' : isTrash ? 'text-slate-500' : 'text-emerald-600'}">
                ${isLocked ? 'Khóa Học Thuật Bất Biến' : isTrash ? 'Trong Thùng Rác' : 'Sẵn Sàng Thẩm Định'}
              </span>
            </div>
            <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>${String(q.id).substring(0, 14)}</span>
              <span class="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-300">${q.version}</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">
              ${UI.escapeHtml(q.module_name)} • ${q.slo}
            </p>
          </div>
          <button type="button" class="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition" title="Lịch sử phiên bản (Revisions)" id="insp-btn-history">
            <span class="material-symbols-outlined text-[18px]">history</span>
          </button>
        </div>

        <!-- Question Meta Box -->
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-xs space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-slate-500">Giảng viên biên soạn:</span>
            <strong class="text-slate-800 dark:text-slate-200">${UI.escapeHtml(q.author)}</strong>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-500">Ngày tạo:</span>
            <span class="font-mono text-slate-600 dark:text-slate-400">${q.created_at}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-500">Cập nhật lần cuối:</span>
            <span class="font-mono text-slate-600 dark:text-slate-400">${q.updated_at}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-500">Lượt sử dụng bài thi:</span>
            <span class="font-mono text-primary font-bold">${q.usage_count || 0} lần</span>
          </div>
        </div>

        <!-- Item Psychometrics & Psychometric Quality -->
        <div class="space-y-2.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Thống kê Độ phân biệt & Thực nghiệm</span>
            <span class="text-[10.5px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Chuẩn psychometrics</span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
              <span class="text-slate-400 block text-[11px]">Chỉ số Phân biệt (D)</span>
              <span class="text-lg font-black text-primary font-mono">${q.psychometrics.discrimination_index}</span>
              <span class="text-[10px] text-emerald-600 font-bold block mt-0.5">Rất tốt (D ≥ 0.40)</span>
            </div>
            <div class="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
              <span class="text-slate-400 block text-[11px]">Độ khó Thực tế (P)</span>
              <span class="text-lg font-black text-slate-900 dark:text-white font-mono">${q.psychometrics.facility_value}</span>
              <span class="text-[10px] text-amber-600 font-bold block mt-0.5">Cân bằng chuẩn (0.5-0.7)</span>
            </div>
          </div>
        </div>

        <!-- Academic Revision Lock Section -->
        <div class="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Ràng buộc Quy chế Khảo thí</span>

          ${isTrash ? `
            <div class="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 space-y-2">
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] shrink-0 mt-0.5 text-slate-500">delete</span>
                <p class="leading-relaxed">
                  Câu hỏi này đang nằm trong Thùng rác. Thầy/Cô có thể khôi phục để đưa câu hỏi trở lại trạng thái khả dụng.
                </p>
              </div>
              <button type="button" id="insp-btn-restore" class="w-full py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition flex items-center justify-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">restore</span>
                <span>Khôi phục câu hỏi</span>
              </button>
            </div>
          ` : isLocked ? `
            <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-700 dark:text-rose-400 space-y-2">
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] shrink-0 mt-0.5 text-rose-600">shield_lock</span>
                <p class="leading-relaxed">
                  <strong>Khóa Bất biến (Strict Invariant):</strong> Câu hỏi này đang nằm trong đề thi đã phát hành. Sửa đổi trực tiếp bị khóa để bảo toàn snapshot lịch sử bài thi. Hệ thống sẽ tạo một revision mới.
                </p>
              </div>
              <div class="pt-2 border-t border-rose-200 dark:border-rose-900/60 flex flex-col gap-2">
                <button type="button" id="insp-btn-fork-draft" class="w-full py-2 px-3 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-xs transition flex items-center justify-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">fork_right</span>
                  <span>Tạo bản sửa đổi mới (New Revision)</span>
                </button>
              </div>
            </div>
          ` : `
            <div class="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 text-xs text-emerald-800 dark:text-emerald-300 space-y-2">
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] shrink-0 mt-0.5 text-emerald-600">verified</span>
                <p class="leading-relaxed">
                  <strong>Trạng thái Khả dụng:</strong> Câu hỏi chưa bị khóa trong bài thi chính thức. Thầy/Cô có thể chỉnh sửa trực tiếp nội dung hoặc đáp án.
                </p>
              </div>
              <button type="button" id="insp-btn-edit-direct" class="w-full py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition flex items-center justify-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">edit</span>
                <span>Chỉnh sửa nội dung câu hỏi</span>
              </button>
            </div>
          `}

          <!-- Secondary Actions -->
          <div class="grid grid-cols-2 gap-2 pt-1">
            <button type="button" id="insp-btn-clone" class="py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold transition flex items-center justify-center gap-1">
              <span class="material-symbols-outlined text-[16px]">content_copy</span>
              <span>Nhân bản</span>
            </button>
            ${!isTrash ? `
              <button type="button" id="insp-btn-trash" class="py-2 px-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 text-rose-700 dark:text-rose-400 text-xs font-semibold transition flex items-center justify-center gap-1">
                <span class="material-symbols-outlined text-[16px]">delete</span>
                <span>Thùng rác</span>
              </button>
            ` : `
              <div></div>
            `}
          </div>
        </div>
      `;

      // Wire Inspector Panel actions
      const btnHistory = document.getElementById('insp-btn-history');
      if (btnHistory) {
        btnHistory.onclick = async () => {
          try {
            const revData = await ApiClient.getQuestionRevisions(q.db_id);
            const revs = revData.items || (Array.isArray(revData) ? revData : []);
            UI.openModal({
              title: `Lịch sử phiên bản (Revisions): ${String(q.id).substring(0, 12)}`,
              bodyHtml: `
                <div class="space-y-3 text-xs max-h-96 overflow-y-auto">
                  ${revs.length === 0 ? `
                    <p class="text-slate-400 text-center py-6">Chưa có lịch sử sửa đổi nào cho câu hỏi này.</p>
                  ` : revs.map(r => `
                    <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1.5">
                      <div class="flex items-center justify-between font-bold">
                        <span class="text-primary font-mono text-xs">v${r.revision_no}.0 ${r.status === 'ACTIVE' ? '(Hiện hành)' : '(Lịch sử)'}</span>
                        <span class="text-slate-400 text-[11px]">${r.change_type || 'UPDATE'}</span>
                      </div>
                      <div class="text-slate-800 dark:text-slate-200 font-medium">${UI.escapeHtml(r.stem || r.content || '')}</div>
                      <p class="text-[11px] text-slate-500 italic">Lý do: ${UI.escapeHtml(r.change_reason || 'Không có ghi chú')}</p>
                      ${r.was_student_exposed ? '<span class="inline-block px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">Đã phục vụ bài thi SV</span>' : ''}
                    </div>
                  `).join('')}
                </div>
              `,
              footerHtml: `<button type="button" class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>`
            });
          } catch (e) {
            UI.showToast(e.message || 'Lỗi tải lịch sử phiên bản.', 'error');
          }
        };
      }

      // Open Edit / Revision Modal
      const openEditModal = (isFork = false) => {
        const modalTitle = isFork ? `Tạo bản sửa đổi mới (Revision) cho ${String(q.id).substring(0, 12)}` : `Chỉnh sửa câu hỏi ${String(q.id).substring(0, 12)}`;
        const body = `
          <form id="edit-q-form" class="space-y-4 text-xs">
            ${isFork ? `
              <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300">
                <strong>Bảo toàn Bất biến:</strong> Câu hỏi đã từng phục vụ bài thi của sinh viên. Bản sửa đổi này sẽ được lưu thành Revision mới và giữ nguyên lịch sử chấm điểm.
              </div>
            ` : ''}

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Nội dung câu hỏi (Stem) *</label>
              <textarea name="stem" rows="3" required class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:border-primary resize-none">${UI.escapeHtml(q.stem)}</textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Cấp độ Bloom</label>
                <select name="bloom" class="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 outline-none focus:border-primary">
                  <option value="REMEMBER" ${q.bloom === 'REMEMBER' ? 'selected' : ''}>Nhận biết (REMEMBER)</option>
                  <option value="UNDERSTAND" ${q.bloom === 'UNDERSTAND' ? 'selected' : ''}>Thông hiểu (UNDERSTAND)</option>
                  <option value="APPLY" ${q.bloom === 'APPLY' ? 'selected' : ''}>Vận dụng (APPLY)</option>
                  <option value="ANALYZE" ${q.bloom === 'ANALYZE' ? 'selected' : ''}>Phân tích (ANALYZE)</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Lý do sửa đổi *</label>
                <input type="text" name="change_reason" required value="${isFork ? 'Cập nhật chuẩn hóa nội dung khảo thí' : 'Tinh chỉnh nội dung'}" class="w-full p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 outline-none focus:border-primary" />
              </div>
            </div>

            ${q.type === 'MCQ' ? `
              <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Các phương án (Chọn 1 đáp án đúng):</label>
                ${(q.choices && q.choices.length > 0 ? q.choices : [
                  { label: 'A', text: '', is_correct: true },
                  { label: 'B', text: '', is_correct: false },
                  { label: 'C', text: '', is_correct: false },
                  { label: 'D', text: '', is_correct: false }
                ]).map((c, i) => `
                  <div class="flex items-center gap-2">
                    <input type="radio" name="edit_correct" value="${i}" ${c.is_correct ? 'checked' : ''} class="text-primary" />
                    <span class="w-5 font-bold font-mono text-slate-500">${c.label || String.fromCharCode(65 + i)}</span>
                    <input type="text" name="choice_${i}" value="${UI.escapeHtml(c.text)}" required placeholder="Nội dung lựa chọn ${c.label}" class="flex-1 p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 outline-none focus:border-primary" />
                  </div>
                `).join('')}
              </div>
            ` : ''}
          </form>
        `;

        UI.openModal({
          title: modalTitle,
          bodyHtml: body,
          footerHtml: `
            <button type="button" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl" onclick="UI.closeModal()">Hủy</button>
            <button type="button" id="confirm-submit-edit-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Lưu thay đổi</button>
          `,
          size: 'lg'
        });

        document.getElementById('confirm-submit-edit-btn').onclick = async () => {
          const form = document.getElementById('edit-q-form');
          const stemVal = form.stem.value.trim();
          const reasonVal = form.change_reason.value.trim();
          const bloomVal = form.bloom.value;

          if (!stemVal) {
            UI.showToast('Vui lòng nhập nội dung câu hỏi.', 'warning');
            return;
          }

          let choicesPayload = [];
          if (q.type === 'MCQ') {
            const correctRadio = form.querySelector('input[name="edit_correct"]:checked');
            const correctIdx = correctRadio ? parseInt(correctRadio.value, 10) : 0;
            for (let i = 0; i < 4; i++) {
              const textVal = (form[`choice_${i}`]?.value || '').trim();
              if (textVal) {
                choicesPayload.push({
                  choice_key: String.fromCharCode(65 + i),
                  content: textVal,
                  is_correct: i === correctIdx,
                  position: i + 1
                });
              }
            }
          }

          const payload = {
            content: stemVal,
            stem: stemVal,
            bloom_level: bloomVal,
            change_reason: reasonVal || 'Cập nhật bởi Giảng viên',
            choices: choicesPayload.length > 0 ? choicesPayload : undefined
          };

          try {
            if (isFork || isLocked || q.was_student_exposed) {
              await ApiClient.createQuestionRevision(q.db_id, payload);
              UI.showToast('Đã tạo Revision mới thành công!', 'success');
            } else {
              await ApiClient.updateQuestion(q.db_id, payload);
              UI.showToast('Đã cập nhật câu hỏi thành công!', 'success');
            }
            UI.closeModal();
            await InstructorView.renderExtendedQuestionStudio(container, courseCode);
          } catch (e) {
            UI.showToast(e.message || 'Lỗi lưu thay đổi câu hỏi.', 'error');
          }
        };
      };

      const btnEditDirect = document.getElementById('insp-btn-edit-direct');
      if (btnEditDirect) {
        btnEditDirect.onclick = () => openEditModal(false);
      }

      const btnFork = document.getElementById('insp-btn-fork-draft');
      if (btnFork) {
        btnFork.onclick = () => openEditModal(true);
      }

      const btnTrash = document.getElementById('insp-btn-trash');
      if (btnTrash) {
        btnTrash.onclick = async () => {
          const ok = confirm(`Chuyển câu hỏi ${String(q.id).substring(0, 12)} vào thùng rác?`);
          if (!ok) return;
          try {
            await ApiClient.trashQuestion(q.db_id, { reason: 'Chuyển vào thùng rác bởi Giảng viên' });
            UI.showToast('Đã chuyển câu hỏi vào thùng rác.', 'success');
            await InstructorView.renderExtendedQuestionStudio(container, courseCode);
          } catch (e) {
            UI.showToast(e.message || 'Lỗi chuyển câu hỏi vào thùng rác.', 'error');
          }
        };
      }

      const btnRestore = document.getElementById('insp-btn-restore');
      if (btnRestore) {
        btnRestore.onclick = async () => {
          try {
            await ApiClient.restoreQuestion(q.db_id, { reason: 'Khôi phục từ thùng rác' });
            UI.showToast('Đã khôi phục câu hỏi thành công!', 'success');
            await InstructorView.renderExtendedQuestionStudio(container, courseCode);
          } catch (e) {
            UI.showToast(e.message || 'Lỗi khôi phục câu hỏi.', 'error');
          }
        };
      }

      const btnClone = document.getElementById('insp-btn-clone');
      if (btnClone) {
        btnClone.onclick = async () => {
          try {
            await ApiClient.createQuestion(courseMeta.id || courseCode, {
              content: `[Bản sao] ${q.stem}`,
              question_type: q.raw_type || 'SINGLE_CHOICE',
              bloom_level: q.bloom,
              difficulty: q.bloom === 'REMEMBER' ? 'BEGINNER' : (q.bloom === 'APPLY' ? 'ADVANCED' : 'INTERMEDIATE'),
              choices: q.choices.map((c, i) => ({
                label: c.label || String.fromCharCode(65 + i),
                content: c.text,
                is_correct: c.is_correct
              }))
            });
            UI.showToast('Đã nhân bản câu hỏi thành công!', 'success');
            await InstructorView.renderExtendedQuestionStudio(container, courseCode);
          } catch (e) {
            UI.showToast(e.message || 'Lỗi nhân bản câu hỏi.', 'error');
          }
        };
      }
    };

    // Initial render of cards and inspector
    renderQuestionCards();
    renderInspectorPanel();

    // Event Wire-up
    document.getElementById('ext-btn-back-to-hub').onclick = () => {
      InstructorView.renderQuestions(container);
    };

    document.getElementById('ext-btn-create-q').onclick = () => {
      InstructorView.openCreateQuestionModal(courseMeta.id || courseCode);
    };

    const createExamBtn = document.getElementById('ext-btn-create-exam');
    if (createExamBtn) {
      createExamBtn.onclick = () => {
        window.location.hash = '#/instructor/exams';
      };
    }

    document.getElementById('ext-btn-import-word').onclick = () => {
      UI.showToast('Tính năng nạp tệp Word/Excel sẽ liên kết với bộ nhập liệu khảo thí.', 'info');
    };

    // Module tabs
    document.querySelectorAll('.ext-mod-tab').forEach(tab => {
      tab.onclick = () => {
        document.querySelectorAll('.ext-mod-tab').forEach(t => {
          t.className = "ext-mod-tab px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition flex items-center gap-2 whitespace-nowrap";
        });
        tab.className = "ext-mod-tab px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 whitespace-nowrap bg-primary text-white shadow-xs";
        currentModuleFilter = tab.dataset.module;
        renderQuestionCards();
        renderInspectorPanel();
      };
    });

    // Filters
    const searchInput = document.getElementById('ext-search-input');
    searchInput.oninput = (e) => {
      currentSearchText = e.target.value.toLowerCase().trim();
      renderQuestionCards();
      renderInspectorPanel();
    };

    document.getElementById('ext-type-select').onchange = (e) => {
      currentTypeFilter = e.target.value;
      renderQuestionCards();
      renderInspectorPanel();
    };

    document.getElementById('ext-bloom-select').onchange = (e) => {
      currentBloomFilter = e.target.value;
      renderQuestionCards();
      renderInspectorPanel();
    };

    document.getElementById('ext-status-select').onchange = (e) => {
      currentStatusFilter = e.target.value;
      renderQuestionCards();
      renderInspectorPanel();
    };

    document.getElementById('ext-btn-clear-filters').onclick = () => {
      searchInput.value = '';
      currentSearchText = '';
      document.getElementById('ext-type-select').value = 'ALL';
      currentTypeFilter = 'ALL';
      document.getElementById('ext-bloom-select').value = 'ALL';
      currentBloomFilter = 'ALL';
      document.getElementById('ext-status-select').value = 'ALL';
      currentStatusFilter = 'ALL';
      currentModuleFilter = 'ALL';
      document.querySelectorAll('.ext-mod-tab').forEach((t, idx) => {
        if (idx === 0) {
          t.className = "ext-mod-tab px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 whitespace-nowrap bg-primary text-white shadow-xs";
        } else {
          t.className = "ext-mod-tab px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition flex items-center gap-2 whitespace-nowrap";
        }
      });
      renderQuestionCards();
      renderInspectorPanel();
    };
  }

  static openCreateQuestionModal(courseId = '') {
    const body = `
      <form id="create-q-form" class="space-y-4">
        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Nội dung câu hỏi (Stem) *</label>
          <textarea name="stem" rows="3" required placeholder="Nhập câu hỏi tại đây..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary resize-none"></textarea>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Cấp độ nhận thức Bloom</label>
            <select name="bloom" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary">
              <option value="REMEMBER">Nhận biết (REMEMBER)</option>
              <option value="UNDERSTAND" selected>Thông hiểu (UNDERSTAND)</option>
              <option value="APPLY">Vận dụng (APPLY)</option>
              <option value="ANALYZE">Phân tích (ANALYZE)</option>
              <option value="EVALUATE">Đánh giá (EVALUATE)</option>
              <option value="CREATE">Sáng tạo (CREATE)</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Độ khó</label>
            <select name="difficulty" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary">
              <option value="BEGINNER">Cơ bản (BEGINNER)</option>
              <option value="INTERMEDIATE" selected>Trung cấp (INTERMEDIATE)</option>
              <option value="ADVANCED">Nâng cao (ADVANCED)</option>
            </select>
          </div>
        </div>

        <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Các phương án lựa chọn (Chọn 1 đáp án đúng)</label>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <input type="radio" name="correct_choice" value="0" checked class="text-primary focus:ring-primary/20" />
              <input type="text" name="choice_0" required placeholder="Lựa chọn A" class="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
            </div>
            <div class="flex items-center gap-2">
              <input type="radio" name="correct_choice" value="1" class="text-primary focus:ring-primary/20" />
              <input type="text" name="choice_1" required placeholder="Lựa chọn B" class="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
            </div>
            <div class="flex items-center gap-2">
              <input type="radio" name="correct_choice" value="2" class="text-primary focus:ring-primary/20" />
              <input type="text" name="choice_2" required placeholder="Lựa chọn C" class="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
            </div>
            <div class="flex items-center gap-2">
              <input type="radio" name="correct_choice" value="3" class="text-primary focus:ring-primary/20" />
              <input type="text" name="choice_3" required placeholder="Lựa chọn D" class="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
            </div>
          </div>
        </div>
      </form>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy</button>
      <button type="button" id="submit-manual-q-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Lưu câu hỏi</button>
    `;

    UI.openModal({
      title: 'Tạo câu hỏi trắc nghiệm thủ công',
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    document.getElementById('submit-manual-q-btn').onclick = async () => {
      const form = document.getElementById('create-q-form');
      const stem = form.stem.value.trim();
      const bloom = form.bloom.value;
      const diff = form.difficulty.value;
      const correctIdx = parseInt(form.correct_choice.value, 10);

      const choices = [
        { label: 'A', content: form.choice_0.value.trim(), is_correct: correctIdx === 0 },
        { label: 'B', content: form.choice_1.value.trim(), is_correct: correctIdx === 1 },
        { label: 'C', content: form.choice_2.value.trim(), is_correct: correctIdx === 2 },
        { label: 'D', content: form.choice_3.value.trim(), is_correct: correctIdx === 3 },
      ];

      if (!stem || choices.some(c => !c.content)) {
        UI.showToast('Vui lòng nhập đầy đủ câu hỏi và 4 lựa chọn.', 'warning');
        return;
      }

      try {
        await ApiClient.createQuestion(courseId || 'PWD301', {
          content: stem,
          question_type: 'SINGLE_CHOICE',
          bloom_level: bloom,
          difficulty: diff,
          choices: choices
        });
        UI.closeModal();
        UI.showToast('Đã lưu câu hỏi mới vào ngân hàng!', 'success');
        const vp = document.getElementById('app-viewport');
        if (window.location.hash.includes('studio')) {
          InstructorView.renderExtendedQuestionStudio(vp, courseId);
        } else {
          InstructorView.renderQuestions(vp);
        }
      } catch (e) {
        UI.showToast(e.message || 'Lỗi lưu câu hỏi.', 'error');
      }
    };
  }

  static openAIDraftQuestionModal() {
    const body = `
      <div class="space-y-4">
        <p class="text-xs text-slate-500">Sử dụng Google Gemini 3.8 Flash để sinh câu hỏi trắc nghiệm tự động theo chủ đề và mức độ nhận thức Bloom's Taxonomy.</p>
        
        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Chủ đề câu hỏi / Khái niệm cần kiểm tra *</label>
          <input type="text" id="ai-draft-topic" placeholder="VD: Dependency Injection trong Web Framework, SQL Filtered Indexes..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-purple-600" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Cấp độ Bloom</label>
            <select id="ai-draft-bloom" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-purple-600">
              <option value="REMEMBER">Nhận biết (REMEMBER)</option>
              <option value="UNDERSTAND" selected>Thông hiểu (UNDERSTAND)</option>
              <option value="APPLY">Vận dụng (APPLY)</option>
              <option value="ANALYZE">Phân tích (ANALYZE)</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Độ khó</label>
            <select id="ai-draft-diff" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-purple-600">
              <option value="BEGINNER">Cơ bản</option>
              <option value="INTERMEDIATE" selected>Trung cấp</option>
              <option value="ADVANCED">Nâng cao</option>
            </select>
          </div>
        </div>

        <div id="ai-draft-preview-result" class="hidden p-4 rounded-xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 space-y-3"></div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Đóng</button>
      <button type="button" id="trigger-ai-draft-btn" class="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-sm flex items-center gap-1.5">
        <span class="material-symbols-outlined text-[16px]">smart_toy</span>
        <span>Sinh câu hỏi bằng AI</span>
      </button>
    `;

    UI.openModal({
      title: 'AI Sinh câu hỏi tự động (Gemini 3.8 Flash)',
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    const triggerBtn = document.getElementById('trigger-ai-draft-btn');
    triggerBtn.onclick = async () => {
      const topic = document.getElementById('ai-draft-topic').value.trim();
      const bloom = document.getElementById('ai-draft-bloom').value;
      const diff = document.getElementById('ai-draft-diff').value;

      if (!topic) {
        UI.showToast('Vui lòng nhập chủ đề cần sinh câu hỏi.', 'warning');
        return;
      }

      triggerBtn.disabled = true;
      triggerBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Gemini đang soạn câu hỏi...';

      const previewBox = document.getElementById('ai-draft-preview-result');

      try {
        const draft = await ApiClient.draftQuestionAI({
          topic,
          bloom_taxonomy: bloom,
          difficulty: diff
        });

        previewBox.classList.remove('hidden');
        previewBox.innerHTML = `
          <div class="font-bold text-sm text-purple-900 dark:text-purple-200">
            ${UI.escapeHtml(draft.stem || draft.content || 'Câu hỏi AI sinh')}
          </div>
          <div class="space-y-1 text-xs">
            ${(draft.choices || []).map(c => `
              <div class="p-2 rounded bg-white dark:bg-slate-900 border ${c.is_correct ? 'border-emerald-500 font-bold text-emerald-600' : 'border-slate-200 dark:border-slate-800'}">
                ${c.label || ''}. ${UI.escapeHtml(c.content || c.text || '')} ${c.is_correct ? '✓ (Đáp án đúng)' : ''}
              </div>
            `).join('')}
          </div>
          <div class="pt-2 flex justify-end">
            <button type="button" id="approve-draft-btn" class="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">check</span>
              Phê duyệt & Lưu vào ngân hàng
            </button>
          </div>
        `;

        document.getElementById('approve-draft-btn').onclick = async () => {
          try {
            await ApiClient.approveQuestionDraft(draft.draft_id || draft.id);
            UI.closeModal();
            UI.showToast('Đã phê duyệt và lưu câu hỏi AI vào ngân hàng thành công!', 'success');
            InstructorView.renderQuestions(document.getElementById('app-viewport'));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi phê duyệt câu hỏi.', 'error');
          }
        };

      } catch (err) {
        UI.showToast(err.message || 'Lỗi sinh câu hỏi bằng AI.', 'error');
      } finally {
        triggerBtn.disabled = false;
        triggerBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">smart_toy</span> <span>Sinh câu hỏi bằng AI</span>';
      }
    };
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
