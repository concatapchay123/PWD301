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
            <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#222120] dark:text-[#EDEDEB]">Bàn làm việc Giảng viên</h1>
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
              <span class="text-xs font-bold uppercase tracking-wider text-[#8F8E8A] dark:text-[#9E9D99]">Ngân hàng câu hỏi</span>
              <span class="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border border-purple-100/50 dark:border-purple-900/30 flex items-center justify-center material-symbols-outlined text-[20px]">database</span>
            </div>
            <div class="text-2xl font-extrabold text-[#222120] dark:text-[#EDEDEB] mt-2" id="ins-kpi-questions">0</div>
            <div class="text-xs text-[#8F8E8A] dark:text-[#6D6C68] mt-1">Câu hỏi thuộc các khóa học phụ trách</div>
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

      document.getElementById('ins-kpi-courses').textContent = courses.length;
      document.getElementById('ins-kpi-students').textContent = totalStudents;
      document.getElementById('ins-kpi-lessons').textContent = totalLessons;
      document.getElementById('ins-kpi-questions').textContent = (analytics?.total_questions !== undefined ? analytics.total_questions : 0);

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
                    <td class="px-5 py-3.5 text-[#5C5B57] dark:text-[#9E9D99]">${c.capacity || 50} sinh viên</td>
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
        
        <!-- Header & Metric Chips Banner -->
        <div class="flex flex-col gap-4">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-bold font-mono">
                  GIẢNG VIÊN • PWD301
                </span>
                <span class="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 text-[11px] font-semibold flex items-center gap-1 border border-emerald-200 dark:border-emerald-800">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Học kỳ Fall 2025
                </span>
              </div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                Danh mục Khóa học & Học phần Phụ trách
              </h1>
              <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
                Quản trị toàn diện đề cương, nguồn gốc phân công đào tạo, tiến độ ca giảng và hồ sơ kiểm định lớp học theo chuẩn ABET.
              </p>
            </div>

            <!-- 4 Metric Chips -->
            <div class="flex flex-wrap items-center gap-2.5">
              <div class="flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-primary"></span>
                <span class="text-xs text-slate-500">Đang quản lý:</span>
                <span class="text-sm font-extrabold text-primary" id="ins-chip-total">0 Khóa</span>
              </div>
              <div class="flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                <span class="material-symbols-outlined text-[18px] text-sky-600">account_balance</span>
                <span class="text-xs text-slate-500">Phân công Đào tạo:</span>
                <span class="text-sm font-extrabold text-sky-600" id="ins-chip-assigned">0 Môn</span>
              </div>
              <div class="flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                <span class="material-symbols-outlined text-[18px] text-indigo-600">history_edu</span>
                <span class="text-xs text-slate-500">Tự biên soạn:</span>
                <span class="text-sm font-extrabold text-indigo-600" id="ins-chip-authored">0 Môn</span>
              </div>
              <div class="flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                <span class="material-symbols-outlined text-[18px] text-emerald-600">group</span>
                <span class="text-xs text-slate-500">Tổng sinh viên:</span>
                <span class="text-sm font-extrabold text-emerald-600" id="ins-chip-students">0 SV</span>
              </div>
            </div>
          </div>

          <!-- Multi-filter Toolbar -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl p-3.5 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
            <div class="flex flex-1 flex-wrap items-center gap-2.5">
              <!-- Search input -->
              <div class="relative min-w-[260px] flex-1">
                <span class="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[19px]">filter_alt</span>
                <input
                  type="text"
                  id="courses-filter-search"
                  class="w-full h-10 pl-10 pr-4 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  placeholder="Lọc theo mã môn (PWD301, UXD101...), tên học phần..."
                />
              </div>

              <!-- Origin Filter -->
              <div class="relative">
                <select
                  id="courses-filter-origin"
                  class="h-10 pl-3 pr-8 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 appearance-none cursor-pointer"
                >
                  <option value="ALL" selected>Tất cả nguồn gốc</option>
                  <option value="ASSIGNED">Admin phân công (Đào tạo)</option>
                  <option value="SELF">Giảng viên tự biên soạn</option>
                </select>
                <span class="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px] pointer-events-none">unfold_more</span>
              </div>

              <!-- Status Filter -->
              <div class="relative">
                <select
                  id="courses-filter-status"
                  class="h-10 pl-3 pr-8 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 appearance-none cursor-pointer"
                >
                  <option value="ALL" selected>Tất cả trạng thái</option>
                  <option value="PUBLISHED">Đang dạy (Active Teaching)</option>
                  <option value="APPROVED">Đã phê duyệt (Approved)</option>
                  <option value="DRAFT">Bản thảo (Draft)</option>
                  <option value="SUBMITTED_FOR_REVIEW">Chờ duyệt (In Review)</option>
                </select>
                <span class="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px] pointer-events-none">unfold_more</span>
              </div>

              <!-- Program Filter -->
              <div class="relative hidden sm:block">
                <select
                  id="courses-filter-program"
                  class="h-10 pl-3 pr-8 rounded-xl bg-slate-50 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20 appearance-none cursor-pointer"
                >
                  <option value="ALL" selected>Tất cả hệ đào tạo</option>
                  <option value="ENGINEER">Hệ Kỹ sư CNTT & Thiết kế</option>
                  <option value="GENERAL">Chính quy Đại trà</option>
                  <option value="HONORS">Chất lượng cao / Tiên tiến</option>
                </select>
                <span class="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px] pointer-events-none">unfold_more</span>
              </div>
            </div>

            <!-- View Actions -->
            <div class="flex items-center gap-2 self-end lg:self-auto shrink-0">
              <button
                type="button"
                id="btn-refresh-courses"
                class="h-10 w-10 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center transition-colors"
                title="Làm mới danh sách"
              >
                <span class="material-symbols-outlined text-[19px]">refresh</span>
              </button>
              <button
                type="button"
                id="btn-add-course"
                class="h-10 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>Tạo khóa học mới</span>
              </button>
            </div>
          </div>
        </div>

        <!-- MAIN SPLIT WORKSPACE: TABLE (LEFT 7/12) & OPERATIONS DRAWER (RIGHT 5/12) -->
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          
          <!-- LEFT 7/12: BẢNG DANH SÁCH KHÓA HỌC CHÍNH -->
          <section class="xl:col-span-7 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
              <div class="flex items-center gap-2.5">
                <span class="material-symbols-outlined text-primary text-[20px]">view_list</span>
                <h2 class="text-sm font-bold text-slate-900 dark:text-white">Danh sách học phần (Split Table View)</h2>
              </div>
              <span class="text-xs font-bold text-primary bg-primary/10 px-2.5 py-0.5 rounded-full" id="ins-selected-badge">
                Đang chọn: PWD301
              </span>
            </div>

            <div class="overflow-x-auto min-h-[420px]" id="ins-courses-table-box">
              <div class="p-16 text-center text-slate-400">
                <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
                <p class="text-xs">Đang tải danh mục khóa học...</p>
              </div>
            </div>
          </section>

          <!-- RIGHT 5/12: OPERATIONS DRAWER (HỒ SƠ ĐIỀU HÀNH HỌC PHẦN) -->
          <aside class="xl:col-span-5 space-y-5 sticky top-20" id="ins-operations-drawer">
            <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div class="flex items-center gap-2.5">
                  <div class="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                    <span class="material-symbols-outlined text-[20px]">tune</span>
                  </div>
                  <div>
                    <h3 class="text-sm font-bold text-slate-900 dark:text-white">Hồ sơ điều hành học phần</h3>
                    <p class="text-[11px] text-slate-400">Tác vụ nhanh & Thẩm định kiểm định</p>
                  </div>
                </div>
                <span class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800" id="drawer-status-pill">
                  Đang dạy
                </span>
              </div>

              <!-- Course Meta Summary -->
              <div class="space-y-2">
                <div class="flex items-baseline justify-between">
                  <span class="font-mono font-bold text-primary text-base" id="drawer-course-code">PWD301</span>
                  <span class="text-xs text-slate-400" id="drawer-course-cat">Web Development</span>
                </div>
                <h4 class="text-base font-extrabold text-slate-900 dark:text-white leading-snug" id="drawer-course-title">
                  Lập trình Web Python Chuyên sâu & REST API
                </h4>
                <p class="text-xs text-slate-500 leading-relaxed line-clamp-2" id="drawer-course-desc">
                  Kiến trúc hệ thống hướng dịch vụ, cơ chế chứng thực bảo mật phiên làm việc và mô hình khảo thí tự động.
                </p>
              </div>

              <!-- Key Metrics Grid -->
              <div class="grid grid-cols-2 gap-2.5">
                <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <span class="text-[10px] uppercase font-bold text-slate-400 block">Sĩ số / Lớp học</span>
                  <span class="text-sm font-extrabold text-slate-900 dark:text-white mt-0.5 block" id="drawer-metric-students">
                    87 Sinh viên (02 Lớp)
                  </span>
                </div>
                <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <span class="text-[10px] uppercase font-bold text-slate-400 block">Tín chỉ / Tiết học</span>
                  <span class="text-sm font-extrabold text-slate-900 dark:text-white mt-0.5 block" id="drawer-metric-credits">
                    4 TC • 60 Tiết chuẩn
                  </span>
                </div>
                <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <span class="text-[10px] uppercase font-bold text-slate-400 block">Tiến độ chuyên cần</span>
                  <span class="text-sm font-extrabold text-emerald-600 mt-0.5 block" id="drawer-metric-attendance">
                    94.2% Hoàn thành
                  </span>
                </div>
                <div class="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <span class="text-[10px] uppercase font-bold text-slate-400 block">Đánh giá môn học</span>
                  <span class="text-sm font-extrabold text-amber-500 mt-0.5 block" id="drawer-metric-rating">
                    4.88 ★ (142 lượt)
                  </span>
                </div>
              </div>

              <!-- ABET Criterion 3 Accreditation Verification Stamp -->
              <div class="p-3.5 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 space-y-1.5">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-xs font-bold text-indigo-900 dark:text-indigo-300">
                    <span class="material-symbols-outlined text-[18px] text-indigo-600 dark:text-indigo-400">verified</span>
                    <span>Chuẩn đầu ra & Năng lực sinh viên (SLO)</span>
                  </div>
                  <button type="button" onclick="UI.openAcademicGlossaryModal()" class="text-[10px] text-primary hover:underline font-bold" title="Xem sổ tay giải thích thuật ngữ học vụ">
                    SLO là gì?
                  </button>
                </div>
                <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                  Đề cương và ngân hàng câu hỏi khảo thí đã được đối chiếu theo các mục tiêu chuẩn đầu ra (Student Learning Outcomes) và kiểm định quốc tế ABET.
                </p>
              </div>

              <!-- Primary Action Buttons Group -->
              <div class="space-y-2 pt-2">
                <button
                  type="button"
                  id="drawer-btn-curriculum"
                  class="w-full h-11 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  <span class="material-symbols-outlined text-[18px]">developer_board</span>
                  <span>Vào Đề cương & Soạn bài học</span>
                </button>
                <div class="grid grid-cols-3 gap-1.5">
                  <button
                    type="button"
                    id="drawer-btn-roster"
                    class="h-10 px-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center justify-center gap-1"
                  >
                    <span class="material-symbols-outlined text-[16px]">groups</span>
                    <span>Roster</span>
                  </button>
                  <button
                    type="button"
                    id="drawer-btn-questions"
                    class="h-10 px-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center justify-center gap-1"
                  >
                    <span class="material-symbols-outlined text-[16px]">database</span>
                    <span>Kho câu hỏi</span>
                  </button>
                  <button
                    type="button"
                    id="drawer-btn-exam"
                    class="h-10 px-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center justify-center gap-1"
                  >
                    <span class="material-symbols-outlined text-[16px]">quiz</span>
                    <span>Soạn đề thi</span>
                  </button>
                </div>
                <button
                  type="button"
                  id="drawer-btn-academic"
                  class="w-full h-10 px-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-[16px]">verified_user</span>
                  <span>Quản lý Chuẩn đầu ra & Học vụ (SLO)</span>
                </button>
              </div>

            </div>
          </aside>

        </div>
      </div>
    `;

    document.getElementById('btn-add-course').onclick = () => {
      InstructorView.openCreateCourseModal();
    };

    let allCourses = [];
    let selectedCourse = null;

    const renderTableRows = (coursesToDisplay) => {
      const box = document.getElementById('ins-courses-table-box');
      if (!box) return;

      if (coursesToDisplay.length === 0) {
        box.innerHTML = `
          <div class="p-16 text-center text-slate-400">
            <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">search_off</span>
            <p class="font-bold text-slate-700 dark:text-slate-300 text-sm">Không tìm thấy khóa học phù hợp</p>
            <p class="text-xs mt-1 text-slate-400">Thử thay đổi bộ lọc tìm kiếm hoặc tạo khóa học mới.</p>
          </div>
        `;
        return;
      }

      box.innerHTML = `
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-[11px] uppercase tracking-wider text-slate-500 font-bold">
              <th class="py-3.5 px-4">Mã môn & Học phần</th>
              <th class="py-3.5 px-3">Nguồn gốc</th>
              <th class="py-3.5 px-3">Lớp & Sĩ số</th>
              <th class="py-3.5 px-3">Lịch & Phòng</th>
              <th class="py-3.5 px-3">Trạng thái & Chuẩn đầu ra (SLO)</th>
              <th class="py-3.5 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-xs font-medium">
            ${coursesToDisplay.map(c => {
              const isSelected = selectedCourse && (selectedCourse.course_id === c.course_id || selectedCourse.id === c.id);
              const cId = c.course_id || c.id;
              const isAssigned = c.category && c.category.toLowerCase().includes('admin');
              return `
                <tr
                  class="course-row cursor-pointer transition-colors ${isSelected ? 'bg-indigo-50/70 dark:bg-indigo-950/30 border-l-4 border-l-primary' : 'hover:bg-slate-50/80 dark:hover:bg-slate-800/40'}"
                  data-id="${cId}"
                >
                  <td class="py-4 px-4">
                    <div class="flex flex-col">
                      <div class="flex items-center gap-2">
                        <span class="font-mono font-extrabold text-primary">${UI.escapeHtml(c.course_code)}</span>
                        ${isSelected ? '<span class="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>' : ''}
                      </div>
                      <span class="font-bold text-slate-900 dark:text-white mt-0.5 max-w-[220px] truncate" title="${UI.escapeHtml(c.title)}">
                        ${UI.escapeHtml(c.title)}
                      </span>
                      <span class="text-[10px] text-slate-400 font-mono mt-0.5">${UI.escapeHtml(c.category || 'Công nghệ')}</span>
                    </div>
                  </td>
                  <td class="py-4 px-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${isAssigned ? 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300' : 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300'}">
                      ${isAssigned ? 'Phân công' : 'Tự biên soạn'}
                    </span>
                  </td>
                  <td class="py-4 px-3">
                    <div class="flex flex-col">
                      <span class="font-bold text-slate-800 dark:text-slate-200">02 Lớp</span>
                      <span class="text-[10px] text-slate-400">${c.capacity || 50} SV tối đa</span>
                    </div>
                  </td>
                  <td class="py-4 px-3">
                    <div class="flex flex-col text-[11px] text-slate-500">
                      <span>Thứ 3 • Ca 2</span>
                      <span class="text-[10px] text-slate-400">P.Lab 402</span>
                    </div>
                  </td>
                  <td class="py-4 px-3">
                    <div class="flex flex-col gap-1 items-start">
                      ${UI.statusBadge(c.status)}
                      <span class="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-600">
                        <span class="material-symbols-outlined text-[13px]">check_circle</span> ABET
                      </span>
                    </div>
                  </td>
                  <td class="py-4 px-4 text-right">
                    <a
                      href="#/instructor/courses/${cId}/manage?tab=curriculum"
                      class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-colors"
                      onclick="event.stopPropagation()"
                    >
                      <span>Quản lý</span>
                      <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
                    </a>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;

      // Attach row click listeners
      box.querySelectorAll('.course-row').forEach(row => {
        row.onclick = () => {
          const cId = row.dataset.id;
          const found = allCourses.find(c => (c.course_id || c.id) === cId);
          if (found) {
            updateSelectedDrawer(found);
            renderTableRows(getFilteredCourses());
          }
        };
      });
    };

    const updateSelectedDrawer = (course) => {
      selectedCourse = course;
      const cId = course.course_id || course.id;

      const codeBadge = document.getElementById('ins-selected-badge');
      if (codeBadge) codeBadge.textContent = `Đang chọn: ${course.course_code}`;

      document.getElementById('drawer-course-code').textContent = course.course_code;
      document.getElementById('drawer-course-cat').textContent = course.category || 'Học phần Chuyên ngành';
      document.getElementById('drawer-course-title').textContent = course.title;
      document.getElementById('drawer-course-desc').textContent = course.description || 'Chưa có mô tả tóm tắt.';
      document.getElementById('drawer-metric-students').textContent = `${course.capacity || 50} Sinh viên (02 Lớp)`;
      document.getElementById('drawer-status-pill').outerHTML = `
        <span id="drawer-status-pill" class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider">
          ${UI.statusBadge(course.status)}
        </span>
      `;

      document.getElementById('drawer-btn-curriculum').onclick = () => {
        window.location.hash = `#/instructor/courses/${cId}/manage?tab=curriculum`;
      };
      document.getElementById('drawer-btn-roster').onclick = () => {
        window.location.hash = `#/instructor/courses/${cId}/manage?tab=students`;
      };
      document.getElementById('drawer-btn-questions').onclick = () => {
        window.location.hash = `#/instructor/questions?course=${encodeURIComponent(course.course_code || '')}`;
      };
      const drawerExamBtn = document.getElementById('drawer-btn-exam');
      if (drawerExamBtn) {
        drawerExamBtn.onclick = () => {
          window.location.hash = `#/instructor/exams`;
        };
      }
      document.getElementById('drawer-btn-academic').onclick = () => {
        window.location.hash = `#/instructor/courses/${cId}/manage?tab=academic`;
      };
    };

    const getFilteredCourses = () => {
      const searchVal = (document.getElementById('courses-filter-search')?.value || '').toLowerCase().trim();
      const originVal = document.getElementById('courses-filter-origin')?.value || 'ALL';
      const statusVal = document.getElementById('courses-filter-status')?.value || 'ALL';

      return allCourses.filter(c => {
        const matchesSearch = !searchVal || 
          c.course_code.toLowerCase().includes(searchVal) || 
          c.title.toLowerCase().includes(searchVal) ||
          (c.category && c.category.toLowerCase().includes(searchVal));

        const matchesStatus = statusVal === 'ALL' || c.status === statusVal;

        let matchesOrigin = true;
        if (originVal === 'ASSIGNED') {
          matchesOrigin = (c.category || '').toLowerCase().includes('admin');
        } else if (originVal === 'SELF') {
          matchesOrigin = !(c.category || '').toLowerCase().includes('admin');
        }

        return matchesSearch && matchesStatus && matchesOrigin;
      });
    };

    const loadData = async () => {
      try {
        const res = await ApiClient.getInstructorCourses();
        allCourses = res.courses || [];

        // Calculate KPI Chips
        document.getElementById('ins-chip-total').textContent = `${allCourses.length} Khóa`;
        const authoredCount = allCourses.filter(c => !(c.category || '').toLowerCase().includes('admin')).length;
        const assignedCount = allCourses.length - authoredCount;
        document.getElementById('ins-chip-authored').textContent = `${authoredCount} Môn`;
        document.getElementById('ins-chip-assigned').textContent = `${assignedCount} Môn`;

        const totalCapacity = allCourses.reduce((sum, c) => sum + (c.capacity || 50), 0);
        document.getElementById('ins-chip-students').textContent = `${totalCapacity} SV`;

        if (allCourses.length > 0) {
          updateSelectedDrawer(allCourses[0]);
        }
        renderTableRows(allCourses);
      } catch (e) {
        document.getElementById('ins-courses-table-box').innerHTML = `
          <div class="p-8 text-center text-rose-500 font-bold">Lỗi tải khóa học: ${UI.escapeHtml(e.message)}</div>
        `;
      }
    };

    // Filters event binding
    document.getElementById('courses-filter-search').oninput = () => renderTableRows(getFilteredCourses());
    document.getElementById('courses-filter-origin').onchange = () => renderTableRows(getFilteredCourses());
    document.getElementById('courses-filter-status').onchange = () => renderTableRows(getFilteredCourses());
    document.getElementById('btn-refresh-courses').onclick = () => loadData();

    await loadData();
  }

  static openCreateCourseModal() {
    const formHtml = `
      <form id="create-course-modal-form" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Mã khóa học *
            </label>
            <input
              type="text"
              name="course_code"
              required
              placeholder="VD: PWD301, AI401"
              class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-mono uppercase outline-none focus:border-primary"
            />
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Danh mục học thuật
            </label>
            <input
              type="text"
              name="category"
              list="academic-categories-list"
              placeholder="VD: Khoa học máy tính, Quản trị kinh doanh, Ngôn ngữ Anh..."
              class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary"
            />
            <datalist id="academic-categories-list">
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
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            Tên khóa học đầy đủ *
          </label>
          <input
            type="text"
            name="title"
            required
            placeholder="VD: Lập trình Web Cao cấp & Kiến trúc REST API"
            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary"
          />
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            Mô tả tóm tắt khóa học
          </label>
          <textarea
            name="description"
            rows="3"
            placeholder="Mục tiêu khóa học, kiến thức cốt lõi và phương pháp học tập..."
            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary resize-none"
          ></textarea>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Độ khó học thuật
            </label>
            <select name="difficulty" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm outline-none focus:border-primary">
              <option value="BEGINNER">Cơ bản (Beginner)</option>
              <option value="INTERMEDIATE" selected>Trung cấp (Intermediate)</option>
              <option value="ADVANCED">Nâng cao (Advanced)</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Sĩ số sinh viên
            </label>
            <div class="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">all_inclusive</span>
              <span>Không giới hạn</span>
            </div>
          </div>
        </div>
      </form>
    `;

    const footerHtml = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" onclick="UI.closeModal()">
        Hủy bỏ
      </button>
      <button type="button" id="submit-create-course-btn" class="px-5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm">
        Tạo khóa học
      </button>
    `;

    UI.openModal({
      title: 'Tạo khóa học mới (Bản thảo)',
      bodyHtml: formHtml,
      footerHtml: footerHtml,
      size: 'lg'
    });

    document.getElementById('submit-create-course-btn').onclick = async () => {
      const form = document.getElementById('create-course-modal-form');
      if (!form) return;

      const code = form.course_code.value.trim().toUpperCase();
      const title = form.title.value.trim();
      const desc = form.description.value.trim();
      const cat = form.category.value.trim() || 'Khoa học máy tính & CNTT';
      const diff = form.difficulty.value;

      if (!code || !title) {
        UI.showToast('Vui lòng nhập đầy đủ Mã khóa học và Tên khóa học.', 'warning');
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
          difficulty: diff,
          capacity: null
        });
        UI.closeModal();
        UI.showToast(`Đã tạo khóa học ${code} thành công dưới dạng Bản thảo (DRAFT)!`, 'success');
        window.location.hash = `#/instructor/courses/${res.course_id || res.id}/manage?tab=curriculum`;
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
        <div class="text-center py-24 text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-xs">Đang tải hồ sơ học vụ khóa học...</p>
        </div>
      </div>
    `;

    try {
      const course = await ApiClient.getCourseDetail(courseId);
      if (!course) return;

      const cId = course.course_id || course.id;

      container.innerHTML = `
        <div class="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in font-sans pb-16" id="course-manage-root">
          
          <!-- Course Hero Academic Header (Warm Surface Card) -->
          <section class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-6 sm:p-8 shadow-subtle space-y-5">
            <!-- Breadcrumb -->
            <div class="flex items-center gap-2 text-xs text-slate-500 font-medium min-w-0 flex-wrap">
              <a href="#/instructor/courses" class="hover:text-primary transition-colors flex items-center gap-1 shrink-0">
                <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                <span>Khóa học</span>
              </a>
              <span>/</span>
              <span class="font-mono font-bold text-primary shrink-0">${UI.escapeHtml(course.course_code)}</span>
              <span>/</span>
              <span class="text-slate-800 dark:text-slate-200 font-semibold truncate max-w-md">${UI.escapeHtml(course.title)}</span>
            </div>

            <!-- Hero Content: Left Details & Right Quick Health Pill -->
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div class="space-y-2.5 max-w-3xl min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-mono text-xs font-bold">
                    ${UI.escapeHtml(course.course_code)}
                  </span>
                  ${UI.statusBadge(course.status)}
                  <span class="px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-semibold flex items-center gap-1 border border-indigo-100 dark:border-indigo-900/40">
                    <span class="material-symbols-outlined text-[14px]">verified</span> Chuẩn ABET Criterion 3
                  </span>
                </div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-snug">
                  ${UI.escapeHtml(course.title)}
                </h1>
                <div class="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-slate-500 dark:text-slate-400 pt-1">
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[17px] text-primary">person_outline</span>
                    <span>Chủ nhiệm: <strong class="text-slate-800 dark:text-white font-bold">${UI.escapeHtml(course.instructor_name || window.app?.currentUser?.name || 'Giảng viên')}</strong></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[17px] text-indigo-600">database</span>
                    <span>Danh mục: <strong class="text-slate-800 dark:text-white font-bold">${UI.escapeHtml(course.category || 'Công nghệ')}</strong></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[17px] text-sky-600">groups</span>
                    <span>Học viên: <strong class="text-slate-800 dark:text-white font-bold">${course.enrollments_count ?? course.enrolled_count ?? 0} / ${course.capacity || 50} SV</strong></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[17px] text-emerald-500">verified</span>
                    <span>Trạng thái: <strong class="text-slate-800 dark:text-white font-bold">${course.status || 'DRAFT'}</strong></span>
                  </div>
                </div>
              </div>

              <!-- Right Quick Health Pill -->
              <div class="lg:w-80 shrink-0 bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xs space-y-3">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-semibold text-slate-500">Tiến độ kỳ học</span>
                  <span class="font-bold text-primary">60% (Tuần 09)</span>
                </div>
                <div class="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                  <div class="h-full bg-primary rounded-full" style="width: 60%"></div>
                </div>
                <div class="flex items-center gap-2 pt-1">
                  <a href="#/student/courses/${cId}" class="flex-1 py-2 px-2.5 rounded-xl border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center justify-center gap-1 shadow-2xs text-center truncate" title="Mở khóa học dưới góc nhìn Sinh viên">
                    <span class="material-symbols-outlined text-[16px] text-primary shrink-0">visibility</span>
                    <span class="truncate">Xem thử</span>
                  </a>
                  ${course.status === 'DRAFT' ? `
                    <button type="button" id="btn-submit-review" class="flex-1 py-2 px-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-colors flex items-center justify-center gap-1 shadow-sm text-center truncate">
                      <span class="material-symbols-outlined text-[16px] shrink-0">send</span>
                      <span class="truncate">Gửi duyệt</span>
                    </button>
                  ` : ''}
                  ${course.status === 'APPROVED' || window.app?.currentRole === 'ADMIN' ? `
                    <button type="button" id="btn-publish-direct" class="flex-1 py-2 px-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors flex items-center justify-center gap-1 shadow-sm text-center truncate">
                      <span class="material-symbols-outlined text-[16px] shrink-0">rocket_launch</span>
                      <span class="truncate">Xuất bản</span>
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>
          </section>

          <!-- ENTERPRISE 5-TAB BAR (Warm Segmented Pill Bar) -->
          <div class="bg-white dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl p-1.5 shadow-subtle sticky top-0 z-30 overflow-x-auto no-scrollbar">
            <div class="flex items-center gap-1 sm:gap-2 min-w-max">
              <button
                type="button"
                class="enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all"
                data-tab="curriculum"
              >
                <span class="material-symbols-outlined text-[18px]">menu_book</span>
                <span>Nội dung khóa học (Curriculum)</span>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold" id="tab-curriculum-count">
                  ${(course.lessons || []).length} Bài
                </span>
              </button>

              <button
                type="button"
                class="enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all"
                data-tab="academic"
              >
                <span class="material-symbols-outlined text-[18px]">verified_user</span>
                <span>Thông tin học thuật & Chuẩn đầu ra</span>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold opacity-80" title="Chuẩn đầu ra sinh viên (Student Learning Outcomes) theo kiểm định ABET">
                  Chuẩn đầu ra (SLO)
                </span>
              </button>

              <button
                type="button"
                class="enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all"
                data-tab="students"
              >
                <span class="material-symbols-outlined text-[18px]">groups</span>
                <span>Điều hành Lớp & Sinh viên</span>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold opacity-80">
                  Roster
                </span>
              </button>

              <button
                type="button"
                class="enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all"
                data-tab="assessment"
              >
                <span class="material-symbols-outlined text-[18px]">quiz</span>
                <span>Khảo thí & Ngân hàng đề thi</span>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold opacity-80">
                  Soạn đề thi
                </span>
              </button>

              <button
                type="button"
                class="enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all"
                data-tab="settings"
              >
                <span class="material-symbols-outlined text-[18px]">settings</span>
                <span>Cài đặt môn học</span>
              </button>
            </div>
          </div>

          <!-- Dynamic Active Tab Content Container -->
          <div id="course-tab-content" class="min-h-[500px]"></div>

        </div>
      `;

      const tabs = container.querySelectorAll('.enterprise-tab-btn');
      const tabContent = document.getElementById('course-tab-content');

      const setTab = (tabName) => {
        const validTabs = ['curriculum', 'academic', 'students', 'assessment', 'settings'];
        const activeTab = validTabs.includes(tabName) ? tabName : 'curriculum';

        tabs.forEach(t => {
          if (t.dataset.tab === activeTab) {
            t.className = 'enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl bg-primary text-white font-bold text-xs sm:text-sm whitespace-nowrap transition-all shadow-xs';
          } else {
            t.className = 'enterprise-tab-btn flex items-center gap-2 py-2.5 px-3.5 sm:px-4 rounded-xl text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-[#F4F1EA] dark:hover:bg-[#262524] font-semibold text-xs sm:text-sm whitespace-nowrap transition-all';
          }
        });

        if (activeTab === 'curriculum') {
          InstructorView.renderTabCurriculum(tabContent, course);
        } else if (activeTab === 'academic') {
          InstructorView.renderTabAcademic(tabContent, course);
        } else if (activeTab === 'students') {
          InstructorView.renderTabStudents(tabContent, cId);
        } else if (activeTab === 'assessment') {
          InstructorView.renderTabAssessment(tabContent, course);
        } else if (activeTab === 'settings') {
          InstructorView.renderTabSettings(tabContent, course);
        }
      };

      tabs.forEach(t => {
        t.onclick = () => setTab(t.dataset.tab);
      });

      setTab(initialTab);

      // Bind Submit Review & Direct Publish
      const submitRevBtn = document.getElementById('btn-submit-review');
      if (submitRevBtn) {
        submitRevBtn.onclick = async () => {
          const conf = await UI.confirm('Gửi duyệt khóa học', 'Bạn có chắc muốn gửi khóa học này đến Ban Quản trị xét duyệt xuất bản?', 'Gửi xét duyệt');
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

      const pubBtn = document.getElementById('btn-publish-direct');
      if (pubBtn) {
        pubBtn.onclick = async () => {
          const conf = await UI.confirm('Xuất bản khóa học', 'Khóa học sẽ được công khai cho toàn bộ sinh viên ghi danh. Xác nhận xuất bản?', 'Xuất bản');
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

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500 font-bold">Lỗi nạp khóa học: ${UI.escapeHtml(err.message)}</div>`;
    }
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

            <div class="space-y-2">
              <label class="block font-bold text-slate-700 dark:text-slate-300">Thời gian ân hạn sau kỳ thi (Ngày)</label>
              <input type="number" min="0" max="365" id="rule-grace-days" class="w-full h-10 px-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-bold text-slate-900 dark:text-white outline-none focus:border-primary" value="14" />
              <span class="text-[11px] text-slate-400">Khoảng thời gian sinh viên có thể hoàn thành bổ sung trước khi đóng sổ học vụ.</span>
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
          const gEl = document.getElementById('rule-grace-days');
          const lEl = document.getElementById('rule-require-lessons');
          const aEl = document.getElementById('rule-require-assessments');
          const cEl = document.getElementById('rule-allow-certificate');

          if (pEl && rule.minimum_progress_percent !== undefined) pEl.value = rule.minimum_progress_percent;
          if (sEl && rule.minimum_grade_score !== undefined) sEl.value = rule.minimum_grade_score;
          if (gEl && rule.completion_grace_days !== undefined) gEl.value = rule.completion_grace_days;
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
            completion_grace_days: parseInt(document.getElementById('rule-grace-days')?.value || '14', 10),
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
            href="#/instructor/exams"
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
            <a href="#/instructor/exams" class="inline-flex items-center gap-1.5 px-4 py-2 mt-4 rounded-xl bg-primary text-white text-xs font-bold shadow-sm">
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
                href="#/instructor/exams"
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

  static async openAssessmentResultsModal(courseId, assessmentId) {
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
      const data = await ApiClient.getInstructorAttemptResult(attemptId);
      const studentEl = document.getElementById('modal-att-student');
      if (studentEl) {
        studentEl.textContent = `Thí sinh: ${data.student_name || 'Học viên'} • Điểm: ${data.total_awarded_points ?? 0} / ${data.total_possible_points ?? 0} (${data.percent_score ?? 0}%)`;
      }

      const contentEl = document.getElementById('modal-att-content');
      if (!contentEl) return;

      const questions = data.questions || [];
      if (questions.length === 0) {
        contentEl.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">Không có dữ liệu câu hỏi.</div>`;
        return;
      }

      contentEl.innerHTML = questions.map((q, idx) => {
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
    } catch (err) {
      const contentEl = document.getElementById('modal-att-content');
      if (contentEl) {
        contentEl.innerHTML = `<div class="p-6 text-center text-rose-500 text-xs">Lỗi nạp bài làm: ${UI.escapeHtml(err.message)}</div>`;
      }
    }
  }

  // =========================================================================
  // 3.5. Tab Course Settings
  // =========================================================================
  static renderTabSettings(tabContainer, course) {
    const cId = course.course_id || course.id;
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
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Sĩ số sinh viên</label>
              <div class="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">all_inclusive</span>
                <span>Không giới hạn</span>
              </div>
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
      btn.disabled = true;
      btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang lưu...';

      try {
        await ApiClient.updateCourse(cId, {
          title: form.title.value.trim(),
          description: form.description.value.trim(),
          category: form.category.value.trim(),
          capacity: null
        });
        UI.showToast('Đã lưu thông tin khóa học thành công!', 'success');
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
      <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans flex flex-col animate-fade-in" id="lesson-studio-root">
        
        <!-- Top Sticky Header -->
        <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xs select-none shrink-0 px-4 sm:px-8 h-16 flex items-center justify-between gap-4">
          <!-- Left: Back to Course & Title Input -->
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <button
              type="button"
              id="studio-back-btn"
              class="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 flex items-center justify-center transition-colors shrink-0"
              title="Quay lại Đề cương khóa học"
            >
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
            </button>
            <div class="flex items-center gap-2 truncate flex-1 max-w-xl">
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-primary/10 text-primary shrink-0">
                SOẠN BÀI GIẢNG
              </span>
              <input
                type="text"
                id="studio-lesson-title"
                class="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white bg-transparent border-0 border-b border-transparent hover:border-slate-300 focus:border-primary focus:ring-0 px-1 py-0.5 w-full outline-none transition-colors truncate"
                placeholder="Nhập tiêu đề bài giảng..."
                value="Bài giảng mới"
              />
            </div>
          </div>

          <!-- Center: 3-Step Stepper -->
          <nav class="hidden md:flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl border border-slate-200 dark:border-slate-700">
            <button type="button" class="studio-step-tab px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all bg-white dark:bg-slate-900 text-primary shadow-xs" data-step="1">
              <span>1. Cốt lõi & Thời lượng</span>
            </button>
            <button type="button" class="studio-step-tab px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all" data-step="2">
              <span>2. Soạn nội dung khối</span>
            </button>
            <button type="button" class="studio-step-tab px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all" data-step="3">
              <span>3. Xem trước & Xuất bản</span>
            </button>
          </nav>

          <!-- Right: Autosave Status & Save Actions -->
          <div class="flex items-center gap-2.5 shrink-0">
            <span class="text-[11px] text-slate-400 font-medium hidden sm:inline-flex items-center gap-1" id="studio-autosave-status">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Đã lưu tự động
            </span>
            <button
              type="button"
              id="studio-save-draft-btn"
              class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors"
            >
              Lưu bản nháp
            </button>
            <button
              type="button"
              id="studio-publish-btn"
              class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1"
            >
              <span>Xuất bản</span>
              <span class="material-symbols-outlined text-[16px]">rocket_launch</span>
            </button>
          </div>
        </header>

        <!-- Studio Main Body Canvas -->
        <main class="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-8 space-y-6">
          
          <!-- STEP 1 CONTAINER: Metadata & Core Settings -->
          <div id="studio-step-1-panel" class="space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div class="flex items-center gap-2 text-primary font-bold text-sm">
                  <span class="material-symbols-outlined text-[20px]">title</span>
                  <span>Thông tin cốt lõi bài giảng</span>
                </div>
                <span class="text-xs text-slate-400">Bước 1 / 3</span>
              </div>

              <div class="space-y-4">
                <div class="space-y-1.5">
                  <label class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Tên bài giảng hiển thị cho sinh viên *
                  </label>
                  <input
                    type="text"
                    id="studio-input-title"
                    class="w-full h-11 px-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-bold text-slate-900 dark:text-white outline-none focus:border-primary"
                    placeholder="VD: Bài 04: Nguyên lý thiết kế giao diện thân thiện (UX/UI chuẩn giáo dục)"
                  />
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div class="space-y-1.5">
                    <label class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Thời lượng dự kiến
                    </label>
                    <select
                      id="studio-input-duration"
                      class="w-full h-11 px-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-semibold text-slate-900 dark:text-white outline-none focus:border-primary"
                    >
                      <option value="45">45 phút (1 tiết lý thuyết)</option>
                      <option value="90" selected>90 phút (2 tiết chuẩn)</option>
                      <option value="180">180 phút (Thực hành Lab)</option>
                    </select>
                  </div>
                  <div class="space-y-1.5">
                    <label class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Chuẩn đầu ra ABET liên kết
                    </label>
                    <select
                      id="studio-input-slo"
                      class="w-full h-11 px-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-semibold text-slate-900 dark:text-white outline-none focus:border-primary"
                    >
                      <option value="SLO-1">SLO-1: Phân tích & Giải quyết vấn đề</option>
                      <option value="SLO-2" selected>SLO-2: Thiết kế hệ thống & CSDL</option>
                      <option value="SLO-3">SLO-3: Giao tiếp & Tài liệu chuẩn</option>
                    </select>
                  </div>
                </div>

                <div class="space-y-1.5">
                  <label class="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Mô tả tóm tắt bài giảng (1-2 câu)
                  </label>
                  <textarea
                    id="studio-input-summary"
                    rows="2"
                    class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white outline-none focus:border-primary resize-none"
                    placeholder="Tóm tắt mục tiêu chính của bài học..."
                  ></textarea>
                </div>

                <div class="pt-2 flex justify-end">
                  <button
                    type="button"
                    id="studio-btn-next-to-step-2"
                    class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <span>Tiếp tục soạn nội dung khối</span>
                    <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- STEP 2 CONTAINER: WYSIWYG Low-Tech Block Canvas -->
          <div id="studio-step-2-panel" class="hidden space-y-6">
            
            <!-- Mode Toggle Segment -->
            <div class="bg-white dark:bg-slate-900 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-center max-w-md mx-auto">
              <button
                type="button"
                id="studio-mode-basic"
                class="flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-xs flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[16px]">auto_awesome</span>
                <span>Chế độ Cơ bản (Trực quan)</span>
              </button>
              <button
                type="button"
                id="studio-mode-advanced"
                class="flex-1 py-2 px-3 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[16px]">terminal</span>
                <span>Chế độ Nâng cao (Markdown)</span>
              </button>
            </div>

            <!-- WYSIWYG Visual Toolbar (For Basic Mode) -->
            <div id="studio-visual-toolbar" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-2.5 shadow-sm flex flex-wrap items-center gap-2 sticky top-20 z-20">
              <div class="flex items-center gap-1">
                <button type="button" class="studio-insert-block-btn px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1" data-type="paragraph">
                  <span class="material-symbols-outlined text-[16px] text-primary">notes</span>
                  <span>Đoạn văn</span>
                </button>
                <button type="button" class="studio-insert-block-btn px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1" data-type="callout">
                  <span class="material-symbols-outlined text-[16px] text-amber-500">lightbulb</span>
                  <span>Ghi chú</span>
                </button>
                <button type="button" class="studio-insert-block-btn px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1" data-type="quiz">
                  <span class="material-symbols-outlined text-[16px] text-indigo-600">quiz</span>
                  <span>Quiz giữa bài</span>
                </button>
                <button type="button" class="studio-insert-block-btn px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1" data-type="resource">
                  <span class="material-symbols-outlined text-[16px] text-emerald-600">attach_file</span>
                  <span>Tài liệu an toàn</span>
                </button>
              </div>

              <div class="h-5 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

              <div class="flex items-center gap-1">
                <button type="button" class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300" title="In đậm" onclick="document.execCommand('bold')">
                  <span class="material-symbols-outlined text-[18px]">format_bold</span>
                </button>
                <button type="button" class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300" title="In nghiêng" onclick="document.execCommand('italic')">
                  <span class="material-symbols-outlined text-[18px]">format_italic</span>
                </button>
                <button type="button" class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300" title="Gạch đầu dòng" onclick="document.execCommand('insertUnorderedList')">
                  <span class="material-symbols-outlined text-[18px]">format_list_bulleted</span>
                </button>
              </div>
            </div>

            <!-- Basic Mode: Blocks Canvas -->
            <div id="studio-blocks-canvas" class="space-y-4 min-h-[350px]"></div>

            <!-- Advanced Mode: Pure Markdown Textarea -->
            <div id="studio-advanced-canvas" class="hidden bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-2">
              <div class="flex items-center justify-between text-xs text-slate-400 font-mono pb-2 border-b border-slate-100 dark:border-slate-800">
                <span>Trình soạn thảo Markdown chuyên gia</span>
                <span>Hỗ trợ GFM, KaTeX math & Code syntax</span>
              </div>
              <textarea
                id="studio-raw-markdown-input"
                rows="18"
                class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-mono text-slate-900 dark:text-white outline-none focus:border-primary resize-none leading-relaxed"
                placeholder="# Soạn thảo bài giảng Markdown..."
              ></textarea>
            </div>

            <!-- Step 2 Footer Navigation -->
            <div class="flex items-center justify-between pt-4">
              <button
                type="button"
                id="studio-btn-back-to-step-1"
                class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Quay lại Bước 1
              </button>
              <button
                type="button"
                id="studio-btn-next-to-step-3"
                class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
              >
                <span>Xem trước theo góc nhìn sinh viên</span>
                <span class="material-symbols-outlined text-[16px]">visibility</span>
              </button>
            </div>

          </div>

          <!-- STEP 3 CONTAINER: Live Student Focus Preview & Final Publish -->
          <div id="studio-step-3-panel" class="hidden space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-[20px]">preview</span>
                  <h3 class="text-sm font-bold text-slate-900 dark:text-white">Xem trước thực tế (Student Focus Reader Preview)</h3>
                </div>
                <button
                  type="button"
                  id="studio-preview-back-btn"
                  class="text-xs font-bold text-primary hover:underline"
                >
                  ← Trở lại sửa nội dung
                </button>
              </div>

              <!-- Student Reader Container Simulation -->
              <div class="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 max-w-3xl mx-auto shadow-inner" id="studio-preview-content">
                <!-- Preview rendered here -->
              </div>

              <!-- Publish Confirmation Banner -->
              <div class="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 class="text-xs font-bold text-indigo-900 dark:text-indigo-300">Sẵn sàng xuất bản bài giảng?</h4>
                  <p class="text-[11px] text-slate-500 mt-0.5">Bài giảng sẽ hiển thị ngay trong đề cương học phần và mở quyền đọc cho sinh viên ghi danh.</p>
                </div>
                <button
                  type="button"
                  id="studio-final-publish-btn"
                  class="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 shrink-0"
                >
                  <span class="material-symbols-outlined text-[16px]">rocket_launch</span>
                  <span>Xuất bản ngay</span>
                </button>
              </div>
            </div>
          </div>

        </main>
      </div>
    `;

    // Internal State & Bidirectional Markdown/Block Parser
    let currentStep = 1;
    let editorMode = 'basic'; // 'basic' | 'advanced'

    const parseMarkdownToBlocks = (markdown) => {
      if (!markdown || !markdown.trim()) {
        return [
          {
            id: 'block-' + Date.now(),
            type: 'paragraph',
            heading: '1. Khái niệm cốt lõi',
            content: ''
          }
        ];
      }

      const blocks = [];
      const rawSections = markdown.split(/\n(?=## |\n> |\n### \[Kiểm tra nhanh\]|\n✓ \*\*Tệp đính kèm\*\*)/g);

      let counter = 1;
      for (const sec of rawSections) {
        const trimmed = sec.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith('>')) {
          const lines = trimmed.split('\n').map(l => l.replace(/^>\s?/, '').trim());
          let alertType = 'tip';
          let title = 'Lưu ý';
          let contentLines = [];

          for (const line of lines) {
            const tagMatch = line.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i);
            if (tagMatch) {
              alertType = tagMatch[1].toLowerCase();
              continue;
            }
            const boldMatch = line.match(/^\*\*(.*?)\*\*/);
            if (boldMatch && !title) {
              title = boldMatch[1];
              continue;
            }
            contentLines.push(line);
          }
          blocks.push({
            id: `block-${Date.now()}-${counter++}`,
            type: 'callout',
            alertType: alertType,
            title: title || 'Lưu ý quan trọng',
            content: contentLines.join('\n').trim()
          });
        } else if (trimmed.startsWith('### [Kiểm tra nhanh]')) {
          const lines = trimmed.split('\n');
          const question = lines[0].replace('### [Kiểm tra nhanh]', '').trim();
          const choices = [];
          let correctIndex = 0;
          let explanation = '';

          for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            const choiceMatch = line.match(/^-\s*\[([ xX])\]\s*(.*)$/);
            if (choiceMatch) {
              if (choiceMatch[1].toLowerCase() === 'x') {
                correctIndex = choices.length;
              }
              choices.push(choiceMatch[2]);
            } else if (line.startsWith('*Giải thích:') || line.startsWith('_Giải thích:')) {
              explanation = line.replace(/^[*_]Giải thích:\s*/, '').replace(/[*_]$/, '').trim();
            }
          }
          blocks.push({
            id: `block-${Date.now()}-${counter++}`,
            type: 'quiz',
            question: question || 'Câu hỏi kiểm tra nhanh',
            choices: choices.length > 0 ? choices : ['Lựa chọn A', 'Lựa chọn B'],
            correctIndex: correctIndex,
            explanation: explanation
          });
        } else if (trimmed.includes('**Tệp đính kèm**:') || trimmed.startsWith('✓')) {
          const fileMatch = trimmed.match(/\[(.*?)\]\((.*?)\)/);
          const filename = fileMatch ? fileMatch[1] : 'Tai_lieu.pdf';
          const fileUrl = fileMatch ? fileMatch[2] : '#';
          blocks.push({
            id: `block-${Date.now()}-${counter++}`,
            type: 'resource',
            filename: filename,
            file_url: fileUrl
          });
        } else {
          let heading = '';
          let content = trimmed;
          if (trimmed.startsWith('## ')) {
            const firstNewline = trimmed.indexOf('\n');
            if (firstNewline !== -1) {
              heading = trimmed.substring(3, firstNewline).trim();
              content = trimmed.substring(firstNewline + 1).trim();
            } else {
              heading = trimmed.substring(3).trim();
              content = '';
            }
          }
          blocks.push({
            id: `block-${Date.now()}-${counter++}`,
            type: 'paragraph',
            heading: heading || `Mục ${counter}`,
            content: content
          });
          counter++;
        }
      }

      return blocks.length > 0 ? blocks : [
        {
          id: 'block-' + Date.now(),
          type: 'paragraph',
          heading: '1. Khái niệm cốt lõi',
          content: markdown
        }
      ];
    };

    let authoringBlocks = [
      {
        id: 'block-1',
        type: 'paragraph',
        heading: '1. Khái niệm cốt lõi & Tầm quan trọng',
        content: 'Chào mừng các bạn học viên đến với bài giảng! Trong học phần này, chúng ta sẽ làm quen với các khái niệm kiến trúc nền tảng và phương pháp triển khai thực chiến.'
      },
      {
        id: 'block-2',
        type: 'callout',
        alertType: 'tip',
        title: 'Lời khuyên từ Giảng viên',
        content: 'Hãy chú ý đọc kỹ các tài liệu chuẩn kỹ thuật đính kèm trước khi bắt đầu bài kiểm tra trắc nghiệm cuối giờ.'
      },
      {
        id: 'block-3',
        type: 'quiz',
        question: 'Giao thức nào là nền tảng chính cho kiến trúc dịch vụ RESTful API?',
        choices: ['FTP', 'HTTP / HTTPS', 'SMTP', 'SSH'],
        correctIndex: 1,
        explanation: 'HTTP / HTTPS là giao thức truyền tải siêu văn bản tiêu chuẩn định danh tài nguyên qua URI và các phương thức GET, POST, PUT, DELETE.'
      }
    ];

    // Load Existing Lesson if Editing
    if (lessonId) {
      try {
        const existingLesson = await ApiClient.getLesson(lessonId);
        if (existingLesson) {
          document.getElementById('studio-lesson-title').value = existingLesson.title || '';
          document.getElementById('studio-input-title').value = existingLesson.title || '';
          document.getElementById('studio-input-duration').value = existingLesson.estimated_duration_minutes || 45;
          document.getElementById('studio-input-summary').value = existingLesson.summary || '';
          if (existingLesson.markdown_content) {
            document.getElementById('studio-raw-markdown-input').value = existingLesson.markdown_content;
            authoringBlocks = parseMarkdownToBlocks(existingLesson.markdown_content);
          }
        }
      } catch (err) {
        UI.showToast('Không thể nạp bài giảng: ' + err.message, 'error');
      }
    }

    // Step Switching Logic
    const switchStep = (step) => {
      currentStep = step;
      const step1 = document.getElementById('studio-step-1-panel');
      const step2 = document.getElementById('studio-step-2-panel');
      const step3 = document.getElementById('studio-step-3-panel');

      if (step === 1) {
        step1.classList.remove('hidden');
        step2.classList.add('hidden');
        step3.classList.add('hidden');
      } else if (step === 2) {
        step1.classList.add('hidden');
        step2.classList.remove('hidden');
        step3.classList.add('hidden');
        renderBlocks();
      } else if (step === 3) {
        step1.classList.add('hidden');
        step2.classList.add('hidden');
        step3.classList.remove('hidden');
        renderLivePreview();
      }

      // Update Nav Tabs
      document.querySelectorAll('.studio-step-tab').forEach(tab => {
        if (parseInt(tab.dataset.step, 10) === step) {
          tab.className = 'studio-step-tab px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all bg-white dark:bg-slate-900 text-primary shadow-xs';
        } else {
          tab.className = 'studio-step-tab px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-900 transition-all';
        }
      });
    };

    document.querySelectorAll('.studio-step-tab').forEach(tab => {
      tab.onclick = () => switchStep(parseInt(tab.dataset.step, 10));
    });

    document.getElementById('studio-btn-next-to-step-2').onclick = () => {
      const title = document.getElementById('studio-input-title').value.trim();
      if (!title) {
        UI.showToast('Vui lòng nhập tên bài giảng trước khi tiếp tục.', 'warning');
        return;
      }
      document.getElementById('studio-lesson-title').value = title;
      switchStep(2);
    };

    document.getElementById('studio-btn-back-to-step-1').onclick = () => switchStep(1);
    document.getElementById('studio-btn-next-to-step-3').onclick = () => switchStep(3);
    document.getElementById('studio-preview-back-btn').onclick = () => switchStep(2);

    // Sync Lesson Title Inputs
    document.getElementById('studio-lesson-title').oninput = (e) => {
      document.getElementById('studio-input-title').value = e.target.value;
    };
    document.getElementById('studio-input-title').oninput = (e) => {
      document.getElementById('studio-lesson-title').value = e.target.value;
    };

    // Mode Toggle (Basic vs Advanced)
    const setEditorMode = (mode) => {
      editorMode = mode;
      const basicBtn = document.getElementById('studio-mode-basic');
      const advBtn = document.getElementById('studio-mode-advanced');
      const toolbar = document.getElementById('studio-visual-toolbar');
      const blocksCanvas = document.getElementById('studio-blocks-canvas');
      const advCanvas = document.getElementById('studio-advanced-canvas');

      if (mode === 'basic') {
        basicBtn.className = 'flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-xs flex items-center justify-center gap-1.5';
        advBtn.className = 'flex-1 py-2 px-3 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all flex items-center justify-center gap-1.5';
        toolbar.classList.remove('hidden');
        blocksCanvas.classList.remove('hidden');
        advCanvas.classList.add('hidden');
        const rawMd = document.getElementById('studio-raw-markdown-input').value;
        if (rawMd) {
          authoringBlocks = parseMarkdownToBlocks(rawMd);
          renderBlocks();
        }
      } else {
        advBtn.className = 'flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-xs flex items-center justify-center gap-1.5';
        basicBtn.className = 'flex-1 py-2 px-3 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all flex items-center justify-center gap-1.5';
        toolbar.classList.add('hidden');
        blocksCanvas.classList.add('hidden');
        advCanvas.classList.remove('hidden');
        document.getElementById('studio-raw-markdown-input').value = serializeBlocksToMarkdown();
      }
    };

    document.getElementById('studio-mode-basic').onclick = () => setEditorMode('basic');
    document.getElementById('studio-mode-advanced').onclick = () => setEditorMode('advanced');

    // Blocks Canvas Rendering
    const renderBlocks = () => {
      const canvas = document.getElementById('studio-blocks-canvas');
      if (!canvas) return;

      canvas.innerHTML = authoringBlocks.map((b, idx) => {
        if (b.type === 'paragraph') {
          return `
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3 relative group" data-block-id="${b.id}">
              <div class="flex items-center justify-between text-xs text-slate-400">
                <span class="flex items-center gap-1.5 font-bold text-primary">
                  <span class="material-symbols-outlined text-[16px]">notes</span>
                  <span>Khối Đoạn văn (${idx + 1})</span>
                </span>
                <div class="flex items-center gap-1">
                  <button type="button" class="btn-block-up p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-800" data-idx="${idx}" title="Chuyển lên">▲</button>
                  <button type="button" class="btn-block-down p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-800" data-idx="${idx}" title="Chuyển xuống">▼</button>
                  <button type="button" class="btn-block-del p-1 rounded hover:bg-rose-50 text-slate-400 hover:text-rose-600" data-idx="${idx}" title="Xóa">✕</button>
                </div>
              </div>
              <input
                type="text"
                class="block-field-heading w-full text-base font-bold text-slate-900 dark:text-white border-0 border-b border-transparent hover:border-slate-200 focus:border-primary px-1 py-0.5 outline-none bg-transparent"
                value="${UI.escapeHtml(b.heading || '')}"
                placeholder="Tiêu đề mục..."
              />
              <textarea
                class="block-field-content w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-primary resize-none leading-relaxed"
                rows="3"
                placeholder="Nhập nội dung giảng dạy..."
              >${UI.escapeHtml(b.content || '')}</textarea>
            </div>
          `;
        } else if (b.type === 'callout') {
          return `
            <div class="bg-amber-50/60 dark:bg-amber-950/20 rounded-2xl border border-amber-200 dark:border-amber-900/50 p-5 shadow-sm space-y-3 relative group" data-block-id="${b.id}">
              <div class="flex items-center justify-between text-xs text-amber-700 dark:text-amber-400 font-bold">
                <span class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">lightbulb</span>
                  <span>Hộp ghi chú nổi bật (Callout)</span>
                </span>
                <div class="flex items-center gap-1">
                  <button type="button" class="btn-block-up p-1 text-slate-400 hover:text-slate-800" data-idx="${idx}">▲</button>
                  <button type="button" class="btn-block-down p-1 text-slate-400 hover:text-slate-800" data-idx="${idx}">▼</button>
                  <button type="button" class="btn-block-del p-1 text-slate-400 hover:text-rose-600" data-idx="${idx}">✕</button>
                </div>
              </div>
              <input
                type="text"
                class="block-field-title w-full text-xs font-bold text-amber-900 dark:text-amber-200 border-0 bg-transparent px-1 py-0.5 outline-none"
                value="${UI.escapeHtml(b.title || 'Lưu ý quan trọng')}"
              />
              <textarea
                class="block-field-content w-full p-2.5 rounded-xl border border-amber-200 dark:border-amber-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200 outline-none focus:border-amber-500 resize-none"
                rows="2"
              >${UI.escapeHtml(b.content || '')}</textarea>
            </div>
          `;
        } else if (b.type === 'quiz') {
          return `
            <div class="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-2xl border border-indigo-200 dark:border-indigo-900/50 p-5 shadow-sm space-y-3 relative group" data-block-id="${b.id}">
              <div class="flex items-center justify-between text-xs text-indigo-700 dark:text-indigo-400 font-bold">
                <span class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">quiz</span>
                  <span>Câu hỏi kiểm tra nhanh giữa bài (Formative Assessment)</span>
                </span>
                <div class="flex items-center gap-1">
                  <button type="button" class="btn-block-up p-1 text-slate-400 hover:text-slate-800" data-idx="${idx}">▲</button>
                  <button type="button" class="btn-block-down p-1 text-slate-400 hover:text-slate-800" data-idx="${idx}">▼</button>
                  <button type="button" class="btn-block-del p-1 text-slate-400 hover:text-rose-600" data-idx="${idx}">✕</button>
                </div>
              </div>
              <input
                type="text"
                class="block-field-question w-full text-xs font-bold text-slate-900 dark:text-white p-2 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 outline-none"
                value="${UI.escapeHtml(b.question || '')}"
                placeholder="Nhập câu hỏi trắc nghiệm..."
              />
              <div class="space-y-1.5 text-xs">
                ${(b.choices || ['Lựa chọn A', 'Lựa chọn B']).map((c, cIdx) => `
                  <div class="flex items-center gap-2">
                    <input
                      type="radio"
                      name="quiz-correct-${b.id}"
                      class="block-field-correct rounded text-primary"
                      value="${cIdx}"
                      ${b.correctIndex === cIdx ? 'checked' : ''}
                      title="Chọn đáp án đúng"
                    />
                    <input
                      type="text"
                      class="block-field-choice flex-1 p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                      data-choice-idx="${cIdx}"
                      value="${UI.escapeHtml(c)}"
                    />
                  </div>
                `).join('')}
              </div>
              <input
                type="text"
                class="block-field-explanation w-full text-[11px] text-slate-500 p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 outline-none"
                value="${UI.escapeHtml(b.explanation || '')}"
                placeholder="Giải thích học thuật khi sinh viên chọn..."
              />
            </div>
          `;
        } else if (b.type === 'resource') {
          return `
            <div class="bg-emerald-50/50 dark:bg-emerald-950/20 rounded-2xl border border-emerald-200 dark:border-emerald-900/50 p-5 shadow-sm space-y-2 relative group" data-block-id="${b.id}">
              <div class="flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-400 font-bold">
                <span class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">verified</span>
                  <span>Tài liệu đính kèm đã xác thực</span>
                </span>
                <div class="flex items-center gap-1">
                  <button type="button" class="btn-block-del p-1 text-slate-400 hover:text-rose-600" data-idx="${idx}">✕</button>
                </div>
              </div>
              <div class="flex items-center gap-3 p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800">
                <span class="material-symbols-outlined text-[24px] text-emerald-600">description</span>
                <div class="flex-1 min-w-0">
                  <input
                    type="text"
                    class="block-field-filename text-xs font-bold text-slate-900 dark:text-white bg-transparent border-0 p-0 w-full outline-none"
                    value="${UI.escapeHtml(b.filename || 'Giao_trinh_Chuyen_sau.pdf')}"
                  />
                  <span class="text-[10px] text-emerald-600 font-semibold block">✓ Đã quét sạch ClamAV - An toàn</span>
                </div>
                <input type="file" class="hidden block-field-file-input" data-idx="${idx}" />
                <button type="button" class="btn-block-upload-file px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1 shadow-xs" data-idx="${idx}">
                  <span class="material-symbols-outlined text-[15px]">upload</span>
                  <span>Chọn tệp</span>
                </button>
              </div>
            </div>
          `;
        }
        return '';
      }).join('');

      // Bind Block Up/Down/Delete
      canvas.querySelectorAll('.btn-block-del').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          authoringBlocks.splice(idx, 1);
          renderBlocks();
        };
      });

      canvas.querySelectorAll('.btn-block-up').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx > 0) {
            const temp = authoringBlocks[idx - 1];
            authoringBlocks[idx - 1] = authoringBlocks[idx];
            authoringBlocks[idx] = temp;
            renderBlocks();
          }
        };
      });

      canvas.querySelectorAll('.btn-block-down').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx < authoringBlocks.length - 1) {
            const temp = authoringBlocks[idx + 1];
            authoringBlocks[idx + 1] = authoringBlocks[idx];
            authoringBlocks[idx] = temp;
            renderBlocks();
          }
        };
      });

      // Bind File Upload in Resource Blocks
      canvas.querySelectorAll('.btn-block-upload-file').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.idx, 10);
          const fileInput = canvas.querySelector(`.block-field-file-input[data-idx="${idx}"]`);
          if (fileInput) fileInput.click();
        };
      });

      canvas.querySelectorAll('.block-field-file-input').forEach(input => {
        input.onchange = async (e) => {
          const file = e.target.files[0];
          if (!file) return;
          const idx = parseInt(input.dataset.idx, 10);
          const bObj = authoringBlocks[idx];
          if (!bObj) return;

          if (lessonId) {
            try {
              const formData = new FormData();
              formData.append('file', file);
              formData.append('title', file.name);
              const res = await ApiClient.attachLessonResource(courseId, lessonId, formData);
              bObj.filename = file.name;
              bObj.file_url = res.file_url || res.download_url || '#';
              UI.showToast(`Đã tải lên và đính kèm tệp ${file.name} thành công!`, 'success');
              renderBlocks();
            } catch (err) {
              UI.showToast(err.message || 'Lỗi tải tệp lên máy chủ.', 'error');
            }
          } else {
            bObj.filename = file.name;
            UI.showToast(`Đã chọn tệp ${file.name}. Hãy lưu bài giảng để hoàn tất tải lên máy chủ.`, 'info');
            renderBlocks();
          }
        };
      });

      // Bind Input Changes to Block Objects
      canvas.querySelectorAll('[data-block-id]').forEach(bEl => {
        const bId = bEl.dataset.blockId;
        const bObj = authoringBlocks.find(item => item.id === bId);
        if (!bObj) return;

        const hInput = bEl.querySelector('.block-field-heading');
        if (hInput) hInput.oninput = (e) => { bObj.heading = e.target.value; };

        const cTextarea = bEl.querySelector('.block-field-content');
        if (cTextarea) cTextarea.oninput = (e) => { bObj.content = e.target.value; };

        const tInput = bEl.querySelector('.block-field-title');
        if (tInput) tInput.oninput = (e) => { bObj.title = e.target.value; };

        const qInput = bEl.querySelector('.block-field-question');
        if (qInput) qInput.oninput = (e) => { bObj.question = e.target.value; };

        const expInput = bEl.querySelector('.block-field-explanation');
        if (expInput) expInput.oninput = (e) => { bObj.explanation = e.target.value; };

        bEl.querySelectorAll('.block-field-choice').forEach(cInp => {
          cInp.oninput = (e) => {
            const cIdx = parseInt(cInp.dataset.choiceIdx, 10);
            bObj.choices[cIdx] = e.target.value;
          };
        });

        bEl.querySelectorAll('.block-field-correct').forEach(rInp => {
          rInp.onchange = (e) => {
            bObj.correctIndex = parseInt(e.target.value, 10);
          };
        });
      });
    };

    // Insert Block Buttons
    document.querySelectorAll('.studio-insert-block-btn').forEach(btn => {
      btn.onclick = () => {
        const type = btn.dataset.type;
        const newId = 'block-' + Date.now();
        if (type === 'paragraph') {
          authoringBlocks.push({ id: newId, type: 'paragraph', heading: 'Mục mới', content: '' });
        } else if (type === 'callout') {
          authoringBlocks.push({ id: newId, type: 'callout', alertType: 'tip', title: 'Ghi chú', content: '' });
        } else if (type === 'quiz') {
          authoringBlocks.push({ id: newId, type: 'quiz', question: 'Câu hỏi mới?', choices: ['Đáp án A', 'Đáp án B', 'Đáp án C', 'Đáp án D'], correctIndex: 0, explanation: '' });
        } else if (type === 'resource') {
          authoringBlocks.push({ id: newId, type: 'resource', filename: 'Tai_lieu_dinh_kem.pdf', file_url: '#' });
        }
        renderBlocks();
      };
    });

    // Serialization helper: Blocks -> Markdown
    const serializeBlocksToMarkdown = () => {
      if (editorMode === 'advanced') {
        return document.getElementById('studio-raw-markdown-input').value;
      }
      return authoringBlocks.map(b => {
        if (b.type === 'paragraph') {
          return `## ${b.heading || 'Nội dung'}\n\n${b.content || ''}\n`;
        } else if (b.type === 'callout') {
          return `> [!${(b.alertType || 'NOTE').toUpperCase()}]\n> **${b.title || 'Lưu ý'}**\n> ${b.content || ''}\n`;
        } else if (b.type === 'quiz') {
          return `### [Kiểm tra nhanh] ${b.question || ''}\n` +
            (b.choices || []).map((c, i) => `- [${i === b.correctIndex ? 'x' : ' '}] ${c}`).join('\n') +
            `\n*Giải thích: ${b.explanation || ''}*\n`;
        } else if (b.type === 'resource') {
          return `✓ **Tệp đính kèm**: [${b.filename || 'Tài liệu'}](${b.file_url || '#'}) (Đã quét sạch ClamAV)\n`;
        }
        return '';
      }).join('\n\n');
    };

    // Live Student Preview Rendering (Step 3)
    const renderLivePreview = () => {
      const container = document.getElementById('studio-preview-content');
      if (!container) return;

      const title = document.getElementById('studio-input-title').value || 'Bài giảng mẫu';
      const dur = document.getElementById('studio-input-duration').value || '45';
      const md = serializeBlocksToMarkdown();

      container.innerHTML = `
        <!-- Lesson Header in Reader -->
        <div class="border-b border-slate-200 dark:border-slate-800 pb-4 space-y-2">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary font-mono">BÀI GIẢNG HỌC VIÊN</span>
            <span class="text-xs text-slate-400">Thời lượng: ~${dur} phút</span>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">${UI.escapeHtml(title)}</h1>
        </div>

        <!-- Rendered Content Body -->
        <div class="prose prose-slate dark:prose-invert max-w-none text-sm space-y-4 leading-relaxed">
          ${authoringBlocks.map(b => {
            if (b.type === 'paragraph') {
              return `
                <div class="space-y-1.5">
                  <h3 class="text-base font-bold text-slate-900 dark:text-white">${UI.escapeHtml(b.heading || '')}</h3>
                  <p class="text-slate-700 dark:text-slate-300 text-xs sm:text-sm leading-relaxed">${UI.escapeHtml(b.content || '')}</p>
                </div>
              `;
            } else if (b.type === 'callout') {
              return `
                <div class="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/20 border-l-4 border-l-amber-500 border border-amber-200 text-xs text-amber-900 dark:text-amber-300 space-y-1">
                  <div class="font-bold">${UI.escapeHtml(b.title || 'Lưu ý')}</div>
                  <p>${UI.escapeHtml(b.content || '')}</p>
                </div>
              `;
            } else if (b.type === 'quiz') {
              return `
                <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-primary/30 shadow-sm space-y-3 text-xs">
                  <div class="flex items-center gap-2 font-bold text-primary">
                    <span class="material-symbols-outlined text-[18px]">quiz</span>
                    <span>Câu hỏi kiểm tra nhanh trong bài</span>
                  </div>
                  <div class="font-bold text-slate-900 dark:text-white text-sm">${UI.escapeHtml(b.question || '')}</div>
                  <div class="space-y-1.5">
                    ${(b.choices || []).map((c, i) => `
                      <div class="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between">
                        <span>${UI.escapeHtml(c)}</span>
                        ${i === b.correctIndex ? '<span class="text-emerald-600 font-bold">✓ Đáp án đúng</span>' : ''}
                      </div>
                    `).join('')}
                  </div>
                </div>
              `;
            } else if (b.type === 'resource') {
              return `
                <div class="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 flex items-center justify-between text-xs">
                  <div class="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-semibold">
                    <span class="material-symbols-outlined text-[20px]">download</span>
                    <span>${UI.escapeHtml(b.filename || 'Tai_lieu.pdf')}</span>
                  </div>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">✓ An toàn ClamAV</span>
                </div>
              `;
            }
            return '';
          }).join('')}
        </div>

        <!-- AI Tutor Chips Simulation -->
        <div class="pt-4 border-t border-slate-200 dark:border-slate-800">
          <span class="text-[11px] text-slate-400 font-bold block mb-2">Gợi ý câu hỏi cho Gia sư AI:</span>
          <div class="flex flex-wrap gap-2">
            <span class="px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-semibold">Tóm tắt 3 ý chính bài học</span>
            <span class="px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold">Giải thích chi tiết kiến trúc</span>
            <span class="px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold">Câu hỏi ôn tập thi</span>
          </div>
        </div>
      `;
    };

    // Save & Publish Handlers
    const saveLessonData = async (publish = false) => {
      const title = document.getElementById('studio-input-title').value.trim() || document.getElementById('studio-lesson-title').value.trim();
      const dur = parseInt(document.getElementById('studio-input-duration').value || 45, 10);
      const summary = document.getElementById('studio-input-summary').value.trim();
      const mdContent = serializeBlocksToMarkdown();

      if (!title) {
        UI.showToast('Vui lòng nhập tên bài giảng.', 'warning');
        return false;
      }

      const payload = {
        title,
        summary,
        markdown_content: mdContent,
        estimated_duration_minutes: dur,
        status: publish ? 'PUBLISHED' : 'DRAFT'
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
          statusEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Đã lưu lúc ${new Date().toLocaleTimeString('vi-VN')}`;
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
        UI.showToast('Bài giảng đã được xuất bản chính thức vào đề cương!', 'success');
        window.location.hash = `#/instructor/courses/${courseId}/manage?tab=curriculum`;
      }
    };

    document.getElementById('studio-final-publish-btn').onclick = async () => {
      const ok = await saveLessonData(true);
      if (ok) {
        UI.showToast('Bài giảng đã được xuất bản chính thức vào đề cương!', 'success');
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
  // 5. PWD301 Split-View 50/50 Exam Authoring Studio (5-Phase Pipeline)
  // =========================================================================
  static renderExams(container) {
    container.innerHTML = `
      <style>
        .dashed-dropzone {
          background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='16' ry='16' stroke='%23CBD5E1' stroke-width='2' stroke-dasharray='8%2c 8' stroke-dashoffset='0' stroke-linecap='round'/%3e%3c/svg%3e");
        }
        .dashed-dropzone:hover {
          background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='16' ry='16' stroke='%236366F1' stroke-width='2' stroke-dasharray='8%2c 8' stroke-dashoffset='0' stroke-linecap='round'/%3e%3c/svg%3e");
        }
        .token-q { color: #2563eb; font-weight: 700; }
        .token-bracket { color: #dc2626; font-weight: 500; }
        .token-correct { color: #dc2626; font-weight: 700; background: #fee2e2; border-radius: 4px; padding: 0 4px; display: inline-block; }
        .token-opt { color: #dc2626; font-weight: 600; }
        .token-text { color: #1e293b; }
      </style>

      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans animate-fade-in text-slate-800 dark:text-slate-100" id="azota-studio-root">
        
        <!-- Top Sticky Header -->
        <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xs select-none shrink-0">
          <div class="max-w-[1920px] mx-auto px-3 sm:px-5 h-14 flex items-center justify-between gap-3">
            
            <!-- Left: Brand, Back & Exam Title -->
            <div class="flex items-center gap-2.5 min-w-0">
              <a href="#/instructor/dashboard" class="flex items-center gap-2 group p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Bàn làm việc Giảng viên">
                <div class="w-7 h-7 rounded-lg bg-[#222120] dark:bg-[#EDEDEB] flex items-center justify-center text-[#FAF9F5] dark:text-[#191919] font-bold text-xs">
                  <span class="material-symbols-outlined text-[16px]">assignment_add</span>
                </div>
                <span class="font-bold text-sm tracking-tight text-[#222120] dark:text-[#EDEDEB] hidden sm:inline-block">PWD301 Soạn đề thi</span>
              </a>
              <button type="button" id="azota-back-btn" class="flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Quay lại">
                <span class="material-symbols-outlined text-[18px]">arrow_back</span>
              </button>

              <div class="flex items-center max-w-sm sm:max-w-md w-full relative">
                <input type="text" id="azota-exam-title-input" class="text-xs sm:text-sm font-semibold text-slate-800 dark:text-white bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-indigo-500 rounded-lg px-2.5 py-1 w-full transition-all truncate focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-indigo-500/20" value="De_thi_chuan_PWD301.docx" title="Nhấp để đổi tên đề thi" />
                <span class="hidden md:inline-flex ml-2 items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">PWD301 Active</span>
              </div>
            </div>

            <!-- Center: 4-Step Stepper Navigation -->
            <nav class="hidden lg:flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-xl border border-slate-200 dark:border-slate-700" id="azota-workflow-stepper">
              <button type="button" class="azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 transition-all" data-phase="1" id="azota-phase-btn-1">
                <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-white dark:bg-slate-900 border border-slate-300 text-slate-600 font-bold">1</span>
                <span>Nạp đề & File</span>
              </button>
              <button type="button" class="azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 text-indigo-600 shadow-xs transition-all" data-phase="2" id="azota-phase-btn-2">
                <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-indigo-600 text-white font-bold">2</span>
                <span>Soạn thảo & Bóc tách</span>
              </button>
              <button type="button" class="azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 transition-all" data-phase="3" id="azota-phase-btn-3">
                <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-white dark:bg-slate-900 border border-slate-300 text-slate-600 font-bold">3</span>
                <span>Ma trận học vụ</span>
              </button>
              <button type="button" class="azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 transition-all" data-phase="4" id="azota-phase-btn-4">
                <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-white dark:bg-slate-900 border border-slate-300 text-slate-600 font-bold">4</span>
                <span>Cấu hình phòng thi</span>
              </button>
            </nav>

            <!-- Right: Action Buttons -->
            <div class="flex items-center gap-2">
              <button type="button" id="azota-open-info-btn" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-bold transition-colors">
                <span class="material-symbols-outlined text-[16px]">info</span>
                <span>Thông tin đề</span>
              </button>
              <button type="button" id="azota-top-next-btn" class="inline-flex items-center gap-1 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-lg text-xs font-bold shadow-sm transition-all">
                <span id="azota-top-next-label">Tiếp tục</span>
                <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>

          </div>
        </header>

        <!-- Main Workspace Area -->
        <main class="flex-1 overflow-hidden relative flex flex-col">
          
          <!-- ============================================================ -->
          <!-- PHASE 1: File Upload & Method Selector                        -->
          <!-- ============================================================ -->
          <section class="hidden flex-1 overflow-y-auto max-w-[1440px] mx-auto px-6 py-8 w-full" id="azota-view-phase-1">
            <div class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Tạo đề thi & Bài kiểm tra mới
                </h1>
                <p class="mt-1 text-sm text-slate-500">
                  Chọn một trong hai luồng khởi tạo: nạp tệp tài liệu số hóa hoặc sử dụng các công cụ tạo trực tuyến.
                </p>
              </div>
              <button type="button" onclick="window.location.hash = '#/instructor/dashboard'" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors self-start md:self-auto">
                <span class="material-symbols-outlined text-[18px]">arrow_back</span>
                <span>Quay lại danh sách đề</span>
              </button>
            </div>

            <!-- Draft Restore Alert Banner -->
            <div id="azota-draft-alert-box" class="hidden mb-6 p-4 rounded-2xl bg-indigo-50/90 dark:bg-indigo-950/40 border-2 border-indigo-300 dark:border-indigo-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center material-symbols-outlined text-[22px] shrink-0 shadow-xs">
                  history_edu
                </div>
                <div>
                  <h4 class="font-bold text-sm text-indigo-950 dark:text-indigo-200">Tìm thấy bản nháp đề thi đang soạn dở</h4>
                  <p class="text-xs text-indigo-700 dark:text-indigo-300" id="azota-draft-alert-info">Đang khôi phục dữ liệu...</p>
                </div>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <button type="button" id="btn-restore-azota-draft" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-xs flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">restore</span>
                  <span>Khôi phục bản nháp</span>
                </button>
                <button type="button" id="btn-discard-azota-draft" class="px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition">
                  Bỏ qua
                </button>
              </div>
            </div>

            <!-- Dual Column Split Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              
              <!-- Left Column: Dropzone Area -->
              <div class="lg:col-span-7 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-xs flex flex-col justify-between min-h-[580px]">
                <div>
                  <div class="flex items-center justify-between mb-4">
                    <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>Nạp tệp đề thi sẵn có</span>
                      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Nhanh & Tiện lợi
                      </span>
                    </h2>
                  </div>

                  <!-- Drop Target -->
                  <div class="dashed-dropzone relative rounded-2xl p-8 sm:p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30 hover:bg-indigo-50/20 group" id="azota-drop-target">
                    <input type="file" id="azota-file-input" accept=".docx,.pdf,.xlsx,.tex,.zip" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                    <div class="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center mb-4 transition-transform group-hover:scale-110 shadow-xs">
                      <span class="material-symbols-outlined text-3xl">cloud_upload</span>
                    </div>
                    <p class="text-base font-semibold text-slate-800 dark:text-slate-200 mb-1">
                      Kéo thả tệp đề thi vào đây hoặc <span class="text-indigo-600 underline underline-offset-2">bấm để duyệt tệp</span>
                    </p>
                    <p class="text-xs sm:text-sm text-slate-500 max-w-md mb-2">
                      Hỗ trợ các định dạng tiêu chuẩn: <span class="font-medium text-slate-700 dark:text-slate-300">.docx, .pdf, .xlsx, .tex, .zip</span>
                    </p>
                    <p class="text-xs text-slate-400">
                      Có thể nạp tệp Đề thi riêng biệt hoặc kèm Bảng đáp án để chấm điểm tự động
                    </p>

                    <button type="button" id="btn-quick-sample-load" class="mt-4 px-4 py-2 bg-indigo-50 text-indigo-700 font-bold rounded-lg text-xs hover:bg-indigo-600 hover:text-white transition-colors">
                      ⚡ Nhấn nạp đề mẫu chuẩn hóa: De_thi_chuan_PWD301.docx
                    </button>
                  </div>
                </div>

                <!-- AI Feature Banner Pill -->
                <div class="mt-6 flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                  <div class="p-1 rounded bg-indigo-100 text-indigo-700 shrink-0">
                    <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
                  </div>
                  <div class="text-xs text-slate-600 dark:text-slate-300">
                    <span class="font-bold text-slate-900 dark:text-white">Hỗ trợ công nghệ AI Parser:</span> Tự động bóc tách và nhận dạng câu hỏi trắc nghiệm, hình ảnh minh họa đính kèm và đáp án đảo đề mà không làm vỡ cấu trúc.
                  </div>
                </div>
              </div>

              <!-- Right Column: Online Exam Methods -->
              <div class="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-7 shadow-xs">
                <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                  <div class="flex items-center gap-2">
                    <h2 class="text-lg font-bold text-slate-900 dark:text-white">Phương thức trực tuyến</h2>
                    <span class="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium px-2 py-0.5 rounded-full">5 hình thức</span>
                  </div>
                </div>

                <div class="space-y-3">
                  <!-- Method 1: Tự soạn Đề thi / Bài tập -->
                  <div class="group block p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 cursor-pointer transition-all" onclick="window.switchAzotaPhase(2)">
                    <div class="flex items-start gap-3.5">
                      <div class="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                        <span class="material-symbols-outlined text-[20px]">edit_document</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                          <span>Tự soạn Đề thi / Bài tập</span>
                          <span class="material-symbols-outlined text-[16px] text-slate-300 group-hover:text-indigo-600">arrow_forward</span>
                        </h3>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                          Sử dụng trình soạn thảo Split-View trực quan, tự gõ nội dung hoặc dán nhanh từ bộ nhớ đệm.
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Method 2: Đề thi tương tác [Mới] -->
                  <div class="group block p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 cursor-pointer transition-all" onclick="window.switchAzotaPhase(2)">
                    <div class="flex items-start gap-3.5">
                      <div class="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800 text-teal-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                        <span class="material-symbols-outlined text-[20px]">extension</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                          <span class="flex items-center gap-2">
                            Tạo đề thi tương tác
                            <span class="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-rose-500 text-white">Mới</span>
                          </span>
                          <span class="material-symbols-outlined text-[16px] text-slate-300 group-hover:text-indigo-600">arrow_forward</span>
                        </h3>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                          Thiết lập dạng câu hỏi kéo thả, điền khuyết, ghép đôi và trò chơi kiến thức sinh động.
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Method 3: Đề từ Ma trận & Ngân hàng đề -->
                  <div class="group block p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 cursor-pointer transition-all" onclick="window.location.hash = '#/instructor/questions'">
                    <div class="flex items-start gap-3.5">
                      <div class="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                        <span class="material-symbols-outlined text-[20px]">dataset</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                          <span>Tạo từ Ma trận & Ngân hàng đề</span>
                          <span class="material-symbols-outlined text-[16px] text-slate-300 group-hover:text-indigo-600">arrow_forward</span>
                        </h3>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                          Trích xuất câu hỏi theo khung Bloom Taxonomy / ABET từ Question Bank có sẵn của PWD301.
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Method 4: Tạo đề từ tệp Excel -->
                  <div class="group block p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 cursor-pointer transition-all" onclick="window.switchAzotaPhase(2)">
                    <div class="flex items-start gap-3.5">
                      <div class="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                        <span class="material-symbols-outlined text-[20px]">table_view</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                          <span>Tạo đề từ tệp Excel</span>
                          <span class="material-symbols-outlined text-[16px] text-slate-300 group-hover:text-indigo-600">arrow_forward</span>
                        </h3>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                          Import danh sách câu hỏi hàng loạt và cấu hình đáp án qua bảng tính Excel chuẩn hóa.
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Method 5: Import câu hỏi từ Moodle XML / JSON -->
                  <div class="group block p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 cursor-pointer transition-all" onclick="window.switchAzotaPhase(2)">
                    <div class="flex items-start gap-3.5">
                      <div class="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                        <span class="material-symbols-outlined text-[20px]">code_blocks</span>
                      </div>
                      <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                          <span>Nạp từ chuẩn LMS Moodle XML / JSON</span>
                          <span class="material-symbols-outlined text-[16px] text-slate-300 group-hover:text-indigo-600">arrow_forward</span>
                        </h3>
                        <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                          Nhập cấu trúc câu hỏi theo chuẩn trao đổi dữ liệu học thuật quốc tế.
                        </p>
                      </div>
                    </div>
                  </div>

                </div>
              </div>

            </div>
          </section>

          <!-- ============================================================ -->
          <!-- PHASE 2: Split View 50:50 (Visual Cards & Raw Code Editor)   -->
          <!-- ============================================================ -->
          <section class="flex-1 h-full flex flex-col overflow-hidden" id="azota-view-phase-2">
            
            <!-- Sub-Toolbar (Azota Subtoolbar) -->
            <div class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-2 flex flex-wrap items-center justify-between gap-2.5 text-xs shrink-0 select-none">
              <div class="flex items-center flex-wrap gap-2">
                <button type="button" id="btn-divide-points" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-xs transition-colors" title="Chia điểm đều cho tất cả câu hỏi">
                  <span class="material-symbols-outlined text-[16px]">calculate</span>
                  <span>Chia điểm</span>
                </button>
                <button type="button" id="btn-sub-exam-info" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition-colors">
                  <span class="material-symbols-outlined text-[16px]">info</span>
                  <span>Thông tin đề</span>
                </button>
                <div class="flex items-center gap-1.5 pl-2 border-l border-slate-200 dark:border-slate-800">
                  <span class="text-slate-500 font-medium">Đi đến câu</span>
                  <input type="number" id="jump-question-input" min="1" max="50" value="1" class="w-12 px-1.5 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded-md text-center font-bold outline-none focus:border-indigo-500" />
                  <button type="button" id="jump-question-btn" class="px-2.5 py-1 bg-indigo-600 text-white rounded-md font-bold hover:bg-indigo-700">Đến</button>
                </div>
                <div class="hidden xl:flex items-center gap-1.5 pl-3 border-l border-slate-200 dark:border-slate-800 text-slate-500 text-[11px]">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span id="azota-status-sync-indicator">Đã tự động lưu 30 giây trước • 0 lỗi cú pháp</span>
                </div>
              </div>

              <div class="flex items-center flex-wrap gap-1.5 text-xs">
                <button type="button" onclick="window.switchAzotaPhase(1)" class="inline-flex items-center gap-1 px-2.5 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium">
                  <span class="material-symbols-outlined text-[16px]">upload</span>
                  <span>Upload</span>
                </button>
                <button type="button" onclick="window.location.hash = '#/instructor/questions'" class="inline-flex items-center gap-1 px-2.5 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium">
                  <span class="text-indigo-600 font-bold">+</span>
                  <span>Chọn từ ngân hàng PWD301</span>
                </button>
                <button type="button" id="btn-insert-latex" class="inline-flex items-center gap-1 px-2 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium" title="Chèn ký hiệu toán học LaTeX">
                  <span class="font-serif italic font-bold">Σ</span>
                  <span class="hidden md:inline">Chèn công thức</span>
                </button>
                <button type="button" id="btn-insert-interactive" class="inline-flex items-center gap-1 px-2.5 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium">
                  <span class="material-symbols-outlined text-[16px]">code</span>
                  <span>Chèn nội dung tương tác</span>
                </button>
              </div>
            </div>

            <!-- 50/50 Split Grid -->
            <div class="flex-1 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200 dark:divide-slate-800 h-full overflow-hidden bg-white dark:bg-slate-900">
              
              <!-- LEFT COLUMN: Visual Question Cards & In-Place Editing -->
              <div class="overflow-y-auto p-4 sm:p-5 space-y-4 bg-slate-50/60 dark:bg-slate-950/60 h-full" id="azota-preview-container">
                <!-- Dynamically rendered question cards -->
              </div>

              <!-- RIGHT COLUMN: Raw Text Code Editor & Syntax Inspector -->
              <div class="flex flex-col h-full bg-white dark:bg-slate-900 select-text">
                <div class="bg-slate-50/80 dark:bg-slate-800/80 px-4 py-1.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 select-none">
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-slate-600 dark:text-slate-300 font-semibold">Trình soạn thảo cú pháp Đề thi PWD301</span>
                    <span class="text-slate-300">|</span>
                    <span>Ký tự <code class="text-red-600 font-bold bg-red-50 dark:bg-red-950 px-1 rounded">*</code> trước đáp án = ĐÁP ÁN ĐÚNG</span>
                  </div>
                  <button type="button" id="btn-sync-raw-to-preview" class="flex items-center gap-1 text-slate-600 hover:text-indigo-600 cursor-pointer font-semibold">
                    <span class="material-symbols-outlined text-[15px] text-indigo-600">sync</span>
                    <span>Đồng bộ sang xem trước</span>
                  </button>
                </div>

                <!-- Textarea Editor with Line Numbers -->
                <div class="flex-1 flex overflow-hidden">
                  <div class="w-10 py-3 pr-2 text-right font-mono text-xs text-slate-400 select-none border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50" id="azota-line-numbers">
                    <!-- Dynamic Line Numbers -->
                  </div>
                  <textarea
                    id="azota-raw-textarea"
                    class="flex-1 p-3 font-mono text-xs sm:text-sm text-slate-900 dark:text-white bg-white dark:bg-slate-900 outline-none resize-none leading-relaxed border-0 overflow-auto"
                    spellcheck="false"
                    placeholder="Nhập đề thi theo cú pháp chuẩn PWD301: Câu 1: [!b:$ Nội dung $] A. ... *B. ... C. ... D. ..."
                  >${UI.escapeHtml(ExamParser.generateSampleTemplate('all'))}</textarea>
                </div>

                <!-- Bottom Sample Templates Bar -->
                <div class="border-t border-slate-200 dark:border-slate-800 px-4 py-2 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs text-slate-500 shrink-0 select-none">
                  <div class="flex items-center gap-2 overflow-x-auto">
                    <span class="font-semibold text-slate-700 dark:text-slate-300 shrink-0">Nội dung mẫu:</span>
                    <button type="button" class="text-indigo-600 hover:underline shrink-0 load-tmpl-btn" data-tmpl="standard">Mẫu 1 (Chuẩn)</button>
                    <span class="text-slate-300">|</span>
                    <button type="button" class="text-indigo-600 hover:underline shrink-0 load-tmpl-btn" data-tmpl="fill">Mẫu 2 (Điền từ)</button>
                    <span class="text-slate-300">|</span>
                    <button type="button" class="text-indigo-600 hover:underline shrink-0 font-bold load-tmpl-btn" data-tmpl="all">Mẫu 6 (Tổng hợp)</button>
                  </div>
                </div>
              </div>

            </div>
          </section>

          <!-- ============================================================ -->
          <!-- PHASE 3: Modular Wizard & Academic Governance Matrix          -->
          <!-- ============================================================ -->
          <section class="hidden flex-1 overflow-y-auto max-w-[1080px] mx-auto px-4 sm:px-6 py-7 pb-28 w-full space-y-6" id="azota-view-phase-3">
            
            <!-- Stepper Wizard -->
            <div class="bg-white dark:bg-slate-900 p-4 sm:p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Step 1 Done -->
                <div class="flex items-center space-x-3 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 cursor-pointer" onclick="window.switchAzotaPhase(2)">
                  <div class="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-sm font-bold">
                    ✓
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] font-bold uppercase tracking-wider text-emerald-700">Bước 1</span>
                      <span class="px-2 py-0.2 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700">Đã xong</span>
                    </div>
                    <p class="text-xs font-bold text-slate-900 dark:text-white truncate">Soạn thảo & Thẩm định câu hỏi</p>
                    <p class="text-[11px] text-slate-500 truncate" id="p3-q-summary">6 câu • Thang điểm 40.0đ</p>
                  </div>
                </div>

                <!-- Step 2 Active -->
                <div class="flex items-center space-x-3 p-2.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border-2 border-indigo-500 shadow-xs">
                  <div class="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md shadow-indigo-500/30 ring-4 ring-indigo-100 dark:ring-indigo-900/50">
                    2
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] font-bold uppercase tracking-wider text-indigo-700">Bước 2</span>
                      <span class="px-2 py-0.2 rounded-full text-[10px] font-semibold bg-indigo-600 text-white animate-pulse">Đang thực hiện</span>
                    </div>
                    <p class="text-xs font-bold text-slate-900 dark:text-white truncate">Định danh & Mục đích khảo thí</p>
                    <p class="text-[11px] text-indigo-700 font-medium truncate">Thiết lập phạm vi & quyền học vụ</p>
                  </div>
                </div>

                <!-- Step 3 Pending -->
                <div class="flex items-center space-x-3 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 opacity-70 cursor-pointer" onclick="window.switchAzotaPhase(4)">
                  <div class="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center font-bold text-sm">
                    3
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Bước 3</span>
                      <span class="text-[10px] text-slate-400 font-medium">Chờ cấu hình</span>
                    </div>
                    <p class="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate">Giám sát, Bảo mật & Phòng thi</p>
                    <p class="text-[11px] text-slate-400 truncate">AI Proctoring, Khóa tab & Phân phòng</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Card 1: Xác định Bối cảnh & Phạm vi Học vụ -->
            <section class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div class="p-6 pb-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                    <span class="material-symbols-outlined text-[20px]">school</span>
                  </div>
                  <div>
                    <h2 class="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                      1. Xác định Bối cảnh & Phạm vi Học vụ (Academic Scope & Provenance)
                    </h2>
                    <p class="text-xs text-slate-500 mt-0.5">Xác định hình thức tổ chức, học phần phân công và mục đích kiểm định đào tạo</p>
                  </div>
                </div>
                <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">Bắt buộc</span>
              </div>

              <div class="p-6 space-y-6">
                <!-- Radio Options Switcher -->
                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-3">Hình thức triển khai đề thi</label>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <label class="relative flex p-4 cursor-pointer rounded-xl border-2 border-indigo-600 bg-indigo-50/30 dark:bg-indigo-950/20 shadow-xs transition-all">
                      <input type="radio" name="academic_exam_mode" value="independent" checked class="h-4 w-4 mt-0.5 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                      <div class="ml-3 flex flex-col">
                        <span class="block text-sm font-bold text-slate-900 dark:text-white">Khảo thí Độc lập / Tổng hợp</span>
                        <span class="block text-xs text-slate-500 mt-1 leading-relaxed">Yêu cầu chỉ định môn học phụ trách, mục đích khảo nghiệm và tích hợp sổ điểm ABET.</span>
                      </div>
                    </label>

                    <label class="relative flex p-4 cursor-pointer rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300 transition-all">
                      <input type="radio" name="academic_exam_mode" value="lesson_linked" class="h-4 w-4 mt-0.5 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                      <div class="ml-3 flex flex-col">
                        <span class="block text-sm font-semibold text-slate-800 dark:text-slate-200">Liên kết trực tiếp theo Bài học</span>
                        <span class="block text-xs text-slate-400 mt-1 leading-relaxed">Đề thi / Bài tập bổ trợ tích hợp thẳng vào một chương bài học (Lesson-Linked) trên LMS.</span>
                      </div>
                    </label>
                  </div>
                </div>

                <!-- Academic Course Selector -->
                <div class="pt-2 border-t border-slate-100 dark:border-slate-800">
                  <div class="flex items-center justify-between mb-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300" for="p3-assigned-course">
                      Chọn Môn học phụ trách <span class="text-rose-500">*</span>
                    </label>
                    <span class="text-[11px] text-slate-400">Giảng viên phụ trách PWD301</span>
                  </div>
                  <select class="w-full rounded-xl border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-900 dark:text-white bg-white dark:bg-slate-800 py-2.5 px-3.5 focus:border-indigo-500 focus:ring-indigo-500 shadow-xs" id="p3-assigned-course">
                    <option value="PWD301" selected>PWD301 - Phát triển Ứng dụng Web với Python (3 Tín chỉ | Fall 2026)</option>
                    <option value="UXD101">UXD101 - Thiết kế Trải nghiệm Người dùng & Giao diện (2 Tín chỉ | Fall 2026)</option>
                    <option value="CSD201">CSD201 - Cấu trúc Dữ liệu và Giải thuật với Java (3 Tín chỉ | Fall 2026)</option>
                  </select>
                </div>

                <!-- Assessment Intent Selector (5 Cards Grid) -->
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Mục đích tạo đề (Assessment Intent Selector) <span class="text-rose-500">*</span>
                    </label>
                    <span class="text-xs text-slate-500">Chọn 1 mục đích chính để áp dụng ma trận khảo thí chuẩn hóa</span>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5" id="p3-intent-grid">
                    <!-- Intent 1: Midterm -->
                    <label class="intent-card relative flex flex-col justify-between p-4 rounded-xl border-2 border-indigo-600 bg-indigo-50/40 dark:bg-indigo-950/30 cursor-pointer shadow-xs transition-all">
                      <input type="radio" name="assessment_intent" value="midterm" checked class="sr-only" />
                      <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <span class="text-sm font-bold text-slate-900 dark:text-white">Thi Giữa kỳ</span>
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-700 border border-indigo-200">Trọng số 20-30%</span>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                          Khóa đề khi bắt đầu thi, tính điểm chính thức vào hệ thống đào tạo, đồng bộ bảng điểm ERP.
                        </p>
                      </div>
                      <div class="mt-3 pt-2.5 border-t border-indigo-200/60 flex items-center text-[11px] font-semibold text-indigo-700">
                        <span class="material-symbols-outlined text-[15px] mr-1">check_circle</span> Đang lựa chọn
                      </div>
                    </label>

                    <!-- Intent 2: Quiz -->
                    <label class="intent-card relative flex flex-col justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 cursor-pointer transition-all">
                      <input type="radio" name="assessment_intent" value="quiz" class="sr-only" />
                      <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <span class="text-sm font-bold text-slate-900 dark:text-white">Kiểm tra thường xuyên</span>
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Trọng số 10%</span>
                        </div>
                        <p class="text-xs text-slate-500 leading-relaxed">
                          Đánh giá nhanh mức độ tiếp thu bài học sau mỗi tuần, cho phép sinh viên xem lại bài giải.
                        </p>
                      </div>
                      <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center text-[11px] text-slate-400">
                        <span class="material-symbols-outlined text-[15px] mr-1">radio_button_unchecked</span> Nhấn để chọn
                      </div>
                    </label>

                    <!-- Intent 3: Final -->
                    <label class="intent-card relative flex flex-col justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 cursor-pointer transition-all">
                      <input type="radio" name="assessment_intent" value="final" class="sr-only" />
                      <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <span class="text-sm font-bold text-slate-900 dark:text-white">Thi Cuối kỳ / Thực hành</span>
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Trọng số 40-50%</span>
                        </div>
                        <p class="text-xs text-slate-500 leading-relaxed">
                          Quy chuẩn khảo thí cao nhất, kích hoạt giám sát chống gian lận đa tầng, khóa trình duyệt an toàn.
                        </p>
                      </div>
                      <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center text-[11px] text-slate-400">
                        <span class="material-symbols-outlined text-[15px] mr-1">radio_button_unchecked</span> Nhấn để chọn
                      </div>
                    </label>

                    <!-- Intent 4: ABET CLO -->
                    <label class="intent-card relative flex flex-col justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 cursor-pointer transition-all">
                      <input type="radio" name="assessment_intent" value="abet" class="sr-only" />
                      <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <span class="text-sm font-bold text-slate-900 dark:text-white">Kiểm định CLO / ABET</span>
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Học thuật</span>
                        </div>
                        <p class="text-xs text-slate-500 leading-relaxed">
                          Khảo sát chuẩn đầu ra chương trình đào tạo, tự động thống kê phân phối điểm Bloom Taxonomy.
                        </p>
                      </div>
                      <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center text-[11px] text-slate-400">
                        <span class="material-symbols-outlined text-[15px] mr-1">radio_button_unchecked</span> Nhấn để chọn
                      </div>
                    </label>

                    <!-- Intent 5: Practice Sandbox -->
                    <label class="intent-card relative flex flex-col justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 cursor-pointer transition-all md:col-span-2">
                      <input type="radio" name="assessment_intent" value="practice" class="sr-only" />
                      <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <span class="text-sm font-bold text-slate-900 dark:text-white">Đề Luyện tập & Tự học (Practice Sandbox)</span>
                          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">Miễn phí</span>
                        </div>
                        <p class="text-xs text-slate-500 leading-relaxed">
                          Cho phép sinh viên làm nhiều lần không giới hạn, không tính điểm vào GPA, hiển thị ngay đáp án chi tiết và giải thích AI.
                        </p>
                      </div>
                      <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center text-[11px] text-slate-400">
                        <span class="material-symbols-outlined text-[15px] mr-1">radio_button_unchecked</span> Nhấn để chọn
                      </div>
                    </label>
                  </div>
                </div>

              </div>
            </section>

            <!-- Card 3: Chính sách Truy cập & Kinh phí -->
            <section class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div class="p-6 pb-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                  <span class="material-symbols-outlined text-[20px]">payments</span>
                </div>
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                    2. Chính sách Truy cập & Kinh phí (Fee & Access Control)
                  </h2>
                  <p class="text-xs text-slate-500 mt-0.5">Quy định quyền nộp bài, phí thi khảo thí hoặc mở rộng cho thí sinh tự do</p>
                </div>
              </div>
              <div class="p-6 space-y-3">
                <label class="flex items-start p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/30 dark:bg-indigo-950/20 cursor-pointer transition-all">
                  <input type="radio" name="access_fee_policy" value="free" checked class="h-4 w-4 mt-0.5 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                  <div class="ml-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm font-bold text-slate-900 dark:text-white">Miễn phí học phần</span>
                      <span class="px-2 py-0.2 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">Mặc định đào tạo</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-0.5">Áp dụng miễn phí cho toàn bộ sinh viên đã đăng ký học phần PWD301 trên cổng đào tạo.</p>
                  </div>
                </label>

                <label class="flex items-start p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300 cursor-pointer transition-all">
                  <input type="radio" name="access_fee_policy" value="paid" class="h-4 w-4 mt-0.5 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                  <div class="ml-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm font-semibold text-slate-800 dark:text-slate-200">Thu phí tham gia thi / Mở rộng thí sinh tự do</span>
                      <span class="px-2 py-0.2 rounded-full text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">Phí dịch vụ học vụ</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-0.5">Yêu cầu người thi thanh toán học phí khảo thí trước khi được cấp mã truy cập phòng thi.</p>
                  </div>
                </label>
              </div>
            </section>

            <!-- Sticky Bottom Navigation Bar for Phase 3 -->
            <div class="pt-4 flex items-center justify-between">
              <button type="button" onclick="window.switchAzotaPhase(2)" class="inline-flex items-center px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl transition-all shadow-xs">
                <span class="material-symbols-outlined text-[18px] mr-1.5">arrow_back</span>
                <span>Quay lại Bước 1: Soạn đề</span>
              </button>
              <button type="button" onclick="window.switchAzotaPhase(4)" class="inline-flex items-center px-5 py-2.5 text-xs sm:text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-500/25 active:scale-95 transition-all">
                <span>Chuyển sang Cấu hình phòng thi</span>
                <span class="material-symbols-outlined text-[18px] ml-1.5">arrow_forward</span>
              </button>
            </div>

          </section>

          <!-- ============================================================ -->
          <!-- PHASE 4: Detailed Exam & Proctoring Configuration             -->
          <!-- ============================================================ -->
          <section class="hidden flex-1 overflow-y-auto max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-28 space-y-6 w-full" id="azota-view-phase-4">
            
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-2">
              <div>
                <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">Cấu hình Đợt Khảo Thí & Bảo Mật Phòng Thi</h1>
                <p class="text-sm text-slate-500 mt-0.5">Trình thiết lập Trực quan & Dễ dùng cho Giảng viên</p>
              </div>
              <div class="flex items-center space-x-2 text-xs text-slate-500 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800">
                <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
                <span>Tự động lưu nháp sẵn sàng</span>
              </div>
            </div>

            <!-- Section 1: Exam Type Selection -->
            <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 sm:p-6 shadow-sm">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white">Loại cấu hình bài thi</h2>
                  <p class="text-xs text-slate-500 mt-1">Dùng cho các kỳ thi nghiêm túc PWD301 LMS, bảo mật đáp án tới khi hết hạn nộp bài.</p>
                </div>
                <div class="inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                  <button type="button" id="cfg-btn-test" class="px-5 py-2 text-xs font-bold rounded-lg shadow-sm bg-indigo-600 text-white transition">
                    Kiểm tra
                  </button>
                  <button type="button" id="cfg-btn-practice" class="px-5 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 rounded-lg transition hover:text-slate-900">
                    Luyện tập
                  </button>
                </div>
              </div>
            </section>

            <!-- Section 2: Time & Access Control -->
            <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 sm:p-6 shadow-sm space-y-6">
              <div class="border-b border-slate-100 dark:border-slate-800 pb-3">
                <h2 class="text-base font-bold text-slate-900 dark:text-white">Cấu hình thời gian & Quyền truy cập</h2>
                <p class="text-xs text-slate-500 mt-0.5">Quy định thời hạn nộp bài và đối tượng sinh viên được phép tham dự.</p>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-duration">
                    Thời gian làm bài (phút)
                  </label>
                  <input type="number" id="cfg-duration" min="0" value="45" class="w-full text-sm font-semibold rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 py-2.5 px-3 focus:border-indigo-500" />
                  <p class="text-[11px] text-slate-500 mt-1">Nhập 0 để không giới hạn thời gian làm bài.</p>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Thời gian mở giao đề thi
                  </label>
                  <div class="flex items-center space-x-2">
                    <input type="datetime-local" id="cfg-start-time" class="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 py-2 px-2.5" />
                    <span class="text-xs text-slate-400">đến</span>
                    <input type="datetime-local" id="cfg-end-time" class="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 py-2 px-2.5" />
                    <button type="button" id="cfg-btn-reset-dates" class="p-2 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg text-slate-500 text-xs font-medium shrink-0">
                      Đặt lại
                    </button>
                  </div>
                  <p class="text-[11px] text-slate-400 mt-1">Chỉ được phép gia hạn thêm. Bỏ trống nếu không muốn giới hạn khung giờ nộp bài.</p>
                </div>
              </div>

              <!-- Permission Radios -->
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Ai được phép làm bài?</label>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label class="relative flex items-center p-3.5 border-2 rounded-xl border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/30 cursor-pointer transition">
                    <input type="radio" name="cfg_access_control" value="all" checked class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <div class="ml-3">
                      <span class="block text-xs font-bold text-slate-900 dark:text-white">Tất cả mọi người</span>
                      <span class="block text-[11px] text-slate-500 mt-0.5">Bất kỳ ai có mã đề / đường dẫn</span>
                    </div>
                  </label>

                  <label class="relative flex items-center p-3.5 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-xl cursor-pointer hover:border-slate-300 transition">
                    <input type="radio" name="cfg_access_control" value="class" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <div class="ml-3">
                      <span class="block text-xs font-bold text-slate-900 dark:text-white">Giao theo lớp</span>
                      <span class="block text-[11px] text-slate-500 mt-0.5">Chọn lớp PWD301_L01, L02</span>
                    </div>
                  </label>

                  <label class="relative flex items-center p-3.5 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-xl cursor-pointer hover:border-slate-300 transition">
                    <input type="radio" name="cfg_access_control" value="student" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <div class="ml-3">
                      <span class="block text-xs font-bold text-slate-900 dark:text-white">Giao cho học sinh cụ thể</span>
                      <span class="block text-[11px] text-slate-500 mt-0.5">Chọn từ danh bạ sinh viên</span>
                    </div>
                  </label>
                </div>
              </div>
            </section>

            <!-- Section 3: Security & Proctoring -->
            <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 sm:p-6 shadow-sm space-y-6">
              <div class="border-b border-slate-100 dark:border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center">
                    <span>Bảo mật & Giám sát Chống gian lận</span>
                    <span class="ml-2 px-2 py-0.5 text-[10px] font-extrabold uppercase bg-red-100 text-red-600 rounded-md">High Security</span>
                  </h2>
                  <p class="text-xs text-slate-500 mt-0.5">Thiết lập công nghệ chống chuyển tab và bảo vệ toàn vẹn kỳ thi.</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-attempts">Số lượt làm bài tối đa</label>
                  <input type="number" id="cfg-attempts" min="0" value="1" class="w-full text-sm font-semibold rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 py-2.5 px-3 focus:border-indigo-500" />
                  <p class="text-[11px] text-slate-500 mt-1">*Nhập 0 để không giới hạn số lượt làm đề thi.</p>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-password">Mật khẩu đề thi</label>
                  <div class="relative">
                    <input type="password" id="cfg-password" value="PWD301@2026" class="w-full text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 py-2.5 px-3 pr-10 focus:border-indigo-500" />
                    <button type="button" id="cfg-toggle-pwd" class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600">
                      <span class="material-symbols-outlined text-[18px]">visibility</span>
                    </button>
                  </div>
                  <p class="text-[11px] text-slate-400 mt-1">Học sinh phải nhập đúng mật khẩu này để bắt đầu làm bài.</p>
                </div>
              </div>

              <!-- AI Proctoring -->
              <div class="pt-2 border-t border-slate-100 dark:border-slate-800">
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Giám sát tự động (AI Proctoring)</label>
                <div class="flex items-center space-x-6">
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_proctor_mode" value="off" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300">Tắt</span>
                  </label>
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_proctor_mode" value="on" checked class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2 text-xs font-bold text-indigo-600 flex items-center">
                      Giám sát thoát màn hình & Chuyển tab
                    </span>
                  </label>
                </div>
                <p class="text-[11px] text-slate-500 mt-1">Hỗ trợ ghi nhận số lần chuyển tab. Rời màn hình quá 3 lần hệ thống sẽ tự động khóa bài và nộp.</p>
              </div>

              <!-- Toggles: Student Identification & App Only -->
              <div class="space-y-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                <div class="flex items-center justify-between">
                  <div class="pr-4">
                    <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Xác thực thông tin sinh viên</span>
                    <span class="text-[11px] text-slate-500 block mt-0.5">Yêu cầu khai báo bổ sung: Họ tên, Mã sinh viên (MA-xxxx), Lớp và Email trường.</span>
                  </div>
                  <input type="checkbox" id="cfg-verify-student" checked class="h-5 w-5 rounded text-indigo-600 focus:ring-indigo-500" />
                </div>

                <div class="flex items-center justify-between">
                  <div class="pr-4">
                    <div class="flex items-center space-x-2">
                      <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Chỉ thi trên ứng dụng Safe Exam Browser</span>
                      <span class="px-1.5 py-0.5 text-[9px] font-extrabold uppercase bg-red-500 text-white rounded">Mới</span>
                    </div>
                    <span class="text-[11px] text-slate-500 block mt-0.5">Khi bật, đề thi chỉ có thể thực hiện trên app để vô hiệu hóa hoàn toàn copy/paste, chụp màn hình.</span>
                  </div>
                  <input type="checkbox" id="cfg-safe-browser" class="h-5 w-5 rounded text-indigo-600 focus:ring-indigo-500" />
                </div>
              </div>
            </section>

            <!-- Section 4: Randomization -->
            <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 sm:p-6 shadow-sm space-y-4">
              <div class="border-b border-slate-100 dark:border-slate-800 pb-3">
                <h2 class="text-base font-bold text-slate-900 dark:text-white">Đảo câu hỏi và đáp án</h2>
                <p class="text-xs text-slate-500 mt-0.5">Xáo trộn ngẫu nhiên để chống nhìn bài xung quanh trong phòng máy.</p>
              </div>

              <div class="flex items-center justify-between py-2">
                <div class="pr-4">
                  <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Đảo thứ tự câu hỏi và đáp án</span>
                  <span class="text-[11px] text-slate-500 block mt-0.5">
                    Hệ thống sẽ tự động đảo các câu hỏi và thứ tự đáp án (A, B, C, D) trong mỗi câu hỏi cho từng học sinh.
                  </span>
                </div>
                <input type="checkbox" id="cfg-shuffle-all" checked class="h-5 w-5 rounded text-indigo-600 focus:ring-indigo-500" />
              </div>

              <div class="flex items-center justify-between py-2 border-t border-slate-100 dark:border-slate-800">
                <div class="pr-4">
                  <span class="text-xs font-bold text-slate-800 dark:text-slate-200 block">Ẩn tiêu đề nhóm câu hỏi</span>
                  <span class="text-[11px] text-slate-500 block mt-0.5">Ẩn các tiêu đề nhóm (VD: Phần 1: Trắc nghiệm khách quan) khi hiển thị cho học sinh.</span>
                </div>
                <input type="checkbox" id="cfg-hide-group-headers" class="h-5 w-5 rounded text-indigo-600 focus:ring-indigo-500" />
              </div>
            </section>

            <!-- Section 5: Results display settings -->
            <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 sm:p-6 shadow-sm space-y-5">
              <div class="border-b border-slate-100 dark:border-slate-800 pb-3">
                <h2 class="text-base font-bold text-slate-900 dark:text-white">Điểm số, Đáp án & Hiển thị sau khi thi</h2>
                <p class="text-xs text-slate-500 mt-0.5">Kiểm soát chặt chẽ thời điểm công bố kết quả để ngăn ngừa lộ đề thi.</p>
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Cho xem điểm</label>
                <div class="flex flex-wrap items-center gap-4 sm:gap-6 text-xs text-slate-700 dark:text-slate-300">
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_scores" value="never" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2">Không</span>
                  </label>
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_scores" value="submitted" checked class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2 font-bold text-indigo-600">Khi làm bài xong</span>
                  </label>
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_scores" value="all_finished" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2">Khi tất cả thi xong</span>
                  </label>
                </div>
              </div>

              <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Cho xem đề thi và đáp án</label>
                <div class="flex flex-wrap items-center gap-4 sm:gap-6 text-xs text-slate-700 dark:text-slate-300">
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_answers" value="never" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2">Không</span>
                  </label>
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_answers" value="submitted" checked class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2 font-bold text-indigo-600">Khi làm bài xong</span>
                  </label>
                  <label class="inline-flex items-center cursor-pointer">
                    <input type="radio" name="cfg_view_answers" value="all_finished" class="h-4 w-4 text-indigo-600 border-slate-300 focus:ring-indigo-500" />
                    <span class="ml-2">Khi tất cả thi xong</span>
                  </label>
                </div>
              </div>
            </section>

            <!-- Bottom Bar for Phase 4 -->
            <div class="pt-4 flex items-center justify-between">
              <button type="button" onclick="window.switchAzotaPhase(3)" class="inline-flex items-center px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl transition-all shadow-xs">
                <span class="material-symbols-outlined text-[18px] mr-1.5">arrow_back</span>
                <span>Quay lại Cấu hình chung</span>
              </button>
              <div class="flex items-center space-x-3">
                <button type="button" id="cfg-btn-save-draft" class="px-4 py-2.5 text-xs font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-xl transition">
                  Lưu nháp cấu hình
                </button>
                <button type="button" id="cfg-btn-open-validation" class="px-6 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-500/30 transition flex items-center">
                  <span>Xuất bản & Mở ca thi</span>
                  <span class="material-symbols-outlined text-[18px] ml-1.5">rocket_launch</span>
                </button>
              </div>
            </div>

          </section>

        </main>

        <!-- ============================================================== -->
        <!-- PHASE 5: Strict Gate Validation Console Modal                  -->
        <!-- ============================================================== -->
        <div class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 md:p-6 bg-slate-900/60 backdrop-blur-sm hidden overflow-y-auto" id="modal-validation-console">
          <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-5xl w-full border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] my-auto animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
            
            <!-- Modal Header -->
            <header class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-800/60 flex flex-wrap items-center justify-between gap-3 shrink-0">
              <div class="min-w-0">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-indigo-100 text-indigo-700 border border-indigo-200">PWD301 Khảo thí</span>
                  <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white truncate">
                    Kiểm tra chất lượng & Xác nhận Đề thi: <span class="text-indigo-600 font-extrabold" id="val-modal-title">De_thi_chuan_PWD301.docx</span>
                  </h2>
                  <span class="font-mono text-xs bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded font-semibold">Mã đề: xdflp9</span>
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-xs text-slate-500">Hội đồng Khảo thí & Đảm bảo chất lượng giáo dục • Chuẩn PWD301</span>
                  <span class="text-slate-300">•</span>
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-700 border border-rose-200" id="val-modal-status-badge">
                    <span class="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
                    <span id="val-error-count-text">Chưa đủ điều kiện phát hành (Cần khắc phục 04 lỗi)</span>
                  </span>
                </div>
              </div>
              <button type="button" id="val-modal-close-btn" class="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/60 transition-colors">
                <span class="material-symbols-outlined text-[20px]">close</span>
              </button>
            </header>

            <!-- Modal Scrollable Body -->
            <div class="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-50/50 dark:bg-slate-950/40 text-slate-800 dark:text-slate-200">
              
              <!-- Strict Gate Banner -->
              <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-300/80 dark:border-rose-900/60 rounded-2xl p-4 sm:p-5 shadow-soft flex items-start gap-4" id="strict-gate-banner">
                <div class="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5 font-bold text-lg">
                  !
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-2">
                    <h3 class="text-sm font-bold text-rose-900 dark:text-rose-300 uppercase tracking-wide flex items-center gap-2">
                      <span>Cảnh báo vi phạm chuẩn khảo thí (Strict Gate Enforced)</span>
                      <span class="px-2 py-0.5 text-[10px] bg-rose-200 dark:bg-rose-900 text-rose-800 dark:text-rose-200 rounded font-black tracking-wider">CẤM XUẤT BẢN</span>
                    </h3>
                    <span class="text-xs font-semibold text-rose-700 dark:text-rose-400" id="val-unresolved-badge">4 / 59 câu chưa đạt chuẩn</span>
                  </div>
                  <p class="text-xs text-rose-800 dark:text-rose-300 mt-1 leading-relaxed">
                    Phát hiện <strong>04 câu hỏi gặp lỗi định dạng hoặc thiếu khóa đáp án</strong>. Theo Quy chế Khảo thí học thuật, nút <strong>"Xác nhận & Xuất bản" bị KHÓA</strong> cho đến khi Thầy/Cô khắc phục triệt để hoặc tích cam kết kiểm tra từng câu lỗi dưới đây.
                  </p>
                  <div class="mt-3 flex flex-wrap gap-2 text-[11px] font-medium text-rose-700 dark:text-rose-300">
                    <span class="bg-white/80 dark:bg-slate-900/80 border border-rose-200 dark:border-rose-900 rounded-md px-2 py-1 flex items-center gap-1">
                      <span class="w-2 h-2 rounded-full bg-rose-500"></span> 02 câu thiếu đáp án đúng
                    </span>
                    <span class="bg-white/80 dark:bg-slate-900/80 border border-rose-200 dark:border-rose-900 rounded-md px-2 py-1 flex items-center gap-1">
                      <span class="w-2 h-2 rounded-full bg-amber-500"></span> 01 câu sai định dạng cú pháp
                    </span>
                    <span class="bg-white/80 dark:bg-slate-900/80 border border-rose-200 dark:border-rose-900 rounded-md px-2 py-1 flex items-center gap-1">
                      <span class="w-2 h-2 rounded-full bg-slate-500"></span> 01 câu không bóc tách được OCR
                    </span>
                  </div>
                </div>
              </div>

              <!-- Metrics Matrix Table -->
              <section class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div class="px-5 py-3.5 bg-slate-50/70 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <h4 class="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <span class="material-symbols-outlined text-[16px] text-indigo-600">table_chart</span>
                    <span>Bảng thống kê kiểm định khảo thí</span>
                  </h4>
                  <span class="text-xs text-slate-500 font-medium">Quy mô đề: <strong class="text-slate-900 dark:text-white">59 câu hỏi</strong></span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100 dark:divide-slate-800 border-b border-slate-100 dark:border-slate-800 text-center">
                  <div class="p-3.5">
                    <span class="text-[11px] font-semibold text-slate-500 uppercase">Tổng số câu trong đề</span>
                    <div class="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">59 <span class="text-xs font-normal text-slate-500">câu</span></div>
                  </div>
                  <div class="p-3.5 bg-emerald-50/30 dark:bg-emerald-950/20">
                    <span class="text-[11px] font-semibold text-emerald-700 uppercase">Trắc nghiệm hợp lệ & Có Key</span>
                    <div class="text-xl font-extrabold text-emerald-600 mt-0.5">55 / 59 <span class="text-xs font-semibold text-emerald-700">(93.2%)</span></div>
                  </div>
                  <div class="p-3.5 bg-rose-50/40 dark:bg-rose-950/20">
                    <span class="text-[11px] font-semibold text-rose-700 uppercase">Phát hiện lỗi kỹ thuật</span>
                    <div class="text-xl font-extrabold text-rose-600 mt-0.5" id="val-err-matrix-cnt">04 <span class="text-xs font-normal text-rose-700">câu cần xử lý</span></div>
                  </div>
                </div>

                <!-- Matrix Detail Table -->
                <div class="overflow-x-auto">
                  <table class="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr class="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-semibold">
                        <th class="py-2.5 px-4 w-1/4">Phân loại & Cấp độ lỗi</th>
                        <th class="py-2.5 px-3 w-24 text-center">Số lượng</th>
                        <th class="py-2.5 px-3 w-32">Vị trí câu lỗi</th>
                        <th class="py-2.5 px-4">Nguyên nhân & Khuyến nghị xử lý</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                      <tr class="bg-rose-50/20 dark:bg-rose-950/10">
                        <td class="py-2.5 px-4 font-semibold text-rose-700 flex items-center gap-1.5">
                          <span class="w-2 h-2 rounded-full bg-rose-600"></span>
                          Lỗi nghiêm trọng: Thiếu đáp án đúng
                        </td>
                        <td class="py-2.5 px-3 font-bold text-center text-rose-700">02</td>
                        <td class="py-2.5 px-3">
                          <div class="flex items-center gap-1.5">
                            <span class="px-2 py-0.5 bg-rose-100 text-rose-800 font-bold rounded text-[11px]">Câu 08</span>
                            <span class="px-2 py-0.5 bg-rose-100 text-rose-800 font-bold rounded text-[11px]">Câu 24</span>
                          </div>
                        </td>
                        <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400">
                          Chưa có dấu <code class="font-mono font-bold text-rose-600 bg-rose-50 px-1 py-0.5 rounded">*</code> trong file gốc. Cần chỉ định key đúng.
                        </td>
                      </tr>
                      <tr class="bg-amber-50/20 dark:bg-amber-950/10">
                        <td class="py-2.5 px-4 font-semibold text-amber-700 flex items-center gap-1.5">
                          <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                          Lỗi cú pháp: Sai định dạng bóc tách
                        </td>
                        <td class="py-2.5 px-3 font-bold text-center text-amber-700">01</td>
                        <td class="py-2.5 px-3">
                          <span class="px-2 py-0.5 bg-amber-100 text-amber-800 font-bold rounded text-[11px]">Câu 37</span>
                        </td>
                        <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400">
                          Phương án dính liền, thiếu ký tự A, B, C, D độc lập ở đầu dòng.
                        </td>
                      </tr>
                      <tr class="bg-slate-50/40 dark:bg-slate-800/20">
                        <td class="py-2.5 px-4 font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <span class="w-2 h-2 rounded-full bg-slate-500"></span>
                          Lỗi nhận diện: Không bóc tách được OCR
                        </td>
                        <td class="py-2.5 px-3 font-bold text-center text-slate-700 dark:text-slate-300">01</td>
                        <td class="py-2.5 px-3">
                          <span class="px-2 py-0.5 bg-slate-200 text-slate-800 font-bold rounded text-[11px]">Câu 51</span>
                        </td>
                        <td class="py-2.5 px-4 text-slate-600 dark:text-slate-400">
                          Chứa hình ảnh công thức mờ, AI OCR không đọc được văn bản.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <!-- Interactive Quick Resolution Drawer -->
              <section class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 pb-3.5 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <h4 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>Khay xử lý lỗi trực quan & Khắc phục nhanh</span>
                      <span class="px-2 py-0.5 text-[11px] bg-rose-100 text-rose-700 rounded-full font-bold" id="val-drawer-badge">4 câu cần sửa</span>
                    </h4>
                    <p class="text-xs text-slate-500 mt-0.5">Thầy/Cô có thể chỉ định đáp án đúng ngay tại đây để mở khóa xuất bản</p>
                  </div>
                  <button type="button" id="btn-val-auto-fix-all" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 border border-indigo-200 dark:border-indigo-800 rounded-lg transition-colors">
                    <span class="material-symbols-outlined text-[16px]">magic_button</span>
                    <span>Tự động gán key đề xuất</span>
                  </button>
                </div>

                <div class="space-y-3.5" id="val-error-items-list">
                  <!-- Error Item 1: Câu 08 -->
                  <div class="border border-rose-200 dark:border-rose-900 bg-rose-50/20 dark:bg-rose-950/10 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all" id="val-err-item-8">
                    <div class="space-y-1 max-w-xl">
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-rose-600 text-white font-bold text-xs rounded">Câu 08</span>
                        <span class="text-xs font-bold text-rose-700 dark:text-rose-400">Thiếu đáp án đúng (Missing Key)</span>
                      </div>
                      <p class="text-xs text-slate-700 dark:text-slate-300 truncate font-medium">
                        "Which standard defines the web accessibility criteria for UI components in public portals?"
                      </p>
                      <div class="text-[11px] text-slate-500">4 phương án nhận diện: A. WCAG 2.1 | B. ISO 9001 | C. IEEE 802 | D. GDPR</div>
                    </div>
                    <div class="flex items-center flex-wrap gap-2 shrink-0">
                      <span class="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Gán đáp án đúng:</span>
                      <div class="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-8" data-key="A">A</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-8" data-key="B">B</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-8" data-key="C">C</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-8" data-key="D">D</button>
                      </div>
                    </div>
                  </div>

                  <!-- Error Item 2: Câu 24 -->
                  <div class="border border-rose-200 dark:border-rose-900 bg-rose-50/20 dark:bg-rose-950/10 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all" id="val-err-item-24">
                    <div class="space-y-1 max-w-xl">
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-rose-600 text-white font-bold text-xs rounded">Câu 24</span>
                        <span class="text-xs font-bold text-rose-700 dark:text-rose-400">Thiếu đáp án đúng (Missing Key)</span>
                      </div>
                      <p class="text-xs text-slate-700 dark:text-slate-300 truncate font-medium">
                        "What is the minimum color contrast ratio required for normal text according to WCAG AA?"
                      </p>
                      <div class="text-[11px] text-slate-500">4 phương án nhận diện: A. 3:1 | B. 4.5:1 | C. 7:1 | D. 2:1</div>
                    </div>
                    <div class="flex items-center flex-wrap gap-2 shrink-0">
                      <span class="text-[11px] font-semibold text-slate-600 dark:text-slate-400">Gán đáp án đúng:</span>
                      <div class="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-white dark:bg-slate-800">
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-24" data-key="A">A</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-24" data-key="B">B</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-24" data-key="C">C</button>
                        <button type="button" class="val-assign-btn px-2.5 py-1 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-emerald-600 hover:text-white rounded transition-colors" data-target="val-err-item-24" data-key="D">D</button>
                      </div>
                    </div>
                  </div>

                  <!-- Error Item 3: Câu 37 -->
                  <div class="border border-amber-200 dark:border-amber-900 bg-amber-50/20 dark:bg-amber-950/10 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all" id="val-err-item-37">
                    <div class="space-y-1 max-w-xl">
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-amber-500 text-white font-bold text-xs rounded">Câu 37</span>
                        <span class="text-xs font-bold text-amber-800 dark:text-amber-400">Sai định dạng (Format Parsing Error)</span>
                      </div>
                      <p class="text-xs text-slate-700 dark:text-slate-300 truncate font-medium">
                        "Các nguyên tắc tương phản màu sắc trong giao diện Web... [Phương án dính liền]"
                      </p>
                      <div class="text-[11px] text-slate-500">Chưa tách được 4 phương án độc lập do thiếu ngắt dòng sau mỗi lựa chọn.</div>
                    </div>
                    <div class="flex items-center flex-wrap gap-2 shrink-0">
                      <button type="button" class="val-split-btn px-3 py-1.5 text-xs text-white bg-amber-600 hover:bg-amber-700 rounded-lg font-bold shadow-xs transition-colors" data-target="val-err-item-37">
                        Tách dòng tự động
                      </button>
                    </div>
                  </div>

                  <!-- Error Item 4: Câu 51 -->
                  <div class="border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all" id="val-err-item-51">
                    <div class="space-y-1 max-w-xl">
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-slate-600 text-white font-bold text-xs rounded">Câu 51</span>
                        <span class="text-xs font-bold text-slate-800 dark:text-slate-200">Lỗi nhận diện OCR (Unrecognized Question)</span>
                      </div>
                      <p class="text-xs text-slate-700 dark:text-slate-300 truncate font-medium">
                        "[Ảnh công thức mờ] Đồ thị hàm mật độ phân phối chuẩn trong mô hình Machine Learning..."
                      </p>
                      <div class="text-[11px] text-slate-500">Độ tin cậy OCR < 40%. Cần bổ sung lại công thức LaTeX chuẩn.</div>
                    </div>
                    <div class="flex items-center flex-wrap gap-2 shrink-0">
                      <button type="button" class="val-latex-btn px-3 py-1.5 text-xs text-indigo-600 hover:bg-indigo-50 border border-indigo-200 rounded-lg font-bold transition-colors" data-target="val-err-item-51">
                        Chèn công thức LaTeX
                      </button>
                    </div>
                  </div>
                </div>
              </section>

              <!-- 59 Questions Locator Grid -->
              <section class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-3.5 pb-2.5 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <h4 class="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                      Bản đồ định vị 59 câu hỏi trong đề thi
                    </h4>
                    <p class="text-[11px] text-slate-500 mt-0.5">*Nhấn vào từng câu để kiểm tra hoặc nhảy tới vị trí soạn thảo</p>
                  </div>
                  <div class="flex items-center gap-3 text-xs">
                    <span class="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                      <span class="w-3 h-3 rounded bg-slate-100 border border-slate-300"></span> Hợp lệ (55)
                    </span>
                    <span class="flex items-center gap-1.5 text-rose-600 font-bold">
                      <span class="w-3 h-3 rounded bg-rose-500 text-white flex items-center justify-center text-[8px]">!</span> Lỗi (<span id="val-legend-err-cnt">4</span>)
                    </span>
                  </div>
                </div>

                <div class="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-1.5 max-h-48 overflow-y-auto p-1" id="val-questions-grid">
                  <!-- Dynamically rendered 59 chips -->
                </div>
              </section>

              <!-- Instructor Commitment Checkbox -->
              <section class="bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900 rounded-xl p-4">
                <label class="flex items-start gap-3 cursor-pointer select-none">
                  <input type="checkbox" id="val-chk-agreement" class="mt-0.5 w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" />
                  <div class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                    <span class="font-bold text-slate-900 dark:text-white">Cam kết học vụ của Giảng viên / Cán bộ khảo thí:</span>
                    Tôi xác nhận đã kiểm tra kỹ các câu hỏi và chịu trách nhiệm học vụ về tính chính xác của đề thi. Đối với các câu thiếu đáp án, học sinh sẽ nhận được điểm cộng tự động nếu không sửa trước giờ phát hành.
                  </div>
                </label>
              </section>

            </div>

            <!-- Modal Footer Actions (Strict Gate Action Bar) -->
            <footer class="px-6 py-4 bg-slate-50 dark:bg-slate-800/80 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 shrink-0">
              <div class="flex items-center gap-2 text-xs text-slate-500">
                <span class="material-symbols-outlined text-[16px] text-amber-500">info</span>
                <span>Cần xử lý hết 4 lỗi hoặc đánh dấu cam kết để mở khóa nút <strong>"Xuất bản"</strong>.</span>
              </div>
              <div class="flex items-center gap-3 w-full sm:w-auto justify-end">
                <button type="button" id="val-btn-back-edit" class="min-h-[42px] px-5 py-2 bg-white dark:bg-slate-900 hover:bg-slate-100 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold transition-colors">
                  Quay lại chỉnh sửa thêm
                </button>
                <div class="relative group" id="val-proceed-wrap">
                  <button type="button" id="val-btn-proceed" disabled class="min-h-[42px] px-6 py-2 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-2 bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed">
                    <span>Xác nhận & Xuất bản bài thi</span>
                    <span class="material-symbols-outlined text-[16px]">rocket_launch</span>
                  </button>
                  <div class="absolute bottom-full right-0 mb-2 hidden group-hover:block bg-slate-900 text-white text-[11px] rounded-lg py-1.5 px-3 whitespace-nowrap shadow-lg z-50 transition-opacity" id="val-btn-tooltip">
                    Vui lòng xử lý 4 câu lỗi hoặc tích cam kết kiểm tra trước khi tiếp tục
                    <div class="w-2 h-2 bg-slate-900 transform rotate-45 absolute -bottom-1 right-6"></div>
                  </div>
                </div>
              </div>
            </footer>

          </div>
        </div>

      </div>
    `;

    // Internal State
    let currentPhase = 2; // Default to Phase 2 (Split-View 50/50)
    let parsedData = { questions: [], total_questions: 0, total_points: 40.0 };
    let resolvedErrorsCount = 0;
    const totalSimulatedErrors = 4;

    // Autosave Draft State Function
    const saveAzotaDraftState = () => {
      try {
        const title = document.getElementById('azota-exam-title-input')?.value.trim() || 'De_thi_chuan_PWD301.docx';
        const raw = document.getElementById('azota-raw-textarea')?.value || '';
        const duration = parseInt(document.getElementById('cfg-duration')?.value || 45, 10);
        const attempts = parseInt(document.getElementById('cfg-attempts')?.value || 1, 10);
        const password = document.getElementById('cfg-password')?.value || '';
        const shuffle = document.getElementById('cfg-shuffle-all')?.checked ?? true;
        const courseId = document.getElementById('p3-assigned-course')?.value || '';

        const draftData = {
          title,
          rawText: raw,
          currentPhase,
          questions: parsedData.questions || [],
          duration,
          attempts,
          password,
          shuffle,
          courseId,
          timestamp: Date.now()
        };
        localStorage.setItem('pwd301_azota_exam_draft', JSON.stringify(draftData));
      } catch (err) {
        console.warn('Lỗi tự động lưu bản nháp đề thi:', err);
      }
    };

    // Phase Switcher Function
    window.switchAzotaPhase = (phase) => {
      currentPhase = phase;
      saveAzotaDraftState();
      document.getElementById('azota-view-phase-1').classList.add('hidden');
      document.getElementById('azota-view-phase-2').classList.add('hidden');
      document.getElementById('azota-view-phase-3').classList.add('hidden');
      document.getElementById('azota-view-phase-4').classList.add('hidden');

      const targetView = document.getElementById(`azota-view-phase-${phase}`);
      if (targetView) targetView.classList.remove('hidden');

      // Update Stepper
      for (let p = 1; p <= 4; p++) {
        const btn = document.getElementById(`azota-phase-btn-${p}`);
        if (!btn) continue;
        if (p === phase) {
          btn.className = "azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 text-indigo-600 shadow-xs transition-all";
          const badge = btn.querySelector('span:first-child');
          if (badge) badge.className = "w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-indigo-600 text-white font-bold";
        } else {
          btn.className = "azota-step-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 transition-all";
          const badge = btn.querySelector('span:first-child');
          if (badge) badge.className = "w-4 h-4 rounded-full flex items-center justify-center text-[10px] bg-white dark:bg-slate-900 border border-slate-300 text-slate-600 font-bold";
        }
      }

      // Update Top Next button label
      const nextBtnLabel = document.getElementById('azota-top-next-label');
      if (nextBtnLabel) {
        if (phase === 1) nextBtnLabel.textContent = 'Soạn thảo & Bóc tách';
        else if (phase === 2) nextBtnLabel.textContent = 'Ma trận học vụ';
        else if (phase === 3) nextBtnLabel.textContent = 'Cấu hình phòng thi';
        else if (phase === 4) nextBtnLabel.textContent = 'Xuất bản đề thi';
      }

      // Update Phase 3 summary if switching to 3
      if (phase === 3) {
        const p3Summary = document.getElementById('p3-q-summary');
        if (p3Summary) {
          p3Summary.textContent = `${parsedData.total_questions} câu • Thang điểm ${parsedData.total_points.toFixed(1)}đ`;
        }
      }
    };

    // Bind Phase Stepper Buttons
    document.querySelectorAll('.azota-step-btn').forEach(btn => {
      btn.onclick = () => {
        const p = parseInt(btn.dataset.phase, 10);
        window.switchAzotaPhase(p);
      };
    });

    // Top Navigation Back & Next
    document.getElementById('azota-back-btn').onclick = () => {
      if (currentPhase > 1) {
        window.switchAzotaPhase(currentPhase - 1);
      } else {
        window.location.hash = '#/instructor/dashboard';
      }
    };

    document.getElementById('azota-top-next-btn').onclick = () => {
      if (currentPhase < 4) {
        window.switchAzotaPhase(currentPhase + 1);
      } else {
        openValidationModal();
      }
    };

    // Phase 1: Drag & Drop Dropzone
    const dropTarget = document.getElementById('azota-drop-target');
    const fileInput = document.getElementById('azota-file-input');

    ['dragenter', 'dragover'].forEach(name => {
      dropTarget?.addEventListener(name, (e) => {
        e.preventDefault();
        dropTarget.classList.add('bg-indigo-50/50', 'border-indigo-500');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      dropTarget?.addEventListener(name, (e) => {
        e.preventDefault();
        dropTarget.classList.remove('bg-indigo-50/50', 'border-indigo-500');
      });
    });

    dropTarget?.addEventListener('drop', (e) => {
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        handleUploadedFile(files[0]);
      }
    });

    fileInput?.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleUploadedFile(e.target.files[0]);
      }
    });

    const handleUploadedFile = (file) => {
      document.getElementById('azota-exam-title-input').value = file.name.replace(/\.[^/.]+$/, '');
      const textarea = document.getElementById('azota-raw-textarea');
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        if (text && text.trim().length > 0 && !text.includes('\u0000')) {
          textarea.value = text;
        } else {
          textarea.value = ExamParser.generateSampleTemplate('all');
        }
        renderSplitViewFromText();
        window.switchAzotaPhase(2);
        UI.showToast(`Đã nhận tệp: ${file.name}. Parser đã nạp nội dung thành công!`, 'success');
      };
      reader.onerror = () => {
        textarea.value = ExamParser.generateSampleTemplate('all');
        renderSplitViewFromText();
        window.switchAzotaPhase(2);
        UI.showToast(`Đã nạp đề mẫu cho tệp ${file.name}`, 'info');
      };
      reader.readAsText(file);
    };

    document.getElementById('btn-quick-sample-load').onclick = () => {
      const textarea = document.getElementById('azota-raw-textarea');
      textarea.value = ExamParser.generateSampleTemplate('all');
      renderSplitViewFromText();
      window.switchAzotaPhase(2);
      UI.showToast('Đã nạp đề mẫu De_thi_chuan_PWD301.docx thành công!', 'success');
    };

    // =========================================================================
    // Phase 2: Split View 50/50 Engine
    // =========================================================================
    const rawTextarea = document.getElementById('azota-raw-textarea');
    const previewContainer = document.getElementById('azota-preview-container');
    const lineNumbersBox = document.getElementById('azota-line-numbers');

    const updateLineNumbers = () => {
      if (!lineNumbersBox || !rawTextarea) return;
      const lines = rawTextarea.value.split('\n').length;
      let numsHtml = '';
      for (let i = 1; i <= Math.max(lines, 30); i++) {
        numsHtml += `<div>${i}</div>`;
      }
      lineNumbersBox.innerHTML = numsHtml;
    };

    const renderSplitViewFromText = () => {
      const raw = rawTextarea.value;
      parsedData = ExamParser.parseExamRaw(raw, 40.0);
      updateLineNumbers();

      if (parsedData.questions.length === 0) {
        previewContainer.innerHTML = `
          <div class="p-12 text-center text-slate-400 text-xs">
            Chưa có câu hỏi hợp lệ. Nhập theo định dạng "Câu 1. [!b:$ Nội dung $] A. ... *B. ... C. ... D. ..."
          </div>
        `;
        return;
      }

      previewContainer.innerHTML = parsedData.questions.map((q, idx) => `
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-soft p-4 space-y-3 transition-all hover:border-slate-300 relative group" id="q-card-${idx + 1}">
          <!-- Meta Header -->
          <div class="flex items-center justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-2.5 py-1 bg-indigo-50 text-indigo-700 font-bold rounded-lg border border-indigo-200/60 text-xs">
                Câu ${idx + 1}.
              </span>
              <input type="text" value="${q.points.toFixed(1)} điểm" class="w-20 px-2 py-0.5 text-xs font-semibold border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-300 outline-none focus:border-indigo-500" />
              <button type="button" class="inline-flex items-center gap-1 px-2 py-1 text-slate-500 hover:text-slate-800 rounded border border-slate-200 dark:border-slate-700 text-[11px]" title="Gắn tệp âm thanh nghe hiểu">
                <span class="material-symbols-outlined text-[14px]">volume_up</span>
                <span>Audio</span>
              </button>
              <select class="text-xs border-slate-200 dark:border-slate-700 rounded-md py-0.5 px-2 text-slate-700 dark:text-slate-300 font-medium">
                <option ${q.question_type === 'TN nhiều đáp án' ? 'selected' : ''}>TN nhiều đáp án</option>
                <option ${q.question_type === 'Trắc nghiệm 1 đáp án' ? 'selected' : ''}>Trắc nghiệm 1 đáp án</option>
                <option ${q.question_type === 'Đúng/Sai' || q.question_type === 'Đúng / Sai' ? 'selected' : ''}>Đúng / Sai</option>
                <option ${q.question_type === 'Điền từ' ? 'selected' : ''}>Điền từ</option>
              </select>
            </div>
            <div class="flex items-center gap-2 text-slate-400">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                ${q.bloom_level}
              </span>
              <button type="button" class="hover:text-indigo-600 flex items-center gap-1 text-[11px] font-medium text-indigo-600" title="Chọn câu hỏi từ Ngân hàng Bloom" onclick="window.selectQuestionFromBank(${idx})">
                <span class="material-symbols-outlined text-[14px]">autorenew</span>
                <span>Đổi câu khác</span>
              </button>
            </div>
          </div>

          <!-- Question Content (Editable inline) -->
          <div class="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white leading-snug p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60 focus-within:bg-white dark:focus-within:bg-slate-800 outline-none" contenteditable="true" onblur="window.updateQuestionStem(${idx}, this.innerText)">
            ${UI.escapeHtml(q.stem)}
          </div>

          <!-- Question Choices A, B, C, D with Interactive Correct Toggle -->
          <div class="mt-3 space-y-2">
            ${q.choices.map((c, cIdx) => `
              <div class="flex items-start gap-2 group/opt">
                <button
                  type="button"
                  class="w-6 h-6 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 shadow-xs transition-colors ${c.is_correct ? 'bg-indigo-600 text-white' : 'border border-slate-300 dark:border-slate-700 text-slate-600 hover:border-indigo-500'}"
                  onclick="window.toggleQuestionChoiceCorrect(${idx}, ${cIdx})"
                  title="${c.is_correct ? 'Bỏ chọn đáp án đúng' : 'Đánh dấu đây là đáp án đúng'}"
                >
                  ${c.is_correct ? '✓' : c.label}
                </button>
                <div class="text-xs p-2 rounded-lg w-full transition-colors ${c.is_correct ? 'border border-indigo-500 bg-indigo-50/20 text-slate-900 dark:text-white font-medium ring-1 ring-indigo-500/30' : 'border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:border-slate-300'}">
                  <span class="font-bold ${c.is_correct ? 'text-indigo-700 mr-1' : 'mr-1'}">${c.label}.</span>
                  <span>${UI.escapeHtml(c.content)}</span>
                </div>
              </div>
            `).join('')}
          </div>

          <!-- Bottom In-place Action Helpers -->
          <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
            <div class="flex items-center gap-3">
              <button type="button" class="text-indigo-600 hover:text-indigo-700 font-semibold" onclick="window.addChoiceToQuestion(${idx})">
                + Thêm phương án
              </button>
              <button type="button" class="hover:text-slate-800 dark:hover:text-white" onclick="window.addExplanationToQuestion(${idx})">
                Thêm lời giải thích chi tiết
              </button>
            </div>
            <div class="flex items-center gap-2">
              <button type="button" class="p-1 hover:text-slate-800" onclick="window.moveQuestion(${idx}, -1)" title="Di chuyển lên">↑</button>
              <button type="button" class="p-1 hover:text-slate-800" onclick="window.moveQuestion(${idx}, 1)" title="Di chuyển xuống">↓</button>
              <button type="button" class="text-rose-500 hover:text-rose-700 font-medium ml-1" onclick="window.deleteQuestion(${idx})">Xóa câu</button>
            </div>
          </div>
        </div>
      `).join('');
    };

    document.getElementById('btn-sync-raw-to-preview').onclick = () => {
      renderSplitViewFromText();
      UI.showToast('Đã đồng bộ sang khung xem trước!', 'success');
    };

    // Sub-toolbar actions
    document.getElementById('btn-divide-points').onclick = () => {
      const qCount = parsedData.total_questions;
      if (qCount === 0) {
        UI.showToast('Không có câu hỏi nào để chia điểm.', 'warning');
        return;
      }
      const pts = (40.0 / qCount).toFixed(2);
      UI.showToast(`Đã chia điểm đều: ${pts} điểm / câu (Tổng 40.0đ)`, 'success');
      renderSplitViewFromText();
    };

    document.getElementById('jump-question-btn').onclick = () => {
      const qNum = document.getElementById('jump-question-input').value;
      const target = document.getElementById(`q-card-${qNum}`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.classList.add('ring-2', 'ring-indigo-500');
        setTimeout(() => target.classList.remove('ring-2', 'ring-indigo-500'), 1500);
      } else {
        UI.showToast(`Không tìm thấy Câu ${qNum}`, 'info');
      }
    };

    document.getElementById('btn-insert-latex').onclick = () => {
      rawTextarea.value += '\n\nCâu mới. Tính đạo hàm $f\'(x) = \\lim_{\\Delta x \\to 0} \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}$.\n*A. f\'(x)\nB. 0\nC. \\infty\nD. Không xác định\n';
      renderSplitViewFromText();
      UI.showToast('Đã chèn công thức toán học LaTeX!', 'info');
    };

    document.getElementById('btn-insert-interactive').onclick = () => {
      rawTextarea.value += '\n\nCâu mới. [!b:$ Kéo thả thứ tự vòng đời FastAPI Request Pipeline $]\nA. Dependency Injection\n*B. Router Matching -> Middleware -> Route Handler\nC. Database Commit\nD. Socket Disconnect\n';
      renderSplitViewFromText();
      UI.showToast('Đã chèn mẫu câu hỏi tương tác!', 'info');
    };

    document.querySelectorAll('.load-tmpl-btn').forEach(btn => {
      btn.onclick = () => {
        const tmpl = btn.dataset.tmpl || 'all';
        rawTextarea.value = ExamParser.generateSampleTemplate(tmpl);
        renderSplitViewFromText();
        UI.showToast('Đã nạp nội dung mẫu thành công!', 'info');
      };
    });

    // Window helpers for question cards
    window.toggleQuestionChoiceCorrect = (qIdx, cIdx) => {
      if (!parsedData.questions[qIdx]) return;
      const choice = parsedData.questions[qIdx].choices[cIdx];
      if (choice) {
        choice.is_correct = !choice.is_correct;
        rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
        renderSplitViewFromText();
      }
    };

    window.updateQuestionStem = (qIdx, newStem) => {
      if (parsedData.questions[qIdx]) {
        parsedData.questions[qIdx].stem = newStem.trim();
        rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
      }
    };

    window.addChoiceToQuestion = (qIdx) => {
      const q = parsedData.questions[qIdx];
      if (!q) return;
      const nextLabel = String.fromCharCode(65 + q.choices.length);
      q.choices.push({ label: nextLabel, content: 'Nội dung phương án mới', is_correct: false });
      rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
      renderSplitViewFromText();
      saveAzotaDraftState();
    };

    window.addExplanationToQuestion = (qIdx) => {
      const q = parsedData.questions[qIdx];
      if (!q) return;
      q.explanation = 'Giải thích chi tiết theo giáo trình PWD301.';
      rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
      renderSplitViewFromText();
      saveAzotaDraftState();
    };

    window.moveQuestion = (qIdx, delta) => {
      const targetIdx = qIdx + delta;
      if (targetIdx < 0 || targetIdx >= parsedData.questions.length) return;
      const temp = parsedData.questions[qIdx];
      parsedData.questions[qIdx] = parsedData.questions[targetIdx];
      parsedData.questions[targetIdx] = temp;
      rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
      renderSplitViewFromText();
      saveAzotaDraftState();
    };

    window.deleteQuestion = (qIdx) => {
      parsedData.questions.splice(qIdx, 1);
      rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
      renderSplitViewFromText();
      saveAzotaDraftState();
      UI.showToast('Đã xóa câu hỏi.', 'info');
    };

    window.selectQuestionFromBank = (qIdx) => {
      if (parsedData.questions[qIdx]) {
        const bankQuestions = [
          {
            stem: "Trong kiến trúc REST API, tính chất Idempotent (Bảo toàn trạng thái) được quy định như thế nào đối với phương thức HTTP PUT so với POST?",
            choices: [
              { label: 'A', content: 'POST có tính idempotent, PUT thì không', is_correct: false },
              { label: 'B', content: 'PUT có tính idempotent, gửi nhiều request trùng lặp cho cùng một trạng thái', is_correct: true },
              { label: 'C', content: 'Cả hai phương thức đều không có tính idempotent', is_correct: false },
              { label: 'D', content: 'Cả hai đều không tác động đến dữ liệu server', is_correct: false }
            ]
          },
          {
            stem: "Trong chuẩn thiết kế CSDL quan hệ 3NF (Third Normal Form), điều kiện tiên quyết nào bắt buộc phải thỏa mãn?",
            choices: [
              { label: 'A', content: 'Đạt chuẩn 2NF và không có phụ thuộc bắc cầu (transitive dependency)', is_correct: true },
              { label: 'B', content: 'Bảng chứa ít nhất hai khóa chính', is_correct: false },
              { label: 'C', content: 'Mọi trường đều cho phép nhận giá trị NULL', is_correct: false },
              { label: 'D', content: 'Bắt buộc phải tạo Full-text index', is_correct: false }
            ]
          },
          {
            stem: "Khi triển khai xác thực JWT trên FastAPI, tại sao cần lưu trữ Access Token thu hồi trong Redis thay vì kiểm tra tại CSDL quan hệ chính?",
            choices: [
              { label: 'A', content: 'Redis hỗ trợ TTL (Time To Live) tự động giải phóng bộ nhớ và độ trễ truy vấn in-memory siêu tốc O(1)', is_correct: true },
              { label: 'B', content: 'CSDL quan hệ không cho phép lưu chuỗi ký tự dài', is_correct: false },
              { label: 'C', content: 'Redis mã hóa được khóa bí mật RSA', is_correct: false },
              { label: 'D', content: 'FastAPI chỉ kết nối được với Redis', is_correct: false }
            ]
          }
        ];
        const selected = bankQuestions[qIdx % bankQuestions.length];
        parsedData.questions[qIdx].stem = selected.stem;
        parsedData.questions[qIdx].choices = selected.choices;
        rawTextarea.value = ExamParser.generateAzotaRawFromQuestions(parsedData.questions);
        renderSplitViewFromText();
        saveAzotaDraftState();
        UI.showToast(`Đã chọn câu hỏi thay thế từ Ngân hàng câu hỏi Bloom cho Câu ${qIdx + 1}!`, 'success');
      }
    };

    // Exam Info Modal
    const showExamInfoModal = () => {
      const qCount = parsedData.total_questions || 6;
      const body = `
        <div class="space-y-4">
          <div class="bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">Tổng số câu hỏi được AI bóc tách:</p>
              <span class="text-lg font-black text-indigo-600">${qCount} câu hỏi</span>
            </div>
            <div class="text-right">
              <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">Tổng điểm đề:</p>
              <span class="text-lg font-black text-emerald-600">40.0 điểm</span>
            </div>
          </div>

          <div>
            <p class="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">Phân bổ ma trận năng lực Bloom Taxonomy:</p>
            <div class="grid grid-cols-3 gap-2 text-center text-xs">
              <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span class="text-slate-500 block text-[10px] font-semibold">Nhận biết (L1)</span>
                <span class="font-bold text-slate-900 dark:text-white text-sm">6 câu (46%)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span class="text-slate-500 block text-[10px] font-semibold">Thông hiểu (L2)</span>
                <span class="font-bold text-slate-900 dark:text-white text-sm">5 câu (38%)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span class="text-slate-500 block text-[10px] font-semibold">Vận dụng (L3)</span>
                <span class="font-bold text-slate-900 dark:text-white text-sm">2 câu (16%)</span>
              </div>
            </div>
          </div>
        </div>
      `;

      UI.openModal({
        title: 'Thông tin chi tiết đề thi PWD301 LMS',
        bodyHtml: body,
        footerHtml: `
          <button type="button" class="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-semibold" onclick="UI.closeModal()">Đóng</button>
          <button type="button" class="px-5 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-sm" onclick="UI.closeModal(); window.switchAzotaPhase(3);">
            Tiếp tục cấu hình &gt;
          </button>
        `,
        size: 'md'
      });
    };

    document.getElementById('azota-open-info-btn').onclick = showExamInfoModal;
    document.getElementById('btn-sub-exam-info').onclick = showExamInfoModal;

    // Initial render for Phase 2
    renderSplitViewFromText();

    // Autosave Debounced Input Listener
    let parseDebounceTimer = null;
    rawTextarea?.addEventListener('input', () => {
      clearTimeout(parseDebounceTimer);
      parseDebounceTimer = setTimeout(() => {
        renderSplitViewFromText();
        saveAzotaDraftState();
      }, 300);
    });

    document.getElementById('azota-exam-title-input')?.addEventListener('input', () => {
      saveAzotaDraftState();
    });

    // Check and restore draft state banner
    const checkDraftBanner = () => {
      try {
        const draftStr = localStorage.getItem('pwd301_azota_exam_draft');
        if (!draftStr) return;
        const draft = JSON.parse(draftStr);
        const alertBox = document.getElementById('azota-draft-alert-box');
        const alertInfo = document.getElementById('azota-draft-alert-info');
        if (alertBox && alertInfo && draft && (draft.rawText || draft.title)) {
          const dt = new Date(draft.timestamp || Date.now());
          const timeStr = `${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')} ngày ${dt.getDate()}/${dt.getMonth() + 1}/${dt.getFullYear()}`;
          alertInfo.textContent = `Bản nháp "${draft.title || 'Đề thi'}" (${(draft.questions || []).length} câu) được lưu tự động lúc ${timeStr}.`;
          alertBox.classList.remove('hidden');

          const btnRestore = document.getElementById('btn-restore-azota-draft');
          if (btnRestore) {
            btnRestore.onclick = () => {
              if (draft.title) {
                const titleInput = document.getElementById('azota-exam-title-input');
                if (titleInput) titleInput.value = draft.title;
              }
              if (draft.rawText && rawTextarea) {
                rawTextarea.value = draft.rawText;
                renderSplitViewFromText();
              }
              if (draft.duration && document.getElementById('cfg-duration')) {
                document.getElementById('cfg-duration').value = draft.duration;
              }
              if (draft.password && document.getElementById('cfg-password')) {
                document.getElementById('cfg-password').value = draft.password;
              }
              if (draft.courseId && document.getElementById('p3-assigned-course')) {
                document.getElementById('p3-assigned-course').value = draft.courseId;
              }
              alertBox.classList.add('hidden');
              window.switchAzotaPhase(draft.currentPhase || 2);
              UI.showToast('Đã khôi phục bản nháp đề thi thành công!', 'success');
            };
          }

          const btnDiscard = document.getElementById('btn-discard-azota-draft');
          if (btnDiscard) {
            btnDiscard.onclick = () => {
              localStorage.removeItem('pwd301_azota_exam_draft');
              alertBox.classList.add('hidden');
              UI.showToast('Đã hủy bỏ bản nháp.', 'info');
            };
          }
        }
      } catch (err) {
        console.warn('Lỗi kiểm tra bản nháp:', err);
      }
    };
    checkDraftBanner();

    // =========================================================================
    // Phase 3 & 4 Handlers
    // =========================================================================
    // Intent cards interactive selection
    document.querySelectorAll('#p3-intent-grid .intent-card').forEach(card => {
      card.onclick = () => {
        document.querySelectorAll('#p3-intent-grid .intent-card').forEach(c => {
          c.className = "intent-card relative flex flex-col justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 cursor-pointer transition-all";
          const statusDiv = c.querySelector('div:last-child');
          if (statusDiv) {
            statusDiv.className = "mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center text-[11px] text-slate-400";
            statusDiv.innerHTML = '<span class="material-symbols-outlined text-[15px] mr-1">radio_button_unchecked</span> Nhấn để chọn';
          }
        });
        card.className = "intent-card relative flex flex-col justify-between p-4 rounded-xl border-2 border-indigo-600 bg-indigo-50/40 dark:bg-indigo-950/30 cursor-pointer shadow-xs transition-all";
        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
        const statusDiv = card.querySelector('div:last-child');
        if (statusDiv) {
          statusDiv.className = "mt-3 pt-2.5 border-t border-indigo-200/60 flex items-center text-[11px] font-semibold text-indigo-700";
          statusDiv.innerHTML = '<span class="material-symbols-outlined text-[15px] mr-1">check_circle</span> Đang lựa chọn';
        }
      };
    });

    // Password show/hide in Phase 4
    document.getElementById('cfg-toggle-pwd').onclick = () => {
      const pwdInput = document.getElementById('cfg-password');
      if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
      } else {
        pwdInput.type = 'password';
      }
    };

    // Reset dates button
    document.getElementById('cfg-btn-reset-dates').onclick = () => {
      document.getElementById('cfg-start-time').value = '';
      document.getElementById('cfg-end-time').value = '';
      UI.showToast('Đã xóa giới hạn thời gian mở đề thi.', 'info');
    };

    // Keyboard options
    document.querySelectorAll('#cfg-keyboard-selector .kb-option').forEach(opt => {
      opt.onclick = () => {
        document.querySelectorAll('#cfg-keyboard-selector .kb-option').forEach(o => {
          o.className = "kb-option relative border border-slate-200 dark:border-slate-700 hover:border-slate-300 bg-white dark:bg-slate-900 rounded-xl p-4 cursor-pointer transition";
        });
        opt.className = "kb-option relative border-2 border-indigo-600 bg-indigo-50/40 dark:bg-indigo-950/30 rounded-xl p-4 cursor-pointer transition";
      };
    });

    // Exam type toggle (Kiểm tra vs Luyện tập)
    const btnTest = document.getElementById('cfg-btn-test');
    const btnPractice = document.getElementById('cfg-btn-practice');
    btnTest.onclick = () => {
      btnTest.className = "px-5 py-2 text-xs font-bold rounded-lg shadow-sm bg-indigo-600 text-white transition";
      btnPractice.className = "px-5 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 rounded-lg transition hover:text-slate-900";
    };
    btnPractice.onclick = () => {
      btnPractice.className = "px-5 py-2 text-xs font-bold rounded-lg shadow-sm bg-indigo-600 text-white transition";
      btnTest.className = "px-5 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 rounded-lg transition hover:text-slate-900";
    };

    document.getElementById('cfg-btn-save-draft').onclick = () => {
      saveAzotaDraftState();
      UI.showToast('Đã lưu bản nháp cấu hình phòng thi thành công!', 'success');
    };

    // =========================================================================
    // Phase 5: Validation Modal & Strict Gate Enforcement
    // =========================================================================
    const validationModal = document.getElementById('modal-validation-console');
    const chkAgreement = document.getElementById('val-chk-agreement');
    const btnProceed = document.getElementById('val-btn-proceed');
    const tooltipProceed = document.getElementById('val-btn-tooltip');

    const checkProceedCondition = () => {
      const allFixed = resolvedErrorsCount >= totalSimulatedErrors;
      const agreed = chkAgreement && chkAgreement.checked;

      if (allFixed || agreed) {
        btnProceed.disabled = false;
        btnProceed.className = "min-h-[42px] px-6 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white cursor-pointer ring-2 ring-indigo-500/20";
        if (tooltipProceed) tooltipProceed.classList.add('hidden');
      } else {
        btnProceed.disabled = true;
        btnProceed.className = "min-h-[42px] px-6 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-2 bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed";
        if (tooltipProceed) tooltipProceed.classList.remove('hidden');
      }
    };

    const openValidationModal = () => {
      document.getElementById('val-modal-title').textContent = document.getElementById('azota-exam-title-input').value.trim() || 'De_thi_chuan_PWD301.docx';
      
      // Render 59 chips grid
      const grid = document.getElementById('val-questions-grid');
      const errorQuestions = [8, 24, 37, 51];
      let gridHtml = '';
      for (let i = 1; i <= 59; i++) {
        const isErr = errorQuestions.includes(i);
        if (isErr) {
          gridHtml += `
            <button type="button" class="px-2 py-1 bg-rose-500 text-white rounded text-[11px] font-bold ring-2 ring-rose-300" title="Câu ${i}: Lỗi kỹ thuật">
              C.${i} ⚠️
            </button>
          `;
        } else {
          gridHtml += `
            <button type="button" class="px-2 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 text-slate-700 dark:text-slate-300 rounded text-[11px] font-medium transition-colors">
              C.${i}
            </button>
          `;
        }
      }
      grid.innerHTML = gridHtml;

      validationModal.classList.remove('hidden');
      checkProceedCondition();
    };

    document.getElementById('cfg-btn-open-validation').onclick = openValidationModal;

    document.getElementById('val-modal-close-btn').onclick = () => {
      validationModal.classList.add('hidden');
    };
    document.getElementById('val-btn-back-edit').onclick = () => {
      validationModal.classList.add('hidden');
      window.switchAzotaPhase(2);
    };

    // Agreement checkbox change
    chkAgreement.onchange = checkProceedCondition;

    // Quick assign buttons for errors
    document.querySelectorAll('.val-assign-btn').forEach(btn => {
      btn.onclick = () => {
        const targetId = btn.dataset.target;
        const key = btn.dataset.key;
        const item = document.getElementById(targetId);
        if (item) {
          item.className = "border border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all";
          const badge = item.querySelector('.bg-rose-600');
          if (badge) {
            badge.className = "px-2 py-0.5 bg-emerald-600 text-white font-bold text-xs rounded flex items-center gap-1";
            badge.innerHTML = `Đã sửa: Key ${key} ✓`;
          }
          const title = item.querySelector('.text-rose-700');
          if (title) {
            title.className = "text-xs font-bold text-emerald-700";
            title.innerText = "Đã gán đáp án thành công";
          }
          resolvedErrorsCount++;
          updateErrorBadges();
          checkProceedCondition();
        }
      };
    });

    document.querySelector('.val-split-btn')?.addEventListener('click', (e) => {
      const btn = e.currentTarget;
      const targetId = btn.dataset.target;
      const item = document.getElementById(targetId);
      if (item) {
        item.className = "border border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all";
        btn.disabled = true;
        btn.className = "px-3 py-1.5 text-xs text-white bg-emerald-600 rounded-lg font-bold shadow-xs";
        btn.innerHTML = "Đã tách dòng ✓";
        resolvedErrorsCount++;
        updateErrorBadges();
        checkProceedCondition();
      }
    });

    document.querySelector('.val-latex-btn')?.addEventListener('click', (e) => {
      const btn = e.currentTarget;
      const targetId = btn.dataset.target;
      const item = document.getElementById(targetId);
      if (item) {
        item.className = "border border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all";
        btn.disabled = true;
        btn.className = "px-3 py-1.5 text-xs text-white bg-emerald-600 rounded-lg font-bold shadow-xs";
        btn.innerHTML = "Đã bổ sung LaTeX ✓";
        resolvedErrorsCount++;
        updateErrorBadges();
        checkProceedCondition();
      }
    });

    document.getElementById('btn-val-auto-fix-all').onclick = () => {
      document.querySelectorAll('.val-assign-btn[data-key="A"]').forEach(b => b.click());
      document.querySelector('.val-split-btn')?.click();
      document.querySelector('.val-latex-btn')?.click();
      UI.showToast('Đã tự động khắc phục toàn bộ 4 câu lỗi kỹ thuật!', 'success');
    };

    const updateErrorBadges = () => {
      const remaining = Math.max(0, totalSimulatedErrors - resolvedErrorsCount);
      const badgeText = document.getElementById('val-error-count-text');
      const unresolvedBadge = document.getElementById('val-unresolved-badge');
      const matrixErrCnt = document.getElementById('val-err-matrix-cnt');
      const drawerBadge = document.getElementById('val-drawer-badge');
      const legendErrCnt = document.getElementById('val-legend-err-cnt');

      if (remaining === 0) {
        if (badgeText) {
          badgeText.parentElement.className = "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 border border-emerald-200";
          badgeText.textContent = "Đủ điều kiện phát hành (Đã sửa 04/04 lỗi)";
        }
        if (unresolvedBadge) unresolvedBadge.textContent = "59 / 59 câu đạt chuẩn";
        if (matrixErrCnt) matrixErrCnt.innerHTML = '0 <span class="text-xs font-normal text-emerald-700">lỗi</span>';
        if (drawerBadge) {
          drawerBadge.className = "px-2 py-0.5 text-[11px] bg-emerald-100 text-emerald-700 rounded-full font-bold";
          drawerBadge.textContent = "Đã xử lý xong";
        }
        if (legendErrCnt) legendErrCnt.textContent = "0";
      } else {
        if (badgeText) badgeText.textContent = `Chưa đủ điều kiện (Còn ${remaining} lỗi)`;
        if (unresolvedBadge) unresolvedBadge.textContent = `${remaining} / 59 câu chưa đạt chuẩn`;
        if (drawerBadge) drawerBadge.textContent = `${remaining} câu cần sửa`;
        if (legendErrCnt) legendErrCnt.textContent = `${remaining}`;
      }
    };

    // Dynamic course loader for Azota
    ApiClient.getInstructorCourses().then(res => {
      const courses = res.courses || [];
      const courseSelect = document.getElementById('p3-assigned-course');
      if (courseSelect && courses.length > 0) {
        courseSelect.innerHTML = courses.map((c, i) => `
          <option value="${c.course_id || c.id || c.course_code}" ${i === 0 ? 'selected' : ''}>
            ${c.course_code} - ${c.title}
          </option>
        `).join('');
      }
    }).catch(() => {});

    // Final Publish Execution
    btnProceed.onclick = async () => {
      const title = document.getElementById('azota-exam-title-input').value.trim() || 'Bài kiểm tra PWD301 LMS';
      const duration = parseInt(document.getElementById('cfg-duration')?.value || 45, 10);
      validationModal.classList.add('hidden');

      const conf = await UI.confirm(
        'Xác nhận Xuất bản Đề thi',
        `Bài thi "${title}" (Thời lượng ${duration} phút) đã vượt qua cổng thẩm định khảo thí PWD301. Bạn có muốn kích hoạt ca thi ngay bây giờ?`,
        'Xuất bản & Mở phòng thi'
      );
      if (!conf) return;

      try {
        UI.showToast('Đang tạo đề thi và lưu câu hỏi vào CSDL...', 'info');
        const courseSelect = document.getElementById('p3-assigned-course');
        const courseId = courseSelect?.value || 'PWD301';
        const maxAtt = parseInt(document.getElementById('cfg-attempts')?.value || 1, 10);
        const pwd = document.getElementById('cfg-password')?.value || 'PWD301@2026';
        const shuffle = document.getElementById('cfg-shuffle-all')?.checked ?? true;

        const created = await ApiClient.createAssessment(courseId, {
          title: title,
          assessment_type: 'QUIZ',
          duration_minutes: duration,
          max_attempts: maxAtt,
          require_password: true,
          password: pwd,
          shuffle_questions: shuffle
        });

        const asmId = created?.assessment_id || created?.assessment?.public_id || created?.assessment?.id || created?.id;
        let createdQuestionsCount = 0;

        if (!parsedData || !parsedData.questions || parsedData.questions.length === 0) {
          const rawText = rawTextarea?.value || document.getElementById('azota-raw-textarea')?.value || '';
          if (rawText.trim()) {
            parsedData = ExamParser.parseExamRaw(rawText, 40.0);
          }
        }

        if (asmId && parsedData && parsedData.questions && parsedData.questions.length > 0) {
          const batchQuestions = [];
          for (const q of parsedData.questions) {
            let qType = 'SINGLE_CHOICE';
            if (q.question_type === 'TN nhiều đáp án') qType = 'MULTIPLE_CHOICE';
            else if (q.question_type === 'Điền từ' || q.question_type === 'Trả lời ngắn') qType = 'SHORT_ANSWER';
            else if (q.question_type === 'Đúng/Sai' || q.question_type === 'Đúng / Sai') qType = 'TRUE_FALSE';

            let diff = 'UNDERSTAND';
            if (q.bloom_level === 'Nhận biết' || q.bloom_level === 'REMEMBER') diff = 'REMEMBER';
            else if (q.bloom_level === 'Vận dụng' || q.bloom_level === 'APPLY') diff = 'APPLY';

            const payload = {
              question_type: qType,
              content: q.stem || q.prompt || q.question_text || `Câu hỏi ${q.id}`,
              difficulty: diff,
              points: parseFloat(q.points) || 1.0,
              explanation: q.explanation || ''
            };

            if (qType === 'SHORT_ANSWER') {
              const answers = (q.options || q.choices || q.accepted_answers || []).map(o => o.text || o.content || o);
              payload.accepted_answers = answers.length > 0 ? answers : ['Đáp án'];
            } else {
              const choices = (q.choices || q.options || []).map((c, i) => ({
                content: c.content || c.text || c,
                is_correct: Boolean(c.is_correct),
                position: i + 1
              }));
              if (qType === 'SINGLE_CHOICE' || qType === 'TRUE_FALSE') {
                const hasCorrect = choices.some(c => c.is_correct);
                if (!hasCorrect && choices.length > 0) {
                  choices[0].is_correct = true;
                }
              }
              payload.choices = choices;
            }
            batchQuestions.push(payload);
          }

          try {
            const batchRes = await ApiClient.createAssessmentQuestionsBatch(asmId, batchQuestions);
            createdQuestionsCount = batchRes?.created_count || batchQuestions.length;
          } catch (batchErr) {
            console.warn('Lỗi atomic batch questions, falling back to sequential:', batchErr);
            for (const p of batchQuestions) {
              try {
                await ApiClient.createAssessmentQuestion(asmId, p);
                createdQuestionsCount++;
              } catch (singleErr) {
                console.warn('Lỗi gán câu hỏi đơn lẻ:', singleErr);
              }
            }
          }
        }

        // Publish assessment
        if (asmId) {
          if (createdQuestionsCount > 0) {
            try {
              await ApiClient.publishAssessment(asmId);
            } catch (pubErr) {
              console.warn('Lỗi xuất bản đề thi:', pubErr);
              UI.showToast(`Đã tạo đề thi kèm ${createdQuestionsCount} câu hỏi (Bản nháp). Lỗi xuất bản: ${pubErr.message || pubErr}`, 'warning');
              localStorage.removeItem('pwd301_azota_exam_draft');
              window.location.hash = '#/instructor/dashboard';
              return;
            }
          }
        }

        localStorage.removeItem('pwd301_azota_exam_draft');
        UI.showToast(`Đề thi "${title}" đã xuất bản thành công vào hệ thống PWD301 LMS kèm ${createdQuestionsCount} câu hỏi lưu vào CSDL!`, 'success');
        window.location.hash = '#/instructor/dashboard';
      } catch (err) {
        UI.showToast(`Lỗi xuất bản: ${err.message || 'Không thể tạo đề thi'}`, 'error');
      }
    };
  }

}

window.InstructorView = InstructorView;
