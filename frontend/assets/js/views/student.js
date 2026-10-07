/**
 * PWD301 LMS - Student Views Layer
 * Implements Dashboard, Catalog, Course Hub, 3-Column Lesson Reader,
 * Assessments Suite (Waiting Room UTC, Exam Attempt Console, Results Drawer),
 * Gemini AI Academic Assistant, and Instructor Self-Nomination.
 */

function cleanChoiceText(text) {
  if (text == null) return '';
  let str = String(text).trim();
  str = str.replace(/\[\[PWD301:G:(?:DRAG|MATCH):[1-9]\d*\]\]/gi, '');
  str = str.replace(/\[\[PWD301:(?:FI|IMAGE|EXTRACTED_IMAGE):[^\]]+\]\]/gi, '');
  if (str.includes('|||')) {
    const parts = str.split('|||');
    str = parts.map(p => p.trim()).filter(Boolean).join(' ➔ ');
  }
  return str.trim();
}

function parseGroupedAttemptChoices(question) {
  const choices = Array.isArray(question?.choices) ? question.choices : [];
  let interactionKind = {
    DRAG_DROP: 'DRAG',
    MATCHING: 'MATCH'
  }[question?.interaction_type];

  // Auto-detect interactionKind if not explicitly specified
  if (!interactionKind && choices.length) {
    if (choices.some(c => c.interaction_kind === 'DRAG' || /\[\[PWD301:G:DRAG:/i.test(c.content || c.text || ''))) {
      interactionKind = 'DRAG';
    } else if (choices.some(c => c.interaction_kind === 'MATCH' || /\[\[PWD301:G:MATCH:/i.test(c.content || c.text || ''))) {
      interactionKind = 'MATCH';
    }
  }

  if (!choices.length || !interactionKind) return null;

  const groups = new Map();
  for (const choice of choices) {
    const rawContent = String(choice.content || choice.text || '').trim();
    let groupIndex = Number(choice.interaction_group);
    let markerKind = choice.interaction_kind;
    let cleanText = rawContent;
    let interactionLeft = choice.interaction_left;

    const markerMatch = rawContent.match(/^\[\[PWD301:G:(DRAG|MATCH):([1-9]\d*)\]\]/i);
    if (markerMatch) {
      markerKind = markerMatch[1].toUpperCase();
      groupIndex = Number(markerMatch[2]);
      cleanText = rawContent.slice(markerMatch[0].length).trim();
    }

    if (markerKind && markerKind !== interactionKind) continue;
    if (!Number.isInteger(groupIndex) || groupIndex < 1) groupIndex = 1;

    if (interactionKind === 'MATCH' && cleanText.includes('|||')) {
      const parts = cleanText.split('|||');
      interactionLeft = parts[0]?.trim() || interactionLeft;
      cleanText = parts[1]?.trim() || cleanText;
    }

    if (!groups.has(groupIndex)) groups.set(groupIndex, []);
    groups.get(groupIndex).push({
      ...choice,
      interaction_left: interactionLeft,
      answerText: cleanChoiceText(cleanText)
    });
  }

  const groupIndexes = Array.from(groups.keys()).sort((a, b) => a - b);
  if (!groupIndexes.length) return null;
  return {
    kind: interactionKind,
    groups: groupIndexes.map(index => ({ index, choices: groups.get(index) }))
  };
}

class StudentView {
  static getAttemptScoreState(data) {
    const released = data?.score_status === 'RELEASED' || data?.is_released === true;
    if (!released) {
      return {
        released: false,
        totalScore: null,
        maxPoints: null,
        passingScore: null,
        isPassed: null,
        scorePct: null,
      };
    }

    const numberOrNull = value => {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    };
    const totalScore = numberOrNull(data.total_score ?? data.raw_score ?? data.score);
    const maxPoints = numberOrNull(data.max_points ?? data.max_score);
    const passingScore = numberOrNull(
      data.passing_score ?? (maxPoints === null ? null : maxPoints * 0.5),
    );
    const isPassed = data.is_passed !== undefined
      ? Boolean(data.is_passed)
      : (totalScore !== null && passingScore !== null ? totalScore >= passingScore : null);

    return {
      released: true,
      totalScore,
      maxPoints,
      passingScore,
      isPassed,
      scorePct: totalScore !== null && maxPoints > 0 ? (totalScore / maxPoints) * 10 : null,
    };
  }

  static getSubmissionKey(attemptId) {
    if (!attemptId || !window.crypto?.randomUUID || !window.sessionStorage) return '';
    try {
      const storageKey = `pwd301:attempt-submit:${attemptId}`;
      const stored = window.sessionStorage.getItem(storageKey);
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(stored || '')) {
        return stored;
      }
      const key = window.crypto.randomUUID();
      window.sessionStorage.setItem(storageKey, key);
      return key;
    } catch (_error) {
      return '';
    }
  }

  static async retryFailedAnswerSaves(failedQuestionIds, answerPayloads, saveAnswer) {
    const retries = Array.from(failedQuestionIds, questionId => {
      const payload = answerPayloads.get(questionId);
      return payload ? saveAnswer(questionId, payload) : Promise.resolve();
    });
    await Promise.allSettled(retries);
    return failedQuestionIds.size;
  }

  static isLessonVideoWatched(lesson) {
    if (!lesson?.video_url) return true;
    const fraction = Number(lesson.progress?.max_view_fraction || 0);
    const spent = Number(lesson.progress?.seconds_spent || 0);
    const minSec = Number(lesson.minimum_completion_seconds || 0);

    if (fraction < 0.90) return false;
    if (minSec > 0 && spent < minSec) return false;
    return true;
  }

  static getPasswordRequirements(password) {
    const value = String(password || '');
    return {
      hasLength: value.length >= 8,
      hasLetter: /[A-Za-z]/.test(value),
      hasDigit: /[0-9]/.test(value),
      hasSpecialCharacter: /[^A-Za-z0-9\s]/.test(value)
    };
  }

  static createRandomAvatarUrl(random = Math.random, style = 'adventurer') {
    const allowed = ['adventurer', 'lorelei', 'fun-emoji', 'pixel-art', 'thumbs', 'bottts'];
    const selected = allowed.includes(style) ? style : 'adventurer';
    const seed = Math.floor(random() * 1_000_000_000).toString(36);
    return `https://api.dicebear.com/10.x/${selected}/svg?seed=${encodeURIComponent(seed)}`;
  }

  static isSupportedAvatarUrl(url) {
    return /^https:\/\/api\.dicebear\.com\/(?:7\.x\/bottts|10\.x\/(?:adventurer|lorelei|fun-emoji|pixel-art|thumbs|bottts))\/svg\?seed=[a-z0-9]+$/.test(String(url));
  }

  static getStoredRandomAvatarUrl(identity) {
    const key = `pwd301:random-avatar:${String(identity || '').trim()}`;
    if (!String(identity || '').trim()) return '';
    try {
      const value = window.localStorage?.getItem(key) || '';
      return StudentView.isSupportedAvatarUrl(value) ? value : '';
    } catch (_error) {
      return '';
    }
  }

  static storeRandomAvatarUrl(identity, avatarUrl) {
    const key = `pwd301:random-avatar:${String(identity || '').trim()}`;
    if (!String(identity || '').trim() || !StudentView.isSupportedAvatarUrl(avatarUrl)) return false;
    try {
      window.localStorage?.setItem(key, avatarUrl);
      return Boolean(window.localStorage);
    } catch (_error) {
      return false;
    }
  }

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
      <div class="py-6 sm:py-8 space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
        
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

          <!-- Card 2: Tiến độ học tập trung bình -->
          <a class="group c-card c-card-hover p-5 flex flex-col justify-between" href="#/student/courses">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Tiến độ trung bình</span>
              <div class="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                <span class="material-symbols-outlined text-[20px]">trending_up</span>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-2xl font-extrabold text-slate-900 dark:text-white" id="kpi-progress-pct">0% Hoàn thành</div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden mt-2">
                <div class="bg-emerald-500 h-full rounded-full transition-all duration-500" id="kpi-progress-bar" style="width: 0%"></div>
              </div>
              <p class="text-xs text-slate-400 mt-1.5 flex items-center justify-between">
                <span id="kpi-progress-ratio">0 / 0 Môn học</span>
                <span class="material-symbols-outlined text-[14px] text-emerald-600 shrink-0">arrow_forward</span>
              </p>
            </div>
          </a>

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

            <!-- AI Course Recommendations Section (Algorithm 14) -->
            <div class="space-y-4 pt-2" id="dashboard-recommendations-section">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center material-symbols-outlined text-[18px]">auto_awesome</span>
                  <div>
                    <h2 class="text-lg font-bold text-slate-900 dark:text-white leading-tight">Gợi ý khóa học tiếp theo</h2>
                    <p class="text-xs text-slate-400">Được phân tích bởi Bạch tuộc AI theo tiến độ và điều kiện tiên quyết</p>
                  </div>
                </div>
                <a href="#/student/courses/catalog" class="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-0.5">
                  <span>Khám phá thêm</span>
                  <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
                </a>
              </div>

              <div id="dashboard-recommendations-list" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="col-span-full text-center py-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
                  <span class="inline-block animate-spin text-base mb-1">⏳</span>
                  <p>Bạch tuộc AI đang tính toán lộ trình tối ưu cho bạn...</p>
                </div>
              </div>
            </div>

          </div>

          <!-- Right Column (4 cols): Sticky Việc cần làm hôm nay (100% Khảo thí & Thi cử) -->
          <div class="xl:col-span-4 xl:sticky xl:top-24 space-y-4">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-[20px] text-primary">assignment_late</span>
                  <h3 class="font-bold text-base text-slate-900 dark:text-white">Việc cần làm hôm nay</h3>
                </div>
                <span class="text-xs font-semibold text-primary font-mono" id="todo-tasks-badge">Khảo thí & Thi cử</span>
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

                <!-- Empty State Placeholder when no pending exams -->
                <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-center space-y-1 hidden" id="todo-empty-state">
                  <span class="material-symbols-outlined text-[24px] text-emerald-500">task_alt</span>
                  <p class="text-xs font-bold text-slate-700 dark:text-slate-300">Không có bài thi cần làm gấp</p>
                  <p class="text-[11px] text-slate-400">Bạn đã hoàn thành các bài thi theo kế hoạch học vụ.</p>
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

      if (upcoming.length === 0 && recentResults.length === 0) {
        const emptyState = document.getElementById('todo-empty-state');
        if (emptyState) emptyState.classList.remove('hidden');
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
                  <div class="aspect-video w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 cursor-pointer" onclick="window.location.hash = '#/student/courses/detail?id=${e.course_id}'">
                    ${e.thumbnail_url ? `
                      <img src="${UI.escapeHtml(e.thumbnail_url)}" alt="${UI.escapeHtml(e.course_title || 'Khóa học')}" class="w-full h-full object-cover object-center hover:scale-105 transition-transform duration-300" onerror="this.remove()" />
                    ` : `
                      <div class="w-full h-full flex flex-col items-center justify-center text-slate-400 gap-1 p-4">
                        <span class="material-symbols-outlined text-[28px] text-primary/40">school</span>
                        <span class="text-[11px] font-semibold">${UI.escapeHtml(e.course_code || 'CRS')}</span>
                      </div>
                    `}
                  </div>
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

      // Load AI Course Recommendations (Algorithm 14) asynchronously
      const recListEl = document.getElementById('dashboard-recommendations-list');
      const recSection = document.getElementById('dashboard-recommendations-section');
      if (recListEl) {
        ApiClient.getRecommendations(2).then(recs => {
          if (!document.getElementById('dashboard-recommendations-list')) return;
          if (recs && recs.length > 0) {
            recListEl.innerHTML = recs.map(r => `
              <div class="bg-white dark:bg-slate-900 border border-indigo-100 dark:border-indigo-900/40 hover:border-indigo-300 dark:hover:border-indigo-700 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-3.5">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] font-mono font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded-md border border-indigo-200/60 dark:border-indigo-800/60">
                      ${UI.escapeHtml(r.course_code)}
                    </span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.difficulty === 'ADVANCED' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300' : (r.difficulty === 'INTERMEDIATE' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300')}">
                      ${r.difficulty || 'Mới bắt đầu'}
                    </span>
                  </div>
                  <h3 class="font-extrabold text-slate-900 dark:text-white text-sm leading-snug hover:text-indigo-600 transition-colors">
                    ${UI.escapeHtml(r.title)}
                  </h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                    ${UI.escapeHtml(r.description || '')}
                  </p>
                </div>

                <div class="p-2.5 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100/80 dark:border-indigo-900/40 text-[11px] text-indigo-800 dark:text-indigo-300 flex items-start gap-2">
                  <span class="material-symbols-outlined text-[15px] text-indigo-500 shrink-0 mt-0.5">psychology</span>
                  <span class="leading-relaxed line-clamp-2">${UI.escapeHtml(r.explanation || 'Phù hợp với mục tiêu và tiến độ học tập hiện tại của bạn.')}</span>
                </div>

                <div class="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <span class="text-[11px] text-slate-400 font-medium">${UI.escapeHtml(r.category || 'Công nghệ thông tin')}</span>
                  <a href="#/student/courses/detail?id=${r.course_id}" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors inline-flex items-center gap-1 shadow-xs">
                    <span>Xem khóa học</span>
                    <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </a>
                </div>
              </div>
            `).join('');
          } else {
            const s = document.getElementById('dashboard-recommendations-section');
            if (s) s.classList.add('hidden');
          }
        }).catch(() => {
          const s = document.getElementById('dashboard-recommendations-section');
          if (s) s.classList.add('hidden');
        });
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
      <div class="py-6 space-y-8 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
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

        <!-- Recommended For You Spotlight Banner (Algorithm 14) -->
        <div id="catalog-recommendations-banner" class="hidden rounded-2xl bg-[#1E1B4B] bg-gradient-to-r from-slate-900 via-indigo-950 to-purple-950 text-white p-6 shadow-xl border border-indigo-700/40 space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-[22px]">auto_awesome</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h2 class="font-extrabold text-base sm:text-lg text-[#F8FAFC]">Được đề xuất cho bạn</h2>
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/25 text-indigo-200 border border-indigo-400/30 uppercase tracking-wider">Bạch tuộc AI</span>
                </div>
                <p class="text-xs text-indigo-200/90 mt-0.5">Các khóa học tối ưu dựa trên trình độ và lộ trình học tập của bạn</p>
              </div>
            </div>
          </div>
          <div id="catalog-recommendations-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <!-- Dynamically populated -->
          </div>
        </div>

        <!-- Catalog Grid (Standardized 3-column Course Cards matching My Learning & Instructor) -->
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

        const colorPresets = [
          { bg: 'from-blue-600 via-indigo-600 to-violet-700', icon: 'terminal', iconColor: 'text-blue-200' },
          { bg: 'from-emerald-600 via-teal-600 to-cyan-700', icon: 'code', iconColor: 'text-emerald-200' },
          { bg: 'from-purple-600 via-fuchsia-600 to-pink-600', icon: 'dataset', iconColor: 'text-purple-200' },
          { bg: 'from-amber-600 via-orange-600 to-rose-600', icon: 'integration_instructions', iconColor: 'text-amber-200' },
          { bg: 'from-cyan-600 via-sky-600 to-blue-700', icon: 'data_object', iconColor: 'text-cyan-200' },
          { bg: 'from-rose-600 via-pink-600 to-purple-700', icon: 'developer_mode', iconColor: 'text-rose-200' },
          { bg: 'from-violet-600 via-purple-700 to-indigo-800', icon: 'memory', iconColor: 'text-violet-200' },
          { bg: 'from-teal-600 via-emerald-600 to-green-700', icon: 'schema', iconColor: 'text-teal-200' },
        ];
        const hashSeed = String(c.course_code || cid || '').split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
        const preset = colorPresets[hashSeed % colorPresets.length];

        return `
          <div class="c-card c-card-hover p-5 flex flex-col justify-between space-y-4">
            <div class="space-y-3">
              <!-- Standardized Aspect-Video Thumbnail Cover -->
              <div class="aspect-video w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 cursor-pointer" onclick="window.location.hash = '#/student/courses/detail?id=${cid}'">
                ${c.thumbnail_url ? `
                  <img src="${UI.escapeHtml(c.thumbnail_url)}" alt="${UI.escapeHtml(c.title)}" class="w-full h-full object-cover object-center hover:scale-105 transition-transform duration-300" onerror="this.remove()" />
                ` : `
                  <div class="w-full h-full flex flex-col items-center justify-center p-4 bg-gradient-to-tr ${preset.bg} text-white relative">
                    <span class="absolute -right-6 -top-6 h-28 w-28 rounded-full border-[12px] border-white/10" aria-hidden="true"></span>
                    <span class="material-symbols-outlined text-4xl ${preset.iconColor} drop-shadow-sm mb-1">${preset.icon}</span>
                    <span class="text-xs font-mono font-bold tracking-wider uppercase bg-black/25 px-2.5 py-0.5 rounded-full border border-white/20">${UI.escapeHtml(c.course_code || 'Khóa học')}</span>
                  </div>
                `}
              </div>

              <div class="flex items-center justify-between">
                <span class="text-xs font-bold font-mono text-primary bg-primary-subtle px-2.5 py-0.5 rounded-full">${UI.escapeHtml(c.course_code)}</span>
                <div class="flex items-center gap-2">
                  ${isEnrolled ? `
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center gap-1">
                      <span class="material-symbols-outlined text-[13px]">check_circle</span>
                      <span>Đã ghi danh</span>
                    </span>
                  ` : ''}
                  ${UI.difficultyBadge(c.difficulty)}
                </div>
              </div>

              <h3
                class="font-extrabold text-slate-900 dark:text-white text-base leading-snug hover:text-primary transition-colors cursor-pointer"
                onclick="window.location.hash = '#/student/courses/detail?id=${cid}'"
              >
                ${UI.escapeHtml(c.title)}
              </h3>

              <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                ${UI.escapeHtml(c.description || c.summary || 'Khóa học đào tạo chính quy theo chuẩn đầu ra ABET.')}
              </p>
            </div>

            <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
              <div class="flex items-center gap-2">
                ${isEnrolled ? `
                  <a
                    href="#/student/courses/detail?id=${cid}"
                    class="w-full c-btn c-btn-primary c-btn-sm flex items-center justify-center gap-1.5 shadow-xs"
                  >
                    <span>Vào học tiếp tục</span>
                    <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </a>
                ` : `
                  <a
                    href="#/student/courses/detail?id=${cid}"
                    class="flex-1 c-btn c-btn-secondary c-btn-sm text-center"
                  >
                    <span>Chi tiết</span>
                  </a>
                  <button
                    type="button"
                    class="flex-1 c-btn c-btn-primary c-btn-sm enroll-action-btn"
                    data-course-id="${cid}"
                    data-course-title="${UI.escapeHtml(c.title)}"
                  >
                    <span>Ghi danh</span>
                  </button>
                `}
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Attach button clicks for enrolling -> Open large dedicated Enrollment Modal
      grid.querySelectorAll('.enroll-action-btn').forEach(btn => {
        btn.onclick = () => {
          const cid = btn.dataset.courseId;
          StudentView.openEnrollmentModal(cid, (enrolledId) => {
            const targetId = enrolledId || cid;
            if (targetId) enrolledCourseIds.add(String(targetId));
            if (cid) enrolledCourseIds.add(String(cid));
            renderFiltered();
          });
        };
      });
    };

    try {
      const [resCatalog, resEnrolled] = await Promise.all([
        ApiClient.getCatalogCourses(),
        ApiClient.getStudentEnrollments().catch(() => ({ enrollments: [] })),
      ]);
      allCourses = resCatalog.items || resCatalog.courses || [];
      const enrolledList = resEnrolled.enrollments || resEnrolled.courses || [];
      enrolledList.forEach(e => {
        if (e.course_id) enrolledCourseIds.add(String(e.course_id));
        if (e.id) enrolledCourseIds.add(String(e.id));
      });

      // Render recommendations spotlight banner asynchronously
      const recBanner = document.getElementById('catalog-recommendations-banner');
      const recList = document.getElementById('catalog-recommendations-list');
      ApiClient.getRecommendations(3).then(recs => {
        if (!document.getElementById('catalog-recommendations-list')) return;
        if (recBanner && recList && Array.isArray(recs) && recs.length > 0) {
          recList.innerHTML = recs.map(r => `
            <div class="bg-white/10 hover:bg-white/[0.14] backdrop-blur-xs rounded-xl p-4 border border-white/15 hover:border-indigo-400/40 flex flex-col justify-between space-y-3 transition-all duration-200 shadow-sm">
              <div>
                <div class="flex items-center justify-between text-[11px] font-mono text-indigo-200">
                  <span class="font-bold tracking-wide">${UI.escapeHtml(r.course_code)}</span>
                  <span class="px-2 py-0.5 rounded-md bg-indigo-500/30 text-indigo-100 border border-indigo-400/30 font-sans font-bold text-[10px]">${UI.escapeHtml(r.difficulty || 'Mới')}</span>
                </div>
                <h3 class="font-bold text-[#F8FAFC] text-sm mt-1.5 line-clamp-1">${UI.escapeHtml(r.title)}</h3>
                <p class="text-xs text-indigo-100/90 line-clamp-2 mt-1 leading-relaxed">${UI.escapeHtml(r.explanation || r.description || '')}</p>
              </div>
              <a href="#/student/courses/detail?id=${r.course_id}" class="w-full py-2 rounded-xl bg-white hover:bg-indigo-50 text-indigo-950 font-bold text-xs text-center transition-all shadow-sm hover:shadow active:scale-[0.99] flex items-center justify-center gap-1.5 cursor-pointer">
                <span>Xem khóa học</span>
                <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
              </a>
            </div>
          `).join('');
          recBanner.classList.remove('hidden');
        } else if (recBanner) {
          recBanner.classList.add('hidden');
        }
      }).catch(() => {
        const b = document.getElementById('catalog-recommendations-banner');
        if (b) b.classList.add('hidden');
      });

      renderFiltered();
    } catch (err) {
      grid.innerHTML = `
        <div class="col-span-full p-8 rounded-2xl bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/50 text-center space-y-3 shadow-sm">
          <span class="material-symbols-outlined text-3xl text-rose-500">sync_problem</span>
          <p class="text-sm font-bold text-slate-900 dark:text-white">Không thể nạp danh mục khóa học</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">${UI.escapeHtml(err.message || 'Lỗi kết nối máy chủ.')}</p>
          <button type="button" class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-1 cursor-pointer" onclick="UI.refreshCurrentRoute()">
            <span class="material-symbols-outlined text-[14px]">refresh</span>
            <span>Thử lại</span>
          </button>
        </div>
      `;
    }

    if (searchInput) searchInput.oninput = renderFiltered;
    if (categorySelect) categorySelect.onchange = renderFiltered;
  }

  static async openEnrollmentModal(courseOrId, onEnrolledCallback = null) {
    try {
      let course = (typeof courseOrId === 'object' && courseOrId !== null)
        ? courseOrId
        : await ApiClient.getCourseDetail(courseOrId);
      if (!course) return;
      const courseObj = course.course ? { ...course.course, lessons: course.lessons || [] } : course;
      course = courseObj;

      const courseId = course.id || course.public_id || (typeof courseOrId === 'string' ? courseOrId : '');

      const lessons = course.lessons || [];
      const lessonCount = lessons.length;
      const capacityText = 'Không giới hạn';
      const instructorName = course.instructor_name || 'Hội đồng Khoa học & Bộ môn';

      const body = `
        <div class="space-y-5">
          <!-- Course Hero Info Bar -->
          <div class="p-5 rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-1 rounded-md bg-primary text-white font-mono text-xs font-bold">${UI.escapeHtml(course.course_code || 'PWD301')}</span>
                <span class="px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold">${UI.escapeHtml(course.category || 'Chuyên ngành')}</span>
                ${UI.statusBadge(course.status)}
              </div>
              <h2 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">${UI.escapeHtml(course.title)}</h2>
            </div>
            <div class="text-right sm:shrink-0">
              <span class="text-[11px] uppercase tracking-wider text-slate-400 font-bold block">Độ khó</span>
              <span class="font-bold text-sm text-slate-800 dark:text-slate-200">${UI.escapeHtml(course.difficulty || 'Tiêu chuẩn')}</span>
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500">Mô tả khóa học</h4>
            <p class="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
              ${UI.escapeHtml(course.description || course.summary || 'Khóa học cung cấp hệ thống kiến thức toàn diện, bám sát thực tế cùng các bài tập thực hành chuyên sâu.')}
            </p>
          </div>

          <!-- 3-Column Highlights Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 space-y-1">
              <div class="flex items-center gap-1.5 text-slate-400 text-xs">
                <span class="material-symbols-outlined text-[16px] text-primary">person</span>
                <span>Giảng viên</span>
              </div>
              <div class="font-bold text-xs text-slate-900 dark:text-white truncate">${UI.escapeHtml(instructorName)}</div>
            </div>

            <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 space-y-1">
              <div class="flex items-center gap-1.5 text-slate-400 text-xs">
                <span class="material-symbols-outlined text-[16px] text-primary">menu_book</span>
                <span>Chương trình học</span>
              </div>
              <div class="font-bold text-xs text-slate-900 dark:text-white">${lessonCount} bài giảng & tài liệu</div>
            </div>

            <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 space-y-1">
              <div class="flex items-center gap-1.5 text-slate-400 text-xs">
                <span class="material-symbols-outlined text-[16px] text-primary">group</span>
                <span>Sĩ số lớp học</span>
              </div>
              <div class="font-bold text-xs text-slate-900 dark:text-white">${capacityText}</div>
            </div>
          </div>

          <!-- Syllabus Preview Highlights -->
          ${lessons.length > 0 ? `
            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs text-slate-500 font-bold uppercase tracking-wider">
                <span>Nội dung bài học tiêu biểu</span>
                <span>${lessons.length} bài học</span>
              </div>
              <div class="border border-slate-200 dark:border-slate-800 rounded-xl divide-y divide-slate-100 dark:divide-slate-800 max-h-44 overflow-y-auto bg-white dark:bg-slate-900">
                ${lessons.slice(0, 6).map((les, idx) => `
                  <div class="p-2.5 flex items-center justify-between text-xs">
                    <div class="flex items-center gap-2.5 truncate">
                      <span class="w-5 h-5 rounded-md bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-mono text-[10px] font-bold text-slate-500">${idx + 1}</span>
                      <span class="font-medium text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(les.title)}</span>
                    </div>
                  </div>
                `).join('')}
                ${lessons.length > 6 ? `
                  <div class="p-2 text-center text-xs text-slate-400 font-medium bg-slate-50/50 dark:bg-slate-800/30">
                    và ${lessons.length - 6} bài giảng bổ trợ khác...
                  </div>
                ` : ''}
              </div>
            </div>
          ` : ''}

          <!-- Enrollment Benefit Note -->
          <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-800/40 flex items-center gap-2 text-xs text-amber-800 dark:text-amber-300">
            <span class="material-symbols-outlined text-[18px] text-amber-600 shrink-0">info</span>
            <span>Sau khi ghi danh, khóa học sẽ xuất hiện ngay trong <strong>Khóa học của tôi</strong> để bạn bắt đầu học tập và làm bài kiểm tra.</span>
          </div>
        </div>
      `;

      const footer = `
        <button type="button" class="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 transition-colors" onclick="UI.closeModal()">
          Để sau
        </button>
        <a href="#/student/courses/detail?id=${courseId}" class="px-4 py-2.5 rounded-xl text-xs font-bold text-primary hover:bg-primary/10 transition-colors" onclick="UI.closeModal()">
          Xem chi tiết môn học
        </a>
        <button type="button" class="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-md shadow-primary/20 flex items-center gap-1.5 cursor-pointer" id="modal-confirm-enroll-btn">
          <span class="material-symbols-outlined text-[16px]">school</span>
          <span>Xác nhận ghi danh môn học</span>
        </button>
      `;

      UI.openModal({
        title: `Ghi danh khóa học: ${course.title}`,
        bodyHtml: body,
        footerHtml: footer,
        size: 'lg'
      });

      const confirmBtn = document.getElementById('modal-confirm-enroll-btn');
      if (confirmBtn) {
        confirmBtn.onclick = async () => {
          confirmBtn.disabled = true;
          confirmBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang ghi danh...';
          try {
            await ApiClient.enrollCourse(courseId);
            UI.closeModal();
            UI.showToast(`Đã ghi danh thành công khóa học: ${course.title}`, 'success');
            if (typeof onEnrolledCallback === 'function') {
              onEnrolledCallback(courseId);
            } else {
              window.location.hash = '#/student/courses';
            }
          } catch (err) {
            UI.showToast(err.message || 'Không thể ghi danh môn học.', 'error');
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">school</span> <span>Xác nhận ghi danh môn học</span>';
          }
        };
      }
    } catch (e) {
      UI.showToast('Không thể nạp thông tin chi tiết môn học.', 'error');
    }
  }

  static async openCourseDetailModal(courseId) {
    await StudentView.openEnrollmentModal(courseId);
  }

  // =========================================================================
  // 3. Enrolled Courses Hub (My Learning)
  // =========================================================================
  static async renderMyLearning(container) {
    container.innerHTML = `
      <div class="py-6 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in">
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
          const progress = Math.round(e.current_progress_percent ?? e.progress_percent ?? 0);
          return `
            <div class="c-card c-card-hover p-5 flex flex-col justify-between space-y-4">
              <div class="space-y-2.5">
                <div class="aspect-video w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 cursor-pointer" onclick="window.location.hash = '#/student/courses/detail?id=${e.course_id}'">
                  ${e.thumbnail_url ? `
                    <img src="${UI.escapeHtml(e.thumbnail_url)}" alt="${UI.escapeHtml(e.course_title)}" class="w-full h-full object-cover object-center hover:scale-105 transition-transform duration-300" onerror="this.remove()" />
                  ` : `
                    <div class="w-full h-full flex flex-col items-center justify-center text-slate-400 gap-1 p-4">
                      <span class="material-symbols-outlined text-[28px] text-primary/40">school</span>
                      <span class="text-[11px] font-semibold">${UI.escapeHtml(e.course_code || 'Khóa học')}</span>
                    </div>
                  `}
                </div>
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
                  ${e.status === 'ACTIVE' ? `
                  <button
                    type="button"
                    class="leave-course-btn c-btn c-btn-secondary c-btn-sm text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                    data-id="${e.course_id}"
                    data-title="${UI.escapeHtml(e.course_title)}"
                    title="Rút khỏi môn học"
                  >
                    <span class="material-symbols-outlined text-[18px]">logout</span>
                  </button>
                  ` : ''}
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
  // 4. Cisco NetAcad Unified Learning Console (Immersive Course Classroom)
  // Merges Course Hub & Lesson Reader into a single Cisco NetAcad-style Console:
  // - Left Sidebar: Search, Tabs [Course Outline] & [Resources], Smart Accordion,
  //   Modules with progress badges (0/12, 100%), sub-item dotted connectors,
  //   integrated Checkpoint Exams.
  // - Right Canvas: Floating [<] [>] navigation chevrons, exact NetAcad Locked Content card,
  //   Video Player (Anti-seek & 100% watch enforcement), Markdown reader, Mini-Quiz,
  //   Lesson attachments, AI Assistant, Sổ tay ghi chú with autosave.
  // =========================================================================
  static async renderCourseConsole(container, courseId, initialLessonId = null, initialExamId = null, initialTab = 'outline') {
    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans animate-fade-in select-none" id="cisco-console-root">
        <div class="flex-1 flex items-center justify-center text-slate-400">
          <div class="text-center space-y-2">
            <span class="inline-block animate-spin text-3xl">⏳</span>
            <p class="text-xs sm:text-sm font-semibold text-slate-500 dark:text-slate-400">Đang khởi tạo Không gian học tập Cisco NetAcad...</p>
          </div>
        </div>
      </div>
    `;

    try {
      // 1. Fetch course details and student learning progress in parallel
      const [courseData, progressData] = await Promise.all([
        ApiClient.getStudentCourseDetail(courseId).catch(() => ApiClient.getCourseDetail(courseId)),
        ApiClient.getStudentCourseProgress(courseId).catch(() => null)
      ]);

      const course = courseData?.course || courseData;
      if (!course || !course.id) {
        container.innerHTML = `
          <div class="h-full flex items-center justify-center p-6 text-center">
            <div class="max-w-md p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3">
              <span class="material-symbols-outlined text-4xl text-rose-500">error</span>
              <h2 class="text-base font-bold text-slate-900 dark:text-white">Không tìm thấy khóa học</h2>
              <p class="text-xs text-slate-500">Khóa học không tồn tại hoặc đã bị gỡ bỏ.</p>
              <a href="#/student/courses" class="c-btn c-btn-primary c-btn-sm inline-flex">Quay lại Khóa học của tôi</a>
            </div>
          </div>
        `;
        return;
      }

      const allLessons = courseData?.lessons || course.lessons || [];
      const allAssessments = courseData?.assessments || course.assessments || [];
      const allResources = courseData?.resources || course.resources || [];
      const learningUnits = courseData?.learning_units || [];
      const isPreview = (window.location.hash.includes('preview=1') || window.location.hash.includes('preview=true'));
      const canBypassLock = (window.location.hash.includes('bypass=1') || window.location.hash.includes('bypass=true'));
      const isInstructorOrAdmin = (window.app?.currentRole === 'INSTRUCTOR' || window.app?.currentRole === 'ADMIN' || localStorage.getItem('pwd301_role') === 'INSTRUCTOR' || localStorage.getItem('pwd301_role') === 'ADMIN');
      const isEnrolled = !!(courseData?.enrollment || progressData?.is_enrolled || progressData?.progress_percent !== undefined) || isInstructorOrAdmin || isPreview;

      // Group modules & build structured headlist
      let modules = [];
      if (learningUnits && learningUnits.length > 0) {
        modules = learningUnits.map((u, uIdx) => {
          const uLessons = (u.lessons && u.lessons.length > 0)
            ? [...u.lessons].sort((a, b) => (a.position || 0) - (b.position || 0))
            : allLessons.filter(l => String(l.learning_unit_id) === String(u.learning_unit_id || u.id));
          const uAssessments = allAssessments.filter(a => String(a.learning_unit_id) === String(u.learning_unit_id || u.id));
          return {
            id: String(u.learning_unit_id || u.id || `unit-${uIdx}`),
            title: u.title || `Module ${uIdx + 1}`,
            position: u.position || uIdx + 1,
            lessons: uLessons,
            assessments: uAssessments
          };
        });
      } else {
        const map = new Map();
        allLessons.forEach((l) => {
          const uId = String(l.learning_unit_id || 'default-module');
          const uTitle = l.learning_unit_title || 'Module 1: Chương trình học tập';
          if (!map.has(uId)) {
            map.set(uId, { id: uId, title: uTitle, position: map.size + 1, lessons: [], assessments: [] });
          }
          map.get(uId).lessons.push(l);
        });
        modules = Array.from(map.values());
        if (modules.length === 0) {
          modules = [{ id: 'module-1', title: 'Module 1: Nội dung khóa học', position: 1, lessons: [], assessments: allAssessments }];
        } else {
          allAssessments.forEach(a => {
            if (!a.learning_unit_id && modules.length > 0) {
              modules[modules.length - 1].assessments.push(a);
            }
          });
        }
      }

      // Calculate sequential unlock status across all lessons and items
      let seqIndex = 0;
      let prevLessonCompleted = true;
      const flatNavList = [];

      modules.forEach((mod, mIdx) => {
        let modCompletedLessons = 0;
        mod.lessons.forEach((les, lIdx) => {
          const isDone = Boolean(les.is_completed || les.progress?.is_completed);
          if (isDone) modCompletedLessons++;

          const isUnlocked = canBypassLock || (seqIndex === 0) || prevLessonCompleted;
          les._isUnlocked = isUnlocked;
          les._isCompleted = isDone;
          les._seqIndex = seqIndex;
          les._moduleTitle = mod.title;
          les._modulePosition = mod.position || mIdx + 1;
          les._displayCode = `${les._modulePosition}.${lIdx + 1}`;

          flatNavList.push({
            type: 'lesson',
            id: String(les.lesson_id || les.id),
            title: les.title,
            displayCode: les._displayCode,
            moduleId: mod.id,
            moduleTitle: mod.title,
            isUnlocked: isUnlocked,
            isCompleted: isDone,
            data: les
          });

          prevLessonCompleted = isDone;
          seqIndex++;
        });

        mod.assessments.forEach((asm, aIdx) => {
          const isAsmDone = (asm.attempts_count > 0 && asm.is_attempt_limit_reached) || asm.passed;
          asm._isCompleted = isAsmDone;
          const chapterLessonsAllDone = (mod.lessons.length === 0) || (modCompletedLessons >= mod.lessons.length);
          asm._isUnlocked = canBypassLock || chapterLessonsAllDone;
          asm._lockReason = asm._isUnlocked ? '' : `Bạn cần hoàn thành tất cả ${mod.lessons.length} bài học trong chương "${mod.title}" trước khi làm bài kiểm tra này.`;
          asm._moduleTitle = mod.title;

          flatNavList.push({
            type: 'exam',
            id: String(asm.assessment_id || asm.id),
            title: asm.title,
            displayCode: `Bài kiểm tra ${mIdx + 1}.${aIdx + 1}`,
            moduleId: mod.id,
            moduleTitle: mod.title,
            isUnlocked: asm._isUnlocked,
            lockReason: asm._lockReason,
            isCompleted: isAsmDone,
            data: asm
          });
        });

        mod._completedCount = modCompletedLessons;
        mod._totalCount = mod.lessons.length;
        mod._isCompleted = mod.lessons.length > 0 && modCompletedLessons === mod.lessons.length;
      });

      // Add standalone course-level assessments (Dedicated Final Test Block)
      const attachedExamIds = new Set(modules.flatMap(m => m.assessments.map(a => String(a.assessment_id || a.id))));
      const rootExams = allAssessments.filter(a => !attachedExamIds.has(String(a.assessment_id || a.id)));
      if (rootExams.length > 0) {
        const totalCourseLessons = modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0);
        const totalCompletedLessons = modules.reduce((acc, m) => acc + (m._completedCount || 0), 0);
        const allCourseLessonsCompleted = totalCourseLessons === 0 || totalCompletedLessons >= totalCourseLessons;
        const now = new Date();

        rootExams.forEach((asm, rIdx) => {
          const isAsmDone = (asm.attempts_count > 0 && asm.is_attempt_limit_reached) || asm.passed;
          asm._isCompleted = isAsmDone;

          const openTime = asm.open_at || asm.opens_at ? new Date(asm.open_at || asm.opens_at) : null;
          const closeTime = asm.close_at || asm.closes_at ? new Date(asm.close_at || asm.closes_at) : null;
          let isWithinWindow = true;
          let timeWindowMsg = '';

          if (openTime && !isNaN(openTime.getTime()) && now < openTime) {
            isWithinWindow = false;
            timeWindowMsg = `Bài thi chưa mở (Thời gian mở: ${UI.formatDate(openTime)}).`;
          } else if (closeTime && !isNaN(closeTime.getTime()) && now > closeTime) {
            isWithinWindow = false;
            timeWindowMsg = `Bài thi đã kết thúc (Thời gian đóng: ${UI.formatDate(closeTime)}).`;
          }

          let lockReason = '';
          if (!allCourseLessonsCompleted) {
            lockReason = `Bạn cần hoàn thành tất cả các bài học trong toàn bộ khóa học (${totalCompletedLessons}/${totalCourseLessons} bài) trước khi làm Final Test.`;
          } else if (!isWithinWindow) {
            lockReason = timeWindowMsg;
          }

          asm._isUnlocked = canBypassLock || (allCourseLessonsCompleted && isWithinWindow);
          asm._lockReason = lockReason;
          asm._isFinalTest = true;

          flatNavList.push({
            type: 'exam',
            id: String(asm.assessment_id || asm.id),
            title: asm.title,
            displayCode: `Final Test`,
            moduleId: 'root-exams',
            moduleTitle: 'Khảo thí & Đánh giá Cuối khóa',
            isUnlocked: asm._isUnlocked,
            lockReason: asm._lockReason,
            isCompleted: isAsmDone,
            isFinalTest: true,
            data: asm
          });
        });
      }

      // Initial active item determination (Auto-Resume)
      let activeItem = null;
      if (initialExamId) {
        activeItem = flatNavList.find(i => i.type === 'exam' && String(i.id) === String(initialExamId)) || null;
      }
      if (!activeItem && initialLessonId) {
        activeItem = flatNavList.find(i => i.type === 'lesson' && String(i.id) === String(initialLessonId)) || null;
      }
      if (!activeItem) {
        const incompleteUnlockedLesson = flatNavList.find(i => i.type === 'lesson' && !i.isCompleted && i.isUnlocked);
        activeItem = incompleteUnlockedLesson || flatNavList.find(i => i.type === 'lesson') || flatNavList[0] || null;
      }

      // Helper to detect non-learning or cover assets (Rule: pure learning resources only)
      const isCoverAsset = (r) => {
        if (!r) return true;
        const fn = String(r.filename || r.name || r.label || '').toLowerCase();
        return (
          fn.includes('_cover') ||
          fn.includes('cover_image') ||
          r.asset_type === 'COURSE_IMAGE' ||
          r.asset_type === 'QUESTION_IMAGE' ||
          r.asset_type === 'IMPORT_SOURCE'
        );
      };

      // Collect all attached resource IDs across all lessons to isolate course-level general files
      const attachedAssetIds = new Set();
      modules.forEach(mod => {
        (mod.lessons || []).forEach(les => {
          (les.resources || []).forEach(r => {
            if (isCoverAsset(r)) return;
            const aid = r.asset_id || r.file_asset?.public_id || r.file_asset?.id || r.id;
            if (aid) attachedAssetIds.add(String(aid));
            if (r.resource_id) attachedAssetIds.add(String(r.resource_id));
            if (r.filename) attachedAssetIds.add(String(r.filename));
          });
        });
      });

      // General course resources: files not attached to any specific lesson
      const generalCourseResources = (allResources || []).filter(r => {
        if (isCoverAsset(r)) return false;
        const aid = r.asset_id || r.resource_id || r.id;
        const fn = r.filename;
        if (aid && attachedAssetIds.has(String(aid))) return false;
        if (fn && attachedAssetIds.has(String(fn))) return false;
        return true;
      });

      // Total valid study resource count
      let totalLessonResourcesCount = 0;
      modules.forEach(mod => {
        (mod.lessons || []).forEach(les => {
          const lRes = (les.resources || []).filter(r => !isCoverAsset(r));
          totalLessonResourcesCount += lRes.length;
        });
      });
      const totalResourceCount = totalLessonResourcesCount + generalCourseResources.length;

      // Track active tabs & expanded accordion module IDs
      let currentTab = (initialTab === 'resources' || initialTab === 'ai') ? initialTab : 'outline';
      let searchQuery = '';
      const expandedModuleIds = new Set();
      if (activeItem && activeItem.moduleId) {
        expandedModuleIds.add(activeItem.moduleId);
      } else if (modules.length > 0) {
        expandedModuleIds.add(modules[0].id);
      }

      // Resources Accordion Expanded Sets
      const expandedResModuleIds = new Set();
      const expandedResLessonIds = new Set();
      let expandedResGeneral = true;

      // Default expand active lesson and its chapter in Resources tab
      if (activeItem && activeItem.type === 'lesson') {
        if (activeItem.moduleId) expandedResModuleIds.add(String(activeItem.moduleId));
        expandedResLessonIds.add(String(activeItem.id));
      }

      // If active item has no resources or none expanded, auto-expand the first module & lesson that has files
      let autoExpanded = false;
      for (const mod of modules) {
        for (const les of (mod.lessons || [])) {
          const lRes = (les.resources || []).filter(r => !isCoverAsset(r));
          if (lRes.length > 0) {
            if (expandedResModuleIds.size === 0) {
              expandedResModuleIds.add(String(mod.id));
              expandedResLessonIds.add(String(les.lesson_id || les.id));
            }
            autoExpanded = true;
            break;
          }
        }
        if (autoExpanded && expandedResModuleIds.size > 0) break;
      }

      // Overall Progress Calculation
      const rawProgVal = progressData?.current_progress_percent ?? progressData?.progress_percent ?? courseData?.enrollment?.current_progress_percent ?? courseData?.enrollment?.progress_percent;
      const courseProgressPercent = rawProgVal !== undefined && rawProgVal !== null
        ? Math.round(rawProgVal)
        : (allLessons.length > 0 ? Math.round((allLessons.filter(l => l.is_completed || l.progress?.is_completed).length / allLessons.length) * 100) : 0);

      // Render Primary Shell
      container.innerHTML = `
        <div id="cisco-console-root" class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans">
          
          <!-- 1. Top Header Bar (Cisco NetAcad Style) -->
          <header class="h-14 px-4 sm:px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 z-20 select-none">
            <div class="flex items-center gap-3">
              <button
                type="button"
                id="sidebar-toggle-btn"
                class="p-2 rounded-xl text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Đóng / Mở Đề cương (Sidebar)"
              >
                <span class="material-symbols-outlined text-[20px]">menu</span>
              </button>

              <div class="h-4 w-px bg-slate-200 dark:bg-slate-800"></div>

              <div class="flex items-center gap-2 min-w-0">
                <span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-[11px] font-bold border border-slate-200 dark:border-slate-700 shrink-0">
                  ${UI.escapeHtml(course.code || 'PWD301')}
                </span>
                <h1 class="text-xs sm:text-sm font-extrabold text-slate-900 dark:text-white truncate max-w-[180px] sm:max-w-xs md:max-w-md" title="${UI.escapeHtml(course.title)}">
                  ${UI.escapeHtml(course.title)}
                </h1>





              </div>
            </div>

            <!-- Header Action Controls -->
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 text-xs font-bold border border-emerald-200 dark:border-emerald-800">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Tiến độ: <strong id="console-progress-percent">${courseProgressPercent}%</strong></span>
              </div>

              <div class="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>

              <a
                href="#/student/courses"
                id="console-exit-btn"
                class="p-1.5 sm:px-2.5 sm:py-1.5 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1 text-xs font-semibold cursor-pointer"
                title="Quay lại Khóa học của tôi"
              >
                <span class="material-symbols-outlined text-[18px]">close</span>
                <span class="hidden sm:inline">Thoát</span>
              </a>
            </div>
          </header>

          <!-- 2. Workspace Body: Left Sidebar + Right Content Canvas -->
          <div class="flex-1 flex overflow-hidden relative">
            
            <!-- Left Sidebar (Collapsible Cisco Headlist Tree) -->
            <aside
              id="cisco-console-sidebar"
              class="w-80 sm:w-88 md:w-96 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col shrink-0 overflow-hidden transition-all duration-300 z-10"
            >
              <!-- Triple Tabs: Course Outline, Resources & Bạch tuộc AI -->
              <div class="h-12 border-b border-slate-200 dark:border-slate-800 grid grid-cols-3 text-xs font-bold select-none shrink-0" id="sidebar-tab-strip">
                <button
                  type="button"
                  id="tab-btn-outline"
                  class="flex items-center justify-center gap-1.5 border-b-2 transition-all cursor-pointer ${currentTab === 'outline' ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400 bg-emerald-50/30 dark:bg-emerald-950/20' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}"
                >
                  <span class="material-symbols-outlined text-[17px]">menu_book</span>
                  <span class="truncate">Đề cương</span>
                </button>
                <button
                  type="button"
                  id="tab-btn-resources"
                  class="flex items-center justify-center gap-1.5 border-b-2 transition-all cursor-pointer ${currentTab === 'resources' ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400 bg-emerald-50/30 dark:bg-emerald-950/20' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}"
                >
                  <span class="material-symbols-outlined text-[17px]">folder_open</span>
                  <span class="truncate" id="tab-resources-badge-label">Tài liệu (${totalResourceCount})</span>
                </button>
                <button
                  type="button"
                  id="tab-btn-ai"
                  class="flex items-center justify-center gap-1.5 border-b-2 transition-all cursor-pointer ${currentTab === 'ai' ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/30 dark:bg-indigo-950/20' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}"
                >
                  <span class="material-symbols-outlined text-[17px] text-indigo-500">smart_toy</span>
                  <span class="truncate">Trợ lý AI</span>
                </button>
              </div>

              <!-- Sidebar Panel 1: Course Outline -->
              <div id="sidebar-panel-outline" class="flex-1 flex flex-col overflow-hidden ${currentTab === 'outline' ? '' : 'hidden'}">
                <!-- Search Box -->
                <div class="p-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
                  <div class="relative">
                    <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-[18px]">search</span>
                    <input
                      id="outline-search-input"
                      type="text"
                      placeholder="Tìm kiếm đề cương khóa học..."
                      class="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:border-emerald-500 transition-all"
                    />
                    <button
                      type="button"
                      id="outline-search-clear"
                      class="hidden absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-[16px] cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px]">close</span>
                    </button>
                  </div>
                </div>

                <!-- Accordion Tree List -->
                <div class="flex-1 overflow-y-auto p-3 space-y-2.5 custom-scrollbar" id="outline-accordion-list">
                  <!-- Rendered dynamically -->
                </div>
              </div>

              <!-- Sidebar Panel 2: Resources Vault (Grouped by Chapter & Lesson) -->
              <div id="sidebar-panel-resources" class="flex-1 overflow-y-auto p-3 space-y-2.5 custom-scrollbar ${currentTab === 'resources' ? '' : 'hidden'}">
                <!-- Rendered dynamically by renderSidebarResources -->
              </div>

              <!-- Sidebar Panel 3: Bạch tuộc trợ lí AI Console -->
              <div id="sidebar-panel-ai" class="flex-1 flex flex-col overflow-hidden ${currentTab === 'ai' ? '' : 'hidden'} bg-slate-50/50 dark:bg-slate-900/50">
                <!-- Context header bar -->
                <div class="p-2.5 px-3 bg-indigo-50/80 dark:bg-indigo-950/40 border-b border-indigo-100 dark:border-indigo-900/50 flex items-center justify-between shrink-0">
                  <div class="flex items-center gap-1.5 min-w-0">
                    <span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse shrink-0"></span>
                    <span class="text-[11px] font-semibold text-indigo-900 dark:text-indigo-200 truncate" id="console-ai-context-label">
                      Ngữ cảnh: Toàn bộ khóa học
                    </span>
                  </div>
                  <button
                    type="button"
                    id="console-ai-new-chat-btn"
                    class="text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline font-medium shrink-0 flex items-center gap-0.5 cursor-pointer ml-1"
                    title="Bắt đầu hội thoại mới"
                  >
                    <span class="material-symbols-outlined text-[14px]">refresh</span> Làm mới
                  </button>
                </div>

                <!-- Messages container -->
                <div id="console-ai-messages" class="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar text-xs">
                  <div class="flex gap-2">
                    <div class="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0">
                      <span class="material-symbols-outlined text-[14px]">smart_toy</span>
                    </div>
                    <div class="bg-white dark:bg-slate-800 p-2.5 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-700 shadow-xs max-w-[85%] space-y-1">
                      <div class="font-bold text-slate-800 dark:text-slate-100 text-[11px]">Bạch tuộc trợ lí AI</div>
                      <div class="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                        Chào bạn! Mình có thể giải đáp kiến thức trong bài giảng, tóm tắt lý thuyết, giải thích câu hỏi hoặc hướng dẫn giải bài tập thực hành. Hãy đặt câu hỏi cho mình nhé!
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Prompt recommendation chips -->
                <div class="p-2 border-t border-slate-100 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 flex gap-1.5 overflow-x-auto no-scrollbar shrink-0" id="console-ai-chips">
                  <button type="button" class="console-prompt-chip px-2 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium border border-indigo-200/60 dark:border-indigo-800/60 shrink-0 cursor-pointer transition-colors" data-prompt="Giải thích ngắn gọn nội dung cốt lõi của bài học này giúp mình">
                    💡 Tóm tắt bài học
                  </button>
                  <button type="button" class="console-prompt-chip px-2 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium border border-indigo-200/60 dark:border-indigo-800/60 shrink-0 cursor-pointer transition-colors" data-prompt="Các khái niệm quan trọng nhất cần ghi nhớ là gì?">
                    🔑 Khái niệm cốt lõi
                  </button>
                  <button type="button" class="console-prompt-chip px-2 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium border border-indigo-200/60 dark:border-indigo-800/60 shrink-0 cursor-pointer transition-colors" data-prompt="Cho mình một ví dụ thực tế liên quan đến bài giảng này">
                    📌 Ví dụ thực tế
                  </button>
                </div>

                <!-- Chat Input Form -->
                <div class="p-2.5 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
                  <form id="console-ai-form" class="flex items-center gap-1.5">
                    <input
                      type="text"
                      id="console-ai-input"
                      placeholder="Hỏi Bạch tuộc AI về bài học..."
                      class="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:border-indigo-500 transition-all"
                      autocomplete="off"
                    />
                    <button
                      type="submit"
                      id="console-ai-send-btn"
                      class="p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-colors cursor-pointer shrink-0 disabled:opacity-50"
                      title="Gửi câu hỏi"
                    >
                      <span class="material-symbols-outlined text-[18px]">send</span>
                    </button>
                  </form>
                </div>
              </div>
            </aside>

            <!-- Right Content Canvas (Scrollable) -->
            <main
              id="cisco-console-canvas"
              class="flex-1 overflow-y-auto relative bg-slate-50 dark:bg-slate-950 p-4 sm:p-8 custom-scrollbar"
            >
              <!-- Floating Left [<] Navigation Chevron -->
              <button
                type="button"
                id="floating-prev-btn"
                class="fixed sm:absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-white dark:bg-slate-900 shadow-md border border-slate-200 dark:border-slate-800 flex items-center justify-center text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-slate-800 hover:scale-105 transition-all cursor-pointer"
                title="Bài phía trước"
              >
                <span class="material-symbols-outlined text-[22px]">chevron_left</span>
              </button>

              <!-- Floating Right [>] Navigation Chevron -->
              <button
                type="button"
                id="floating-next-btn"
                class="fixed sm:absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-white dark:bg-slate-900 shadow-md border border-slate-200 dark:border-slate-800 flex items-center justify-center text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-slate-800 hover:scale-105 transition-all cursor-pointer"
                title="Bài tiếp theo"
              >
                <span class="material-symbols-outlined text-[22px]">chevron_right</span>
              </button>

              <!-- Dynamic Inner Content Canvas -->
              <div id="cisco-inner-content" class="max-w-3xl mx-auto space-y-6">
                <!-- Injected via renderActiveContent() -->
              </div>
            </main>
          </div>
        </div>
      `;

      // -----------------------------------------------------------------------
      // Controller State & Methods
      // -----------------------------------------------------------------------
      let activeProgressTimer = null;
      let activeIframeMessageListener = null;
      let activeIframePollInterval = null;

      const cleanupPreviousLesson = () => {
        if (activeProgressTimer) {
          clearInterval(activeProgressTimer);
          activeProgressTimer = null;
        }
        if (activeIframePollInterval) {
          clearInterval(activeIframePollInterval);
          activeIframePollInterval = null;
        }
        if (activeIframeMessageListener) {
          window.removeEventListener('message', activeIframeMessageListener);
          activeIframeMessageListener = null;
        }
      };

      // Sidebar Toggle Handler
      const sidebarEl = document.getElementById('cisco-console-sidebar');
      const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
      if (sidebarToggleBtn && sidebarEl) {
        sidebarToggleBtn.onclick = () => {
          sidebarEl.classList.toggle('hidden');
        };
      }

      // Tab Switching Handler
      const tabBtnOutline = document.getElementById('tab-btn-outline');
      const tabBtnResources = document.getElementById('tab-btn-resources');
      const tabBtnAi = document.getElementById('tab-btn-ai');
      const panelOutline = document.getElementById('sidebar-panel-outline');
      const panelResources = document.getElementById('sidebar-panel-resources');
      const panelAi = document.getElementById('sidebar-panel-ai');

      const switchSidebarTab = (tab) => {
        currentTab = tab;
        const activeTabClass = 'flex items-center justify-center gap-1.5 border-b-2 border-emerald-600 text-emerald-600 dark:text-emerald-400 bg-emerald-50/30 dark:bg-emerald-950/20 transition-all cursor-pointer';
        const activeAiTabClass = 'flex items-center justify-center gap-1.5 border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/30 dark:bg-indigo-950/20 transition-all cursor-pointer';
        const inactiveTabClass = 'flex items-center justify-center gap-1.5 border-b-2 border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all cursor-pointer';

        if (tabBtnOutline) tabBtnOutline.className = tab === 'outline' ? activeTabClass : inactiveTabClass;
        if (tabBtnResources) tabBtnResources.className = tab === 'resources' ? activeTabClass : inactiveTabClass;
        if (tabBtnAi) tabBtnAi.className = tab === 'ai' ? activeAiTabClass : inactiveTabClass;

        if (panelOutline) panelOutline.classList.toggle('hidden', tab !== 'outline');
        if (panelResources) panelResources.classList.toggle('hidden', tab !== 'resources');
        if (panelAi) panelAi.classList.toggle('hidden', tab !== 'ai');

        if (tab === 'outline') {
          renderSidebarOutline();
        } else if (tab === 'resources') {
          renderSidebarResources();
        } else if (tab === 'ai') {
          updateAIContextBadge();
          const aiInput = document.getElementById('console-ai-input');
          if (aiInput) aiInput.focus();
        }
      };

      if (tabBtnOutline) tabBtnOutline.onclick = () => switchSidebarTab('outline');
      if (tabBtnResources) tabBtnResources.onclick = () => switchSidebarTab('resources');
      if (tabBtnAi) tabBtnAi.onclick = () => switchSidebarTab('ai');

      // AI Chat Controller inside NetAcad Course Console
      let consoleConvId = null;
      let isAiSending = false;

      const updateAIContextBadge = () => {
        const badge = document.getElementById('console-ai-context-label');
        if (!badge) return;
        if (activeItem && activeItem.type === 'lesson') {
          badge.textContent = `Ngữ cảnh: Bài học - ${activeItem.title}`;
          badge.title = `Bài học: ${activeItem.title}`;
        } else if (activeItem && activeItem.type === 'exam') {
          badge.textContent = `Ngữ cảnh: Khảo thí - ${activeItem.title}`;
          badge.title = `Khảo thí: ${activeItem.title}`;
        } else {
          badge.textContent = `Ngữ cảnh: Khóa học - ${course.title || 'Toàn khóa'}`;
          badge.title = `Khóa học: ${course.title}`;
        }
      };

      const appendConsoleAIMessage = (role, text) => {
        const msgContainer = document.getElementById('console-ai-messages');
        if (!msgContainer) return;
        const div = document.createElement('div');
        div.className = 'flex gap-2' + (role === 'user' ? ' justify-end' : '');
        if (role === 'user') {
          div.innerHTML = `
            <div class="bg-indigo-600 text-white p-2.5 rounded-2xl rounded-tr-sm shadow-xs max-w-[85%] text-[11px] leading-relaxed break-words whitespace-pre-wrap">
              ${UI.escapeHtml(text)}
            </div>
          `;
        } else {
          div.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-[14px]">smart_toy</span>
            </div>
            <div class="bg-white dark:bg-slate-800 p-2.5 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-700 shadow-xs max-w-[85%] space-y-1">
              <div class="font-bold text-slate-800 dark:text-slate-100 text-[11px]">Bạch tuộc trợ lí AI</div>
              <div class="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed prose prose-invert prose-xs max-w-none">
                ${UI.renderMarkdown ? UI.renderMarkdown(text) : UI.escapeHtml(text).replace(/\n/g, '<br/>')}
              </div>
            </div>
          `;
        }
        msgContainer.appendChild(div);
        msgContainer.scrollTop = msgContainer.scrollHeight;
      };

      const sendConsoleAIMessage = async (text) => {
        const query = (text || '').trim();
        if (!query || isAiSending) return;
        isAiSending = true;

        const sendBtn = document.getElementById('console-ai-send-btn');
        const inputEl = document.getElementById('console-ai-input');
        if (sendBtn) sendBtn.disabled = true;
        if (inputEl) inputEl.value = '';

        appendConsoleAIMessage('user', query);

        // Show typing indicator
        const msgContainer = document.getElementById('console-ai-messages');
        const typingId = 'console-ai-typing-' + Date.now();
        if (msgContainer) {
          const typingDiv = document.createElement('div');
          typingDiv.id = typingId;
          typingDiv.className = 'flex gap-2';
          typingDiv.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-[14px]">smart_toy</span>
            </div>
            <div class="bg-white dark:bg-slate-800 p-2.5 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-700 shadow-xs text-slate-500 text-[11px] flex items-center gap-1.5">
              <span class="inline-block animate-spin text-[12px]">⏳</span> Bạch tuộc đang suy nghĩ câu trả lời...
            </div>
          `;
          msgContainer.appendChild(typingDiv);
          msgContainer.scrollTop = msgContainer.scrollHeight;
        }

        try {
          const curLessonId = (activeItem && activeItem.type === 'lesson') ? activeItem.id : null;
          const res = await ApiClient.sendAIChat(query, consoleConvId, courseId, curLessonId);
          const typingEl = document.getElementById(typingId);
          if (typingEl) typingEl.remove();

          if (res && res.conversation_id) {
            consoleConvId = res.conversation_id;
          }
          const reply = res?.reply || res?.data?.reply || (typeof res?.assistant_message === 'string' ? res.assistant_message : res?.assistant_message?.content) || res?.message || res?.content || 'Xin lỗi bạn, mình chưa thể xử lý yêu cầu lúc này.';
          appendConsoleAIMessage('assistant', reply);
        } catch (err) {
          const typingEl = document.getElementById(typingId);
          if (typingEl) typingEl.remove();
          const errText = err?.data?.error?.message || err?.message || 'Lỗi mạng hoặc hệ thống tạm thời bận';
          appendConsoleAIMessage('assistant', `⚠️ Không thể gửi câu hỏi: ${errText}. Vui lòng thử lại sau ít phút.`);
        } finally {
          isAiSending = false;
          if (sendBtn) sendBtn.disabled = false;
          if (inputEl) inputEl.focus();
        }
      };

      // Form submit & Prompt chips listeners
      const aiForm = document.getElementById('console-ai-form');
      if (aiForm) {
        aiForm.onsubmit = (e) => {
          e.preventDefault();
          const val = document.getElementById('console-ai-input')?.value;
          sendConsoleAIMessage(val);
        };
      }

      document.querySelectorAll('.console-prompt-chip').forEach(btn => {
        btn.onclick = () => {
          const prompt = btn.dataset.prompt;
          if (prompt) {
            sendConsoleAIMessage(prompt);
          }
        };
      });

      const newChatBtn = document.getElementById('console-ai-new-chat-btn');
      if (newChatBtn) {
        newChatBtn.onclick = () => {
          consoleConvId = null;
          const msgContainer = document.getElementById('console-ai-messages');
          if (msgContainer) {
            msgContainer.innerHTML = `
              <div class="flex gap-2">
                <div class="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-[14px]">smart_toy</span>
                </div>
                <div class="bg-white dark:bg-slate-800 p-2.5 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-700 shadow-xs max-w-[85%] space-y-1">
                  <div class="font-bold text-slate-800 dark:text-slate-100 text-[11px]">Bạch tuộc trợ lí AI</div>
                  <div class="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                    Đã làm mới phiên thảo luận. Bạn muốn tìm hiểu hoặc cần mình giải đáp phần nào trong bài học này?
                  </div>
                </div>
              </div>
            `;
          }
          UI.showToast('Đã bắt đầu phiên trao đổi mới với Bạch tuộc AI', 'info');
        };
      }

      // Search Box in Outline
      const searchInput = document.getElementById('outline-search-input');
      const searchClear = document.getElementById('outline-search-clear');
      if (searchInput) {
        searchInput.oninput = (e) => {
          searchQuery = (e.target.value || '').trim().toLowerCase();
          if (searchClear) searchClear.classList.toggle('hidden', !searchQuery);
          renderSidebarOutline();
        };
      }
      if (searchClear && searchInput) {
        searchClear.onclick = () => {
          searchInput.value = '';
          searchQuery = '';
          searchClear.classList.add('hidden');
          renderSidebarOutline();
        };
      }

      // Render Outline Accordion
      const accordionContainer = document.getElementById('outline-accordion-list');
      const renderSidebarOutline = () => {
        if (!accordionContainer) return;

        const modulesHtml = modules.map((mod, mIdx) => {
          const modLessons = mod.lessons;
          const modExams = mod.assessments;

          // Search filter matching
          const matchesQuery = (text) => !searchQuery || String(text || '').toLowerCase().includes(searchQuery);
          const hasMatchingLesson = modLessons.some(l => matchesQuery(l.title));
          const hasMatchingExam = modExams.some(e => matchesQuery(e.title));
          const isModMatched = matchesQuery(mod.title) || hasMatchingLesson || hasMatchingExam;

          if (searchQuery && !isModMatched) {
            return '';
          }

          const isExpanded = searchQuery ? true : expandedModuleIds.has(mod.id);
          const modCompleted = mod._isCompleted;
          const modProgress = mod._totalCount > 0 ? `${mod._completedCount} / ${mod._totalCount}` : '';

          return `
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden transition-all shadow-2xs">
              <!-- Module Header Button -->
              <div
                class="p-3 flex items-center justify-between gap-2.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors select-none group/mod"
                data-mod-id="${mod.id}"
                onclick="window._ciscoToggleMod('${mod.id}')"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${modCompleted ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/80 dark:text-emerald-400' : 'bg-slate-100 text-slate-400 dark:bg-slate-800'}">
                    <span class="material-symbols-outlined text-[16px]">
                      ${modCompleted ? 'check' : 'radio_button_unchecked'}
                    </span>
                  </span>
                  <div class="min-w-0">
                    <h3 class="text-xs font-bold text-slate-900 dark:text-white truncate group-hover/mod:text-emerald-600 transition-colors" title="${UI.escapeHtml(mod.title)}">
                      ${UI.escapeHtml(mod.title)}
                    </h3>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  ${modProgress ? `
                    <span class="text-[11px] font-mono font-semibold text-slate-400">
                      ${modProgress}
                    </span>
                  ` : ''}
                  <span class="material-symbols-outlined text-[18px] text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180 text-emerald-600' : ''}">
                    expand_more
                  </span>
                </div>
              </div>

              <!-- Module Sub-Items (Expanded List with Dotted Connector Line) -->
              <div class="${isExpanded ? '' : 'hidden'} border-t border-slate-100 dark:border-slate-800/60 p-2 bg-slate-50/40 dark:bg-slate-950/30">
                <div class="relative pl-3 ml-2 border-l-2 border-dashed border-slate-300 dark:border-slate-700 space-y-1 py-1">
                  
                  <!-- Sub-Lessons -->
                  ${modLessons.map((l, lIdx) => {
                    const lId = String(l.lesson_id || l.id);
                    const isCur = activeItem && activeItem.type === 'lesson' && String(activeItem.id) === lId;
                    const isDone = l._isCompleted;
                    const isUnlocked = l._isUnlocked;
                    const displayCode = l._displayCode || `${mod.position || mIdx+1}.${lIdx+1}`;

                    if (!isUnlocked) {
                      return `
                        <div
                          class="p-2.5 rounded-xl text-slate-400 opacity-60 flex items-center justify-between gap-2 text-xs cursor-not-allowed select-none bg-slate-100/50 dark:bg-slate-800/30 border border-slate-200/50 dark:border-slate-800/50"
                          onclick="UI.showToast('Bài học đang bị khóa. Vui lòng hoàn thành bài học trước để mở khóa.', 'warning')"
                          title="Chưa mở khóa"
                        >
                          <div class="flex items-center gap-2 min-w-0">
                            <span class="material-symbols-outlined text-[16px] text-slate-400 shrink-0">lock</span>
                            <span class="truncate font-medium text-slate-400 dark:text-slate-500">${displayCode} ${UI.escapeHtml(l.title)}</span>
                          </div>
                          <span class="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-500 text-[10px] font-bold shrink-0">
                            Khóa
                          </span>
                        </div>
                      `;
                    }

                    return `
                      <div
                        class="p-2.5 rounded-xl transition-all cursor-pointer flex items-center justify-between gap-2 text-xs select-none ${isCur ? 'bg-emerald-50 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-100 border-l-4 border-emerald-600 font-bold shadow-2xs ring-1 ring-emerald-500/20' : 'text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'}"
                        onclick="window._ciscoSelectItem('lesson', '${lId}')"
                      >
                        <div class="flex items-center gap-2 min-w-0">
                          ${isCur ? `
                            <span class="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-xs animate-pulse" title="Đang học">
                              <span class="material-symbols-outlined text-[14px]">play_arrow</span>
                            </span>
                          ` : `
                            <span class="material-symbols-outlined text-[16px] shrink-0 ${isDone ? 'text-emerald-600' : 'text-slate-400'}">
                              ${isDone ? 'check_circle' : 'radio_button_unchecked'}
                            </span>
                          `}
                          <span class="truncate ${isCur ? 'font-bold text-emerald-900 dark:text-emerald-100' : 'font-medium'}">${displayCode} ${UI.escapeHtml(l.title)}</span>
                        </div>
                        ${isCur ? `
                          <span class="px-2 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-bold uppercase tracking-wider shrink-0 shadow-2xs flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                            <span>Đang học</span>
                          </span>
                        ` : (isDone ? `
                          <span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold shrink-0">
                            Đã xong
                          </span>
                        ` : '')}
                      </div>
                    `;
                  }).join('')}

                  <!-- Module Checkpoint Exams (Locked or Unlocked) -->
                  ${modExams.map((e) => {
                    const eId = String(e.assessment_id || e.id);
                    const isCur = activeItem && activeItem.type === 'exam' && String(activeItem.id) === eId;
                    const isDone = e._isCompleted;
                    const isUnlocked = e._isUnlocked;

                    if (!isUnlocked) {
                      return `
                        <div
                          class="p-2 rounded-xl text-slate-400 opacity-60 flex items-center justify-between gap-2 text-xs cursor-not-allowed select-none bg-slate-100/40 dark:bg-slate-800/20"
                          onclick="UI.showToast('${UI.escapeHtml(e._lockReason || 'Bài kiểm tra đang bị khóa.')}', 'warning')"
                          title="${UI.escapeHtml(e._lockReason || 'Chưa mở khóa')}"
                        >
                          <div class="flex items-center gap-2 min-w-0">
                            <span class="material-symbols-outlined text-[16px] text-slate-400 shrink-0">lock</span>
                            <span class="truncate font-medium">${UI.escapeHtml(e.title)}</span>
                          </div>
                          <span class="px-1.5 py-0.5 rounded bg-slate-200/60 dark:bg-slate-800 text-slate-500 text-[10px] font-bold shrink-0">
                            Khóa
                          </span>
                        </div>
                      `;
                    }

                    return `
                      <div
                        class="p-2 rounded-xl transition-all cursor-pointer flex items-center justify-between gap-2 text-xs select-none ${isCur ? 'bg-purple-50 dark:bg-purple-950/60 text-purple-950 dark:text-purple-100 border-l-4 border-purple-600 font-bold' : 'text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'}"
                        onclick="window._ciscoSelectItem('exam', '${eId}')"
                      >
                        <div class="flex items-center gap-2 min-w-0">
                          <span class="material-symbols-outlined text-[16px] shrink-0 ${isDone ? 'text-purple-600' : 'text-slate-400'}">
                            ${isDone ? 'task_alt' : 'assignment'}
                          </span>
                          <span class="truncate font-semibold">${UI.escapeHtml(e.title)}</span>
                        </div>
                        <span class="px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 text-[10px] font-bold shrink-0">
                          Bài kiểm tra
                        </span>
                      </div>
                    `;
                  }).join('')}

                </div>
              </div>
            </div>
          `;
        }).join('');

        let finalTestHtml = '';
        if (rootExams && rootExams.length > 0) {
          finalTestHtml = `
            <div class="mt-4 pt-3 border-t-2 border-dashed border-slate-200 dark:border-slate-800 space-y-2">
              <div class="px-1 flex items-center justify-between">
                <span class="text-[11px] font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400 flex items-center gap-1 font-mono">
                  <span class="material-symbols-outlined text-[15px]">military_tech</span>
                  Final Test
                </span>
                <span class="text-[10px] text-slate-400">Đánh giá cuối khóa</span>
              </div>
              ${rootExams.map(fe => {
                const feId = String(fe.assessment_id || fe.id);
                const isCur = activeItem && activeItem.type === 'exam' && String(activeItem.id) === feId;
                const isDone = fe._isCompleted;
                const isUnlocked = fe._isUnlocked;

                if (!isUnlocked) {
                  return `
                    <div
                      class="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 opacity-70 flex items-center justify-between gap-2 text-xs cursor-not-allowed select-none shadow-2xs"
                      onclick="UI.showToast('${UI.escapeHtml(fe._lockReason || 'Final Test chưa mở khóa.')}', 'warning')"
                      title="${UI.escapeHtml(fe._lockReason || 'Đang khóa')}"
                    >
                      <div class="flex items-center gap-2 min-w-0">
                        <span class="w-7 h-7 rounded-lg bg-slate-200/60 dark:bg-slate-800 text-slate-400 flex items-center justify-center shrink-0">
                          <span class="material-symbols-outlined text-[16px]">lock</span>
                        </span>
                        <div class="min-w-0">
                          <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 truncate">${UI.escapeHtml(fe.title)}</h4>
                          <p class="text-[10px] text-slate-400 truncate">${UI.escapeHtml(fe._lockReason || 'Hoàn thành các bài học trước khi thi')}</p>
                        </div>
                      </div>
                      <span class="px-1.5 py-0.5 rounded bg-slate-200/80 dark:bg-slate-800 text-slate-500 text-[10px] font-bold shrink-0">
                        Khóa
                      </span>
                    </div>
                  `;
                }

                return `
                  <div
                    class="p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-2 text-xs select-none shadow-2xs ${isCur ? 'border-purple-500 bg-purple-50/80 dark:bg-purple-950/60 text-purple-950 dark:text-purple-100 shadow-xs' : 'border-purple-200 dark:border-purple-800/80 bg-white dark:bg-slate-900 hover:border-purple-400 hover:shadow-xs'}"
                    onclick="window._ciscoSelectItem('exam', '${feId}')"
                  >
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="w-7 h-7 rounded-lg ${isDone ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/80' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/60'} flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-[16px]">${isDone ? 'task_alt' : 'assignment_turned_in'}</span>
                      </span>
                      <div class="min-w-0">
                        <h4 class="text-xs font-bold text-slate-900 dark:text-white truncate">${UI.escapeHtml(fe.title)}</h4>
                        <p class="text-[10px] text-purple-600 dark:text-purple-400">${fe.duration_minutes || 45} phút • ${fe.question_count || fe.total_questions || 30} câu hỏi</p>
                      </div>
                    </div>
                    <span class="px-2 py-0.5 rounded ${isDone ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-300' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/60 dark:text-purple-300'} text-[10px] font-bold shrink-0">
                      ${isDone ? 'Đã hoàn thành' : 'Sẵn sàng thi'}
                    </span>
                  </div>
                `;
              }).join('')}
            </div>
          `;
        }

        accordionContainer.innerHTML = modulesHtml + finalTestHtml;
      };

      // Render Resources Accordion (Grouped by Chapter & Lesson)
      const resourcesContainer = document.getElementById('sidebar-panel-resources');
      const renderSidebarResources = () => {
        if (!resourcesContainer) return;

        if (totalResourceCount === 0) {
          resourcesContainer.innerHTML = `
            <div class="text-center py-16 text-slate-400 text-xs space-y-2">
              <span class="material-symbols-outlined text-3xl text-slate-300 dark:text-slate-700">folder_off</span>
              <p>Khóa học hiện chưa có tệp tài liệu nào.</p>
            </div>
          `;
          return;
        }

        const renderFileItem = (r) => {
          const fname = r.filename || r.label || r.name || 'Tai-lieu.pdf';
          const ext = (fname.split('.').pop() || 'FILE').toUpperCase();
          const sizeBytes = r.byte_size || r.size_bytes || r.file_size;
          const sizeKb = sizeBytes ? Math.round(sizeBytes / 1024) : null;
          const sizeStr = sizeKb ? (sizeKb > 1024 ? `${(sizeKb / 1024).toFixed(1)} MB` : `${sizeKb} KB`) : '';
          const downloadUrl = r.download_url || `/student/files/${encodeURIComponent(r.asset_id || r.id || r.resource_id)}/download`;

          let badgeColor = 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800';
          if (['PDF'].includes(ext)) {
            badgeColor = 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border-rose-200 dark:border-rose-800';
          } else if (['MP4', 'WEBM', 'MKV', 'AVI', 'MOV'].includes(ext)) {
            badgeColor = 'bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-400 border-sky-200 dark:border-sky-800';
          } else if (['ZIP', 'RAR', '7Z', 'TAR', 'GZ'].includes(ext)) {
            badgeColor = 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-400 border-purple-200 dark:border-purple-800';
          } else if (['DOC', 'DOCX'].includes(ext)) {
            badgeColor = 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border-blue-200 dark:border-blue-800';
          } else if (['PPT', 'PPTX'].includes(ext)) {
            badgeColor = 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border-amber-200 dark:border-amber-800';
          }

          return `
            <div class="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 hover:border-emerald-500/50 hover:shadow-xs transition-all flex items-center justify-between gap-2.5 group">
              <div class="flex items-center gap-2.5 min-w-0">
                <span class="w-8 h-8 rounded-lg font-mono font-bold text-[10px] flex items-center justify-center shrink-0 border ${badgeColor}">
                  ${ext}
                </span>
                <div class="min-w-0">
                  <p class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate group-hover:text-emerald-600 transition-colors" title="${UI.escapeHtml(fname)}">
                    ${UI.escapeHtml(fname)}
                  </p>
                  ${sizeStr ? `<span class="text-[10px] text-slate-400 font-mono">${sizeStr}</span>` : ''}
                </div>
              </div>
              <a
                href="${downloadUrl}"
                download
                class="p-1.5 rounded-lg text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-colors shrink-0"
                title="Tải về ${UI.escapeHtml(fname)}"
              >
                <span class="material-symbols-outlined text-[18px]">download</span>
              </a>
            </div>
          `;
        };

        let html = `
          <div class="text-xs text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <span>Tài liệu bài giảng theo chương:</span>
            <span class="font-mono text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">${totalResourceCount} tệp</span>
          </div>
        `;

        // 1. General Course Resources Section (if any)
        if (generalCourseResources.length > 0) {
          const isGenExpanded = expandedResGeneral;
          html += `
            <div class="rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/20 dark:bg-indigo-950/20 overflow-hidden transition-all shadow-2xs">
              <div
                class="p-3 flex items-center justify-between gap-2.5 cursor-pointer hover:bg-indigo-50/60 dark:hover:bg-indigo-950/40 transition-colors select-none group/gen"
                onclick="window._ciscoToggleResGeneral()"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span class="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-200 dark:border-indigo-800">
                    <span class="material-symbols-outlined text-[18px]">school</span>
                  </span>
                  <div class="min-w-0">
                    <h3 class="text-xs font-bold text-slate-900 dark:text-white truncate group-hover/gen:text-indigo-600 transition-colors">
                      Tài liệu chung khóa học
                    </h3>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
                    ${generalCourseResources.length} tệp
                  </span>
                  <span class="material-symbols-outlined text-[18px] text-slate-400 transition-transform duration-200 ${isGenExpanded ? 'rotate-180 text-indigo-600' : ''}">
                    expand_more
                  </span>
                </div>
              </div>

              <div class="${isGenExpanded ? '' : 'hidden'} border-t border-indigo-100 dark:border-indigo-900/40 p-2.5 bg-white/60 dark:bg-slate-900/40 space-y-1.5">
                ${generalCourseResources.map(renderFileItem).join('')}
              </div>
            </div>
          `;
        }

        // 2. Chapters (Modules) Accordion
        modules.forEach((mod, mIdx) => {
          // Filter lessons that actually have resources
          const lessonsWithFiles = (mod.lessons || []).map((les, lIdx) => {
            const lRes = (les.resources || []).filter(r => !isCoverAsset(r));
            return {
              les,
              lIdx,
              lRes,
              lesId: String(les.lesson_id || les.id),
              displayCode: les._displayCode || `${mod.position || mIdx + 1}.${lIdx + 1}`
            };
          }).filter(item => item.lRes.length > 0);

          // If no lessons in this module have files, hide the module
          if (lessonsWithFiles.length === 0) return;

          const modTotalFiles = lessonsWithFiles.reduce((acc, item) => acc + item.lRes.length, 0);
          const isModExpanded = expandedResModuleIds.has(String(mod.id));

          html += `
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden transition-all shadow-2xs">
              <!-- Module Header Button -->
              <div
                class="p-3 flex items-center justify-between gap-2.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors select-none group/mod"
                onclick="window._ciscoToggleResMod('${mod.id}')"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span class="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-200/50 dark:border-emerald-800/50">
                    <span class="material-symbols-outlined text-[18px]">folder</span>
                  </span>
                  <div class="min-w-0">
                    <h3 class="text-xs font-bold text-slate-900 dark:text-white truncate group-hover/mod:text-emerald-600 transition-colors" title="${UI.escapeHtml(mod.title)}">
                      ${UI.escapeHtml(mod.title)}
                    </h3>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    ${modTotalFiles} tệp
                  </span>
                  <span class="material-symbols-outlined text-[18px] text-slate-400 transition-transform duration-200 ${isModExpanded ? 'rotate-180 text-emerald-600' : ''}">
                    expand_more
                  </span>
                </div>
              </div>

              <!-- Module Sub-Items (Lessons that have resources) -->
              <div class="${isModExpanded ? '' : 'hidden'} border-t border-slate-100 dark:border-slate-800/60 p-2.5 bg-slate-50/40 dark:bg-slate-950/30 space-y-2">
                ${lessonsWithFiles.map(({ les, lRes, lesId, displayCode }) => {
                  const isLesExpanded = expandedResLessonIds.has(lesId);
                  return `
                    <div class="rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-slate-900/50 overflow-hidden">
                      <!-- Lesson Header Toggle (does NOT navigate away, only toggles files) -->
                      <div
                        class="p-2.5 flex items-center justify-between gap-2 cursor-pointer hover:bg-slate-100/70 dark:hover:bg-slate-800/60 transition-colors select-none group/les"
                        onclick="window._ciscoToggleResLesson('${lesId}')"
                      >
                        <div class="flex items-center gap-2 min-w-0">
                          <span class="material-symbols-outlined text-[16px] text-slate-400 group-hover/les:text-emerald-600 transition-colors shrink-0">
                            description
                          </span>
                          <span class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate group-hover/les:text-emerald-600 transition-colors" title="${UI.escapeHtml(les.title)}">
                            ${displayCode} ${UI.escapeHtml(les.title)}
                          </span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0">
                          <span class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                            ${lRes.length} tệp
                          </span>
                          <span class="material-symbols-outlined text-[16px] text-slate-400 transition-transform duration-200 ${isLesExpanded ? 'rotate-180 text-emerald-600' : ''}">
                            expand_more
                          </span>
                        </div>
                      </div>

                      <!-- Lesson Files List (Collapsible) -->
                      <div class="${isLesExpanded ? '' : 'hidden'} p-2 space-y-1.5 border-t border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-950/40">
                        ${lRes.map(renderFileItem).join('')}
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        });

        resourcesContainer.innerHTML = html;
      };

      // Global window helpers for inline onclick
      window._ciscoToggleMod = (modId) => {
        if (expandedModuleIds.has(modId)) {
          expandedModuleIds.delete(modId);
        } else {
          expandedModuleIds.add(modId);
        }
        renderSidebarOutline();
      };

      // Global window helpers for inline onclick in Resources Tab
      window._ciscoToggleResMod = (modId) => {
        const idStr = String(modId);
        if (expandedResModuleIds.has(idStr)) {
          expandedResModuleIds.delete(idStr);
        } else {
          expandedResModuleIds.add(idStr);
        }
        renderSidebarResources();
      };

      window._ciscoToggleResLesson = (lesId) => {
        const idStr = String(lesId);
        if (expandedResLessonIds.has(idStr)) {
          expandedResLessonIds.delete(idStr);
        } else {
          expandedResLessonIds.add(idStr);
        }
        renderSidebarResources();
      };

      window._ciscoToggleResGeneral = () => {
        expandedResGeneral = !expandedResGeneral;
        renderSidebarResources();
      };

      window._ciscoSelectItem = (itemType, itemId) => {
        const target = flatNavList.find(i => i.type === itemType && String(i.id) === String(itemId));
        if (!target) return;

        if (target.type === 'lesson' && !target.isUnlocked) {
          UI.showToast('Vui lòng hoàn thành bài học trước để mở khóa bài học này.', 'warning');
          return;
        }

        if (target.type === 'exam' && !target.isUnlocked) {
          UI.showToast(target.lockReason || 'Bài kiểm tra này đang bị khóa.', 'warning');
          return;
        }

        activeItem = target;
        if (target.moduleId) {
          expandedModuleIds.add(target.moduleId);
          expandedResModuleIds.add(String(target.moduleId));
        }
        if (target.type === 'lesson') {
          expandedResLessonIds.add(String(target.id));
        }

        // Update URL hash via replaceState (Rule 10.7)
        const newHash = `#/student/courses/${encodeURIComponent(courseId)}?${itemType === 'exam' ? 'exam_id' : 'lesson_id'}=${encodeURIComponent(itemId)}`;
        window.history.replaceState(null, '', newHash);

        renderSidebarOutline();
        renderSidebarResources();
        renderActiveContent();
        updateFloatingNav();
        updateAIContextBadge();
      };

      // Floating [<] and [>] Nav Controller
      const prevBtn = document.getElementById('floating-prev-btn');
      const nextBtn = document.getElementById('floating-next-btn');

      const updateFloatingNav = () => {
        if (!activeItem || flatNavList.length === 0) {
          if (prevBtn) prevBtn.classList.add('hidden');
          if (nextBtn) nextBtn.classList.add('hidden');
          return;
        }

        const curIdx = flatNavList.findIndex(i => i.type === activeItem.type && String(i.id) === String(activeItem.id));
        const prevItem = curIdx > 0 ? flatNavList[curIdx - 1] : null;
        const nextItem = curIdx < flatNavList.length - 1 ? flatNavList[curIdx + 1] : null;

        if (prevBtn) {
          prevBtn.classList.toggle('hidden', !prevItem);
          if (prevItem) {
            prevBtn.title = `Bài phía trước: ${prevItem.title}`;
            prevBtn.onclick = () => window._ciscoSelectItem(prevItem.type, prevItem.id);
          }
        }

        if (nextBtn) {
          nextBtn.classList.toggle('hidden', !nextItem);
          if (nextItem) {
            nextBtn.title = `Bài tiếp theo: ${nextItem.title}`;
            nextBtn.onclick = () => window._ciscoSelectItem(nextItem.type, nextItem.id);
          }
        }
      };

      // Render Active Content in Main Pane
      const contentContainer = document.getElementById('cisco-inner-content');

      const renderActiveContent = async () => {
        cleanupPreviousLesson();
        if (!contentContainer) return;

        // If not enrolled: show Public Course Overview or Lesson Syllabus Preview
        if (!isEnrolled) {
          if (activeItem && activeItem.type === 'lesson') {
            contentContainer.innerHTML = `
              <div class="space-y-6 animate-fade-in">
                <!-- Top Sticky Enrollment Banner -->
                <div class="p-4 rounded-2xl bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0">
                      <span class="material-symbols-outlined text-[22px]">lock_open</span>
                    </div>
                    <div>
                      <div class="text-xs font-bold text-emerald-900 dark:text-emerald-200">Bạn đang xem trước đề cương khóa học</div>
                      <div class="text-[11px] text-emerald-700 dark:text-emerald-400">Ghi danh ngay để mở khóa toàn bộ video, tài liệu và làm bài kiểm tra.</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    id="console-enroll-btn"
                    class="w-full sm:w-auto px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-xs inline-flex items-center justify-center gap-1.5 cursor-pointer shrink-0"
                  >
                    <span class="material-symbols-outlined text-[16px]">how_to_reg</span>
                    <span>Ghi danh ngay</span>
                  </button>
                </div>

                <!-- Lesson Header & Objectives Preview -->
                <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 space-y-4 shadow-xs">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      ${UI.escapeHtml(activeItem.displayCode || 'Bài giảng')}
                    </span>
                    <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 flex items-center gap-1">
                      <span class="material-symbols-outlined text-[14px]">lock</span> Cần ghi danh
                    </span>
                  </div>

                  <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white leading-snug">
                    ${UI.escapeHtml(activeItem.title)}
                  </h1>

                  <div class="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-2">
                    <p class="font-medium text-slate-800 dark:text-slate-200">
                      Mục tiêu & Đề cương bài giảng:
                    </p>
                    <p class="text-slate-500 dark:text-slate-400">
                      ${UI.escapeHtml(activeItem.data?.summary || activeItem.data?.description || course.description || 'Bài học trang bị các kiến thức nền tảng và kỹ năng thực hành theo chuẩn ABET.')}
                    </p>
                  </div>

                  <!-- Locked Video / Content Placeholder -->
                  <div class="mt-6 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-950/40 p-8 sm:p-12 text-center space-y-3">
                    <div class="w-14 h-14 rounded-2xl bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center mx-auto">
                      <span class="material-symbols-outlined text-[28px]">smart_display</span>
                    </div>
                    <div class="space-y-1">
                      <h3 class="text-sm font-bold text-slate-800 dark:text-slate-200">Video bài giảng và bài tập thực hành được khóa</h3>
                      <p class="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                        Hãy ghi danh vào môn học để xem video trực tuyến, tài liệu đính kèm và nhận chứng chỉ hoàn thành môn học.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            `;
          } else {
            contentContainer.innerHTML = `
              <div class="py-8 px-4 text-center space-y-6 animate-fade-in">
                <div class="max-w-xl mx-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 sm:p-10 shadow-sm space-y-5">
                  <div class="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto border border-emerald-200 dark:border-emerald-800">
                    <span class="material-symbols-outlined text-[36px]">school</span>
                  </div>
                  <div class="space-y-2">
                    <h2 class="text-xl font-black text-slate-900 dark:text-white">Ghi danh để Bắt đầu Học tập</h2>
                    <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                      ${UI.escapeHtml(course.description || 'Tham gia khóa học để mở khóa toàn bộ lộ trình bài giảng, video hướng dẫn và các bài kiểm tra thực hành.')}
                    </p>
                  </div>
                  <div class="pt-2">
                    <button
                      type="button"
                      id="console-enroll-btn"
                      class="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-2 cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[18px]">how_to_reg</span>
                      <span>Ghi danh môn học ngay</span>
                    </button>
                  </div>
                </div>
              </div>
            `;
          }

          const enrollBtn = document.getElementById('console-enroll-btn');
          if (enrollBtn) {
            enrollBtn.onclick = async () => {
              try {
                enrollBtn.disabled = true;
                enrollBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang ghi danh...';
                await ApiClient.enrollCourse(course.id || courseId);
                UI.showToast(`Ghi danh thành công khóa học: ${course.title}`, 'success');
                await StudentView.renderCourseConsole(container, courseId, activeItem?.id || null);
              } catch (err) {
                UI.showToast(err.message || 'Không thể ghi danh.', 'error');
                enrollBtn.disabled = false;
                enrollBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">how_to_reg</span> <span>Ghi danh môn học ngay</span>';
              }
            };
          }
          return;
        }

        // If no active item
        if (!activeItem) {
          contentContainer.innerHTML = `
            <div class="py-20 text-center text-slate-400 space-y-2">
              <span class="material-symbols-outlined text-4xl text-slate-300">menu_book</span>
              <p class="text-sm">Hãy chọn một bài giảng trong đề cương bên trái để bắt đầu học.</p>
            </div>
          `;
          return;
        }

        // Case 1: Locked Lesson Content (Exact Cisco NetAcad Style)
        if (activeItem.type === 'lesson' && !activeItem.isUnlocked) {
          contentContainer.innerHTML = `
            <div class="flex-1 flex items-center justify-center p-6 sm:p-12 min-h-[500px] animate-fade-in">
              <div class="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 sm:p-10 shadow-sm text-center space-y-5">
                <div class="w-16 h-16 rounded-2xl bg-rose-50 dark:bg-rose-950/60 text-rose-500 flex items-center justify-center mx-auto border border-rose-100 dark:border-rose-900/60">
                  <span class="material-symbols-outlined text-[34px]">lock</span>
                </div>
                <div class="space-y-2">
                  <h2 class="text-xl font-black text-slate-900 dark:text-white">Nội dung bị khóa (Locked Content)</h2>
                  <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Nội dung của bài giảng này hiện chưa thể hiển thị vì đang bị khóa. Bạn cần hoàn thành bài giảng trước đó để mở khóa bài học này.
                  </p>
                </div>
                <div class="pt-2">
                  <button
                    type="button"
                    id="btn-back-to-unlocked"
                    class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all inline-flex items-center gap-2 cursor-pointer shadow-sm"
                  >
                    <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                    <span>Quay lại bài học đã mở</span>
                  </button>
                </div>
              </div>
            </div>
          `;

          const backBtn = document.getElementById('btn-back-to-unlocked');
          if (backBtn) {
            backBtn.onclick = () => {
              const lastUnlocked = flatNavList.filter(i => i.type === 'lesson' && i.isUnlocked).pop();
              if (lastUnlocked) window._ciscoSelectItem(lastUnlocked.type, lastUnlocked.id);
            };
          }
          return;
        }

        // Case 2: Checkpoint Exam / Final Test Selected
        if (activeItem.type === 'exam') {
          if (!activeItem.isUnlocked) {
            contentContainer.innerHTML = `
              <div class="flex-1 flex items-center justify-center p-6 sm:p-12 min-h-[500px] animate-fade-in">
                <div class="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 sm:p-10 shadow-sm text-center space-y-5">
                  <div class="w-16 h-16 rounded-2xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 flex items-center justify-center mx-auto border border-amber-200 dark:border-amber-900/60">
                    <span class="material-symbols-outlined text-[34px]">lock</span>
                  </div>
                  <div class="space-y-2">
                    <h2 class="text-xl font-black text-slate-900 dark:text-white">Bài kiểm tra bị khóa</h2>
                    <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      ${UI.escapeHtml(activeItem.lockReason || 'Bạn cần hoàn thành tất cả các bài học yêu cầu trước khi được phép làm bài kiểm tra này.')}
                    </p>
                  </div>
                  <div class="pt-2">
                    <button
                      type="button"
                      id="btn-back-to-unlocked-exam"
                      class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all inline-flex items-center gap-2 cursor-pointer shadow-sm"
                    >
                      <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                      <span>Quay lại bài học đã mở</span>
                    </button>
                  </div>
                </div>
              </div>
            `;
            const backBtn = document.getElementById('btn-back-to-unlocked-exam');
            if (backBtn) {
              backBtn.onclick = () => {
                const lastUnlocked = flatNavList.filter(i => i.type === 'lesson' && i.isUnlocked).pop();
                if (lastUnlocked) window._ciscoSelectItem(lastUnlocked.type, lastUnlocked.id);
              };
            }
            return;
          }

          contentContainer.innerHTML = `
            <div class="text-center py-16 text-slate-400">
              <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
              <p class="text-xs">Đang nạp hồ sơ khảo thí...</p>
            </div>
          `;

          try {
            const asmData = await ApiClient.getStudentAssessment(activeItem.id).catch(() => activeItem.data);
            const asm = asmData?.assessment || asmData || activeItem.data;
            const attemptsCount = asm.attempts_count || 0;
            const attemptLimit = asm.attempt_limit || 'Không giới hạn';
            const isLimitReached = Boolean(asm.is_attempt_limit_reached);
            const attemptsHistory = Array.isArray(asm.attempts) ? asm.attempts : [];

            contentContainer.innerHTML = `
              <div class="space-y-6 animate-fade-in select-none">
                <!-- Breadcrumb -->
                <div class="flex items-center gap-2 text-xs text-slate-400">
                  <span>${UI.escapeHtml(activeItem.moduleTitle || 'Khóa học')}</span>
                  <span>&rsaquo;</span>
                  <span class="font-bold text-slate-700 dark:text-slate-300">Bài kiểm tra Checkpoint</span>
                </div>

                <!-- Exam Hero Card -->
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
                  <div class="flex items-center gap-3">
                    <div class="w-12 h-12 rounded-2xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0 border border-purple-200 dark:border-purple-800">
                      <span class="material-symbols-outlined text-[26px]">quiz</span>
                    </div>
                    <div>
                      <h1 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                        ${UI.escapeHtml(asm.title)}
                      </h1>
                      <p class="text-xs text-slate-500 mt-1">${UI.escapeHtml(asm.description || 'Đánh giá kiến thức và kỹ năng thực hành qua bài kiểm tra.')}</p>
                    </div>
                  </div>

                  <!-- 4 Metrics Grid -->
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                    <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                      <span class="text-slate-400 block text-[11px]">Thời gian làm bài</span>
                      <strong class="text-sm font-bold text-slate-900 dark:text-white">${asm.duration_minutes || 45} phút</strong>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                      <span class="text-slate-400 block text-[11px]">Số lượng câu hỏi</span>
                      <strong class="text-sm font-bold text-slate-900 dark:text-white">${asm.question_count || asm.total_questions || 30} câu</strong>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                      <span class="text-slate-400 block text-[11px]">Điểm đạt chuẩn</span>
                      <strong class="text-sm font-bold text-emerald-600">${asm.passing_score || 50}%</strong>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                      <span class="text-slate-400 block text-[11px]">Lượt đã làm</span>
                      <strong class="text-sm font-bold text-slate-900 dark:text-white">${attemptsCount} / ${attemptLimit}</strong>
                    </div>
                  </div>

                  <!-- Historical Attempts Table -->
                  ${attemptsHistory.length > 0 ? `
                    <div class="pt-2 space-y-2">
                      <h4 class="text-xs font-bold text-slate-700 dark:text-slate-300">Lịch sử các lần làm bài:</h4>
                      <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs">
                          <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-bold border-b border-slate-200 dark:border-slate-800">
                            <tr>
                              <th class="p-3">Lần thi</th>
                              <th class="p-3">Thời gian nộp</th>
                              <th class="p-3">Điểm số</th>
                              <th class="p-3">Kết quả</th>
                            </tr>
                          </thead>
                          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                            ${attemptsHistory.map((att, idx) => `
                              <tr>
                                <td class="p-3 font-bold text-slate-900 dark:text-white">Lần ${idx + 1}</td>
                                <td class="p-3 text-slate-500">${att.submitted_at ? UI.formatDate(att.submitted_at) : 'Đang xử lý'}</td>
                                <td class="p-3 font-mono font-bold text-slate-900 dark:text-white">${att.score !== null && att.score !== undefined ? `${att.score} / ${att.max_score || 100}` : 'Chờ công bố'}</td>
                                <td class="p-3">
                                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${att.passed ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'}">
                                    ${att.passed ? 'Đạt' : 'Chưa đạt'}
                                  </span>
                                </td>
                              </tr>
                            `).join('')}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ` : ''}

                  <!-- Action Buttons -->
                  <div class="pt-4 flex items-center justify-between">
                    <div></div>
                    <div class="flex items-center gap-3">
                      ${isLimitReached ? `
                        <div class="flex items-center gap-2">
                          <span class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-bold">
                            Đã hết lượt làm bài (${attemptsCount}/${attemptLimit})
                          </span>
                          ${asm.latest_attempt_id ? `
                            <a
                              href="#/student/assessments/attempts/${asm.latest_attempt_id}/results"
                              class="c-btn c-btn-secondary c-btn-sm"
                            >
                              Xem lại kết quả
                            </a>
                          ` : ''}
                        </div>
                      ` : `
                        <a
                          href="#/student/assessments/waiting-room?id=${asm.assessment_id || asm.id}"
                          class="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-2 cursor-pointer"
                        >
                          <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                          <span>Bắt đầu làm bài thi</span>
                        </a>
                      `}
                    </div>
                  </div>
                </div>
              </div>
            `;
          } catch (err) {
            contentContainer.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp bài kiểm tra: ${UI.escapeHtml(err.message)}</div>`;
          }
          return;
        }

        // Case 3: Unlocked Lesson Content
        contentContainer.innerHTML = `
          <div class="text-center py-20 text-slate-400">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-xs">Đang nạp bài giảng...</p>
          </div>
        `;

        const expectedLessonId = String(activeItem.id);
        try {
          const lesson = await ApiClient.getStudentLesson(courseId, expectedLessonId);
          if (!activeItem || String(activeItem.id) !== expectedLessonId) {
            return;
          }

          // Multi-tier Video Detection: video_url -> video_urls array -> lesson resources
          let activeVideoUrl = lesson.video_url || null;
          if (!activeVideoUrl && Array.isArray(lesson.video_urls) && lesson.video_urls.length > 0) {
            activeVideoUrl = lesson.video_urls[0];
          }
          if (!activeVideoUrl && Array.isArray(lesson.resources)) {
            const vidRes = lesson.resources.find(r => {
              const mime = (r.file_asset?.mime_type || r.mime_type || '').toLowerCase();
              const fn = (r.file_asset?.original_filename || r.filename || r.label || '').toLowerCase();
              return mime.startsWith('video/') || fn.match(/\.(mp4|webm|mkv|mov)$/i);
            });
            if (vidRes) {
              const baseUrl = vidRes.file_url || vidRes.download_url || `/student/files/${vidRes.file_asset?.public_id || vidRes.id}/download`;
              activeVideoUrl = baseUrl.includes('disposition=') ? baseUrl : `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}disposition=inline`;
            }
          }
          lesson.video_url = activeVideoUrl;

          const hasVideo = Boolean(lesson.video_url);
          let videoWatched = StudentView.isLessonVideoWatched(lesson);
          let isCompleted = Boolean(lesson.progress?.is_completed) && (!hasVideo || videoWatched);
          const hasMiniQuiz = Array.isArray(lesson.quiz) && lesson.quiz.length > 0;
          let quizPassingPercent = 80;
          if (typeof lesson.quiz_passing_percent === 'number') {
            quizPassingPercent = lesson.quiz_passing_percent;
          } else if (lesson.meta && typeof lesson.meta.quiz_passing_percent === 'number') {
            quizPassingPercent = lesson.meta.quiz_passing_percent;
          } else {
            const mMatch = (lesson.markdown_content || '').match(/<!--\s*mini_quiz_passing:\s*(\d+)\s*-->/);
            if (mMatch) quizPassingPercent = parseInt(mMatch[1], 10);
          }
          const hasNewerRevision = Boolean(lesson.has_newer_revision || lesson.status === 'HISTORICAL' || (lesson.latest_lesson_id && lesson.latest_lesson_id !== activeItem.id));

          // Lesson-specific resources
          const currentLessonId = String(activeItem.id);
          const lessonResources = (Array.isArray(lesson.resources) ? lesson.resources : [])
            .filter(r => !r.lesson_id || String(r.lesson_id) === currentLessonId);

          contentContainer.innerHTML = `
            <div class="space-y-6 animate-fade-in" id="cisco-lesson-content-body" data-lesson-id="${UI.escapeHtml(currentLessonId)}">

              <!-- Breadcrumb & Status Header -->
              <div class="flex items-center justify-between gap-3 text-xs text-slate-400 select-none">
                <div class="flex items-center gap-2 truncate">
                  <span>${UI.escapeHtml(activeItem.moduleTitle || 'Chương')}</span>
                  <span>&rsaquo;</span>
                  <span class="font-bold text-slate-700 dark:text-slate-300 truncate">${activeItem.displayCode} ${UI.escapeHtml(lesson.title)}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isCompleted ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}">
                    ${isCompleted ? '✓ Đã xong' : 'Đang học'}
                  </span>
                </div>
              </div>

              ${hasNewerRevision ? `
                <!-- Lesson Revision Opt-In Banner -->
                <div id="cisco-revision-banner" class="rounded-2xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/90 dark:bg-indigo-950/50 p-4 sm:p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="material-symbols-outlined text-[22px]">published_with_changes</span>
                    </div>
                    <div>
                      <h3 class="text-sm font-bold text-indigo-950 dark:text-indigo-200">Đã có phiên bản bài giảng mới hơn</h3>
                      <p class="text-xs text-indigo-800/90 dark:text-indigo-300/90 mt-1 leading-relaxed">
                        ${lesson.material_change_summary ? `<strong>Thay đổi:</strong> ${UI.escapeHtml(lesson.material_change_summary)}. ` : ''}
                        Bạn đang xem phiên bản lưu trữ an toàn. Bạn có thể cập nhật sang bản mới nhất bất cứ lúc nào.
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    id="btn-opt-in-revision"
                    class="shrink-0 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <span class="material-symbols-outlined text-[16px]">sync</span>
                    <span>Cập nhật bản mới</span>
                  </button>
                </div>
              ` : ''}

              <!-- Lesson Title & Objectives Card -->
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm space-y-3">
                <div class="flex items-center gap-2 text-xs text-slate-400">
                  <span class="flex items-center gap-1">
                    <span>Chuẩn đầu ra: Kỹ năng & Năng lực thực hành</span>
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

              <!-- Media Player / Video Block -->
              ${lesson.video_url ? `
                <div class="bg-black rounded-2xl overflow-hidden shadow-lg border border-slate-800">
                  <div class="aspect-video w-full bg-black relative">
                    ${StudentView._getEmbedVideoHtml(lesson.video_url, 'cisco-stream-player', isCompleted)}
                  </div>
                  <div class="px-4 py-2 bg-slate-900/95 border-t border-slate-800 flex items-center justify-between text-xs text-slate-300">
                    <div class="flex items-center gap-2">
                      <span class="material-symbols-outlined text-[16px] ${isCompleted ? 'text-emerald-400' : 'text-amber-400'}">
                        ${isCompleted ? 'verified' : (/youtube\.com|youtu\.be/i.test(lesson.video_url || '') ? 'smart_display' : 'lock_clock')}
                      </span>
                      <span id="cisco-anti-seek-label" class="font-medium text-[11px] sm:text-xs">
                        ${isCompleted ? 'Đã hoàn thành 100% video • Bạn có thể tua lại nội dung tùy ý.' : (/youtube\.com|youtu\.be/i.test(lesson.video_url || '') ? 'Video YouTube: Bạn có thể theo dõi tiến độ video.' : 'Khóa tua nhanh đang bật: Cần xem tuần tự bài giảng để ghi nhận tiến độ.')}
                      </span>
                    </div>
                    <span id="cisco-anti-seek-badge" class="font-mono text-[11px] px-2 py-0.5 rounded ${isCompleted ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}">
                      ${isCompleted ? '100%' : (/youtube\.com|youtu\.be/i.test(lesson.video_url || '') ? 'YouTube' : 'Tiến độ: 0%')}
                    </span>
                  </div>
                </div>
              ` : ''}

              <!-- Supplementary Videos -->
              ${(lesson.video_urls || []).filter(url => url !== lesson.video_url).map((url, index) => `
                <section class="space-y-2">
                  <h3 class="text-xs font-bold text-slate-700 dark:text-slate-300">Video bổ sung ${index + 2}</h3>
                  <div class="aspect-video rounded-xl overflow-hidden bg-slate-900">
                    ${StudentView._getEmbedVideoHtml(url, `cisco-extra-video-${index}`, isCompleted)}
                  </div>
                </section>
              `).join('')}

              <!-- Clean Markdown Reader -->
              <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-10 shadow-sm text-slate-800 dark:text-slate-200 leading-relaxed text-sm sm:text-base space-y-5">
                ${UI.renderMarkdown(lesson.markdown_content || 'Nội dung bài giảng đang được hoàn thiện.')}
              </div>

              <!-- Interactive Mini-Quiz Section (Coursera-Style Pagination) -->
              ${hasMiniQuiz ? `
                <div class="bg-white dark:bg-slate-900 border border-indigo-100 dark:border-indigo-900/60 rounded-2xl p-6 sm:p-8 shadow-sm space-y-5" id="cisco-mini-quiz-section">
                  ${hasVideo && !videoWatched ? `
                    <div id="cisco-quiz-video-notice" class="flex items-center gap-2 p-3 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 text-indigo-800 dark:text-indigo-300 text-xs">
                      <span class="material-symbols-outlined text-[18px]">info</span>
                      <span>💡 <strong>Gợi ý:</strong> Bạn có thể theo dõi trước các câu hỏi củng cố bên dưới và nộp câu trả lời sau khi xem video bài giảng.</span>
                    </div>
                  ` : ''}

                  <!-- Quiz Header -->
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div class="flex items-center gap-2.5">
                      <span class="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center material-symbols-outlined text-[20px]">quiz</span>
                      <div>
                        <h3 class="font-black text-slate-900 dark:text-white text-base">Bài kiểm tra Củng cố Kiến thức (Mini-Quiz)</h3>
                        <p class="text-xs text-slate-400 mt-0.5">Yêu cầu đạt điểm tối thiểu: <strong class="text-indigo-600 dark:text-indigo-400 font-bold">${quizPassingPercent}%</strong> để hoàn thành bài giảng</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 text-xs font-bold border border-indigo-100 dark:border-indigo-900/50">
                        ${lesson.quiz.length} câu hỏi
                      </span>
                      <span class="px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 text-xs font-bold border border-emerald-100 dark:border-emerald-900/50">
                        Chuẩn: &ge; ${quizPassingPercent}%
                      </span>
                    </div>
                  </div>

                  <!-- Coursera-Style Step Navigation Bar (if >= 2 questions) -->
                  ${lesson.quiz.length >= 2 ? `
                    <div class="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs select-none" id="cisco-quiz-pagination-bar">
                      <div class="flex items-center gap-1.5 overflow-x-auto py-0.5" id="cisco-quiz-pills-bar">
                        ${lesson.quiz.map((_, qIdx) => `
                          <button
                            type="button"
                            class="cisco-quiz-step-pill px-3 py-1 rounded-lg font-mono font-bold text-xs transition-all cursor-pointer ${qIdx === 0 ? 'bg-indigo-600 text-white shadow-2xs' : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100'}"
                            data-target-idx="${qIdx}"
                          >
                            Câu ${qIdx + 1}
                          </button>
                        `).join('')}
                      </div>
                      <span id="cisco-quiz-slide-indicator" class="text-xs font-bold text-slate-500 shrink-0 font-mono">
                        1 / ${lesson.quiz.length}
                      </span>
                    </div>
                  ` : ''}

                  <!-- Questions Container -->
                  <div class="space-y-6" id="cisco-mini-quiz-list">
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

                      const qImg = q.image_url || q.question_image_url || '';
                      const optImages = Array.isArray(q.option_images) ? q.option_images : [];

                      return `
                        <div class="p-4 sm:p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-4 cisco-quiz-card" data-qidx="${qIdx}" data-qtype="${qType}" style="${lesson.quiz.length >= 2 && qIdx !== 0 ? 'display: none;' : ''}">
                          <!-- Question Header -->
                          <div class="flex items-start justify-between gap-3">
                            <div class="flex items-start gap-2.5 flex-1">
                              <span class="px-2.5 py-0.5 rounded-lg bg-indigo-600 text-white font-mono font-bold text-xs shrink-0 mt-0.5">Câu ${qIdx + 1}</span>
                              <div class="font-bold text-slate-900 dark:text-white text-sm sm:text-base leading-snug">
                                ${qType === 'FILL_BLANK'
                                  ? UI.escapeHtml(q.question).replace(/\[___\]/g, '<span class="inline-block px-2.5 py-0.5 mx-1 rounded-lg bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 font-bold font-mono text-xs border border-emerald-300 dark:border-emerald-700 shadow-2xs">[ Chỗ trống ]</span>')
                                  : UI.escapeHtml(q.question)}
                              </div>
                            </div>
                            <div class="shrink-0">
                              ${typeBadge}
                            </div>
                          </div>

                          <!-- Question Illustration Image (if available) -->
                          ${qImg ? `
                            <div class="my-2 p-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 inline-block max-w-full">
                              <img
                                src="${UI.escapeHtml(qImg)}"
                                alt="Hình ảnh minh họa câu hỏi"
                                class="max-h-64 sm:max-h-80 max-w-full rounded-lg object-contain block mx-auto cursor-zoom-in"
                                onclick="UI.openImageModal ? UI.openImageModal('${UI.escapeHtml(qImg)}') : window.open('${UI.escapeHtml(qImg)}', '_blank')"
                                title="Bấm để xem ảnh phóng to"
                              />
                            </div>
                          ` : ''}

                          <!-- Question interaction body -->
                          ${qType === 'MULTIPLE_CHOICE' ? `
                            <div class="space-y-2.5 pt-1">
                              ${choices.map((ch, chIdx) => {
                                const chImg = optImages[chIdx] || '';
                                return `
                                  <label class="flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-indigo-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all cisco-quiz-choice-label" data-chidx="${chIdx}">
                                    <div class="flex items-center gap-3 min-w-0 flex-1">
                                      ${isMulti ? `
                                        <input type="checkbox" name="cisco-quiz-q-${qIdx}" value="${chIdx}" class="text-primary focus:ring-primary w-4 h-4 rounded cursor-pointer cisco-quiz-chk" />
                                      ` : `
                                        <input type="radio" name="cisco-quiz-q-${qIdx}" value="${chIdx}" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer cisco-quiz-radio" />
                                      `}
                                      <span class="w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center shrink-0 choice-badge">
                                        ${String.fromCharCode(65 + chIdx)}
                                      </span>
                                      <span class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed choice-text">${UI.escapeHtml(ch)}</span>
                                    </div>
                                    ${chImg ? `
                                      <div class="shrink-0 pl-7 sm:pl-0">
                                        <img src="${UI.escapeHtml(chImg)}" alt="Ảnh đáp án ${String.fromCharCode(65 + chIdx)}" class="h-14 sm:h-16 rounded-lg border border-slate-200 dark:border-slate-700 object-contain bg-slate-50 dark:bg-slate-800" />
                                      </div>
                                    ` : ''}
                                  </label>
                                `;
                              }).join('')}
                            </div>
                          ` : ''}

                          ${qType === 'FILL_BLANK' ? `
                            <div class="space-y-3 p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/30 dark:bg-emerald-950/20">
                              <div class="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[18px] text-emerald-600">edit_note</span>
                                <span>Nhập câu trả lời của bạn vào ô bên dưới:</span>
                              </div>
                              ${(q.blanks || [{ accepted_answers: [] }]).map((b, bIdx) => `
                                <div class="flex items-center gap-2.5 p-2 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-white dark:bg-slate-900 cisco-quiz-blank-row shadow-2xs">
                                  <span class="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold text-xs flex items-center justify-center shrink-0">
                                    #${bIdx + 1}
                                  </span>
                                  <input
                                    type="text"
                                    class="cisco-quiz-blank-input flex-1 px-3.5 py-2 text-xs sm:text-sm rounded-lg border-0 bg-transparent text-slate-900 dark:text-white outline-none focus:ring-0 font-medium"
                                    data-qidx="${qIdx}"
                                    data-bidx="${bIdx}"
                                    placeholder="Gõ từ hoặc cụm từ cần điền vào đây..."
                                    autocomplete="off"
                                  />
                                </div>
                              `).join('')}
                              <p class="text-[11px] text-emerald-700/80 dark:text-emerald-400/80 italic">
                                * Lưu ý: Câu trả lời không phân biệt chữ hoa, chữ thường.
                              </p>
                            </div>
                          ` : ''}

                          ${qType === 'MATCHING' ? `
                            <div class="space-y-3 p-4 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/30 dark:bg-amber-950/20">
                              <div class="text-xs font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[18px] text-amber-600">join_inner</span>
                                <span>Ghép từng khái niệm ở Cột Trái với ý nghĩa đúng ở Cột Phải:</span>
                              </div>
                              <div class="space-y-2.5 pt-1">
                                ${(q.pairs || []).map((p, pIdx) => {
                                  // Shuffle right options deterministically to prevent obvious line-up
                                  const shuffledOptions = [...(q.pairs || [])].sort((a, b) => (a.right > b.right ? 1 : -1));
                                  return `
                                    <div class="flex flex-col sm:flex-row sm:items-center gap-2.5 p-3 rounded-xl border border-amber-200/80 dark:border-amber-800/60 bg-white dark:bg-slate-900 cisco-quiz-matching-row shadow-2xs" data-qidx="${qIdx}" data-pidx="${pIdx}">
                                      <div class="flex items-center gap-2.5 sm:w-1/2 font-medium text-xs sm:text-sm text-slate-800 dark:text-slate-200">
                                        <span class="w-6 h-6 rounded-lg bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 font-bold text-xs flex items-center justify-center shrink-0">${pIdx + 1}</span>
                                        <span class="font-semibold">${UI.escapeHtml(p.left)}</span>
                                      </div>
                                      <div class="flex items-center gap-2 sm:w-1/2">
                                        <span class="material-symbols-outlined text-amber-500 text-[18px] hidden sm:inline shrink-0">arrow_forward</span>
                                        <select class="cisco-quiz-matching-select w-full px-3 py-2 rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50/40 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-amber-500 transition-all cursor-pointer font-medium" data-qidx="${qIdx}" data-pidx="${pIdx}">
                                          <option value="">-- Chọn ý nghĩa tương ứng --</option>
                                          ${shuffledOptions.map(optPair => `
                                            <option value="${UI.escapeHtml(optPair.right)}">${UI.escapeHtml(optPair.right)}</option>
                                          `).join('')}
                                        </select>
                                      </div>
                                    </div>
                                  `;
                                }).join('')}
                              </div>
                            </div>
                          ` : ''}

                          ${qType === 'TRUE_FALSE' ? `
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                              <label class="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-emerald-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all cisco-quiz-tf-label" data-qidx="${qIdx}" data-val="true">
                                <input type="radio" name="cisco-quiz-tf-${qIdx}" value="true" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer cisco-quiz-tf-radio" />
                                <span class="material-symbols-outlined text-emerald-600 text-[18px]">check_circle</span>
                                <span class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200">Đúng (True)</span>
                              </label>
                              <label class="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-rose-50/40 dark:hover:bg-slate-800/80 cursor-pointer transition-all cisco-quiz-tf-label" data-qidx="${qIdx}" data-val="false">
                                <input type="radio" name="cisco-quiz-tf-${qIdx}" value="false" class="text-primary focus:ring-primary w-4 h-4 cursor-pointer cisco-quiz-tf-radio" />
                                <span class="material-symbols-outlined text-rose-600 text-[18px]">cancel</span>
                                <span class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200">Sai (False)</span>
                              </label>
                            </div>
                          ` : ''}

                          <div class="cisco-quiz-explanation hidden p-3.5 rounded-xl text-xs space-y-1"></div>
                        </div>
                      `;
                    }).join('')}
                  </div>

                  <!-- Bottom Actions & Navigation Bar -->
                  <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                    <div id="cisco-quiz-score-banner" class="text-xs text-slate-500 font-medium">
                      Hãy hoàn thành câu trả lời cho các câu hỏi rồi bấm <strong>Kiểm tra đáp án</strong>.
                    </div>
                    <div class="flex items-center gap-2">
                      ${lesson.quiz.length >= 2 ? `
                        <button type="button" id="cisco-quiz-prev-btn" class="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 font-bold text-xs transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed" disabled>
                          <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                          <span>Quay lại</span>
                        </button>
                        <button type="button" id="cisco-quiz-next-btn" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-900 text-white dark:bg-slate-700 dark:hover:bg-slate-600 font-bold text-xs transition-colors flex items-center gap-1 cursor-pointer">
                          <span>Tiếp theo</span>
                          <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
                        </button>
                      ` : ''}
                      <button type="button" id="cisco-quiz-check-btn" class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-colors shadow-sm flex items-center gap-1.5 cursor-pointer ${lesson.quiz.length >= 2 ? 'hidden' : ''}">
                        <span class="material-symbols-outlined text-[16px]">check_circle</span>
                        <span>Kiểm tra đáp án</span>
                      </button>
                      <button type="button" id="cisco-quiz-reset-btn" class="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors hidden cursor-pointer flex items-center gap-1.5 shadow-sm">
                        <span class="material-symbols-outlined text-[16px]">restart_alt</span>
                        <span>Làm lại từ đầu</span>
                      </button>
                    </div>
                  </div>
                </div>
              ` : ''}

              <!-- Lesson Resources List (if any) -->
              ${lessonResources.length > 0 ? `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-3">
                  <h3 class="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">Tài liệu đính kèm bài giảng (${lessonResources.length})</h3>
                  <div class="space-y-2">
                    ${lessonResources.map(r => `
                      <div class="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                        <span class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(r.filename || r.name)}</span>
                        <a href="/student/files/${encodeURIComponent(r.asset_id || r.id)}/download" download class="c-btn c-btn-secondary c-btn-sm inline-flex items-center gap-1 text-emerald-600">
                          <span class="material-symbols-outlined text-[16px]">download</span> Tải về
                        </a>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              <!-- Linked Assessment Card (if an exam is linked to this lesson) -->
              ${(() => {
                const curId = String(lesson.id || lesson.lesson_id || activeItem.id);
                const linkedExam = (allAssessments || []).find(a => String(a.lesson_id) === curId);
                if (!linkedExam) return '';
                const examId = linkedExam.assessment_id || linkedExam.id;
                const examAttempts = linkedExam.attempts_count || 0;
                const examLimit = linkedExam.attempt_limit || linkedExam.max_attempts || null;
                const isLimitReached = linkedExam.is_attempt_limit_reached || (examLimit && examAttempts >= examLimit);
                const isPassed = Boolean(linkedExam.passed);
                const examDuration = linkedExam.time_limit_minutes || linkedExam.duration_minutes || null;

                return `
                  <div class="bg-gradient-to-br from-indigo-50/90 to-purple-50/90 dark:from-slate-900 dark:to-indigo-950/40 border border-indigo-200/80 dark:border-indigo-800/80 rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
                    <div class="flex items-start justify-between gap-4 flex-wrap">
                      <div class="flex items-start gap-3.5">
                        <div class="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                          <span class="material-symbols-outlined text-[26px]">assignment_turned_in</span>
                        </div>
                        <div>
                          <div class="flex items-center gap-2 flex-wrap mb-1">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                              Bài kiểm tra gắn liền bài học
                            </span>
                            ${isPassed ? `
                              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300">
                                ✓ Đã đạt
                              </span>
                            ` : ''}
                          </div>
                          <h3 class="text-base sm:text-lg font-black text-slate-900 dark:text-white">
                            ${UI.escapeHtml(linkedExam.title)}
                          </h3>
                          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
                            ${UI.escapeHtml(linkedExam.description || 'Bài thi củng cố kiến thức trực tiếp cho bài học này theo đề cương học phần.')}
                          </p>
                        </div>
                      </div>

                      <div class="flex items-center gap-3 shrink-0">
                        ${isLimitReached ? `
                          <div class="flex items-center gap-2">
                            <span class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-bold">
                              Hết lượt làm (${examAttempts}/${examLimit})
                            </span>
                            ${linkedExam.latest_attempt_id ? `
                              <a href="#/student/assessments/attempts/${linkedExam.latest_attempt_id}/results" class="c-btn c-btn-secondary c-btn-sm">
                                Xem kết quả
                              </a>
                            ` : ''}
                          </div>
                        ` : `
                          <a
                            href="#/student/assessments/waiting-room?id=${encodeURIComponent(examId)}"
                            class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-sm inline-flex items-center gap-2 cursor-pointer"
                          >
                            <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                            <span>Bắt đầu bài kiểm tra</span>
                          </a>
                        `}
                      </div>
                    </div>

                    <div class="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-indigo-100/80 dark:border-indigo-900/40">
                      <span class="flex items-center gap-1 font-mono">
                        <span class="material-symbols-outlined text-[15px]">timer</span>
                        ${examDuration ? `${examDuration} phút` : 'Không giới hạn thời gian'}
                      </span>
                      <span class="flex items-center gap-1 font-mono">
                        <span class="material-symbols-outlined text-[15px]">repeat</span>
                        ${examLimit ? `${examLimit} lượt làm` : 'Không giới hạn số lượt'}
                      </span>
                      ${linkedExam.total_questions ? `
                        <span class="flex items-center gap-1 font-mono">
                          <span class="material-symbols-outlined text-[15px]">quiz</span>
                          ${linkedExam.total_questions} câu hỏi
                        </span>
                      ` : ''}
                    </div>
                  </div>
                `;
              })()}

              <!-- Bottom Action Navigation Bar -->
              <div class="flex items-center justify-between pt-4 pb-12 gap-2 flex-wrap">
                <div id="cisco-bottom-prev-box">
                  <!-- Prev Button dynamically updated -->
                </div>

                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    id="cisco-ask-ai-lesson-btn"
                    class="px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/50 dark:hover:bg-indigo-900/60 dark:text-indigo-300 border border-indigo-200/80 dark:border-indigo-800/80 cursor-pointer"
                    title="Mở tab Trợ lý AI trao đổi về bài học này"
                  >
                    <span class="material-symbols-outlined text-[18px]">smart_toy</span>
                    <span>Hỏi Trợ lý AI</span>
                  </button>

                  <button
                    type="button"
                    id="cisco-complete-btn"
                    class="px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${isCompleted ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 cursor-default' : (hasVideo ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-200 dark:border-slate-700 cursor-not-allowed opacity-80' : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm cursor-pointer')}"
                    ${hasVideo && !isCompleted ? 'disabled title="Bạn cần xem hết 100% video bài học để hoàn thành"' : ''}
                  >
                    <span class="material-symbols-outlined text-[18px]">${isCompleted ? 'check_circle' : (hasVideo ? 'lock' : 'check')}</span>
                    <span>${isCompleted ? 'Đã hoàn thành' : (hasVideo ? 'Cần xem hết video' : 'Đánh dấu hoàn thành')}</span>
                  </button>
                </div>

                <div id="cisco-bottom-next-box">
                  <!-- Next Button dynamically updated -->
                </div>
              </div>

            </div>
          `;

          // Hook Bottom Prev/Next Buttons
          const curIdx = flatNavList.findIndex(i => i.type === activeItem.type && String(i.id) === String(activeItem.id));
          const prevItem = curIdx > 0 ? flatNavList[curIdx - 1] : null;
          const nextItem = curIdx < flatNavList.length - 1 ? flatNavList[curIdx + 1] : null;

          const bottomPrevBox = document.getElementById('cisco-bottom-prev-box');
          if (bottomPrevBox && prevItem) {
            bottomPrevBox.innerHTML = `
              <button type="button" title="${UI.escapeHtml(prevItem.title)}" class="px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 hover:border-emerald-600 transition-colors flex items-center gap-1.5 cursor-pointer">
                <span class="material-symbols-outlined text-[16px]">arrow_back</span>
                <span>Bài phía trước</span>
              </button>
            `;
            bottomPrevBox.firstElementChild.onclick = () => window._ciscoSelectItem(prevItem.type, prevItem.id);
          }

          const bottomNextBox = document.getElementById('cisco-bottom-next-box');
          if (bottomNextBox && nextItem) {
            bottomNextBox.innerHTML = `
              <button type="button" title="${UI.escapeHtml(nextItem.title)}" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer">
                <span>Bài tiếp theo</span>
                <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            `;
            bottomNextBox.firstElementChild.onclick = () => window._ciscoSelectItem(nextItem.type, nextItem.id);
          }

          // Hook Ask AI Button in Lesson Reader
          const askAiBtn = document.getElementById('cisco-ask-ai-lesson-btn');
          if (askAiBtn) {
            askAiBtn.onclick = () => {
              if (sidebarEl && sidebarEl.classList.contains('hidden')) {
                sidebarEl.classList.remove('hidden');
              }
              switchSidebarTab('ai');
            };
          }

          // Revision Opt-In Button
          const optInBtn = document.getElementById('btn-opt-in-revision');
          if (optInBtn) {
            optInBtn.onclick = async () => {
              try {
                optInBtn.disabled = true;
                optInBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang chuyển đổi...';
                const res = await ApiClient.optInLessonRevision(activeItem.id);
                UI.showToast('Đã nâng cấp lên phiên bản bài giảng mới nhất!', 'success');
                const targetLessonId = res?.active_lesson_id || res?.new_lesson_id || lesson.latest_lesson_id;
                await StudentView.renderCourseConsole(container, courseId, targetLessonId);
              } catch (err) {
                UI.showToast(err.message || 'Không thể chuyển đổi phiên bản.', 'error');
                optInBtn.disabled = false;
                optInBtn.innerHTML = '<span class="material-symbols-outlined text-[16px]">sync</span> <span>Cập nhật bản mới</span>';
              }
            };
          }


          // Mark Lesson Completed Controller
          const completeBtn = document.getElementById('cisco-complete-btn');
          const setLessonCompleted = () => {
            isCompleted = true;
            activeItem.isCompleted = true;
            if (activeItem.data) {
              activeItem.data.is_completed = true;
              activeItem.data._isCompleted = true;
            }
            const targetLes = allLessons.find(l => String(l.lesson_id || l.id) === String(activeItem.id));
            if (targetLes) {
              targetLes.is_completed = true;
              targetLes._isCompleted = true;
            }

            // Recalculate unlocking of subsequent items
            let prevDone = true;
            flatNavList.forEach(item => {
              if (item.type === 'lesson') {
                if (String(item.id) === String(activeItem.id)) {
                  item.isCompleted = true;
                  if (item.data) {
                    item.data.is_completed = true;
                    item.data._isCompleted = true;
                  }
                }
                item.isUnlocked = isPreview || prevDone;
                prevDone = item.isCompleted;
              }
            });

            // Reconcile module counts and status for sidebar outline
            modules.forEach(mod => {
              let compCount = 0;
              (mod.lessons || []).forEach(l => {
                if (String(l.lesson_id || l.id) === String(activeItem.id)) {
                  l.is_completed = true;
                  l._isCompleted = true;
                }
                const navItem = flatNavList.find(i => i.type === 'lesson' && String(i.id) === String(l.lesson_id || l.id));
                if (navItem) {
                  l._isUnlocked = navItem.isUnlocked;
                  if (navItem.isCompleted) {
                    l.is_completed = true;
                    l._isCompleted = true;
                  }
                }
                if (l._isCompleted || l.is_completed) {
                  compCount++;
                }
              });
              mod._completedCount = compCount;
              mod._isCompleted = mod.lessons.length > 0 && compCount === mod.lessons.length;
            });

            renderSidebarOutline();
            updateFloatingNav();

            // Recalculate dynamic course progress in header
            const completedCount = allLessons.filter(l => l._isCompleted || l.is_completed || l.progress?.is_completed).length;
            const newPercent = allLessons.length > 0 ? Math.round((completedCount / allLessons.length) * 100) : 0;
            const progressBadge = document.getElementById('console-progress-percent');
            if (progressBadge) {
              progressBadge.textContent = `${newPercent}%`;
            }

            // Background reconcile authoritative backend course progress
            ApiClient.getStudentCourseProgress(courseId).then(freshProg => {
              const freshVal = freshProg?.current_progress_percent ?? freshProg?.progress_percent;
              if (freshVal !== undefined && freshVal !== null && progressBadge) {
                progressBadge.textContent = `${Math.round(freshVal)}%`;
              }
            }).catch(() => {});

            if (completeBtn) {
              completeBtn.disabled = true;
              completeBtn.className = 'px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center gap-2 cursor-default';
              completeBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">check_circle</span> <span>Đã hoàn thành</span>';
            }
          };

          if (completeBtn) {
            completeBtn.onclick = async () => {
              if (isPreview) {
                UI.showToast('Bạn đang xem thử với quyền Giảng viên. Tiến độ xem thử không ghi nhận vào CSDL sinh viên.', 'info');
                return;
              }
              if (hasVideo && !videoWatched) {
                UI.showToast('Bạn cần xem ít nhất 90% video bài học mới có thể hoàn thành bài giảng này.', 'warning');
                return;
              }
              if (hasMiniQuiz) {
                const quizSection = document.getElementById('cisco-mini-quiz-section');
                if (quizSection) quizSection.scrollIntoView({ behavior: 'smooth' });
                UI.showToast('Hãy trả lời các câu hỏi trắc nghiệm củng cố của bài học trước khi hoàn thành.', 'warning');
                return;
              }
              try {
                const result = await ApiClient.recordLessonProgress(activeItem.id, 30, 1.0, false);
                if (!result?.is_completed) {
                  UI.showToast('Bạn cần đáp ứng đủ thời lượng học trước khi hoàn thành.', 'warning');
                  return;
                }
                setLessonCompleted();
                UI.showToast('Chúc mừng bạn đã hoàn thành bài học này!', 'success');
              } catch (e) {
                UI.showToast('Không thể lưu trạng thái bài học.', 'error');
              }
            };
          }

          // Universal Video Watcher Controller
          const videoEl = document.getElementById('cisco-stream-player');
          const antiSeekLabel = document.getElementById('cisco-anti-seek-label');
          const antiSeekBadge = document.getElementById('cisco-anti-seek-badge');

          const updateProgressUI = (current, duration) => {
            if (!duration || duration <= 0) return;
            const pct = Math.min(100, Math.round((current / duration) * 100));
            if (antiSeekBadge) {
              antiSeekBadge.textContent = `${pct}%`;
              if (pct >= 100) {
                antiSeekBadge.className = 'font-mono text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300';
              }
            }
          };

          let customPlayerCtrl = null;

          const handleVideoCompleted = async (durationSec) => {
            if (videoWatched) return;
            videoWatched = true;
            if (customPlayerCtrl) customPlayerCtrl.unlockSeeking();
            if (antiSeekLabel) {
              antiSeekLabel.textContent = 'Đã hoàn thành 100% video • Bạn có thể tua lại nội dung tùy ý.';
            }
            if (antiSeekBadge) {
              antiSeekBadge.textContent = '100%';
              antiSeekBadge.className = 'font-mono text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300';
            }
            const quizSec = document.getElementById('cisco-mini-quiz-section');
            if (quizSec) quizSec.classList.remove('hidden');

            if (completeBtn && !hasMiniQuiz) {
              completeBtn.disabled = false;
              completeBtn.className = 'px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer';
              completeBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">check</span> <span>Đánh dấu hoàn thành</span>';
            }

            if (!isPreview) {
              try {
                const res = await ApiClient.recordLessonProgress(activeItem.id, Math.round(durationSec || 60), 1.0, false);
                if (res?.is_completed) setLessonCompleted();
              } catch (_) {}
            }
          };

          if (videoEl && videoEl.tagName === 'VIDEO') {
            customPlayerCtrl = StudentView.setupCustomVideoPlayer('cisco-stream-player', {
              isCompleted,
              onProgress: (maxWatched, dur) => updateProgressUI(maxWatched, dur),
              onComplete: (dur) => handleVideoCompleted(dur)
            });
          } else if (videoEl && videoEl.tagName === 'IFRAME') {
            if (typeof VideoArmor !== 'undefined' && videoEl.parentElement) {
              const currentUser = (typeof AuthState !== 'undefined' && AuthState.getUser) ? AuthState.getUser() : {};
              VideoArmor.mount(videoEl.parentElement, {
                student: currentUser,
                ip: (typeof window !== 'undefined' && window.clientIp) || '127.0.0.1'
              });
            }
            const iframeSrc = videoEl.src || '';
            let iframeOrigin = '';
            try {
              const parsed = new URL(iframeSrc);
              iframeOrigin = parsed.origin;
            } catch (_) {}

            let maxWatchedTime = 0;
            let iframeDuration = 0;

            activeIframeMessageListener = (event) => {
              let data = null;
              if (typeof event.data === 'string') {
                try { data = JSON.parse(event.data); } catch (_) {}
              } else if (typeof event.data === 'object' && event.data !== null) {
                data = event.data;
              }
              if (!data) return;

              if (data.event === 'infoDelivery' && data.info) {
                const info = data.info;
                if (typeof info.duration === 'number' && info.duration > 0) iframeDuration = info.duration;
                if (typeof info.currentTime === 'number') {
                  if (info.currentTime > maxWatchedTime) {
                    if (isCompleted || info.currentTime - maxWatchedTime <= 3.0) {
                      maxWatchedTime = info.currentTime;
                    }
                  }
                  if (iframeDuration > 0) {
                    updateProgressUI(maxWatchedTime, iframeDuration);
                    if ((isCompleted || maxWatchedTime >= iframeDuration * 0.90) && info.currentTime >= iframeDuration - 2.0) {
                      handleVideoCompleted(iframeDuration);
                    }
                  }
                }
                if (info.playerState === 0 && (isCompleted || iframeDuration <= 0 || maxWatchedTime >= iframeDuration * 0.90)) {
                  handleVideoCompleted(iframeDuration || 60);
                }
              }

              if (data.event === 'timeupdate' && data.data) {
                const cur = data.data.seconds || 0;
                const dur = data.data.duration || 0;
                if (dur > 0) iframeDuration = dur;
                if (cur > maxWatchedTime) {
                  if (isCompleted || cur - maxWatchedTime <= 3.0) {
                    maxWatchedTime = cur;
                  }
                }
                if (iframeDuration > 0) {
                  updateProgressUI(maxWatchedTime, iframeDuration);
                  if ((isCompleted || maxWatchedTime >= iframeDuration * 0.90) && cur >= iframeDuration - 2.0) {
                    handleVideoCompleted(iframeDuration);
                  }
                }
              } else if (data.event === 'ended' && (isCompleted || iframeDuration <= 0 || maxWatchedTime >= iframeDuration * 0.90)) {
                handleVideoCompleted(iframeDuration || 60);
              }
            };

            window.addEventListener('message', activeIframeMessageListener);

            const handshake = () => {
              try {
                if (!videoEl.contentWindow) return;
                videoEl.contentWindow.postMessage(JSON.stringify({ event: 'listening' }), '*');
                videoEl.contentWindow.postMessage(JSON.stringify({ method: 'addEventListener', value: 'timeupdate' }), '*');
                videoEl.contentWindow.postMessage(JSON.stringify({ method: 'addEventListener', value: 'ended' }), '*');
              } catch (_) {}
            };
            videoEl.addEventListener('load', () => { handshake(); setTimeout(handshake, 500); });

            activeIframePollInterval = setInterval(() => {
              try {
                if (!videoEl.contentWindow) return;
                videoEl.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'getCurrentTime' }), '*');
                if (iframeDuration <= 0) {
                  videoEl.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'getDuration' }), '*');
                }
              } catch (_) {}
            }, 1000);
          }

          // Supplementary videos setup: strictly lock forward seeking by default
          (lesson.video_urls || []).filter(url => url !== lesson.video_url).forEach((_, idx) => {
            StudentView.setupCustomVideoPlayer(`cisco-extra-video-${idx}`, {
              isCompleted: isCompleted,
              onProgress: null,
              onComplete: null
            });
          });

          // Heartbeat Progress Tracker
          if (!isPreview) {
            activeProgressTimer = setInterval(() => {
              const bodyRoot = document.getElementById('cisco-lesson-content-body');
              if (!bodyRoot || bodyRoot.dataset.lessonId !== String(activeItem.id)) {
                clearInterval(activeProgressTimer);
                activeProgressTimer = null;
                return;
              }
              const trackLessonId = activeItem.id;
              ApiClient.recordLessonProgress(trackLessonId, 15, videoWatched ? 1.0 : 0.5, false)
                .then(res => {
                  const currentBody = document.getElementById('cisco-lesson-content-body');
                  if (currentBody && currentBody.dataset.lessonId === String(trackLessonId)) {
                    if (res?.is_completed) setLessonCompleted();
                  }
                })
                .catch(() => {});
            }, 15000);
          }

          // Mini-Quiz Engine Handler (Coursera-Style Slide Pagination & Passing Threshold)
          const checkQuizBtn = document.getElementById('cisco-quiz-check-btn');
          const resetQuizBtn = document.getElementById('cisco-quiz-reset-btn');
          const quizSection = document.getElementById('cisco-mini-quiz-section');
          const prevQuizBtn = document.getElementById('cisco-quiz-prev-btn');
          const nextQuizBtn = document.getElementById('cisco-quiz-next-btn');

          if (quizSection && lesson.quiz && lesson.quiz.length) {
            const totalQuizSlides = lesson.quiz.length;
            let currentQuizSlide = 0;
            let hasPassedQuiz = false;

            const updateQuizSlideView = () => {
              if (totalQuizSlides < 2) return;
              const cards = quizSection.querySelectorAll('.cisco-quiz-card');
              cards.forEach((c, idx) => {
                c.style.display = idx === currentQuizSlide ? 'block' : 'none';
              });

              const pills = quizSection.querySelectorAll('.cisco-quiz-step-pill');
              pills.forEach((p, idx) => {
                if (idx === currentQuizSlide) {
                  p.className = 'cisco-quiz-step-pill px-3 py-1 rounded-lg font-mono font-bold text-xs transition-all cursor-pointer bg-indigo-600 text-white shadow-2xs';
                } else {
                  p.className = 'cisco-quiz-step-pill px-3 py-1 rounded-lg font-mono font-bold text-xs transition-all cursor-pointer bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100';
                }
              });

              const indicator = document.getElementById('cisco-quiz-slide-indicator');
              if (indicator) indicator.textContent = `${currentQuizSlide + 1} / ${totalQuizSlides}`;

              if (prevQuizBtn) prevQuizBtn.disabled = currentQuizSlide === 0;

              if (nextQuizBtn) {
                if (currentQuizSlide === totalQuizSlides - 1) {
                  nextQuizBtn.classList.add('hidden');
                  if (checkQuizBtn && !hasPassedQuiz) checkQuizBtn.classList.remove('hidden');
                } else {
                  nextQuizBtn.classList.remove('hidden');
                  if (checkQuizBtn) checkQuizBtn.classList.add('hidden');
                }
              }
            };

            if (totalQuizSlides >= 2) {
              if (prevQuizBtn) {
                prevQuizBtn.onclick = () => {
                  if (currentQuizSlide > 0) {
                    currentQuizSlide--;
                    updateQuizSlideView();
                  }
                };
              }
              if (nextQuizBtn) {
                nextQuizBtn.onclick = () => {
                  if (currentQuizSlide < totalQuizSlides - 1) {
                    currentQuizSlide++;
                    updateQuizSlideView();
                  }
                };
              }
              quizSection.querySelectorAll('.cisco-quiz-step-pill').forEach(pill => {
                pill.onclick = () => {
                  const targetIdx = parseInt(pill.dataset.targetIdx, 10);
                  if (!isNaN(targetIdx)) {
                    currentQuizSlide = targetIdx;
                    updateQuizSlideView();
                  }
                };
              });
            }

            if (checkQuizBtn) {
              checkQuizBtn.onclick = async () => {
                const answers = lesson.quiz.map((q, qIdx) => {
                  const card = quizSection.querySelector(`.cisco-quiz-card[data-qidx="${qIdx}"]`);
                  const qType = q.type || 'MULTIPLE_CHOICE';
                  if (qType === 'MULTIPLE_CHOICE') {
                    return Array.from(card.querySelectorAll(`input[name="cisco-quiz-q-${qIdx}"]:checked`))
                      .map(inp => Number.parseInt(inp.value, 10));
                  }
                  if (qType === 'FILL_BLANK') {
                    return Array.from(card.querySelectorAll('.cisco-quiz-blank-input')).map(inp => inp.value.trim());
                  }
                  if (qType === 'MATCHING') {
                    return Array.from(card.querySelectorAll('.cisco-quiz-matching-select')).map(inp => inp.value);
                  }
                  if (qType === 'TRUE_FALSE') {
                    const sel = card.querySelector(`input[name="cisco-quiz-tf-${qIdx}"]:checked`);
                    return sel ? sel.value : null;
                  }
                  return null;
                });

                // Check completeness across all questions
                let firstUnansweredIdx = -1;
                answers.forEach((ans, qIdx) => {
                  if (firstUnansweredIdx !== -1) return;
                  const qType = lesson.quiz[qIdx].type || 'MULTIPLE_CHOICE';
                  let answered = false;
                  if (qType === 'MULTIPLE_CHOICE') answered = ans.length > 0;
                  else if (qType === 'FILL_BLANK' || qType === 'MATCHING') {
                    answered = ans.length > 0 && ans.every(v => String(v).trim().length > 0);
                  } else if (qType === 'TRUE_FALSE') answered = ans !== null;
                  else answered = ans !== null && String(ans).trim().length > 0;

                  if (!answered) firstUnansweredIdx = qIdx;
                });

                if (firstUnansweredIdx !== -1) {
                  currentQuizSlide = firstUnansweredIdx;
                  updateQuizSlideView();
                  UI.showToast(`Vui lòng trả lời Câu ${firstUnansweredIdx + 1} trước khi kiểm tra đáp án.`, 'warning');
                  return;
                }

                checkQuizBtn.disabled = true;
                let correctCount = 0;
                const cards = quizSection.querySelectorAll('.cisco-quiz-card');

                // Grade each question in memory
                const questionResults = [];
                cards.forEach((card, qIdx) => {
                  const qData = lesson.quiz[qIdx];
                  if (!qData) return;
                  const qType = qData.type || 'MULTIPLE_CHOICE';
                  let isCorrect = false;
                  let feedbackDetail = '';

                  if (qType === 'MULTIPLE_CHOICE') {
                    const expectedSet = new Set(
                      Array.isArray(qData.correct_answers)
                        ? qData.correct_answers
                        : (typeof qData.correct_index === 'number' ? [qData.correct_index] : [0])
                    );
                    const selectedInputs = card.querySelectorAll(`input[name="cisco-quiz-q-${qIdx}"]:checked`);
                    const selectedSet = new Set(Array.from(selectedInputs).map(inp => parseInt(inp.value, 10)));
                    isCorrect = expectedSet.size === selectedSet.size && [...expectedSet].every(x => selectedSet.has(x));

                    const correctLetters = [...expectedSet].sort((a, b) => a - b).map(idx => String.fromCharCode(65 + idx)).join(', ');
                    feedbackDetail = isCorrect
                      ? (qData.explanation ? UI.escapeHtml(qData.explanation) : 'Chính xác! Bạn đã chọn đúng tất cả đáp án.')
                      : `Đáp án đúng là: <strong>${correctLetters}</strong>. ${qData.explanation ? UI.escapeHtml(qData.explanation) : ''}`;

                  } else if (qType === 'FILL_BLANK') {
                    const blankInputs = card.querySelectorAll('.cisco-quiz-blank-input');
                    const blanks = qData.blanks || [];
                    let allBlanksCorrect = true;
                    const answerDetails = [];

                    blankInputs.forEach(inp => {
                      const bIdx = parseInt(inp.dataset.bidx, 10);
                      const userVal = (inp.value || '').trim().toLowerCase();
                      const blankDef = blanks[bIdx] || {};
                      const rawAccepted = Array.isArray(blankDef.accepted_answers)
                        ? blankDef.accepted_answers
                        : (blankDef.accepted_answers ? [blankDef.accepted_answers] : []);
                      const acceptedList = rawAccepted.map(a => String(a).trim().toLowerCase()).filter(Boolean);
                      const blankMatches = userVal.length > 0 && acceptedList.includes(userVal);
                      if (!blankMatches) allBlanksCorrect = false;
                      answerDetails.push(`Ô #${bIdx + 1}: <strong>${UI.escapeHtml(rawAccepted.filter(Boolean).join(' / ') || '(chưa thiết lập)')}</strong>`);
                    });

                    isCorrect = allBlanksCorrect && blankInputs.length > 0;
                    feedbackDetail = `
                      <div>${isCorrect ? 'Tuyệt vời! Bạn đã điền chính xác tất cả chỗ trống.' : 'Đáp án được chấp nhận:'}</div>
                      <div class="mt-1 space-y-0.5 text-xs text-slate-700 dark:text-slate-300">${answerDetails.join(' | ')}</div>
                      ${qData.explanation ? `<div class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-700 italic">${UI.escapeHtml(qData.explanation)}</div>` : ''}
                    `;

                  } else if (qType === 'MATCHING') {
                    const selectInputs = card.querySelectorAll('.cisco-quiz-matching-select');
                    const pairs = qData.pairs || [];
                    let allPairsCorrect = true;
                    const correctPairsDisplay = [];

                    selectInputs.forEach(sel => {
                      const pIdx = parseInt(sel.dataset.pidx, 10);
                      const userVal = sel.value;
                      const expectedRight = pairs[pIdx]?.right;
                      if (!userVal || userVal !== expectedRight) allPairsCorrect = false;
                      if (pairs[pIdx]) {
                        correctPairsDisplay.push(`<li><strong>${UI.escapeHtml(pairs[pIdx].left)}</strong> &rarr; ${UI.escapeHtml(pairs[pIdx].right)}</li>`);
                      }
                    });

                    isCorrect = allPairsCorrect && selectInputs.length > 0;
                    feedbackDetail = `
                      <div>${isCorrect ? 'Xuất sắc! Bạn đã ghép đúng tất cả các cặp.' : 'Các cặp ghép chính xác:'}</div>
                      <ul class="mt-1 list-disc list-inside space-y-0.5 text-xs text-slate-700 dark:text-slate-300">${correctPairsDisplay.join('')}</ul>
                      ${qData.explanation ? `<div class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-700 italic">${UI.escapeHtml(qData.explanation)}</div>` : ''}
                    `;

                  } else if (qType === 'TRUE_FALSE') {
                    const selectedRadio = card.querySelector(`input[name="cisco-quiz-tf-${qIdx}"]:checked`);
                    const rawVal = qData.correct_value !== undefined ? qData.correct_value : qData.correct_answer;
                    const expectedVal = rawVal === true || String(rawVal).trim().toLowerCase() === 'true';
                    isCorrect = selectedRadio && (selectedRadio.value === 'true') === expectedVal;
                    feedbackDetail = isCorrect
                      ? (qData.explanation ? UI.escapeHtml(qData.explanation) : 'Chính xác! Mệnh đề này là ' + (expectedVal ? 'Đúng.' : 'Sai.'))
                      : `Đáp án đúng là: <strong>${expectedVal ? 'Đúng (True)' : 'Sai (False)'}</strong>. ${qData.explanation ? UI.escapeHtml(qData.explanation) : ''}`;
                  }

                  if (isCorrect) correctCount++;
                  questionResults.push({ card, qData, qType, isCorrect, feedbackDetail });
                });

                const percent = Math.round((correctCount / totalQuizSlides) * 100);
                const isPassed = percent >= quizPassingPercent;
                const banner = document.getElementById('cisco-quiz-score-banner');

                if (isPassed) {
                  // PASS: Reveal answers & explanations on all cards
                  questionResults.forEach(({ card, qData, qType, isCorrect, feedbackDetail }) => {
                    const explDiv = card.querySelector('.cisco-quiz-explanation');

                    if (qType === 'MULTIPLE_CHOICE') {
                      const expectedSet = new Set(
                        Array.isArray(qData.correct_answers)
                          ? qData.correct_answers
                          : (typeof qData.correct_index === 'number' ? [qData.correct_index] : [0])
                      );
                      const selectedInputs = card.querySelectorAll('input:checked');
                      const selectedSet = new Set(Array.from(selectedInputs).map(inp => parseInt(inp.value, 10)));
                      const choiceLabels = card.querySelectorAll('.cisco-quiz-choice-label');
                      choiceLabels.forEach(lbl => {
                        const chIdx = parseInt(lbl.dataset.chidx, 10);
                        const badge = lbl.querySelector('.choice-badge');
                        lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                        if (expectedSet.has(chIdx)) {
                          lbl.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                          if (badge) badge.className = 'w-6 h-6 rounded-lg bg-emerald-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
                        } else if (selectedSet.has(chIdx)) {
                          lbl.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                          if (badge) badge.className = 'w-6 h-6 rounded-lg bg-rose-600 text-white font-bold text-xs flex items-center justify-center shrink-0';
                        }
                      });
                    } else if (qType === 'FILL_BLANK') {
                      const blankInputs = card.querySelectorAll('.cisco-quiz-blank-input');
                      const blanks = qData.blanks || [];
                      blankInputs.forEach(inp => {
                        const bIdx = parseInt(inp.dataset.bidx, 10);
                        const userVal = (inp.value || '').trim().toLowerCase();
                        const blankDef = blanks[bIdx] || {};
                        const rawAccepted = Array.isArray(blankDef.accepted_answers) ? blankDef.accepted_answers : (blankDef.accepted_answers ? [blankDef.accepted_answers] : []);
                        const acceptedList = rawAccepted.map(a => String(a).trim().toLowerCase()).filter(Boolean);
                        const blankMatches = userVal.length > 0 && acceptedList.includes(userVal);
                        inp.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                        inp.classList.add(blankMatches ? 'border-emerald-500' : 'border-rose-500', blankMatches ? 'bg-emerald-50' : 'bg-rose-50');
                      });
                    } else if (qType === 'MATCHING') {
                      const selectInputs = card.querySelectorAll('.cisco-quiz-matching-select');
                      const pairs = qData.pairs || [];
                      selectInputs.forEach(sel => {
                        const pIdx = parseInt(sel.dataset.pidx, 10);
                        const userVal = sel.value;
                        const expectedRight = pairs[pIdx]?.right;
                        const row = sel.closest('.cisco-quiz-matching-row');
                        if (row) {
                          row.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                          row.classList.add(userVal === expectedRight ? 'border-emerald-500' : 'border-rose-500', userVal === expectedRight ? 'bg-emerald-50' : 'bg-rose-50');
                        }
                      });
                    } else if (qType === 'TRUE_FALSE') {
                      const selectedRadio = card.querySelector(`input[name="cisco-quiz-tf-${qIdx}"]:checked`);
                      const rawVal = qData.correct_value !== undefined ? qData.correct_value : qData.correct_answer;
                      const expectedVal = rawVal === true || String(rawVal).trim().toLowerCase() === 'true';
                      const labels = card.querySelectorAll('.cisco-quiz-tf-label');
                      labels.forEach(lbl => {
                        const lblVal = lbl.dataset.val === 'true';
                        lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                        if (lblVal === expectedVal) lbl.classList.add('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40');
                        else if (selectedRadio && (selectedRadio.value === 'true') === lblVal) lbl.classList.add('border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                      });
                    }

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

                  const targetLessonId = activeItem.id;
                  try {
                    if (hasVideo) {
                      await ApiClient.recordLessonProgress(targetLessonId, 30, 1.0, false);
                    }
                    const result = await ApiClient.completeLessonMiniQuiz(targetLessonId, answers);
                    const currentBody = document.getElementById('cisco-lesson-content-body');
                    if (currentBody && currentBody.dataset.lessonId === String(targetLessonId)) {
                      hasPassedQuiz = true;
                      checkQuizBtn.classList.add('hidden');
                      if (resetQuizBtn) resetQuizBtn.classList.add('hidden');
                      if (totalQuizSlides >= 2 && nextQuizBtn) nextQuizBtn.classList.add('hidden');
                      if (banner) {
                        banner.innerHTML = `
                          <div class="flex items-center gap-2">
                            <span class="px-2.5 py-1 rounded-xl bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200 font-bold">
                              Đạt yêu cầu: ${correctCount}/${totalQuizSlides} (${percent}% &ge; ${quizPassingPercent}%)
                            </span>
                            <span class="text-slate-600 dark:text-slate-300">
                              Xuất sắc! Bạn đã vượt qua bài kiểm tra củng cố kiến thức.
                            </span>
                          </div>
                        `;
                      }
                      if (result?.is_completed) {
                        setLessonCompleted();
                        UI.showToast('Chúc mừng bạn đã hoàn thành bài giảng!', 'success');
                      } else {
                        UI.showToast('Đã ghi nhận điểm số bài kiểm tra.', 'info');
                      }
                    }
                  } catch (error) {
                    hasPassedQuiz = false;
                    checkQuizBtn.classList.remove('hidden');
                    if (resetQuizBtn) resetQuizBtn.classList.remove('hidden');
                    if (banner) {
                      banner.innerHTML = `
                        <div class="flex items-center gap-2">
                          <span class="px-2.5 py-1 rounded-xl bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200 font-bold">
                            Chưa lưu kết quả: Lỗi máy chủ
                          </span>
                          <span class="text-slate-600 dark:text-slate-300">
                            ${UI.escapeHtml(error.message || 'Lỗi lưu kết quả bài kiểm tra. Vui lòng thử lại.')}
                          </span>
                        </div>
                      `;
                    }
                    UI.showToast(error.message || 'Lỗi lưu kết quả bài kiểm tra.', 'error');
                  }

                } else {
                  // FAIL: ANTI-LEAK PROTECTION — DO NOT reveal correct answers or explanations!
                  if (banner) {
                    banner.innerHTML = `
                      <div class="flex items-center gap-2">
                        <span class="px-2.5 py-1 rounded-xl bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200 font-bold">
                          Chưa đạt: ${correctCount}/${totalQuizSlides} (${percent}% / Yêu cầu: ${quizPassingPercent}%)
                        </span>
                        <span class="text-rose-600 dark:text-rose-400 font-medium">
                          Bạn chưa đạt chuẩn hoàn thành. Vui lòng bấm "Làm lại từ đầu" để kiểm tra lại.
                        </span>
                      </div>
                    `;
                  }

                  // Hide check button and next button, show "Làm lại từ đầu"
                  checkQuizBtn.classList.add('hidden');
                  if (nextQuizBtn) nextQuizBtn.classList.add('hidden');
                  if (resetQuizBtn) resetQuizBtn.classList.remove('hidden');
                  UI.showToast(`Bạn đạt ${percent}%, chưa đủ điểm chuẩn ${quizPassingPercent}%. Hãy làm lại từ đầu!`, 'warning');
                }

                checkQuizBtn.disabled = false;
              };
            }

            if (resetQuizBtn) {
              resetQuizBtn.onclick = () => {
                hasPassedQuiz = false;
                // Reset form inputs
                quizSection.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(r => r.checked = false);
                quizSection.querySelectorAll('.cisco-quiz-blank-input').forEach(inp => {
                  inp.value = '';
                  inp.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                });
                quizSection.querySelectorAll('.cisco-quiz-matching-select').forEach(sel => sel.value = '');
                quizSection.querySelectorAll('.cisco-quiz-matching-row').forEach(row => {
                  row.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                });
                quizSection.querySelectorAll('.cisco-quiz-explanation').forEach(e => {
                  e.classList.add('hidden');
                  e.innerHTML = '';
                });
                quizSection.querySelectorAll('.cisco-quiz-choice-label').forEach(lbl => {
                  lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                  const badge = lbl.querySelector('.choice-badge');
                  if (badge) badge.className = 'w-6 h-6 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center shrink-0 choice-badge';
                });
                quizSection.querySelectorAll('.cisco-quiz-tf-label').forEach(lbl => {
                  lbl.classList.remove('border-emerald-500', 'bg-emerald-50', 'dark:bg-emerald-950/40', 'border-rose-500', 'bg-rose-50', 'dark:bg-rose-950/40');
                });

                // Reset to Slide 0 (Question 1)
                currentQuizSlide = 0;
                updateQuizSlideView();

                const banner = document.getElementById('cisco-quiz-score-banner');
                if (banner) {
                  banner.innerHTML = 'Hãy hoàn thành câu trả lời cho các câu hỏi rồi bấm <strong>Kiểm tra đáp án</strong>.';
                }
                resetQuizBtn.classList.add('hidden');
                UI.showToast('Đã đặt lại bài kiểm tra. Hãy bắt đầu làm lại từ Câu 1.', 'info');
              };
            }
          }

        } catch (err) {
          contentContainer.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp nội dung bài giảng: ${UI.escapeHtml(err.message)}</div>`;
        }
      };

      // Initial Mount of Sidebar and Main Canvas
      renderSidebarOutline();
      renderSidebarResources();
      updateFloatingNav();
      await renderActiveContent();

    } catch (err) {
      container.innerHTML = `
        <div class="h-full flex items-center justify-center p-6 text-center animate-fade-in">
          <div class="max-w-md p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
            <span class="material-symbols-outlined text-4xl text-rose-500">error</span>
            <h2 class="text-base font-bold text-slate-900 dark:text-white">Lỗi tải không gian học tập</h2>
            <p class="text-xs text-slate-500">${UI.escapeHtml(err.message || 'Không thể nạp dữ liệu khóa học.')}</p>
            <div class="pt-2">
              <a href="#/student/courses" class="c-btn c-btn-primary c-btn-sm inline-flex">Quay lại danh sách môn học</a>
            </div>
          </div>
        </div>
      `;
    }
  }

  // Helper to render video player (YouTube iframe, Vimeo iframe, or HTML5 video)
  static _getEmbedVideoHtml(url, playerId = 'lesson-stream-player', isCompleted = false) {
    if (!url) return '';
    const trimmed = String(url).trim();
    // YouTube (regular watch, embed, v, youtu.be, shorts, live, extra parameters, or embed code)
    const ytId = UI.parseYouTubeId(trimmed);
    if (ytId) {
      const baseEmbed = UI.getYouTubeEmbedUrl(ytId);
      const glue = baseEmbed.includes('?') ? '&' : '?';
      return `<iframe id="${playerId}" class="w-full h-full aspect-video rounded-xl bg-black" src="${baseEmbed}${glue}enablejsapi=1&rel=0&modestbranding=1" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
    }
    // Vimeo
    const vimeoMatch = trimmed.match(/vimeo\.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|video\/|)(\d+)/);
    if (vimeoMatch && vimeoMatch[1]) {
      return `<iframe id="${playerId}" class="w-full h-full aspect-video rounded-xl bg-black" src="https://player.vimeo.com/video/${vimeoMatch[1]}?api=1" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>`;
    }
    // Direct file / HLS Encrypted Stream with Anti-Seek Custom Controls & VideoArmor
    const isHls = trimmed.includes('.m3u8') || trimmed.includes('/video/playlist');
    return `
      <div class="relative group w-full h-full aspect-video rounded-xl overflow-hidden bg-slate-950 flex flex-col justify-end select-none" id="${playerId}-container" data-custom-player="true" tabindex="0">
        <video id="${playerId}" oncontextmenu="return false;" controlsList="nodownload nofullscreen noremoteplayback" disablePictureInPicture playsinline class="w-full h-full aspect-video bg-slate-950 object-contain cursor-pointer" src="${isHls ? '' : UI.escapeHtml(trimmed)}" data-hls-src="${isHls ? UI.escapeHtml(trimmed) : ''}" preload="metadata"><p>Trình duyệt của bạn không hỗ trợ thẻ video HTML5.</p></video>

        <!-- Big Play Button Overlay -->
        <button type="button" id="${playerId}-big-play" class="absolute inset-0 m-auto w-16 h-16 rounded-full bg-slate-900/80 hover:bg-slate-900 border border-white/20 text-white flex items-center justify-center backdrop-blur-sm transition-all shadow-xl group-hover:scale-105 z-10 cursor-pointer" aria-label="Phát video">
          <span class="material-symbols-outlined text-[34px] ml-0.5 pointer-events-none">play_arrow</span>
        </button>

        <!-- Custom Control Bar -->
        <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950/95 via-slate-950/70 to-transparent p-3 pt-6 flex flex-col gap-2 z-20 transition-opacity duration-200" id="${playerId}-controls">
          <!-- Scrubber Track -->
          <div class="relative w-full h-2.5 bg-slate-700/60 rounded-full cursor-pointer group/track hover:h-3 transition-all" id="${playerId}-progress-track" title="${isCompleted ? 'Tua video tự do' : 'Khóa tua nhanh: Chỉ có thể tua lại đoạn đã xem'}">
            <div id="${playerId}-buffered-bar" class="absolute left-0 top-0 bottom-0 bg-slate-500/40 rounded-full w-0 transition-all pointer-events-none"></div>
            <div id="${playerId}-watched-bar" class="absolute left-0 top-0 bottom-0 bg-amber-500/30 rounded-full w-0 pointer-events-none"></div>
            <div id="${playerId}-played-bar" class="absolute left-0 top-0 bottom-0 bg-indigo-500 rounded-full w-0 pointer-events-none"></div>
          </div>

          <div class="flex items-center justify-between text-xs text-slate-200">
            <div class="flex items-center gap-3">
              <button type="button" id="${playerId}-play-btn" class="p-1 rounded-lg hover:bg-white/10 text-white transition-colors cursor-pointer" title="Phát/Tạm dừng">
                <span class="material-symbols-outlined text-[20px] align-middle">play_arrow</span>
              </button>
              <button type="button" id="${playerId}-mute-btn" class="p-1 rounded-lg hover:bg-white/10 text-white transition-colors cursor-pointer" title="Bật/Tắt âm">
                <span class="material-symbols-outlined text-[20px] align-middle">volume_up</span>
              </button>
              <span id="${playerId}-time" class="font-mono text-[11px] text-slate-300">00:00 / 00:00</span>
            </div>

            <div class="flex items-center gap-2">
              <span id="${playerId}-lock-indicator" class="text-[11px] ${isCompleted ? 'text-emerald-400' : 'text-amber-400'} flex items-center gap-1 font-medium">
                <span class="material-symbols-outlined text-[14px]">${isCompleted ? 'lock_open' : 'lock_clock'}</span>
                <span>${isCompleted ? 'Đã mở khóa tua' : 'Khóa tua nhanh'}</span>
              </span>
              <button type="button" id="${playerId}-fullscreen-btn" class="p-1 rounded-lg hover:bg-white/10 text-white transition-colors cursor-pointer" title="Toàn màn hình">
                <span class="material-symbols-outlined text-[20px] align-middle">fullscreen</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  static setupCustomVideoPlayer(playerId, options = {}) {
    const video = document.getElementById(playerId);
    if (!video || video.tagName !== 'VIDEO') return null;
    const container = document.getElementById(`${playerId}-container`);
    const bigPlayBtn = document.getElementById(`${playerId}-big-play`);
    const playBtn = document.getElementById(`${playerId}-play-btn`);
    const muteBtn = document.getElementById(`${playerId}-mute-btn`);
    const timeDisplay = document.getElementById(`${playerId}-time`);
    const track = document.getElementById(`${playerId}-progress-track`);
    const bufferedBar = document.getElementById(`${playerId}-buffered-bar`);
    const watchedBar = document.getElementById(`${playerId}-watched-bar`);
    const playedBar = document.getElementById(`${playerId}-played-bar`);
    const fullscreenBtn = document.getElementById(`${playerId}-fullscreen-btn`);
    const lockIndicator = document.getElementById(`${playerId}-lock-indicator`);

    // Encrypted HLS streaming playback initialization
    let hlsInstance = null;
    const streamSrc = options.streamUrl || video.src || video.getAttribute('data-hls-src') || '';
    if (streamSrc && (streamSrc.includes('.m3u8') || streamSrc.includes('/video/playlist'))) {
      if (typeof Hls !== 'undefined' && Hls.isSupported()) {
        hlsInstance = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          xhrSetup: (xhr) => {
            xhr.withCredentials = true;
          }
        });
        hlsInstance.loadSource(streamSrc);
        hlsInstance.attachMedia(video);
      } else if (typeof video.canPlayType === 'function' && video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = streamSrc;
      }
    }

    // Dynamic Forensic Watermark & Anti-Tamper Armor attachment
    let armorInstance = null;
    if (typeof VideoArmor !== 'undefined' && container) {
      const student = (typeof AuthState !== 'undefined' && AuthState.getUser) ? AuthState.getUser() : {};
      armorInstance = VideoArmor.mount(container, {
        student,
        ip: (typeof window !== 'undefined' && window.clientIp) || '127.0.0.1',
        onSecurityViolation: (reason, details) => {
          if (typeof ApiClient !== 'undefined' && ApiClient.recordTelemetry) {
            ApiClient.recordTelemetry('VIDEO_SECURITY_VIOLATION', { reason, ...details });
          }
        }
      });
    }

    let isDone = !!options.isCompleted;
    let maxWatched = isDone ? 999999 : 0;
    let lastToastTime = 0;

    if (watchedBar) watchedBar.style.width = isDone ? '100%' : '0%';
    if (playedBar) playedBar.style.width = '0%';

    const showThrottleToast = (msg, type = 'warning') => {
      const now = Date.now();
      if (now - lastToastTime > 2500) {
        lastToastTime = now;
        UI.showToast(msg, type);
      }
    };

    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds) || seconds < 0) return '00:00';
      const m = Math.floor(seconds / 60);
      const s = Math.floor(seconds % 60);
      return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    };

    const updatePlayState = () => {
      if (!playBtn) return;
      const icon = playBtn.querySelector('.material-symbols-outlined');
      if (video.paused || video.ended) {
        if (icon) icon.textContent = 'play_arrow';
        if (bigPlayBtn) bigPlayBtn.classList.remove('hidden');
      } else {
        if (icon) icon.textContent = 'pause';
        if (bigPlayBtn) bigPlayBtn.classList.add('hidden');
      }
    };

    const togglePlay = () => {
      if (video.paused || video.ended) {
        video.play().catch(() => {});
      } else {
        video.pause();
      }
    };

    if (bigPlayBtn) bigPlayBtn.onclick = (e) => { e.stopPropagation(); togglePlay(); };
    if (playBtn) playBtn.onclick = (e) => { e.stopPropagation(); togglePlay(); };
    video.onclick = () => togglePlay();

    if (muteBtn) {
      muteBtn.onclick = (e) => {
        e.stopPropagation();
        video.muted = !video.muted;
        const icon = muteBtn.querySelector('.material-symbols-outlined');
        if (icon) icon.textContent = video.muted ? 'volume_off' : 'volume_up';
      };
    }

    if (fullscreenBtn && container) {
      fullscreenBtn.onclick = (e) => {
        e.stopPropagation();
        if (!document.fullscreenElement) {
          if (container.requestFullscreen) container.requestFullscreen();
          else if (video.requestFullscreen) video.requestFullscreen();
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
        }
      };
    }

    // Scrubber click: STRICT anti-seek
    if (track) {
      track.onclick = (e) => {
        e.stopPropagation();
        const dur = video.duration;
        if (!dur || dur <= 0) return;
        const rect = track.getBoundingClientRect();
        const clickRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const targetTime = clickRatio * dur;

        if (isDone) {
          video.currentTime = targetTime;
        } else {
          // Strictly lock forward seeking: only allow jumping back to segments already watched
          if (targetTime <= maxWatched) {
            video.currentTime = targetTime;
          } else {
            video.currentTime = maxWatched;
            showThrottleToast('Khóa tua nhanh đang bật: Bạn chỉ có thể tua lại những đoạn video đã xem.');
          }
        }
      };
    }

    // Seeking event listener: strictly clamp forward jumps (from devtools, keyboard, or touch)
    video.addEventListener('seeking', () => {
      if (!isDone && video.currentTime > maxWatched + 0.3) {
        video.currentTime = maxWatched;
        showThrottleToast('Khóa tua nhanh đang bật: Cần xem tuần tự bài giảng để ghi nhận tiến độ.');
      }
    });

    // Keyboard guard: prevent forward seeking keys
    const handleKeydown = (e) => {
      if (!isDone && (['ArrowRight', 'KeyL', 'PageDown'].includes(e.code) || e.key === 'ArrowRight')) {
        e.preventDefault();
        e.stopPropagation();
        showThrottleToast('Khóa tua nhanh đang bật: Cần xem tuần tự bài giảng để ghi nhận tiến độ.');
      }
    };
    if (container) container.addEventListener('keydown', handleKeydown);
    video.addEventListener('keydown', handleKeydown);

    // Timeupdate listener
    video.addEventListener('timeupdate', () => {
      const cur = video.currentTime;
      const dur = video.duration || 0;

      // Disallow playback jumping forward past allowed buffer
      if (!isDone && cur > maxWatched + 0.8) {
        video.currentTime = maxWatched;
        return;
      }

      if (cur > maxWatched) {
        maxWatched = cur;
      }

      const pct = dur > 0 ? (cur / dur) * 100 : 0;
      const watchedPct = isDone ? 100 : (dur > 0 ? (maxWatched / dur) * 100 : 0);

      if (playedBar) playedBar.style.width = `${pct}%`;
      if (watchedBar) watchedBar.style.width = `${Math.min(100, watchedPct)}%`;
      if (timeDisplay) timeDisplay.textContent = `${formatTime(cur)} / ${formatTime(dur)}`;

      if (typeof options.onProgress === 'function') {
        options.onProgress(maxWatched, dur);
      }

      // Completion check: require at least 90% watched AND near the end
      if (dur > 0 && maxWatched >= dur * 0.90 && cur >= dur - 1.0) {
        if (!isDone) {
          isDone = true;
          maxWatched = dur || 999999;
          if (lockIndicator) {
            lockIndicator.className = 'text-[11px] text-emerald-400 flex items-center gap-1 font-medium';
            lockIndicator.innerHTML = '<span class="material-symbols-outlined text-[14px]">lock_open</span><span>Đã mở khóa tua</span>';
          }
          if (track) track.title = 'Tua video tự do';
        }
        if (typeof options.onComplete === 'function') {
          options.onComplete(dur);
        }
      }
    });

    video.addEventListener('progress', () => {
      if (video.buffered.length > 0 && video.duration > 0 && bufferedBar) {
        const bufferedEnd = video.buffered.end(video.buffered.length - 1);
        bufferedBar.style.width = `${(bufferedEnd / video.duration) * 100}%`;
      }
    });

    video.addEventListener('play', updatePlayState);
    video.addEventListener('pause', updatePlayState);
    video.addEventListener('ended', () => {
      updatePlayState();
      const dur = video.duration || 0;
      if (isDone || (dur > 0 && maxWatched >= dur * 0.90)) {
        if (!isDone) {
          isDone = true;
          maxWatched = dur || 999999;
          if (lockIndicator) {
            lockIndicator.className = 'text-[11px] text-emerald-400 flex items-center gap-1 font-medium';
            lockIndicator.innerHTML = '<span class="material-symbols-outlined text-[14px]">lock_open</span><span>Đã mở khóa tua</span>';
          }
          if (track) track.title = 'Tua video tự do';
        }
        if (typeof options.onComplete === 'function') {
          options.onComplete(dur);
        }
      } else if (!isDone) {
        showThrottleToast('Bạn cần xem ít nhất 90% thời lượng video để hoàn thành.');
      }
    });

    return {
      armor: armorInstance,
      hls: hlsInstance,
      unlockSeeking: () => {
        isDone = true;
        maxWatched = 999999;
        if (lockIndicator) {
          lockIndicator.className = 'text-[11px] text-emerald-400 flex items-center gap-1 font-medium';
          lockIndicator.innerHTML = '<span class="material-symbols-outlined text-[14px]">lock_open</span><span>Đã mở khóa tua</span>';
        }
        if (track) track.title = 'Tua video tự do';
      },
      destroy: () => {
        if (armorInstance && typeof armorInstance.destroy === 'function') armorInstance.destroy();
        if (hlsInstance && typeof hlsInstance.destroy === 'function') hlsInstance.destroy();
      }
    };
  }


  // Backwards-compatible proxies:
  static async renderCourseDetail(container, courseId, activeTab = 'syllabus') {
    return StudentView.renderCourseConsole(container, courseId, null, null, activeTab === 'resources' ? 'resources' : 'outline');
  }

  static async renderLessonReader(container, courseId, lessonId) {
    return StudentView.renderCourseConsole(container, courseId, lessonId, null, 'outline');
  }

  // =========================================================================
  // 6. Assessments Suite: Waiting Room (UTC Countdown)
  // =========================================================================
  static getWaitingRoomState(data) {
    if (data.active_attempt_id) return 'RESUME';
    if (data.is_closed) return 'CLOSED';
    if (data.is_attempt_limit_reached) return 'EXHAUSTED';
    if (data.is_waiting_room_open === false) return 'WAITING_ROOM_LOCKED';
    if (!data.is_open) return 'UPCOMING';
    return data.can_start ? 'READY' : 'UNAVAILABLE';
  }

  static async renderWaitingRoom(container, assessmentId) {
    container.innerHTML = `
      <main class="min-h-full bg-slate-50 dark:bg-slate-950 px-4 py-8 sm:py-12">
        <div class="mx-auto max-w-[1720px] w-full px-4 sm:px-6 lg:px-10 animate-pulse space-y-6">
          <div class="h-5 w-36 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="h-12 w-3/4 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="h-24 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-24 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-24 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
            <div class="h-24 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
          </div>
          <div class="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
        </div>
      </main>`;

    try {
      const data = await ApiClient.getStudentAssessmentDetail(assessmentId);
      if (!data) return;
      const assessment = data.assessment || {};
      const state = StudentView.getWaitingRoomState(data);
      const attempts = data.attempts || [];
      const latest = attempts[attempts.length - 1];
      const duration = assessment.time_limit_minutes || assessment.duration_minutes || 60;
      let remaining = Math.max(0, Number(data.seconds_until_open) || 0);
      let remainingWaitLock = Math.max(0, Number(data.seconds_until_waiting_room_open) || 0);

      const statusConfig = {
        READY: { text: 'Sẵn sàng vào thi', class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700' },
        RESUME: { text: 'Đang làm dở dang', class: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-300 dark:border-amber-700' },
        UPCOMING: { text: 'Phòng chờ đang mở (Chờ phát đề)', class: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-300 dark:border-indigo-700' },
        WAITING_ROOM_LOCKED: { text: 'Chưa mở phòng chờ (Mở trước 30p)', class: 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300 border-purple-300 dark:border-purple-700' },
        CLOSED: { text: 'Đã kết thúc', class: 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border-rose-300 dark:border-rose-700' },
        EXHAUSTED: { text: 'Đã hết lượt thi', class: 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700' },
        UNAVAILABLE: { text: 'Chưa thể bắt đầu', class: 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700' }
      }[state] || { text: 'Chưa xác định', class: 'bg-slate-100 text-slate-700 border-slate-300' };

      const actionText = state === 'RESUME' ? 'Tiếp Tục Phiên Làm Bài' : 'Bắt Đầu Làm Bài Thi';
      const canAct = state === 'READY' || state === 'RESUME';

      const candidateName = data.student_name || 'Thí sinh PWD301';
      const candidateEmail = data.student_email || 'student@pwd301.edu.vn';
      const questionsCount = data.questions_count || assessment.question_count || 'Theo đề';
      const passScore = assessment.pass_score != null ? assessment.pass_score : '5.0';

      container.innerHTML = `
        <main class="min-h-full bg-slate-50 dark:bg-slate-950 px-4 py-8 sm:py-10 text-slate-800 dark:text-slate-100 font-sans">
          <div class="mx-auto max-w-[1720px] w-full px-4 sm:px-6 lg:px-10 space-y-6">
            
            <!-- Breadcrumbs -->
            <div class="flex items-center justify-between">
              <a href="#/student/assessments" class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-primary transition-colors">
                <span class="material-symbols-outlined text-base">arrow_back</span>
                <span>Quay lại danh sách bài thi</span>
              </a>
              <span class="text-xs font-mono text-slate-400">Mã bài: #${UI.escapeHtml(assessmentId).slice(0, 8)}</span>
            </div>

            <!-- Exam Hero Header Card -->
            <div class="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-8 shadow-sm space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold ${statusConfig.class}">
                    <span class="w-2 h-2 rounded-full bg-current animate-pulse"></span>
                    ${statusConfig.text}
                  </span>
                  <span class="inline-flex items-center gap-1 rounded-full bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 px-3 py-1 text-xs font-bold text-rose-700 dark:text-rose-300">
                    <span class="material-symbols-outlined text-[15px]">security</span>
                    Giám sát khảo thí bắt buộc 100%
                  </span>
                </div>
                <div class="text-xs text-slate-500 font-mono">
                  ${assessment.course_code ? `<span class="font-bold text-primary">${UI.escapeHtml(assessment.course_code)}</span> · ` : ''}
                  ${UI.escapeHtml(assessment.course_title || 'Khóa học')}
                </div>
              </div>

              <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                  ${UI.escapeHtml(assessment.title || data.title || 'Bài kiểm tra')}
                </h1>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Giảng viên phụ trách: <strong class="text-slate-700 dark:text-slate-300">${UI.escapeHtml(assessment.instructor_name || 'Bộ môn Khảo thí')}</strong> · Hình thức: <strong class="text-slate-700 dark:text-slate-300">Khảo thí trực tuyến có giám sát hành vi</strong>
                </p>
              </div>

              <!-- 4 Metrics Grid -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                <div class="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-3.5 space-y-1">
                  <div class="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <span class="material-symbols-outlined text-base text-indigo-500">timer</span>
                    Thời lượng thi
                  </div>
                  <div class="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white">${duration} <span class="text-xs font-normal text-slate-500">phút</span></div>
                </div>

                <div class="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-3.5 space-y-1">
                  <div class="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <span class="material-symbols-outlined text-base text-sky-500">quiz</span>
                    Số lượng câu
                  </div>
                  <div class="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white">${questionsCount} <span class="text-xs font-normal text-slate-500">câu</span></div>
                </div>

                <div class="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-3.5 space-y-1">
                  <div class="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <span class="material-symbols-outlined text-base text-emerald-500">check_circle</span>
                    Điểm đạt yêu cầu
                  </div>
                  <div class="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white">${passScore} <span class="text-xs font-normal text-slate-500">/ 10</span></div>
                </div>

                <div class="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-3.5 space-y-1">
                  <div class="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <span class="material-symbols-outlined text-base text-amber-500">replay</span>
                    Lượt làm bài
                  </div>
                  <div class="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white">
                    ${data.attempt_limit ? `${data.attempts_count || 0}/${data.attempt_limit}` : 'Không giới hạn'}
                  </div>
                </div>
              </div>
            </div>

            <!-- Two Columns Section -->
            <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px] items-start">
              
              <!-- Left Column: Candidate Card, Proctoring Rules, Pledge & Action -->
              <div class="space-y-6">
                
                <!-- Candidate Identity Card -->
                <div class="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
                  <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-base text-primary">badge</span>
                      Thông tin thí sinh dự thi
                    </div>
                    <span class="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-800">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      Hồ sơ hợp lệ
                    </span>
                  </div>

                  <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-primary to-indigo-500 text-white flex items-center justify-center font-bold text-xl shadow-md shrink-0">
                      ${UI.escapeHtml(candidateName.charAt(0).toUpperCase())}
                    </div>
                    <div class="space-y-1 min-w-0">
                      <div class="text-base font-extrabold text-slate-900 dark:text-white truncate">
                        ${UI.escapeHtml(candidateName)}
                      </div>
                      <div class="text-xs text-slate-500 dark:text-slate-400 font-mono truncate">
                        ${UI.escapeHtml(candidateEmail)}
                      </div>
                      <div class="text-[11px] text-slate-400 flex items-center gap-2 pt-0.5">
                        <span>Thiết bị: Trình duyệt Web</span>
                        <span>·</span>
                        <span>Phiên đăng nhập an toàn</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Official Proctoring Regulations (Rules Box) -->
                <div class="rounded-2xl border-2 border-rose-200 dark:border-rose-900/60 bg-gradient-to-b from-rose-50/40 to-white dark:from-rose-950/20 dark:to-slate-900 p-6 shadow-sm space-y-4">
                  <div class="flex items-center gap-2.5 text-rose-700 dark:text-rose-400">
                    <div class="w-8 h-8 rounded-xl bg-rose-100 dark:bg-rose-950/60 flex items-center justify-center shrink-0">
                      <span class="material-symbols-outlined text-xl">shield</span>
                    </div>
                    <div>
                      <h2 class="text-sm font-extrabold uppercase tracking-wide">Quy chế giám sát khảo thí (Bắt buộc 100%)</h2>
                      <p class="text-[11px] text-slate-500 dark:text-slate-400">Hệ thống áp dụng các tiêu chuẩn an toàn khảo thí nghiêm ngặt trong suốt thời gian thi</p>
                    </div>
                  </div>

                  <div class="grid gap-3 sm:grid-cols-2 pt-1 text-xs">
                    <div class="p-3 rounded-xl border border-rose-100 dark:border-rose-900/40 bg-white dark:bg-slate-900/80 space-y-1">
                      <div class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-rose-500 text-base">fullscreen</span>
                        Toàn màn hình bắt buộc
                      </div>
                      <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                        Chế độ toàn màn hình tự động bật khi vào thi. Nếu thoát ra ngoài, hệ thống sẽ kích hoạt màn hình khóa khẩn cấp và ghi nhận vi phạm.
                      </p>
                    </div>

                    <div class="p-3 rounded-xl border border-rose-100 dark:border-rose-900/40 bg-white dark:bg-slate-900/80 space-y-1">
                      <div class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-rose-500 text-base">hourglass_top</span>
                        Đo đếm thời gian vắng mặt
                      </div>
                      <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                        Hệ thống tự động tính toán tổng số giây thí sinh rời khỏi tab hoặc mất tiêu điểm, báo cáo trực tiếp về biên bản thi của giảng viên.
                      </p>
                    </div>

                    <div class="p-3 rounded-xl border border-rose-100 dark:border-rose-900/40 bg-white dark:bg-slate-900/80 space-y-1">
                      <div class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-rose-500 text-base">block</span>
                        Chặn chuột phải & Phím tắt
                      </div>
                      <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                        Vô hiệu hóa chuột phải (Context menu), cấm sao chép nội dung (Copy/Cut), vô hiệu hóa F12 và các phím tắt công cụ nhà phát triển.
                      </p>
                    </div>

                    <div class="p-3 rounded-xl border border-rose-100 dark:border-rose-900/40 bg-white dark:bg-slate-900/80 space-y-1">
                      <div class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-rose-500 text-base">cloud_sync</span>
                        Tự lưu & Khóa phiên sửa
                      </div>
                      <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                        Lưu đáp án tự động từng câu hỏi lên máy chủ. Mỗi bài thi chỉ cho phép 01 phiên làm bài duy nhất hoạt động để chống can thiệp nhiều thiết bị.
                      </p>
                    </div>
                  </div>
                </div>

                <!-- Honor Code Pledge & Action CTA -->
                <div class="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-8 shadow-sm space-y-6">
                  ${state === 'WAITING_ROOM_LOCKED' ? `
                    <div class="text-center py-6 space-y-4">
                      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 text-xs font-bold border border-purple-200 dark:border-purple-800">
                        <span class="material-symbols-outlined text-[16px]">lock_clock</span>
                        <span>Phòng chờ thi chưa kích hoạt</span>
                      </div>
                      <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Đếm ngược đến giờ mở phòng chờ (30 phút trước thi)</div>
                      <div id="waiting-room-countdown" class="text-5xl font-black font-mono tracking-tight text-purple-700 dark:text-purple-300 tabular-nums">
                        ${UI.formatDuration(remainingWaitLock)}
                      </div>
                      <p class="text-xs text-slate-500 max-w-md mx-auto">
                        Theo quy chế, phòng chờ chỉ mở trước giờ thi 30 phút. Vui lòng quay lại hoặc chờ màn hình tự động làm mới khi hết thời gian đếm ngược.
                      </p>
                    </div>
                  ` : ''}

                  ${state === 'UPCOMING' ? `
                    <div class="text-center py-6 space-y-3">
                      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800 mb-1">
                        <span class="material-symbols-outlined text-[16px]">meeting_room</span>
                        <span>Đang trong phòng chờ thi</span>
                      </div>
                      <div class="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">Đếm ngược đến giờ phát đề & mở bài thi</div>
                      <div id="waiting-room-countdown" class="text-5xl font-black font-mono tracking-tight text-indigo-700 dark:text-indigo-300 tabular-nums">
                        ${UI.formatDuration(remaining)}
                      </div>
                      <p class="text-xs text-slate-500">Trang phòng chờ sẽ tự động kích hoạt nút vào thi khi bộ đếm về 00:00:00.</p>
                    </div>
                  ` : ''}

                  ${state === 'CLOSED' ? `
                    <div class="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-200 space-y-1">
                      <div class="font-bold text-sm">Bài thi đã kết thúc thời gian làm bài</div>
                      <p>Kỳ thi này hiện đã đóng. Bạn không thể bắt đầu thêm lượt làm bài mới.</p>
                    </div>
                  ` : ''}

                  ${state === 'EXHAUSTED' ? `
                    <div class="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200 space-y-1">
                      <div class="font-bold text-sm">Bạn đã dùng hết số lượt làm bài được phép</div>
                      <p>Số lượt thi tối đa là ${data.attempt_limit} lượt. Bạn đã hoàn thành tất cả các lượt thi quy định.</p>
                    </div>
                  ` : ''}

                  ${state === 'UNAVAILABLE' ? `
                    <div class="p-4 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 space-y-1">
                      <div class="font-bold text-sm">Bài thi hiện chưa thể bắt đầu</div>
                      <p>Vui lòng kiểm tra lịch thi của khóa học hoặc liên hệ giảng viên phụ trách để được hướng dẫn.</p>
                    </div>
                  ` : ''}

                  ${canAct ? `
                    <!-- Honor Code Pledge -->
                    <div class="p-4 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/60 dark:bg-indigo-950/30 flex items-start gap-3 transition-colors">
                      <input
                        type="checkbox"
                        id="waiting-room-pledge-check"
                        class="mt-1 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary cursor-pointer shrink-0"
                      />
                      <label for="waiting-room-pledge-check" class="text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200 cursor-pointer select-none leading-relaxed">
                        Tôi xác nhận là thí sinh chính chủ, cam đoan tự giác làm bài trung thực, không gian lận, tuân thủ 100% quy chế khảo thí và đồng ý kích hoạt chế độ giám sát toàn màn hình.
                      </label>
                    </div>

                    <!-- Action Button -->
                    <button
                      type="button"
                      id="start-exam-action-btn"
                      disabled
                      class="w-full py-4 px-6 rounded-xl font-extrabold text-sm sm:text-base bg-indigo-700 hover:bg-indigo-800 text-white shadow-lg shadow-indigo-700/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                    >
                      <span class="material-symbols-outlined text-xl">fullscreen</span>
                      <span>${actionText}</span>
                      <span class="material-symbols-outlined text-xl">arrow_forward</span>
                    </button>
                    <p class="text-[11px] text-center text-slate-500 dark:text-slate-400">
                      Khi bấm nút, màn hình sẽ mở chế độ toàn màn hình và đồng hồ đếm ngược bắt đầu chạy.
                    </p>
                  ` : ''}

                  ${latest?.is_score_released ? `
                    <div class="pt-2">
                      <a class="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 px-5 py-3 text-xs sm:text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" href="#/student/assessments/results?id=${UI.escapeHtml(latest.attempt_id)}">
                        <span class="material-symbols-outlined text-base">analytics</span>
                        Xem Bảng Điểm & Kết Quả Lượt Trước
                      </a>
                    </div>
                  ` : ''}
                </div>

              </div>

              <!-- Right Column: Exam Instructions & Guidance -->
              <aside class="space-y-6">
                <!-- Exam Instructions Card -->
                <div class="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-3 text-xs leading-relaxed">
                  <h3 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-base text-amber-500">lightbulb</span>
                    Lưu ý quan trọng
                  </h3>
                  <ul class="space-y-2 text-slate-600 dark:text-slate-400 list-disc list-inside">
                    <li>Giao diện thi: <strong class="text-slate-800 dark:text-slate-200">${assessment.exam_layout === 'FOCUS' ? 'Tập trung từng câu một' : 'Toàn bộ danh sách câu hỏi'}</strong>.</li>
                    <li>Vui lòng tắt các phần mềm chat, ứng dụng ghi màn hình và thông báo trước khi bắt đầu.</li>
                    <li>Tuyệt đối không tải lại trang (F5) hoặc đóng trình duyệt. Nếu rớt mạng, hãy giữ nguyên và kết nối lại ngay.</li>
                    <li>Hệ thống lưu tự động theo từng câu; điểm số được chốt khi bấm "Nộp bài thi" hoặc hết giờ.</li>
                  </ul>
                </div>

              </aside>
            </div>

          </div>
        </main>
      `;

      // Pledge checkbox logic
      const pledgeCheck = container.querySelector('#waiting-room-pledge-check');
      const startButton = container.querySelector('#start-exam-action-btn');
      if (pledgeCheck && startButton) {
        pledgeCheck.addEventListener('change', () => {
          startButton.disabled = !pledgeCheck.checked;
        });
      }

      // Start Exam Handler
      startButton?.addEventListener('click', async () => {
        // Request fullscreen immediately within the user gesture click!
        try {
          if (document.documentElement.requestFullscreen) {
            await document.documentElement.requestFullscreen();
          } else if (container.requestFullscreen) {
            await container.requestFullscreen();
          }
        } catch (_fsErr) {
          // Fullscreen may fail on restricted browsers; do not block learner
        }

        if (state === 'RESUME') {
          window.location.hash = `#/student/assessments/attempt?id=${data.active_attempt_id}`;
          return;
        }

        startButton.disabled = true;
        startButton.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span> Đang Mở Bài Thi...';
        try {
          const attempt = await ApiClient.startAssessmentAttempt(assessmentId);
          window.location.hash = `#/student/assessments/attempt?id=${attempt.attempt_id}`;
        } catch (error) {
          UI.showToast(error.message || 'Không thể bắt đầu bài thi.', 'error');
          startButton.disabled = false;
          startButton.innerHTML = `<span class="material-symbols-outlined text-xl">fullscreen</span><span>${actionText}</span><span class="material-symbols-outlined text-xl">arrow_forward</span>`;
        }
      });

      // Waiting room locked countdown ticker (waiting for room to open 30 min before exam)
      if (state === 'WAITING_ROOM_LOCKED' && remainingWaitLock > 0) {
        const lockTicker = setInterval(() => {
          const countdown = container.querySelector('#waiting-room-countdown');
          if (!countdown) { clearInterval(lockTicker); return; }
          remainingWaitLock = Math.max(0, remainingWaitLock - 1);
          countdown.textContent = UI.formatDuration(remainingWaitLock);
          if (remainingWaitLock === 0) {
            clearInterval(lockTicker);
            StudentView.renderWaitingRoom(container, assessmentId);
          }
        }, 1000);
      }

      // Upcoming countdown ticker (waiting room is open, waiting for exam to open)
      if (state === 'UPCOMING' && remaining > 0) {
        const ticker = setInterval(() => {
          const countdown = container.querySelector('#waiting-room-countdown');
          if (!countdown) { clearInterval(ticker); return; }
          remaining = Math.max(0, remaining - 1);
          countdown.textContent = UI.formatDuration(remaining);
          if (remaining === 0) {
            clearInterval(ticker);
            StudentView.renderWaitingRoom(container, assessmentId);
          }
        }, 1000);
      }
    } catch (error) {
      container.innerHTML = `<div class="p-8 text-center text-rose-700 dark:text-rose-300">Không tải được phòng chờ: ${UI.escapeHtml(error.message)}</div>`;
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

      if (data.is_completed || ['GRADED', 'SUBMITTED', 'PENDING_GRADING'].includes(data.status)) {
        window.location.hash = `#/student/assessments/results?id=${attemptId}`;
        return;
      }

      const leaseToken = data.lease_token || '';
      const questions = data.questions || [];
      const focusLayout = data.exam_layout === 'FOCUS';
      let remainingSeconds = data.remaining_seconds || ((data.time_limit_minutes || data.duration_minutes) ? (data.time_limit_minutes || data.duration_minutes) * 60 : 3600);

      const flaggedQuestions = new Set();
      const answeredQuestions = new Set();
      const pendingAnswerSaves = new Set();
      const answerSaveTails = new Map();
      const failedAnswerSaves = new Set();
      const answerPayloads = new Map();
      let maxInitialSeq = data.max_sequence || 0;
      if (Array.isArray(questions)) {
        questions.forEach(q => {
          if (typeof q.last_client_sequence === 'number' && q.last_client_sequence > maxInitialSeq) {
            maxInitialSeq = q.last_client_sequence;
          }
        });
      }
      let clientSeqCounter = maxInitialSeq;
      const saveAnswerInOrder = (questionId, answer) => {
        clientSeqCounter++;
        const enrichedPayload = {
          ...answer,
          client_sequence: clientSeqCounter,
          client_change_id: typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
            ? crypto.randomUUID()
            : ('chg-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9))
        };
        answerPayloads.set(questionId, enrichedPayload);
        const updateAutosaveHeader = () => {
          const indicator = document.getElementById('exam-autosave-indicator');
          if (!indicator) return;
          if (pendingAnswerSaves.size > 0) {
            indicator.innerHTML = '<span class="material-symbols-outlined text-[16px] text-amber-500 animate-spin">sync</span> <span class="hidden sm:inline">Đang lưu tự động...</span>';
          } else if (failedAnswerSaves.size > 0) {
            indicator.innerHTML = `<span class="material-symbols-outlined text-[16px] text-rose-500">sync_problem</span> <span class="hidden sm:inline">${failedAnswerSaves.size} câu chưa lưu</span>`;
          } else {
            indicator.innerHTML = '<span class="material-symbols-outlined text-[16px] text-emerald-500">check_circle</span> <span class="hidden sm:inline">Đã lưu tự động</span>';
          }
        };

        const previous = answerSaveTails.get(questionId) || Promise.resolve();
        const save = previous
          .catch(() => {})
          .then(() => ApiClient.saveAttemptAnswer(attemptId, questionId, enrichedPayload, leaseToken));
        answerSaveTails.set(questionId, save);
        pendingAnswerSaves.add(save);
        updateAutosaveHeader();
        return save
          .then(result => {
            failedAnswerSaves.delete(questionId);
            updateAutosaveHeader();
            return result;
          })
          .catch(error => {
            failedAnswerSaves.add(questionId);
            updateAutosaveHeader();
            throw error;
          })
          .finally(() => {
            pendingAnswerSaves.delete(save);
            if (answerSaveTails.get(questionId) === save) answerSaveTails.delete(questionId);
            updateAutosaveHeader();
          });
      };

      // Check pre-selected answers
      questions.forEach((q, idx) => {
        const grouped = parseGroupedAttemptChoices(q);
        const selectedKeys = new Set(
          (Array.isArray(q.selected_choice_keys) ? q.selected_choice_keys : []).map(String)
        );
        const fillBlankCount = (String(q.content || '').match(/_{3,}/g) || []).length || 1;
        const fillAnswers = String(q.answer_text || '').split('|||');
        const hasSelected = q.interaction_type === 'FILL_IN'
          ? fillAnswers.length === fillBlankCount && fillAnswers.every(value => value.trim())
          : grouped
          ? grouped.groups.every(group => group.choices.some(choice =>
            selectedKeys.has(String(choice.choice_key || choice.choice_id || choice.id))
          ))
          : (q.choices || []).some(c => c.is_selected)
            || selectedKeys.size > 0
            || Boolean(String(q.answer_text || '').trim());
        if (hasSelected) answeredQuestions.add(idx);
      });

      container.innerHTML = `
        <div id="exam-attempt-console-root" class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans select-none">
          
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

            <!-- Proctoring Status Pill & Controls -->
            <div class="flex items-center gap-3">
              <div id="exam-proctoring-indicator" class="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 text-[11px] font-mono font-semibold flex items-center gap-1.5 transition-all">
                <span id="exam-proctoring-dot" class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span id="exam-proctoring-text">Giám sát trực tiếp (0 vi phạm)</span>
              </div>

              <button type="button" id="exam-fullscreen-btn" class="rounded-lg border border-slate-300 dark:border-slate-700 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1 transition-colors" title="Bật/Tắt Toàn Màn Hình">
                <span class="material-symbols-outlined text-[16px]">fullscreen</span>
                <span class="hidden md:inline">Toàn màn hình</span>
              </button>

              <!-- View Mode Switcher (Icon-Only per user contract) -->
              <div class="flex items-center p-0.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" id="exam-view-mode-toggle" role="group" aria-label="Chế độ hiển thị bài thi">
                <button type="button" id="btn-mode-focus" class="p-1.5 rounded-lg transition-all ${focusLayout ? 'bg-white dark:bg-slate-700 text-primary shadow-2xs font-bold' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}" title="Chế độ tập trung (Từng câu một)">
                  <span class="material-symbols-outlined text-[18px]">view_agenda</span>
                </button>
                <button type="button" id="btn-mode-standard" class="p-1.5 rounded-lg transition-all ${!focusLayout ? 'bg-white dark:bg-slate-700 text-primary shadow-2xs font-bold' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}" title="Chế độ danh sách (Toàn bộ đề thi)">
                  <span class="material-symbols-outlined text-[18px]">format_list_bulleted</span>
                </button>
              </div>

              <div id="exam-autosave-indicator" class="text-xs text-slate-400 flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px] text-emerald-500">cloud_done</span>
                <span class="hidden xl:inline">Tự động lưu bài UTC</span>
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

          <!-- Emergency Fullscreen Lockdown Overlay -->
          <div id="exam-fullscreen-lockdown-overlay" class="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 hidden">
            <div class="max-w-md w-full bg-white dark:bg-slate-900 border-2 border-rose-500 rounded-2xl p-6 sm:p-8 text-center space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
              <div class="w-16 h-16 mx-auto rounded-full bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl">screen_lock_portrait</span>
              </div>
              <div class="space-y-2">
                <h3 class="text-xl font-extrabold text-slate-900 dark:text-white">CẢNH BÁO VI PHẠM KHẢO THÍ!</h3>
                <p class="text-xs text-rose-600 dark:text-rose-400 font-semibold uppercase tracking-wider">Đã thoát khỏi chế độ toàn màn hình</p>
                <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  Kỳ thi yêu cầu duy trì chế độ toàn màn hình liên tục để chống gian lận. Hệ thống đang tính thời gian vắng mặt và gửi báo cáo vi phạm trực tiếp về máy chủ của giảng viên.
                </p>
              </div>
              <div class="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-700 dark:text-slate-300 flex justify-around">
                <div>
                  <div class="text-[10px] text-slate-500 uppercase">Số lần vi phạm</div>
                  <div class="text-base font-bold text-rose-600 dark:text-rose-400" id="lockdown-violation-count">1</div>
                </div>
                <div class="border-r border-slate-200 dark:border-slate-700"></div>
                <div>
                  <div class="text-[10px] text-slate-500 uppercase">Tổng thời gian rời màn</div>
                  <div class="text-base font-bold text-amber-600 dark:text-amber-400" id="lockdown-away-seconds">0s</div>
                </div>
              </div>
              <button type="button" id="lockdown-return-fullscreen-btn" class="w-full py-3 px-6 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm shadow-lg shadow-rose-600/30 transition-all flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-lg">fullscreen</span>
                <span>QUAY LẠI TOÀN MÀN HÌNH NGAY</span>
              </button>
            </div>
          </div>

          <!-- Main Layout: Question Palette & Contextual Navigator -->
          <div class="flex-1 flex overflow-hidden">
            
            <!-- Left/Center Canvas: Question Palette -->
            <div class="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6 max-w-4xl mx-auto" id="questions-viewport">
              ${questions.map((q, idx) => `
                <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4 question-card transition-all ${focusLayout && idx > 0 ? 'hidden' : ''}" id="q_card_${idx}" data-q-index="${idx}" data-qid="${q.attempt_question_id || q.question_id || q.id}">
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
                    ${(() => {
                      const grouped = parseGroupedAttemptChoices(q);
                      const questionText = String(q.content || q.stem || '')
                        .replace(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):[^\]]+\]\]/gi, '')
                        .replace(/!\[.*?\]\([^\)]+\)/gi, '')
                        .replace(/<img[^>]*>/gi, '')
                        .trim();
                      if (q.interaction_type === 'FILL_IN') {
                        const answers = String(q.answer_text || '').split('|||');
                        const placeholderCount = (questionText.match(/_{3,}/g) || []).length;
                        let blankIndex = 0;
                        const promptWithInputs = UI.escapeHtml(questionText).replace(/_{3,}/g, () => {
                          const index = blankIndex++;
                          return `<label class="inline-flex flex-col align-middle gap-1 mx-1 my-1 min-w-28">
                            <span class="text-[10px] font-semibold text-indigo-800 dark:text-indigo-200">Blank ${index + 1}</span>
                            <input type="text" class="assessment-fill-blank rounded-md border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2 py-1.5 text-sm font-medium text-slate-900 dark:text-slate-100" data-blank-index="${index}" value="${UI.escapeHtml(answers[index] || '')}" aria-label="Answer for blank ${index + 1}" autocomplete="off" />
                          </label>`;
                        });
                        const remainingInputs = placeholderCount === 0
                          ? `<label class="block mt-3 space-y-1"><span class="text-xs font-semibold">Answer</span><input type="text" class="assessment-fill-blank w-full rounded-md border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2 py-1.5 text-sm font-medium text-slate-900 dark:text-slate-100" data-blank-index="0" value="${UI.escapeHtml(answers[0] || '')}" aria-label="Answer for blank 1" autocomplete="off" /></label>`
                          : '';
                        return `${promptWithInputs}${remainingInputs}`;
                      }
                      if (!grouped) return UI.escapeHtml(questionText);

                      const selectedKeys = new Set(
                        (Array.isArray(q.selected_choice_keys) ? q.selected_choice_keys : []).map(String)
                      );
                      const renderSlot = group => {
                        const left = grouped.kind === 'MATCH'
                          ? (group.choices[0]?.interaction_left || `Item ${group.index}`)
                          : `Blank ${group.index}`;
                        const options = group.choices.map(choice => {
                          const key = String(choice.choice_key || choice.choice_id || choice.id);
                          const answerText = choice.answerText;
                          return `<option value="${UI.escapeHtml(key)}" data-answer-text="${UI.escapeHtml(answerText)}" ${selectedKeys.has(key) ? 'selected' : ''}>${UI.escapeHtml(answerText)}</option>`;
                        }).join('');
                        return `<span class="interactive-drop-slot inline-flex flex-col align-middle gap-1 mx-1 my-1 min-w-32 rounded-lg border border-dashed border-indigo-300 dark:border-indigo-700 bg-indigo-50/70 dark:bg-indigo-950/30 p-2" data-group-index="${group.index}">
                          <label class="text-[10px] font-semibold text-indigo-800 dark:text-indigo-200">${UI.escapeHtml(left)}</label>
                          <select class="interactive-slot-select w-full rounded-md border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2 py-1 text-xs font-medium text-slate-900 dark:text-slate-100" data-group-index="${group.index}" aria-label="${UI.escapeHtml(left)}">
                            <option value="">Choose an answer</option>${options}
                          </select>
                        </span>`;
                      };

                      let groupCursor = 0;
                      const escapedQuestion = UI.escapeHtml(questionText);
                      const promptWithSlots = grouped.kind === 'MATCH'
                        ? escapedQuestion
                        : escapedQuestion.replace(/_{3,}/g, () => renderSlot(grouped.groups[groupCursor++] || grouped.groups[grouped.groups.length - 1]));
                      const remainingSlots = grouped.kind === 'MATCH'
                        ? grouped.groups.map(renderSlot).join('')
                        : grouped.groups.slice(groupCursor).map(renderSlot).join('');
                      const tokenLabels = grouped.kind === 'DRAG'
                        ? Array.from(new Set(grouped.groups.flatMap(group => group.choices.map(choice => choice.answerText))))
                        : [];
                      const tokenBank = tokenLabels.length ? `<div class="interactive-token-bank mt-3 flex flex-wrap gap-2" aria-label="Draggable answer tokens">
                        ${tokenLabels.map(token => `<button type="button" draggable="true" class="interactive-token cursor-grab touch-manipulation rounded-full border border-indigo-200 dark:border-indigo-800 bg-indigo-100 dark:bg-indigo-900 px-3 py-1.5 text-xs font-semibold text-indigo-950 dark:text-indigo-100" data-token="${UI.escapeHtml(token)}">${UI.escapeHtml(token)}</button>`).join('')}
                      </div>` : '';
                      return `<div>${promptWithSlots}${remainingSlots ? `<div class="mt-2 flex flex-wrap items-start gap-2">${remainingSlots}</div>` : ''}</div>${tokenBank}`;
                    })()}
                  </div>

                  ${(() => {
                    const rawContent = String(q.content || q.stem || '');
                    const markerIds = [...rawContent.matchAll(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):([^\]]+)\]\]/gi)].map(m => m[1]);
                    const mdMatches = [...rawContent.matchAll(/!\[.*?\]\((https?:\/\/[^\s\)]+|\/[^\s\)]+|data:image\/[^\s\)]+)\)/gi)].map(m => m[1]);
                    const htmlImgMatches = [...rawContent.matchAll(/<img[^>]+src=["']([^"']+)["']/gi)].map(m => m[1]);
                    const resList = (Array.isArray(q.resources) && q.resources.length > 0)
                      ? q.resources.map(r => r.download_url || r.url || (r.asset_id ? `/student/files/${r.asset_id}/download?disposition=inline` : '')).filter(Boolean)
                      : [];
                    const idList = [
                      ...(q.image_asset_ids || []),
                      ...(q.image_asset_id ? [q.image_asset_id] : []),
                      ...markerIds
                    ].filter(Boolean);
                    idList.forEach(aid => {
                      const url = `/student/files/${aid}/download?disposition=inline`;
                      if (!resList.includes(url)) resList.push(url);
                    });
                    mdMatches.forEach(u => { if (!resList.includes(u)) resList.push(u); });
                    htmlImgMatches.forEach(u => { if (!resList.includes(u)) resList.push(u); });
                    if (q.image_url && !resList.includes(q.image_url)) resList.push(q.image_url);
                    if (q.media_url && !resList.includes(q.media_url)) resList.push(q.media_url);

                    if (!resList.length) return '';
                    return `
                      <div class="space-y-3 my-2">
                        ${resList.map((imgUrl, imageIndex) => `
                          <img
                            src="${UI.escapeHtml(imgUrl)}"
                            alt="Question ${idx + 1} illustration ${imageIndex + 1}"
                            loading="lazy"
                            class="max-h-80 max-w-full rounded-lg border border-slate-200 dark:border-slate-700 object-contain bg-white dark:bg-slate-900"
                            onerror="this.onerror=null; this.style.display='none'"
                          />
                        `).join('')}
                      </div>
                    `;
                  })()}

                  <!-- Choices List -->
                  <div class="space-y-2.5 pt-1">
                    ${q.interaction_type === 'FILL_IN' || parseGroupedAttemptChoices(q) ? '' : q.question_type === 'SHORT_ANSWER' ? `
                      <label class="block space-y-2">
                        <span class="block text-xs font-semibold text-slate-600 dark:text-slate-300">Câu trả lời</span>
                        <input
                          type="text"
                          class="assessment-short-answer w-full px-3 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                          data-q-index="${idx}"
                          value="${UI.escapeHtml(q.answer_text || '')}"
                          placeholder="Nhập câu trả lời của bạn"
                          autocomplete="off"
                        />
                      </label>
                    ` : (q.choices || []).map(c => `
                      <label class="flex items-start gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer transition-colors choice-label">
                        <input
                          type="${q.question_type === 'MULTIPLE_CHOICE' ? 'checkbox' : 'radio'}"
                          name="q_answer_${idx}"
                          value="${c.choice_key || c.choice_id || c.id}"
                          class="mt-1 text-primary focus:ring-primary/20 cursor-pointer"
                          ${c.is_selected || (q.selected_choice_keys || []).includes(String(c.choice_key || c.choice_id || c.id)) ? 'checked' : ''}
                        />
                        <span class="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-normal flex-1">
                          <strong>${c.label || ''}</strong> ${UI.escapeHtml(cleanChoiceText(c.content || c.text || ''))}
                        </span>
                      </label>
                    `).join('')}
                  </div>
                </div>
              `).join('')}
              <!-- Focus Mode Navigation Bar -->
              <nav id="focus-nav-container" class="flex items-center justify-between gap-3 pt-3 ${focusLayout ? '' : 'hidden'}" aria-label="Điều hướng câu hỏi">
                <button type="button" id="exam-prev-question" class="rounded-xl border border-slate-300 dark:border-slate-700 px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-1.5 cursor-pointer">
                  <span class="material-symbols-outlined text-[18px]">arrow_back</span>
                  <span>Câu Trước</span>
                </button>
                <span id="exam-focus-position" class="text-sm font-bold font-mono px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700">
                  Câu 1 / ${questions.length}
                </span>
                <button type="button" id="exam-next-question" class="rounded-xl bg-primary hover:bg-primary/90 px-4 py-2 text-sm font-semibold text-slate-50 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer">
                  <span>Câu Tiếp</span>
                  <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              </nav>

              <!-- Standard Mode Bottom Submit Bar -->
              <div id="standard-submit-container" class="pt-8 pb-12 flex flex-col items-center justify-center gap-2 ${focusLayout ? 'hidden' : ''}">
                <button type="button" id="exam-submit-standard-btn" class="px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2 cursor-pointer">
                  <span class="material-symbols-outlined text-[20px]">task_alt</span>
                  <span>Nộp bài thi</span>
                </button>
                <p class="text-[11px] text-slate-400">Bạn đã xem toàn bộ câu hỏi. Nhấn nộp bài để hoàn tất kỳ thi.</p>
              </div>
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
                      data-navigate-question="${idx}"
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

      let currentLayout = focusLayout ? 'FOCUS' : 'STANDARD';
      let activeQuestionIndex = 0;

      const getConsoleRoot = () => document.getElementById('exam-attempt-console-root') || container;
      const getConsoleEl = (selector) => getConsoleRoot()?.querySelector(selector) || document.querySelector(selector);
      const getConsoleAll = (selector) => {
        const root = getConsoleRoot();
        const nodes = root?.querySelectorAll(selector);
        return (nodes && nodes.length > 0) ? nodes : document.querySelectorAll(selector);
      };

      const updateMatrixHighlight = (index) => {
        getConsoleAll('.matrix-cell').forEach((cell, cellIdx) => {
          if (cellIdx === index) {
            cell.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-600', 'dark:ring-offset-slate-900', 'font-black');
          } else {
            cell.classList.remove('ring-2', 'ring-offset-2', 'ring-indigo-600', 'dark:ring-offset-slate-900', 'font-black');
          }
        });
      };

      const showQuestion = index => {
        const next = Math.max(0, Math.min(questions.length - 1, index));
        activeQuestionIndex = next;

        if (currentLayout === 'FOCUS') {
          getConsoleAll('.question-card').forEach((card, cardIndex) => {
            card.classList.toggle('hidden', cardIndex !== next);
          });
          const position = getConsoleEl('#exam-focus-position');
          if (position) position.textContent = `Câu ${next + 1} / ${questions.length}`;

          const prevBtn = getConsoleEl('#exam-prev-question');
          if (prevBtn) prevBtn.disabled = next === 0;

          const nextBtn = getConsoleEl('#exam-next-question');
          if (nextBtn) {
            if (next === questions.length - 1) {
              nextBtn.className = 'rounded-xl bg-emerald-600 hover:bg-emerald-700 px-5 py-2 text-sm font-bold text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer';
              nextBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">task_alt</span><span>Nộp bài thi</span>';
            } else {
              nextBtn.className = 'rounded-xl bg-primary hover:bg-primary/90 px-4 py-2 text-sm font-semibold text-slate-50 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer';
              nextBtn.innerHTML = '<span>Câu Tiếp</span><span class="material-symbols-outlined text-[18px]">arrow_forward</span>';
            }
          }
          getConsoleEl('#questions-viewport')?.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          getConsoleEl(`#q_card_${next}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        updateMatrixHighlight(next);
      };

      const setLayout = (mode) => {
        currentLayout = mode;
        const btnFocus = getConsoleEl('#btn-mode-focus');
        const btnStandard = getConsoleEl('#btn-mode-standard');
        const focusNav = getConsoleEl('#focus-nav-container');
        const standardSubmit = getConsoleEl('#standard-submit-container');

        if (mode === 'FOCUS') {
          btnFocus?.classList.add('bg-white', 'dark:bg-slate-700', 'text-primary', 'shadow-2xs', 'font-bold');
          btnFocus?.classList.remove('text-slate-400');
          btnStandard?.classList.remove('bg-white', 'dark:bg-slate-700', 'text-primary', 'shadow-2xs', 'font-bold');
          btnStandard?.classList.add('text-slate-400');
          focusNav?.classList.remove('hidden');
          standardSubmit?.classList.add('hidden');
          showQuestion(activeQuestionIndex);
        } else {
          btnStandard?.classList.add('bg-white', 'dark:bg-slate-700', 'text-primary', 'shadow-2xs', 'font-bold');
          btnStandard?.classList.remove('text-slate-400');
          btnFocus?.classList.remove('bg-white', 'dark:bg-slate-700', 'text-primary', 'shadow-2xs', 'font-bold');
          btnFocus?.classList.add('text-slate-400');
          focusNav?.classList.add('hidden');
          standardSubmit?.classList.remove('hidden');
          getConsoleAll('.question-card').forEach(card => card.classList.remove('hidden'));
          showQuestion(activeQuestionIndex);
        }
      };

      // Robust delegated click handler on console root
      getConsoleRoot().addEventListener('click', async (e) => {
        const navBtn = e.target.closest('[data-navigate-question]');
        if (navBtn) {
          e.preventDefault();
          showQuestion(Number(navBtn.dataset.navigateQuestion));
          return;
        }
        const prevBtn = e.target.closest('#exam-prev-question');
        if (prevBtn) {
          e.preventDefault();
          showQuestion(activeQuestionIndex - 1);
          return;
        }
        const nextBtn = e.target.closest('#exam-next-question');
        if (nextBtn) {
          e.preventDefault();
          if (activeQuestionIndex === questions.length - 1) {
            handleSubmit(false);
          } else {
            showQuestion(activeQuestionIndex + 1);
          }
          return;
        }
        const submitStd = e.target.closest('#exam-submit-standard-btn');
        if (submitStd) {
          e.preventDefault();
          handleSubmit(false);
          return;
        }
        const modeFocus = e.target.closest('#btn-mode-focus');
        if (modeFocus) {
          e.preventDefault();
          setLayout('FOCUS');
          return;
        }
        const modeStd = e.target.closest('#btn-mode-standard');
        if (modeStd) {
          e.preventDefault();
          setLayout('STANDARD');
          return;
        }
        const flagBtn = e.target.closest('.flag-question-btn');
        if (flagBtn) {
          e.preventDefault();
          const idx = parseInt(flagBtn.dataset.qIndex, 10);
          const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
          const badge = matrixBtn?.querySelector('.flag-icon-badge');
          if (flaggedQuestions.has(idx)) {
            flaggedQuestions.delete(idx);
            flagBtn.classList.remove('bg-amber-50', 'text-amber-600', 'border-amber-300');
            badge?.classList.add('hidden');
          } else {
            flaggedQuestions.add(idx);
            flagBtn.classList.add('bg-amber-50', 'text-amber-600', 'border-amber-300');
            badge?.classList.remove('hidden');
          }
          return;
        }
        if (e.target.closest('#exam-fullscreen-btn')) {
          e.preventDefault();
          if (document.fullscreenElement) {
            try {
              if (document.exitFullscreen) await document.exitFullscreen();
            } catch (_e) {}
          } else {
            await requestFullscreenSafe();
          }
          return;
        }
        if (e.target.closest('#lockdown-return-fullscreen-btn')) {
          e.preventDefault();
          await requestFullscreenSafe();
          return;
        }
      });

      if (questions.length) showQuestion(0);

      const requestFullscreenSafe = async () => {
        try {
          if (document.documentElement.requestFullscreen) {
            await document.documentElement.requestFullscreen();
          } else if (getConsoleRoot().requestFullscreen) {
            await getConsoleRoot().requestFullscreen();
          }
          getConsoleEl('#exam-fullscreen-lockdown-overlay')?.classList.add('hidden');
        } catch (_error) {
          UI.showToast('Trình duyệt không thể mở toàn màn hình. Hãy tối đa hóa cửa sổ trình duyệt.', 'warning');
        }
      };

      // Browser proctoring & focus monitoring (Default 100% active)
      const focusEventStarts = new Map();
      const antiCheat = new ExamAntiCheatManager({
        watchFullscreen: true,
        onEvent: event => {
          if (event.phase === 'START') {
            focusEventStarts.set(event.event_id, ApiClient.recordAttemptFocusEvent(attemptId, event)
              .then(() => true)
              .catch(() => false));
          } else {
            const started = focusEventStarts.get(event.event_id) || Promise.resolve();
            started.then(ok => ok && ApiClient.recordAttemptFocusEvent(attemptId, event))
              .catch(() => {});
            focusEventStarts.delete(event.event_id);
          }
        },
        onObservation: (count, type, durationSeconds, totalAwaySeconds) => {
          const proctoringIndicator = getConsoleEl('#exam-proctoring-indicator');
          const proctoringText = getConsoleEl('#exam-proctoring-text');
          const proctoringDot = getConsoleEl('#exam-proctoring-dot');
          const lockdownViolations = getConsoleEl('#lockdown-violation-count');
          const lockdownAway = getConsoleEl('#lockdown-away-seconds');
          if (proctoringIndicator && proctoringText) {
            proctoringText.textContent = `Rời màn hình: ${count} lần (${totalAwaySeconds}s)`;
            proctoringIndicator.className = 'px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-800 text-[11px] font-mono font-semibold flex items-center gap-1.5 transition-all';
            if (proctoringDot) proctoringDot.className = 'w-2 h-2 rounded-full bg-amber-500 animate-ping';
          }
          if (lockdownViolations) lockdownViolations.textContent = String(count);
          if (lockdownAway) lockdownAway.textContent = `${totalAwaySeconds}s`;

          if (durationSeconds > 0) {
            UI.showToast(`Đã quay lại bài thi. Thời gian vắng mặt: ${durationSeconds} giây (Tổng cộng: ${totalAwaySeconds}s - ${count} vi phạm).`, 'warning');
          }
        },
        onFullscreenExit: () => {
          getConsoleEl('#exam-fullscreen-lockdown-overlay')?.classList.remove('hidden');
        },
        onFullscreenEnter: () => {
          getConsoleEl('#exam-fullscreen-lockdown-overlay')?.classList.add('hidden');
        }
      });

      antiCheat.start();

      // Check initial fullscreen state
      if (!document.fullscreenElement) {
        getConsoleEl('#exam-fullscreen-lockdown-overlay')?.classList.remove('hidden');
      }

      // Answer selection auto-save handler
      container.querySelectorAll('input[type="radio"], input[type="checkbox"], select.interactive-slot-select').forEach(input => {
        input.onchange = async () => {
          const card = input.closest('.question-card');
          if (!card) return;
          const idx = parseInt(card.dataset.qIndex, 10);
          const qid = card.dataset.qid;
          const selectedChoiceIds = Array.from(card.querySelectorAll(
            'input[type="radio"]:checked, input[type="checkbox"]:checked, select.interactive-slot-select'
          )).map(choice => choice.value).filter(Boolean);
          const grouped = parseGroupedAttemptChoices(questions[idx]);
          const hasCompleteGroupedAnswer = !grouped || (
            card.querySelectorAll('select.interactive-slot-select').length === grouped.groups.length
            && Array.from(card.querySelectorAll('select.interactive-slot-select')).every(select => Boolean(select.value))
          );

          if (selectedChoiceIds.length && hasCompleteGroupedAnswer) answeredQuestions.add(idx);
          else answeredQuestions.delete(idx);
          const indicatorCount = document.getElementById('answered-count-indicator');
          if (indicatorCount) {
            indicatorCount.textContent = `${answeredQuestions.size}/${questions.length} câu`;
          }

          // Update Matrix cell style
          const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
          if (matrixBtn) {
            matrixBtn.classList.toggle('bg-primary', selectedChoiceIds.length > 0);
            matrixBtn.classList.toggle('text-white', selectedChoiceIds.length > 0);
            matrixBtn.classList.toggle('border-primary', selectedChoiceIds.length > 0);
          }

          try {
            await saveAnswerInOrder(qid, {
              selected_choice_keys: selectedChoiceIds,
              selected_choice_ids: selectedChoiceIds
            }, leaseToken);
          } catch (e) {
            UI.showToast(e.message || 'Lỗi lưu đáp án.', 'error');
          }
        };
      });

      container.querySelectorAll('.interactive-token').forEach(tokenButton => {
        tokenButton.addEventListener('dragstart', event => {
          event.dataTransfer?.setData('text/plain', tokenButton.dataset.token || '');
          if (event.dataTransfer) event.dataTransfer.effectAllowed = 'copy';
        });
        tokenButton.addEventListener('click', () => {
          const card = tokenButton.closest('.question-card');
          const selects = Array.from(card?.querySelectorAll('select.interactive-slot-select') || []);
          const target = selects.find(select => !select.value) || selects[0];
          if (!target) return;
          const tokenText = (tokenButton.dataset.token || '').toLocaleLowerCase();
          const option = Array.from(target.options).find(item =>
            (item.dataset.answerText || '').toLocaleLowerCase() === tokenText
          );
          if (option) {
            target.value = option.value;
            target.dispatchEvent(new Event('change', { bubbles: true }));
          }
        });
      });

      container.querySelectorAll('.interactive-drop-slot').forEach(dropSlot => {
        dropSlot.addEventListener('dragover', event => {
          event.preventDefault();
          dropSlot.classList.add('ring-2', 'ring-indigo-400');
          if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy';
        });
        dropSlot.addEventListener('dragleave', event => {
          if (!dropSlot.contains(event.relatedTarget)) {
            dropSlot.classList.remove('ring-2', 'ring-indigo-400');
          }
        });
        dropSlot.addEventListener('drop', event => {
          event.preventDefault();
          dropSlot.classList.remove('ring-2', 'ring-indigo-400');
          const tokenText = (event.dataTransfer?.getData('text/plain') || '').toLocaleLowerCase();
          const select = dropSlot.querySelector('select.interactive-slot-select');
          if (!tokenText || !select) return;
          const option = Array.from(select.options).find(item =>
            (item.dataset.answerText || '').toLocaleLowerCase() === tokenText
          );
          if (option) {
            select.value = option.value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
          }
        });
      });

      const textDebounceTimers = new Map();

      const saveShortAnswer = async (input) => {
        const card = input.closest('.question-card');
        if (!card) return;
        const idx = Number(input.dataset.qIndex);
        const qid = card.dataset.qid;
        const answerText = input.value.trim();
        if (answerText) answeredQuestions.add(idx);
        else answeredQuestions.delete(idx);

        const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
        if (matrixBtn) {
          matrixBtn.classList.toggle('bg-primary', Boolean(answerText));
          matrixBtn.classList.toggle('text-white', Boolean(answerText));
          matrixBtn.classList.toggle('border-primary', Boolean(answerText));
        }
        const indicatorCount = document.getElementById('answered-count-indicator');
        if (indicatorCount) indicatorCount.textContent = `${answeredQuestions.size}/${questions.length} câu`;

        try {
          await saveAnswerInOrder(qid, { answer_text: answerText });
        } catch (err) {
          UI.showToast(err.message || 'Không thể lưu câu trả lời.', 'error');
        }
      };

      container.querySelectorAll('.assessment-short-answer').forEach(input => {
        input.addEventListener('input', () => {
          clearTimeout(textDebounceTimers.get(input));
          textDebounceTimers.set(input, setTimeout(() => saveShortAnswer(input), 1200));
        });
        input.addEventListener('change', () => {
          clearTimeout(textDebounceTimers.get(input));
          saveShortAnswer(input);
        });
        input.addEventListener('blur', () => {
          clearTimeout(textDebounceTimers.get(input));
          saveShortAnswer(input);
        });
      });

      const saveFillBlank = async (card) => {
        if (!card) return;
        const idx = Number(card.dataset.qIndex);
        const qid = card.dataset.qid;
        const inputs = Array.from(card.querySelectorAll('.assessment-fill-blank'));
        const values = inputs.map(blank => blank.value.trim());
        const answerText = values.join('|||');
        if (values.length && values.every(Boolean)) answeredQuestions.add(idx);
        else answeredQuestions.delete(idx);

        const matrixBtn = document.getElementById(`matrix_btn_${idx}`);
        if (matrixBtn) {
          const complete = values.length > 0 && values.every(Boolean);
          matrixBtn.classList.toggle('bg-primary', complete);
          matrixBtn.classList.toggle('text-white', complete);
          matrixBtn.classList.toggle('border-primary', complete);
        }
        const indicatorCount = document.getElementById('answered-count-indicator');
        if (indicatorCount) indicatorCount.textContent = `${answeredQuestions.size}/${questions.length} câu`;

        try {
          await saveAnswerInOrder(qid, { answer_text: answerText });
        } catch (error) {
          UI.showToast(error.message || 'Không thể lưu câu trả lời điền khuyết.', 'error');
        }
      };

      container.querySelectorAll('.assessment-fill-blank').forEach(input => {
        const card = input.closest('.question-card');
        input.addEventListener('input', () => {
          if (!card) return;
          clearTimeout(textDebounceTimers.get(card));
          textDebounceTimers.set(card, setTimeout(() => saveFillBlank(card), 1200));
        });
        input.addEventListener('change', () => {
          if (!card) return;
          clearTimeout(textDebounceTimers.get(card));
          saveFillBlank(card);
        });
        input.addEventListener('blur', () => {
          if (!card) return;
          clearTimeout(textDebounceTimers.get(card));
          saveFillBlank(card);
        });
      });

      const flushAllUnsavedInputs = async () => {
        if (document.activeElement && typeof document.activeElement.blur === 'function') {
          try { document.activeElement.blur(); } catch (_e) {}
        }
        const promises = [];
        container.querySelectorAll('.assessment-short-answer').forEach(input => {
          if (textDebounceTimers.has(input)) {
            clearTimeout(textDebounceTimers.get(input));
            textDebounceTimers.delete(input);
            promises.push(saveShortAnswer(input));
          }
        });
        container.querySelectorAll('.question-card').forEach(card => {
          if (textDebounceTimers.has(card)) {
            clearTimeout(textDebounceTimers.get(card));
            textDebounceTimers.delete(card);
            promises.push(saveFillBlank(card));
          }
        });
        if (promises.length > 0) {
          await Promise.allSettled(promises);
        }
      };

      const handleExamBeforeUnload = (e) => {
        if (textDebounceTimers.size > 0 || pendingAnswerSaves.size > 0) {
          container.querySelectorAll('.assessment-short-answer').forEach(input => {
            if (textDebounceTimers.has(input)) {
              clearTimeout(textDebounceTimers.get(input));
              textDebounceTimers.delete(input);
              saveShortAnswer(input);
            }
          });
          container.querySelectorAll('.question-card').forEach(card => {
            if (textDebounceTimers.has(card)) {
              clearTimeout(textDebounceTimers.get(card));
              textDebounceTimers.delete(card);
              saveFillBlank(card);
            }
          });
          e.preventDefault();
          e.returnValue = '';
        }
      };
      window.addEventListener('beforeunload', handleExamBeforeUnload);

      // Submit exam action with mandatory verification checkbox modal
      const submitBtn = document.getElementById('exam-submit-btn');

      const showSubmitConfirmModal = async (unansweredCount, totalCount) => {
        return new Promise((resolve) => {
          const modalId = 'modal-submit-exam-confirm';
          document.getElementById(modalId)?.remove();

          const answeredCount = totalCount - unansweredCount;
          const modal = document.createElement('div');
          modal.id = modalId;
          modal.className = 'fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150';
          modal.innerHTML = `
            <div class="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200 select-none">
              <div class="flex items-center gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div class="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-primary flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-2xl">assignment_turned_in</span>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900 dark:text-white">Xác nhận nộp bài thi</h3>
                  <p class="text-xs text-slate-500">Kiểm tra lại trạng thái bài làm trước khi nộp</p>
                </div>
              </div>

              <div class="space-y-3 text-xs">
                <div class="grid grid-cols-2 gap-2">
                  <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span class="text-slate-500 block mb-1">Đã trả lời:</span>
                    <span class="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">${answeredCount} / ${totalCount} câu</span>
                  </div>
                  <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span class="text-slate-500 block mb-1">Chưa trả lời:</span>
                    <span class="text-lg font-bold font-mono ${unansweredCount > 0 ? 'text-amber-600 dark:text-amber-400 font-extrabold' : 'text-slate-400'}">${unansweredCount} câu</span>
                  </div>
                </div>

                ${unansweredCount > 0 ? `
                  <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 flex items-start gap-2">
                    <span class="material-symbols-outlined text-[18px] text-amber-600 shrink-0 mt-0.5">warning</span>
                    <span>Bạn vẫn còn <strong>${unansweredCount}</strong> câu chưa trả lời. Những câu chưa trả lời sẽ được tính là 0 điểm.</span>
                  </div>
                ` : `
                  <div class="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 flex items-start gap-2">
                    <span class="material-symbols-outlined text-[18px] text-emerald-600 shrink-0 mt-0.5">check_circle</span>
                    <span>Bạn đã hoàn thành đủ <strong>${totalCount}/${totalCount}</strong> câu hỏi của bài thi.</span>
                  </div>
                `}

                <label class="flex items-start gap-3 p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/60 dark:bg-indigo-950/30 cursor-pointer select-none transition-colors hover:bg-indigo-50 dark:hover:bg-indigo-950/50">
                  <input type="checkbox" id="exam-confirm-checkbox" class="mt-0.5 rounded text-primary focus:ring-primary w-4 h-4 cursor-pointer" />
                  <span class="font-semibold text-slate-800 dark:text-slate-200 leading-snug">
                    Tôi xác nhận đã đọc kĩ nội dung bài làm và muốn nộp bài thi ngay bây giờ.
                  </span>
                </label>
              </div>

              <div class="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button type="button" id="exam-confirm-cancel-btn" class="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors">
                  Kiểm tra lại
                </button>
                <button type="button" id="exam-confirm-submit-btn" disabled class="px-5 py-2 rounded-xl bg-rose-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[16px]">send</span>
                  <span>Xác nhận nộp bài</span>
                </button>
              </div>
            </div>
          `;

          document.body.appendChild(modal);

          const checkbox = modal.querySelector('#exam-confirm-checkbox');
          const submitBtnModal = modal.querySelector('#exam-confirm-submit-btn');
          const cancelBtnModal = modal.querySelector('#exam-confirm-cancel-btn');

          checkbox.addEventListener('change', () => {
            submitBtnModal.disabled = !checkbox.checked;
          });

          cancelBtnModal.addEventListener('click', () => {
            modal.remove();
            resolve(false);
          });

          submitBtnModal.addEventListener('click', () => {
            if (checkbox.checked) {
              modal.remove();
              resolve(true);
            }
          });
        });
      };

      const handleSubmit = async (forced = false) => {
        if (!forced) {
          const unanswered = questions.length - answeredQuestions.size;
          const confirmed = await showSubmitConfirmModal(unanswered, questions.length);
          if (!confirmed) return;
        }

        // Flush all active/focused text inputs that were in debounce timers
        await flushAllUnsavedInputs();

        if (pendingAnswerSaves.size > 0) {
          await Promise.allSettled(Array.from(pendingAnswerSaves));
        }
        if (!forced && failedAnswerSaves.size > 0) {
          const failedCount = await StudentView.retryFailedAnswerSaves(
            failedAnswerSaves, answerPayloads, saveAnswerInOrder
          );
          if (failedCount > 0) {
            const submitSavedOnly = await UI.confirm(
              'Một số đáp án chưa lưu được',
              `${failedCount} câu trả lời vẫn chưa được lưu sau khi thử lại. Nếu nộp ngay, chỉ các đáp án đã lưu trên máy chủ được tính điểm.`,
              'Nộp Các Đáp Án Đã Lưu',
              'Tiếp Tục Làm Bài',
              true
            );
            if (!submitSavedOnly) return;
          }
        }

        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang nộp bài...';
        }

        try {
          await ApiClient.submitAttempt(attemptId, leaseToken, StudentView.getSubmissionKey(attemptId));
          antiCheat.stop();
          window.removeEventListener('beforeunload', handleExamBeforeUnload);
          if (document.fullscreenElement && document.exitFullscreen) {
            try { await document.exitFullscreen(); } catch (_e) {}
          }
          UI.showToast('Nộp bài thi thành công! Đang chuyển đến bảng kết quả.', 'success');
          window.location.hash = `#/student/assessments/results?id=${attemptId}`;
        } catch (err) {
          try {
            const result = await ApiClient.getAttemptResult(attemptId);
            if (['SUBMITTED', 'PENDING_GRADING', 'GRADED'].includes(result?.status)) {
              antiCheat.stop();
              window.removeEventListener('beforeunload', handleExamBeforeUnload);
              if (document.fullscreenElement && document.exitFullscreen) {
                try { await document.exitFullscreen(); } catch (_e) {}
              }
              window.location.hash = `#/student/assessments/results?id=${attemptId}`;
              return;
            }
          } catch (_lookupError) {
            // Preserve the original submit error for the learner.
          }
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
          window.removeEventListener('beforeunload', handleExamBeforeUnload);
          return;
        }
        if (remainingSeconds > 0) {
          remainingSeconds--;
          if (timerEl) timerEl.textContent = UI.formatDuration(remainingSeconds);
        } else {
          clearInterval(examInterval);
          antiCheat.stop();
          window.removeEventListener('beforeunload', handleExamBeforeUnload);
          UI.showToast('Đã hết giờ làm bài! Hệ thống tự động nộp bài thi.', 'warning');
          handleSubmit(true);
        }
      }, 1000);

    } catch (err) {
      const isCompletedErr = err?.message?.includes('GRADED') || err?.message?.includes('SUBMITTED') || err?.message?.includes('not in progress');
      if (isCompletedErr) {
        window.location.hash = `#/student/assessments/results?id=${attemptId}`;
        return;
      }
      container.innerHTML = `
        <div class="p-8 max-w-xl mx-auto my-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4 animate-fade-in font-sans">
          <div class="w-14 h-14 mx-auto rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <span class="material-symbols-outlined text-3xl">assignment_turned_in</span>
          </div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Thông báo Khảo thí Học vụ</h2>
          <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            ${UI.escapeHtml(err.message || 'Không thể tải bàn thi hoặc ca làm bài này đã hoàn tất.')}
          </p>
          <div class="flex items-center justify-center gap-3 pt-2">
            <a href="#/student/assessments/results?id=${encodeURIComponent(attemptId)}" class="c-btn c-btn-primary text-xs">
              <span class="material-symbols-outlined text-[16px]">visibility</span>
              <span>Xem kết quả bài thi</span>
            </a>
            <a href="#/student/assessments" class="c-btn c-btn-secondary text-xs">
              <span>Danh sách bài thi</span>
            </a>
          </div>
        </div>
      `;
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
      <div class="py-6 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in">
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

      const scoreState = StudentView.getAttemptScoreState(data);
      if (!scoreState.released) {
        container.innerHTML = `
          <div class="p-8 text-center max-w-xl mx-auto space-y-3">
            <span class="material-symbols-outlined text-4xl text-amber-500">hourglass_top</span>
            <h1 class="text-xl font-bold text-slate-900 dark:text-white">Điểm chưa được công bố</h1>
            <p class="text-sm text-slate-600 dark:text-slate-300">Bài làm đã được ghi nhận. Kết quả sẽ hiển thị sau khi hoàn tất chấm và công bố.</p>
            <button type="button" class="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-sm font-semibold" onclick="window.history.back()">Quay lại</button>
          </div>
        `;
        return;
      }

      const { totalScore, maxPoints, passingScore, isPassed, scorePct } = scoreState;
      const questions = data.questions || [];
      const answerVisibilityPolicy = String(data.answer_visibility_policy || '').toUpperCase();
      const hiddenAnswerPolicies = new Set(['NEVER', 'AFTER_CLOSE', 'AFTER_ALL_ATTEMPTS']);
      const assessType = (data.assessment_type || data.type || 'QUIZ').toUpperCase();
      const isFormalExam = assessType === 'MIDTERM' || assessType === 'FINAL_EXAM' || maxPoints >= 10;
      const courseCode = data.assessment_code || 'PWD301';
      const courseId = data.course_id || '';
      const resultPdfHref = `/student/attempt/${encodeURIComponent(attemptId)}/result.pdf`;
      const assessmentTitle = data.assessment_title || (isFormalExam ? 'Kết quả Đánh giá Midterm (Chính thức)' : 'Kết quả Khảo thí Trắc nghiệm');
      const instructorName = data.instructor_name || 'Chưa có dữ liệu';
      const durationMinutes = Number(data.duration_minutes);
      const durationLabel = Number.isFinite(durationMinutes) && durationMinutes > 0
        ? `${durationMinutes} phút`
        : 'Chưa có dữ liệu';
      const signatureHash = String(data.signature_hash || '').trim();
      const correctQuestions = questions.filter(q => q.is_correct);
      const correctCount = correctQuestions.length;
      const wrongCount = questions.length - correctCount;
      // Candidate Profile extraction
      const studentName = data.candidate_name || currentUser?.full_name || currentUser?.display_name || currentUser?.name || 'Học viên';
      const studentEmail = data.candidate_email || currentUser?.email || '';
      const nameParts = studentName.trim().split(/\s+/);
      const studentInitials = nameParts.length >= 2
        ? (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
        : studentName.slice(0, 2).toUpperCase();

      const letterGrade = data.letter_grade || 'Chưa có dữ liệu';
      const gradeDescriptor = data.grade_descriptor || 'Chưa có dữ liệu';
      const percentileText = data.percentile_text || 'Chưa có dữ liệu';

      container.innerHTML = `
        <div class="space-y-6 max-w-[1720px] w-full mx-auto py-4 sm:py-6 lg:py-8 px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
          
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

            <div class="flex items-center gap-2 sm:gap-3 shrink-0"></div>
          </header>

          <!-- Grade Revision Notice Banner (Mode B / Formal Exam) -->
          ${data.appeal && ['PENDING', 'APPROVED', 'REJECTED'].includes(data.appeal.status) ? `
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
                <span>Xem lịch sử duyệt điểm</span>
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
                    ${studentEmail ? `
                      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5 truncate">
                        <span class="material-symbols-outlined text-[14px] text-slate-400 shrink-0">mail</span>
                        <span class="truncate">${UI.escapeHtml(studentEmail)}</span>
                      </p>
                    ` : ''}
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
                        <span class="text-3xl font-black text-slate-900 dark:text-white tracking-tight">${Number.isFinite(scorePct) ? scorePct.toFixed(1) : '0.0'}</span>
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
                      <span class="font-semibold text-slate-800 dark:text-slate-200 font-mono">${durationLabel}</span>
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

                  <!-- Action Buttons: Completed -> Appeal -> Export PDF -->
                  <div class="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <a
                      href="${courseId ? `#/student/courses/detail?id=${courseId}` : '#/student/dashboard'}"
                      class="w-full py-2.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-xs transition cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px]">check_circle</span>
                      <span>Đã hoàn tất</span>
                    </a>
                    <button
                      type="button"
                      id="request-appeal-btn"
                      class="w-full py-2 px-3 bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px]">gavel</span>
                      <span>Phúc khảo</span>
                    </button>
                    <a
                      id="download-student-result-pdf-btn"
                      href="${UI.escapeHtml(resultPdfHref)}"
                      download
                      class="w-full py-2 px-3 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/60 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 font-semibold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-2xs transition cursor-pointer"
                    >
                      <span class="material-symbols-outlined text-[16px] text-slate-500">download</span>
                      <span>Xuất bảng điểm (PDF)</span>
                    </a>
                  </div>

                  <!-- Digital Signature -->
                  <div class="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                    <span>Chữ ký số:</span>
                    ${signatureHash
                      ? `<span class="font-mono text-slate-500 dark:text-slate-400 text-[10px]" title="SHA-256 Server UTC Integrity Verified">${UI.escapeHtml(signatureHash)}</span>`
                      : '<span class="text-slate-500 dark:text-slate-400 text-[10px]">Chưa có dữ liệu</span>'}
                  </div>
                </div>
              </div>

              <!-- Official Result Policy Card (Replaces Attempts Pagination) -->
              <div class="bg-indigo-50/70 dark:bg-indigo-950/40 rounded-2xl border border-indigo-100 dark:border-indigo-900/60 p-4 text-xs space-y-1.5 shadow-2xs">
                <div class="flex items-center gap-1.5 font-bold text-indigo-900 dark:text-indigo-300">
                  <span class="material-symbols-outlined text-[17px] text-indigo-600 dark:text-indigo-400">verified</span>
                  <span>Kết quả Khảo thí Chính thức</span>
                </div>
                <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                  Kết quả hiển thị được ghi nhận theo quy chế: <strong class="text-slate-900 dark:text-white">${data.scoring_policy === 'LATEST' ? 'Lượt làm bài thi gần nhất' : 'Lượt thi đạt điểm cao nhất'}</strong> theo quy định khảo thí của Giảng viên.
                </p>
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
                  const questionType = String(q.question_type || '').toUpperCase();
                  const isEssay = questionType === 'ESSAY';
                  const isManualEssay = isEssay && q.grading_status === 'MANUAL_GRADED';
                  const pointsAssigned = Number(q.points_assigned ?? 0);
                  const rawAwardedPts = Number(q.awarded_points);
                  const awardedPts = Number.isFinite(rawAwardedPts)
                    ? rawAwardedPts
                    : (isCorrect ? 1.0 : 0.0);
                  const manualEssayIsFullCredit = isManualEssay && awardedPts >= pointsAssigned;
                  const essayAnswerIsHidden = isEssay
                    && !String(q.student_answer_text || q.answer_text || '').trim()
                    && hiddenAnswerPolicies.has(answerVisibilityPolicy);
                  const chosenAns = String(isEssay
                    ? (q.student_answer_text || q.answer_text || (essayAnswerIsHidden
                      ? 'Câu trả lời đang được ẩn theo chính sách khảo thí'
                      : 'Không trả lời'))
                    : (q.chosen_answer || 'Không trả lời'));
                  const correctAns = String(q.correct_answer || '');
                  const choices = q.choices || [];
                  const cardTone = isManualEssay
                    ? (manualEssayIsFullCredit ? 'border-emerald-200 dark:border-emerald-800' : 'border-amber-200 dark:border-amber-800')
                    : (isCorrect ? 'border-slate-200 dark:border-slate-800' : 'border-rose-200 dark:border-rose-900/50');
                  const scoreTone = isManualEssay
                    ? (manualEssayIsFullCredit ? 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800' : 'text-amber-700 bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800')
                    : (isCorrect ? 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800' : 'text-rose-700 bg-rose-50 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800');
                  const scoreLabel = isManualEssay ? `${awardedPts} / ${pointsAssigned} đ` : (isCorrect ? `+${awardedPts} đ` : '0 đ');
                  const answerLabel = isEssay ? 'Câu trả lời của bạn' : 'Đáp án bạn chọn';
                  const evaluationTone = isManualEssay
                    ? (manualEssayIsFullCredit ? 'text-emerald-600' : 'text-amber-600')
                    : (isCorrect ? 'text-emerald-600' : 'text-rose-600');
                  const evaluationLabel = isManualEssay
                    ? `${manualEssayIsFullCredit ? '✓ Đạt điểm tối đa' : '• Đã chấm thủ công'} (${awardedPts}/${pointsAssigned} đ)`
                    : (isCorrect ? '✓ Trả lời chính xác' : '✗ Trả lời chưa chính xác');

                  return `
                    <article
                      class="question-item bg-white dark:bg-slate-900 rounded-2xl border ${cardTone} p-5 sm:p-6 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-colors space-y-4"
                      data-correct="${isCorrect}"
                    >
                      <!-- Question Header -->
                      <div class="flex items-start justify-between gap-4">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-extrabold text-slate-900 dark:text-white font-mono">Câu ${idx + 1}</span>
                          <span class="text-xs font-bold px-2 py-0.5 rounded-lg border ${scoreTone}">
                            ${scoreLabel}
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
                        ${UI.escapeHtml(String(q.content || q.stem || '')
                          .replace(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):[^\]]+\]\]/gi, '')
                          .replace(/!\[.*?\]\([^\)]+\)/gi, '')
                          .replace(/<img[^>]*>/gi, '')
                          .trim())}
                      </p>

                      <!-- Question Illustration in Review -->
                      ${(() => {
                        const rawContent = String(q.content || q.stem || '');
                        const markerIds = [...rawContent.matchAll(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):([^\]]+)\]\]/gi)].map(m => m[1]);
                        const mdMatches = [...rawContent.matchAll(/!\[.*?\]\((https?:\/\/[^\s\)]+|\/[^\s\)]+|data:image\/[^\s\)]+)\)/gi)].map(m => m[1]);
                        const htmlImgMatches = [...rawContent.matchAll(/<img[^>]+src=["']([^"']+)["']/gi)].map(m => m[1]);
                        const resList = (Array.isArray(q.resources) && q.resources.length > 0)
                          ? q.resources.map(r => r.download_url || r.url || (r.asset_id ? `/student/files/${r.asset_id}/download?disposition=inline` : '')).filter(Boolean)
                          : [];
                        const idList = [
                          ...(q.image_asset_ids || []),
                          ...(q.image_asset_id ? [q.image_asset_id] : []),
                          ...markerIds
                        ].filter(Boolean);
                        idList.forEach(aid => {
                          const url = `/student/files/${aid}/download?disposition=inline`;
                          if (!resList.includes(url)) resList.push(url);
                        });
                        mdMatches.forEach(u => { if (!resList.includes(u)) resList.push(u); });
                        htmlImgMatches.forEach(u => { if (!resList.includes(u)) resList.push(u); });
                        if (q.image_url && !resList.includes(q.image_url)) resList.push(q.image_url);
                        if (q.media_url && !resList.includes(q.media_url)) resList.push(q.media_url);

                        if (!resList.length) return '';
                        return `
                          <div class="flex items-center gap-3 flex-wrap my-3">
                            ${resList.map(imgUrl => `
                              <img src="${UI.escapeHtml(imgUrl)}" alt="Hình ảnh câu hỏi ${idx + 1}" loading="lazy" class="max-h-72 max-w-full rounded-lg border border-slate-200 dark:border-slate-700 object-contain bg-white dark:bg-slate-900" onerror="this.onerror=null; this.style.display='none'" />
                            `).join('')}
                          </div>
                        `;
                      })()}

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
                                <span class="flex-1">${UI.escapeHtml(UI.cleanChoiceText(c.content || c.text || ''))}</span>
                                ${isTheCorrect ? '<span class="text-emerald-600 font-bold">✓</span>' : (isSelected && !isCorrect ? '<span class="text-rose-600 font-bold">✗</span>' : '')}
                              </div>
                            `;
                          }).join('')}
                        </div>
                      ` : `
                        <div class="space-y-1.5 text-xs text-slate-600 dark:text-slate-400 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40">
                          <div>${answerLabel}: <strong class="${isManualEssay ? (manualEssayIsFullCredit ? 'text-emerald-600 font-bold' : 'text-amber-600 font-bold') : (isCorrect ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold')}">${UI.escapeHtml(UI.cleanChoiceText(chosenAns))}</strong></div>
                          ${correctAns ? `<div class="text-emerald-600">Đáp án chính xác: <strong>${UI.escapeHtml(UI.cleanChoiceText(correctAns))}</strong></div>` : ''}
                        </div>
                      `}

                      ${isManualEssay && q.feedback ? `
                        <div class="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200">
                          <span class="font-bold">Nhận xét chấm:</span> ${UI.escapeHtml(q.feedback)}
                        </div>
                      ` : ''}

                      <!-- Answer Evaluation & Indicator Bar -->
                      <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                        <div class="flex items-center gap-2">
                          <span class="font-bold ${evaluationTone}">
                            ${evaluationLabel}
                          </span>
                          ${correctAns ? `<span class="text-slate-400">• Đáp án chuẩn: <strong class="text-emerald-600">${UI.escapeHtml(correctAns)}</strong></span>` : ''}
                        </div>

                        <!-- MC indicators [A][B][C][D] style matching mockup -->
                        ${!isEssay ? `<div class="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-xs font-semibold">
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
                        </div>` : ''}
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
        let appealData;
        let historyData;
        try {
          [appealData, historyData] = await Promise.all([
            ApiClient.getAttemptAppeal(attemptId),
            ApiClient.getAttemptGradeHistory(attemptId),
          ]);
        } catch (error) {
          UI.openDrawer({
            side: 'right',
            title: 'Không thể tải lịch sử kết quả',
            width: 'max-w-xl',
            bodyHtml: `
              <div class="p-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                <p>Hệ thống chưa tải được dữ liệu phúc khảo và lịch sử điểm. Vui lòng thử lại.</p>
                <p class="text-xs text-rose-600">${UI.escapeHtml(error?.message || 'Lỗi kết nối')}</p>
                <button type="button" id="retry-audit-drawer-btn" class="px-4 py-2 rounded-xl bg-primary text-white font-semibold">Thử lại</button>
              </div>
            `,
          });
          const retryButton = document.getElementById('retry-audit-drawer-btn');
          if (retryButton) retryButton.onclick = openAuditDrawer;
          return;
        }

        const appeal = appealData?.appeal;
        const historyItems = [
          ...(historyData?.overall_history || []).map(item => ({ ...item, scope: 'Tổng điểm' })),
          ...(historyData?.question_history || []).map(item => ({ ...item, scope: 'Câu hỏi' })),
        ].sort((left, right) => String(left.created_at || '').localeCompare(String(right.created_at || '')));
        const appealHtml = appeal
          ? `<div class="p-3 rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/30 space-y-1">
              <strong>Phúc khảo: ${UI.escapeHtml(appeal.status || 'PENDING')}</strong>
              <div>Lý do: ${UI.escapeHtml(appeal.reason || 'Không có')}</div>
              <div>Ghi chú: ${UI.escapeHtml(appeal.note || 'Không có')}</div>
              <div class="text-xs text-slate-500">${UI.formatDateTime(appeal.created_at)}</div>
            </div>`
          : '<p class="text-sm text-slate-500">Chưa có đơn phúc khảo được lưu.</p>';
        const historyHtml = historyItems.length
          ? historyItems.map(item => `
              <li class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                <div class="flex justify-between gap-3 font-semibold"><span>${UI.escapeHtml(item.scope)}</span><span class="text-xs text-slate-500">${UI.formatDateTime(item.created_at)}</span></div>
                <div class="text-xs">${item.old_score ?? item.old_points ?? '—'} → ${item.new_score ?? item.new_points ?? '—'}</div>
                <div class="text-xs text-slate-500">${UI.escapeHtml(item.reason || item.reason_code || 'Không có lý do')}</div>
              </li>
            `).join('')
          : '<li class="text-sm text-slate-500">Chưa có bản ghi điều chỉnh điểm được lưu.</li>';

        UI.openDrawer({
          side: 'right',
          title: 'Chi tiết phúc khảo',
          width: 'max-w-xl',
          bodyHtml: `<div class="space-y-5 text-xs text-slate-700 dark:text-slate-300">
            <section><h4 class="font-bold text-sm mb-2">Trạng thái phúc khảo</h4>${appealHtml}</section>
            <section><h4 class="font-bold text-sm mb-2">Lịch sử điều chỉnh điểm đã lưu</h4><ol class="space-y-2">${historyHtml}</ol></section>
          </div>`,
          footerHtml: '<div class="flex justify-end w-full"><button type="button" class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 font-semibold" onclick="UI.closeDrawer()">Đóng</button></div>',
        });
        return;
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
      } catch (error) {
        UI.showToast('Không thể tải trạng thái phúc khảo. Bạn có thể thử lại.', 'warning');
      }

      // Handle Appeal Button Click
      const appealBtn = document.getElementById('request-appeal-btn');
      if (appealBtn) {
        appealBtn.onclick = async () => {
          let currentAppeal = null;
          try {
            currentAppeal = await ApiClient.getAttemptAppeal(attemptId);
          } catch (error) {
            if (error?.status !== 404) {
              UI.showToast('Không thể kiểm tra trạng thái phúc khảo. Vui lòng thử lại.', 'error');
              return;
            }
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
            `Tổng điểm bài thi: ${totalScore}/${maxPoints} điểm (Tỷ lệ: ${Number.isFinite(scorePct) ? (scorePct * 10).toFixed(1) : '0.0'}%).\n` +
            `Quy đổi hệ 10.0: ${Number.isFinite(scorePct) ? scorePct.toFixed(1) : '0.0'} / 10.0.\n` +
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
          const courseId = data.course_id || data.assessment?.course_id || null;
          if (window.FloatingAITutor) {
            FloatingAITutor.openWithQuestion(prompt, courseId);
          } else {
            UI.showToast('Trợ lý AI đang sẵn sàng, vui lòng thử lại sau giây lát...', 'info');
          }
        };
      });

    } catch (err) {
      container.innerHTML = `
        <div class="p-8 max-w-xl mx-auto my-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4 animate-fade-in font-sans">
          <div class="w-14 h-14 mx-auto rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <span class="material-symbols-outlined text-3xl">assignment</span>
          </div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Thông báo Kết quả Khảo thí</h2>
          <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            ${UI.escapeHtml(err.message || 'Hệ thống đang chuẩn bị kết quả hoặc bài thi chưa hoàn tất chấm điểm.')}
          </p>
          <div class="flex items-center justify-center gap-3 pt-2">
            <button type="button" id="retry-student-result-btn" class="c-btn c-btn-primary text-xs cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">refresh</span>
              <span>Thử lại</span>
            </button>
            <button type="button" class="c-btn c-btn-secondary text-xs cursor-pointer" onclick="window.history.back()">
              <span>Quay lại</span>
            </button>
          </div>
        </div>
      `;
      document.getElementById('retry-student-result-btn')?.addEventListener(
        'click',
        () => StudentView.renderAttemptResults(container, attemptId),
      );
    }
  }

  // =========================================================================
  // 8b. Student Assessments Master List View
  // =========================================================================
  // 9. Assessments Suite: Assessment List Grouped by Course
  // =========================================================================
  static async renderAssessmentsList(container) {
    container.innerHTML = `
      <div class="py-4 sm:py-6 lg:py-8 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in font-sans">
        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[28px]">quiz</span>
              <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Danh sách Bài kiểm tra</h1>
            </div>
            <p class="text-xs sm:text-sm text-slate-500 mt-1">Theo dõi, tham gia làm bài và đối chiếu điểm số các đợt khảo thí theo từng học phần bạn đang học.</p>
          </div>
          <div id="student-assessments-stats" class="hidden sm:flex items-center gap-3"></div>
        </div>

        <div id="student-assessments-grid" class="space-y-6">
          <div class="text-center py-20 text-slate-400">
            <span class="inline-block animate-spin text-3xl mb-3">⏳</span>
            <p class="text-sm font-medium">Đang tải danh sách bài kiểm tra...</p>
          </div>
        </div>
      </div>
    `;

    try {
      const data = await ApiClient.getStudentAssessments();
      const items = data.assessments || data.items || [];
      const grid = document.getElementById('student-assessments-grid');
      const statsBox = document.getElementById('student-assessments-stats');

      if (items.length === 0) {
        grid.innerHTML = `
          <div class="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 text-slate-400 text-sm space-y-2">
            <span class="material-symbols-outlined text-5xl text-slate-300 dark:text-slate-600">assignment_turned_in</span>
            <p class="font-bold text-base text-slate-700 dark:text-slate-300">Không có bài kiểm tra nào</p>
            <p class="text-xs text-slate-400 max-w-md mx-auto">Hiện tại các học phần bạn tham gia chưa có đợt khảo thí nào. Khi giảng viên mở bài thi, bài sẽ hiển thị phân loại theo môn tại đây.</p>
          </div>
        `;
        return;
      }

      // 1. Phân loại 3 danh sách độc lập:
      const activeList = [];
      const upcomingList = [];
      const completedList = [];

      items.forEach(a => {
        if (a.is_closed || a.is_attempt_limit_reached) {
          completedList.push(a);
        } else if (!a.is_open) {
          upcomingList.push(a);
        } else {
          activeList.push(a);
        }
      });

      // 2. Helper nhóm theo Môn học
      const groupByCourse = (assessmentList) => {
        const grouped = {};
        assessmentList.forEach(a => {
          const cCode = a.course_code || 'CRS';
          const cTitle = a.course_title || `Học phần ${cCode}`;
          const key = a.course_id ? String(a.course_id) : cCode;
          if (!grouped[key]) {
            grouped[key] = {
              course_id: a.course_id || '',
              course_code: cCode,
              course_title: cTitle,
              assessments: []
            };
          }
          grouped[key].assessments.push(a);
        });
        return Object.values(grouped);
      };

      // Đếm tổng số môn học duy nhất trên toàn bộ bài thi
      const uniqueCourses = new Set(items.map(a => a.course_id || a.course_code || 'CRS'));
      const completedExamsCount = items.filter(a => a.is_attempt_limit_reached || a.attempts_count > 0).length;

      // Render top overview stats badges
      if (statsBox) {
        statsBox.innerHTML = `
          <div class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-200 dark:border-slate-700">
            <span class="material-symbols-outlined text-[16px] text-primary">school</span>
            <span><strong>${uniqueCourses.size}</strong> học phần</span>
          </div>
          <div class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-200 dark:border-slate-700">
            <span class="material-symbols-outlined text-[16px] text-emerald-600">play_circle</span>
            <span><strong>${activeList.length}</strong> bài đang mở</span>
          </div>
          <div class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-200 dark:border-slate-700">
            <span class="material-symbols-outlined text-[16px] text-teal-600">fact_check</span>
            <span><strong>${completedExamsCount}</strong>/${items.length} bài đã nộp</span>
          </div>
        `;
      }

      // Helper render thẻ bài thi cá nhân (Đảm bảo CHỈ CÓ 1 STATUS BADGE DUY NHẤT)
      const renderAssessmentCard = (a) => {
        const assessType = (a.assessment_type || a.type || 'QUIZ').toUpperCase();
        let typeLabel = 'Trắc nghiệm củng cố';
        let typeClass = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
        if (assessType === 'MIDTERM') {
          typeLabel = 'Khảo thí Giữa kỳ';
          typeClass = 'bg-amber-50 text-amber-800 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
        } else if (assessType === 'FINAL_EXAM') {
          typeLabel = 'Khảo thí Cuối kỳ';
          typeClass = 'bg-purple-50 text-purple-800 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800';
        }

        // BẤT BIẾN DUY NHẤT 01 STATUS BADGE
        let singleStatusBadge = '';
        if (a.is_closed) {
          singleStatusBadge = `
            <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800 flex items-center gap-1.5 shadow-2xs">
              <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
              <span>Đã kết thúc</span>
            </span>
          `;
        } else if (a.is_attempt_limit_reached) {
          singleStatusBadge = `
            <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-md bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800 flex items-center gap-1.5 shadow-2xs">
              <span class="material-symbols-outlined text-[13px]">check_circle</span>
              <span>Đã hoàn thành</span>
            </span>
          `;
        } else if (a.is_waiting_room_open && !a.is_open) {
          singleStatusBadge = `
            <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800 flex items-center gap-1.5 shadow-2xs">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
              <span>Phòng chờ đang mở</span>
            </span>
          `;
        } else if (!a.is_open) {
          singleStatusBadge = `
            <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800 flex items-center gap-1.5 shadow-2xs">
              <span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
              <span>Sắp mở</span>
            </span>
          `;
        } else {
          singleStatusBadge = `
            <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800 flex items-center gap-1.5 shadow-2xs">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Đang diễn ra</span>
            </span>
          `;
        }

        // Định dạng khung thời gian thi
        let timingText = '';
        if (a.open_at || a.close_at) {
          const formatTime = (iso) => {
            if (!iso) return '';
            const d = new Date(iso);
            const pad = (n) => String(n).padStart(2, '0');
            return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
          };
          timingText = `<span class="flex items-center gap-1 text-slate-500"><span class="material-symbols-outlined text-[15px] text-slate-400">calendar_clock</span><span>Khung thi: <strong>${a.open_at ? formatTime(a.open_at) : 'Mở tự do'} → ${a.close_at ? formatTime(a.close_at) : 'Không hạn'}</strong></span></span>`;
        }

        // Nút hành động
        let actionHtml = '';
        if (a.is_closed) {
          actionHtml = `
            ${a.attempts_count > 0 ? `
              <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1 font-bold">
                <span class="material-symbols-outlined text-[15px]">fact_check</span>
                <span>Xem kết quả</span>
              </a>
            ` : ''}
            <button type="button" disabled class="c-btn c-btn-secondary c-btn-sm opacity-50 cursor-not-allowed text-rose-600 dark:text-rose-400">
              <span class="material-symbols-outlined text-[15px]">lock</span>
              <span>Đã đóng ca thi</span>
            </button>
          `;
        } else if (a.is_attempt_limit_reached) {
          actionHtml = `
            <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1.5 font-bold shadow-2xs">
              <span class="material-symbols-outlined text-[16px] text-teal-600">fact_check</span>
              <span>Xem kết quả chính thức</span>
            </a>
          `;
        } else if (a.is_waiting_room_open && !a.is_open) {
          actionHtml = `
            ${a.attempts_count > 0 ? `
              <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1 font-bold" title="Xem kết quả bài làm trước">
                <span class="material-symbols-outlined text-[15px]">fact_check</span>
                <span>Xem kết quả</span>
              </a>
            ` : ''}
            <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1.5 font-bold shadow-2xs bg-indigo-600 hover:bg-indigo-700 text-white">
              <span class="material-symbols-outlined text-[16px]">meeting_room</span>
              <span>Vào phòng chờ</span>
            </a>
          `;
        } else if (!a.is_open) {
          actionHtml = `
            <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1.5 font-bold text-slate-600 dark:text-slate-300 hover:text-primary" title="Xem thông tin và đếm ngược phòng chờ">
              <span class="material-symbols-outlined text-[16px] text-purple-600">lock_clock</span>
              <span>Chờ mở phòng (trước 30p)</span>
            </a>
          `;
        } else {
          actionHtml = `
            ${a.attempts_count > 0 ? `
              <a href="#/student/assessments/results?id=${a.attempt_id || ''}" class="c-btn c-btn-secondary c-btn-sm flex items-center gap-1 font-bold" title="Xem kết quả bài làm trước">
                <span class="material-symbols-outlined text-[15px]">fact_check</span>
                <span>Xem kết quả</span>
              </a>
              <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1.5 font-bold shadow-2xs">
                <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                <span>Làm bài tiếp</span>
              </a>
            ` : `
              <a href="#/student/assessments/waiting-room?id=${a.assessment_id || a.id}" class="c-btn c-btn-primary c-btn-sm flex items-center gap-1.5 font-bold shadow-2xs">
                <span class="material-symbols-outlined text-[16px]">play_arrow</span>
                <span>Vào thi</span>
              </a>
            `}
          `;
        }

        return `
          <div class="p-5 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="space-y-1.5 min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-[11px] font-bold px-2 py-0.5 rounded-md ${typeClass}">
                  ${typeLabel}
                </span>
                ${singleStatusBadge}
                ${a.attempts_count > 0 ? `
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[13px] text-emerald-600">done</span>
                    <span>Đã thi ${a.attempts_count}${a.attempt_limit ? `/${a.attempt_limit}` : ''} lượt</span>
                  </span>
                ` : ''}
              </div>

              <h3 class="font-bold text-sm sm:text-base text-slate-900 dark:text-white leading-snug">
                ${UI.escapeHtml(a.title)}
              </h3>

              <div class="flex items-center gap-3 text-xs text-slate-500 pt-0.5 flex-wrap">
                <span class="flex items-center gap-1">
                  <span class="material-symbols-outlined text-[15px] text-slate-400">timer</span>
                  <span>Thời lượng: <strong>${a.time_limit_minutes || 45} phút</strong></span>
                </span>
                <span>•</span>
                <span class="flex items-center gap-1">
                  <span class="material-symbols-outlined text-[15px] text-slate-400">grade</span>
                  <span>Điểm tối đa: <strong>${a.max_points || 10}đ</strong></span>
                </span>
                ${timingText ? `<span>•</span>${timingText}` : ''}
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2 shrink-0 pt-2 sm:pt-0">
              ${actionHtml}
            </div>
          </div>
        `;
      };

      // Helper render một Nhóm Lớn (Cấp 1) có Accordion và danh sách Môn học (Cấp 2)
      const renderSectionBlock = (secConfig) => {
        const { secId, title, subtitle, icon, iconBg, iconColor, iconBorder, badgeClass, list, defaultExpanded } = secConfig;
        const courseGroups = groupByCourse(list);

        let contentInnerHtml = '';
        if (courseGroups.length === 0) {
          contentInnerHtml = `
            <div class="p-6 text-center text-xs text-slate-400 bg-white/50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
              Hiện không có bài kiểm tra nào trong phân mục này.
            </div>
          `;
        } else {
          contentInnerHtml = courseGroups.map((group, gIdx) => {
            const courseAccordionId = `course-acc-${secId}-${gIdx}`;
            return `
              <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
                <!-- Course Header (Cấp 2 - Click để thu gọn/mở rộng môn này) -->
                <div class="px-4 py-3 bg-slate-50/80 dark:bg-slate-800/60 hover:bg-slate-100/70 dark:hover:bg-slate-800 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 transition-colors cursor-pointer select-none" data-course-toggle="${courseAccordionId}">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="material-symbols-outlined text-[18px] text-slate-400">menu_book</span>
                    <span class="font-mono font-bold text-xs px-2 py-0.5 rounded bg-primary-subtle text-primary border border-primary/20">
                      ${UI.escapeHtml(group.course_code)}
                    </span>
                    <h3 class="font-bold text-xs sm:text-sm text-slate-800 dark:text-slate-100 truncate">
                      ${UI.escapeHtml(group.course_title)}
                    </h3>
                  </div>

                  <div class="flex items-center gap-2.5 shrink-0" onclick="event.stopPropagation()">
                    <span class="text-[11px] font-semibold text-slate-500 bg-white dark:bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-700 shadow-2xs">
                      ${group.assessments.length} bài
                    </span>
                    ${group.course_id ? `
                      <a href="#/student/courses/detail?id=${group.course_id}" class="text-xs font-bold text-primary hover:underline flex items-center gap-0.5" title="Đến trang học phần">
                        <span>Vào môn</span>
                        <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
                      </a>
                    ` : ''}
                    <button type="button" class="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded transition-colors" data-course-btn="${courseAccordionId}" aria-label="Thu gọn hoặc mở rộng môn">
                      <span class="material-symbols-outlined text-[20px] transition-transform duration-200" data-course-arrow="${courseAccordionId}">
                        expand_less
                      </span>
                    </button>
                  </div>
                </div>

                <!-- Course Assessments List -->
                <div id="${courseAccordionId}" class="divide-y divide-slate-100 dark:divide-slate-800">
                  ${group.assessments.map(a => renderAssessmentCard(a)).join('')}
                </div>
              </div>
            `;
          }).join('');
        }

        return `
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden" id="section-card-${secId}">
            <!-- Section Header (Cấp 1 - Click để thu gọn/mở rộng toàn bộ nhóm) -->
            <button type="button" class="w-full px-5 py-4 bg-slate-50/90 dark:bg-slate-800/80 hover:bg-slate-100/80 dark:hover:bg-slate-800 flex items-center justify-between gap-4 transition-colors select-none text-left" data-sec-toggle="${secId}" aria-expanded="${defaultExpanded}">
              <div class="flex items-center gap-3 min-w-0">
                <span class="w-10 h-10 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center shrink-0 border ${iconBorder}">
                  <span class="material-symbols-outlined text-[22px]">${icon}</span>
                </span>
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <h2 class="font-black text-base sm:text-lg text-slate-900 dark:text-white tracking-tight">${title}</h2>
                    <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${badgeClass}">
                      ${list.length} bài
                    </span>
                  </div>
                  <p class="text-xs text-slate-500 mt-0.5 truncate">${subtitle}</p>
                </div>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <span class="material-symbols-outlined text-slate-400 transition-transform duration-200 text-[24px]" data-sec-arrow="${secId}">
                  ${defaultExpanded ? 'expand_less' : 'expand_more'}
                </span>
              </div>
            </button>

            <!-- Section Body (Chứa các Môn học) -->
            <div id="sec-body-${secId}" class="${defaultExpanded ? '' : 'hidden'} p-4 sm:p-5 space-y-4 bg-slate-50/30 dark:bg-slate-950/20 border-t border-slate-100 dark:border-slate-800">
              ${contentInnerHtml}
            </div>
          </div>
        `;
      };

      // 3. Render 3 phân vùng theo thứ tự ưu tiên chuẩn xác:
      grid.innerHTML = [
        // Phân vùng 1: Đang diễn ra (Mặc định MỞ)
        renderSectionBlock({
          secId: 'active',
          title: 'Bài kiểm tra đang diễn ra',
          subtitle: 'Các bài kiểm tra đang mở ca thi và bạn có thể vào làm bài ngay.',
          icon: 'play_circle',
          iconBg: 'bg-emerald-50 dark:bg-emerald-950/80',
          iconColor: 'text-emerald-600 dark:text-emerald-400',
          iconBorder: 'border-emerald-200 dark:border-emerald-800',
          badgeClass: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300',
          list: activeList,
          defaultExpanded: true
        }),
        // Phân vùng 2: Sắp mở (Mặc định MỞ)
        renderSectionBlock({
          secId: 'upcoming',
          title: 'Bài kiểm tra sắp mở',
          subtitle: 'Các ca thi sắp mở trong thời gian tới. Phòng chờ sẽ mở trước 30 phút để kiểm tra thiết bị.',
          icon: 'pending_actions',
          iconBg: 'bg-indigo-50 dark:bg-indigo-950/80',
          iconColor: 'text-indigo-600 dark:text-indigo-400',
          iconBorder: 'border-indigo-200 dark:border-indigo-800',
          badgeClass: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300',
          list: upcomingList,
          defaultExpanded: true
        }),
        // Phân vùng 3: Đã thi & Hết lượt thi lại / Quá hạn thi (Mặc định THU GỌN)
        renderSectionBlock({
          secId: 'completed',
          title: 'Bài kiểm tra đã kết thúc & Quá hạn',
          subtitle: 'Các bài kiểm tra đã nộp hết số lượt làm bài hoặc ca thi đã chính thức khóa.',
          icon: 'history_toggle_off',
          iconBg: 'bg-slate-100 dark:bg-slate-800',
          iconColor: 'text-slate-600 dark:text-slate-400',
          iconBorder: 'border-slate-200 dark:border-slate-700',
          badgeClass: 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
          list: completedList,
          defaultExpanded: false
        })
      ].join('');

      // 4. Wiring tương tác Accordion 2 Tầng:
      // Tầng 1: Toggle Phân vùng Lớn
      grid.querySelectorAll('[data-sec-toggle]').forEach(secBtn => {
        secBtn.addEventListener('click', () => {
          const sId = secBtn.dataset.secToggle;
          const bodyEl = document.getElementById(`sec-body-${sId}`);
          const arrowEl = grid.querySelector(`[data-sec-arrow="${sId}"]`);
          if (!bodyEl) return;
          const isHidden = bodyEl.classList.contains('hidden');
          if (isHidden) {
            bodyEl.classList.remove('hidden');
            if (arrowEl) arrowEl.textContent = 'expand_less';
            secBtn.setAttribute('aria-expanded', 'true');
          } else {
            bodyEl.classList.add('hidden');
            if (arrowEl) arrowEl.textContent = 'expand_more';
            secBtn.setAttribute('aria-expanded', 'false');
          }
        });
      });

      // Tầng 2: Toggle Từng Môn học trong phân vùng
      grid.querySelectorAll('[data-course-toggle]').forEach(courseHeader => {
        courseHeader.addEventListener('click', () => {
          const targetId = courseHeader.dataset.courseToggle;
          const courseBody = document.getElementById(targetId);
          const arrowEl = grid.querySelector(`[data-course-arrow="${targetId}"]`);
          if (!courseBody) return;
          const isHidden = courseBody.classList.contains('hidden');
          if (isHidden) {
            courseBody.classList.remove('hidden');
            if (arrowEl) arrowEl.textContent = 'expand_less';
          } else {
            courseBody.classList.add('hidden');
            if (arrowEl) arrowEl.textContent = 'expand_more';
          }
        });
      });

    } catch (err) {
      document.getElementById('student-assessments-grid').innerHTML = `
        <div class="p-8 text-center text-rose-500 bg-rose-50 dark:bg-rose-950/20 rounded-2xl border border-rose-200 dark:border-rose-900">
          Lỗi nạp bài kiểm tra: ${UI.escapeHtml(err.message)}
        </div>
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
                Bạch tuộc trợ lí AI
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
              <p class="font-bold text-slate-900 dark:text-white">Xin chào! Tôi là Bạch tuộc trợ lí AI.</p>
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
    let chatGeneration = 0;

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
        chatGeneration++;
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
        <span>Bạch tuộc trợ lí AI đang phân tích kiến thức...</span>
      `;
      chatContainer.appendChild(typing);
      chatContainer.scrollTop = chatContainer.scrollHeight;

      const currentGen = ++chatGeneration;
      const courseId = courseSelect?.value || null;
      try {
        const res = await ApiClient.sendAIChat(text, conversationId, courseId);
        typing.remove();

        if (currentGen !== chatGeneration) {
          return; // Stale request discarded (SYNC-035)
        }

        if (res && res.conversation_id) {
          conversationId = res.conversation_id;
        }

        const reply = res.reply || res.response || (res.data && res.data.reply) || 'Tôi đã tiếp nhận câu hỏi của bạn.';
        appendAIBubble(reply);
      } catch (err) {
        typing.remove();
        if (currentGen !== chatGeneration) return;
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
        chatGeneration++;
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
            UI.refreshCurrentRoute(() => StudentView.renderBecomeInstructor(container));
          } catch (e) {
            UI.showToast(e.message || 'Không thể hủy đơn.', 'error');
          }
        };
        return;
      }

      // State for files
      let cvSelectedFile = null;
      let evidenceSelectedFiles = [];

      // Render fresh application form with Warm Editorial single-column layout
      box.innerHTML = `
        <div class="space-y-1.5 pb-4 border-b border-slate-200/80 dark:border-slate-800">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-md bg-primary/10 text-primary text-[11px] font-bold tracking-wide uppercase">Cổng Học Viên</span>
            <span class="text-xs text-slate-400">•</span>
            <span class="text-xs text-slate-500">Gia nhập đội ngũ Giảng viên</span>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">Đăng Ký Trở Thành Giảng Viên</h1>
          <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Chia sẻ kiến thức chuyên môn, kỹ năng thực chiến và đồng hành cùng cộng đồng học viên PWD301.</p>
        </div>

        <form id="become-instructor-form" class="space-y-7 pt-2 max-w-2xl" enctype="multipart/form-data">
          
          <!-- Section 1: Personal Information -->
          <div class="space-y-4">
            <div class="flex items-center gap-2 pb-1.5 border-b border-slate-200/80 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">person</span>
              <span>1. Thông tin cá nhân & Định danh</span>
            </div>

            <!-- Full Name -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Họ và tên đầy đủ <span class="text-rose-500 font-bold ml-0.5">*</span>
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
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Ngày sinh <span class="text-rose-500 font-bold ml-0.5">*</span>
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
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Số điện thoại liên hệ <span class="text-rose-500 font-bold ml-0.5">*</span>
              </label>
              <input
                type="tel"
                name="phone_number"
                required
                placeholder="VD: 0912 345 678"
                class="c-input"
              />
            </div>

            <!-- Contact Email -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Email liên hệ <span class="text-rose-500 font-bold ml-0.5">*</span>
              </label>
              <input
                type="email"
                name="contact_email"
                required
                placeholder="VD: nguyen.vana@domain.com"
                class="c-input"
              />
            </div>

            <!-- Citizen ID (CCCD) -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Số CCCD / CMND / Hộ chiếu <span class="text-rose-500 font-bold ml-0.5">*</span>
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
            <div class="flex items-center gap-2 pb-1.5 border-b border-slate-200/80 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">school</span>
              <span>2. Chuyên môn & Lĩnh vực đào tạo</span>
            </div>

            <!-- Specialization -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Chuyên môn / Lĩnh vực giảng dạy chính <span class="text-rose-500 font-bold ml-0.5">*</span>
              </label>
              <input
                type="text"
                name="specialization"
                required
                placeholder="VD: Lập trình Python chuyên sâu, UI/UX Product Design, Cloud Architecture..."
                class="c-input"
              />
            </div>

            <!-- Statement of Purpose / Bio -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Giới thiệu bản thân & Định hướng giảng dạy <span class="text-rose-500 font-bold ml-0.5">*</span>
              </label>
              <textarea
                name="statement"
                rows="4"
                required
                placeholder="Tóm tắt kinh nghiệm thực tế, dự án tiêu biểu và nội dung kiến thức bạn dự định chia sẻ tới học viên..."
                class="c-input resize-none"
              ></textarea>
            </div>

            <!-- Portfolio / GitHub / Website URL -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Đường dẫn Portfolio / GitHub / Website <span class="text-[11px] text-slate-400 font-normal lowercase">(không bắt buộc)</span>
              </label>
              <input
                type="url"
                name="portfolio_url"
                placeholder="https://github.com/... hoặc https://behance.net/..."
                class="c-input"
              />
            </div>

            <div class="space-y-1.5">
              <label for="certificate-drive-url" class="block text-xs font-bold text-slate-700 dark:text-slate-300">
                Link chứng chỉ, bằng cấp trên Google Drive <span class="font-normal text-slate-400">(Không bắt buộc)</span>
              </label>
              <input
                id="certificate-drive-url"
                type="url"
                name="certificate_drive_url"
                maxlength="512"
                placeholder="https://drive.google.com/file/d/..."
                class="c-input"
              />
              <p class="text-xs text-slate-500">Chia sẻ quyền xem cho người có liên kết để hội đồng có thể đối chiếu.</p>
            </div>

            <!-- Institution Name (Optional) -->
            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Đơn vị công tác / Tổ chức <span class="text-[11px] text-slate-400 font-normal lowercase">(không bắt buộc)</span>
              </label>
              <input
                type="text"
                name="institution_name"
                placeholder="Để trống nếu hoạt động tự do / Freelancer"
                class="c-input"
              />
            </div>
          </div>

          <!-- Section 3: Evidence & Verification Uploads -->
          <div class="space-y-4">
            <div class="flex items-center gap-2 pb-1.5 border-b border-slate-200/80 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              <span class="material-symbols-outlined text-[18px] text-primary">upload_file</span>
              <span>3. Hồ sơ năng lực & Minh chứng</span>
            </div>
            <p class="text-xs text-slate-500">
              Tải lên hồ sơ để Quản trị viên đối soát năng lực. Tệp CV chỉ chấp nhận 1 file PDF; tệp minh chứng tối đa 4 file (PDF, hình ảnh) dưới 2MB/tệp.
            </p>

            <!-- CV / Portfolio File Dropzone -->
            <div class="space-y-2">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Tệp CV hoặc Portfolio tóm tắt năng lực <span class="text-rose-500 font-bold ml-0.5">*</span>
              </label>
              <div id="cv-dropzone" class="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-primary dark:hover:border-primary rounded-2xl p-5 text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30">
                <input type="file" id="cv_file_input" name="cv_file" accept=".pdf,application/pdf" class="hidden" />
                <div id="cv-empty-view" class="space-y-1 pointer-events-none">
                  <span class="material-symbols-outlined text-[32px] text-primary">cloud_upload</span>
                  <div class="text-xs font-bold text-slate-700 dark:text-slate-200">Bấm hoặc kéo thả tệp CV / Portfolio vào đây</div>
                  <div class="text-[11px] text-slate-400">Chỉ chấp nhận duy nhất 1 tệp định dạng PDF</div>
                </div>
                <div id="cv-selected-view" class="hidden flex items-center justify-between p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-left">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="material-symbols-outlined text-[20px] text-primary">description</span>
                    <div class="min-w-0">
                      <div id="cv-file-name" class="font-bold text-xs text-slate-900 dark:text-white truncate">cv.pdf</div>
                      <div id="cv-file-size" class="text-[10px] text-slate-500 font-mono">0 KB</div>
                    </div>
                  </div>
                  <button type="button" id="cv-remove-btn" class="p-1 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors" title="Bỏ chọn tệp">
                    <span class="material-symbols-outlined text-[18px]">close</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Additional Evidence Files Dropzone -->
            <div class="space-y-2">
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Chứng chỉ, bằng cấp hoặc minh chứng bổ sung <span class="text-[11px] text-slate-400 font-normal lowercase">(Tối đa 4 tệp PDF/PNG/JPG, dưới 2MB/tệp)</span>
              </label>
              <div id="evidence-dropzone" class="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-primary dark:hover:border-primary rounded-2xl p-4 text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30">
                <input type="file" id="evidence_files_input" name="evidence_files" multiple accept=".pdf,image/png,image/jpeg,image/jpg" class="hidden" />
                <div class="flex items-center justify-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-200 pointer-events-none">
                  <span class="material-symbols-outlined text-[20px] text-slate-400">attach_file</span>
                  <span>Bấm hoặc kéo thả để chọn thêm tệp minh chứng</span>
                </div>
                <div class="text-[11px] text-slate-400 mt-0.5 pointer-events-none">Tối đa 4 tệp: Bằng tốt nghiệp, chứng chỉ nghề (PDF, PNG, JPG dưới 2MB)</div>
              </div>
              <div id="evidence-files-list" class="space-y-1.5 empty:hidden pt-1"></div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="pt-6 border-t border-slate-200/80 dark:border-slate-800 flex justify-end">
            <button
              type="submit"
              id="submit-nomination-btn"
              class="px-6 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer"
            >
              <span>Gửi Hồ Sơ Xét Duyệt</span>
              <span class="material-symbols-outlined text-[16px]">send</span>
            </button>
          </div>
        </form>
      `;

      // Wire CV Dropzone
      const cvDropzone = document.getElementById('cv-dropzone');
      const cvInput = document.getElementById('cv_file_input');
      const cvEmptyView = document.getElementById('cv-empty-view');
      const cvSelectedView = document.getElementById('cv-selected-view');
      const cvFileName = document.getElementById('cv-file-name');
      const cvFileSize = document.getElementById('cv-file-size');
      const cvRemoveBtn = document.getElementById('cv-remove-btn');

      const setCvFile = (file) => {
        if (!file) {
          cvSelectedFile = null;
          if (cvInput) cvInput.value = '';
          cvEmptyView?.classList.remove('hidden');
          cvSelectedView?.classList.add('hidden');
          return;
        }
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'pdf' && file.type !== 'application/pdf') {
          UI.showToast('Tệp CV hoặc Portfolio chỉ chấp nhận định dạng PDF.', 'warning');
          if (cvInput) cvInput.value = '';
          return;
        }
        cvSelectedFile = file;
        if (cvFileName) cvFileName.textContent = file.name;
        if (cvFileSize) cvFileSize.textContent = UI.formatBytes(file.size);
        cvEmptyView?.classList.add('hidden');
        cvSelectedView?.classList.remove('hidden');
      };

      cvDropzone?.addEventListener('click', (e) => {
        if (e.target.closest('#cv-remove-btn')) return;
        cvInput?.click();
      });

      cvInput?.addEventListener('change', () => {
        if (cvInput.files && cvInput.files[0]) {
          setCvFile(cvInput.files[0]);
        }
      });

      cvRemoveBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        setCvFile(null);
      });

      cvDropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        cvDropzone.classList.add('border-primary', 'bg-primary/5');
      });
      cvDropzone?.addEventListener('dragleave', () => {
        cvDropzone.classList.remove('border-primary', 'bg-primary/5');
      });
      cvDropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        cvDropzone.classList.remove('border-primary', 'bg-primary/5');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          setCvFile(e.dataTransfer.files[0]);
        }
      });

      // Wire Evidence Dropzone
      const evDropzone = document.getElementById('evidence-dropzone');
      const evInput = document.getElementById('evidence_files_input');
      const evList = document.getElementById('evidence-files-list');

      const handleAddEvidenceFiles = (incomingFiles) => {
        if (!incomingFiles || incomingFiles.length === 0) return;
        const allowedExts = ['pdf', 'png', 'jpg', 'jpeg'];
        const maxBytes = 2 * 1024 * 1024; // 2MB
        let count = evidenceSelectedFiles.length;

        for (let i = 0; i < incomingFiles.length; i++) {
          const f = incomingFiles[i];
          const ext = f.name.split('.').pop().toLowerCase();
          if (!allowedExts.includes(ext)) {
            UI.showToast(`Tệp '${f.name}' không đúng định dạng. Chỉ chấp nhận PDF, PNG, JPG.`, 'warning');
            continue;
          }
          if (f.size > maxBytes) {
            UI.showToast(`Tệp '${f.name}' (${UI.formatBytes(f.size)}) vượt quá dung lượng tối đa 2MB.`, 'warning');
            continue;
          }
          if (count >= 4) {
            UI.showToast('Bạn chỉ được đính kèm tối đa 4 tệp minh chứng bổ sung.', 'warning');
            break;
          }
          if (!evidenceSelectedFiles.some(item => item.name === f.name && item.size === f.size)) {
            evidenceSelectedFiles.push(f);
            count++;
          }
        }
        renderEvidenceList();
      };

      const renderEvidenceList = () => {
        if (!evList) return;
        if (evidenceSelectedFiles.length === 0) {
          evList.innerHTML = '';
          return;
        }
        evList.innerHTML = evidenceSelectedFiles.map((file, idx) => `
          <div class="flex items-center justify-between p-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <div class="flex items-center gap-2 min-w-0">
              <span class="material-symbols-outlined text-[16px] text-slate-400">attach_file</span>
              <span class="font-medium text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(file.name)}</span>
              <span class="text-[10px] text-slate-400 font-mono">(${UI.formatBytes(file.size)})</span>
            </div>
            <button type="button" data-idx="${idx}" class="remove-ev-btn p-1 rounded text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors" title="Xóa tệp này">
              <span class="material-symbols-outlined text-[16px]">close</span>
            </button>
          </div>
        `).join('');

        evList.querySelectorAll('.remove-ev-btn').forEach(btn => {
          btn.onclick = (e) => {
            e.stopPropagation();
            const idx = parseInt(btn.dataset.idx, 10);
            evidenceSelectedFiles.splice(idx, 1);
            renderEvidenceList();
          };
        });
      };

      evDropzone?.addEventListener('click', () => {
        evInput?.click();
      });

      evInput?.addEventListener('change', () => {
        if (evInput.files) {
          handleAddEvidenceFiles(evInput.files);
          evInput.value = '';
        }
      });

      evDropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        evDropzone.classList.add('border-primary', 'bg-primary/5');
      });
      evDropzone?.addEventListener('dragleave', () => {
        evDropzone.classList.remove('border-primary', 'bg-primary/5');
      });
      evDropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        evDropzone.classList.remove('border-primary', 'bg-primary/5');
        if (e.dataTransfer.files) {
          handleAddEvidenceFiles(e.dataTransfer.files);
        }
      });

      // Submit Form
      document.getElementById('become-instructor-form').onsubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        const btn = document.getElementById('submit-nomination-btn');

        if (!cvSelectedFile && (!cvInput || !cvInput.files || cvInput.files.length === 0)) {
          UI.showToast('Vui lòng tải lên tệp CV hoặc Portfolio để hoàn tất đăng ký.', 'warning');
          return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang tải lên và gửi hồ sơ...';

        const formData = new FormData(form);

        // Ensure cv_file is the actual selected file
        if (cvSelectedFile) {
          formData.set('cv_file', cvSelectedFile);
        }

        // Populate evidence_files
        formData.delete('evidence_files');
        for (const f of evidenceSelectedFiles) {
          formData.append('evidence_files', f);
        }

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
          UI.refreshCurrentRoute(() => StudentView.renderBecomeInstructor(container));
        } catch (err) {
          UI.showToast(err.message || 'Lỗi gửi hồ sơ.', 'error');
          btn.disabled = false;
          btn.innerHTML = '<span>Gửi Hồ Sơ Xét Duyệt</span> <span class="material-symbols-outlined text-[16px]">send</span>';
        }
      };

    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-500">Lỗi nạp thông tin: ${UI.escapeHtml(err.message)}</div>`;
    }
  }
  // =========================================================================
  // Settings: Profile, Password Security & Notification Preferences
  // =========================================================================
  static async renderSettings(container) {
    container.innerHTML = `
      <div class="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
        <div class="p-8 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang nạp dữ liệu hồ sơ và cài đặt tài khoản...</p>
        </div>
      </div>
    `;

    try {
      const [profileRes, prefsRes] = await Promise.allSettled([
        ApiClient.getProfile(),
        ApiClient.getPreferences()
      ]);

      const profile = (profileRes.status === 'fulfilled' && profileRes.value?.profile) 
        ? profileRes.value.profile 
        : (window.app?.currentUser || {});

      let preferencesMap = { email_course: true, email_assessment: true, email_grade: true, email_marketing: false };
      if (prefsRes.status === 'fulfilled' && prefsRes.value) {
        const val = prefsRes.value;
        if (val.preferences_map && typeof val.preferences_map === 'object') {
          preferencesMap = { ...preferencesMap, ...val.preferences_map };
        } else if (Array.isArray(val.preferences)) {
          val.preferences.forEach(p => {
            const cat = (p.category || '').toLowerCase();
            const chan = (p.channel || 'EMAIL').toUpperCase();
            if (chan === 'EMAIL') {
              if (cat.includes('course')) preferencesMap.email_course = Boolean(p.enabled);
              else if (cat.includes('assessment') || cat.includes('exam')) preferencesMap.email_assessment = Boolean(p.enabled);
              else if (cat.includes('grade')) preferencesMap.email_grade = Boolean(p.enabled);
              else if (cat.includes('marketing')) preferencesMap.email_marketing = Boolean(p.enabled);
            }
          });
        } else if (typeof val.preferences === 'object') {
          preferencesMap = { ...preferencesMap, ...val.preferences };
        }
      }
      const preferences = preferencesMap;

      const userInitials = (profile.display_name || profile.email || 'U')
        .split(' ')
        .map(w => w[0])
        .join('')
        .slice(0, 2)
        .toUpperCase();
      const profileIdentity = profile.public_id || profile.user_id || profile.id;
      const generatedAvatar = StudentView.getStoredRandomAvatarUrl(profileIdentity);
      const currentAvatarUrl = generatedAvatar || profile.avatar_url;

      container.innerHTML = `
        <div class="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
          
          <!-- Page Header -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
            <div>
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[24px]">settings</span>
                <h1 class="text-xl font-bold text-slate-900 dark:text-white">Cài Đặt Tài Khoản</h1>
              </div>
              <p class="text-xs text-slate-500 mt-1">Quản lý thông tin định danh cá nhân, an toàn mật khẩu và tùy chọn nhận thông báo học vụ.</p>
            </div>
            <div class="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>${UI.escapeHtml(profile.email || '')}</span>
            </div>
          </div>

          <!-- Navigation Segmented Tabs -->
          <div class="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
            <button type="button" class="settings-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-xs" data-tab="profile">
              <span class="inline-flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">person</span>
                Hồ Sơ Cá Nhân
              </span>
            </button>
            <button type="button" class="settings-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition-all bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700" data-tab="security">
              <span class="inline-flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">lock</span>
                Bảo Mật & Mật Khẩu
              </span>
            </button>
            <button type="button" class="settings-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition-all bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700" data-tab="notifications">
              <span class="inline-flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">notifications</span>
                Tùy Chọn Thông Báo
              </span>
            </button>
          </div>

          <!-- Tab Pane 1: Profile (Hồ sơ cá nhân) -->
          <div id="settings-pane-profile" class="settings-pane space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              
              <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-6 border-b border-slate-100 dark:border-slate-800">
                <!-- Avatar Visual Box -->
                <div class="relative group shrink-0 text-center">
                  <div id="avatar-preview-box" class="w-24 h-24 rounded-2xl bg-gradient-to-tr from-primary to-indigo-600 text-white font-bold text-2xl flex items-center justify-center overflow-hidden border-2 border-white dark:border-slate-800 shadow-md">
                    ${currentAvatarUrl ? `
                      <img src="${UI.escapeHtml(currentAvatarUrl)}" alt="Avatar" class="w-full h-full object-cover" id="avatar-preview-img" onerror="this.remove();" />
                    ` : `
                      <span id="avatar-preview-initials">${userInitials}</span>
                    `}
                  </div>
                  <span class="text-[10px] text-slate-400 mt-2 block font-medium">Ảnh đại diện</span>
                </div>

                <div class="flex-1 space-y-3 w-full">
                  <div class="flex flex-wrap items-center gap-2">
                    <button type="button" id="btn-avatar-preset" class="px-3.5 py-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800 transition-colors flex items-center gap-1.5 shadow-2xs">
                      <span class="material-symbols-outlined text-[16px]">shuffle</span>
                      <span>Tạo ảnh đại diện ngẫu nhiên</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Profile Fields Form -->
              <form id="profile-settings-form" class="space-y-5">
                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
                    Họ và tên hiển thị <span class="text-rose-500">*</span>
                  </label>
                  <input type="text" id="settings-display-name" required minlength="2" maxlength="100" placeholder="Nhập họ và tên của bạn..." value="${UI.escapeHtml(profile.display_name || '')}" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white outline-none focus:border-primary transition-colors shadow-2xs" />
                  <p class="text-[11px] text-slate-400 mt-1">Tên này sẽ hiển thị trên bảng điểm, chứng nhận và diễn đàn trao đổi học thuật.</p>
                </div>

                <div>
                  <div class="flex items-center justify-between mb-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Email đăng nhập & định danh
                    </label>
                    <span class="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">Không thể sửa</span>
                  </div>
                  <input type="email" disabled value="${UI.escapeHtml(profile.email || '')}" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/60 text-xs sm:text-sm text-slate-500 dark:text-slate-400 outline-none cursor-not-allowed font-mono" />
                  <p class="text-[11px] text-slate-400 mt-1">Email là định danh bất biến phục vụ xác thực bảo mật và cấp chứng chỉ khảo thí.</p>
                </div>

                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
                    Vai trò hiện tại trong hệ thống
                  </label>
                  <div class="flex flex-wrap gap-2">
                    ${(profile.roles || ['STUDENT']).map(r => `
                      <span class="px-3 py-1 rounded-xl bg-primary-subtle text-primary border border-primary/20 text-xs font-bold flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">verified</span>
                        ${r === 'ADMIN' ? 'Quản trị viên (ADMIN)' : (r === 'INSTRUCTOR' ? 'Giảng viên (INSTRUCTOR)' : 'Sinh viên (STUDENT)')}
                      </span>
                    `).join('')}
                  </div>
                </div>

                <div class="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                  <button type="submit" id="btn-save-profile" class="px-6 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs sm:text-sm font-bold transition-all shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">save</span>
                    <span>Lưu Thay Đổi Hồ Sơ</span>
                  </button>
                </div>
              </form>

            </div>
          </div>

          <!-- Tab Pane 2: Security & Password (Bảo mật & Mật khẩu) -->
          <div id="settings-pane-security" class="settings-pane hidden space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              
              <div class="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 text-amber-900 dark:text-amber-300 text-xs space-y-1">
                <div class="font-bold flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-amber-600 text-[18px]">security</span>
                  Chính sách bảo mật mật khẩu tài khoản:
                </div>
                <p class="leading-relaxed text-amber-800/90 dark:text-amber-400/90">
                  Mật khẩu mới phải có độ dài tối thiểu 8 ký tự, bao gồm cả chữ cái và chữ số. Sau khi đổi mật khẩu, phiên đăng nhập hiện tại sẽ được bảo lưu an toàn.
                </p>
              </div>

              <form id="password-settings-form" class="space-y-5">
                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
                    Mật khẩu hiện tại <span class="text-rose-500">*</span>
                  </label>
                  <div class="relative">
                    <input type="password" id="settings-curr-password" required placeholder="Nhập mật khẩu đang sử dụng..." class="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white outline-none focus:border-primary transition-colors" />
                    <button type="button" class="toggle-pwd-visibility absolute right-3 top-2.5 z-10 cursor-pointer text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 flex items-center justify-center transition-colors" data-target="settings-curr-password" aria-label="Hiện/ẩn mật khẩu">
                      <span class="material-symbols-outlined text-[18px] pointer-events-none select-none">visibility</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
                    Mật khẩu mới <span class="text-rose-500">*</span>
                  </label>
                  <div class="relative">
                    <input type="password" id="settings-new-password" required minlength="8" placeholder="Nhập mật khẩu mới (tối thiểu 8 ký tự)..." class="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white outline-none focus:border-primary transition-colors" />
                    <button type="button" class="toggle-pwd-visibility absolute right-3 top-2.5 z-10 cursor-pointer text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 flex items-center justify-center transition-colors" data-target="settings-new-password" aria-label="Hiện/ẩn mật khẩu">
                      <span class="material-symbols-outlined text-[18px] pointer-events-none select-none">visibility</span>
                    </button>
                  </div>

                  <!-- Realtime Password Strength Checklist -->
                  <div class="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1 text-xs">
                    <div class="flex items-center gap-2 text-slate-500" id="pwd-check-len">
                      <span class="material-symbols-outlined text-[14px]">cancel</span>
                      <span>Độ dài từ 8 ký tự trở lên</span>
                    </div>
                    <div class="flex items-center gap-2 text-slate-500" id="pwd-check-letter">
                      <span class="material-symbols-outlined text-[14px]">cancel</span>
                      <span>Chứa ít nhất một chữ cái (A-Z hoặc a-z)</span>
                    </div>
                    <div class="flex items-center gap-2 text-slate-500" id="pwd-check-digit">
                      <span class="material-symbols-outlined text-[14px]">cancel</span>
                      <span>Chứa ít nhất một chữ số (0-9)</span>
                    </div>
                    <div class="flex items-center gap-2 text-slate-500" id="pwd-check-special">
                      <span class="material-symbols-outlined text-[14px]">cancel</span>
                      <span>Chứa ít nhất một ký tự đặc biệt (ví dụ !@#)</span>
                    </div>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
                    Xác nhận mật khẩu mới <span class="text-rose-500">*</span>
                  </label>
                  <div class="relative">
                    <input type="password" id="settings-conf-password" required minlength="8" placeholder="Nhập lại mật khẩu mới..." class="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs sm:text-sm text-slate-900 dark:text-white outline-none focus:border-primary transition-colors" />
                    <button type="button" class="toggle-pwd-visibility absolute right-3 top-2.5 z-10 cursor-pointer text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 flex items-center justify-center transition-colors" data-target="settings-conf-password" aria-label="Hiện/ẩn mật khẩu">
                      <span class="material-symbols-outlined text-[18px] pointer-events-none select-none">visibility</span>
                    </button>
                  </div>
                  <div id="pwd-match-feedback" class="text-[11px] font-bold mt-1 text-slate-400"></div>
                </div>

                <div class="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                  <button type="submit" id="btn-save-password" class="px-6 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs sm:text-sm font-bold transition-all shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">key</span>
                    <span>Cập Nhật Mật Khẩu</span>
                  </button>
                </div>
              </form>

            </div>
          </div>

          <!-- Tab Pane 3: Notification Preferences (Tùy chọn thông báo) -->
          <div id="settings-pane-notifications" class="settings-pane hidden space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              
              <div>
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-[18px]">mail</span>
                  Kênh nhận thông báo học vụ & sự kiện
                </h3>
                <p class="text-xs text-slate-400 mt-0.5">Tùy biến các danh mục sự kiện bạn muốn nhận qua chuông thông báo hệ thống và email liên kết.</p>
              </div>

              <div class="divide-y divide-slate-100 dark:divide-slate-800 text-xs sm:text-sm">
                
                <!-- Pref 1: Course -->
                <div class="py-4 flex items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-800 dark:text-slate-200">Thông báo tiến độ khóa học</div>
                    <div class="text-xs text-slate-400">Nhận cập nhật khi có bài giảng mới, tài liệu bổ trợ hoặc bài đăng trao đổi từ giảng viên.</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer shrink-0">
                    <input type="checkbox" id="pref-email-course" class="sr-only peer" ${preferences.email_course !== false ? 'checked' : ''}>
                    <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <!-- Pref 2: Assessment -->
                <div class="py-4 flex items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-800 dark:text-slate-200">Thông báo khảo thí & bài kiểm tra</div>
                    <div class="text-xs text-slate-400">Nhắc nhở lịch mở phòng thi, thời hạn nộp bài tập và cảnh báo đếm ngược thời gian.</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer shrink-0">
                    <input type="checkbox" id="pref-email-assessment" class="sr-only peer" ${preferences.email_assessment !== false ? 'checked' : ''}>
                    <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <!-- Pref 3: Grade -->
                <div class="py-4 flex items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-800 dark:text-slate-200">Kết quả đánh giá & Điểm số</div>
                    <div class="text-xs text-slate-400">Thông báo ngay khi bài thi hoàn tất chấm điểm tự động hoặc giảng viên trả nhận xét chi tiết.</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer shrink-0">
                    <input type="checkbox" id="pref-email-grade" class="sr-only peer" ${preferences.email_grade !== false ? 'checked' : ''}>
                    <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <!-- Pref 4: Marketing / News -->
                <div class="py-4 flex items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <div class="font-bold text-slate-800 dark:text-slate-200">Bản tin học thuật & Khóa học mới</div>
                    <div class="text-xs text-slate-400">Khám phá các khóa học gợi ý dựa trên năng lực và thông tin hội thảo công nghệ.</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer shrink-0">
                    <input type="checkbox" id="pref-email-marketing" class="sr-only peer" ${preferences.email_marketing === true ? 'checked' : ''}>
                    <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

              </div>

              <div class="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                <button type="button" id="btn-save-preferences" class="px-6 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs sm:text-sm font-bold transition-all shadow-sm flex items-center gap-2">
                  <span class="material-symbols-outlined text-[18px]">check_circle</span>
                  <span>Lưu Tùy Chọn Thông Báo</span>
                </button>
              </div>

            </div>
          </div>

        </div>
      `;

      // 1. Tab Switching Handlers
      const tabBtns = container.querySelectorAll('.settings-tab-btn');
      const panes = {
        profile: container.querySelector('#settings-pane-profile'),
        security: container.querySelector('#settings-pane-security'),
        notifications: container.querySelector('#settings-pane-notifications')
      };

      tabBtns.forEach(btn => {
        btn.onclick = () => {
          const tabKey = btn.dataset.tab;
          tabBtns.forEach(b => {
            b.className = 'settings-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition-all bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700';
          });
          btn.className = 'settings-tab-btn px-4 py-2 rounded-xl text-xs font-bold transition-all bg-primary text-white shadow-xs';

          Object.keys(panes).forEach(k => {
            if (panes[k]) {
              if (k === tabKey) panes[k].classList.remove('hidden');
              else panes[k].classList.add('hidden');
            }
          });
        };
      });

      // 2. Avatar Actions & Live Preview
      const avatarBox = container.querySelector('#avatar-preview-box');
      let generatedAvatarUrl = '';

      const btnAvatarPreset = container.querySelector('#btn-avatar-preset');
      if (btnAvatarPreset) {
        btnAvatarPreset.onclick = () => {
          const styles = ['adventurer', 'lorelei', 'fun-emoji', 'pixel-art', 'thumbs', 'bottts'];
          const randomStyle = styles[Math.floor(Math.random() * styles.length)];
          generatedAvatarUrl = StudentView.createRandomAvatarUrl(Math.random, randomStyle);
          const activeBox = document.getElementById('avatar-preview-box') || avatarBox;
          if (activeBox) {
            activeBox.innerHTML = `<img src="${UI.escapeHtml(generatedAvatarUrl)}" alt="Avatar ngẫu nhiên" class="w-full h-full object-cover" onerror="this.remove();" />`;
          }
          UI.showToast('Đã tạo ảnh đại diện xem trước. Nhấn "Lưu thay đổi" để áp dụng lên hệ thống!', 'info');
        };
      }

      // 3. Profile Save Handler
      const profileForm = container.querySelector('#profile-settings-form');
      if (profileForm) {
        profileForm.onsubmit = async (e) => {
          e.preventDefault();
          const activeForm = e.target || document.getElementById('profile-settings-form');
          const nameInput = activeForm ? (activeForm.querySelector('#settings-display-name') || document.getElementById('settings-display-name')) : document.getElementById('settings-display-name');
          const saveBtn = activeForm ? (activeForm.querySelector('#btn-save-profile') || document.getElementById('btn-save-profile')) : document.getElementById('btn-save-profile');
          const newName = nameInput ? nameInput.value.trim() : (profile.display_name || '');

          if (!newName || newName.length < 2) {
            UI.showToast('Vui lòng nhập họ và tên hiển thị hợp lệ (tối thiểu 2 ký tự).', 'warning');
            return;
          }

          if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang lưu...';
          }

          try {
            const updatePayload = {
              display_name: newName
            };
            const targetAvatarUrl = generatedAvatarUrl || currentAvatarUrl;
            if (targetAvatarUrl) {
              updatePayload.avatar_url = targetAvatarUrl;
            }
            const res = await ApiClient.updateProfile(updatePayload);
            const avatarStored = !generatedAvatarUrl
              || StudentView.storeRandomAvatarUrl(profileIdentity, generatedAvatarUrl);

            UI.showToast(
              avatarStored
                ? 'Cập nhật thông tin hồ sơ cá nhân thành công!'
                : 'Đã lưu thông tin hồ sơ cá nhân thành công!',
              'success'
            );
            const updatedProfile = res?.profile || res?.user || {};
            const resolvedAvatar = updatedProfile.avatar_url || targetAvatarUrl;
            if (window.app && window.app.currentUser) {
              window.app.currentUser.display_name = newName;
              if (resolvedAvatar) {
                window.app.currentUser.avatar_url = resolvedAvatar;
              }
            }
            try {
              const cached = JSON.parse(localStorage.getItem('pwd301_user') || '{}');
              cached.display_name = newName;
              if (resolvedAvatar) cached.avatar_url = resolvedAvatar;
              localStorage.setItem('pwd301_user', JSON.stringify(cached));
            } catch (_) {}

            // Immediately synchronize UI across the application
            if (window.app && typeof window.app.updateUserUI === 'function') {
              window.app.updateUserUI();
            }

            // Synchronize topbar user display name and initials
            const topbarNameEl = document.getElementById('topbar-user-name');
            if (topbarNameEl) topbarNameEl.textContent = newName;

          } catch (err) {
            UI.showToast(err.message || 'Lỗi cập nhật hồ sơ.', 'error');
          } finally {
            if (saveBtn) {
              saveBtn.disabled = false;
              saveBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">save</span><span>Lưu Thay Đổi Hồ Sơ</span>';
            }
          }
        };
      }

      // 4. Password Toggle & Validation
      container.querySelectorAll('.toggle-pwd-visibility').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const targetId = btn.dataset.target;
          const input = document.getElementById(targetId) || container.querySelector('#' + targetId);
          if (input) {
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) {
              icon.textContent = isPassword ? 'visibility_off' : 'visibility';
            }
          }
        });
      });

      const newPwdInput = container.querySelector('#settings-new-password');
      const confPwdInput = container.querySelector('#settings-conf-password');
      const checkLen = container.querySelector('#pwd-check-len');
      const checkLetter = container.querySelector('#pwd-check-letter');
      const checkDigit = container.querySelector('#pwd-check-digit');
      const checkSpecial = container.querySelector('#pwd-check-special');
      const matchFeedback = container.querySelector('#pwd-match-feedback');

      const validatePwdRealtime = () => {
        const val = newPwdInput ? newPwdInput.value : '';
        const confVal = confPwdInput ? confPwdInput.value : '';

        const requirements = StudentView.getPasswordRequirements(val);

        if (checkLen) {
          checkLen.className = `flex items-center gap-2 ${requirements.hasLength ? 'text-emerald-600 font-bold' : 'text-slate-400'}`;
          checkLen.querySelector('.material-symbols-outlined').textContent = requirements.hasLength ? 'check_circle' : 'cancel';
        }
        if (checkLetter) {
          checkLetter.className = `flex items-center gap-2 ${requirements.hasLetter ? 'text-emerald-600 font-bold' : 'text-slate-400'}`;
          checkLetter.querySelector('.material-symbols-outlined').textContent = requirements.hasLetter ? 'check_circle' : 'cancel';
        }
        if (checkDigit) {
          checkDigit.className = `flex items-center gap-2 ${requirements.hasDigit ? 'text-emerald-600 font-bold' : 'text-slate-400'}`;
          checkDigit.querySelector('.material-symbols-outlined').textContent = requirements.hasDigit ? 'check_circle' : 'cancel';
        }
        if (checkSpecial) {
          checkSpecial.className = `flex items-center gap-2 ${requirements.hasSpecialCharacter ? 'text-emerald-600 font-bold' : 'text-slate-400'}`;
          checkSpecial.querySelector('.material-symbols-outlined').textContent = requirements.hasSpecialCharacter ? 'check_circle' : 'cancel';
        }

        if (matchFeedback && confVal) {
          if (val === confVal) {
            matchFeedback.textContent = '✓ Mật khẩu xác nhận trùng khớp.';
            matchFeedback.className = 'text-[11px] font-bold mt-1 text-emerald-600';
          } else {
            matchFeedback.textContent = '✕ Mật khẩu xác nhận chưa khớp.';
            matchFeedback.className = 'text-[11px] font-bold mt-1 text-rose-500';
          }
        } else if (matchFeedback) {
          matchFeedback.textContent = '';
        }
      };

      if (newPwdInput) newPwdInput.oninput = validatePwdRealtime;
      if (confPwdInput) confPwdInput.oninput = validatePwdRealtime;

      // Password Submit
      const passwordForm = container.querySelector('#password-settings-form');
      if (passwordForm) {
        passwordForm.onsubmit = async (e) => {
          e.preventDefault();
          const currInput = document.getElementById('settings-curr-password') || container.querySelector('#settings-curr-password');
          const newCurrentInput = document.getElementById('settings-new-password') || container.querySelector('#settings-new-password') || newPwdInput;
          const confCurrentInput = document.getElementById('settings-conf-password') || container.querySelector('#settings-conf-password') || confPwdInput;
          const savePwdBtn = document.getElementById('btn-save-password') || container.querySelector('#btn-save-password');

          const currVal = currInput ? currInput.value : '';
          const newVal = newCurrentInput ? newCurrentInput.value : '';
          const confVal = confCurrentInput ? confCurrentInput.value : '';

          if (!currVal) {
            UI.showToast('Vui lòng nhập mật khẩu hiện tại.', 'warning');
            return;
          }
          if (newVal.length < 8) {
            UI.showToast('Mật khẩu mới phải có tối thiểu 8 ký tự.', 'warning');
            return;
          }
          if (!StudentView.getPasswordRequirements(newVal).hasSpecialCharacter) {
            UI.showToast('Mật khẩu mới cần có ít nhất một ký tự đặc biệt (ví dụ !@#).', 'warning');
            return;
          }
          if (newVal !== confVal) {
            UI.showToast('Mật khẩu xác nhận không khớp.', 'warning');
            return;
          }

          if (savePwdBtn) {
            savePwdBtn.disabled = true;
            savePwdBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang cập nhật...';
          }

          try {
            await ApiClient.changePassword(currVal, newVal, confVal);
            UI.showToast('Cập nhật mật khẩu thành công! Hãy ghi nhớ mật khẩu mới.', 'success');
            passwordForm.reset();
            validatePwdRealtime();
          } catch (err) {
            UI.showToast(err.message || 'Lỗi đổi mật khẩu.', 'error');
          } finally {
            if (savePwdBtn) {
              savePwdBtn.disabled = false;
              savePwdBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">key</span><span>Cập Nhật Mật Khẩu</span>';
            }
          }
        };
      }

      // 5. Preferences Save Handler
      const savePrefsBtn = container.querySelector('#btn-save-preferences');
      if (savePrefsBtn) {
        savePrefsBtn.onclick = async () => {
          const prefCourse = container.querySelector('#pref-email-course')?.checked ?? true;
          const prefAssessment = container.querySelector('#pref-email-assessment')?.checked ?? true;
          const prefGrade = container.querySelector('#pref-email-grade')?.checked ?? true;
          const prefMarketing = container.querySelector('#pref-email-marketing')?.checked ?? false;

          savePrefsBtn.disabled = true;
          savePrefsBtn.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> Đang lưu...';

          try {
            await ApiClient.updatePreferences({
              email_course: prefCourse,
              email_assessment: prefAssessment,
              email_grade: prefGrade,
              email_marketing: prefMarketing
            });
            UI.showToast('Đã lưu tùy chọn nhận thông báo học vụ thành công!', 'success');
          } catch (err) {
            UI.showToast(err.message || 'Lỗi cập nhật tùy chọn thông báo.', 'error');
          } finally {
            savePrefsBtn.disabled = false;
            savePrefsBtn.innerHTML = '<span class="material-symbols-outlined text-[18px]">check_circle</span><span>Lưu Tùy Chọn Thông Báo</span>';
          }
        };
      }

    } catch (err) {
      console.error('Settings load error:', err);
      container.innerHTML = `
        <div class="max-w-xl mx-auto p-8 text-center text-rose-500">
          <p class="font-bold">Lỗi nạp thông tin cài đặt: ${UI.escapeHtml(err.message || 'Lỗi hệ thống')}</p>
          <button type="button" class="mt-4 px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.refreshCurrentRoute(() => StudentView.renderSettings(document.getElementById('main-content'))) ">Thử lại</button>
        </div>
      `;
    }
  }
}

window.StudentView = StudentView;
