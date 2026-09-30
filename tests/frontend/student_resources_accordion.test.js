const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function setupEnvironment() {
  const elements = new Map();

  function createElement(tag) {
    const el = {
      tagName: tag.toUpperCase(),
      isConnected: true,
      classList: {
        _classes: new Set(),
        add: (...cls) => cls.forEach(c => el.classList._classes.add(c)),
        remove: (...cls) => cls.forEach(c => el.classList._classes.delete(c)),
        contains: (c) => el.classList._classes.has(c),
        toggle: (c, force) => {
          if (force === undefined) {
            if (el.classList._classes.has(c)) el.classList._classes.delete(c);
            else el.classList._classes.add(c);
          } else if (force) {
            el.classList._classes.add(c);
          } else {
            el.classList._classes.delete(c);
          }
        }
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
        return null;
      },
      querySelectorAll: (sel) => {
        return [];
      },
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
    location: { hash: '#/student/courses/ops401' },
    history: {
      replaceState: () => {}
    },
    localStorage: {
      getItem: () => 'STUDENT',
      setItem: () => {}
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
    getYouTubeEmbedUrl: () => '',
    confirm: async () => true,
    statusBadge: () => '',
    difficultyBadge: () => ''
  };

  const fakeCourseData = {
    course: {
      id: 'course-ops401',
      public_id: 'course-ops401',
      code: 'OPS401',
      title: 'DevOps & CI/CD Pipeline',
    },
    learning_units: [
      {
        learning_unit_id: 'unit-1',
        title: 'Chương 1: Container với Docker',
        position: 1,
        lessons: [
          {
            lesson_id: 'les-1-1',
            learning_unit_id: 'unit-1',
            title: 'Bài 1: Dockerfile',
            position: 1,
            resources: [
              {
                resource_id: 'res-pdf-1',
                asset_id: 'asset-pdf-1',
                filename: 'Dockerfile_Best_Practices_Guide.pdf',
                byte_size: 204800,
                download_url: '/student/courses/ops401/files/asset-pdf-1/download'
              }
            ]
          },
          {
            lesson_id: 'les-1-2',
            learning_unit_id: 'unit-1',
            title: 'Bài 2: Docker Compose',
            position: 2,
            resources: [
              {
                resource_id: 'res-vid-1',
                asset_id: 'asset-vid-1',
                filename: 'huong_dan_docker_compose.mp4',
                byte_size: 10485760,
                download_url: '/student/courses/ops401/files/asset-vid-1/download'
              },
              {
                resource_id: 'res-pdf-2',
                asset_id: 'asset-pdf-2',
                filename: 'Docker_Compose_Production_Setup.pdf',
                byte_size: 512000,
                download_url: '/student/courses/ops401/files/asset-pdf-2/download'
              }
            ]
          },
          {
            lesson_id: 'les-1-3',
            learning_unit_id: 'unit-1',
            title: 'Bài 3: Bài học lý thuyết thuần (không có file)',
            position: 3,
            resources: []
          }
        ]
      },
      {
        learning_unit_id: 'unit-2',
        title: 'Chương 2: Tự động hóa CI/CD',
        position: 2,
        lessons: [
          {
            lesson_id: 'les-2-1',
            learning_unit_id: 'unit-2',
            title: 'Bài 4: GitHub Actions',
            position: 1,
            resources: [
              {
                resource_id: 'res-pdf-3',
                asset_id: 'asset-pdf-3',
                filename: 'GitHub_Actions_CICD_Cookbook.pdf',
                byte_size: 307200,
                download_url: '/student/courses/ops401/files/asset-pdf-3/download'
              }
            ]
          }
        ]
      },
      {
        learning_unit_id: 'unit-3',
        title: 'Chương 3: Chương không có tài liệu',
        position: 3,
        lessons: [
          {
            lesson_id: 'les-3-1',
            learning_unit_id: 'unit-3',
            title: 'Bài 5: Không có tài liệu',
            position: 1,
            resources: []
          }
        ]
      }
    ],
    resources: [
      // Course-level file asset (cover image, should be filtered out)
      {
        resource_id: 'asset-cover',
        asset_id: 'asset-cover',
        filename: 'ops401_cover.png',
        asset_type: 'COURSE_IMAGE',
        byte_size: 102400
      },
      // Course-level general study document
      {
        resource_id: 'asset-syllabus',
        asset_id: 'asset-syllabus',
        filename: 'OPS401_De_Cuong_Tong_Quat.pdf',
        asset_type: 'RESOURCE',
        byte_size: 409600,
        download_url: '/student/courses/ops401/files/asset-syllabus/download'
      }
    ]
  };

  const ApiClient = {
    getStudentCourseDetail: async () => fakeCourseData,
    getCourseDetail: async () => fakeCourseData,
    getStudentCourseProgress: async () => ({ progress_percent: 50, is_enrolled: true }),
    recordLessonProgress: async () => ({ is_completed: false })
  };

  const sandbox = {
    window,
    document,
    container,
    UI,
    ApiClient,
    localStorage: window.localStorage,
    setTimeout: (fn) => fn(),
    clearTimeout: () => {},
    setInterval: () => 1,
    clearInterval: () => {}
  };

  const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
  vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), sandbox, { filename: sourcePath });

  return { sandbox, container, elements, fakeCourseData };
}

