const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function setupTestEnvironment() {
  const elements = new Map();
  function createElement(tag) {
    const el = {
      tagName: tag.toUpperCase(),
      isConnected: true,
      classList: {
        add: () => {},
        remove: () => {},
        contains: () => false
      },
      style: {},
      attributes: {},
      setAttribute: (k, v) => { el.attributes[k] = v; },
      getAttribute: (k) => el.attributes[k],
      removeAttribute: (k) => { delete el.attributes[k]; },
      addEventListener: () => {},
      removeEventListener: () => {},
      querySelector: (sel) => {
        if (sel.startsWith('#')) return elements.get(sel.slice(1)) || null;
        if (sel.startsWith('.')) {
          for (const item of elements.values()) {
            if (item.classList && item.classList.contains && item.classList.contains(sel.slice(1))) return item;
          }
        }
        return null;
      },
      querySelectorAll: (sel) => {
        const res = [];
        if (sel.startsWith('.')) {
          const cls = sel.slice(1);
          for (const item of elements.values()) {
            if (item.className && item.className.includes(cls)) res.push(item);
          }
        }
        return res;
      },
      prepend: () => {},
      appendChild: (child) => child,
      replaceChildren: () => {},
      remove: () => {},
      children: [],
      childNodes: []
    };

    Object.defineProperty(el, 'innerHTML', {
      set(html) {
        el._html = html;
        const idMatches = String(html || '').matchAll(/id=["']([^"']+)["']/g);
        for (const m of idMatches) {
          const id = m[1];
          if (!elements.has(id)) {
            const child = createElement('div');
            child.id = id;
            if (id === 'studio-input-title') child.value = 'Bài giảng mới';
            if (id === 'studio-input-duration') child.value = '15';
            if (id === 'studio-content-editor') child.innerHTML = '<p>Nội dung</p>';
            elements.set(id, child);
          }
        }
      },
      get() {
        return el._html || '';
      }
    });

    return el;
  }

  const container = createElement('div');
  container.id = 'app-viewport';

  const window = {
    _currentStudioTimer: null,
    location: {
      hash: '#/instructor/courses/course-123/lessons/new?learning_unit_id=unit-1'
    },
    history: {
      replacedStateUrl: null,
      replaceState: (state, title, url) => {
        window.history.replacedStateUrl = url;
      }
    }
  };

  const document = {
    createElement,
    getElementById: (id) => elements.get(id) || null,
    body: createElement('body')
  };

  const UI = {
    escapeHtml: (s) => String(s || ''),
    showToast: () => {},
    renderMarkdown: (s) => String(s || ''),
    parseYouTubeId: () => null,
    confirm: async () => true,
    statusBadge: () => ''
  };

  const apiCalls = {
    createLessonCalls: [],
    getLearningUnitsCalls: [],
    getLessonCalls: []
  };

  const ApiClient = {
    getLearningUnits: async (courseId) => {
      apiCalls.getLearningUnitsCalls.push(courseId);
      return {
        items: [
          {
            learning_unit_id: 'unit-1',
            title: 'Chương 1: Cơ bản',
            lessons: [
              { lesson_id: 'lesson-existing-1', title: 'Bài giảng 1', position: 1 }
            ]
          }
        ]
      };
    },
    getCourse: async () => ({ id: 'course-123', title: 'Khóa học Web' }),
    createLesson: async (courseId, payload) => {
      apiCalls.createLessonCalls.push({ courseId, payload });
      return {
        lesson_id: 'lesson-new-generated-99',
        learning_unit_id: payload.learning_unit_id || 'unit-1',
        title: payload.title,
        status: payload.status
      };
    },
    getLesson: async (lessonId) => {
      apiCalls.getLessonCalls.push(lessonId);
      return null;
    }
  };

  const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  const code = fs.readFileSync(sourcePath, 'utf8');

  const context = {
    window,
    document,
    UI,
    ApiClient,
    console,
    setInterval: () => 123,
    clearInterval: () => {},
    FormData: class {},
    Option: function(text, val) { this.text = text; this.value = val; },
    InstructorView: null
  };

  vm.runInNewContext(code + '\n;globalThis.InstructorView = InstructorView;', context, { filename: sourcePath });
  const InstructorView = context.InstructorView;

  return { InstructorView, container, window, document, apiCalls, elements };
}

