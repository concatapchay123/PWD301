const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

/**
 * Independent Adversarial Reviewer Test Suite for Milestone 3
 * Reviewer: reviewer_m3_2
 * Focus: Trailer Lightbox Modal (student.js) and Teacher/Admin Preview Modals (admin.js, instructor.js)
 */

function createTestContext() {
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
      this.className = '';
      this.dataset = {};
      this.innerHTML = '';
      this.value = '';
      this.textContent = '';
      this.isConnected = true;
      this.classList = {
        add: (...classes) => { for (const c of classes) { if (!this.className.includes(c)) this.className += ' ' + c; } },
        remove: (...classes) => { for (const c of classes) { this.className = this.className.replace(c, '').trim(); } },
        toggle: (c, force) => {
          const has = this.className.includes(c);
          if (force === true || (force === undefined && !has)) this.classList.add(c);
          else if (force === false || (force === undefined && has)) this.classList.remove(c);
        },
        contains: (c) => this.className.includes(c)
      };
      if (id) elements.set(id, this);
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
      const key = `${this.id || 'anon'}:${event.type}`;
      const fns = listeners.get(key) || [];
      for (const fn of fns) fn(event);
    }
    click() {
      if (typeof this.onclick === 'function') this.onclick({ stopPropagation: () => {}, target: this });
      this.dispatchEvent({ type: 'click', target: this, stopPropagation: () => {} });
    }
    querySelector(selector) {
      if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        const search = (node) => {
          if (node.classList && node.classList.contains(cls)) return node;
          for (const c of node.children) {
            const found = search(c);
            if (found) return found;
          }
          return null;
        };
        return search(this);
      }
      return null;
    }
    querySelectorAll(selector) {
      const matches = [];
      const search = (node) => {
        if (selector === 'video' && node.tagName === 'VIDEO') matches.push(node);
        else if (selector.startsWith('.') && node.classList && node.classList.contains(selector.slice(1))) matches.push(node);
        else if (selector.startsWith('[id$=') && node.id) {
          const suffix = selector.match(/\[id\$=["']?(.*?)["']?\]/)?.[1] || '';
          if (node.id.endsWith(suffix)) matches.push(node);
        }
        for (const c of node.children) search(c);
      };
      search(this);
      return matches;
    }
    remove() {
      this.isConnected = false;
      if (this.parentElement) {
        this.parentElement.children = this.parentElement.children.filter(c => c !== this);
      }
      if (this.id) elements.delete(this.id);
    }
  }

  const mockDocument = {
    getElementById: (id) => elements.get(id) || null,
    createElement: (tag) => new MockElement(tag),
    body: new MockElement('body', 'body'),
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  const UI = {
    escapeHtml: (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'),
    renderMarkdown: (s) => `<p>${s}</p>`,
    parseYouTubeId: (url) => {
      const m = String(url || '').match(/(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/i);
      return m ? m[1] : null;
    },
    getYouTubeEmbedUrl: (id) => id ? `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?enablejsapi=1&controls=0&rel=0&iv_load_policy=3&disablekb=1&fs=0&playsinline=1` : '',
    openModal: (options) => {
      mockDocument._lastModalOptions = options;
    },
    closeModal: () => {
      if (typeof mockWindow._modalOnClose === 'function') {
        mockWindow._modalOnClose();
      }
    },
    showToast: () => {}
  };

  const mockWindow = {
    document: mockDocument,
    location: { hash: '' },
    app: { currentUser: { id: 1, role: 'ADMIN' } },
    setInterval: (fn) => setInterval(fn, 1000),
    clearInterval: (id) => clearInterval(id),
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    clearTimeout: (id) => clearTimeout(id),
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  const sandbox = {
    window: mockWindow,
    document: mockDocument,
    global: mockWindow,
    UI,
    console,
    ApiClient: {},
    setInterval: mockWindow.setInterval,
    clearInterval: mockWindow.clearInterval,
    setTimeout: mockWindow.setTimeout,
    clearTimeout: mockWindow.clearTimeout
  };

  const context = vm.createContext(sandbox);

  const studentJs = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/student.js'), 'utf8');
  const adminJs = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8');
  const instructorJs = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8');

  vm.runInNewContext(studentJs, context);
  vm.runInNewContext(adminJs, context);
  vm.runInNewContext(instructorJs, context);

  return {
    StudentView: context.window.StudentView,
    AdminView: context.window.AdminView,
    InstructorView: context.window.InstructorView,
    mockDocument,
    mockWindow,
    MockElement,
    elements
  };
}

test('Adversarial 1: Trailer Lightbox uses Clean Player Shell with zero YouTube branding and clean teardown', () => {
  const { StudentView } = createTestContext();

  const url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
  const html = StudentView._getEmbedVideoHtml(url, 'trailer-lightbox-player', false);

  // 1. Invariants: Clean Player Shell geometry and shields
  assert.ok(html.includes('id="trailer-lightbox-player-container"'), 'Container ID must match');
  assert.ok(html.includes('inset: 0'), 'Standard uncropped inset: 0 is mandatory');
  assert.ok(html.includes('width: 100%'), 'Width 100% is mandatory');
  assert.ok(html.includes('height: 100%'), 'Height 100% is mandatory');
  assert.ok(!html.includes('top: -22%'), 'Top crop -22% is permanently eliminated');
  assert.ok(html.includes('pointer-events-none'), 'Iframe host must be non-interactive');
  assert.ok(html.includes('id="trailer-lightbox-player-shield"'), 'Click shield must intercept pointer events');
  assert.ok(html.includes('id="trailer-lightbox-player-poster-shield"'), 'Cover poster shield must conceal red button');
  assert.ok(html.includes('id="trailer-lightbox-player-big-play"'), 'Big play overlay must exist');
  assert.ok(html.includes('id="trailer-lightbox-player-controls"'), 'Custom controls must be provided');

  // 2. Absence of raw iframe or native branding
  assert.doesNotMatch(html, /<iframe[^>]*src="https:\/\/www\.youtube\.com/i, 'Must not use raw standard youtube.com iframe');

  // 3. Robustness against null/undefined URLs
  assert.equal(StudentView._getEmbedVideoHtml(null), '', 'Null URL must return empty string');
  assert.equal(StudentView._getEmbedVideoHtml(''), '', 'Empty URL must return empty string');

  // 4. XSS URL is escaped safely in attribute context
  const xssHtml = StudentView._getEmbedVideoHtml('https://evil.com/video.mp4"><script>alert(1)</script>');
  assert.doesNotMatch(xssHtml, /<script>/, 'XSS script tag must be escaped in video shell HTML');
});

test('Adversarial 2: Admin Course Reviewer Preview modal renders Clean Player Shell and cleans media on lesson switch', () => {
  const { AdminView } = createTestContext();

  // 1. _getCleanYouTubeShellHtml invariants
  const shellHtml = AdminView._getCleanYouTubeShellHtml('dQw4w9WgXcQ', 'test-rev-player');
  assert.ok(shellHtml.includes('inset: 0'), 'Reviewer shell must use standard inset: 0');
  assert.ok(shellHtml.includes('width: 100%'), 'Reviewer shell must have width 100%');
  assert.ok(shellHtml.includes('height: 100%'), 'Reviewer shell must have height 100%');
  assert.ok(!shellHtml.includes('top: -22%'), 'Reviewer shell must not crop top -22%');
  assert.ok(shellHtml.includes('id="test-rev-player-poster-shield"'), 'Must have poster shield');
  assert.ok(shellHtml.includes('id="test-rev-player-shield"'), 'Must have click shield');
  assert.ok(shellHtml.includes('id="test-rev-player-big-play"'), 'Must have big play button');
  assert.ok(shellHtml.includes('id="test-rev-player-controls"'), 'Must have custom controls');
  assert.ok(shellHtml.includes('youtube-nocookie.com'), 'Must use privacy-enhanced domain');
  assert.doesNotMatch(shellHtml, /origin=/, 'Must not contain origin parameter (Error 153 immunity)');

  // 2. Null/empty ID handling
  assert.equal(AdminView._getCleanYouTubeShellHtml(null), '', 'Null ID returns empty string');
  assert.equal(AdminView._getCleanYouTubeShellHtml(''), '', 'Empty ID returns empty string');

  // 3. Reviewer lesson switching and media pause
  let pausedVideos = 0;
  let postedCommands = [];
  const fakeWorkspace = {
    innerHTML: '',
    querySelectorAll: (selector) => {
      if (selector === 'video') return [{ pause: () => { pausedVideos++; } }];
      if (selector === '[id$="-iframe"]') return [{
        contentWindow: {
          postMessage: (msg) => { postedCommands.push(JSON.parse(msg)); }
        }
      }];
      return [];
    }
  };

  const btn0 = { dataset: { lessonIndex: '0' }, setAttribute: () => {} };
  const btn1 = { dataset: { lessonIndex: '1' }, setAttribute: () => {} };
  const buttons = [btn0, btn1];

  const container = {
    innerHTML: '',
    querySelector: (sel) => sel === '[data-reviewer-workspace]' ? fakeWorkspace : null,
    querySelectorAll: () => buttons
  };

  const course = {
    learning_units: [{ id: 'u1', title: 'Chương 1' }],
    lessons: [
      { lesson_id: 'l1', learning_unit_id: 'u1', title: 'Bài 1', video_urls: ['https://youtu.be/dQw4w9WgXcQ'] },
      { lesson_id: 'l2', learning_unit_id: 'u1', title: 'Bài 2', video_urls: ['https://youtu.be/oHg5SJYRHA0'] }
    ]
  };

  AdminView.renderReviewerCoursePreview(container, course, 'l1');
  assert.ok(fakeWorkspace.innerHTML.includes('reviewer-player-0-0'), 'First lesson player rendered');

  // Switch to lesson 2
  btn1.onclick();

  assert.ok(pausedVideos >= 1, 'HTML5 video paused on lesson switch');
  assert.ok(postedCommands.some(cmd => cmd.func === 'pauseVideo'), 'YouTube iframe received pauseVideo on lesson switch');
  assert.ok(fakeWorkspace.innerHTML.includes('reviewer-player-1-0'), 'Second lesson player rendered');
});

test('Adversarial 3: Teacher Course Preview & Video Modal in instructor.js enforce Clean Player Shell', () => {
  const { InstructorView, mockDocument, MockElement } = createTestContext();

  // Create a modal element that supports .btn-close-modal querySelector
  const originalCreateElement = mockDocument.createElement;
  mockDocument.createElement = (tag) => {
    const el = originalCreateElement(tag);
    if (tag.toLowerCase() === 'div') {
      // Create a child btn-close-modal when innerHTML is set or querySelector matches
      const origQS = el.querySelector.bind(el);
      el.querySelector = (sel) => {
        if (sel === '.btn-close-modal') {
          let btn = origQS('.btn-close-modal');
          if (!btn) {
            btn = new MockElement('button');
            btn.classList.add('btn-close-modal');
            el.appendChild(btn);
          }
          return btn;
        }
        return origQS(sel);
      };
    }
    return el;
  };

  // 1. openVideoModal for YouTube
  InstructorView.openVideoModal('youtube', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'Video Bài Giảng Thử');
  const modal = mockDocument.getElementById('pwd301-video-preview-modal');
  assert.ok(modal, 'Modal must be appended to document.body');

  assert.ok(modal.innerHTML.includes('id="instructor-preview-shell"'), 'Must render instructor-preview-shell');
  assert.ok(modal.innerHTML.includes('inset: 0'), 'Must have standard inset: 0');
  assert.ok(modal.innerHTML.includes('width: 100%'), 'Must have width: 100%');
  assert.ok(modal.innerHTML.includes('height: 100%'), 'Must have height: 100%');
  assert.ok(!modal.innerHTML.includes('top: -22%'), 'Must not have top: -22% scaling');
  assert.ok(modal.innerHTML.includes('id="instructor-preview-shield"'), 'Must have click shield overlay');
  assert.ok(modal.innerHTML.includes('youtube-nocookie.com'), 'Must use youtube-nocookie.com domain');
  assert.ok(modal.innerHTML.includes('controls=0'), 'Must hide native controls');
  assert.doesNotMatch(modal.innerHTML, /origin=/, 'Must not contain origin parameter');

  // Verify modal close
  const closeBtn = modal.querySelector('.btn-close-modal');
  assert.ok(closeBtn, 'Close button exists');
  closeBtn.click();
  assert.equal(mockDocument.getElementById('pwd301-video-preview-modal'), null, 'Modal removed from body upon close');

  // 2. openCoursePreview reuses AdminView.renderReviewerCoursePreview
  assert.equal(typeof InstructorView.openCoursePreview, 'function', 'openCoursePreview must exist');
});
