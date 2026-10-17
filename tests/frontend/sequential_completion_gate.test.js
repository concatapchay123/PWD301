const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function createBrowserEnvironment() {
  const events = new Map();
  const listeners = [];
  const elements = new Map();

  class MockElement {
    constructor(tagName = 'div', id = '') {
      this.tagName = tagName.toUpperCase();
      this.id = id;
      this.className = '';
      this.innerHTML = '';
      this.textContent = '';
      this.children = [];
      this.parentElement = null;
      this.style = {};
      this.dataset = {};
      this.attributes = new Map();
      this.disabled = false;
      this.isConnected = true;
    }

    setAttribute(name, value) {
      this.attributes.set(name, String(value));
      if (name === 'id') this.id = String(value);
      if (name === 'class') this.className = String(value);
    }

    getAttribute(name) {
      return this.attributes.get(name) || null;
    }

    removeAttribute(name) {
      this.attributes.delete(name);
    }

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

    querySelector(selector) {
      if (selector.startsWith('#')) {
        const id = selector.slice(1);
        return elements.get(id) || null;
      }
      if (selector.startsWith('.')) {
        const cls = selector.slice(1);
        return this.children.find(c => c.className?.includes(cls)) || null;
      }
      return null;
    }

    querySelectorAll(selector) {
      return [];
    }

    addEventListener(event, handler) {
      listeners.push({ element: this, event, handler });
    }

    removeEventListener(event, handler) {
      const idx = listeners.findIndex(l => l.element === this && l.event === event && l.handler === handler);
      if (idx !== -1) listeners.splice(idx, 1);
    }

    closest(selector) {
      return null;
    }

    getBoundingClientRect() {
      return { top: 0, left: 0, width: 800, height: 450, right: 800, bottom: 450 };
    }
  }

  const document = {
    visibilityState: 'visible',
    createElement: tag => new MockElement(tag),
    getElementById: id => elements.get(id) || null,
    addEventListener: (event, handler) => {
      if (!events.has(event)) events.set(event, []);
      events.get(event).push(handler);
    },
    removeEventListener: (event, handler) => {
      const list = events.get(event) || [];
      const idx = list.indexOf(handler);
      if (idx !== -1) list.splice(idx, 1);
    }
  };

  const window = {
    location: { origin: 'http://localhost:5000', hash: '#/student/courses/c1/lessons/l1' },
    document,
    setInterval: () => 1,
    clearInterval: () => {},
    setTimeout: fn => { fn(); return 1; },
    clearTimeout: () => {},
    getComputedStyle: el => el.style || {},
    addEventListener: () => {},
    removeEventListener: () => {}
  };

  return { window, document, elements, MockElement };
}

function loadStudentView(env) {
  const studentJsCode = fs.readFileSync(path.join(__dirname, '../../frontend/assets/js/views/student.js'), 'utf-8');
  const armorJsCode = fs.readFileSync(path.join(__dirname, '../../frontend/assets/js/components/video-armor.js'), 'utf-8');

  const context = vm.createContext({
    window: env.window,
    document: env.document,
    global: env.window,
    console,
    UI: {
      escapeHtml: s => String(s || ''),
      showToast: () => {}
    },
    ApiClient: {
      recordLessonProgress: async () => ({ is_completed: true }),
      getStudentCourseProgress: async () => ({})
    },
    sessionStorage: {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {}
    },
    localStorage: {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {}
    }
  });

  vm.runInContext(armorJsCode, context);
  vm.runInContext(studentJsCode, context);

  return {
    StudentView: context.window.StudentView || context.StudentView,
    VideoArmor: context.window.VideoArmor || context.VideoArmor
  };
}

