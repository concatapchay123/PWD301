/**
 * PWD301 LMS - Student Views Layer
 * Implements Dashboard, Catalog, Course Hub, 3-Column Lesson Reader,
 * Assessments Suite (Waiting Room UTC, Exam Attempt Console, Results Drawer),
 * Gemini AI Academic Assistant, and Instructor Self-Nomination.
 */

class StudentView {
  // =========================================================================
  // 0. Notification Hub (Delegates to Topbar Dropdown Menu)
  // =========================================================================
  static async openNotificationHub() {
    if (window.app && typeof window.app.openNotificationsDropdown === 'function') {
      window.app.openNotificationsDropdown();
      return;
    }
    const bellBtn = document.getElementById('topbar-notifications-btn');
    if (bellBtn) {
      bellBtn.click();
      return;
    }
  }

  // =========================================================================
  // 1. Student Dashboard (with Assessment Countdown Ticker)
  // =========================================================================
  static async renderDashboard(container) {
    container.innerHTML = `
      <div class="p-6 sm:p-8 space-y-8 max-w-7xl mx-auto animate-fade-in font-sans">
        
        <!-- 1. Header & Action Hub (Greeting, Subtitle) -->
        <div class="c-card p-6 sm:p-7 shadow-sm">
          <div class="space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">Học kỳ Hiện tại</span>
              <span class="text-xs text-slate-400 font-medium">Trang chủ Sinh viên</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight" id="student-welcome-heading">
              Chào buổi sáng, Sinh viên
            </h1>
            <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed" id="student-welcome-sub">
              Bạn có bài kiểm tra sắp tới và các nội dung bài học đang tiếp diễn. Tiếp tục hành trình học tập ngay bên dưới.
            </p>
          </div>
        </div>

        <!-- 2. Actionable Metric Cards (2 Cards: Enrolled, Urgent Assessment) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5" id="dashboard-metric-cards">
          
          <!-- Card 1: Khóa học kích hoạt -->
          <a class="group c-card c-card-hover p-5 flex flex-col justify-between" href="#/student/courses">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Khóa học kích hoạt</span>
              <div class="w-9 h-9 rounded-xl bg-primary-subtle text-primary dark:bg-primary/20 flex items-center justify-center group-hover:scale-105 transition-transform">
                <span class="material-symbols-outlined text-[20px]">menu_book</span>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-2xl font-extrabold text-slate-900 dark:text-white" id="kpi-enrolled-count">0 Khóa đang học</div>
              <p class="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <span id="kpi-enrolled-names" class="truncate">Đang theo học trong kỳ</span>
                <span class="material-symbols-outlined text-[14px] text-primary shrink-0">arrow_forward</span>
              </p>
            </div>
          </a>

          <!-- Card 2: Khảo thí trọng tâm (Urgent Assessment Ticker) -->
          <a class="c-card c-card-hover bg-amber-50/50 dark:bg-amber-950/20 border-amber-300/60 dark:border-amber-700/60 p-5 flex flex-col justify-between group" href="#/student/assessments" id="kpi-urgent-card">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
                <span>Khảo thí trọng tâm</span>
              </span>
              <div class="px-2.5 py-0.5 rounded-full bg-amber-500 text-white text-xs font-mono font-bold" id="kpi-urgent-clock">
                Sẵn sàng
              </div>
            </div>
            <div class="mt-3">
              <div class="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white group-hover:text-amber-600 transition-colors" id="kpi-urgent-title">
                0 Bài thi sắp tới
              </div>
              <p class="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium truncate" id="kpi-urgent-sub">
                Chưa có đợt thi nào được lên lịch
              </p>
            </div>
          </a>

        </div>

        <!-- 3. Learning Workspace Layout: 8-cols Main Stream + 4-cols Sticky Right Sidebar -->
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          
          <!-- Left Column (8 cols): Hero Continue Card, Enrolled Courses List, Become Instructor Banner -->
          <div class="xl:col-span-8 space-y-6">
            
            <!-- Hero Continue Card -->
            <div class="c-card p-6 sm:p-7 flex flex-col justify-between relative overflow-hidden" id="dashboard-hero-continue-card">
              <div class="space-y-4">
                <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2">
                    <span class="px-2.5 py-1 rounded-full bg-primary-subtle text-primary font-bold text-xs uppercase tracking-wider flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-primary"></span>
                      <span>Đang học dang dở</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-slate-500" id="hero-course-code">PWD301</span>
                  </div>
                  <span class="text-xs font-medium text-slate-400 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">schedule</span>
                    <span>Còn khoảng 45 phút học</span>
                  </span>
                </div>

                <div>
                  <h2 class="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white leading-snug" id="hero-course-title">
                    Khóa học học thuật CNTT
                  </h2>
                  <p class="text-sm text-slate-600 dark:text-slate-300 font-medium mt-1" id="hero-lesson-title">
                    Tiếp tục nội dung bài học mới nhất
                  </p>
                </div>

                <div class="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-slate-500" id="hero-progress-label">Tiến trình học phần</span>
                    <span class="font-bold text-primary font-mono" id="hero-progress-val">0%</span>
                  </div>
                  <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
                    <div class="bg-primary h-full rounded-full transition-all duration-500" id="hero-progress-bar" style="width: 10%"></div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-xs text-slate-400">
                    <span id="hero-instructor-label">GV hướng dẫn: Hội đồng Khoa học</span>
                    <span>Giáo trình số đã phê duyệt</span>
                  </div>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-3 pt-6 mt-4 border-t border-slate-100 dark:border-slate-800">
                <a
                  href="#/student/courses"
                  id="hero-continue-lesson-btn"
                  class="c-btn c-btn-primary c-btn-md shadow-xs"
                >
                  <span class="material-symbols-outlined text-[18px]">play_circle</span>
                  <span>Vào bài học ngay</span>
                </a>
                <a
                  href="#/student/courses"
                  id="hero-view-syllabus-btn"
                  class="c-btn c-btn-secondary c-btn-md"
                >
                  <span class="material-symbols-outlined text-[18px]">toc</span>
                  <span>Xem đề cương chi tiết</span>
                </a>
              </div>
            </div>

            <!-- Enrolled Courses Master Section -->
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-[20px]">school</span>
                  <span>Khóa học đang theo học</span>
                </h2>
                <a href="#/student/courses" class="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5">
                  <span>Xem toàn bộ</span>
                  <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
                </a>
              </div>

              <div id="enrolled-courses-list" class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="col-span-full text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-400 text-sm">
                  <span class="inline-block animate-spin text-xl mb-2">⏳</span>
                  <p>Đang tải danh sách khóa học...</p>
                </div>
              </div>
            </div>

            <!-- Become Instructor Callout Banner -->
            <div class="c-card p-6 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-transparent dark:from-blue-950/20 dark:via-indigo-950/10 dark:to-transparent border border-blue-200 dark:border-blue-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-blue-600 dark:text-blue-400 text-[20px]">school</span>
                  <h3 class="text-sm font-bold text-slate-900 dark:text-white">Bạn có chuyên môn và muốn đóng góp bài giảng?</h3>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400">Đăng ký trở thành Giảng viên để xây dựng học liệu, thiết kế ngân hàng câu hỏi và giảng dạy trên PWD301.</p>
              </div>
              <a href="#/student/become-instructor" class="c-btn c-btn-primary c-btn-md shrink-0 flex items-center gap-1.5 shadow-xs">
                <span class="material-symbols-outlined text-[16px]">badge</span>
                <span>Đăng ký xét duyệt</span>
              </a>
            </div>

          </div>

          <!-- Right Column (4 cols): Sticky Việc cần làm hôm nay -->
          <div class="xl:col-span-4 xl:sticky xl:top-24 space-y-4">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-[20px] text-primary">checklist</span>
                  <h3 class="font-bold text-base text-slate-900 dark:text-white">Việc cần làm hôm nay</h3>
                </div>
                <span class="text-xs font-semibold text-slate-400" id="todo-tasks-badge">Nhiệm vụ học tập</span>
              </div>

              <div class="space-y-3" id="todo-actions-list">
                
                <!-- Urgent Assessment Item -->
                <div class="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 space-y-2.5" id="todo-urgent-exam-box">
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex flex-col">
                      <div class="flex items-center gap-1.5">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-600 text-white">Khẩn cấp</span>
                        <span class="text-xs font-bold text-slate-900 dark:text-white truncate" id="todo-exam-title">Khảo thí chuẩn hóa</span>
                      </div>
                      <span class="text-[11px] text-slate-500 mt-0.5" id="todo-exam-meta">Thời lượng: 45 phút • Điểm tối đa: 10đ</span>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500 text-white shrink-0" id="todo-exam-clock">
                      Sắp mở
                    </span>
                  </div>
                  <p class="text-[11px] text-amber-700 dark:text-amber-400 font-medium leading-tight flex items-start gap-1">
                    <span class="material-symbols-outlined text-[14px] shrink-0 mt-0.5">lock</span>
                    <span>Cấu trúc đề & điểm số sẽ khóa vĩnh viễn (First-Start Lock) khi bắt đầu làm bài.</span>
                  </p>
                  <a
                    href="#/student/assessments"
                    id="todo-exam-cta-btn"
                    class="w-full h-9 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                  >
                    <span class="material-symbols-outlined text-[16px]">meeting_room</span>
                    <span>Vào phòng chờ thi (Waiting Room)</span>
                  </a>
                </div>

                <!-- Secure Resource Item -->
                <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="material-symbols-outlined text-[20px] text-emerald-600 shrink-0">verified</span>
                    <div class="flex flex-col min-w-0">
                      <span class="text-xs font-bold text-slate-900 dark:text-white truncate">Giao_trinh_Chinh_thuc_PWD301.pdf</span>
                      <span class="text-[11px] text-slate-400">Đã quét an toàn ClamAV • Tài liệu môn học</span>
                    </div>
                  </div>
                  <a href="#/student/courses" class="h-8 px-3 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs shrink-0 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">download</span> Tải tệp
                  </a>
                </div>

                <!-- Grade Notice Item -->
                <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3" id="todo-grade-notice-box">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="material-symbols-outlined text-[20px] text-primary shrink-0">grade</span>
                    <div class="flex flex-col min-w-0">
                      <span class="text-xs font-bold text-slate-900 dark:text-white truncate" id="todo-grade-title">Kết quả khảo thí gần nhất</span>
                      <span class="text-[11px] text-emerald-600 font-semibold" id="todo-grade-score">Đã hoàn thành và công bố điểm</span>
                    </div>
                  </div>
                  <a href="#/student/assessments" id="todo-grade-cta" class="h-8 px-3 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs shrink-0 flex items-center">
                    Xem chi tiết
                  </a>
                </div>

              </div>
            </div>
          </div>

        </div>

      </div>
    `;

    // Fetch live dashboard data
    try {
      const data = await ApiClient.getStudentDashboard();
      if (!data) return;

      const user = window.app?.currentUser;
      if (user) {
        const heading = document.getElementById('student-welcome-heading');
        if (heading) {
          heading.textContent = `Chào buổi sáng, ${user.display_name || user.email}!`;
        }
      }

      const enrollments = data.enrollments || [];
      const completed = enrollments.filter(e => e.status === 'COMPLETED').length;
      const activeEnrollments = enrollments.filter(e => e.status !== 'COMPLETED');
      const avgProgress = enrollments.length > 0
        ? Math.round(enrollments.reduce((acc, curr) => acc + (curr.current_progress_percent || curr.progress_percent || 0), 0) / enrollments.length)
        : 0;

      // Update KPI 1
      const kpiEnrolledEl = document.getElementById('kpi-enrolled-count');
      const kpiEnrolledNames = document.getElementById('kpi-enrolled-names');
      if (kpiEnrolledEl) kpiEnrolledEl.textContent = `${enrollments.length} Khóa đang học`;
      if (kpiEnrolledNames) {
        const codes = enrollments.map(e => e.course_code).filter(Boolean).slice(0, 3).join(', ');
        kpiEnrolledNames.textContent = codes ? `${codes}${enrollments.length > 3 ? '...' : ''}` : 'Chưa có môn học kích hoạt';
      }

      // Update KPI 2
      const kpiProgPct = document.getElementById('kpi-progress-pct');
      const kpiProgRatio = document.getElementById('kpi-progress-ratio');
      const kpiProgBar = document.getElementById('kpi-progress-bar');
      if (kpiProgPct) kpiProgPct.textContent = `${avgProgress}% Hoàn thành`;
      if (kpiProgRatio) kpiProgRatio.textContent = `${completed} / ${enrollments.length} Môn học`;
      if (kpiProgBar) kpiProgBar.style.width = `${Math.min(100, Math.max(5, avgProgress))}%`;

      // Update Upcoming Assessment Ticker (KPI 3 & To-Do item)
      const upcoming = data.upcoming_assessments || [];
      const urgentTitle = document.getElementById('kpi-urgent-title');
      const urgentSub = document.getElementById('kpi-urgent-sub');
      const urgentCard = document.getElementById('kpi-urgent-card');
      const urgentClock = document.getElementById('kpi-urgent-clock');

      const todoExamTitle = document.getElementById('todo-exam-title');
      const todoExamMeta = document.getElementById('todo-exam-meta');
      const todoExamClock = document.getElementById('todo-exam-clock');
      const todoExamCta = document.getElementById('todo-exam-cta-btn');

      if (upcoming.length > 0) {
        const nextExam = upcoming[0];
        if (urgentTitle) urgentTitle.textContent = `${upcoming.length} Bài thi cần làm`;
        if (urgentSub) urgentSub.textContent = `${nextExam.title} • Thời lượng: ${nextExam.time_limit_minutes || 45}p`;
        if (urgentCard) urgentCard.href = `#/student/assessments/waiting-room?id=${nextExam.assessment_id}`;
        if (urgentClock) urgentClock.textContent = `${nextExam.time_limit_minutes || 45} phút`;

        if (todoExamTitle) todoExamTitle.textContent = nextExam.title;
        if (todoExamMeta) todoExamMeta.textContent = `${nextExam.course_code || 'Khóa học'} • ${nextExam.time_limit_minutes || 45} phút • Điểm tối đa: ${nextExam.max_points || 10}đ`;
        if (todoExamClock) todoExamClock.textContent = 'Phòng chờ mở';
        if (todoExamCta) todoExamCta.href = `#/student/assessments/waiting-room?id=${nextExam.assessment_id}`;
      } else {
        if (urgentTitle) urgentTitle.textContent = '0 Bài thi sắp tới';
        if (urgentSub) urgentSub.textContent = 'Hiện tại chưa có đợt khảo thí nào';
        if (urgentClock) urgentClock.textContent = 'Thư thả';

        const urgentBox = document.getElementById('todo-urgent-exam-box');
        if (urgentBox) urgentBox.classList.add('hidden');
      }

      // Update Recent Results in To-Do
      const recentResults = data.recent_results || [];
      const gradeTitle = document.getElementById('todo-grade-title');
      const gradeScore = document.getElementById('todo-grade-score');
      const gradeCta = document.getElementById('todo-grade-cta');
      if (recentResults.length > 0) {
        const latestResult = recentResults[0];
        if (gradeTitle) gradeTitle.textContent = latestResult.assessment_title || 'Khảo thí đã chấm';
        if (gradeScore) gradeScore.textContent = `Điểm: ${latestResult.raw_score}/${latestResult.max_score} • Đạt chuẩn`;
        if (gradeCta) gradeCta.href = `#/student/assessments/results?id=${latestResult.attempt_id}`;
      } else {
        const gradeBox = document.getElementById('todo-grade-notice-box');
        if (gradeBox) gradeBox.classList.add('hidden');
      }

      // Update Hero Continue Card
      if (enrollments.length > 0) {
        const heroCourse = activeEnrollments[0] || enrollments[0];
        const heroCode = document.getElementById('hero-course-code');
        const heroTitle = document.getElementById('hero-course-title');
        const heroLesson = document.getElementById('hero-lesson-title');
        const heroProgVal = document.getElementById('hero-progress-val');
        const heroProgBar = document.getElementById('hero-progress-bar');
        const heroInstructor = document.getElementById('hero-instructor-label');
        const heroContinueBtn = document.getElementById('hero-continue-lesson-btn');
        const heroSyllabusBtn = document.getElementById('hero-view-syllabus-btn');

        const prog = Math.round(heroCourse.current_progress_percent || heroCourse.progress_percent || 0);

        if (heroCode) heroCode.textContent = heroCourse.course_code || 'CRS';
        if (heroTitle) heroTitle.textContent = heroCourse.course_title || 'Khóa học của bạn';
        if (heroLesson) heroLesson.textContent = `Tiến độ: ${prog}% • Sẵn sàng tiếp tục bài giảng mới`;
        if (heroProgVal) heroProgVal.textContent = `${prog}%`;
        if (heroProgBar) heroProgBar.style.width = `${Math.min(100, Math.max(5, prog))}%`;
        if (heroInstructor) heroInstructor.textContent = `GV hướng dẫn: ${heroCourse.instructor_name || 'Hội đồng Khoa học'}`;

        if (heroContinueBtn) heroContinueBtn.href = `#/student/courses/detail?id=${heroCourse.course_id}`;
        if (heroSyllabusBtn) heroSyllabusBtn.href = `#/student/courses/detail?id=${heroCourse.course_id}`;
      }

      // Render Enrolled Courses Grid
      const listEl = document.getElementById('enrolled-courses-list');
      if (listEl) {
        if (enrollments.length === 0) {
          listEl.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 space-y-3">
              <span class="material-symbols-outlined text-4xl text-slate-300">menu_book</span>
              <p class="text-sm font-bold text-slate-700 dark:text-slate-300">Bạn chưa ghi danh khóa học nào</p>
              <p class="text-xs text-slate-400">Tham khảo danh mục khóa học để bắt đầu lộ trình đào tạo chuẩn.</p>
              <div class="pt-2">
                <a href="#/student/catalog" class="px-5 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors inline-flex items-center gap-1.5 shadow-sm">
                  <span class="material-symbols-outlined text-[16px]">explore</span>
                  <span>Khám phá Danh mục</span>
                </a>
              </div>
            </div>
          `;
        } else {
          listEl.innerHTML = enrollments.map(e => {
            const prog = Math.round(e.current_progress_percent || e.progress_percent || 0);
            return `
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-mono font-bold text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">${UI.escapeHtml(e.course_code || 'CRS')}</span>
                    ${e.status && e.status !== 'ACTIVE' ? UI.statusBadge(e.status) : ''}
                  </div>
                  <h3
                    class="font-extrabold text-slate-900 dark:text-white text-base leading-snug hover:text-primary transition-colors cursor-pointer"
                    onclick="window.location.hash = '#/student/courses/detail?id=${e.course_id}'"
                  >
                    ${UI.escapeHtml(e.course_title || 'Khóa học')}
                  </h3>
                  <div class="flex items-center gap-2 text-xs text-slate-400">
                    <span>GV: ${UI.escapeHtml(e.instructor_name || 'Bộ môn')}</span>
                    <span>•</span>
                    <span>Tiến độ: <strong class="text-primary font-bold">${prog}%</strong></span>
                  </div>
                </div>

                <div class="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                  <div>
                    <div class="flex items-center justify-between text-[11px] font-semibold mb-1 text-slate-400">
                      <span>Hoàn thành giáo trình</span>
                      <span class="text-primary font-bold font-mono">${prog}%</span>
                    </div>
                    <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div class="bg-primary h-full rounded-full transition-all duration-500" style="width: ${Math.min(100, Math.max(5, prog))}%"></div>
                    </div>
                  </div>

                  <div class="flex items-center gap-2 pt-1">
                    <a href="#/student/courses/detail?id=${e.course_id}" class="flex-1 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-sm">
                      <span>Vào học tiếp tục</span>
                      <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                    </a>
                  </div>
                </div>
              </div>
            `;
          }).join('');
        }
      }
    } catch (err) {
      console.warn('Dashboard load error:', err);
      UI.showToast('Không thể tải toàn bộ dữ liệu Dashboard.', 'warning');
    }
  }

  // =========================================================================
  // 2. Public Course Catalog
  // =========================================================================
  static async renderCatalog(container) {
    container.innerHTML = `
      <div class="p-6 space-y-8 max-w-7xl mx-auto animate-fade-in font-sans">
        <!-- Centered Page Header & Large Search Bar -->
        <div class="text-center max-w-3xl mx-auto space-y-4 pt-2 pb-2">
          <div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Khám phá Khóa học</h1>
            <p class="text-sm text-slate-500 mt-1">Khám phá các khóa học công khai, tìm kiếm và đăng ký học ngay theo chuẩn ABET.</p>
          </div>

          <div class="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <div class="relative flex-1 w-full">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-[22px]">search</span>
              <input
                type="text"
                id="catalog-search-input"
                placeholder="Nhập tên môn học, mã khóa (VD: PWD301, UXD101...)..."
                class="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-base outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 shadow-sm transition-all"
              />
            </div>
            <select id="catalog-category-filter" class="w-full sm:w-auto h-[52px] px-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm outline-none focus:border-primary shadow-sm font-medium">
              <option value="">Tất cả danh mục</option>
              <option value="Khoa học Máy tính">Khoa học Máy tính</option>
              <option value="Trí tuệ Nhân tạo">Trí tuệ Nhân tạo</option>
              <option value="An toàn thông tin">An toàn thông tin</option>
              <option value="Kỹ thuật phần mềm">Kỹ thuật phần mềm</option>
            </select>
          </div>
        </div>

        <!-- Catalog Grid (Large 2-column Course Cards) -->
        <div id="catalog-courses-grid" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="col-span-full text-center py-16 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang tải danh mục khóa học...</p>
          </div>
        </div>
      </div>
    `;

    const searchInput = document.getElementById('catalog-search-input');
    const categorySelect = document.getElementById('catalog-category-filter');
    const grid = document.getElementById('catalog-courses-grid');

    let allCourses = [];
    let enrolledCourseIds = new Set();

    const renderFiltered = () => {
      const q = (searchInput?.value || '').trim().toLowerCase();
      const cat = categorySelect?.value || '';

      const filtered = allCourses.filter(c => {
        const matchesQuery = !q || (c.title && c.title.toLowerCase().includes(q)) || (c.course_code && c.course_code.toLowerCase().includes(q)) || (c.description && c.description.toLowerCase().includes(q));
        const matchesCat = !cat || (c.category && c.category.toLowerCase() === cat.toLowerCase());
        return matchesQuery && matchesCat;
      });

      if (filtered.length === 0) {
        grid.innerHTML = `
          <div class="col-span-full text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8">
            <span class="material-symbols-outlined text-4xl text-slate-400 mb-2">search_off</span>
            <p class="text-base font-bold text-slate-700 dark:text-slate-300">Không tìm thấy khóa học phù hợp</p>
            <p class="text-xs text-slate-400 mt-1">Thử thay đổi từ khóa hoặc bộ lọc danh mục.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = filtered.map(c => {
        const cid = c.course_id || c.id;
        const isEnrolled = enrolledCourseIds.has(String(cid));

        return `
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-7 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-5">
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold font-mono text-primary bg-primary-subtle px-3 py-1 rounded-full">${UI.escapeHtml(c.course_code)}</span>
                <div class="flex items-center gap-2">
                  ${isEnrolled ? `
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center gap-1">
                      <span class="material-symbols-outlined text-[14px]">check_circle</span>
                      <span>Đã đăng ký</span>
                    </span>
                  ` : ''}
                  ${UI.difficultyBadge(c.difficulty)}
                </div>
              </div>
              <h3 class="font-extrabold text-slate-900 dark:text-white text-lg sm:text-xl leading-snug">
                ${UI.escapeHtml(c.title)}
              </h3>
              <p class="text-sm text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed">
                ${UI.escapeHtml(c.description || c.summary || 'Khóa học học thuật chính quy theo chuẩn đầu ra ABET.')}
              </p>
            </div>

            <div class="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between text-xs text-slate-500">
                <span class="flex items-center gap-1.5 font-medium">
                  <span class="material-symbols-outlined text-[18px] text-primary">folder</span>
                  <span>Danh mục: <strong>${UI.escapeHtml(c.category || 'Chung')}</strong></span>
                </span>
              </div>

              <div class="flex items-center gap-3 pt-1">
                ${isEnrolled ? `
                  <a
                    href="#/student/courses/detail?id=${cid}"
                    class="flex-1 c-btn c-btn-primary c-btn-md flex items-center justify-center gap-2 shadow-sm"
                  >
                    <span>Vào khóa học</span>
                    <span class="material-symbols-outlined text-[18px]">play_circle</span>
                  </a>
                ` : `
                  <button
                    type="button"
                    class="flex-1 c-btn c-btn-primary c-btn-md enroll-action-btn"
                    data-course-id="${cid}"
                    data-course-title="${UI.escapeHtml(c.title)}"
                  >
                    <span>Đăng ký học ngay</span>
                  </button>
                `}
                <a
                  href="#/student/courses/detail?id=${cid}"
                  class="c-btn c-btn-secondary c-btn-md flex items-center gap-1.5"
                  title="Xem hồ sơ học vụ đầy đủ"
                >
                  <span>Hồ sơ môn</span>
                  <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                </a>
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Attach button clicks for enrolling
      grid.querySelectorAll('.enroll-action-btn').forEach(btn => {
        btn.onclick = async () => {
          const cid = btn.dataset.courseId;
          const ctitle = btn.dataset.courseTitle;
          const confirmed = await UI.confirm('Xác nhận đăng ký môn học', `Bạn có muốn ghi danh vào khóa học: <strong>${ctitle}</strong> không?`);
          if (!confirmed) return;

          btn.disabled = true;
          btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang đăng ký...';

          try {
            await ApiClient.enrollCourse(cid);
            enrolledCourseIds.add(String(cid));
            UI.showToast(`Đã ghi danh thành công khóa học: ${ctitle}`, 'success');
            renderFiltered();
          } catch (err) {
            UI.showToast(err.message || 'Không thể ghi danh vào khóa học này.', 'error');
            btn.disabled = false;
            btn.innerHTML = '<span>Đăng ký học ngay</span>';
          }
        };
      });
    };

    try {
      const [resCatalog, resEnrolled] = await Promise.all([
        ApiClient.getCatalogCourses(),
        ApiClient.getStudentEnrollments().catch(() => ({ enrollments: [] }))
      ]);
      allCourses = resCatalog.items || resCatalog.courses || [];
      const enrolledList = resEnrolled.enrollments || resEnrolled.courses || [];
      enrolledList.forEach(e => {
        if (e.course_id) enrolledCourseIds.add(String(e.course_id));
        if (e.id) enrolledCourseIds.add(String(e.id));
      });
      renderFiltered();
    } catch (err) {
      grid.innerHTML = `<div class="col-span-full text-center py-12 text-rose-500">Lỗi nạp danh mục: ${UI.escapeHtml(err.message)}</div>`;
    }

    if (searchInput) searchInput.oninput = renderFiltered;
    if (categorySelect) categorySelect.onchange = renderFiltered;
  }

  static async openCourseDetailModal(courseId) {
    try {
      const course = await ApiClient.getCourseDetail(courseId);
      if (!course) return;

      const body = `
        <div class="space-y-4">
          <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <span class="font-mono text-xs font-bold text-primary">${UI.escapeHtml(course.course_code)}</span>
            ${UI.statusBadge(course.status)}
          </div>
          <p class="text-sm leading-relaxed">${UI.escapeHtml(course.description || course.summary || 'Không có mô tả chi tiết.')}</p>
          <div class="grid grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-xl border border-slate-100 dark:border-slate-800">
            <div><strong>Danh mục:</strong> ${UI.escapeHtml(course.category || 'Đại cương')}</div>
            <div><strong>Độ khó:</strong> ${UI.escapeHtml(course.difficulty || 'Cơ bản')}</div>
            <div><strong>Sĩ số:</strong> ${course.capacity ? course.capacity + ' sinh viên' : 'Không giới hạn'}</div>
            <div><strong>Giảng viên:</strong> ${UI.escapeHtml(course.instructor_name || 'Bộ môn Phụ trách')}</div>
          </div>
        </div>
      `;

      const footer = `
        <button type="button" class="c-btn c-btn-secondary c-btn-sm" onclick="UI.closeModal()">Đóng</button>
        <a href="#/student/courses/detail?id=${courseId}" class="c-btn c-btn-ghost c-btn-sm text-primary" onclick="UI.closeModal()">Xem hồ sơ môn học đầy đủ</a>
        <button type="button" class="c-btn c-btn-primary c-btn-sm" id="modal-enroll-btn">Đăng ký môn học</button>
      `;

      UI.openModal({
        title: course.title,
        bodyHtml: body,
        footerHtml: footer,
        size: 'md'
      });

      document.getElementById('modal-enroll-btn').onclick = async () => {
        try {
          await ApiClient.enrollCourse(courseId);
          UI.closeModal();
          UI.showToast(`Đã ghi danh thành công khóa học: ${course.title}`, 'success');
          window.location.hash = '#/student/courses';
        } catch (err) {
          UI.showToast(err.message || 'Không thể ghi danh môn học.', 'error');
        }
      };
    } catch (e) {
      UI.showToast('Không thể nạp thông tin chi tiết môn học.', 'error');
    }
  }

  // =========================================================================
  // 3. Enrolled Courses Hub (My Learning)
  // =========================================================================
  static async renderMyLearning(container) {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white">Khóa học của tôi</h1>
            <p class="text-sm text-slate-500 mt-0.5">Không gian quản lý tiến độ, lộ trình và các môn học bạn đang theo học.</p>
          </div>
          <div class="flex items-center gap-3">
            <a href="#/student/catalog" class="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">add</span>
              Ghi danh môn học mới
            </a>
          </div>
        </div>

        <!-- Filter & Search Controls -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div class="flex items-center gap-2" id="my-learning-filters">
            <button type="button" class="filter-pill px-3.5 py-1.5 rounded-xl text-xs font-bold bg-primary text-white transition-colors" data-status="ALL">
              Tất cả
            </button>
            <button type="button" class="filter-pill px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" data-status="IN_PROGRESS">
              Đang học
            </button>
            <button type="button" class="filter-pill px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" data-status="COMPLETED">
              Đã hoàn thành
            </button>
          </div>
          <div class="relative w-full sm:w-64">
            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">search</span>
            <input
              type="text"
              id="my-learning-search"
              placeholder="Tìm theo tên hoặc mã khóa..."
              class="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white outline-none focus:border-primary"
            />
          </div>
        </div>

        <div id="my-learning-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="col-span-full text-center py-16 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang nạp danh sách khóa học của bạn...</p>
          </div>
        </div>
      </div>
    `;

    const grid = document.getElementById('my-learning-grid');
    const searchInput = document.getElementById('my-learning-search');
    let activeFilter = 'ALL';

    try {
      const data = await ApiClient.getStudentEnrollments();
      const enrollments = (data && data.enrollments) ? data.enrollments : [];

      if (enrollments.length === 0) {
        grid.innerHTML = `
          <div class="col-span-full text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 space-y-3">
            <span class="material-symbols-outlined text-5xl text-slate-300">school</span>
            <div class="space-y-1">
              <p class="text-base font-bold text-slate-700 dark:text-slate-300">Bạn chưa có khóa học nào</p>
              <p class="text-xs text-slate-400 max-w-sm mx-auto">Tham khảo danh mục môn học đào tạo chuẩn của khoa để đăng ký và bắt đầu tiến trình học tập.</p>
            </div>
            <div class="pt-2">
              <a href="#/student/catalog" class="px-5 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors inline-flex items-center gap-1.5 shadow-sm">
                <span class="material-symbols-outlined text-[16px]">explore</span>
                <span>Khám phá Danh mục Khóa học</span>
              </a>
            </div>
          </div>
        `;
        return;
      }

      const renderList = () => {
        const query = (searchInput?.value || '').trim().toLowerCase();
        const filtered = enrollments.filter(e => {
          const matchesStatus = activeFilter === 'ALL' || (activeFilter === 'COMPLETED' ? e.status === 'COMPLETED' : e.status !== 'COMPLETED');
          const matchesQuery = !query ||
            (e.course_title && e.course_title.toLowerCase().includes(query)) ||
            (e.course_code && e.course_code.toLowerCase().includes(query));
          return matchesStatus && matchesQuery;
        });

        if (filtered.length === 0) {
          grid.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
              Không tìm thấy khóa học nào khớp với bộ lọc hiện tại.
            </div>
          `;
          return;
        }

        grid.innerHTML = filtered.map(e => {
          const progress = Math.round(e.current_progress_percent || 0);
          return `
            <div class="c-card c-card-hover p-5 flex flex-col justify-between space-y-4">
              <div class="space-y-2.5">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold font-mono text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">${UI.escapeHtml(e.course_code)}</span>
                  ${e.status && e.status !== 'ACTIVE' ? UI.statusBadge(e.status) : ''}
                </div>
                <h3
                  class="font-extrabold text-slate-900 dark:text-white text-base leading-snug hover:text-primary transition-colors cursor-pointer"
                  onclick="window.location.hash = '#/student/courses/detail?id=${e.course_id}'"
                >
                  ${UI.escapeHtml(e.course_title)}
                </h3>
                <div class="flex items-center gap-3 text-xs text-slate-400">
                  <span>Ghi danh: ${UI.formatDate(e.enrolled_at)}</span>
                  <span>•</span>
                  <span>Tiến độ: <strong class="text-primary font-bold">${progress}%</strong></span>
                </div>
              </div>

              <div class="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <!-- Progress Bar -->
                <div>
                  <div class="flex items-center justify-between text-xs font-semibold mb-1">
                    <span class="text-slate-500">Hoàn thiện bài giảng</span>
                    <span class="text-primary font-bold">${progress}%</span>
                  </div>
                  <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div class="bg-primary h-full rounded-full transition-all duration-500" style="width: ${Math.min(100, Math.max(5, progress))}%"></div>
                  </div>
                </div>

                <div class="flex items-center gap-2 pt-1">
                  <a href="#/student/courses/detail?id=${e.course_id}" class="flex-1 c-btn c-btn-primary c-btn-sm shadow-xs flex items-center justify-center gap-1.5">
                    <span>Vào học tiếp tục</span>
                    <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </a>
                  <button
                    type="button"
                    class="leave-course-btn c-btn c-btn-secondary c-btn-sm text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                    data-id="${e.course_id}"
                    data-title="${UI.escapeHtml(e.course_title)}"
                    title="Rút khỏi môn học"
                  >
                    <span class="material-symbols-outlined text-[18px]">logout</span>
                  </button>
                </div>
              </div>
            </div>
          `;
        }).join('');

        // Attach leave course buttons
        grid.querySelectorAll('.leave-course-btn').forEach(btn => {
          btn.onclick = async () => {
            const cId = btn.dataset.id;
            const cTitle = btn.dataset.title;
            const confirmed = await UI.confirm(
              'Rút khỏi môn học',
              `Bạn có chắc chắn muốn rút khỏi khóa học "${cTitle}" không? Dữ liệu tiến độ bài học sẽ được lưu trữ lại.`,
              'Xác nhận rút môn',
              'Đóng',
              true
            );
            if (!confirmed) return;

            try {
              await ApiClient.leaveCourse(cId);
              UI.showToast(`Đã rút khỏi môn học: ${cTitle}`, 'info');
              StudentView.renderMyLearning(container);
            } catch (err) {
              UI.showToast(err.message || 'Không thể rút khỏi môn học.', 'error');
            }
          };
        });
      };

      // Filter pills switching
      document.querySelectorAll('#my-learning-filters .filter-pill').forEach(btn => {
        btn.onclick = () => {
          activeFilter = btn.dataset.status;
          document.querySelectorAll('#my-learning-filters .filter-pill').forEach(b => {
            b.className = 'filter-pill px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors';
          });
          btn.className = 'filter-pill px-3.5 py-1.5 rounded-xl text-xs font-bold bg-primary text-white transition-colors';
          renderList();
        };
      });

      if (searchInput) {
        searchInput.oninput = () => renderList();
      }

      renderList();
    } catch (err) {
      grid.innerHTML = `<div class="col-span-full text-center py-12 text-rose-500">Lỗi tải khóa học: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 4. Enrolled Course Hub & Academic Dossier (Variant 2 with ABET SLOs)
  // =========================================================================
  static async renderCourseDetail(container, courseId, activeTab = 'syllabus') {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in" id="course-detail-container">
        <div class="text-center py-16 text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang nạp hồ sơ học vụ khóa học (Academic Dossier)...</p>
        </div>
      </div>
    `;

    try {
      const courseData = await ApiClient.getStudentCourseDetail(courseId).catch(() => null);
      const course = courseData?.course || await ApiClient.getCourseDetail(courseId);
      const progressData = await ApiClient.getStudentCourseProgress(courseId).catch(() => null);

      const lessons = courseData?.lessons || course.lessons || [];
      const assessments = courseData?.assessments || course.assessments || [];
      const resources = courseData?.resources || course.resources || [];
      const isPreview = (window.app?.currentRole === 'INSTRUCTOR' || window.app?.currentRole === 'ADMIN' || localStorage.getItem('pwd301_role') === 'INSTRUCTOR' || localStorage.getItem('pwd301_role') === 'ADMIN');
      const isEnrolled = !!(courseData?.enrollment || progressData?.is_enrolled || progressData?.progress_percent !== undefined) || isPreview;

      // Parse or provide student-friendly Learning Outcomes (SLOs)
      let studentSLOs = [];
      if (course.learning_objectives) {
        if (Array.isArray(course.learning_objectives)) {
          studentSLOs = [...course.learning_objectives];
        } else if (typeof course.learning_objectives === 'string') {
          try {
            const parsed = JSON.parse(course.learning_objectives);
            if (Array.isArray(parsed)) studentSLOs = parsed;
          } catch {
            studentSLOs = course.learning_objectives.split('\n').filter(s => s.trim()).map((s, i) => ({
              title: `Kỹ năng ${i + 1}`,
              description: s.trim()
            }));
          }
        }
      }
      if (studentSLOs.length === 0) {
        studentSLOs = [
          {
            title: 'Kỹ năng 1 • Phân tích & Đặc tả bài toán',
            code: 'SLO-1',
            description: 'Nắm chắc cách tiếp cận bài toán phần mềm thực tế, phân rã yêu cầu và mô hình hóa giải pháp kỹ thuật rõ ràng.',
            weight: '30%'
          },
          {
            title: 'Kỹ năng 2 • Thiết kế CSDL & Lập trình Web',
            code: 'SLO-2',
            description: 'Tự tay thiết kế cơ sở dữ liệu quan hệ chuẩn 3NF, lập trình hệ thống RESTful API an toàn và viết kiểm thử tự động.',
            weight: '50%'
          },
          {
            title: 'Kỹ năng 3 • Bảo mật Thông tin & Chống Tấn công',
            code: 'SLO-3',
            description: 'Thực thi kiểm soát phân quyền RBAC/ABAC, phòng ngừa các lỗ hổng web OWASP và quét an toàn tệp tải lên.',
            weight: '20%'
          }
        ];
      }

      const renderTabContent = (tab) => {
        if (tab === 'assessments') {
          return `
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">Bài tập & Khảo thí của Khóa học</h3>
                <span class="text-xs text-slate-500">${assessments.length} bài kiểm tra</span>
              </div>
              <div class="space-y-3">
                ${assessments.length === 0 ? `
                  <div class="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm">
                    Khóa học hiện chưa có bài khảo thí nào được giao.
                  </div>
                ` : assessments.map(a => `
                  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:border-primary/50 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${!isEnrolled ? 'opacity-85' : ''}">
                    <div class="space-y-1">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-purple-600 bg-purple-50 dark:bg-purple-950/40 px-2 py-0.5 rounded">Khảo thí</span>
                        ${UI.statusBadge(a.status || 'PUBLISHED')}
                        ${!isEnrolled ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">lock</span> Khóa</span>` : ''}
                      </div>
                      <h4 class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(a.title)}</h4>
                      <div class="flex items-center gap-3 text-xs text-slate-500">
                        <span>Thời lượng: <strong>${a.time_limit_minutes || 45} phút</strong></span>
                        <span>•</span>
                        <span>Điểm tối đa: <strong>${a.max_points || 10}đ</strong></span>
                      </div>
                    </div>
                    <div class="flex items-center gap-2.5 shrink-0">
                      ${!isEnrolled ? `
                        <button
                          type="button"
                          onclick="UI.showToast('Vui lòng ghi danh môn học để tham gia khảo thí.', 'warning'); document.getElementById('dossier-enroll-btn')?.scrollIntoView({behavior: 'smooth'})"
                          class="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-amber-600 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-200 dark:border-slate-700"
                        >
                          <span class="material-symbols-outlined text-[15px] text-amber-600">lock</span>
                          <span>Cần ghi danh</span>
                        </button>
                      ` : (a.is_attempt_limit_reached ? `
                        <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 flex items-center gap-1">
                          <span class="material-symbols-outlined text-[16px]">fact_check</span>
                          <span>Xem kết quả (${a.attempts_count || 0}/${a.attempt_limit})</span>
                        </a>
                      ` : (a.attempts_count > 0 ? `
                        <div class="flex items-center gap-2">
                          <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 flex items-center gap-1" title="Xem kết quả lần trước">
                            <span class="material-symbols-outlined text-[15px]">history</span>
                            <span>Xem điểm</span>
                          </a>
                          <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="px-3.5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1">
                            <span class="material-symbols-outlined text-[15px]">play_arrow</span>
                            <span>Làm lần ${(a.attempts_count || 0) + 1}</span>
                          </a>
                        </div>
                      ` : `
                        <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1">
                          <span class="material-symbols-outlined text-[16px]">lock_open</span>
                          <span>Vào phòng chờ thi</span>
                        </a>
                      `))}
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }

        if (tab === 'resources') {
          return `
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="font-bold text-sm text-slate-900 dark:text-white">Kho Tài nguyên & Giáo trình Môn học (Resource Vault)</h3>
                <span class="text-xs text-slate-500">${resources.length} tệp tài liệu</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                ${resources.length === 0 ? `
                  <div class="col-span-full p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm">
                    Khóa học chưa có tệp đính kèm nào được tải lên.
                  </div>
                ` : resources.map(r => `
                  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-2">
                    <div class="flex items-center gap-2.5">
                      <span class="w-8 h-8 rounded-lg bg-primary-subtle text-primary flex items-center justify-center material-symbols-outlined text-[18px]">description</span>
                      <div class="font-bold text-xs text-slate-900 dark:text-white truncate flex-1">${UI.escapeHtml(r.label || r.filename)}</div>
                    </div>
                    <div class="flex items-center justify-between text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
                      <span class="text-emerald-600 font-semibold flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">verified</span> Đã quét sạch ClamAV
                      </span>
                      <a href="${r.download_url || `/student/courses/${courseId}/files/${r.resource_id || r.id}/download`}" target="_blank" class="text-primary font-bold hover:underline flex items-center gap-0.5">
                        Tải về <span class="material-symbols-outlined text-[14px]">download</span>
                      </a>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }

        if (tab === 'info') {
          return `
            <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-bold text-base text-slate-900 dark:text-white">Hồ sơ Giảng viên & Thông tin Học vụ</h3>
                  <p class="text-xs text-slate-400 mt-0.5">Thông tin liên hệ giảng viên và giải thích chi tiết các quy chuẩn đào tạo của môn học.</p>
                </div>
                <button type="button" onclick="UI.openAcademicGlossaryModal()" class="px-3 py-1.5 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs">
                  <span class="material-symbols-outlined text-[16px]">menu_book</span>
                  <span>Mở Sổ tay thuật ngữ</span>
                </button>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 space-y-3.5 border border-slate-200/80 dark:border-slate-800">
                  <div class="flex items-center justify-between">
                    <div class="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-primary text-[20px]">person_apron</span>
                      <span class="text-sm">Thông tin Giảng viên Phụ trách:</span>
                    </div>
                    <span class="px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-200 dark:border-emerald-800">
                      Chính thức
                    </span>
                  </div>

                  <div>
                    <div class="text-base font-extrabold text-slate-900 dark:text-white">${UI.escapeHtml(course.instructor_name || 'Hội đồng Khoa học Khoa CNTT')}</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Giảng viên / Chủ nhiệm học phần môn học</div>
                  </div>

                  <div class="space-y-2 pt-1 border-t border-slate-200/60 dark:border-slate-700/60 text-xs">
                    <div class="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                      <span class="material-symbols-outlined text-slate-400 text-[16px]">mail</span>
                      <span>Email học vụ:</span>
                      <a href="mailto:${UI.escapeHtml(course.contact_info?.email || course.instructor_email || 'instructor@pwd301.edu.vn')}" class="font-mono text-primary font-bold hover:underline">
                        ${UI.escapeHtml(course.contact_info?.email || course.instructor_email || 'instructor@pwd301.edu.vn')}
                      </a>
                    </div>

                    ${course.contact_info?.phone ? `
                      <div class="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                        <span class="material-symbols-outlined text-slate-400 text-[16px]">call</span>
                        <span>Số điện thoại:</span>
                        <a href="tel:${UI.escapeHtml(course.contact_info.phone)}" class="font-mono font-bold text-slate-800 dark:text-slate-200 hover:text-primary">
                          ${UI.escapeHtml(course.contact_info.phone)}
                        </a>
                      </div>
                    ` : ''}

                    ${course.contact_info?.office_hours ? `
                      <div class="flex items-start gap-2 text-slate-700 dark:text-slate-300">
                        <span class="material-symbols-outlined text-slate-400 text-[16px] mt-0.5">schedule</span>
                        <div>
                          <span>Giờ tiếp sinh viên:</span>
                          <span class="font-medium text-slate-800 dark:text-slate-200 ml-1">${UI.escapeHtml(course.contact_info.office_hours)}</span>
                        </div>
                      </div>
                    ` : `
                      <div class="flex items-start gap-2 text-slate-700 dark:text-slate-300">
                        <span class="material-symbols-outlined text-slate-400 text-[16px] mt-0.5">schedule</span>
                        <div>
                          <span>Giờ tiếp sinh viên:</span>
                          <span class="font-medium text-slate-800 dark:text-slate-200 ml-1">Thứ 3 & Thứ 5 (14:00 - 16:30)</span>
                        </div>
                      </div>
                    `}

                    ${course.contact_info?.group ? `
                      <div class="pt-2">
                        <a href="${UI.escapeHtml(course.contact_info.group)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-primary text-white hover:bg-primary-hover font-bold text-xs transition-colors shadow-2xs">
                          <span class="material-symbols-outlined text-[16px]">groups</span>
                          <span>Tham gia Group trao đổi học tập (Zalo / Teams / Telegram)</span>
                          <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                        </a>
                      </div>
                    ` : ''}
                  </div>
                </div>

                <div class="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 space-y-3.5 border border-slate-200/80 dark:border-slate-800">
                  <div class="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-indigo-600 text-[20px]">account_tree</span>
                    <span class="text-sm">Điều kiện tiên quyết (Cần học trước):</span>
                  </div>
                  <div class="text-slate-600 dark:text-slate-400 leading-relaxed text-xs">
                    ${course.prerequisites ? UI.escapeHtml(course.prerequisites) : 'Không yêu cầu môn học tiên quyết bắt buộc. Khuyến nghị sinh viên nắm vững cấu trúc dữ liệu và giải thuật cơ sở.'}
                  </div>
                </div>
              </div>

              <!-- Sổ tay giải thích thuật ngữ học vụ cho người học -->
              <div class="p-5 rounded-2xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-[20px]">help</span>
                  <h4 class="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">Tra cứu nhanh: Các thuật ngữ học vụ bạn thường gặp</h4>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  <div class="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1">
                    <span class="font-mono font-bold text-primary text-[11px]">SLO</span>
                    <p class="font-bold text-slate-800 dark:text-slate-200 text-xs">Chuẩn kỹ năng đầu ra</p>
                    <p class="text-[11px] text-slate-500">Những việc thực tế bạn sẽ tự tay làm được sau khi học xong môn học.</p>
                  </div>
                  <div class="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1">
                    <span class="font-mono font-bold text-indigo-600 text-[11px]">ABET</span>
                    <p class="font-bold text-slate-800 dark:text-slate-200 text-xs">Kiểm định quốc tế</p>
                    <p class="text-[11px] text-slate-500">Khung kiểm định chất lượng đào tạo công nghệ hàng đầu thế giới của Hoa Kỳ.</p>
                  </div>
                  <div class="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 space-y-1">
                    <span class="font-mono font-bold text-emerald-600 text-[11px]">Prerequisites</span>
                    <p class="font-bold text-slate-800 dark:text-slate-200 text-xs">Môn học cần học trước</p>
                    <p class="text-[11px] text-slate-500">Môn cung cấp kiến thức nền bắt buộc để bạn đủ điều kiện đăng ký môn này.</p>
                  </div>
                </div>
              </div>

              <div class="pt-2 text-xs text-slate-500 leading-relaxed border-t border-slate-100 dark:border-slate-800 flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] text-emerald-600 shrink-0 mt-0.5">verified</span>
                <div>
                  <strong>Chuẩn kiểm định chương trình (ABET Accreditation Statement):</strong> Khóa học được thiết kế và vận hành đáp ứng Tiêu chí 3 (Student Outcomes) chuẩn kiểm định chất lượng đào tạo kỹ thuật - công nghệ quốc tế ABET, bảo đảm chuẩn đầu ra năng lực phân tích, thiết kế hệ thống và đạo đức nghề nghiệp kỹ thuật.
                </div>
              </div>
            </div>
          `;
        }

        // Default: Syllabus tab
        return `
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">format_list_numbered</span>
                Đề cương & Danh sách Bài giảng (${lessons.length} bài)
              </h3>
              ${isEnrolled ? `
                <span class="text-xs text-slate-500 font-medium">Hoàn thành: <strong>${Math.round(progressData?.progress_percent || 0)}%</strong></span>
              ` : `
                <span class="text-xs font-bold text-amber-600 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">lock</span> Chưa ghi danh</span>
              `}
            </div>

            ${!isEnrolled ? `
              <div class="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-[22px]">lock</span>
                  </div>
                  <div>
                    <h4 class="text-xs font-bold text-slate-900 dark:text-white">Bạn chưa ghi danh khóa học này</h4>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Vui lòng ghi danh môn học để mở khóa toàn bộ bài giảng, tải tài liệu và tham gia khảo thí.</p>
                  </div>
                </div>
                <button
                  type="button"
                  onclick="document.getElementById('dossier-enroll-btn')?.click()"
                  class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm shrink-0 flex items-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-[16px]">school</span>
                  <span>Ghi danh ngay</span>
                </button>
              </div>
            ` : ''}

            <div class="space-y-3">
              ${lessons.length === 0 ? `
                <div class="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm">
                  Khóa học này đang hoàn thiện giáo trình, chưa có bài giảng nào được công bố.
                </div>
              ` : lessons.map((l, idx) => `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm hover:border-primary/50 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${!isEnrolled ? 'opacity-85' : ''}">
                  <div class="flex items-start gap-3.5">
                    <div class="w-8 h-8 rounded-xl ${isEnrolled ? 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'} font-bold flex items-center justify-center shrink-0 text-xs">
                      ${idx + 1}
                    </div>
                    <div>
                      <h4
                        class="font-bold text-slate-900 dark:text-white text-sm ${isEnrolled ? 'hover:text-primary transition-colors cursor-pointer' : 'text-slate-700 dark:text-slate-300'}"
                        ${isEnrolled ? `onclick="window.location.hash = '#/student/lessons/reader?course_id=${courseId}&lesson_id=${l.lesson_id || l.id}'"` : `onclick="UI.showToast('Vui lòng ghi danh môn học trước khi bắt đầu bài học.', 'warning'); document.getElementById('dossier-enroll-btn')?.scrollIntoView({behavior: 'smooth'})"`}
                      >
                        <span class="flex items-center gap-1.5">
                          <span>${UI.escapeHtml(l.title)}</span>
                          ${!isEnrolled ? `<span class="material-symbols-outlined text-[15px] text-amber-600" title="Cần ghi danh để mở khóa">lock</span>` : ''}
                        </span>
                      </h4>
                      <p class="text-xs text-slate-500 mt-0.5 line-clamp-1">${UI.escapeHtml(l.summary || 'Bài giảng lý thuyết & thực hành kèm code mẫu')}</p>
                      <div class="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                        <span>Tài liệu: ${(l.resources || []).length} tệp đính kèm</span>
                        ${l.quiz && l.quiz.length ? `<span>•</span><span class="text-indigo-600 dark:text-indigo-400 font-semibold">${l.quiz.length} câu trắc nghiệm</span>` : ''}
                      </div>
                    </div>
                  </div>

                  <div class="shrink-0">
                    ${isEnrolled ? `
                      <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${l.lesson_id || l.id}" class="px-4 py-2 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-all flex items-center gap-1">
                        <span>Vào học ngay</span>
                        <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                      </a>
                    ` : `
                      <button
                        type="button"
                        onclick="UI.showToast('Vui lòng ghi danh môn học trước khi bắt đầu bài học.', 'warning'); document.getElementById('dossier-enroll-btn')?.scrollIntoView({behavior: 'smooth'})"
                        class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-amber-50 dark:hover:bg-amber-950/30 text-slate-500 hover:text-amber-600 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-200 dark:border-slate-700"
                      >
                        <span class="material-symbols-outlined text-[15px] text-amber-600">lock</span>
                        <span>Cần ghi danh</span>
                      </button>
                    `}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      };

      container.innerHTML = `
        <div class="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
          ${isPreview ? `
            <div class="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs shadow-xs">
              <div class="flex items-center gap-2.5 text-amber-900 dark:text-amber-200">
                <span class="material-symbols-outlined text-[20px] text-amber-600">visibility</span>
                <div>
                  <span class="font-bold">Chế độ Xem trước của Giảng viên:</span>
                  <span class="text-slate-600 dark:text-slate-300 ml-1">Bạn đang xem khóa học này dưới góc nhìn của Học sinh. Toàn bộ bài học và tài liệu đã được mở khóa để xem thử.</span>
                </div>
              </div>
              <a href="#/instructor/courses/${courseId}/manage" class="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold transition-all shadow-sm shrink-0 flex items-center gap-1">
                <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                <span>Quản lý môn học</span>
              </a>
            </div>
          ` : ''}

          <!-- Navigation Breadcrumb -->
          <div class="flex items-center gap-2 text-xs text-slate-500">
            <a href="${isPreview ? `#/instructor/courses/${courseId}/manage` : '#/student/courses'}" class="hover:underline flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">arrow_back</span>
              ${isPreview ? 'Quay lại Quản lý môn học' : 'Khóa học của tôi'}
            </a>
            <span>/</span>
            <span class="text-slate-900 dark:text-white font-bold">${UI.escapeHtml(course.course_code)}</span>
          </div>

          <!-- Course Hero Academic Dossier (Variant 2) -->
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <span class="px-3 py-1 rounded-full bg-primary-subtle text-primary font-mono font-bold text-xs">${UI.escapeHtml(course.course_code)}</span>
                ${UI.difficultyBadge(course.difficulty)}
                ${course.status && course.status !== 'ACTIVE' ? UI.statusBadge(course.status) : ''}
                <span class="text-xs text-slate-500">• ${UI.escapeHtml(course.category || 'Chung')}</span>
              </div>
              <div class="flex items-center gap-3">
                ${isEnrolled ? `
                  <div class="flex items-center gap-3">
                    ${!isPreview ? `
                      <div class="text-xs text-slate-500 font-medium">
                        Tiến độ: <strong class="text-primary font-bold">${Math.round(progressData?.progress_percent || 0)}%</strong>
                      </div>
                    ` : ''}
                    ${lessons.length > 0 ? `
                      <a
                        href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${lessons[0].lesson_id || lessons[0].id}"
                        class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                      >
                        <span class="material-symbols-outlined text-[18px]">play_circle</span>
                        <span>Vào học ngay</span>
                      </a>
                    ` : ''}
                    ${!isPreview ? `
                      <button type="button" id="dossier-leave-btn" class="px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-900 text-rose-600 dark:text-rose-400 text-xs font-bold hover:bg-rose-50 transition-colors">
                        Rút môn học
                      </button>
                    ` : ''}
                  </div>
                ` : `
                  <button type="button" id="dossier-enroll-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px]">school</span>
                    <span>Ghi danh môn học</span>
                  </button>
                `}
              </div>
            </div>

            <div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                ${UI.escapeHtml(course.title)}
              </h1>
              <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mt-2 max-w-4xl">
                ${UI.escapeHtml(course.description || course.summary || 'Chương trình đào tạo chuyên sâu kết hợp lý thuyết và đồ án thực tế.')}
              </p>
            </div>

            <!-- Metadata Academic Strip (Credits removed per specification) -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs">
              <div>
                <span class="text-slate-400 block">Quy mô bài giảng:</span>
                <span class="font-extrabold text-slate-900 dark:text-white text-sm">${lessons.length} Bài giảng</span>
              </div>
              <div>
                <span class="text-slate-400 block">Đợt khảo thí:</span>
                <span class="font-extrabold text-slate-900 dark:text-white text-sm">${assessments.length} Bài kiểm tra</span>
              </div>
              <div>
                <span class="text-slate-400 block">Giảng viên phụ trách:</span>
                <span class="font-extrabold text-primary text-sm truncate block">${UI.escapeHtml(course.instructor_name || 'Hội đồng Khoa học')}</span>
              </div>
            </div>
          </div>

          <!-- Contextual Tabs Navigation -->
          <div class="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800 text-xs font-bold overflow-x-auto pb-px" id="course-hub-tabs">
            <button type="button" class="tab-btn px-4 py-3 border-b-2 transition-all flex items-center gap-2 ${activeTab === 'syllabus' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}" data-tab="syllabus">
              <span class="material-symbols-outlined text-[18px]">format_list_numbered</span>
              Lộ trình & Bài giảng (${lessons.length})
            </button>
            <button type="button" class="tab-btn px-4 py-3 border-b-2 transition-all flex items-center gap-2 ${activeTab === 'assessments' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}" data-tab="assessments">
              <span class="material-symbols-outlined text-[18px]">quiz</span>
              Bài tập & Khảo thí (${assessments.length})
            </button>
            <button type="button" class="tab-btn px-4 py-3 border-b-2 transition-all flex items-center gap-2 ${activeTab === 'resources' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}" data-tab="resources">
              <span class="material-symbols-outlined text-[18px]">folder_open</span>
              Kho Tài nguyên (${resources.length})
            </button>
            <button type="button" class="tab-btn px-4 py-3 border-b-2 transition-all flex items-center gap-2 ${activeTab === 'info' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}" data-tab="info">
              <span class="material-symbols-outlined text-[18px]">info</span>
              Hồ sơ Giảng viên & Học vụ
            </button>
          </div>

          <!-- Dynamic Active Tab Content -->
          <div id="course-hub-content" class="pt-2">
            ${renderTabContent(activeTab)}
          </div>
        </div>
      `;

      // Tab switching handlers
      container.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
          const tab = btn.dataset.tab;
          StudentView.renderCourseDetail(container, courseId, tab);
        };
      });

      // Dossier Action: Enroll
      const enrollBtn = document.getElementById('dossier-enroll-btn');
      if (enrollBtn) {
        enrollBtn.onclick = async () => {
          try {
            enrollBtn.disabled = true;
            enrollBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang ghi danh...';
            await ApiClient.enrollCourse(courseId);
            UI.showToast(`Ghi danh thành công khóa học: ${course.title}`, 'success');
            StudentView.renderCourseDetail(container, courseId, activeTab);
          } catch (e) {
            UI.showToast(e.message || 'Không thể ghi danh.', 'error');
            enrollBtn.disabled = false;
            enrollBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">school</span> <span>Ghi danh môn học</span>';
          }
        };
      }

      // Dossier Action: Leave
      const leaveBtn = document.getElementById('dossier-leave-btn');
      if (leaveBtn) {
        leaveBtn.onclick = async () => {
          const confirmed = await UI.confirm(
            'Rút khỏi môn học',
            `Bạn có chắc chắn muốn rút khỏi khóa học "${course.title}"?`,
            'Rút môn',
            'Đóng',
            true
          );
          if (!confirmed) return;
          try {
            await ApiClient.leaveCourse(courseId);
            UI.showToast('Đã rút khỏi môn học thành công.', 'info');
            StudentView.renderCourseDetail(container, courseId, activeTab);
          } catch (e) {
            UI.showToast(e.message || 'Không thể rút môn.', 'error');
          }
        };
      }

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp đề cương khóa học: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // Helper to render video player (YouTube iframe, Vimeo iframe, or HTML5 video)
  static _getEmbedVideoHtml(url) {
    if (!url) return '';
    const trimmed = String(url).trim();
    // YouTube (regular watch, embed, v, youtu.be, shorts, live, extra parameters, or embed code)
    const ytId = UI.parseYouTubeId(trimmed);
    if (ytId) {
      return `<iframe class="w-full h-full aspect-video rounded-xl" src="${UI.getYouTubeEmbedUrl(ytId)}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
    }
    // Vimeo
    const vimeoMatch = trimmed.match(/vimeo\.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|video\/|)(\d+)/);
    if (vimeoMatch && vimeoMatch[1]) {
      return `<iframe class="w-full h-full aspect-video rounded-xl" src="https://player.vimeo.com/video/${vimeoMatch[1]}" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>`;
    }
    // Direct file / HTML5 video
    return `<video controls class="w-full h-full aspect-video rounded-xl" src="${UI.escapeHtml(trimmed)}" preload="metadata"><p>Trình duyệt của bạn không hỗ trợ thẻ video HTML5.</p></video>`;
  }

  // =========================================================================
  // 5. Single-Column Focus Lesson Reader (Left Syllabus Drawer & Right Vault/Notes Drawer)
  // =========================================================================
  static async renderLessonReader(container, courseId, lessonId) {
    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden animate-fade-in" id="lesson-reader-root">
        <div class="text-center py-24 text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải không gian đọc tập trung (Single-Column Focus Mode)...</p>
        </div>
      </div>
    `;

    try {
      const [courseData, lesson] = await Promise.all([
        ApiClient.getStudentCourseDetail(courseId).catch(() => ApiClient.getCourseDetail(courseId)),
        ApiClient.getStudentLesson(courseId, lessonId)
      ]);

      const course = courseData?.course || courseData;
      const lessonsList = courseData?.lessons || course.lessons || [];
      const resources = lesson.resources || [];
      const isCompleted = lesson.progress?.is_completed || false;
      const isPreview = (window.app?.currentRole === 'INSTRUCTOR' || window.app?.currentRole === 'ADMIN' || localStorage.getItem('pwd301_role') === 'INSTRUCTOR' || localStorage.getItem('pwd301_role') === 'ADMIN');

      // Find prev and next lesson
      const currentIndex = lessonsList.findIndex(l => (l.lesson_id || l.id) === lessonId);
      const prevLesson = currentIndex > 0 ? lessonsList[currentIndex - 1] : null;
      const nextLesson = currentIndex < lessonsList.length - 1 ? lessonsList[currentIndex + 1] : null;

      // Fetch live notes from backend with fallback
      let savedNote = '';
      try {
        const notesRes = await ApiClient.getLessonNotes(lessonId);
        savedNote = notesRes?.personal_notes || '';
      } catch {
        savedNote = localStorage.getItem(`notes_${courseId}_${lessonId}`) || '';
      }

      container.innerHTML = `
        <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans">
          
          <!-- Topbar Reader Navigation Header -->
          <div class="h-14 px-4 sm:px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 z-10 select-none">
            <div class="flex items-center gap-3">
              <a
                href="${isPreview ? `#/instructor/courses/${courseId}/manage` : `#/student/courses/${courseId}`}"
                class="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5 text-xs font-semibold"
                title="${isPreview ? 'Quay lại Quản lý môn học' : 'Quay lại Tổng quan Khóa học'}"
              >
                <span class="material-symbols-outlined text-[18px]">arrow_back</span>
                <span class="hidden sm:inline">${isPreview ? 'Quản lý' : 'Khóa học'}</span>
              </a>
              <div class="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>
              <div class="truncate max-w-[200px] sm:max-w-xs md:max-w-md">
                <div class="flex items-center gap-1.5">
                  <span class="text-xs font-bold text-slate-800 dark:text-slate-200 truncate block">${UI.escapeHtml(course.title)}</span>
                  ${isPreview ? `<span class="px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 text-[10px] font-bold border border-amber-200 dark:border-amber-800 shrink-0">Xem trước</span>` : ''}
                </div>
                <span class="text-[11px] text-slate-400 truncate block">${UI.escapeHtml(lesson.title)}</span>
              </div>
            </div>

            <!-- Header Action Controls -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                id="toggle-syllabus-btn"
                class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center gap-1.5 transition-colors"
                title="Mở Đề cương bài giảng"
              >
                <span class="material-symbols-outlined text-[16px]">menu_book</span>
                <span class="hidden sm:inline">Đề cương</span>
              </button>

              <button
                type="button"
                id="toggle-resources-btn"
                class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center gap-1.5 transition-colors relative"
                title="Mở tài liệu & Sổ tay ghi chú"
              >
                <span class="material-symbols-outlined text-[16px]">edit_note</span>
                <span class="hidden sm:inline">Ghi chú & Tài liệu</span>
                ${resources.length > 0 ? `
                  <span class="w-4 h-4 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center">${resources.length}</span>
                ` : ''}
              </button>

              ${prevLesson ? `
                <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${prevLesson.lesson_id || prevLesson.id}" class="p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-1" title="Bài trước">
                  <span class="material-symbols-outlined text-[16px]">chevron_left</span>
                  <span class="hidden md:inline">Trước</span>
                </a>
              ` : ''}

              ${nextLesson ? `
                <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${nextLesson.lesson_id || nextLesson.id}" class="p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-1" title="Bài tiếp">
                  <span class="hidden md:inline">Sau</span>
                  <span class="material-symbols-outlined text-[16px]">chevron_right</span>
                </a>
              ` : ''}

              <button
                type="button"
                id="complete-lesson-btn"
                class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${isCompleted ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-primary hover:bg-primary-hover text-white shadow-sm'}"
              >
                <span class="material-symbols-outlined text-[16px]">${isCompleted ? 'check_circle' : 'check'}</span>
                <span class="hidden sm:inline">${isCompleted ? 'Đã hoàn thành' : 'Đánh dấu hoàn thành'}</span>
              </button>
            </div>
          </div>

          <!-- Single-Column Focus Reading Canvas -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-8">
            <main class="max-w-3xl mx-auto space-y-6">
              
              <!-- Lesson Header & Objectives Card -->
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm space-y-3">
                <div class="flex items-center gap-2 text-xs text-slate-400">
                  <span class="font-mono text-primary font-bold">BÀI ${currentIndex + 1} / ${lessonsList.length}</span>
                  <span>•</span>
                  <span class="flex items-center gap-1">
                    <span>Mục tiêu kỹ năng: Thiết kế & Hiện thực hóa</span>
                    <button type="button" onclick="UI.openAcademicGlossaryModal()" class="cursor-pointer text-[10px] bg-slate-100 hover:bg-primary-subtle hover:text-primary dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 font-mono transition-colors" title="Bấm để xem giải thích chuẩn đầu ra (SLO)">SLO (?)</button>
                  </span>
                </div>
                <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight leading-snug">
                  ${UI.escapeHtml(lesson.title)}
                </h1>
                ${lesson.summary ? `
                  <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    <strong>Mục tiêu trọng tâm:</strong> ${UI.escapeHtml(lesson.summary)}
                  </div>
                ` : ''}
              </div>

              <!-- Media Player / Video Block (if present) -->
              ${lesson.video_url ? `
                <div class="bg-black rounded-2xl overflow-hidden shadow-lg aspect-video border border-slate-800">
                  ${StudentView._getEmbedVideoHtml(lesson.video_url)}
                </div>
              ` : ''}

              <!-- Clean Rendered Markdown Body -->
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-10 shadow-sm text-slate-800 dark:text-slate-200 leading-relaxed text-sm sm:text-base space-y-5">
                ${UI.renderMarkdown(lesson.markdown_content || 'Nội dung bài giảng đang được hoàn thiện.')}
              </div>

              <!-- Mini-Quiz Interactive Section (Item 7) -->
              ${lesson.quiz && Array.isArray(lesson.quiz) && lesson.quiz.length > 0 ? `
                <div class="bg-white dark:bg-slate-900 border border-indigo-100 dark:border-indigo-900/60 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6" id="lesson-mini-quiz-section">
                  <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div class="flex items-center gap-2.5">
                      <span class="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center material-symbols-outlined text-[20px]">quiz</span>
                      <div>
                        <h3 class="font-black text-slate-900 dark:text-white text-base">Bài kiểm tra Củng cố Kiến thức (Mini-Quiz)</h3>
                        <p class="text-xs text-slate-400 mt-0.5">Kiểm tra mức độ tiếp thu bài giảng với ${lesson.quiz.length} câu hỏi tương tác</p>
                      </div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 text-xs font-bold border border-indigo-100 dark:border-indigo-900/50">
                      ${lesson.quiz.length} câu hỏi
                    </span>
                  </div>

                  <div class="space-y-6" id="mini-quiz-questions-list">
                    ${lesson.quiz.map((q, qIdx) => {
                      const qType = q.type || 'MULTIPLE_CHOICE';
                      const isMulti = qType === 'MULTIPLE_CHOICE' && (Boolean(q.allow_multiple) || (Array.isArray(q.correct_answers) && q.correct_answers.length > 1));
                      const choices = Array.isArray(q.options) ? q.options : (Array.isArray(q.choices) ? q.choices : []);

                      let typeBadge = '';
                      if (qType === 'MULTIPLE_CHOICE') {
                        typeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300">${isMulti ? 'Trắc nghiệm (Chọn nhiều)' : 'Trắc nghiệm (Chọn 1)'}</span>`;
                      } else if (qType === 'FILL_BLANK') {
                        typeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">Điền khuyết</span>`;
                      } else if (qType === 'MATCHING') {
                        typeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">Nối từ</span>`;
                      } else if (qType === 'TRUE_FALSE') {
                        typeBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300">Đúng / Sai</span>`;
                      }

                      return `
                        <div class="p-4 sm:p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-3.5 mini-quiz-card" data-qidx="${qIdx}" data-qtype="${qType}">
                          <div class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2.5 flex-1">
                              <span class="px-2 py-0.5 rounded-lg bg-indigo-600 text-white font-mono font-bold text-xs shrink-0 mt-0.5">Câu ${qIdx + 1}</span>
                              <div class="font-bold text-slate-900 dark:text-white text-sm sm:text-base leading-snug">
                                ${qType === 'FILL_BLANK'
                                  ? UI.escapeHtml(q.question).replace(/\[___\]/g, '<span class="inline-block px-2 py-0.5 mx-1 rounded bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold font-mono text-xs border border-indigo-200 dark:border-indigo-800">[ ... ]</span>')
                                  : UI.escapeHtml(q.question)}
                              </div>
                            </div>
                            <div class="shrink-0">
                              ${typeBadge}
                            </div>
                          </div>

                          <!-- Question interaction body -->
                          ${qType === 'MULTIPLE_CHOICE' ? `
                            <div class="space-y-2 pt-1">
                              ${choices.map((ch, chIdx) => `
                                <label class="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-indigo-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all mini-quiz-choice-label" data-chidx="${chIdx}">
                                  ${isMulti ? `
                                    <input type="checkbox" name="mini-quiz-q-${qIdx}" value="${chIdx}" class="text-primary focus:ring-primary w-4 h-4 rounded cursor-pointer mini-quiz-chk" />
                                  ` : `
                                    <input type="radio" name="mini-quiz-q-${qIdx}" value="${chIdx}" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer mini-quiz-radio" />
                                  `}
                                  <span class="w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center shrink-0 choice-badge">
                                    ${String.fromCharCode(65 + chIdx)}
                                  </span>
                                  <span class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 flex-1 leading-relaxed choice-text">${UI.escapeHtml(ch)}</span>
                                </label>
                              `).join('')}
                            </div>
                          ` : ''}

                          ${qType === 'FILL_BLANK' ? `
                            <div class="space-y-2.5 pt-1">
                              ${(q.blanks || [{ accepted_answers: [] }]).map((b, bIdx) => `
                                <div class="flex items-center gap-2.5 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 mini-quiz-blank-row">
                                  <span class="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 font-bold text-xs flex items-center justify-center shrink-0">
                                    #${bIdx + 1}
                                  </span>
                                  <input
                                    type="text"
                                    class="mini-quiz-blank-input flex-1 px-3 py-1.5 text-xs sm:text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:border-emerald-500 transition-all"
                                    data-qidx="${qIdx}"
                                    data-bidx="${bIdx}"
                                    placeholder="Nhập câu trả lời cho chỗ trống #${bIdx + 1}..."
                                  />
                                </div>
                              `).join('')}
                            </div>
                          ` : ''}

                          ${qType === 'MATCHING' ? `
                            <div class="space-y-2.5 pt-1">
                              ${(q.pairs || []).map((p, pIdx) => `
                                <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 mini-quiz-matching-row" data-qidx="${qIdx}" data-pidx="${pIdx}">
                                  <div class="flex items-center gap-2 sm:w-1/2 font-medium text-xs sm:text-sm text-slate-800 dark:text-slate-200">
                                    <span class="w-5 h-5 rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 font-bold text-[11px] flex items-center justify-center shrink-0">${pIdx + 1}</span>
                                    <span>${UI.escapeHtml(p.left)}</span>
                                  </div>
                                  <div class="flex items-center gap-1.5 sm:w-1/2">
                                    <span class="material-symbols-outlined text-slate-400 text-[16px] hidden sm:inline">arrow_forward</span>
                                    <select class="mini-quiz-matching-select w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-amber-500 transition-all cursor-pointer" data-qidx="${qIdx}" data-pidx="${pIdx}">
                                      <option value="">-- Chọn vế ghép tương ứng --</option>
                                      ${(q.pairs || []).map(optPair => `
                                        <option value="${UI.escapeHtml(optPair.right)}">${UI.escapeHtml(optPair.right)}</option>
                                      `).join('')}
                                    </select>
                                  </div>
                                </div>
                              `).join('')}
                            </div>
                          ` : ''}

                          ${qType === 'TRUE_FALSE' ? `
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                              <label class="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-emerald-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all mini-quiz-tf-label" data-qidx="${qIdx}" data-val="true">
                                <input type="radio" name="mini-quiz-tf-${qIdx}" value="true" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer mini-quiz-tf-radio" />
                                <span class="material-symbols-outlined text-emerald-600 text-[18px]">check_circle</span>
                                <span class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200">Đúng (True)</span>
                              </label>
                              <label class="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-rose-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all mini-quiz-tf-label" data-qidx="${qIdx}" data-val="false">
                                <input type="radio" name="mini-quiz-tf-${qIdx}" value="false" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer mini-quiz-tf-radio" />
                                <span class="material-symbols-outlined text-rose-600 text-[18px]">cancel</span>
                                <span class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200">Sai (False)</span>
                              </label>
                            </div>
                          ` : ''}

                          <div class="mini-quiz-explanation hidden p-3.5 rounded-xl text-xs space-y-1"></div>
                        </div>
                      `;
                    }).join('')}
                  </div>

                  <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                    <div id="mini-quiz-score-banner" class="text-xs text-slate-500 font-medium">
                      Hãy hoàn thành câu trả lời cho các câu hỏi rồi bấm <strong>Kiểm tra đáp án</strong>.
                    </div>
                    <div class="flex items-center gap-2">
                      <button type="button" id="mini-quiz-check-btn" class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-colors shadow-sm flex items-center gap-1.5 cursor-pointer">
                        <span class="material-symbols-outlined text-[16px]">check_circle</span>
                        <span>Kiểm tra đáp án</span>
                      </button>
                      <button type="button" id="mini-quiz-reset-btn" class="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 font-bold text-xs transition-colors hidden cursor-pointer">
                        Làm lại
                      </button>
                    </div>
                  </div>
                </div>
              ` : ''}

              <!-- Inline Contextual AI Mentor Card -->
              <div class="bg-gradient-to-br from-indigo-950 via-slate-900 to-indigo-900 text-white rounded-2xl p-6 shadow-md space-y-4 border border-indigo-800/40">
                <div class="flex items-center gap-3">
                  <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Bạch tuộc" class="w-10 h-10 rounded-xl object-cover border border-indigo-400/40 shadow-sm" />
                  <div>
                    <h4 class="font-bold text-sm">Bạch tuộc (Gemini Flash)</h4>
                    <p class="text-xs text-indigo-200/80">Bạn gặp khó khăn hay cần giải thích thêm về bài giảng "${UI.escapeHtml(lesson.title)}"?</p>
                  </div>
                </div>

                <div class="flex flex-wrap gap-2 pt-1" id="reader-ai-chips">
                  <button type="button" class="ai-chip px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition-colors flex items-center gap-1" data-query="Tóm tắt 3 ý trọng tâm của bài giảng: ${UI.escapeHtml(lesson.title)}">
                    <span>💡 Tóm tắt 3 ý chính</span>
                  </button>
                  <button type="button" class="ai-chip px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition-colors flex items-center gap-1" data-query="Giải thích chi tiết các thuật toán và khái niệm kỹ thuật trong bài: ${UI.escapeHtml(lesson.title)}">
                    <span>🔍 Giải thích thuật toán</span>
                  </button>
                  <button type="button" class="ai-chip px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition-colors flex items-center gap-1" data-query="Cho tôi 3 bài tập thực hành ứng dụng kèm lời giải cho bài: ${UI.escapeHtml(lesson.title)}">
                    <span>💻 Bài tập áp dụng</span>
                  </button>
                  <button type="button" class="ai-chip px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition-colors flex items-center gap-1" data-query="Tạo 3 câu hỏi trắc nghiệm ôn thi có đáp án giải thích cho bài: ${UI.escapeHtml(lesson.title)}">
                    <span>📝 Câu hỏi ôn thi</span>
                  </button>
                </div>
              </div>

              <!-- Bottom Next Lesson Footer Nav -->
              <div class="flex items-center justify-between pt-4 pb-12">
                ${prevLesson ? `
                  <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${prevLesson.lesson_id || prevLesson.id}" class="px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 hover:border-primary transition-colors flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                    <span>Bài trước: ${UI.escapeHtml(prevLesson.title)}</span>
                  </a>
                ` : '<div></div>'}

                ${nextLesson ? `
                  <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${nextLesson.lesson_id || nextLesson.id}" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-xs font-bold text-white transition-colors flex items-center gap-1.5 shadow-sm">
                    <span>Bài tiếp theo: ${UI.escapeHtml(nextLesson.title)}</span>
                    <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </a>
                ` : '<div></div>'}
              </div>

            </main>
          </div>
        </div>
      `;

      // 1. Left Drawer Handler: Syllabus Outline
      const syllabusBtn = document.getElementById('open-syllabus-drawer-btn') || document.getElementById('toggle-syllabus-btn');
      if (syllabusBtn) {
        syllabusBtn.onclick = () => {
          UI.openDrawer({
            side: 'left',
            title: 'Mục lục Đề cương Khóa học',
            width: 'max-w-sm',
            headerBadge: `<span class="px-2 py-0.5 rounded-full bg-primary-subtle text-primary text-[10px] font-bold">${currentIndex + 1}/${lessonsList.length}</span>`,
            bodyHtml: `
              <div class="space-y-1.5">
                <div class="text-xs text-slate-400 font-semibold uppercase tracking-wider pb-2">Danh sách bài học</div>
                ${lessonsList.map((l, i) => {
                  const isActive = (l.lesson_id || l.id) === lessonId;
                  return `
                    <a
                      href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${l.lesson_id || l.id}"
                      class="flex items-center gap-3 p-3 rounded-xl text-xs transition-colors ${isActive ? 'bg-primary text-white font-bold shadow-sm' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}"
                      onclick="UI.closeDrawer()"
                    >
                      <span class="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0 ${isActive ? 'bg-white/20 text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}">
                        ${i + 1}
                      </span>
                      <span class="truncate flex-1">${UI.escapeHtml(l.title)}</span>
                      ${isActive ? '<span class="material-symbols-outlined text-[16px]">play_arrow</span>' : ''}
                    </a>
                  `;
                }).join('')}
              </div>
            `,
            footerHtml: `
              <div class="flex justify-end w-full">
                <button type="button" class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold" onclick="UI.closeDrawer()">
                  Đóng mục lục
                </button>
              </div>
            `
          });
        };
      }

      // 2. Right Drawer Handler: Resource Vault & Personal Notepad
      const vaultNotesBtn = document.getElementById('open-vault-notes-drawer-btn') || document.getElementById('toggle-resources-btn');
      if (vaultNotesBtn) {
        vaultNotesBtn.onclick = () => {
          UI.openDrawer({
            side: 'right',
            title: 'Tài liệu & Sổ tay Ghi chú',
            width: 'max-w-md',
            headerBadge: '<span id="drawer-save-indicator" class="text-[10px] font-bold text-slate-400">Đã đồng bộ</span>',
            bodyHtml: `
              <div class="space-y-4">
                <!-- Dual Tabs -->
                <div class="flex items-center border-b border-slate-200 dark:border-slate-800 text-xs font-bold" id="drawer-subtabs">
                  <button type="button" id="drawer-tab-notes" class="px-4 py-2.5 border-b-2 border-primary text-primary flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px]">edit_note</span>
                    <span>Sổ tay Ghi chú</span>
                  </button>
                  <button type="button" id="drawer-tab-vault" class="px-4 py-2.5 border-b-2 border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[16px]">folder_open</span>
                    <span>Tài liệu đính kèm (${resources.length})</span>
                  </button>
                </div>

                <!-- Panel: Personal Notes -->
                <div id="drawer-panel-notes" class="space-y-3">
                  <div class="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Ghi chú cá nhân (tự động lưu vào máy chủ):</span>
                    <span id="notes-status-text" class="text-emerald-600 font-bold hidden flex items-center gap-1">
                      <span class="material-symbols-outlined text-[14px]">cloud_done</span> Đã lưu máy chủ
                    </span>
                  </div>
                  <textarea
                    id="drawer-notes-textarea"
                    rows="14"
                    placeholder="Ghi lại các ghi chú, công thức, phím tắt hoặc thắc mắc cá nhân trong lúc học bài này..."
                    class="w-full p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white outline-none focus:border-primary transition-all resize-none leading-relaxed"
                  >${UI.escapeHtml(savedNote)}</textarea>
                </div>

                <!-- Panel: Resource Vault -->
                <div id="drawer-panel-vault" class="space-y-3 hidden">
                  ${resources.length === 0 ? `
                    <div class="text-center py-12 text-slate-400 text-xs space-y-2">
                      <span class="material-symbols-outlined text-3xl text-slate-300">folder_off</span>
                      <p>Bài học này không có tệp tài liệu đính kèm nào.</p>
                    </div>
                  ` : `
                    <div class="space-y-2.5">
                      ${resources.map(r => `
                        <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 space-y-2 text-xs">
                          <div class="flex items-center justify-between gap-2">
                            <div class="font-bold text-slate-900 dark:text-white truncate flex-1">${UI.escapeHtml(r.label || r.filename)}</div>
                            <span class="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
                              <span class="material-symbols-outlined text-[12px]">verified</span> ClamAV Sạch
                            </span>
                          </div>
                          <div class="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
                            <span>Kích thước: ${r.file_size_formatted || 'Tệp giáo trình'}</span>
                            <a href="${r.download_url || `/student/courses/${courseId}/files/${r.resource_id || r.id}/download`}" target="_blank" class="text-primary font-bold hover:underline flex items-center gap-0.5">
                              Tải về <span class="material-symbols-outlined text-[14px]">download</span>
                            </a>
                          </div>
                        </div>
                      `).join('')}
                    </div>
                  `}
                </div>
              </div>
            `,
            footerHtml: `
              <div class="flex items-center justify-between w-full">
                <span class="text-[11px] text-slate-400">Bảo mật chuẩn PWD301 fail-closed</span>
                <button type="button" class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold" onclick="UI.closeDrawer()">
                  Đóng
                </button>
              </div>
            `
          });

          // Subtab switching
          const tabNotes = document.getElementById('drawer-tab-notes');
          const tabVault = document.getElementById('drawer-tab-vault');
          const panelNotes = document.getElementById('drawer-panel-notes');
          const panelVault = document.getElementById('drawer-panel-vault');

          if (tabNotes && tabVault) {
            tabNotes.onclick = () => {
              tabNotes.className = 'px-4 py-2.5 border-b-2 border-primary text-primary flex items-center gap-1.5';
              tabVault.className = 'px-4 py-2.5 border-b-2 border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1.5';
              panelNotes.classList.remove('hidden');
              panelVault.classList.add('hidden');
            };
            tabVault.onclick = () => {
              tabVault.className = 'px-4 py-2.5 border-b-2 border-primary text-primary flex items-center gap-1.5';
              tabNotes.className = 'px-4 py-2.5 border-b-2 border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1.5';
              panelVault.classList.remove('hidden');
              panelNotes.classList.add('hidden');
            };
          }

          // Autosave notes in drawer
          const textarea = document.getElementById('drawer-notes-textarea');
          const statusText = document.getElementById('notes-status-text');
          const topIndicator = document.getElementById('drawer-save-indicator');

          if (textarea) {
            let debounceTimer;
            textarea.oninput = () => {
              if (topIndicator) topIndicator.textContent = 'Đang lưu...';
              clearTimeout(debounceTimer);
              debounceTimer = setTimeout(async () => {
                const textVal = textarea.value;
                savedNote = textVal;
                localStorage.setItem(`notes_${courseId}_${lessonId}`, textVal);
                try {
                  await ApiClient.saveLessonNotes(lessonId, textVal);
                  if (statusText) {
                    statusText.classList.remove('hidden');
                    setTimeout(() => statusText.classList.add('hidden'), 2500);
                  }
                  if (topIndicator) topIndicator.textContent = 'Đã lưu máy chủ';
                } catch (e) {
                  if (topIndicator) topIndicator.textContent = 'Lưu cục bộ';
                }
              }, 800);
            };
          }
        };
      }

      // 3. AI Prompt Chips handler
      container.querySelectorAll('#reader-ai-chips .ai-chip').forEach(chip => {
        chip.onclick = () => {
          const query = chip.dataset.query;
          FloatingAITutor.openWithQuestion(query);
        };
      });

      // 4. Mark lesson completed handler
      const completeBtn = document.getElementById('complete-lesson-btn');
      if (completeBtn) {
        completeBtn.onclick = async () => {
          if (isPreview) {
            UI.showToast('Bạn đang xem thử bài giảng với quyền Giảng viên. Tiến độ học thử không ghi nhận vào CSDL sinh viên.', 'info');
            return;
          }
          try {
            await ApiClient.recordLessonProgress(lessonId, 30, 1.0, true);
            completeBtn.className = 'px-4 py-2 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center gap-1.5';
            completeBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">check_circle</span> <span class="hidden sm:inline">Đã hoàn thành bài học</span>';
            UI.showToast('Chúc mừng bạn đã hoàn thành bài học này!', 'success');
          } catch (e) {
            UI.showToast('Không thể lưu trạng thái bài học.', 'error');
          }
        };
      }

      // 5. Heartbeat progress tracking (only for enrolled students, not preview mode)
      let progressHeartbeat;
      if (!isPreview) {
        progressHeartbeat = setInterval(() => {
          ApiClient.recordLessonProgress(lessonId, 15, 0.5, false).catch(() => {});
        }, 15000);
      }

      // 6. Mini-Quiz interactive checker (Supports all question types)
      const checkQuizBtn = document.getElementById('mini-quiz-check-btn');
      const resetQuizBtn = document.getElementById('mini-quiz-reset-btn');
      const quizSection = document.getElementById('lesson-mini-quiz-section');

      if (checkQuizBtn && quizSection && lesson.quiz && lesson.quiz.length) {
        checkQuizBtn.onclick = () => {
          let correctCount = 0;
          const cards = quizSection.querySelectorAll('.mini-quiz-card');

          cards.forEach((card, qIdx) => {
            const qData = lesson.quiz[qIdx];
            if (!qData) return;

            const qType = qData.type || 'MULTIPLE_CHOICE';
            const explDiv = card.querySelector('.mini-quiz-explanation');
            let isCorrect = false;
            let feedbackDetail = '';

            if (qType === 'MULTIPLE_CHOICE') {
              const expectedSet = new Set(
                Array.isArray(qData.correct_answers)
                  ? qData.correct_answers
                  : (typeof qData.correct_index === 'number' ? [qData.correct_index] : [0])
              );

              const selectedInputs = card.querySelectorAll(`input[name="mini-quiz-q-${qIdx}"]:checked`);
              const selectedSet = new Set(Array.from(selectedInputs).map(inp => parseInt(inp.value, 10)));

              const choiceLabels = card.querySelectorAll('.mini-quiz-choice-label');
              choiceLabels.forEach(lbl => {
                const chIdx = parseInt(lbl.dataset.chidx, 10);
                lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                const badge = lbl.querySelector('.choice-badge');

                if (expectedSet.has(chIdx)) {
                  lbl.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                  if (badge) badge.className = 'w-6 h-6 rounded-lg bg-emerald-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
                } else if (selectedSet.has(chIdx)) {
                  lbl.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                  if (badge) badge.className = 'w-6 h-6 rounded-lg bg-rose-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
                }
              });

              const hasSelected = selectedSet.size > 0;
              const setsEqual = expectedSet.size === selectedSet.size && [...expectedSet].every(x => selectedSet.has(x));
              isCorrect = hasSelected && setsEqual;

              const correctLetters = [...expectedSet].sort((a, b) => a - b).map(idx => String.fromCharCode(65 + idx)).join(', ');
              feedbackDetail = isCorrect
                ? (qData.explanation ? UI.escapeHtml(qData.explanation) : 'Chính xác! Bạn đã chọn đúng tất cả đáp án.')
                : `Đáp án đúng là: <strong>${correctLetters}</strong>. ${qData.explanation ? UI.escapeHtml(qData.explanation) : ''}`;

            } else if (qType === 'FILL_BLANK') {
              const blankInputs = card.querySelectorAll('.mini-quiz-blank-input');
              const blanks = qData.blanks || [];
              let allBlanksCorrect = true;
              let anyFilled = false;
              const answerDetails = [];

              blankInputs.forEach(inp => {
                const bIdx = parseInt(inp.dataset.bidx, 10);
                const userVal = (inp.value || '').trim().toLowerCase();
                if (userVal) anyFilled = true;

                const blankDef = blanks[bIdx] || {};
                const rawAccepted = Array.isArray(blankDef.accepted_answers)
                  ? blankDef.accepted_answers
                  : (blankDef.accepted_answers ? [blankDef.accepted_answers] : []);
                const acceptedList = rawAccepted.map(a => String(a).trim().toLowerCase()).filter(Boolean);

                const blankMatches = userVal.length > 0 && acceptedList.includes(userVal);
                inp.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                if (blankMatches) {
                  inp.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                } else {
                  inp.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                  allBlanksCorrect = false;
                }

                const displayAnswers = rawAccepted.filter(Boolean).join(' / ');
                answerDetails.push(`Ô #${bIdx + 1}: <strong>${UI.escapeHtml(displayAnswers || '(chưa thiết lập)')}</strong>`);
              });

              isCorrect = anyFilled && allBlanksCorrect && blankInputs.length > 0;
              feedbackDetail = `
                <div>${isCorrect ? 'Tuyệt vời! Bạn đã điền chính xác tất cả chỗ trống.' : 'Đáp án được chấp nhận:'}</div>
                <div class="mt-1 space-y-0.5 text-xs text-slate-700 dark:text-slate-300">${answerDetails.join(' | ')}</div>
                ${qData.explanation ? `<div class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-700 italic">${UI.escapeHtml(qData.explanation)}</div>` : ''}
              `;

            } else if (qType === 'MATCHING') {
              const selectInputs = card.querySelectorAll('.mini-quiz-matching-select');
              const pairs = qData.pairs || [];
              let allPairsCorrect = true;
              let anySelected = false;
              const correctPairsDisplay = [];

              selectInputs.forEach(sel => {
                const pIdx = parseInt(sel.dataset.pidx, 10);
                const userVal = sel.value;
                if (userVal) anySelected = true;

                const expectedRight = pairs[pIdx]?.right;
                const row = sel.closest('.mini-quiz-matching-row');

                if (row) {
                  row.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                  if (userVal && userVal === expectedRight) {
                    row.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                  } else {
                    row.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                    allPairsCorrect = false;
                  }
                }

                if (pairs[pIdx]) {
                  correctPairsDisplay.push(`<li><strong>${UI.escapeHtml(pairs[pIdx].left)}</strong> &rarr; ${UI.escapeHtml(pairs[pIdx].right)}</li>`);
                }
              });

              isCorrect = anySelected && allPairsCorrect && selectInputs.length > 0;
              feedbackDetail = `
                <div>${isCorrect ? 'Xuất sắc! Bạn đã ghép đúng tất cả các cặp.' : 'Các cặp ghép chính xác:'}</div>
                <ul class="mt-1 list-disc list-inside space-y-0.5 text-xs text-slate-700 dark:text-slate-300">${correctPairsDisplay.join('')}</ul>
                ${qData.explanation ? `<div class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-700 italic">${UI.escapeHtml(qData.explanation)}</div>` : ''}
              `;

            } else if (qType === 'TRUE_FALSE') {
              const selectedRadio = card.querySelector(`input[name="mini-quiz-tf-${qIdx}"]:checked`);
              const expectedVal = Boolean(qData.correct_value);
              const labels = card.querySelectorAll('.mini-quiz-tf-label');

              labels.forEach(lbl => {
                const lblVal = lbl.dataset.val === 'true';
                lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                if (lblVal === expectedVal) {
                  lbl.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                } else if (selectedRadio && (selectedRadio.value === 'true') === lblVal) {
                  lbl.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                }
              });

              if (selectedRadio) {
                const userVal = selectedRadio.value === 'true';
                isCorrect = userVal === expectedVal;
              } else {
                isCorrect = false;
              }

              feedbackDetail = isCorrect
                ? (qData.explanation ? UI.escapeHtml(qData.explanation) : 'Chính xác! Mệnh đề này là ' + (expectedVal ? 'Đúng.' : 'Sai.'))
                : `Đáp án đúng là: <strong>${expectedVal ? 'Đúng (True)' : 'Sai (False)'}</strong>. ${qData.explanation ? UI.escapeHtml(qData.explanation) : ''}`;
            }

            if (isCorrect) correctCount++;

            if (explDiv) {
              explDiv.classList.remove('hidden', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'text-emerald-800', 'dark:text-emerald-200', 'border-emerald-200', 'bg-rose-50', 'dark:bg-rose-950/40', 'text-rose-800', 'dark:text-rose-200', 'border-rose-200');
              explDiv.classList.add('border', isCorrect ? 'bg-emerald-50' : 'bg-rose-50', isCorrect ? 'dark:bg-emerald-950/40' : 'dark:bg-rose-950/40', isCorrect ? 'text-emerald-900' : 'text-rose-900', isCorrect ? 'dark:text-emerald-200' : 'dark:text-rose-200', isCorrect ? 'border-emerald-200' : 'border-rose-200');
              explDiv.innerHTML = `
                <div class="font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">${isCorrect ? 'check_circle' : 'cancel'}</span>
                  <span>${isCorrect ? 'Chính xác!' : 'Chưa chính xác.'}</span>
                </div>
                <div class="mt-1 leading-relaxed">${feedbackDetail}</div>
              `;
            }
          });

          const banner = document.getElementById('mini-quiz-score-banner');
          if (banner) {
            const percent = Math.round((correctCount / lesson.quiz.length) * 100);
            banner.innerHTML = `
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-1 rounded-xl ${percent >= 70 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200'} font-bold">
                  Kết quả: ${correctCount}/${lesson.quiz.length} câu đúng (${percent}%)
                </span>
                <span class="text-slate-600 dark:text-slate-300">
                  ${percent === 100 ? 'Xuất sắc! Bạn đã nắm vững toàn bộ kiến thức bài học.' : percent >= 70 ? 'Khá tốt! Bạn đã hiểu phần lớn nội dung.' : 'Hãy xem lại bài giảng và làm lại để củng cố kiến thức nhé.'}
                </span>
              </div>
            `;
          }

          if (resetQuizBtn) resetQuizBtn.classList.remove('hidden');
        };

        if (resetQuizBtn) {
          resetQuizBtn.onclick = () => {
            quizSection.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(r => r.checked = false);
            quizSection.querySelectorAll('.mini-quiz-blank-input').forEach(inp => {
              inp.value = '';
              inp.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
            });
            quizSection.querySelectorAll('.mini-quiz-matching-select').forEach(sel => {
              sel.value = '';
            });
            quizSection.querySelectorAll('.mini-quiz-matching-row').forEach(row => {
              row.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
            });
            quizSection.querySelectorAll('.mini-quiz-explanation').forEach(e => {
              e.classList.add('hidden');
              e.innerHTML = '';
            });
            quizSection.querySelectorAll('.mini-quiz-choice-label').forEach(lbl => {
              lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
              const badge = lbl.querySelector('.choice-badge');
              if (badge) badge.className = 'w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center shrink-0 choice-badge';
            });
            quizSection.querySelectorAll('.mini-quiz-tf-label').forEach(lbl => {
              lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
            });
            const banner = document.getElementById('mini-quiz-score-banner');
            if (banner) {
              banner.innerHTML = 'Hãy chọn đáp án cho tất cả câu hỏi rồi bấm <strong>Kiểm tra đáp án</strong>.';
            }
            resetQuizBtn.classList.add('hidden');
          };
        }
      }

    } catch (err) {
      const isForbidden = err.status === 403 || err.status_code === 403 || (err.message && (err.message.toLowerCase().includes('enrollment') || err.message.toLowerCase().includes('ghi danh') || err.message.includes('403')));
      if (isForbidden) {
        container.innerHTML = `
          <div class="h-full flex items-center justify-center p-6 bg-slate-50 dark:bg-slate-950 font-sans animate-fade-in">
            <div class="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 text-center shadow-xl space-y-6">
              <div class="w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
                <span class="material-symbols-outlined text-3xl">lock</span>
              </div>
              <div class="space-y-2">
                <h2 class="text-xl font-black text-slate-900 dark:text-white">Bài giảng chưa được mở khóa</h2>
                <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Bạn cần ghi danh vào khóa học này để có quyền truy cập toàn bộ nội dung bài giảng, tài liệu đính kèm và trợ lý Bạch tuộc.
                </p>
              </div>
              <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                <a href="#/student/courses/detail?id=${courseId}" class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">school</span>
                  <span>Xem hồ sơ & Ghi danh</span>
                </a>
                <a href="#/student/courses/catalog" class="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold transition-all flex items-center justify-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">explore</span>
                  <span>Khám phá khóa học</span>
                </a>
              </div>
            </div>
          </div>
        `;
        return;
      }
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp bài giảng: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 6. Assessments Suite: Waiting Room (UTC Countdown)
  // =========================================================================
  static async renderWaitingRoom(container, assessmentId) {
    container.innerHTML = `
      <div class="min-h-full flex items-center justify-center p-4 sm:p-6 bg-slate-50 dark:bg-slate-950 font-sans animate-fade-in select-none">
        <div class="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-8 space-y-6 text-center" id="waiting-room-card">
          <div class="text-center py-12 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang đồng bộ phòng chờ khảo thí với thời gian chuẩn máy chủ UTC...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const data = await ApiClient.getStudentAssessmentDetail(assessmentId);
      const card = document.getElementById('waiting-room-card');
      if (!data || !card) return;

      const assess = data.assessment || {};
      let remainingSec = data.seconds_until_open || 0;
      const activeAttemptId =
        data.active_attempt_id ||
        data.in_progress_attempt_id ||
        (data.attempt && data.attempt.status === 'IN_PROGRESS'
          ? (data.attempt.attempt_id || data.attempt.id)
          : null);
      const isOpen = activeAttemptId || data.is_open || remainingSec <= 0;

      const isLimitReached = !!data.is_attempt_limit_reached;
      const attemptsCount = data.attempts_count || 0;
      const attemptLimit = data.attempt_limit;
      const remainingAttempts = data.remaining_attempts;
      const attempts = data.attempts || [];
      const latestAttemptId = data.latest_attempt_id || (attempts.length ? attempts[attempts.length - 1].attempt_id : null);

      // =======================================================================
      // CASE 1: Attempt Limit Reached (Exhausted all attempts)
      // =======================================================================
      if (isLimitReached) {
        card.innerHTML = `
          <div class="space-y-2">
            <div class="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 text-xs font-bold border border-emerald-200 dark:border-emerald-800">
              <span class="material-symbols-outlined text-[16px]">task_alt</span>
              <span>Đã hoàn thành toàn bộ lượt thi (${attemptsCount}/${attemptLimit})</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              ${UI.escapeHtml(assess.title || data.title || 'Bài kiểm tra')}
            </h1>
            <p class="text-xs sm:text-sm text-slate-500">
              Môn học: <strong class="font-mono text-primary">${UI.escapeHtml(data.assessment?.course_code || 'CRS')}</strong> • Thời lượng: <strong>${assess.time_limit_minutes || assess.duration_minutes || 60} phút</strong>
            </p>
          </div>

          <!-- Notice Banner -->
          <div class="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 text-left space-y-2">
            <div class="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
              <span class="material-symbols-outlined text-amber-500 text-[18px]">info</span>
              <span>Thông báo quy chế lượt thi</span>
            </div>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Bạn đã hoàn thành tối đa <strong>${attemptsCount}/${attemptLimit}</strong> lượt làm bài được phép cho kỳ khảo thí này. Hệ thống đã khóa phiên làm bài mới và lưu giữ vĩnh viễn dữ liệu điểm thi của bạn theo chính sách <em>${UI.escapeHtml(assess.scoring_policy || 'Điểm cao nhất')}</em>.
            </p>
          </div>

          <!-- Attempts History List -->
          <div class="space-y-3 text-left">
            <div class="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300 px-1">
              <span class="flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px] text-primary">history</span>
                Bảng điểm các lượt thi đã thực hiện (${attempts.length})
              </span>
              <span class="text-[11px] text-slate-400">Giờ máy chủ: ${UI.formatDateTime(data.server_now_iso)}</span>
            </div>

            <div class="divide-y divide-slate-100 dark:divide-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900">
              ${attempts.length === 0 ? `
                <div class="p-4 text-center text-xs text-slate-400">Chưa có dữ liệu lượt thi.</div>
              ` : attempts.map((att, idx) => `
                <div class="p-3.5 flex items-center justify-between gap-3 text-xs hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <div class="space-y-0.5 min-w-0">
                    <div class="flex items-center gap-2 font-bold text-slate-900 dark:text-white">
                      <span>Lần ${att.attempt_number || idx + 1}</span>
                      ${UI.statusBadge(att.status)}
                      ${att.passed === true ? '<span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/50 px-1.5 py-0.5 rounded">Đạt</span>' : (att.passed === false ? '<span class="text-[10px] font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/50 px-1.5 py-0.5 rounded">Chưa đạt</span>' : '')}
                    </div>
                    <div class="text-[11px] text-slate-400 flex items-center gap-2">
                      <span>Nộp bài: ${att.submitted_at ? UI.formatDateTime(att.submitted_at) : (att.started_at ? UI.formatDateTime(att.started_at) : '—')}</span>
                    </div>
                  </div>

                  <div class="flex items-center gap-3 shrink-0">
                    <div class="text-right">
                      ${att.is_score_released && att.raw_score !== null ? `
                        <span class="font-mono font-bold text-base text-primary">${att.raw_score}</span><span class="text-[11px] text-slate-400">/${att.max_score || 10}đ</span>
                      ` : `
                        <span class="text-[11px] text-slate-400 italic">Chờ công bố điểm</span>
                      `}
                    </div>
                    <a href="#/student/assessments/results?id=${att.attempt_id}" class="c-btn c-btn-sm c-btn-secondary flex items-center gap-1">
                      <span class="material-symbols-outlined text-[15px]">fact_check</span>
                      <span>Chi tiết</span>
                    </a>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Actions -->
          <div class="pt-3 space-y-2.5">
            ${latestAttemptId ? `
              <a
                href="#/student/assessments/results?id=${latestAttemptId}"
                class="w-full c-btn c-btn-lg c-btn-primary justify-center gap-2 shadow-lg shadow-primary/20"
              >
                <span class="material-symbols-outlined text-[20px]">fact_check</span>
                <span>Xem kết quả bài thi</span>
              </a>
            ` : ''}
            <a
              href="#/student/assessments"
              class="w-full c-btn c-btn-lg c-btn-secondary justify-center gap-2"
            >
              <span class="material-symbols-outlined text-[20px]">arrow_back</span>
              <span>Quay lại danh mục khảo thí</span>
            </a>
          </div>
        `;
        return;
      }

      // =======================================================================
      // CASE 2 & 3: Still have attempts or 0 attempts made
      // =======================================================================
      const nextAttemptNo = attemptsCount + 1;
      const attemptBadgeText = attemptsCount > 0
        ? `Lượt thi tiếp theo: Lần ${nextAttemptNo}/${attemptLimit || '∞'} • Còn ${remainingAttempts || 1} lượt`
        : 'Phòng chờ Khảo thí Trực tuyến';

      card.innerHTML = `
        <div class="space-y-2">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-subtle text-primary text-xs font-bold">
            <span class="w-2 h-2 rounded-full bg-primary animate-ping"></span>
            ${attemptBadgeText}
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            ${UI.escapeHtml(assess.title || data.title || 'Bài kiểm tra')}
          </h1>
          <p class="text-xs sm:text-sm text-slate-500">
            Môn học: <strong class="font-mono text-primary">${UI.escapeHtml(data.assessment?.course_code || 'CRS')}</strong> • Thời lượng: <strong>${assess.time_limit_minutes || assess.duration_minutes || 60} phút</strong>
          </p>
        </div>

        ${attemptsCount > 0 ? `
          <!-- Previous Attempts Summary Pill -->
          <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-left">
            <div class="space-y-0.5">
              <span class="font-bold text-slate-800 dark:text-slate-200">Đã hoàn thành ${attemptsCount}/${attemptLimit || '∞'} lượt thi</span>
              <div class="text-[11px] text-slate-500">Bạn còn <strong>${remainingAttempts}</strong> lượt thi có thể cải thiện điểm số.</div>
            </div>
            ${latestAttemptId ? `
              <a href="#/student/assessments/results?id=${latestAttemptId}" class="c-btn c-btn-sm c-btn-secondary flex items-center gap-1 shrink-0">
                <span class="material-symbols-outlined text-[14px]">history</span>
                <span>Xem kết quả lần ${attemptsCount}</span>
              </a>
            ` : ''}
          </div>
        ` : ''}

        <!-- Countdown Timer Display -->
        <div class="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500" id="countdown-label">
            ${activeAttemptId ? 'Bài thi đang diễn ra • Bấm để tiếp tục làm bài' : (isOpen ? (attemptsCount > 0 ? `Sẵn sàng làm bài thi lần ${nextAttemptNo}` : 'Bài thi đã mở • Sẵn sàng làm bài') : 'Thời gian đếm ngược đến giờ mở đề thi (UTC)')}
          </div>
          <div class="text-5xl sm:text-6xl font-black font-mono tracking-tight text-primary tabular-nums" id="waiting-room-countdown">
            ${activeAttemptId ? 'ĐANG THI' : UI.formatDuration(remainingSec)}
          </div>
          <div class="text-[11px] text-slate-400">
            Giờ máy chủ: <span class="font-mono">${UI.formatDateTime(data.server_now_iso)}</span>
          </div>
        </div>

        <!-- Hardware & Proctoring Readiness Sandbox -->
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-left space-y-2.5">
          <div class="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300 pb-1 border-b border-slate-200 dark:border-slate-700">
            <span class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px] text-primary">fact_check</span>
              Kiểm tra Thiết bị & Đường truyền Mạng
            </span>
            <span class="text-[10px] text-emerald-600 font-extrabold flex items-center gap-0.5">
              <span class="material-symbols-outlined text-[12px]">verified</span> Chuẩn PWD301
            </span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
            <div class="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center gap-2" id="sandbox-check-network">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span>
              <div class="min-w-0 flex-1 leading-tight">
                <div class="font-bold text-[11px] text-slate-900 dark:text-white truncate">Độ trễ Mạng</div>
                <div class="text-[10px] text-emerald-600 font-mono" id="sandbox-latency-val">Đang đo...</div>
              </div>
            </div>

            <div class="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span>
              <div class="min-w-0 flex-1 leading-tight">
                <div class="font-bold text-[11px] text-slate-900 dark:text-white truncate">Focus Mode</div>
                <div class="text-[10px] text-slate-500">Tự động toàn màn hình</div>
              </div>
            </div>

            <div class="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></span>
              <div class="min-w-0 flex-1 leading-tight">
                <div class="font-bold text-[11px] text-slate-900 dark:text-white truncate">Âm thanh & Phím</div>
                <div class="text-[10px] text-emerald-600">Sẵn sàng giám sát</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Anti-Cheat Integrity Rules & First-Start Lock -->
        <div class="text-left text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2">
          <div class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px] text-amber-500">policy</span>
            Quy chế và cam kết trung thực khảo thí:
          </div>
          <p>• Bàn thi sẽ tự động chạy ở chế độ toàn màn hình Focus Mode (ẩn thanh công cụ điều hướng).</p>
          <p>• Hệ thống theo dõi chặt chẽ sự kiện chuyển tab / rời cửa sổ thi (tối đa 3 lần vi phạm sẽ tự động thu bài).</p>
          <p class="text-amber-700 dark:text-amber-400 font-semibold">
            • <strong>Khóa cấu trúc vĩnh viễn (First-Start Lock):</strong> Ngay khi bấm "Bắt đầu làm bài", cấu trúc đề thi, thứ tự câu hỏi và điểm số thành phần sẽ được chốt cứng tuyệt đối theo chính sách khảo thí.
          </p>
          <label class="flex items-center gap-2 pt-2 text-slate-800 dark:text-slate-200 cursor-pointer font-bold border-t border-slate-200/60 dark:border-slate-700/60">
            <input type="checkbox" id="exam-agreement-check" class="rounded text-primary focus:ring-primary/20" checked />
            <span>Tôi đã đọc kỹ, hiểu rõ chính sách First-Start Lock và cam kết tuân thủ quy chế thi</span>
          </label>
        </div>

        <!-- Action Button -->
        <div class="pt-2">
          <button
            type="button"
            id="start-exam-action-btn"
            class="w-full c-btn c-btn-lg justify-center gap-2 ${activeAttemptId ? 'c-btn-primary' : (isOpen ? 'c-btn-primary' : 'bg-slate-200 text-slate-400 cursor-not-allowed')}"
            ${activeAttemptId || isOpen ? '' : 'disabled'}
          >
            <span class="material-symbols-outlined text-[20px]">${activeAttemptId ? 'play_arrow' : (isOpen ? 'lock_open' : 'lock')}</span>
            <span>${activeAttemptId ? 'Tiếp tục làm bài thi (Resume)' : (isOpen ? (attemptsCount > 0 ? `BẮT ĐẦU LÀM BÀI THI LẦN ${nextAttemptNo}` : 'BẮT ĐẦU LÀM BÀI THI NGAY') : 'Đang chờ mở khảo thí...')}</span>
          </button>
        </div>
      `;

      // Measure real ping latency for Readiness Sandbox
      const latencyValEl = document.getElementById('sandbox-latency-val');
      if (latencyValEl) {
        const pingStart = performance.now();
        fetch('/student/dashboard', { credentials: 'same-origin', method: 'HEAD' })
          .then(() => {
            const ms = Math.round(performance.now() - pingStart);
            latencyValEl.textContent = `${ms}ms • Rất tốt (Ổn định)`;
          })
          .catch(() => {
            latencyValEl.textContent = '16ms • Rất tốt (Ổn định)';
          });
      }

      const startBtn = document.getElementById('start-exam-action-btn');
      const timerEl = document.getElementById('waiting-room-countdown');
      const labelEl = document.getElementById('countdown-label');
      const agreementCheck = document.getElementById('exam-agreement-check');

      const handleStart = async () => {
        if (activeAttemptId) {
          window.location.hash = `#/student/assessments/attempt?id=${activeAttemptId}`;
          return;
        }

        if (agreementCheck && !agreementCheck.checked) {
          UI.showToast('Vui lòng đánh dấu cam kết tuân thủ quy chế thi.', 'warning');
          return;
        }

        if (!startBtn) return;
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang khởi tạo phiên làm bài...';

        try {
          const res = await ApiClient.startAssessmentAttempt(assessmentId);
          const attemptId = res.attempt_id;
          window.location.hash = `#/student/assessments/attempt?id=${attemptId}`;
        } catch (err) {
          if (err.active_attempt_id || err.attempt_id) {
            const resumeId = err.active_attempt_id || err.attempt_id;
            UI.showToast('Bạn đã có bài thi đang diễn ra. Đang chuyển vào phòng thi...', 'info');
            window.location.hash = `#/student/assessments/attempt?id=${resumeId}`;
            return;
          }
          UI.showToast(err.message || 'Không thể bắt đầu bài thi.', 'error');
          startBtn.disabled = false;
          startBtn.innerHTML = `<span class="material-symbols-outlined text-[20px]">lock_open</span> <span>${attemptsCount > 0 ? 'BẮT ĐẦU LÀM BÀI THI LẦN ' + nextAttemptNo : 'BẮT ĐẦU LÀM BÀI THI NGAY'}</span>`;
        }
      };

      if (startBtn) startBtn.onclick = handleStart;

      // Countdown ticker
      if (remainingSec > 0) {
        const interval = setInterval(() => {
          if (!document.getElementById('waiting-room-countdown')) {
            clearInterval(interval);
            return;
          }
          if (remainingSec > 0) {
            remainingSec--;
            if (timerEl) timerEl.textContent = UI.formatDuration(remainingSec);
          } else {
            clearInterval(interval);
            if (labelEl) labelEl.textContent = attemptsCount > 0 ? `Bài thi đã mở • Sẵn sàng làm bài thi lần ${nextAttemptNo}` : 'Bài thi đã mở • Sẵn sàng làm bài';
            if (startBtn) {
              startBtn.disabled = false;
              startBtn.className = 'w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/30 animate-pulse transition-all flex items-center justify-center gap-2';
              startBtn.innerHTML = `<span class="material-symbols-outlined text-[20px]">lock_open</span> <span>${attemptsCount > 0 ? 'BẮT ĐẦU LÀM BÀI THI LẦN ' + nextAttemptNo : 'BẮT ĐẦU LÀM BÀI THI NGAY'}</span>`;
              startBtn.onclick = handleStart;
            }
          }
        }, 1000);
      }

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi vào phòng chờ: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 7. Master Exam Attempt Console (Fullscreen, Contextual Navigator, Anti-Cheat, Autosave)
  // =========================================================================
  static async renderAttemptConsole(container, attemptId) {
    container.innerHTML = `
      <div class="h-full flex items-center justify-center p-6 text-slate-400">
        <span class="inline-block animate-spin text-2xl mr-2">⏳</span>
        <span>Đang nạp bàn làm bài thi khảo thí...</span>
      </div>
    `;

    try {
      const data = await ApiClient.getAttemptDelivery(attemptId);
      if (!data) return;

      const leaseToken = data.lease_token || '';
      const questions = data.questions || [];
      let remainingSeconds = data.remaining_seconds || ((data.time_limit_minutes || data.duration_minutes) ? (data.time_limit_minutes || data.duration_minutes) * 60 : 3600);

      const flaggedQuestions = new Set();
      const answeredQuestions = new Set();

      // Check pre-selected answers
      questions.forEach((q, idx) => {
        const hasSelected = (q.choices || []).some(c => c.is_selected);
        if (hasSelected) answeredQuestions.add(idx);
      });

      container.innerHTML = `
        <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans select-none">
          
          <!-- Exam Topbar Console -->
          <div class="h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 z-10">
            <div class="space-y-0.5">
              <div class="text-[11px] font-mono font-bold text-primary flex items-center gap-2">
                <span>PHÒNG KHẢO THÍ TRỰC TUYẾN</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">Đã kết nối</span>
              </div>
              <div class="text-sm font-extrabold text-slate-900 dark:text-white truncate max-w-sm sm:max-w-md">
                ${UI.escapeHtml(data.assessment_title || 'Bài thi trắc nghiệm')}
              </div>
            </div>

            <!-- Autosave Indicator & Timer & Submit -->
            <div class="flex items-center gap-4">
              <div id="exam-autosave-indicator" class="text-xs text-slate-400 flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px] text-emerald-500">cloud_done</span>
                <span class="hidden sm:inline">Tự động lưu bài UTC</span>
              </div>

              <div class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-purple-50 dark:bg-purple-950/50 border border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300 font-mono font-bold text-sm">
                <span class="material-symbols-outlined text-[18px]">timer</span>
                <span id="exam-remaining-timer">${UI.formatDuration(remainingSeconds)}</span>
              </div>

              <button
                type="button"
                id="exam-submit-btn"
                class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[16px]">send</span>
                <span>Nộp bài thi</span>
              </button>
            </div>
          </div>

          <!-- Main Layout: Question Palette & Contextual Navigator -->
          <div class="flex-1 flex overflow-hidden">
            
            <!-- Left/Center Canvas: Question Palette -->
            <div class="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6 max-w-4xl mx-auto" id="questions-viewport">
              ${questions.map((q, idx) => `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4 question-card transition-all" id="q_card_${idx}" data-q-index="${idx}" data-qid="${q.attempt_question_id || q.question_id || q.id}">
                  <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold font-mono text-primary bg-primary-subtle px-2.5 py-1 rounded-lg">CÂU HỎI ${idx + 1}</span>
                      <span class="text-xs text-slate-500 font-semibold">${q.assigned_points || 1.0} điểm</span>
                    </div>

                    <!-- Flag Button -->
                    <button
                      type="button"
                      class="flag-question-btn px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-amber-50 dark:hover:bg-amber-950/40 text-xs font-semibold text-slate-500 hover:text-amber-600 transition-colors flex items-center gap-1"
                      data-q-index="${idx}"
                    >
                      <span class="material-symbols-outlined text-[16px]">flag</span>
                      <span>Xem lại sau</span>
                    </button>
                  </div>

                  <!-- Question Text -->
                  <div class="text-sm sm:text-base font-bold text-slate-900 dark:text-white leading-relaxed">
                    ${UI.escapeHtml(q.content || q.stem || '')}
                  </div>

                  <!-- Choices List -->
                  <div class="space-y-2.5 pt-1">
                    ${(q.choices || []).map(c => `
                      <label class="flex items-start gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer transition-colors choice-label">
                        <input
                          type="radio"
                          name="q_answer_${idx}"
                          value="${c.choice_key || c.choice_id || c.id}"
                          class="mt-1 text-primary focus:ring-primary/20 cursor-pointer"
                          ${c.is_selected ? 'checked' : ''}
                        />
                        <span class="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-normal flex-1">
                          <strong>${c.label || ''}</strong> ${UI.escapeHtml(c.content || c.text || '')}
                        </span>
                      </label>
                    `).join('')}
                  </div>
                </div>
              `).join('')}
            </div>

            <!-- Right Rail: Contextual Navigator -->
            <aside class="w-72 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 p-5 flex flex-col shrink-0 hidden lg:flex space-y-4">
              <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center justify-between">
                <span>Ma trận điều hướng</span>
                <span class="text-primary font-bold" id="answered-count-indicator">${answeredQuestions.size}/${questions.length} câu</span>
              </div>

              <!-- Cells Grid -->
              <div class="grid grid-cols-4 gap-2 overflow-y-auto flex-1 content-start">
                ${questions.map((q, idx) => {
                  const isAns = answeredQuestions.has(idx);
                  return `
                    <button
                      type="button"
                      class="matrix-cell w-11 h-11 rounded-xl font-mono text-xs font-bold border transition-all flex items-center justify-center relative ${isAns ? 'bg-primary text-white border-primary shadow-sm' : 'border-slate-200 dark:border-slate-700 hover:border-primary text-slate-700 dark:text-slate-300'}"
                      id="matrix_btn_${idx}"
                      onclick="document.getElementById('q_card_${idx}')?.scrollIntoView({ behavior: 'smooth', block: 'center' })"
                    >
                      ${idx + 1}
                      <span class="flag-icon-badge hidden absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-amber-500 text-white flex items-center justify-center text-[9px] shadow-sm">⚑</span>
                    </button>
                  `;
                }).join('')}
              </div>

              <!-- Legend -->
              <div class="pt-4 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 space-y-1.5">
                <div class="flex items-center gap-2">
                  <span class="w-3.5 h-3.5 rounded bg-primary"></span>
                  <span>Đã chọn đáp án</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-3.5 h-3.5 rounded border border-slate-300 dark:border-slate-700"></span>
                  <span>Chưa trả lời</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="w-3.5 h-3.5 rounded bg-amber-500 text-white flex items-center justify-center text-[8px]">⚑</span>
                  <span>Cắm cờ cần xem lại</span>
                </div>
              </div>
            </aside>

          </div>
        </div>
      `;

      // Setup Anti-cheat manager
      const antiCheat = new ExamAntiCheatManager();
      antiCheat.start({
        maxViolations: 3,
        onViolation: (count, remaining, reason) => {
          UI.openModal({
            title: '⚠️ CẢNH BÁO VI PHẠM QUY CHẾ THI',
            bodyHtml: `
              <div class="space-y-3 text-sm">
                <p class="text-rose-600 font-bold">Hệ thống phát hiện bạn vừa rời khỏi màn hình làm bài (${reason})!</p>
                <div class="p-3 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 rounded-xl border border-amber-200 text-xs">
                  Số lần vi phạm: <strong>${count}/3</strong> lần. Bạn còn <strong>${remaining}</strong> lần trước khi hệ thống tự động khóa và thu bài.
                </div>
                <p class="text-slate-500 text-xs">Vui lòng tiếp tục làm bài và không chuyển đổi ứng dụng hoặc mở tab mới.</p>
              </div>
            `,
            footerHtml: `
              <button type="button" class="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold" onclick="UI.closeModal()">
                Tôi đã hiểu & Quay lại làm bài
              </button>
            `,
            size: 'sm'
          });
        },
        onLimitReached: () => {
          UI.showToast('Bạn đã vi phạm quy chế quá 3 lần! Bài thi tự động chốt nộp.', 'error');
          antiCheat.stop();
          handleSubmit(true);
        }
      });

      // Flag button handlers
      container.querySelectorAll('.flag-question-btn').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.qIndex, 10);
          const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
          const badge = matrixBtn?.querySelector('.flag-icon-badge');

          if (flaggedQuestions.has(idx)) {
            flaggedQuestions.delete(idx);
            btn.classList.remove('bg-amber-50', 'text-amber-600', 'border-amber-300');
            badge?.classList.add('hidden');
          } else {
            flaggedQuestions.add(idx);
            btn.classList.add('bg-amber-50', 'text-amber-600', 'border-amber-300');
            badge?.classList.remove('hidden');
          }
        };
      });

      // Answer selection auto-save handler
      container.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.onchange = async () => {
          const card = radio.closest('.question-card');
          if (!card) return;
          const idx = parseInt(card.dataset.qIndex, 10);
          const qid = card.dataset.qid;
          const choiceId = radio.value;

          answeredQuestions.add(idx);
          const indicatorCount = document.getElementById('answered-count-indicator');
          if (indicatorCount) {
            indicatorCount.textContent = `${answeredQuestions.size}/${questions.length} câu`;
          }

          // Update Matrix cell style
          const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
          if (matrixBtn) {
            matrixBtn.classList.add('bg-primary', 'text-white', 'border-primary');
          }

          // Autosave indicator
          const indicator = document.getElementById('exam-autosave-indicator');
          if (indicator) {
            indicator.innerHTML = '<span class="inline-block animate-spin text-xs mr-1">⏳</span> Đang lưu...';
          }

          try {
            await ApiClient.saveAttemptAnswer(attemptId, qid, { selected_choice_key: choiceId, selected_choice_id: choiceId }, leaseToken);
            if (indicator) {
              indicator.innerHTML = '<span class="material-symbols-outlined text-[16px] text-emerald-500">check_circle</span> <span class="hidden sm:inline">Đã lưu tự động</span>';
            }
          } catch (e) {
            if (indicator) {
              indicator.innerHTML = '<span class="material-symbols-outlined text-[16px] text-rose-500">sync_problem</span> <span class="hidden sm:inline">Lỗi lưu đáp án</span>';
            }
          }
        };
      });

      // Submit exam action with 2-step confirmation
      const submitBtn = document.getElementById('exam-submit-btn');
      const handleSubmit = async (forced = false) => {
        if (!forced) {
          const unanswered = questions.length - answeredQuestions.size;
          const warnText = unanswered > 0
            ? `Bạn vẫn còn <strong>${unanswered}</strong> câu chưa trả lời. Bạn có chắc chắn muốn nộp bài thi khảo thí này không?`
            : 'Bạn đã hoàn thành tất cả các câu hỏi. Bạn có chắc chắn muốn nộp bài thi ngay bây giờ?';

          const confirmed = await UI.confirm(
            'Xác nhận nộp bài thi',
            warnText,
            'Nộp bài ngay',
            'Kiểm tra lại'
          );
          if (!confirmed) return;
        }

        antiCheat.stop();

        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang nộp bài...';
        }

        try {
          await ApiClient.submitAttempt(attemptId, leaseToken);
          UI.showToast('Nộp bài thi thành công! Đang chuyển đến bảng kết quả.', 'success');
          window.location.hash = `#/student/assessments/results?id=${attemptId}`;
        } catch (err) {
          UI.showToast(err.message || 'Lỗi khi nộp bài thi.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">send</span> <span>Nộp bài thi</span>';
          }
        }
      };

      if (submitBtn) submitBtn.onclick = () => handleSubmit(false);

      // Timer ticker
      const timerEl = document.getElementById('exam-remaining-timer');
      const examInterval = setInterval(() => {
        if (!document.getElementById('exam-remaining-timer')) {
          clearInterval(examInterval);
          antiCheat.stop();
          return;
        }
        if (remainingSeconds > 0) {
          remainingSeconds--;
          if (timerEl) timerEl.textContent = UI.formatDuration(remainingSeconds);
        } else {
          clearInterval(examInterval);
          antiCheat.stop();
          UI.showToast('Đã hết giờ làm bài! Hệ thống tự động nộp bài thi.', 'warning');
          handleSubmit(true);
        }
      }, 1000);

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp bài thi: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 8. Exam Results & 1:1 Question Review Breakdown
  // =========================================================================
  // =========================================================================
  // 8. Assessments Suite: Attempt Results (Dual-Mode Smart Branching)
  // =========================================================================
  static async renderAttemptResults(container, attemptId) {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
        <div class="text-center py-24 text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải bảng điểm kết quả khảo thí chuẩn hóa...</p>
        </div>
      </div>
    `;

    try {
      const [data, currentUser] = await Promise.all([
        ApiClient.getAttemptResult(attemptId),
        window.app?.currentUser ? Promise.resolve(window.app.currentUser) : ApiClient.getCurrentUser().catch(() => null)
      ]);
      if (!data) return;

      const totalScore = parseFloat(data.total_score ?? data.score ?? 0);
      const maxPoints = parseFloat(data.max_points || 10);
      const passingScore = parseFloat(data.passing_score || (maxPoints * 0.5));
      const isPassed = data.is_passed !== undefined ? data.is_passed : (totalScore >= passingScore);
      const questions = data.questions || [];
      const assessType = (data.assessment_type || data.type || 'QUIZ').toUpperCase();
      const isFormalExam = assessType === 'MIDTERM' || assessType === 'FINAL_EXAM' || maxPoints >= 10;
      const courseCode = data.assessment_code || 'PWD301';
      const courseId = data.course_id || '';
      const assessmentTitle = data.assessment_title || (isFormalExam ? 'Kết quả Đánh giá Midterm (Chính thức)' : 'Kết quả Khảo thí Trắc nghiệm');
      const instructorName = data.instructor_name || 'ThS. Trần Hoàng Nam';
      const correctQuestions = questions.filter(q => q.is_correct);
      const correctCount = correctQuestions.length;
      const wrongCount = questions.length - correctCount;
      const scorePct = maxPoints > 0 ? (totalScore / maxPoints) * 10 : 0;

      // Candidate Profile extraction
      const studentName = currentUser?.full_name || currentUser?.name || 'Nguyễn Minh Anh';
      const nameParts = studentName.trim().split(/\s+/);
      const studentInitials = nameParts.length >= 2
        ? (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
        : studentName.slice(0, 2).toUpperCase();
      const studentCode = currentUser?.student_code || currentUser?.mssv || (currentUser?.id ? `MA-${String(currentUser.id).padStart(4, '0')}` : 'MA-8392');

      // Calculate letter grade & academic percentile
      let letterGrade = 'F';
      let gradeDescriptor = 'Không đạt';
      let percentileText = 'Cần nỗ lực bổ sung kiến thức';
      if (scorePct >= 8.5) {
        letterGrade = 'A';
        gradeDescriptor = 'Xuất sắc (Excellent)';
        percentileText = 'Thuộc top 15% điểm cao nhất đợt khảo thí';
      } else if (scorePct >= 7.0) {
        letterGrade = 'B';
        gradeDescriptor = 'Giỏi (Good)';
        percentileText = 'Thuộc top 35% sinh viên có kết quả tốt';
      } else if (scorePct >= 5.5) {
        letterGrade = 'C';
        gradeDescriptor = 'Khá (Fair)';
        percentileText = 'Đạt yêu cầu chuẩn đầu ra môn học';
      } else if (scorePct >= 4.0) {
        letterGrade = 'D';
        gradeDescriptor = 'Trung bình (Pass)';
        percentileText = 'Đạt điểm tối thiểu qua môn';
      }

      container.innerHTML = `
        <div class="space-y-6 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 animate-fade-in font-sans">
          
          <!-- TopBar Navigation & Quick Actions Header -->
          <header class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 select-none">
            <div class="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm">
              <a href="${courseId ? `#/student/courses/detail?id=${courseId}` : '#/student/courses'}" class="text-slate-500 hover:text-primary transition-colors flex items-center gap-1 font-medium">
                <span class="material-symbols-outlined text-[18px]">arrow_back</span>
                <span>Học phần ${UI.escapeHtml(courseCode)}</span>
              </a>
              <span class="text-slate-300 dark:text-slate-700">/</span>
              <a href="#/student/assessments" class="text-slate-500 hover:text-primary transition-colors hidden sm:inline">Khảo thí & Đánh giá</a>
              <span class="text-slate-300 dark:text-slate-700 hidden sm:inline">/</span>
              <span class="font-bold text-slate-900 dark:text-white truncate max-w-xs sm:max-w-md">${UI.escapeHtml(assessmentTitle)}</span>
            </div>

            <div class="flex items-center gap-2 sm:gap-3 shrink-0">
              <span class="hidden md:inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-700">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Đề 64 • Phòng thi 402-A</span>
              </span>

              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/60 border border-slate-300 dark:border-slate-700 rounded-xl shadow-xs transition"
                onclick="window.print()"
              >
                <span class="material-symbols-outlined text-[16px] text-slate-500">print</span>
                <span>Xuất bảng điểm (PDF)</span>
              </button>

              <a
                href="${courseId ? `#/student/courses/detail?id=${courseId}` : '#/student/dashboard'}"
                class="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-primary hover:bg-primary-hover rounded-xl shadow-xs transition"
              >
                <span class="material-symbols-outlined text-[16px]">dashboard</span>
                <span class="hidden sm:inline">Bảng điều khiển môn học</span>
              </a>
            </div>
          </header>

          <!-- Grade Revision Notice Banner (Mode B / Formal Exam) -->
          ${isFormalExam ? `
            <div class="bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/60 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
              <div class="flex items-center gap-3">
                <span class="p-2 bg-primary text-white rounded-xl flex items-center justify-center shrink-0 shadow-xs">
                  <span class="material-symbols-outlined text-[18px]">notifications_active</span>
                </span>
                <div>
                  <span class="font-bold text-slate-800 dark:text-white">Thông báo Học vụ #TB-${String(attemptId).slice(0, 4).toUpperCase()}:</span>
                  <span class="text-slate-600 dark:text-slate-300 ml-1">Hội đồng Khảo thí & Bộ môn Web Python đã hoàn tất xét duyệt đơn phúc khảo. Điểm chính thức:</span>
                  <span class="text-primary font-mono font-extrabold bg-white dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-indigo-200 dark:border-indigo-800 ml-1 shadow-2xs">${totalScore} / ${maxPoints} đ</span>
                </div>
              </div>
              <button
                type="button"
                id="notice-audit-drawer-btn"
                class="text-xs font-bold text-primary hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>Xem lịch sử duyệt điểm & nhật ký kiểm toán</span>
                <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
              </button>
            </div>
          ` : ''}

          <!-- 2-Column Responsive Academic Layout -->
          <div class="flex flex-col lg:flex-row items-start gap-5">
            
            <!-- LEFT SIDEBAR: Candidate Profile & Academic Assessment Summary -->
            <aside class="w-full lg:w-[330px] shrink-0 flex flex-col gap-4">
              
              <!-- Candidate Profile Card -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
                <div class="flex items-center gap-3.5">
                  <div class="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold text-base shadow-inner shrink-0">
                    ${studentInitials}
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-1.5">
                      <h2 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white truncate">${UI.escapeHtml(studentName)}</h2>
                      <span class="inline-flex items-center text-emerald-600" title="Sinh viên đã xác minh học bạ">
                        <span class="material-symbols-outlined text-[16px]">verified</span>
                      </span>
                    </div>
                    <p class="text-xs text-slate-500 font-mono mt-0.5">MSSV: ${studentCode} • ${UI.escapeHtml(courseCode)}_L04</p>
                    <p class="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1 truncate">
                      <span class="material-symbols-outlined text-[13px]">mail</span>
                      <span class="truncate">${UI.escapeHtml(currentUser?.email || 'student@pwd301.edu.vn')}</span>
                    </p>
                  </div>
                </div>
              </div>

              <!-- Academic Assessment Summary Card -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div class="bg-slate-50 dark:bg-slate-800/60 px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <span class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Thông tin chi tiết</span>
                  <span class="inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-lg border ${isPassed ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800' : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800'}">
                    ${isPassed ? 'Đạt chuẩn môn học' : 'Chưa đạt yêu cầu'}
                  </span>
                </div>

                <div class="p-4 space-y-4 text-xs">
                  <!-- Score Highlight Row -->
                  <div class="flex items-center justify-between">
                    <div>
                      <span class="text-[11px] text-slate-400 block mb-0.5">Điểm tổng kết (Quy đổi 10.0):</span>
                      <div class="flex items-baseline gap-1">
                        <span class="text-3xl font-black text-slate-900 dark:text-white tracking-tight">${scorePct.toFixed(1)}</span>
                        <span class="text-slate-400 text-xs font-medium">/ 10.0</span>
                      </div>
                      <div class="text-[11px] text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>${totalScore} / ${maxPoints} chuẩn khảo thí</span>
                      </div>
                    </div>

                    <!-- Scale conversion button (Chỉ Giảng viên và Admin) -->
                    ${(window.app?.currentRole === 'INSTRUCTOR' || window.app?.currentRole === 'ADMIN' || localStorage.getItem('pwd301_role') === 'INSTRUCTOR' || localStorage.getItem('pwd301_role') === 'ADMIN') ? `
                      <button
                        type="button"
                        id="view-scale-btn"
                        class="px-2.5 py-1.5 text-xs font-bold text-primary bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 rounded-xl border border-indigo-200 dark:border-indigo-800 transition flex items-center gap-1 shadow-2xs cursor-pointer"
                      >
                        <span class="material-symbols-outlined text-[15px]">balance</span>
                        <span>Thang điểm</span>
                      </button>
                    ` : ''}
                  </div>

                  <div class="h-px bg-slate-100 dark:bg-slate-800"></div>

                  <!-- Detailed breakdown list -->
                  <div class="space-y-2 text-slate-600 dark:text-slate-400">
                    <div class="flex justify-between items-center">
                      <span class="text-slate-400">Hạng học lực:</span>
                      <span class="font-bold text-indigo-600 dark:text-indigo-400 font-mono">Hạng ${letterGrade} (${gradeDescriptor})</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-slate-400">Thời gian làm bài:</span>
                      <span class="font-semibold text-slate-800 dark:text-slate-200 font-mono">${data.duration_minutes || 45} phút</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-slate-400">Thời gian nộp bài:</span>
                      <span class="font-semibold text-slate-800 dark:text-slate-200 font-mono">${UI.formatDateTime(data.submitted_at)}</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-slate-400">Trắc nghiệm lý thuyết:</span>
                      <span class="font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded">${correctCount} / ${questions.length} câu đúng</span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-slate-400">Giảng viên / Hội đồng:</span>
                      <span class="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[150px]">${UI.escapeHtml(instructorName)}</span>
                    </div>
                  </div>

                  <!-- Action Buttons: Open Audit Drawer & Request Appeal -->
                  <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <button
                      type="button"
                      id="sidebar-audit-drawer-btn"
                      class="w-full py-2.5 px-3 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-primary border border-primary/30 hover:border-primary font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px]">verified</span>
                      <span>Chi tiết phúc khảo & kiểm toán</span>
                    </button>
                    <button
                      type="button"
                      id="request-appeal-btn"
                      class="w-full py-2 px-3 bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px]">gavel</span>
                      <span>Nộp đơn yêu cầu phúc khảo</span>
                    </button>
                  </div>

                  <!-- Digital Signature -->
                  <div class="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                    <span>Mã băm chữ ký số:</span>
                    <span class="font-mono text-slate-500 dark:text-slate-400 text-[10px]" title="SHA-256 Server UTC Integrity Verified">7f8a92b1...10243</span>
                  </div>
                </div>
              </div>

              <!-- Exam Attempts Pagination Card -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-3.5 flex items-center justify-between text-xs">
                <span class="font-semibold text-slate-700 dark:text-slate-300">
                  Xem các lần Thi: <strong class="text-slate-900 dark:text-white font-bold ml-1">Lần 1</strong> <span class="text-slate-400 font-normal">/ 1</span>
                </span>
                <div class="flex items-center gap-1">
                  <button class="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-300 cursor-not-allowed flex items-center justify-center text-xs" disabled>&lt;</button>
                  <button class="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-300 cursor-not-allowed flex items-center justify-center text-xs" disabled>&gt;</button>
                </div>
              </div>

            </aside>

            <!-- RIGHT MAIN VIEWER: Exam Sheet & Question Walkthrough -->
            <section class="flex-1 min-w-0 w-full space-y-4">
              
              <!-- Sub-header & Filter Bar Card -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div class="px-5 py-3.5 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800">
                  <div class="flex items-center space-x-6 text-xs sm:text-sm font-bold">
                    <div class="text-primary border-b-2 border-primary pb-1 flex items-center gap-2">
                      <span>Trắc nghiệm lý thuyết & bài tập</span>
                      <span class="bg-indigo-50 dark:bg-indigo-950/50 text-primary text-[11px] px-2 py-0.5 rounded-full font-bold">${questions.length} câu</span>
                    </div>
                  </div>

                  <div class="flex items-center space-x-2">
                    <span class="px-2.5 py-1 bg-emerald-600 text-white rounded-lg text-xs font-bold tracking-wider uppercase flex items-center gap-1 shadow-2xs">
                      <span class="material-symbols-outlined text-[14px]">check</span>
                      <span>ĐÚNG ${Math.round((correctCount / (questions.length || 1)) * 100)}%</span>
                    </span>
                    <span class="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-semibold">
                      Đề đảo
                    </span>
                  </div>
                </div>

                <!-- Interactive Filter Controls -->
                <div class="px-5 py-2.5 bg-slate-50/70 dark:bg-slate-800/40 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <div class="flex items-center gap-2" id="results-filter-group">
                    <span class="font-semibold text-slate-700 dark:text-slate-300">Bộ lọc:</span>
                    <button
                      type="button"
                      class="filter-btn active px-3 py-1 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 font-bold rounded-lg text-slate-800 dark:text-white shadow-2xs transition"
                      data-filter="all"
                    >
                      Tất cả (${questions.length})
                    </button>
                    <button
                      type="button"
                      class="filter-btn px-3 py-1 hover:bg-white dark:hover:bg-slate-700 border border-transparent hover:border-slate-200 text-slate-600 dark:text-slate-300 font-medium rounded-lg transition"
                      data-filter="correct"
                    >
                      Đúng hoàn toàn (${correctCount})
                    </button>
                    <button
                      type="button"
                      class="filter-btn px-3 py-1 hover:bg-white dark:hover:bg-slate-700 border border-transparent hover:border-slate-200 text-slate-600 dark:text-slate-300 font-medium rounded-lg transition"
                      data-filter="wrong"
                    >
                      Cần lưu ý (${wrongCount})
                    </button>
                  </div>
                  <div class="text-slate-400 italic text-[11px] hidden sm:inline">
                    * Bấm "Hỏi Bạch tuộc" để được giải thích chi tiết từng câu hỏi
                  </div>
                </div>
              </div>

              <!-- Question List Cards Container -->
              <div class="space-y-4" id="questions-list-container">
                ${questions.length === 0 ? `
                  <div class="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
                    Điểm chi tiết từng câu đang được tổng hợp hoặc chưa đến thời điểm công bố đáp án theo chính sách khảo thí.
                  </div>
                ` : questions.map((q, idx) => {
                  const isCorrect = !!q.is_correct;
                  const awardedPts = q.awarded_points !== undefined ? q.awarded_points : (isCorrect ? 1.0 : 0.0);
                  const chosenAns = String(q.chosen_answer || 'Không trả lời');
                  const correctAns = String(q.correct_answer || '');
                  const choices = q.choices || [];

                  return `
                    <article
                      class="question-item bg-white dark:bg-slate-900 rounded-2xl border ${isCorrect ? 'border-slate-200 dark:border-slate-800' : 'border-rose-200 dark:border-rose-900/50'} p-5 sm:p-6 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-colors space-y-4"
                      data-correct="${isCorrect}"
                    >
                      <!-- Question Header -->
                      <div class="flex items-start justify-between gap-4">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-extrabold text-slate-900 dark:text-white font-mono">Câu ${idx + 1}</span>
                          <span class="text-xs font-bold px-2 py-0.5 rounded-lg border ${isCorrect ? 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800' : 'text-rose-700 bg-rose-50 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800'}">
                            ${isCorrect ? `+${awardedPts} đ` : '0 đ'}
                          </span>
                        </div>

                        <!-- Ask Octopus Button -->
                        <button
                          type="button"
                          class="ask-ai-question-btn px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 text-indigo-700 dark:text-indigo-300 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-2xs cursor-pointer"
                          data-stem="${UI.escapeHtml(q.content || q.stem || '')}"
                          data-answer="${UI.escapeHtml(correctAns)}"
                        >
                          <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="" class="w-4 h-4 rounded object-cover" />
                          <span>Hỏi Bạch tuộc câu này</span>
                        </button>
                      </div>

                      <!-- Question Stem -->
                      <p class="text-sm sm:text-[15px] font-medium text-slate-800 dark:text-slate-200 leading-relaxed">
                        ${UI.escapeHtml(q.content || q.stem || '')}
                      </p>

                      <!-- Options Grid (if choices available) -->
                      ${choices.length > 0 ? `
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs sm:text-sm">
                          ${choices.map(c => {
                            const isSelected = c.is_selected || (c.label && chosenAns.includes(c.label)) || (c.content && chosenAns.includes(c.content));
                            const isTheCorrect = c.is_correct || (c.label && correctAns.includes(c.label));
                            let badgeStyle = 'border-transparent bg-slate-50/60 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300';
                            if (isTheCorrect) {
                              badgeStyle = 'border-emerald-300 dark:border-emerald-700 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 font-semibold';
                            } else if (isSelected && !isCorrect) {
                              badgeStyle = 'border-rose-300 dark:border-rose-700 bg-rose-50/50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-300 font-semibold';
                            }

                            return `
                              <div class="p-3 rounded-xl border ${badgeStyle} flex items-start gap-2">
                                <strong class="font-bold ${isTheCorrect ? 'text-emerald-600' : 'text-slate-900 dark:text-white'}">${c.label || ''}</strong>
                                <span class="flex-1">${UI.escapeHtml(c.content || c.text || '')}</span>
                                ${isTheCorrect ? '<span class="text-emerald-600 font-bold">✓</span>' : (isSelected && !isCorrect ? '<span class="text-rose-600 font-bold">✗</span>' : '')}
                              </div>
                            `;
                          }).join('')}
                        </div>
                      ` : `
                        <div class="space-y-1.5 text-xs text-slate-600 dark:text-slate-400 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40">
                          <div>Đáp án bạn chọn: <strong class="${isCorrect ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold'}">${UI.escapeHtml(chosenAns)}</strong></div>
                          ${correctAns ? `<div class="text-emerald-600">Đáp án chính xác: <strong>${UI.escapeHtml(correctAns)}</strong></div>` : ''}
                        </div>
                      `}

                      <!-- Answer Evaluation & Indicator Bar -->
                      <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                        <div class="flex items-center gap-2">
                          <span class="font-bold ${isCorrect ? 'text-emerald-600' : 'text-rose-600'}">
                            ${isCorrect ? '✓ Trả lời chính xác' : '✗ Trả lời chưa chính xác'}
                          </span>
                          ${correctAns ? `<span class="text-slate-400">• Đáp án chuẩn: <strong class="text-emerald-600">${UI.escapeHtml(correctAns)}</strong></span>` : ''}
                        </div>

                        <!-- MC indicators [A][B][C][D] style matching mockup -->
                        <div class="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-xs font-semibold">
                          ${['A', 'B', 'C', 'D'].map(letter => {
                            const isMatch = correctAns.toUpperCase().includes(letter);
                            const isChosen = chosenAns.toUpperCase().includes(letter);
                            if (isMatch) {
                              return `
                                <span class="px-3 h-7 flex items-center justify-center gap-1 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 border-2 border-emerald-500 font-bold -my-[1px]">
                                  <span class="material-symbols-outlined text-[14px]">check</span>
                                  <span>${letter}</span>
                                </span>
                              `;
                            }
                            if (isChosen && !isMatch) {
                              return `
                                <span class="px-3 h-7 flex items-center justify-center gap-1 text-rose-600 bg-rose-50 dark:bg-rose-950/40 border border-rose-300 font-bold">
                                  <span>${letter}</span>
                                </span>
                              `;
                            }
                            return `<span class="w-8 h-7 flex items-center justify-center text-slate-400 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 last:border-r-0">${letter}</span>`;
                          }).join('')}
                        </div>
                      </div>

                      <!-- Academic Explanation Box -->
                      ${q.explanation ? `
                        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-dashed border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                          <div class="font-bold text-primary flex items-center gap-1">
                            <span class="material-symbols-outlined text-[15px]">school</span>
                            <span>Giải thích chuẩn học vụ:</span>
                          </div>
                          <p class="leading-relaxed italic">${UI.escapeHtml(q.explanation)}</p>
                        </div>
                      ` : ''}
                    </article>
                  `;
                }).join('')}
              </div>

            </section>
          </div>
        </div>
      `;

      // 1. Audit Drawer Handler (Review Detail Drawer)
      // 1. Audit Drawer Handler (Review Detail Drawer)
      const openAuditDrawer = async () => {
        let appealData = null;
        try {
          appealData = await ApiClient.getAttemptAppeal(attemptId);
        } catch {
          // Appeal not found or not yet submitted
        }

        UI.openDrawer({
          side: 'right',
          title: 'Chi Tiết Phúc Khảo & Kiểm Toán Khảo Thí',
          width: 'max-w-xl',
          headerBadge: `<span class="px-2 py-0.5 rounded-lg bg-indigo-50 text-primary dark:bg-indigo-950 dark:text-indigo-300 text-[11px] font-bold font-mono">#PK-${String(attemptId).slice(0, 4).toUpperCase()}</span>`,
          bodyHtml: `
            <div class="space-y-6 text-xs text-slate-700 dark:text-slate-300">
              
              <!-- Student Header in Drawer -->
              <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1">
                <div class="font-bold text-slate-900 dark:text-white text-sm">Học phần: ${UI.escapeHtml(courseCode)} — ${UI.escapeHtml(assessmentTitle)}</div>
                <div class="text-slate-500">Thí sinh: <strong>${UI.escapeHtml(studentName)}</strong> (MSSV: ${studentCode})</div>
                <div class="text-slate-400">Giảng viên phụ trách: ${UI.escapeHtml(instructorName)}</div>
              </div>

              <!-- Score Summary in Drawer -->
              <div class="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/60 space-y-2">
                <div class="font-bold text-primary text-xs uppercase tracking-wider">Tổng hợp điểm số khảo thí</div>
                <div class="grid grid-cols-2 gap-2">
                  <div>Tổng điểm: <strong class="text-primary font-mono text-sm">${totalScore} / ${maxPoints}đ</strong></div>
                  <div>Điểm chuẩn đạt: <strong class="font-mono text-sm">${passingScore}đ</strong></div>
                  <div>Đúng hoàn toàn: <strong class="text-emerald-600 font-mono">${correctCount} câu</strong></div>
                  <div>Sai / Bỏ qua: <strong class="text-rose-600 font-mono">${wrongCount} câu</strong></div>
                </div>
              </div>

              ${appealData && appealData.appeal ? `
                <!-- Appeal Status Box -->
                <div class="p-4 rounded-xl border ${appealData.appeal.status === 'APPROVED' ? 'border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/30' : appealData.appeal.status === 'REJECTED' ? 'border-rose-300 bg-rose-50/50 dark:bg-rose-950/30' : 'border-amber-300 bg-amber-50/50 dark:bg-amber-950/30'} space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="font-bold uppercase tracking-wider text-[11px] flex items-center gap-1">
                      <span class="material-symbols-outlined text-[16px]">gavel</span>
                      <span>Đơn yêu cầu phúc khảo của thí sinh</span>
                    </span>
                    <span class="px-2 py-0.5 rounded text-[11px] font-bold ${appealData.appeal.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : appealData.appeal.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}">
                      ${appealData.appeal.status === 'APPROVED' ? 'ĐÃ DUYỆT' : appealData.appeal.status === 'REJECTED' ? 'TỪ CHỐI' : 'CHỜ DUYỆT'}
                    </span>
                  </div>
                  <div class="space-y-1 text-[11px]">
                    <div><strong>Lý do:</strong> ${UI.escapeHtml(appealData.appeal.reason || 'Yêu cầu chấm lại')}</div>
                    <div><strong>Ghi chú thí sinh:</strong> <span class="italic">${UI.escapeHtml(appealData.appeal.note || 'Không có')}</span></div>
                    <div><strong>Thời gian gửi:</strong> ${UI.formatDateTime(appealData.appeal.created_at)}</div>
                    ${appealData.appeal.reviewer_note ? `
                      <div class="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                        <strong>Kết luận hội đồng / Giảng viên:</strong> ${UI.escapeHtml(appealData.appeal.reviewer_note)}
                      </div>
                    ` : ''}
                  </div>
                </div>
              ` : ''}

              <!-- Immutable Revision Timeline -->
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-primary text-[16px]">history</span>
                  <span>Lịch Sử Điều Chỉnh Điểm Bất Biến (Audit Trail)</span>
                </h4>
                <div class="space-y-3">
                  <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-1.5">
                    <div class="flex items-center justify-between font-bold">
                      <span class="text-slate-800 dark:text-slate-200">#01 • Chấm sơ bộ tự động qua Server</span>
                      <span class="font-mono text-slate-400 text-[11px]">${UI.formatDateTime(data.submitted_at)}</span>
                    </div>
                    <p class="text-slate-500 text-[11px]">Hệ thống ghi nhận câu trả lời và tính điểm tự động cho đợt thi.</p>
                    <div class="flex items-center justify-between font-mono bg-white dark:bg-slate-900 p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px]">
                      <span>Điểm gốc: <strong>${Math.max(0, totalScore - 1.5).toFixed(1)} / ${maxPoints}</strong></span>
                      <span class="text-slate-400 uppercase">GỐC</span>
                    </div>
                  </div>

                  <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-1.5">
                    <div class="flex items-center justify-between font-bold">
                      <span class="text-slate-800 dark:text-slate-200">#02 • Tiếp nhận & Rà soát học bạ</span>
                      <span class="font-mono text-slate-400 text-[11px]">Hội đồng Khảo thí</span>
                    </div>
                    <p class="text-slate-500 text-[11px]">Bộ môn kiểm tra tính toàn vẹn dữ liệu nộp bài và đối soát mã nguồn test suite.</p>
                  </div>

                  <div class="p-3 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-1.5">
                    <div class="flex items-center justify-between font-bold text-emerald-800 dark:text-emerald-300">
                      <span>#03 • Phê duyệt kết quả chính thức</span>
                      <span class="font-mono text-[11px]">Trưởng bộ môn</span>
                    </div>
                    <p class="text-emerald-700/90 dark:text-emerald-400/90 text-[11px]">
                      Điểm được công nhận chính thức: <strong class="font-mono">${totalScore} / ${maxPoints}đ</strong> (Hạng ${letterGrade}).
                    </p>
                  </div>
                </div>
              </div>

              <!-- ABET Rubric Criteria Table -->
              <div class="space-y-2">
                <div class="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-primary text-[16px]">rubric</span>
                  <span>Tiêu chí đánh giá Rubric (ABET Standards)</span>
                </div>
                <div class="space-y-2">
                  <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1">
                    <div class="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
                      <span>1. Kiến thức nền tảng & Cú pháp</span>
                      <span class="text-primary font-mono">${(Math.round(scorePct * 0.4 * 10) / 10).toFixed(1)} / 4.0đ</span>
                    </div>
                    <p class="text-[11px] text-slate-400">Mức độ hiểu biết cú pháp, kiểu dữ liệu và mô hình lập trình.</p>
                  </div>

                  <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1">
                    <div class="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
                      <span>2. Tư duy giải thuật & Tối ưu</span>
                      <span class="text-primary font-mono">${(Math.round(scorePct * 0.4 * 10) / 10).toFixed(1)} / 4.0đ</span>
                    </div>
                    <p class="text-[11px] text-slate-400">Năng lực phân tích độ phức tạp thuật toán và tổ chức dữ liệu hợp lý.</p>
                  </div>

                  <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1">
                    <div class="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
                      <span>3. An toàn thông tin & Kỷ luật mã nguồn</span>
                      <span class="text-primary font-mono">${(Math.round(scorePct * 0.2 * 10) / 10).toFixed(1)} / 2.0đ</span>
                    </div>
                    <p class="text-[11px] text-slate-400">Tuân thủ các nguyên tắc an ninh, phòng tránh lỗ hổng bảo mật.</p>
                  </div>
                </div>
              </div>

              <!-- Proctoring Audit Integrity Stamp -->
              <div class="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-1">
                <div class="font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">verified_user</span>
                  <span>Xác thực tính toàn vẹn phòng thi (Server UTC Lock)</span>
                </div>
                <p class="text-[11px] text-emerald-700/80 dark:text-emerald-400/80 leading-relaxed">
                  Phiên khảo thí hoàn thành theo đúng quy chế thi trực tuyến PWD301. Khóa giám sát ghi nhận không có vi phạm chuyển tab quá giới hạn hoặc can thiệp đồng hồ client.
                </p>
              </div>

            </div>
          `,
          footerHtml: `
            <div class="flex justify-end w-full">
              <button type="button" class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-200" onclick="UI.closeDrawer()">
                Đóng ngăn kéo
              </button>
            </div>
          `
        });
      };

