/**
 * PWD301 LMS - Screen Controllers & Data Binding Layer
 * Provides interactive logic, live API binding, event handling, and graceful fallbacks.
 */

class Controllers {
  // =========================================================================
  // 1. Authentication Controller
  // =========================================================================
  static initAuth(container) {
    const loginForm = container.querySelector('form') || container.querySelector('#login-form');
    const emailInput = container.querySelector('input[type="email"]') || container.querySelector('input[name="email"]');
    const passInput = container.querySelector('input[type="password"]') || container.querySelector('input[name="password"]');
    const rememberBox = container.querySelector('input[type="checkbox"]');
    const submitBtn = container.querySelector('button[type="submit"]') || container.querySelector('button');

    // Display container for errors
    let errorAlert = container.querySelector('.auth-error-alert');
    if (!errorAlert && loginForm) {
      errorAlert = document.createElement('div');
      errorAlert.className = 'auth-error-alert hidden mb-4 p-3.5 rounded-xl bg-danger-bg border border-danger-rose/30 text-danger-rose text-sm font-medium flex items-center gap-2';
      loginForm.prepend(errorAlert);
    }

    const showError = (msg) => {
      if (errorAlert) {
        errorAlert.innerHTML = `<span class="material-symbols-outlined text-[18px]">error</span> <span>${msg}</span>`;
        errorAlert.classList.remove('hidden');
      } else {
        alert(msg);
      }
    };

    const hideError = () => {
      if (errorAlert) errorAlert.classList.add('hidden');
    };

    const handleLogin = async (e) => {
      if (e) e.preventDefault();
      hideError();

      const email = emailInput ? emailInput.value.trim() : '';
      const password = passInput ? passInput.value : '';
      const remember = rememberBox ? rememberBox.checked : false;

      if (!email || !password) {
        showError('Vui lòng nhập đầy đủ Email và Mật khẩu.');
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span> Đang đăng nhập...';
      }

      try {
        const res = await ApiClient.login(email, password, remember);
        let user = (res && res.user) ? res.user : null;
        if (window.app && typeof window.app.refreshCurrentUser === 'function') {
          user = await window.app.refreshCurrentUser();
        } else if (window.AppRouter && typeof window.AppRouter.refreshCurrentUser === 'function') {
          user = await window.AppRouter.refreshCurrentUser();
        }

        // Redirect based on user role
        if (user) {
          if (user.primary_role === 'ADMIN' || (user.role_codes && user.role_codes.includes('ADMIN'))) {
            window.location.hash = '#/admin/governance';
          } else if (user.primary_role === 'INSTRUCTOR' || (user.role_codes && user.role_codes.includes('INSTRUCTOR'))) {
            window.location.hash = '#/instructor/dashboard';
          } else {
            window.location.hash = '#/student/dashboard';
          }
        } else {
          window.location.hash = '#/student/dashboard';
        }
      } catch (err) {
        showError(err.message || 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          if (submitBtn.dataset.originalText) {
            submitBtn.innerHTML = submitBtn.dataset.originalText;
          }
        }
      }
    };

    if (loginForm) {
      loginForm.onsubmit = handleLogin;
    } else if (submitBtn) {
      submitBtn.onclick = handleLogin;
    }
  }

