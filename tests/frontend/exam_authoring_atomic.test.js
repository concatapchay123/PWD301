const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function setup(api) {
  let draft = { assessmentId: 'assessment-a', courseId: 'course-a', questions: [{ stem: 'Question A' }] };
  const scope = { userId: 'owner-a', role: 'INSTRUCTOR' };
  const window = { InstructorView: {}, ExamStore: { getDraft: () => draft, getCurrentScope: () => scope, saveDraft: change => { draft = { ...draft, ...change }; }, clearDraft: () => { draft = { questions: [] }; } } };
  const context = { window, document: {}, ApiClient: {
    getAssessmentDetail: async () => ({ assessment_id: draft.assessmentId, course_id: draft.courseId,
      status: 'DRAFT', questions: draft.questions.map((q, index) => ({ question_id: q.question_id,
        position: index + 1, points: 1, question: { current_revision: { revision_no: 1 } } })) }),
    ...api
  }, crypto: { randomUUID: () => 'stable-question-a' }, console };
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/instructor-exams.js', 'utf8'), context);
  return { view: window.InstructorView, getDraft: () => draft, scope };
}
test('079: rejected atomic authoring keeps stable retry IDs and local draft', async () => {
  const bodies = [];
  const env = setup({ saveAssessmentAuthoring: async (id, body) => { bodies.push(body); throw new Error('atomic failure'); } });
  for (let i = 0; i < 2; i++) {
    await assert.rejects(env.view.saveExamAuthoring('assessment-a', {}, [{ content: 'Question A' }]), /atomic failure/);
  }
  assert.equal(env.getDraft().questions[0].client_question_id, 'stable-question-a');
  assert.equal(bodies[0].questions[0].client_question_id, bodies[1].questions[0].client_question_id);
});
test('079: authoritative acknowledgement checkpoints IDs for publish retry', async () => {
  const env = setup({ saveAssessmentAuthoring: async () => ({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }) });
  await env.view.saveExamAuthoring('assessment-a', {}, [{ content: 'Question A' }]);
  assert.equal(env.getDraft().questions[0].question_id, 'server-question-a');
});
test('079: late acknowledgement cannot replace a different owner draft', async () => {
  let resolve;
  const env = setup({ saveAssessmentAuthoring: () => new Promise(done => { resolve = done; }) });
  const pending = env.view.saveExamAuthoring('assessment-a', {}, [{ content: 'Question A' }]);
  env.scope.userId = 'owner-b';
  resolve({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] });
  await assert.rejects(pending, /context changed/i);
  assert.equal(env.getDraft().questions[0].question_id, undefined);
});

test('024: unsupported Bloom levels are rejected before saving', () => {
  const env = setup({});
  assert.equal(env.view.normalizeExamBloom('NHẬN BIẾT'), 'REMEMBER');
  assert.equal(env.view.normalizeExamBloom('UNDERSTAND'), 'UNDERSTAND');
  assert.throws(() => env.view.normalizeExamBloom('ANALYZE'), /ANALYZE/);
});

test('079: API client sends one authoring request with settings and manifest', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, console });
  let captured;
  window.ApiClient.request = async (url, options) => { captured = { url, options }; return {}; };
  const payload = { assessment: { title: 'Snapshot' }, questions: [] };
  await window.ApiClient.saveAssessmentAuthoring('assessment-a', payload);
  assert.equal(captured.url, '/instructor/assessments/assessment-a/authoring');
  assert.equal(captured.options.method, 'POST');
  assert.equal(captured.options.body, payload);
});

test('079: API authoring wrapper returns the acknowledged data from the JSON envelope', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, console });
  const data = { assessment_id: 'owned-assessment', questions: [{ question_id: 'saved-question' }], authoring_token: 'a'.repeat(64) };
  window.ApiClient.request = async () => ({ success: true, data, error: null });
  assert.equal(await window.ApiClient.saveAssessmentAuthoring('owned-assessment', {}), data);
});

test('079: numeric local display ordinals are not server question identities', async () => {
  let body;
  const env = setup({ saveAssessmentAuthoring: async (_id, payload) => {
    body = payload;
    return { authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] };
  } });
  env.getDraft().questions[0].id = 1;
  await env.view.saveExamAuthoring('assessment-a', {}, [{ content: 'Question A' }]);
  assert.equal(body.questions[0].client_question_id, 'stable-question-a');
  assert.equal(body.questions[0].question_id, undefined);
});

test('079: create acknowledgement cannot checkpoint into another owner draft', async () => {
  let resolve;
  const env = setup({ createAssessment: () => new Promise(done => { resolve = done; }) });
  env.getDraft().assessmentId = null;
  const pending = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  await Promise.resolve();
  env.scope.userId = 'owner-b';
  resolve({ assessment_id: 'new-assessment' });
  await assert.rejects(pending, /context changed/i);
  assert.equal(env.getDraft().assessmentId, null);
});

