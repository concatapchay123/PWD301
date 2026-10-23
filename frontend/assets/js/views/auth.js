/**
 * PWD301 LMS - Authentication & Account Lifecycle View
 * Warm Editorial Notion-like Edition: Focused Minimalist Card, Clean Typography, Zero-distraction
 */

class AuthView {
  static isCapsLockActive = false;

  static attachDemoButtons(root) {
    root.querySelectorAll('.seed-acc-btn').forEach(btn => {
      btn.onclick = () => {
        const email = document.getElementById('login-email');
        const password = document.getElementById('login-password');
        if (email) email.value = btn.dataset.email || '';
        if (password) password.value = btn.dataset.pass || '';
        window._demoSelectedRole = btn.dataset.role || null;
        document.getElementById('auth-error-alert')?.classList.add('hidden');
        document.getElementById('login-submit-btn')?.focus();
      };
    });
  }

  static checkCapsLock(event) {
    if (!event || typeof event.getModifierState !== 'function') {
      return false;
    }
    return Boolean(event.getModifierState('CapsLock'));
  }

  static setupCapsLockWarning(inputElement, warningElement) {
    if (!inputElement || !warningElement) return null;

    const show = () => warningElement.classList.remove('hidden');
    const hide = () => warningElement.classList.add('hidden');

    const onKey = (e) => {
      if (!e || typeof e.getModifierState !== 'function') return;
      const isCaps = e.getModifierState('CapsLock');
      AuthView.isCapsLockActive = isCaps;
      if (isCaps) {
        show();
      } else {
        hide();
      }
    };

    const onClick = (e) => {
      if (e && typeof e.getModifierState === 'function') {
        const isCaps = e.getModifierState('CapsLock');
        AuthView.isCapsLockActive = isCaps;
        if (isCaps) {
          show();
          return;
        }
      }
      if (AuthView.isCapsLockActive) {
        show();
      } else {
        hide();
      }
    };

    const onFocus = () => {
      if (AuthView.isCapsLockActive) {
        show();
      }
    };

    const onBlur = () => {
      hide();
    };

    inputElement.addEventListener('keydown', onKey);
    inputElement.addEventListener('keyup', onKey);
    inputElement.addEventListener('click', onClick);
    inputElement.addEventListener('focus', onFocus);
    inputElement.addEventListener('blur', onBlur);

    return {
      cleanup: () => {
        inputElement.removeEventListener('keydown', onKey);
        inputElement.removeEventListener('keyup', onKey);
        inputElement.removeEventListener('click', onClick);
        inputElement.removeEventListener('focus', onFocus);
        inputElement.removeEventListener('blur', onBlur);
      }
    };
  }

