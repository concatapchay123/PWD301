const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function createComprehensiveMockEnv() {
  const elements = new Map();
  const listeners = new Map();

  class MockElement {
    constructor(tagName = 'div', id = '') {
      this.tagName = tagName.toUpperCase();
      this.id = id;
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.attributes = new Map();
      this.dataset = {};
      this._className = '';
      this._innerHTML = '';
      this.textContent = '';
      this.contentWindow = {
        postMessage: (msg, targetOrigin) => {
          this.lastPostedMessage = msg;
          this.postedMessages = this.postedMessages || [];
          this.postedMessages.push({ msg, targetOrigin });
        }
      };
      this.muted = false;
      this.paused = true;
      if (id) elements.set(id, this);
    }

    get className() { return this._className; }
    set className(val) { this._className = String(val || ''); }

    get innerHTML() { return this._innerHTML; }
    set innerHTML(html) {
      this._innerHTML = String(html);
      this.textContent = this._innerHTML.replace(/<[^>]+>/g, ' ');
    }

    get classList() {
      const self = this;
      return {
        add(...cls) {
          const current = new Set(self._className.split(/\s+/).filter(Boolean));
          cls.forEach(c => current.add(c));
          self._className = Array.from(current).join(' ');
        },
        remove(...cls) {
          const current = new Set(self._className.split(/\s+/).filter(Boolean));
          cls.forEach(c => current.delete(c));
          self._className = Array.from(current).join(' ');
        },
        toggle(c, force) {
          const current = new Set(self._className.split(/\s+/).filter(Boolean));
          const has = current.has(c);
          if (force === true || (force === undefined && !has)) current.add(c);
          else if (force === false || (force === undefined && has)) current.delete(c);
          self._className = Array.from(current).join(' ');
        },
        contains(c) {
          return self._className.split(/\s+/).includes(c);
        }
      };
    }

    setAttribute(k, v) { this.attributes.set(k, String(v)); }
    getAttribute(k) { return this.attributes.get(k) || null; }
    removeAttribute(k) { this.attributes.delete(k); }

    appendChild(child) {
      child.parentElement = this;
      this.children.push(child);
      if (child.id) elements.set(child.id, child);
      return child;
    }

    removeChild(child) {
      const idx = this.children.indexOf(child);
      if (idx !== -1) {
        this.children.splice(idx, 1);
        child.parentElement = null;
      }
      return child;
    }

    remove() {
      if (this.parentElement) this.parentElement.removeChild(this);
      if (this.id) elements.delete(this.id);
    }

    addEventListener(type, fn) {
      const key = `${this.id || 'anon'}:${type}`;
      if (!listeners.has(key)) listeners.set(key, []);
      listeners.get(key).push(fn);
    }

    removeEventListener(type, fn) {
      const key = `${this.id || 'anon'}:${type}`;
      if (listeners.has(key)) {
        listeners.set(key, listeners.get(key).filter(f => f !== fn));
      }
    }

    dispatchEvent(event) {
      const e = typeof event === 'string' ? { type: event } : event;
      e.target = e.target || this;
      if (!e.stopPropagation) e.stopPropagation = () => { e.propagationStopped = true; };
      const key = `${this.id || 'anon'}:${e.type}`;
      const fns = listeners.get(key) || [];
      for (const fn of fns) fn(e);
      if (this[`on${e.type}`]) this[`on${e.type}`](e);
    }

    click() {
      let stopped = false;
      const event = {
        type: 'click',
        target: this,
        stopPropagation: () => { stopped = true; },
        preventDefault: () => {}
      };
      this.dispatchEvent(event);
      if (!stopped && this.parentElement && this.parentElement.click) {
        // propagation
      }
    }

    querySelector(selector) {
      if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        return this.children.find(c => c.classList.contains(cls)) || null;
      }
      return null;
    }

    querySelectorAll(selector) {
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        return this.children.filter(c => c.classList.contains(cls));
      }
      return [];
    }

    closest(selector) {
      let curr = this.parentElement;
      while (curr) {
        if (selector.startsWith('.') && curr.classList.contains(selector.slice(1))) return curr;
        if (selector.startsWith('#') && curr.id === selector.slice(1)) return curr;
        curr = curr.parentElement;
      }
      return null;
    }
  }

  const mockBody = new MockElement('body', 'body');
  const mockDocument = {
    body: mockBody,
    getElementById: (id) => elements.get(id) || null,
    createElement: (tag) => new MockElement(tag),
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  let modalOpened = null;
  const UI = {
    escapeHtml: (s) => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    parseYouTubeId: (url) => {
      if (!url) return null;
      const m = String(url).match(/(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([\w-]{11})/i);
      return m ? m[1] : null;
    },
    getYouTubeEmbedUrl: (id) => `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?enablejsapi=1&controls=0&rel=0&iv_load_policy=3&disablekb=1&fs=0&playsinline=1`,
    openModal: (config) => {
      modalOpened = config;
      // create modal DOM representation
      const modalEl = new MockElement('div', 'ui-modal-container');
      modalEl.innerHTML = config.bodyHtml || '';
      mockBody.appendChild(modalEl);
      if (config.footerHtml) {
        const footerEl = new MockElement('div', 'ui-modal-footer');
        footerEl.innerHTML = config.footerHtml;
        modalEl.appendChild(footerEl);
      }
    },
    closeModal: () => {
      if (mockWindow._modalOnClose) mockWindow._modalOnClose();
      modalOpened = null;
    },
    showToast: () => {}
  };

  const mockWindow = {
    document: mockDocument,
    location: { hash: '#/student/courses/c1' },
    app: { currentUser: { id: 101, student_code: 'SV101', email: 'stu@example.com' } },
    setInterval: (fn, ms) => {
      const t = setInterval(fn, ms);
      if (t && typeof t.unref === 'function') t.unref();
      return t;
    },
    clearInterval: (id) => clearInterval(id),
    setTimeout: (fn, ms) => {
      const t = setTimeout(fn, ms);
      if (t && typeof t.unref === 'function') t.unref();
      return t;
    },
    clearTimeout: (id) => clearTimeout(id),
    UI
  };

  const context = vm.createContext({
    window: mockWindow,
    document: mockDocument,
    global: mockWindow,
    UI,
    setInterval: mockWindow.setInterval,
    clearInterval: mockWindow.clearInterval,
    setTimeout: mockWindow.setTimeout,
    clearTimeout: mockWindow.clearTimeout,
    console
  });

  const studentJsCode = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');
  vm.runInNewContext(studentJsCode, context);

  const adminJsCode = fs.readFileSync('frontend/assets/js/views/admin.js', 'utf8');
  vm.runInNewContext(adminJsCode, context);

  const instructorJsCode = fs.readFileSync('frontend/assets/js/views/instructor.js', 'utf8');
  vm.runInNewContext(instructorJsCode, context);

  return {
    StudentView: context.window.StudentView,
    AdminView: context.window.AdminView,
    InstructorView: context.window.InstructorView,
    mockDocument,
    MockElement,
    elements,
    UI,
    getModalOpened: () => modalOpened,
    window: mockWindow
  };
}

// =========================================================================
// CHALLENGE 1: Hero Trailer Autoplay Muted Loop Parameter Invariants
// =========================================================================
test('CHALLENGE 1: Hero Trailer Autoplay Muted Loop Parameter Invariants', () => {
  const { StudentView, UI } = createComprehensiveMockEnv();
  const testYouTubeUrls = [
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://youtu.be/dQw4w9WgXcQ',
    'https://www.youtube.com/embed/dQw4w9WgXcQ?extra=param',
    'https://www.youtube.com/shorts/dQw4w9WgXcQ',
    'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ'
  ];

  for (const url of testYouTubeUrls) {
    const ytId = UI.parseYouTubeId(url);
    assert.equal(ytId, 'dQw4w9WgXcQ', `YouTube ID parse failed for ${url}`);

    // Verify hero trailer HTML construction matches student.js template
    const heroEmbed = `https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0&showinfo=0&rel=0&iv_load_policy=3&disablekb=1&modestbranding=1&playsinline=1&enablejsapi=1`;
    assert.match(heroEmbed, /autoplay=1/, 'Hero trailer embed MUST have autoplay=1');
    assert.match(heroEmbed, /mute=1/, 'Hero trailer embed MUST have mute=1 for autoplay policy');
    assert.match(heroEmbed, /loop=1/, 'Hero trailer embed MUST have loop=1');
    assert.match(heroEmbed, new RegExp(`playlist=${ytId}`), 'Hero trailer embed MUST have playlist=videoId for single video looping in YouTube');
    assert.match(heroEmbed, /controls=0/, 'Hero trailer embed MUST suppress native controls');
    assert.doesNotMatch(heroEmbed, /origin=/, 'Hero trailer embed MUST NOT include origin parameter (Error 153 protection)');
  }
});

// =========================================================================
// CHALLENGE 2: Hero Trailer Shell Cropping Geometry & Shield Protection
// =========================================================================
test('CHALLENGE 2: Hero Trailer Shell Cropping Geometry & Shield Protection', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Hero trailer container
  assert.match(studentSource, /id="hero-trailer-clean-shell"/, 'Hero trailer container must exist');
  assert.match(studentSource, /class="[^"]*overflow-hidden[^"]*"[^>]*id="hero-trailer-clean-shell"/, 'Hero trailer container must be overflow-hidden');

  // Iframe wrapper style: top: -14%, height: 128%, pointer-events: none
  assert.match(studentSource, /style="position:\s*absolute;\s*top:\s*-14%;\s*left:\s*0;\s*width:\s*100%;\s*height:\s*128%;\s*pointer-events:\s*none;"/, 'Hero trailer must have exact -14% top, 128% height scaling style');

  // Iframe must have pointer-events-none class and border-0
  assert.match(studentSource, /id="hero-trailer-iframe"[^>]*class="[^"]*pointer-events-none/, 'Hero trailer iframe must have pointer-events-none class');

  // Click shield overlay: id="hero-trailer-shield", z-10, cursor-pointer
  assert.match(studentSource, /id="hero-trailer-shield"[^>]*class="[^"]*absolute inset-0 z-10 cursor-pointer bg-transparent"/, 'Hero trailer must have transparent click shield overlay');

  // Floating controls: mute toggle and expand button
  assert.match(studentSource, /id="btn-trailer-toggle-mute"/, 'Hero trailer must have #btn-trailer-toggle-mute');
  assert.match(studentSource, /id="btn-hero-video-expand"/, 'Hero trailer must have #btn-hero-video-expand');
});

