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
    addEventListener: () => {},
    removeEventListener: () => {},
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
    getCourseDetail: async (courseId) => ({
      id: 'course-123',
      course_id: 'course-123',
      title: 'Khóa học Web',
      status: 'PUBLISHED',
      learning_units: [
        {
          learning_unit_id: 'unit-1',
          id: 'unit-1',
          title: 'Chương 1: Cơ bản',
          lessons: [
            { lesson_id: 'lesson-existing-1', id: 'lesson-existing-1', title: 'Bài giảng 1', position: 1, learning_unit_id: 'unit-1', content: '' }
          ]
        }
      ]
    }),
    getCourseAssessments: async () => ({ assessments: [] }),
    getCourseChangesetStatus: async () => ({ status: 'NONE' }),
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
    getLessonDetail: async (lessonId) => {
      apiCalls.getLessonCalls.push(lessonId);
      return {
        lesson_id: lessonId,
        id: lessonId,
        title: 'Bài giảng 1',
        content: '',
        learning_unit_id: 'unit-1'
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

test('renderLessonAuthoringStudio on existing lesson does not trigger unintended createLesson calls', async () => {
  const { InstructorView, container, window, apiCalls } = setupTestEnvironment();

  window.location.hash = '#/instructor/courses/course-123/lessons/lesson-existing-1/edit';
  await InstructorView.renderLessonAuthoringStudio(container, 'course-123', 'lesson-existing-1', 'unit-1');

  assert.equal(apiCalls.createLessonCalls.length, 0, 'No createLesson should be called on viewing lesson');
});

test('Curriculum studio navigation maintains single-page layout without eager DB mutations', async () => {
  const { InstructorView, container, apiCalls } = setupTestEnvironment();

  await InstructorView.renderCourseManage(container, 'course-123', 'curriculum');

  assert.equal(
    apiCalls.createLessonCalls.length,
    0,
    'renderCourseManage must NOT eagerly create any lesson in DB'
  );
});

