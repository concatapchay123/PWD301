/**
 * PWD301 LMS - Authentication & Account Lifecycle View
 * Warm Editorial Notion-like Edition: Focused Minimalist Card, Clean Typography, Zero-distraction
 */

class AuthView {
  static render() {
    return `
      <div class="min-h-full w-full flex flex-col justify-center items-center px-4 py-8 sm:py-14 bg-[#FAF9F5] dark:bg-[#191919] font-sans selection:bg-[#ECE8DF] selection:text-[#222120] dark:selection:bg-[#37352F] dark:selection:text-[#EDEDEB]">
        
        <!-- Brand Header -->
        <div class="mb-6 text-center select-none">
          <div class="w-11 h-11 mx-auto mb-2.5 rounded-xl bg-[#222120] dark:bg-[#EDEDEB] text-[#FAF9F5] dark:text-[#191919] flex items-center justify-center shadow-subtle">
            <span class="material-symbols-outlined text-[22px]">school</span>
          </div>
          <h1 class="text-xl sm:text-2xl font-bold text-[#222120] dark:text-[#EDEDEB] tracking-tight">PWD301 LMS</h1>
          <p class="text-xs text-[#8F8E8A] mt-0.5">Cổng Học tập & Khảo thí Học thuật Trực tuyến</p>
        </div>

        <div class="w-full max-w-sm">
          
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
              <p class="text-xs text-[#8F8E8A] mt-0.5">Sử dụng tài khoản học vụ định danh của bạn để tiếp tục</p>
            </div>

            <!-- Dynamic Error Alert -->
            <div id="auth-error-alert" class="hidden p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 text-xs font-medium flex items-start gap-2">
              <span class="material-symbols-outlined text-[16px] shrink-0 mt-0.5">error</span>
              <span id="auth-error-text" class="flex-1 leading-snug"></span>
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
                    placeholder="name@pwd301.local"
                    class="c-input pl-9"
                  />
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
                  Bảo mật TLS
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

            <!-- Quick Seed Demo Accounts Accordion -->
            <div class="pt-3 border-t border-[#E8E6DF] dark:border-[#2E2D2B]">
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
                    placeholder="student@example.com"
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
                  placeholder="name@pwd301.local"
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

          <!-- Footer Copyright -->
          <div class="mt-6 text-center text-[11px] text-[#8F8E8A]">
            <p>Hệ thống Học tập & Khảo thí PWD301 LMS</p>
          </div>

        </div>
      </div>
    `;
  }

  static attachEvents() {
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

    // Nav buttons
    const tabNavLogin = document.getElementById('tab-nav-login');
    const tabNavRegister = document.getElementById('tab-nav-register');

    const tabPanels = {
      login: document.getElementById('auth-tab-login'),
      register: document.getElementById('auth-tab-register'),
      recovery: document.getElementById('auth-tab-recovery'),
      twofa: document.getElementById('auth-tab-twofa'),
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

    // Seed account buttons
    document.querySelectorAll('.seed-acc-btn').forEach(btn => {
      btn.onclick = () => {
        if (emailInput) emailInput.value = btn.dataset.email || '';
        if (passInput) passInput.value = btn.dataset.pass || '';
        hideError();
        if (submitBtn) submitBtn.focus();
      };
    });

    const showError = (msg) => {
      if (errorAlert && errorText) {
        errorText.textContent = msg;
        errorAlert.classList.remove('hidden');
      }
    };

    const hideError = () => {
      if (errorAlert) errorAlert.classList.add('hidden');
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
            return;
          }

          UI.showToast('Đăng nhập thành công! Đang chuyển hướng...', 'success');

          // Refresh current user and redirect
          if (window.app) {
            await window.app.refreshCurrentUser();
            window.app.redirectToRoleHome();
          }
        } catch (err) {
          showError(err.message || 'Email hoặc mật khẩu không chính xác.');
        } finally {
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
          await ApiClient.register(name, email, password);
          UI.showToast('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success');
          if (emailInput) emailInput.value = email;
          if (passInput) passInput.value = password;
          switchTab('login');
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
  }
}

window.AuthView = AuthView;