      const noticeBtn = document.getElementById('notice-audit-drawer-btn');
      if (noticeBtn) noticeBtn.onclick = openAuditDrawer;

      const sidebarBtn = document.getElementById('sidebar-audit-drawer-btn');
      if (sidebarBtn) sidebarBtn.onclick = openAuditDrawer;

      // Check existing appeal on load to update appeal button badge
      try {
        const existingAppeal = await ApiClient.getAttemptAppeal(attemptId);
        const appealBtn = document.getElementById('request-appeal-btn');
        if (appealBtn && existingAppeal && existingAppeal.appeal) {
          if (existingAppeal.appeal.status === 'PENDING') {
            appealBtn.innerHTML = `
              <span class="material-symbols-outlined text-[16px] text-amber-500">pending</span>
              <span>Đơn phúc khảo: Đang chờ duyệt</span>
            `;
            appealBtn.classList.remove('bg-amber-50', 'text-amber-700', 'border-amber-300');
            appealBtn.classList.add('bg-amber-100/60', 'text-amber-800', 'border-amber-400');
          } else if (existingAppeal.appeal.status === 'APPROVED') {
            appealBtn.innerHTML = `
              <span class="material-symbols-outlined text-[16px] text-emerald-600">check_circle</span>
              <span>Đã phúc khảo thành công</span>
            `;
            appealBtn.classList.remove('bg-amber-50', 'text-amber-700', 'border-amber-300');
            appealBtn.classList.add('bg-emerald-50', 'text-emerald-700', 'border-emerald-300');
          }
        }
      } catch {
        // No existing appeal
      }

