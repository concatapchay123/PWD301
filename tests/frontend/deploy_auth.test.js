const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('auth demo accounts are hidden until explicitly enabled by server', () => {
  const window = { location: { protocol: 'http:' } };
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/auth.js', 'utf8'), { window });
  const html = window.AuthView.render();
  assert.doesNotMatch(html, /Tài khoản demo nhanh|data-pass=/);
  assert.doesNotMatch(html, /Bảo mật TLS/);
});