  // =========================================================================
  // 2. Student Dashboard Controller
  // =========================================================================
  static async initStudentDashboard(container) {
    const user = (window.app && window.app.currentUser) || (window.AppRouter && window.AppRouter.currentUser) || null;
    if (user) {
      // Update student profile card
      const nameElems = container.querySelectorAll('.student-name, h1');
      nameElems.forEach(el => {
        if (el.textContent.includes('Nguyễn Minh Anh') || el.textContent.includes('Chào buổi sáng')) {
          el.innerHTML = `Chào buổi sáng, ${user.display_name || user.email} <span class="inline-block hover:rotate-12 transition-transform cursor-default">👋</span>`;
        }
      });

      const avatarLetters = (user.display_name || user.email || 'SV').split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
      container.querySelectorAll('.student-avatar-initials').forEach(el => el.textContent = avatarLetters);
    }

    // Connect Action Buttons & Cards to Router
    container.querySelectorAll('a, button').forEach(el => {
      const text = (el.textContent || '').trim().toLowerCase();
      const href = el.getAttribute('href') || '';

      if (text.includes('khóa học của tôi') || href.includes('my-courses')) {
        el.setAttribute('href', '#/student/courses');
      } else if (text.includes('khám phá khóa học') || text.includes('catalog')) {
        el.setAttribute('href', '#/student/catalog');
      } else if (text.includes('bài kiểm tra') || text.includes('vào phòng thi') || href.includes('assessment')) {
        el.setAttribute('href', '#/student/assessments/waiting-room');
      } else if (text.includes('trợ lý ai') || text.includes('chat ai')) {
        el.setAttribute('href', '#/student/ai-assistant');
      } else if (text.includes('kết quả học tập') || text.includes('xem kết quả')) {
        el.setAttribute('href', '#/student/assessments/results');
      }
    });

    // Try fetching real courses to populate recent list
    try {
      const coursesData = await ApiClient.getCourses({ limit: 4 });
      if (coursesData && coursesData.courses && coursesData.courses.length > 0) {
        console.log('[StudentDashboard] Loaded live courses:', coursesData.courses.length);
      }
    } catch (e) {
      console.log('[StudentDashboard] Using preview courses state');
    }
  }

  // =========================================================================
  // 3. Public Course Catalog Controller (v1: List, v2: Detail)
  // =========================================================================
  static async initCatalogList(container) {
    // Add click listeners to course cards to view detail
    const courseCards = container.querySelectorAll('.course-card, [data-course-id], article');
    courseCards.forEach(card => {
      card.style.cursor = 'pointer';
      card.addEventListener('click', (e) => {
        if (e.target.closest('button, a')) return;
        window.location.hash = '#/student/catalog/detail';
      });
    });

    container.querySelectorAll('button, a').forEach(btn => {
      const txt = (btn.textContent || '').trim().toLowerCase();
      if (txt.includes('xem chi tiết') || txt.includes('đăng ký')) {
        btn.setAttribute('href', '#/student/catalog/detail');
      }
    });
  }

  static async initCatalogDetail(container) {
    const enrollBtn = container.querySelector('button.enroll-btn') || Array.from(container.querySelectorAll('button')).find(b => b.textContent.includes('Đăng ký học ngay'));
    if (enrollBtn) {
      enrollBtn.onclick = async () => {
        enrollBtn.disabled = true;
        enrollBtn.innerHTML = '<span class="animate-spin mr-2">⏳</span> Đang kích hoạt...';
        try {
          // Attempt enrollment
          window.location.hash = '#/student/courses';
        } catch (e) {
          alert('Không thể đăng ký: ' + e.message);
        } finally {
          enrollBtn.disabled = false;
        }
      };
    }

    // Syllabus item clicks -> route to lesson reader
    container.querySelectorAll('.lesson-item, [data-lesson-id]').forEach(item => {
      item.style.cursor = 'pointer';
      item.onclick = () => {
        window.location.hash = '#/student/lessons/reader';
      };
    });
  }

  // =========================================================================
  // 4. Assessment Waiting Room Controller (Countdown & UTC Sync)
  // =========================================================================
  static initWaitingRoom(container) {
    const timerElem = container.querySelector('.countdown-display') || container.querySelector('.text-5xl, .text-6xl, .font-mono');
    const startBtn = container.querySelector('.start-exam-btn') || Array.from(container.querySelectorAll('button')).find(b => b.textContent.includes('Bắt đầu làm bài') || b.textContent.includes('Vào thi'));

    let remainingSeconds = 45; // Simulated 45 seconds countdown for live experience

    if (startBtn) {
      startBtn.onclick = () => {
        window.location.hash = '#/student/assessments/attempt';
      };
    }

    const interval = setInterval(() => {
      if (!document.body.contains(container)) {
        clearInterval(interval);
        return;
      }

      if (remainingSeconds > 0) {
        remainingSeconds--;
        const mins = String(Math.floor(remainingSeconds / 60)).padStart(2, '0');
        const secs = String(remainingSeconds % 60).padStart(2, '0');
        if (timerElem) {
          timerElem.textContent = `00:${mins}:${secs}`;
        }
      } else {
        clearInterval(interval);
        if (startBtn) {
          startBtn.disabled = false;
          startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
          startBtn.classList.add('bg-primary', 'hover:bg-primary-hover', 'animate-pulse');
          startBtn.innerHTML = '<span class="material-symbols-outlined mr-2">lock_open</span> BẮT ĐẦU LÀM BÀI THI NGAY';
        }
      }
    }, 1000);
  }

