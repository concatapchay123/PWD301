const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function harness(reject = false) {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8').replace(/\r\n/g, '\n');
  const start = source.indexOf('    const saveAcademicBtn =');
  const end = source.indexOf('\n  }\n', start);
  const button = {}, calls = [], notices = [];
  const ctx = {
    console, cId: 'course', course: { learning_objectives: ['old'] }, customSLOs: ['old'],
    stagedPrerequisites: [{ prerequisite_course_id: 'prereq', is_new: true, reason: 'reason' }],
    harvestDOMtoSLOs: () => ['new'], loadPrerequisites: async () => {},
    document: { getElementById: id => id === 'btn-save-academic-settings' ? button : id === 'academic-pending-badge' ? null : { value: '80', checked: true } },
    UI: { showToast: (...args) => notices.push(args) },
    ApiClient: {
      updateCourse: async () => { calls.push('old-metadata'); },
      updateCourseCompletionRules: async () => { calls.push('old-rules'); },
      addCoursePrerequisite: async () => { calls.push('old-prerequisite'); },
      saveCourseAcademicSettings: async (...args) => {
        calls.push(args);
        if (reject) throw new Error('transaction rejected');
        return { course: { learning_objectives: ['new'] }, pending_approval: false };
      }
    }
  };
  vm.runInNewContext(source.slice(start, end), ctx);
  return { ctx, button, calls, notices };
}

test('016: academic Save sends one transaction manifest', async () => {
  const h = harness();
  await h.button.onclick();
  assert.equal(h.calls.length, 1);
  assert.equal(h.calls[0][0], 'course');
  assert.equal(h.calls[0][1].prerequisites.add[0].prerequisite_course_id, 'prereq');
});

test('016: acknowledged atomic Save reports success instead of a client exception', async () => {
  const h = harness();
  await h.button.onclick();
  assert.equal(h.notices.at(-1)[1], 'success');
  assert.equal(h.notices.some(notice => notice[1] === 'error'), false);
  assert.equal(h.button.disabled, false);
});

test('016: rejected academic transaction preserves SLO draft and staged prerequisites', async () => {
  const h = harness(true);
  await h.button.onclick();
  assert.equal(h.ctx.customSLOs[0], 'old');
  assert.equal(h.ctx.course.learning_objectives[0], 'old');
  assert.equal(h.ctx.stagedPrerequisites[0].is_new, true);
  assert.equal(h.notices.at(-1)[1], 'error');
});
