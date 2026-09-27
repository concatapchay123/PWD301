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

test('raw exam parser retains every image marker on the question', () => {
  const parsed = window.ExamParser.parseExamRaw(
    'Question 1: Question with two diagrams\n[[PWD301:IMAGE:9d1dbcd3-47a5-47b2-9a73-1de1596521b2]]\n[[PWD301:IMAGE:0d1dbcd3-47a5-47b2-9a73-1de1596521b2]]\n*A. Yes\nB. No'
  );

  assert.deepEqual([...parsed.questions[0].image_asset_ids], [
    '9d1dbcd3-47a5-47b2-9a73-1de1596521b2',
    '0d1dbcd3-47a5-47b2-9a73-1de1596521b2',
  ]);
  assert.equal(parsed.questions[0].stem, 'Question with two diagrams');
});

test('pasted image markers attach to the question at the cursor and preserve existing images', () => {
  const source = 'Question 1: A diagram\n*A. Yes\nQuestion 2: Another diagram\nB. No';
  const cursor = source.indexOf('Another diagram') + 5;
  const updated = window.ExamParser.insertImageMarkers(source, cursor, [
    '9d1dbcd3-47a5-47b2-9a73-1de1596521b2',
    '0d1dbcd3-47a5-47b2-9a73-1de1596521b2',
  ]);

  assert.match(updated, /Question 1: A diagram\n\*A\. Yes/);
  assert.match(updated, /Question 2: Another diagram\n\[\[PWD301:IMAGE:9d1dbcd3-47a5-47b2-9a73-1de1596521b2\]\]\n\[\[PWD301:IMAGE:0d1dbcd3-47a5-47b2-9a73-1de1596521b2\]\]/);
});

test('pasted image markers recognize Vietnamese question headers', () => {
  const source = 'Câu 1: Hình học\nĐề bài';
  const updated = window.ExamParser.insertImageMarkers(source, source.length, [
    '9d1dbcd3-47a5-47b2-9a73-1de1596521b2',
  ]);

  assert.match(updated, /Câu 1: Hình học\n\[\[PWD301:IMAGE:/);
});