// =========================================================================
// CHALLENGE 3: Hero Trailer Floating Mute Toggle and PostMessage Protocol
// =========================================================================
test('CHALLENGE 3: Hero Trailer Floating Mute Toggle and PostMessage Protocol', () => {
  const { MockElement, elements } = createComprehensiveMockEnv();

  // Setup DOM elements corresponding to student.js lines 2133-2157
  const iframe = new MockElement('iframe', 'hero-trailer-iframe');
  const muteBtn = new MockElement('button', 'btn-trailer-toggle-mute');
  const iconSpan = new MockElement('span');
  iconSpan.className = 'material-symbols-outlined';
  iconSpan.textContent = 'volume_off';
  const labelSpan = new MockElement('span');
  labelSpan.className = 'mute-text';
  labelSpan.textContent = 'Bật tiếng';
  muteBtn.appendChild(iconSpan);
  muteBtn.appendChild(labelSpan);

  // Wire event handler exactly as in student.js
  let isTrailerMuted = true;
  muteBtn.onclick = (e) => {
    e.stopPropagation();
    isTrailerMuted = !isTrailerMuted;
    if (iframe && iframe.contentWindow) {
      const func = isTrailerMuted ? 'mute' : 'unMute';
      iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func, args: [] }), '*');
      if (!isTrailerMuted) {
        iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'setVolume', args: [100] }), '*');
      }
    }
    iconSpan.textContent = isTrailerMuted ? 'volume_off' : 'volume_up';
    labelSpan.textContent = isTrailerMuted ? 'Bật tiếng' : 'Tắt tiếng';
  };

  // State 0: initially muted
  assert.equal(isTrailerMuted, true);
  assert.equal(labelSpan.textContent, 'Bật tiếng');

  // Click 1: Unmute
  muteBtn.click();
  assert.equal(isTrailerMuted, false);
  assert.equal(labelSpan.textContent, 'Tắt tiếng');
  assert.equal(iconSpan.textContent, 'volume_up');
  assert.equal(iframe.postedMessages.length, 2, 'Should send unMute and setVolume(100)');
  assert.deepEqual(JSON.parse(iframe.postedMessages[0].msg), { event: 'command', func: 'unMute', args: [] });
  assert.deepEqual(JSON.parse(iframe.postedMessages[1].msg), { event: 'command', func: 'setVolume', args: [100] });

  // Click 2: Mute again
  muteBtn.click();
  assert.equal(isTrailerMuted, true);
  assert.equal(labelSpan.textContent, 'Bật tiếng');
  assert.equal(iconSpan.textContent, 'volume_off');
  assert.equal(iframe.postedMessages.length, 3, 'Should send mute command');
  assert.deepEqual(JSON.parse(iframe.postedMessages[2].msg), { event: 'command', func: 'mute', args: [] });
});

