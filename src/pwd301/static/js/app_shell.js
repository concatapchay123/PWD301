/**
 * PWD301 — Master AppShell Controller
 * Integrates sidebar sync, notification dropdown, and Floating AI Study Assistant.
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  const appShell = {
    init() {
      this.initSidebarToggle();
      this.syncActiveSidebarLink();
      this.initNotificationBell();
      this.initAIChat();
      if (window.PWDMotion && typeof window.PWDMotion.init === 'function') {
        window.PWDMotion.init();
      }
    },

    // 0. Sidebar Collapse / Expand Toggle
    initSidebarToggle() {
      const topbarToggleBtn = document.getElementById('sidebar-toggle-btn');
      const footerToggleBtn = document.getElementById('sidebar-collapse-btn');
      const brandWrapper = document.querySelector('.topbar-brand-wrapper');

      if (topbarToggleBtn && !topbarToggleBtn._boundToggle) {
        topbarToggleBtn._boundToggle = true;
        topbarToggleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.toggleSidebar(e);
        });
      }

      if (footerToggleBtn && !footerToggleBtn._boundToggle) {
        footerToggleBtn._boundToggle = true;
        footerToggleBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.toggleSidebar(e);
        });
      }

      if (brandWrapper && !brandWrapper._boundToggle) {
        brandWrapper._boundToggle = true;
        brandWrapper.addEventListener('click', (e) => {
          // If the click originated from or inside the toggle button, do nothing (handled by button)
          if (e.target.closest('#sidebar-toggle-btn')) {
            return;
          }
          if (document.documentElement.classList.contains('sidebar-collapsed')) {
            e.preventDefault();
            e.stopPropagation();
            this.toggleSidebar(e);
          }
        });
      }

      // Keyboard shortcut: Ctrl + B (or Cmd + B on Mac)
      if (!this._boundKeyboard) {
        this._boundKeyboard = true;
        document.addEventListener('keydown', (e) => {
          if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
            const target = e.target;
            const isInput = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
            if (!isInput) {
              e.preventDefault();
              this.toggleSidebar(e);
            }
          }
        });
      }

      // Initialize Bootstrap Tooltips for sidebar links in collapsed state
      if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Tooltip) {
        document.querySelectorAll('.sidebar-link[title]').forEach(el => {
          try {
            new window.bootstrap.Tooltip(el, {
              placement: 'right',
              trigger: 'hover',
              fallbackPlacements: ['bottom']
            });
          } catch (err) {}
        });
      }
    },

    _lastToggleTime: 0,
    toggleSidebar(e) {
      const now = Date.now();
      if (now - (this._lastToggleTime || 0) < 200) {
        if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
        return;
      }
      this._lastToggleTime = now;
      if (e && typeof e.stopPropagation === 'function') {
        e.stopPropagation();
      }
      const isCurrentlyCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
      const nextState = !isCurrentlyCollapsed;

      if (nextState) {
        document.documentElement.classList.add('sidebar-collapsed');
        document.body.classList.add('sidebar-collapsed');
        try {
          localStorage.setItem('pwd301_sidebar_collapsed', 'true');
        } catch (err) {}
      } else {
        document.documentElement.classList.remove('sidebar-collapsed');
        document.body.classList.remove('sidebar-collapsed');
        try {
          localStorage.setItem('pwd301_sidebar_collapsed', 'false');
        } catch (err) {}
      }

      const topbarToggleBtn = document.getElementById('sidebar-toggle-btn');
      if (topbarToggleBtn) {
        topbarToggleBtn.setAttribute('aria-expanded', String(!nextState));
        topbarToggleBtn.setAttribute('title', nextState ? 'Mở rộng menu (Ctrl+B)' : 'Thu gọn menu (Ctrl+B)');
        topbarToggleBtn.setAttribute('aria-label', nextState ? 'Mở rộng menu' : 'Thu gọn menu');
      }
    },

    // 1. Highlight current sidebar link based on current path
    syncActiveSidebarLink() {
      const currentPath = window.location.pathname;
      const links = document.querySelectorAll('.sidebar-link');
      links.forEach(link => {
        const href = link.getAttribute('href');
        if (!href) return;
        if (href === currentPath || (href.length > 2 && currentPath.startsWith(href))) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    },

    // 2. Notification Popover Box
    initNotificationBell() {
      const notifBtn = document.getElementById('topbar-notif-btn');
      const dropdown = document.getElementById('notif-dropdown');
      if (!notifBtn || !dropdown) return;

      notifBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropdown.classList.toggle('d-none');
      });

      document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !notifBtn.contains(e.target)) {
          dropdown.classList.add('d-none');
        }
      });
    },

    markAllNotificationsRead(event) {
      if (event) event.preventDefault();
      fetch('/student/notifications/mark-all-read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        }
      }).then(res => res.json()).then(() => {
        const badge = document.getElementById('notif-badge');
        if (badge) badge.classList.add('d-none');
        const headerBadge = document.getElementById('notif-header-badge');
        if (headerBadge) headerBadge.textContent = '0 mới';
        const listContainer = document.getElementById('notif-list-container');
        if (listContainer) {
          listContainer.innerHTML = '<div class="p-3 text-center text-muted small">Không có thông báo mới.</div>';
        }
      }).catch(err => console.warn('Error marking notifications read:', err));
    },

    // 3. Floating AI Chatbot
    initAIChat() {
      const launcher = document.getElementById('ai-fab-launcher');
      if (launcher) {
        launcher.addEventListener('click', () => this.toggleAIChat());
      }
      const closeBtn = document.getElementById('ai-chat-close-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.closeAIChat());
      }
      const expandBtn = document.getElementById('ai-chat-expand-btn');
      if (expandBtn) {
        expandBtn.addEventListener('click', () => this.toggleExpandAIChat());
      }
      const input = document.getElementById('ai-floating-input');
      if (input) {
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.sendFloatingAIMessage();
          }
        });
      }
    },

    toggleExpandAIChat() {
      const win = document.getElementById('ai-chat-window');
      const btn = document.getElementById('ai-chat-expand-btn');
      const expandIcon = document.getElementById('ai-expand-icon');
      const compressIcon = document.getElementById('ai-compress-icon');
      if (!win) return;

      const isExpanded = win.classList.toggle('ai-expanded');
      if (btn) {
        btn.setAttribute('title', isExpanded ? 'Thu nhỏ' : 'Phóng to');
        btn.setAttribute('aria-label', isExpanded ? 'Thu nhỏ giao diện' : 'Phóng to giao diện');
      }
      if (expandIcon && compressIcon) {
        if (isExpanded) {
          expandIcon.classList.add('d-none');
          compressIcon.classList.remove('d-none');
        } else {
          expandIcon.classList.remove('d-none');
          compressIcon.classList.add('d-none');
        }
      }
      const msgContainer = document.getElementById('ai-floating-messages');
      if (msgContainer) {
        msgContainer.scrollTop = msgContainer.scrollHeight;
      }
    },

    toggleAIChat() {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      if (!win) return;
      const isHidden = win.classList.contains('d-none');
      if (isHidden) {
        if (window.PWDMotion && typeof window.PWDMotion.openAIChat === 'function') {
          window.PWDMotion.openAIChat(win);
        } else {
          win.classList.remove('d-none');
        }
        if (launcher) launcher.classList.add('active');
        const input = document.getElementById('ai-floating-input');
        if (input) setTimeout(() => input.focus(), 150);
      } else {
        if (window.PWDMotion && typeof window.PWDMotion.closeAIChat === 'function') {
          window.PWDMotion.closeAIChat(win);
        } else {
          win.classList.add('d-none');
        }
        if (launcher) launcher.classList.remove('active');
      }
    },

    openAIChat(starterQuestion = '') {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      if (!win) return;
      if (window.PWDMotion && typeof window.PWDMotion.openAIChat === 'function') {
        window.PWDMotion.openAIChat(win);
      } else {
        win.classList.remove('d-none');
      }
      if (launcher) launcher.classList.add('active');
      if (starterQuestion) {
        this.selectQuickPrompt(starterQuestion);
      } else {
        const input = document.getElementById('ai-floating-input');
        if (input) setTimeout(() => input.focus(), 150);
      }
    },

    closeAIChat() {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      if (window.PWDMotion && typeof window.PWDMotion.closeAIChat === 'function') {
        window.PWDMotion.closeAIChat(win);
      } else if (win) {
        win.classList.add('d-none');
      }
      if (launcher) launcher.classList.remove('active');
    },

    selectQuickPrompt(promptText) {
      const input = document.getElementById('ai-floating-input');
      if (input) {
        input.value = promptText;
        this.sendFloatingAIMessage();
      }
    },

    sendFloatingAIMessage() {
      const input = document.getElementById('ai-floating-input');
      const text = (input?.value || '').trim();
      if (!text) return;

      const msgContainer = document.getElementById('ai-floating-messages');
      if (!msgContainer) return;

      // 1. Append user message with real user avatar
      const win = document.getElementById('ai-chat-window');
      const userAvatar = win?.dataset?.userAvatar || window.PWD?.currentUser?.avatarUrl || '';
      const userInitials = win?.dataset?.userInitials || window.PWD?.currentUser?.initials || 'US';
      const userName = win?.dataset?.userName || window.PWD?.currentUser?.name || 'Bạn';

      let avatarInner;
      if (userAvatar) {
        avatarInner = `<img src="${escapeHtml(userAvatar)}" alt="${escapeHtml(userName)}">`;
      } else {
        avatarInner = escapeHtml(userInitials);
      }

      const userMsg = document.createElement('div');
      userMsg.className = 'ai-chat-msg ai-msg-user';
      userMsg.innerHTML = `
        <div class="ai-msg-avatar" title="${escapeHtml(userName)}">${avatarInner}</div>
        <div class="ai-msg-content">${escapeHtml(text)}</div>
      `;
      msgContainer.appendChild(userMsg);
      input.value = '';
      msgContainer.scrollTop = msgContainer.scrollHeight;

      // 2. Typing indicator
      const typingIndicator = document.createElement('div');
      typingIndicator.id = 'ai-typing-indicator';
      typingIndicator.className = 'ai-chat-msg ai-msg-bot';
      typingIndicator.innerHTML = `
        <div class="ai-msg-avatar">
          <img src="/static/img/octopus_mascot.png" alt="Bạch Tuộc AI" class="rounded-circle" width="30" height="30">
        </div>
        <div class="ai-msg-content">
          <div class="ai-typing-indicator">
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
          </div>
        </div>
      `;
      msgContainer.appendChild(typingIndicator);
      msgContainer.scrollTop = msgContainer.scrollHeight;

      // 3. Request AI response from backend
      const payload = { message: text };
      if (this._activeConversationId) {
        payload.conversation_id = this._activeConversationId;
      }

      fetch('/student/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        const ind = document.getElementById('ai-typing-indicator');
        if (ind) ind.remove();

        if (data.conversation_id) {
          this._activeConversationId = data.conversation_id;
        }

        const reply = data.reply || (data.error && data.error.message) || 'Cảm ơn câu hỏi của bạn. Hãy cùng xem lại bài học nhé!';
        const citationSource = data.course_title || data.citations;
        const citationHtml = citationSource
          ? `<div class="ai-citation-badge mt-2">🐙 <strong>Trợ lý Bạch Tuộc AI:</strong> Nguồn: ${escapeHtml(citationSource)}</div>`
          : '';
        const botMsg = document.createElement('div');
        botMsg.className = 'ai-chat-msg ai-msg-bot';
        botMsg.innerHTML = `
          <div class="ai-msg-avatar">
            <img src="/static/img/octopus_mascot.png" alt="Bạch Tuộc AI" class="rounded-circle" width="30" height="30">
          </div>
          <div class="ai-msg-content">
            <div style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(reply)}</div>
            ${citationHtml}
          </div>
        `;
        msgContainer.appendChild(botMsg);
        msgContainer.scrollTop = msgContainer.scrollHeight;
      })
      .catch(() => {
        const ind = document.getElementById('ai-typing-indicator');
        if (ind) ind.remove();

        const botMsg = document.createElement('div');
        botMsg.className = 'ai-chat-msg ai-msg-bot';
        botMsg.innerHTML = `
          <div class="ai-msg-avatar">
            <img src="/static/img/octopus_mascot.png" alt="Bạch Tuộc AI" class="rounded-circle" width="30" height="30">
          </div>
          <div class="ai-msg-content">
            <div>Chào bạn! Hiện tại kết nối AI đang bận hoặc có gián đoạn tạm thời. Bạn có thể xem lại tài liệu bài học hoặc đặt lại câu hỏi sau ít giây nhé! 🐙</div>
          </div>
        `;
        msgContainer.appendChild(botMsg);
        msgContainer.scrollTop = msgContainer.scrollHeight;
      });
    }
  };

  window.PWD.appShell = appShell;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      appShell.init();
    });
  } else {
    appShell.init();
  }
})();
