/**
 * PWD301 LMS - Core UI Helpers & Reusable Component System
 * Warm Editorial / Notion-like Design System - Minimalist, Academic & Focused
 * 
 * Provides:
 * - Minimal Instant Loading Indicator (UI.startMicroLoading, UI.stopMicroLoading)
 * - Declarative Component Generators: UI.button, UI.input, UI.card, UI.statCard, UI.pageHeader, UI.emptyState, UI.table
 * - Global Systems: Toast Notifications, Modals, Multi-Directional Drawers
 * - Markdown Parser, Date/Duration Formatters, Standardized Status Badges
 * - Exam Syntax Parser & Generator (ExamParser / Soạn đề thi Studio)
 * - Anti-Cheat Security Manager & Floating AI Tutor Controller
 */

class UI {
  static refreshCurrentRoute(fallback) {
    const refresh = window.app?.handleRoute;
    if (typeof refresh === 'function') return refresh.call(window.app);
    if (typeof fallback === 'function') return fallback();
  }

  // =========================================================================
  // 0. Minimal Instant Top Micro Progress Bar
  // =========================================================================
  static startMicroLoading() {
    const loader = document.getElementById('top-micro-loader');
    const bar = document.getElementById('top-micro-loader-bar');
    if (!loader || !bar) return;
    loader.classList.remove('opacity-0');
    loader.classList.add('opacity-100');
    bar.style.width = '35%';
    setTimeout(() => {
      if (bar.style.width === '35%') bar.style.width = '75%';
    }, 80);
  }

  static stopMicroLoading() {
    const loader = document.getElementById('top-micro-loader');
    const bar = document.getElementById('top-micro-loader-bar');
    if (!loader || !bar) return;
    bar.style.width = '100%';
    setTimeout(() => {
      loader.classList.remove('opacity-100');
      loader.classList.add('opacity-0');
      setTimeout(() => {
        bar.style.width = '0%';
      }, 120);
    }, 100);
  }

  // =========================================================================
  // =========================================================================
  // 1. Toast Notification System (Warm Editorial Style - Top Right & Progress Bar)
  // =========================================================================
  static showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toastId = 'toast_' + Math.random().toString(36).substring(2, 9);
    const toast = document.createElement('div');
    toast.id = toastId;

    let icon = 'info';
    let iconBadgeBg = 'bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400 border border-blue-100 dark:border-blue-900/50';
    let progressBarColor = 'bg-blue-600 dark:bg-blue-500';

    if (type === 'success') {
      icon = 'check_circle';
      iconBadgeBg = 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/50';
      progressBarColor = 'bg-emerald-600 dark:bg-emerald-500';
    } else if (type === 'error' || type === 'danger') {
      icon = 'error';
      iconBadgeBg = 'bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400 border border-rose-100 dark:border-rose-900/50';
      progressBarColor = 'bg-rose-600 dark:bg-rose-500';
    } else if (type === 'warning') {
      icon = 'warning';
      iconBadgeBg = 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-100 dark:border-amber-900/50';
      progressBarColor = 'bg-amber-600 dark:bg-amber-500';
    }

    toast.className = 'relative flex items-center gap-3 px-4 py-3 rounded-2xl border border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FFFFFF] dark:bg-[#202020] text-[#222120] dark:text-[#EDEDEB] shadow-none transition-all duration-200 transform -translate-y-3 opacity-0 text-xs font-medium select-none pointer-events-auto max-w-sm w-full overflow-hidden';
    toast.innerHTML = `
      <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${iconBadgeBg}">
        <span class="material-symbols-outlined text-[18px]">${icon}</span>
      </div>
      <div class="flex-1 min-w-0 pr-1 leading-snug break-words text-xs text-[#222120] dark:text-[#EDEDEB]">
        ${UI.escapeHtml(message)}
      </div>
      <button type="button" class="text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-[#FAF9F5] dark:hover:bg-[#262524] rounded-lg transition-colors p-1 shrink-0" onclick="UI.dismissToast('${toastId}')" title="Đóng">
        <span class="material-symbols-outlined text-[16px]">close</span>
      </button>
      <div class="absolute bottom-0 left-0 right-0 h-[2.5px] bg-[#E8E6DF]/50 dark:bg-[#2E2D2B]/50 overflow-hidden">
        <div id="${toastId}_progress" class="h-full ${progressBarColor} transition-all ease-linear" style="width: 100%;"></div>
      </div>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.remove('-translate-y-3', 'opacity-0');
      toast.classList.add('translate-y-0', 'opacity-100');

      // Animate countdown progress bar to 0%
      const progressBar = document.getElementById(`${toastId}_progress`);
      if (progressBar) {
        progressBar.style.transitionDuration = `${duration}ms`;
        requestAnimationFrame(() => {
          progressBar.style.width = '0%';
        });
      }
    });

    const timer = setTimeout(() => {
      UI.dismissToast(toastId);
    }, duration);

    toast._dismissTimer = timer;
  }

  static dismissToast(toastId) {
    const toast = document.getElementById(toastId);
    if (!toast) return;
    if (toast._dismissTimer) {
      clearTimeout(toast._dismissTimer);
      toast._dismissTimer = null;
    }
    toast.classList.remove('translate-y-0', 'opacity-100');
    toast.classList.add('-translate-y-3', 'opacity-0');
    setTimeout(() => {
      if (toast && toast.parentNode) toast.remove();
    }, 200);
  }

  // =========================================================================
  // 2. Global Modal System (Warm Editorial Style with Stack Support)
  // =========================================================================
  static _modalStack = [];

  static openModal({ title, bodyHtml, footerHtml = '', size = 'md', onClose = null, noShadow = false }) {
    const container = document.getElementById('modal-container');
    if (!container) return;

    if (!UI._modalStack) UI._modalStack = [];

    // If an existing modal is open, push it to stack and hide it temporarily
    const activeLayer = container.querySelector('.modal-layer:last-child');
    if (activeLayer) {
      activeLayer.style.display = 'none';
      UI._modalStack.push({
        element: activeLayer,
        onClose: window._modalOnClose
      });
    }

    window._modalOnClose = onClose;

    let maxWidth = 'max-w-xl';
    if (size === 'sm') maxWidth = 'max-w-md';
    if (size === 'lg') maxWidth = 'max-w-3xl';
    if (size === 'xl') maxWidth = 'max-w-5xl';
    if (size === 'full') maxWidth = 'max-w-[95vw] h-[90vh]';

    const shadowClass = noShadow ? 'shadow-none' : 'shadow-elevated';

    const modalLayer = document.createElement('div');
    modalLayer.className = 'modal-layer fixed inset-0 bg-[#222120]/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 sm:p-6';
    modalLayer.innerHTML = `
      <div class="bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl ${shadowClass} w-full ${maxWidth} max-h-[90vh] flex flex-col overflow-hidden transform transition-all modal-dialog">
        <!-- Modal Header -->
        <div class="px-5 py-3.5 border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between shrink-0 bg-[#FAF9F5] dark:bg-[#242423]">
          <h3 class="text-sm sm:text-base font-bold text-[#222120] dark:text-[#EDEDEB] flex items-center gap-2">
            ${title}
          </h3>
          <button type="button" class="p-1 rounded-md text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] transition-colors btn-modal-close" title="Đóng">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="px-5 py-4 overflow-y-auto flex-1 text-[#5C5B57] dark:text-[#9E9D99] text-xs sm:text-sm space-y-3 leading-relaxed">
          ${bodyHtml}
        </div>

