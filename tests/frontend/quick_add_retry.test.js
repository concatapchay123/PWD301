const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function setup(createAssessmentQuestion) {
  const source = fs.readFileSync('frontend/assets/js/views/instructor-exams.js', 'utf8');
  const start = source.indexOf("document.getElementById('form-quick-add-question')?.addEventListener('submit'");
  const end = source.indexOf('\n      });', start) + '\n      });'.length;
  const fields = {
    'new-q-stem': { value: 'One question' }, 'new-q-bloom': { value: 'UNDERSTAND' },
    'new-q-points': { value: '1' }, 'btn-submit-add-q': { disabled: false },
  };
  let submit;
  fields['form-quick-add-question'] = { addEventListener: (_event, callback) => { submit = callback; } };
  let uuidCount = 0;
  const context = {
    document: { getElementById: id => fields[id] || null },
    crypto: { randomUUID: () => `stable-${++uuidCount}` },
    UI: { showToast() {} }, ApiClient: { createAssessmentQuestion },
    qTypeSelect: { value: 'ESSAY' }, addModal: { classList: { add() {} } },
    assessmentId: 'owned-assessment', questions: [], render() {},
  };
  vm.runInNewContext(`let quickAddRequestId = null; let quickAddPending = false; ${source.slice(start, end)}`, context);
  return { submit: () => submit({ preventDefault() {} }), fields, context };
}

test('Quick Add retains creation identity after lost ACK and rotates it only after success', async () => {
  const calls = [];
  const env = setup(async (_assessment, payload) => {
    calls.push({ ...payload });
    if (calls.length === 1) throw new Error('acknowledgement lost');
    return { question: { question_id: payload.client_question_id, content: payload.content } };
  });
  await env.submit();
  assert.equal(env.fields['btn-submit-add-q'].disabled, false);
  await env.submit();
  assert.equal(calls[0].client_question_id, calls[1].client_question_id);
  assert.equal(env.context.questions.length, 1);
  await env.submit();
  assert.notEqual(calls[1].client_question_id, calls[2].client_question_id);
});

test('Quick Add concurrent clicks admit one pending creation request', async () => {
  let finish;
  let calls = 0;
  const env = setup((_assessment, payload) => {
    calls++;
    return new Promise(resolve => { finish = () => resolve({ question: { question_id: payload.client_question_id } }); });
  });
  const pending = env.submit();
  assert.equal(env.fields['btn-submit-add-q'].disabled, true);
  await env.submit();
  assert.equal(calls, 1);
  finish();
  await pending;
  assert.equal(env.fields['btn-submit-add-q'].disabled, false);
});
