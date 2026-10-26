/**
 * PWD301 Realtime Reactive EventBus & SSE Engine
 * Connects to /api/events/stream via EventSource with resilient auto-reconnect.
 * Enables zero-F5 instant state reactivity across all roles (Student, Instructor, Admin).
 */
(function (global) {
  'use strict';

  // =========================================================================
  // 1. Reactive EventBus
  // =========================================================================
  class EventBusImpl {
    constructor() {
      this.listeners = new Map();
    }

    on(event, handler) {
      if (typeof handler !== 'function') return () => {};
      if (!this.listeners.has(event)) {
        this.listeners.set(event, new Set());
      }
      this.listeners.get(event).add(handler);

      // Return unsubscriber function
      return () => this.off(event, handler);
    }

    off(event, handler) {
      if (!this.listeners.has(event)) return;
      if (handler) {
        this.listeners.get(event).delete(handler);
      } else {
        this.listeners.delete(event);
      }
    }

    once(event, handler) {
      const wrapper = (data) => {
        this.off(event, wrapper);
        handler(data);
      };
      return this.on(event, wrapper);
    }

    emit(event, data) {
      // Direct handlers
      if (this.listeners.has(event)) {
        this.listeners.get(event).forEach((fn) => {
          try {
            fn(data);
          } catch (err) {
            console.error(`[EventBus] Error in handler for event "${event}":`, err);
          }
        });
      }

      // Wildcard handlers
      if (this.listeners.has('*')) {
        this.listeners.get('*').forEach((fn) => {
          try {
            fn(event, data);
          } catch (err) {
            console.error(`[EventBus] Error in wildcard handler for "${event}":`, err);
          }
        });
      }
    }
  }

  const EventBus = new EventBusImpl();

  // =========================================================================
  // 2. Realtime SSE Engine
  // =========================================================================
  class RealtimeEngineImpl {
    constructor() {
      this.eventSource = null;
      this.status = 'disconnected'; // 'disconnected' | 'connecting' | 'connected' | 'reconnecting'
      this.reconnectTimer = null;
      this.reconnectAttempts = 0;
      this.baseReconnectDelay = 1000;
      this.maxReconnectDelay = 15000;
      this.streamUrl = '/api/events/stream';
      this.registeredEventTypes = [
        'notification:new',
        'notification:broadcast',
        'changeset:submitted',
        'changeset:approved',
        'changeset:rejected',
        'course:created',
        'course:updated',
        'course:published',
        'course:trashed',
        'auth:concurrent_session_revoked',
        'connected',
        'ping'
      ];

      this._initDefaultSubscribers();
    }

    getAuthToken() {
      try {
        return (
          localStorage.getItem('token') ||
          localStorage.getItem('access_token') ||
          sessionStorage.getItem('token') ||
          ''
        );
      } catch (_) {
        return '';
      }
    }

    connect() {
      if (this.eventSource && (this.status === 'connected' || this.status === 'connecting')) {
        return;
      }

      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      const token = this.getAuthToken();
      const url = token ? `${this.streamUrl}?token=${encodeURIComponent(token)}` : this.streamUrl;

      this.status = 'connecting';

      try {
        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
          this.status = 'connected';
          this.reconnectAttempts = 0;
          EventBus.emit('realtime:connected', { time: Date.now() });
        };

        this.eventSource.onerror = () => {
          this._handleError();
        };

        this.eventSource.onmessage = (e) => {
          this._dispatchMessage('message', e.data);
        };

        // Register listeners for all specific SSE event types
        this.registeredEventTypes.forEach((evtType) => {
          this.eventSource.addEventListener(evtType, (e) => {
            this._dispatchMessage(evtType, e.data);
          });
        });
      } catch (err) {
        this._handleError();
      }
    }

    _handleError() {
      this.status = 'reconnecting';
      if (this.eventSource) {
        try {
          this.eventSource.close();
        } catch (_) {}
        this.eventSource = null;
      }

      this.reconnectAttempts++;
      const jitter = Math.random() * 500;
      const delay = Math.min(
        this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts) + jitter,
        this.maxReconnectDelay
      );

      if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, delay);

      EventBus.emit('realtime:reconnecting', {
        attempt: this.reconnectAttempts,
        nextDelay: delay
      });
    }

    _dispatchMessage(eventType, rawData) {
      let parsedData = rawData;
      if (typeof rawData === 'string') {
        try {
          parsedData = JSON.parse(rawData);
        } catch (_) {
          parsedData = { text: rawData };
        }
      }

      // Special event handlers
      if (eventType === 'ping') {
        EventBus.emit('realtime:ping', parsedData);
        return;
      }
      if (eventType === 'connected') {
        EventBus.emit('realtime:authenticated', parsedData);
        return;
      }

      EventBus.emit(eventType, parsedData);
    }

    disconnect() {
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      if (this.eventSource) {
        try {
          this.eventSource.close();
        } catch (_) {}
        this.eventSource = null;
      }
      this.status = 'disconnected';
      this.reconnectAttempts = 0;
      EventBus.emit('realtime:disconnected', { time: Date.now() });
    }

    reconnect() {
      this.disconnect();
      this.connect();
    }

    // =======================================================================
    // 3. Default Built-in Reactive Subscriptions
    // =======================================================================
    _initDefaultSubscribers() {
      // A0. Single Active Device Takeover (Eviction) & Polite Informational Modal (WF23)
      EventBus.on('auth:concurrent_session_revoked', (data) => {
        if (global.UI && typeof global.UI.showConcurrentSessionModal === 'function') {
          global.UI.showConcurrentSessionModal(data);
        } else if (global.app && typeof global.app.handleConcurrentSessionLogout === 'function') {
          global.app.handleConcurrentSessionLogout(data);
        } else {
          alert('Phiên làm việc trên thiết bị này đã kết thúc do tài khoản vừa được đăng nhập trên một thiết bị khác.');
          window.location.hash = '#/auth/login';
          window.location.reload();
        }
      });

      // A. Notifications (Badge Update without F5 - Streamlined, no noisy toast for routine notifications)
      EventBus.on('notification:new', (data) => {
        const isSelfBroadcast = (
          window._lastBroadcastSent &&
          Date.now() - window._lastBroadcastSent.timestamp < 10000 &&
          (window._lastBroadcastSent.title === (data.title || data.message))
        );
        const isUrgent = Boolean(
          data && (
            data.priority === 'URGENT' ||
            data.priority === 'HIGH' ||
            data.is_urgent === true ||
            data.category === 'URGENT' ||
            data.category === 'CRITICAL'
          )
        );
        // Only trigger floating toast if the notification is explicitly marked as urgent/critical
        if (!isSelfBroadcast && isUrgent && global.UI && typeof global.UI.showToast === 'function') {
          global.UI.showToast(data.title || data.message || 'Bạn có thông báo khẩn.', 'warning');
        }
        this._updateNotificationBadgeUI();
      });

      EventBus.on('notification:broadcast', (data) => {
        const isSelfBroadcast = (
          (window._lastBroadcastSent &&
           Date.now() - window._lastBroadcastSent.timestamp < 10000 &&
           (window._lastBroadcastSent.title === (data.title || data.message) ||
            window._lastBroadcastSent.body === (data.body || ''))) ||
          (data.sender_id && global.app?.currentUser?.id && String(data.sender_id) === String(global.app.currentUser.id)) ||
          (data.created_by_user_id && global.app?.currentUser?.id && String(data.created_by_user_id) === String(global.app.currentUser.id))
        );
        if (!isSelfBroadcast && global.UI && typeof global.UI.showToast === 'function') {
          global.UI.showToast(data.title || data.message || 'Thông báo từ Ban Quản Trị.', 'info');
        }
        this._updateNotificationBadgeUI();
      });

      // B. Changeset Submitted -> Admin instant reaction
      EventBus.on('changeset:submitted', (data) => {
        const cTitle = data.course_title || data.title || 'Khóa học';
        const role = localStorage.getItem('role') || localStorage.getItem('active_role') || '';

        // If user is Admin or on Admin screen, notify and update badge/table
        if (role.toUpperCase().includes('ADMIN') || window.location.hash.startsWith('#/admin')) {
          if (global.UI && typeof global.UI.showToast === 'function') {
            global.UI.showToast(`Khóa học "${cTitle}" vừa được gửi xét duyệt!`, 'info');
          }

          // Update Admin badges
          if (global.app && typeof global.app.fetchAdminPendingCounts === 'function') {
            global.app.fetchAdminPendingCounts();
          }

          // If on admin reviews page, live refresh or append to table
          if (window.location.hash.startsWith('#/admin/reviews')) {
            const tbody = document.getElementById('cr-table-pending') || document.getElementById('admin-review-queue-tbody');
            if (tbody && global.AdminView && typeof global.AdminView.renderReviews === 'function') {
              const viewport = document.getElementById('app-viewport');
              if (viewport) {
                global.AdminView.renderReviews(viewport);
              }
            }
          }
        }
      });

      // C. Changeset Approved / Rejected -> Instructor instant reaction
      EventBus.on('changeset:approved', (data) => {
        const cTitle = data.course_title || data.title || 'Khóa học';
        if (global.UI && typeof global.UI.showToast === 'function') {
          global.UI.showToast(`Đợt cập nhật khóa học "${cTitle}" đã được Quản trị viên phê duyệt!`, 'success');
        }
        this._refreshInstructorManageIfActive(data.course_id);
      });

      EventBus.on('changeset:rejected', (data) => {
        const cTitle = data.course_title || data.title || 'Khóa học';
        const reason = data.reason ? `: ${data.reason}` : '';
        if (global.UI && typeof global.UI.showToast === 'function') {
          global.UI.showToast(`Đợt cập nhật khóa học "${cTitle}" đã bị từ chối${reason}`, 'warning');
        }
        this._refreshInstructorManageIfActive(data.course_id);
      });

      // D. Course Trashed -> Remove from DOM live without F5
      EventBus.on('course:trashed', (data) => {
        const courseId = data.course_id;
        if (!courseId) return;

        // Auto remove row or card from DOM across all screens
        const targets = document.querySelectorAll(
          `[data-course-id="${courseId}"], [data-course-id="${String(courseId)}"]`
        );
        targets.forEach((el) => {
          const rowOrCard = el.closest('tr, .course-card, .unit-tree-node, [data-course-card="true"]');
          if (rowOrCard) {
            rowOrCard.style.transition = 'all 0.3s ease-out';
            rowOrCard.style.opacity = '0';
            rowOrCard.style.transform = 'scale(0.95)';
            setTimeout(() => {
              rowOrCard.remove();
              // Update count badge if present
              const activeCountEl = document.getElementById('admin-active-courses-count');
              if (activeCountEl) {
                const remainingRows = document.querySelectorAll('#admin-active-courses-tbody tr').length;
                activeCountEl.textContent = `${remainingRows} khóa học`;
              }
            }, 300);
          }
        });
      });
    }

    _updateNotificationBadgeUI() {
      if (global.app && typeof global.app.refreshNotificationBadge === 'function') {
        global.app.refreshNotificationBadge(true);
      }
      const badges = document.querySelectorAll('#topbar-notification-badge, #bell-notification-badge, #kpi-notif-count');
      badges.forEach((b) => {
        const cur = parseInt(b.textContent.trim(), 10) || 0;
        b.textContent = String(cur + 1);
        b.classList.remove('hidden');
        b.style.display = '';
      });
    }

    _refreshInstructorManageIfActive(targetCourseId) {
      const curHash = window.location.hash;
      if (curHash.startsWith('#/instructor/courses/') && curHash.includes('/manage')) {
        const m = curHash.match(/#\/instructor\/courses\/([^/]+)\/manage/);
        if (m && (!targetCourseId || String(m[1]) === String(targetCourseId))) {
          const cId = m[1];
          if (global.InstructorView && typeof global.InstructorView.refreshChangesetStatus === 'function') {
            global.InstructorView.refreshChangesetStatus(cId);
          }
        }
      }
    }
  }

  const RealtimeEngine = new RealtimeEngineImpl();

  // Export to global scope
  global.EventBus = EventBus;
  global.RealtimeEngine = RealtimeEngine;
  global.RealtimeClient = RealtimeEngine;

  // Connect when authenticated session exists
  function _tryAutoConnect() {
    const isAuthRoute = (window.location.hash || '').startsWith('#/auth');
    const hasToken = RealtimeEngine.getAuthToken();
    const hasSessionUser = window.App?.router?.currentUser || window.currentUser;
    if (!isAuthRoute && (hasToken || hasSessionUser)) {
      RealtimeEngine.connect();
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _tryAutoConnect);
    } else {
      _tryAutoConnect();
    }
  }
})(typeof window !== 'undefined' ? window : this);