  static render(runtime = {}) {
    return `
      <div class="min-h-full w-full flex flex-col justify-center items-center px-4 py-8 sm:py-14 bg-[#FAF9F5] dark:bg-[#191919] font-sans selection:bg-[#ECE8DF] selection:text-[#222120] dark:selection:bg-[#37352F] dark:selection:text-[#EDEDEB] relative">
        
        <div class="w-full max-w-sm">
          
          <!-- Brand Logo: Căn chính giữa ngay trên UI cụm đăng nhập -->
          <div class="flex justify-center items-center mb-6 select-none">
            <a href="#/" class="inline-flex items-center justify-center transition-transform hover:scale-[1.02] active:scale-[0.98]" title="PPTQ LMS">
              <img src="/frontend/assets/img/pptq_logo.png" alt="PPTQ Logo" class="h-10 sm:h-11 w-auto object-contain dark:hidden" />
              <img src="/frontend/assets/img/pptq_logo_dark.png" alt="PPTQ Logo" class="h-10 sm:h-11 w-auto object-contain hidden dark:inline-block" />
            </a>
          </div>
          
          <!-- Security Alert Banner (if locked down) -->
          ${(() => {
            let secAlert = null;
            try {
              if (typeof sessionStorage !== 'undefined') {
                secAlert = sessionStorage.getItem('pwd301_security_alert');
              }
              if (!secAlert && typeof window !== 'undefined' && window.location && window.location.hash.includes('security_lockdown=1')) {
                secAlert = 'Cảnh báo an ninh: Phiên làm việc đã bị thu hồi do phát hiện hành vi vi phạm chính sách bảo mật hệ thống.';
              }
            } catch (_) {}
            if (!secAlert) return '';
            return `
              <div id="auth-security-alert-banner" class="mb-4 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 text-xs font-medium flex items-start gap-3 animate-fade-in shadow-xs" role="alert">
                <span class="material-symbols-outlined text-[20px] text-rose-600 dark:text-rose-400 shrink-0">shield</span>
                <div class="space-y-1">
                  <div class="font-bold text-rose-900 dark:text-rose-200">🛡️ CẢNH BÁO AN NINH HỆ THỐNG</div>
                  <div class="leading-relaxed text-[11.5px] text-rose-700 dark:text-rose-300">${typeof UI !== 'undefined' && UI.escapeHtml ? UI.escapeHtml(secAlert) : secAlert}</div>
                </div>
              </div>
            `;
          })()}

          <!-- Mode Switcher Tabs -->
          <div class="flex p-1 bg-[#ECE8DF] dark:bg-[#252525] rounded-xl mb-4 text-xs font-semibold select-none">
            <button type="button" id="tab-nav-login" class="flex-1 py-1.5 text-center rounded-lg transition-all bg-[#FFFFFF] dark:bg-[#1E1E1E] text-[#222120] dark:text-[#EDEDEB] shadow-xs cursor-pointer">
              Đăng nhập
            </button>
            <button type="button" id="tab-nav-register" class="flex-1 py-1.5 text-center rounded-lg transition-all text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer">
              Đăng ký
            </button>
          </div>

          <!-- PRIMARY CARD: ĐĂNG NHẬP -->
          <div id="auth-tab-login" class="c-card p-6 space-y-5 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div>
              <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] tracking-tight">Đăng nhập tài khoản</h2>
              <p class="text-xs text-[#8F8E8A] mt-0.5">Dùng email và mật khẩu của bạn để tiếp tục</p>
            </div>

            <!-- Dynamic Error Alert -->
            <div id="auth-error-alert" class="hidden p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 text-xs font-medium flex items-start gap-2">
              <span class="material-symbols-outlined text-[16px] shrink-0 mt-0.5">error</span>
              <span id="auth-error-text" class="flex-1 leading-snug"></span>
            </div>

            <!-- Unverified Email Alert -->
            <div id="login-unverified-alert" class="hidden p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-900/60 text-amber-900 dark:text-amber-200 text-xs space-y-2">
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-[18px] text-amber-600 dark:text-amber-400 shrink-0">mark_email_unread</span>
                <span id="login-unverified-text" class="flex-1 font-medium leading-relaxed">Tài khoản của bạn chưa được xác thực email.</span>
              </div>
              <div class="flex items-center gap-2 pt-1">
                <button type="button" id="btn-login-resend-verification" class="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold text-[11.5px] cursor-pointer shadow-xs transition-colors">
                  Gửi lại email xác thực
                </button>
              </div>
            </div>

            <form id="auth-login-form" class="space-y-3.5" novalidate>
              <!-- Email Input -->
              <div class="space-y-1">
                <label for="login-email" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                  Email học thuật
                </label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">mail</span>
                  </span>
                  <input
                    type="email"
                    id="login-email"
                    name="email"
                    required
                    autocomplete="email"
                    placeholder="Nhập email..."
                    class="c-input pl-9"
                  />
                </div>
                <!-- Caps Lock Warning for Email -->
                <div id="login-email-capslock-warning" class="hidden px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-all" role="alert" aria-live="polite">
                  <span class="material-symbols-outlined text-[15px] shrink-0 text-amber-600 dark:text-amber-400">keyboard_capslock</span>
                  <span>Đang bật Caps Lock</span>
                </div>
              </div>

              <!-- Password Input -->
              <div class="space-y-1">
                <div class="flex items-center justify-between">
                  <label for="login-password" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                    Mật khẩu
                  </label>
                  <button type="button" class="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline cursor-pointer" id="btn-goto-recovery">
                    Quên mật khẩu?
                  </button>
                </div>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">lock</span>
                  </span>
                  <input
                    type="password"
                    id="login-password"
                    name="password"
                    required
                    autocomplete="current-password"
                    placeholder="Nhập mật khẩu..."
                    class="c-input pl-9 pr-9"
                  />
                  <button
                    type="button"
                    id="toggle-password-btn"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] transition-colors cursor-pointer"
                    title="Ẩn / Hiện mật khẩu"
                  >
                    <span class="material-symbols-outlined text-[16px]" id="password-eye-icon">visibility</span>
                  </button>
                </div>
                <!-- Caps Lock Warning for Password -->
                <div id="login-capslock-warning" class="hidden px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-all" role="alert" aria-live="polite">
                  <span class="material-symbols-outlined text-[15px] shrink-0 text-amber-600 dark:text-amber-400">keyboard_capslock</span>
                  <span>Đang bật Caps Lock</span>
                </div>
              </div>

              <!-- Remember Me -->
              <div class="flex items-center justify-between pt-0.5">
                <label class="flex items-center gap-2 cursor-pointer select-none text-xs text-[#5C5B57] dark:text-[#9E9D99]">
                  <input
                    type="checkbox"
                    id="login-remember"
                    class="w-3.5 h-3.5 rounded text-[#222120] focus:ring-0 border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] cursor-pointer"
                  />
                  <span>Ghi nhớ đăng nhập</span>
                </label>
                <span class="text-[10px] text-[#8F8E8A] flex items-center gap-1">
                  <span class="material-symbols-outlined text-[13px] text-emerald-600">lock</span>
                  ${window.location?.protocol === 'https:' ? 'Bảo mật TLS' : 'Kết nối cục bộ'}
                </span>
              </div>

              <!-- Submit Button -->
              <button
                type="submit"
                id="login-submit-btn"
                class="w-full c-btn c-btn-primary c-btn-lg justify-center mt-2"
              >
                <span class="material-symbols-outlined text-[17px]">login</span>
                <span>Đăng nhập hệ thống</span>
              </button>

              <div class="text-center pt-2">
                <button type="button" id="btn-goto-register-from-login" class="text-xs text-blue-600 dark:text-blue-400 hover:underline cursor-pointer">
                  Chưa có tài khoản? Đăng ký ngay
                </button>
              </div>
            </form>

            <div id="auth-demo-anchor">
            ${runtime.demo_accounts_enabled === true && ['development', 'testing'].includes(runtime.environment) ? `
            <!-- Quick Seed Demo Accounts Accordion -->
            <div id="auth-demo-accounts" class="pt-3 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
              <details class="group">
                <summary class="flex items-center justify-between text-xs font-semibold text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer select-none py-1">
                  <span class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[15px] text-amber-600">bolt</span>
                    Tài khoản demo nhanh
                  </span>
                  <span class="material-symbols-outlined text-[15px] group-open:rotate-180 transition-transform">expand_more</span>
                </summary>
                
                <div class="mt-2 space-y-1.5 pt-1">
                  <!-- Student 1 -->
                  <button
                    type="button"
                    class="seed-acc-btn text-left p-2 rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#262524] hover:border-[#222120] dark:hover:border-[#EDEDEB] transition-all flex items-center justify-between group/btn cursor-pointer w-full"
                    data-email="student1@pwd301.local"
                    data-pass="Password123!"
                    data-role="STUDENT"
                  >
                    <div>
                      <div class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Học viên (Student)</div>
                      <div class="text-[10px] text-[#8F8E8A] font-mono">student1@pwd301.local</div>
                    </div>
                    <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB]">SV</span>
                  </button>

