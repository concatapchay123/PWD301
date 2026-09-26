const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const window = {};
const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/ui.js');
vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window }, { filename: sourcePath });

test('raw exam parser keeps a question image marker out of the visible stem', () => {
  const parsed = window.ExamParser.parseExamRaw(
    'Câu 1: Question with a diagram\n[[PWD301:IMAGE:9d1dbcd3-47a5-47b2-9a73-1de1596521b2]]\n*A. Yes\nB. No'
  );

  assert.equal(parsed.questions[0].image_asset_id, '9d1dbcd3-47a5-47b2-9a73-1de1596521b2');
  assert.equal(parsed.questions[0].stem, 'Question with a diagram');
});