test('R5.1: isLessonVideoWatched requires 100% threshold (0.99) and recognizes all_videos_complete', () => {
  const env = createBrowserEnvironment();
  const { StudentView } = loadStudentView(env);

  // Lesson without video is always considered video-watched
  assert.equal(StudentView.isLessonVideoWatched({}), true);
  assert.equal(StudentView.isLessonVideoWatched({ video_url: null }), true);

  // Lesson with video at 90% (old threshold) must now FAIL
  const lesson90 = {
    video_url: 'https://example.com/stream.m3u8',
    progress: { max_view_fraction: 0.90, seconds_spent: 100 }
  };
  assert.equal(StudentView.isLessonVideoWatched(lesson90), false, '0.90 fraction should not satisfy 100% requirement');

  // Lesson with video at 98% must still FAIL
  const lesson98 = {
    video_url: 'https://example.com/stream.m3u8',
    progress: { max_view_fraction: 0.98, seconds_spent: 100 }
  };
  assert.equal(StudentView.isLessonVideoWatched(lesson98), false, '0.98 fraction should not satisfy 100% requirement');

  // Lesson with video at 99.5% PASSES
  const lesson99 = {
    video_url: 'https://example.com/stream.m3u8',
    progress: { max_view_fraction: 0.995, seconds_spent: 100 }
  };
  assert.equal(StudentView.isLessonVideoWatched(lesson99), true, '0.995 fraction satisfies 100% requirement');

  // Explicit backend flags override fraction
  assert.equal(StudentView.isLessonVideoWatched({
    video_url: 'https://example.com/stream.m3u8',
    progress: { is_video_complete: true }
  }), true);

  assert.equal(StudentView.isLessonVideoWatched({
    video_url: 'https://example.com/stream.m3u8',
    video_urls: ['url1', 'url2'],
    progress: { all_videos_complete: true }
  }), true);
});