        <!-- Modal Footer (Optional) -->
        ${footerHtml ? `
        <div class="px-5 py-3 bg-[#FAF9F5] dark:bg-[#242423] border-t border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-end gap-2 shrink-0">
          ${footerHtml}
        </div>
        ` : ''}
      </div>
    `;

    modalLayer.querySelector('.btn-modal-close')?.addEventListener('click', () => UI.closeModal());
    modalLayer.addEventListener('click', (e) => {
      if (e.target === modalLayer) UI.closeModal();
    });

    container.appendChild(modalLayer);
    container.classList.remove('hidden');

    const onEsc = (e) => {
      if (e.key === 'Escape') {
        UI.closeModal();
        document.removeEventListener('keydown', onEsc);
      }
    };
    document.addEventListener('keydown', onEsc);
  }

  static closeModal() {
    const container = document.getElementById('modal-container');
    if (!container) return;

    const onClose = window._modalOnClose;
    window._modalOnClose = null;
    if (typeof onClose === 'function') {
      try { onClose(); } catch (err) { console.error('Error in modal onClose:', err); }
    }

    const currentLayer = container.querySelector('.modal-layer:last-child');
    if (currentLayer) {
      currentLayer.remove();
    }

    // Check if there are stacked modals behind
    if (UI._modalStack && UI._modalStack.length > 0) {
      const prev = UI._modalStack.pop();
      if (prev && prev.element) {
        prev.element.style.display = '';
        window._modalOnClose = prev.onClose;
      }
    } else {
      container.innerHTML = '';
      container.classList.add('hidden');
    }
  }

  // =========================================================================
  // 2.1. Dedicated Modern Confirmation Dialog (macOS Clean Alert - No Shadow)
  // =========================================================================
  static confirm(title, message, confirmText = 'Xác nhận', cancelText = 'Hủy', isDanger = false) {
    return new Promise((resolve) => {
      const container = document.getElementById('modal-container');
      if (!container) {
        resolve(false);
        return;
      }

      if (!UI._modalStack) UI._modalStack = [];
      const activeLayer = container.querySelector('.modal-layer:last-child');
      if (activeLayer) {
        activeLayer.style.display = 'none';
        UI._modalStack.push({
          element: activeLayer,
          onClose: window._modalOnClose
        });
      }

      let settled = false;
      let cleanupKeyHandler = null;

      const finish = (value) => {
        if (!settled) {
          settled = true;
          if (cleanupKeyHandler) cleanupKeyHandler();
          window._modalOnClose = null;
          UI.closeModal();
          resolve(value);
        }
      };

      const btnColor = isDanger
        ? 'bg-rose-600 hover:bg-rose-700 text-white border border-rose-600'
        : 'c-btn-primary';

      const icon = isDanger ? 'warning' : 'help';
      const iconBadgeBg = isDanger
        ? 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-900/50'
        : 'bg-blue-50 dark:bg-blue-950/50 text-primary dark:text-blue-400 border border-blue-100 dark:border-blue-900/50';

      const confirmLayer = document.createElement('div');
      confirmLayer.className = 'modal-layer fixed inset-0 bg-[#222120]/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 sm:p-6';
      confirmLayer.innerHTML = `
        <div class="bg-[#FFFFFF] dark:bg-[#202020] border border-[#E8E6DF] dark:border-[#2E2D2B] rounded-2xl shadow-none w-full max-w-md p-6 flex flex-col gap-4 transform transition-all duration-150 scale-95 opacity-0" id="confirm-dialog-card">
          <!-- Header: Contextual Icon Badge & Close Action -->
          <div class="flex items-start justify-between gap-3">
            <div class="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${iconBadgeBg}">
              <span class="material-symbols-outlined text-[26px]">${icon}</span>
            </div>
            <button type="button" id="confirm-close-x-btn" class="p-1 rounded-lg text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-[#FAF9F5] dark:hover:bg-[#262524] transition-colors" title="Đóng">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>

