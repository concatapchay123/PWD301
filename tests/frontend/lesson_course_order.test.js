const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync('frontend/assets/js/views/instructor.js', 'utf8');

test('lesson move inside one chapter sends the complete course order', async () => {
  let move;
  const requests = [];
  const context = {
    currentUnits: [
      { id: 'u1', lessons: [{ id: 'first' }, { id: 'second' }] },
      { id: 'u2', lessons: [{ id: 'third' }] },
    ],
    cId: 'course',
    treeContainer: { querySelectorAll() { return [{ dataset: { unitId: 'u1', lessonIdx: '0' }, addEventListener(_event, handler) { move = handler; } }]; } },
    ApiClient: { async reorderLessons(course, ids) { requests.push([course, Array.from(ids)]); } },
    UI: { showToast() {} },
    renderTree() {},
  };
  const start = source.indexOf("      treeContainer.querySelectorAll('.btn-lesson-move-down')");
  const end = source.indexOf("      treeContainer.querySelectorAll('.btn-unit-quick-add-lesson')", start);
  vm.runInNewContext(source.slice(start, end), context);
  await move({ stopPropagation() {} });
  assert.deepEqual(requests, [['course', ['second', 'first', 'third']]]);
  assert.equal(context.currentUnits[1].lessons[0].id, 'third');
});

test('pending lesson reorder keeps the authoritative tree instead of showing applied placement', async () => {
  let move;
  const notices = [];
  const context = {
    currentUnits: [{ id: 'u1', lessons: [{ id: 'first' }, { id: 'second' }] }],
    cId: 'course',
    treeContainer: { querySelectorAll() { return [{ dataset: { unitId: 'u1', lessonIdx: '0' }, addEventListener(_event, handler) { move = handler; } }]; } },
    ApiClient: { async reorderLessons() { return { pending_approval: true, message: 'Awaiting review' }; } },
    UI: { showToast(...args) { notices.push(args); } },
    renderTree() {},
  };
  const start = source.indexOf("      treeContainer.querySelectorAll('.btn-lesson-move-down')");
  const end = source.indexOf("      treeContainer.querySelectorAll('.btn-unit-quick-add-lesson')", start);
  vm.runInNewContext(source.slice(start, end), context);
  await move({ stopPropagation() {} });
  assert.deepEqual(Array.from(context.currentUnits[0].lessons, row => row.id), ['first', 'second']);
  assert.deepEqual(notices, [['Awaiting review', 'info']]);
});

test('cross-chapter wrapper includes placement and order in one existing endpoint request', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, console });
  const requests = [];
  window.ApiClient.request = async (...args) => { requests.push(args); return {}; };
  const placement = { lesson_id: 'first', learning_unit_id: 'target' };
  await window.ApiClient.reorderLessons('course', ['second', 'first', 'third'], placement);
  assert.equal(requests.length, 1);
  assert.equal(requests[0][0], '/instructor/courses/course/lessons/reorder');
  assert.equal(requests[0][1].method, 'POST');
  assert.deepEqual(Array.from(requests[0][1].body.ordered_lesson_ids), ['second', 'first', 'third']);
  assert.equal(requests[0][1].body.move, placement);
});
