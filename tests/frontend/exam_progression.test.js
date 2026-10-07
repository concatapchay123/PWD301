const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function createStore() {
  const values = new Map();
  const window = {};
  const localStorage = {
    getItem: key => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/exam-store.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, localStorage, console }, { filename });
  return window.ExamStore;
}

test('exam steps open only after the preceding step is complete', () => {
  const store = createStore();
  assert.equal(store.canVisitStep(2), false);
  assert.equal(store.canVisitStep(3), false);
  assert.equal(store.canVisitStep(4), false);

  store.saveDraft({ sourceMethod: 'interactive', methodSelected: true, courseId: 'course-1' });
  assert.equal(store.canVisitStep(2), true);
  assert.equal(store.canVisitStep(3), false);

  store.saveDraft({ questions: [{ stem: 'Question 1' }] });
  assert.equal(store.canVisitStep(3), true);
  assert.equal(store.canVisitStep(4), false);

  store.saveDraft({ matrixConfirmed: true });
  assert.equal(store.canVisitStep(4), true);
  store.saveDraft({ questions: [{ stem: 'Revised question' }] });
  assert.equal(store.canVisitStep(4), false);
  store.saveDraft({ matrixConfirmed: true });
  store.saveDraft({ questions: [] });
  assert.equal(store.canVisitStep(4), false);
  assert.equal(store.canVisitStep(2), true);
});

test('SYNC-042: account-scoped draft isolation, no global legacy hydration, and password memory-only', () => {
  const sharedStorage = new Map();
  // Simulate legacy global draft in localStorage
  sharedStorage.set('pwd301_azota_exam_draft', JSON.stringify({
    title: 'Legacy Global Draft',
    questions: [{ stem: 'Global Question' }]
  }));

  const makeContext = (currentUser) => {
    const window = {
      app: { currentUser }
    };
    const localStorage = {
      getItem: key => sharedStorage.get(key) || null,
      setItem: (key, val) => sharedStorage.set(key, val),
      removeItem: key => sharedStorage.delete(key),
    };
    const filename = path.resolve(__dirname, '../../frontend/assets/js/exam-store.js');
    vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, localStorage, console }, { filename });
    return window.ExamStore;
  };

  // Instructor A creates a draft with password
  const storeA = makeContext({ id: 'instructor-a', active_role: 'INSTRUCTOR' });
  storeA.saveDraft({
    title: 'Draft A',
    questions: [{ stem: 'Question A' }],
    config: { examPassword: 'SecretPasswordA!', duration: 60 }
  });

  // Verify Instructor A memory has password, but durable storage does NOT persist plain password
  const memoryA = storeA.getDraft();
  assert.equal(memoryA.title, 'Draft A');
  assert.equal(memoryA.config.examPassword, 'SecretPasswordA!');

  const durableA = JSON.parse(sharedStorage.get('pwd301_azota_exam_draft_instructor-a'));
  assert.equal(durableA.title, 'Draft A');
  assert.equal(durableA.config.examPassword, '', 'Durable storage must sanitize password to empty string');

  // Instructor B must NOT read Instructor A draft, AND must NOT hydrate legacy global draft
  const storeB = makeContext({ id: 'instructor-b', active_role: 'INSTRUCTOR' });
  const draftB = storeB.getDraft();
  assert.notEqual(draftB.title, 'Draft A', 'Instructor B must not read Instructor A draft');
  assert.notEqual(draftB.title, 'Legacy Global Draft', 'Instructor B must not hydrate legacy global draft');
  assert.equal(storeB.hasDraft(), false, 'Instructor B has no draft yet');

  // Instructor B saves their own draft
  storeB.saveDraft({ title: 'Draft B', questions: [{ stem: 'Question B' }] });
  assert.equal(storeB.getDraft().title, 'Draft B');

  // Clearing Draft A must not touch Draft B or legacy
  storeA.clearDraft();
  assert.equal(storeA.hasDraft(), false);
  assert.equal(sharedStorage.has('pwd301_azota_exam_draft_instructor-a'), false);
  assert.equal(sharedStorage.has('pwd301_azota_exam_draft_instructor-b'), true, 'Draft B must still exist');
  assert.equal(sharedStorage.has('pwd301_azota_exam_draft'), true, 'Legacy draft must not be deleted by clearDraft A');

  // Student role must not hydrate authoring draft
  const storeStudent = makeContext({ id: 'student-c', active_role: 'STUDENT' });
  assert.equal(storeStudent.hasDraft(), false, 'Student must not have or hydrate authoring draft');
  assert.equal(storeStudent.getDraft().title, 'De_thi_moi.docx');
});

