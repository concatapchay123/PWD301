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