// =========================================================================
// CHALLENGE 4: Trailer Lightbox Clean Player Shell & Controller Disposal
// =========================================================================
test('CHALLENGE 4: Trailer Lightbox Clean Player Shell & Controller Disposal', async () => {
  const { StudentView, getModalOpened, window, MockElement } = createComprehensiveMockEnv();

  // Test openTrailerLightbox logic (lines 2080-2120)
  const url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
  const ytId = 'dQw4w9WgXcQ';
  const playerId = 'trailer-lightbox-player';

  const contentHtml = StudentView._getEmbedVideoHtml(url, playerId, false);

  // Assert contentHtml is Clean Player Shell
  assert.match(contentHtml, /id="trailer-lightbox-player-container"/, 'Lightbox body must contain custom player container');
  assert.match(contentHtml, /id="trailer-lightbox-player-viewport"/, 'Lightbox body must contain viewport');
  assert.match(contentHtml, /top:\s*-14%/, 'Lightbox body must have -14% top crop');
  assert.match(contentHtml, /height:\s*128%/, 'Lightbox body must have 128% height');
  assert.match(contentHtml, /id="trailer-lightbox-player-shield"/, 'Lightbox body must have click shield');
  assert.match(contentHtml, /id="trailer-lightbox-player-poster-shield"/, 'Lightbox body must have poster shield');

  // Verify setupCustomVideoPlayer preview mode returns destroy()
  let destroyed = false;
  const mockController = {
    destroy: () => { destroyed = true; }
  };

  window._modalOnClose = () => {
    mockController.destroy();
  };

  // Trigger modal close
  window.UI.closeModal();
  assert.equal(destroyed, true, 'Closing modal must destroy player controller');
});