test('079: publish acknowledgement cannot clear another owner draft', async () => {
  let resolve;
  const env = setup({
    saveAssessmentAuthoring: async () => ({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }),
    publishAssessment: () => new Promise(done => { resolve = done; })
  });
  const pending = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  while (!resolve) await new Promise(done => setImmediate(done));
  env.scope.userId = 'owner-b';
  resolve({});
  await assert.rejects(pending, /context changed/i);
  assert.equal(env.getDraft().questions.length, 1);
});

test('079: successful publish clears only the acknowledged draft', async () => {
  const calls = [];
  const env = setup({
    saveAssessmentAuthoring: async () => { calls.push('save'); return { authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }; },
    publishAssessment: async () => { calls.push('publish'); }
  });
  const result = await env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  assert.equal(result.assessmentId, 'assessment-a');
  assert.deepEqual(calls, ['save', 'publish']);
  assert.equal(env.getDraft().questions.length, 0);
});

test('079: publish acknowledgement retains title and settings edited during the request', async () => {
  let resolve;
  const env = setup({
    saveAssessmentAuthoring: async () => ({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }),
    publishAssessment: () => new Promise(done => { resolve = done; })
  });
  const pending = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  while (!resolve) await new Promise(done => setImmediate(done));
  env.getDraft().title = 'Later title';
  env.getDraft().config = { duration: 20 };
  resolve({});
  await assert.rejects(pending, /published.*snapshot/i);
  assert.equal(env.getDraft().title, 'Later title');
  assert.equal(env.getDraft().config.duration, 20);
});

test('079: authoring acknowledgement retains later settings without replacing question IDs', async () => {
  let resolve;
  const env = setup({ saveAssessmentAuthoring: () => new Promise(done => { resolve = done; }) });
  const pending = env.view.saveExamAuthoring('assessment-a', {}, [{ content: 'Question A' }]);
  env.getDraft().config = { duration: 20 };
  resolve({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] });
  await assert.rejects(pending, /context changed/i);
  assert.equal(env.getDraft().config.duration, 20);
  assert.equal(env.getDraft().questions[0].question_id, undefined);
});

test('079: creation acknowledgement retains a title changed during creation', async () => {
  let resolve;
  const env = setup({ createAssessment: () => new Promise(done => { resolve = done; }) });
  env.getDraft().assessmentId = null;
  const pending = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  env.getDraft().title = 'Later title';
  resolve({ assessment_id: 'new-assessment' });
  await assert.rejects(pending, /context changed/i);
  assert.equal(env.getDraft().title, 'Later title');
  assert.equal(env.getDraft().assessmentId, null);
});

test('079: lost publish ACK recovers matching published snapshot without rewriting locked questions', async () => {
  let published = false;
  let authoringCalls = 0;
  const env = setup({
    saveAssessmentAuthoring: async () => {
      authoringCalls++;
      if (published) throw new Error('first student started: authoring locked');
      return { authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] };
    },
    getAssessmentDetail: async () => ({ assessment_id: 'assessment-a', course_id: 'course-a', authoring_token: 'a'.repeat(64),
      title: 'Submitted title', status: published ? 'PUBLISHED' : 'DRAFT', first_attempt_started_at: published ? 'started' : null,
      questions: [{ question_id: 'server-question-a', position: 1, points: 1,
        question: { current_revision: { revision_no: 1 } } }] }),
    publishAssessment: async () => { published = true; throw new Error('ACK lost'); }
  });
  await assert.rejects(env.view.publishExamDraft('course-a', { title: 'Submitted title' }, [{ content: 'Question A' }]), /ACK lost/);
  const result = await env.view.publishExamDraft('course-a', { title: 'Submitted title' }, [{ question_id: 'server-question-a', content: 'Question A' }]);
  assert.equal(result.assessmentId, 'assessment-a');
  assert.equal(authoringCalls, 1);
  assert.equal(env.getDraft().questions.length, 0);
});

