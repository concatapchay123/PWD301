const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const code = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js'), 'utf8');

test('matching preview offers one answer per prompt and can score that choice', () => {
  const window = { InstructorView: {} };
  vm.runInNewContext(code, { window, document: {} }, { filename: 'instructor-exams.js' });
  const rows = window.InstructorView.buildInteractiveMatchPreview([
    { left: 'HTTP', right: '80' },
    { left: 'HTTPS', right: '443' }
  ]);
  assert.equal(rows.length, 2);
  assert.deepEqual(JSON.parse(JSON.stringify(rows[0])), {
    left: 'HTTP', expected: '80', options: ['80', '443']
  });
  assert.deepEqual(JSON.parse(JSON.stringify(rows[1])), {
    left: 'HTTPS', expected: '443', options: ['80', '443']
  });
});