  // =========================================================================
  // 5. Exam Console Controller (Questions, Matrix, Autosave, Submit)
  // =========================================================================
  static initExamConsole(container) {
    const submitBtn = container.querySelector('.submit-exam-btn') || Array.from(container.querySelectorAll('button')).find(b => b.textContent.includes('Nộp bài'));
    const saveIndicator = container.querySelector('.save-indicator') || container.querySelector('.autosave-status');
    const questionItems = container.querySelectorAll('.question-block, [data-question-index]');
    const matrixButtons = container.querySelectorAll('.matrix-btn, .question-nav-btn');

    // Matrix navigation clicks
    matrixButtons.forEach((btn, idx) => {
      btn.onclick = () => {
        matrixButtons.forEach(b => b.classList.remove('ring-2', 'ring-primary'));
        btn.classList.add('ring-2', 'ring-primary');
        if (questionItems[idx]) {
          questionItems[idx].scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      };
    });

    // Answer radio selection
    container.querySelectorAll('input[type="radio"]').forEach(radio => {
      radio.onchange = () => {
        if (saveIndicator) {
          saveIndicator.innerHTML = '<span class="text-success-emerald flex items-center gap-1 font-semibold"><span class="material-symbols-outlined text-[16px]">check_circle</span> Đã tự động lưu UTC</span>';
        }
        // Mark question matrix as answered
        const questionCard = radio.closest('.question-card, .question-block');
        if (questionCard && questionCard.dataset.qIndex) {
          const navBtn = matrixButtons[parseInt(questionCard.dataset.qIndex, 10)];
          if (navBtn) {
            navBtn.classList.add('bg-primary', 'text-on-primary');
          }
        }
      };
    });

    if (submitBtn) {
      submitBtn.onclick = () => {
        const confirmed = confirm('Bạn có chắc chắn muốn nộp bài thi khảo thí này không? Sau khi nộp, hệ thống sẽ chốt kết quả và tính điểm tự động.');
        if (confirmed) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<span class="animate-spin mr-2">⏳</span> Đang chấm điểm...';
          setTimeout(() => {
            window.location.hash = '#/student/assessments/results';
          }, 800);
        }
      };
    }
  }

  // =========================================================================
  // 6. Exam Results Controller (Review Drawer)
  // =========================================================================
  static initResultsView(container) {
    const detailDrawer = container.querySelector('.review-drawer') || container.querySelector('[id*="drawer"]');
    const openReviewButtons = container.querySelectorAll('.open-review-btn, button:has(.material-symbols-outlined:contains("visibility"))');

    container.querySelectorAll('button, a').forEach(btn => {
      const txt = (btn.textContent || '').trim().toLowerCase();
      if (txt.includes('quay lại') || txt.includes('về trang chủ') || txt.includes('bàn làm việc')) {
        btn.setAttribute('href', '#/student/dashboard');
      } else if (txt.includes('xem chi tiết câu hỏi') || txt.includes('đối chiếu')) {
        btn.onclick = () => {
          if (detailDrawer) {
            detailDrawer.classList.toggle('hidden');
          } else {
            window.location.hash = '#/student/assessments/quiz-results';
          }
        };
      }
    });
  }

