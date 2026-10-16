const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function harness(reject = false) {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8').replace(/\r\n/g, '\n');
  const start = source.indexOf('    const saveBtn =', source.indexOf('static async openCourseLandingEditorModal'));
  const end = source.indexOf('\n  }\n', start);
  const button = {}, calls = [], notices = [], closed = [];
  const window = {}; vm.runInNewContext(source, { window, console });
  const ctx = {
    console, cId: 'course', course: { learning_objectives: ['old'] }, customSLOs: ['old'],
    InstructorView: window.InstructorView, academicRules: {}, slos: ['new'], initialPrerequisites: [], selectedPrerequisites: [{ prerequisite_course_id: 'prereq', min_grade_point: 5 }],

    document: { getElementById: id => id === 'btn-save-unified-intro' ? button : { value: id === 'unified-contact-email' ? 'teacher@example.test' : id === 'unified-min-score' ? '5' : '80', checked: true } },
    UI: { showToast: (...args) => notices.push(args), closeModal: () => closed.push(true) },
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
  return { ctx, button, calls, notices, closed };
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
  assert.equal(h.closed.length, 1);
});

test('016: rejected academic transaction preserves SLO draft and staged prerequisites', async () => {
  const h = harness(true);
  await h.button.onclick();
  assert.equal(h.ctx.customSLOs[0], 'old');
  assert.equal(h.ctx.course.learning_objectives[0], 'old');
  assert.equal(h.ctx.selectedPrerequisites[0].prerequisite_course_id, 'prereq');
  assert.equal(h.closed.length, 0);
  assert.equal(h.button.disabled, false);
  assert.equal(h.notices.at(-1)[1], 'error');
});
