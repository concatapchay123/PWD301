const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadRouter() {
  const calls = [];
  const context = {
    window: {},
    document: { getElementById: () => null },
    URLSearchParams,
    console,
    StudentView: {
      renderAttemptResults: async (_container, id) => calls.push({ view: 'student', id }),
    },
    InstructorView: {
      renderAssessmentResultsPage: async (_container, id, courseId) =>
        calls.push({ view: 'instructor', id, courseId }),
    },
  };
  vm.createContext(context);
  const routerPath = path.resolve(__dirname, '../../frontend/assets/js/router.js');
  vm.runInContext(fs.readFileSync(routerPath, 'utf8'), context, { filename: routerPath });
  return { router: new context.window.AppRouter(), calls };
}

function loadStudentView() {
  const context = { window: {}, document: {}, console };
  vm.createContext(context);
  const viewPath = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
  vm.runInContext(fs.readFileSync(viewPath, 'utf8'), context, { filename: viewPath });
  return context.window.StudentView;
}

test('dispatchRoute keeps instructor result routes in the instructor renderer', async () => {
  const { router, calls } = loadRouter();
  const course = '7f8753c7-5788-4b04-9c06-edeedfbbd915';
  const assessment = '649eb226-0712-4f35-96d1-407b1e2dc55a';
  const attempt = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
  const cases = [
    {
      route: `#/instructor/courses/${course}/assessments/${assessment}/results`,
      query: {},
      expected: { view: 'instructor', id: assessment, courseId: course },
    },
    {
      route: `#/instructor/assessments/${assessment}/results`,
      query: {},
      expected: { view: 'instructor', id: assessment, courseId: null },
    },
    {
      route: '#/instructor/exams/results',
      query: { id: assessment },
      expected: { view: 'instructor', id: assessment, courseId: null },
    },
    {
      route: `#/student/assessments/attempts/${attempt}/results`,
      query: {},
      expected: { view: 'student', id: attempt },
    },
    {
      route: '#/student/assessments/results',
      query: { id: attempt },
      expected: { view: 'student', id: attempt },
    },
  ];

  for (const item of cases) {
    calls.length = 0;
    await router.dispatchRoute(item.route, item.query, {});
    assert.deepEqual(calls[0], item.expected, item.route);
    assert.equal(calls.length, 1, item.route);
  }
});

test('administrator attempt detail flow provides a localized reason retry instead of raw backend text', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'),
    'utf8',
  );
  assert.match(source, /Lý do truy cập/);
  assert.match(source, /attempt-detail-reason/);
  assert.match(source, /getInstructorAttemptResult\(attemptId, accessReason\)/);
});

test('student result score state does not invent values while score is hidden', () => {
  const studentView = loadStudentView();
  assert.deepEqual(
    JSON.parse(JSON.stringify(studentView.getAttemptScoreState({ score_status: 'SCORE_HIDDEN', raw_score: null }))),
    {
      released: false,
      totalScore: null,
      maxPoints: null,
      passingScore: null,
      isPassed: null,
      scorePct: null,
    },
  );
});

test('student result action downloads a PDF attachment instead of invoking print', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '../../frontend/assets/js/views/student.js'),
    'utf8',
  );
  assert.match(source, /download-student-result-pdf-btn/);
  assert.match(source, /\/result\.pdf/);
  assert.doesNotMatch(source, /window\.print\(\)/);
});

test('student result does not fabricate signature, instructor, or duration values', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '../../frontend/assets/js/views/student.js'),
    'utf8',
  );
  assert.doesNotMatch(source, /7f8a92b1\.\.\.10243/);
  assert.doesNotMatch(source, /Trần Hoàng Nam/);
  assert.doesNotMatch(source, /data\.duration_minutes \|\| 45/);
  assert.match(source, /signature_hash/);
});

test('instructor attempt detail modal exposes dialog semantics and keyboard close support', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'),
    'utf8',
  );
  assert.match(source, /modal\.setAttribute\('role', 'dialog'\)/);
  assert.match(source, /modal\.setAttribute\('aria-modal', 'true'\)/);
  assert.match(source, /keydown[\s\S]*Escape/);
  assert.match(source, /aria-label=\"Đóng chi tiết bài làm\"/);
});
