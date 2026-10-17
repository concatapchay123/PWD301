/** Internal HLS watermark and Anti-Tamper & Blackout Shield Guard. */

class VideoArmor {
  constructor(container, options = {}) {
    this.container = container;
    this.options = options;
    this.student = options.student || {};
    this.ip = options.ip || 'IP chưa được xác nhận';
    this.onSecurityViolation = options.onSecurityViolation || (() => {});
    this.onRestore = options.onRestore || (() => {});
    this.repositionIntervalMs = options.repositionIntervalMs || 7000;
    this.isBlackedOut = false;

    this.watermarkEl = null;
    this.blackoutEl = null;
    this.observer = null;
    this.repositionTimer = null;
    this.devtoolsCheckTimer = null;

    this._onVisibilityChange = this._onVisibilityChange.bind(this);
    this._onWindowBlur = this._onWindowBlur.bind(this);
    this._onKeyDown = this._onKeyDown.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
    this._onContextMenu = this._onContextMenu.bind(this);

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
    this._startDevtoolsDetection();
  }

  _formatWatermarkText() {
    const studentId = this.student.student_code || this.student.full_name || this.student.display_name || 'HỌC VIÊN';
    const email = this.student.email || (this.student.is_email_verified !== false ? 'Email đã xác nhận' : 'Email chưa xác thực');
    const now = new Date();
    const timeStr = now.toLocaleTimeString ? now.toLocaleTimeString('vi-VN', { hour12: false }) : now.toTimeString().slice(0, 8);
    const ipStr = this.ip || '127.0.0.1';
    return `${studentId} • ${email} • ${ipStr} • ${timeStr}`;
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
      top: '0',
      left: '0',
      width: '1px',
      height: '1px',
      overflow: 'hidden',
      display: 'block',
      visibility: 'visible',
      opacity: '0.001',
      pointerEvents: 'none',
      fontSize: '0px',
      lineHeight: '0',
      color: 'transparent',
      backgroundColor: 'transparent',
      border: 'none',
      boxShadow: 'none',
      zIndex: '1'
    });

    this.watermarkEl = el;
    this.container.appendChild(el);
  }

  reposition() {
    if (!this.watermarkEl) return;

    this._inspectMutations([]);
    this.watermarkEl.textContent = this._formatWatermarkText();

    const randomTop = Math.floor(Math.random() * 74) + 8;
    const randomLeft = Math.floor(Math.random() * 70) + 8;

    this.watermarkEl.style.top = `${randomTop}%`;
    this.watermarkEl.style.left = `${randomLeft}%`;
  }

  _startRepositioning() {
    // Disabled jumping interval to eliminate distracting floating watermark across video
    return;
  }

  _startDevtoolsDetection() {
    if (this.options.disableDevtoolsCheck) return;
    const win = (typeof window !== 'undefined') ? window : global;
    if (!win || !win.setInterval) return;

    this.devtoolsCheckTimer = win.setInterval(() => {
      this._checkDevTools();
    }, 1000);

    if (this.devtoolsCheckTimer && typeof this.devtoolsCheckTimer.unref === 'function') {
      this.devtoolsCheckTimer.unref();
    }
  }

  _checkDevTools() {
    if (this.isBlackedOut) return;
    if (this.options.silentWatermark) return;
    if (!this.container || this.container.isConnected === false) return;
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;

    const start = Date.now();
    try {
      (function() {
        debugger;
      })();
    } catch (_) {}
    const delta = Date.now() - start;
    if (delta > 100) {
      this.triggerBlackout('DEVTOOLS_DETECTED');
      return;
    }

    try {
      const win = typeof window !== 'undefined' ? window : null;
      if (win && typeof win.outerWidth === 'number' && typeof win.innerWidth === 'number') {
        const widthThreshold = win.outerWidth - win.innerWidth > 160;
        const heightThreshold = win.outerHeight - win.innerHeight > 160;
        if (widthThreshold || heightThreshold) {
          this.triggerBlackout('DEVTOOLS_DETECTED');
        }
      }
    } catch (_) {}
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
      attributeFilter: ['data-armor-guard', 'data-armor-blackout', 'style', 'class', 'hidden']
    });
  }

  _inspectMutations(mutations) {
    if (this.options.silentWatermark) return;
    if (this.isBlackedOut) return;
    if (!this.container || this.container.isConnected === false) return;
    if (this.container.closest?.('.route-render-stage[aria-hidden="true"]')) {
      this._pauseAllMedia();
      return;
    }

    // If the watermark parent element is temporarily detached (e.g. route transition or tab switch)
    if (this.container.parentElement && this.container.parentElement.isConnected === false) {
      return;
    }

    let tampered = false;

    // Check if the watermark element was forcefully removed from DOM while container is active
    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      // Gracefully re-attach if watermark was temporarily shifted or detached during DOM lifecycle
      if (this.watermarkEl && (this.container.contains?.(this.watermarkEl) || this.options.gracefulReattach)) {
        try {
          this.container.appendChild(this.watermarkEl);
        } catch (e) {
          tampered = true;
        }
      } else {
        tampered = true;
      }
    }

    let element = this.watermarkEl;
    while (element && !tampered) {
      const computed = typeof window !== 'undefined' && window.getComputedStyle ? window.getComputedStyle(element) : element.style;
      const isAnimating = Boolean(
        element.style?.animation ||
        element.style?.transition ||
        (typeof element.className === 'string' && (element.className.includes('animate-') || element.className.includes('transition'))) ||
        (computed?.animationName && computed.animationName !== 'none') ||
        (computed?.transitionProperty && computed.transitionProperty !== 'none')
      );

      if (element === this.watermarkEl) {
        // Guard against false-positive blackouts caused by sub-pixel rendering (e.g. opacity: 0.001 rounding to 0 in computedStyle)
        const isInlineZero = element.style?.opacity !== undefined && element.style.opacity !== '' && Number(element.style.opacity) === 0;
        const isComputedZero = computed?.opacity !== undefined && computed.opacity !== '' && Number(computed.opacity) === 0;
        const isLegitSubPixel = element.style?.opacity === '0.001' || Number(element.style?.opacity) === 0.001;

        if (element.hidden ||
            computed?.display === 'none' ||
            computed?.visibility === 'hidden' ||
            computed?.visibility === 'collapse' ||
            (isInlineZero) ||
            (isComputedZero && !isLegitSubPixel && !isAnimating)) {
          tampered = true;
        }
      } else {
        // Ancestor element in player container: ignore 0 opacity during CSS animations / transitions
        const isAncestorHidden = element.hidden || computed?.display === 'none' || computed?.visibility === 'hidden' || computed?.visibility === 'collapse';
        const isAncestorZeroOpacity = computed?.opacity !== undefined && computed.opacity !== '' && Number(computed.opacity) <= 0;
        if (isAncestorHidden || (isAncestorZeroOpacity && !isAnimating)) {
          tampered = true;
        }
      }
      if (element === this.container) break; // Confine DOM check to player container to avoid false positive from tab/route wrappers
      element = element.parentElement;
    }

    if (tampered) {
      this.triggerBlackout('DOM_TAMPER');
    }
  }

  _clearClipboard() {
    const nav = (typeof navigator !== 'undefined') ? navigator : null;
    if (nav && nav.clipboard && typeof nav.clipboard.writeText === 'function') {
      try {
        nav.clipboard.writeText('');
      } catch (_) {}
    }
  }

  triggerBlackout(reason = 'SECURITY_VIOLATION') {
    this._clearClipboard();
    this._pauseAllMedia();

    if (this.options.silentWatermark) {
      this.onSecurityViolation(reason, {
        student: this.student,
        timestamp: new Date().toISOString()
      });
      return;
    }
    if (this.isBlackedOut) return;
    this.isBlackedOut = true;

    const doc = (typeof document !== 'undefined') ? document : null;
    if (!doc) return;

    // Reveal the watermark prominently during blackout
    if (this.watermarkEl) {
      Object.assign(this.watermarkEl.style, {
        display: 'block',
        visibility: 'visible',
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
    sub.className = 'video-armor-reason';
    sub.style.fontSize = '14px';
    sub.style.fontWeight = '600';
    sub.style.color = '#ef4444';
    sub.style.marginBottom = '10px';

    if (reason === 'SCREEN_CAPTURE_ATTEMPT') {
      sub.textContent = 'PHÁT HIỆN THAO TÁC CHỤP / QUAY MÀN HÌNH';
    } else if (reason === 'DEVTOOLS_DETECTED') {
      sub.textContent = 'PHÁT HIỆN CÔNG CỤ DEVTOOLS / MÃ NGUỒN';
    } else if (reason === 'CONTEXT_MENU_BLOCKED') {
      sub.textContent = 'PHÁT HIỆN THAO TÁC CHUỘT PHẢI MÃ NGUỒN';
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
      color: '#f8fafc',
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

    // Restore the visible internal watermark
    if (!this.watermarkEl || this.watermarkEl.parentElement !== this.container) {
      this._createWatermark();
    } else {
      Object.assign(this.watermarkEl.style, {
        width: '1px',
        height: '1px',
        overflow: 'hidden',
        display: 'block',
        visibility: 'visible',
        opacity: '0.001',
        pointerEvents: 'none',
        fontSize: '0px',
        lineHeight: '0',
        color: 'transparent',
        backgroundColor: 'transparent',
        border: 'none',
        boxShadow: 'none',
        zIndex: '1'
      });
    }

    this.onRestore();
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
      if (this.options.globalProtection) {
        doc.addEventListener('contextmenu', this._onContextMenu);
      }
    }
    if (win && win.addEventListener) {
      win.addEventListener('blur', this._onWindowBlur);
      win.addEventListener('keydown', this._onKeyDown);
      win.addEventListener('keyup', this._onKeyUp);
    }
    if (this.container && this.container.addEventListener) {
      this.container.addEventListener('contextmenu', this._onContextMenu);
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
    if (this.options.silentWatermark) return;
    // Pause playback when focus is lost, without disruptive lockout
    this._pauseAllMedia();
  }

  _checkShortcutViolation(event) {
    if (!event) return null;
    const key = event.key || '';
    const keyCode = event.keyCode || 0;
    const ctrlOrMeta = Boolean(event.ctrlKey || event.metaKey);
    const shift = Boolean(event.shiftKey);
    const alt = Boolean(event.altKey);

    // 1. Screen Capture Shortcuts: PrintScreen, Win+Shift+S, Meta+Shift+S, Cmd+Shift+3/4/5
    if (key === 'PrintScreen' || keyCode === 44) {
      return 'SCREEN_CAPTURE_ATTEMPT';
    }
    if (shift && (event.metaKey || event.ctrlKey) && (key === 's' || key === 'S' || keyCode === 83)) {
      return 'SCREEN_CAPTURE_ATTEMPT';
    }
    if (shift && event.metaKey && (['3', '4', '5'].includes(key) || [51, 52, 53].includes(keyCode))) {
      return 'SCREEN_CAPTURE_ATTEMPT';
    }

    // 2. DevTools & View Source Shortcuts: F12, Ctrl+Shift+I/J/C, Ctrl+U, Cmd+Option+I/J/C/U
    if (key === 'F12' || keyCode === 123) {
      return 'DEVTOOLS_DETECTED';
    }
    if ((ctrlOrMeta && shift && (key === 'i' || key === 'I' || keyCode === 73)) ||
        (event.metaKey && alt && (key === 'i' || key === 'I' || keyCode === 73))) {
      return 'DEVTOOLS_DETECTED';
    }
    if ((ctrlOrMeta && shift && (key === 'j' || key === 'J' || keyCode === 74)) ||
        (event.metaKey && alt && (key === 'j' || key === 'J' || keyCode === 74))) {
      return 'DEVTOOLS_DETECTED';
    }
    if ((ctrlOrMeta && shift && (key === 'c' || key === 'C' || keyCode === 67)) ||
        (event.metaKey && alt && (key === 'c' || key === 'C' || keyCode === 67))) {
      return 'DEVTOOLS_DETECTED';
    }
    if ((ctrlOrMeta && (key === 'u' || key === 'U' || keyCode === 85)) ||
        (event.metaKey && alt && (key === 'u' || key === 'U' || keyCode === 85))) {
      return 'DEVTOOLS_DETECTED';
    }

    return null;
  }

  _handleKeySecurity(event) {
    if (!this.container || this.container.isConnected === false) return;
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;

    const violation = this._checkShortcutViolation(event);
    if (violation) {
      if (typeof event.preventDefault === 'function') event.preventDefault();
      if (typeof event.stopPropagation === 'function') event.stopPropagation();
      this._clearClipboard();
      this.triggerBlackout(violation);
    }
  }

  _onKeyDown(event) {
    this._handleKeySecurity(event);
  }

  _onKeyUp(event) {
    this._handleKeySecurity(event);
  }

  _onContextMenu(event) {
    if (!this.container || this.container.isConnected === false) return;
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;

    if (event) {
      if (typeof event.preventDefault === 'function') event.preventDefault();
      if (typeof event.stopPropagation === 'function') event.stopPropagation();
    }
    this._clearClipboard();
    this.triggerBlackout('CONTEXT_MENU_BLOCKED');
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
      if (this.options.globalProtection) {
        doc.removeEventListener('contextmenu', this._onContextMenu);
      }
    }
    if (win && win.removeEventListener) {
      win.removeEventListener('blur', this._onWindowBlur);
      win.removeEventListener('keydown', this._onKeyDown);
      win.removeEventListener('keyup', this._onKeyUp);
    }
    if (this.container && this.container.removeEventListener) {
      this.container.removeEventListener('contextmenu', this._onContextMenu);
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
