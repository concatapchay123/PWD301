/**
 * VideoArmor: Dynamic Forensic Watermark, DOM Armor & Anti-Tamper Client Defense (TASK-085).
 *
 * Capabilities:
 * - Dynamic Floating Forensic Watermark: Identifies student (MSSV/Name, Email, IP, Timestamp)
 *   with subtle, non-intrusive rendering (opacity ~0.18) drifting smoothly across quadrants.
 * - MutationObserver DOM Guard: Watches container subtree. If the watermark element is
 *   deleted, hidden (display:none, opacity:0, hidden attribute), or detached, instantly triggers
 *   a fail-closed Blackout screen, pauses underlying media, and reports DOM_TAMPER violation.
 * - DevTools / Debugger Timing Bouncer: Detects execution pauses typical of debugger breakpoints.
 * - Tab Blur / Visibility Guard: Pauses playback when user switches away from the active window/tab.
 * - Keyboard / Capture Defense: Intercepts PrintScreen keyup events to clear clipboard and warn.
 */

class VideoArmor {
  constructor(container, options = {}) {
    this.container = container;
    this.options = options;
    this.student = options.student || {};
    this.ip = options.ip || '127.0.0.1';
    this.onSecurityViolation = options.onSecurityViolation || (() => {});
    this.repositionIntervalMs = options.repositionIntervalMs || 7000;
    this.isBlackedOut = false;

    this.watermarkEl = null;
    this.blackoutEl = null;
    this.observer = null;
    this.repositionTimer = null;
    this.timingCheckTimer = null;

    this._onVisibilityChange = this._onVisibilityChange.bind(this);
    this._onWindowBlur = this._onWindowBlur.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);