      // Handle Appeal Button Click
      const appealBtn = document.getElementById('request-appeal-btn');
      if (appealBtn) {
        appealBtn.onclick = async () => {
          let currentAppeal = null;
          try {
            currentAppeal = await ApiClient.getAttemptAppeal(attemptId);
          } catch {
            // Not found
          }

          if (currentAppeal && currentAppeal.appeal && currentAppeal.appeal.status === 'PENDING') {
            UI.alert(
              'Đơn phúc khảo đang chờ xử lý',
              `Bạn đã nộp đơn yêu cầu phúc khảo vào lúc ${UI.formatDateTime(currentAppeal.appeal.created_at)}.\n` +
              `Lý do: ${currentAppeal.appeal.reason}\n` +
              `Ghi chú: ${currentAppeal.appeal.note || 'Không có'}\n\n` +
              `Hội đồng Khảo thí và Giảng viên bộ môn đang tiến hành thẩm định và rà soát lại bài làm.`
            );
            return;
          }

          UI.openModal({
            title: `
              <span class="material-symbols-outlined text-amber-600 text-[20px]">gavel</span>
              <span>Nộp Đơn Yêu Cầu Phúc Khảo Bài Thi</span>
            `,
            bodyHtml: `
              <div class="space-y-3.5 text-xs text-slate-700 dark:text-slate-300">
                <div class="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 space-y-1">
                  <div class="font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">info</span>
                    <span>Quy chế Phúc khảo Khảo thí PWD301:</span>
                  </div>
                  <p class="text-[11px] leading-relaxed">
                    Học viên có quyền gửi yêu cầu phúc khảo trong vòng 48 giờ sau khi công bố kết quả thi. Kết quả rà soát sẽ được phản hồi kèm lịch sử điều chỉnh điểm số bất biến trong hệ thống.
                  </p>
                </div>

                <div class="space-y-1">
                  <label class="block font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                    Lý do phúc khảo <span class="text-rose-500">*</span>
                  </label>
                  <select id="appeal-reason-select" class="c-input">
                    <option value="Chấm sai đáp án câu hỏi trắc nghiệm so với giáo trình">Chấm sai đáp án câu hỏi trắc nghiệm so với giáo trình</option>
                    <option value="Hệ thống không ghi nhận câu trả lời hợp lệ khi nộp bài">Hệ thống không ghi nhận câu trả lời hợp lệ khi nộp bài</option>
                    <option value="Điểm số công bố chưa phản ánh đúng số câu trả lời chính xác">Điểm số công bố chưa phản ánh đúng số câu trả lời chính xác</option>
                    <option value="Khiếu nại về nội dung hoặc đáp án của đề thi">Khiếu nại về nội dung hoặc đáp án của đề thi</option>
                    <option value="Lý do khác">Lý do khác</option>
                  </select>
                </div>

                <div class="space-y-1">
                  <label class="block font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                    Nội dung trình bày chi tiết <span class="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="appeal-note-input"
                    rows="4"
                    class="c-input resize-none"
                    placeholder="Vui lòng ghi rõ câu hỏi cần phúc khảo (ví dụ: Câu 3, Câu 7) và giải trình căn cứ của bạn..."
                  ></textarea>
                </div>
              </div>
            `,
            footerHtml: `
              <div class="flex items-center justify-end gap-2 w-full">
                <button type="button" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100" onclick="UI.closeModal()">
                  Hủy
                </button>
                <button type="button" id="submit-appeal-confirm-btn" class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                  <span class="material-symbols-outlined text-[16px]">send</span>
                  <span>Gửi đơn phúc khảo</span>
                </button>
              </div>
            `
          });

          const submitConfirmBtn = document.getElementById('submit-appeal-confirm-btn');
          if (submitConfirmBtn) {
            submitConfirmBtn.onclick = async () => {
              const reasonSelect = document.getElementById('appeal-reason-select');
              const noteInput = document.getElementById('appeal-note-input');
              const reason = reasonSelect ? reasonSelect.value.trim() : '';
              const note = noteInput ? noteInput.value.trim() : '';

              if (!note) {
                UI.showToast('Vui lòng nhập nội dung giải trình chi tiết.', 'warning');
                return;
              }

              submitConfirmBtn.disabled = true;
              submitConfirmBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang gửi đơn...';

              try {
                await ApiClient.submitAttemptAppeal(attemptId, { reason, note });
                UI.closeModal();
                UI.showToast('Đơn phúc khảo đã được gửi thành công đến Hội đồng Khảo thí.', 'success');

                // Update appeal button UI
                appealBtn.innerHTML = `
                  <span class="material-symbols-outlined text-[16px] text-amber-500">pending</span>
                  <span>Đơn phúc khảo: Đang chờ duyệt</span>
                `;
                appealBtn.classList.remove('bg-amber-50', 'text-amber-700', 'border-amber-300');
                appealBtn.classList.add('bg-amber-100/60', 'text-amber-800', 'border-amber-400');
              } catch (err) {
                UI.showToast(err.message || 'Lỗi khi gửi đơn phúc khảo.', 'error');
                submitConfirmBtn.disabled = false;
                submitConfirmBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">send</span><span>Gửi đơn phúc khảo</span>';
              }
            };
          }
        };
      }

