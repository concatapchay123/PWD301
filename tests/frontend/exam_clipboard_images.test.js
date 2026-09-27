const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('pasted image placeholders become question image markers in order', () => {
  const window = { InstructorView: {} };
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window }, { filename });
  const ids = [
    '9d1dbcd3-47a5-47b2-9a73-1de1596521b2',
    '9d1dbcd3-47a5-47b2-9a73-1de1596521b3',
  ];
  const source = 'Câu 1: Tam giác\n[[PWD301:PASTE_IMAGE:0]]\n*A. Đúng\nB. Sai\nCâu 2: Hình tròn\n[[PWD301:PASTE_IMAGE:1]]\n*A. Đúng\nB. Sai';
  const result = window.InstructorView.resolvePastedExamImages(source, ids);
  assert.match(result, new RegExp(`IMAGE:${ids[0]}`));
  assert.match(result, new RegExp(`IMAGE:${ids[1]}`));
  assert.doesNotMatch(result, /PASTE_IMAGE/);
});
