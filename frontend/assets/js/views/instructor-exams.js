/**
 * PWD301 Instructor Exam Studio - Dedicated Sub-Pages & Interactive Authoring
 * 
 * Implements dedicated standalone pages for the 4 exam creation methods:
 * 1. Hub & File Dropzone (#/instructor/exams)
 * 2a. Split-View Raw Syntax Editor (#/instructor/exams/editor) - Starts empty + User Guide popup
 * 2b. Visual Interactive Builder (#/instructor/exams/interactive) - Drag & drop, Fill-in, Matching
 * 2c. Excel Import Studio (#/instructor/exams/excel) - Template download, Parse, Validation Grid
 * 2d. LMS Moodle XML & JSON Studio (#/instructor/exams/moodle) - Upload & Direct Code Paste
 * 3. Academic Governance Matrix (#/instructor/exams/matrix)
 * 4. Proctoring & Exam Publishing (#/instructor/exams/settings)
 */

(function () {
  const InstructorView = window.InstructorView || {};

  InstructorView.readExamPolicy = function (root = document) {
    return {
      exam_layout: root.getElementById('cfg-exam-layout')?.value || 'STANDARD',
      monitoring_enabled: Boolean(root.getElementById('cfg-monitoring')?.checked),
      request_fullscreen: Boolean(root.getElementById('cfg-fullscreen')?.checked)
    };
  };

  InstructorView.resolvePastedExamImages = function (text, assetIds) {
    return text.replace(/\[\[PWD301:PASTE_IMAGE:(\d+)\]\]/g, (_, index) => {
      const assetId = assetIds[Number(index)];
      if (!assetId || !/^[0-9a-f-]{36}$/i.test(assetId)) {
        throw new Error('Ảnh trong đề thi chưa được tải lên hợp lệ.');
      }
      return `[[PWD301:IMAGE:${assetId}]]`;
    });
  };

  InstructorView.isInteractiveFillAnswerCorrect = function (submitted, acceptedAnswers) {
    if (!Array.isArray(submitted) || !submitted.length) return false;
    const acceptedGroups = String(acceptedAnswers || '').split(';').map(group =>
      group.split(',').map(answer => answer.trim().normalize('NFKC').toLowerCase()).filter(Boolean)
    );
    return submitted.length === acceptedGroups.length
      && submitted.every((answer, index) =>
        acceptedGroups[index].includes(String(answer).trim().normalize('NFKC').toLowerCase())
      );
  };

  InstructorView.buildInteractiveMatchPreview = function (pairs) {
    const complete = (pairs || []).filter(pair => pair.left && pair.right);
    const options = complete.map(pair => pair.right);
    return complete.map(pair => ({ left: pair.left, expected: pair.right, options: [...options] }));
  };

  // =========================================================================
  // 1. Unified Sticky Workflow Header
  // =========================================================================
  InstructorView.renderExamWorkflowHeader = function (activeStep, stepTitle, nextRoute, nextLabel, onNextAction) {
    const draft = window.ExamStore ? window.ExamStore.getDraft() : { title: 'De_thi_moi.docx', questions: [] };
    const qCount = (draft.questions || []).length;
    const currentTitle = draft.title || 'De_thi_moi.docx';
    const step2Route = draft.sourceMethod === 'manual' ? 'editor' : draft.sourceMethod;
    const canVisit = step => window.ExamStore?.canVisitStep(step);

    return `
      <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xs select-none shrink-0">
        <div class="max-w-[1920px] mx-auto px-3 sm:px-5 h-14 flex items-center justify-between gap-3">
          
          <!-- Left: Back & Exam Title -->
          <div class="flex items-center gap-2.5 min-w-0">
            <button type="button" id="workflow-back-btn" class="flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Quay lại">
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
            </button>

            <div class="flex items-center max-w-sm sm:max-w-md w-full relative gap-2">
              <input
                type="text"
                id="workflow-exam-title-input"
                class="text-xs sm:text-sm font-semibold text-slate-800 dark:text-white bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-indigo-500 rounded-lg px-2.5 py-1 w-full transition-all truncate focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-indigo-500/20"
                value="${UI.escapeHtml(currentTitle)}"
                title="Nhấp để đổi tên đề thi"
              />
              <span id="workflow-course-badge" class="${(draft.courseCode || draft.courseTitle) ? '' : 'hidden'} hidden sm:inline-flex items-center px-2 py-0.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 font-bold text-[11px] border border-indigo-200/60 dark:border-indigo-800 shrink-0" title="Môn học đang chọn">
                ${UI.escapeHtml(draft.courseCode || draft.courseTitle || '')}
              </span>
            </div>
          </div>

          <!-- Center: 4-Step Stepper Navigation -->
          <nav class="hidden lg:flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-xl border border-slate-200 dark:border-slate-700">
            <!-- Step 1 -->
            <a
              href="#/instructor/exams"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 1 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 1 ? 'bg-indigo-600 text-white font-bold' : (activeStep > 1 ? 'bg-emerald-600 text-white' : 'border border-slate-300 text-slate-600')}">
                ${activeStep > 1 ? '✓' : '1'}
              </span>
              <span>Nạp đề & Chọn cách</span>
            </a>

            <!-- Step 2 -->
            <a
              ${canVisit(2) ? `href="#/instructor/exams/${step2Route}"` : 'aria-disabled="true" tabindex="-1"'}
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 2 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 2 ? 'bg-indigo-600 text-white font-bold' : (activeStep > 2 ? 'bg-emerald-600 text-white' : 'border border-slate-300 text-slate-600')}">
                ${activeStep > 2 ? '✓' : '2'}
              </span>
              <span>${stepTitle || 'Soạn thảo & Nhập liệu'}</span>
            </a>

            <!-- Step 3 -->
            <a
              ${canVisit(3) ? 'href="#/instructor/exams/matrix"' : 'aria-disabled="true" tabindex="-1"'}
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 3 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 3 ? 'bg-indigo-600 text-white font-bold' : (activeStep > 3 ? 'bg-emerald-600 text-white' : 'border border-slate-300 text-slate-600')}">
                ${activeStep > 3 ? '✓' : '3'}
              </span>
              <span>Kiểm tra đề</span>
            </a>

            <!-- Step 4 -->
            <a
              ${canVisit(4) ? 'href="#/instructor/exams/settings"' : 'aria-disabled="true" tabindex="-1"'}
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 4 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 4 ? 'bg-indigo-600 text-white font-bold' : 'border border-slate-300 text-slate-600'}">
                4
              </span>
              <span>Cấu hình phòng thi</span>
            </a>
          </nav>

          <!-- Right: Sync Indicator & Next Action -->
          <div class="flex items-center gap-2">
            <div class="hidden md:flex items-center gap-1.5 text-xs text-slate-500 mr-1">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span id="workflow-sync-badge">${qCount} câu • Tự động lưu</span>
            </div>

            ${nextLabel ? `
              <button
                type="button"
                id="workflow-top-next-btn"
                class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-lg text-xs font-bold shadow-sm transition-all"
              >
                <span>${nextLabel}</span>
                <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            ` : ''}
          </div>

        </div>
      </header>
    `;
  };

  InstructorView.bindExamWorkflowHeaderEvents = function (activeStep, nextRoute, onNextAction) {
    const titleInput = document.getElementById('workflow-exam-title-input');
    if (titleInput) {
      titleInput.addEventListener('change', (e) => {
        const val = e.target.value.trim() || 'Bài kiểm tra mới';
        window.ExamStore.saveDraft({ title: val });
        UI.showToast(`Đã đổi tên đề thi: ${val}`, 'info');
      });
    }

    const backBtn = document.getElementById('workflow-back-btn');
    if (backBtn) {
      backBtn.onclick = () => {
        if (activeStep === 1) {
          window.location.hash = '#/instructor/dashboard';
        } else if (activeStep === 2) {
          window.location.hash = '#/instructor/exams';
        } else if (activeStep === 3) {
          window.location.hash = '#/instructor/exams/editor';
        } else if (activeStep === 4) {
          window.location.hash = '#/instructor/exams/matrix';
        }
      };
    }

    const nextBtn = document.getElementById('workflow-top-next-btn');
    if (nextBtn) {
      nextBtn.onclick = () => {
        if (typeof onNextAction === 'function') {
          onNextAction();
        } else if (nextRoute) {
          window.location.hash = nextRoute;
        }
      };
    }
  };


  // =========================================================================
  // 2. PAGE 1: Hub & File Upload Dropzone (#/instructor/exams)
  // =========================================================================
  InstructorView.renderExamsHub = function (container, query = {}) {
    const draft = window.ExamStore.getDraft();
    const hasDraft = window.ExamStore.hasDraft();

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(1, 'Chọn phương thức', null, null)}

        <main class="flex-1 overflow-y-auto max-w-[1440px] mx-auto px-4 sm:px-6 py-8 w-full pb-24">
          
          <!-- Page Heading -->
          <div class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                Chọn cách tạo đề
              </h1>
              <p class="mt-1 text-sm text-slate-500">
                Chọn môn học, rồi tải tệp hoặc tự soạn câu hỏi.
              </p>
            </div>
            <button type="button" onclick="window.location.hash = '#/instructor/dashboard'" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors self-start md:self-auto">
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Quay lại Trang chủ</span>
            </button>
          </div>

          <!-- Course Scope Selection Card -->
          <div class="mb-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 sm:p-5 shadow-xs">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-[22px]">school</span>
                </div>
                <div>
                  <h3 class="font-bold text-sm text-slate-900 dark:text-white">Môn học</h3>
                  <p class="text-xs text-slate-500">Đề thi sẽ thuộc môn học bạn chọn.</p>
                </div>
              </div>
              <div class="w-full sm:w-80 shrink-0">
                <select id="hub-course-select" class="w-full h-10 px-3 text-xs sm:text-sm font-semibold rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors">
                  <option value="">-- Đang tải danh sách môn học... --</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Draft Restore Alert Banner -->
          <div id="hub-draft-alert-box" class="${hasDraft ? '' : 'hidden'} mb-6 p-4 rounded-2xl bg-indigo-50/90 dark:bg-indigo-950/40 border-2 border-indigo-300 dark:border-indigo-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center material-symbols-outlined text-[22px] shrink-0 shadow-xs">
                history_edu
              </div>
              <div>
                <h4 class="font-bold text-sm text-indigo-950 dark:text-indigo-200">Tìm thấy bản nháp đề thi đang soạn dở</h4>
                <p class="text-xs text-indigo-700 dark:text-indigo-300">
                  <strong>${UI.escapeHtml(draft.title || 'De_thi_moi.docx')}</strong> • ${draft.questions ? draft.questions.length : 0} câu hỏi đã lưu.
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button type="button" id="btn-hub-resume-draft" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-xs flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">restore</span>
                <span>Tiếp tục soạn bản nháp</span>
              </button>
              <button type="button" id="btn-hub-discard-draft" class="px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition">
                Tạo đề mới (Xóa nháp)
              </button>
            </div>
          </div>

          <!-- Dual Column Split Layout -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            <!-- Left Column: File Dropzone Area -->
            <div class="lg:col-span-7 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-xs flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-4">
                  <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>Tải tệp đề thi</span>
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Tự đọc câu hỏi
                    </span>
                  </h2>
                </div>

                <!-- Drop Target -->
                <div class="dashed-dropzone relative rounded-2xl p-8 sm:p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30 hover:bg-indigo-50/20 group" id="hub-drop-target">
                  <input type="file" id="hub-file-input" accept=".docx,.pdf,.xlsx,.txt,.md" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                  <div class="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center mb-4 transition-transform group-hover:scale-110 shadow-xs">
                    <span class="material-symbols-outlined text-3xl">cloud_upload</span>
                  </div>
                  <p class="text-base font-semibold text-slate-800 dark:text-slate-200 mb-1">
                    Kéo tệp vào đây hoặc <span class="text-indigo-600 underline underline-offset-2">chọn tệp</span>
                  </p>
                  <p class="text-xs sm:text-sm text-slate-500 max-w-md mb-2">
                    <span class="font-medium text-slate-700 dark:text-slate-300">.docx, .pdf, .txt, .md, .xlsx</span>
                  </p>
                  <button type="button" id="btn-hub-quick-sample" class="mt-4 px-4 py-2 bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold rounded-lg text-xs hover:bg-indigo-600 hover:text-white transition-colors">
                    Xem đề mẫu
                  </button>
                </div>

                <!-- Optional file-format help -->
                <details class="mt-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300">
                  <summary class="cursor-pointer font-bold text-sm text-slate-900 dark:text-white">Hướng dẫn định dạng tệp</summary>
                  <div class="mt-3 space-y-1.5 text-slate-600 dark:text-slate-300 text-xs">
                    <div><strong>1. Đầu đề:</strong> Bắt đầu bằng <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">Câu 1:</code>, <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">Câu 1.</code> hoặc <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">1.</code></div>
                    <div><strong>2. Phương án:</strong> Bắt đầu bằng <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">A.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">B.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">C.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">D.</code></div>
                    <div><strong>3. Đáp án đúng:</strong> Đặt dấu hoa thị <code class="bg-rose-100 text-rose-600 font-bold px-1 rounded">*</code> ngay trước chữ cái (ví dụ: <code class="text-rose-600 font-bold">*A.</code>)</div>
                    <div><strong>4. Lời giải:</strong> Bắt đầu bằng <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">Lời giải:</code> hoặc <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">Giải thích:</code></div>
                  </div>
                </details>
              </div>
            </div>

            <!-- Right Column: 4 Dedicated Online Methods -->
            <div class="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-7 shadow-xs">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div class="flex items-center gap-2">
                  <h2 class="text-lg font-bold text-slate-900 dark:text-white">Tự tạo đề</h2>
                </div>
              </div>

              <div class="space-y-3.5">
                
                <!-- Method 1: Tự soạn Đề thi / Bài tập -->
                <a
                  href="#/instructor/exams/editor"
                  data-exam-method="manual"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 hover:bg-indigo-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">edit_document</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                        <span>Soạn câu hỏi</span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Gõ hoặc dán nội dung đề thi.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 2: Tạo đề thi tương tác [MỚI] -->
                <a
                  href="#/instructor/exams/interactive"
                  data-exam-method="interactive"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-teal-500 hover:bg-teal-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800 text-teal-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">extension</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors flex items-center justify-between">
                        <span class="flex items-center gap-2">
                          Tạo đề thi tương tác
                          <span class="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-rose-500 text-white">Mới</span>
                        </span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Tạo câu kéo thả, điền từ và ghép đôi.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 3: Tạo đề từ tệp Excel -->
                <a
                  href="#/instructor/exams/excel"
                  data-exam-method="excel"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-emerald-500 hover:bg-emerald-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">table_view</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 transition-colors flex items-center justify-between">
                        <span>Tạo đề từ tệp Excel</span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Dùng bảng tính để thêm nhiều câu hỏi.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 4: Nạp từ chuẩn LMS Moodle XML / JSON -->
                <a
                  href="#/instructor/exams/moodle"
                  data-exam-method="moodle"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-amber-500 hover:bg-amber-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">code_blocks</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-amber-600 transition-colors flex items-center justify-between">
                        <span>Nhập tệp Moodle XML / JSON</span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Tải tệp hoặc dán nội dung câu hỏi.
                      </p>
                    </div>
                  </div>
                </a>

              </div>
            </div>

          </div>
        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(1, null);

    container.querySelectorAll('[data-exam-method]').forEach(link => {
      link.addEventListener('click', event => {
        const courseId = window.ExamStore.getDraft().courseId;
        if (!courseId) {
          event.preventDefault();
          UI.showToast('Hãy chọn môn học trước khi soạn đề.', 'warning');
          return;
        }
        window.ExamStore.saveDraft({
          sourceMethod: link.dataset.examMethod,
          methodSelected: true,
          matrixConfirmed: false
        });
      });
    });

    // Course Loader & Auto-Scoping
    const hubCourseSelect = document.getElementById('hub-course-select');
    const headerCourseBadge = document.getElementById('workflow-course-badge');
    const targetCourseId = (query && query.course_id) || new URLSearchParams(window.location.hash.split('?')[1] || '').get('course_id') || draft.courseId;

    ApiClient.getInstructorCourses().then(res => {
      const courses = (res && res.data && Array.isArray(res.data.courses))
        ? res.data.courses
        : (res && Array.isArray(res.courses) ? res.courses : []);
      if (!hubCourseSelect) return;

      if (courses.length === 0) {
        hubCourseSelect.innerHTML = `<option value="">Chưa có môn học nào</option>`;
        return;
      }

      // Find matching course or default to first course in list
      let selectedCourse = null;
      if (targetCourseId) {
        selectedCourse = courses.find(c => String(c.course_id || c.id || c.course_code) === String(targetCourseId));
      }
      if (!selectedCourse) {
        selectedCourse = courses[0];
      }

      const activeCourseId = selectedCourse.course_id || selectedCourse.id || selectedCourse.course_code;

      // Update draft and workflow header badge
      window.ExamStore.saveDraft({
        courseId: activeCourseId,
        courseCode: selectedCourse.course_code,
        courseTitle: selectedCourse.title
      });

      if (headerCourseBadge) {
        headerCourseBadge.textContent = selectedCourse.course_code || selectedCourse.title;
        headerCourseBadge.classList.remove('hidden');
      }

      hubCourseSelect.innerHTML = courses.map(c => {
        const cid = c.course_id || c.id || c.course_code;
        const isSel = String(cid) === String(activeCourseId);
        return `<option value="${cid}" ${isSel ? 'selected' : ''}>${c.course_code} - ${c.title}</option>`;
      }).join('');

      hubCourseSelect.addEventListener('change', (e) => {
        const chosen = courses.find(c => String(c.course_id || c.id || c.course_code) === String(e.target.value));
        if (chosen) {
          const chosenId = chosen.course_id || chosen.id || chosen.course_code;
          window.ExamStore.saveDraft({
            courseId: chosenId,
            courseCode: chosen.course_code,
            courseTitle: chosen.title
          });
          if (headerCourseBadge) {
            headerCourseBadge.textContent = chosen.course_code || chosen.title;
            headerCourseBadge.classList.remove('hidden');
          }
          UI.showToast(`Đã chọn môn học: ${chosen.course_code} - ${chosen.title}`, 'info');
        }
      });
    }).catch(err => {
      console.warn('Lỗi nạp danh sách môn học tại Hub đề thi:', err);
      if (hubCourseSelect) {
        hubCourseSelect.innerHTML = `<option value="">Lỗi tải danh mục môn học</option>`;
      }
    });

    // Resume / Discard draft
    document.getElementById('btn-hub-resume-draft')?.addEventListener('click', () => {
      const draft = window.ExamStore.getDraft() || {};
      if (!draft.courseId) {
        let fallbackCourseId = document.getElementById('hub-course-select')?.value;
        if (!fallbackCourseId) {
          const selectElem = document.getElementById('hub-course-select');
          if (selectElem && selectElem.options.length > 0) {
            for (let opt of selectElem.options) {
              if (opt.value) { fallbackCourseId = opt.value; break; }
            }
          }
        }
        if (fallbackCourseId) {
          window.ExamStore.saveDraft({ courseId: fallbackCourseId });
        }
      }
      if (!window.ExamStore.canVisitStep(2)) {
        UI.showToast('Hãy chọn môn học và cách tạo đề để tiếp tục.', 'warning');
        return;
      }
      const method = window.ExamStore.getDraft().sourceMethod;
      window.location.hash = `#/instructor/exams/${method === 'manual' ? 'editor' : method}`;
    });

    document.getElementById('btn-hub-discard-draft')?.addEventListener('click', () => {
      window.ExamStore.clearDraft();
      document.getElementById('hub-draft-alert-box')?.classList.add('hidden');
      UI.showToast('Đã xóa bản nháp cũ. Bạn có thể bắt đầu tạo đề thi mới!', 'info');
    });

    // File dropzone
    const dropTarget = document.getElementById('hub-drop-target');
    const fileInput = document.getElementById('hub-file-input');

    const handleFile = async (file) => {
      if (!file) return;
      const ext = (file.name.split('.').pop() || '').toLowerCase();
      UI.showToast(`Đang bóc tách tệp: ${file.name}...`, 'info');

      try {
        if (ext === 'xlsx' || ext === 'xls') {
          // Route to Excel studio
          const res = await ApiClient.parseExcelExam(file);
          if (res && res.success && res.questions && res.questions.length > 0) {
            window.ExamStore.replaceQuestions(res.questions);
            window.ExamStore.saveDraft({ title: file.name.replace(/\.[^/.]+$/, ''), sourceMethod: 'excel', methodSelected: true });
            UI.showToast(`Đã bóc tách thành công ${res.total_questions} câu hỏi từ tệp Excel!`, 'success');
            window.location.hash = '#/instructor/exams/excel';
            return;
          }
        }

        let rawContent = '';
        if (ext === 'txt' || ext === 'md') {
          rawContent = await file.text();
        } else if (ext === 'docx' || ext === 'pdf') {
          const res = await ApiClient.parseExamFile(file);
          rawContent = res.raw_text || res.text || '';
        } else {
          rawContent = await file.text();
        }

        if (rawContent && rawContent.trim().length > 0) {
          const parsed = ExamParser.parseExamRaw(rawContent, 100.0);
          const currentDraft = window.ExamStore.getDraft() || {};
          let courseId = currentDraft.courseId || document.getElementById('hub-course-select')?.value;
          if (!courseId) {
            const selectElem = document.getElementById('hub-course-select');
            if (selectElem && selectElem.options.length > 0) {
              for (let opt of selectElem.options) {
                if (opt.value) { courseId = opt.value; break; }
              }
            }
          }
          window.ExamStore.saveDraft({
            title: file.name.replace(/\.[^/.]+$/, ''),
            rawText: rawContent,
            questions: parsed.questions,
            sourceMethod: 'manual',
            methodSelected: true,
            courseId: courseId || ''
          });
          UI.showToast(`Đã bóc tách thành công ${parsed.questions.length} câu hỏi từ tệp!`, 'success');
          window.location.hash = '#/instructor/exams/editor';
        } else {
          UI.showToast('Tệp rỗng hoặc không chứa nội dung văn bản hợp lệ.', 'warning');
        }
      } catch (err) {
        console.error('Lỗi nạp tệp đề thi:', err);
        UI.showToast(`Lỗi bóc tách tệp: ${err.message || err}`, 'error');
      }
    };

    dropTarget?.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropTarget.classList.add('bg-indigo-50/50', 'border-indigo-500');
    });
    dropTarget?.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropTarget.classList.remove('bg-indigo-50/50', 'border-indigo-500');
    });
    dropTarget?.addEventListener('drop', (e) => {
      e.preventDefault();
      dropTarget.classList.remove('bg-indigo-50/50', 'border-indigo-500');
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) handleFile(files[0]);
    });
    fileInput?.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    document.getElementById('btn-hub-quick-sample')?.addEventListener('click', () => {
      const sampleText = ExamParser.generateSampleTemplate('standard');
      const parsed = ExamParser.parseExamRaw(sampleText, 40.0);
      window.ExamStore.saveDraft({
        title: 'De_thi_mau_chuan_hoa.docx',
        rawText: sampleText,
        questions: parsed.questions,
        sourceMethod: 'manual',
        methodSelected: true
      });
      UI.showToast('Đã nạp đề thi mẫu De_thi_mau.docx!', 'success');
      window.location.hash = '#/instructor/exams/editor';
    });
  };


  // =========================================================================
  // 3. PAGE 2a: Split-View Raw Syntax Editor (#/instructor/exams/editor)
  //    Starts EMPTY by default + Rich User Guide Modal Popup
  // =========================================================================
  InstructorView.renderExamEditor = function (container) {
    const draft = window.ExamStore.getDraft();
    const hasExistingText = Boolean(draft.rawText && draft.rawText.trim().length > 0);
    const initialText = hasExistingText ? draft.rawText : '';

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(2, 'Tự soạn đề thi', '#/instructor/exams/matrix', 'Tiếp tục: Ma trận học vụ')}

        <!-- Sub-Toolbar -->
        <div class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-2 flex flex-wrap items-center justify-between gap-2.5 text-xs shrink-0 select-none">
          <div class="flex items-center flex-wrap gap-2">
            <button type="button" id="editor-btn-divide-points" class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-xs transition-colors" title="Chia điểm đều cho tất cả câu hỏi">
              <span class="material-symbols-outlined text-[16px]">calculate</span>
              <span>Chia điểm</span>
            </button>
            <div class="flex items-center gap-1.5 pl-2 border-l border-slate-200 dark:border-slate-800">
              <span class="text-slate-500 font-medium">Đi đến câu</span>
              <input type="number" id="editor-jump-input" min="1" max="100" value="1" class="w-12 px-1.5 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded-md text-center font-bold outline-none focus:border-indigo-500 bg-white dark:bg-slate-800" />
              <button type="button" id="editor-jump-btn" class="px-2.5 py-1 bg-indigo-600 text-white rounded-md font-bold hover:bg-indigo-700">Đến</button>
            </div>
            <div class="hidden xl:flex items-center gap-1.5 pl-3 border-l border-slate-200 dark:border-slate-800 text-slate-500 text-[11px]">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span id="editor-syntax-status">Sẵn sàng • Tự động lưu</span>
            </div>
          </div>

          <div class="flex items-center flex-wrap gap-1.5 text-xs">
            <!-- Prominent User Guide Button -->
            <button
              type="button"
              id="editor-btn-open-guide"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 rounded-lg border border-indigo-200 dark:border-indigo-800 font-bold transition-all shadow-xs"
              title="Xem hướng dẫn chi tiết quy chuẩn cú pháp soạn thảo"
            >
              <span class="material-symbols-outlined text-[16px]">help_outline</span>
              <span>Hướng dẫn cú pháp & Sử dụng</span>
            </button>
            <button type="button" id="editor-btn-latex" class="inline-flex items-center gap-1 px-2.5 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium" title="Chèn ký hiệu toán học LaTeX">
              <span class="font-serif italic font-bold">Σ</span>
              <span class="hidden md:inline">Chèn công thức</span>
            </button>
            <button type="button" onclick="window.location.hash = '#/instructor/exams/interactive'" class="inline-flex items-center gap-1 px-2.5 py-1.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-medium" title="Mở bộ tạo câu hỏi tương tác kéo thả / điền từ">
              <span class="material-symbols-outlined text-[16px] text-teal-600">extension</span>
              <span>Dạng tương tác</span>
            </button>
          </div>
        </div>

        <!-- 50/50 Split View Workspace -->
        <div class="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200 dark:divide-slate-800 overflow-hidden bg-white dark:bg-slate-900">
          
          <!-- LEFT COLUMN: Visual Question Cards & In-Place Editing -->
          <div class="overflow-y-auto p-4 sm:p-5 space-y-4 bg-slate-50/60 dark:bg-slate-950/60 h-full pb-36 scroll-smooth" id="editor-preview-container">
            <!-- Dynamically populated question cards or Empty State -->
          </div>

          <!-- RIGHT COLUMN: Raw Text Code Editor & Syntax Inspector -->
          <div class="flex flex-col h-full min-h-0 bg-white dark:bg-slate-900 select-text">
            <div class="bg-slate-50/80 dark:bg-slate-800/80 px-4 py-1.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 select-none shrink-0">
              <div class="flex items-center gap-2">
                <span class="font-mono text-slate-600 dark:text-slate-300 font-semibold">Trình soạn thảo cú pháp</span>
                <span class="text-slate-300">|</span>
                <span>Ký tự <code class="text-red-600 font-bold bg-red-50 dark:bg-red-950 px-1 rounded">*</code> trước đáp án = ĐÁP ÁN ĐÚNG</span>
              </div>
              <button type="button" id="editor-btn-sync" class="flex items-center gap-1 text-slate-600 hover:text-indigo-600 cursor-pointer font-semibold">
                <span class="material-symbols-outlined text-[15px] text-indigo-600">sync</span>
                <span>Đồng bộ xem trước</span>
              </button>
            </div>

            <!-- Textarea with Line Numbers (STARTS COMPLETELY EMPTY BY DEFAULT) -->
            <div class="flex-1 min-h-0 flex overflow-hidden">
              <div class="w-10 py-3 pr-2 text-right font-mono text-xs text-slate-400 select-none border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50" id="editor-line-numbers">
                <!-- Line numbers -->
              </div>
              <textarea
                id="editor-raw-textarea"
                class="flex-1 p-3 pb-36 font-mono text-xs sm:text-sm text-slate-900 dark:text-white bg-white dark:bg-slate-900 outline-none resize-none leading-relaxed border-0 overflow-auto"
                spellcheck="false"
                placeholder="Khung soạn thảo đang trống. Bạn có thể tự gõ nội dung đề thi tại đây theo cú pháp:&#10;&#10;Câu 1: Nội dung câu hỏi...&#10;*A. Phương án đúng&#10;B. Phương án sai&#10;C. Phương án sai&#10;D. Phương án sai&#10;Lời giải: Giải thích chi tiết...&#10;&#10;(Nhấn nút 'Hướng dẫn cú pháp & Sử dụng' phía trên để xem chi tiết)"
              >${UI.escapeHtml(initialText)}</textarea>
            </div>

            <!-- Bottom Sample Bar -->
            <div class="border-t border-slate-200 dark:border-slate-800 px-4 py-2 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs text-slate-500 shrink-0 select-none">
              <div class="flex items-center gap-2 overflow-x-auto">
                <span class="font-semibold text-slate-700 dark:text-slate-300 shrink-0">Chèn nội dung mẫu:</span>
                <button type="button" class="text-indigo-600 hover:underline shrink-0 editor-load-tmpl-btn" data-tmpl="standard">Mẫu trắc nghiệm chuẩn</button>
                <span class="text-slate-300">|</span>
                <button type="button" class="text-indigo-600 hover:underline shrink-0 editor-load-tmpl-btn" data-tmpl="fill">Mẫu điền từ</button>
                <span class="text-slate-300">|</span>
                <button type="button" class="text-indigo-600 hover:underline shrink-0 font-bold editor-load-tmpl-btn" data-tmpl="all">Mẫu tổng hợp (6 câu)</button>
              </div>
              <button type="button" id="editor-btn-clear-all" class="text-rose-600 hover:underline shrink-0 text-xs font-semibold">
                Làm trống khung soạn
              </button>
            </div>
          </div>

        </div>

        <!-- ================================================================ -->
        <!-- POPUP: Hướng dẫn sử dụng & Quy chuẩn soạn thảo cú pháp             -->
        <!-- ================================================================ -->
        <div id="modal-syntax-guide" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm hidden animate-fade-in">
          <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            
            <!-- Modal Header -->
            <div class="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-indigo-50/40 dark:bg-indigo-950/30">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold shadow-xs">
                  <span class="material-symbols-outlined text-[22px]">menu_book</span>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900 dark:text-white">Hướng dẫn Quy chuẩn Soạn thảo Đề thi</h3>
                  <p class="text-xs text-slate-500">Cú pháp chuẩn hóa giúp hệ thống tự động bóc tách câu hỏi và đáp án chính xác 100%</p>
                </div>
              </div>
              <button type="button" id="btn-close-syntax-guide" class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <span class="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 overflow-y-auto space-y-4 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              
              <!-- Rule 1 -->
              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 mt-0.5 text-xs">1</span>
                <div>
                  <strong class="text-slate-900 dark:text-white text-sm">Đầu đề câu hỏi:</strong>
                  <p class="mt-0.5">Bắt đầu bằng <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1.5 py-0.5 rounded">Câu 1:</code>, <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1.5 py-0.5 rounded">Câu 1.</code>, <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1.5 py-0.5 rounded">Question 1:</code> hoặc chỉ đơn giản là số thứ tự <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1.5 py-0.5 rounded">1.</code> ở đầu dòng.</p>
                </div>
              </div>

              <!-- Rule 2 -->
              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 mt-0.5 text-xs">2</span>
                <div>
                  <strong class="text-slate-900 dark:text-white text-sm">Các phương án lựa chọn:</strong>
                  <p class="mt-0.5">Bắt đầu bằng chữ cái in hoa <code class="bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white font-bold px-1.5 py-0.5 rounded">A.</code>, <code class="bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white font-bold px-1.5 py-0.5 rounded">B.</code>, <code class="bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white font-bold px-1.5 py-0.5 rounded">C.</code>, <code class="bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white font-bold px-1.5 py-0.5 rounded">D.</code> (mỗi phương án trên một dòng riêng hoặc phân tách rõ ràng trên cùng một dòng).</p>
                </div>
              </div>

              <!-- Rule 3 -->
              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 mt-0.5 text-xs">3</span>
                <div>
                  <strong class="text-slate-900 dark:text-white text-sm">Đánh dấu đáp án đúng:</strong>
                  <p class="mt-0.5">Thêm dấu hoa thị <code class="bg-rose-100 text-rose-600 font-bold px-1.5 py-0.5 rounded">*</code> ngay trước chữ cái phương án đúng (Ví dụ: <code class="text-rose-600 font-bold bg-rose-50 px-1 py-0.5 rounded">*A. Nội dung đáp án đúng</code>) hoặc ghi bảng đáp án ở cuối câu: <code class="font-mono bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded">Đáp án: A</code>.</p>
                </div>
              </div>

              <!-- Rule 4 -->
              <div class="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 mt-0.5 text-xs">4</span>
                <div>
                  <strong class="text-slate-900 dark:text-white text-sm">Lời giải & Công thức:</strong>
                  <p class="mt-0.5">Bắt đầu bằng <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1.5 py-0.5 rounded">Lời giải:</code> hoặc <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1.5 py-0.5 rounded">Giải thích:</code>. Đối với công thức toán học/khoa học, đặt giữa cặp dấu <code class="bg-slate-200 dark:bg-slate-700 font-mono px-1 rounded">$...$</code> hoặc <code class="bg-slate-200 dark:bg-slate-700 font-mono px-1 rounded">$$...$$</code>.</p>
                </div>
              </div>

              <!-- Example Box -->
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <span class="font-bold text-slate-800 dark:text-slate-200">Đoạn cú pháp ví dụ mẫu chuẩn:</span>
                  <button type="button" id="btn-guide-copy-example" class="text-indigo-600 font-bold hover:underline flex items-center gap-1">
                    <span class="material-symbols-outlined text-[15px]">content_copy</span>
                    <span>Sao chép ví dụ</span>
                  </button>
                </div>
                <pre class="bg-slate-900 text-indigo-200 rounded-xl p-3.5 font-mono text-[11px] leading-relaxed select-all overflow-x-auto" id="guide-code-example">Câu 1. Đâu là giao thức truyền tải siêu văn bản có mã hóa SSL/TLS?
