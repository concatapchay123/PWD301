/**
 * PWD301 — Instructor Views
 * Course Authoring, Question Bank, Assessment Builder, AI Generator, Essay Grading
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};
  window.PWD.views = window.PWD.views || {};

  const instructorViews = {
    // 1. Instructor Dashboard
    dashboard() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const myCourses = store.courses.filter(c => c.instructorId === 'u_instructor');

      return `
        ${cmp.heroWelcome(
          'Chào mừng trở lại, Thầy Nam! 👨‍🏫',
          'Quản lý giảng dạy, chấm điểm tự luận và thiết lập kỳ thi chuẩn đầu ra môn học PWD301.',
          `<a href="#/instructor/course-editor/new" class="btn btn-light fw-semibold px-3 py-2" style="color: #1e3a8a; border-radius: var(--radius-md); box-shadow: 0 4px 12px rgba(0,0,0,0.1);">+ Tạo khóa học mới</a>`
        )}

        <div class="row g-4 mb-4">
          <div class="col-md-4">
            ${cmp.statCard('Khóa học quản lý', myCourses.length, '1 Published, 1 Draft, 1 Chờ duyệt', 'book', 'primary')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Bài tự luận cần chấm', '1 bài', 'Học viên: Nguyễn Minh Anh', 'edit', 'rose')}
          </div>
          <div class="col-md-4">
            ${cmp.statCard('Ngân hàng câu hỏi', store.questionBank.length, 'Đã cập nhật 28 câu hỏi', 'database', 'violet')}
          </div>
        </div>

        <div class="row g-4">
          <div class="col-lg-8">
            <div class="card mb-4">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Khóa học đang phụ trách</h5>
                <a href="#/instructor/courses" class="text-caption text-decoration-none">Quản lý tất cả →</a>
              </div>
              <div class="card-body p-0">
                <table class="app-table">
                  <thead>
                    <tr>
                      <th>Khóa học</th>
                      <th>Sĩ số</th>
                      <th>Trạng thái</th>
                      <th class="text-end">Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${myCourses.map(c => `
                      <tr>
                        <td>
                          <div class="fw-medium">${c.title}</div>
                          <div class="text-caption text-muted">${c.code} • ${c.lessonsCount} bài học</div>
                        </td>
                        <td>${c.enrolledCount} / ${c.capacity}</td>
                        <td>
                          ${c.status === 'published' ? cmp.badge('success', 'Đã xuất bản') : c.status === 'draft' ? cmp.badge('neutral', 'Bản nháp') : cmp.badge('warning', 'Chờ Admin duyệt')}
                        </td>
                        <td class="text-end">
                          <a href="#/instructor/curriculum/${c.id}" class="btn btn-secondary btn-sm">Chương trình</a>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Task needing attention: Pending Essay Grading -->
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="sub-title m-0">Công việc cần xử lý ngay</h5>
                <span class="badge badge-danger">1 bài chờ chấm</span>
              </div>
              <div class="card-body">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded d-flex justify-content-between align-items-center">
                  <div>
                    <div class="fw-medium text-slate-900">Bài tập Lớn — Thiết kế Kiến trúc Hệ thống</div>
                    <div class="text-caption text-muted">Học viên: Nguyễn Minh Anh • Nộp lúc 10:20 ngày 05/09/2026</div>
                  </div>
                  <a href="#/instructor/grade-editor/att_pending_02" class="btn btn-primary btn-sm">Chấm bài ngay</a>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-4">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="sub-title m-0">Lối tắt tác vụ nhanh</h5>
              </div>
              <div class="card-body">
                <div class="d-grid gap-2">
                  <a href="#/instructor/questions" class="btn btn-secondary btn-sm text-start">
                    • Ngân hàng câu hỏi (${store.questionBank.length} câu)
                  </a>
                  <a href="#/instructor/import" class="btn btn-secondary btn-sm text-start">
                    • Import đề thi từ DOCX/PDF
                  </a>
                  <a href="#/instructor/ai-generator" class="btn btn-secondary btn-sm text-start">
                    • AI sinh câu hỏi trắc nghiệm
                  </a>
                  <a href="#/instructor/assessments" class="btn btn-secondary btn-sm text-start">
                    • Quản lý bài kiểm tra & Đề thi
                  </a>
                  <a href="#/instructor/export" class="btn btn-secondary btn-sm text-start">
                    • Xuất bảng điểm môn học
                  </a>
                </div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h5 class="sub-title m-0">Góc nhìn Sinh viên</h5>
              </div>
              <div class="card-body">
                <p class="text-caption text-muted mb-3">Xem trước giao diện khóa học dưới góc nhìn học viên để kiểm tra trải nghiệm.</p>
                <button onclick="PWD.app.switchPerspective('student'); PWD.router.navigate('#/student/dashboard');" class="btn btn-secondary btn-sm w-100">
                  Chuyển sang góc nhìn Sinh viên
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 2. My Courses
    courses() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const myCourses = store.courses.filter(c => c.instructorId === 'u_instructor');

      return `
        ${cmp.pageHeader({
          title: 'Khóa học Giảng dạy',
          subtitle: 'Danh sách các khóa học bạn phụ trách nội dung và kiểm tra',
          primaryAction: `<a href="#/instructor/course-editor/new" class="btn btn-primary btn-sm">+ Tạo khóa học mới</a>`
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Mã môn</th>
                  <th>Tên khóa học</th>
                  <th>Phân môn</th>
                  <th>Sĩ số</th>
                  <th>Trạng thái</th>
                  <th class="text-end">Hành động</th>
                </tr>
              </thead>
              <tbody>
                ${myCourses.map(c => `
                  <tr>
                    <td class="fw-bold">${c.code}</td>
                    <td>
                      <div class="fw-medium">${c.title}</div>
                      <div class="text-caption text-muted">${c.lessonsCount} bài giảng</div>
                    </td>
                    <td>${c.category}</td>
                    <td>${c.enrolledCount} / ${c.capacity}</td>
                    <td>
                      ${c.status === 'published' ? cmp.badge('success', 'Đã xuất bản') : c.status === 'draft' ? cmp.badge('neutral', 'Bản nháp') : cmp.badge('warning', 'Chờ duyệt thay đổi')}
                    </td>
                    <td class="text-end">
                      <div class="table-actions">
                        <a href="#/instructor/curriculum/${c.id}" class="btn btn-secondary btn-sm" title="Quản lý bài học">Bài giảng</a>
                        <a href="#/instructor/course-editor/${c.id}" class="btn btn-ghost btn-sm" title="Sửa thông tin">${cmp.icon('edit')}</a>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 3. Course Editor
    courseEditor(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const isNew = params.id === 'new';
      const course = isNew ? { code: '', title: '', category: 'Phát triển Web', capacity: 50, completionRule: '', description: '', status: 'draft' } : store.courses.find(c => c.id === params.id) || store.courses[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: isNew ? 'Tạo Khóa học mới' : `Chỉnh sửa: ${course.code}`,
            subtitle: 'Thiết lập thông tin môn học và quy chuẩn hoàn thành',
            breadcrumbs: [
              { label: 'Khóa học của tôi', href: '#/instructor/courses' },
              { label: isNew ? 'Tạo mới' : course.code, href: `#/instructor/course-editor/${course.id}` }
            ]
          })}

          ${!isNew && course.status === 'published' ? `
            <div class="alert-card alert-card-warning mb-4">
              <span style="flex-shrink:0;">${cmp.icon('alertTriangle')}</span>
              <div>
                <strong>Lưu ý về thay đổi tài liệu khóa học đã xuất bản:</strong>
                <div class="text-caption mt-1">Các chỉnh sửa lớn về đề cương và quy chuẩn đánh giá sẽ được chuyển sang trạng thái "Chờ Admin phê duyệt" trước khi áp dụng chính thức cho học viên.</div>
              </div>
            </div>
          ` : ''}

          <div class="card">
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.views.instructor.saveCourse('${course.id}');">
                <div class="row g-3 mb-3">
                  <div class="col-md-4">
                    <label class="form-label">Mã khóa học <span class="required">*</span></label>
                    <input type="text" id="course-code" class="form-control form-control-sm" value="${course.code}" required placeholder="Ví dụ: PWD301">
                  </div>
                  <div class="col-md-8">
                    <label class="form-label">Tên khóa học <span class="required">*</span></label>
                    <input type="text" id="course-title" class="form-control form-control-sm" value="${course.title}" required placeholder="Ví dụ: Lập trình Web với Python">
                  </div>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-md-6">
                    <label class="form-label">Phân loại chuyên môn</label>
                    <select id="course-cat" class="form-select form-select-sm">
                      <option ${course.category === 'Phát triển Web' ? 'selected' : ''}>Phát triển Web</option>
                      <option ${course.category === 'Frontend' ? 'selected' : ''}>Frontend</option>
                      <option ${course.category === 'Dữ liệu' ? 'selected' : ''}>Dữ liệu</option>
                      <option ${course.category === 'Bảo mật' ? 'selected' : ''}>Bảo mật</option>
                      <option ${course.category === 'Hệ thống' ? 'selected' : ''}>Hệ thống</option>
                    </select>
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">Giới hạn sĩ số (Capacity)</label>
                    <input type="number" id="course-cap" class="form-control form-control-sm" value="${course.capacity}">
                  </div>
                </div>

                <div class="form-group mb-3">
                  <label class="form-label">Mô tả tóm tắt môn học</label>
                  <textarea id="course-desc" class="form-control form-control-sm" rows="3">${course.description}</textarea>
                </div>

                <div class="form-group mb-4">
                  <label class="form-label">Quy chuẩn hoàn thành môn (Completion Rule)</label>
                  <input type="text" id="course-rule" class="form-control form-control-sm" value="${course.completionRule}">
                  <div class="form-hint">Quy định điều kiện sinh viên hoàn tất môn và được cấp chứng chỉ.</div>
                </div>

                <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                  <a href="#/instructor/courses" class="btn btn-secondary btn-sm">Hủy bỏ</a>
                  <button type="submit" class="btn btn-primary btn-sm">Lưu thông tin khóa học</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    saveCourse(courseId) {
      window.PWD.components.showToast('Đã lưu thông tin khóa học thành công!', 'success');
      window.PWD.router.navigate('#/instructor/courses');
    },

    // 4. Curriculum & Lesson Ordering (Scenario 5)
    curriculum(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const course = store.courses.find(c => c.id === params.id) || store.courses[0];
      const lessons = store.lessons.filter(l => l.courseId === course.id);

      return `
        ${cmp.pageHeader({
          title: `Khung chương trình: ${course.code}`,
          subtitle: course.title,
          breadcrumbs: [
            { label: 'Khóa học', href: '#/instructor/courses' },
            { label: 'Chương trình đào tạo', href: `#/instructor/curriculum/${course.id}` }
          ],
          primaryAction: `<a href="#/instructor/lesson-editor/new" class="btn btn-primary btn-sm">+ Thêm bài học</a>`
        })}

        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="sub-title m-0">Danh sách bài học (${lessons.length} bài)</h5>
            <span class="text-caption text-muted">Sử dụng nút mũi tên để điều chỉnh thứ tự bài học</span>
          </div>
          <div class="card-body p-0">
            <ul class="list-group list-group-flush" id="curriculum-list">
              ${lessons.map((les, idx) => `
                <li class="list-group-item d-flex justify-content-between align-items-center px-4 py-3">
                  <div class="d-flex align-items-center gap-3">
                    <span class="badge badge-neutral" style="min-width: 28px; text-align: center;">${idx + 1}</span>
                    <div>
                      <div class="fw-medium">${les.title}</div>
                      <div class="text-caption text-muted">${les.duration} • ${les.resources ? les.resources.length : 0} tài liệu đính kèm</div>
                    </div>
                  </div>
                  <div class="d-flex align-items-center gap-2">
                    <button class="btn btn-secondary btn-sm" ${idx === 0 ? 'disabled' : ''} onclick="PWD.views.instructor.moveLesson('${les.id}', -1)" title="Di chuyển lên">↑</button>
                    <button class="btn btn-secondary btn-sm" ${idx === lessons.length - 1 ? 'disabled' : ''} onclick="PWD.views.instructor.moveLesson('${les.id}', 1)" title="Di chuyển xuống">↓</button>
                    <a href="#/instructor/lesson-editor/${les.id}" class="btn btn-secondary btn-sm">Sửa nội dung</a>
                  </div>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      `;
    },

    moveLesson(lessonId, direction) {
      window.PWD.components.showToast('Đã cập nhật thứ tự bài học trong chương trình đào tạo.', 'success');
    },

    // 5. Lesson Editor
    lessonEditor(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const isNew = params.id === 'new';
      const lesson = isNew ? { title: '', duration: '45 phút', content: '' } : store.lessons.find(l => l.id === params.id) || store.lessons[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: isNew ? 'Soạn bài học mới' : `Soạn bài: ${lesson.title}`,
            subtitle: 'Chỉnh sửa nội dung giảng dạy và tài liệu bổ trợ',
            breadcrumbs: [
              { label: 'Chương trình', href: '#/instructor/curriculum/c1' },
              { label: 'Soạn thảo', href: `#/instructor/lesson-editor/${lesson.id}` }
            ]
          })}

          <div class="card">
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.components.showToast('Đã lưu bài học thành công!', 'success'); PWD.router.navigate('#/instructor/curriculum/c1');">
                <div class="form-group mb-3">
                  <label class="form-label">Tên bài học <span class="required">*</span></label>
                  <input type="text" class="form-control form-control-sm" value="${lesson.title}" required placeholder="Ví dụ: Bài 7: Bảo mật phiên làm việc">
                </div>

                <div class="form-group mb-3">
                  <label class="form-label">Thời lượng ước tính</label>
                  <input type="text" class="form-control form-control-sm" value="${lesson.duration}">
                </div>

                <div class="form-group mb-4">
                  <label class="form-label">Nội dung bài học (HTML / Markdown)</label>
                  <textarea class="form-control" rows="12">${lesson.content || ''}</textarea>
                </div>

                <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                  <a href="#/instructor/curriculum/c1" class="btn btn-secondary btn-sm">Hủy bỏ</a>
                  <button type="submit" class="btn btn-primary btn-sm">Lưu bài học</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    // 6. Resources Manager
    resources() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Quản lý Tài nguyên & Tệp tin',
          subtitle: 'Tải lên slide bài giảng, bài tập mẫu và kiểm tra an toàn tệp ClamAV'
        })}

        <div class="card mb-4">
          <div class="card-body text-center p-5 border border-dashed border-slate-300 rounded bg-slate-50">
            <div class="mb-2 text-slate-400">${cmp.icon('upload')}</div>
            <div class="fw-semibold text-slate-800">Kéo thả tệp tin vào đây hoặc bấm để chọn tệp</div>
            <div class="text-caption text-muted mt-1">Hỗ trợ PDF, DOCX, ZIP (Tối đa 50MB, video < 1GB). Hệ thống tự động quét virus trước khi kích hoạt.</div>
            <button class="btn btn-secondary btn-sm mt-3" onclick="PWD.components.showToast('Mô phỏng mở hộp thoại chọn tệp...', 'info')">Chọn tệp từ máy tính</button>
          </div>
        </div>
      `;
    },

    // 7. Question Bank (Scenario 6)
    questions() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Ngân hàng Câu hỏi',
          subtitle: 'Kho lưu trữ và phiên bản câu hỏi trắc nghiệm, tự luận PWD301',
          primaryAction: `<a href="#/instructor/question-editor/new" class="btn btn-primary btn-sm">+ Tạo câu hỏi mới</a>`,
          secondaryActions: `
            <a href="#/instructor/import" class="btn btn-secondary btn-sm">Import DOCX/PDF</a>
            <a href="#/instructor/ai-generator" class="btn btn-secondary btn-sm">AI sinh câu hỏi</a>
          `
        })}

        <div class="card mb-4">
          <div class="card-body p-3">
            <div class="row g-3">
              <div class="col-md-5">
                <input type="text" id="qb-search" class="form-control form-control-sm" placeholder="Tìm theo nội dung câu hỏi hoặc chủ đề..." oninput="PWD.views.instructor.filterQuestions()">
              </div>
              <div class="col-md-4">
                <select id="qb-type-filter" class="form-select form-select-sm" onchange="PWD.views.instructor.filterQuestions()">
                  <option value="all">Tất cả loại câu hỏi</option>
                  <option value="single_choice">Trắc nghiệm 1 đáp án</option>
                  <option value="multi_select">Trắc nghiệm nhiều đáp án</option>
                  <option value="short_answer">Điền câu trả lời ngắn</option>
                  <option value="essay">Tự luận</option>
                </select>
              </div>
              <div class="col-md-3">
                <select id="qb-diff-filter" class="form-select form-select-sm" onchange="PWD.views.instructor.filterQuestions()">
                  <option value="all">Tất cả độ khó</option>
                  <option value="easy">Dễ</option>
                  <option value="medium">Trung bình</option>
                  <option value="hard">Khó</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Nội dung câu hỏi</th>
                  <th>Loại</th>
                  <th>Chủ đề</th>
                  <th>Độ khó</th>
                  <th>Phiên bản</th>
                  <th class="text-end">Thao tác</th>
                </tr>
              </thead>
              <tbody id="qb-table-body">
                ${store.questionBank.map(q => {
                  let typeLabel = 'Trắc nghiệm đơn';
                  if (q.type === 'multi_select') typeLabel = 'Nhiều đáp án';
                  else if (q.type === 'short_answer') typeLabel = 'Trả lời ngắn';
                  else if (q.type === 'essay') typeLabel = 'Tự luận';

                  const diffBadge = q.difficulty === 'easy' ? cmp.badge('success', 'Dễ') : q.difficulty === 'hard' ? cmp.badge('danger', 'Khó') : cmp.badge('warning', 'Vừa');

                  return `
                    <tr class="qb-row" data-type="${q.type}" data-diff="${q.difficulty}" data-query="${q.stem.toLowerCase()} ${q.topic.toLowerCase()}">
                      <td>
                        <div class="fw-medium text-slate-900" style="max-width: 440px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                          ${q.stem}
                        </div>
                        <div class="text-caption text-muted">Được sử dụng trong ${q.usedCount} đề thi</div>
                      </td>
                      <td class="text-caption">${typeLabel}</td>
                      <td><span class="badge badge-neutral">${q.topic}</span></td>
                      <td>${diffBadge}</td>
                      <td><span class="badge badge-info">v${q.revision || 1}</span></td>
                      <td class="text-end">
                        <div class="table-actions">
                          <a href="#/instructor/question-history/${q.id}" class="btn btn-ghost btn-sm" title="Lịch sử phiên bản">${cmp.icon('clock')}</a>
                          <a href="#/instructor/question-editor/${q.id}" class="btn btn-secondary btn-sm">Sửa</a>
                        </div>
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

    filterQuestions() {
      const q = (document.getElementById('qb-search')?.value || '').toLowerCase().trim();
      const type = document.getElementById('qb-type-filter')?.value || 'all';
      const diff = document.getElementById('qb-diff-filter')?.value || 'all';

      document.querySelectorAll('.qb-row').forEach(row => {
        const query = row.getAttribute('data-query') || '';
        const rType = row.getAttribute('data-type') || '';
        const rDiff = row.getAttribute('data-diff') || '';

        const mQ = !q || query.includes(q);
        const mT = type === 'all' || rType === type;
        const mD = diff === 'all' || rDiff === diff;

        row.style.display = (mQ && mT && mD) ? '' : 'none';
      });
    },

    // 8. Question Editor (Scenario 6: Preserves revisions when editing used questions)
    questionEditor(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const isNew = params.id === 'new';
      const q = isNew 
        ? { id: 'new', stem: '', type: 'single_choice', difficulty: 'medium', topic: 'Flask', points: 2.0, revision: 1, usedCount: 0 }
        : store.questionBank.find(item => item.id === params.id) || store.questionBank[0];

      const isUsed = q.usedCount > 0;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: isNew ? 'Tạo câu hỏi mới' : `Chỉnh sửa câu hỏi (Phiên bản v${q.revision || 1})`,
            subtitle: isUsed ? `Câu hỏi này đang được sử dụng trong ${q.usedCount} đề thi` : 'Câu hỏi chưa được đưa vào bài thi nào',
            breadcrumbs: [
              { label: 'Ngân hàng câu hỏi', href: '#/instructor/questions' },
              { label: isNew ? 'Tạo mới' : `v${q.revision || 1}`, href: `#/instructor/question-editor/${q.id}` }
            ]
          })}

          ${isUsed ? `
            <div class="alert-card alert-card-warning mb-4">
              <span style="flex-shrink:0;">${cmp.icon('alertTriangle')}</span>
              <div>
                <strong>Quy chuẩn bảo toàn lịch sử (Invariant 6 & 15):</strong>
                <div class="text-caption mt-1">Câu hỏi đã có bài thi sử dụng. Khi sửa đổi nội dung hoặc đáp án, hệ thống sẽ tự động tạo một <strong>phiên bản mới (Revision v${(q.revision || 1) + 1})</strong> và lưu vết kiểm toán, không ghi đè trực tiếp lên bài thi sinh viên đã làm.</div>
              </div>
            </div>
          ` : ''}

          <div class="card">
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.views.instructor.saveQuestion('${q.id}', ${isUsed});">
                <div class="form-group mb-3">
                  <label class="form-label">Nội dung câu hỏi (Stem) <span class="required">*</span></label>
                  <textarea id="q-stem" class="form-control form-control-sm" rows="3" required>${q.stem}</textarea>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-md-4">
                    <label class="form-label">Loại câu hỏi</label>
                    <select id="q-type" class="form-select form-select-sm" ${isUsed ? 'disabled title="Không thể đổi loại câu hỏi đã có sinh viên làm"' : ''}>
                      <option value="single_choice" ${q.type === 'single_choice' ? 'selected' : ''}>Trắc nghiệm 1 đáp án</option>
                      <option value="multi_select" ${q.type === 'multi_select' ? 'selected' : ''}>Nhiều đáp án</option>
                      <option value="short_answer" ${q.type === 'short_answer' ? 'selected' : ''}>Trả lời ngắn</option>
                      <option value="essay" ${q.type === 'essay' ? 'selected' : ''}>Tự luận</option>
                    </select>
                  </div>
                  <div class="col-md-4">
                    <label class="form-label">Độ khó</label>
                    <select id="q-diff" class="form-select form-select-sm">
                      <option value="easy" ${q.difficulty === 'easy' ? 'selected' : ''}>Dễ</option>
                      <option value="medium" ${q.difficulty === 'medium' ? 'selected' : ''}>Trung bình</option>
                      <option value="hard" ${q.difficulty === 'hard' ? 'selected' : ''}>Khó</option>
                    </select>
                  </div>
                  <div class="col-md-4">
                    <label class="form-label">Chủ đề</label>
                    <input type="text" id="q-topic" class="form-control form-control-sm" value="${q.topic}">
                  </div>
                </div>

                ${isUsed ? `
                  <div class="form-group mb-4">
                    <label class="form-label">Lý do điều chỉnh / đính chính <span class="required">*</span></label>
                    <input type="text" id="q-reason" class="form-control form-control-sm" required placeholder="Ghi rõ căn cứ sửa đổi cho nhật ký kiểm toán...">
                  </div>
                ` : ''}

                <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                  <a href="#/instructor/questions" class="btn btn-secondary btn-sm">Hủy bỏ</a>
                  <button type="submit" class="btn btn-primary btn-sm">
                    ${isUsed ? `Lưu phiên bản mới (v${(q.revision || 1) + 1})` : 'Lưu câu hỏi'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    saveQuestion(qId, isUsed) {
      const stem = document.getElementById('q-stem')?.value || '';
      const topic = document.getElementById('q-topic')?.value || 'Chung';
      const difficulty = document.getElementById('q-diff')?.value || 'medium';
      const reason = document.getElementById('q-reason')?.value || 'Hiệu chỉnh đáp án';

      if (isUsed) {
        window.PWD.store.updateQuestionWithRevision(qId, { stem, topic, difficulty }, reason);
        window.PWD.components.showToast('Đã lưu thành công phiên bản mới và ghi nhận vào Audit Log.', 'success');
      } else {
        window.PWD.store.createQuestion({ stem, topic, difficulty, type: 'single_choice', points: 2.0 });
        window.PWD.components.showToast('Đã tạo câu hỏi mới trong ngân hàng.', 'success');
      }
      window.PWD.router.navigate('#/instructor/questions');
    },

    // 9. Question Revision History
    questionHistory(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const q = store.questionBank.find(item => item.id === params.id) || store.questionBank[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: `Lịch sử Sửa đổi Câu hỏi`,
            subtitle: `Mã câu hỏi: ${q.id} • Phiên bản hiện tại: v${q.revision || 1}`,
            breadcrumbs: [
              { label: 'Ngân hàng câu hỏi', href: '#/instructor/questions' },
              { label: 'Lịch sử', href: `#/instructor/question-history/${q.id}` }
            ]
          })}

          <div class="card">
            <div class="card-header">
              <h5 class="sub-title m-0">Tiến trình các phiên bản (Immutable Audit Trail)</h5>
            </div>
            <div class="card-body p-0">
              <ul class="list-group list-group-flush">
                <li class="list-group-item p-4">
                  <div class="d-flex justify-content-between mb-1">
                    <span class="fw-bold">Phiên bản v${q.revision || 1} (Hiện tại)</span>
                    <span class="text-caption text-muted">08/09/2026 11:30</span>
                  </div>
                  <div class="text-slate-800 mb-2">${q.stem}</div>
                  <div class="text-caption text-muted">Thực hiện bởi: Trần Hoàng Nam • Trạng thái: Đang áp dụng</div>
                </li>
                <li class="list-group-item p-4 bg-slate-50">
                  <div class="d-flex justify-content-between mb-1">
                    <span class="fw-bold text-muted">Phiên bản v1 (Lịch sử)</span>
                    <span class="text-caption text-muted">01/08/2026 09:15</span>
                  </div>
                  <div class="text-slate-600 mb-2">Bản thảo câu hỏi khởi tạo ban đầu trước khi đính chính.</div>
                  <div class="text-caption text-muted">Thực hiện bởi: Trần Hoàng Nam • Trạng thái: Lưu trữ lịch sử</div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      `;
    },

    // 10. Assessments List
    assessments() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Quản lý Bài kiểm tra & Đề thi',
          subtitle: 'Thiết lập cấu hình, ngân hàng đề và xuất bản bài thi',
          primaryAction: `<a href="#/instructor/assessment-builder/a4" class="btn btn-primary btn-sm">+ Tạo đề thi mới</a>`
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Tên bài kiểm tra</th>
                  <th>Thời lượng</th>
                  <th>Số câu hỏi</th>
                  <th>Trạng thái xuất bản</th>
                  <th>Khóa cấu hình</th>
                  <th class="text-end">Hành động</th>
                </tr>
              </thead>
              <tbody>
                ${store.assessments.map(a => `
                  <tr>
                    <td>
                      <div class="fw-medium">${a.title}</div>
                      <div class="text-caption text-muted">${a.totalPoints} điểm tổng</div>
                    </td>
                    <td>${a.durationMinutes} phút</td>
                    <td>${a.questionIds.length} câu</td>
                    <td>
                      ${a.status === 'published' ? cmp.badge('success', 'Đã xuất bản') : a.status === 'closed' ? cmp.badge('neutral', 'Đã đóng') : cmp.badge('neutral', 'Bản nháp')}
                    </td>
                    <td>
                      <div class="d-flex gap-1 flex-wrap">
                        ${a.timingLocked ? cmp.badge('warning', 'Khóa thời gian') : ''}
                        ${a.studentStarted ? cmp.badge('danger', 'Khóa cấu trúc') : ''}
                      </div>
                    </td>
                    <td class="text-end">
                      <a href="#/instructor/assessment-builder/${a.id}" class="btn btn-secondary btn-sm">Thiết lập</a>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 11. Assessment Builder (Scenario 7: Published timing lock & Student started structure lock)
    // 11. Assessment Builder (Multi-step Wizard & Lock Invariants)
    assessmentBuilder(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const a = store.assessments.find(item => item.id === params.id) || store.assessments[0];

      // Current Step: 0: Cấu hình & Thời gian, 1: Ma trận & Câu hỏi, 2: Kiểm tra & Xuất bản
      const currentStep = store.assessmentBuilderStep !== undefined ? store.assessmentBuilderStep : 0;

      const steps = [
        { title: 'Bước 1: Cấu hình & Thời gian' },
        { title: 'Bước 2: Ma trận & Câu hỏi' },
        { title: 'Bước 3: Kiểm tra & Xuất bản' }
      ];

      return `
        <div class="content-wide">
          ${cmp.pageHeader({
            title: `Cấu hình Đề thi: ${a.title}`,
            subtitle: `Mã đề: ${a.id} • ${a.questionIds.length} câu hỏi • ${a.totalPoints} điểm`,
            breadcrumbs: [
              { label: 'Bài kiểm tra', href: '#/instructor/assessments' },
              { label: a.id, href: `#/instructor/assessment-builder/${a.id}` }
            ],
            primaryAction: a.status === 'draft' 
              ? `<button class="btn btn-primary btn-sm px-3" onclick="PWD.views.instructor.publishAssessment('${a.id}')">Xuất bản đề thi</button>`
              : `<span class="badge badge-success px-3 py-2">Đã xuất bản</span>`
          })}

          <!-- Simulation Toolbar for Lock States (Scenario 7) -->
          <div class="p-3 mb-4 bg-slate-100 border border-slate-300 rounded d-flex justify-content-between align-items-center" style="border-radius: var(--radius-lg);">
            <div class="d-flex align-items-center gap-3">
              <span class="fw-bold text-slate-700">Mô phỏng trạng thái đề thi (Demo Controls):</span>
              <button class="btn btn-sm ${a.status === 'published' ? 'btn-secondary' : 'btn-primary'}" onclick="PWD.views.instructor.togglePublishState('${a.id}')">
                ${a.status === 'published' ? 'Đưa về Bản nháp (Draft)' : 'Xuất bản (Publish) → Khóa thời gian'}
              </button>
              <button class="btn btn-sm ${a.studentStarted ? 'btn-danger' : 'btn-secondary'}" onclick="PWD.views.instructor.toggleStudentStarted('${a.id}')">
                ${a.studentStarted ? 'Đang bật: Học viên đã bắt đầu thi → Khóa cấu trúc' : 'Mô phỏng: Chưa có ai bắt đầu thi'}
              </button>
            </div>
            <div>
              <a href="#/instructor/publish-validation/${a.id}" class="btn btn-secondary btn-sm">Kiểm tra điều kiện xuất bản</a>
            </div>
          </div>

          <!-- Lock warnings -->
          ${a.timingLocked ? `
            <div class="alert-card alert-card-warning mb-3">
              <span style="flex-shrink:0;">${cmp.icon('lock')}</span>
              <div>
                <strong>Thời gian làm bài đã bị khóa (Invariant 13):</strong>
                <div class="text-caption mt-1">Bài thi đã xuất bản chính thức, các trường Thời lượng và Hạn mở/đóng đề thi không được phép sửa đổi tự do.</div>
              </div>
            </div>
          ` : ''}

          ${a.studentStarted ? `
            <div class="alert-card alert-card-danger mb-4">
              <span style="flex-shrink:0;">${cmp.icon('lock')}</span>
              <div>
                <strong>Cấu trúc câu hỏi và phân bổ điểm số đã bị khóa (Invariant 14):</strong>
                <div class="text-caption mt-1">Đã có sinh viên bắt đầu làm bài thi. Nghiêm cấm thêm/bớt câu hỏi hoặc thay đổi thang điểm. Nếu phát hiện sai sót, vui lòng sử dụng quy trình Đính chính câu hỏi (Correction/Revision).</div>
              </div>
            </div>
          ` : ''}

          <!-- Step Wizard Stepper UI -->
          <div class="mb-4">
            ${cmp.stepWizard(steps, currentStep)}
          </div>

          <!-- STEP 1: Cấu hình & Thời lượng -->
          ${currentStep === 0 ? `
            <div class="card border-0 mb-4" style="box-shadow: var(--shadow-sm); border-radius: var(--radius-xl);">
              <div class="card-header bg-transparent py-3 px-4 border-bottom border-slate-100 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                  ${cmp.iconBox('clock', 'amber')}
                  <div>
                    <h5 class="sub-title m-0">Bước 1: Thiết lập Thông số & Thời lượng</h5>
                    <div class="text-caption text-muted">Cấu hình thời gian bắt đầu, kết thúc và cơ chế giao đề</div>
                  </div>
                </div>
                <span class="badge ${a.timingLocked ? 'badge-danger' : 'badge-neutral'}">${a.timingLocked ? 'Đã khóa sửa đổi' : 'Có thể chỉnh sửa'}</span>
              </div>
              <div class="card-body p-4">
                <div class="row g-4">
                  <div class="col-md-6">
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Tên bài kiểm tra / Kỳ thi</label>
                      <input type="text" class="form-control" value="${a.title}" ${a.timingLocked ? 'disabled' : ''}>
                    </div>
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Thời lượng làm bài (phút)</label>
                      <input type="number" class="form-control" value="${a.durationMinutes}" ${a.timingLocked ? 'disabled' : ''}>
                      <div class="form-hint mt-1">Thời gian đếm ngược tự động khóa bài khi hết giờ.</div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Thời gian mở đề</label>
                      <input type="text" class="form-control" value="${a.openAt || '2026-09-01 08:00'}" ${a.timingLocked ? 'disabled' : ''}>
                    </div>
                    <div class="form-group mb-3">
                      <label class="form-label fw-semibold">Thời gian đóng đề</label>
                      <input type="text" class="form-control" value="${a.closeAt || '2026-09-30 23:59'}" ${a.timingLocked ? 'disabled' : ''}>
                    </div>
                  </div>
                </div>
                <div class="p-3 bg-slate-50 border border-slate-200 rounded-3 mt-2">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" checked ${a.timingLocked ? 'disabled' : ''} id="shuffle-check">
                    <label class="form-check-label fw-medium text-slate-800 ms-2" for="shuffle-check">Tự động xáo trộn thứ tự câu hỏi và đáp án cho từng sinh viên</label>
                  </div>
                </div>
              </div>
              <div class="card-footer bg-white border-top border-slate-100 p-3 px-4 d-flex justify-content-end">
                <button class="btn btn-primary px-4" onclick="PWD.views.instructor.setAssessmentBuilderStep(1)">Tiếp tục: Ma trận & Câu hỏi →</button>
              </div>
            </div>
          ` : ''}

          <!-- STEP 2: Ma trận & Câu hỏi -->
          ${currentStep === 1 ? `
            <div class="card border-0 mb-4" style="box-shadow: var(--shadow-sm); border-radius: var(--radius-xl);">
              <div class="card-header bg-transparent py-3 px-4 border-bottom border-slate-100 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                  ${cmp.iconBox('database', 'violet')}
                  <div>
                    <h5 class="sub-title m-0">Bước 2: Danh sách Câu hỏi & Phân bổ điểm (${a.questionIds.length} câu • ${a.totalPoints} điểm)</h5>
                    <div class="text-caption text-muted">Lựa chọn câu hỏi từ ngân hàng hoặc phân bổ tự động theo ma trận đề</div>
                  </div>
                </div>
                ${!a.studentStarted ? `
                  <div class="d-flex gap-2">
                    <a href="#/instructor/question-picker/${a.id}" class="btn btn-secondary btn-sm">+ Thêm câu hỏi</a>
                    <a href="#/instructor/blueprint-builder/${a.id}" class="btn btn-secondary btn-sm">Ma trận đề</a>
                  </div>
                ` : `<span class="badge badge-danger">Khóa thêm/bớt câu (Đã có sinh viên thi)</span>`}
              </div>
              <div class="card-body p-0">
                <ul class="list-group list-group-flush">
                  ${a.questionIds.map((qid, idx) => {
                    const q = store.questionBank.find(x => x.id === qid);
                    return `
                      <li class="list-group-item d-flex justify-content-between align-items-center px-4 py-3">
                        <div>
                          <div class="fw-medium">${idx + 1}. ${q ? q.stem : qid}</div>
                          <div class="text-caption text-muted">${q ? q.topic : ''} • ${q ? q.points : 2.0} điểm</div>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                          ${a.studentStarted ? `
                            <a href="#/instructor/question-editor/${qid}" class="btn btn-secondary btn-sm">Đính chính đáp án</a>
                          ` : `
                            <button class="btn btn-ghost btn-sm text-danger" onclick="PWD.components.showToast('Mô phỏng xóa câu hỏi khỏi đề', 'info')">${cmp.icon('trash')}</button>
                          `}
                        </div>
                      </li>
                    `;
                  }).join('')}
                </ul>
              </div>
              <div class="card-footer bg-white border-top border-slate-100 p-3 px-4 d-flex justify-content-between">
                <button class="btn btn-secondary px-3" onclick="PWD.views.instructor.setAssessmentBuilderStep(0)">← Quay lại Bước 1</button>
                <button class="btn btn-primary px-4" onclick="PWD.views.instructor.setAssessmentBuilderStep(2)">Tiếp tục: Kiểm tra & Xuất bản →</button>
              </div>
            </div>
          ` : ''}

          <!-- STEP 3: Kiểm tra & Xuất bản -->
          ${currentStep === 2 ? `
            <div class="card border-0 mb-4" style="box-shadow: var(--shadow-sm); border-radius: var(--radius-xl);">
              <div class="card-header bg-transparent py-3 px-4 border-bottom border-slate-100 d-flex align-items-center gap-2">
                ${cmp.iconBox('checkCircle', 'emerald')}
                <div>
                  <h5 class="sub-title m-0">Bước 3: Kiểm định Điều kiện & Xuất bản chính thức</h5>
                  <div class="text-caption text-muted">Kiểm tra các bất biến kỹ thuật Invariants trước khi sinh viên bắt đầu làm bài</div>
                </div>
              </div>
              <div class="card-body p-4">
                <div class="row g-3 mb-4">
                  <div class="col-md-4">
                    <div class="p-3 bg-slate-50 border border-slate-200 rounded-3">
                      <div class="text-caption text-muted mb-1">Tổng điểm đề thi</div>
                      <div class="fs-4 fw-bold text-slate-900">${a.totalPoints} / 10.0</div>
                      <span class="badge badge-success mt-1">Đạt chuẩn thang điểm</span>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="p-3 bg-slate-50 border border-slate-200 rounded-3">
                      <div class="text-caption text-muted mb-1">Số lượng câu hỏi</div>
                      <div class="fs-4 fw-bold text-slate-900">${a.questionIds.length} câu</div>
                      <span class="badge badge-success mt-1">Phủ 3 chủ đề</span>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="p-3 bg-slate-50 border border-slate-200 rounded-3">
                      <div class="text-caption text-muted mb-1">Trạng thái hiện tại</div>
                      <div class="fs-4 fw-bold text-slate-900">${a.status === 'published' ? 'Đã xuất bản' : 'Bản nháp (Draft)'}</div>
                      <span class="badge ${a.status === 'published' ? 'badge-success' : 'badge-neutral'} mt-1">${a.status === 'published' ? 'Sinh viên có thể thi' : 'Chưa công bố'}</span>
                    </div>
                  </div>
                </div>

                <div class="p-4 bg-slate-50 border border-slate-200 rounded-3 mb-4">
                  <h6 class="fw-bold text-slate-900 mb-2">Quy định khóa an toàn (Security Invariants):</h6>
                  <ul class="m-0 ps-3 text-caption text-slate-700 d-flex flex-column gap-2">
                    <li><strong>Invariant 13:</strong> Khi đề thi đã xuất bản, thời lượng và lịch mở/đóng thi sẽ tự động khóa để bảo đảm tính công bằng.</li>
                    <li><strong>Invariant 14:</strong> Ngay khi sinh viên đầu tiên nhấn "Bắt đầu làm bài", cấu trúc câu hỏi và phân bổ điểm sẽ khóa vĩnh viễn.</li>
                  </ul>
                </div>

                <div class="d-flex align-items-center justify-content-between p-3 bg-blue-50 border border-blue-200 rounded-3">
                  <div>
                    <div class="fw-semibold text-slate-900">Sẵn sàng xuất bản bài thi?</div>
                    <div class="text-caption text-muted">Bài thi sẽ hiển thị trong danh sách của toàn bộ sinh viên đã ghi danh khóa học.</div>
                  </div>
                  ${a.status === 'draft' ? `
                    <button class="btn btn-primary px-4 py-2" onclick="PWD.views.instructor.publishAssessment('${a.id}')">
                      Xuất bản bài thi ngay
                    </button>
                  ` : `
                    <button class="btn btn-secondary px-4 py-2" disabled>
                      ✓ Bài thi đã xuất bản
                    </button>
                  `}
                </div>
              </div>
              <div class="card-footer bg-white border-top border-slate-100 p-3 px-4 d-flex justify-content-between">
                <button class="btn btn-secondary px-3" onclick="PWD.views.instructor.setAssessmentBuilderStep(1)">← Quay lại Bước 2</button>
                <a href="#/instructor/assessments" class="btn btn-outline-secondary px-3">Hoàn tất & Xem danh sách đề thi</a>
              </div>
            </div>
          ` : ''}
        </div>
      `;
    },

    setAssessmentBuilderStep(step) {
      window.PWD.store.state.assessmentBuilderStep = step;
      window.PWD.router.handleRouting();
    },

    togglePublishState(id) {
      const a = window.PWD.store.state.assessments.find(x => x.id === id);
      if (a) {
        a.status = a.status === 'published' ? 'draft' : 'published';
        a.timingLocked = a.status === 'published';
        window.PWD.store.persist();
        window.PWD.components.showToast(`Trạng thái đề thi: ${a.status.toUpperCase()}`, 'info');
        window.PWD.router.handleRouting();
      }
    },

    toggleStudentStarted(id) {
      const a = window.PWD.store.state.assessments.find(x => x.id === id);
      if (a) {
        a.studentStarted = !a.studentStarted;
        window.PWD.store.persist();
        window.PWD.components.showToast(`Mô phỏng học viên bắt đầu: ${a.studentStarted ? 'BẬT (Khóa cấu trúc)' : 'TẮT'}`, 'info');
        window.PWD.router.handleRouting();
      }
    },

    publishAssessment(id) {
      window.PWD.store.publishAssessment(id);
      window.PWD.components.showToast('Xuất bản đề thi thành công! Cấu hình thời gian đã được khóa.', 'success');
      window.PWD.router.handleRouting();
    },

    // 12. Manual Question Picker
    questionPicker(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Chọn Câu hỏi từ Ngân hàng',
            subtitle: 'Thêm câu hỏi vào đề kiểm tra',
            breadcrumbs: [
              { label: 'Cấu hình bài thi', href: `#/instructor/assessment-builder/${params.id}` },
              { label: 'Chọn câu hỏi', href: `#/instructor/question-picker/${params.id}` }
            ]
          })}

          <div class="card">
            <div class="card-body p-0">
              <table class="app-table">
                <thead>
                  <tr>
                    <th>Nội dung câu hỏi</th>
                    <th>Chủ đề</th>
                    <th>Điểm</th>
                    <th class="text-end">Chọn</th>
                  </tr>
                </thead>
                <tbody>
                  ${store.questionBank.map(q => `
                    <tr>
                      <td class="fw-medium">${q.stem}</td>
                      <td><span class="badge badge-neutral">${q.topic}</span></td>
                      <td>${q.points}</td>
                      <td class="text-end">
                        <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Đã thêm câu hỏi vào đề thi!', 'success')">+ Thêm</button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;
    },

    // 13. Blueprint / Matrix Builder
    blueprintBuilder(params) {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Ma trận Đề thi (Blueprint Builder)',
            subtitle: 'Cấu hình quy tắc sinh đề thi tự động theo ma trận độ khó và chủ đề',
            breadcrumbs: [
              { label: 'Cấu hình đề thi', href: `#/instructor/assessment-builder/${params.id}` },
              { label: 'Ma trận đề', href: `#/instructor/blueprint-builder/${params.id}` }
            ]
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Quy tắc sinh câu hỏi tự động</h5>
            </div>
            <div class="card-body">
              <table class="app-table mb-3">
                <thead>
                  <tr>
                    <th>Chủ đề bài giảng</th>
                    <th>Độ khó</th>
                    <th>Số lượng câu</th>
                    <th>Điểm / câu</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Giao thức HTTP & Kiến trúc</td>
                    <td><span class="badge badge-success">Dễ</span></td>
                    <td>2 câu</td>
                    <td>2.0 điểm</td>
                  </tr>
                  <tr>
                    <td>Flask Blueprints & Factory</td>
                    <td><span class="badge badge-warning">Vừa</span></td>
                    <td>2 câu</td>
                    <td>2.0 điểm</td>
                  </tr>
                  <tr>
                    <td>Bảo mật Web & CSRF</td>
                    <td><span class="badge badge-danger">Khó</span></td>
                    <td>1 câu</td>
                    <td>2.0 điểm</td>
                  </tr>
                </tbody>
              </table>

              <button class="btn btn-secondary btn-sm mb-3">+ Thêm quy tắc ma trận</button>

              <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                <a href="#/instructor/assessment-builder/${params.id}" class="btn btn-secondary btn-sm">Quay lại</a>
                <button class="btn btn-primary btn-sm" onclick="PWD.components.showToast('Đã lưu cấu hình ma trận đề thi!', 'success')">Lưu ma trận đề</button>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 14. Publish Validation
    publishValidation(params) {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Kiểm tra Điều kiện Xuất bản Đề thi',
            subtitle: 'Xác thực cấu hình bài thi trước khi công bố cho sinh viên',
            breadcrumbs: [
              { label: 'Cấu hình đề thi', href: `#/instructor/assessment-builder/${params.id}` },
              { label: 'Kiểm tra xuất bản', href: `#/instructor/publish-validation/${params.id}` }
            ]
          })}

          <div class="card mb-4">
            <div class="card-body">
              <ul class="list-group list-group-flush">
                <li class="list-group-item d-flex align-items-center gap-3 py-3">
                  <span class="text-success">${cmp.icon('checkCircle')}</span>
                  <div>
                    <div class="fw-medium">Số lượng câu hỏi trong đề đạt yêu cầu</div>
                    <div class="text-caption text-muted">Đề thi có 5 câu hỏi (tối thiểu 3 câu).</div>
                  </div>
                </li>
                <li class="list-group-item d-flex align-items-center gap-3 py-3">
                  <span class="text-success">${cmp.icon('checkCircle')}</span>
                  <div>
                    <div class="fw-medium">Tổng điểm hợp lệ</div>
                    <div class="text-caption text-muted">Tổng điểm số câu hỏi đạt 18.0 điểm.</div>
                  </div>
                </li>
                <li class="list-group-item d-flex align-items-center gap-3 py-3">
                  <span class="text-success">${cmp.icon('checkCircle')}</span>
                  <div>
                    <div class="fw-medium">Khung thời gian mở/đóng đề hợp lệ</div>
                    <div class="text-caption text-muted">Hạn đóng đề sau thời điểm mở đề ít nhất 24 giờ.</div>
                  </div>
                </li>
              </ul>

              <div class="alert-card alert-card-success mt-4">
                <span style="flex-shrink:0;">${cmp.icon('checkCircle')}</span>
                <div>
                  <strong>Đủ điều kiện xuất bản:</strong> Tất cả các tiêu chuẩn kiểm tra an toàn đều đạt yêu cầu.
                </div>
              </div>

              <div class="text-end mt-3">
                <a href="#/instructor/assessment-builder/${params.id}" class="btn btn-primary btn-sm">Quay lại xuất bản đề thi</a>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 15. DOCX/PDF Import (Scenario 8)
    import() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Import Đề thi từ DOCX/PDF',
            subtitle: 'Tự động trích xuất câu hỏi và đáp án từ tệp tài liệu Word hoặc PDF'
          })}

          <div class="card mb-4">
            <div class="card-body p-5 text-center border border-dashed border-slate-300 rounded bg-slate-50">
              <div class="mb-2 text-slate-400">${cmp.icon('upload')}</div>
              <h5 class="sub-title">Chọn tệp tài liệu đề thi (.docx hoặc .pdf)</h5>
              <p class="text-caption text-muted mb-3" style="max-width: 440px; margin: 0 auto;">
                Hệ thống sẽ phân tích cấu trúc, nhận diện câu hỏi trắc nghiệm (A, B, C, D) và tự động lọc các trường hợp nghi ngờ để giảng viên duyệt.
              </p>
              <button class="btn btn-primary btn-sm" onclick="PWD.views.instructor.simulateImportProgress()">
                Chọn tệp mẫu: De_Thi_Mau_PWD301.docx (Mô phỏng)
              </button>

              <div id="import-progress-area" class="mt-4" style="display: none;">
                <div class="d-flex justify-content-between text-caption mb-1">
                  <span>Đang phân tích cú pháp tệp tài liệu...</span>
                  <span id="import-pct">65%</span>
                </div>
                ${cmp.progressBar(65)}
              </div>
            </div>
          </div>
        </div>
      `;
    },

    simulateImportProgress() {
      const pArea = document.getElementById('import-progress-area');
      if (pArea) pArea.style.display = 'block';

      setTimeout(() => {
        window.PWD.components.showToast('Phân tích tài liệu thành công! 3 câu hỏi đã sẵn sàng duyệt.', 'success');
        window.PWD.router.navigate('#/instructor/import-review');
      }, 1000);
    },

    // 16. Imported Questions Review
    importReview() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Xem xét Câu hỏi vừa Import',
          subtitle: 'Phê duyệt, chỉnh sửa hoặc loại bỏ câu hỏi trước khi thêm vào Ngân hàng câu hỏi'
        })}

        <div class="row g-4">
          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <span class="badge badge-success mb-2">Độ tin cậy: Cao (98%)</span>
                <h5 class="sub-title" style="font-size: 14px;">Câu 1: Cơ chế CSRF Token</h5>
                <p class="text-caption text-muted">Phương thức HTTP nào an toàn (Safe Method) không làm thay đổi tài nguyên máy chủ?</p>
                <div class="text-caption text-success mb-3">Đáp án: GET</div>
                <div class="d-flex gap-2">
                  <button class="btn btn-primary btn-sm w-100" onclick="PWD.components.showToast('Đã duyệt câu hỏi vào ngân hàng!', 'success')">Duyệt lưu</button>
                  <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Loại bỏ câu hỏi.', 'info')">Loại bỏ</button>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <span class="badge badge-warning mb-2">Cần xem lại (Ambiguous)</span>
                <h5 class="sub-title" style="font-size: 14px;">Câu 2: Nhận diện thiếu đáp án đúng</h5>
                <p class="text-caption text-muted">Trong Flask, câu lệnh nào được dùng để render template từ thư mục templates/?</p>
                <div class="text-caption text-warning mb-3">Chưa gắn nhãn đáp án đúng rõ ràng</div>
                <div class="d-flex gap-2">
                  <button class="btn btn-secondary btn-sm w-100" onclick="PWD.components.showToast('Mở trình chỉnh sửa đáp án', 'info')">Chỉnh sửa</button>
                  <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Loại bỏ câu hỏi.', 'info')">Loại bỏ</button>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <span class="badge badge-neutral mb-2">Trùng lặp tiềm năng</span>
                <h5 class="sub-title" style="font-size: 14px;">Câu 3: Thuộc tính HttpOnly</h5>
                <p class="text-caption text-muted">Nội dung tương tự câu hỏi q1 đã tồn tại trong ngân hàng.</p>
                <div class="text-caption text-muted mb-3">Độ tương đồng: 92%</div>
                <div class="d-flex gap-2">
                  <button class="btn btn-secondary btn-sm w-100" onclick="PWD.components.showToast('Đã bỏ qua câu trùng lặp.', 'info')">Bỏ qua</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 17. AI Question Generator (Scenario 8)
    aiGenerator() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'AI Tạo Câu hỏi Tự động',
            subtitle: 'Sử dụng mô hình ngôn ngữ để sinh bản thảo câu hỏi bám sát giáo trình'
          })}

          <div class="card">
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.views.instructor.simulateAIGeneration();">
                <div class="form-group mb-3">
                  <label class="form-label">Chọn bài học làm ngữ cảnh tài liệu</label>
                  <select class="form-select form-select-sm">
                    <option>Bài 1: Giao thức HTTP & Quản lý phiên</option>
                    <option>Bài 2: Flask Blueprint & Factory</option>
                    <option>Bài 4: Xử lý Biểu mẫu với Flask-WTF & CSRF</option>
                  </select>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-md-6">
                    <label class="form-label">Loại câu hỏi muốn sinh</label>
                    <select class="form-select form-select-sm">
                      <option>Trắc nghiệm 1 đáp án (Single Choice)</option>
                      <option>Trắc nghiệm nhiều đáp án (Multi Select)</option>
                      <option>Tự luận phân tích (Essay)</option>
                    </select>
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">Độ khó mục tiêu</label>
                    <select class="form-select form-select-sm">
                      <option>Trung bình (Khuyến nghị)</option>
                      <option>Dễ (Nhận biết)</option>
                      <option>Khó (Vận dụng cao)</option>
                    </select>
                  </div>
                </div>

                <div class="form-group mb-4">
                  <label class="form-label">Số lượng bản thảo muốn sinh</label>
                  <input type="number" class="form-control form-control-sm" value="3" min="1" max="5">
                  <div class="form-hint">Mỗi câu hỏi do AI tạo đều có nhãn nguồn gốc "AI Generated" và bắt buộc giảng viên phê duyệt trước khi đưa vào ngân hàng.</div>
                </div>

                <button type="submit" class="btn btn-primary btn-sm w-100">
                  ${cmp.icon('sparkles')} Sinh bản thảo câu hỏi
                </button>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    simulateAIGeneration() {
      window.PWD.components.showToast('AI đã hoàn tất sinh 3 bản thảo câu hỏi!', 'success');
      window.PWD.router.navigate('#/instructor/ai-draft-review');
    },

    // 18. AI Draft Review (Scenario 8: Keep / Edit / Reject)
    aiDraftReview() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Xem xét Bản thảo Câu hỏi AI',
          subtitle: 'Kiểm duyệt tính sư phạm, chỉnh sửa hoặc chấp thuận đưa vào Ngân hàng câu hỏi'
        })}

        <div class="row g-4">
          <div class="col-md-6" id="ai-draft-1">
            <div class="card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="badge badge-info">${cmp.icon('sparkles')} AI Generated</span>
                  <span class="badge badge-warning">Trung bình</span>
                </div>
                <h5 class="sub-title" style="font-size: 1rem;">Cơ chế bảo vệ của thuộc tính SameSite trong Cookie</h5>
                <p class="text-caption text-slate-700 mb-3">
                  Giá trị nào của thuộc tính SameSite sẽ ngăn chặn trình duyệt gửi Cookie trong toàn bộ các truy vấn điều hướng từ trang web bên thứ ba?
                </p>
                <div class="p-2 bg-slate-50 border border-slate-200 rounded text-caption mb-3">
                  ✓ Đáp án đề xuất: <strong>SameSite=Strict</strong>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-primary btn-sm w-100" onclick="PWD.views.instructor.keepDraft('ai-draft-1')">Duyệt lưu (Keep)</button>
                  <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mở trình sửa bản thảo', 'info')">Sửa (Edit)</button>
                  <button class="btn btn-ghost btn-sm text-danger" onclick="PWD.views.instructor.rejectDraft('ai-draft-1')">Bỏ (Reject)</button>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-6" id="ai-draft-2">
            <div class="card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="badge badge-info">${cmp.icon('sparkles')} AI Generated</span>
                  <span class="badge badge-success">Dễ</span>
                </div>
                <h5 class="sub-title" style="font-size: 1rem;">Vai trò của CSRF Token trong biểu mẫu Flask-WTF</h5>
                <p class="text-caption text-slate-700 mb-3">
                  Thẻ HTML ẩn nào trong form thường chứa giá trị CSRF Token được sinh ra bởi Flask-WTF?
                </p>
                <div class="p-2 bg-slate-50 border border-slate-200 rounded text-caption mb-3">
                  ✓ Đáp án đề xuất: <strong>&lt;input type="hidden" name="csrf_token"&gt;</strong>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-primary btn-sm w-100" onclick="PWD.views.instructor.keepDraft('ai-draft-2')">Duyệt lưu (Keep)</button>
                  <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Mở trình sửa bản thảo', 'info')">Sửa (Edit)</button>
                  <button class="btn btn-ghost btn-sm text-danger" onclick="PWD.views.instructor.rejectDraft('ai-draft-2')">Bỏ (Reject)</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    keepDraft(elId) {
      document.getElementById(elId)?.remove();
      window.PWD.components.showToast('Đã lưu bản thảo vào Ngân hàng câu hỏi (Gắn nhãn nguồn gốc: AI Generated)', 'success');
    },

    rejectDraft(elId) {
      document.getElementById(elId)?.remove();
      window.PWD.components.showToast('Đã loại bỏ bản thảo.', 'info');
    },

    // 19. Attempt Monitoring
    monitoring(params) {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Giám sát Bài thi Trực tiếp',
          subtitle: 'Theo dõi các thí sinh đang làm bài kiểm tra PWD301'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Học viên</th>
                  <th>Mã bài thi</th>
                  <th>Bắt đầu lúc</th>
                  <th>Thời gian còn lại</th>
                  <th>Trạng thái phiên</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="fw-medium">Nguyễn Minh Anh (u_student)</td>
                  <td>a1 — Kiểm tra giữa kỳ</td>
                  <td>12:40:15</td>
                  <td>42 phút</td>
                  <td><span class="badge badge-success"><span class="badge-dot"></span>Đang làm bài (Active Lease)</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 20. Pending Essay Grading Queue (Scenario 9)
    gradingQueue() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Hàng đợi Chấm bài Tự luận',
          subtitle: 'Danh sách các bài thi có câu hỏi tự luận đang chờ giảng viên đánh giá'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Học viên</th>
                  <th>Bài kiểm tra</th>
                  <th>Thời điểm nộp</th>
                  <th>Số câu tự luận</th>
                  <th class="text-end">Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <div class="fw-medium">Nguyễn Minh Anh</div>
                    <div class="text-caption text-muted">student@demo.local</div>
                  </td>
                  <td>
                    <div class="fw-medium">Bài tập Lớn — Thiết kế Kiến trúc Hệ thống</div>
                    <div class="text-caption text-muted">Môn: PWD301</div>
                  </td>
                  <td>05/09/2026 10:20</td>
                  <td>1 câu hỏi</td>
                  <td class="text-end">
                    <a href="#/instructor/grade-editor/att_pending_02" class="btn btn-primary btn-sm">Chấm bài</a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 21. Manual Grade Editor + Revision History (Scenario 9)
    gradeEditor(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const res = store.results.find(r => r.attemptId === params.id) || store.results[1];
      const essay = res.essayAnswers ? res.essayAnswers[0] : {
        questionId: 'q5',
        questionStem: 'Phân tích sự khác biệt giữa cơ chế lưu phiên bằng Server-side Session và JWT...',
        studentText: 'Server-side session ưu việt hơn trong bài toán thu hồi quyền vì dữ liệu phiên nằm dưới sự kiểm soát trực tiếp của backend...',
        assignedScore: 9.0,
        instructorComment: 'Phân tích mạch lạc, nêu bật được bản chất việc thu hồi phiên tức thời.'
      };

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Chấm bài Tự luận: Nguyễn Minh Anh',
            subtitle: 'Bài thi: Bài tập Lớn — Thiết kế Kiến trúc Hệ thống',
            breadcrumbs: [
              { label: 'Hàng đợi chấm bài', href: '#/instructor/grading-queue' },
              { label: 'Chấm điểm', href: `#/instructor/grade-editor/${params.id}` }
            ]
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Đề bài câu hỏi tự luận</h5>
            </div>
            <div class="card-body">
              <p class="fw-medium mb-3">${essay.questionStem}</p>
              <div class="p-3 bg-slate-50 border border-slate-200 rounded">
                <div class="text-caption text-muted mb-1">Bài làm của học viên:</div>
                <p class="m-0 text-slate-900" style="white-space: pre-wrap; line-height: 1.6;">${essay.studentText}</p>
              </div>
            </div>
          </div>

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Đánh giá và Nhập điểm</h5>
            </div>
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.views.instructor.saveGrade('${params.id}', '${essay.questionId}');">
                <div class="row g-3 mb-3">
                  <div class="col-sm-4">
                    <label class="form-label">Điểm số (Thang 10) <span class="required">*</span></label>
                    <input type="number" id="grade-score" step="0.5" min="0" max="10" class="form-control form-control-sm" value="${essay.assignedScore || 9.0}" required>
                  </div>
                  <div class="col-sm-8">
                    <label class="form-label">Lý do điều chỉnh điểm (Bắt buộc khi chấm lại)</label>
                    <input type="text" id="grade-reason" class="form-control form-control-sm" placeholder="Ghi nhận vào lịch sử phúc khảo...">
                  </div>
                </div>

                <div class="form-group mb-4">
                  <label class="form-label">Nhận xét của Giảng viên</label>
                  <textarea id="grade-comment" class="form-control form-control-sm" rows="3" placeholder="Nhận xét chi tiết cho sinh viên...">${essay.instructorComment || ''}</textarea>
                </div>

                <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                  <a href="#/instructor/grading-queue" class="btn btn-secondary btn-sm">Quay lại</a>
                  <button type="submit" class="btn btn-primary btn-sm">Lưu điểm & Công bố kết quả</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    saveGrade(attemptId, qId) {
      const score = document.getElementById('grade-score')?.value || 9.0;
      const comment = document.getElementById('grade-comment')?.value || '';
      const reason = document.getElementById('grade-reason')?.value || 'Giảng viên chấm điểm tự luận';

      window.PWD.store.gradeEssayAnswer(attemptId, qId, score, comment);
      window.PWD.components.showToast('Đã lưu điểm và thông báo cho sinh viên.', 'success');
      window.PWD.router.navigate('#/instructor/regrade-status/att_pending_02');
    },

    // 22. Regrade Job Status (Scenario 9)
    regradeStatus(params) {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Tiến trình Chấm lại Bài thi (Regrade Job)',
            subtitle: 'Trạng thái tính toán lại điểm sau khi cập nhật đáp án hoặc phúc khảo'
          })}

          <div class="card mb-4">
            <div class="card-body p-4 text-center">
              <div class="mb-2 text-success">${cmp.icon('checkCircle')}</div>
              <h4 class="page-title mb-1" style="font-size: 1.2rem;">Tiến trình chấm lại đã hoàn tất 100%</h4>
              <p class="text-caption text-muted mb-4">Đã tính toán lại điểm cho 38 bài thi. Bảng điểm đã đồng bộ.</p>
              ${cmp.progressBar(100, true)}
            </div>
          </div>

          <div class="text-center">
            <a href="#/instructor/dashboard" class="btn btn-primary btn-sm">Về Tổng quan Giảng viên</a>
          </div>
        </div>
      `;
    },

    // 23. Assessment Analytics
    analyticsAssessment(params) {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Phân tích Kết quả Bài thi: PWD301 Giữa kỳ',
          subtitle: 'Phổ điểm và tỷ lệ trả lời đúng theo từng câu hỏi'
        })}

        <div class="row g-3 mb-4">
          <div class="col-md-3">${cmp.statCard('Điểm trung bình', '7.8 / 10', '38 thí sinh', 'activity')}</div>
          <div class="col-md-3">${cmp.statCard('Điểm cao nhất', '10.0', '2 sinh viên', 'checkCircle')}</div>
          <div class="col-md-3">${cmp.statCard('Điểm thấp nhất', '5.5', '1 sinh viên', 'alertTriangle')}</div>
          <div class="col-md-3">${cmp.statCard('Tỷ lệ hoàn thành', '100%', '38 / 38 nộp bài', 'clock')}</div>
        </div>

        <div class="card">
          <div class="card-header">
            <h5 class="sub-title m-0">Tỷ lệ trả lời chính xác theo câu hỏi</h5>
          </div>
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Câu hỏi</th>
                  <th>Chủ đề</th>
                  <th>Độ khó</th>
                  <th>Tỷ lệ làm đúng</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Câu 1: Thuộc tính HttpOnly của Cookie</td>
                  <td>HTTP & Cookie</td>
                  <td><span class="badge badge-warning">Vừa</span></td>
                  <td>${cmp.progressBar(84, true)}</td>
                </tr>
                <tr>
                  <td>Câu 2: Application Factory Pattern</td>
                  <td>Flask</td>
                  <td><span class="badge badge-success">Dễ</span></td>
                  <td>${cmp.progressBar(92, true)}</td>
                </tr>
                <tr>
                  <td>Câu 3: Biện pháp phòng chống CSRF</td>
                  <td>Bảo mật Web</td>
                  <td><span class="badge badge-danger">Khó</span></td>
                  <td>${cmp.progressBar(65)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 24. Student Analytics
    analyticsStudents() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Phân tích Mức độ Tham gia của Sinh viên',
          subtitle: 'Theo dõi tiến độ học tập và kết quả của các học viên môn PWD301'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Học viên</th>
                  <th>Tiến độ bài giảng</th>
                  <th>Bài thực hành</th>
                  <th>Giữa kỳ</th>
                  <th>Trạng thái môn</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="fw-medium">Nguyễn Minh Anh</td>
                  <td>${cmp.progressBar(50)}</td>
                  <td>10.0 / 10</td>
                  <td>Chờ chấm luận</td>
                  <td><span class="badge badge-info">Đang học</span></td>
                </tr>
                <tr>
                  <td class="fw-medium">Phạm Thanh Tùng</td>
                  <td>${cmp.progressBar(85)}</td>
                  <td>9.0 / 10</td>
                  <td>8.5 / 10</td>
                  <td><span class="badge badge-info">Đang học</span></td>
                </tr>
                <tr>
                  <td class="fw-medium">Hoàng Bảo Ngọc</td>
                  <td>${cmp.progressBar(20)}</td>
                  <td>6.0 / 10</td>
                  <td>Chưa thi</td>
                  <td><span class="badge badge-danger">Tạm ngưng</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 25. Grade Export UI
    export() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Xuất Bảng điểm & Dữ liệu Môn học',
            subtitle: 'Trích xuất bảng điểm tổng kết ra định dạng Excel hoặc CSV'
          })}

          <div class="card">
            <div class="card-body">
              <div class="form-group mb-3">
                <label class="form-label">Chọn khóa học</label>
                <select class="form-select form-select-sm">
                  <option>PWD301 — Lập trình Web với Python & Flask</option>
                  <option>FED102 — HTML5, CSS3 & Thiết kế Web</option>
                </select>
              </div>

              <div class="form-group mb-4">
                <label class="form-label">Định dạng tệp tin</label>
                <div class="d-flex gap-3">
                  <label class="d-flex align-items-center gap-2">
                    <input type="radio" name="export-fmt" checked> <span>Excel (.xlsx)</span>
                  </label>
                  <label class="d-flex align-items-center gap-2">
                    <input type="radio" name="export-fmt"> <span>CSV (UTF-8)</span>
                  </label>
                </div>
              </div>

              <button class="btn btn-primary btn-sm w-100" onclick="PWD.components.showToast('Mô phỏng: Tệp bang_diem_PWD301.xlsx đã tải về máy.', 'success')">
                ${cmp.icon('download')} Tải xuống bảng điểm
              </button>
            </div>
          </div>
        </div>
      `;
    },

    // 26. Profile & Notifications
    profile() {
      const user = window.PWD.store.getCurrentUser() || window.PWD.store.state.personas.instructor;
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Hồ sơ Giảng viên',
            subtitle: 'Thông tin học hàm và cấu hình thông báo'
          })}

          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center gap-3 mb-4">
                <div class="topbar-brand-mark fs-4" style="width: 54px; height: 54px;">${user.avatar}</div>
                <div>
                  <h4 class="sub-title m-0">${user.name}</h4>
                  <div class="text-caption text-muted">${user.email} • Vai trò: Giảng viên</div>
                </div>
              </div>

              <div class="form-group mb-3">
                <label class="form-label">Bộ môn / Khoa</label>
                <input type="text" class="form-control form-control-sm" value="Bộ môn Kỹ thuật Phần mềm" readonly>
              </div>
              <div class="form-group mb-0">
                <label class="form-label">Số khóa học đang phụ trách</label>
                <input type="text" class="form-control form-control-sm" value="3 khóa học" readonly>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  };

  window.PWD.views.instructor = instructorViews;
})();
