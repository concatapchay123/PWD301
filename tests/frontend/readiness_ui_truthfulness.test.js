const assert = require('node:assert/strict');
const fs = require('node:fs'); const vm = require('node:vm'); const test = require('node:test');
function view(file, name, additions = {}) { const window = { location: { protocol: 'http:' } }; vm.runInNewContext(fs.readFileSync(`frontend/assets/js/views/${file}.js`, 'utf8'), { window, ...additions }); return { value: window[name], window }; }
test('auth hides demo credentials by default and on production even if a flag is set', () => {
  const { value: auth, window } = view('auth', 'AuthView');
  assert.doesNotMatch(auth.render(), /Tài khoản demo nhanh|data-pass=/);
  assert.doesNotMatch(auth.render({ environment: 'production', demo_accounts_enabled: true }), /Tài khoản demo nhanh/);
  assert.match(auth.render({ environment: 'development', demo_accounts_enabled: true }), /Tài khoản demo nhanh/);
  assert.doesNotMatch(auth.render(), /Bảo mật TLS/);
  window.location.protocol = 'https:'; assert.match(auth.render(), /Bảo mật TLS/);
});
test('worker summary reports only real matrix status and available queue counts', () => {
  const { value: admin } = view('admin', 'AdminView');
  assert.equal(typeof admin.workerSummary, 'function');
  assert.match(admin.workerSummary({ workers: { status: 'HEALTHY', running_jobs: 0, queued_jobs: 2 } }), /HEALTHY.*0.*2/);
  assert.match(admin.workerSummary({}), /Chưa có dữ liệu/);
  assert.doesNotMatch(admin.workerSummary({ workers: { status: 'DOWN' } }), /running: 0|queued: 0/);
});
test('backup verified label requires actual checksum and size metadata', () => {
  const { value: admin } = view('admin', 'AdminView');
  assert.equal(typeof admin.backupMetadata, 'function');
  assert.equal(admin.backupMetadata({ verified_at: '2026-10-09' }).verified, false);
  const result = admin.backupMetadata({ checksum_sha256: 'a'.repeat(64), file_size_bytes: 1048576, verified_at: '2026-10-09' });
  assert.equal(result.verified, true); assert.equal(result.size, '1.00 MB');
});
test('empty student dashboard has no in-progress hero or invented upcoming work', () => {
  const { value: student } = view('student', 'StudentView');
  assert.equal(typeof student.dashboardActivity, 'function');
  const empty = student.dashboardActivity([], []);
  assert.equal(empty.showHero, false); assert.doesNotMatch(empty.subtitle, /bài kiểm tra sắp tới/);
  assert.equal(student.dashboardActivity([{ status: 'ACTIVE' }], []).showHero, true);
});