          <!-- Content Area: Title & Visual Hierarchy -->
          <div class="space-y-1.5">
            <h3 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] leading-snug">
              ${UI.escapeHtml(title)}
            </h3>
            <div class="text-xs sm:text-sm text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed break-words">
              ${message}
            </div>
          </div>

          <!-- Footer: Balanced Pill Actions -->
          <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-[#E8E6DF]/70 dark:border-[#2E2D2B]/70 shrink-0">
            <button type="button" id="confirm-cancel-btn" class="c-btn c-btn-secondary c-btn-md rounded-xl px-4 py-2.5 text-xs font-semibold">
              ${UI.escapeHtml(cancelText)}
            </button>
            <button type="button" id="confirm-action-btn" class="c-btn ${btnColor} c-btn-md rounded-xl px-5 py-2.5 text-xs font-bold">
              ${UI.escapeHtml(confirmText)}
            </button>
          </div>
        </div>
      `;

      container.appendChild(confirmLayer);
      container.classList.remove('hidden');

      const card = confirmLayer.querySelector('#confirm-dialog-card');
      if (card) {
        requestAnimationFrame(() => {
          card.classList.remove('scale-95', 'opacity-0');
          card.classList.add('scale-100', 'opacity-100');
        });
      }

      confirmLayer.addEventListener('click', (e) => {
        if (e.target === confirmLayer) finish(false);
      });

      confirmLayer.querySelector('#confirm-close-x-btn')?.addEventListener('click', () => finish(false));
      confirmLayer.querySelector('#confirm-cancel-btn')?.addEventListener('click', () => finish(false));
      confirmLayer.querySelector('#confirm-action-btn')?.addEventListener('click', () => finish(true));

      const onKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          finish(false);
        } else if (e.key === 'Enter') {
          if (document.activeElement && document.activeElement.id === 'confirm-cancel-btn') {
            finish(false);
          } else {
            e.preventDefault();
            finish(true);
          }
        }
      };
      document.addEventListener('keydown', onKeyDown);
      cleanupKeyHandler = () => document.removeEventListener('keydown', onKeyDown);
    });
  }

  static prompt(title, message, defaultValue = '', placeholder = '', minLength = 1) {
    return new Promise((resolve) => {
      let settled = false;
      const finish = (value) => {
        if (!settled) {
          settled = true;
          window._modalOnClose = null;
          UI.closeModal();
          resolve(value);
        }
      };

      const inputId = 'prompt_input_' + Math.random().toString(36).substring(2, 7);
      const body = `
        <div class="space-y-2.5">
          <p class="text-xs text-[#5C5B57] dark:text-[#9E9D99] leading-relaxed">${UI.escapeHtml(message)}</p>
          <textarea id="${inputId}" rows="3" class="c-input resize-none text-xs" placeholder="${UI.escapeHtml(placeholder)}">${UI.escapeHtml(defaultValue)}</textarea>
        </div>
      `;
      const footer = `
        <button type="button" id="prompt-cancel-btn" class="c-btn c-btn-secondary c-btn-md">
          Hủy
        </button>
        <button type="button" id="prompt-action-btn" class="c-btn c-btn-primary c-btn-md">
          Xác nhận
        </button>
      `;

      UI.openModal({
        title,
        bodyHtml: body,
        footerHtml: footer,
        size: 'sm',
        onClose: () => {
          if (!settled) {
            settled = true;
            resolve(null);
          }
        }
      });

      const input = document.getElementById(inputId);
      if (input) {
        if (typeof input.focus === 'function') input.focus();
        if (typeof input.setSelectionRange === 'function' && typeof input.value === 'string') {
          input.setSelectionRange(input.value.length, input.value.length);
        }
      }

      document.getElementById('prompt-cancel-btn')?.addEventListener('click', () => finish(null));

      document.getElementById('prompt-action-btn')?.addEventListener('click', () => {
        const val = document.getElementById(inputId)?.value?.trim();
        if (minLength > 0 && (!val || val.length < minLength)) {
          UI.showToast(`Nội dung bắt buộc tối thiểu ${minLength} ký tự.`, 'warning');
          return;
        }
        finish(val);
      });
    });
  }

  // =========================================================================
  // 3. Multi-Directional Drawer System
  // =========================================================================
  static openDrawer({ side = 'right', title = '', bodyHtml = '', footerHtml = '', width = 'w-[440px] max-w-[95vw]', headerBadge = '', onClose = null }) {
    let backdrop = document.getElementById('app-drawer-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'app-drawer-backdrop';
      backdrop.className = 'hidden fixed inset-0 bg-[#222120]/30 backdrop-blur-xs z-50 transition-opacity duration-150';
      document.body.appendChild(backdrop);
    }
    let container = document.getElementById('app-drawer-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'app-drawer-container';
      container.className = 'hidden fixed inset-y-0 z-50 flex shadow-elevated transition-all duration-200';
      document.body.appendChild(container);
    }

    window._drawerOnClose = onClose;

    backdrop.classList.remove('hidden');
    container.classList.remove('hidden', 'left-0', 'right-0');

    const sideClass = side === 'left' ? 'left-0 border-r border-[#E8E6DF] dark:border-[#2E2D2B]' : 'right-0 border-l border-[#E8E6DF] dark:border-[#2E2D2B]';

    container.className = `fixed inset-y-0 z-50 flex flex-col bg-[#FFFFFF] dark:bg-[#202020] shadow-elevated ${sideClass} ${width}`;

    container.innerHTML = `
      <!-- Drawer Header -->
      <div class="h-14 px-5 border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between shrink-0 bg-[#FAF9F5] dark:bg-[#242423] select-none">
        <div class="flex items-center gap-2 min-w-0">
          <h3 class="font-bold text-sm text-[#222120] dark:text-[#EDEDEB] truncate">
            ${title}
          </h3>
          ${headerBadge ? `<span class="px-2 py-0.2 rounded text-[9px] font-bold bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB]">${headerBadge}</span>` : ''}
        </div>
        <button
          type="button"
          class="p-1 rounded-md text-[#8F8E8A] hover:text-[#222120] dark:hover:text-[#EDEDEB] hover:bg-[#E8E6DF] dark:hover:bg-[#2E2D2B] transition-colors"
          onclick="UI.closeDrawer()"
          title="Đóng"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <!-- Drawer Body -->
      <div class="flex-1 overflow-y-auto p-5 text-[#37352F] dark:text-[#EDEDEB] text-xs space-y-3" id="drawer-body-content">
        ${bodyHtml}
      </div>

      <!-- Drawer Footer (Optional) -->
      ${footerHtml ? `
      <div class="p-3.5 border-t border-[#E8E6DF] dark:border-[#2E2D2B] bg-[#FAF9F5] dark:bg-[#242423] shrink-0">
        ${footerHtml}
      </div>
      ` : ''}
    `;

    backdrop.onclick = () => UI.closeDrawer();

    const onEsc = (e) => {
      if (e.key === 'Escape') {
        UI.closeDrawer();
        document.removeEventListener('keydown', onEsc);
      }
    };
    document.addEventListener('keydown', onEsc);
  }

  static closeDrawer() {
    const backdrop = document.getElementById('app-drawer-backdrop');
    const container = document.getElementById('app-drawer-container');
    if (backdrop) backdrop.classList.add('hidden');
    if (container) {
      container.classList.add('hidden');
      container.innerHTML = '';
    }
    if (typeof window._drawerOnClose === 'function') {
      window._drawerOnClose();
      window._drawerOnClose = null;
    }
  }

  // =========================================================================
  // 4. Warm Editorial Component Generators
  // =========================================================================

  static button({
    text = '',
    icon = '',
    variant = 'primary', // 'primary', 'secondary', 'ghost', 'danger', 'accent'
    size = 'md',         // 'sm', 'md', 'lg'
    onClick = '',
    className = '',
    disabled = false,
    type = 'button',
    id = ''
  }) {
    const variantClass = `c-btn-${variant}`;
    const sizeClass = `c-btn-${size}`;
    const idAttr = id ? `id="${id}"` : '';
    const clickAttr = onClick ? `onclick="${onClick}"` : '';
    const disAttr = disabled ? 'disabled' : '';

    return `
      <button
        type="${type}"
        ${idAttr}
        ${clickAttr}
        ${disAttr}
        class="c-btn ${variantClass} ${sizeClass} ${className}"
      >
        ${icon ? `<span class="material-symbols-outlined text-[16px] shrink-0">${icon}</span>` : ''}
        ${text ? `<span>${text}</span>` : ''}
      </button>
    `;
  }

  static input({
    label = '',
    id = '',
    name = '',
    type = 'text',
    value = '',
    placeholder = '',
    icon = '',
    error = '',
    helperText = '',
    disabled = false,
    required = false,
    autocomplete = 'off',
    className = ''
  }) {
    const inputId = id || (name ? `input_${name}` : `input_${Math.random().toString(36).substring(2, 8)}`);
    const errorClass = error ? 'c-input-error' : '';
    const plClass = icon ? 'pl-9' : '';

    return `
      <div class="space-y-1 ${className}">
        ${label ? `
          <div class="flex items-center justify-between">
            <label for="${inputId}" class="block text-xs font-semibold text-[#5C5B57] dark:text-[#9E9D99]">
              ${label} ${required ? '<span class="text-rose-600">*</span>' : ''}
            </label>
          </div>
        ` : ''}
        <div class="relative">
          ${icon ? `
            <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#8F8E8A]">
              <span class="material-symbols-outlined text-[16px]">${icon}</span>
            </span>
          ` : ''}
          <input
            type="${type}"
            id="${inputId}"
            name="${name || inputId}"
            value="${UI.escapeHtml(value)}"
            placeholder="${UI.escapeHtml(placeholder)}"
            autocomplete="${autocomplete}"
            ${required ? 'required' : ''}
            ${disabled ? 'disabled' : ''}
            class="c-input ${plClass} ${errorClass}"
          />
        </div>
        ${error ? `<p class="text-[11px] text-rose-600 font-medium">${error}</p>` : ''}
        ${helperText && !error ? `<p class="text-[11px] text-[#8F8E8A]">${helperText}</p>` : ''}
      </div>
    `;
  }

  static card({
    title = '',
    subtitle = '',
    icon = '',
    badge = '',
    action = '',
    bodyHtml = '',
    footerHtml = '',
    className = '',
    hover = false
  }) {
    const hoverClass = hover ? 'c-card-hover' : '';

    return `
      <div class="c-card ${hoverClass} ${className} flex flex-col overflow-hidden">
        ${(title || action || icon || badge) ? `
          <div class="px-5 py-3.5 border-b border-[#E8E6DF] dark:border-[#2E2D2B] flex items-center justify-between gap-3 shrink-0 bg-[#FAF9F5]/50 dark:bg-[#242423]/50">
            <div class="flex items-center gap-2.5 min-w-0">
              ${icon ? `
                <div class="w-8 h-8 rounded-lg bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-[18px]">${icon}</span>
                </div>
              ` : ''}
              <div class="min-w-0">
                ${title ? `<h3 class="text-xs sm:text-sm font-bold text-[#222120] dark:text-[#EDEDEB] truncate">${title}</h3>` : ''}
                ${subtitle ? `<p class="text-[11px] text-[#8F8E8A] truncate">${subtitle}</p>` : ''}
              </div>
              ${badge ? badge : ''}
            </div>
            ${action ? `<div class="shrink-0">${action}</div>` : ''}
          </div>
        ` : ''}

        <div class="p-5 flex-1 text-xs sm:text-sm text-[#37352F] dark:text-[#EDEDEB]">
          ${bodyHtml}
        </div>

        ${footerHtml ? `
          <div class="px-5 py-3 bg-[#FAF9F5] dark:bg-[#242423] border-t border-[#E8E6DF] dark:border-[#2E2D2B] text-xs shrink-0">
            ${footerHtml}
          </div>
        ` : ''}
      </div>
    `;
  }

  static statCard({
    label = '',
    value = '0',
    change = '',
    changeType = 'positive',
    icon = 'analytics',
    subtext = ''
  }) {
    return `
      <div class="c-card c-card-hover p-4 flex flex-col justify-between">
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-[11px] font-bold text-[#8F8E8A] uppercase tracking-wider truncate">${label}</span>
          <div class="w-7 h-7 rounded-lg bg-[#F4F1EA] dark:bg-[#262524] text-[#222120] dark:text-[#EDEDEB] flex items-center justify-center shrink-0 border border-[#E8E6DF] dark:border-[#2E2D2B]">
            <span class="material-symbols-outlined text-[16px]">${icon}</span>
          </div>
        </div>
        <div>
          <div class="text-xl sm:text-2xl font-bold text-[#222120] dark:text-[#EDEDEB] tracking-tight">
            ${value}
          </div>
          ${(change || subtext) ? `
            <div class="mt-1.5 flex items-center gap-1.5 text-[11px]">
              ${change ? `
                <span class="inline-flex items-center gap-0.5 font-bold ${changeType === 'positive' ? 'text-emerald-700 dark:text-emerald-400' : (changeType === 'negative' ? 'text-rose-700 dark:text-rose-400' : 'text-[#8F8E8A]')}">
                  ${changeType === 'positive' ? '↑' : (changeType === 'negative' ? '↓' : '•')} ${change}
                </span>
              ` : ''}
              ${subtext ? `<span class="text-[#8F8E8A] truncate">${subtext}</span>` : ''}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  static pageHeader({
    title = '',
    subtitle = '',
    breadcrumb = '',
    primaryAction = '',
    secondaryActions = '',
    tabs = [],
    activeTab = '',
    onTabChange = ''
  }) {
    return `
      <div class="mb-5 space-y-3">
        ${breadcrumb ? `
          <div class="flex items-center gap-1 text-[11px] text-[#8F8E8A] font-medium">
            ${breadcrumb}
          </div>
        ` : ''}
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 class="text-lg sm:text-xl font-bold text-[#222120] dark:text-[#EDEDEB] tracking-tight">${title}</h1>
            ${subtitle ? `<p class="text-xs text-[#8F8E8A] mt-0.5">${subtitle}</p>` : ''}
          </div>
          ${(primaryAction || secondaryActions) ? `
            <div class="flex items-center gap-2 shrink-0 flex-wrap">
              ${secondaryActions}
              ${primaryAction}
            </div>
          ` : ''}
        </div>

        ${tabs && tabs.length > 0 ? `
          <div class="flex items-center gap-1 bg-[#F4F1EA] dark:bg-[#202020] p-1 rounded-xl border border-[#E8E6DF] dark:border-[#2E2D2B] overflow-x-auto w-max">
            ${tabs.map(tab => {
              const isActive = tab.id === activeTab;
              return `
                <button
                  type="button"
                  class="px-3 py-1.5 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-[#FFFFFF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] font-bold shadow-2xs'
                      : 'text-[#5C5B57] dark:text-[#9E9D99] hover:text-[#222120] dark:hover:text-[#EDEDEB]'
                  }"
                  ${onTabChange ? `onclick="${onTabChange}('${tab.id}')"` : ''}
                  data-tab="${tab.id}"
                >
                  ${tab.icon ? `<span class="material-symbols-outlined text-[15px] mr-1 align-middle">${tab.icon}</span>` : ''}
                  ${tab.label}
                  ${tab.count !== undefined ? `<span class="ml-1.5 px-1.5 py-0.2 rounded text-[10px] ${isActive ? 'bg-[#222120] text-white dark:bg-white dark:text-black' : 'bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#5C5B57] dark:text-[#EDEDEB]'}">${tab.count}</span>` : ''}
                </button>
              `;
            }).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }

  static emptyState({
    icon = 'inbox',
    title = 'Chưa có dữ liệu',
    description = 'Hiện tại không có mục nào để hiển thị.',
    actionText = '',
    onAction = '',
    actionIcon = 'add'
  }) {
    return `
      <div class="c-card p-10 text-center flex flex-col items-center justify-center">
        <div class="w-12 h-12 rounded-xl bg-[#F4F1EA] dark:bg-[#262524] text-[#8F8E8A] flex items-center justify-center mb-3 border border-[#E8E6DF] dark:border-[#2E2D2B]">
          <span class="material-symbols-outlined text-[24px]">${icon}</span>
        </div>
        <h4 class="text-sm font-bold text-[#222120] dark:text-[#EDEDEB]">${title}</h4>
        <p class="text-xs text-[#8F8E8A] max-w-sm mt-1 leading-relaxed">${description}</p>
        ${actionText && onAction ? `
          <div class="mt-4">
            ${UI.button({
              text: actionText,
              icon: actionIcon,
              variant: 'primary',
              size: 'md',
              onClick: onAction
            })}
          </div>
        ` : ''}
      </div>
    `;
  }

  static table({
    columns = [],
    rows = [],
    emptyText = 'Không tìm thấy dữ liệu phù hợp',
    className = ''
  }) {
    if (!rows || rows.length === 0) {
      return UI.emptyState({
        icon: 'table_chart_view',
        title: 'Bảng dữ liệu trống',
        description: emptyText
      });
    }

    return `
      <div class="c-table-wrapper ${className}">
        <table class="c-table">
          <thead>
            <tr>
              ${columns.map(col => `
                <th class="c-table-th ${col.className || ''}" ${col.width ? `style="width: ${col.width}"` : ''}>
                  ${col.label}
                </th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row, idx) => `
              <tr class="c-table-tr ${row._rowClass || ''}">
                ${columns.map(col => `
                  <td class="c-table-td ${col.cellClass || ''}">
                    ${typeof col.render === 'function' ? col.render(row, idx) : (row[col.key] !== undefined ? row[col.key] : '—')}
                  </td>
                `).join('')}
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  // =========================================================================
  // 5. Lightweight Markdown & Rich Document WYSIWYG Parser
  // =========================================================================
  static renderMarkdown(raw) {
    if (!raw) return '';

    // Strip internal storage annotations (video_url, mini_quiz, contact_info)
    let text = String(raw)
      .replace(/<!--\s*(?:video_url|mini_quiz|contact_info):[\s\S]*?-->/g, '')
      .trim();

    if (!text) return '';

    // Check if content is already rich HTML (from Word-like WYSIWYG editor)
    const isHtml = /<[a-z][\s\S]*>/i.test(text) && (
      text.includes('<p') || text.includes('<div') || text.includes('<h1') ||
      text.includes('<h2') || text.includes('<h3') || text.includes('<table') ||
      text.includes('<ul') || text.includes('<ol') || text.includes('<strong') ||
      text.includes('<em') || text.includes('<u') || text.includes('<span') ||
      text.includes('<blockquote')
    );

    if (isHtml) {
      if (typeof DOMPurify !== 'undefined') {
        return DOMPurify.sanitize(text, {
          ADD_ATTR: ['target', 'style', 'class', 'border', 'cellpadding', 'cellspacing'],
          ADD_TAGS: ['iframe', 'u', 's', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'colgroup', 'col']
        });
      }
      // Basic sanitization fallback
      return text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                 .replace(/on\w+="[^"]*"/gi, '')
                 .replace(/on\w+='[^']*'/gi, '');
    }

    // Markdown Parser
    let escaped = UI.escapeHtml(text);

    // Code blocks ```language ... ```
    escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre class="my-2 p-3 rounded-lg bg-[#222120] text-[#FAF9F5] dark:bg-[#151515] dark:text-[#EDEDEB] overflow-x-auto text-xs font-mono leading-relaxed border border-[#3E3D3A]"><code>${code.trim()}</code></pre>`;
    });

    // Inline code `...`
    escaped = escaped.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.2 rounded bg-[#ECE8DF] dark:bg-[#2E2D2B] text-[#222120] dark:text-[#EDEDEB] font-mono text-xs border border-[#E8E6DF] dark:border-[#3D3C3A]">$1</code>');

    // Headers
    escaped = escaped.replace(/^### (.*$)/gim, '<h3 class="text-xs sm:text-sm font-bold text-[#222120] dark:text-[#EDEDEB] mt-3 mb-1">$1</h3>');
    escaped = escaped.replace(/^## (.*$)/gim, '<h2 class="text-sm sm:text-base font-bold text-[#222120] dark:text-[#EDEDEB] mt-4 mb-1.5">$1</h2>');
    escaped = escaped.replace(/^# (.*$)/gim, '<h1 class="text-base sm:text-lg font-bold text-[#222120] dark:text-[#EDEDEB] mt-5 mb-2">$1</h1>');

    // Bold & Italic
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Blockquote
    escaped = escaped.replace(/^\> (.*$)/gim, '<blockquote class="border-l-2 border-[#222120] dark:border-[#EDEDEB] pl-3 py-1 my-2 text-[#5C5B57] dark:text-[#9E9D99] italic bg-[#F4F1EA] dark:bg-[#262524] rounded-r-md">$1</blockquote>');

    // Lists
    escaped = escaped.replace(/^\s*[-*]\s+(.*$)/gim, '<li class="ml-4 list-disc text-[#37352F] dark:text-[#EDEDEB] my-0.5">$1</li>');
    escaped = escaped.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<li class="ml-4 list-decimal text-[#37352F] dark:text-[#EDEDEB] my-0.5">$2</li>');

    // Horizontal rules
    escaped = escaped.replace(/^---$/gim, '<hr class="my-3 border-[#E8E6DF] dark:border-[#2E2D2B]" />');

    // Links [text](url)
    escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 hover:underline font-medium inline-flex items-center gap-0.5">$1 <span class="material-symbols-outlined text-[13px]">open_in_new</span></a>');

    // Paragraphs
    const paragraphs = escaped.split(/\n{2,}/).map(p => {
      if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<blockquote') || p.startsWith('<li') || p.startsWith('<hr')) {
        return p;
      }
      return `<p class="my-1.5 leading-relaxed">${p.replace(/\n/g, '<br/>')}</p>`;
    });

    return paragraphs.join('');
  }

  // =========================================================================
  // 6. Standardized Badges & Pills (Warm Editorial Style)
  // =========================================================================
  static statusBadge(status) {
    const s = String(status || '').toUpperCase();
    let label = s;
    let colorClass = 'bg-[#F4F1EA] text-[#5C5B57] dark:bg-[#262524] dark:text-[#9E9D99] border-[#E8E6DF] dark:border-[#2E2D2B]';

    switch (s) {
      case 'PUBLISHED':
      case 'ACTIVE':
      case 'APPROVED':
      case 'PASSED':
      case 'RELEASED':
      case 'CLEAN':
        label = s === 'PUBLISHED' ? 'Đang mở' : s === 'ACTIVE' ? 'Hoạt động' : s === 'APPROVED' ? 'Đã duyệt' : s === 'PASSED' ? 'Đạt' : s === 'CLEAN' ? 'An toàn' : 'Công bố';
        colorClass = 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';
        break;
      case 'SUBMITTED_FOR_REVIEW':
      case 'PENDING':
      case 'IN_PROGRESS':
        label = s === 'SUBMITTED_FOR_REVIEW' ? 'Chờ duyệt' : s === 'PENDING' ? 'Chờ xử lý' : 'Đang làm';
        colorClass = 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
        break;
      case 'DRAFT':
        label = 'Bản thảo';
        colorClass = 'bg-[#ECE8DF] text-[#5C5B57] border-[#E8E6DF] dark:bg-[#2E2D2B] dark:text-[#9E9D99] dark:border-[#3D3C3A]';
        break;
      case 'REJECTED':
      case 'FAILED':
      case 'SUSPENDED':
      case 'INFECTED':
      case 'TRASH':
        label = s === 'REJECTED' ? 'Bị từ chối' : s === 'FAILED' ? 'Chưa đạt' : s === 'SUSPENDED' ? 'Đã khóa' : s === 'INFECTED' ? 'Nhiễm mã độc' : 'Thùng rác';
        colorClass = 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800';
        break;
      case 'SUBMITTED':
      case 'COMPLETED':
        label = s === 'SUBMITTED' ? 'Đã nộp bài' : 'Hoàn thành';
        colorClass = 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800';
        break;
      case 'ARCHIVED':
      case 'CLOSED':
        label = s === 'ARCHIVED' ? 'Đã lưu trữ' : 'Đã đóng';
        colorClass = 'bg-[#ECE8DF] text-[#8F8E8A] border-[#E8E6DF] dark:bg-[#2E2D2B] dark:text-[#6D6C68] dark:border-[#3D3C3A]';
        break;
      default:
        break;
    }

    return `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold border ${colorClass}"><span class="w-1.5 h-1.5 rounded-full bg-current"></span>${label}</span>`;
  }

  static difficultyBadge(diff) {
    const d = String(diff || '').toUpperCase();
    if (d === 'BEGINNER') {
      return '<span class="px-2 py-0.2 rounded text-[10px] font-bold bg-sky-50 text-sky-800 dark:bg-sky-950/40 dark:text-sky-300 border border-sky-200 dark:border-sky-800">Cơ bản</span>';
    } else if (d === 'INTERMEDIATE') {
      return '<span class="px-2 py-0.2 rounded text-[10px] font-bold bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800">Trung cấp</span>';
    } else if (d === 'ADVANCED') {
      return '<span class="px-2 py-0.2 rounded text-[10px] font-bold bg-purple-50 text-purple-800 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800">Nâng cao</span>';
    }
    return `<span class="px-2 py-0.2 rounded text-[10px] font-bold bg-[#F4F1EA] text-[#5C5B57] dark:bg-[#262524] dark:text-[#9E9D99] border border-[#E8E6DF] dark:border-[#2E2D2B]">${diff || 'Khác'}</span>`;
  }

  // =========================================================================
  // 7. Formatting Helpers
  // =========================================================================
  static parseUtcDate(isoString) {
    if (!isoString) return null;
    let s = String(isoString).trim();
    if (s.includes('T') && !s.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(s)) {
      s += 'Z';
    }
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }

  static formatDate(isoString) {
    if (!isoString) return '—';
    try {
      const d = UI.parseUtcDate(isoString);
      if (!d) return isoString;
      return d.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  }

  static formatDateTime(isoString) {
    if (!isoString) return '—';
    try {
      const d = UI.parseUtcDate(isoString);
      if (!d) return isoString;
      return d.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return isoString;
    }
  }

  static formatDuration(minutes) {
    const m = parseInt(minutes, 10);
    if (isNaN(m) || m <= 0) return '0 phút';
    const hours = Math.floor(m / 60);
    const mins = m % 60;
    if (hours > 0 && mins > 0) return `${hours} giờ ${mins} phút`;
    if (hours > 0) return `${hours} giờ`;
    return `${mins} phút`;
  }

  static formatSeconds(totalSecs) {
    const sec = Math.max(0, parseInt(totalSecs, 10) || 0);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  static formatBytes(bytes) {
    const b = parseInt(bytes, 10);
    if (isNaN(b) || b <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(1024));
    return `${(b / Math.pow(1024, i)).toFixed(1)} ${units[i] || 'MB'}`;
  }

  static escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // =========================================================================
  // 8. Video URL & Embed Helpers (YouTube, Vimeo, HTML5)
  // =========================================================================
  static parseYouTubeId(url) {
    if (!url) return null;
    const str = String(url).trim();
    // Matches:
    // - youtu.be/ID
    // - youtube.com/watch?v=ID or &v=ID
    // - youtube.com/embed/ID
    // - youtube.com/v/ID
    // - youtube.com/shorts/ID
    // - youtube.com/live/ID
    // - iframe code containing youtube URL
    const regExp = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?|shorts|live)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})/;
    const match = str.match(regExp);
    if (match && match[1]) return match[1];
    if (/^[a-zA-Z0-9_-]{11}$/.test(str)) return str;
    return null;
  }

  static getYouTubeEmbedUrl(id) {
    if (!id) return '';
    return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`;
  }
}


// =========================================================================
// 8. PWD301 LMS Exam Syntax Parser & Generator (Formerly Azota, now unified)
// =========================================================================
class ExamParser {
  static parse(rawText) {
    if (!rawText || typeof rawText !== 'string') {
      return { success: false, questions: [], errors: ['Nội dung đề thi trống.'] };
    }

    const lines = rawText.split(/\r?\n/);
    const questions = [];
    const errors = [];

    let currentQ = null;
    let currentExplanation = null;
    let inExplanation = false;

    const commitQuestion = () => {
      if (currentQ) {
        if (currentExplanation) {
          currentQ.explanation = currentExplanation.trim();
        }
        if (!currentQ.question_text) {
          errors.push(`Câu ${currentQ.number}: Nội dung câu hỏi còn trống.`);
        }
        if (currentQ.choices.length < 2) {
          errors.push(`Câu ${currentQ.number}: Cần ít nhất 2 đáp án lựa chọn (A, B, C, D).`);
        }
        const correctCount = currentQ.choices.filter(c => c.is_correct).length;
        if (correctCount === 0) {
          if (currentQ.pending_correct_label) {
            const matchChoice = currentQ.choices.find(c => c.label.toUpperCase() === currentQ.pending_correct_label.toUpperCase());
            if (matchChoice) {
              matchChoice.is_correct = true;
            } else {
              errors.push(`Câu ${currentQ.number}: Chưa đánh dấu đáp án đúng (dùng dấu * trước đáp án hoặc gạch chân).`);
            }
          } else {
            errors.push(`Câu ${currentQ.number}: Chưa đánh dấu đáp án đúng (dùng dấu * trước đáp án hoặc gạch chân).`);
          }
        }
        questions.push(currentQ);
      }
      currentQ = null;
      currentExplanation = null;
      inExplanation = false;
    };

    // Check if the document uses explicit prefixes like "Câu \d+", "Bài \d+", or "Question \d+"
    const hasExplicitPrefix = lines.some(l => /^(?:Câu|Bài|Question)\s*\d+[:.]/i.test(l.trim()));

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const imageMarker = line.match(/^\[\[PWD301:IMAGE:([0-9a-f-]{36})\]\]$/i);
      if (imageMarker && currentQ) {
        currentQ.image_asset_id = imageMarker[1];
        continue;
      }

      const expMatch = line.match(/^(?:Hướng dẫn giải|Giải thích|Lời giải)[:.]\s*(.*)$/i);
      const ansMatch = line.match(/^(?:Đáp án|Đ\/A|ĐA)[:.]\s*([A-D])/i);
      const optMatch = line.match(/^(\*?\s*(?:<u>)?[A-D](?:<\/u>)?)(?:[:.)\]\s])\s*(.*)$/i);

      let qMatch = null;
      if (hasExplicitPrefix) {
        qMatch = line.match(/^(?:Câu|Bài|Question)\s*(\d+)[:.]\s*(.*)$/i);
      } else {
        const rawNumMatch = line.match(/^(\d+)[:.]\s+(.*)$/i);
        if (rawNumMatch && !optMatch && !ansMatch && !expMatch) {
          const num = parseInt(rawNumMatch[1], 10);
          // Only start a new question if no current question exists, or if current question
          // already has choices and the new number is the sequential next question
          if (!currentQ || (currentQ.choices.length >= 2 && num === currentQ.number + 1)) {
            qMatch = rawNumMatch;
          }
        }
      }

      if (qMatch && !optMatch && !ansMatch && !expMatch) {
        commitQuestion();
        const rawStem = qMatch[2] ? qMatch[2].trim() : '';
        const cleanStem = rawStem.replace(/\[!b:\$\s*([\s\S]*?)\s*\$\]/g, '$1').trim();
        currentQ = {
          number: parseInt(qMatch[1], 10),
          question_text: cleanStem || rawStem,
          stem: cleanStem || rawStem,
          choices: [],
          explanation: '',
          points: 1.0,
          type: 'MULTIPLE_CHOICE'
        };
      } else if (expMatch && currentQ) {
        inExplanation = true;
        currentExplanation = expMatch[1] ? expMatch[1].trim() : '';
      } else if (ansMatch && currentQ) {
        currentQ.pending_correct_label = ansMatch[1].toUpperCase();
      } else if (optMatch && currentQ && !inExplanation) {
        // Check for horizontal choices on the same line: e.g. "A. Đúng  B. Sai  *C. Khác"
        const inlineChoices = [...line.matchAll(/(?:^|\s+)(\*?\s*(?:<u>)?[A-D](?:<\/u>)?)(?:[:.)\]\s])\s*([^\n]*?)(?=(?:\s+[*]?\s*(?:<u>)?[A-D](?:<\/u>)?[:.)\]\s])|$)/gi)];
        if (inlineChoices.length > 1) {
          inlineChoices.forEach(match => {
            const rawPrefix = match[1].trim();
            const content = match[2] ? match[2].trim() : '';
            const isCorrect = rawPrefix.includes('*') || rawPrefix.includes('<u>') || content.includes('(đúng)') || content.includes('(chính xác)');
            const cleanLabel = rawPrefix.replace(/[^A-D]/gi, '').toUpperCase();
            currentQ.choices.push({
              label: cleanLabel || String.fromCharCode(65 + currentQ.choices.length),
              content: content,
              is_correct: isCorrect
            });
          });
        } else {
          let rawPrefix = optMatch[1].trim();
          let content = optMatch[2] ? optMatch[2].trim() : '';

          let isCorrect = false;
          if (rawPrefix.includes('*') || rawPrefix.includes('<u>') || content.includes('(đúng)') || content.includes('(chính xác)')) {
            isCorrect = true;
          }

          const cleanLabel = rawPrefix.replace(/[^A-D]/gi, '').toUpperCase();

          currentQ.choices.push({
            label: cleanLabel || String.fromCharCode(65 + currentQ.choices.length),
            content: content,
            is_correct: isCorrect
          });
        }
      } else if (currentQ) {
        if (inExplanation) {
          currentExplanation += '\n' + line;
        } else if (currentQ.choices.length > 0) {
          currentQ.choices[currentQ.choices.length - 1].content += '\n' + line;
        } else {
          const addText = line.replace(/\[!b:\$\s*([\s\S]*?)\s*\$\]/g, '$1').trim();
          currentQ.question_text += '\n' + addText;
          currentQ.stem = currentQ.question_text;
        }
      }
    }

    commitQuestion();

    return {
      success: errors.length === 0,
      questions,
      errors
    };
  }

  static parseExamRaw(rawText, totalPoints = 40.0) {
    const res = ExamParser.parse(rawText);
    const count = Math.max(res.questions.length, 1);
    const pointsPerQ = totalPoints / count;
    const questions = res.questions.map((q, idx) => {
      const isMultiple = q.choices.filter(c => c.is_correct).length > 1;
      return {
        number: q.number || (idx + 1),
        stem: q.stem || q.question_text || `Câu hỏi ${idx + 1}`,
        question_text: q.question_text || q.stem || `Câu hỏi ${idx + 1}`,
        image_asset_id: q.image_asset_id || null,
        choices: q.choices || [],
        explanation: q.explanation || '',
        points: q.points || pointsPerQ,
        question_type: isMultiple ? 'TN nhiều đáp án' : (q.type || 'Trắc nghiệm 1 đáp án'),
        bloom_level: q.bloom_level || (idx % 3 === 0 ? 'Vận dụng' : idx % 2 === 0 ? 'Thông hiểu' : 'Nhận biết')
      };
    });
    return {
      success: res.success,
      questions,
      errors: res.errors
    };
  }

  static generateRawFromQuestions(questions) {
    if (!Array.isArray(questions) || questions.length === 0) return '';
    return questions.map((q, idx) => {
      const qNum = idx + 1;
      let out = `Câu ${qNum}. ${q.stem || q.question_text}\n`;
      if (q.choices && Array.isArray(q.choices)) {
        q.choices.forEach(c => {
          const star = c.is_correct ? '*' : '';
          out += `${star}${c.label}. ${c.content}\n`;
        });
      }
      if (q.explanation) {
        out += `Lời giải: ${q.explanation}\n`;
      }
      return out;
    }).join('\n');
  }

  static generateSampleTemplate(type = 'standard') {
    if (type === 'fill') {
      return `Câu 1: Phương thức HTTP dùng để cập nhật một phần tài nguyên là ___.
A. POST
*B. PATCH
C. PUT
D. GET
Lời giải: PATCH được chuẩn hóa trong RFC 5789 để áp dụng các thay đổi cục bộ cho một tài nguyên.

Câu 2: Ràng buộc tính toàn vẹn tham chiếu trong cơ sở dữ liệu quan hệ được duy trì thông qua ___.
A. Primary Key
*B. Foreign Key
C. Unique Index
D. Check Constraint
Lời giải: Khóa ngoại (Foreign Key) đảm bảo các bản ghi con luôn tham chiếu đến khóa chính hợp lệ.`;
    }

    if (type === 'all' || type === 'rich') {
      return `Câu 1. Để một phát minh được cấp bằng sáng chế, phát minh đó phải thỏa mãn các tiêu chuẩn nào sau đây?
A. Phải là tài sản trí tuệ và do con người tạo ra
*B. Phải có tính mới, có trình độ sáng tạo và có khả năng áp dụng công nghiệp
C. Phải được phổ biến rộng rãi cho công chúng trước khi nộp đơn
*D. Không được là điều hiển nhiên đối với chuyên gia trong ngành kỹ thuật tương ứng

Câu 2. Bạn dự định tối ưu trải nghiệm sản phẩm số nhưng vẫn muốn tôn trọng quyền tự chủ của người dùng. Hành động nào sau đây đáp ứng nguyên tắc này?
A. Áp dụng AI thao túng hành vi người dùng mà không thông báo
*B. Tôn trọng quyền lựa chọn và tùy biến trải nghiệm của người dùng
*C. Tránh điều hướng người dùng vào các quyết định ngoài ý muốn của họ
D. Buộc người dùng cung cấp thông tin cá nhân ngoài phạm vi bài học

Câu 3. Trong hệ thống khuyến nghị, thuật toán Explainable AI giải quyết câu hỏi trọng tâm nào?
*A. Why? (Tại sao đưa ra gợi ý này)
B. How?
C. Who?
D. When?

Câu 4. Thuật toán mạng nơ-ron học sâu (Deep Learning) đặt ra thách thức gì đối với tính minh bạch Explainable AI?
A. Cấu trúc quá đơn giản
*B. Độ phức tạp cao dạng hộp đen (Black-box) gây khó khăn khi diễn giải trọng số
C. Không xử lý được dữ liệu văn bản
D. Tiêu tốn ít tài nguyên tính toán

Câu 5. Mã trạng thái HTTP nào đại diện cho việc tài nguyên được tạo mới thành công trên máy chủ?
A. 200 OK
*B. 201 Created
C. 204 No Content
D. 400 Bad Request
Lời giải: Mã 201 Created xác nhận tài nguyên mới tương ứng đã được khởi tạo thành công trên REST API server.`;
    }

    return ExamParser.generateSampleExamText();
  }

  static generateSampleExamText() {
    return `Câu 1: Mã trạng thái HTTP nào sau đây đại diện cho việc tài nguyên được tạo thành công trên máy chủ?
A. 200 OK
*B. 201 Created
C. 204 No Content
D. 400 Bad Request
Lời giải: Mã 201 Created thông báo yêu cầu đã thành công và một tài nguyên mới tương ứng đã được khởi tạo trên máy chủ REST API.

Câu 2: Trong hệ quản trị cơ sở dữ liệu Microsoft SQL Server, ràng buộc khóa chính (Primary Key) mặc định tự động tạo loại chỉ mục (Index) nào sau đây?
*A. Clustered Index
B. Non-Clustered Index
C. Full-Text Index
D. Columnstore Index
Lời giải: Theo kiến trúc SQL Server, Primary Key mặc định được gán thuộc tính Clustered Index trừ khi được chỉ định rõ NONCLUSTERED.

Câu 3: Giao thức mạng nào sau đây hoạt động tại tầng Ứng dụng (Application Layer) trong mô hình TCP/IP?
*A. HTTPS
B. TCP
C. IP
D. Ethernet
Lời giải: HTTPS là giao thức tầng ứng dụng, hoạt động trên nền mã hóa TLS/SSL và giao vận TCP.

Câu 4: Kỹ thuật kiểm thử phần mềm nào nhằm kiểm tra xem các chức năng đã có có bị lỗi sau khi thêm mã nguồn mới hay không?
A. Unit Testing
B. Stress Testing
*C. Regression Testing
D. Smoke Testing
Lời giải: Regression Testing (Kiểm thử hồi quy) đảm bảo các thay đổi mã nguồn mới không phá vỡ các chức năng cũ.`;
  }

  // Backwards compatibility aliases
  static generateAzotaRawFromQuestions(questions) {
    return ExamParser.generateRawFromQuestions(questions);
  }
  static generateSampleAzotaText() {
    return ExamParser.generateSampleExamText();
  }
}

// =========================================================================
// 9. Exam Anti-Cheat & Security Manager
// =========================================================================
class ExamAntiCheatManager {
  constructor({ maxViolations = 3, onViolation = null, onLimitReached = null } = {}) {
    this.maxViolations = maxViolations;
    this.violationCount = 0;
    this.onViolationCb = onViolation;
    this.onLimitReachedCb = onLimitReached;
    this.isActive = false;
    this._lastViolationTime = 0;

    this._handleVisibilityChange = this._handleVisibilityChange.bind(this);
    this._handleWindowBlur = this._handleWindowBlur.bind(this);
  }

  start() {
    this.isActive = true;
    this.violationCount = 0;
    document.addEventListener('visibilitychange', this._handleVisibilityChange);
    window.addEventListener('blur', this._handleWindowBlur);
  }

  stop() {
    this.isActive = false;
    document.removeEventListener('visibilitychange', this._handleVisibilityChange);
    window.removeEventListener('blur', this._handleWindowBlur);
  }

  _triggerViolation(reason) {
    if (!this.isActive) return;
    const now = Date.now();
    if (now - this._lastViolationTime < 1500) return;
    this._lastViolationTime = now;

    this.violationCount++;
    const remaining = Math.max(0, this.maxViolations - this.violationCount);

    if (typeof this.onViolationCb === 'function') {
      this.onViolationCb(this.violationCount, remaining, reason);
    }

    if (this.violationCount >= this.maxViolations) {
      if (typeof this.onLimitReachedCb === 'function') {
        this.onLimitReachedCb(this.violationCount);
      }
    }
  }

  _handleVisibilityChange() {
    if (document.hidden) {
      this._triggerViolation('Rời tab thi / Ẩn cửa sổ làm bài');
    }
  }

  _handleWindowBlur() {
    this._triggerViolation('Chuyển cửa sổ ứng dụng khác');
  }
}

// =========================================================================
// 10. Floating Circular AI Tutor Widget Controller (Warm Editorial Style)
// =========================================================================
class FloatingAITutor {
  static init() {
    const launcher = document.getElementById('floating-ai-launcher');
    const drawer = document.getElementById('floating-ai-drawer');
    const closeBtn = document.getElementById('floating-ai-close-btn');
    const form = document.getElementById('floating-ai-form');
    const input = document.getElementById('floating-ai-input');

    if (!launcher || !drawer || !form) return;

    launcher.onclick = () => {
      drawer.classList.toggle('hidden');
      if (!drawer.classList.contains('hidden') && input) {
        input.focus();
      }
    };

    if (closeBtn) {
      closeBtn.onclick = () => {
        drawer.classList.add('hidden');
      };
    }

    form.onsubmit = async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      FloatingAITutor.appendMessage('user', text);

      const loadingId = 'ai_load_' + Date.now();
      FloatingAITutor.appendLoadingBubble(loadingId);

      try {
        const res = await ApiClient.sendAIChat(text);
        FloatingAITutor.removeLoadingBubble(loadingId);
        const reply = res?.reply || res?.message || res?.data?.reply || 'Tôi đã tiếp nhận câu hỏi của bạn.';
        FloatingAITutor.appendMessage('ai', reply);
      } catch (err) {
        FloatingAITutor.removeLoadingBubble(loadingId);
        FloatingAITutor.appendMessage('ai', `Xin lỗi, có sự cố kết nối: ${err.message || 'Không thể liên hệ với Gemini AI.'}`);
      }
    };
  }

  static openWithQuestion(promptText) {
    const drawer = document.getElementById('floating-ai-drawer');
    const input = document.getElementById('floating-ai-input');
    const form = document.getElementById('floating-ai-form');

    if (drawer) {
      drawer.classList.remove('hidden');
    }
    if (input && form) {
      input.value = promptText;
      form.dispatchEvent(new Event('submit'));
    }
  }

  static close() {
    const drawer = document.getElementById('floating-ai-drawer');
    if (drawer) {
      drawer.classList.add('hidden');
    }
  }

  static appendMessage(sender, text) {
    const box = document.getElementById('floating-ai-messages');
    if (!box) return;

    const div = document.createElement('div');
    if (sender === 'user') {
      div.className = 'flex justify-end';
      div.innerHTML = `
        <div class="bg-[#222120] text-[#FAF9F5] dark:bg-[#EDEDEB] dark:text-[#191919] p-3 rounded-xl rounded-tr-none max-w-[85%] leading-relaxed text-xs">
          ${UI.escapeHtml(text)}
        </div>
      `;
    } else {
      div.className = 'flex gap-2.5 items-start';
      div.innerHTML = `
        <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Bạch tuộc" class="w-6 h-6 rounded-md object-cover shrink-0 border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs" />
        <div class="bg-[#F4F1EA] dark:bg-[#262524] text-[#222120] dark:text-[#EDEDEB] p-3 rounded-xl rounded-tl-none max-w-[85%] leading-relaxed text-xs border border-[#E8E6DF] dark:border-[#2E2D2B]">
          ${UI.renderMarkdown(text)}
        </div>
      `;
    }
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  static appendLoadingBubble(id) {
    const box = document.getElementById('floating-ai-messages');
    if (!box) return;

    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex gap-2.5 items-start';
    div.innerHTML = `
      <img src="/frontend/assets/img/octopus_ai_icon.png?v=2" alt="Bạch tuộc" class="w-6 h-6 rounded-md object-cover shrink-0 border border-[#E8E6DF] dark:border-[#2E2D2B] shadow-2xs animate-pulse" />
      <div class="bg-[#F4F1EA] dark:bg-[#262524] text-[#8F8E8A] p-2.5 rounded-xl rounded-tl-none text-xs flex items-center gap-1.5 border border-[#E8E6DF] dark:border-[#2E2D2B]">
        <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#222120] dark:bg-[#EDEDEB] animate-bounce"></span>
        <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#222120] dark:bg-[#EDEDEB] animate-bounce [animation-delay:0.2s]"></span>
        <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#222120] dark:bg-[#EDEDEB] animate-bounce [animation-delay:0.4s]"></span>
        <span class="ml-1">Bạch tuộc đang suy nghĩ...</span>
      </div>
    `;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  static removeLoadingBubble(id) {
    document.getElementById(id)?.remove();
  }

  // =========================================================================
  // 12. Plain-Language Academic Glossary & Low-Tech Friendly Helpers
  // =========================================================================
  static helpTooltip(tooltipText, termName = '') {
    const escapedText = UI.escapeHtml(tooltipText);
    const escapedTerm = UI.escapeHtml(termName);
    return `
      <span class="inline-flex items-center gap-1 group relative cursor-help select-none" title="${escapedText}">
        ${escapedTerm ? `<span class="underline decoration-dotted decoration-slate-400 dark:decoration-slate-500 underline-offset-2">${escapedTerm}</span>` : ''}
        <span class="material-symbols-outlined text-[15px] text-slate-400 hover:text-primary transition-colors">help</span>
      </span>
    `;
  }

  static openAcademicGlossaryModal(initialTerm = null) {
    const glossary = [
      {
        term: 'SLO (Student Learning Outcomes)',
        vnTitle: 'Chuẩn kỹ năng đầu ra của người học',
        badge: 'Học vụ & Kỹ năng',
        description: 'Bản cam kết rõ ràng về những kiến thức, kỹ năng và sản phẩm thực tế mà bạn chắc chắn sẽ tự tay làm được sau khi học xong môn học này. Giảng viên căn cứ vào chuẩn này để ra đề thi công bằng, sát thực tế.',
        example: 'Ví dụ: "Tự tay thiết kế và lập trình được website bán hàng an toàn, bảo vệ tài khoản người dùng."'
      },
      {
        term: 'ABET Criterion 3',
        vnTitle: 'Khung kiểm định chất lượng quốc tế',
        badge: 'Tiêu chuẩn quốc tế',
        description: 'Tổ chức kiểm định hàng đầu thế giới của Hoa Kỳ dành cho các chương trình đào tạo kỹ thuật - công nghệ (Computing Accreditation Commission). Khi môn học đạt chuẩn ABET, bằng cấp và kiến thức của bạn được công nhận tương đương tiêu chuẩn quốc tế.',
        example: 'Gồm các chuẩn năng lực: Phân tích vấn đề, Thiết kế giải pháp, Đạo đức nghề nghiệp, Giao tiếp kỹ thuật.'
      },
      {
        term: 'Prerequisites',
        vnTitle: 'Môn học điều kiện cần học trước',
        badge: 'Lộ trình học tập',
        description: 'Những môn học cung cấp kiến thức nền tảng mà bạn bắt buộc phải học và thi đạt trước khi đăng ký môn học này, giúp bạn tiếp thu kiến thức mới một cách thuận lợi và không bị bỡ ngỡ.',
        example: 'Ví dụ: Cần hoàn thành môn "Nhập môn Lập trình" trước khi học môn "Lập trình Web nâng cao".'
      },
      {
        term: 'Assessment',
        vnTitle: 'Đợt khảo thí & Đánh giá năng lực',
        badge: 'Kiểm tra & Thi',
        description: 'Các bài tập, bài kiểm tra trắc nghiệm, tự luận hoặc đồ án thực hành giúp bạn tự đo lường mức độ hiểu bài và tích lũy điểm số cho học phần.',
        example: 'Gồm: Bài kiểm tra thường xuyên (Quizzes), Thi giữa kỳ (Midterm), Đồ án cuối kỳ (Final Project).'
      },
      {
        term: 'Rubric',
        vnTitle: 'Tiêu chí và thang điểm chi tiết',
        badge: 'Minh bạch điểm số',
        description: 'Bảng hướng dẫn chấm điểm công khai chỉ rõ từng mức độ hoàn thành bài tập tương ứng với bao nhiêu điểm, giúp bạn biết chính xác mình cần làm gì để đạt điểm tối đa.',
        example: 'Ví dụ: Giao diện đẹp đạt 2 điểm, Code chạy đúng đạt 5 điểm, Bảo mật tốt đạt 3 điểm.'
      }
    ];

    const bodyHtml = `
      <div class="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        <div class="p-4 rounded-xl bg-primary-subtle text-primary border border-primary/20 space-y-1">
          <div class="flex items-center gap-2 font-bold text-sm">
            <span class="material-symbols-outlined text-[20px]">help</span>
            <span>Sổ tay giải thích thuật ngữ học vụ (Dành cho người học & Người mới)</span>
          </div>
          <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Hệ thống PWD301 áp dụng các tiêu chuẩn giáo dục quốc tế nhưng luôn cam kết ngôn ngữ tường minh, gần gũi nhất để bất kỳ ai (kể cả người mới bắt đầu hoặc người không chuyên công nghệ) cũng hiểu rõ quyền lợi và lộ trình học tập của mình.
          </p>
        </div>

        <div class="space-y-3">
          ${glossary.map(item => `
            <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span class="text-xs font-bold text-primary font-mono">${UI.escapeHtml(item.term)}</span>
                  <h4 class="text-sm font-extrabold text-slate-900 dark:text-white">${UI.escapeHtml(item.vnTitle)}</h4>
                </div>
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">${UI.escapeHtml(item.badge)}</span>
              </div>
              <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">${UI.escapeHtml(item.description)}</p>
              ${item.example ? `
                <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 text-[11px] text-slate-500 italic border-l-2 border-primary">
                  ${UI.escapeHtml(item.example)}
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `;

    UI.openModal({
      title: 'Sổ tay thuật ngữ học vụ & Chuẩn đầu ra',
      bodyHtml,
      footerHtml: `
        <button type="button" class="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-xl text-xs font-bold transition-all" onclick="UI.closeModal()">
          Đã hiểu rõ
        </button>
      `,
      size: 'lg'
    });
  }
}

// Global exports
window.UI = UI;
window.ExamParser = ExamParser;
window.AzotaParser = ExamParser;
window.ExamAntiCheatManager = ExamAntiCheatManager;
window.FloatingAITutor = FloatingAITutor;
