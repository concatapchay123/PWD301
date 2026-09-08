/**
 * PWD301 — Student Views
 * Distraction-Free Learning & Full Assessment Engine Simulation
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};
  window.PWD.views = window.PWD.views || {};

  const studentViews = {
    // 1. Student Dashboard (Functional Minimalism)
    dashboard() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const enrolledCourses = store.courses.filter(c => c.enrolled);
      const activeCourse = store.courses.find(c => c.id === 'c1');
      const upcomingAssessment = store.assessments.find(a => a.id === 'a1');

      return `
        ${cmp.heroWelcome(
          'Chào mừng trở lại, Minh Anh! 👋',
          'Tiếp tục hành trình học tập hôm nay. Bạn có 1 bài tập sắp đến hạn và 1 bài kiểm tra đang mở.',
          activeCourse ? `<a href="#/student/lesson/les_4" class="btn btn-light fw-semibold px-3 py-2" style="color: #1e3a8a; border-radius: var(--radius-md); box-shadow: 0 4px 12px rgba(0,0,0,0.1);">Tiếp tục học: Bài 4 →</a>` : ''
        )}

        <!-- Essential KPI Cards with vibrant accent colors -->
        <div class="row g-4 mb-4">
          <div class="col-md-4">
            ${cmp.statCard('Khóa học đang học', enrolledCourses.filter(c => c.status === 'published' && c.progress < 100).length, 'Tiến độ trung bình: 50%', 'book', 'primary')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Khóa học hoàn thành', enrolledCourses.filter(c => c.progress === 100).length, 'Đã cấp chứng chỉ xuất sắc', 'checkCircle', 'emerald')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Bài kiểm tra đang mở', store.assessments.filter(a => a.status === 'published').length, 'Hạn chót: 30/09/2026', 'clock', 'amber')}
          </div>
        </div>

        <div class="row g-4">
          <!-- Primary: Tiếp tục học -->
          <div class="col-lg-8">
            <div class="card mb-4">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Đang học gần đây</h5>
                <a href="#/student/my-learning" class="text-caption text-decoration-none">Tất cả khóa học →</a>
              </div>
              <div class="card-body">
                ${activeCourse ? `
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <span class="text-caption fw-bold" style="color: var(--brand-primary);">${activeCourse.code}</span>
                      <h4 class="sub-title mb-1" style="font-size: 1.1rem;">${activeCourse.title}</h4>
                      <p class="text-caption text-muted m-0">Giảng viên: ${activeCourse.instructorName} • 6 bài học</p>
                    </div>
                    <span class="badge badge-info">Đang học</span>
                  </div>

                  <div class="my-3">
                    <div class="d-flex justify-content-between text-caption mb-1">
                      <span class="text-muted">Tiến độ hoàn thành</span>
                      <span class="fw-semibold">${activeCourse.progress}%</span>
                    </div>
                    ${cmp.progressBar(activeCourse.progress)}
                  </div>

                  <div class="p-3 bg-slate-50 border border-slate-200 rounded d-flex justify-content-between align-items-center mt-3">
                    <div>
                      <div class="text-caption text-muted">Bài học tiếp theo:</div>
                      <div class="fw-medium text-slate-800">Bài 4: Xử lý Biểu mẫu với Flask-WTF & Phòng chống CSRF</div>
                    </div>
                    <a href="#/student/lesson/les_4" class="btn btn-primary btn-sm">Vào học ngay</a>
                  </div>
                ` : cmp.emptyState('Chưa có khóa học', 'Bạn chưa ghi danh khóa học nào.', `<a href="#/student/catalog" class="btn btn-primary btn-sm">Khám phá khóa học</a>`)}
              </div>
            </div>

            <!-- Bài kiểm tra sắp tới -->
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Bài kiểm tra & Đánh giá</h5>
                <a href="#/student/assessments" class="text-caption text-decoration-none">Xem tất cả →</a>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="app-table">
                    <thead>
                      <tr>
                        <th>Bài kiểm tra</th>
                        <th>Thời lượng</th>
                        <th>Trạng thái</th>
                        <th class="text-end">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${upcomingAssessment ? `
                        <tr>
                          <td>
                            <div class="fw-medium">${upcomingAssessment.title}</div>
                            <div class="text-caption text-muted">Môn: PWD301 • Hạn nộp: ${upcomingAssessment.closeAt}</div>
                          </td>
                          <td>${upcomingAssessment.durationMinutes} phút</td>
                          <td>${cmp.badge('warning', 'Đang mở làm bài')}</td>
                          <td class="text-end">
                            <a href="#/student/assessment-detail/${upcomingAssessment.id}" class="btn btn-primary btn-sm">Làm bài</a>
                          </td>
                        </tr>
                      ` : ''}
                      <tr>
                        <td>
                          <div class="fw-medium">Bài thực hành 01 — Routing & Templating</div>
                          <div class="text-caption text-muted">Môn: PWD301 • Hoàn thành ngày 28/08</div>
                        </td>
                        <td>30 phút</td>
                        <td>${cmp.badge('success', '10.0 / 10.0')}</td>
                        <td class="text-end">
                          <a href="#/student/result/att_completed_01" class="btn btn-secondary btn-sm">Xem kết quả</a>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Secondary: Lịch học & Lối tắt Trợ lý AI -->
          <div class="col-lg-4">
            <!-- Lịch học & Deadline sắp tới -->
            <div class="card mb-4">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Lịch học & Hạn chót</h5>
                <span class="badge badge-warning">3 sự kiện</span>
              </div>
              <div class="card-body p-0">
                <ul class="list-group list-group-flush">
                  <li class="list-group-item px-3 py-3">
                    <div class="d-flex justify-content-between align-items-start">
                      <div>
                        <div class="fw-semibold text-slate-800" style="font-size: 13px;">Học bù chuyên đề Docker</div>
                        <div class="text-caption text-muted mt-1">Môn ARC302 • Phòng Lab B204</div>
                      </div>
                      <span class="badge badge-neutral" style="font-size: 11px;">Thứ 7 08:30</span>
                    </div>
                  </li>
                  <li class="list-group-item px-3 py-3">
                    <div class="d-flex justify-content-between align-items-start">
                      <div>
                        <div class="fw-semibold text-slate-800" style="font-size: 13px;">Hạn chót: Bài kiểm tra giữa kỳ</div>
                        <div class="text-caption text-muted mt-1">Môn PWD301 • 10 câu trắc nghiệm</div>
                      </div>
                      <span class="badge badge-warning" style="font-size: 11px;">30/09 23:59</span>
                    </div>
                  </li>
                  <li class="list-group-item px-3 py-3">
                    <div class="d-flex justify-content-between align-items-start">
                      <div>
                        <div class="fw-semibold text-slate-800" style="font-size: 13px;">Live Q&A: Kiến trúc Web MVC</div>
                        <div class="text-caption text-muted mt-1">GV. Trần Hoàng Nam • Trực tuyến</div>
                      </div>
                      <span class="badge badge-info" style="font-size: 11px;">05/10 19:30</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Trợ lý học tập AI (Liên kết kích hoạt Chatbot hình tròn) -->
            <div class="card">
              <div class="card-header d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2">
                  <div class="icon-box icon-box-primary" style="width: 30px; height: 30px; border-radius: 6px;">${cmp.icon('sparkles')}</div>
                  <h5 class="sub-title m-0">Trợ lý học tập AI</h5>
                </div>
                <span class="badge badge-success" style="font-size: 11px;">24/7 Online</span>
              </div>
              <div class="card-body">
                <p class="text-caption text-muted mb-3">Hỏi đáp kiến thức, gỡ rối code Flask và hướng dẫn làm bài kiểm tra bám sát giáo trình.</p>
                <div class="d-grid gap-2">
                  <button type="button" class="btn btn-primary btn-sm d-flex align-items-center justify-content-center gap-2" onclick="PWD.app.openAIChat()">
                    <span>${cmp.icon('sparkles')}</span>
                    <span>Bật Chatbot AI ngay</span>
                  </button>
                  <a href="#/student/ai-assistant" class="btn btn-secondary btn-sm text-center">
                    Mở giao diện đầy đủ →
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 2. Student Course Catalog
    catalog() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const courses = store.courses.filter(c => c.status === 'published');

      return `
        ${cmp.pageHeader({
          title: 'Khám phá Khóa học',
          subtitle: 'Tìm kiếm và đăng ký các môn học trong chương trình đào tạo',
          primaryAction: `<a href="#/student/my-learning" class="btn btn-secondary btn-sm">Khóa học của tôi</a>`
        })}

        <div class="row g-3 mb-4 align-items-center">
          <div class="col-md-5">
            <div class="catalog-search-wrap">
              <span class="text-slate-400 me-2">${cmp.icon('search')}</span>
              <input type="text" id="stu-search" class="catalog-search-input border-0 w-100" placeholder="Tìm theo tên môn hoặc mã môn..." oninput="PWD.views.student.filterCatalog()">
            </div>
          </div>
          <div class="col-md-4">
            <select id="stu-cat-filter" class="form-select" onchange="PWD.views.student.filterCatalog()">
              <option value="all">Tất cả môn học</option>
              <option value="Phát triển Web">Phát triển Web</option>
              <option value="Frontend">Frontend</option>
              <option value="Dữ liệu">Dữ liệu</option>
              <option value="Bảo mật">Bảo mật</option>
              <option value="AI / ML">AI / ML</option>
            </select>
          </div>
          <div class="col-md-3 text-md-end d-none d-md-block">
            <span class="text-caption text-muted">Hiển thị: <strong>${courses.length}</strong> khóa học</span>
          </div>
        </div>

        <div class="row g-4" id="stu-catalog-grid">
          ${courses.map(course => cmp.renderCourseCard(course, { targetLink: `#/student/course/${course.id}` })).join('')}
        </div>
      `;
    },

    filterCatalog() {
      const q = (document.getElementById('stu-search')?.value || '').toLowerCase().trim();
      const cat = document.getElementById('stu-cat-filter')?.value || 'all';

      document.querySelectorAll('#stu-catalog-grid > div').forEach(card => {
        const query = (card.getAttribute('data-query') || '').toLowerCase();
        const category = card.getAttribute('data-category') || card.getAttribute('data-cat') || '';
        const matchQ = !q || query.includes(q);
        const matchC = cat === 'all' || category === cat;
        card.style.display = (matchQ && matchC) ? 'block' : 'none';
      });
    },

    // 3. Student Course Detail (Handles Prerequisites Blocked & Capacity - Scenario 2)
    courseDetail(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const course = store.courses.find(c => c.id === params.id);

      if (!course) {
        return cmp.emptyState('Không tìm thấy khóa học', 'Khóa học không tồn tại.', `<a href="#/student/catalog" class="btn btn-secondary btn-sm">Quay lại danh mục</a>`);
      }

      // Check prerequisite condition
      let prereqBlocked = false;
      let missingPrereqCourse = null;

      if (course.prerequisites && course.prerequisites.length > 0) {
        for (const pid of course.prerequisites) {
          const pCourse = store.courses.find(c => c.id === pid);
          if (!pCourse || pCourse.progress < 100) {
            prereqBlocked = true;
            missingPrereqCourse = pCourse;
            break;
          }
        }
      }

      const isFull = course.enrolledCount >= course.capacity;
      const isEnrolled = course.enrolled;
      const lessons = store.lessons.filter(l => l.courseId === course.id);

      return `
        ${cmp.pageHeader({
          title: course.title,
          subtitle: `Mã môn: ${course.code} • Giảng viên: ${course.instructorName}`,
          breadcrumbs: [
            { label: 'Khám phá khóa học', href: '#/student/catalog' },
            { label: course.code, href: `#/student/course/${course.id}` }
          ],
          primaryAction: isEnrolled 
            ? `<a href="#/student/course-dashboard/${course.id}" class="btn btn-primary btn-sm">Vào lớp học ngay</a>`
            : prereqBlocked 
              ? `<button class="btn btn-primary btn-sm" disabled title="Thiếu môn tiên quyết">Chưa đủ điều kiện ghi danh</button>`
              : isFull
                ? `<button class="btn btn-primary btn-sm" disabled title="Khóa học đã hết chỉ tiêu">Đã hết chỗ</button>`
                : `<button class="btn btn-primary btn-sm" onclick="PWD.views.student.handleEnroll('${course.id}')">Ghi danh khóa học</button>`
        })}

        ${prereqBlocked ? `
          <div class="alert-card alert-card-danger mb-4">
            <span style="flex-shrink:0;">${cmp.icon('alertCircle')}</span>
            <div>
              <strong>Ghi danh bị chặn do chưa đạt điều kiện tiên quyết:</strong>
              <div class="mt-1">
                Để đăng ký môn học này, bạn cần phải hoàn thành và đạt điểm tổng kết khóa học 
                <strong>${missingPrereqCourse ? `${missingPrereqCourse.code} — ${missingPrereqCourse.title}` : 'môn học tiên quyết'}</strong> (tiến độ 100%).
              </div>
              ${missingPrereqCourse ? `
                <div class="mt-2">
                  <a href="#/student/course/${missingPrereqCourse.id}" class="btn btn-secondary btn-sm">
                    Đến môn học tiên quyết: ${missingPrereqCourse.code} →
                  </a>
                </div>
              ` : ''}
            </div>
          </div>
        ` : ''}

        ${isFull && !isEnrolled ? `
          <div class="alert-card alert-card-warning mb-4">
            <span style="flex-shrink:0;">${cmp.icon('alertTriangle')}</span>
            <div>
              <strong>Lớp học đã đủ chỉ tiêu sinh viên:</strong>
              <div class="mt-1">Khóa học đã đạt giới hạn tuyển sinh (${course.capacity}/${course.capacity}). Vui lòng theo dõi đợt mở lớp tiếp theo.</div>
            </div>
          </div>
        ` : ''}

        <div class="row g-4">
          <div class="col-lg-8">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="sub-title m-0">Mô tả và mục tiêu môn học</h5>
              </div>
              <div class="card-body">
                <p style="line-height: 1.6;">${course.description}</p>
                <div class="alert-card alert-card-info mt-3">
                  <span style="flex-shrink:0;">${cmp.icon('checkCircle')}</span>
                  <div>
                    <strong>Quy định hoàn thành môn:</strong>
                    <div class="text-caption mt-1">${course.completionRule}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Chương trình đào tạo</h5>
                <span class="text-caption text-muted">${lessons.length} bài học</span>
              </div>
              <div class="card-body p-0">
                <ul class="list-group list-group-flush">
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
                <h5 class="sub-title m-0">Trạng thái khóa học</h5>
              </div>
              <div class="card-body">
                <div class="mb-3">
                  <div class="text-caption text-muted">Trạng thái của bạn</div>
                  <div class="fw-semibold mt-1">
                    ${isEnrolled ? cmp.badge('info', 'Đã ghi danh') : cmp.badge('neutral', 'Chưa ghi danh')}
                  </div>
                </div>
                <div class="mb-3">
                  <div class="text-caption text-muted">Sĩ số lớp học</div>
                  <div class="fw-medium">${course.enrolledCount} / ${course.capacity} sinh viên</div>
                </div>
                <div class="mb-3">
                  <div class="text-caption text-muted">Môn học tiên quyết</div>
                  <div class="fw-medium">
                    ${course.prerequisites && course.prerequisites.length > 0 
                      ? course.prerequisites.map(p => `<span class="badge badge-warning me-1">${p}</span>`).join('') 
                      : 'Không có'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    handleEnroll(courseId) {
      const res = window.PWD.store.enrollCourse(courseId);
      if (res.success) {
        window.PWD.components.showToast(res.message, 'success');
        window.PWD.router.navigate('#/student/my-learning');
      } else {
        window.PWD.components.showToast(res.message, 'danger');
      }
    },

    // 4. My Learning
    myLearning() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const enrolled = store.courses.filter(c => c.enrolled);

      return `
        ${cmp.pageHeader({
          title: 'Khóa học của tôi',
          subtitle: 'Các chương trình đào tạo bạn đang theo học hoặc đã hoàn thành',
          primaryAction: `<a href="#/student/catalog" class="btn btn-primary btn-sm">Khám phá thêm khóa học</a>`
        })}

        <div class="row g-4" id="stu-mylearning-grid">
          ${enrolled.map(c => cmp.renderCourseCard(c, { targetLink: `#/student/lesson/${c.id === 'c1' ? 'les_4' : 'les_1'}` })).join('')}
        </div>
      `;
    },

    // 5. Course Dashboard
    courseDashboard(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const course = store.courses.find(c => c.id === params.id) || store.courses[0];
      const lessons = store.lessons.filter(l => l.courseId === course.id);

      return `
        ${cmp.pageHeader({
          title: `${course.code} — ${course.title}`,
          subtitle: `Giảng viên: ${course.instructorName} • Tiến độ: ${course.progress}%`,
          breadcrumbs: [
            { label: 'Khóa học của tôi', href: '#/student/my-learning' },
            { label: course.code, href: `#/student/course-dashboard/${course.id}` }
          ],
          primaryAction: `<a href="#/student/lesson/les_4" class="btn btn-primary btn-sm">Vào Trình phát Udemy Player →</a>`
        })}

        <div class="row g-4">
          <div class="col-lg-8">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Danh sách bài học</h5>
                <span class="text-caption text-muted">${lessons.length} bài học</span>
              </div>
              <div class="card-body p-0">
                <ul class="list-group list-group-flush">
                  ${lessons.map((les, idx) => `
                    <li class="list-group-item d-flex justify-content-between align-items-center px-4 py-3">
                      <div class="d-flex align-items-center gap-3">
                        <span style="color: ${les.completed ? 'var(--color-success)' : 'var(--slate-400)'};">
                          ${les.completed ? cmp.icon('checkCircle') : cmp.icon('clock')}
                        </span>
                        <div>
                          <div class="fw-medium">${les.title}</div>
                          <div class="text-caption text-muted">${les.duration} • ${les.resources ? les.resources.length : 0} tài liệu đính kèm</div>
                        </div>
                      </div>
                      <a href="#/student/lesson/${les.id}" class="btn ${les.completed ? 'btn-secondary' : 'btn-primary'} btn-sm">
                        ${les.completed ? 'Xem lại bài' : 'Vào học'}
                      </a>
                    </li>
                  `).join('')}
                </ul>
              </div>
            </div>
          </div>

          <div class="col-lg-4">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="sub-title m-0">Tiến độ khóa học</h5>
              </div>
              <div class="card-body">
                <div class="d-flex justify-content-between text-caption mb-1">
                  <span>Hoàn thành bài giảng</span>
                  <span class="fw-semibold">${course.progress}%</span>
                </div>
                ${cmp.progressBar(course.progress, course.progress === 100)}
                <div class="text-caption text-muted mt-3">
                  ${course.completionRule}
                </div>
                <div class="mt-3">
                  <a href="#/student/progress/${course.id}" class="btn btn-secondary btn-sm w-100">Xem chi tiết tiến độ</a>
                </div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h5 class="sub-title m-0">Bài kiểm tra môn học</h5>
              </div>
              <div class="card-body">
                <div class="fw-medium mb-1">Kiểm tra giữa kỳ</div>
                <div class="text-caption text-muted mb-3">Thời lượng 45 phút • Hạn chót: 30/09/2026</div>
                <a href="#/student/assessment-detail/a1" class="btn btn-primary btn-sm w-100">Bắt đầu làm bài thi</a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 6. UDEMY COURSE LEARNING PLAYER (1:1 Match with Image 3)
    lessonReader(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const lesson = store.lessons.find(l => l.id === params.id) || store.lessons.find(l => l.courseId === 'c1') || store.lessons[0];
      const course = store.courses.find(c => c.id === lesson.courseId) || store.courses[0];
      const courseLessons = store.lessons.filter(l => l.courseId === course.id);

      // Group into sections
      const sections = {};
      courseLessons.forEach(l => {
        const secTitle = l.sectionTitle || 'Phần 1: Nội dung bài giảng';
        if (!sections[secTitle]) sections[secTitle] = [];
        sections[secTitle].push(l);
      });

      // Progress metrics
      const completedCount = courseLessons.filter(l => l.completed).length;
      const totalLessons = courseLessons.length;
      const progressPercent = totalLessons > 0 ? Math.round((completedCount / totalLessons) * 100) : 0;

      // Prev & Next navigation
      const currentIndex = courseLessons.findIndex(l => l.id === lesson.id);
      const prevLesson = currentIndex > 0 ? courseLessons[currentIndex - 1] : null;
      const nextLesson = currentIndex < courseLessons.length - 1 ? courseLessons[currentIndex + 1] : null;

      // Active tab
      const activeTab = window.PWD.currentUdemyTab || 'overview';

      return `
        <div class="udemy-player-page">
          <!-- 1. Udemy Black Topbar -->
          <header class="udemy-player-topbar">
            <div class="udemy-brand-title">
              <a href="#/student/my-learning" class="udemy-back-btn" title="Quay lại khóa học của tôi">
                ${cmp.icon('arrowLeft')}
                <span class="d-none d-sm-inline">Quay lại</span>
              </a>
              <span class="text-slate-600">|</span>
              <span class="fw-bold text-truncate" style="max-width: 500px;" title="${course.title}">
                ${course.code}: ${course.title}
              </span>
            </div>

            <div class="udemy-topbar-actions">
              <!-- Leave Rating Button -->
              <button type="button" class="udemy-topbar-btn d-none d-md-inline-flex" onclick="PWD.views.student.openRatingModal('${course.id}')">
                <span>⭐</span> <span>Đưa ra xếp hạng</span>
              </button>

              <!-- Progress Dropdown -->
              <div class="dropdown d-inline-block">
                <button type="button" class="udemy-topbar-btn dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false" id="udemy-progress-dropdown-btn">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                  <span>Tiến độ của bạn (${progressPercent}%)</span>
                </button>
                <div class="dropdown-menu dropdown-menu-end p-3 shadow-lg" style="min-width: 280px; font-size: 13px;">
                  <div class="fw-bold mb-1">Tiến độ hoàn thành khóa học</div>
                  <div class="text-caption text-muted mb-2">${completedCount}/${totalLessons} bài học đã hoàn tất</div>
                  <div class="mb-3">${cmp.progressBar(progressPercent, progressPercent === 100)}</div>
                  <div class="border-top pt-2 text-caption">
                    ${progressPercent === 100 
                      ? '<span class="text-success fw-bold">✓ Chúc mừng! Bạn đã đủ điều kiện nhận Chứng chỉ tốt nghiệp!</span>' 
                      : 'Hoàn thành tất cả các bài giảng để mở khóa chứng chỉ tốt nghiệp.'}
                  </div>
                </div>
              </div>

              <!-- Share Button -->
              <button type="button" class="udemy-topbar-btn" onclick="PWD.views.student.handleShareCourse('${course.id}')" title="Chia sẻ khóa học">
                ${cmp.icon('share')}
                <span class="d-none d-sm-inline">Chia sẻ</span>
              </button>
            </div>
          </header>

          <!-- 2. Main Stage Split View -->
          <div class="udemy-player-split">
            <!-- Left: Video & Interaction Tabs -->
            <div class="udemy-stage-col" id="udemy-player-stage-col">
              <!-- 16:9 Video Canvas -->
              <div class="udemy-video-stage" id="udemy-video-canvas">
                <!-- Floating Edge Chevrons -->
                ${prevLesson ? `
                  <button type="button" class="udemy-edge-nav-btn prev" onclick="PWD.views.student.switchLecture('${prevLesson.id}')" title="Bài trước: ${prevLesson.title}">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
                  </button>
                ` : ''}
                ${nextLesson ? `
                  <button type="button" class="udemy-edge-nav-btn next" onclick="PWD.views.student.switchLecture('${nextLesson.id}')" title="Bài tiếp theo: ${nextLesson.title}">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
                  </button>
                ` : ''}

                <!-- Center Play Button & Title Overlay -->
                <div class="text-center position-relative" style="z-index: 10;">
                  <button type="button" class="udemy-video-center-btn mx-auto mb-3" id="udemy-center-play-btn" onclick="PWD.views.student.handlePlayerPlayPause()" title="Phát video">
                    ${cmp.icon('play')}
                  </button>
                  <div class="text-white fw-bold px-3" style="font-size: 16px; text-shadow: 0 2px 10px rgba(0,0,0,0.85);">
                    ${lesson.title}
                  </div>
                  <div class="text-slate-300 text-caption mt-1" style="text-shadow: 0 1px 4px rgba(0,0,0,0.8);">
                    Trình phát video trực tuyến Full HD 1080p • Thời lượng: ${lesson.duration}
                  </div>
                </div>

                <!-- Bottom Video Controls -->
                <div class="udemy-video-controls">
                  <!-- Scrubber slider -->
                  <div class="udemy-scrubber-track" id="udemy-scrubber" onclick="PWD.views.student.handleScrubberClick(event)">
                    <div class="udemy-scrubber-fill" id="udemy-scrubber-fill" style="width: 28%;">
                      <div class="udemy-scrubber-thumb"></div>
                    </div>
                  </div>

                  <div class="udemy-controls-row">
                    <div class="d-flex align-items-center gap-2">
                      <button type="button" class="udemy-btn-icon" id="udemy-ctrl-play-btn" onclick="PWD.views.student.handlePlayerPlayPause()" title="Phát / Tạm dừng">
                        ${cmp.icon('play')}
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.views.student.handlePlayerSeek(-10)" title="Tua lại 10 giây">
                        ${cmp.icon('rotateCcw')}
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.views.student.handlePlayerSeek(10)" title="Tua tới 10 giây">
                        ${cmp.icon('rotateCw')}
                      </button>
                      <button type="button" class="udemy-btn-icon fw-bold" id="udemy-speed-btn" style="font-size: 12px;" onclick="PWD.views.student.cyclePlaybackSpeed()" title="Tốc độ phát">
                        1x
                      </button>
                      <span class="text-caption ms-2" id="udemy-time-readout" style="font-size: 12px; color: #ffffff;">
                        02:15 / ${lesson.duration || '35:00'}
                      </span>
                    </div>

                    <div class="d-flex align-items-center gap-2">
                      <button type="button" class="udemy-btn-icon" onclick="PWD.views.student.handleToggleMute()" id="udemy-mute-btn" title="Âm lượng">
                        ${cmp.icon('volume2')}
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.components.showToast('Đã bật phụ đề tiếng Việt (Closed Captions)', 'info')" title="Phụ đề CC">
                        <span style="font-size: 11px; font-weight: 800; border: 1px solid currentColor; padding: 1px 3px; border-radius: 2px;">CC</span>
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.components.showToast('Chất lượng video: Tự động (1080p 60fps)', 'info')" title="Cài đặt phát">
                        ${cmp.icon('settings')}
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.views.student.toggleCurriculumSidebar()" title="Chế độ Mở rộng (Theater Mode)">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><polyline points="2 10 22 10"/></svg>
                      </button>
                      <button type="button" class="udemy-btn-icon" onclick="PWD.views.student.toggleFullscreen()" title="Toàn màn hình">
                        ${cmp.icon('maximize2')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Tabs Navigation Bar -->
              <div class="udemy-tabs-container">
                <ul class="udemy-tabs-nav">
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'overview' ? 'active' : ''}" onclick="PWD.views.student.switchTab('overview')">
                      Tổng quan
                    </button>
                  </li>
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'qa' ? 'active' : ''}" onclick="PWD.views.student.switchTab('qa')">
                      Hỏi đáp (Q&A)
                    </button>
                  </li>
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'notes' ? 'active' : ''}" onclick="PWD.views.student.switchTab('notes')">
                      Ghi chú
                    </button>
                  </li>
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'announcements' ? 'active' : ''}" onclick="PWD.views.student.switchTab('announcements')">
                      Thông báo
                    </button>
                  </li>
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'reviews' ? 'active' : ''}" onclick="PWD.views.student.switchTab('reviews')">
                      Đánh giá
                    </button>
                  </li>
                  <li>
                    <button type="button" class="udemy-tab-link ${activeTab === 'resources' ? 'active' : ''}" onclick="PWD.views.student.switchTab('resources')">
                      Công cụ học tập & Tài nguyên (${lesson.resources ? lesson.resources.length : 0})
                    </button>
                  </li>
                </ul>
              </div>

              <!-- Tab Content Area -->
              <div class="udemy-tab-content-area" id="udemy-tab-content">
                ${this.renderUdemyTabContent(course, lesson, activeTab)}
              </div>
            </div>

            <!-- Right: Curriculum Sidebar ("Nội dung khóa học") -->
            <aside class="udemy-curriculum-sidebar" id="udemy-curriculum-sidebar">
              <div class="udemy-curriculum-header">
                <span class="fw-bold" style="font-size: 15px;">Nội dung khóa học</span>
                <button type="button" class="btn btn-ghost btn-sm p-1 text-slate-500" onclick="PWD.views.student.toggleCurriculumSidebar()" title="Thu gọn danh sách bài học" aria-label="Đóng">
                  ${cmp.icon('x')}
                </button>
              </div>

              <div class="udemy-curriculum-body">
                ${Object.keys(sections).map((secTitle, sIdx) => {
                  const sLessons = sections[secTitle];
                  const sCompleted = sLessons.filter(l => l.completed).length;
                  const isCurrentSection = sLessons.some(l => l.id === lesson.id);

                  return `
                    <div class="udemy-section-card">
                      <div class="udemy-section-header" onclick="PWD.views.student.toggleSectionAccordion('sec-body-${sIdx}', 'sec-arrow-${sIdx}')">
                        <div>
                          <div class="fw-bold" style="font-size: 13.5px;">${secTitle}</div>
                          <div class="text-caption text-muted mt-1">${sCompleted}/${sLessons.length} | ${sLessons.length * 35} phút</div>
                        </div>
                        <span class="text-slate-400" id="sec-arrow-${sIdx}">${isCurrentSection ? '▲' : '▼'}</span>
                      </div>

                      <div class="udemy-section-content ${isCurrentSection ? '' : 'd-none'}" id="sec-body-${sIdx}">
                        ${sLessons.map(l => {
                          const isActive = l.id === lesson.id;
                          return `
                            <div class="udemy-lecture-row ${isActive ? 'active' : ''}" onclick="PWD.views.student.switchLecture('${l.id}')">
                              <input type="checkbox" class="udemy-lecture-checkbox" ${l.completed ? 'checked' : ''} onclick="PWD.views.student.handleToggleLecture('${course.id}', '${l.id}', event)" title="${l.completed ? 'Đánh dấu chưa hoàn thành' : 'Đánh dấu đã hoàn thành'}">
                              <div class="flex-grow-1" style="min-width: 0;">
                                <div class="fw-medium ${isActive ? 'fw-bold' : ''}" style="font-size: 13px; line-height: 1.4; color: ${isActive ? '#5624d0' : 'inherit'};">
                                  ${l.title}
                                </div>
                                <div class="d-flex align-items-center gap-2 mt-1 text-caption text-muted" style="font-size: 12px;">
                                  <span>${l.type === 'quiz' ? '📝 Trắc nghiệm' : l.type === 'certificate' ? '🏆 Chứng chỉ' : '📺 Video'}</span>
                                  <span>•</span>
                                  <span>${l.duration}</span>
                                </div>
                                ${l.resources && l.resources.length > 0 ? `
                                  <button type="button" class="udemy-resource-dropdown-btn" onclick="event.stopPropagation(); PWD.views.student.showLectureResourcesModal('${l.id}')">
                                    📁 Tài nguyên (${l.resources.length}) ▾
                                  </button>
                                ` : ''}
                              </div>
                            </div>
                          `;
                        }).join('')}
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </aside>

            <!-- Floating Button to Re-open Sidebar when collapsed -->
            <button type="button" class="udemy-sidebar-open-tab d-none" id="udemy-sidebar-reopen-tab" onclick="PWD.views.student.toggleCurriculumSidebar()" title="Mở danh sách bài học">
              <span>☰</span> Nội dung khóa học
            </button>
          </div>
        </div>
      `;
    },

    // Render Tab Content for Udemy Player
    renderUdemyTabContent(course, lesson, activeTab) {
      const cmp = window.PWD.components;

      if (activeTab === 'overview') {
        return `
          <div style="max-width: 900px;">
            <h2 class="section-title mb-2" style="font-size: 1.35rem; font-weight: 700;">
              ${course.title}
            </h2>
            <div class="d-flex align-items-center flex-wrap gap-3 text-caption text-muted mb-4 pb-3 border-bottom">
              <span class="d-flex align-items-center gap-1 text-warning fw-bold">
                ⭐ ${course.rating || '4.8'} (${course.ratingCount || '18.420 xếp hạng'})
              </span>
              <span>•</span>
              <span>👥 ${course.studentsCount || '16.538'} học viên</span>
              <span>•</span>
              <span>⏱ ${course.totalDuration || '33,5 giờ'} tổng thời lượng</span>
              <span>•</span>
              <span>Giảng viên: <strong>${course.instructorName}</strong></span>
            </div>

            <div class="mb-4">
              <h4 class="sub-title" style="font-size: 1.05rem;">Nội dung bài giảng hiện tại: ${lesson.title}</h4>
              <div class="p-3 bg-slate-50 border border-slate-200 rounded my-3" style="line-height: 1.7; font-size: 14.5px;">
                ${lesson.content}
              </div>
            </div>

            <div class="card mb-4">
              <div class="card-header bg-white">
                <h5 class="sub-title m-0" style="font-size: 0.95rem;">Mục tiêu và kiến thức cốt lõi</h5>
              </div>
              <div class="card-body">
                <ul class="mb-0" style="font-size: 14px; line-height: 1.8; padding-left: 20px;">
                  <li>Hiểu rõ nguyên lý vận hành của kiến trúc phân tầng trong ứng dụng thực tế.</li>
                  <li>Áp dụng các chuẩn an toàn, phòng ngừa lỗ hổng bảo mật phổ biến.</li>
                  <li>Thực hành trực tiếp với mã nguồn chuẩn mực, phục vụ dự án thực chiến.</li>
                </ul>
              </div>
            </div>

            <div class="d-flex justify-content-between align-items-center pt-3 border-top">
              <span class="text-caption text-muted">Trạng thái: <strong>${lesson.completed ? '✓ Đã hoàn thành' : 'Đang học'}</strong></span>
              <button class="btn btn-sm ${lesson.completed ? 'btn-secondary' : 'btn-primary'}" onclick="PWD.views.student.handleToggleLecture('${course.id}', '${lesson.id}', event)">
                ${lesson.completed ? 'Đánh dấu chưa hoàn thành' : '✓ Đánh dấu hoàn thành bài này'}
              </button>
            </div>
          </div>
        `;
      }

      if (activeTab === 'qa') {
        return `
          <div style="max-width: 860px;">
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h4 class="sub-title m-0">Hỏi đáp & Thảo luận cộng đồng</h4>
              <button class="btn btn-primary btn-sm" onclick="PWD.components.showToast('Mở khung soạn thảo câu hỏi mới...', 'info')">
                + Đặt câu hỏi mới
              </button>
            </div>

            <div class="d-flex align-items-center bg-white border border-slate-200 rounded px-3 py-1 mb-4" style="height: 38px;">
              <span class="text-slate-400 me-2">${cmp.icon('search')}</span>
              <input type="text" class="border-0 w-100" style="outline: none; font-size: 13.5px;" placeholder="Tìm kiếm trong tất cả câu hỏi của khóa học...">
            </div>

            <div class="list-group list-group-flush border rounded">
              <div class="list-group-item p-3">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <div class="fw-bold" style="font-size: 14px;">Làm thế nào để xử lý Cookie khi chạy qua Reverse Proxy Nginx?</div>
                    <p class="text-caption text-muted mt-1 mb-2">Thưa thầy, khi deploy production sau Nginx thì thuộc tính SameSite và Secure cần config thế nào để không bị mất Session ạ?</p>
                    <div class="text-caption text-slate-500">Hỏi bởi: <strong>Trần Quốc Bảo</strong> • 2 ngày trước</div>
                  </div>
                  <span class="badge badge-success">Đã giải đáp</span>
                </div>
                <div class="mt-3 p-3 bg-slate-50 border-start border-3 border-primary rounded-end text-caption" style="line-height: 1.6;">
                  <strong>Giảng viên ${course.instructorName}:</strong> Em cần thêm chỉ thị <code>proxy_set_header X-Forwarded-Proto $scheme;</code> vào file cấu hình Nginx để Flask nhận diện đúng giao thức HTTPS nhé!
                </div>
              </div>

              <div class="list-group-item p-3">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <div class="fw-bold" style="font-size: 14px;">Lỗi CSRF Token Missing khi submit AJAX Form?</div>
                    <p class="text-caption text-muted mt-1 mb-2">Em dùng fetch API để post dữ liệu thì bị báo lỗi 400 Bad Request CSRF missing ạ.</p>
                    <div class="text-caption text-slate-500">Hỏi bởi: <strong>Lê Hoàng Nam</strong> • 5 ngày trước</div>
                  </div>
                  <span class="badge badge-info">1 trả lời</span>
                </div>
              </div>
            </div>
          </div>
        `;
      }

      if (activeTab === 'notes') {
        return `
          <div style="max-width: 800px;">
            <h4 class="sub-title mb-3">Ghi chú cá nhân của bạn</h4>
            <div class="card mb-4">
              <div class="card-body p-3">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <span class="badge badge-info">Tạo ghi chú tại [02:15]</span>
                  <span class="text-caption text-muted">Tự động gắn mốc thời gian video</span>
                </div>
                <textarea class="form-control form-control-sm mb-3" id="udemy-note-input" rows="3" placeholder="Nhập nhanh ghi chú kiến thức cần lưu tâm tại bài học này..."></textarea>
                <button type="button" class="btn btn-primary btn-sm" onclick="PWD.views.student.handleSaveNote('${course.id}', '${lesson.id}')">
                  Lưu ghi chú
                </button>
              </div>
            </div>

            <h5 class="sub-title" style="font-size: 14px;">Các ghi chú đã lưu trong khóa học:</h5>
            <div class="list-group list-group-flush border rounded" id="udemy-saved-notes-list">
              <div class="list-group-item p-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <span class="badge badge-primary">⏱ 01:45</span>
                  <span class="text-caption text-muted">Hôm qua</span>
                </div>
                <div style="font-size: 13.5px;">Phải luôn bật <code>HttpOnly=True</code> để chặn JavaScript truy cập vào Session ID Cookie.</div>
              </div>
            </div>
          </div>
        `;
      }

      if (activeTab === 'announcements') {
        return `
          <div style="max-width: 800px;">
            <h4 class="sub-title mb-3">Thông báo từ Giảng viên</h4>
            <div class="card mb-3">
              <div class="card-body p-4">
                <div class="d-flex align-items-center gap-3 mb-3">
                  <div class="avatar bg-primary text-white" style="width: 42px; height: 42px; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-weight:bold;">HN</div>
                  <div>
                    <div class="fw-bold">${course.instructorName}</div>
                    <div class="text-caption text-muted">Đăng ngày 02/09/2026 • Khóa học ${course.code}</div>
                  </div>
                </div>
                <h5 class="sub-title" style="font-size: 15px;">Cập nhật bài giảng mẫu: Xử lý CSRF Token với AJAX & Jinja2</h5>
                <p style="font-size: 14px; line-height: 1.6; color: var(--slate-700);">
                  Chào các bạn sinh viên, thầy vừa bổ sung tệp mã nguồn mẫu cho Bài 4. Trong tệp đính kèm có code cấu hình Meta CSRF Token ở thẻ head của HTML để các bạn làm việc mượt mà với Fetch API nhé.
                </p>
                <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mô phỏng tải xuống mã nguồn bổ sung.', 'info')">
                  Tải tệp đính kèm bài viết (zip)
                </button>
              </div>
            </div>
          </div>
        `;
      }

      if (activeTab === 'reviews') {
        return `
          <div style="max-width: 800px;">
            <h4 class="sub-title mb-3">Đánh giá của học viên</h4>
            <div class="row g-4 align-items-center mb-4 p-3 bg-slate-50 border rounded">
              <div class="col-sm-4 text-center border-end">
                <div class="display-5 fw-bold text-warning">${course.rating || '4.8'}</div>
                <div class="text-warning mb-1">⭐⭐⭐⭐⭐</div>
                <div class="text-caption text-muted">${course.ratingCount || '18.420 xếp hạng'}</div>
              </div>
              <div class="col-sm-8">
                <div class="d-flex align-items-center gap-2 mb-1" style="font-size: 12px;">
                  <span style="width: 40px;">5 sao</span>
                  <div class="progress flex-grow-1" style="height: 8px;"><div class="progress-bar bg-warning" style="width: 82%;"></div></div>
                  <span style="width: 30px;" class="text-end text-muted">82%</span>
                </div>
                <div class="d-flex align-items-center gap-2 mb-1" style="font-size: 12px;">
                  <span style="width: 40px;">4 sao</span>
                  <div class="progress flex-grow-1" style="height: 8px;"><div class="progress-bar bg-warning" style="width: 13%;"></div></div>
                  <span style="width: 30px;" class="text-end text-muted">13%</span>
                </div>
                <div class="d-flex align-items-center gap-2" style="font-size: 12px;">
                  <span style="width: 40px;">3 sao</span>
                  <div class="progress flex-grow-1" style="height: 8px;"><div class="progress-bar bg-warning" style="width: 5%;"></div></div>
                  <span style="width: 30px;" class="text-end text-muted">5%</span>
                </div>
              </div>
            </div>

            <div class="list-group list-group-flush border rounded">
              <div class="list-group-item p-3">
                <div class="d-flex justify-content-between mb-1">
                  <strong>Nguyễn Văn Tuấn</strong>
                  <span class="text-warning">⭐⭐⭐⭐⭐</span>
                </div>
                <p class="text-caption text-muted mb-0">Khóa học rất chi tiết và dễ hiểu, kiến thức bảo mật web thực tế giúp mình áp dụng ngay vào đồ án tốt nghiệp!</p>
              </div>
              <div class="list-group-item p-3">
                <div class="d-flex justify-content-between mb-1">
                  <strong>Trần Mai Phương</strong>
                  <span class="text-warning">⭐⭐⭐⭐⭐</span>
                </div>
                <p class="text-caption text-muted mb-0">Giảng viên giảng cuốn hút, có slide và code mẫu đầy đủ cho từng bài học.</p>
              </div>
            </div>
          </div>
        `;
      }

      if (activeTab === 'resources') {
        const resources = lesson.resources || [];
        return `
          <div style="max-width: 800px;">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h4 class="sub-title m-0">Tài liệu & Công cụ học tập đính kèm</h4>
              <span class="badge badge-info">${resources.length} tệp tin</span>
            </div>

            ${resources.length > 0 ? `
              <div class="list-group border rounded">
                ${resources.map(r => `
                  <div class="list-group-item d-flex justify-content-between align-items-center p-3">
                    <div class="d-flex align-items-center gap-3">
                      <span class="text-primary">${cmp.icon('fileText')}</span>
                      <div>
                        <div class="fw-medium">${r.title}</div>
                        <div class="text-caption text-muted">Định dạng: ${r.type.toUpperCase()} • Dung lượng: ${r.size}</div>
                      </div>
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mô phỏng tải xuống tệp: ${r.title}', 'info')">
                      ${cmp.icon('download')} Tải xuống
                    </button>
                  </div>
                `).join('')}
              </div>
            ` : `
              <div class="p-4 text-center bg-slate-50 border rounded text-muted">
                Bài học này không có tệp tin đính kèm bổ sung. Hãy theo dõi video hướng dẫn trực tiếp.
              </div>
            `}
          </div>
        `;
      }

      return '';
    },

    // Udemy Player Interactive Actions
    switchTab(tabName) {
      window.PWD.currentUdemyTab = tabName;
      document.querySelectorAll('.udemy-tab-link').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
      });
      const store = window.PWD.store.state;
      const lesson = store.lessons.find(l => l.id === (PWD.router.currentRoute?.params?.id || 'les_4')) || store.lessons[3];
      const course = store.courses.find(c => c.id === lesson.courseId) || store.courses[0];
      const contentEl = document.getElementById('udemy-tab-content');
      if (contentEl) {
        contentEl.innerHTML = this.renderUdemyTabContent(course, lesson, tabName);
      }
    },

    toggleCurriculumSidebar() {
      const sidebar = document.getElementById('udemy-curriculum-sidebar');
      const reopenTab = document.getElementById('udemy-sidebar-reopen-tab');
      if (sidebar) {
        sidebar.classList.toggle('collapsed');
        if (reopenTab) {
          reopenTab.classList.toggle('d-none', !sidebar.classList.contains('collapsed'));
        }
      }
    },

    toggleSectionAccordion(secBodyId, secArrowId) {
      const body = document.getElementById(secBodyId);
      const arrow = document.getElementById(secArrowId);
      if (body) {
        body.classList.toggle('d-none');
        if (arrow) {
          arrow.textContent = body.classList.contains('d-none') ? '▼' : '▲';
        }
      }
    },

    switchLecture(lessonId) {
      window.PWD.router.navigate(`#/student/lesson/${lessonId}`);
    },

    handleToggleLecture(courseId, lessonId, event) {
      if (event) event.stopPropagation();
      const res = window.PWD.store.toggleLessonComplete(courseId, lessonId);
      if (res) {
        const lesson = window.PWD.store.state.lessons.find(l => l.id === lessonId);
        const title = lesson ? lesson.title : 'Bài học';
        if (res.completed) {
          window.PWD.components.showToast(`✓ Đã hoàn thành: ${title}`, 'success');
        } else {
          window.PWD.components.showToast(`Đã bỏ đánh dấu: ${title}`, 'info');
        }
        // Re-render view to refresh progress and checkmarks seamlessly
        window.PWD.router.handleRouting();
      }
    },

    handlePlayerPlayPause() {
      const centerBtn = document.getElementById('udemy-center-play-btn');
      const ctrlBtn = document.getElementById('udemy-ctrl-play-btn');
      const cmp = window.PWD.components;
      window.PWD.isPlaying = !window.PWD.isPlaying;

      if (window.PWD.isPlaying) {
        if (centerBtn) centerBtn.innerHTML = cmp.icon('pause');
        if (ctrlBtn) ctrlBtn.innerHTML = cmp.icon('pause');
        window.PWD.components.showToast('Đang phát bài giảng video...', 'info');
      } else {
        if (centerBtn) centerBtn.innerHTML = cmp.icon('play');
        if (ctrlBtn) ctrlBtn.innerHTML = cmp.icon('play');
        window.PWD.components.showToast('Đã tạm dừng video.', 'info');
      }
    },

    handlePlayerSeek(seconds) {
      const msg = seconds > 0 ? `Đã tua tới ${seconds}s` : `Đã tua lùi ${Math.abs(seconds)}s`;
      window.PWD.components.showToast(msg, 'info');
    },

    cyclePlaybackSpeed() {
      const speeds = ['0.75x', '1x', '1.25x', '1.5x', '2x'];
      const current = document.getElementById('udemy-speed-btn')?.textContent.trim() || '1x';
      const nextIdx = (speeds.indexOf(current) + 1) % speeds.length;
      const next = speeds[nextIdx];
      const btn = document.getElementById('udemy-speed-btn');
      if (btn) btn.textContent = next;
      window.PWD.components.showToast(`Tốc độ phát: ${next}`, 'info');
    },

    handleToggleMute() {
      const btn = document.getElementById('udemy-mute-btn');
      const cmp = window.PWD.components;
      window.PWD.isMuted = !window.PWD.isMuted;
      if (btn) {
        btn.innerHTML = window.PWD.isMuted ? cmp.icon('volumeX') : cmp.icon('volume2');
      }
      window.PWD.components.showToast(window.PWD.isMuted ? 'Đã tắt âm thanh' : 'Đã bật âm thanh', 'info');
    },

    handleScrubberClick(e) {
      const track = document.getElementById('udemy-scrubber');
      const fill = document.getElementById('udemy-scrubber-fill');
      if (track && fill) {
        const rect = track.getBoundingClientRect();
        const percent = Math.max(0, Math.min(100, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
        fill.style.width = percent + '%';
        window.PWD.components.showToast(`Chuyển đến ${percent}% thời lượng video`, 'info');
      }
    },

    toggleFullscreen() {
      const stage = document.getElementById('udemy-video-canvas');
      if (!stage) return;
      if (!document.fullscreenElement) {
        stage.requestFullscreen ? stage.requestFullscreen() : null;
        window.PWD.components.showToast('Đã vào chế độ toàn màn hình', 'info');
      } else {
        document.exitFullscreen ? document.exitFullscreen() : null;
      }
    },

    openRatingModal(courseId) {
      const modalHtml = `
        <div class="modal fade" id="udemy-rating-modal" tabindex="-1">
          <div class="modal-dialog modal-dialog-centered" style="max-width: 440px;">
            <div class="modal-content border-0 shadow-lg" style="border-radius: 12px; overflow:hidden;">
              <div class="modal-header border-0 bg-slate-900 text-white p-3">
                <h5 class="modal-title sub-title text-white m-0" style="font-size: 15px;">Đánh giá khóa học</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body p-4 text-center">
                <p class="text-caption text-muted mb-2">Trải nghiệm học tập của bạn thế nào?</p>
                <div class="fs-2 text-warning mb-3" style="cursor: pointer;">
                  <span onclick="this.parentElement.setAttribute('data-stars', 1)">⭐</span>
                  <span onclick="this.parentElement.setAttribute('data-stars', 2)">⭐</span>
                  <span onclick="this.parentElement.setAttribute('data-stars', 3)">⭐</span>
                  <span onclick="this.parentElement.setAttribute('data-stars', 4)">⭐</span>
                  <span onclick="this.parentElement.setAttribute('data-stars', 5)">⭐</span>
                </div>
                <textarea class="form-control form-control-sm" rows="3" placeholder="Chia sẻ cảm nhận chi tiết của bạn về khóa học..."></textarea>
              </div>
              <div class="modal-footer border-0 p-3 bg-slate-50">
                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Hủy</button>
                <button type="button" class="btn btn-primary btn-sm" data-bs-dismiss="modal" onclick="PWD.components.showToast('Cảm ơn bạn đã gửi đánh giá 5 sao!', 'success')">
                  Gửi đánh giá
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      let m = document.getElementById('udemy-rating-modal');
      if (m) m.remove();
      const div = document.createElement('div');
      div.innerHTML = modalHtml;
      document.body.appendChild(div.firstElementChild);
      const bsModal = new bootstrap.Modal(document.getElementById('udemy-rating-modal'));
      bsModal.show();
    },

    handleShareCourse(courseId) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(window.location.href);
      }
      window.PWD.components.showToast('Đã sao chép liên kết khóa học vào bộ nhớ tạm!', 'success');
    },

    handleSaveNote(courseId, lessonId) {
      const input = document.getElementById('udemy-note-input');
      const val = input ? input.value.trim() : '';
      if (!val) {
        window.PWD.components.showToast('Vui lòng nhập nội dung ghi chú.', 'danger');
        return;
      }
      const list = document.getElementById('udemy-saved-notes-list');
      if (list) {
        const item = document.createElement('div');
        item.className = 'list-group-item p-3';
        item.innerHTML = `
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge badge-primary">⏱ 02:15</span>
            <span class="text-caption text-muted">Vừa xong</span>
          </div>
          <div style="font-size: 13.5px;">${val}</div>
        `;
        list.prepend(item);
      }
      input.value = '';
      window.PWD.components.showToast('Đã lưu ghi chú học tập thành công!', 'success');
    },

    showLectureResourcesModal(lessonId) {
      const store = window.PWD.store.state;
      const lesson = store.lessons.find(l => l.id === lessonId);
      if (!lesson || !lesson.resources || !lesson.resources.length) return;

      const listHtml = lesson.resources.map(r => `
        <li class="list-group-item d-flex justify-content-between align-items-center px-3 py-2">
          <div>
            <div class="fw-medium" style="font-size: 13.5px;">${r.title}</div>
            <div class="text-caption text-muted">${r.size}</div>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mô phỏng tải xuống: ${r.title}', 'info')">
            Tải về
          </button>
        </li>
      `).join('');

      let m = document.getElementById('udemy-resources-modal');
      if (m) m.remove();
      const div = document.createElement('div');
      div.innerHTML = `
        <div class="modal fade" id="udemy-resources-modal" tabindex="-1">
          <div class="modal-dialog modal-dialog-centered" style="max-width: 440px;">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title sub-title m-0">Tài nguyên đính kèm bài học</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body p-0">
                <ul class="list-group list-group-flush">${listHtml}</ul>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(div.firstElementChild);
      const bsModal = new bootstrap.Modal(document.getElementById('udemy-resources-modal'));
      bsModal.show();
    },

    // 7. Lesson Resources
    lessonResources(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const allResources = [];
      store.lessons.forEach(l => {
        if (l.resources) {
          l.resources.forEach(r => allResources.push({ ...r, lessonTitle: l.title }));
        }
      });

      return `
        ${cmp.pageHeader({
          title: 'Tài nguyên Học tập — PWD301',
          subtitle: 'Tổng hợp tài liệu slide, bài tập mẫu và tệp tin đính kèm'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Tên tài liệu</th>
                  <th>Thuộc bài học</th>
                  <th>Dung lượng</th>
                  <th class="text-end">Tải về</th>
                </tr>
              </thead>
              <tbody>
                ${allResources.map(r => `
                  <tr>
                    <td>
                      <div class="d-flex align-items-center gap-2">
                        <span class="text-slate-400">${cmp.icon('fileText')}</span>
                        <span class="fw-medium">${r.title}</span>
                      </div>
                    </td>
                    <td class="text-caption text-muted">${r.lessonTitle}</td>
                    <td class="text-caption">${r.size}</td>
                    <td class="text-end">
                      <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mô phỏng tải xuống tệp: ${r.title}', 'info')">
                        Tải xuống
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 8. Progress
    progress(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const course = store.courses.find(c => c.id === (params.id || 'c1')) || store.courses[0];
      const lessons = store.lessons.filter(l => l.courseId === course.id);
      const completedCount = lessons.filter(l => l.completed).length;

      return `
        ${cmp.pageHeader({
          title: `Tiến độ học tập — ${course.code}`,
          subtitle: course.title,
          breadcrumbs: [
            { label: 'Khóa học của tôi', href: '#/student/my-learning' },
            { label: course.code, href: `#/student/course-dashboard/${course.id}` }
          ]
        })}

        <div class="row g-4 mb-4">
          <div class="col-md-4">
            ${cmp.statCard('Bài học hoàn thành', `${completedCount} / ${lessons.length}`, `${course.progress}% lộ trình`, 'checkCircle')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Điểm kiểm tra giữa kỳ', '10.0 / 10.0', 'Đạt yêu cầu môn', 'award')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Trạng thái hoàn thành', course.progress === 100 ? 'Đã hoàn thành' : 'Đang thực hiện', course.completionRule, 'clock')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h5 class="sub-title m-0">Chi tiết trạng thái từng bài giảng</h5>
          </div>
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Thứ tự</th>
                  <th>Tên bài học</th>
                  <th>Thời lượng</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                ${lessons.map((les, idx) => `
                  <tr>
                    <td>${idx + 1}</td>
                    <td class="fw-medium">${les.title}</td>
                    <td>${les.duration}</td>
                    <td>
                      ${les.completed ? cmp.badge('success', 'Đã hoàn thành') : cmp.badge('neutral', 'Chưa hoàn thành')}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 9. Assessments List
    assessments() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Bài kiểm tra & Đánh giá',
          subtitle: 'Danh sách các bài thi trắc nghiệm, bài tập lớn và kết quả điểm số'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Tên bài kiểm tra</th>
                  <th>Khóa học</th>
                  <th>Thời lượng</th>
                  <th>Hạn nộp</th>
                  <th>Trạng thái</th>
                  <th class="text-end">Hành động</th>
                </tr>
              </thead>
              <tbody>
                ${store.assessments.map(a => {
                  const course = store.courses.find(c => c.id === a.courseId);
                  const isSubmitted = store.results.some(r => r.assessmentId === a.id);
                  return `
                    <tr>
                      <td>
                        <div class="fw-medium">${a.title}</div>
                        <div class="text-caption text-muted">${a.totalPoints} điểm tối đa</div>
                      </td>
                      <td>${course ? course.code : a.courseId}</td>
                      <td>${a.durationMinutes} phút</td>
                      <td class="text-caption">${a.closeAt || 'Không giới hạn'}</td>
                      <td>
                        ${isSubmitted 
                          ? cmp.badge('success', 'Đã nộp bài') 
                          : a.status === 'published' 
                            ? cmp.badge('warning', 'Đang mở') 
                            : cmp.badge('neutral', a.status)}
                      </td>
                      <td class="text-end">
                        ${isSubmitted 
                          ? `<a href="#/student/result/att_completed_01" class="btn btn-secondary btn-sm">Xem kết quả</a>`
                          : `<a href="#/student/assessment-detail/${a.id}" class="btn btn-primary btn-sm">Bắt đầu</a>`}
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 10. Assessment Detail / Readiness
    assessmentDetail(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const assessment = store.assessments.find(a => a.id === params.id) || store.assessments[0];
      const course = store.courses.find(c => c.id === assessment.courseId) || store.courses[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: assessment.title,
            subtitle: `Môn học: ${course.code} — ${course.title}`,
            breadcrumbs: [
              { label: 'Bài kiểm tra', href: '#/student/assessments' },
              { label: 'Chi tiết bài thi', href: `#/student/assessment-detail/${assessment.id}` }
            ]
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Quy chế và thông số bài thi</h5>
            </div>
            <div class="card-body">
              <div class="row g-3 mb-4">
                <div class="col-sm-4">
                  <div class="text-caption text-muted">Thời gian làm bài</div>
                  <div class="fw-bold fs-5">${assessment.durationMinutes} phút</div>
                </div>
                <div class="col-sm-4">
                  <div class="text-caption text-muted">Số lượng câu hỏi</div>
                  <div class="fw-bold fs-5">${assessment.questionIds.length} câu hỏi</div>
                </div>
                <div class="col-sm-4">
                  <div class="text-caption text-muted">Số lần làm tối đa</div>
                  <div class="fw-bold fs-5">1 lần duy nhất</div>
                </div>
              </div>

              <div class="alert-card alert-card-warning">
                <span style="flex-shrink:0;">${cmp.icon('alertTriangle')}</span>
                <div>
                  <strong>Lưu ý quan trọng trước khi bắt đầu:</strong>
                  <ul class="m-0 mt-1 ps-3 text-caption" style="line-height: 1.6;">
                    <li>Hệ thống tự động lưu câu trả lời sau mỗi thao tác chọn hoặc nhập liệu.</li>
                    <li>Nếu mất kết nối mạng, các câu trả lời sẽ được lưu tạm tại trình duyệt và tự động đồng bộ khi có mạng trở lại.</li>
                    <li>Mỗi tài khoản chỉ được phép có 1 phiên làm bài hoạt động (Active Lease). Nếu mở bài thi ở thiết bị khác, phiên cũ sẽ bị khóa.</li>
                  </ul>
                </div>
              </div>

              <div class="text-center mt-4">
                <a href="#/student/attempt/${assessment.id}" class="btn btn-primary px-5">
                  Tôi đã sẵn sàng — Bắt đầu làm bài
                </a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 11. Assessment Attempt (Interactive Engine: Timer, Autosave, Offline, Lease - Scenarios 1, 3, 4)
    attempt(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const attempt = store.activeAttempt;
      const questions = store.questionBank.filter(q => ['q1', 'q2', 'q3', 'q4', 'q5'].includes(q.id));
      const currentQIndex = attempt.currentQuestionIndex || 0;
      const currentQ = questions[currentQIndex] || questions[0];

      // Format remaining time
      const mins = Math.floor(attempt.remainingSeconds / 60);
      const secs = attempt.remainingSeconds % 60;
      const timeStr = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

      const isLeaseLost = attempt.leaseState === 'lost';
      const isOffline = attempt.isOffline;

      const answeredCount = questions.filter(q => {
        const a = attempt.answers[q.id];
        return a && (Array.isArray(a) ? a.length > 0 : a.toString().trim().length > 0);
      }).length;
      const progressPct = Math.round((answeredCount / questions.length) * 100);

      return `
        <div class="content-wide">
          <!-- Top Sticky Simulation Controls for Demo -->
          <div class="d-flex justify-content-between align-items-center p-3 mb-4 bg-slate-100 border border-slate-300 rounded text-caption" style="border-radius: var(--radius-lg);">
            <div class="d-flex align-items-center gap-3">
              <span class="fw-bold text-slate-700">Mô phỏng trạng thái (Demo State):</span>
              
              <!-- Offline Simulation Toggle -->
              <button class="btn btn-sm ${isOffline ? 'btn-danger' : 'btn-secondary'}" onclick="PWD.views.student.toggleOfflineSimulation()">
                ${isOffline ? `${cmp.icon('wifiOff')} Đang mất mạng (Offline)` : `${cmp.icon('wifi')} Đang có mạng (Online)`}
              </button>

              <!-- Lease Simulation Toggle -->
              <button class="btn btn-sm ${isLeaseLost ? 'btn-danger' : 'btn-secondary'}" onclick="PWD.views.student.toggleLeaseSimulation()">
                ${isLeaseLost ? `${cmp.icon('lock')} Bị mất quyền (Lease Lost)` : `${cmp.icon('unlock')} Giữ quyền làm bài (Lease Active)`}
              </button>
            </div>

            <!-- Sync Status Indicator -->
            <div class="d-flex align-items-center gap-2">
              <span class="sync-status-indicator ${attempt.saveStatus}">
                ${attempt.saveStatus === 'saved' ? `✓ Đã tự động lưu` : attempt.saveStatus === 'saving' ? `Đang lưu...` : `⚠ Chưa đồng bộ (${attempt.unsyncedChangesCount})`}
              </span>
            </div>
          </div>

          <!-- Lease Lost Warning Banner (Scenario 4) -->
          ${isLeaseLost ? `
            <div class="alert-card alert-card-danger mb-4">
              <span style="flex-shrink:0;">${cmp.icon('lock')}</span>
              <div class="d-flex justify-content-between align-items-center w-100">
                <div>
                  <strong>Phiên làm bài đã bị chiếm bởi một thiết bị khác (Lease Lost):</strong>
                  <div class="text-caption mt-1">Biểu mẫu làm bài hiện bị khóa để bảo toàn dữ liệu. Bạn có thể yêu cầu chiếm lại phiên để tiếp tục.</div>
                </div>
                <button class="btn btn-danger btn-sm" onclick="PWD.store.takeoverAttemptLease(); PWD.router.handleRouting();">
                  Chiếm lại phiên (Takeover)
                </button>
              </div>
            </div>
          ` : ''}

          <!-- Offline Warning Banner (Scenario 3) -->
          ${isOffline ? `
            <div class="alert-card alert-card-warning mb-4">
              <span style="flex-shrink:0;">${cmp.icon('wifiOff')}</span>
              <div>
                <strong>Mất kết nối mạng (Offline Mode):</strong>
                <div class="text-caption mt-1">Các câu trả lời bạn chọn đang được ghi nhận vào bộ nhớ tạm trình duyệt. Vui lòng không đóng tab. Khi mạng hoạt động trở lại, hệ thống sẽ tự động gửi lên máy chủ.</div>
              </div>
            </div>
          ` : ''}

          <!-- Visual Multi-step Stepper Header -->
          <div class="card mb-4">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center gap-2">
                  <span class="badge badge-primary" style="font-size: 13px; padding: 5px 12px;">Câu ${currentQIndex + 1} / ${questions.length}</span>
                  <span class="text-caption text-muted">Chủ đề: <strong>${currentQ.topic}</strong></span>
                  <span class="badge badge-neutral">${currentQ.points} điểm</span>
                </div>
                <span class="fw-semibold text-muted" style="font-size: 13px;">Đã trả lời ${answeredCount} / ${questions.length} câu (${progressPct}%)</span>
              </div>
              ${cmp.progressBar(progressPct)}
            </div>
          </div>

          <div class="attempt-shell">
            <!-- Left: Question Presentation -->
            <div>
              <div class="attempt-question-card">
                <div class="attempt-question-stem fw-semibold mb-4" style="font-size: 1.15rem; line-height: 1.6;">
                  ${currentQ.stem}
                </div>

                <fieldset ${isLeaseLost ? 'disabled' : ''}>
                  <!-- Single Choice MCQ -->
                  ${currentQ.type === 'single_choice' ? `
                    <div class="options-list d-flex flex-column gap-3">
                      ${currentQ.options.map(opt => {
                        const isSelected = attempt.answers[currentQ.id] === opt.id;
                        return `
                          <label class="attempt-option-label ${isSelected ? 'selected' : ''}" onclick="PWD.views.student.handleAnswerChoice('${currentQ.id}', '${opt.id}')">
                            <input type="radio" name="${currentQ.id}" value="${opt.id}" ${isSelected ? 'checked' : ''}>
                            <span class="ms-2">${opt.text}</span>
                          </label>
                        `;
                      }).join('')}
                    </div>
                  ` : ''}

                  <!-- Multi Select -->
                  ${currentQ.type === 'multi_select' ? `
                    <div class="options-list d-flex flex-column gap-3">
                      <div class="text-caption text-muted mb-2">Chọn tất cả đáp án đúng:</div>
                      ${currentQ.options.map(opt => {
                        const selectedList = attempt.answers[currentQ.id] || [];
                        const isSelected = selectedList.includes(opt.id);
                        return `
                          <label class="attempt-option-label ${isSelected ? 'selected' : ''}" onclick="PWD.views.student.handleMultiSelectChoice('${currentQ.id}', '${opt.id}')">
                            <input type="checkbox" name="${currentQ.id}" value="${opt.id}" ${isSelected ? 'checked' : ''}>
                            <span class="ms-2">${opt.text}</span>
                          </label>
                        `;
                      }).join('')}
                    </div>
                  ` : ''}

                  <!-- Short Answer -->
                  ${currentQ.type === 'short_answer' ? `
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Câu trả lời ngắn của bạn:</label>
                      <input type="text" class="form-control" style="font-size: 15px; padding: 12px 16px;" placeholder="Gõ câu trả lời..." value="${attempt.answers[currentQ.id] || ''}" oninput="PWD.views.student.handleTextAnswer('${currentQ.id}', this.value)">
                      <div class="form-hint mt-2">Nhập chính xác từ khóa ngắn hoặc câu lệnh.</div>
                    </div>
                  ` : ''}

                  <!-- Essay -->
                  ${currentQ.type === 'essay' ? `
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Nội dung bài luận:</label>
                      <textarea class="form-control" rows="8" style="font-size: 15px; padding: 14px 16px; line-height: 1.6;" placeholder="Trình bày chi tiết quan điểm và phân tích..." oninput="PWD.views.student.handleTextAnswer('${currentQ.id}', this.value)">${attempt.answers[currentQ.id] || ''}</textarea>
                      <div class="form-hint mt-2">Bài luận sẽ được giảng viên chấm điểm thủ công sau khi bạn nộp bài.</div>
                    </div>
                  ` : ''}
                </fieldset>

                <div class="d-flex justify-content-between mt-4 pt-3 border-top">
                  <button class="btn btn-secondary px-3 py-2" ${currentQIndex === 0 ? 'disabled' : ''} onclick="PWD.views.student.navigateQuestion(${currentQIndex - 1})">
                    ← Câu trước
                  </button>
                  <button class="btn btn-primary px-3 py-2" ${currentQIndex === questions.length - 1 ? 'disabled' : ''} onclick="PWD.views.student.navigateQuestion(${currentQIndex + 1})">
                    Câu tiếp theo →
                  </button>
                </div>
              </div>
            </div>

            <!-- Right Panel: Timer & Question Navigation Matrix -->
            <div>
              <div class="card mb-4">
                <div class="card-body text-center p-4">
                  <div class="text-caption text-muted mb-2 text-uppercase fw-semibold" style="letter-spacing: 0.5px;">Thời gian còn lại</div>
                  <div class="fw-bold fs-2" style="color: var(--color-amber); font-feature-settings: 'tnum';" id="attempt-timer-display">${timeStr}</div>
                  <div class="text-caption text-muted mt-2">Hệ thống tự động lưu bài làm</div>
                </div>
              </div>

              <div class="card mb-4">
                <div class="card-header py-3 px-4 d-flex justify-content-between align-items-center">
                  <h5 class="sub-title m-0" style="font-size: 14px;">Bảng câu hỏi</h5>
                  <span class="badge badge-neutral">${questions.length} câu</span>
                </div>
                <div class="card-body p-4">
                  <div class="question-nav-grid" style="gap: 8px;">
                    ${questions.map((q, idx) => {
                      const ans = attempt.answers[q.id];
                      const isAnswered = ans && (Array.isArray(ans) ? ans.length > 0 : ans.toString().trim().length > 0);
                      const isActive = idx === currentQIndex;
                      let cls = 'q-nav-btn';
                      if (isActive) cls += ' active';
                      else if (isAnswered) cls += ' answered';

                      return `
                        <button class="${cls}" onclick="PWD.views.student.navigateQuestion(${idx})">
                          ${idx + 1}
                        </button>
                      `;
                    }).join('')}
                  </div>
                </div>
              </div>

              <button class="btn btn-primary w-100 py-2 fw-semibold" style="box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25); border-radius: var(--radius-md);" onclick="PWD.views.student.confirmSubmit()">
                Nộp bài thi chính thức
              </button>
            </div>
          </div>
        </div>
      `;
    },

    navigateQuestion(newIndex) {
      window.PWD.store.state.activeAttempt.currentQuestionIndex = newIndex;
      window.PWD.store.persist();
      window.PWD.router.handleRouting();
    },

    handleAnswerChoice(qId, optId) {
      if (window.PWD.store.state.activeAttempt.leaseState === 'lost') return;
      window.PWD.store.saveAttemptAnswer(qId, optId);
      window.PWD.router.handleRouting();
    },

    handleMultiSelectChoice(qId, optId) {
      if (window.PWD.store.state.activeAttempt.leaseState === 'lost') return;
      const current = window.PWD.store.state.activeAttempt.answers[qId] || [];
      const updated = current.includes(optId) ? current.filter(x => x !== optId) : [...current, optId];
      window.PWD.store.saveAttemptAnswer(qId, updated);
      window.PWD.router.handleRouting();
    },

    handleTextAnswer(qId, text) {
      if (window.PWD.store.state.activeAttempt.leaseState === 'lost') return;
      window.PWD.store.saveAttemptAnswer(qId, text);
    },

    toggleOfflineSimulation() {
      window.PWD.store.toggleAttemptOffline();
      window.PWD.router.handleRouting();
    },

    toggleLeaseSimulation() {
      const current = window.PWD.store.state.activeAttempt.leaseState;
      const next = current === 'owner' ? 'lost' : 'owner';
      window.PWD.store.setAttemptLeaseState(next);
      window.PWD.router.handleRouting();
    },

    confirmSubmit() {
      window.PWD.components.openConfirmModal({
        title: 'Nộp bài thi chính thức',
        message: `Bạn có chắc chắn muốn nộp bài thi? Sau khi nộp, bạn sẽ không thể chỉnh sửa lại các câu trả lời.`,
        confirmText: 'Xác nhận nộp bài',
        confirmBtnClass: 'btn-primary',
        onConfirm: () => {
          window.PWD.store.submitAttempt();
          window.PWD.components.showToast('Nộp bài thi thành công!', 'success');
          window.PWD.router.navigate('#/student/attempt-submitted/a1');
        }
      });
    },

    // 12. Assessment Submitted / Pending Grading
    submitted(params) {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow text-center py-5">
          <div class="mb-3 text-success">${cmp.icon('checkCircle')}</div>
          <h2 class="page-title mb-2">Đã nộp bài thi thành công!</h2>
          <p class="text-slate-600 mb-4" style="max-width: 520px; margin: 0 auto;">
            Bài làm của bạn cho <strong>Kiểm tra giữa kỳ — Lập trình Web Flask</strong> đã được ghi nhận vào hệ thống.
          </p>

          <div class="card mb-4 text-start">
            <div class="card-body p-4">
              <div class="alert-card alert-card-info mb-3">
                <span style="flex-shrink:0;">${cmp.icon('clock')}</span>
                <div>
                  <strong>Thông báo chấm bài tự luận:</strong>
                  <div class="text-caption mt-1">Đề thi có chứa 01 câu hỏi tự luận (Câu 5). Điểm tổng kết sẽ được công bố sau khi Giảng viên hoàn tất chấm điểm bài làm của bạn.</div>
                </div>
              </div>
              <div class="d-flex justify-content-between py-2 border-bottom border-slate-200 text-caption">
                <span class="text-muted">Mã phiên làm bài:</span>
                <span class="font-monospace">att_2026_901</span>
              </div>
              <div class="d-flex justify-content-between py-2 text-caption">
                <span class="text-muted">Thời điểm nộp:</span>
                <span>${new Date().toLocaleTimeString()} • 08/09/2026</span>
              </div>
            </div>
          </div>

          <div class="d-flex justify-content-center gap-3">
            <a href="#/student/dashboard" class="btn btn-primary btn-sm">Về trang chủ học tập</a>
            <a href="#/student/assessments" class="btn btn-secondary btn-sm">Xem danh sách bài thi</a>
          </div>
        </div>
      `;
    },

    // 13. Assessment Result
    result(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const res = store.results[0]; // Completed practice quiz

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Kết quả Bài thực hành 01',
            subtitle: 'Môn học: PWD301 • Đã chấm điểm ngày 28/08/2026',
            breadcrumbs: [
              { label: 'Bài kiểm tra', href: '#/student/assessments' },
              { label: 'Kết quả', href: '#/student/result/att_completed_01' }
            ],
            primaryAction: `<a href="#/student/score-history/att_completed_01" class="btn btn-secondary btn-sm">Lịch sử điều chỉnh điểm</a>`
          })}

          <div class="card mb-4 text-center p-4">
            <div class="text-caption text-muted">Điểm tổng kết chính thức</div>
            <div class="fw-bold text-success my-2" style="font-size: 3rem; line-height: 1;">10.0 <span class="text-muted fs-5">/ 10.0</span></div>
            <div class="text-caption text-slate-600">Đánh giá: Xuất sắc • Đạt tối đa điểm chuyên cần và thực hành.</div>
          </div>

          <div class="card">
            <div class="card-header">
              <h5 class="sub-title m-0">Chi tiết câu trả lời</h5>
            </div>
            <div class="card-body p-0">
              <ul class="list-group list-group-flush">
                <li class="list-group-item p-4">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="fw-medium">Câu 1: Application Factory Pattern</span>
                    <span class="badge badge-success">5.0 / 5.0 điểm</span>
                  </div>
                  <p class="text-caption text-muted mb-2">Mẫu thiết kế nào được khuyến nghị để khởi tạo Flask App...</p>
                  <div class="text-caption text-success">✓ Câu trả lời của bạn: Application Factory Pattern (Chính xác)</div>
                </li>
                <li class="list-group-item p-4">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="fw-medium">Câu 2: Jinja2 Layout Inheritance</span>
                    <span class="badge badge-success">5.0 / 5.0 điểm</span>
                  </div>
                  <p class="text-caption text-muted mb-2">Từ khóa nào được sử dụng để kế thừa template...</p>
                  <div class="text-caption text-success">✓ Câu trả lời của bạn: extends (Chính xác)</div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      `;
    },

    // 14. Score History / Regrade History
    scoreHistory(params) {
      const cmp = window.PWD.components;
      const res = window.PWD.store.state.results[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Lịch sử Điều chỉnh Điểm số (Score Audit)',
            subtitle: 'Bản ghi lịch sử các lần chấm và phúc khảo điểm bài kiểm tra',
            breadcrumbs: [
              { label: 'Bài kiểm tra', href: '#/student/assessments' },
              { label: 'Kết quả', href: '#/student/result/att_completed_01' },
              { label: 'Lịch sử điểm', href: '#/student/score-history/att_completed_01' }
            ]
          })}

          <div class="card">
            <div class="card-header">
              <h5 class="sub-title m-0">Tiến trình thay đổi điểm (Audit Trail)</h5>
            </div>
            <div class="card-body p-0">
              <ul class="list-group list-group-flush">
                ${res.regradeHistory.map(h => `
                  <li class="list-group-item p-4">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                      <span class="fw-bold fs-6">Phiên bản v${h.version}: ${h.score} điểm</span>
                      <span class="text-caption text-muted">${h.timestamp}</span>
                    </div>
                    <div class="text-caption text-slate-700 mb-1"><strong>Người thực hiện:</strong> ${h.actor}</div>
                    <div class="text-caption text-slate-600"><strong>Lý do điều chỉnh:</strong> ${h.reason}</div>
                  </li>
                `).join('')}
              </ul>
            </div>
          </div>
        </div>
      `;
    },

    // 15. AI Assistant View
    aiAssistant() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Trợ lý Học tập AI',
          subtitle: 'Hỏi đáp bài giảng có trích dẫn nguồn gốc tài liệu khóa học PWD301'
        })}

        <div class="row g-4">
          <div class="col-lg-8">
            <div class="card d-flex flex-column border-0" style="height: 560px; box-shadow: var(--shadow-sm); border-radius: var(--radius-xl); overflow: hidden;">
              <div class="card-header d-flex justify-content-between align-items-center py-3 px-4 bg-white border-bottom border-slate-100">
                <div class="d-flex align-items-center gap-2">
                  ${cmp.iconBox('sparkles', 'violet')}
                  <span class="sub-title m-0 fw-semibold" style="color: var(--slate-900);">Hội thoại học tập thông minh</span>
                </div>
                <span class="badge badge-neutral" style="font-size: 11px;">Bảo mật: Phiên tự hủy sau 5p</span>
              </div>
              <div class="card-body flex-grow-1 overflow-auto p-4" id="ai-chat-messages" style="background: linear-gradient(180deg, #fbfcfe 0%, #f8fafc 100%);">
                <!-- Assistant Greeting -->
                <div class="d-flex gap-3 mb-4">
                  <div class="icon-box icon-box-violet" style="width: 36px; height: 36px; border-radius: var(--radius-md); font-size: 14px;">${cmp.icon('sparkles')}</div>
                  <div class="p-3 bg-white border border-slate-200 rounded-3" style="max-width: 82%; box-shadow: var(--shadow-sm);">
                    <p class="m-0" style="font-size: 14px; line-height: 1.6; color: var(--slate-800);">Xin chào Minh Anh! Mình là Trợ lý AI của môn học PWD301. Bạn có thắc mắc gì về bài học hoặc tài liệu nào hôm nay không?</p>
                  </div>
                </div>

                <!-- Sample Q&A -->
                <div class="d-flex gap-3 mb-4 justify-content-end">
                  <div class="p-3 text-white rounded-3" style="max-width: 82%; background: var(--brand-primary); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);">
                    <p class="m-0" style="font-size: 14px; line-height: 1.6;">Tại sao trong Cookie phiên làm việc luôn bắt buộc phải có cờ HttpOnly?</p>
                  </div>
                  <div class="topbar-brand-mark" style="background: var(--slate-700); width: 36px; height: 36px; border-radius: var(--radius-md); font-size: 12px;">MA</div>
                </div>

                <div class="d-flex gap-3 mb-4">
                  <div class="icon-box icon-box-violet" style="width: 36px; height: 36px; border-radius: var(--radius-md); font-size: 14px;">${cmp.icon('sparkles')}</div>
                  <div class="p-3 bg-white border border-slate-200 rounded-3" style="max-width: 82%; box-shadow: var(--shadow-sm);">
                    <p class="mb-2" style="font-size: 14px; line-height: 1.6; color: var(--slate-800);">
                      Thuộc tính <code>HttpOnly</code> giúp ngăn chặn JavaScript phía client (như mã độc XSS) truy cập vào Cookie thông qua lệnh <code>document.cookie</code>. Nếu tin tặc chèn được mã độc vào website, chúng cũng không thể đánh cắp Cookie phiên này.
                    </p>
                    <div class="text-caption text-muted pt-2 border-top border-slate-100" style="font-size: 12px;">
                      📖 <strong>Nguồn trích dẫn:</strong> Bài 1: Giao thức HTTP & Quản lý phiên (Slide trang 12).
                    </div>
                  </div>
                </div>
              </div>

              <div class="card-footer bg-white border-top border-slate-200 p-3 px-4">
                <form onsubmit="event.preventDefault(); PWD.views.student.sendAIMessage();" class="d-flex gap-2">
                  <input type="text" id="ai-input" class="form-control" style="font-size: 14px; padding: 10px 16px; border-radius: var(--radius-md);" placeholder="Nhập câu hỏi liên quan đến nội dung môn học...">
                  <button type="submit" class="btn btn-primary px-4 fw-medium" style="border-radius: var(--radius-md);">Gửi</button>
                </form>
              </div>
            </div>
          </div>

          <div class="col-lg-4">
            <div class="card border-0" style="box-shadow: var(--shadow-sm); border-radius: var(--radius-xl);">
              <div class="card-header bg-transparent py-3 px-4 border-bottom border-slate-100">
                <h5 class="sub-title m-0" style="font-size: 14px;">Gợi ý câu hỏi phổ biến</h5>
              </div>
              <div class="card-body p-4">
                <div class="d-grid gap-2">
                  <button class="btn btn-secondary text-start p-3" style="border-radius: var(--radius-md); font-size: 13px; line-height: 1.5;" onclick="PWD.views.student.fillAIInput('CSRF Token hoạt động thế nào trong Flask-WTF?')">
                    💡 CSRF Token hoạt động thế nào?
                  </button>
                  <button class="btn btn-secondary text-start p-3" style="border-radius: var(--radius-md); font-size: 13px; line-height: 1.5;" onclick="PWD.views.student.fillAIInput('Sự khác biệt giữa HTTP GET và POST?')">
                    💡 Phân biệt HTTP GET và POST?
                  </button>
                  <button class="btn btn-secondary text-start p-3" style="border-radius: var(--radius-md); font-size: 13px; line-height: 1.5;" onclick="PWD.views.student.fillAIInput('Cấu trúc thư mục chuẩn của dự án Flask Blueprint?')">
                    💡 Cấu trúc chuẩn Flask Blueprint?
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    fillAIInput(text) {
      const input = document.getElementById('ai-input');
      if (input) input.value = text;
    },

    sendAIMessage() {
      const input = document.getElementById('ai-input');
      const val = (input?.value || '').trim();
      if (!val) return;

      const container = document.getElementById('ai-chat-messages');
      if (!container) return;

      // Add user message
      const userDiv = document.createElement('div');
      userDiv.className = 'd-flex gap-3 mb-4 justify-content-end';
      userDiv.innerHTML = `
        <div class="p-3 text-white rounded" style="max-width: 80%; background: var(--brand-primary) !important;">
          <p class="m-0" style="font-size: 14px;">${val}</p>
        </div>
        <div class="topbar-brand-mark" style="background: var(--slate-700);">MA</div>
      `;
      container.appendChild(userDiv);
      input.value = '';

      // Simulated AI reply
      setTimeout(() => {
        const aiDiv = document.createElement('div');
        aiDiv.className = 'd-flex gap-3 mb-4';
        aiDiv.innerHTML = `
          <div class="topbar-brand-mark" style="background: var(--brand-primary);">${window.PWD.components.icon('sparkles')}</div>
          <div class="p-3 bg-white border border-slate-200 rounded" style="max-width: 80%;">
            <p class="mb-2" style="font-size: 14px;">
              Về câu hỏi "<strong>${val}</strong>": Trong giáo trình môn PWD301, nội dung này được giảng viên nhấn mạnh trong phần bảo mật và kiến trúc mô đun ứng dụng. Bạn có thể xem thêm trong tài liệu PDF đính kèm tại Bài 4.
            </p>
            <div class="text-caption text-muted pt-2 border-top border-slate-200">
              📖 <strong>Nguồn trích dẫn:</strong> PWD301 Syllabus & Form_Validation_Security_Rules.pdf.
            </div>
          </div>
        `;
        container.appendChild(aiDiv);
        container.scrollTop = container.scrollHeight;
      }, 500);

      container.scrollTop = container.scrollHeight;
    },

    // 16. Course Recommendations
    recommendations() {
      const cmp = window.PWD.components;
      const store = window.PWD.store.state;

      return `
        ${cmp.pageHeader({
          title: 'Gợi ý Học tập Tiếp theo',
          subtitle: 'Đề xuất dựa trên các môn bạn đã hoàn thành (HTML/CSS) và mục tiêu chuyên ngành'
        })}

        <div class="row g-4">
          <div class="col-md-6">
            <div class="card h-100">
              <div class="card-body">
                <span class="badge badge-success mb-2">Được đề xuất cao nhất</span>
                <h4 class="sub-title">Lập trình RESTful API An toàn với JWT & OAuth2</h4>
                <p class="text-caption text-muted mb-3">Môn học tiếp nối hoàn hảo cho học viên đang theo học PWD301 để nâng cao năng lực bảo mật ứng dụng web.</p>
                <a href="#/student/course/c6" class="btn btn-secondary btn-sm">Xem chi tiết khóa học</a>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card h-100">
              <div class="card-body">
                <span class="badge badge-info mb-2">Đề xuất chuyên ngành</span>
                <h4 class="sub-title">Trí tuệ Nhân tạo Ứng dụng & RAG Pipeline</h4>
                <p class="text-caption text-muted mb-3">Tích hợp mô hình AI ngôn ngữ lớn vào ứng dụng web hiện đại.</p>
                <a href="#/student/course/c7" class="btn btn-secondary btn-sm">Xem chi tiết khóa học</a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 17. Notifications Center
    notifications() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Trung tâm Thông báo',
          subtitle: 'Các cập nhật về khóa học, bài thi và hoạt động tài khoản',
          primaryAction: `<button class="btn btn-secondary btn-sm" onclick="PWD.views.student.markAllNotificationsRead()">Đánh dấu tất cả đã đọc</button>`
        })}

        <div class="card">
          <div class="card-body p-0">
            <ul class="list-group list-group-flush">
              ${store.notifications.map(n => `
                <li class="list-group-item p-4 d-flex justify-content-between align-items-start ${n.read ? '' : 'bg-slate-50'}">
                  <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                      ${n.read ? '' : `<span class="badge-dot" style="background: var(--brand-primary); width: 8px; height: 8px;"></span>`}
                      <span class="fw-semibold text-slate-900">${n.title}</span>
                    </div>
                    <p class="text-caption text-slate-600 m-0">${n.body}</p>
                  </div>
                  <span class="text-caption text-muted">${n.time}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      `;
    },

    markAllNotificationsRead() {
      window.PWD.store.state.notifications.forEach(n => n.read = true);
      window.PWD.store.persist();
      if (window.PWD.app && window.PWD.app.updateNotificationBadge) {
        window.PWD.app.updateNotificationBadge();
        window.PWD.app.renderNotificationList();
      }
      window.PWD.components.showToast('Đã đánh dấu đọc tất cả thông báo.', 'info');
      window.PWD.router.handleRouting();
    },

    // 18. Profile & Preferences
    profile() {
      const user = window.PWD.store.getCurrentUser() || window.PWD.store.state.personas.student;
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Hồ sơ Sinh viên',
            subtitle: 'Thông tin cá nhân và tùy chọn tài khoản'
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Thông tin cá nhân</h5>
            </div>
            <div class="card-body">
              <div class="d-flex align-items-center gap-3 mb-4">
                <div class="topbar-brand-mark fs-4" style="width: 54px; height: 54px;">${user.avatar}</div>
                <div>
                  <h4 class="sub-title m-0">${user.name}</h4>
                  <div class="text-caption text-muted">${user.email} • Vai trò: ${user.role}</div>
                </div>
              </div>

              <div class="form-group mb-3">
                <label class="form-label">Họ và tên</label>
                <input type="text" class="form-control form-control-sm" value="${user.name}" readonly>
              </div>
              <div class="form-group mb-3">
                <label class="form-label">Email học viên</label>
                <input type="email" class="form-control form-control-sm" value="${user.email}" readonly>
              </div>
              <div class="form-group mb-0">
                <label class="form-label">Mã số sinh viên (Demo)</label>
                <input type="text" class="form-control form-control-sm" value="SV2026-9812" readonly>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  };

  window.PWD.views.student = studentViews;
})();