test('student resources accordion groups files by chapter and lesson, hides empty ones, and isolates cover image', async () => {
  const { sandbox, container, elements } = setupEnvironment();

  await sandbox.window.StudentView.renderCourseConsole(container, 'ops401', 'les-1-1');

  // 1. Check badge count:
  // 1 file (Bài 1) + 2 files (Bài 2) + 1 file (Bài 4) + 1 general syllabus = 5 study files
  // ops401_cover.png MUST be excluded (was 6 files total, now 5)
  assert.equal(container.innerHTML.includes('Tài liệu (5)'), true, 'Badge in container must reflect 5 valid study files (excluding cover)');

  // 2. Check Resources panel content
  const resPanel = elements.get('sidebar-panel-resources');
  assert.ok(resPanel, 'sidebar-panel-resources must exist');
  const panelHtml = resPanel.innerHTML;

  // Must include Chapter 1 and Chapter 2
  assert.equal(panelHtml.includes('Chương 1: Container với Docker'), true);
  assert.equal(panelHtml.includes('Chương 2: Tự động hóa CI/CD'), true);

  // Must NOT include Chapter 3 because it has 0 files
  assert.equal(panelHtml.includes('Chương 3: Chương không có tài liệu'), false, 'Empty chapter must be hidden');

  // Must NOT include Lesson 3 because it has 0 files
  assert.equal(panelHtml.includes('Bài 3: Bài học lý thuyết thuần'), false, 'Lesson without files must be hidden');

  // Must include General Course Resources section
  assert.equal(panelHtml.includes('Tài liệu chung khóa học'), true, 'General course resources section must appear');
  assert.equal(panelHtml.includes('OPS401_De_Cuong_Tong_Quat.pdf'), true, 'Syllabus must appear under general course resources');

  // Must NOT include cover image
  assert.equal(panelHtml.includes('ops401_cover.png'), false, 'ops401_cover.png must never appear in study resources');

  // Must include the actual lesson files
  assert.equal(panelHtml.includes('Dockerfile_Best_Practices_Guide.pdf'), true);
  assert.equal(panelHtml.includes('huong_dan_docker_compose.mp4'), true);
  assert.equal(panelHtml.includes('Docker_Compose_Production_Setup.pdf'), true);
  assert.equal(panelHtml.includes('GitHub_Actions_CICD_Cookbook.pdf'), true);

  // 3. Test accordion toggle without page navigation
  assert.equal(typeof sandbox.window._ciscoToggleResMod, 'function', '_ciscoToggleResMod must be defined');
  assert.equal(typeof sandbox.window._ciscoToggleResLesson, 'function', '_ciscoToggleResLesson must be defined');
  assert.equal(typeof sandbox.window._ciscoToggleResGeneral, 'function', '_ciscoToggleResGeneral must be defined');

  // Toggle unit-1
  sandbox.window._ciscoToggleResMod('unit-1');
  // Hash must remain unchanged
  assert.equal(sandbox.window.location.hash, '#/student/courses/ops401');
});
