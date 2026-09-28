const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('submission retries and reloads reuse one key per attempt', () => {
  const values = new Map();
  const sessionStorage = {
    getItem: key => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
  };
  let sequence = 0;
  const crypto = { randomUUID: () => `00000000-0000-4000-8000-${String(++sequence).padStart(12, '0')}` };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
  const load = () => {
    const window = { sessionStorage, crypto };
    vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
    return window.StudentView;
  };

  const first = load();
  const key = first.getSubmissionKey('attempt-a');
  assert.equal(first.getSubmissionKey('attempt-a'), key);
  assert.notEqual(first.getSubmissionKey('attempt-b'), key);
  assert.equal(load().getSubmissionKey('attempt-a'), key);
  assert.equal(sequence, 2);
});

test('failed answer saves are retried before submit without dropping their latest payload', async () => {
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
  const window = {};
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });

  const failed = new Set(['question-a', 'question-b']);
  const payloads = new Map([
    ['question-a', { answer_text: 'latest answer' }],
    ['question-b', { selected_choice_keys: ['choice-2'] }],
  ]);
  const calls = [];
  const save = async (questionId, payload) => {
    calls.push([questionId, payload]);
    if (questionId === 'question-a') failed.delete(questionId);
  };

  const remaining = await window.StudentView.retryFailedAnswerSaves(failed, payloads, save);
  assert.equal(remaining, 1);
  assert.equal(calls.length, 2);
  assert.equal(calls[0][1].answer_text, 'latest answer');
  assert.equal(calls[1][1].selected_choice_keys[0], 'choice-2');
});
