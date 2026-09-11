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
      this.syncActiveSidebarLink();
      this.initNotificationBell();
      this.initAIChat();
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

    toggleAIChat() {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      if (!win) return;
      const isHidden = win.classList.contains('d-none');
      if (isHidden) {
        win.classList.remove('d-none');
        if (launcher) launcher.classList.add('active');
        const input = document.getElementById('ai-floating-input');
        if (input) setTimeout(() => input.focus(), 150);
      } else {
        win.classList.add('d-none');
        if (launcher) launcher.classList.remove('active');
      }
    },

    openAIChat(starterQuestion = '') {
      const win = document.getElementById('ai-chat-window');
      const launcher = document.getElementById('ai-fab-launcher');
      if (!win) return;
      win.classList.remove('d-none');
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
      if (win) win.classList.add('d-none');
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

      // 1. Append user message
      const userMsg = document.createElement('div');
      userMsg.className = 'ai-chat-msg ai-msg-user';
      userMsg.innerHTML = `
        <div class="ai-msg-avatar">HV</div>
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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.912 5.885L20 10.8l-4.756 3.662L16.824 20 12 16.326 7.176 20l1.58-5.538L4 10.8l6.088-1.915L12 3z"></path></svg>
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
      fetch('/student/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ message: text })
      })
      .then(res => res.json())
      .then(data => {
        const ind = document.getElementById('ai-typing-indicator');
        if (ind) ind.remove();

        const reply = data.reply || (data.error && data.error.message) || 'Cảm ơn câu hỏi của bạn. Hãy cùng xem lại bài học nhé!';
        const botMsg = document.createElement('div');
        botMsg.className = 'ai-chat-msg ai-msg-bot';
        botMsg.innerHTML = `
          <div class="ai-msg-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.912 5.885L20 10.8l-4.756 3.662L16.824 20 12 16.326 7.176 20l1.58-5.538L4 10.8l6.088-1.915L12 3z"></path></svg>
          </div>
          <div class="ai-msg-content">
            <div>${escapeHtml(reply)}</div>
            <div class="ai-citation-badge mt-2">📖 <strong>Nguồn:</strong> Giáo trình trực tuyến PWD301</div>
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
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.912 5.885L20 10.8l-4.756 3.662L16.824 20 12 16.326 7.176 20l1.58-5.538L4 10.8l6.088-1.915L12 3z"></path></svg>
          </div>
          <div class="ai-msg-content">
            <div>Chào bạn! Trong môn PWD301, bạn có thể tham khảo mục tài liệu và bài giảng của từng bài học để nắm vững khái niệm này nhé.</div>
            <div class="ai-citation-badge mt-2">📖 <strong>Nguồn:</strong> Giáo trình môn học PWD301</div>
          </div>
        `;
        msgContainer.appendChild(botMsg);
        msgContainer.scrollTop = msgContainer.scrollHeight;
      });
    }
  };

  window.PWD.appShell = appShell;

  document.addEventListener('DOMContentLoaded', () => {
    appShell.init();
  });
})();