A. HTTP
*B. HTTPS
C. FTP
D. Telnet
Lời giải: HTTPS (Hypertext Transfer Protocol Secure) sử dụng chứng chỉ mã hóa SSL/TLS để bảo vệ dữ liệu.

Câu 2: Ràng buộc toàn vẹn tham chiếu được duy trì qua ___.
A. Primary Key
*B. Foreign Key
C. Unique Index
D. Check Constraint
Lời giải: Khóa ngoại tham chiếu đến khóa chính bảng khác.</pre>
              </div>

            </div>

            <!-- Modal Footer -->
            <div class="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 flex flex-col sm:flex-row items-center justify-between gap-3">
              <label class="flex items-center gap-2 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none">
                <input type="checkbox" id="chk-guide-dont-show-again" class="rounded text-indigo-600 focus:ring-indigo-500" />
                <span>Không tự động hiển thị popup này trong các lần soạn thảo sau</span>
              </label>
              <div class="flex items-center gap-2 w-full sm:w-auto">
                <button type="button" id="btn-guide-insert-sample" class="w-full sm:w-auto px-3.5 py-2 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold text-xs hover:bg-indigo-100 transition-colors">
                  Chèn ví dụ mẫu vào đề
                </button>
                <button type="button" id="btn-guide-got-it" class="w-full sm:w-auto px-5 py-2 rounded-xl bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 shadow-xs transition-colors">
                  Đã hiểu & Bắt đầu soạn
                </button>
              </div>
            </div>

          </div>
        </div>

      </div>
    `;

    // Bind Workflow Header
    InstructorView.bindExamWorkflowHeaderEvents(2, '#/instructor/exams/matrix', () => {
      onProceedToMatrix();
    });

    const textarea = document.getElementById('editor-raw-textarea');
    const previewContainer = document.getElementById('editor-preview-container');
    const lineNumbersBox = document.getElementById('editor-line-numbers');
    const syntaxModal = document.getElementById('modal-syntax-guide');
    const chkDontShow = document.getElementById('chk-guide-dont-show-again');

    // Auto-popup logic: If never hidden and textarea is empty, pop up automatically!
    const hideGuidePref = localStorage.getItem('pwd301_hide_syntax_guide');
    if (hideGuidePref !== 'true' && (!initialText || initialText.trim().length === 0)) {
      syntaxModal?.classList.remove('hidden');
    }

    // Modal controls
    const closeGuide = () => {
      if (chkDontShow?.checked) {
        localStorage.setItem('pwd301_hide_syntax_guide', 'true');
      }
      syntaxModal?.classList.add('hidden');
    };

    document.getElementById('btn-close-syntax-guide')?.addEventListener('click', closeGuide);
    document.getElementById('btn-guide-got-it')?.addEventListener('click', closeGuide);
    document.getElementById('editor-btn-open-guide')?.addEventListener('click', () => {
      syntaxModal?.classList.remove('hidden');
    });

    document.getElementById('btn-guide-copy-example')?.addEventListener('click', async () => {
      const ex = document.getElementById('guide-code-example')?.innerText || '';
      try {
        await navigator.clipboard.writeText(ex);
        UI.showToast('Đã sao chép ví dụ mẫu vào clipboard!', 'success');
      } catch {
        UI.showToast('Vui lòng bôi đen văn bản để sao chép.', 'info');
      }
    });

    document.getElementById('btn-guide-insert-sample')?.addEventListener('click', () => {
      const ex = document.getElementById('guide-code-example')?.innerText || '';
      if (textarea) {
        textarea.value = ex;
        renderEditorPreview();
        saveEditorState();
      }
      closeGuide();
      UI.showToast('Đã chèn ví dụ mẫu vào khung soạn thảo!', 'success');
    });

    // Update Line Numbers
    const updateLineNumbers = () => {
      if (!lineNumbersBox || !textarea) return;
      const lines = textarea.value.split('\n').length;
      let html = '';
      for (let i = 1; i <= Math.max(lines, 30); i++) {
        html += `<div>${i}</div>`;
      }
      lineNumbersBox.innerHTML = html;
    };

    // Render Preview from Text
    let currentParsed = null;
    const renderEditorPreview = () => {
      const raw = textarea.value;
      updateLineNumbers();

      if (!raw || raw.trim().length === 0) {
        previewContainer.innerHTML = `
          <div class="p-12 text-center text-slate-400 space-y-3">
            <div class="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950 text-indigo-500 mx-auto flex items-center justify-center">
              <span class="material-symbols-outlined text-3xl">edit_note</span>
            </div>
            <h4 class="font-bold text-sm text-slate-700 dark:text-slate-200">Trình soạn thảo đang để trống</h4>
            <p class="text-xs max-w-sm mx-auto text-slate-500 leading-relaxed">
              Bạn có thể tự do gõ đề thi vào khung bên phải theo định dạng hoặc nhấp nút dưới đây để xem hướng dẫn cú pháp.
            </p>
            <button type="button" id="btn-empty-show-guide" class="px-4 py-2 bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 font-bold rounded-xl text-xs hover:bg-indigo-100 transition-colors">
              📖 Mở hướng dẫn cú pháp
            </button>
          </div>
        `;
        document.getElementById('btn-empty-show-guide')?.addEventListener('click', () => {
          syntaxModal?.classList.remove('hidden');
        });
        currentParsed = { questions: [] };
        return;
      }

      currentParsed = ExamParser.parseExamRaw(raw, 40.0);
      const questions = currentParsed.questions || [];

      if (questions.length === 0) {
        previewContainer.innerHTML = `
          <div class="p-12 text-center text-slate-400 text-xs leading-relaxed">
            Chưa nhận dạng được câu hỏi hợp lệ. Bắt đầu bằng: <code>Câu 1: ... *A. ... B. ...</code>
          </div>
        `;
        return;
      }

      previewContainer.innerHTML = questions.map((q, idx) => `
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-soft p-4 space-y-3 transition-all hover:border-indigo-400 relative group cursor-pointer" id="editor-q-card-${idx + 1}" data-q-num="${idx + 1}" title="Nhấp để chuyển đến vị trí trên mã nguồn">
          <!-- Meta Header -->
          <div class="flex items-center justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-2.5 py-1 bg-indigo-50 text-indigo-700 font-bold rounded-lg border border-indigo-200/60 text-xs">
                Câu ${idx + 1}.
              </span>
              <input type="text" value="${(q.points || 1.0).toFixed(2)} điểm" data-q-index="${idx}" class="q-points-input w-24 px-2 py-0.5 text-xs font-semibold border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-300 outline-none focus:border-indigo-500" onclick="event.stopPropagation()" />
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                ${q.question_type}
              </span>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              ${q.bloom_level}
            </span>
          </div>

          <!-- Question Content -->
          <!-- Attached Images Preview -->
          ${(() => {
            const allImages = (q.resources && q.resources.length > 0)
              ? q.resources.map(r => r.asset_id || r.id).filter(Boolean)
              : (q.image_asset_ids && q.image_asset_ids.length > 0)
                ? q.image_asset_ids
                : (q.image_asset_id ? [q.image_asset_id] : []);
            if (!allImages.length) return '';
            return `
              <div class="flex items-center gap-3 flex-wrap p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800" onclick="event.stopPropagation()">
                ${allImages.map((assetId, imgIdx) => `
                  <div class="relative group/thumb rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xs">
                    <img src="/instructor/files/${assetId}/download" alt="Hình ảnh câu hỏi ${idx + 1}" class="h-28 w-auto max-w-xs object-contain cursor-pointer transition-transform hover:scale-105" onclick="window.open('/instructor/files/${assetId}/download', '_blank')" onerror="this.onerror=null; this.parentElement.innerHTML='<span class=\'text-[11px] text-amber-600 p-2 block\'>🖼️ Ảnh đã gắn (${assetId.substring(0,8)}...)</span>'" />
                    <span class="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/60 text-white text-[9px] rounded font-mono">#${imgIdx + 1}</span>
                  </div>
                `).join('')}
              </div>
            `;
          })()}

          <!-- Question Content -->
          <div class="flex items-center gap-2 text-[11px]" onclick="event.stopPropagation()">
            <label class="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 dark:border-slate-700 rounded-lg cursor-pointer text-slate-700 dark:text-slate-300 hover:border-indigo-500">
              <span class="material-symbols-outlined text-[16px]">image</span>
              <span>${q.image_asset_id || (q.resources && q.resources.length > 0) ? 'Thay / thêm ảnh' : 'Thêm ảnh câu hỏi'}</span>
              <input type="file" class="raw-question-image-input sr-only" data-q-index="${idx}" accept="image/png,image/jpeg,image/webp,image/gif" />
            </label>
            <span class="text-slate-500">${q.image_asset_id || (q.resources && q.resources.length > 0) ? 'Đã đính kèm ảnh câu hỏi' : 'PNG, JPEG, WebP hoặc GIF; tối đa 5 MB'}</span>
          </div>
          <div class="q-card-stem text-xs sm:text-sm font-semibold text-slate-900 dark:text-white leading-snug p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60 focus-within:bg-white dark:focus-within:bg-slate-800 outline-none" contenteditable="true" data-q-index="${idx}" onclick="event.stopPropagation()">
            ${UI.escapeHtml((q.stem || q.question_text || '').replace(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):[^\]]+\]\]/gi, '').trim())}
          </div>

          <!-- Choices -->
          <div class="mt-3 space-y-2" onclick="event.stopPropagation()">
            ${(q.choices || []).map((c, cIdx) => `
              <div class="flex items-start gap-2 group/opt">
                <button
                  type="button"
                  class="q-choice-btn w-6 h-6 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 shadow-xs transition-colors ${c.is_correct ? 'bg-indigo-600 text-white' : 'border border-slate-300 dark:border-slate-700 text-slate-600 hover:border-indigo-500'}"
                  data-q-index="${idx}"
                  data-c-index="${cIdx}"
                  title="${c.is_correct ? 'Đáp án đúng (nhấp để bỏ)' : 'Đánh dấu đáp án đúng'}"
                >
                  ${c.is_correct ? '✓' : (c.label || String.fromCharCode(65 + cIdx))}
                </button>
                <div class="q-choice-content text-xs p-2 rounded-lg w-full transition-colors ${c.is_correct ? 'border border-indigo-500 bg-indigo-50/20 text-slate-900 dark:text-white font-medium ring-1 ring-indigo-500/30' : 'border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800'}" contenteditable="true" data-q-index="${idx}" data-c-index="${cIdx}">
                  <span class="font-bold ${c.is_correct ? 'text-indigo-700 mr-1' : 'mr-1'}">${c.label || String.fromCharCode(65 + cIdx)}.</span>
                  <span>${UI.escapeHtml(c.content || '')}</span>
                </div>
              </div>
            `).join('')}
          </div>

          ${q.explanation ? `
            <div class="text-[11px] p-2 rounded bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 border-l-2 border-indigo-500">
              <strong>Lời giải:</strong> ${UI.escapeHtml(q.explanation)}
            </div>
          ` : ''}
        </div>
      `).join('');

      // Bind click on card -> jump to question in textarea
      questions.forEach((_, idx) => {
        const card = document.getElementById(`editor-q-card-${idx + 1}`);
        if (card) {
          card.onclick = (e) => {
            if (e.target.closest('input') || e.target.closest('[contenteditable="true"]') || e.target.closest('button')) return;
            jumpToQuestionInTextarea(idx + 1);
          };
        }
      });

      // Bind input on q-points-input
      previewContainer.querySelectorAll('.q-points-input').forEach(input => {
        input.onchange = (e) => {
          const idx = parseInt(e.target.dataset.qIndex, 10);
          const rawVal = parseFloat(e.target.value.replace(/[^0-9.]/g, ''));
          if (!isNaN(rawVal) && rawVal >= 0 && questions[idx]) {
            questions[idx].points = rawVal;
            e.target.value = `${rawVal.toFixed(2)} điểm`;
            saveEditorState();
            const total = questions.reduce((sum, item) => sum + (parseFloat(item.points) || 0), 0);
            const syncBadge = document.getElementById('workflow-sync-badge');
            if (syncBadge) syncBadge.textContent = `${questions.length} câu • ${total.toFixed(1)}đ • Tự động lưu`;
          }
        };
      });

      // Stem in-place editing
      previewContainer.querySelectorAll('.q-card-stem').forEach(stemEl => {
        stemEl.onblur = (e) => {
          const idx = parseInt(e.target.dataset.qIndex, 10);
          const newStem = e.target.innerText.trim();
          if (questions[idx] && newStem && newStem !== questions[idx].stem) {
            questions[idx].stem = newStem;
            questions[idx].question_text = newStem;
            textarea.value = ExamParser.generateRawFromQuestions(questions);
            updateLineNumbers();
            saveEditorState();
          }
        };
      });

      // Choice toggle correct
      previewContainer.querySelectorAll('.q-choice-btn').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          const qIdx = parseInt(btn.dataset.qIndex, 10);
          const cIdx = parseInt(btn.dataset.cIndex, 10);
          const q = questions[qIdx];
          if (!q || !q.choices || !q.choices[cIdx]) return;
          if (q.type === 'MULTIPLE_CHOICE' || q.question_type === 'TN nhiều đáp án') {
            q.choices[cIdx].is_correct = !q.choices[cIdx].is_correct;
          } else {
            q.choices.forEach((c, i) => {
              c.is_correct = (i === cIdx);
            });
          }
          textarea.value = ExamParser.generateRawFromQuestions(questions);
          renderEditorPreview();
          saveEditorState();
        };
      });

      // Choice content in-place editing
      previewContainer.querySelectorAll('.q-choice-content').forEach(cEl => {
        cEl.onblur = (e) => {
          const qIdx = parseInt(cEl.dataset.qIndex, 10);
          const cIdx = parseInt(cEl.dataset.cIndex, 10);
          const rawText = cEl.innerText.trim();
          const q = questions[qIdx];
          if (q && q.choices && q.choices[cIdx]) {
            const cleanContent = rawText.replace(/^[A-F]\.\s*/i, '').trim();
            if (cleanContent && cleanContent !== q.choices[cIdx].content) {
              q.choices[cIdx].content = cleanContent;
              textarea.value = ExamParser.generateRawFromQuestions(questions);
              updateLineNumbers();
              saveEditorState();
            }
          }
        };
      });

      previewContainer.querySelectorAll('.raw-question-image-input').forEach(input => {
        input.onchange = async event => {
          const file = event.currentTarget.files?.[0];
          if (!file) return;
          if (file.size > 5 * 1024 * 1024 || !['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type)) {
            event.currentTarget.value = '';
            UI.showToast('Choose a PNG, JPEG, WebP, or GIF image smaller than 5 MB.', 'warning');
            return;
          }
          const draft = window.ExamStore.getDraft();
          if (!draft.courseId) {
            event.currentTarget.value = '';
            UI.showToast('Choose a course before adding an image to a question.', 'warning');
            return;
          }
          const questionIndex = Number(event.currentTarget.dataset.qIndex);
          const question = currentParsed?.questions?.[questionIndex];
          if (!question || !textarea) return;
          event.currentTarget.disabled = true;
          try {
            const uploaded = await ApiClient.uploadCourseFile(draft.courseId, file);
            const assetId = uploaded?.asset_id || uploaded?.public_id;
            if (!assetId || !/^[0-9a-f-]{36}$/i.test(assetId)) throw new Error('The upload did not return a valid image asset ID.');
            const lines = textarea.value.split(/\r?\n/);
            const marker = `[[PWD301:IMAGE:${assetId}]]`;
            const questionNumber = Number(question.number || questionIndex + 1);
            const headerPattern = new RegExp(`^\\s*(?:(?:Câu|Bài|Question)\\s*)?${questionNumber}[:.]`, 'i');
            const headerIndex = lines.findIndex(line => headerPattern.test(line));
            if (headerIndex < 0) throw new Error('Could not locate this question in the source text.');
            let nextHeaderIndex = lines.length;
            for (let index = headerIndex + 1; index < lines.length; index += 1) {
              if (headerPattern.test(lines[index])) {
                nextHeaderIndex = index;
                break;
              }
            }
            const existingMarkerIndex = lines.findIndex((line, index) =>
              index > headerIndex && index < nextHeaderIndex
              && /^\[\[PWD301:IMAGE:[0-9a-f-]{36}\]\]$/i.test(line.trim())
            );
            if (existingMarkerIndex > headerIndex) lines.splice(existingMarkerIndex, 1);
            lines.splice(headerIndex + 1, 0, marker);
            textarea.value = lines.join('\n');
            renderEditorPreview();
            saveEditorState();
            UI.showToast('Question image uploaded and attached. It will display after the security scan.', 'success');
          } catch (error) {
            UI.showToast(error.message || 'Question image upload failed.', 'error');
          } finally {
            event.currentTarget.disabled = false;
          }
        };
      });

      const badge = document.getElementById('workflow-sync-badge');
      const totalScore = questions.reduce((sum, item) => sum + (parseFloat(item.points) || 0), 0);
      if (badge) badge.textContent = `${questions.length} câu • ${totalScore.toFixed(1)}đ • Tự động lưu`;
    };

    const saveEditorState = () => {
      const raw = textarea.value;
      if (currentParsed && currentParsed.questions) {
        window.ExamStore.saveDraft({
          rawText: raw,
          questions: currentParsed.questions
        });
      } else {
        window.ExamStore.saveDraft({ rawText: raw });
      }
    };

    // Helper: Jump to question in Raw Textarea
    const jumpToQuestionInTextarea = (qNum) => {
      if (!textarea) return;
      const text = textarea.value;
      if (!text) return;

      const pattern = new RegExp(`(^|\\n)\\s*(?:Câu|Question|\\b)\\s*${qNum}[:.]`, 'i');
      const match = pattern.exec(text);
      if (match) {
        const matchPos = match.index + (match[0].startsWith('\n') ? 1 : 0);
        textarea.focus();
        textarea.setSelectionRange(matchPos, matchPos + match[0].trim().length);
        const linesBefore = text.substring(0, matchPos).split('\n').length;
        const approxLineHeight = 22;
        textarea.scrollTop = Math.max(0, (linesBefore - 3) * approxLineHeight);
      }
    };

    // Helper: Jump to question on both Card and Textarea
    const handleJumpToQuestion = (targetNum) => {
      const qNum = parseInt(targetNum, 10);
      if (isNaN(qNum) || qNum < 1) {
        UI.showToast('Vui lòng nhập số thứ tự câu hỏi hợp lệ!', 'warning');
        return;
      }

      const card = document.getElementById(`editor-q-card-${qNum}`);
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.classList.add('ring-2', 'ring-indigo-500', 'bg-indigo-50/40', 'dark:bg-indigo-950/40');
        setTimeout(() => {
          card.classList.remove('ring-2', 'ring-indigo-500', 'bg-indigo-50/40', 'dark:bg-indigo-950/40');
        }, 2200);
      } else {
        UI.showToast(`Không tìm thấy Câu ${qNum} trong danh sách xem trước!`, 'warning');
      }

      jumpToQuestionInTextarea(qNum);
    };

    // Bind Jump Button & Enter Key
    const jumpInput = document.getElementById('editor-jump-input');
    document.getElementById('editor-jump-btn')?.addEventListener('click', () => {
      if (jumpInput) handleJumpToQuestion(jumpInput.value);
    });
    jumpInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleJumpToQuestion(jumpInput.value);
      }
    });

    // Bind "Chia điểm" (100% total points evenly divided)
    document.getElementById('editor-btn-divide-points')?.addEventListener('click', () => {
      const draftState = window.ExamStore.getDraft();
      let questions = (currentParsed && currentParsed.questions && currentParsed.questions.length > 0)
        ? currentParsed.questions
        : (draftState.questions || []);

      if (!questions || questions.length === 0) {
        UI.showToast('Chưa có câu hỏi nào để chia điểm. Vui lòng nhập nội dung đề thi trước!', 'warning');
        return;
      }

      const N = questions.length;
      const basePt = parseFloat((100.0 / N).toFixed(2));
      const remainder = parseFloat((100.0 - basePt * (N - 1)).toFixed(2));

      questions.forEach((q, idx) => {
        q.points = (idx === N - 1) ? remainder : basePt;
      });

      if (currentParsed) currentParsed.questions = questions;
      window.ExamStore.saveDraft({ questions: questions });
      renderEditorPreview();
      UI.showToast(`Đã chia đều 100 điểm cho ${N} câu hỏi (${basePt}đ/câu)!`, 'success');
    });

    // Bind "Chèn công thức" (LaTeX Formula Picker Modal)
    document.getElementById('editor-btn-latex')?.addEventListener('click', () => {
      const mathCategories = [
        {
          name: 'Toán học cơ bản',
          items: [
            { label: 'Phân số', latex: '\\frac{a}{b}', preview: 'a/b' },
            { label: 'Căn bậc hai', latex: '\\sqrt{x}', preview: '√x' },
            { label: 'Căn bậc n', latex: '\\sqrt[n]{x}', preview: 'ⁿ√x' },
            { label: 'Số mũ', latex: 'x^{2}', preview: 'x²' },
            { label: 'Chỉ số dưới', latex: 'x_{i}', preview: 'xᵢ' },
            { label: 'Nhân & Chia', latex: 'a \\times b \\div c', preview: 'a × b ÷ c' }
          ]
        },
        {
          name: 'Giải tích & Đại số',
          items: [
            { label: 'Tích phân xác định', latex: '\\int_{a}^{b} f(x)dx', preview: '∫ₐᵇ f(x)dx' },
            { label: 'Tổng xích-ma', latex: '\\sum_{i=1}^{n} x_i', preview: '∑ xᵢ' },
            { label: 'Giới hạn', latex: '\\lim_{x \\to \\infty} f(x)', preview: 'lim f(x)' },
            { label: 'Đạo hàm', latex: '\\frac{df}{dx}', preview: 'df/dx' },
            { label: 'Vô cực', latex: '\\infty', preview: '∞' },
            { label: 'Đẳng thức vector', latex: '\\vec{v}', preview: 'v⃗' }
          ]
        },
        {
          name: 'Lượng giác & Ký hiệu Hy Lạp',
          items: [
            { label: 'Sin & Cos', latex: '\\sin^2(x) + \\cos^2(x) = 1', preview: 'sin²(x)+cos²(x)=1' },
            { label: 'Góc Alpha', latex: '\\alpha', preview: 'α' },
            { label: 'Góc Beta', latex: '\\beta', preview: 'β' },
            { label: 'Số Pi', latex: '\\pi', preview: 'π' },
            { label: 'Góc Theta', latex: '\\theta', preview: 'θ' },
            { label: 'Delta', latex: '\\Delta', preview: 'Δ' }
          ]
        },
        {
          name: 'Quan hệ so sánh & Tập hợp',
          items: [
            { label: 'Nhỏ hơn hoặc bằng', latex: '\\le', preview: '≤' },
            { label: 'Lớn hơn hoặc bằng', latex: '\\ge', preview: '≥' },
            { label: 'Khác', latex: '\\neq', preview: '≠' },
            { label: 'Xấp xỉ', latex: '\\approx', preview: '≈' },
            { label: 'Thuộc tập hợp', latex: '\\in', preview: '∈' },
            { label: 'Tập hợp con', latex: '\\subset', preview: '⊂' },
            { label: 'Hợp & Giao', latex: 'A \\cup B \\cap C', preview: 'A ∪ B ∩ C' }
          ]
        },
        {
          name: 'Hóa học & Phương trình phản ứng',
          items: [
            { label: 'Mũi tên phản ứng', latex: '\\rightarrow', preview: '→' },
            { label: 'Phản ứng thuận nghịch', latex: '\\rightleftharpoons', preview: '⇌' },
            { label: 'Nhiệt lượng Delta H', latex: '\\Delta H < 0', preview: 'ΔH < 0' },
            { label: 'Kết tủa (mũi tên xuống)', latex: '\\downarrow', preview: '↓' },
            { label: 'Bay hơi (mũi tên lên)', latex: '\\uparrow', preview: '↑' }
          ]
        }
      ];

      const modalHtml = `
        <div class="space-y-5 text-xs text-slate-700 dark:text-slate-300">
          <p class="text-slate-500">
            Chọn công thức toán học/khoa học để chèn vào vị trí con trỏ hiện tại trong trình soạn thảo:
          </p>

          <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
            ${mathCategories.map(cat => `
              <div>
                <h4 class="font-bold text-xs uppercase tracking-wider text-indigo-700 dark:text-indigo-400 mb-2 pb-1 border-b border-slate-100 dark:border-slate-800">
                  ${cat.name}
                </h4>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  ${cat.items.map(item => `
                    <button
                      type="button"
                      class="latex-insert-btn p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 hover:bg-indigo-50 hover:border-indigo-300 dark:bg-slate-800 dark:hover:bg-slate-700 transition text-left flex flex-col justify-between gap-1 group shadow-2xs"
                      data-latex="${UI.escapeHtml(item.latex)}"
                    >
                      <div class="flex items-center justify-between w-full">
                        <span class="font-bold text-slate-800 dark:text-slate-100 group-hover:text-indigo-600">${item.label}</span>
                        <span class="text-[10px] font-mono text-slate-400 font-bold">$...$</span>
                      </div>
                      <div class="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-300 bg-white dark:bg-slate-900 px-2 py-1 rounded border border-slate-200/60 dark:border-slate-700/60 truncate">
                        ${UI.escapeHtml(item.preview)}
                      </div>
                    </button>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>

          <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs text-slate-500 flex items-center justify-between">
            <span>Bạn cũng có thể tự gõ công thức bất kỳ giữa cặp dấu <code>$...$</code></span>
            <span class="font-mono text-indigo-600 font-bold">$E = mc^2$</span>
          </div>
        </div>
      `;

      UI.openModal({
        title: 'Bảng Ký hiệu & Công thức Toán học LaTeX',
        bodyHtml: modalHtml,
        size: 'lg',
        footerHtml: `
          <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800" onclick="UI.closeModal()">
            Đóng
          </button>
        `
      });

      document.querySelectorAll('.latex-insert-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const ltx = btn.dataset.latex;
          if (textarea && ltx) {
            const start = textarea.selectionStart || 0;
            const end = textarea.selectionEnd || 0;
            const val = textarea.value;
            const insertText = `$${ltx}$`;
            textarea.value = val.substring(0, start) + insertText + val.substring(end);
            const newPos = start + insertText.length;
            textarea.focus();
            textarea.setSelectionRange(newPos, newPos);
            renderEditorPreview();
            saveEditorState();
            UI.closeModal();
            UI.showToast(`Đã chèn công thức: ${insertText}`, 'success');
          }
        });
      });
    });

    // Bi-directional Cursor Sync: Cursor position in textarea highlights preview card
    const syncActiveQuestionFromCursor = () => {
      if (!textarea) return;
      const cursorPos = textarea.selectionStart || 0;
      const textUpToCursor = textarea.value.substring(0, cursorPos);
      const qMatches = [...textUpToCursor.matchAll(/(?:^|\n)\s*(?:Câu|Question|\b)\s*(\d+)[:.]/gi)];
      if (qMatches.length > 0) {
        const lastMatch = qMatches[qMatches.length - 1];
        const activeQNum = parseInt(lastMatch[1], 10);
        if (!isNaN(activeQNum)) {
          document.querySelectorAll('#editor-preview-container > [id^="editor-q-card-"]').forEach(c => {
            c.classList.remove('ring-2', 'ring-indigo-500', 'border-indigo-500');
          });
          const activeCard = document.getElementById(`editor-q-card-${activeQNum}`);
          if (activeCard) {
            activeCard.classList.add('ring-2', 'ring-indigo-500', 'border-indigo-500');
            const containerRect = previewContainer.getBoundingClientRect();
            const cardRect = activeCard.getBoundingClientRect();
            if (cardRect.top < containerRect.top || cardRect.bottom > containerRect.bottom) {
              activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
          }
        }
      }
    };

    textarea.addEventListener('keyup', syncActiveQuestionFromCursor);
    textarea.addEventListener('click', syncActiveQuestionFromCursor);

    textarea.addEventListener('paste', async event => {
      const clipboard = event.clipboardData;
      const imageFiles = Array.from(clipboard?.items || [])
        .filter(item => item.type.startsWith('image/'))
        .map(item => item.getAsFile())
        .filter(Boolean);
      const html = clipboard?.getData('text/html') || '';
      if (!imageFiles.length && !/<img\b/i.test(html)) return;
      event.preventDefault();
      const courseId = window.ExamStore.getDraft().courseId;
      if (!courseId) {
        UI.showToast('Chọn khóa học trước khi dán đề thi có hình ảnh.', 'warning');
        return;
      }
      const selectionStart = textarea.selectionStart;
      const selectionEnd = textarea.selectionEnd;

      const images = [];
      let pasteText = clipboard.getData('text/plain') || '';
      if (/<img\b/i.test(html)) {
        const parsed = new DOMParser().parseFromString(html, 'text/html');
        let clipboardImageIndex = 0;
        const chunks = [];
        const visit = node => {
          if (node.nodeType === Node.TEXT_NODE) {
            chunks.push(node.textContent || '');
            return;
          }
          if (node.nodeType !== Node.ELEMENT_NODE) return;
          const tag = node.tagName.toLowerCase();
          if (tag === 'img') {
            const source = node.getAttribute('src') || '';
            const file = source.startsWith('data:image/')
              ? null : (imageFiles[clipboardImageIndex++] || null);
            images.push({ file, source });
            chunks.push(`\n[[PWD301:PASTE_IMAGE:${images.length - 1}]]\n`);
            return;
          }
          if (tag === 'br') {
            chunks.push('\n');
            return;
          }
          const block = /^(p|div|li|tr|h[1-6])$/.test(tag);
          if (block) chunks.push('\n');
          node.childNodes.forEach(visit);
          if (block) chunks.push('\n');
        };
        parsed.body.childNodes.forEach(visit);
        pasteText = chunks.join('').replace(/\n{3,}/g, '\n\n').trim();
      } else {
        images.push(...imageFiles.map(file => ({ file, source: '' })));
        const headers = [...pasteText.matchAll(/^(?:Câu|Bài|Question)\s*\d+[:.].*$/gmi)];
        if (headers.length === images.length) {
          let offset = 0;
          headers.forEach((header, index) => {
            const at = header.index + header[0].length + offset;
            const marker = `\n[[PWD301:PASTE_IMAGE:${index}]]`;
            pasteText = pasteText.slice(0, at) + marker + pasteText.slice(at);
            offset += marker.length;
          });
        } else {
          pasteText += images.map((_, index) => `\n[[PWD301:PASTE_IMAGE:${index}]]`).join('');
        }
      }

      try {
        const assetIds = [];
        let hasLocalFilePaths = false;
        for (let idx = 0; idx < images.length; idx++) {
          const image = images[idx];
          let file = image.file;
          if (!file && /^data:image\/(?:png|jpeg|webp|gif);base64,/i.test(image.source)) {
            try {
              const response = await fetch(image.source);
              const blob = await response.blob();
              file = new File([blob], `hinh-de-thi-${assetIds.length + 1}.png`, { type: blob.type });
            } catch (fetchErr) {
              console.warn('Could not decode data URI image:', fetchErr);
            }
          }
          if (!file && image.source && /^file:\/\//i.test(image.source)) {
            hasLocalFilePaths = true;
          }
          if (file) {
            if (file.size <= 5 * 1024 * 1024 && ['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type)) {
              try {
                const uploaded = await ApiClient.uploadCourseFile(courseId, file);
                const assetId = uploaded?.asset_id || uploaded?.public_id;
                if (assetId) {
                  assetIds.push(assetId);
                  pasteText = pasteText.replace(`[[PWD301:PASTE_IMAGE:${idx}]]`, `\n[[PWD301:IMAGE:${assetId}]]\n`);
                  continue;
                }
              } catch (upErr) {
                console.warn('Failed to upload clipboard image:', upErr);
              }
            }
          }
          pasteText = pasteText.replace(`[[PWD301:PASTE_IMAGE:${idx}]]`, '\n[Hình ảnh đính kèm: Hãy kéo thả ảnh hoặc tải tệp .docx vào đây]\n');
        }

        if (document.getElementById('editor-raw-textarea') !== textarea) return;
        textarea.setRangeText(pasteText, selectionStart, selectionEnd, 'end');
        renderEditorPreview();
        saveEditorState();

        if (assetIds.length > 0) {
          UI.showToast(`Đã nhận diện và tải lên ${assetIds.length} hình ảnh vào đề thi.`, 'success');
        } else if (hasLocalFilePaths) {
          UI.showToast('Đã dán nội dung. Các hình ảnh từ Word có đường dẫn cục bộ (file:///) cần dùng nút "Tải tệp đề thi (.docx)" để hệ thống tự động bóc tách ảnh.', 'info');
        }
      } catch (error) {
        console.error('Paste error:', error);
        textarea.setRangeText(clipboard.getData('text/plain') || '', selectionStart, selectionEnd, 'end');
        renderEditorPreview();
        saveEditorState();
        UI.showToast('Đã dán nội dung văn bản.', 'info');
      }
    });

    textarea.addEventListener('input', () => {
      renderEditorPreview();
      saveEditorState();
    });

    document.getElementById('editor-btn-sync')?.addEventListener('click', () => {
      renderEditorPreview();
      saveEditorState();
      UI.showToast('Đã đồng bộ sang xem trước!', 'success');
    });

    // Clear all button
    document.getElementById('editor-btn-clear-all')?.addEventListener('click', async () => {
      const conf = await UI.confirm('Xóa trắng nội dung', 'Bạn có chắc chắn muốn làm trống toàn bộ khung soạn thảo để tự gõ mới?', 'Làm trống');
      if (conf) {
        textarea.value = '';
        renderEditorPreview();
        window.ExamStore.saveDraft({ rawText: '', questions: [] });
        UI.showToast('Khung soạn thảo đã để trống hoàn toàn.', 'info');
      }
    });

    // Sample template loaders
    document.querySelectorAll('.editor-load-tmpl-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tmpl = btn.dataset.tmpl;
        textarea.value = ExamParser.generateSampleTemplate(tmpl);
        renderEditorPreview();
        saveEditorState();
        UI.showToast(`Đã nạp mẫu: ${btn.textContent}`, 'success');
      });
    });

    // Proceed to Matrix
    const onProceedToMatrix = () => {
      renderEditorPreview();
      saveEditorState();
      const draftState = window.ExamStore.getDraft();
      if (!draftState.questions || draftState.questions.length === 0) {
        UI.showToast('Vui lòng nhập ít nhất 1 câu hỏi hợp lệ trước khi sang Ma trận học vụ!', 'warning');
        return;
      }
      window.location.hash = '#/instructor/exams/matrix';
    };

    // Initial render
    renderEditorPreview();
  };


  // =========================================================================
  // 4. PAGE 2b: Visual Interactive Builder (#/instructor/exams/interactive)
  //    Drag-and-Drop text tokens, Fill-in-the-blank, Matching pairs
  // =========================================================================
  InstructorView.renderExamInteractive = function (container) {
    const draft = window.ExamStore.getDraft();
    let interactiveQuestions = (draft.questions || []).filter(q => 
      q.question_type === 'Kéo thả' || q.question_type === 'Điền từ' || q.question_type === 'Ghép đôi' || q.type === 'SHORT_ANSWER' || q.is_interactive
    );

    let activeTab = 'drag'; // 'drag' | 'fill' | 'match'
    let pendingImageAssetId = null
    let imageUploadInProgress = false

    container.innerHTML = `
      <div id="interactive-builder-root" class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(2, 'Soạn câu hỏi tương tác', '#/instructor/exams/matrix', 'Tiếp tục: Kiểm tra đề')}

        <main class="flex-1 overflow-y-auto max-w-[1520px] mx-auto px-4 sm:px-6 py-6 w-full pb-28">
          
          <!-- Banner -->
          <div class="mb-6 p-4 rounded-2xl bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center material-symbols-outlined text-[22px] shrink-0 shadow-xs">
                extension
              </div>
              <div>
                <h3 class="font-bold text-sm text-teal-950 dark:text-teal-200">Soạn câu hỏi tương tác</h3>
                <p class="text-xs text-teal-700 dark:text-teal-300">Chọn dạng câu hỏi, nhập nội dung rồi thử trước khi thêm vào đề.</p>
              </div>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 border border-teal-200 self-start sm:self-auto shrink-0">
              ${interactiveQuestions.length} câu tương tác đã thêm
            </span>
          </div>

          <!-- 2 Columns: Left Form / Right Interactive Preview -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- LEFT: Builder Form (6 cols) -->
            <div class="lg:col-span-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs space-y-5">
              
              <!-- Tab Switcher -->
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-200 mb-2">Dạng câu hỏi</label>
                <div class="grid grid-cols-3 gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-bold">
                  <button type="button" id="tab-btn-drag" class="py-2 rounded-lg transition-all bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs">
                    Kéo thả từ
                  </button>
                  <button type="button" id="tab-btn-fill" class="py-2 rounded-lg transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900">
                    Điền khuyết
                  </button>
                  <button type="button" id="tab-btn-match" class="py-2 rounded-lg transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900">
                    Ghép đôi
                  </button>
                </div>
              </div>

              <!-- FORM 1: Kéo thả từ vào chỗ trống -->
              <div id="form-container-drag" class="space-y-4">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Nội dung câu hỏi · đặt đáp án trong dấu [ ]
                  </label>
                  <textarea
                    id="drag-stem-input"
                    rows="4"
                    class="w-full p-3 text-xs sm:text-sm border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: Giao thức [HTTPS] bảo vệ đường truyền bằng chứng chỉ [SSL/TLS] chạy mặc định trên cổng [443]."
                  ></textarea>
                  <span class="text-[11px] text-slate-500 dark:text-slate-300 mt-1 block">Ví dụ: Giao thức [HTTPS] bảo vệ đường truyền. Từ trong [ ] trở thành ô trống.</span>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Từ lựa chọn thêm (Không bắt buộc)</label>
                  <input
                    type="text"
                    id="drag-distractors-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: HTTP, 80, 21, SSH"
                    value=""
                  />
                </div>
              </div>

              <!-- FORM 2: Điền khuyết / Trả lời ngắn -->
              <div id="form-container-fill" class="space-y-4 hidden">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Nội dung câu hỏi · dùng ___ cho mỗi ô trống
                  </label>
                  <textarea
                    id="fill-stem-input"
                    rows="3"
                    class="w-full p-3 text-xs sm:text-sm border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: Cơ chế xác thực không trạng thái trong REST API sử dụng mã thông báo định dạng ___."
                  ></textarea>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Đáp án được chấp nhận
                  </label>
                  <input
                    type="text"
                    id="fill-answers-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: JWT, JSON Web Token, jwt"
                    value=""
                  />
                <p class="text-[11px] text-slate-500 dark:text-slate-300 mt-1">Nhiều cách viết cho cùng một ô: ngăn bằng dấu phẩy. Nhiều ô: ngăn nhóm đáp án bằng dấu chấm phẩy.</p></div>

              </div>

              <!-- FORM 3: Ghép đôi cặp tương ứng -->
              <div id="form-container-match" class="space-y-4 hidden">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Đề bài yêu cầu ghép đôi</label>
                  <input
                    type="text"
                    id="match-stem-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: Ghép giao thức với cổng mạng tương ứng"
                  />
                </div>

                <div>
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-xs font-bold text-slate-700 dark:text-slate-300">Danh sách các cặp ghép (Cột A ➔ Cột B)</label>
                    <button type="button" id="btn-add-match-pair" class="text-teal-600 font-bold text-xs hover:underline flex items-center gap-1">
                      <span class="material-symbols-outlined text-[16px]">add</span>
                      <span>Thêm cặp</span>
                    </button>
                  </div>
                  <div id="match-pairs-list" class="space-y-2">
                    <div class="flex items-center gap-2 match-pair-row">
                      <input type="text" placeholder="Ví dụ: HTTP" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ví dụ: Cổng 80" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" />
                    </div>
                    <div class="flex items-center gap-2 match-pair-row">
                      <input type="text" placeholder="Ví dụ: HTTPS" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ví dụ: Cổng 443" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" />
                    </div>
                    <div class="flex items-center gap-2 match-pair-row">
                      <input type="text" placeholder="Ví dụ: SSH" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ví dụ: Cổng 22" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Shared Meta -->
              <div class="pt-4 border-t border-slate-100 dark:border-slate-700 space-y-4">
                <div>
                  <label for="interactive-points-input" class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Điểm cho câu hỏi</label>
                  <input type="number" id="interactive-points-input" min="0.5" step="0.5" value="1.5" class="w-full px-3 py-2.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 font-bold" />
                </div>
                <div>
                  <label for="interactive-exp-input" class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Lời giải thích (Không bắt buộc)</label>
                  <input type="text" id="interactive-exp-input" class="w-full px-3 py-2.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800" placeholder="Giải thích đáp án sau khi học viên nộp bài..." />
                </div>
                <details class="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                  <summary class="cursor-pointer text-xs font-bold text-slate-700 dark:text-slate-200">Tùy chọn thêm</summary>
                  <div class="space-y-4 mt-4">
                <div>
                  <label for="interactive-bloom-select" class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Mức độ tư duy</label>
                  <select id="interactive-bloom-select" class="w-full px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 font-semibold">
                    <option value="Nhận biết">Nhận biết</option>
                    <option value="Thông hiểu" selected>Thông hiểu</option>
                    <option value="Vận dụng">Vận dụng</option>
                  </select>
                </div>
              <div>
                <label for="interactive-image-input" class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Ảnh minh họa (Không bắt buộc)</label>
                <input type="file" id="interactive-image-input" accept="image/png,image/jpeg,image/webp,image/gif" class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-lg bg-slate-50 dark:bg-slate-800" />
                <p id="interactive-image-status" class="mt-1 text-[11px] text-slate-500 dark:text-slate-300">PNG, JPEG, WebP hoặc GIF, tối đa 5 MB.</p>
              </div>
                  </div>
                </details>
              </div>

              <!-- Submit Button -->
              <button
                type="button"
                id="btn-add-interactive-question"
                class="w-full py-2.5 bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-bold rounded-xl text-xs shadow-md shadow-teal-500/20 transition-all flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>Thêm Câu Hỏi</span>
              </button>

            </div>

            <!-- RIGHT: Live Interactive Preview & Questions List (6 cols) -->
            <div class="lg:col-span-6 space-y-6">
              
              <!-- Live Interactive Test Box -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border-2 border-teal-500/40 p-5 sm:p-6 shadow-sm">
                <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                  <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></span>
                    <h3 class="text-sm font-bold text-slate-900 dark:text-white">Xem trước câu hỏi</h3>
                  </div>
                  <span class="text-[11px] px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-semibold">Góc nhìn học viên</span>
                </div>

                <div id="interactive-live-preview-box" class="min-h-[160px] flex flex-col justify-center">
                  <!-- Live interactive preview elements -->
                </div>

                <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <button type="button" id="btn-test-interactive-answer" class="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-teal-50 text-slate-700 dark:text-slate-300 font-bold rounded-lg text-xs transition-colors">
                    Kiểm tra đáp án
                  </button>
                  <span id="test-feedback-msg" class="text-xs font-semibold text-slate-500"></span>
                </div>
              </div>

              <!-- List of Questions currently in Exam -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
                <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                  <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>Danh sách câu hỏi trong đề thi</span>
                    <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700" id="exam-questions-count-badge">
                      ${(draft.questions || []).length} câu
                    </span>
                  </h3>
                  <button type="button" id="btn-go-to-matrix" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-xs shadow-xs transition-colors flex items-center gap-1">
                    <span>Tiếp tục: Kiểm tra đề</span>
                    <span class="material-symbols-outlined text-[15px]">arrow_forward</span>
                  </button>
                </div>

                <div id="interactive-questions-list" class="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                  <!-- Dynamic Question Items -->
                </div>
              </div>

            </div>

          </div>
        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(2, '#/instructor/exams/matrix', () => {
      window.location.hash = '#/instructor/exams/matrix';
    });

    // Tab switcher logic
    const tabBtnDrag = document.getElementById('tab-btn-drag');
    const tabBtnFill = document.getElementById('tab-btn-fill');
    const tabBtnMatch = document.getElementById('tab-btn-match');
    const formDrag = document.getElementById('form-container-drag');
    const formFill = document.getElementById('form-container-fill');
    const formMatch = document.getElementById('form-container-match');

    const switchTab = (tab) => {
      activeTab = tab;
      [tabBtnDrag, tabBtnFill, tabBtnMatch].forEach(b => {
        b.className = "py-2 rounded-lg transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900";
      });
      [formDrag, formFill, formMatch].forEach(f => f.classList.add('hidden'));

      if (tab === 'drag') {
        tabBtnDrag.className = "py-2 rounded-lg transition-all bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs";
        formDrag.classList.remove('hidden');
      } else if (tab === 'fill') {
        tabBtnFill.className = "py-2 rounded-lg transition-all bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs";
        formFill.classList.remove('hidden');
      } else {
        tabBtnMatch.className = "py-2 rounded-lg transition-all bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs";
        formMatch.classList.remove('hidden');
      }
      renderLivePreview();
    };

    tabBtnDrag?.addEventListener('click', () => switchTab('drag'));
    tabBtnFill?.addEventListener('click', () => switchTab('fill'));
    tabBtnMatch?.addEventListener('click', () => switchTab('match'));

    // Dynamic Matching Pair Adder
    document.getElementById('btn-add-match-pair')?.addEventListener('click', () => {
      const list = document.getElementById('match-pairs-list');
      if (list) {
        const row = document.createElement('div');
        row.className = "flex items-center gap-2 match-pair-row";
        row.innerHTML = `
          <input type="text" placeholder="Khái niệm A" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" />
          <span class="text-slate-400">➔</span>
          <input type="text" placeholder="Ý nghĩa B" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" />
          <button type="button" class="text-slate-400 hover:text-rose-500" onclick="this.parentElement.remove(); renderLivePreview();">×</button>
        `;
        list.appendChild(row);
        renderLivePreview();
      }
    });

    // Render Live Preview Box
    const previewBox = document.getElementById('interactive-live-preview-box');
    const feedbackMsg = document.getElementById('test-feedback-msg');

    const renderLivePreview = () => {
      if (!previewBox) return;
      if (feedbackMsg) feedbackMsg.textContent = '';

      const inputId = activeTab === 'drag' ? 'drag-stem-input' : activeTab === 'fill' ? 'fill-stem-input' : 'match-stem-input';
      if (!document.getElementById(inputId)?.value.trim()) {
        previewBox.innerHTML = '<p class="text-sm text-slate-600 dark:text-slate-300 text-center py-8">Nhập nội dung ở bên trái để xem trước câu hỏi.</p>';
        return;
      }

      if (activeTab === 'drag') {
        const text = document.getElementById('drag-stem-input')?.value || '';
        const tokens = [...text.matchAll(/\[(.*?)\]/g)].map(match => match[1]);
        const distractors = (document.getElementById('drag-distractors-input')?.value || '')
          .split(',')
          .map(value => value.trim())
          .filter(Boolean);
        const allPills = [...tokens, ...distractors];
        let previewHtml = UI.escapeHtml(text);
        tokens.forEach(token => {
          const safeToken = UI.escapeHtml(token);
          previewHtml = previewHtml.replace(
            `[${safeToken}]`,
            `<button type="button" class="drop-slot inline-block border-2 border-dashed border-teal-500 bg-teal-50/40 rounded-lg px-3 py-1 min-w-[60px] text-center font-bold text-teal-700 text-xs" data-expected="${safeToken}" aria-label="Drop a word here">___</button>`
          );
        });

        previewBox.innerHTML = `
          <div class="space-y-4">
            <div class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-loose">${previewHtml}</div>
            <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
              <span class="text-[11px] font-bold text-slate-500 block mb-1.5">Drag or select a word:</span>
              <div class="flex flex-wrap gap-2" id="preview-drag-pills">
                ${allPills.map((word, index) => `
                  <button type="button" draggable="true" class="px-2.5 py-1 rounded-lg bg-teal-600 text-white font-bold text-xs cursor-grab drag-pill-btn" data-word-index="${index}" data-word="${UI.escapeHtml(word)}">${UI.escapeHtml(word)}</button>
                `).join('')}
              </div>
            </div>
          </div>
        `;

        const assignWord = (slot, wordIndex) => {
          const previousIndex = Number(slot.dataset.wordIndex);
          if (Number.isInteger(previousIndex)) {
            const previousPill = previewBox.querySelector(`.drag-pill-btn[data-word-index="${previousIndex}"]`);
            if (previousPill) previousPill.disabled = false;
          }
          const pill = previewBox.querySelector(`.drag-pill-btn[data-word-index="${wordIndex}"]`);
          if (!pill) return;
          slot.dataset.wordIndex = String(wordIndex);
          slot.textContent = pill.dataset.word || '';
          pill.disabled = true;
        };
        previewBox.querySelectorAll('.drag-pill-btn').forEach(pill => {
          pill.addEventListener('click', () => {
            const emptySlot = Array.from(previewBox.querySelectorAll('.drop-slot'))
              .find(slot => !slot.dataset.wordIndex);
            if (emptySlot) assignWord(emptySlot, Number(pill.dataset.wordIndex));
          });
          pill.addEventListener('dragstart', event => {
            event.dataTransfer?.setData('text/plain', pill.dataset.wordIndex || '');
          });
        });
        previewBox.querySelectorAll('.drop-slot').forEach(slot => {
          slot.addEventListener('dragover', event => event.preventDefault());
          slot.addEventListener('drop', event => {
            event.preventDefault();
            const rawWordIndex = event.dataTransfer?.getData('text/plain');
            if (!rawWordIndex) return;
            const wordIndex = Number(rawWordIndex);
            if (Number.isInteger(wordIndex)) assignWord(slot, wordIndex);
          });
        });
      } else if (activeTab === 'fill') {
        const stem = document.getElementById('fill-stem-input')?.value || '';
        let liveBlankIndex = 0;
        const stemRendered = UI.escapeHtml(stem).replace(/_{3,}/g, () => {
          const blankIndex = liveBlankIndex++;
          return `<input type="text" id="live-fill-input-${blankIndex}" aria-label="Answer for blank ${blankIndex + 1}" placeholder="Blank ${blankIndex + 1}" class="inline-block px-2 py-1 text-xs font-bold border-b-2 border-teal-600 bg-teal-50/50 outline-none w-32 text-center" />`;
        });
        previewBox.innerHTML = `
          <div class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
            ${stemRendered}
          </div>
        `;
      } else if (activeTab === 'match') {
        const stem = document.getElementById('match-stem-input')?.value || '';
        const rows = document.querySelectorAll('.match-pair-row');
        const pairs = Array.from(rows).map(row => ({
          left: row.querySelector('.pair-left')?.value.trim() || '',
          right: row.querySelector('.pair-right')?.value.trim() || ''
        })).filter(pair => pair.left && pair.right);
        const matchRows = InstructorView.buildInteractiveMatchPreview(pairs);

        previewBox.innerHTML = `
          <div class="space-y-3">
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">${UI.escapeHtml(stem)}</p>
            <p class="text-[11px] text-slate-600 dark:text-slate-300">Chọn một đáp án cho mỗi mục:</p>
            <div class="space-y-2">
              ${matchRows.map((row, index) => `
                <label class="flex flex-col sm:flex-row sm:items-center gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                  <span class="font-bold text-slate-900 dark:text-white sm:w-1/2">${index + 1}. ${UI.escapeHtml(row.left)}</span>
                  <select class="preview-match-choice w-full sm:w-1/2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-xs text-slate-900 dark:text-slate-100" data-expected="${UI.escapeHtml(row.expected)}" aria-label="Ghép với ${UI.escapeHtml(row.left)}">
                    <option value="">Chọn đáp án</option>
                    ${row.options.map(option => `<option value="${UI.escapeHtml(option)}">${UI.escapeHtml(option)}</option>`).join('')}
                  </select>
                </label>
              `).join('')}
            </div>
          </div>
        `;
      }
    };

    // Test answer button
    document.getElementById('btn-test-interactive-answer')?.addEventListener('click', () => {
      if (activeTab === 'drag') {
        const slots = document.querySelectorAll('.drop-slot');
        let correct = 0;
        slots.forEach(s => {
          if (s.textContent.trim() === s.dataset.expected) correct++;
        });
        if (slots.length > 0 && correct === slots.length) {
          feedbackMsg.innerHTML = `<span class="text-emerald-600 font-bold">✓ Chính xác 100%! (${correct}/${slots.length} vị trí)</span>`;
        } else {
          feedbackMsg.innerHTML = `<span class="text-amber-600 font-bold">Đúng ${correct}/${slots.length} vị trí. Thử lại!</span>`;
        }
      } else if (activeTab === 'fill') {
        const submitted = Array.from(previewBox.querySelectorAll('[id^="live-fill-input-"]'))
          .map(input => input.value.trim());
        const acceptedAnswers = document.getElementById('fill-answers-input')?.value || '';
        const isCorrect = InstructorView.isInteractiveFillAnswerCorrect(submitted, acceptedAnswers);
        if (isCorrect) {
          feedbackMsg.innerHTML = `<span class="text-emerald-600 font-bold">✓ Chính xác! Trùng khớp đáp án.</span>`;
        } else {
          feedbackMsg.innerHTML = `<span class="text-rose-600 font-bold">Chưa đúng đáp án.</span>`;
        }
      } else {
        const choices = Array.from(previewBox.querySelectorAll('.preview-match-choice'));
        const correctCount = choices.length;
        const correctSelected = choices.filter(input => input.value && input.value === input.dataset.expected).length;
        const isCompleteMatch = correctCount > 0 && correctSelected === correctCount;
        feedbackMsg.textContent = isCompleteMatch
          ? `Đúng ${correctSelected}/${correctCount} cặp.`
          : `Đúng ${correctSelected}/${correctCount} cặp. Hãy chọn một đáp án cho mỗi mục.`;
        feedbackMsg.className = isCompleteMatch
          ? 'text-xs font-bold text-emerald-600'
          : 'text-xs font-bold text-amber-600';
      }
    });

    document.getElementById('interactive-image-input')?.addEventListener('change', async event => {
      const input = event.currentTarget;
      const file = input.files?.[0];
      const status = document.getElementById('interactive-image-status');
      if (!file) return;
      if (file.size > 5 * 1024 * 1024 || !['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type)) {
        input.value = '';
        UI.showToast('Choose a PNG, JPEG, WebP, or GIF image smaller than 5 MB.', 'warning');
        return;
      }
      if (!draft.courseId) {
        UI.showToast('Choose a course before adding an image to a question.', 'warning');
        input.value = '';
        return;
      }
      input.disabled = true;
      imageUploadInProgress = true;
      if (status) status.textContent = 'Uploading and scanning image...';
      try {
        const uploaded = await ApiClient.uploadCourseFile(draft.courseId, file);
        pendingImageAssetId = uploaded?.asset_id || uploaded?.public_id || null;
        if (!pendingImageAssetId) throw new Error('The uploaded image did not return an asset ID.');
        if (status) status.textContent = `Image added: ${file.name}`;
        UI.showToast('Question image uploaded. It will appear after the security scan completes.', 'success');
      } catch (error) {
        input.value = '';
        pendingImageAssetId = null;
        if (status) status.textContent = 'The image could not be uploaded.';
        UI.showToast(error.message || 'Image upload failed.', 'error');
      } finally {
        imageUploadInProgress = false;
        input.disabled = false;
      }
    });

    const showInteractiveError = (fieldId, message) => {
      document.querySelectorAll('[data-interactive-error]').forEach(node => node.remove());
      document.querySelectorAll('.interactive-field-error').forEach(node => node.classList.remove('interactive-field-error', 'border-rose-500'));
      const field = document.getElementById(fieldId);
      if (!field) {
        UI.showToast(message, 'warning');
        return;
      }
      field.classList.add('interactive-field-error', 'border-rose-500');
      const hint = document.createElement('p');
      hint.dataset.interactiveError = fieldId;
      hint.className = 'mt-1 text-xs font-medium text-rose-700 dark:text-rose-300';
      hint.textContent = message;
      field.insertAdjacentElement('afterend', hint);
      field.focus();
    };
    document.getElementById('interactive-builder-root')?.addEventListener('input', event => {
      const field = event.target;
      if (!field.classList?.contains('interactive-field-error')) return;
      field.classList.remove('interactive-field-error', 'border-rose-500');
      container.querySelector(`[data-interactive-error="${field.id}"]`)?.remove();
    });

    // Add Interactive Question to Exam
    document.getElementById('btn-add-interactive-question')?.addEventListener('click', () => {
      if (imageUploadInProgress) {
        UI.showToast(
          'Wait for the question image upload to finish before adding this question.',
          'warning'
        );
        return;
      }
      const pts = Number.parseFloat(document.getElementById('interactive-points-input')?.value || '');
      if (!Number.isFinite(pts) || pts <= 0) {
        showInteractiveError('interactive-points-input', 'Nhập số điểm lớn hơn 0.');
        return;
      }
      const bloom = document.getElementById('interactive-bloom-select')?.value || 'Thông hiểu';
      const exp = document.getElementById('interactive-exp-input')?.value.trim() || '';

      let newQuestion = null;

      if (activeTab === 'drag') {
        const stem = document.getElementById('drag-stem-input')?.value.trim();
        if (!stem) {
          showInteractiveError('drag-stem-input', 'Nhập câu hỏi có ít nhất một đáp án trong dấu [ ].');
          return;
        }
        const tokens = [...stem.matchAll(/\[(.*?)\]/g)].map(match => match[1].trim()).filter(Boolean);
        if (!tokens.length || tokens.length > 6) {
          showInteractiveError('drag-stem-input', 'Dùng từ 1 đến 6 đáp án trong dấu [ ].');
          return;
        }
        const cleanStem = stem.replace(/\[(.*?)\]/g, '___');
        const distractors = (document.getElementById('drag-distractors-input')?.value || '')
          .split(',').map(word => word.trim()).filter(Boolean);
        const optionsByValue = new Map();
        [...tokens, ...distractors].forEach(word => {
          const key = word.toLocaleLowerCase();
          if (!optionsByValue.has(key)) optionsByValue.set(key, word);
        });
        const options = Array.from(optionsByValue.values());
        if (options.length > 16) {
          showInteractiveError('drag-distractors-input', 'Tối đa 16 từ lựa chọn, gồm đáp án và từ thêm.');
          return;
        }
        const choices = tokens.flatMap((answer, blankIndex) => options.map((option, optionIndex) => ({
          content: `[[PWD301:G:DRAG:${blankIndex + 1}]]${option}`,
          is_correct: option.toLocaleLowerCase() === answer.toLocaleLowerCase(),
          position: blankIndex * options.length + optionIndex + 1
        })));
        newQuestion = {
          stem: `${cleanStem}\nDrag one token into each blank.`,
          question_text: `${cleanStem}\nDrag one token into each blank.`,
          question_type: 'Drag and drop',
          type: 'MULTIPLE_CHOICE',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          choices,
          is_interactive: true,
          interactive_type: 'DRAG_DROP',
          tokens
        };
      } else if (activeTab === 'fill') {
        const stem = document.getElementById('fill-stem-input')?.value.trim();
        const answersStr = document.getElementById('fill-answers-input')?.value.trim();
        if (!stem || !answersStr) {
          showInteractiveError(!stem ? 'fill-stem-input' : 'fill-answers-input', 'Nhập câu hỏi và đáp án cho từng ô trống.');
          return;
        }
        const blankCount = (stem.match(/_{3,}/g) || []).length || 1;
        if (blankCount > 6) {
          showInteractiveError('fill-stem-input', 'Một câu hỏi có tối đa 6 ô trống.');
          return;
        }
        const acceptedGroups = answersStr.split(';').map(group =>
          group.split(',').map(answer => answer.trim()).filter(Boolean)
        );
        if (acceptedGroups.length !== blankCount || acceptedGroups.some(group => !group.length)) {
          showInteractiveError('fill-answers-input', `Cần ${blankCount} nhóm đáp án, ngăn bằng dấu chấm phẩy.`);
          return;
        }
        newQuestion = {
          stem: `[[PWD301:FI_V1]]${stem}`,
          question_text: stem,
          question_type: 'Fill in the blank',
          type: 'SHORT_ANSWER',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          accepted_answers: acceptedGroups.flatMap((group, groupIndex) => group.map(answer =>
            `[[PWD301:FI:${groupIndex + 1}]]${answer}`
          )),
          is_interactive: true,
          interactive_type: 'FILL_IN'
        };
      } else if (activeTab === 'match') {
        const stem = document.getElementById('match-stem-input')?.value.trim();
        const rows = document.querySelectorAll('.match-pair-row');
        const allPairs = Array.from(rows).map(row => ({
          left: row.querySelector('.pair-left')?.value.trim() || '',
          right: row.querySelector('.pair-right')?.value.trim() || ''
        }));
        const pairs = allPairs.filter(pair => pair.left && pair.right);
        if (allPairs.some(pair => Boolean(pair.left) !== Boolean(pair.right))) {
          showInteractiveError('match-stem-input', 'Điền đủ cả hai vế cho mỗi cặp ghép.');
          return;
        }
        if (!stem || pairs.length < 2) {
          showInteractiveError('match-stem-input', 'Nhập đề bài và ít nhất hai cặp ghép đầy đủ.');
          return;
        }
        const normalizedLefts = pairs.map(pair => pair.left.toLocaleLowerCase());
        const normalizedRights = pairs.map(pair => pair.right.toLocaleLowerCase());
        if (new Set(normalizedLefts).size !== pairs.length || new Set(normalizedRights).size !== pairs.length) {
          showInteractiveError('match-stem-input', 'Mỗi vế trong danh sách phải khác nhau.');
          return;
        }
        if (pairs.length > 6) {
          showInteractiveError('match-stem-input', 'Một câu hỏi có tối đa 6 cặp ghép.');
          return;
        }
        const choices = pairs.flatMap((leftPair, leftIndex) => pairs.map((rightPair, rightIndex) => ({
          content: `[[PWD301:G:MATCH:${leftIndex + 1}]]${leftPair.left}|||${rightPair.right}`,
          is_correct: leftIndex === rightIndex,
          position: leftIndex * pairs.length + rightIndex + 1
        })));
        newQuestion = {
          stem,
          question_text: stem,
          question_type: 'Matching pairs',
          type: 'MULTIPLE_CHOICE',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          choices,
          is_interactive: true,
          interactive_type: 'MATCHING',
          pairs
        };
      }
      if (newQuestion) {
        if (pendingImageAssetId) newQuestion.image_asset_id = pendingImageAssetId;
        window.ExamStore.appendQuestions([newQuestion]);
        pendingImageAssetId = null;
        const imageInput = document.getElementById('interactive-image-input');
        if (imageInput) imageInput.value = '';
        const imageStatus = document.getElementById('interactive-image-status');
        if (imageStatus) imageStatus.textContent = 'PNG, JPEG, WebP, or GIF up to 5 MB.';
        interactiveQuestions.push(newQuestion);
        for (const id of ['drag-stem-input', 'drag-distractors-input', 'fill-stem-input', 'fill-answers-input', 'match-stem-input', 'interactive-exp-input']) {
          const field = document.getElementById(id);
          if (field) field.value = '';
        }
        document.querySelectorAll('.match-pair-row').forEach(row => {
          const left = row.querySelector('.pair-left');
          const right = row.querySelector('.pair-right');
          if (left) left.value = '';
          if (right) right.value = '';
        });
        renderQuestionsList();
        renderLivePreview();
        document.getElementById(activeTab === 'drag' ? 'drag-stem-input' : activeTab === 'fill' ? 'fill-stem-input' : 'match-stem-input')?.focus();
        UI.showToast('Đã thêm câu hỏi. Bạn có thể soạn câu tiếp theo.', 'success');
      }
    });

    const chr = (n) => String.fromCharCode(n);

    // Render Questions List
    const renderQuestionsList = () => {
      const typeLabels = {
        MULTIPLE_CHOICE: 'Trắc nghiệm',
        SINGLE_CHOICE: 'Chọn một đáp án',
        MULTI_SELECT: 'Chọn nhiều đáp án',
        'Drag and drop': 'Kéo thả từ',
        'Fill in the blank': 'Điền khuyết',
        'Matching pairs': 'Ghép đôi',
        DRAG_AND_DROP: 'Kéo thả từ',
        FILL_IN_THE_BLANK: 'Điền khuyết',
        MATCHING: 'Ghép đôi'
      };
      const currentDraft = window.ExamStore.getDraft();
      const listEl = document.getElementById('interactive-questions-list');
      const badge = document.getElementById('exam-questions-count-badge');
      const qList = currentDraft.questions || [];

      if (badge) badge.textContent = `${qList.length} câu`;
      if (!listEl) return;

      if (qList.length === 0) {
        listEl.innerHTML = `
          <div class="p-6 text-center text-slate-400 text-xs">
            Đề thi chưa có câu hỏi. Soạn câu hỏi ở bên trái rồi bấm Thêm Câu Hỏi.
          </div>
        `;
        return;
      }

      listEl.innerHTML = qList.map((q, i) => `
        <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-start justify-between gap-3 text-xs">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-bold text-[11px]">Câu ${i + 1}</span>
              <span class="text-slate-500 font-medium">${typeLabels[q.question_type || q.type] || 'Câu hỏi'}</span>
              <span class="text-indigo-600 font-semibold">• ${(q.points || 1.0).toFixed(1)}đ</span>
            </div>
            <p class="font-semibold text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(String(q.stem || q.question_text || '').replace(/^\[\[PWD301:FI_V1\]\]/, ''))}</p>
          </div>
          <button type="button" class="text-slate-400 hover:text-rose-500 p-1" title="Xóa câu này" onclick="window.handleDeleteQuestion(${i})">
            <span class="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      `).join('');
    };

    window.handleDeleteQuestion = (index) => {
      window.ExamStore.deleteQuestion(index);
      UI.showToast('Đã xóa câu hỏi khỏi đề thi.', 'info');
      renderQuestionsList();
    };

    document.getElementById('btn-go-to-matrix')?.addEventListener('click', () => {
      const currentDraft = window.ExamStore.getDraft();
      if (!currentDraft.questions || currentDraft.questions.length === 0) {
        UI.showToast('Thêm ít nhất một câu hỏi trước khi kiểm tra đề.', 'warning');
        return;
      }
      window.location.hash = '#/instructor/exams/matrix';
    });

    // Form live listeners
    ['drag-stem-input', 'drag-distractors-input', 'fill-stem-input', 'fill-answers-input', 'match-stem-input'].forEach(id => {
      document.getElementById(id)?.addEventListener('input', renderLivePreview);
    });

    renderLivePreview();
    renderQuestionsList();
  };


  // =========================================================================
  // 5. PAGE 2c: Excel Import Studio (#/instructor/exams/excel)
  //    Template download, File Dropzone, Data Validation Grid, Append / Replace
  // =========================================================================
  InstructorView.renderExamExcel = function (container) {
    let parsedQuestions = [];
    let warningsList = [];
    let errorsList = [];

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(2, 'Tạo đề từ tệp Excel', '#/instructor/exams/matrix', 'Tiếp tục: Ma trận học vụ')}

        <main class="flex-1 overflow-y-auto max-w-[1520px] mx-auto px-4 sm:px-6 py-6 w-full pb-28">
          
          <!-- Download Template Banner -->
          <div class="mb-6 p-5 rounded-2xl bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center material-symbols-outlined text-[24px] shrink-0 shadow-xs">
                table_view
              </div>
              <div>
                <h3 class="font-bold text-sm sm:text-base text-emerald-950 dark:text-emerald-200">
                  Import danh sách câu hỏi hàng loạt bằng tệp Excel chuẩn hóa
                </h3>
                <p class="text-xs text-emerald-700 dark:text-emerald-300 mt-0.5">
                  Tải bảng tính mẫu chuẩn 8 cột (STT, Loại câu, Nội dung, Các phương án A/B/C/D, Đáp án đúng, Điểm, Mức độ Bloom, Giải thích).
                </p>
              </div>
            </div>
            <button
              type="button"
              id="btn-download-excel-template"
              class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all flex items-center gap-2 self-start md:self-auto shrink-0"
            >
              <span class="material-symbols-outlined text-[18px]">download</span>
              <span>Tải tệp Excel mẫu (.xlsx)</span>
            </button>
          </div>

          <!-- Upload Dropzone -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs mb-6" id="excel-upload-card">
            <div class="dashed-dropzone relative rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30 hover:bg-emerald-50/20 group" id="excel-drop-target">
              <input type="file" id="excel-file-input" accept=".xlsx,.xls" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
              <div class="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center mb-3 transition-transform group-hover:scale-110 shadow-xs">
                <span class="material-symbols-outlined text-3xl">upload_file</span>
              </div>
              <p class="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                Kéo thả bảng tính Excel vào đây hoặc <span class="text-emerald-600 underline underline-offset-2">bấm để chọn tệp (.xlsx, .xls)</span>
              </p>
              <p class="text-xs text-slate-500">
                Hệ thống hỗ trợ cả định dạng mẫu chính thức lẫn bảng tính có tên cột linh hoạt.
              </p>
            </div>
          </div>

          <!-- Data Validation Grid (Appears after parse) -->
          <div id="excel-validation-grid-container" class="hidden bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs space-y-4">
            
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>Bảng kiểm định dữ liệu câu hỏi Excel (Data Validation Grid)</span>
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700" id="excel-parsed-count-badge">
                    0 câu hỏi
                  </span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">Kiểm tra trạng thái từng dòng câu hỏi trước khi lưu vào đề thi.</p>
              </div>

              <!-- Append vs Replace Radio -->
              <div class="flex items-center gap-4 text-xs font-semibold p-1.5 bg-slate-100 dark:bg-slate-800 rounded-xl">
                <label class="flex items-center gap-1.5 cursor-pointer text-slate-700 dark:text-slate-300">
                  <input type="radio" name="excel_import_mode" value="append" checked class="text-emerald-600 focus:ring-emerald-500" />
                  <span>Nạp nối tiếp (Append)</span>
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer text-slate-700 dark:text-slate-300">
                  <input type="radio" name="excel_import_mode" value="replace" class="text-emerald-600 focus:ring-emerald-500" />
                  <span>Ghi đè mới (Replace)</span>
                </label>
              </div>
            </div>

            <!-- Validation Warnings Box -->
            <div id="excel-warnings-box" class="hidden p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 text-xs text-amber-800 dark:text-amber-300">
              <!-- Warning messages -->
            </div>

            <!-- Table -->
            <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-[500px] overflow-y-auto">
              <table class="w-full text-left text-xs border-collapse">
                <thead class="bg-slate-50 dark:bg-slate-800/80 sticky top-0 z-10 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th class="p-3 w-12 text-center">STT</th>
                    <th class="p-3 w-28">Loại câu</th>
                    <th class="p-3 min-w-[240px]">Nội dung câu hỏi</th>
                    <th class="p-3 min-w-[200px]">Các phương án</th>
                    <th class="p-3 w-28 text-center">Đáp án đúng</th>
                    <th class="p-3 w-16 text-center">Điểm</th>
                    <th class="p-3 w-24 text-center">Bloom</th>
                    <th class="p-3 w-24 text-center">Trạng thái</th>
                  </tr>
                </thead>
                <tbody id="excel-table-body" class="divide-y divide-slate-100 dark:divide-slate-800">
                  <!-- Rows -->
                </tbody>
              </table>
            </div>

            <!-- Action Bar -->
            <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
              <button type="button" id="btn-reupload-excel" class="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-semibold underline">
                Tải tệp Excel khác
              </button>

              <button
                type="button"
                id="btn-confirm-excel-import"
                class="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold rounded-xl text-xs shadow-md shadow-emerald-500/20 transition-all flex items-center gap-2"
              >
                <span class="material-symbols-outlined text-[18px]">check_circle</span>
                <span>Xác nhận lưu vào đề thi & Tiếp tục</span>
              </button>
            </div>

          </div>

        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(2, '#/instructor/exams/matrix', () => {
      window.location.hash = '#/instructor/exams/matrix';
    });

    // Download template
    document.getElementById('btn-download-excel-template')?.addEventListener('click', () => {
      ApiClient.downloadExcelExamTemplate();
    });

    const dropTarget = document.getElementById('excel-drop-target');
    const fileInput = document.getElementById('excel-file-input');
    const gridContainer = document.getElementById('excel-validation-grid-container');
    const uploadCard = document.getElementById('excel-upload-card');

    const handleExcelFile = async (file) => {
      if (!file) return;
      UI.showToast(`Đang bóc tách tệp Excel: ${file.name}...`, 'info');

      try {
        const res = await ApiClient.parseExcelExam(file);
        if (!res || !res.success) {
          throw new Error(res?.errors?.[0] || 'Không thể bóc tách câu hỏi từ tệp Excel.');
        }

        parsedQuestions = res.questions || [];
        warningsList = res.warnings || [];
        errorsList = res.errors || [];

        renderValidationGrid(parsedQuestions, warningsList);
        uploadCard?.classList.add('hidden');
        gridContainer?.classList.remove('hidden');
        UI.showToast(`Đã bóc tách thành công ${res.total_questions} câu hỏi từ Excel!`, 'success');
      } catch (err) {
        console.error('Lỗi phân tích Excel:', err);
        UI.showToast(`Lỗi bóc tách: ${err.message || err}`, 'error');
      }
    };

    dropTarget?.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropTarget.classList.add('bg-emerald-50/50', 'border-emerald-500');
    });
    dropTarget?.addEventListener('dragleave', (e) => {
      e.preventDefault();
      dropTarget.classList.remove('bg-emerald-50/50', 'border-emerald-500');
    });
    dropTarget?.addEventListener('drop', (e) => {
      e.preventDefault();
      dropTarget.classList.remove('bg-emerald-50/50', 'border-emerald-500');
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) handleExcelFile(files[0]);
    });
    fileInput?.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) handleExcelFile(e.target.files[0]);
    });

    document.getElementById('btn-reupload-excel')?.addEventListener('click', () => {
      uploadCard?.classList.remove('hidden');
      gridContainer?.classList.add('hidden');
    });

    // Render Table Body
    const renderValidationGrid = (questions, warnings) => {
      const tbody = document.getElementById('excel-table-body');
      const badge = document.getElementById('excel-parsed-count-badge');
      const warnBox = document.getElementById('excel-warnings-box');

      if (badge) badge.textContent = `${questions.length} câu hỏi`;

      if (warnings && warnings.length > 0) {
        warnBox.classList.remove('hidden');
        warnBox.innerHTML = `
          <strong>Lưu ý bóc tách:</strong>
          <ul class="list-disc list-inside mt-1 space-y-0.5">
            ${warnings.map(w => `<li>${UI.escapeHtml(w)}</li>`).join('')}
          </ul>
        `;
      } else {
        warnBox?.classList.add('hidden');
      }

      if (!tbody) return;
      tbody.innerHTML = questions.map((q, idx) => {
        const hasCorrect = q.choices ? q.choices.some(c => c.is_correct) : Boolean(q.accepted_answers);
        const statusBadge = hasCorrect
          ? `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">✓ Hợp lệ</span>`
          : `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700">⚠️ Thiếu key</span>`;

        const choicesHtml = (q.choices || []).map(c => `
          <span class="inline-block px-1.5 py-0.5 rounded text-[11px] mr-1 ${c.is_correct ? 'bg-emerald-100 text-emerald-800 font-bold' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}">
            ${c.label}. ${UI.escapeHtml(c.content)}
          </span>
        `).join('') || (q.accepted_answers ? `Đáp án: <strong>${q.accepted_answers.join(', ')}</strong>` : '');

        const correctKeys = (q.choices || []).filter(c => c.is_correct).map(c => c.label).join(', ') || (q.accepted_answers ? q.accepted_answers[0] : '');

        return `
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
            <td class="p-3 text-center font-bold text-slate-500">${idx + 1}</td>
            <td class="p-3 font-semibold text-slate-700 dark:text-slate-300">${q.question_type}</td>
            <td class="p-3 font-medium text-slate-900 dark:text-white">${UI.escapeHtml(q.stem || q.question_text)}</td>
            <td class="p-3">${choicesHtml}</td>
            <td class="p-3 text-center font-bold text-emerald-600">${correctKeys || '—'}</td>
            <td class="p-3 text-center font-semibold">${(q.points || 1.0).toFixed(1)}</td>
            <td class="p-3 text-center">${q.bloom_level}</td>
            <td class="p-3 text-center">${statusBadge}</td>
          </tr>
        `;
      }).join('');
    };

    // Confirm Import
    document.getElementById('btn-confirm-excel-import')?.addEventListener('click', () => {
      if (!parsedQuestions || parsedQuestions.length === 0) {
        UI.showToast('Chưa có câu hỏi nào để lưu vào đề thi!', 'warning');
        return;
      }

      const mode = document.querySelector('input[name="excel_import_mode"]:checked')?.value || 'append';
      if (mode === 'append') {
        window.ExamStore.appendQuestions(parsedQuestions);
        UI.showToast(`Đã nạp nối tiếp ${parsedQuestions.length} câu hỏi vào đề thi thành công!`, 'success');
      } else {
        window.ExamStore.replaceQuestions(parsedQuestions);
        UI.showToast(`Đã thay thế toàn bộ đề thi bằng ${parsedQuestions.length} câu hỏi từ Excel!`, 'success');
      }

      window.location.hash = '#/instructor/exams/matrix';
    });
  };


  // =========================================================================
  // 6. PAGE 2d: LMS Moodle XML & JSON Studio (#/instructor/exams/moodle)
  //    Upload file & Direct Raw Code Paste Editor
  // =========================================================================
  InstructorView.renderExamMoodle = function (container) {
    let activeFormat = 'xml'; // 'xml' | 'json'
    let activeMode = 'paste';  // 'paste' | 'upload'
    let parsedQuestions = [];

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(2, 'Nạp chuẩn Moodle XML / JSON', '#/instructor/exams/matrix', 'Tiếp tục: Ma trận học vụ')}

        <main class="flex-1 overflow-y-auto max-w-[1520px] mx-auto px-4 sm:px-6 py-6 w-full pb-28">
          
          <!-- Banner -->
          <div class="mb-6 p-5 rounded-2xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
            <div class="flex items-center gap-3.5">
              <div class="w-12 h-12 rounded-xl bg-amber-600 text-white flex items-center justify-center material-symbols-outlined text-[24px] shrink-0 shadow-xs">
                code_blocks
              </div>
              <div>
                <h3 class="font-bold text-sm sm:text-base text-amber-950 dark:text-amber-200">
                  Nạp từ Chuẩn LMS Quốc tế Moodle XML & JSON
                </h3>
                <p class="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
                  Tương thích hoàn toàn với định dạng xuất ngân hàng câu hỏi của Moodle và trao đổi dữ liệu học thuật JSON.
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 self-start md:self-auto shrink-0">
              <button type="button" id="btn-download-moodle-xml-sample" class="px-3.5 py-2 bg-white dark:bg-slate-900 border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200 font-bold rounded-xl text-xs hover:bg-amber-100 transition-colors shadow-xs">
                Tải mẫu XML (.xml)
              </button>
              <button type="button" id="btn-download-json-sample" class="px-3.5 py-2 bg-white dark:bg-slate-900 border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200 font-bold rounded-xl text-xs hover:bg-amber-100 transition-colors shadow-xs">
                Tải mẫu JSON (.json)
              </button>
            </div>
          </div>

          <!-- Controls Bar -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs mb-6 flex flex-wrap items-center justify-between gap-4">
            <!-- Format Selector -->
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Định dạng:</span>
              <div class="inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-bold">
                <button type="button" id="format-btn-xml" class="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-amber-700 dark:text-amber-300 shadow-xs transition-all">
                  Moodle XML
                </button>
                <button type="button" id="format-btn-json" class="px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all">
                  Chuẩn hóa JSON
                </button>
              </div>
            </div>

            <!-- Input Mode Selector -->
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Hình thức nạp:</span>
              <div class="inline-flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-bold">
                <button type="button" id="mode-btn-paste" class="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 shadow-xs transition-all">
                  Dán mã nguồn trực tiếp
                </button>
                <button type="button" id="mode-btn-upload" class="px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all">
                  Nạp tệp tải lên
                </button>
              </div>
            </div>

            <!-- Paste sample button -->
            <button type="button" id="btn-paste-sample-code" class="text-indigo-600 hover:underline font-bold text-xs flex items-center gap-1">
              <span class="material-symbols-outlined text-[16px]">content_paste</span>
              <span>Dán mã mẫu thử nghiệm</span>
            </button>
          </div>

          <!-- Input Area (Editor vs Upload) -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs mb-6 space-y-4">
            
            <!-- Paste Textarea -->
            <div id="moodle-paste-container" class="space-y-3">
              <div class="flex items-center justify-between text-xs text-slate-500">
                <span class="font-mono font-semibold" id="moodle-code-label">Khung dán mã Moodle XML:</span>
                <span class="text-[11px]">Hỗ trợ định dạng UTF-8</span>
              </div>
              <textarea
                id="moodle-raw-textarea"
                rows="12"
                class="w-full p-4 font-mono text-xs sm:text-sm text-slate-900 dark:text-white bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl outline-none focus:border-amber-500 leading-relaxed"
                spellcheck="false"
                placeholder="Dán nội dung tệp XML hoặc JSON vào đây..."
              ></textarea>
            </div>

            <!-- Upload File Dropzone -->
            <div id="moodle-upload-container" class="hidden space-y-3">
              <div class="dashed-dropzone relative rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50/50 dark:bg-slate-800/30 hover:bg-amber-50/20 group" id="moodle-drop-target">
                <input type="file" id="moodle-file-input" accept=".xml,.json,.txt" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                <div class="w-14 h-14 rounded-2xl bg-amber-50 dark:bg-amber-950 text-amber-600 flex items-center justify-center mb-3 transition-transform group-hover:scale-110 shadow-xs">
                  <span class="material-symbols-outlined text-3xl">cloud_upload</span>
                </div>
                <p class="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-200 mb-1">
                  Kéo thả tệp <span id="upload-ext-label">.xml</span> vào đây hoặc bấm để chọn tệp
                </p>
                <p class="text-xs text-slate-500">Hệ thống sẽ tự kiểm tra định dạng câu hỏi.</p>
              </div>
            </div>

            <!-- Parse Button -->
            <div class="flex items-center justify-between pt-2">
              <div class="flex items-center gap-4 text-xs font-semibold p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
                <label class="flex items-center gap-1.5 cursor-pointer text-slate-700 dark:text-slate-300">
                  <input type="radio" name="moodle_import_mode" value="append" checked class="text-amber-600 focus:ring-amber-500" />
                  <span>Nạp nối tiếp (Append)</span>
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer text-slate-700 dark:text-slate-300">
                  <input type="radio" name="moodle_import_mode" value="replace" class="text-amber-600 focus:ring-amber-500" />
                  <span>Ghi đè mới (Replace)</span>
                </label>
              </div>

              <button
                type="button"
                id="btn-parse-moodle-code"
                class="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 active:bg-amber-800 text-white font-bold rounded-xl text-xs shadow-md shadow-amber-500/20 transition-all flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[18px]">verified</span>
                <span>Đọc Và Kiểm Tra Tệp</span>
              </button>
            </div>

          </div>

          <!-- Parsed Questions Preview Box -->
          <div id="moodle-preview-box" class="hidden bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Kết quả bóc tách câu hỏi</span>
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700" id="moodle-parsed-count-badge">
                  0 câu
                </span>
              </h3>
              <button
                type="button"
                id="btn-confirm-moodle-import"
                class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs shadow-xs transition-colors flex items-center gap-1.5"
              >
                <span>Xác nhận lưu vào đề thi & Tiếp tục</span>
                <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>

            <div id="moodle-cards-list" class="space-y-3">
              <!-- Parsed cards -->
            </div>
          </div>

        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(2, '#/instructor/exams/matrix', () => {
      window.location.hash = '#/instructor/exams/matrix';
    });

    // Sample downloads
    document.getElementById('btn-download-moodle-xml-sample')?.addEventListener('click', () => {
      ApiClient.downloadMoodleXmlSample();
    });
    document.getElementById('btn-download-json-sample')?.addEventListener('click', () => {
      ApiClient.downloadMoodleJsonSample();
    });

    const formatBtnXml = document.getElementById('format-btn-xml');
    const formatBtnJson = document.getElementById('format-btn-json');
    const modeBtnPaste = document.getElementById('mode-btn-paste');
    const modeBtnUpload = document.getElementById('mode-btn-upload');
    const pasteContainer = document.getElementById('moodle-paste-container');
    const uploadContainer = document.getElementById('moodle-upload-container');
    const codeLabel = document.getElementById('moodle-code-label');
    const rawTextarea = document.getElementById('moodle-raw-textarea');
    const uploadExtLabel = document.getElementById('upload-ext-label');

    // Format toggle
    formatBtnXml?.addEventListener('click', () => {
      activeFormat = 'xml';
      formatBtnXml.className = "px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-amber-700 dark:text-amber-300 shadow-xs transition-all";
      formatBtnJson.className = "px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all";
      if (codeLabel) codeLabel.textContent = "Khung dán mã Moodle XML:";
      if (uploadExtLabel) uploadExtLabel.textContent = ".xml";
    });

    formatBtnJson?.addEventListener('click', () => {
      activeFormat = 'json';
      formatBtnJson.className = "px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-amber-700 dark:text-amber-300 shadow-xs transition-all";
      formatBtnXml.className = "px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all";
      if (codeLabel) codeLabel.textContent = "Khung dán mã JSON câu hỏi:";
      if (uploadExtLabel) uploadExtLabel.textContent = ".json";
    });

    // Mode toggle
    modeBtnPaste?.addEventListener('click', () => {
      activeMode = 'paste';
      modeBtnPaste.className = "px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 shadow-xs transition-all";
      modeBtnUpload.className = "px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all";
      pasteContainer.classList.remove('hidden');
      uploadContainer.classList.add('hidden');
    });

    modeBtnUpload?.addEventListener('click', () => {
      activeMode = 'upload';
      modeBtnUpload.className = "px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 shadow-xs transition-all";
      modeBtnPaste.className = "px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 transition-all";
      uploadContainer.classList.remove('hidden');
      pasteContainer.classList.add('hidden');
    });

    // Paste sample code
    document.getElementById('btn-paste-sample-code')?.addEventListener('click', async () => {
      if (activeFormat === 'xml') {
        const sampleXml = `<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Giao thức HTTPS</text></name>
    <questiontext format="html"><text><![CDATA[<p>Đâu là giao thức truyền tải siêu văn bản an toàn?</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <single>true</single>
    <answer fraction="0"><text>HTTP</text></answer>
    <answer fraction="100"><text>HTTPS</text></answer>
    <answer fraction="0"><text>FTP</text></answer>
    <answer fraction="0"><text>Telnet</text></answer>
  </question>
  <question type="truefalse">
    <name><text>Khóa ngoại</text></name>
    <questiontext format="html"><text><![CDATA[<p>Khóa ngoại có thể mang giá trị NULL.</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <answer fraction="100"><text>true</text></answer>
    <answer fraction="0"><text>false</text></answer>
  </question>
</quiz>`;
        if (rawTextarea) rawTextarea.value = sampleXml;
      } else {
        const sampleJson = JSON.stringify({
          questions: [
            {
              question_type: "SINGLE_CHOICE",
              stem: "Đâu là giao thức truyền tải an toàn?",
              points: 1.0,
              choices: [
                { label: "A", content: "HTTP", is_correct: false },
                { label: "B", content: "HTTPS", is_correct: true },
                { label: "C", content: "FTP", is_correct: false },
                { label: "D", content: "Telnet", is_correct: false }
              ]
            }
          ]
        }, null, 2);
        if (rawTextarea) rawTextarea.value = sampleJson;
      }
      UI.showToast('Đã dán đoạn mã mẫu vào khung soạn thảo!', 'info');
    });

    // Parse button handler
    const previewBox = document.getElementById('moodle-preview-box');
    const cardsList = document.getElementById('moodle-cards-list');
    const countBadge = document.getElementById('moodle-parsed-count-badge');

    const executeParse = async (contentOrFile) => {
      UI.showToast('Đang bóc tách cú pháp...', 'info');
      try {
        let res = null;
        if (activeFormat === 'xml') {
          res = await ApiClient.parseMoodleXml(contentOrFile);
        } else {
          res = await ApiClient.parseMoodleJson(contentOrFile);
        }

        if (!res || !res.success || !res.questions || res.questions.length === 0) {
          throw new Error(res?.errors?.[0] || 'Không tìm thấy câu hỏi hợp lệ.');
        }

        parsedQuestions = res.questions;
        if (countBadge) countBadge.textContent = `${parsedQuestions.length} câu hỏi`;

        cardsList.innerHTML = parsedQuestions.map((q, i) => `
          <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-2 text-xs">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[11px]">Câu ${i + 1}</span>
                <span class="font-semibold text-slate-700 dark:text-slate-300">${q.question_type || q.type}</span>
                <span class="text-indigo-600 font-semibold">• ${(q.points || 1.0).toFixed(1)}đ</span>
              </div>
              <span class="text-slate-400">${q.bloom_level || 'Thông hiểu'}</span>
            </div>
            <p class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(q.stem || q.question_text)}</p>
            <div class="space-y-1">
              ${(q.choices || []).map(c => `
                <div class="flex items-center gap-2 ${c.is_correct ? 'text-emerald-700 font-bold' : 'text-slate-600 dark:text-slate-400'}">
                  <span class="w-4 text-center">${c.is_correct ? '✓' : c.label}.</span>
                  <span>${UI.escapeHtml(c.content)}</span>
                </div>
              `).join('')}
              ${q.accepted_answers ? `<div class="text-emerald-700 font-bold">Đáp án chấp nhận: ${q.accepted_answers.join(', ')}</div>` : ''}
            </div>
          </div>
        `).join('');

        previewBox?.classList.remove('hidden');
        previewBox?.scrollIntoView({ behavior: 'smooth' });
        UI.showToast(`Đã bóc tách thành công ${parsedQuestions.length} câu hỏi!`, 'success');
      } catch (err) {
        console.error('Lỗi bóc tách Moodle XML/JSON:', err);
        UI.showToast(`Lỗi bóc tách: ${err.message || err}`, 'error');
      }
    };

    document.getElementById('btn-parse-moodle-code')?.addEventListener('click', () => {
      const code = rawTextarea?.value || '';
      if (!code.trim()) {
        UI.showToast('Vui lòng nhập hoặc dán mã nguồn trước khi bóc tách!', 'warning');
        return;
      }
      executeParse(code);
    });

    // File input handler
    document.getElementById('moodle-file-input')?.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        executeParse(e.target.files[0]);
      }
    });

    // Confirm import button
    document.getElementById('btn-confirm-moodle-import')?.addEventListener('click', () => {
      if (!parsedQuestions || parsedQuestions.length === 0) {
        UI.showToast('Chưa có câu hỏi nào để lưu!', 'warning');
        return;
      }
      const mode = document.querySelector('input[name="moodle_import_mode"]:checked')?.value || 'append';
      if (mode === 'append') {
        window.ExamStore.appendQuestions(parsedQuestions);
        UI.showToast(`Đã nạp nối tiếp ${parsedQuestions.length} câu hỏi vào đề thi!`, 'success');
      } else {
        window.ExamStore.replaceQuestions(parsedQuestions);
        UI.showToast(`Đã thay thế toàn bộ đề thi bằng ${parsedQuestions.length} câu hỏi!`, 'success');
      }
      window.location.hash = '#/instructor/exams/matrix';
    });
  };


  // =========================================================================
  // 7. PAGE 3: Academic Governance Matrix (#/instructor/exams/matrix)
  // =========================================================================
  InstructorView.renderExamMatrix = function (container) {
    const draft = window.ExamStore.getDraft();
    const questions = draft.questions || [];
    const totalPoints = questions.reduce((sum, q) => sum + (parseFloat(q.points) || 1.0), 0);

    const bloomStats = { 'Nhận biết': 0, 'Thông hiểu': 0, 'Vận dụng': 0 };
    questions.forEach(q => {
      const b = q.bloom_level || 'Thông hiểu';
      if (bloomStats[b] !== undefined) bloomStats[b]++;
      else bloomStats['Thông hiểu']++;
    });

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(3, 'Ma trận học vụ', '#/instructor/exams/settings', 'Tiếp tục: Cấu hình phòng thi')}

        <main class="flex-1 overflow-y-auto max-w-[1280px] mx-auto px-4 sm:px-6 py-6 w-full pb-28 space-y-6">
          
          <!-- Stepper Overview Summary -->
          <div class="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="p-3.5 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800">
              <span class="text-xs font-semibold text-indigo-700 dark:text-indigo-300">Tổng số câu hỏi</span>
              <p class="text-2xl font-bold text-slate-900 dark:text-white mt-1">${questions.length} <span class="text-xs font-medium text-slate-500">câu</span></p>
            </div>
            <div class="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
              <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Thang điểm tính toán</span>
              <p class="text-2xl font-bold text-slate-900 dark:text-white mt-1">${totalPoints.toFixed(1)} <span class="text-xs font-medium text-slate-500">điểm</span></p>
            </div>
            <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span class="text-xs font-semibold text-slate-600 dark:text-slate-400">Phân bổ Mức độ Bloom</span>
              <div class="flex items-center gap-2 mt-2 text-xs font-bold">
                <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800">NB: ${bloomStats['Nhận biết']}</span>
                <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-800">TH: ${bloomStats['Thông hiểu']}</span>
                <span class="px-2 py-0.5 rounded bg-rose-100 text-rose-800">VD: ${bloomStats['Vận dụng']}</span>
              </div>
            </div>
          </div>

          <!-- Academic Scope Configuration -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-6">
            <div class="border-b border-slate-100 dark:border-slate-800 pb-3 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                  <span class="material-symbols-outlined text-[20px]">school</span>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                    1. Xác định Bối cảnh & Phạm vi Học vụ (Academic Provenance)
                  </h3>
                  <p class="text-xs text-slate-500">Chỉ định học phần phụ trách và mục đích kiểm định</p>
                </div>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">Bắt buộc</span>
            </div>

            <!-- Mode Selector -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-3">Hình thức tổ chức đề thi</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label class="relative flex p-4 cursor-pointer rounded-xl border-2 border-indigo-600 bg-indigo-50/20 dark:bg-indigo-950/20 shadow-xs">
                  <input type="radio" name="matrix_academic_mode" value="independent" checked class="h-4 w-4 mt-0.5 text-indigo-600 focus:ring-indigo-500" />
                  <div class="ml-3">
                    <span class="block text-sm font-bold text-slate-900 dark:text-white">Khảo thí Độc lập / Tổng hợp</span>
                    <span class="block text-xs text-slate-500 mt-0.5">Kỳ thi đánh giá năng lực, thi giữa kỳ hoặc kết thúc học phần.</span>
                  </div>
                </label>
                <label class="relative flex p-4 cursor-pointer rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300">
                  <input type="radio" name="matrix_academic_mode" value="lesson_linked" class="h-4 w-4 mt-0.5 text-indigo-600 focus:ring-indigo-500" />
                  <div class="ml-3">
                    <span class="block text-sm font-bold text-slate-900 dark:text-white">Liên kết theo Bài học (Lesson-Linked)</span>
                    <span class="block text-xs text-slate-500 mt-0.5">Bài tập củng cố kiến thức gắn trực tiếp vào một bài học cụ thể.</span>
                  </div>
                </label>
              </div>
            </div>

            <!-- Course Selector -->
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2" for="matrix-course-select">
                Chọn Môn học phụ trách <span class="text-rose-500">*</span>
              </label>
              <select id="matrix-course-select" class="w-full p-3 text-xs sm:text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 bg-slate-50 dark:bg-slate-800">
                <option value="">-- Đang tải danh sách môn học... --</option>
              </select>
            </div>
          </div>

          <!-- Questions Matrix Table -->
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
            <h3 class="text-sm font-bold text-slate-900 dark:text-white">Danh sách câu hỏi trong ma trận đề thi</h3>
            <div class="divide-y divide-slate-100 dark:divide-slate-800 max-h-[360px] overflow-y-auto">
              ${questions.map((q, idx) => `
                <div class="py-2.5 flex items-center justify-between text-xs gap-3">
                  <div class="flex items-center gap-2.5 flex-1 min-w-0">
                    <span class="w-6 text-center font-bold text-slate-400">#${idx + 1}</span>
                    <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold">${q.question_type}</span>
                    <span class="font-medium text-slate-900 dark:text-white truncate">${UI.escapeHtml(q.stem || q.question_text)}</span>
                  </div>
                  <div class="flex items-center gap-3 shrink-0">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">${q.bloom_level}</span>
                    <span class="font-bold text-indigo-600">${(q.points || 1.0).toFixed(1)}đ</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Navigation Action Bar -->
          <div class="flex items-center justify-between pt-2">
            <button
              type="button"
              onclick="window.location.hash = '#/instructor/exams/editor'"
              class="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 text-slate-700 dark:text-slate-300 font-bold text-xs shadow-xs transition-colors flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Quay lại chỉnh sửa câu hỏi</span>
            </button>

            <button
              type="button"
              id="btn-matrix-proceed"
              class="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition-all flex items-center gap-2"
            >
              <span>Tiếp tục: Cấu hình phòng thi</span>
              <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>

        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(3, '#/instructor/exams/settings', () => {
      onProceedToSettings();
    });

    // Dynamic Course loader
    const courseSelect = document.getElementById('matrix-course-select');
    ApiClient.getInstructorCourses().then(res => {
      const courses = res.courses || [];
      if (courseSelect && courses.length > 0) {
        const targetId = draft.courseId || (courses[0] ? (courses[0].course_id || courses[0].id) : '');
        courseSelect.innerHTML = courses.map(c => {
          const cid = c.course_id || c.id || c.course_code;
          const isSelected = String(cid) === String(targetId);
          return `<option value="${cid}" ${isSelected ? 'selected' : ''}>
            ${c.course_code} - ${c.title}
          </option>`;
        }).join('');
      } else if (courseSelect) {
        courseSelect.innerHTML = `<option value="">Không tìm thấy môn học nào</option>`;
      }
    }).catch(err => {
      console.warn('Lỗi tải danh sách môn học:', err);
      if (courseSelect) courseSelect.innerHTML = `<option value="">Lỗi nạp môn học</option>`;
    });

    const onProceedToSettings = () => {
      const courseId = courseSelect?.value;
      if (!courseId) {
        UI.showToast('Vui lòng chọn môn học phụ trách cho đề thi!', 'warning');
        return;
      }
      const mode = document.querySelector('input[name="matrix_academic_mode"]:checked')?.value || 'independent';
      window.ExamStore.saveDraft({ courseId: courseId, academicMode: mode, matrixConfirmed: true });
      window.location.hash = '#/instructor/exams/settings';
    };

    document.getElementById('btn-matrix-proceed')?.addEventListener('click', onProceedToSettings);
  };


  // =========================================================================
  // 8. PAGE 4: Exam Settings & Final Publish (#/instructor/exams/settings)
  // =========================================================================
  InstructorView.renderExamSettings = function (container) {
    const draft = window.ExamStore.getDraft();
    const questions = draft.questions || [];
    const config = draft.config || {};

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(4, 'Cấu hình & Xuất bản', null, 'Xuất bản đề thi')}

        <main class="flex-1 overflow-y-auto max-w-[1280px] mx-auto px-4 sm:px-6 py-6 w-full pb-28 space-y-6">
          
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- Left: Config Forms (8 cols) -->
            <div class="lg:col-span-8 space-y-6">
              
              <!-- Card 1: Time & Attempts -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
                <div class="flex items-center gap-2.5 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <span class="material-symbols-outlined text-[22px] text-indigo-600">timer</span>
                  <h3 class="text-base font-bold text-slate-900 dark:text-white">1. Thời gian & Điều kiện làm bài</h3>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-assessment-type">
                      Thể loại đề thi <span class="text-rose-500">*</span>
                    </label>
                    <select id="cfg-assessment-type" class="w-full px-3.5 py-2 text-xs sm:text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 bg-slate-50 dark:bg-slate-800">
                      <option value="QUIZ" ${(!config.assessmentType || config.assessmentType === 'QUIZ') ? 'selected' : ''}>Bài kiểm tra ngắn (QUIZ)</option>
                      <option value="PRACTICE" ${config.assessmentType === 'PRACTICE' ? 'selected' : ''}>Luyện tập tự do (PRACTICE)</option>
                      <option value="MIDTERM" ${config.assessmentType === 'MIDTERM' ? 'selected' : ''}>Thi giữa kỳ (MIDTERM)</option>
                      <option value="FINAL" ${config.assessmentType === 'FINAL' ? 'selected' : ''}>Thi cuối kỳ (FINAL)</option>
                      <option value="PLACEMENT" ${config.assessmentType === 'PLACEMENT' ? 'selected' : ''}>Khảo sát năng lực (PLACEMENT)</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-duration">
                      Thời lượng làm bài (Phút) <span class="text-rose-500">*</span>
                    </label>
                    <input type="number" id="cfg-duration" min="5" max="300" value="${config.duration || 45}" class="w-full px-3.5 py-2 text-xs sm:text-sm font-bold border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 bg-slate-50 dark:bg-slate-800" />
                  </div>

                  <div>
                    <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-attempts">
                      Số lần làm bài tối đa
                    </label>
                    <select id="cfg-attempts" class="w-full px-3.5 py-2 text-xs sm:text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 bg-slate-50 dark:bg-slate-800">
                      <option value="1" ${config.maxAttempts === 1 ? 'selected' : ''}>1 lần duy nhất</option>
                      <option value="2" ${config.maxAttempts === 2 ? 'selected' : ''}>2 lần</option>
                      <option value="3" ${config.maxAttempts === 3 ? 'selected' : ''}>3 lần</option>
                      <option value="999" ${config.maxAttempts > 3 ? 'selected' : ''}>Không giới hạn (Luyện tập)</option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1" for="cfg-scoring-policy">
                      Quy chế tính điểm hiển thị
                    </label>
                    <select id="cfg-scoring-policy" class="w-full px-3.5 py-2 text-xs sm:text-sm font-semibold border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-indigo-500 bg-slate-50 dark:bg-slate-800">
                      <option value="HIGHEST" ${config.scoringPolicy === 'HIGHEST' || !config.scoringPolicy ? 'selected' : ''}>Lấy điểm cao nhất (HIGHEST)</option>
                      <option value="LATEST" ${config.scoringPolicy === 'LATEST' ? 'selected' : ''}>Lấy lần thi mới nhất (LATEST)</option>
                    </select>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
                  <label class="flex items-center gap-3 cursor-pointer text-xs font-semibold select-none">
                    <input type="checkbox" id="cfg-shuffle-all" class="rounded text-indigo-600 focus:ring-indigo-500" ${config.shuffleQuestions !== false ? 'checked' : ''} />
                    <span>Xáo trộn ngẫu nhiên thứ tự câu hỏi và phương án đáp án cho mỗi thí sinh</span>
                  </label>
                </div>
              </div>

              <!-- Card 2: Security & Proctoring -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
                <div class="flex items-center gap-2.5 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <span class="material-symbols-outlined text-[22px] text-indigo-600">security</span>
                  <h3 class="text-base font-bold text-slate-900 dark:text-slate-100">2. Cách hiển thị phòng thi</h3>
                </div>

                <div class="space-y-4 text-sm">
                  <div>
                    <label for="cfg-exam-layout" class="block font-semibold mb-2">Giao diện làm bài</label>
                    <select id="cfg-exam-layout" class="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2">
                      <option value="STANDARD" ${config.examLayout !== 'FOCUS' ? 'selected' : ''}>Tiêu chuẩn</option>
                      <option value="FOCUS" ${config.examLayout === 'FOCUS' ? 'selected' : ''}>Tập trung</option>
                    </select>
                  </div>
                  <label class="flex items-start gap-3 cursor-pointer">
                    <input type="checkbox" id="cfg-monitoring" class="mt-1 rounded text-indigo-600 focus:ring-indigo-500" ${config.monitoringEnabled ? 'checked' : ''} />
                    <span><strong class="block">Ghi nhận khi rời trang thi</strong><small class="block font-normal text-slate-600 dark:text-slate-300">Cảnh báo thí sinh và lưu lần rời tab, mất tiêu điểm hoặc thoát toàn màn hình để giảng viên xem lại.</small></span>
                  </label>
                  <label class="flex items-start gap-3 cursor-pointer">
                    <input type="checkbox" id="cfg-fullscreen" class="mt-1 rounded text-indigo-600 focus:ring-indigo-500" ${config.requestFullscreen ? 'checked' : ''} />
                    <span><strong class="block">Đề nghị mở toàn màn hình</strong><small class="block font-normal text-slate-600 dark:text-slate-300">Trình duyệt có thể từ chối; thí sinh vẫn làm bài được. Không khóa bàn di chuột hoặc chụp màn hình.</small></span>
                  </label>
                </div>
              </div>

            </div>

            <!-- Right: Pre-Flight Checklist & Publish Execution (4 cols) -->
            <div class="lg:col-span-4 space-y-6">
              
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
                <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-[20px] text-indigo-600">fact_check</span>
                  <span>Kiểm định kỹ thuật</span>
                </h3>

                <!-- Validation Status Checklist -->
                <div class="space-y-2.5 text-xs" id="preflight-status-list">
                  <!-- Generated dynamically -->
                </div>

                <!-- Auto fix missing keys button -->
                <div id="autofix-container" class="hidden pt-2">
                  <button type="button" id="btn-autofix-keys" class="w-full py-2 bg-amber-50 dark:bg-amber-950 text-amber-800 dark:text-amber-200 font-bold rounded-xl text-xs hover:bg-amber-100 transition-colors border border-amber-200">
                    ⚡ Tự động gán đáp án A cho câu thiếu key
                  </button>
                </div>

                <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
                  <label class="flex items-start gap-2.5 cursor-pointer text-xs text-slate-600 dark:text-slate-400 select-none">
                    <input type="checkbox" id="chk-publish-agreement" class="rounded text-indigo-600 focus:ring-indigo-500 mt-0.5" />
                    <span>Tôi đã kiểm tra nội dung đề thi và sẵn sàng xuất bản.</span>
                  </label>
                </div>

                <button
                  type="button"
                  id="btn-execute-publish-exam"
                  disabled
                  class="w-full py-3 bg-slate-300 text-slate-500 font-bold rounded-xl text-xs sm:text-sm transition-all cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <span class="material-symbols-outlined text-[20px]">rocket_launch</span>
                  <span>Xuất bản & Kích hoạt Ca thi</span>
                </button>
              </div>

            </div>

          </div>

        </main>
      </div>
    `;

    InstructorView.bindExamWorkflowHeaderEvents(4, null, () => {
      document.getElementById('btn-execute-publish-exam')?.click();
    });

    // Run Pre-flight Inspection
    const preflightList = document.getElementById('preflight-status-list');
    const btnAutoFix = document.getElementById('btn-autofix-keys');
    const autoFixBox = document.getElementById('autofix-container');
    const chkAgreement = document.getElementById('chk-publish-agreement');
    const btnPublish = document.getElementById('btn-execute-publish-exam');

    let hasFatalErrors = false;

    const runPreflight = () => {
      const currentDraft = window.ExamStore.getDraft();
      const qList = currentDraft.questions || [];
      let missingKeys = 0;

      qList.forEach(q => {
        if (q.choices && q.choices.length > 0 && !q.choices.some(c => c.is_correct)) {
          missingKeys++;
        }
      });

      hasFatalErrors = qList.length === 0;

      let itemsHtml = `
        <div class="flex items-center justify-between p-2.5 rounded-xl ${qList.length > 0 ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'}">
          <span>Số lượng câu hỏi:</span>
          <strong>${qList.length} câu ${qList.length > 0 ? '✓' : '❌ (Trống)'}</strong>
        </div>
      `;

      if (missingKeys > 0) {
        itemsHtml += `
          <div class="flex items-center justify-between p-2.5 rounded-xl bg-amber-50 text-amber-800">
            <span>Thiếu đáp án đúng:</span>
            <strong>${missingKeys} câu ⚠️</strong>
          </div>
        `;
        autoFixBox?.classList.remove('hidden');
      } else {
        itemsHtml += `
          <div class="flex items-center justify-between p-2.5 rounded-xl bg-emerald-50 text-emerald-800">
            <span>Đáp án đúng:</span>
            <strong>100% đầy đủ ✓</strong>
          </div>
        `;
        autoFixBox?.classList.add('hidden');
      }

      if (preflightList) preflightList.innerHTML = itemsHtml;
      updatePublishButtonState();
    };

    const updatePublishButtonState = () => {
      if (btnPublish && chkAgreement) {
        if (!hasFatalErrors && chkAgreement.checked) {
          btnPublish.disabled = false;
          btnPublish.className = "w-full py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-bold rounded-xl text-xs sm:text-sm shadow-md shadow-indigo-500/25 transition-all cursor-pointer flex items-center justify-center gap-2";
        } else {
          btnPublish.disabled = true;
          btnPublish.className = "w-full py-3 bg-slate-300 dark:bg-slate-800 text-slate-500 font-bold rounded-xl text-xs sm:text-sm transition-all cursor-not-allowed flex items-center justify-center gap-2";
        }
      }
    };

    chkAgreement?.addEventListener('change', updatePublishButtonState);

    // Auto-fix button
    btnAutoFix?.addEventListener('click', () => {
      const currentDraft = window.ExamStore.getDraft();
      let fixed = 0;
      (currentDraft.questions || []).forEach(q => {
        if (q.choices && q.choices.length > 0 && !q.choices.some(c => c.is_correct)) {
          q.choices[0].is_correct = true;
          fixed++;
        }
      });
      if (fixed > 0) {
        window.ExamStore.saveDraft({ questions: currentDraft.questions });
        UI.showToast(`Đã tự động gán đáp án A cho ${fixed} câu hỏi!`, 'success');
        runPreflight();
      }
    });

    // Execute Publish
    btnPublish?.addEventListener('click', async () => {
      const currentDraft = window.ExamStore.getDraft();
      const title = currentDraft.title || 'Bài kiểm tra mới';
      const duration = parseInt(document.getElementById('cfg-duration')?.value || 45, 10);
      const courseId = currentDraft.courseId;

      if (!courseId) {
        UI.showToast('Chưa chỉ định môn học cho đề thi! Vui lòng quay lại Bước 3.', 'warning');
        window.location.hash = '#/instructor/exams/matrix';
        return;
      }

      const conf = await UI.confirm(
        'Xác nhận Xuất bản Đề thi',
        `Bài thi "${title}" (${duration} phút) đã sẵn sàng. Bạn có muốn mở bài thi ngay bây giờ?`,
        'Xuất bản & Mở phòng thi'
      );
      if (!conf) return;

      try {
        UI.showToast('Đang tạo đề thi và lưu câu hỏi vào CSDL...', 'info');
        const maxAtt = parseInt(document.getElementById('cfg-attempts')?.value || 1, 10);
        const shuffle = document.getElementById('cfg-shuffle-all')?.checked ?? true;
        const scoringPolicy = document.getElementById('cfg-scoring-policy')?.value || 'HIGHEST';
        const policy = InstructorView.readExamPolicy();
        window.ExamStore.saveDraft({ config: {
          duration,
          maxAttempts: maxAtt,
          shuffleQuestions: shuffle,
          scoringPolicy,
          examLayout: policy.exam_layout,
          monitoringEnabled: policy.monitoring_enabled,
          requestFullscreen: policy.request_fullscreen
        } });

        // 1. Create or Update Assessment
        let asmId = currentDraft.isEditingExisting ? currentDraft.assessmentId : null;
        if (asmId) {
          await ApiClient.updateAssessment(asmId, {
            title: title,
            assessment_type: document.getElementById('cfg-assessment-type')?.value || currentDraft.assessment_type || 'QUIZ',
            duration_minutes: duration,
            max_attempts: maxAtt,
            require_password: false,
            shuffle_questions: shuffle,
            scoring_policy: scoringPolicy,
            ...policy
          });
        } else {
          const created = await ApiClient.createAssessment(courseId, {
            title: title,
            assessment_type: document.getElementById('cfg-assessment-type')?.value || currentDraft.assessment_type || 'QUIZ',
            duration_minutes: duration,
            max_attempts: maxAtt,
            require_password: false,
            shuffle_questions: shuffle,
            scoring_policy: scoringPolicy,
            ...policy
          });
          asmId = created?.assessment_id || created?.assessment?.public_id || created?.assessment?.id || created?.id;
        }

        const questionsToSave = currentDraft.questions || [];
        let createdQuestionsCount = 0;

        // 2. Batch create questions
        if (asmId && questionsToSave.length > 0) {
          const batchQuestions = questionsToSave.map(q => {
            let qType = 'SINGLE_CHOICE';
            if (q.type === 'MULTIPLE_CHOICE' || q.question_type === 'TN nhiều đáp án' || q.question_type === 'Kéo thả' || (q.stem && q.stem.includes('[[PWD301:G:DRAG:'))) qType = 'MULTIPLE_CHOICE';
            else if (q.type === 'TRUE_FALSE' || q.question_type === 'Đúng / Sai') qType = 'TRUE_FALSE';
            else if (q.type === 'SHORT_ANSWER' || q.question_type === 'Điền từ') qType = 'SHORT_ANSWER';
            else if (q.type === 'ESSAY' || q.question_type === 'Tự luận') qType = 'ESSAY';

            let diff = 'UNDERSTAND';
            if (q.bloom_level === 'Nhận biết') diff = 'REMEMBER';
            else if (q.bloom_level === 'Vận dụng') diff = 'APPLY';

            const payload = {
              question_type: qType,
              content: q.stem || q.question_text || `Câu hỏi`,
              difficulty: diff,
              points: parseFloat(q.points) || 1.0,
              explanation: q.explanation || '',
              image_asset_id: q.image_asset_id || null,
              resources: (Array.isArray(q.resources) && q.resources.length > 0) ? q.resources : (q.image_asset_id ? [{ asset_id: q.image_asset_id, position: 1, resource_role: 'IMAGE' }] : [])
            };

            if (qType === 'SHORT_ANSWER') {
              const ans = q.accepted_answers || (q.choices || []).map(c => c.content);
              payload.accepted_answers = ans.length > 0 ? ans : ['Đáp án'];
            } else {
              const choices = (q.choices || []).map((c, i) => ({
                content: c.content || c.text || '',
                is_correct: Boolean(c.is_correct),
                position: i + 1
              }));
              if (choices.length > 0 && !choices.some(c => c.is_correct)) {
                choices[0].is_correct = true;
              }
              payload.choices = choices;
            }
            return payload;
          });

          try {
            const batchRes = await ApiClient.createAssessmentQuestionsBatch(asmId, batchQuestions);
            createdQuestionsCount = batchRes?.created_count || batchQuestions.length;
          } catch (batchErr) {
            console.warn('Lỗi atomic batch, chuyển sang tuần tự:', batchErr);
            for (const p of batchQuestions) {
              try {
                await ApiClient.createAssessmentQuestion(asmId, p);
                createdQuestionsCount++;
              } catch (singleErr) {
                console.warn('Lỗi gán câu hỏi:', singleErr);
              }
            }
          }
        }

        // 3. Publish Assessment
        if (asmId && createdQuestionsCount > 0) {
          try {
            await ApiClient.publishAssessment(asmId);
            window.ExamStore.clearDraft();
            UI.showToast(`Đề thi "${title}" đã xuất bản thành công kèm ${createdQuestionsCount} câu hỏi lưu vào CSDL!`, 'success');
            window.location.hash = '#/instructor/dashboard';
          } catch (pubErr) {
            console.error('Lỗi kích hoạt xuất bản:', pubErr);
            UI.showToast(`Đề thi đã lưu nhưng kích hoạt xuất bản thất bại: ${pubErr.message || pubErr}. Bản nháp vẫn được giữ lại để bạn kiểm tra lại.`, 'warning');
          }
        } else {
          UI.showToast('Không có câu hỏi nào được lưu thành công vào đề thi. Vui lòng kiểm tra lại cấu trúc câu hỏi.', 'error');
        }
      } catch (err) {
        console.error('Lỗi xuất bản đề thi:', err);
        UI.showToast(`Lỗi xuất bản: ${err.message || err}`, 'error');
      }
    });

    runPreflight();
  };


  // =========================================================================
  // 8. Dedicated Exam Edit Studio (#/instructor/exams/edit)
  // =========================================================================
  InstructorView.renderExamEdit = async function (container, assessmentId, query = {}) {
    if (!assessmentId) {
      container.innerHTML = `
        <div class="max-w-2xl mx-auto py-16 px-4 text-center">
          <div class="w-16 h-16 rounded-2xl bg-amber-50 dark:bg-amber-950 text-amber-600 flex items-center justify-center mx-auto mb-4">
            <span class="material-symbols-outlined text-3xl">error_outline</span>
          </div>
          <h2 class="text-base font-bold text-slate-900 dark:text-white mb-1.5">Không tìm thấy mã đề thi</h2>
          <p class="text-xs text-slate-500 mb-6">Mã định danh đề thi không tồn tại hoặc chưa được cung cấp.</p>
          <a href="#/instructor/courses" class="px-5 py-2.5 rounded-xl bg-primary text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-sm">
            <span class="material-symbols-outlined text-[16px]">arrow_back</span>
            <span>Về danh sách khóa học</span>
          </a>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="max-w-6xl mx-auto py-16 px-4 text-center text-slate-400">
        <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
        <p class="text-xs font-semibold text-slate-600 dark:text-slate-300">Đang tải thông tin chi tiết đề thi...</p>
      </div>
    `;

    let detail;
    try {
      detail = await ApiClient.getAssessmentDetail(assessmentId);
    } catch (err) {
      container.innerHTML = `
        <div class="max-w-2xl mx-auto py-16 px-4 text-center">
          <div class="w-16 h-16 rounded-2xl bg-rose-50 dark:bg-rose-950 text-rose-600 flex items-center justify-center mx-auto mb-4">
            <span class="material-symbols-outlined text-3xl">error</span>
          </div>
          <h2 class="text-base font-bold text-slate-900 dark:text-white mb-1.5">Lỗi tải dữ liệu đề thi</h2>
          <p class="text-xs text-slate-500 mb-6">${UI.escapeHtml(err.message || String(err))}</p>
          <a href="#/instructor/courses" class="px-5 py-2.5 rounded-xl bg-primary text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-sm">
            <span class="material-symbols-outlined text-[16px]">arrow_back</span>
            <span>Về danh sách khóa học</span>
          </a>
        </div>
      `;
      return;
    }

    const assessment = detail.assessment || detail;
    let questions = detail.question_assignments || detail.questions || [];
    const isLocked = Boolean(assessment.first_attempt_started_at);
    const isPub = assessment.status === 'PUBLISHED';
    const cId = assessment.course_id || query.course_id || '';

    const render = () => {
      const totalPoints = questions.reduce((sum, q) => sum + (parseFloat(q.points) || 1.0), 0);

      container.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
          
          <!-- Top Header -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
            <div class="flex items-start gap-3">
              <a
                href="#/instructor/courses/${cId}?tab=assessments"
                class="p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors shrink-0 mt-0.5"
                title="Quay lại danh sách kỳ thi"
              >
                <span class="material-symbols-outlined text-[20px]">arrow_back</span>
              </a>
              <div>
                <div class="flex items-center gap-2 flex-wrap">
                  <h1 class="text-lg font-bold text-slate-900 dark:text-white">${UI.escapeHtml(assessment.title || 'Chỉnh sửa đề thi')}</h1>
                  <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${isPub ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200' : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-200'}">
                    ${isPub ? 'Đã xuất bản' : 'Bản nháp'}
                  </span>
                  ${isLocked ? `
                    <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border border-rose-200 flex items-center gap-1">
                      <span class="material-symbols-outlined text-[13px]">lock</span>
                      <span>Đã khóa cấu trúc (Invariant 14)</span>
                    </span>
                  ` : ''}
                </div>
                <div class="flex items-center gap-3 text-xs text-slate-500 mt-1">
                  <span>${questions.length} câu hỏi</span>
                  <span>•</span>
                  <span>Tổng ${totalPoints.toFixed(1)} điểm</span>
                  <span>•</span>
                  <span>${assessment.duration_minutes || 45} phút</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                id="btn-edit-in-studio"
                class="px-3.5 py-2 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-bold text-xs hover:bg-indigo-100 transition-colors inline-flex items-center gap-1.5"
                title="Mở toàn bộ câu hỏi trong trình soạn thảo cú pháp chia đôi màn hình"
              >
                <span class="material-symbols-outlined text-[16px]">terminal</span>
                <span>Soạn thảo Split-View</span>
              </button>

              ${!isPub ? `
                <button
                  type="button"
                  id="btn-publish-from-edit"
                  class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors inline-flex items-center gap-1.5 shadow-sm"
                >
                  <span class="material-symbols-outlined text-[16px]">publish</span>
                  <span>Xuất bản</span>
                </button>
              ` : ''}

              <button
                type="button"
                id="btn-save-edit-settings"
                class="px-5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-xs transition-colors inline-flex items-center gap-1.5 shadow-sm"
              >
                <span class="material-symbols-outlined text-[16px]">save</span>
                <span>Lưu thay đổi</span>
              </button>
            </div>
          </div>

          <!-- Main Layout: 2 Columns (Settings & Question List) -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- Left Column: Settings Panel -->
            <div class="lg:col-span-1 space-y-4">
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                  <span class="material-symbols-outlined text-[18px] text-primary">tune</span>
                  <span>Thông số & Cấu hình</span>
                </h3>

                <div class="space-y-3 text-xs">
                  <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Tên bài thi / Đề thi</label>
                    <input
                      type="text"
                      id="edit-exam-title"
                      class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-primary focus:bg-white dark:focus:bg-slate-900 transition-colors"
                      value="${UI.escapeHtml(assessment.title || '')}"
                    />
                  </div>

                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Thời lượng (phút)</label>
                      <input
                        type="number"
                        id="edit-exam-duration"
                        min="5"
                        max="360"
                        class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-primary"
                        value="${assessment.duration_minutes || 45}"
                      />
                    </div>
                    <div>
                      <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Số lần làm tối đa</label>
                      <input
                        type="number"
                        id="edit-exam-attempts"
                        min="1"
                        max="10"
                        class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-primary"
                        value="${assessment.max_attempts || 1}"
                      />
                    </div>
                  </div>

                  <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Cách tính điểm khi làm lại</label>
                    <select
                      id="edit-exam-scoring-policy"
                      class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-primary"
                    >
                      <option value="HIGHEST" ${assessment.scoring_policy === 'HIGHEST' ? 'selected' : ''}>Điểm cao nhất (HIGHEST)</option>
                      <option value="LATEST" ${assessment.scoring_policy === 'LATEST' ? 'selected' : ''}>Lần làm cuối cùng (LATEST)</option>
                      <option value="AVERAGE" ${assessment.scoring_policy === 'AVERAGE' ? 'selected' : ''}>Trung bình các lần làm (AVERAGE)</option>
                    </select>
                  </div>

                  <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Bố cục hiển thị câu hỏi</label>
                    <select
                      id="edit-exam-layout"
                      class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none focus:border-primary"
                    >
                      <option value="STANDARD" ${assessment.exam_layout === 'STANDARD' ? 'selected' : ''}>Tiêu chuẩn (Danh sách liên tục)</option>
                      <option value="SINGLE_QUESTION" ${assessment.exam_layout === 'SINGLE_QUESTION' ? 'selected' : ''}>Từng câu hỏi một</option>
                      <option value="ALL_PAGED" ${assessment.exam_layout === 'ALL_PAGED' ? 'selected' : ''}>Phân trang nhóm câu hỏi</option>
                    </select>
                  </div>

                  <div class="pt-2 space-y-2 border-t border-slate-100 dark:border-slate-800">
                    <label class="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        id="edit-exam-shuffle"
                        class="rounded text-primary focus:ring-primary"
                        ${assessment.shuffle_questions !== false ? 'checked' : ''}
                      />
                      <span class="text-slate-700 dark:text-slate-300 font-medium">Trộn thứ tự câu hỏi khi làm</span>
                    </label>

                    <label class="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        id="edit-exam-monitoring"
                        class="rounded text-primary focus:ring-primary"
                        ${assessment.monitoring_enabled ? 'checked' : ''}
                      />
                      <span class="text-slate-700 dark:text-slate-300 font-medium">Bật giám sát tab rời / gian lận</span>
                    </label>

                    <label class="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        id="edit-exam-fullscreen"
                        class="rounded text-primary focus:ring-primary"
                        ${assessment.request_fullscreen ? 'checked' : ''}
                      />
                      <span class="text-slate-700 dark:text-slate-300 font-medium">Bắt buộc chế độ toàn màn hình</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column: Question List & Reordering -->
            <div class="lg:col-span-2 space-y-4">
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
                
                <div class="flex items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3 flex-wrap">
                  <div>
                    <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span class="material-symbols-outlined text-[18px] text-primary">format_list_numbered</span>
                      <span>Danh sách & Thứ tự câu hỏi (${questions.length})</span>
                    </h3>
                    <p class="text-[11px] text-slate-500 mt-0.5">Sử dụng nút Mũi tên lên / xuống để hoán đổi thứ tự câu hỏi trong đề thi.</p>
                  </div>

                  ${!isLocked ? `
                    <button
                      type="button"
                      id="btn-open-add-question-modal"
                      class="px-3.5 py-1.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-xs"
                    >
                      <span class="material-symbols-outlined text-[15px]">add_circle</span>
                      <span>Thêm câu hỏi</span>
                    </button>
                  ` : ''}
                </div>

                ${isLocked ? `
                  <div class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2.5">
                    <span class="material-symbols-outlined text-[18px] text-amber-600 shrink-0 mt-0.5">lock</span>
                    <div>
                      <strong class="font-bold">Cấu trúc đề thi và phân bổ điểm số đã bị khóa (Invariant 14)</strong>
                      <p class="mt-0.5">Đã có sinh viên bắt đầu làm bài kiểm tra này. Các chức năng đổi thứ tự câu hỏi, xóa câu hỏi và điều chỉnh điểm bị khóa để bảo toàn tính toàn vẹn kết quả.</p>
                    </div>
                  </div>
                ` : ''}

                <!-- Question Cards Container -->
                <div id="edit-questions-list-container" class="space-y-3">
                  ${questions.length === 0 ? `
                    <div class="py-12 text-center text-slate-400 text-xs">
                      Đề thi này chưa có câu hỏi nào. Nhấn "Thêm câu hỏi" hoặc mở trong Studio Soạn thảo.
                    </div>
                  ` : questions.map((q, idx) => {
                    const qId = q.question_id || q.id;
                    const qStem = q.stem || q.content || q.question_text || 'Câu hỏi chưa có nội dung';
                    const qType = q.question_type || q.type || 'SINGLE_CHOICE';
                    const qPts = parseFloat(q.points) || 1.0;
                    return `
                      <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-slate-300 dark:hover:border-slate-700 transition-all flex items-start justify-between gap-3 text-xs" data-q-id="${qId}" data-q-index="${idx}">
                        
                        <!-- Left: Reorder buttons & Position badge -->
                        <div class="flex items-center gap-1.5 shrink-0 pt-0.5">
                          ${!isLocked ? `
                            <div class="flex flex-col gap-0.5">
                              <button
                                type="button"
                                class="btn-move-q-up w-6 h-6 rounded flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed"
                                ${idx === 0 ? 'disabled' : ''}
                                data-idx="${idx}"
                                title="Di chuyển lên trên"
                              >
                                <span class="material-symbols-outlined text-[16px]">arrow_upward</span>
                              </button>
                              <button
                                type="button"
                                class="btn-move-q-down w-6 h-6 rounded flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed"
                                ${idx === questions.length - 1 ? 'disabled' : ''}
                                data-idx="${idx}"
                                title="Di chuyển xuống dưới"
                              >
                                <span class="material-symbols-outlined text-[16px]">arrow_downward</span>
                              </button>
                            </div>
                          ` : ''}

                          <span class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold flex items-center justify-center border border-indigo-200/60 text-xs shrink-0">
                            #${idx + 1}
                          </span>
                        </div>

                        <!-- Center: Stem snippet & Type badge -->
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2 mb-1 flex-wrap">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                              ${qType}
                            </span>
                            <span class="text-[11px] text-slate-400">
                              ${(q.choices || []).length > 0 ? `${q.choices.length} phương án` : (q.accepted_answers ? 'Điền từ' : '')}
                            </span>
                          </div>
                          <p class="text-slate-800 dark:text-slate-200 line-clamp-2 leading-relaxed">
                            ${UI.escapeHtml(qStem.replace(/\[\[PWD301:(?:IMAGE|EXTRACTED_IMAGE):[^\]]+\]\]/gi, '').trim())}
                          </p>
                        </div>

                        <!-- Right: Points input & Delete button -->
                        <div class="flex items-center gap-2 shrink-0 pt-0.5">
                          <div class="flex items-center gap-1">
                            <input
                              type="number"
                              step="0.25"
                              min="0.1"
                              max="100"
                              value="${qPts}"
                              class="q-edit-points-input w-16 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-bold text-center outline-none focus:border-primary disabled:bg-slate-100 disabled:text-slate-400"
                              ${isLocked ? 'disabled' : ''}
                              data-q-id="${qId}"
                              data-idx="${idx}"
                              title="Điểm của câu hỏi"
                            />
                            <span class="text-[11px] text-slate-400">đ</span>
                          </div>

                          ${!isLocked ? `
                            <button
                              type="button"
                              class="btn-delete-q p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                              data-q-id="${qId}"
                              data-idx="${idx}"
                              title="Xóa câu hỏi khỏi đề thi"
                            >
                              <span class="material-symbols-outlined text-[18px]">delete</span>
                            </button>
                          ` : ''}
                        </div>

                      </div>
                    `;
                  }).join('')}
                </div>

              </div>
            </div>

          </div>

        </div>

        <!-- Add Question Modal -->
        <div id="modal-quick-add-question" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm hidden animate-fade-in">
          <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div class="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
              <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px] text-primary">add_circle</span>
                <span>Thêm câu hỏi mới vào đề thi</span>
              </h3>
              <button type="button" id="btn-close-add-q-modal" class="text-slate-400 hover:text-slate-700 dark:hover:text-white">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <form id="form-quick-add-question" class="p-5 overflow-y-auto space-y-3 text-xs">
              <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Loại câu hỏi</label>
                <select id="new-q-type" class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                  <option value="SINGLE_CHOICE">Trắc nghiệm 1 đáp án (SINGLE_CHOICE)</option>
                  <option value="MULTIPLE_CHOICE">Trắc nghiệm nhiều đáp án (MULTIPLE_CHOICE)</option>
                  <option value="TRUE_FALSE">Đúng / Sai (TRUE_FALSE)</option>
                  <option value="SHORT_ANSWER">Điền từ / Trả lời ngắn (SHORT_ANSWER)</option>
                  <option value="ESSAY">Tự luận (ESSAY)</option>
                </select>
              </div>

              <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Nội dung câu hỏi</label>
                <textarea id="new-q-stem" rows="3" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" placeholder="Nhập câu hỏi..."></textarea>
              </div>

              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Mức độ nhận thức</label>
                  <select id="new-q-bloom" class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                    <option value="UNDERSTAND">Thông hiểu</option>
                    <option value="REMEMBER">Nhận biết</option>
                    <option value="APPLY">Vận dụng</option>
                  </select>
                </div>
                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Điểm phân bổ</label>
                  <input type="number" id="new-q-points" step="0.25" min="0.1" value="1.0" class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
                </div>
              </div>

              <div id="new-q-choices-section" class="space-y-2">
                <label class="block font-semibold text-slate-700 dark:text-slate-300">Các lựa chọn (Tích chọn đáp án đúng):</label>
                <div class="flex items-center gap-2">
                  <input type="radio" name="new-q-correct" value="0" checked class="text-primary" />
                  <input type="text" class="new-q-choice-text flex-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" placeholder="Phương án A" />
                </div>
                <div class="flex items-center gap-2">
                  <input type="radio" name="new-q-correct" value="1" class="text-primary" />
                  <input type="text" class="new-q-choice-text flex-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" placeholder="Phương án B" />
                </div>
                <div class="flex items-center gap-2">
                  <input type="radio" name="new-q-correct" value="2" class="text-primary" />
                  <input type="text" class="new-q-choice-text flex-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" placeholder="Phương án C" />
                </div>
                <div class="flex items-center gap-2">
                  <input type="radio" name="new-q-correct" value="3" class="text-primary" />
                  <input type="text" class="new-q-choice-text flex-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" placeholder="Phương án D" />
                </div>
              </div>

              <div>
                <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Giải thích đáp án</label>
                <input type="text" id="new-q-explanation" class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" placeholder="Giải thích chi tiết..." />
              </div>

              <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-2">
                <button type="button" id="btn-cancel-add-q" class="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-bold text-xs">
                  Hủy
                </button>
                <button type="submit" id="btn-submit-add-q" class="px-5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-xs shadow-sm">
                  Thêm vào đề thi
                </button>
              </div>
            </form>
          </div>
        </div>
      `;

      // Event: Save Settings
      document.getElementById('btn-save-edit-settings')?.addEventListener('click', async () => {
        const title = document.getElementById('edit-exam-title')?.value?.trim();
        const duration = parseInt(document.getElementById('edit-exam-duration')?.value || 45, 10);
        const maxAttempts = parseInt(document.getElementById('edit-exam-attempts')?.value || 1, 10);
        const scoringPolicy = document.getElementById('edit-exam-scoring-policy')?.value || 'HIGHEST';
        const examLayout = document.getElementById('edit-exam-layout')?.value || 'STANDARD';
        const shuffle = Boolean(document.getElementById('edit-exam-shuffle')?.checked);
        const monitoring = Boolean(document.getElementById('edit-exam-monitoring')?.checked);
        const fullscreen = Boolean(document.getElementById('edit-exam-fullscreen')?.checked);

        if (!title) {
          UI.showToast('Tên đề thi không được để trống.', 'warning');
          return;
        }

        try {
          UI.showToast('Đang lưu thay đổi...', 'info');
          await ApiClient.updateAssessment(assessmentId, {
            title: title,
            duration_minutes: duration,
            max_attempts: maxAttempts,
            scoring_policy: scoringPolicy,
            exam_layout: examLayout,
            shuffle_questions: shuffle,
            monitoring_enabled: monitoring,
            request_fullscreen: fullscreen
          });
          assessment.title = title;
          assessment.duration_minutes = duration;
          assessment.max_attempts = maxAttempts;
          assessment.scoring_policy = scoringPolicy;
          assessment.exam_layout = examLayout;
          assessment.shuffle_questions = shuffle;
          assessment.monitoring_enabled = monitoring;
          assessment.request_fullscreen = fullscreen;
          UI.showToast('Đã lưu cấu hình đề thi thành công!', 'success');
        } catch (saveErr) {
          UI.showToast('Lỗi lưu cấu hình: ' + (saveErr.message || saveErr), 'error');
        }
      });

      // Event: Publish
      document.getElementById('btn-publish-from-edit')?.addEventListener('click', async () => {
        const conf = await UI.confirm('Xuất bản đề thi', 'Bạn có chắc chắn muốn xuất bản đề thi này để sinh viên có thể bắt đầu làm bài?', 'Xuất bản');
        if (!conf) return;
        try {
          UI.showToast('Đang xuất bản đề thi...', 'info');
          await ApiClient.publishAssessment(assessmentId);
          UI.showToast('Đã xuất bản đề thi thành công!', 'success');
          assessment.status = 'PUBLISHED';
          render();
        } catch (pubErr) {
          UI.showToast('Lỗi xuất bản: ' + (pubErr.message || pubErr), 'error');
        }
      });

      // Event: Open in Studio
      document.getElementById('btn-edit-in-studio')?.addEventListener('click', () => {
        const mapped = questions.map((q, idx) => ({
          number: idx + 1,
          question_id: q.question_id || q.id,
          stem: q.stem || q.content || q.question_text || '',
          question_text: q.stem || q.content || q.question_text || '',
          type: q.question_type || q.type || 'SINGLE_CHOICE',
          question_type: (
            (q.question_type === 'MULTIPLE_CHOICE' || q.type === 'MULTIPLE_CHOICE') ? 'TN nhiều đáp án'
            : (q.question_type === 'TRUE_FALSE' || q.type === 'TRUE_FALSE') ? 'Đúng / Sai'
            : (q.question_type === 'SHORT_ANSWER' || q.type === 'SHORT_ANSWER') ? 'Điền từ'
            : (q.question_type === 'ESSAY' || q.type === 'ESSAY') ? 'Tự luận'
            : 'Trắc nghiệm 1 đáp án'
          ),
          points: parseFloat(q.points) || 1.0,
          bloom_level: q.difficulty === 'REMEMBER' ? 'Nhận biết' : q.difficulty === 'APPLY' ? 'Vận dụng' : 'Thông hiểu',
          explanation: q.explanation || '',
          choices: (q.choices || []).map((c, cIdx) => ({
            label: c.label || String.fromCharCode(65 + cIdx),
            content: c.content || c.text || '',
            is_correct: Boolean(c.is_correct),
            position: c.position || cIdx + 1
          })),
          accepted_answers: (q.accepted_answers || []).map(a => typeof a === 'string' ? a : (a.answer_text || a.content || '')),
          resources: q.resources || [],
          image_asset_id: q.image_asset_id || (q.resources && q.resources[0] ? q.resources[0].asset_id : null)
        }));

        window.ExamStore.saveDraft({
          assessmentId: assessmentId,
          isEditingExisting: true,
          title: assessment.title || 'Đề thi',
          courseId: cId,
          courseTitle: assessment.course_title || '',
          questions: mapped,
          rawText: ExamParser.generateRawFromQuestions(mapped),
          config: {
            duration: assessment.duration_minutes || 45,
            maxAttempts: assessment.max_attempts || 1,
            shuffleQuestions: assessment.shuffle_questions !== false,
            scoringPolicy: assessment.scoring_policy || 'HIGHEST',
            examLayout: assessment.exam_layout || 'STANDARD',
            monitoringEnabled: Boolean(assessment.monitoring_enabled),
            requestFullscreen: Boolean(assessment.request_fullscreen),
            scoreScale: assessment.max_points || 40.0
          },
          sourceMethod: 'editor',
          methodSelected: true,
          matrixConfirmed: true
        });
        window.location.hash = '#/instructor/exams/editor';
      });

      // Events: Move Question Up/Down (Reordering)
      container.querySelectorAll('.btn-move-q-up').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx <= 0) return;
          const temp = questions[idx];
          questions[idx] = questions[idx - 1];
          questions[idx - 1] = temp;

          const orderedIds = questions.map(q => q.question_id || q.id);
          try {
            await ApiClient.reorderAssessmentQuestions(assessmentId, orderedIds);
            UI.showToast('Đã cập nhật thứ tự câu hỏi!', 'success');
            render();
          } catch (reorderErr) {
            UI.showToast('Lỗi sắp xếp câu hỏi: ' + (reorderErr.message || reorderErr), 'error');
            // Revert
            const rev = questions[idx];
            questions[idx] = questions[idx - 1];
            questions[idx - 1] = rev;
          }
        };
      });

      container.querySelectorAll('.btn-move-q-down').forEach(btn => {
        btn.onclick = async () => {
          const idx = parseInt(btn.dataset.idx, 10);
          if (idx >= questions.length - 1) return;
          const temp = questions[idx];
          questions[idx] = questions[idx + 1];
          questions[idx + 1] = temp;

          const orderedIds = questions.map(q => q.question_id || q.id);
          try {
            await ApiClient.reorderAssessmentQuestions(assessmentId, orderedIds);
            UI.showToast('Đã cập nhật thứ tự câu hỏi!', 'success');
            render();
          } catch (reorderErr) {
            UI.showToast('Lỗi sắp xếp câu hỏi: ' + (reorderErr.message || reorderErr), 'error');
            // Revert
            const rev = questions[idx];
            questions[idx] = questions[idx + 1];
            questions[idx + 1] = rev;
          }
        };
      });

      // Event: Edit Points
      container.querySelectorAll('.q-edit-points-input').forEach(input => {
        input.onchange = async () => {
          const qId = input.dataset.qId;
          const idx = parseInt(input.dataset.idx, 10);
          const val = parseFloat(input.value);
          if (isNaN(val) || val <= 0) {
            UI.showToast('Điểm phân bổ phải lớn hơn 0.', 'warning');
            input.value = questions[idx]?.points || 1.0;
            return;
          }
          try {
            await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/${qId}/edit`, {
              method: 'POST',
              body: { points: val }
            });
            questions[idx].points = val;
            UI.showToast('Đã cập nhật điểm câu hỏi!', 'success');
          } catch (ptErr) {
            UI.showToast('Lỗi đổi điểm: ' + (ptErr.message || ptErr), 'error');
            input.value = questions[idx]?.points || 1.0;
          }
        };
      });

      // Event: Delete Question
      container.querySelectorAll('.btn-delete-q').forEach(btn => {
        btn.onclick = async () => {
          const qId = btn.dataset.qId;
          const idx = parseInt(btn.dataset.idx, 10);
          const conf = await UI.confirm('Gỡ câu hỏi', `Bạn có chắc muốn xóa câu hỏi #${idx + 1} khỏi đề thi này?`, 'Gỡ câu hỏi');
          if (!conf) return;
          try {
            await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/${qId}`, {
              method: 'DELETE'
            });
            questions.splice(idx, 1);
            UI.showToast('Đã gỡ câu hỏi khỏi đề thi!', 'success');
            render();
          } catch (delErr) {
            UI.showToast('Lỗi gỡ câu hỏi: ' + (delErr.message || delErr), 'error');
          }
        };
      });

      // Modal Quick Add Question
      const addModal = document.getElementById('modal-quick-add-question');
      document.getElementById('btn-open-add-question-modal')?.addEventListener('click', () => {
        addModal?.classList.remove('hidden');
      });
      document.getElementById('btn-close-add-q-modal')?.addEventListener('click', () => {
        addModal?.classList.add('hidden');
      });
      document.getElementById('btn-cancel-add-q')?.addEventListener('click', () => {
        addModal?.classList.add('hidden');
      });

      const qTypeSelect = document.getElementById('new-q-type');
      const choicesSection = document.getElementById('new-q-choices-section');
      qTypeSelect?.addEventListener('change', () => {
        const val = qTypeSelect.value;
        if (val === 'SHORT_ANSWER' || val === 'ESSAY') {
          if (choicesSection) choicesSection.classList.add('hidden');
        } else {
          if (choicesSection) choicesSection.classList.remove('hidden');
        }
      });

      document.getElementById('form-quick-add-question')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const stem = document.getElementById('new-q-stem')?.value?.trim();
        if (!stem) {
          UI.showToast('Nội dung câu hỏi không được để trống.', 'warning');
          return;
        }
        const qType = qTypeSelect?.value || 'SINGLE_CHOICE';
        const bloom = document.getElementById('new-q-bloom')?.value || 'UNDERSTAND';
        const points = parseFloat(document.getElementById('new-q-points')?.value || 1.0);
        const explanation = document.getElementById('new-q-explanation')?.value?.trim();

        const payload = {
          question_type: qType,
          content: stem,
          difficulty: bloom,
          points: points,
          explanation: explanation
        };

        if (qType === 'SINGLE_CHOICE' || qType === 'MULTIPLE_CHOICE' || qType === 'TRUE_FALSE') {
          const choiceInputs = document.querySelectorAll('.new-q-choice-text');
          const correctIdx = document.querySelector('input[name="new-q-correct"]:checked')?.value || '0';
          const choices = [];
          choiceInputs.forEach((inp, i) => {
            const txt = inp.value.trim();
            if (txt) {
              choices.push({
                content: txt,
                is_correct: (String(i) === String(correctIdx)),
                position: i + 1
              });
            }
          });
          if (choices.length < 2 && qType !== 'TRUE_FALSE') {
            UI.showToast('Vui lòng nhập tối thiểu 2 phương án lựa chọn.', 'warning');
            return;
          }
          payload.choices = choices;
        } else if (qType === 'SHORT_ANSWER') {
          payload.accepted_answers = ['Đáp án'];
        }

        try {
          UI.showToast('Đang thêm câu hỏi vào đề...', 'info');
          const res = await ApiClient.createAssessmentQuestion(assessmentId, payload);
          addModal?.classList.add('hidden');
          UI.showToast('Đã thêm câu hỏi vào đề thi thành công!', 'success');
          if (res?.question) {
            questions.push({
              question_id: res.question.question_id || res.question.id,
              stem: res.question.content || stem,
              question_type: qType,
              difficulty: bloom,
              points: points,
              explanation: explanation,
              choices: payload.choices || []
            });
            render();
          } else {
            // Reload detail
            const refreshed = await ApiClient.getAssessmentDetail(assessmentId);
            questions = refreshed.question_assignments || refreshed.questions || [];
            render();
          }
        } catch (createErr) {
          UI.showToast('Lỗi tạo câu hỏi: ' + (createErr.message || createErr), 'error');
        }
      });
    };

    render();
  };

  // =========================================================================
  // 9. Backwards compatibility alias
  // =========================================================================
  InstructorView.renderExams = function (container) {
    return InstructorView.renderExamsHub(container);
  };

  window.InstructorView = InstructorView;
})();