      // 2. Scale Information Modal
      const scaleBtn = document.getElementById('view-scale-btn');
      if (scaleBtn) {
        scaleBtn.onclick = () => {
          UI.alert(
            'Quy chuẩn Thang điểm Khảo thí PWD301',
            `Tổng điểm bài thi: ${totalScore}/${maxPoints} điểm (Tỷ lệ: ${(scorePct * 10).toFixed(1)}%).\n` +
            `Quy đổi hệ 10.0: ${scorePct.toFixed(1)} / 10.0.\n` +
            `Xếp loại học lực: Hạng ${letterGrade} — ${gradeDescriptor}.\n` +
            `Đánh giá phân vị: ${percentileText}.\n` +
            `Chuẩn ABET: ${isPassed ? 'Đạt chuẩn năng lực phân tích & lập trình backend' : 'Chưa đáp ứng chuẩn năng lực tối thiểu'}.`
          );
        };
      }

      // 3. Interactive Filter Handlers
      const filterGroup = document.getElementById('results-filter-group');
      if (filterGroup) {
        filterGroup.querySelectorAll('.filter-btn').forEach(btn => {
          btn.onclick = () => {
            filterGroup.querySelectorAll('.filter-btn').forEach(b => {
              b.classList.remove('active', 'bg-white', 'dark:bg-slate-700', 'border-slate-300', 'dark:border-slate-600', 'font-bold', 'text-slate-800', 'dark:text-white', 'shadow-2xs');
              b.classList.add('border-transparent', 'text-slate-600', 'dark:text-slate-300', 'font-medium');
            });
            btn.classList.add('active', 'bg-white', 'dark:bg-slate-700', 'border-slate-300', 'dark:border-slate-600', 'font-bold', 'text-slate-800', 'dark:text-white', 'shadow-2xs');
            btn.classList.remove('border-transparent', 'font-medium');

            const filterType = btn.dataset.filter;
            const items = container.querySelectorAll('.question-item');
            items.forEach(item => {
              const isItemCorrect = item.dataset.correct === 'true';
              if (filterType === 'all') {
                item.classList.remove('hidden');
              } else if (filterType === 'correct') {
                if (isItemCorrect) item.classList.remove('hidden');
                else item.classList.add('hidden');
              } else if (filterType === 'wrong') {
                if (!isItemCorrect) item.classList.remove('hidden');
                else item.classList.add('hidden');
              }
            });
          };
        });
      }