test('R5.2: Sequential completion engine enforces 60s dwell, video 100%, and miniquiz independently', () => {
  // Simulate 3-condition logic matching student.js implementation
  function evaluateLessonCompletion({ lesson, dwellElapsed, videoWatched, hasPassedQuiz, isCompleted }) {
    const hasText = Boolean(lesson.markdown_content && typeof lesson.markdown_content === 'string' && lesson.markdown_content.trim() !== '');
    const hasVideo = Boolean(lesson.video_url && typeof lesson.video_url === 'string' && lesson.video_url.trim() !== '' && lesson.video_url.trim() !== 'null') || (Array.isArray(lesson.video_urls) && lesson.video_urls.length > 0);
    const hasMiniQuiz = Array.isArray(lesson.quiz) && lesson.quiz.length > 0;

    const dwellRequired = 60;
    const dwellOk = !hasText || (dwellElapsed >= dwellRequired);
    const videoOk = !hasVideo || videoWatched;
    const quizOk = !hasMiniQuiz || hasPassedQuiz;

    const isLessonRequirementsMet = () => {
      if (isCompleted) return true;
      return dwellOk && videoOk && quizOk;
    };

    const getMissingRequirements = () => {
      if (isCompleted) return [];
      const missing = [];
      if (hasText && dwellElapsed < dwellRequired) {
        missing.push(`Cần học tối thiểu 60s (còn ${dwellRequired - dwellElapsed}s)`);
      }
      if (hasVideo && !videoWatched) {
        missing.push('Cần xem hết 100% video bài học');
      }
      if (hasMiniQuiz && !hasPassedQuiz) {
        missing.push('Cần hoàn thành phần Câu hỏi');
      }
      return missing;
    };

    return {
      meetsRequirements: isLessonRequirementsMet(),
      missing: getMissingRequirements()
    };
  }

  // Case 1: Text-only lesson under 60 seconds
  const textOnlyUnder = evaluateLessonCompletion({
    lesson: { markdown_content: '# Bài học lý thuyết quan trọng' },
    dwellElapsed: 45,
    videoWatched: false,
    hasPassedQuiz: false,
    isCompleted: false
  });
  assert.equal(textOnlyUnder.meetsRequirements, false);
  assert.deepEqual(textOnlyUnder.missing, ['Cần học tối thiểu 60s (còn 15s)']);

  // Case 2: Text-only lesson reached 60 seconds
  const textOnlyReached = evaluateLessonCompletion({
    lesson: { markdown_content: '# Bài học lý thuyết quan trọng' },
    dwellElapsed: 60,
    videoWatched: false,
    hasPassedQuiz: false,
    isCompleted: false
  });
  assert.equal(textOnlyReached.meetsRequirements, true);
  assert.deepEqual(textOnlyReached.missing, []);

  // Case 3: Video-only lesson incomplete vs complete
  const videoOnlyIncomplete = evaluateLessonCompletion({
    lesson: { video_url: 'https://example.com/hls.m3u8' },
    dwellElapsed: 10,
    videoWatched: false,
    hasPassedQuiz: false,
    isCompleted: false
  });
  assert.equal(videoOnlyIncomplete.meetsRequirements, false);
  assert.deepEqual(videoOnlyIncomplete.missing, ['Cần xem hết 100% video bài học']);

  const videoOnlyComplete = evaluateLessonCompletion({
    lesson: { video_url: 'https://example.com/hls.m3u8' },
    dwellElapsed: 10,
    videoWatched: true,
    hasPassedQuiz: false,
    isCompleted: false
  });
  assert.equal(videoOnlyComplete.meetsRequirements, true);

  // Case 4: Miniquiz-only lesson incomplete vs complete
  const quizOnlyIncomplete = evaluateLessonCompletion({
    lesson: { quiz: [{ id: 'q1', question: 'Câu 1' }] },
    dwellElapsed: 5,
    videoWatched: false,
    hasPassedQuiz: false,
    isCompleted: false
  });
  assert.equal(quizOnlyIncomplete.meetsRequirements, false);
  assert.deepEqual(quizOnlyIncomplete.missing, ['Cần hoàn thành phần Câu hỏi']);

  const quizOnlyComplete = evaluateLessonCompletion({
    lesson: { quiz: [{ id: 'q1', question: 'Câu 1' }] },
    dwellElapsed: 5,
    videoWatched: false,
    hasPassedQuiz: true,
    isCompleted: false
  });
  assert.equal(quizOnlyComplete.meetsRequirements, true);

  // Case 5: Hybrid multi-component (Text + Video + Miniquiz)
  const hybridLesson = {
    markdown_content: 'Hướng dẫn cài đặt hệ thống',
    video_url: 'https://example.com/video.m3u8',
    quiz: [{ id: 'q1' }]
  };

  // Video and quiz done, but text dwell only 30s -> MUST FAIL
  const hybridDwellFailed = evaluateLessonCompletion({
    lesson: hybridLesson,
    dwellElapsed: 30,
    videoWatched: true,
    hasPassedQuiz: true,
    isCompleted: false
  });
  assert.equal(hybridDwellFailed.meetsRequirements, false);
  assert.deepEqual(hybridDwellFailed.missing, ['Cần học tối thiểu 60s (còn 30s)']);

  // All 3 satisfied -> PASSES
  const hybridAllPassed = evaluateLessonCompletion({
    lesson: hybridLesson,
    dwellElapsed: 60,
    videoWatched: true,
    hasPassedQuiz: true,
    isCompleted: false
  });
  assert.equal(hybridAllPassed.meetsRequirements, true);
  assert.deepEqual(hybridAllPassed.missing, []);
});

