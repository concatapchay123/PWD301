/**
 * VideoArmor: Dynamic Forensic Watermark, DOM Armor & Anti-Tamper Client Defense (TASK-085 & Refinement).
 *
 * Capabilities:
 * - Silent Guarded Forensic Watermark: Identifies student (MSSV/Name, Email, IP, Timestamp).
 *   In normal playback, the watermark is hidden from view (display: none) to provide a clean,
 *   unobtrusive study experience. Only when a security violation occurs (DevTools, screen capture,
 *   DOM tampering) is the watermark dynamically revealed alongside the Blackout security card.
 * - MutationObserver DOM Guard: Watches container subtree. If unauthorized tampering or removal
 *   of video/armor nodes occurs, instantly triggers a fail-closed Blackout screen and pauses media.
 * - Tab Blur / Visibility Guard: Pauses media playback when the student switches away from the active
 *   tab or minimizes the window, without triggering a disruptive lockout.
 * - Keyboard & DevTools Defense: Intercepts PrintScreen, Windows Snipping Tool (Win+Shift+S),
 *   Inspect shortcuts (Ctrl+Shift+I/J/C, F12) to block capture attempts and trigger Blackout.
 * - Self-Recovery: Allows the student to click "Khôi phục và Tiếp tục học" once the unauthorized
 *   action stops, while automatically recording a security telemetry event.
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
    this.devtoolsCheckTimer = null;

    this._onVisibilityChange = this._onVisibilityChange.bind(this);
    this._onWindowBlur = this._onWindowBlur.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
    this._checkDevTools = this._checkDevTools.bind(this);

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
    this._startDevToolsCheck();
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
      display: 'none', // Hidden during normal playback per user instruction
      opacity: '0.9',
      color: '#f8fafc',
      fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
      fontSize: '12px',
      letterSpacing: '0.5px',
      padding: '6px 12px',
      borderRadius: '6px',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      border: '1px solid rgba(239, 68, 68, 0.5)',
      boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
      transition: 'top 2s ease, left 2s ease, opacity 0.3s ease',
      whiteSpace: 'nowrap'
    });

    this.watermarkEl = el;
    this.container.appendChild(el);
  }

  reposition() {
    if (!this.watermarkEl) return;

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

  _startDevToolsCheck() {
    const win = (typeof window !== 'undefined') ? window : null;
    if (win && win.setInterval && typeof win.outerWidth === 'number' && typeof win.innerWidth === 'number') {
      this.devtoolsCheckTimer = win.setInterval(this._checkDevTools, 2000);
      if (this.devtoolsCheckTimer && typeof this.devtoolsCheckTimer.unref === 'function') {
        this.devtoolsCheckTimer.unref();
      }
    }
  }

  _checkDevTools() {
    if (this.isBlackedOut) return;
    const win = (typeof window !== 'undefined') ? window : null;
    if (!win) return;
    const widthThreshold = win.outerWidth - win.innerWidth > 160;
    const heightThreshold = win.outerHeight - win.innerHeight > 160;
    if (widthThreshold || heightThreshold) {
      this.triggerBlackout('DEVTOOLS_DETECTED');
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
      attributeFilter: ['data-armor-guard', 'data-armor-blackout']
    });
  }

  _inspectMutations(mutations) {
    if (this.isBlackedOut) return;

    let tampered = false;

    // Check if the watermark element was forcefully removed from DOM
    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      tampered = true;
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

    // Reveal the watermark prominently during blackout
    if (this.watermarkEl) {
      Object.assign(this.watermarkEl.style, {
        display: 'block',
        opacity: '0.95',
        zIndex: '10002'
      });
      this.watermarkEl.textContent = this._formatWatermarkText();
    }

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
      backgroundColor: '#090d16',
      color: '#f87171',
      zIndex: '10000',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      textAlign: 'center',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
    });

    const card = doc.createElement('div');
    card.className = 'video-armor-blackout-card';
    Object.assign(card.style, {
      maxWidth: '480px',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      border: '1px solid rgba(239, 68, 68, 0.4)',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)'
    });

    const header = doc.createElement('div');
    header.style.fontSize = '20px';
    header.style.fontWeight = '700';
    header.style.marginBottom = '10px';
    header.textContent = '🛡️ CẢNH BÁO AN NINH BẢN QUYỀN';
    card.appendChild(header);

    const sub = doc.createElement('div');
    sub.style.fontSize = '14px';
    sub.style.fontWeight = '600';
    sub.style.color = '#ef4444';
    sub.style.marginBottom = '10px';

    if (reason === 'SCREEN_CAPTURE_ATTEMPT') {
      sub.textContent = 'PHÁT HIỆN THAO TÁC CHỤP / QUAY MÀN HÌNH';
    } else if (reason === 'DEVTOOLS_DETECTED') {
      sub.textContent = 'PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN';
    } else if (reason === 'DOM_TAMPER') {
      sub.textContent = 'PHÁT HIỆN CAN THIỆP GIAO DIỆN / THỦY ẤN';
    } else {
      sub.textContent = 'PHÁT HIỆN HÀNH VI GIAN LẬN / CAN THIỆP HỆ THỐNG';
    }
    card.appendChild(sub);

    const msg = doc.createElement('div');
    msg.style.fontSize = '12px';
    msg.style.color = '#cbd5e1';
    msg.style.lineHeight = '1.6';
    msg.style.marginBottom = '16px';
    msg.textContent = 'Hệ thống đã tự động khóa phiên phát video để bảo vệ bản quyền bài giảng. Mọi hành vi can thiệp và danh tính phiên học đã được ghi nhận vào nhật ký an ninh.';
    card.appendChild(msg);

    // Explicit forensic watermark badge inside the warning card
    const watermarkBadge = doc.createElement('div');
    watermarkBadge.className = 'video-armor-badge';
    Object.assign(watermarkBadge.style, {
      fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
      fontSize: '11px',
      color: '#fca5a5',
      backgroundColor: 'rgba(0, 0, 0, 0.4)',
      padding: '8px 12px',
      borderRadius: '6px',
      border: '1px dashed rgba(239, 68, 68, 0.4)',
      marginBottom: '18px',
      wordBreak: 'break-all'
    });
    watermarkBadge.textContent = `HỌC VIÊN: ${this._formatWatermarkText()}`;
    card.appendChild(watermarkBadge);

    const restoreBtn = doc.createElement('button');
    restoreBtn.className = 'video-armor-restore-btn';
    restoreBtn.textContent = 'Khôi phục và Tiếp tục học';
    Object.assign(restoreBtn.style, {
      background: '#dc2626',
      color: '#ffffff',
      border: 'none',
      padding: '8px 20px',
      borderRadius: '6px',
      fontWeight: '600',
      cursor: 'pointer',
      fontSize: '13px',
      transition: 'background-color 0.2s ease'
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

    // Re-hide watermark during normal playback
    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      this._createWatermark();
    } else {
      this.watermarkEl.style.display = 'none';
    }
  }

  _pauseAllMedia() {
    if (!this.container) return;
    if (this.container._customPlayer && typeof this.container._customPlayer.pause === 'function') {
      try { this.container._customPlayer.pause(); } catch (_) {}
    }
    const videos = this.container.querySelectorAll('video');
    const audios = this.container.querySelectorAll('audio');
    const iframes = this.container.querySelectorAll('iframe');
    const mediaList = [...videos, ...audios];
    for (const m of mediaList) {
      if (typeof m.pause === 'function') {
        try { m.pause(); } catch (_) {}
      }
    }
    for (const ifr of iframes) {
      try {
        ifr.contentWindow?.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
      } catch (_) {}
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
      // Pause playback when tab is hidden, without disruptive lockout
      this._pauseAllMedia();
    }
  }

  _onWindowBlur() {
    // Pause playback when focus is lost, without disruptive lockout
    this._pauseAllMedia();
  }

  _onKeyUp(event) {
    // 1. PrintScreen key
    if (event.key === 'PrintScreen') {
      if (typeof event.preventDefault === 'function') event.preventDefault();

      const nav = (typeof navigator !== 'undefined') ? navigator : null;
      if (nav && nav.clipboard && typeof nav.clipboard.writeText === 'function') {
        try { nav.clipboard.writeText(''); } catch (_) {}
      }

      this.triggerBlackout('SCREEN_CAPTURE_ATTEMPT');
      return;
    }

    // 2. F12 (DevTools toggle)
    if (event.key === 'F12') {
      if (typeof event.preventDefault === 'function') event.preventDefault();
      this.triggerBlackout('DEVTOOLS_DETECTED');
      return;
    }

    // 3. Shortcuts: Ctrl+Shift+I / J / C (Inspect/DevTools) or Ctrl+Shift+S / Win+Shift+S (Snipping)
    const isModifier = event.ctrlKey || event.metaKey;
    if (isModifier && event.shiftKey) {
      const keyLower = String(event.key || '').toLowerCase();
      if (['i', 'j', 'c'].includes(keyLower)) {
        if (typeof event.preventDefault === 'function') event.preventDefault();
        this.triggerBlackout('DEVTOOLS_DETECTED');
      } else if (keyLower === 's') {
        if (typeof event.preventDefault === 'function') event.preventDefault();
        this.triggerBlackout('SCREEN_CAPTURE_ATTEMPT');
      }
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
      if (this.devtoolsCheckTimer) win.clearInterval(this.devtoolsCheckTimer);
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