test('SYNC-043: truthful storage failure handling and recovery on subsequent success', () => {
  let failStorage = true;
  const storage = new Map();
  const window = {
    app: { currentUser: { id: 'instructor-fail', active_role: 'INSTRUCTOR' } }
  };
  const localStorage = {
    getItem: key => storage.get(key) || null,
    setItem: (key, val) => {
      if (failStorage) {
        throw new Error('QuotaExceededError: storage full');
      }
      storage.set(key, val);
    },
    removeItem: key => storage.delete(key),
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/exam-store.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, localStorage, console }, { filename });
  const store = window.ExamStore;

  // When storage fails
  const draft = store.saveDraft({ title: 'Attempt 1', questions: [{ stem: 'Q1' }] });
  assert.equal(draft.storageFailed, true, 'storageFailed flag must be set on failure');
  assert.equal(draft.lastSaved, null, 'lastSaved must be null when persistence fails');
  assert.equal(draft.title, 'Attempt 1', 'Memory state must remain intact');

  // When retry succeeds
  failStorage = false;
  const retryDraft = store.saveDraft({ title: 'Attempt 1 Retry' });
  assert.equal(Boolean(retryDraft.storageFailed), false, 'storageFailed flag must be cleared on success');
  assert.ok(retryDraft.lastSaved, 'lastSaved must be a valid timestamp on successful persistence');
  assert.equal(retryDraft.title, 'Attempt 1 Retry');
  assert.ok(storage.has('pwd301_azota_exam_draft_instructor-fail'));
});


test('SYNC-042 same runtime A to B to A clears memory and restores only scoped durable draft', () => {
  const storage = new Map();
  const window = { app: { currentUser: { id: 'a', active_role: 'INSTRUCTOR' } } };
  const localStorage = {
    getItem: key => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: key => storage.delete(key),
  };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/exam-store.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, localStorage, console }, { filename });
  const store = window.ExamStore;
  store.saveDraft({ title: 'A', questions: [{ stem: 'Private A' }], config: { examPassword: 'secret-A' } });
  window.app.currentUser = { id: 'b', active_role: 'INSTRUCTOR' };
  assert.equal(store.hasDraft(), false);
  assert.notEqual(store.getDraft().title, 'A');
  assert.notEqual(store.getDraft().config.examPassword, 'secret-A');
  store.saveDraft({ title: 'B', questions: [{ stem: 'Private B' }] });
  window.app.currentUser = { id: 'a', active_role: 'INSTRUCTOR' };
  assert.equal(store.getDraft().title, 'A');
  assert.equal(store.getDraft().config.examPassword, '');
  window.app.currentUser = { id: 'a', active_role: 'STUDENT' };
  assert.equal(store.hasDraft(), false);
  assert.notEqual(store.getDraft().title, 'A');
  store.saveDraft({ title: 'Forbidden student draft' });
  assert.equal(JSON.parse(storage.get('pwd301_azota_exam_draft_a')).title, 'A');
  window.app.currentUser = { id: 'a', active_role: 'INSTRUCTOR' };
  store.clearDraft();
  assert.equal(storage.has('pwd301_azota_exam_draft_a'), false);
  assert.equal(JSON.parse(storage.get('pwd301_azota_exam_draft_b')).title, 'B');
});

test('SYNC-029: debounced text input flushes dirty answers before submit or navigation', async () => {
  const savedAnswers = [];
  const textDebounceTimers = new Map();
  const inputEl = { dataset: { qIndex: '0' }, value: '   My Typed Answer   ' };
  const cardEl = { dataset: { qid: 'q-uuid-1' }, closest: () => cardEl };
  inputEl.closest = (sel) => sel === '.question-card' ? cardEl : null;

  const saveShortAnswer = async (input) => {
    savedAnswers.push({ qid: cardEl.dataset.qid, answer_text: input.value.trim() });
  };

  // 1. Simulate input event debounce timer
  let timerFired = false;
  textDebounceTimers.set(inputEl, setTimeout(() => { timerFired = true; }, 1200));
  assert.equal(textDebounceTimers.has(inputEl), true);
  assert.equal(savedAnswers.length, 0);

  // 2. Simulate flush before submit or beforeunload
  const flushAll = async () => {
    const promises = [];
    if (textDebounceTimers.has(inputEl)) {
      clearTimeout(textDebounceTimers.get(inputEl));
      textDebounceTimers.delete(inputEl);
      promises.push(saveShortAnswer(inputEl));
    }
    await Promise.allSettled(promises);
  };

  await flushAll();
  assert.equal(textDebounceTimers.size, 0);
  assert.equal(savedAnswers.length, 1);
  assert.equal(savedAnswers[0].qid, 'q-uuid-1');
  assert.equal(savedAnswers[0].answer_text, 'My Typed Answer');
});