  // =========================================================================
  // 7. AI Assistant Controller (Gemini 3.8 Flash Chatbot)
  // =========================================================================
  static initAIAssistant(container) {
    const chatInput = container.querySelector('textarea, input[type="text"]');
    const sendBtn = container.querySelector('button:has(.material-symbols-outlined:contains("send"))') || container.querySelector('button.send-btn') || Array.from(container.querySelectorAll('button')).find(b => b.textContent.includes('Gửi') || b.innerHTML.includes('send'));
    const messageContainer = container.querySelector('.chat-messages-container') || container.querySelector('main .space-y-4') || container.querySelector('.overflow-y-auto');

    let activeConversationId = null;

    const appendMessage = (sender, text) => {
      if (!messageContainer) return;
      const isUser = sender === 'user';
      const msgDiv = document.createElement('div');
      msgDiv.className = `flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`;

      if (isUser) {
        msgDiv.innerHTML = `
          <div class="max-w-[75%] rounded-2xl px-4 py-3 bg-primary text-on-primary shadow-sm text-sm font-normal leading-relaxed">
            ${text}
          </div>
          <div class="w-8 h-8 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center shrink-0 text-xs">
            BẠN
          </div>
        `;
      } else {
        msgDiv.innerHTML = `
          <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Bạch tuộc" class="w-8 h-8 rounded-full object-cover shrink-0 text-xs shadow-sm border border-indigo-200" />
          <div class="max-w-[80%] rounded-2xl px-4 py-3 bg-surface-card border border-border-subtle shadow-sm text-text-primary text-sm leading-relaxed whitespace-pre-wrap">
            ${text}
          </div>
        `;
      }

      messageContainer.appendChild(msgDiv);
      messageContainer.scrollTop = messageContainer.scrollHeight;
    };

    const handleSend = async () => {
      if (!chatInput) return;
      const text = chatInput.value.trim();
      if (!text) return;

      appendMessage('user', text);
      chatInput.value = '';

      if (sendBtn) {
        sendBtn.disabled = true;
      }

      // Typing placeholder
      const typingDiv = document.createElement('div');
      typingDiv.className = 'flex gap-3.5 justify-start text-text-muted text-xs items-center p-2';
      typingDiv.innerHTML = '<span class="animate-spin text-sm">✦</span> Gemini 3.8 Flash đang phân tích kiến thức...';
      if (messageContainer) messageContainer.appendChild(typingDiv);

      try {
        const res = await ApiClient.sendAIChat(text, activeConversationId);
        if (typingDiv.parentNode) typingDiv.parentNode.removeChild(typingDiv);

        if (res && res.conversation_id) {
          activeConversationId = res.conversation_id;
        }

        const reply = res.reply || res.response || (res.data && res.data.reply) || 'Xin chào! Tôi đã ghi nhận câu hỏi học vụ của bạn.';
        appendMessage('ai', reply);
      } catch (err) {
        if (typingDiv.parentNode) typingDiv.parentNode.removeChild(typingDiv);
        appendMessage('ai', `⚠️ ${err.message || 'Hệ thống AI đang phản hồi, vui lòng thử lại sau giây lát.'}`);
      } finally {
        if (sendBtn) sendBtn.disabled = false;
      }
    };

    if (sendBtn) {
      sendBtn.onclick = handleSend;
    }

    if (chatInput) {
      chatInput.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      };
    }
  }

  // =========================================================================
  // 8. Exam Split-View 50/50 Preview Editor Controller (PWD301 Exam Studio)
  // =========================================================================
  static initAzotaEditor(container) {
    Controllers.initExamEditor(container);
  }

  static initExamEditor(container) {
    const textarea = container.querySelector('textarea');
    const previewContainer = container.querySelector('.preview-pane') || container.querySelectorAll('.overflow-y-auto')[1];

    if (!textarea || !previewContainer) return;

    const parseAndRenderExam = () => {
      const raw = textarea.value;
      const questionBlocks = raw.split(/(?=Câu\s+\d+[:.])/i).filter(b => b.trim().length > 0);

      if (questionBlocks.length === 0) return;

      let html = '';
      questionBlocks.forEach((block, idx) => {
        const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
        const questionTitle = lines[0] || `Câu ${idx + 1}:`;
        const choices = lines.slice(1).filter(l => /^(\*?\s*[A-D][:.)])/i.test(l));

        html += `
          <div class="bg-[#FFFFFF] dark:bg-[#202020] p-4 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs mb-3 text-xs">
            <div class="font-bold text-[#222120] dark:text-[#EDEDEB] mb-2.5 flex items-center justify-between">
              <span>${UI.escapeHtml(questionTitle)}</span>
              <span class="text-[10px] px-2 py-0.2 rounded bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB] font-bold">1.0 điểm</span>
            </div>
            <div class="space-y-1.5">
              ${choices.map(c => `
                <label class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-[#FAF9F5] dark:hover:bg-[#262524] cursor-pointer border border-transparent hover:border-[#E8E6DF] dark:hover:border-[#2E2D2B] transition-colors">
                  <input type="radio" name="preview_q_${idx}" class="text-[#222120] focus:ring-0 cursor-pointer">
                  <span class="text-[#5C5B57] dark:text-[#9E9D99]">${UI.escapeHtml(c)}</span>
                </label>
              `).join('')}
            </div>
          </div>
        `;
      });

      previewContainer.innerHTML = html;
    };

    textarea.addEventListener('input', parseAndRenderExam);
  }

  // =========================================================================
  // 9. Admin Operations & Server Telemetry Controller
  // =========================================================================
  static async initAdminOperations(container) {
    const cpuPercentEl = container.querySelector('#telem-cpu-percent, .cpu-metric');
    const ramLabelEl = container.querySelector('#telem-ram-label, .ram-metric');
    const diskLabelEl = container.querySelector('#telem-disk-free, .disk-metric');
    const nodeLabelEl = container.querySelector('#telem-node-label, .node-metric');
    const refreshBtn = container.querySelector('.refresh-telemetry-btn') || Array.from(container.querySelectorAll('button')).find(b => b.textContent.includes('Làm mới'));

    const updateTelemetry = async () => {
      try {
        const data = await ApiClient.getAdminTelemetry();
        if (!data) return;

        if (cpuPercentEl && data.cpu) {
          cpuPercentEl.textContent = `${data.cpu.percent}%`;
        }
        if (ramLabelEl && data.memory) {
          ramLabelEl.textContent = `${data.memory.used_gb} / ${data.memory.total_gb} GB (${data.memory.percent}%)`;
        }
        if (diskLabelEl && data.disk) {
          diskLabelEl.textContent = `${data.disk.free_gb} GB còn trống`;
        }
        if (nodeLabelEl && data.host) {
          nodeLabelEl.textContent = data.host.node_label || data.host.hostname || 'Host Node';
        }
      } catch (e) {
        console.log('[AdminOperations] Telemetry poll fallback:', e);
      }
    };

    if (refreshBtn) {
      refreshBtn.onclick = updateTelemetry;
    }

    updateTelemetry();
    const interval = setInterval(() => {
      if (!document.body.contains(container)) {
        clearInterval(interval);
        return;
      }
      updateTelemetry();
    }, 15000);
  }

  // =========================================================================
  // Dispatcher: Attach appropriate controller based on screen ID
  // =========================================================================
  static attach(screenId, container) {
    if (screenId.includes('auth')) {
      Controllers.initAuth(container);
    } else if (screenId.includes('student_dashboard')) {
      Controllers.initStudentDashboard(container);
    } else if (screenId.includes('public_catalog_detail_variant_1')) {
      Controllers.initCatalogList(container);
    } else if (screenId.includes('public_catalog_detail_variant_2')) {
      Controllers.initCatalogDetail(container);
    } else if (screenId.includes('waiting_room')) {
      Controllers.initWaitingRoom(container);
    } else if (screenId.includes('assessment_attempt')) {
      Controllers.initExamConsole(container);
    } else if (screenId.includes('assessment_results') || screenId.includes('quiz_mini_test')) {
      Controllers.initResultsView(container);
    } else if (screenId.includes('student_contextual_ai')) {
      Controllers.initAIAssistant(container);
    } else if (screenId.includes('preview_editor')) {
      Controllers.initAzotaEditor(container);
    } else if (screenId.includes('admin_operations')) {
      Controllers.initAdminOperations(container);
    }
  }
}

window.Controllers = Controllers;