test('renderLessonAuthoringStudio on /lessons/new does NOT auto-create lesson in DB on page load', async () => {
  const { InstructorView, container, window, apiCalls } = setupTestEnvironment();

  await InstructorView.renderLessonAuthoringStudio(container, 'course-123', null, 'unit-1');

  assert.equal(
    apiCalls.createLessonCalls.length,
    0,
    'ApiClient.createLesson must NOT be called automatically when visiting /lessons/new'
  );

  assert.equal(
    window.location.hash,
    '#/instructor/courses/course-123/lessons/new?learning_unit_id=unit-1',
    'window.location.hash must remain on current route and not push an edit hash on load'
  );
});

test('Saving a new lesson lazily creates the draft and uses replaceState', async () => {
  const { InstructorView, container, window, apiCalls, elements } = setupTestEnvironment();

  await InstructorView.renderLessonAuthoringStudio(container, 'course-123', null, 'unit-1');

  assert.equal(apiCalls.createLessonCalls.length, 0);

  const saveBtn = elements.get('studio-save-btn');
  assert.ok(saveBtn && typeof saveBtn.onclick === 'function', 'Save button must be bound');

  // Trigger explicit save
  await saveBtn.onclick();

  assert.equal(apiCalls.createLessonCalls.length, 1, 'createLesson should be called once on save');
  assert.equal(apiCalls.createLessonCalls[0].payload.title, 'Bài giảng mới');
  assert.equal(
    window.history.replacedStateUrl,
    '#/instructor/courses/course-123/lessons/lesson-new-generated-99/edit',
    'replaceState must be called to replace URL without adding an extra history stack entry'
  );
  assert.equal(
    window.location.hash,
    '#/instructor/courses/course-123/lessons/new?learning_unit_id=unit-1',
    'window.location.hash must NOT be set directly to prevent polluting browser history'
  );
});

test('studio-back-btn returns cleanly to course curriculum tab and clears timer', async () => {
  const { InstructorView, container, window, elements } = setupTestEnvironment();

  await InstructorView.renderLessonAuthoringStudio(container, 'course-123', null, 'unit-1');

  const backBtn = elements.get('studio-back-btn');
  assert.ok(backBtn && typeof backBtn.onclick === 'function', 'Back button must be bound');

  backBtn.onclick();

  assert.equal(
    window.location.hash,
    '#/instructor/courses/course-123/manage?tab=curriculum',
    'Back button should navigate to course curriculum tab'
  );
  assert.equal(window._currentStudioTimer, null, 'Studio timer must be cleared on back');
});

test('handleAddNewLesson transitions to /lessons/new without eager DB creation', async () => {
  const { InstructorView, container, window, apiCalls, elements } = setupTestEnvironment();

  // Suppose instructor is on an existing lesson
  window.location.hash = '#/instructor/courses/course-123/lessons/lesson-existing-1/edit';
  await InstructorView.renderLessonAuthoringStudio(container, 'course-123', 'lesson-existing-1', 'unit-1');

  assert.equal(apiCalls.createLessonCalls.length, 0);

  // Navigator contains the add lesson button
  const addBtn = elements.get('btn-nav-add-lesson');
  assert.ok(addBtn && typeof addBtn.onclick === 'function', 'Add lesson button must be bound');

  // Trigger add new lesson
  await addBtn.onclick({ preventDefault: () => {} });

  // Verify NO eager createLesson was called
  assert.equal(
    apiCalls.createLessonCalls.length,
    0,
    'handleAddNewLesson must NOT eagerly create a lesson in DB before user saves'
  );

  assert.equal(
    window.location.hash,
    '#/instructor/courses/course-123/lessons/new?learning_unit_id=unit-1',
    'handleAddNewLesson must navigate to /lessons/new route cleanly'
  );
});

