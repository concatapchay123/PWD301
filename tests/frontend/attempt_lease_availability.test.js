const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

function load(delivery) {
  const window = { location: { hash: '#/student/assessments/attempt?id=owned' } };
  const retry = {};
  const container = { innerHTML: '', querySelector: selector => selector === '#exam-lease-retry' ? retry : null };
  let refreshes = 0;
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/student.js', 'utf8'), {
    window, console, ApiClient: { getAttemptDelivery: async () => delivery },
    UI: { escapeHtml: String, refreshCurrentRoute() { refreshes++; } },
  });
  return { window, container, retry, refreshes: () => refreshes };
}

test('an active Attempt without a lease renders retry instead of editable answers', async () => {
  const h = load({ status: 'IN_PROGRESS', lease_token: null, questions: [{ question_id: 'private-question' }] });
  await h.window.StudentView.renderAttemptConsole(h.container, 'owned');
  assert.match(h.container.innerHTML, /id="exam-lease-unavailable"/);
  assert.doesNotMatch(h.container.innerHTML, /question-card|assessment-short-answer/);
  h.retry.onclick();
  assert.equal(h.refreshes(), 1);
});

test('a terminal Attempt still resolves its result before lease admission', async () => {
  const h = load({ status: 'PENDING_GRADING', lease_token: null });
  await h.window.StudentView.renderAttemptConsole(h.container, 'owned');
  assert.equal(h.window.location.hash, '#/student/assessments/results?id=owned');
  assert.doesNotMatch(h.container.innerHTML, /exam-lease-unavailable/);
});