test('079: server identity checkpoints retain matrix approval after publish failure and reload', async () => {
  const values = new Map();
  const window = { InstructorView: {}, app: { currentUser: { id: 'owner-a', active_role: 'INSTRUCTOR' } } };
  const context = { window, document: {}, console, crypto: { randomUUID: () => 'stable-question-a' },
    localStorage: { getItem: key => values.get(key) || null, setItem: (key, value) => values.set(key, value) },
    ApiClient: { saveAssessmentAuthoring: async () => ({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }),
      getAssessmentDetail: async () => ({ assessment_id: 'assessment-a', course_id: 'course-a', authoring_token: 'a'.repeat(64), status: 'DRAFT',
        questions: [{ question_id: 'server-question-a', position: 1, points: 1,
          question: { current_revision: { revision_no: 1 } } }] }),
      publishAssessment: async () => { throw new Error('publish unavailable'); } } };
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/exam-store.js', 'utf8'), context);
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/instructor-exams.js', 'utf8'), context);
  window.ExamStore.saveDraft({ assessmentId: 'assessment-a', courseId: 'course-a', methodSelected: true,
    questions: [{ stem: 'Question A' }], matrixConfirmed: true, config: { examPassword: 'fixture-secret' } });
  await assert.rejects(window.InstructorView.publishExamDraft('course-a', {}, [{ content: 'Question A' }]), /publish unavailable/);
  window.ExamStore.clearMemoryDraft();
  const restored = window.ExamStore.getDraft();
  assert.equal(restored.questions[0].question_id, 'server-question-a');
  assert.equal(restored.matrixConfirmed, true);
  assert.equal(restored.publishPending.assessmentId, 'assessment-a');
  assert.equal(Array.from(values.values()).some(value => value.includes('fixture-secret')), false);
});

test('079: concurrent publish clicks cannot dispatch a second authoring request', async () => {
  const resolvers = [];
  let authoringCalls = 0;
  const env = setup({
    saveAssessmentAuthoring: () => { authoringCalls++; return new Promise(done => { resolvers.push(done); }); },
    publishAssessment: async () => {}
  });
  const first = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  const second = env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]);
  for (const resolve of resolvers) resolve({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] });
  await assert.rejects(second, /already in progress/i);
  assert.equal(authoringCalls, 1);
  await first;
});

test('079: publisher uses atomic ACK token and does not rebase onto another GET snapshot', async () => {
  let getCalls = 0;
  let sentToken;
  const env = setup({
    saveAssessmentAuthoring: async () => ({ authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }),
    getAssessmentDetail: async () => { getCalls++; return { authoring_token: 'b'.repeat(64) }; },
    publishAssessment: async (_id, token) => { sentToken = token; throw new Error('authoring changed: 409'); }
  });
  await assert.rejects(env.view.publishExamDraft('course-a', {}, [{ content: 'Question A' }]), /409/);
  assert.equal(sentToken, 'a'.repeat(64));
  assert.equal(getCalls, 0);
  assert.equal(env.getDraft().questions.length, 1);
});

test('079: API publish carries optional token while preserving empty legacy publication', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, console });
  const calls = [];
  window.ApiClient.request = async (url, options) => { calls.push({ url, options }); };
  await window.ApiClient.publishAssessment('assessment-a', 'a'.repeat(64));
  await window.ApiClient.publishAssessment('assessment-a');
  assert.equal(calls[0].options.body.expected_authoring_token, 'a'.repeat(64));
  assert.equal(calls[1].options.body, undefined);
});

for (const mismatch of ['local title', 'server revision', 'server points', 'server settings']) {
  test(`079: lost publish ACK retains draft when ${mismatch} changed`, async () => {
    let published = false;
    let authoringCalls = 0;
    const detail = { assessment_id: 'assessment-a', course_id: 'course-a', authoring_token: 'a'.repeat(64), title: 'Submitted title',
      questions: [{ question_id: 'server-question-a', position: 1, points: 1,
        question: { current_revision: { revision_no: 1 } } }] };
    const env = setup({
      saveAssessmentAuthoring: async () => { authoringCalls++; return { authoring_token: 'a'.repeat(64), questions: [{ question_id: 'server-question-a' }] }; },
      getAssessmentDetail: async () => ({ ...detail, status: published ? 'PUBLISHED' : 'DRAFT' }),
      publishAssessment: async () => { published = true; throw new Error('ACK lost'); }
    });
    await assert.rejects(env.view.publishExamDraft('course-a', { title: 'Submitted title' }, [{ content: 'Question A' }]), /ACK lost/);
    if (mismatch === 'local title') env.getDraft().title = 'Later title';
    if (mismatch === 'server revision') detail.questions[0].question.current_revision.revision_no++;
    if (mismatch === 'server points') detail.questions[0].points = 2;
    if (mismatch === 'server settings') detail.title = 'Other title';
    if (mismatch.startsWith('server ')) detail.authoring_token = 'b'.repeat(64);
    await assert.rejects(env.view.publishExamDraft('course-a', { title: 'Submitted title' }, [{ content: 'Question A' }]), /different snapshot/i);
    assert.equal(env.getDraft().questions.length, 1);
    assert.equal(authoringCalls, 1);
  });
}
