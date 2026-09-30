const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const window = {};
const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/ui.js');
vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window }, { filename: sourcePath });

test('ExamParser supports multi-image markers inline and on dedicated lines with A-F choices', () => {
  const rawText = `Câu 1: Cho sơ đồ mạch điện [[PWD301:IMAGE:11111111-1111-1111-1111-111111111111]]
[[PWD301:EXTRACTED_IMAGE:2]]
*A. Lựa chọn A
B. Lựa chọn B
C. Lựa chọn C
D. Lựa chọn D
E. Lựa chọn E
Lời giải: Giải thích chi tiết`;

  const parsed = window.ExamParser.parseExamRaw(rawText);
  assert.equal(parsed.success, true);
  assert.equal(parsed.questions.length, 1);

  const q = parsed.questions[0];
  assert.equal(q.number, 1);
  assert.equal(q.choices.length, 5);
  assert.equal(q.choices[0].label, 'A');
  assert.equal(q.choices[0].is_correct, true);
  assert.equal(q.choices[4].label, 'E');
  assert.equal(q.choices[4].is_correct, false);

  assert.equal(q.image_asset_id, '11111111-1111-1111-1111-111111111111');
  assert.equal(q.image_asset_ids.length, 2);
  assert.equal(q.image_asset_ids[0], '11111111-1111-1111-1111-111111111111');
  assert.equal(q.image_asset_ids[1], '2');
  assert.equal(q.resources.length, 2);
  assert.equal(q.resources[0].asset_id, '11111111-1111-1111-1111-111111111111');
  assert.equal(q.resources[1].asset_id, '2');

  // Test generateRawFromQuestions includes image markers
  const generatedRaw = window.ExamParser.generateRawFromQuestions(parsed.questions);
  assert.match(generatedRaw, /11111111-1111-1111-1111-111111111111/);
  assert.match(generatedRaw, /\*A\. Lựa chọn A/);
  assert.match(generatedRaw, /E\. Lựa chọn E/);
});
