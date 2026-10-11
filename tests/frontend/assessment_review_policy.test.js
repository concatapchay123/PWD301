const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

async function renderResult(overrides = {}) {
  const window = { app: { currentUser: { full_name: 'Student' } } };
  const UI = {
    escapeHtml: value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;'),
    cleanChoiceText: value => String(value ?? ''),
    formatDateTime: () => '10/10/2026',
    showToast: () => {},
  };
  const data = { score_status: 'RELEASED', raw_score: 0, max_score: 10, answer_visibility_policy: 'IMMEDIATE', answers_visible: true, questions: [], ...overrides };
  const ApiClient = { getAttemptResult: async () => data, getAttemptAppeal: async () => ({}) };
  const container = { innerHTML: '', querySelector: () => null, querySelectorAll: () => [] };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, localStorage: { getItem: () => null }, document: { getElementById: () => null, querySelectorAll: () => [] }, UI, ApiClient, console }, { filename });
  await window.StudentView.renderAttemptResults(container, 'attempt');
  assert.match(container.innerHTML, /questions-list-container/);
  return container.innerHTML;
}

const question = {
  content: 'Question', question_type: 'MULTIPLE_CHOICE', points_assigned: 10, awarded_points: 0, is_correct: false,
  choices: [
    { content: 'Selected correct', is_selected: true, is_correct: true },
    { content: 'Selected wrong', is_selected: true, is_correct: false },
    { content: 'Missed correct', is_selected: false, is_correct: true },
  ],
};

test('full review labels selected correct, selected wrong and omitted correct inline', async () => {
  const html = await renderResult({ questions: [question] });
  assert.match(html, /Đúng \(Bạn đã chọn\)/);
  assert.match(html, /Sai \(Bạn đã chọn\)/);
  assert.match(html, /Thiếu \(Bỏ sót\)/);
  assert.doesNotMatch(html, /MC indicators/);
});

test('restricted multi-choice review uses selected option correctness, not total question grade', async () => {
  const limited = { ...question, choices: question.choices.map(c => c.is_selected ? c : { content: c.content, is_selected: false }) };
  const html = await renderResult({ answer_visibility_policy: 'CORRECT_WRONG_ONLY', answers_visible: false, questions: [limited] });
  assert.match(html, /Đúng \(Bạn đã chọn\)/);
  assert.match(html, /Sai \(Bạn đã chọn\)/);
  assert.doesNotMatch(html, /Thiếu \(Bỏ sót\)/);
});

test('delayed review keeps selected choices neutral when correctness is undisclosed', async () => {
  const hidden = { ...question, explanation: 'PRIVATE EXPLANATION', correct_answer: 'PRIVATE ANSWER', choices: [{ content: 'Chosen', is_selected: true }] };
  const html = await renderResult({ answer_visibility_policy: 'AFTER_CLOSE', answers_visible: false, questions: [hidden] });
  assert.doesNotMatch(html, /PRIVATE EXPLANATION|PRIVATE ANSWER/);
  assert.doesNotMatch(html, /✗ Sai|✓ Đúng/);
  assert.match(html, /Bạn đã chọn/);
});

test('content substrings cannot infer whether a choice was selected', async () => {
  const html = await renderResult({ questions: [{ ...question, chosen_answer: 'First correct answer', choices: [{ content: 'correct', is_selected: false, is_correct: false }] }] });
  assert.doesNotMatch(html, /✗ Sai|✓ Đúng/);
});

test('never policy renders total score safely with absent question details', async () => {
  await renderResult({ answer_visibility_policy: 'NEVER', answers_visible: false, questions: null });
});

test('instructor settings retain existing delayed answer policies instead of silently selecting full review', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js'), 'utf8');
  for (const id of ['cfg-answer-visibility-policy', 'edit-exam-answer-visibility-policy']) {
    const start = source.lastIndexOf('<select', source.indexOf(`id="${id}"`));
    const end = source.indexOf('</select>', start) + '</select>'.length;
    const template = source.slice(start, end);
    for (const policy of ['AFTER_CLOSE', 'AFTER_ALL_ATTEMPTS']) {
      const html = vm.runInNewContext('`' + template + '`', { config: { answerVisibilityPolicy: policy }, assessment: { answer_visibility_policy: policy } });
      assert.match(html, new RegExp(`value="${policy}" selected`));
    }
  }
});
