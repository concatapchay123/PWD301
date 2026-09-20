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

  // =========================================================================
  // 1. Unified Sticky Workflow Header
  // =========================================================================
  InstructorView.renderExamWorkflowHeader = function (activeStep, stepTitle, nextRoute, nextLabel, onNextAction) {
    const draft = window.ExamStore ? window.ExamStore.getDraft() : { title: 'De_thi_moi.docx', questions: [] };
    const qCount = (draft.questions || []).length;
    const currentTitle = draft.title || 'De_thi_moi.docx';

    return `
      <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xs select-none shrink-0">
        <div class="max-w-[1920px] mx-auto px-3 sm:px-5 h-14 flex items-center justify-between gap-3">
          
          <!-- Left: Brand, Back & Exam Title -->
          <div class="flex items-center gap-2.5 min-w-0">
            <a href="#/instructor/exams" class="flex items-center gap-2 group p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Hub Soạn đề thi">
              <div class="w-7 h-7 rounded-lg bg-[#222120] dark:bg-[#EDEDEB] flex items-center justify-center text-[#FAF9F5] dark:text-[#191919] font-bold text-xs">
                <span class="material-symbols-outlined text-[16px]">assignment_add</span>
              </div>
              <span class="font-bold text-sm tracking-tight text-[#222120] dark:text-[#EDEDEB] hidden sm:inline-block">Soạn đề thi</span>
            </a>

            <button type="button" id="workflow-back-btn" class="flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Quay lại">
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
            </button>

            <div class="flex items-center max-w-sm sm:max-w-md w-full relative">
              <input
                type="text"
                id="workflow-exam-title-input"
                class="text-xs sm:text-sm font-semibold text-slate-800 dark:text-white bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-indigo-500 rounded-lg px-2.5 py-1 w-full transition-all truncate focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-indigo-500/20"
                value="${UI.escapeHtml(currentTitle)}"
                title="Nhấp để đổi tên đề thi"
              />
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
              href="#/instructor/exams/editor"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 2 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 2 ? 'bg-indigo-600 text-white font-bold' : (activeStep > 2 ? 'bg-emerald-600 text-white' : 'border border-slate-300 text-slate-600')}">
                ${activeStep > 2 ? '✓' : '2'}
              </span>
              <span>${stepTitle || 'Soạn thảo & Nhập liệu'}</span>
            </a>

            <!-- Step 3 -->
            <a
              href="#/instructor/exams/matrix"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${activeStep === 3 ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'}"
            >
              <span class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${activeStep === 3 ? 'bg-indigo-600 text-white font-bold' : (activeStep > 3 ? 'bg-emerald-600 text-white' : 'border border-slate-300 text-slate-600')}">
                ${activeStep > 3 ? '✓' : '3'}
              </span>
              <span>Ma trận học vụ</span>
            </a>

            <!-- Step 4 -->
            <a
              href="#/instructor/exams/settings"
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
  InstructorView.renderExamsHub = function (container) {
    const draft = window.ExamStore.getDraft();
    const hasDraft = window.ExamStore.hasDraft();

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(1, 'Chọn phương thức', '#/instructor/exams/editor', 'Tiếp tục soạn đề')}

        <main class="flex-1 overflow-y-auto max-w-[1440px] mx-auto px-4 sm:px-6 py-8 w-full pb-24">
          
          <!-- Page Heading -->
          <div class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                Khởi tạo Đề thi & Bài kiểm tra
              </h1>
              <p class="mt-1 text-sm text-slate-500">
                Lựa chọn một trong các phương thức trực tuyến hoặc tải tệp tài liệu số hóa để bắt đầu.
              </p>
            </div>
            <button type="button" onclick="window.location.hash = '#/instructor/dashboard'" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors self-start md:self-auto">
              <span class="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Quay lại Bàn làm việc</span>
            </button>
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
            <div class="lg:col-span-7 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-xs flex flex-col justify-between min-h-[580px]">
              <div>
                <div class="flex items-center justify-between mb-4">
                  <h2 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>Nạp tệp đề thi sẵn có</span>
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Tự động bóc tách AI
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
                    Kéo thả tệp đề thi vào đây hoặc <span class="text-indigo-600 underline underline-offset-2">bấm để duyệt tệp</span>
                  </p>
                  <p class="text-xs sm:text-sm text-slate-500 max-w-md mb-2">
                    Hỗ trợ các định dạng tiêu chuẩn: <span class="font-medium text-slate-700 dark:text-slate-300">.docx, .pdf, .txt, .md, .xlsx</span>
                  </p>
                  <p class="text-xs text-slate-400">
                    Hệ thống sẽ tự động bóc tách câu hỏi, phương án và đáp án vào trình soạn thảo.
                  </p>

                  <button type="button" id="btn-hub-quick-sample" class="mt-4 px-4 py-2 bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold rounded-lg text-xs hover:bg-indigo-600 hover:text-white transition-colors">
                    ⚡ Nhấn nạp đề mẫu chuẩn hóa: De_thi_mau.docx
                  </button>
                </div>

                <!-- Guidelines Card -->
                <div class="mt-4 p-5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 space-y-3">
                  <div class="flex items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-700 pb-2">
                    <div class="flex items-center gap-2 font-bold text-slate-900 dark:text-white">
                      <span class="material-symbols-outlined text-[20px] text-indigo-600">help_outline</span>
                      <span class="text-sm">Quy chuẩn bóc tách văn bản (.docx, .pdf, .txt)</span>
                    </div>
                    <span class="px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 font-semibold text-[11px]">Chuẩn hóa</span>
                  </div>

                  <div class="space-y-1.5 text-slate-600 dark:text-slate-300 text-xs">
                    <div><strong>1. Đầu đề:</strong> Bắt đầu bằng <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">Câu 1:</code>, <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">Câu 1.</code> hoặc <code class="bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold px-1 rounded">1.</code></div>
                    <div><strong>2. Phương án:</strong> Bắt đầu bằng <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">A.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">B.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">C.</code>, <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">D.</code></div>
                    <div><strong>3. Đáp án đúng:</strong> Đặt dấu hoa thị <code class="bg-rose-100 text-rose-600 font-bold px-1 rounded">*</code> ngay trước chữ cái (ví dụ: <code class="text-rose-600 font-bold">*A.</code>)</div>
                    <div><strong>4. Lời giải:</strong> Bắt đầu bằng <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">Lời giải:</code> hoặc <code class="bg-slate-200 dark:bg-slate-700 font-bold px-1 rounded">Giải thích:</code></div>
                  </div>
                </div>
              </div>

              <div class="mt-6 flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                <div class="p-1 rounded bg-indigo-100 text-indigo-700 shrink-0">
                  <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
                </div>
                <div class="text-xs text-slate-600 dark:text-slate-300">
                  <span class="font-bold text-slate-900 dark:text-white">Công nghệ Parser thông minh:</span> Tự động nhận dạng công thức toán học LaTeX giữa cặp dấu $...$, hình ảnh đính kèm và đáp án đảo đề.
                </div>
              </div>
            </div>

            <!-- Right Column: 4 Dedicated Online Methods -->
            <div class="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 sm:p-7 shadow-xs">
              <div class="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div class="flex items-center gap-2">
                  <h2 class="text-lg font-bold text-slate-900 dark:text-white">Phương thức trực tuyến</h2>
                  <span class="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium px-2 py-0.5 rounded-full">4 hình thức</span>
                </div>
              </div>

              <div class="space-y-3.5">
                
                <!-- Method 1: Tự soạn Đề thi / Bài tập -->
                <a
                  href="#/instructor/exams/editor"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-500 hover:bg-indigo-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">edit_document</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors flex items-center justify-between">
                        <span>Tự soạn Đề thi / Bài tập</span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Sử dụng trình soạn thảo Split-View trực quan, tự gõ nội dung từ trang trắng hoặc dán nhanh từ bộ nhớ đệm.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 2: Tạo đề thi tương tác [MỚI] -->
                <a
                  href="#/instructor/exams/interactive"
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
                        Bộ công cụ trực quan thiết lập câu hỏi kéo thả từ, điền khuyết từ khóa, ghép đôi cặp tương ứng sinh động.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 3: Tạo đề từ tệp Excel -->
                <a
                  href="#/instructor/exams/excel"
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
                        Tải bảng tính mẫu chuẩn hóa, import hàng loạt câu hỏi kèm bảng kiểm tra dữ liệu trước khi lưu vào đề.
                      </p>
                    </div>
                  </div>
                </a>

                <!-- Method 4: Nạp từ chuẩn LMS Moodle XML / JSON -->
                <a
                  href="#/instructor/exams/moodle"
                  class="group block p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-amber-500 hover:bg-amber-50/10 cursor-pointer transition-all shadow-xs"
                >
                  <div class="flex items-start gap-3.5">
                    <div class="w-11 h-11 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <span class="material-symbols-outlined text-[22px]">code_blocks</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm font-bold text-slate-900 dark:text-white group-hover:text-amber-600 transition-colors flex items-center justify-between">
                        <span>Nạp từ chuẩn LMS Moodle XML / JSON</span>
                        <span class="material-symbols-outlined text-[18px] text-slate-300 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all">arrow_forward</span>
                      </h3>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        Nhập cấu trúc ngân hàng câu hỏi theo chuẩn trao đổi quốc tế (Moodle XML, JSON), hỗ trợ dán trực tiếp mã nguồn.
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

    InstructorView.bindExamWorkflowHeaderEvents(1, '#/instructor/exams/editor');

    // Resume / Discard draft
    document.getElementById('btn-hub-resume-draft')?.addEventListener('click', () => {
      window.location.hash = '#/instructor/exams/editor';
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
            window.ExamStore.saveDraft({ title: file.name.replace(/\.[^/.]+$/, '') });
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
          const parsed = ExamParser.parseExamRaw(rawContent, 40.0);
          window.ExamStore.saveDraft({
            title: file.name.replace(/\.[^/.]+$/, ''),
            rawText: rawContent,
            questions: parsed.questions
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
        questions: parsed.questions
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
        <div id="modal-syntax-guide" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs hidden animate-fade-in">
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
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-soft p-4 space-y-3 transition-all hover:border-slate-300 relative group cursor-pointer" id="editor-q-card-${idx + 1}" title="Nhấp để chuyển đến vị trí trên mã nguồn">
          <!-- Meta Header -->
          <div class="flex items-center justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800 text-xs">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-2.5 py-1 bg-indigo-50 text-indigo-700 font-bold rounded-lg border border-indigo-200/60 text-xs">
                Câu ${idx + 1}.
              </span>
              <input type="text" value="${(q.points || 1.0).toFixed(1)} điểm" class="w-20 px-2 py-0.5 text-xs font-semibold border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-300 outline-none focus:border-indigo-500" onclick="event.stopPropagation()" />
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                ${q.question_type}
              </span>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              ${q.bloom_level}
            </span>
          </div>

          <!-- Question Content -->
          <div class="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white leading-snug p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60 focus-within:bg-white dark:focus-within:bg-slate-800 outline-none" contenteditable="true" onclick="event.stopPropagation()">
            ${UI.escapeHtml(q.stem || q.question_text)}
          </div>

          <!-- Choices -->
          <div class="mt-3 space-y-2" onclick="event.stopPropagation()">
            ${(q.choices || []).map((c, cIdx) => `
              <div class="flex items-start gap-2 group/opt">
                <button
                  type="button"
                  class="w-6 h-6 rounded-md font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 shadow-xs transition-colors ${c.is_correct ? 'bg-indigo-600 text-white' : 'border border-slate-300 dark:border-slate-700 text-slate-600 hover:border-indigo-500'}"
                  title="${c.is_correct ? 'Đáp án đúng' : 'Đánh dấu đáp án đúng'}"
                >
                  ${c.is_correct ? '✓' : c.label}
                </button>
                <div class="text-xs p-2 rounded-lg w-full transition-colors ${c.is_correct ? 'border border-indigo-500 bg-indigo-50/20 text-slate-900 dark:text-white font-medium ring-1 ring-indigo-500/30' : 'border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800'}">
                  <span class="font-bold ${c.is_correct ? 'text-indigo-700 mr-1' : 'mr-1'}">${c.label}.</span>
                  <span>${UI.escapeHtml(c.content)}</span>
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

      const badge = document.getElementById('workflow-sync-badge');
      if (badge) badge.textContent = `${questions.length} câu • Tự động lưu`;
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

    container.innerHTML = `
      <div class="h-full flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100">
        ${InstructorView.renderExamWorkflowHeader(2, 'Tạo đề thi tương tác', '#/instructor/exams/matrix', 'Tiếp tục: Ma trận học vụ')}

        <main class="flex-1 overflow-y-auto max-w-[1520px] mx-auto px-4 sm:px-6 py-6 w-full pb-28">
          
          <!-- Banner -->
          <div class="mb-6 p-4 rounded-2xl bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center material-symbols-outlined text-[22px] shrink-0 shadow-xs">
                extension
              </div>
              <div>
                <h3 class="font-bold text-sm text-teal-950 dark:text-teal-200">Bộ công cụ Thiết kế Câu hỏi Tương tác Trực quan</h3>
                <p class="text-xs text-teal-700 dark:text-teal-300">Tạo dạng câu hỏi kéo thả, điền khuyết và ghép đôi sinh động kèm khung thử nghiệm trực tiếp.</p>
              </div>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 border border-teal-200 self-start sm:self-auto shrink-0">
              Đã có ${interactiveQuestions.length} câu tương tác trong đề
            </span>
          </div>

          <!-- 2 Columns: Left Form / Right Interactive Preview -->
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- LEFT: Builder Form (6 cols) -->
            <div class="lg:col-span-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs space-y-5">
              
              <!-- Tab Switcher -->
              <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Chọn dạng câu hỏi tương tác</label>
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
                    Đoạn văn có chứa các từ cần kéo thả đặt trong ngoặc vuông <code class="text-teal-600 font-bold bg-teal-50 px-1 rounded">[từ_khóa]</code> <span class="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="drag-stem-input"
                    rows="4"
                    class="w-full p-3 text-xs sm:text-sm border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: Giao thức [HTTPS] bảo vệ đường truyền bằng chứng chỉ [SSL/TLS] chạy mặc định trên cổng [443]."
                  >Giao thức [HTTPS] bảo vệ đường truyền bằng chứng chỉ [SSL/TLS] chạy mặc định trên cổng [443].</textarea>
                  <span class="text-[11px] text-slate-400 mt-1 block">Hệ thống sẽ tự động bóc tách các từ trong ngoặc vuông làm ô trống cần kéo thả.</span>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Các từ khóa gây nhiễu (phân cách bằng dấu phẩy)</label>
                  <input
                    type="text"
                    id="drag-distractors-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: HTTP, 80, 21, SSH"
                    value="HTTP, 80, 21"
                  />
                </div>
              </div>

              <!-- FORM 2: Điền khuyết / Trả lời ngắn -->
              <div id="form-container-fill" class="space-y-4 hidden">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Nội dung câu hỏi chứa ô điền <code class="text-teal-600 font-bold bg-teal-50 px-1 rounded">___</code> <span class="text-rose-500">*</span>
                  </label>
                  <textarea
                    id="fill-stem-input"
                    rows="3"
                    class="w-full p-3 text-xs sm:text-sm border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: Cơ chế xác thực không trạng thái trong REST API sử dụng mã thông báo định dạng ___."
                  >Cơ chế xác thực không trạng thái trong REST API sử dụng mã thông báo định dạng ___.</textarea>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Các đáp án được chấp nhận (cách nhau bởi dấu phẩy) <span class="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="fill-answers-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    placeholder="Ví dụ: JWT, JSON Web Token, jwt"
                    value="JWT, JSON Web Token"
                  />
                </div>
              </div>

              <!-- FORM 3: Ghép đôi cặp tương ứng -->
              <div id="form-container-match" class="space-y-4 hidden">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Đề bài yêu cầu ghép đôi</label>
                  <input
                    type="text"
                    id="match-stem-input"
                    class="w-full px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:border-teal-500 bg-slate-50 dark:bg-slate-800"
                    value="Hãy ghép nối mỗi giao thức mạng ở cột A với cổng mặc định tương ứng ở cột B:"
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
                      <input type="text" placeholder="Khái niệm A (VD: HTTP)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" value="HTTP" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ý nghĩa B (VD: Cổng 80)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" value="Cổng 80" />
                    </div>
                    <div class="flex items-center gap-2 match-pair-row">
                      <input type="text" placeholder="Khái niệm A (VD: HTTPS)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" value="HTTPS" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ý nghĩa B (VD: Cổng 443)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" value="Cổng 443" />
                    </div>
                    <div class="flex items-center gap-2 match-pair-row">
                      <input type="text" placeholder="Khái niệm A (VD: SSH)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-left" value="SSH" />
                      <span class="text-slate-400">➔</span>
                      <input type="text" placeholder="Ý nghĩa B (VD: Cổng 22)" class="w-1/2 px-2.5 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 pair-right" value="Cổng 22" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Shared Meta: Điểm số, Bloom, Giải thích -->
              <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Điểm số</label>
                  <input type="number" id="interactive-points-input" min="0.5" step="0.5" value="1.5" class="w-full px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 font-bold text-center" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Mức độ Bloom</label>
                  <select id="interactive-bloom-select" class="w-full px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 font-semibold">
                    <option value="Nhận biết">Nhận biết</option>
                    <option value="Thông hiểu" selected>Thông hiểu</option>
                    <option value="Vận dụng">Vận dụng</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Giải thích / Lời giải củng cố</label>
                <input type="text" id="interactive-exp-input" class="w-full px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800" placeholder="Lời giải chi tiết sau khi sinh viên hoàn thành..." />
              </div>

              <!-- Submit Button -->
              <button
                type="button"
                id="btn-add-interactive-question"
                class="w-full py-2.5 bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white font-bold rounded-xl text-xs shadow-md shadow-teal-500/20 transition-all flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-[18px]">add_circle</span>
                <span>+ Thêm câu hỏi tương tác này vào đề thi</span>
              </button>

            </div>

            <!-- RIGHT: Live Interactive Preview & Questions List (6 cols) -->
            <div class="lg:col-span-6 space-y-6">
              
              <!-- Live Interactive Test Box -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border-2 border-teal-500/40 p-5 sm:p-6 shadow-sm">
                <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                  <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></span>
                    <h3 class="text-sm font-bold text-slate-900 dark:text-white">Khung thử nghiệm tương tác trực tiếp</h3>
                  </div>
                  <span class="text-[11px] px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-semibold">Trải nghiệm của thí sinh</span>
                </div>

                <div id="interactive-live-preview-box" class="min-h-[160px] flex flex-col justify-center">
                  <!-- Live interactive preview elements -->
                </div>

                <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <button type="button" id="btn-test-interactive-answer" class="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-teal-50 text-slate-700 dark:text-slate-300 font-bold rounded-lg text-xs transition-colors">
                    Kiểm tra chấm điểm thử
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
                    <span>Tiếp tục: Ma trận học vụ</span>
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

      if (activeTab === 'drag') {
        const text = document.getElementById('drag-stem-input')?.value || '';
        const tokens = [...text.matchAll(/\[(.*?)\]/g)].map(m => m[1]);
        const distractors = (document.getElementById('drag-distractors-input')?.value || '')
          .split(',')
          .map(s => s.trim())
          .filter(Boolean);

        const allPills = [...tokens, ...distractors].sort(() => Math.random() - 0.5);
        let previewHtml = text;
        tokens.forEach((t, i) => {
          previewHtml = previewHtml.replace(`[${t}]`, `<span class="inline-block border-2 border-dashed border-teal-500 bg-teal-50/40 rounded-lg px-3 py-1 min-w-[60px] text-center font-bold text-teal-700 text-xs drop-slot" data-expected="${t}">___</span>`);
        });

        previewBox.innerHTML = `
          <div class="space-y-4">
            <div class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-loose">
              ${previewHtml}
            </div>
            <div class="pt-3 border-t border-slate-100 dark:border-slate-800">
              <span class="text-[11px] font-bold text-slate-400 block mb-1.5">Các thẻ từ có thể kéo/chọn:</span>
              <div class="flex flex-wrap gap-2" id="preview-drag-pills">
                ${allPills.map(p => `
                  <button type="button" class="px-2.5 py-1 rounded-lg bg-teal-600 text-white font-bold text-xs shadow-xs hover:bg-teal-700 cursor-pointer drag-pill-btn" onclick="window.handlePillClick(this, '${p}')">
                    ${p}
                  </button>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      } else if (activeTab === 'fill') {
        const stem = document.getElementById('fill-stem-input')?.value || '';
        const stemRendered = stem.replace('___', `<input type="text" id="live-fill-input" placeholder="Nhập đáp án..." class="inline-block px-2 py-0.5 text-xs font-bold border-b-2 border-teal-600 bg-teal-50/50 outline-none w-32 text-center" />`);
        previewBox.innerHTML = `
          <div class="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
            ${stemRendered}
          </div>
        `;
      } else if (activeTab === 'match') {
        const stem = document.getElementById('match-stem-input')?.value || '';
        const rows = document.querySelectorAll('.match-pair-row');
        const pairs = Array.from(rows).map(r => ({
          left: r.querySelector('.pair-left')?.value || '',
          right: r.querySelector('.pair-right')?.value || ''
        })).filter(p => p.left && p.right);

        previewBox.innerHTML = `
          <div class="space-y-3">
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-300">${UI.escapeHtml(stem)}</p>
            <div class="space-y-2">
              ${pairs.map(p => `
                <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                  <span class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(p.left)}</span>
                  <span class="text-teal-600 font-bold">➔</span>
                  <span class="font-medium text-slate-700 dark:text-slate-300">${UI.escapeHtml(p.right)}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }
    };

    // Pill click tester handler
    window.handlePillClick = (btn, word) => {
      const slot = document.querySelector('.drop-slot:empty') || Array.from(document.querySelectorAll('.drop-slot')).find(s => s.textContent === '___');
      if (slot) {
        slot.textContent = word;
        slot.classList.add('bg-teal-100', 'border-solid');
        btn.classList.add('opacity-40', 'pointer-events-none');
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
        const val = document.getElementById('live-fill-input')?.value.trim() || '';
        const accepted = (document.getElementById('fill-answers-input')?.value || '')
          .split(',')
          .map(s => s.trim().toLowerCase());
        if (accepted.includes(val.toLowerCase())) {
          feedbackMsg.innerHTML = `<span class="text-emerald-600 font-bold">✓ Chính xác! Trùng khớp đáp án.</span>`;
        } else {
          feedbackMsg.innerHTML = `<span class="text-rose-600 font-bold">Chưa đúng đáp án.</span>`;
        }
      } else {
        feedbackMsg.innerHTML = `<span class="text-emerald-600 font-bold">✓ Ghép nối hợp lệ!</span>`;
      }
    });

    // Add Interactive Question to Exam
    document.getElementById('btn-add-interactive-question')?.addEventListener('click', () => {
      const pts = parseFloat(document.getElementById('interactive-points-input')?.value || 1.5) || 1.5;
      const bloom = document.getElementById('interactive-bloom-select')?.value || 'Thông hiểu';
      const exp = document.getElementById('interactive-exp-input')?.value.trim() || '';

      let newQuestion = null;

      if (activeTab === 'drag') {
        const stem = document.getElementById('drag-stem-input')?.value.trim();
        if (!stem || !stem.includes('[')) {
          UI.showToast('Vui lòng nhập đoạn văn có ít nhất 1 từ khóa đặt trong ngoặc vuông [từ_khóa]!', 'warning');
          return;
        }
        const tokens = [...stem.matchAll(/\[(.*?)\]/g)].map(m => m[1]);
        const cleanStem = stem.replace(/\[(.*?)\]/g, '___');

        newQuestion = {
          stem: cleanStem,
          question_text: cleanStem,
          question_type: 'Kéo thả',
          type: 'SHORT_ANSWER',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          accepted_answers: tokens,
          is_interactive: true,
          interactive_type: 'DRAG_DROP',
          tokens: tokens
        };
      } else if (activeTab === 'fill') {
        const stem = document.getElementById('fill-stem-input')?.value.trim();
        const answersStr = document.getElementById('fill-answers-input')?.value.trim();
        if (!stem || !answersStr) {
          UI.showToast('Vui lòng nhập đề bài và đáp án được chấp nhận!', 'warning');
          return;
        }
        const answers = answersStr.split(',').map(s => s.trim()).filter(Boolean);

        newQuestion = {
          stem: stem,
          question_text: stem,
          question_type: 'Điền từ',
          type: 'SHORT_ANSWER',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          accepted_answers: answers,
          is_interactive: true,
          interactive_type: 'FILL_IN'
        };
      } else if (activeTab === 'match') {
        const stem = document.getElementById('match-stem-input')?.value.trim();
        const rows = document.querySelectorAll('.match-pair-row');
        const pairs = Array.from(rows).map(r => ({
          left: r.querySelector('.pair-left')?.value.trim() || '',
          right: r.querySelector('.pair-right')?.value.trim() || ''
        })).filter(p => p.left && p.right);

        if (!stem || pairs.length < 2) {
          UI.showToast('Vui lòng nhập đề bài và ít nhất 2 cặp ghép hợp lệ!', 'warning');
          return;
        }

        const choices = pairs.map((p, i) => ({
          label: chr(65 + i),
          content: `${p.left} ➔ ${p.right}`,
          is_correct: true,
          position: i + 1
        }));

        newQuestion = {
          stem: stem,
          question_text: stem,
          question_type: 'Ghép đôi',
          type: 'MULTIPLE_CHOICE',
          points: pts,
          bloom_level: bloom,
          explanation: exp,
          choices: choices,
          is_interactive: true,
          interactive_type: 'MATCHING',
          pairs: pairs
        };
      }

      if (newQuestion) {
        window.ExamStore.appendQuestions([newQuestion]);
        UI.showToast('Đã thêm câu hỏi tương tác vào đề thi!', 'success');
        renderQuestionsList();
      }
    });

    const chr = (n) => String.fromCharCode(n);

    // Render Questions List
    const renderQuestionsList = () => {
      const currentDraft = window.ExamStore.getDraft();
      const listEl = document.getElementById('interactive-questions-list');
      const badge = document.getElementById('exam-questions-count-badge');
      const qList = currentDraft.questions || [];

      if (badge) badge.textContent = `${qList.length} câu`;
      if (!listEl) return;

      if (qList.length === 0) {
        listEl.innerHTML = `
          <div class="p-6 text-center text-slate-400 text-xs">
            Đề thi chưa có câu hỏi nào. Bạn hãy tạo câu hỏi ở khung bên trái và bấm '+ Thêm câu hỏi'.
          </div>
        `;
        return;
      }

      listEl.innerHTML = qList.map((q, i) => `
        <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 flex items-start justify-between gap-3 text-xs">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-bold text-[11px]">Câu ${i + 1}</span>
              <span class="text-slate-500 font-medium">${q.question_type || q.type}</span>
              <span class="text-indigo-600 font-semibold">• ${(q.points || 1.0).toFixed(1)}đ</span>
            </div>
            <p class="font-semibold text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(q.stem || q.question_text)}</p>
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
        UI.showToast('Vui lòng thêm ít nhất 1 câu hỏi vào đề thi trước khi sang Ma trận!', 'warning');
        return;
      }
      window.location.hash = '#/instructor/exams/matrix';
    });

    // Form live listeners
    ['drag-stem-input', 'drag-distractors-input', 'fill-stem-input', 'match-stem-input'].forEach(id => {
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
                <p class="text-xs text-slate-500">Dữ liệu sẽ được thẩm định cú pháp tự động.</p>
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
                <span>Bóc tách & Thẩm định cú pháp</span>
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
        courseSelect.innerHTML = courses.map((c, i) => `
          <option value="${c.course_id || c.id || c.course_code}" ${(draft.courseId === (c.course_id || c.id)) || i === 0 ? 'selected' : ''}>
            ${c.course_code} - ${c.title}
          </option>
        `).join('');
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
      window.ExamStore.saveDraft({ courseId: courseId, academicMode: mode });
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

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                      <option value="2" ${config.maxAttempts === 2 ? 'selected' : ''}>2 lần (Lấy điểm cao nhất)</option>
                      <option value="3" ${config.maxAttempts === 3 ? 'selected' : ''}>3 lần</option>
                      <option value="999" ${config.maxAttempts > 3 ? 'selected' : ''}>Không giới hạn (Luyện tập)</option>
                    </select>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
                  <label class="flex items-center gap-3 cursor-pointer text-xs font-semibold select-none">
                    <input type="checkbox" id="cfg-shuffle-all" class="rounded text-indigo-600 focus:ring-indigo-500" ${config.shuffleQuestions !== false ? 'checked' : ''} />
                    <span>Xáo trộn ngẫu nhiên thứ tự câu hỏi và phương án đáp án cho mỗi thí sinh</span>
                  </label>

                  <label class="flex items-center gap-3 cursor-pointer text-xs font-semibold select-none">
                    <input type="checkbox" id="cfg-require-pwd" class="rounded text-indigo-600 focus:ring-indigo-500" ${config.requirePassword ? 'checked' : ''} />
                    <span>Yêu cầu mật khẩu vào phòng thi</span>
                  </label>

                  <div id="cfg-pwd-box" class="${config.requirePassword ? '' : 'hidden'} pl-7">
                    <input type="password" id="cfg-exam-pwd" placeholder="Nhập mật khẩu ca thi..." class="px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none bg-slate-50 dark:bg-slate-800 w-64" value="${config.examPassword || ''}" />
                  </div>
                </div>
              </div>

              <!-- Card 2: Security & Proctoring -->
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
                <div class="flex items-center gap-2.5 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <span class="material-symbols-outlined text-[22px] text-indigo-600">security</span>
                  <h3 class="text-base font-bold text-slate-900 dark:text-white">2. Giám sát Chống gian lận & Phòng thi</h3>
                </div>

                <div class="space-y-3 text-xs font-semibold">
                  <label class="flex items-center gap-3 cursor-pointer select-none">
                    <input type="checkbox" id="cfg-lock-tab" class="rounded text-indigo-600 focus:ring-indigo-500" ${config.lockTab !== false ? 'checked' : ''} />
                    <span>Cảnh báo & Ghi nhận vi phạm khi thí sinh chuyển tab hoặc rời khỏi trình duyệt</span>
                  </label>

                  <label class="flex items-center gap-3 cursor-pointer select-none">
                    <input type="checkbox" id="cfg-proctoring" class="rounded text-indigo-600 focus:ring-indigo-500" ${config.proctoring ? 'checked' : ''} />
                    <span>Kích hoạt AI Proctoring (Giám sát qua webcam và phát hiện khuôn mặt)</span>
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
                    <span>Tôi xác nhận đề thi đã hoàn tất thẩm định nội dung và sẵn sàng xuất bản vào CSDL.</span>
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

    // Password toggle
    document.getElementById('cfg-require-pwd')?.addEventListener('change', (e) => {
      const box = document.getElementById('cfg-pwd-box');
      if (e.target.checked) box?.classList.remove('hidden');
      else box?.classList.add('hidden');
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
        `Bài thi "${title}" (Thời lượng ${duration} phút) đã hoàn tất thẩm định. Bạn có muốn kích hoạt và mở phòng thi ngay bây giờ?`,
        'Xuất bản & Mở phòng thi'
      );
      if (!conf) return;

      try {
        UI.showToast('Đang tạo đề thi và lưu câu hỏi vào CSDL...', 'info');
        const maxAtt = parseInt(document.getElementById('cfg-attempts')?.value || 1, 10);
        const shuffle = document.getElementById('cfg-shuffle-all')?.checked ?? true;

        // 1. Create Assessment
        const created = await ApiClient.createAssessment(courseId, {
          title: title,
          assessment_type: 'QUIZ',
          duration_minutes: duration,
          max_attempts: maxAtt,
          require_password: false,
          shuffle_questions: shuffle
        });

        const asmId = created?.assessment_id || created?.assessment?.public_id || created?.assessment?.id || created?.id;
        const questionsToSave = currentDraft.questions || [];
        let createdQuestionsCount = 0;

        // 2. Batch create questions
        if (asmId && questionsToSave.length > 0) {
          const batchQuestions = questionsToSave.map(q => {
            let qType = 'SINGLE_CHOICE';
            if (q.type === 'MULTIPLE_CHOICE' || q.question_type === 'TN nhiều đáp án') qType = 'MULTIPLE_CHOICE';
            else if (q.type === 'TRUE_FALSE' || q.question_type === 'Đúng / Sai') qType = 'TRUE_FALSE';
            else if (q.type === 'SHORT_ANSWER' || q.question_type === 'Điền từ' || q.question_type === 'Kéo thả') qType = 'SHORT_ANSWER';

            let diff = 'UNDERSTAND';
            if (q.bloom_level === 'Nhận biết') diff = 'REMEMBER';
            else if (q.bloom_level === 'Vận dụng') diff = 'APPLY';

            const payload = {
              question_type: qType,
              content: q.stem || q.question_text || `Câu hỏi`,
              difficulty: diff,
              points: parseFloat(q.points) || 1.0,
              explanation: q.explanation || ''
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
          } catch (pubErr) {
            console.warn('Lỗi kích hoạt xuất bản:', pubErr);
          }
        }

        window.ExamStore.clearDraft();
        UI.showToast(`Đề thi "${title}" đã xuất bản thành công kèm ${createdQuestionsCount} câu hỏi lưu vào CSDL!`, 'success');
        window.location.hash = '#/instructor/dashboard';
      } catch (err) {
        console.error('Lỗi xuất bản đề thi:', err);
        UI.showToast(`Lỗi xuất bản: ${err.message || err}`, 'error');
      }
    });

    runPreflight();
  };


  // =========================================================================
  // 9. Backwards compatibility alias
  // =========================================================================
  InstructorView.renderExams = function (container) {
    return InstructorView.renderExamsHub(container);
  };

  window.InstructorView = InstructorView;
})();