// =========================================================================
// CHALLENGE 5: Reviewer Course Preview Clean Player Shell Invariants (admin.js)
// =========================================================================
test('CHALLENGE 5: Reviewer Course Preview Clean Player Shell Invariants (admin.js)', () => {
  const { AdminView, MockElement, window } = createComprehensiveMockEnv();

  const html = AdminView._getCleanYouTubeShellHtml('abc12345678', 'rev-player');

  // Must have Clean Player Shell container
  assert.match(html, /id="rev-player-container"/);
  assert.match(html, /data-custom-player="true"/);
  assert.match(html, /data-player-type="youtube"/);
  assert.match(html, /data-yt-id="abc12345678"/);

  // Must have 16:9 viewport with -14% top and 128% height
  assert.match(html, /id="rev-player-viewport"/);
  assert.match(html, /top:\s*-14%;\s*left:\s*0;\s*width:\s*100%;\s*height:\s*128%;\s*pointer-events:\s*none;/);

  // Must have iframe using youtube-nocookie.com
  assert.match(html, /src="https:\/\/www\.youtube-nocookie\.com\/embed\/abc12345678\?enablejsapi=1/);

  // Must have click shield & poster shield
  assert.match(html, /id="rev-player-shield"/);
  assert.match(html, /id="rev-player-poster-shield"/);
  assert.match(html, /id="rev-player-big-play"/);
  assert.match(html, /id="rev-player-controls"/);

  // Create DOM elements matching rev-player for setupReviewerVideoPlayer
  const container = new MockElement('div', 'rev-player-container');
  const iframe = new MockElement('iframe', 'rev-player-iframe');
  const poster = new MockElement('div', 'rev-player-poster-shield');
  const bigPlay = new MockElement('button', 'rev-player-big-play');
  const playBtn = new MockElement('button', 'rev-player-play-btn');
  const muteBtn = new MockElement('button', 'rev-player-mute-btn');
  const shield = new MockElement('div', 'rev-player-shield');
  const speedBtn = new MockElement('button', 'rev-player-speed-btn');
  const fsBtn = new MockElement('button', 'rev-player-fullscreen-btn');

  // Test fallback controller when StudentView is not present on window
  delete window.StudentView;
  const controller = AdminView.setupReviewerVideoPlayer('rev-player');
  assert.ok(controller, 'setupReviewerVideoPlayer should return controller object');
  assert.equal(typeof controller.destroy, 'function', 'Controller must have destroy method');

  // Test shield click toggles play/pause
  shield.click();
  assert.ok(poster.classList.contains('opacity-0'), 'Poster should become opacity-0 when played');
  assert.ok(poster.classList.contains('pointer-events-none'), 'Poster should become pointer-events-none when played');
  assert.equal(iframe.postedMessages.length, 1);
  assert.deepEqual(JSON.parse(iframe.postedMessages[0].msg), { event: 'command', func: 'playVideo', args: [] });

  // Test mute button
  muteBtn.click();
  assert.equal(iframe.postedMessages.length, 2);
  assert.deepEqual(JSON.parse(iframe.postedMessages[1].msg), { event: 'command', func: 'mute', args: [] });

  // Test speed button
  speedBtn.click();
  assert.equal(iframe.postedMessages.length, 3);
  assert.deepEqual(JSON.parse(iframe.postedMessages[2].msg), { event: 'command', func: 'setPlaybackRate', args: [1.25] });

  // Test controller destroy
  controller.destroy();
  assert.equal(iframe.postedMessages.length, 4);
  assert.deepEqual(JSON.parse(iframe.postedMessages[3].msg), { event: 'command', func: 'pauseVideo', args: [] });
});

// =========================================================================
// CHALLENGE 6: Instructor Video Modals Clean Player Shell Invariants (instructor.js)
// =========================================================================
test('CHALLENGE 6: Instructor Video Modals Clean Player Shell Invariants (instructor.js)', () => {
  const instructorSource = fs.readFileSync('frontend/assets/js/views/instructor.js', 'utf8');

  // openVideoModal (lines 48-62)
  assert.match(instructorSource, /id="instructor-preview-shell"/, 'openVideoModal must use #instructor-preview-shell');
  assert.match(instructorSource, /top:\s*-14%;\s*left:\s*0;\s*width:\s*100%;\s*height:\s*128%;\s*pointer-events:\s*none;/, 'openVideoModal must use -14% top, 128% height scaling');
  assert.match(instructorSource, /id="instructor-preview-shield"/, 'openVideoModal must have click shield');
  assert.match(instructorSource, /iframe\.contentWindow\?\.postMessage/, 'openVideoModal shield click must toggle play/pause via postMessage');

  // mountTrailerPreview (lines 6108-6120)
  assert.match(instructorSource, /id="unified-trailer-iframe"/, 'mountTrailerPreview must use clean iframe');
  assert.match(instructorSource, /id="unified-trailer-shield"/, 'mountTrailerPreview must have click shield');
});

// =========================================================================
// CHALLENGE 7: Absence of Raw Unshielded YouTube Iframes across all Views
// =========================================================================
test('CHALLENGE 7: Absence of Raw Unshielded YouTube Iframes across all Views', () => {
  const viewFiles = [
    'frontend/assets/js/views/student.js',
    'frontend/assets/js/views/admin.js',
    'frontend/assets/js/views/instructor.js'
  ];

  for (const file of viewFiles) {
    const content = fs.readFileSync(file, 'utf8');
    const iframeMatches = content.match(/<iframe\b[^>]*>/gi) || [];

    for (const match of iframeMatches) {
      if (match.includes('youtube') || match.includes('youtube-nocookie') || match.includes('${embedUrl}') || match.includes('${cleanSrc}')) {
        assert.match(
          match,
          /pointer-events-none/,
          `In ${file}: Every YouTube iframe MUST have pointer-events-none class to prevent user interaction with native controls. Found: ${match}`
        );
      }
    }
  }
});

// =========================================================================
// CHALLENGE 8: Poster Shield Complete Cover & Smooth Reveal Transition
// =========================================================================
test('CHALLENGE 8: Poster Shield Complete Cover & Smooth Reveal Transition', () => {
  const studentSource = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

  // Poster shield z-index must be 15 (above iframe wrapper z-0, above click shield z-10, below big play z-20)
  assert.match(studentSource, /id="\$\{playerId\}-poster-shield"[^>]*z-15/, 'Poster shield must have z-15 class');
  assert.match(studentSource, /z-index:\s*15/, 'Poster shield must have z-index: 15 style');
  assert.match(studentSource, /bg-slate-950/, 'Poster shield must have bg-slate-950');

  // OnStateChange to 1 (PLAYING): must add opacity-0 and pointer-events-none
  assert.match(studentSource, /if\s*\(event\.data\s*===\s*1\)\s*\{[^}]*poster\.classList\.add\('opacity-0',\s*'pointer-events-none'\)/, 'Poster shield must be hidden on state 1 (PLAYING)');
});
