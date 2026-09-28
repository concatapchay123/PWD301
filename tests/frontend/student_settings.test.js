const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const storedValues = new Map();
const window = {
  localStorage: {
    getItem: key => storedValues.get(key) || null,
    setItem: (key, value) => storedValues.set(key, String(value))
  }
};
vm.runInNewContext(source, { window }, { filename: sourcePath });

test('password feedback requires length, letter, digit, and special character', () => {
  const checks = window.StudentView.getPasswordRequirements('SecurePass123');

  assert.deepEqual({ ...checks }, {
    hasLength: true,
    hasLetter: true,
    hasDigit: true,
    hasSpecialCharacter: false
  });
  assert.equal(window.StudentView.getPasswordRequirements('SecurePass123 ').hasSpecialCharacter, false);
  assert.equal(window.StudentView.getPasswordRequirements('SecurePass123!').hasSpecialCharacter, true);
});

test('random avatar generator returns an encoded Dicebear URL for its seed', () => {
  const avatarUrl = window.StudentView.createRandomAvatarUrl(() => 0.5);
  const parsed = new URL(avatarUrl);

  assert.equal(parsed.origin, 'https://api.dicebear.com');
  assert.equal(parsed.pathname, '/10.x/adventurer/svg');
  assert.equal(parsed.searchParams.has('seed'), true);
});

test('avatar choice supports several non-robot styles and rejects unknown styles', () => {
  const styles = ['adventurer', 'lorelei', 'fun-emoji', 'pixel-art', 'thumbs'];
  for (const style of styles) {
    const url = window.StudentView.createRandomAvatarUrl(() => 0.5, style);
    assert.equal(new URL(url).pathname, `/10.x/${style}/svg`);
    assert.equal(window.StudentView.storeRandomAvatarUrl('user-123', url), true);
  }
  assert.equal(window.StudentView.storeRandomAvatarUrl('user-123', 'https://api.dicebear.com/10.x/unknown/svg?seed=abc'), false);
});

test('random avatar choice persists by account and rejects arbitrary URLs', () => {
  const avatarUrl = window.StudentView.createRandomAvatarUrl(() => 0.5);

  assert.equal(window.StudentView.storeRandomAvatarUrl('user-123', avatarUrl), true);
  assert.equal(window.StudentView.getStoredRandomAvatarUrl('user-123'), avatarUrl);
  assert.equal(window.StudentView.getStoredRandomAvatarUrl('another-user'), '');
  assert.equal(window.StudentView.storeRandomAvatarUrl('user-123', 'https://example.com/avatar.svg'), false);
});

test('settings view does not expose a free-form avatar URL field', () => {
  assert.doesNotMatch(source, /id="settings-avatar-url"/);
  assert.match(source, /id="btn-avatar-preset"/);
});
