const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
const window = { InstructorView: {} };
vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window }, { filename });

test('exam policy settings use browser-observable monitoring without webcam claims', () => {
  const controls = {
    'cfg-exam-layout': { value: 'FOCUS' },
    'cfg-monitoring': { checked: true },
    'cfg-fullscreen': { checked: true },
  };
  const policy = window.InstructorView.readExamPolicy({
    getElementById: id => controls[id],
  });
  assert.equal(policy.exam_layout, 'FOCUS');
  assert.equal(policy.monitoring_enabled, true);
  assert.equal(policy.request_fullscreen, true);
  assert.equal(policy.proctoring, undefined);
});

test('exam policy enforces monitoring and fullscreen defaults even without form controls', () => {
  const policy = window.InstructorView.readExamPolicy({
    getElementById: () => null,
  });
  assert.equal(policy.monitoring_enabled, true);
  assert.equal(policy.request_fullscreen, true);
});