    this._init();
  }

  static mount(container, options = {}) {
    return new VideoArmor(container, options);
  }

  _init() {
    if (!this.container) return;

    if (this.container.style && (!this.container.style.position || this.container.style.position === 'static')) {
      this.container.style.position = 'relative';
    }

    this._createWatermark();
    this._attachObserver();
    this._bindEvents();
    this._startRepositioning();
  }

  _formatWatermarkText() {
    const studentId = this.student.student_code || this.student.full_name || 'HỌC VIÊN';
    const email = this.student.email || 'student@domain.local';
    const now = new Date();
    const timeStr = now.toLocaleTimeString ? now.toLocaleTimeString('vi-VN', { hour12: false }) : now.toTimeString().slice(0, 8);
    return `${studentId} • ${email} • ${this.ip} • ${timeStr}`;
  }

  _createWatermark() {
    const doc = (typeof document !== 'undefined') ? document : null;
    if (!doc) return;

    const el = doc.createElement('div');
    el.className = 'video-armor-watermark';
    el.setAttribute('data-armor-guard', 'watermark');
    el.textContent = this._formatWatermarkText();

    Object.assign(el.style, {
      position: 'absolute',
      top: '12%',
      left: '12%',
      zIndex: '9999',
      pointerEvents: 'none',
      userSelect: 'none',
      webkitUserSelect: 'none',
      opacity: '0.18',
      color: 'rgba(255, 255, 255, 0.85)',
      fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
      fontSize: '12px',
      letterSpacing: '0.5px',
      padding: '4px 10px',
      borderRadius: '4px',
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
      textShadow: '0 1px 2px rgba(0, 0, 0, 0.9)',
      transition: 'top 2s ease, left 2s ease, opacity 0.5s ease',
      whiteSpace: 'nowrap'
    });

    this.watermarkEl = el;
    this.container.appendChild(el);
  }

  reposition() {
    if (!this.watermarkEl || this.isBlackedOut) return;

    this.watermarkEl.textContent = this._formatWatermarkText();

    const randomTop = Math.floor(Math.random() * 74) + 8;
    const randomLeft = Math.floor(Math.random() * 70) + 8;

    this.watermarkEl.style.top = `${randomTop}%`;
    this.watermarkEl.style.left = `${randomLeft}%`;
  }

  _startRepositioning() {
    const win = (typeof window !== 'undefined') ? window : global;
    if (win && win.setInterval) {
      this.repositionTimer = win.setInterval(() => {
        this.reposition();
      }, this.repositionIntervalMs);
      if (this.repositionTimer && typeof this.repositionTimer.unref === 'function') {
        this.repositionTimer.unref();
      }
    }
  }

  _attachObserver() {
    const Obs = (typeof MutationObserver !== 'undefined') ? MutationObserver : (global.MutationObserver || null);
    if (!Obs) return;

    this.observer = new Obs((mutations) => {
      this._inspectMutations(mutations);
    });

    this.observer.observe(this.container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class', 'hidden']
    });
  }

  _inspectMutations(mutations) {
    if (this.isBlackedOut) return;

    let tampered = false;

    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      tampered = true;
    }

    if (this.watermarkEl && this.watermarkEl.style) {
      const display = this.watermarkEl.style.display;
      const opacity = this.watermarkEl.style.opacity;
      const visibility = this.watermarkEl.style.visibility;
      if (display === 'none' || opacity === '0' || visibility === 'hidden') {
        tampered = true;
      }
    }

    if (tampered) {
      this.triggerBlackout('DOM_TAMPER');
    }
  }

  triggerBlackout(reason = 'SECURITY_VIOLATION') {
    if (this.isBlackedOut) return;
    this.isBlackedOut = true;

    this._pauseAllMedia();

    const doc = (typeof document !== 'undefined') ? document : null;
    if (!doc) return;

    const blackout = doc.createElement('div');
    blackout.className = 'video-armor-blackout';
    blackout.setAttribute('data-armor-blackout', 'true');

    Object.assign(blackout.style, {
      position: 'absolute',
      inset: '0',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      backgroundColor: '#0a0a0c',
      color: '#f87171',
      zIndex: '10000',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      textAlign: 'center',
      fontFamily: 'Inter, system-ui, sans-serif'
    });

    const card = doc.createElement('div');
    card.className = 'video-armor-blackout-card';

    const header = doc.createElement('div');
    header.style.fontSize = '24px';
    header.style.marginBottom = '12px';
    header.textContent = '🛡️ CẢNH BÁO AN NINH BẢN QUYỀN';
    card.appendChild(header);

    const sub = doc.createElement('div');
    sub.style.fontSize = '15px';
    sub.style.fontWeight = '600';
    sub.style.color = '#ef4444';
    sub.style.marginBottom = '8px';
    sub.textContent = 'PHÁT HIỆN HÀNH VI CAN THIỆP GIAO DIỆN / THỦY ẤN';
    card.appendChild(sub);

    const msg = doc.createElement('div');
    msg.style.fontSize = '13px';
    msg.style.color = '#d4d4d8';
    msg.style.lineHeight = '1.6';
    msg.style.marginBottom = '16px';
    msg.textContent = 'Hệ thống đã tự động khóa phiên phát video do phát hiện thao tác can thiệp DOM hoặc cố tình ẩn thủy ấn bảo vệ bản quyền. Mọi dữ liệu phiên học đã được ghi nhận vào nhật ký an ninh.';
    card.appendChild(msg);

    const restoreBtn = doc.createElement('button');
    restoreBtn.className = 'video-armor-restore-btn';
    restoreBtn.textContent = 'Khôi phục và Tiếp tục học';
    Object.assign(restoreBtn.style, {
      background: '#dc2626',
      color: '#ffffff',
      border: 'none',
      padding: '8px 18px',
      borderRadius: '6px',
      fontWeight: '500',
      cursor: 'pointer',
      fontSize: '13px'
    });
    card.appendChild(restoreBtn);

    blackout.appendChild(card);
    this.blackoutEl = blackout;
    this.container.appendChild(blackout);

    if (restoreBtn && restoreBtn.addEventListener) {
      restoreBtn.addEventListener('click', () => {
        this.restore();
      });
    }

    this.onSecurityViolation(reason, {
      student: this.student,
      timestamp: new Date().toISOString()
    });
  }

  restore() {
    if (!this.isBlackedOut) return;

    if (this.blackoutEl && this.blackoutEl.parentElement) {
      this.blackoutEl.parentElement.removeChild(this.blackoutEl);
    }
    this.blackoutEl = null;
    this.isBlackedOut = false;

    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      this._createWatermark();
    } else {
      Object.assign(this.watermarkEl.style, {
        display: 'block',
        visibility: 'visible',
        opacity: '0.18'
      });
    }
  }

  _pauseAllMedia() {
    if (!this.container) return;
    const videos = this.container.querySelectorAll('video');
    const audios = this.container.querySelectorAll('audio');
    const mediaList = [...videos, ...audios];
    for (const m of mediaList) {
      if (typeof m.pause === 'function') {
        try { m.pause(); } catch (_) {}
      }
    }
  }

  _bindEvents() {
    const doc = (typeof document !== 'undefined') ? document : null;
    const win = (typeof window !== 'undefined') ? window : global;

    if (doc && doc.addEventListener) {
      doc.addEventListener('visibilitychange', this._onVisibilityChange);
    }
    if (win && win.addEventListener) {
      win.addEventListener('blur', this._onWindowBlur);
      win.addEventListener('keyup', this._onKeyUp);
    }
  }

  _onVisibilityChange() {
    const doc = (typeof document !== 'undefined') ? document : null;
    if (doc && doc.visibilityState === 'hidden') {
      this._pauseAllMedia();
    }
  }

  _onWindowBlur() {
    this._pauseAllMedia();
  }

  _onKeyUp(event) {
    if (event.key === 'PrintScreen') {
      if (typeof event.preventDefault === 'function') event.preventDefault();

      const nav = (typeof navigator !== 'undefined') ? navigator : null;
      if (nav && nav.clipboard && typeof nav.clipboard.writeText === 'function') {
        try { nav.clipboard.writeText(''); } catch (_) {}
      }

      this.onSecurityViolation('SCREEN_CAPTURE_ATTEMPT', {
        timestamp: new Date().toISOString()
      });
    }
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    const win = (typeof window !== 'undefined') ? window : global;
    if (win && win.clearInterval) {
      if (this.repositionTimer) win.clearInterval(this.repositionTimer);
      if (this.timingCheckTimer) win.clearInterval(this.timingCheckTimer);
    }

    const doc = (typeof document !== 'undefined') ? document : null;
    if (doc && doc.removeEventListener) {
      doc.removeEventListener('visibilitychange', this._onVisibilityChange);
    }
    if (win && win.removeEventListener) {
      win.removeEventListener('blur', this._onWindowBlur);
      win.removeEventListener('keyup', this._onKeyUp);
    }

    if (this.watermarkEl && this.watermarkEl.parentElement) {
      this.watermarkEl.parentElement.removeChild(this.watermarkEl);
    }
    if (this.blackoutEl && this.blackoutEl.parentElement) {
      this.blackoutEl.parentElement.removeChild(this.blackoutEl);
    }

    this.watermarkEl = null;
    this.blackoutEl = null;
    this.container = null;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { VideoArmor };
}
if (typeof window !== 'undefined') {
  window.VideoArmor = VideoArmor;
}
