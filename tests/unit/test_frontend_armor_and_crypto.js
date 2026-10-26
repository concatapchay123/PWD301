const assert = require('assert');
const crypto = require('crypto');
const { CryptoHelper } = require('../../frontend/assets/js/crypto-helper.js');
const { VideoArmor } = require('../../frontend/assets/js/components/video-armor.js');

async function runTests() {
  console.log('--- TEST 1: VideoArmor Shortcut Violation Detector ---');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'F12', keyCode: 123 }), 'DEVTOOLS_DETECTED');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'i', ctrlKey: true, shiftKey: true }), 'DEVTOOLS_DETECTED');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'j', metaKey: true, shiftKey: true }), 'DEVTOOLS_DETECTED');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'c', ctrlKey: true, shiftKey: true }), 'DEVTOOLS_DETECTED');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'u', ctrlKey: true }), 'VIEW_SOURCE_ATTEMPT');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'PrintScreen', keyCode: 44 }), 'SCREEN_CAPTURE_ATTEMPT');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 's', metaKey: true, shiftKey: true }), 'SCREEN_CAPTURE_ATTEMPT');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: '3', metaKey: true, shiftKey: true }), 'SCREEN_CAPTURE_ATTEMPT');
  assert.strictEqual(VideoArmor.checkShortcutViolation({ key: 'a' }), null);
  console.log('✅ Shortcut violation detector passed all test cases.');

  console.log('--- TEST 2: VideoArmor Admin Exemption ---');
  assert.strictEqual(VideoArmor.isAdminUser({ primary_role: 'ADMIN' }), true);
  assert.strictEqual(VideoArmor.isAdminUser({ active_role: 'ADMIN' }), true);
  assert.strictEqual(VideoArmor.isAdminUser({ role_codes: ['STUDENT', 'ADMIN'] }), true);
  assert.strictEqual(VideoArmor.isAdminUser({ primary_role: 'STUDENT', role_codes: ['STUDENT'] }), false);
  assert.strictEqual(VideoArmor.isAdminUser(null), false);
  console.log('✅ Admin exemption check passed.');

  console.log('--- TEST 3: VideoArmor DevTools Dimension Divergence ---');
  // Mock window with normal dimensions
  global.window = {
    innerWidth: 1920,
    outerWidth: 1920,
    innerHeight: 1080,
    outerHeight: 1080
  };
  assert.strictEqual(VideoArmor.checkDevToolsOpen(), false);

  // Mock window with docked DevTools (> 160px diff)
  global.window = {
    innerWidth: 1500,
    outerWidth: 1920,
    innerHeight: 1080,
    outerHeight: 1080
  };
  assert.strictEqual(VideoArmor.checkDevToolsOpen(), true);

  // Reset window
  delete global.window;
  console.log('✅ DevTools dimension check passed.');

  console.log('--- TEST 4: CryptoHelper Hybrid WebCrypto Encryption ---');
  // Generate 2048-bit RSA test keypair
  const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding: { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
  });

  const importedKey = await CryptoHelper.importPublicKey(publicKey);
  CryptoHelper._cachedCryptoKey = importedKey;

  const testEmail = 'admin@pwd301.local';
  const testPassword = 'AdminStrongPassw0rd!';
  const envelope = await CryptoHelper.encryptLoginPayload(testEmail, testPassword);

  assert.strictEqual(envelope.prefix, 'PPTQ LMS');
  assert.ok(envelope.key && typeof envelope.key === 'string' && envelope.key.length > 50);
  assert.ok(envelope.iv && typeof envelope.iv === 'string');
  assert.ok(envelope.ciphertext && typeof envelope.ciphertext === 'string');
  assert.ok(typeof envelope.timestamp === 'number');

  // Verify server-side decryption logic (RSA-OAEP + AES-256-GCM)
  const rawAesKey = crypto.privateDecrypt(
    {
      key: privateKey,
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: 'sha256'
    },
    Buffer.from(envelope.key, 'base64')
  );
  assert.strictEqual(rawAesKey.length, 32); // 256 bits

  const ivBuffer = Buffer.from(envelope.iv, 'base64');
  const cipherBuffer = Buffer.from(envelope.ciphertext, 'base64');
  const authTag = cipherBuffer.subarray(cipherBuffer.length - 16);
  const encData = cipherBuffer.subarray(0, cipherBuffer.length - 16);

  const decipher = crypto.createDecipheriv('aes-256-gcm', rawAesKey, ivBuffer);
  decipher.setAuthTag(authTag);
  const decrypted = Buffer.concat([decipher.update(encData), decipher.final()]);
  const decryptedJson = JSON.parse(decrypted.toString('utf8'));

  assert.strictEqual(decryptedJson.email, testEmail);
  assert.strictEqual(decryptedJson.password, testPassword);
  assert.ok(decryptedJson.nonce);
  assert.ok(decryptedJson.timestamp);
  console.log('✅ CryptoHelper hybrid encryption & decryption round-trip verified successfully.');

  console.log('All tests passed successfully!');
}

runTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
