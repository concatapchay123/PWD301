const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const examViewPath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
const examViewContent = fs.readFileSync(examViewPath, 'utf8');

test('U05 - SYNC-024: Bloom taxonomy dropdown restricted to canonical tiers', () => {
  // Matrix select must not contain non-canonical levels ANALYZE, EVALUATE, CREATE
  const matrixBloomMatch = examViewContent.match(/class="matrix-bloom-select[\s\S]*?<\/select>/);
  assert.ok(matrixBloomMatch, 'matrix-bloom-select must exist');
  const matrixSelectHtml = matrixBloomMatch[0];
  assert.ok(matrixSelectHtml.includes('value="REMEMBER"'), 'Must have REMEMBER');
  assert.ok(matrixSelectHtml.includes('value="UNDERSTAND"'), 'Must have UNDERSTAND');
  assert.ok(matrixSelectHtml.includes('value="APPLY"'), 'Must have APPLY');
  assert.ok(!matrixSelectHtml.includes('value="ANALYZE"'), 'Must NOT have ANALYZE in matrix');
  assert.ok(!matrixSelectHtml.includes('value="EVALUATE"'), 'Must NOT have EVALUATE in matrix');
  assert.ok(!matrixSelectHtml.includes('value="CREATE"'), 'Must NOT have CREATE in matrix');
});

test('U05 - SYNC-025: No dummy ["Đáp án"] fallback for short answers', () => {
  assert.ok(!examViewContent.includes("payload.accepted_answers = ans.length > 0 ? ans : ['Đáp án']"),
    'Must not silently fall back to ["Đáp án"]');
  assert.ok(!examViewContent.includes("ans.length > 0 ? ans : ['Đáp án']"),
    'Must not have ["Đáp án"] fallback anywhere in publish or authoring');
});

test('U05 - SYNC-005: Publish handler must NOT have blind sequential partial fallback', () => {
  assert.ok(!examViewContent.includes("console.warn('Lỗi atomic batch, chuyển sang tuần tự:'"),
    'Must not have blind sequential retry fallback in publish handler');
});

test('U05 - SYNC-008: Edit settings must preserve null for unlimited attempts', () => {
  // Check that edit-exam-attempts doesn't force || 1
  assert.ok(!examViewContent.includes("parseInt(document.getElementById('edit-exam-attempts')?.value || 1, 10)"),
    'Must not force maxAttempts to 1 when empty/null');
});

test('U05 - SYNC-007: Edit questions list must read choices from nested question object', () => {
  // In edit questions list, choices count must be read from qObj.choices or q.choices
  assert.ok(examViewContent.includes('qObj = q.question || q') || examViewContent.includes('q.question || q'),
    'Must resolve qObj for nested assignment.question');
});
