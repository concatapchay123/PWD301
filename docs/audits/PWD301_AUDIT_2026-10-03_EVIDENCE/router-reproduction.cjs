// Read-only audit reproduction: executes the existing router with stub views.
// No network requests, application data writes, or product patches occur.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const calls = [];
const context = {
  window: {},
  document: { getElementById: () => null },
  URLSearchParams,
  console,
  StudentView: { renderAttemptResults: async (_container, id) => calls.push({ view: 'student', id }) },
  InstructorView: { renderAssessmentResultsPage: async (_container, id, courseId) => calls.push({ view: 'instructor', id, courseId }) },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.resolve('frontend/assets/js/router.js'), 'utf8'), context);
const router = new context.window.AppRouter();
const course = '7f8753c7-5788-4b04-9c06-edeedfbbd915';
const assessment = '649eb226-0712-4f35-96d1-407b1e2dc55a';
const attempt = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
const cases = [
  { route: `#/instructor/courses/${course}/assessments/${assessment}/results`, query: {}, expected: 'instructor' },
  { route: `#/instructor/assessments/${assessment}/results`, query: {}, expected: 'instructor' },
  { route: '#/instructor/exams/results', query: { id: assessment }, expected: 'instructor' },
  { route: `#/student/assessments/attempts/${attempt}/results`, query: {}, expected: 'student' },
  { route: '#/student/assessments/results', query: { id: attempt }, expected: 'student' },
];
(async () => {
  let failures = 0;
  for (const item of cases) {
    calls.length = 0;
    await router.dispatchRoute(item.route, item.query, {});
    const observed = calls[0];
    const ok = observed?.view === item.expected;
    if (!ok) failures++;
    const wirePath = observed?.view === 'student'
      ? new URL(`/student/attempt/${observed.id}/result`, 'http://127.0.0.1:5000').pathname
      : `/instructor/assessments/${observed?.id}/attempts`;
    console.log(JSON.stringify({ ...item, observed, wirePath, result: ok ? 'PASS' : 'FAIL' }));
  }
  console.log(`SUMMARY: ${cases.length - failures} passed, ${failures} failed`);
  process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 2; });
