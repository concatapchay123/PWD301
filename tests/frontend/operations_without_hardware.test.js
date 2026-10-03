const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

test('admin operations UI does not show or poll live hardware metrics', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8');
  assert.doesNotMatch(source, /ApiClient\.getAdminTelemetry\(/);
  assert.doesNotMatch(source, /id="telem-(?:cpu|ram|disk|node|net)-/);
  assert.doesNotMatch(source, /Tải phần cứng thời gian thực|Giám sát hạ tầng phần cứng/);
});

test('admin operations UI does not present fabricated infrastructure or job claims', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/admin.js'), 'utf8');

  for (const fabricatedClaim of [
    'Daemon Threads: 8 Active',
    '#RG-2026-LIVE',
    'stg-eval-pwd.edu.vn',
    '148k Giáo trình Embeddings',
    'Dung lượng: 1.84 TB / 5 TB',
    '9b2df41e88b63dc4e9a3efd8e23910c2',
    "'14.82 MB'",
    'Response time: ~22ms',
    'Active workers: 8',
    'Query: 28ms',
    'style="width: 100%;"',
  ]) {
    assert.equal(source.includes(fabricatedClaim), false, `fabricated claim remains: ${fabricatedClaim}`);
  }

  assert.match(source, /ApiClient\.getAdminBackgroundJobs\(/);
  assert.match(source, /s\.name \|\| s\.service_name \|\| k/);
  assert.match(source, /Chưa có dữ liệu/);
  assert.match(source, /Chưa ghi nhận/);
});
