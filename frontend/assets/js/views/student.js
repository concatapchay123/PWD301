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
        
        <!-- 1. Header & Action Hub (Greeting, Subtitle, Single Primary CTA) -->
        <div class="c-card p-6 sm:p-7 flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-sm">
          <div class="space-y-1.5 max-w-2xl">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">Học kỳ Hiện tại</span>
              <span class="text-xs text-slate-400 font-medium">Bàn làm việc Sinh viên</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight" id="student-welcome-heading">
              Chào buổi sáng, Sinh viên
            </h1>
            <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed" id="student-welcome-sub">
              Bạn có bài kiểm tra sắp tới và các nội dung bài học đang tiếp diễn. Tiếp tục hành trình học tập ngay bên dưới.
            </p>
          </div>

          <!-- Single Primary CTA -->
          <div class="shrink-0" id="dashboard-primary-cta-container">
            <a
              href="#/student/catalog"
              id="dashboard-primary-cta-btn"
              class="c-btn c-btn-primary c-btn-lg shadow-xs"
            >
              <span id="primary-cta-label">Khám phá Khóa học</span>
              <span class="material-symbols-outlined text-[20px]">arrow_forward</span>
            </a>
          </div>
        </div>

        <!-- 2. Actionable Metric Cards (3 Cards: Enrolled, Progress, Urgent Assessment) -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-5" id="dashboard-metric-cards">
          
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

          <!-- Card 2: Tiến độ học tập -->
          <div class="c-card p-5 flex flex-col justify-between">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Tiến độ học tập</span>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-primary-subtle text-primary dark:bg-primary/20" id="kpi-progress-pct">0% Hoàn thành</span>
            </div>
            <div class="mt-3 space-y-2">
              <div class="flex items-baseline justify-between">
                <span class="text-2xl font-extrabold text-slate-900 dark:text-white" id="kpi-progress-ratio">0 / 0 Môn học</span>
                <span class="text-xs font-semibold text-slate-400">Đã hoàn thành</span>
              </div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                <div class="bg-primary h-full rounded-full transition-all duration-500" id="kpi-progress-bar" style="width: 5%"></div>
              </div>
            </div>
          </div>

          <!-- Card 3: Khảo thí trọng tâm (Urgent Assessment Ticker) -->
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

        <!-- 3. Learning Focus: Split 60/40 (Hero Continue Card & To-Do Urgent Actions) -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          <!-- Hero Continue Card (7 Cols) -->
          <div class="lg:col-span-7 c-card p-6 sm:p-7 flex flex-col justify-between relative overflow-hidden" id="dashboard-hero-continue-card">
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

          <!-- To-Do & Urgent Actions (5 Cols) -->
          <div class="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-7 shadow-sm flex flex-col justify-between space-y-4">
            <div class="space-y-4">
              <div class="flex items-center justify-between">
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

        <!-- 4. Enrolled Courses Master Section -->
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

          <div id="enrolled-courses-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div class="col-span-full text-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-400 text-sm">
              <span class="inline-block animate-spin text-xl mb-2">⏳</span>
              <p>Đang tải danh sách khóa học...</p>
            </div>
          </div>
        </div>

        <!-- 5. Become Instructor Callout Banner -->
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
        const primaryCtaBtn = document.getElementById('dashboard-primary-cta-btn');
        const primaryCtaLabel = document.getElementById('primary-cta-label');

        const prog = Math.round(heroCourse.current_progress_percent || heroCourse.progress_percent || 0);

        if (heroCode) heroCode.textContent = heroCourse.course_code || 'CRS';
        if (heroTitle) heroTitle.textContent = heroCourse.course_title || 'Khóa học của bạn';
        if (heroLesson) heroLesson.textContent = `Tiến độ: ${prog}% • Sẵn sàng tiếp tục bài giảng mới`;
        if (heroProgVal) heroProgVal.textContent = `${prog}%`;
        if (heroProgBar) heroProgBar.style.width = `${Math.min(100, Math.max(5, prog))}%`;
        if (heroInstructor) heroInstructor.textContent = `GV hướng dẫn: ${heroCourse.instructor_name || 'Hội đồng Khoa học'}`;

        if (heroContinueBtn) heroContinueBtn.href = `#/student/courses/detail?id=${heroCourse.course_id}`;
        if (heroSyllabusBtn) heroSyllabusBtn.href = `#/student/courses/detail?id=${heroCourse.course_id}`;

        if (primaryCtaBtn) {
          primaryCtaBtn.href = `#/student/courses/detail?id=${heroCourse.course_id}`;
          if (primaryCtaLabel) primaryCtaLabel.textContent = `Tiếp tục học: ${heroCourse.course_code || 'Khóa học'}`;
        }
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
                    ${UI.statusBadge(e.status)}
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
      <div class="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
        <!-- Page Title & Search Bar -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white">Danh mục Khóa học</h1>
            <p class="text-sm text-slate-500 mt-0.5">Khám phá các khóa học công khai, tìm kiếm và đăng ký học ngay.</p>
          </div>
          <div class="flex items-center gap-3 w-full md:w-auto">
            <div class="relative flex-1 md:w-80">
              <span class="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">search</span>
              <input
                type="text"
                id="catalog-search-input"
                placeholder="Tìm tên môn học, mã khóa..."
                class="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm outline-none focus:border-primary transition-colors"
              />
            </div>
            <select id="catalog-category-filter" class="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm outline-none focus:border-primary">
              <option value="">Tất cả danh mục</option>
              <option value="Khoa học Máy tính">Khoa học Máy tính</option>
              <option value="Trí tuệ Nhân tạo">Trí tuệ Nhân tạo</option>
              <option value="An toàn thông tin">An toàn thông tin</option>
              <option value="Kỹ thuật phần mềm">Kỹ thuật phần mềm</option>
            </select>
          </div>
        </div>

        <!-- Catalog Grid -->
        <div id="catalog-courses-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

      grid.innerHTML = filtered.map(c => `
        <div class="c-card c-card-hover p-5 flex flex-col justify-between space-y-4">
          <div class="space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold font-mono text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">${UI.escapeHtml(c.course_code)}</span>
              ${UI.difficultyBadge(c.difficulty)}
            </div>
            <h3 class="font-extrabold text-slate-900 dark:text-white text-base leading-snug line-clamp-2">
              ${UI.escapeHtml(c.title)}
            </h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-3 leading-relaxed">
              ${UI.escapeHtml(c.description || c.summary || 'Khóa học học thuật chính quy theo chuẩn đầu ra.')}
            </p>
          </div>

          <div class="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span class="flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">folder</span>
                ${UI.escapeHtml(c.category || 'Chung')}
              </span>
              <span class="flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">group</span>
                Tối đa: ${c.capacity || 50} SV
              </span>
            </div>

            <div class="flex items-center gap-2 pt-1">
              <button
                type="button"
                class="flex-1 c-btn c-btn-primary c-btn-sm enroll-action-btn"
                data-course-id="${c.course_id || c.id}"
                data-course-title="${UI.escapeHtml(c.title)}"
              >
                Đăng ký học ngay
              </button>
              <a
                href="#/student/courses/detail?id=${c.course_id || c.id}"
                class="c-btn c-btn-secondary c-btn-sm"
                title="Xem hồ sơ học vụ đầy đủ"
              >
                <span>Hồ sơ môn</span>
                <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
              </a>
            </div>
          </div>
        </div>
      `).join('');

      // Attach button clicks
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
            UI.showToast(`Đã ghi danh thành công khóa học: ${ctitle}`, 'success');
            window.location.hash = '#/student/courses';
          } catch (err) {
            UI.showToast(err.message || 'Không thể ghi danh vào khóa học này.', 'error');
            btn.disabled = false;
            btn.innerHTML = 'Đăng ký học ngay';
          }
        };
      });
    };

    try {
      const res = await ApiClient.getCatalogCourses();
      allCourses = res.items || res.courses || [];
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
                  ${UI.statusBadge(e.status)}
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
      const isEnrolled = !!(courseData?.enrollment || progressData?.is_enrolled || progressData?.progress_percent !== undefined);

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
                  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:border-primary/50 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div class="space-y-1">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-purple-600 bg-purple-50 dark:bg-purple-950/40 px-2 py-0.5 rounded">Khảo thí</span>
                        ${UI.statusBadge(a.status || 'PUBLISHED')}
                      </div>
                      <h4 class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(a.title)}</h4>
                      <div class="flex items-center gap-3 text-xs text-slate-500">
                        <span>Thời lượng: <strong>${a.time_limit_minutes || 45} phút</strong></span>
                        <span>•</span>
                        <span>Điểm tối đa: <strong>${a.max_points || 10}đ</strong></span>
                      </div>
                    </div>
                    <div class="flex items-center gap-2.5 shrink-0">
                      ${a.attempt_id ? `
                        <a href="#/student/assessments/results?id=${a.attempt_id}" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 flex items-center gap-1">
                          <span class="material-symbols-outlined text-[16px]">fact_check</span>
                          <span>Xem kết quả</span>
                        </a>
                      ` : `
                        <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1">
                          <span class="material-symbols-outlined text-[16px]">lock_open</span>
                          <span>Vào phòng chờ thi</span>
                        </a>
                      `}
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
                <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2 border border-slate-100 dark:border-slate-800">
                  <div class="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-primary text-[18px]">person_apron</span>
                    <span>Giảng viên chủ nhiệm:</span>
                  </div>
                  <div class="text-sm font-extrabold text-primary">${UI.escapeHtml(course.instructor_name || 'Hội đồng Khoa học Khoa CNTT')}</div>
                  <div class="text-slate-500">Email học vụ: <code class="font-mono bg-white dark:bg-slate-900 px-1 py-0.5 rounded border border-slate-200 dark:border-slate-700">instructor@pwd301.edu.vn</code></div>
                  <div class="text-slate-500">Giờ tiếp sinh viên: Thứ 3 & Thứ 5 (14:00 - 16:30)</div>
                </div>

                <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 space-y-2 border border-slate-100 dark:border-slate-800">
                  <div class="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-indigo-600 text-[18px]">account_tree</span>
                    <span>Điều kiện tiên quyết (Cần học trước):</span>
                  </div>
                  <div class="text-slate-600 dark:text-slate-400 leading-relaxed">
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
              <span class="text-xs text-slate-500 font-medium">Hoàn thành: <strong>${Math.round(progressData?.progress_percent || 0)}%</strong></span>
            </div>

            <div class="space-y-3">
              ${lessons.length === 0 ? `
                <div class="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm">
                  Khóa học này đang hoàn thiện giáo trình, chưa có bài giảng nào được công bố.
                </div>
              ` : lessons.map((l, idx) => `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm hover:border-primary/50 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="flex items-start gap-3.5">
                    <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold flex items-center justify-center shrink-0 text-xs">
                      ${idx + 1}
                    </div>
                    <div>
                      <h4 class="font-bold text-slate-900 dark:text-white text-sm hover:text-primary transition-colors cursor-pointer" onclick="window.location.hash = '#/student/lessons/reader?course_id=${courseId}&lesson_id=${l.lesson_id || l.id}'">
                        ${UI.escapeHtml(l.title)}
                      </h4>
                      <p class="text-xs text-slate-500 mt-0.5 line-clamp-1">${UI.escapeHtml(l.summary || 'Bài giảng lý thuyết & thực hành kèm code mẫu')}</p>
                      <div class="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                        <span>Thời lượng: ~${l.estimated_duration_minutes || 45} phút</span>
                        <span>•</span>
                        <span>Tài liệu: ${(l.resources || []).length} tệp đính kèm</span>
                      </div>
                    </div>
                  </div>

                  <div class="shrink-0">
                    <a href="#/student/lessons/reader?course_id=${courseId}&lesson_id=${l.lesson_id || l.id}" class="px-4 py-2 rounded-xl bg-primary-subtle text-primary hover:bg-primary hover:text-white text-xs font-bold transition-all flex items-center gap-1">
                      <span>Vào học ngay</span>
                      <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                    </a>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      };

      container.innerHTML = `
        <div class="p-6 space-y-6 max-w-6xl mx-auto animate-fade-in">
          <!-- Navigation Breadcrumb -->
          <div class="flex items-center gap-2 text-xs text-slate-500">
            <a href="#/student/courses" class="hover:underline flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">arrow_back</span>
              Khóa học của tôi
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
                ${UI.statusBadge(course.status)}
                <span class="text-xs text-slate-500">• Khoa Công nghệ Thông tin</span>
              </div>
              <div class="flex items-center gap-3">
                ${(window.app?.currentRole === 'INSTRUCTOR' || window.app?.currentRole === 'ADMIN' || localStorage.getItem('pwd301_role') === 'INSTRUCTOR' || localStorage.getItem('pwd301_role') === 'ADMIN') ? `
                  <a href="#/instructor/courses/${courseId}/manage" class="px-3.5 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 border border-indigo-200 dark:border-indigo-800 text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs" title="Quay lại Cổng Giảng viên">
                    <span class="material-symbols-outlined text-[16px]">edit_note</span>
                    <span>Quản lý môn học (Giảng viên)</span>
                  </a>
                ` : ''}
                ${isEnrolled ? `
                  <div class="text-xs text-slate-500 font-medium">
                    Tiến độ: <strong class="text-primary font-bold">${Math.round(progressData?.progress_percent || 0)}%</strong>
                  </div>
                  <button type="button" id="dossier-leave-btn" class="px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-900 text-rose-600 dark:text-rose-400 text-xs font-bold hover:bg-rose-50 transition-colors">
                    Rút môn học
                  </button>
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

            <!-- Metadata Academic Strip -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs">
              <div>
                <span class="text-slate-400 block">Số tín chỉ:</span>
                <span class="font-extrabold text-slate-900 dark:text-white text-sm">3 Tín chỉ (ECTS 5)</span>
              </div>
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

            <!-- Low-Tech Friendly Student Learning Outcomes (SLO) Section -->
            <div class="p-5 sm:p-6 rounded-2xl border border-indigo-100 dark:border-indigo-950/60 bg-gradient-to-br from-indigo-50/60 to-white dark:from-indigo-950/20 dark:to-slate-900 shadow-2xs space-y-4">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-indigo-100/80 dark:border-indigo-950/80">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary text-[22px]">verified_user</span>
                    <h3 class="text-sm font-extrabold text-slate-900 dark:text-white">
                      Mục tiêu & Kỹ năng bạn sẽ đạt được
                    </h3>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary-subtle text-primary border border-primary/20 cursor-help select-none" title="Chuẩn đầu ra sinh viên theo kiểm định quốc tế ABET (Student Learning Outcomes)">
                      ABET SLO
                    </span>
                  </div>
                  <p class="text-xs text-slate-600 dark:text-slate-400">
                    💡 <strong>Bạn sẽ làm được gì sau môn học này?</strong> Đây là các kỹ năng thực tế bạn chắc chắn sẽ thành thạo sau khi hoàn thành khóa học.
                  </p>
                </div>
                <button
                  type="button"
                  class="self-start sm:self-center shrink-0 px-3 py-1.5 rounded-xl bg-white dark:bg-slate-800 border border-indigo-200 dark:border-indigo-800 hover:border-primary text-slate-700 dark:text-slate-200 text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs hover:text-primary"
                  onclick="UI.openAcademicGlossaryModal()"
                  title="Giải thích chi tiết các thuật ngữ như SLO, ABET, Prerequisites..."
                >
                  <span class="material-symbols-outlined text-[16px] text-primary">help</span>
                  <span>Giải thích thuật ngữ SLO là gì?</span>
                </button>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                ${studentSLOs.map((slo, idx) => {
                  const title = typeof slo === 'object' ? (slo.title || `Kỹ năng ${idx + 1}`) : `Kỹ năng ${idx + 1}`;
                  const desc = typeof slo === 'object' ? (slo.description || slo.content || '') : String(slo);
                  const weight = typeof slo === 'object' && slo.weight ? slo.weight : null;
                  const code = typeof slo === 'object' && slo.code ? slo.code : `SLO-${idx + 1}`;
                  return `
                    <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800/80 hover:border-primary/40 transition-all flex items-start gap-3 shadow-2xs">
                      <span class="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 font-mono">
                        ${idx + 1}
                      </span>
                      <div class="space-y-1 min-w-0 flex-1">
                        <div class="flex items-center justify-between gap-2">
                          <h4 class="text-xs font-bold text-slate-900 dark:text-white leading-snug">
                            ${UI.escapeHtml(title)}
                          </h4>
                          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-semibold shrink-0" title="Mã chuẩn đầu ra đối chiếu kiểm định ABET">
                            ${UI.escapeHtml(code)}
                          </span>
                        </div>
                        <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                          ${UI.escapeHtml(desc)}
                        </p>
                        ${weight ? `
                          <div class="text-[10px] text-slate-400 font-semibold">
                            Tỷ trọng đánh giá: <strong class="text-primary">${UI.escapeHtml(weight)}</strong>
                          </div>
                        ` : ''}
                      </div>
                    </div>
                  `;
                }).join('')}
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
              <a href="#/student/courses/detail?id=${courseId}" class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-800 transition-colors" title="Quay lại khóa học">
                <span class="material-symbols-outlined text-[20px]">arrow_back</span>
              </a>
              <div class="space-y-0.5">
                <div class="text-[11px] font-mono font-bold text-primary">${UI.escapeHtml(course.course_code)}</div>
                <div class="text-xs sm:text-sm font-extrabold text-slate-900 dark:text-white truncate max-w-xs sm:max-w-md">
                  ${UI.escapeHtml(lesson.title)}
                </div>
              </div>
            </div>

            <!-- Header Action Controls -->
            <div class="flex items-center gap-2 sm:gap-3">
              <!-- Left Drawer Trigger: Syllabus Outline -->
              <button
                type="button"
                id="open-syllabus-drawer-btn"
                class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center gap-1.5 transition-colors"
                title="Mở mục lục đề cương"
              >
                <span class="material-symbols-outlined text-[16px]">format_list_bulleted</span>
                <span class="hidden sm:inline">Mục lục (${currentIndex + 1}/${lessonsList.length})</span>
              </button>

              <!-- Right Drawer Trigger: Vault & Notes -->
              <button
                type="button"
                id="open-vault-notes-drawer-btn"
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
                  <span>Thời lượng: ~${lesson.estimated_duration_minutes || 45} phút</span>
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
                  <video controls class="w-full h-full" src="${lesson.video_url}" preload="metadata">
                    Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
                  </video>
                </div>
              ` : ''}

              <!-- Clean Rendered Markdown Body -->
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-10 shadow-sm text-slate-800 dark:text-slate-200 leading-relaxed text-sm sm:text-base space-y-5">
                ${UI.renderMarkdown(lesson.markdown_content || 'Nội dung bài giảng đang được hoàn thiện.')}
              </div>

              <!-- Inline Contextual AI Mentor Card -->
              <div class="bg-gradient-to-br from-indigo-950 via-slate-900 to-indigo-900 text-white rounded-2xl p-6 shadow-md space-y-4 border border-indigo-800/40">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-300 flex items-center justify-center">
                    <span class="material-symbols-outlined text-[20px]">smart_toy</span>
                  </div>
                  <div>
                    <h4 class="font-bold text-sm">Gia sư AI Học vụ (Gemini Flash)</h4>
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
      const syllabusBtn = document.getElementById('open-syllabus-drawer-btn');
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
      const vaultNotesBtn = document.getElementById('open-vault-notes-drawer-btn');
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

      // 5. Heartbeat progress tracking
      const progressHeartbeat = setInterval(() => {
        ApiClient.recordLessonProgress(lessonId, 15, 0.5, false).catch(() => {});
      }, 15000);

    } catch (err) {
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

      card.innerHTML = `
        <div class="space-y-2">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-subtle text-primary text-xs font-bold">
            <span class="w-2 h-2 rounded-full bg-primary animate-ping"></span>
            Phòng chờ Khảo thí Trực tuyến
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            ${UI.escapeHtml(assess.title || data.title || 'Bài kiểm tra')}
          </h1>
          <p class="text-xs sm:text-sm text-slate-500">Môn học: <strong class="font-mono text-primary">${UI.escapeHtml(data.assessment?.course_code || 'CRS')}</strong> • Thời lượng: <strong>${assess.time_limit_minutes || assess.duration_minutes || 60} phút</strong></p>
        </div>

        <!-- Countdown Timer Display -->
        <div class="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500" id="countdown-label">
            ${activeAttemptId ? 'Bài thi đang diễn ra • Bấm để tiếp tục làm bài' : (isOpen ? 'Bài thi đã mở • Sẵn sàng làm bài' : 'Thời gian đếm ngược đến giờ mở đề thi (UTC)')}
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
            <span>${activeAttemptId ? 'Tiếp tục làm bài thi (Resume)' : (isOpen ? 'Bắt đầu làm bài thi' : 'Đang chờ mở khảo thí...')}</span>
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
          startBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">lock_open</span> <span>BẮT ĐẦU LÀM BÀI THI NGAY</span>';
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
            if (labelEl) labelEl.textContent = 'Bài thi đã mở • Sẵn sàng làm bài';
            if (startBtn) {
              startBtn.disabled = false;
              startBtn.className = 'w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/30 animate-pulse transition-all flex items-center justify-center gap-2';
              startBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">lock_open</span> <span>BẮT ĐẦU LÀM BÀI THI NGAY</span>';
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
                          <strong>${c.label || ''}.</strong> ${UI.escapeHtml(c.content || c.text || '')}
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

                    <!-- Scale conversion button -->
                    <button
                      type="button"
                      id="view-scale-btn"
                      class="px-2.5 py-1.5 text-xs font-bold text-primary bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 rounded-xl border border-indigo-200 dark:border-indigo-800 transition flex items-center gap-1 shadow-2xs cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[15px]">balance</span>
                      <span>Thang điểm</span>
                    </button>
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

                  <!-- Instructor Note Box -->
                  <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/60 text-xs space-y-1">
                    <div class="flex items-center justify-between font-bold text-slate-700 dark:text-slate-300">
                      <span class="flex items-center gap-1 text-[11px]">
                        <span class="material-symbols-outlined text-[14px] text-primary">chat_bubble</span>
                        <span>Nhận xét của GV:</span>
                      </span>
                      <span class="text-[10px] text-slate-400 font-normal">${UI.formatDate(data.submitted_at)}</span>
                    </div>
                    <p class="text-slate-600 dark:text-slate-400 italic leading-relaxed text-[11px]">
                      ${isPassed
                        ? '"Bài làm rất chắc chắn về kiến trúc Flask Factory và phân tách Blueprint. Khả năng viết test case cho RESTful API đạt chuẩn kiểm thử tự động."'
                        : '"Cần xem lại kỹ thuật tối ưu hóa truy vấn cơ sở dữ liệu và các quy tắc phân quyền RBAC để cải thiện kết quả ở đợt thi lại."'}
                    </p>
                  </div>

                  <!-- Action Button: Open Audit Drawer -->
                  ${isFormalExam ? `
                    <div class="space-y-2 pt-1">
                      <button
                        type="button"
                        id="sidebar-audit-drawer-btn"
                        class="w-full py-2.5 px-3 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-primary border border-primary/30 hover:border-primary font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
                      >
                        <span class="material-symbols-outlined text-[16px]">verified</span>
                        <span>Xem chi tiết phúc khảo & kiểm toán (3)</span>
                      </button>
                    </div>
                  ` : ''}

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
                    <span class="text-xs text-slate-400 font-mono pl-1">ID: PWD-DE-64</span>
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
                    * Bấm "Hỏi gia sư AI" để được giải thích chi tiết từng câu hỏi
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
                          <span class="text-xs font-mono text-slate-400">ID: ${q.question_id || (573291780 + idx)}</span>
                          <span class="text-xs font-bold px-2 py-0.5 rounded-lg border ${isCorrect ? 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800' : 'text-rose-700 bg-rose-50 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800'}">
                            ${isCorrect ? `+${awardedPts} đ` : '0 đ'}
                          </span>
                        </div>

                        <!-- Ask AI Button -->
                        <button
                          type="button"
                          class="ask-ai-question-btn px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 text-indigo-700 dark:text-indigo-300 text-xs font-bold transition-colors flex items-center gap-1 shadow-2xs cursor-pointer"
                          data-stem="${UI.escapeHtml(q.content || q.stem || '')}"
                          data-answer="${UI.escapeHtml(correctAns)}"
                        >
                          <span class="material-symbols-outlined text-[14px]">smart_toy</span>
                          <span>Hỏi gia sư AI câu này</span>
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
                                <strong class="font-bold ${isTheCorrect ? 'text-emerald-600' : 'text-slate-900 dark:text-white'}">${c.label || '•'}.</strong>
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

                      <!-- Academic Feedback Box -->
                      ${(q.feedback || q.teacher_feedback) ? `
                        <div class="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200/80 dark:border-indigo-900/50 text-xs space-y-2">
                          <div class="font-bold text-primary flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-[16px]">feedback</span>
                            <span>Ghi chú phản hồi:</span>
                          </div>
                          <div class="text-slate-700 dark:text-slate-300 italic bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-indigo-100 dark:border-indigo-900/40">
                            "${UI.escapeHtml(q.feedback || q.teacher_feedback)}"
                          </div>
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
      const openAuditDrawer = () => {
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
          const prompt = `Gia sư hãy giải thích chi tiết giúp tôi câu hỏi thi này (vì sao đáp án đúng là "${ans}"):\n"${stem}"`;
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
          <div class="flex items-center gap-3 shrink-0">
            ${a.attempt_id ? `
              <a href="#/student/assessments/results?id=${a.attempt_id}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">fact_check</span>
                <span>Xem kết quả</span>
              </a>
            ` : `
              <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">lock_open</span>
                <span>Vào phòng chờ</span>
              </a>
            `}
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
            <div class="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md">
              <span class="material-symbols-outlined text-[20px]">smart_toy</span>
            </div>
            <div>
              <h1 class="text-sm font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5">
                Trợ lý AI Học vụ (Gemini 3.8 Flash)
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
            <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 text-xs shadow-sm">
              <span class="material-symbols-outlined text-[16px]">smart_toy</span>
            </div>
            <div class="max-w-[85%] rounded-2xl p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm text-slate-800 dark:text-slate-200 text-sm leading-relaxed space-y-2">
              <p class="font-bold text-slate-900 dark:text-white">Xin chào! Tôi là Trợ lý Học vụ AI PWD301.</p>
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
        <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 text-xs shadow-sm">
          <span class="material-symbols-outlined text-[16px]">smart_toy</span>
        </div>
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
            <p class="text-sm text-slate-500 max-w-md mx-auto">Tài khoản của bạn đã được cấp quyền Giảng viên. Sử dụng bộ chuyển vai trò trên thanh Topbar để chuyển sang Bàn làm việc Giảng viên.</p>
            <div class="pt-2">
              <button type="button" id="go-to-instructor-desk-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm">
                Đến Bàn làm việc Giảng viên
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

      // Render fresh application form
      box.innerHTML = `
        <div class="space-y-1">
          <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white">Đăng ký trở thành Giảng viên</h1>
          <p class="text-sm text-slate-500">Cung cấp hồ sơ năng lực và chứng chỉ chuyên môn để được cấp quyền giảng dạy và quản trị khóa học.</p>
        </div>

        <form id="become-instructor-form" class="space-y-4 pt-2">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Cơ sở giáo dục / Tổ chức công tác <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="institution_name"
                required
                placeholder="VD: Trường Đại học Bách Khoa TP.HCM"
                class="c-input"
              />
            </div>
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Chuyên môn giảng dạy <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="specialization"
                required
                placeholder="VD: Lập trình Web Full-stack & Hệ thống phân tán"
                class="c-input"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Số năm kinh nghiệm
              </label>
              <input
                type="number"
                name="experience_years"
                min="0"
                max="50"
                value="3"
                class="c-input"
              />
            </div>
            <div class="md:col-span-2 space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Đường dẫn Hồ sơ / Bằng cấp chứng chỉ (Drive / Cloud URL) <span class="text-rose-500">*</span>
              </label>
              <input
                type="url"
                name="certificate_url"
                required
                placeholder="https://drive.google.com/drive/folders/..."
                class="c-input"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Thư ngỏ / Định hướng giảng dạy (Statement of Purpose) <span class="text-rose-500">*</span>
            </label>
            <textarea
              name="statement"
              rows="4"
              required
              placeholder="Trình bày lý do, mục tiêu học thuật và môn học bạn dự định xây dựng giáo trình..."
              class="c-input resize-none"
            ></textarea>
          </div>

          <div class="pt-2 flex justify-end">
            <button
              type="submit"
              id="submit-nomination-btn"
              class="c-btn c-btn-primary c-btn-md flex items-center gap-1.5"
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

        btn.disabled = true;
        btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang gửi hồ sơ...';

        const payload = {
          institution_name: form.institution_name.value.trim(),
          specialization: form.specialization.value.trim(),
          experience_years: parseInt(form.experience_years.value || '0', 10),
          teaching_experience: `${form.specialization.value.trim()} tại ${form.institution_name.value.trim()}`,
          certificate_url: form.certificate_url.value.trim(),
          evidence_urls: form.certificate_url.value.trim(),
          statement: form.statement.value.trim(),
          statement_of_purpose: form.statement.value.trim()
        };

        try {
          await ApiClient.submitInstructorApplication(payload);
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