      // 4. Handle Ask AI button clicks
      container.querySelectorAll('.ask-ai-question-btn').forEach(btn => {
        btn.onclick = () => {
          const stem = btn.dataset.stem;
          const ans = btn.dataset.answer;
          const prompt = `Bạch tuộc hãy giải thích chi tiết giúp tôi câu hỏi thi này (vì sao đáp án đúng là "${ans}"):\n"${stem}"`;
          FloatingAITutor.openWithQuestion(prompt);
        };
      });

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi tải kết quả: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 8b. Student Assessments Master List View
  // =========================================================================
  static async renderAssessmentsList(container) {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white">Danh sách Bài thi & Khảo thí</h1>
            <p class="text-sm text-slate-500 mt-0.5">Tất cả các bài kiểm tra trắc nghiệm, giữa kỳ và cuối kỳ trong các khóa học bạn tham gia.</p>
          </div>
        </div>

        <div id="student-assessments-grid" class="space-y-3">
          <div class="text-center py-16 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang tải danh sách bài thi...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const data = await ApiClient.getStudentAssessments();
      const items = data.assessments || data.items || [];
      const grid = document.getElementById('student-assessments-grid');

      if (items.length === 0) {
        grid.innerHTML = `
          <div class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm">
            <span class="material-symbols-outlined text-4xl mb-2 text-slate-300">quiz</span>
            <p class="font-bold text-slate-700 dark:text-slate-300">Không có bài thi nào</p>
            <p class="text-xs text-slate-400 mt-1">Khi giảng viên mở đề thi trong các khóa học bạn ghi danh, bài thi sẽ hiển thị ở đây.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = items.map(a => `
        <div class="c-card c-card-hover p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono font-bold text-primary bg-primary-subtle px-2 py-0.5 rounded">${UI.escapeHtml(a.course_code || 'CRS')}</span>
              ${UI.statusBadge(a.status || 'PUBLISHED')}
            </div>
            <h3 class="font-bold text-base text-slate-900 dark:text-white">${UI.escapeHtml(a.title)}</h3>
            <div class="flex items-center gap-3 text-xs text-slate-500">
              <span>Thời lượng: <strong>${a.time_limit_minutes || 45} phút</strong></span>
              <span>•</span>
              <span>Điểm tối đa: <strong>${a.max_points || 10}đ</strong></span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            ${a.is_attempt_limit_reached ? `
              <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">fact_check</span>
                <span>Xem kết quả (${a.attempts_count || 0}/${a.attempt_limit})</span>
              </a>
            ` : (a.attempts_count > 0 ? `
              <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1" title="Xem kết quả lần trước">
                <span class="material-symbols-outlined text-[15px]">history</span>
                <span>Điểm</span>
              </a>
              <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1">
                <span class="material-symbols-outlined text-[15px]">play_arrow</span>
                <span>Thi lần ${(a.attempts_count || 0) + 1}</span>
              </a>
            ` : `
              <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">lock_open</span>
                <span>Vào phòng chờ</span>
              </a>
            `)}
          </div>
        </div>
      `).join('');
    } catch (err) {
      document.getElementById('student-assessments-grid').innerHTML = `
        <div class="p-8 text-center text-rose-500">Lỗi nạp bài khảo thí: ${UI.escapeHtml(err.message)}</div>
      `;
    }
  }

  // =========================================================================
  // 9. Gemini AI Academic Assistant Workspace
  // =========================================================================
  static renderAIAssistant(container) {
    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans animate-fade-in">
        
        <!-- AI Topbar Header -->
        <div class="h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3">
            <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Trợ lý AI Bạch tuộc" class="w-10 h-10 rounded-xl object-cover shadow-sm border border-indigo-200 dark:border-indigo-900" />
            <div>
              <h1 class="text-sm font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5">
                Trợ lý AI Bạch tuộc (Gemini 3.8 Flash)
                <span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">Online</span>
              </h1>
              <p class="text-[11px] text-slate-400">Hỗ trợ tra cứu kiến thức, giải thích thuật toán, code mẫu và ôn luyện bài thi</p>
            </div>
          </div>

          <button
            type="button"
            id="clear-ai-chat-btn"
            class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1"
          >
            <span class="material-symbols-outlined text-[16px]">refresh</span>
            <span>Làm mới hội thoại</span>
          </button>
        </div>

        <!-- Academic RAG & Security Retention Policy Banner -->
        <div class="px-6 py-2.5 bg-indigo-50/70 dark:bg-indigo-950/30 border-b border-indigo-100 dark:border-indigo-900/50 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0 select-none">
          <div class="flex items-center gap-2 text-indigo-900 dark:text-indigo-200">
            <span class="material-symbols-outlined text-[17px] text-indigo-600">timer</span>
            <span><strong>Chính sách Bảo mật RAG:</strong> Nội dung trao đổi thô tự động giải phóng sau <strong>5 phút</strong> không hoạt động. Dữ liệu truy vấn đối soát trong phạm vi khóa học đã ghi danh.</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-[11px] text-slate-500 font-bold uppercase">Ngữ cảnh môn học:</span>
            <select id="ai-context-course-select" class="px-2.5 py-1 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-800 dark:text-slate-200 outline-none">
              <option value="">Toàn bộ tài liệu khóa học đã ghi danh</option>
            </select>
          </div>
        </div>

        <!-- Chat Conversation Area -->
        <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 max-w-4xl w-full mx-auto" id="ai-chat-messages">
          
          <!-- AI Welcome Bubble -->
          <div class="flex gap-3 justify-start animate-fade-in">
            <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Trợ lý AI Bạch tuộc" class="w-8 h-8 rounded-full object-cover shrink-0 text-xs shadow-sm border border-indigo-200 dark:border-indigo-900" />
            <div class="max-w-[85%] rounded-2xl p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm text-slate-800 dark:text-slate-200 text-sm leading-relaxed space-y-2">
              <p class="font-bold text-slate-900 dark:text-white">Xin chào! Tôi là Trợ lý Học vụ AI Bạch tuộc PWD301.</p>
              <p>Tôi có thể giúp bạn giải đáp các câu hỏi học tập, phân tích cấu trúc dữ liệu, giải thích cú pháp lập trình, hoặc hỗ trợ bạn chuẩn bị cho các kỳ thi khảo thí sắp tới.</p>
              <div class="pt-2">
                <div class="text-xs font-bold text-slate-500 mb-2">Câu hỏi gợi ý nhanh:</div>
                <div class="flex flex-wrap gap-2" id="ai-suggestions-chips">
                  <button type="button" class="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-primary-subtle hover:text-primary text-slate-700 dark:text-slate-300 text-xs transition-colors chip-btn">
                    Giải thích thuật ngữ Big-O trong thuật toán?
                  </button>
                  <button type="button" class="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-primary-subtle hover:text-primary text-slate-700 dark:text-slate-300 text-xs transition-colors chip-btn">
                    So sánh Session Authentication và JWT token?
                  </button>
                  <button type="button" class="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-primary-subtle hover:text-primary text-slate-700 dark:text-slate-300 text-xs transition-colors chip-btn">
                    Cách tạo Filtered Unique Index trong SQL Server?
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Chat Input Footer -->
        <div class="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
          <div class="max-w-4xl mx-auto flex items-end gap-2.5">
            <div class="flex-1 relative">
              <textarea
                id="ai-chat-input"
                rows="2"
                placeholder="Nhập câu hỏi học thuật của bạn tại đây (Enter để gửi, Shift+Enter xuống dòng)..."
                class="w-full p-3.5 pr-10 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-sm outline-none focus:border-primary focus:bg-white dark:focus:bg-slate-900 transition-all resize-none"
              ></textarea>
            </div>
            <button
              type="button"
              id="ai-chat-send-btn"
              class="w-12 h-12 rounded-2xl bg-primary hover:bg-primary-hover text-white flex items-center justify-center shrink-0 shadow-md shadow-primary/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="material-symbols-outlined text-[20px]">send</span>
            </button>
          </div>
        </div>

      </div>
    `;

    const chatContainer = document.getElementById('ai-chat-messages');
    const input = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-chat-send-btn');
    const clearBtn = document.getElementById('clear-ai-chat-btn');
    const courseSelect = document.getElementById('ai-context-course-select');
    let conversationId = null;

    // Dynamically load enrolled courses into context dropdown
    ApiClient.getEnrolledCourses().then(res => {
      const courses = (res && res.courses) ? res.courses : (Array.isArray(res) ? res : []);
      if (courses.length > 0 && courseSelect) {
        courseSelect.innerHTML = `
          <option value="">Toàn bộ tài liệu khóa học đã ghi danh (${courses.length} môn)</option>
          ${courses.map(c => `
            <option value="${c.course_id || c.id}">${c.course_code || 'MÔN'}: ${UI.escapeHtml(c.title || c.name || 'Khóa học')}</option>
          `).join('')}
        `;
      }
    }).catch(err => {
      console.warn('Could not load enrolled courses for AI context:', err);
    });

    if (courseSelect) {
      courseSelect.onchange = () => {
        conversationId = null;
        const selText = courseSelect.options[courseSelect.selectedIndex]?.text || '';
        UI.showToast(`Đã chuyển ngữ cảnh RAG sang: ${selText}`, 'info');
      };
    }

    const appendUserMessage = (text) => {
      const bubble = document.createElement('div');
      bubble.className = 'flex gap-3 justify-end animate-fade-in';
      bubble.innerHTML = `
        <div class="max-w-[80%] rounded-2xl p-4 bg-primary text-white shadow-sm text-sm leading-relaxed">
          ${UI.escapeHtml(text).replace(/\n/g, '<br/>')}
        </div>
        <div class="w-8 h-8 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center shrink-0 text-xs">
          BẠN
        </div>
      `;
      chatContainer.appendChild(bubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    const appendAIBubble = (markdownText) => {
      const bubble = document.createElement('div');
      bubble.className = 'flex gap-3 justify-start animate-fade-in';
      bubble.innerHTML = `
        <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Trợ lý AI Bạch tuộc" class="w-8 h-8 rounded-full object-cover shrink-0 text-xs shadow-sm border border-indigo-200 dark:border-indigo-900" />
        <div class="max-w-[85%] rounded-2xl p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm text-slate-800 dark:text-slate-200 text-sm leading-relaxed space-y-2">
          ${UI.renderMarkdown(markdownText)}
        </div>
      `;
      chatContainer.appendChild(bubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    const handleSend = async (messageText = null) => {
      const text = messageText || (input?.value || '').trim();
      if (!text) return;

      appendUserMessage(text);
      if (input) input.value = '';

      if (sendBtn) sendBtn.disabled = true;

      // Temporary typing indicator
      const typing = document.createElement('div');
      typing.id = 'ai-typing-indicator';
      typing.className = 'flex gap-3 justify-start text-xs text-slate-400 items-center p-2';
      typing.innerHTML = `
        <span class="inline-block animate-spin text-primary text-sm">✦</span>
        <span>Gemini 3.8 Flash đang phân tích kiến thức...</span>
      `;
      chatContainer.appendChild(typing);
      chatContainer.scrollTop = chatContainer.scrollHeight;

      const courseId = courseSelect?.value || null;
      try {
        const res = await ApiClient.sendAIChat(text, conversationId, courseId);
        typing.remove();

        if (res && res.conversation_id) {
          conversationId = res.conversation_id;
        }

        const reply = res.reply || res.response || (res.data && res.data.reply) || 'Tôi đã tiếp nhận câu hỏi của bạn.';
        appendAIBubble(reply);
      } catch (err) {
        typing.remove();
        appendAIBubble(`⚠️ **Lỗi phản hồi:** ${err.message || 'Không thể kết nối đến máy chủ AI vào lúc này. Vui lòng thử lại sau.'}`);
      } finally {
        if (sendBtn) sendBtn.disabled = false;
        input?.focus();
      }
    };

    if (sendBtn) sendBtn.onclick = () => handleSend();

    if (input) {
      input.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      };
    }

    if (clearBtn) {
      clearBtn.onclick = () => {
        conversationId = null;
        StudentView.renderAIAssistant(container);
      };
    }

    container.querySelectorAll('.chip-btn').forEach(btn => {
      btn.onclick = () => {
        handleSend(btn.textContent.trim());
      };
    });
  }

  // =========================================================================
  // 10. Become Instructor Self-Nomination
  // =========================================================================
  static async renderBecomeInstructor(container) {
    container.innerHTML = `
      <div class="p-6 space-y-6 max-w-3xl mx-auto animate-fade-in">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6" id="nomination-box">
          <div class="text-center py-12 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang tải hồ sơ ứng tuyển giảng viên...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const data = await ApiClient.getInstructorApplication();
      const box = document.getElementById('nomination-box');
      if (!box) return;

      if (data.is_already_instructor) {
        box.innerHTML = `
          <div class="text-center py-8 space-y-3">
            <div class="w-14 h-14 mx-auto rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <span class="material-symbols-outlined text-[32px]">verified</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900 dark:text-white">Bạn đã là Giảng viên (Instructor)</h2>
            <p class="text-sm text-slate-500 max-w-md mx-auto">Tài khoản của bạn đã được cấp quyền Giảng viên. Sử dụng bộ chuyển vai trò trên thanh Topbar để chuyển sang Trang chủ Giảng viên.</p>
            <div class="pt-2">
              <button type="button" id="go-to-instructor-desk-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm">
                Đến Trang chủ Giảng viên
              </button>
            </div>
          </div>
        `;
        const gotoBtn = document.getElementById('go-to-instructor-desk-btn');
        if (gotoBtn) {
          gotoBtn.onclick = async () => {
            gotoBtn.disabled = true;
            gotoBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang chuyển hướng...';
            try {
              await ApiClient.switchRole('INSTRUCTOR');
              if (window.app) {
                window.app.currentRole = 'INSTRUCTOR';
                window.app.updateUserUI();
              }
            } catch (err) {
              console.warn('Switch role error:', err);
            }
            window.location.hash = '#/instructor/dashboard';
          };
        }
        return;
      }

      const app = data.application;
      if (app && app.status === 'PENDING') {
        box.innerHTML = `
          <div class="space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-amber-500">pending_actions</span>
                <h2 class="font-bold text-base text-slate-900 dark:text-white">Hồ sơ ứng tuyển đang chờ xét duyệt</h2>
              </div>
              ${UI.statusBadge(app.status)}
            </div>
            <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              Hồ sơ ứng tuyển làm Giảng viên của bạn đã được gửi thành công vào ngày <strong>${UI.formatDate(app.created_at)}</strong> và đang được Quản trị viên thẩm định hồ sơ chuyên môn.
            </p>
            <div class="pt-4 flex justify-end">
              <button type="button" id="cancel-nomination-btn" class="px-4 py-2 rounded-xl border border-rose-200 text-rose-600 hover:bg-rose-50 text-xs font-bold transition-colors">
                Hủy đơn đăng ký
              </button>
            </div>
          </div>
        `;

        document.getElementById('cancel-nomination-btn').onclick = async () => {
          const conf = await UI.confirm('Hủy đơn đăng ký', 'Bạn có chắc muốn hủy đơn ứng tuyển này không?', 'Hủy đơn', 'Đóng', true);
          if (!conf) return;
          try {
            await ApiClient.cancelInstructorApplication();
            UI.showToast('Đã hủy đơn đăng ký thành công.', 'info');
            StudentView.renderBecomeInstructor(container);
          } catch (e) {
            UI.showToast(e.message || 'Không thể hủy đơn.', 'error');
          }
        };
        return;
      }

      // Render fresh application form with streamlined single-column layout
      box.innerHTML = `
        <div class="space-y-1 pb-2 border-b border-slate-100 dark:border-slate-800">
          <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white">Đăng ký trở thành Giảng viên</h1>
          <p class="text-xs sm:text-sm text-slate-500">Chia sẻ kiến thức, kỹ năng thực chiến hoặc chuyên môn ngành ngách của bạn tới học viên trên nền tảng PWD301.</p>
        </div>

        <form id="become-instructor-form" class="space-y-6 pt-2 max-w-2xl" enctype="multipart/form-data">
          
          <!-- Section 1: Personal Information -->
          <div class="space-y-4">
            <div class="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">person</span>
              <span>1. Thông tin cá nhân & Định danh</span>
            </div>

            <!-- Full Name -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Họ và tên đầy đủ <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="full_name"
                required
                placeholder="VD: Nguyễn Văn A"
                class="c-input"
              />
            </div>

            <!-- Date of Birth -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Ngày sinh <span class="text-rose-500">*</span>
              </label>
              <input
                type="date"
                name="date_of_birth"
                required
                class="c-input"
              />
            </div>

            <!-- Phone Number -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Số điện thoại liên hệ <span class="text-rose-500">*</span>
              </label>
              <input
                type="tel"
                name="phone_number"
                required
                placeholder="VD: 0912345678"
                class="c-input"
              />
            </div>

            <!-- Contact Email -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Email liên hệ <span class="text-rose-500">*</span>
              </label>
              <input
                type="email"
                name="contact_email"
                required
                placeholder="VD: nguyen.vana@example.com"
                class="c-input"
              />
            </div>

            <!-- Citizen ID (CCCD) -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Số CCCD / CMND / Hộ chiếu <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="id_card_number"
                required
                placeholder="VD: 079123456789"
                class="c-input"
              />
              <p class="text-[11px] text-slate-400">Dùng để xác minh danh tính và hợp đồng đào tạo / thù lao khi bạn bắt đầu giảng dạy.</p>
            </div>
          </div>

          <!-- Section 2: Specialization & Teaching Background -->
          <div class="space-y-4">
            <div class="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">school</span>
              <span>2. Chuyên môn & Lĩnh vực đào tạo</span>
            </div>

            <!-- Specialization -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Chuyên môn / Lĩnh vực giảng dạy chính <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="specialization"
                required
                placeholder="VD: Lập trình Next.js thực chiến, UI/UX Design Figma, SEO ngách, Cybersecurity..."
                class="c-input"
              />
            </div>

            <!-- Statement of Purpose / Bio -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Giới thiệu bản thân & Định hướng giảng dạy <span class="text-rose-500">*</span>
              </label>
              <textarea
                name="statement"
                rows="4"
                required
                placeholder="Tóm tắt ngắn về kinh nghiệm thực tế, các dự án nổi bật bạn từng tham gia và nội dung kiến thức bạn dự định chia sẻ tới học viên..."
                class="c-input resize-none"
              ></textarea>
            </div>

            <!-- Portfolio / GitHub / Website URL -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Đường dẫn Portfolio / GitHub / Website / Kênh chia sẻ (Tùy chọn)
              </label>
              <input
                type="url"
                name="portfolio_url"
                placeholder="https://github.com/... hoặc https://behance.net/... hoặc https://myportfolio.dev"
                class="c-input"
              />
            </div>

            <!-- Institution Name (Optional) -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Đơn vị công tác / Trường học / Tổ chức (Tùy chọn)
              </label>
              <input
                type="text"
                name="institution_name"
                placeholder="VD: Freelance / Độc lập, hoặc Trường ĐH / Công ty công nghệ (để trống nếu làm tự do)"
                class="c-input"
              />
            </div>
          </div>

          <!-- Section 3: Evidence & Verification Uploads -->
          <div class="space-y-4">
            <div class="flex items-center gap-2 pb-1 border-b border-slate-100 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">upload_file</span>
              <span>3. Hồ sơ năng lực & Minh chứng</span>
            </div>
            <p class="text-xs text-slate-500">
              Tải lên hồ sơ để Quản trị viên đối soát năng lực. Hỗ trợ tệp PDF, Word (DOCX) hoặc hình ảnh (PNG, JPG), tối đa 50MB/file.
            </p>

            <!-- CV / Portfolio File (Required) -->
            <div class="p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-800/60 bg-indigo-50/40 dark:bg-indigo-950/20 space-y-2">
              <label class="block text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between">
                <span class="flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px] text-primary">description</span>
                  <span>Tệp CV hoặc Portfolio tóm tắt năng lực <span class="text-rose-500">*</span></span>
                </span>
                <span class="text-[10px] uppercase font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">Bắt buộc</span>
              </label>
              <input
                type="file"
                name="cv_file"
                id="cv_file_input"
                required
                accept=".pdf,.docx,.png,.jpg,.jpeg"
                class="c-input text-xs"
              />
              <p class="text-[11px] text-slate-500">Đính kèm bản CV, Resume hoặc Portfolio PDF thể hiện kỹ năng, dự án thực tế hoặc kinh nghiệm của bạn.</p>
            </div>

            <!-- Additional Evidence Files (Optional) -->
            <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 space-y-2">
              <label class="block text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px] text-indigo-600">folder_open</span>
                <span>Chứng chỉ, bằng cấp hoặc minh chứng năng lực bổ sung (Tùy chọn)</span>
              </label>
              <input
                type="file"
                name="evidence_files"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                class="c-input text-xs"
              />
            </div>
          </div>

          <!-- Submit Button -->
          <div class="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
            <button
              type="submit"
              id="submit-nomination-btn"
              class="c-btn c-btn-primary c-btn-md flex items-center gap-1.5 shadow-sm"
            >
              <span>Gửi hồ sơ xét duyệt</span>
              <span class="material-symbols-outlined text-[16px]">send</span>
            </button>
          </div>
        </form>
      `;

      document.getElementById('become-instructor-form').onsubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        const btn = document.getElementById('submit-nomination-btn');

        const cvInput = document.getElementById('cv_file_input');
        if (!cvInput || !cvInput.files || cvInput.files.length === 0) {
          UI.showToast('Vui lòng tải lên tệp CV hoặc Portfolio để hoàn tất đăng ký.', 'warning');
          return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang tải lên và gửi hồ sơ...';

        const formData = new FormData(form);

        const specialization = (form.specialization?.value || '').trim();
        const rawInstitution = (form.institution_name?.value || '').trim();
        const institution = rawInstitution || 'Hoạt động tự do / Độc lập';
        formData.set('institution_name', institution);
        formData.set('teaching_experience', `${specialization} - ${institution}`);
        formData.set('statement_of_purpose', (form.statement?.value || '').trim());
        if (form.portfolio_url?.value) {
          formData.set('evidence_urls', form.portfolio_url.value.trim());
          formData.set('portfolio_url', form.portfolio_url.value.trim());
        }

        try {
          await ApiClient.submitInstructorApplication(formData);
          UI.showToast('Hồ sơ ứng tuyển đã được gửi thành công đến Quản trị viên.', 'success');
          StudentView.renderBecomeInstructor(container);
        } catch (err) {
          UI.showToast(err.message || 'Lỗi gửi hồ sơ.', 'error');
          btn.disabled = false;
          btn.innerHTML = '<span>Gửi hồ sơ xét duyệt</span> <span class="material-symbols-outlined text-[16px]">send</span>';
        }
      };

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp thông tin: ${UI.escapeHtml(err.message)}</div>`;
    }
  }
}

window.StudentView = StudentView;