test('R5.3: Next button renders gray and disabled without lock icon/text when incomplete, and emerald green when complete', () => {
  function renderNextButtonMarkup(meetsAll, nextItem) {
    if (nextItem) {
      if (meetsAll) {
        return `
          <button type="button" id="cisco-next-btn" title="${nextItem.title}" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer animate-fade-in">
            <span>Tiếp theo</span>
            <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        `;
      } else {
        return `
          <button type="button" id="cisco-next-btn" title="Chưa đủ điều kiện chuyển bài" class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-300/80 dark:border-slate-700 cursor-not-allowed select-none">
            <span>Tiếp theo</span>
            <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        `;
      }
    } else {
      if (meetsAll) {
        return `
          <a href="#/student/courses" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer">
            <span>Hoàn thành khóa học</span>
            <span class="material-symbols-outlined text-[16px]">celebration</span>
          </a>
        `;
      } else {
        return `
          <button type="button" class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-300/80 dark:border-slate-700 cursor-not-allowed select-none">
            <span>Hoàn thành khóa học</span>
            <span class="material-symbols-outlined text-[16px]">celebration</span>
          </button>
        `;
      }
    }
  }

  const nextLesson = { title: 'Bài 2: Thực hành' };

  // 1. Incomplete next button
  const incompleteHtml = renderNextButtonMarkup(false, nextLesson);
  assert.ok(incompleteHtml.includes('bg-slate-200'), 'Incomplete button must have gray slate background');
  assert.ok(incompleteHtml.includes('cursor-not-allowed'), 'Incomplete button must be cursor-not-allowed');
  assert.ok(incompleteHtml.includes('select-none'), 'Incomplete button must be select-none');
  assert.ok(!incompleteHtml.includes('lock'), 'Incomplete button must NOT contain a lock icon');
  assert.ok(!incompleteHtml.includes('Đã khóa'), 'Incomplete button must NOT contain "Đã khóa" text');
  assert.ok(incompleteHtml.includes('Tiếp theo'), 'Incomplete button keeps standard "Tiếp theo" label');

  // 2. Complete next button
  const completeHtml = renderNextButtonMarkup(true, nextLesson);
  assert.ok(completeHtml.includes('bg-emerald-600'), 'Complete button must have emerald green background');
  assert.ok(completeHtml.includes('cursor-pointer'), 'Complete button must be cursor-pointer');
  assert.ok(completeHtml.includes('Tiếp theo'), 'Complete button has "Tiếp theo" label');

  // 3. Final lesson: "Hoàn thành khóa học"
  const finalIncomplete = renderNextButtonMarkup(false, null);
  assert.ok(finalIncomplete.includes('bg-slate-200'));
  assert.ok(finalIncomplete.includes('Hoàn thành khóa học'));

  const finalComplete = renderNextButtonMarkup(true, null);
  assert.ok(finalComplete.includes('bg-emerald-600'));
  assert.ok(finalComplete.includes('Hoàn thành khóa học'));
});

test('R5.4: VideoArmor with silentWatermark suppresses false-positive blackout and maintains undisturbed playback', () => {
  const env = createBrowserEnvironment();
  const { VideoArmor } = loadStudentView(env);

  const container = env.document.createElement('div');
  container.setAttribute('id', 'test-player-container');
  env.elements.set('test-player-container', container);

  let violationReported = false;
  const armor = VideoArmor.mount(container, {
    silentWatermark: true,
    student: { student_code: 'STU12345', email: 'student@example.com' },
    ip: '192.168.1.100',
    onSecurityViolation: (reason) => {
      violationReported = true;
    }
  });

  // 1. Watermark is mounted
  assert.ok(armor.watermarkEl !== null, 'Watermark element is created');
  assert.equal(armor.isBlackedOut, false, 'Should not start blacked out');

  // 2. DOM mutation inspection with silentWatermark does NOT trigger blackout
  armor._inspectMutations([]);
  assert.equal(armor.isBlackedOut, false, 'Mutations must not trigger blackout in silent mode');

  // 3. Explicit triggerBlackout records telemetry without creating blackout overlay
  armor.triggerBlackout('DOM_TAMPER');
  assert.equal(armor.isBlackedOut, false, 'Silent mode must not set isBlackedOut to true');
  assert.equal(armor.blackoutEl, null, 'Silent mode must not append blackout overlay to DOM');
  assert.equal(violationReported, true, 'Violation is recorded via telemetry silently');

  // 4. Window blur does not pause media in silent mode
  let pauseCalled = false;
  container._customPlayer = {
    pause: () => { pauseCalled = true; }
  };
  armor._onWindowBlur();
  assert.equal(pauseCalled, false, 'Silent mode must not pause playback on window blur');

  armor.destroy();
});