                  <!-- Instructor 1 -->
                  <button
                    type="button"
                    class="seed-acc-btn text-left p-2 rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#262524] hover:border-[#222120] dark:hover:border-[#EDEDEB] transition-all flex items-center justify-between group/btn cursor-pointer w-full"
                    data-email="instructor1@pwd301.local"
                    data-pass="Password123!"
                    data-role="INSTRUCTOR"
                  >
                    <div>
                      <div class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Giảng viên (Instructor)</div>
                      <div class="text-[10px] text-[#8F8E8A] font-mono">instructor1@pwd301.local</div>
                    </div>
                    <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB]">GV</span>
                  </button>

                  <!-- Admin -->
                  <button
                    type="button"
                    class="seed-acc-btn text-left p-2 rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#262524] hover:border-[#222120] dark:hover:border-[#EDEDEB] transition-all flex items-center justify-between group/btn cursor-pointer w-full"
                    data-email="admin@pwd301.local"
                    data-pass="Password123!"
                    data-role="ADMIN"
                  >
                    <div>
                      <div class="text-xs font-bold text-[#222120] dark:text-[#EDEDEB]">Quản trị viên (Admin)</div>
                      <div class="text-[10px] text-[#8F8E8A] font-mono">admin@pwd301.local</div>
                    </div>
                    <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB]">Admin</span>
                  </button>
                </div>
              </details>
            </div>
            ` : ''}
            </div>
          </div>

          <!-- SECONDARY CARD: ĐĂNG KÝ TÀI KHOẢN -->
          <div id="auth-tab-register" class="hidden c-card p-6 space-y-5 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div>
              <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] tracking-tight">Đăng ký tài khoản</h2>
              <p class="text-xs text-[#8F8E8A] mt-0.5">Tạo tài khoản học viên để tham gia học tập trực tuyến</p>
            </div>

            <!-- Dynamic Error Alert -->
            <div id="register-error-alert" class="hidden p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 text-xs font-medium flex items-start gap-2">
              <span class="material-symbols-outlined text-[16px] shrink-0 mt-0.5">error</span>
              <span id="register-error-text" class="flex-1 leading-snug"></span>
            </div>

            <form id="auth-register-form" class="space-y-3.5" novalidate>
              <!-- Name Input -->
              <div class="space-y-1">
                <label for="register-name" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                  Họ và tên <span class="text-rose-500">*</span>
                </label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">person</span>
                  </span>
                  <input
                    type="text"
                    id="register-name"
                    name="name"
                    required
                    autocomplete="name"
                    placeholder="Nguyễn Văn A"
                    class="c-input pl-9"
                  />
                </div>
              </div>

              <!-- Email Input -->
              <div class="space-y-1">
                <label for="register-email" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                  Email học thuật <span class="text-rose-500">*</span>
                </label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">mail</span>
                  </span>
                  <input
                    type="email"
                    id="register-email"
                    name="email"
                    required
                    autocomplete="email"
                    placeholder="Nhập email..."
                    class="c-input pl-9"
                  />
                </div>
              </div>

              <!-- Password Input -->
              <div class="space-y-1">
                <label for="register-password" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                  Mật khẩu <span class="text-rose-500">*</span>
                </label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">lock</span>
                  </span>
                  <input
                    type="password"
                    id="register-password"
                    name="password"
                    required
                    autocomplete="new-password"
                    placeholder="Nhập mật khẩu..."
                    class="c-input pl-9 pr-9"
                  />
                  <button
                    type="button"
                    id="toggle-register-pass-btn"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] transition-colors cursor-pointer"
                    title="Ẩn / Hiện mật khẩu"
                  >
                    <span class="material-symbols-outlined text-[16px]" id="register-pass-eye-icon">visibility</span>
                  </button>
                </div>

                <!-- Caps Lock Warning for Register Password -->
                <div id="register-capslock-warning" class="hidden px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-all" role="alert" aria-live="polite">
                  <span class="material-symbols-outlined text-[15px] shrink-0 text-amber-600 dark:text-amber-400">keyboard_capslock</span>
                  <span>Đang bật Caps Lock</span>
                </div>

                <!-- Live Password Rules Checklist -->
                <div class="p-2.5 rounded-lg bg-[#FAF9F5] dark:bg-[#262524] border border-[#E8E6DF] dark:border-[#2E2D2B] space-y-1 mt-1.5 text-[11px]">
                  <div class="font-semibold text-[#8F8E8A] text-[10px] uppercase tracking-wider mb-1">Yêu cầu bảo mật mật khẩu:</div>
                  <div id="pwd-check-len" class="flex items-center gap-1.5 text-[#8F8E8A] transition-colors">
                    <span class="material-symbols-outlined text-[14px]">cancel</span>
                    <span>Tối thiểu 8 ký tự</span>
                  </div>
                  <div id="pwd-check-letter" class="flex items-center gap-1.5 text-[#8F8E8A] transition-colors">
                    <span class="material-symbols-outlined text-[14px]">cancel</span>
                    <span>Chứa ít nhất một chữ cái (a-z, A-Z)</span>
                  </div>
                  <div id="pwd-check-digit" class="flex items-center gap-1.5 text-[#8F8E8A] transition-colors">
                    <span class="material-symbols-outlined text-[14px]">cancel</span>
                    <span>Chứa ít nhất một chữ số (0-9)</span>
                  </div>
                  <div id="pwd-check-special" class="flex items-center gap-1.5 text-[#8F8E8A] transition-colors">
                    <span class="material-symbols-outlined text-[14px]">cancel</span>
                    <span>Chứa ít nhất một ký tự đặc biệt (!@#$%^&*...)</span>
                  </div>
                </div>
              </div>

              <!-- Confirm Password Input -->
              <div class="space-y-1">
                <label for="register-confirm-password" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                  Xác nhận mật khẩu <span class="text-rose-500">*</span>
                </label>
                <div class="relative">
                  <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                    <span class="material-symbols-outlined text-[16px]">lock_reset</span>
                  </span>
                  <input
                    type="password"
                    id="register-confirm-password"
                    name="confirm_password"
                    required
                    autocomplete="new-password"
                    placeholder="Nhập lại mật khẩu..."
                    class="c-input pl-9"
                  />
                </div>
                <!-- Caps Lock Warning for Register Confirm Password -->
                <div id="register-confirm-capslock-warning" class="hidden px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-all" role="alert" aria-live="polite">
                  <span class="material-symbols-outlined text-[15px] shrink-0 text-amber-600 dark:text-amber-400">keyboard_capslock</span>
                  <span>Đang bật Caps Lock</span>
                </div>
              </div>

              <!-- Submit Button -->
              <button
                type="submit"
                id="register-submit-btn"
                class="w-full c-btn c-btn-primary c-btn-lg justify-center mt-2"
              >
                <span class="material-symbols-outlined text-[17px]">how_to_reg</span>
                <span>Tạo tài khoản học viên</span>
              </button>

              <div class="text-center pt-2">
                <button type="button" id="btn-goto-login-from-reg" class="text-xs text-blue-600 dark:text-blue-400 hover:underline cursor-pointer">
                  Đã có tài khoản? Đăng nhập ngay
                </button>
              </div>
            </form>
          </div>

          <!-- SECONDARY CARD: KHÔI PHỤC MẬT KHẨU -->
          <div id="auth-tab-recovery" class="hidden c-card p-6 space-y-4 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div class="text-center space-y-1">
              <div class="w-10 h-10 mx-auto rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 flex items-center justify-center">
                <span class="material-symbols-outlined text-[22px]">lock_reset</span>
              </div>
              <h2 class="text-base font-bold text-[#222120] dark:text-[#EDEDEB]">Khôi phục mật khẩu</h2>
              <p class="text-xs text-[#8F8E8A] max-w-xs mx-auto leading-relaxed">Nhập địa chỉ email học vụ để nhận liên kết đặt lại mật khẩu.</p>
            </div>

            <div class="space-y-1">
              <label for="recovery-email" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
                Email học thuật
              </label>
              <div class="relative">
                <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
                  <span class="material-symbols-outlined text-[16px]">mail</span>
                </span>
                <input
                  type="email"
                  id="recovery-email"
                  placeholder="Nhập email..."
                  class="c-input pl-9"
                />
              </div>
            </div>

            <div class="space-y-2 pt-1">
              <button type="button" id="btn-send-recovery" class="w-full c-btn c-btn-primary c-btn-md justify-center">
                Gửi liên kết khôi phục
              </button>
              <button type="button" id="btn-back-to-login" class="w-full c-btn c-btn-ghost c-btn-md justify-center">
                Quay lại Đăng nhập
              </button>
            </div>
          </div>

          <!-- OPTIONAL 2FA CARD -->
          <div id="auth-tab-twofa" class="hidden c-card p-6 space-y-4 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B]">
            <div class="text-center space-y-1">
              <div class="w-10 h-10 mx-auto rounded-xl bg-[#F4F1EA] dark:bg-[#262524] text-[#222120] dark:text-[#EDEDEB] flex items-center justify-center">
                <span class="material-symbols-outlined text-[22px]">verified_user</span>
              </div>
              <h2 class="text-base font-bold text-[#222120] dark:text-[#EDEDEB]">Xác thực 2 Bước (2FA)</h2>
              <p class="text-xs text-[#8F8E8A] leading-relaxed">Nhập mã xác thực từ ứng dụng Authenticator.</p>
            </div>

            <div class="space-y-2 text-center">
              <div class="flex justify-center gap-1.5" id="twofa-digit-inputs">
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="4" />
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="8" />
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="2" />
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="9" />
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="1" />
                <input type="text" maxlength="1" class="w-9 h-11 text-center text-base font-mono font-bold rounded-lg border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] outline-none focus:border-[#222120] dark:focus:border-[#EDEDEB]" value="0" />
              </div>
            </div>

            <div class="space-y-2 pt-1">
              <button type="button" id="btn-verify-twofa-demo" class="w-full c-btn c-btn-primary c-btn-md justify-center">
                Xác nhận mã 2FA
              </button>
              <button type="button" class="w-full c-btn c-btn-ghost c-btn-md justify-center" onclick="document.querySelector('#btn-back-to-login')?.click()">
                Hủy & Quay lại
              </button>
            </div>
          </div>

          <!-- SECONDARY CARD: CHỜ XÁC THỰC EMAIL -->
          <div id="auth-tab-verification-pending" class="hidden c-card p-6 space-y-5 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] text-center">
            <div class="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
              <span class="material-symbols-outlined text-[32px]">mark_email_read</span>
            </div>
            <div class="space-y-1">
              <h2 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB]">Kiểm tra hộp thư của bạn</h2>
              <p class="text-xs text-[#8F8E8A] max-w-sm mx-auto leading-relaxed">
                Chúng tôi đã gửi một liên kết xác nhận kích hoạt tài khoản đến địa chỉ:
              </p>
              <p id="verify-pending-email-display" class="font-bold text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 py-1.5 px-3 rounded-lg inline-block break-all border border-emerald-200 dark:border-emerald-800/50 mt-1">
                email@example.com
              </p>
            </div>
            <p class="text-xs text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed max-w-xs mx-auto">
              Vui lòng mở email và nhấn vào nút <strong>"Xác nhận kích hoạt tài khoản"</strong> để hoàn tất đăng ký và bắt đầu đăng nhập.
            </p>
            <div class="space-y-2 pt-2">
              <button type="button" id="btn-pending-resend" class="w-full c-btn c-btn-secondary c-btn-md justify-center">
                <span class="material-symbols-outlined text-[16px]">forward_to_inbox</span>
                <span>Gửi lại email xác thực</span>
              </button>
              <button type="button" id="btn-pending-back-login" class="w-full c-btn c-btn-primary c-btn-md justify-center">
                Đến trang Đăng nhập
              </button>
            </div>
          </div>

          <!-- SECONDARY CARD: TRẠNG THÁI XÁC THỰC EMAIL TỪ TOKEN -->
          <div id="auth-tab-verify-action" class="hidden c-card p-6 space-y-5 bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] text-center">
            <!-- Loading state -->
            <div id="verify-action-loading" class="space-y-4 py-4">
              <div class="w-12 h-12 mx-auto rounded-full border-4 border-emerald-500 border-t-transparent animate-spin"></div>
              <div>
                <h3 class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB]">Đang xác thực tài khoản...</h3>
                <p class="text-xs text-[#8F8E8A] mt-1">Vui lòng đợi trong giây lát</p>
              </div>
            </div>
            <!-- Success state -->
            <div id="verify-action-success" class="hidden space-y-4 py-2">
              <div class="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <span class="material-symbols-outlined text-[32px]">check_circle</span>
              </div>
              <div class="space-y-1">
                <h3 class="text-base font-bold text-emerald-800 dark:text-emerald-300">Xác thực email thành công!</h3>
                <p class="text-xs text-[#8F8E8A] leading-relaxed">Tài khoản của bạn đã được kích hoạt. Bạn có thể đăng nhập ngay bây giờ.</p>
              </div>
              <button type="button" id="btn-verify-success-login" class="w-full c-btn c-btn-primary c-btn-md justify-center mt-2">
                Đăng nhập ngay
              </button>
            </div>
            <!-- Error state -->
            <div id="verify-action-error" class="hidden space-y-4 py-2">
              <div class="w-14 h-14 mx-auto rounded-2xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center">
                <span class="material-symbols-outlined text-[32px]">error</span>
              </div>
              <div class="space-y-1">
                <h3 class="text-base font-bold text-rose-800 dark:text-rose-300">Xác thực không thành công</h3>
                <p id="verify-action-error-msg" class="text-xs text-[#8F8E8A] leading-relaxed">Liên kết xác thực không hợp lệ hoặc đã hết hạn.</p>
              </div>
              <div class="space-y-2 pt-2">
                <button type="button" id="btn-verify-error-resend" class="w-full c-btn c-btn-secondary c-btn-md justify-center">
                  Gửi lại email kích hoạt mới
                </button>
                <button type="button" id="btn-verify-error-login" class="w-full c-btn c-btn-ghost c-btn-md justify-center">
                  Quay lại Đăng nhập
                </button>
              </div>
            </div>
          </div>



        </div>
      </div>
    `;
  }

  static attachEvents() {
    try {
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.removeItem('pwd301_security_alert');
      }
    } catch (_) {}
    const anchor = document.getElementById('auth-demo-anchor');
    if (anchor && typeof fetch === 'function') {
      fetch('/auth/runtime-config', { credentials: 'same-origin', cache: 'no-store' })
        .then(response => response.ok ? response.json() : null)
        .then(result => {
          if (anchor.isConnected) {
            const config = result?.data;
            if (config?.demo_accounts_enabled === true && ['development', 'testing'].includes(config.environment)) {
              const template = document.createElement('template');
              template.innerHTML = AuthView.render(config);
              const panel = template.content.querySelector('#auth-demo-accounts');
              if (panel) {
                anchor.replaceChildren(panel);
                AuthView.attachDemoButtons(anchor);
              }
            }
          }
        })
        .catch(() => {}); // Default render already omits demo credentials.
    }
    // Login elements
    const loginForm = document.getElementById('auth-login-form');
    const emailInput = document.getElementById('login-email');
    const passInput = document.getElementById('login-password');
    const rememberInput = document.getElementById('login-remember');
    const submitBtn = document.getElementById('login-submit-btn');
    const errorAlert = document.getElementById('auth-error-alert');
    const errorText = document.getElementById('auth-error-text');
    const togglePassBtn = document.getElementById('toggle-password-btn');
    const passEyeIcon = document.getElementById('password-eye-icon');

    // Register elements
    const registerForm = document.getElementById('auth-register-form');
    const registerNameInput = document.getElementById('register-name');
    const registerEmailInput = document.getElementById('register-email');
    const registerPassInput = document.getElementById('register-password');
    const registerConfirmPassInput = document.getElementById('register-confirm-password');
    const registerSubmitBtn = document.getElementById('register-submit-btn');
    const registerErrorAlert = document.getElementById('register-error-alert');
    const registerErrorText = document.getElementById('register-error-text');
    const toggleRegisterPassBtn = document.getElementById('toggle-register-pass-btn');
    const registerPassEyeIcon = document.getElementById('register-pass-eye-icon');

    // Caps Lock Warning Elements & Handlers
    const loginEmailWarn = document.getElementById('login-email-capslock-warning');
    const loginPassWarn = document.getElementById('login-capslock-warning');
    const regPassWarn = document.getElementById('register-capslock-warning');
    const regConfirmPassWarn = document.getElementById('register-confirm-capslock-warning');

    AuthView.setupCapsLockWarning(emailInput, loginEmailWarn);
    AuthView.setupCapsLockWarning(passInput, loginPassWarn);
    AuthView.setupCapsLockWarning(registerPassInput, regPassWarn);
    AuthView.setupCapsLockWarning(registerConfirmPassInput, regConfirmPassWarn);

    // Global keyboard listener to track Caps Lock state
    if (typeof document !== 'undefined' && !AuthView._globalKeyListening) {
      AuthView._globalKeyListening = true;
      const updateGlobal = (e) => {
        if (e && typeof e.getModifierState === 'function') {
          AuthView.isCapsLockActive = e.getModifierState('CapsLock');
        }
      };
      document.addEventListener('keydown', updateGlobal);
      document.addEventListener('keyup', updateGlobal);
    }

    // Nav buttons
    const tabNavLogin = document.getElementById('tab-nav-login');
    const tabNavRegister = document.getElementById('tab-nav-register');

    const tabPanels = {
      login: document.getElementById('auth-tab-login'),
      register: document.getElementById('auth-tab-register'),
      recovery: document.getElementById('auth-tab-recovery'),
      twofa: document.getElementById('auth-tab-twofa'),
      verificationPending: document.getElementById('auth-tab-verification-pending'),
      verifyAction: document.getElementById('auth-tab-verify-action'),
    };

    const updateNavState = (tabName) => {
      if (!tabNavLogin || !tabNavRegister) return;
      if (tabName === 'login') {
        tabNavLogin.className = 'flex-1 py-1.5 text-center rounded-lg transition-all bg-[#FFFFFF] dark:bg-[#1E1E1E] text-[#222120] dark:text-[#EDEDEB] shadow-xs cursor-pointer';
        tabNavRegister.className = 'flex-1 py-1.5 text-center rounded-lg transition-all text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer';
      } else if (tabName === 'register') {
        tabNavRegister.className = 'flex-1 py-1.5 text-center rounded-lg transition-all bg-[#FFFFFF] dark:bg-[#1E1E1E] text-[#222120] dark:text-[#EDEDEB] shadow-xs cursor-pointer';
        tabNavLogin.className = 'flex-1 py-1.5 text-center rounded-lg transition-all text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer';
      } else {
        tabNavLogin.className = 'flex-1 py-1.5 text-center rounded-lg transition-all text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer';
        tabNavRegister.className = 'flex-1 py-1.5 text-center rounded-lg transition-all text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] cursor-pointer';
      }
    };

    const switchTab = (tabName) => {
      Object.keys(tabPanels).forEach(k => {
        if (tabPanels[k]) {
          if (k === tabName) {
            tabPanels[k].classList.remove('hidden');
          } else {
            tabPanels[k].classList.add('hidden');
          }
        }
      });
      updateNavState(tabName);
      hideError();
      hideRegisterError();
    };

    if (tabNavLogin) tabNavLogin.onclick = () => switchTab('login');
    if (tabNavRegister) tabNavRegister.onclick = () => switchTab('register');

    const gotoRegisterFromLoginBtn = document.getElementById('btn-goto-register-from-login');
    if (gotoRegisterFromLoginBtn) gotoRegisterFromLoginBtn.onclick = () => switchTab('register');

    const gotoLoginFromRegBtn = document.getElementById('btn-goto-login-from-reg');
    if (gotoLoginFromRegBtn) gotoLoginFromRegBtn.onclick = () => switchTab('login');

    // Navigation triggers between Login and Recovery
    const gotoRecoveryBtn = document.getElementById('btn-goto-recovery');
    if (gotoRecoveryBtn) {
      gotoRecoveryBtn.onclick = () => switchTab('recovery');
    }

    const backToLoginBtn = document.getElementById('btn-back-to-login');
    if (backToLoginBtn) {
      backToLoginBtn.onclick = () => switchTab('login');
    }

    // Toggle password visibility - Login
    if (togglePassBtn && passInput && passEyeIcon) {
      togglePassBtn.onclick = () => {
        const isPassword = passInput.type === 'password';
        passInput.type = isPassword ? 'text' : 'password';
        passEyeIcon.textContent = isPassword ? 'visibility_off' : 'visibility';
      };
    }

    // Toggle password visibility - Register
    if (toggleRegisterPassBtn && registerPassInput && registerPassEyeIcon) {
      toggleRegisterPassBtn.onclick = () => {
        const isPassword = registerPassInput.type === 'password';
        registerPassInput.type = isPassword ? 'text' : 'password';
        registerPassEyeIcon.textContent = isPassword ? 'visibility_off' : 'visibility';
      };
    }

    // Live Password Rule Checking in Registration
    const setRuleState = (ruleElementId, isValid) => {
      const el = document.getElementById(ruleElementId);
      if (!el) return;
      const icon = el.querySelector('.material-symbols-outlined');
      if (isValid) {
        el.className = 'flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium transition-colors';
        if (icon) icon.textContent = 'check_circle';
      } else {
        el.className = 'flex items-center gap-1.5 text-[#8F8E8A] transition-colors';
        if (icon) icon.textContent = 'cancel';
      }
    };

    if (registerPassInput) {
      registerPassInput.oninput = () => {
        const val = registerPassInput.value || '';
        setRuleState('pwd-check-len', val.length >= 8);
        setRuleState('pwd-check-letter', /[A-Za-z]/.test(val));
        setRuleState('pwd-check-digit', /\d/.test(val));
        setRuleState('pwd-check-special', /[^A-Za-z0-9]/.test(val));
      };
    }

    AuthView.attachDemoButtons(document);

    const showError = (msg) => {
      if (errorAlert && errorText) {
        errorText.textContent = msg;
        errorAlert.classList.remove('hidden');
      }
    };

    const hideError = () => {
      if (errorAlert) errorAlert.classList.add('hidden');
      const unverifiedAlert = document.getElementById('login-unverified-alert');
      if (unverifiedAlert) unverifiedAlert.classList.add('hidden');
    };

    const showRegisterError = (msg) => {
      if (registerErrorAlert && registerErrorText) {
        registerErrorText.textContent = msg;
        registerErrorAlert.classList.remove('hidden');
      }
    };

    const hideRegisterError = () => {
      if (registerErrorAlert) registerErrorAlert.classList.add('hidden');
    };

    // Handle Login Form Submit
    if (loginForm) {
      loginForm.onsubmit = async (e) => {
        e.preventDefault();
        hideError();

        const email = emailInput?.value?.trim();
        const password = passInput?.value;
        const remember = rememberInput?.checked || false;

        if (!email) {
          showError('Vui lòng nhập địa chỉ email học thuật.');
          emailInput?.focus();
          return;
        }

        if (!password) {
          showError('Vui lòng nhập mật khẩu đăng nhập.');
          passInput?.focus();
          return;
        }

        // Loading state
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = `
            <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            <span>Đang xác thực...</span>
          `;
        }

        try {
          const res = await ApiClient.login(email, password, remember);

          // Check if 2FA is required
          if (res && res.two_factor_required) {
            switchTab('twofa');
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.innerHTML = `
                <span class="material-symbols-outlined text-[17px]">login</span>
                <span>Đăng nhập hệ thống</span>
              `;
            }
            return;
          }

          UI.showToast('Đăng nhập thành công! Đang chuyển hướng...', 'success');

          // Keep submit button disabled to prevent duplicate clicks while redirecting
          if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
              <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span>Đang vào hệ thống...</span>
            `;
          }

          // Instantly sync user state into AppRouter without an extra HTTP GET roundtrip
          if (window.app) {
            if (res && res.user) {
              window.app.currentUser = res.user;
              const preferredRole = (window._demoSelectedRole && res.user.role_codes && res.user.role_codes.includes(window._demoSelectedRole))
                ? window._demoSelectedRole
                : (res.user.primary_role || (res.user.role_codes && res.user.role_codes[0]) || 'STUDENT');
              window.app.currentRole = preferredRole;
              if (window.app.currentUser) {
                window.app.currentUser.active_role = preferredRole;
              }
              window._demoSelectedRole = null;
              window.app.updateUserUI();
              window.app.refreshNotificationBadge();
            } else {
              await window.app.refreshCurrentUser();
            }
            if (window.RealtimeEngine && typeof window.RealtimeEngine.reconnect === 'function') {
              window.RealtimeEngine.reconnect();
            }
            window.app.redirectToRoleHome();
          }
        } catch (err) {
          if (err.code === 'EMAIL_NOT_VERIFIED' || (err.message && err.message.includes('chưa được xác thực email'))) {
            const unverifiedAlert = document.getElementById('login-unverified-alert');
            const unverifiedText = document.getElementById('login-unverified-text');
            if (unverifiedAlert) {
              if (unverifiedText) unverifiedText.textContent = err.message || 'Tài khoản chưa được xác thực email. Vui lòng kiểm tra hộp thư hoặc bấm gửi lại.';
              unverifiedAlert.classList.remove('hidden');
              if (errorAlert) errorAlert.classList.add('hidden');
            } else {
              showError(err.message);
            }
          } else {
            showError(err.message || 'Email hoặc mật khẩu không chính xác.');
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
              <span class="material-symbols-outlined text-[17px]">login</span>
              <span>Đăng nhập hệ thống</span>
            `;
          }
        }
      };
    }

    // Handle Register Form Submit
    if (registerForm) {
      registerForm.onsubmit = async (e) => {
        e.preventDefault();
        hideRegisterError();

        const name = registerNameInput?.value?.trim();
        const email = registerEmailInput?.value?.trim();
        const password = registerPassInput?.value;
        const confirmPassword = registerConfirmPassInput?.value;

        if (!name) {
          showRegisterError('Vui lòng nhập họ và tên của bạn.');
          registerNameInput?.focus();
          return;
        }

        if (!email) {
          showRegisterError('Vui lòng nhập địa chỉ email học thuật.');
          registerEmailInput?.focus();
          return;
        }

        if (!password) {
          showRegisterError('Vui lòng nhập mật khẩu.');
          registerPassInput?.focus();
          return;
        }

        if (password.length < 8) {
          showRegisterError('Mật khẩu phải có tối thiểu 8 ký tự.');
          registerPassInput?.focus();
          return;
        }

        if (!/[A-Za-z]/.test(password)) {
          showRegisterError('Mật khẩu phải chứa ít nhất một chữ cái.');
          registerPassInput?.focus();
          return;
        }

        if (!/\d/.test(password)) {
          showRegisterError('Mật khẩu phải chứa ít nhất một chữ số.');
          registerPassInput?.focus();
          return;
        }

        if (!/[^A-Za-z0-9]/.test(password)) {
          showRegisterError('Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%^&*...).');
          registerPassInput?.focus();
          return;
        }

        if (password !== confirmPassword) {
          showRegisterError('Mật khẩu xác nhận không khớp.');
          registerConfirmPassInput?.focus();
          return;
        }

        if (registerSubmitBtn) {
          registerSubmitBtn.disabled = true;
          registerSubmitBtn.innerHTML = `
            <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            <span>Đang tạo tài khoản...</span>
          `;
        }

        try {
          const regRes = await ApiClient.register(name, email, password);
          if (regRes && regRes.requires_email_verification) {
            UI.showToast('Đăng ký thành công! Vui lòng kiểm tra email để kích hoạt.', 'success');
            const displayBox = document.getElementById('verify-pending-email-display');
            if (displayBox) displayBox.textContent = email;
            if (emailInput) emailInput.value = email;
            switchTab('verificationPending');
          } else {
            UI.showToast('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success');
            if (emailInput) emailInput.value = email;
            if (passInput) passInput.value = password;
            switchTab('login');
          }
        } catch (err) {
          showRegisterError(err.message || 'Không thể đăng ký tài khoản. Vui lòng kiểm tra lại thông tin.');
        } finally {
          if (registerSubmitBtn) {
            registerSubmitBtn.disabled = false;
            registerSubmitBtn.innerHTML = `
              <span class="material-symbols-outlined text-[17px]">how_to_reg</span>
              <span>Tạo tài khoản học viên</span>
            `;
          }
        }
      };
    }

    // Handle Recovery Submit
    const sendRecoveryBtn = document.getElementById('btn-send-recovery');
    const recoveryEmailInput = document.getElementById('recovery-email');
    if (sendRecoveryBtn) {
      sendRecoveryBtn.onclick = async () => {
        const email = recoveryEmailInput?.value?.trim();
        if (!email) {
          UI.showToast('Vui lòng nhập địa chỉ email học thuật.', 'warning');
          return;
        }
        try {
          await ApiClient.forgotPassword(email);
          UI.showToast('Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.', 'success');
          switchTab('login');
        } catch (err) {
          UI.showToast(err.message || 'Không thể gửi liên kết khôi phục.', 'error');
        }
      };
    }

    // Handle 2FA Demo Submit
    const verifyTwofaBtn = document.getElementById('btn-verify-twofa-demo');
    if (verifyTwofaBtn) {
      verifyTwofaBtn.onclick = async () => {
        UI.showToast('Xác thực 2FA thành công!', 'success');
        if (window.app) {
          await window.app.refreshCurrentUser();
          window.app.redirectToRoleHome();
        }
      };
    }

    // Wire Email Verification Handlers
    const btnLoginResend = document.getElementById('btn-login-resend-verification');
    if (btnLoginResend) {
      btnLoginResend.onclick = async () => {
        const email = emailInput?.value?.trim();
        if (!email) {
          UI.showToast('Vui lòng nhập địa chỉ email.', 'warning');
          return;
        }
        btnLoginResend.disabled = true;
        btnLoginResend.textContent = 'Đang gửi...';
        try {
          await ApiClient.resendVerification(email);
          UI.showToast('Đã gửi lại email xác thực! Vui lòng kiểm tra hộp thư.', 'success');
        } catch (e) {
          UI.showToast(e.message || 'Không thể gửi lại email xác thực.', 'error');
        } finally {
          btnLoginResend.disabled = false;
          btnLoginResend.textContent = 'Gửi lại email xác thực';
        }
      };
    }

    const btnPendingResend = document.getElementById('btn-pending-resend');
    if (btnPendingResend) {
      btnPendingResend.onclick = async () => {
        const email = document.getElementById('verify-pending-email-display')?.textContent?.trim() || registerEmailInput?.value?.trim() || emailInput?.value?.trim();
        if (!email) {
          UI.showToast('Vui lòng nhập địa chỉ email.', 'warning');
          return;
        }
        btnPendingResend.disabled = true;
        btnPendingResend.innerHTML = '<span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span><span>Đang gửi...</span>';
        try {
          await ApiClient.resendVerification(email);
          UI.showToast('Đã gửi email kích hoạt mới! Vui lòng kiểm tra hộp thư.', 'success');
        } catch (e) {
          UI.showToast(e.message || 'Không thể gửi email kích hoạt.', 'error');
        } finally {
          setTimeout(() => {
            btnPendingResend.disabled = false;
            btnPendingResend.innerHTML = '<span class="material-symbols-outlined text-[16px]">forward_to_inbox</span><span>Gửi lại email xác thực</span>';
          }, 3000);
        }
      };
    }

    const btnPendingBackLogin = document.getElementById('btn-pending-back-login');
    if (btnPendingBackLogin) {
      btnPendingBackLogin.onclick = () => switchTab('login');
    }

    const btnVerifySuccessLogin = document.getElementById('btn-verify-success-login');
    if (btnVerifySuccessLogin) {
      btnVerifySuccessLogin.onclick = () => switchTab('login');
    }

    const btnVerifyErrorLogin = document.getElementById('btn-verify-error-login');
    if (btnVerifyErrorLogin) {
      btnVerifyErrorLogin.onclick = () => switchTab('login');
    }

    const btnVerifyErrorResend = document.getElementById('btn-verify-error-resend');
    if (btnVerifyErrorResend) {
      btnVerifyErrorResend.onclick = () => switchTab('login');
    }

    // Process direct URL Hash triggers for verification
    const hash = window.location.hash || '';
    if (hash.includes('verify-email')) {
      let token = '';
      if (hash.includes('token=')) {
        const queryPart = hash.split('?')[1] || '';
        const params = new URLSearchParams(queryPart);
        token = params.get('token') || '';
      }
      if (token) {
        switchTab('verifyAction');
        const loadingBox = document.getElementById('verify-action-loading');
        const successBox = document.getElementById('verify-action-success');
        const errorBox = document.getElementById('verify-action-error');
        const errorMsg = document.getElementById('verify-action-error-msg');

        ApiClient.verifyEmail(token)
          .then(() => {
            if (loadingBox) loadingBox.classList.add('hidden');
            if (successBox) successBox.classList.remove('hidden');
            UI.showToast('Xác thực tài khoản thành công! Bạn có thể đăng nhập ngay.', 'success');
            setTimeout(() => {
              switchTab('login');
            }, 3000);
          })
          .catch(err => {
            if (loadingBox) loadingBox.classList.add('hidden');
            if (errorBox) errorBox.classList.remove('hidden');
            if (errorMsg) errorMsg.textContent = err.message || 'Liên kết xác thực không hợp lệ hoặc đã hết hạn.';
          });
      }
    } else if (hash.includes('verified=1')) {
      UI.showToast('Email đã được xác thực thành công! Vui lòng đăng nhập.', 'success');
      switchTab('login');
    } else if (hash.includes('verification_failed=1')) {
      showError('Liên kết xác thực email không hợp lệ hoặc đã hết hạn.');
      switchTab('login');
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AuthView };
}
if (typeof window !== 'undefined') {
  window.AuthView = AuthView;
}
