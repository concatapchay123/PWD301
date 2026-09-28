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
