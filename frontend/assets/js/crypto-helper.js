/**
 * CryptoHelper - Client-side Hybrid Encryption for PPTQ LMS Authentication
 *
 * Implements two-tier in-transit hybrid encryption:
 * 1. Generates ephemeral AES-GCM 256 key for payload encryption (IV 12 bytes).
 * 2. Encrypts ephemeral AES key using Server's RSA-OAEP 2048 public key (SHA-256).
 * 3. Formats payload with "prefix": "PPTQ LMS" and anti-replay timestamp.
 */

class CryptoHelper {
  static _cachedPublicKeyPem = null;
  static _cachedCryptoKey = null;
  static _fetchPromise = null;

  /**
   * Check whether the browser environment supports Web Crypto API
   * @returns {boolean}
   */
  static isSupported() {
    const cryptoObj = (typeof window !== 'undefined' && window.crypto) ? window.crypto : (typeof crypto !== 'undefined' ? crypto : null);
    return Boolean(cryptoObj && cryptoObj.subtle && typeof cryptoObj.subtle.importKey === 'function');
  }

  /**
   * Convert ArrayBuffer or Uint8Array to standard Base64 string
   * @param {ArrayBuffer|Uint8Array} buffer
   * @returns {string}
   */
  static arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 string to Uint8Array binary buffer
   * @param {string} base64
   * @returns {Uint8Array}
   */
  static base64ToUint8Array(base64) {
    const cleanBase64 = String(base64)
      .replace(/-----BEGIN [A-Z ]+-----/g, '')
      .replace(/-----END [A-Z ]+-----/g, '')
      .replace(/\s+/g, '');
    const binary = atob(cleanBase64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  /**
   * Import RSA Public Key from PEM string or JWK object into CryptoKey
   * @param {string|object} keyData
   * @returns {Promise<CryptoKey>}
   */
  static async importPublicKey(keyData) {
    const cryptoSubtle = (typeof window !== 'undefined' && window.crypto && window.crypto.subtle)
      ? window.crypto.subtle
      : (typeof crypto !== 'undefined' && crypto.subtle ? crypto.subtle : null);

    if (!cryptoSubtle) {
      throw new Error('Web Crypto API (crypto.subtle) is not available in the current environment.');
    }

    if (typeof keyData === 'object' && keyData !== null && keyData.kty === 'RSA') {
      return await cryptoSubtle.importKey(
        'jwk',
        keyData,
        {
          name: 'RSA-OAEP',
          hash: 'SHA-256'
        },
        true,
        ['encrypt']
      );
    }

    if (typeof keyData === 'string') {
      const bytes = CryptoHelper.base64ToUint8Array(keyData);
      return await cryptoSubtle.importKey(
        'spki',
        bytes.buffer,
        {
          name: 'RSA-OAEP',
          hash: 'SHA-256'
        },
        true,
        ['encrypt']
      );
    }

    throw new Error('Invalid RSA public key data format.');
  }

  /**
   * Retrieve and cache the Server's RSA Public Key from /auth/security-key or /auth/session
   * @param {boolean} forceRefresh
   * @returns {Promise<CryptoKey>}
   */
  static async getServerPublicKey(forceRefresh = false) {
    if (!forceRefresh && CryptoHelper._cachedCryptoKey) {
      return CryptoHelper._cachedCryptoKey;
    }

    if (CryptoHelper._fetchPromise) {
      return CryptoHelper._fetchPromise;
    }

    CryptoHelper._fetchPromise = (async () => {
      let publicKeyPem = null;

      // 1. Try dedicated security-key endpoint
      try {
        const response = await fetch('/auth/security-key', {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        });
        if (response.ok) {
          const resJson = await response.json();
          const data = resJson.data || resJson;
          publicKeyPem = data.public_key || data.rsa_public_key || data.key || (typeof data === 'string' ? data : null);
        }
      } catch (_) {}

      // 2. Fallback to auth session endpoint
      if (!publicKeyPem) {
        try {
          const response = await fetch('/auth/session', {
            method: 'GET',
            headers: {
              'Accept': 'application/json'
            }
          });
          if (response.ok) {
            const resJson = await response.json();
            const data = resJson.data || resJson;
            publicKeyPem = data?.public_key || data?.security_key || resJson.public_key;
          }
        } catch (_) {}
      }

      if (!publicKeyPem) {
        throw new Error('Không thể tải khóa công khai bảo mật RSA từ máy chủ.');
      }

      CryptoHelper._cachedPublicKeyPem = publicKeyPem;
      const cryptoKey = await CryptoHelper.importPublicKey(publicKeyPem);
      CryptoHelper._cachedCryptoKey = cryptoKey;
      return cryptoKey;
    })().finally(() => {
      CryptoHelper._fetchPromise = null;
    });

    return CryptoHelper._fetchPromise;
  }

  /**
   * Encrypt login credentials using Web Crypto API hybrid encryption
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{prefix: string, key: string, iv: string, ciphertext: string, timestamp: number}>}
   */
  static async encryptLoginPayload(email, password) {
    if (!CryptoHelper.isSupported()) {
      throw new Error('Trình duyệt không hỗ trợ Web Crypto API bảo mật.');
    }

    const cryptoObj = (typeof window !== 'undefined' && window.crypto) ? window.crypto : crypto;
    const cryptoSubtle = cryptoObj.subtle;

    // 1. Fetch Server's RSA Public Key
    const rsaPublicKey = await CryptoHelper.getServerPublicKey();

    // 2. Generate ephemeral AES-GCM 256 key
    const aesKey = await cryptoSubtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256
      },
      true, // extractable so we can export raw bytes to encrypt with RSA
      ['encrypt', 'decrypt']
    );

    // 3. Prepare payload and cryptographic nonce
    const nonce = (typeof cryptoObj.randomUUID === 'function')
      ? cryptoObj.randomUUID()
      : (Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15));

    const timestamp = Date.now();
    const payload = {
      email: String(email).trim(),
      password: String(password),
      timestamp,
      nonce
    };

    // 4. Encrypt payload with AES-GCM using 12-byte IV
    const iv = cryptoObj.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const encodedPayload = encoder.encode(JSON.stringify(payload));

    const encryptedPayloadBuffer = await cryptoSubtle.encrypt(
      {
        name: 'AES-GCM',
        iv
      },
      aesKey,
      encodedPayload
    );

    // 5. Export raw AES key and encrypt with RSA-OAEP SHA-256
    const rawAesKeyBuffer = await cryptoSubtle.exportKey('raw', aesKey);
    const encryptedAesKeyBuffer = await cryptoSubtle.encrypt(
      {
        name: 'RSA-OAEP'
      },
      rsaPublicKey,
      rawAesKeyBuffer
    );

    // 6. Return standardized encrypted envelope
    return {
      prefix: 'PPTQ LMS',
      key: CryptoHelper.arrayBufferToBase64(encryptedAesKeyBuffer),
      iv: CryptoHelper.arrayBufferToBase64(iv),
      ciphertext: CryptoHelper.arrayBufferToBase64(encryptedPayloadBuffer),
      timestamp
    };
  }

  /**
   * Encrypt registration credentials using Web Crypto API hybrid encryption
   * @param {string} name
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{prefix: string, key: string, iv: string, ciphertext: string, timestamp: number}>}
   */
  static async encryptRegisterPayload(name, email, password) {
    if (!CryptoHelper.isSupported()) {
      throw new Error('Trình duyệt không hỗ trợ Web Crypto API bảo mật.');
    }

    const cryptoObj = (typeof window !== 'undefined' && window.crypto) ? window.crypto : crypto;
    const cryptoSubtle = cryptoObj.subtle;

    const rsaPublicKey = await CryptoHelper.getServerPublicKey();

    const aesKey = await cryptoSubtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256
      },
      true,
      ['encrypt', 'decrypt']
    );

    const nonce = (typeof cryptoObj.randomUUID === 'function')
      ? cryptoObj.randomUUID()
      : (Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15));

    const timestamp = Date.now();
    const payload = {
      name: String(name).trim(),
      email: String(email).trim(),
      password: String(password),
      timestamp,
      nonce
    };

    const iv = cryptoObj.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const encodedPayload = encoder.encode(JSON.stringify(payload));

    const encryptedPayloadBuffer = await cryptoSubtle.encrypt(
      {
        name: 'AES-GCM',
        iv
      },
      aesKey,
      encodedPayload
    );

    const rawAesKeyBuffer = await cryptoSubtle.exportKey('raw', aesKey);
    const encryptedAesKeyBuffer = await cryptoSubtle.encrypt(
      {
        name: 'RSA-OAEP'
      },
      rsaPublicKey,
      rawAesKeyBuffer
    );

    return {
      prefix: 'PPTQ LMS',
      key: CryptoHelper.arrayBufferToBase64(encryptedAesKeyBuffer),
      iv: CryptoHelper.arrayBufferToBase64(iv),
      ciphertext: CryptoHelper.arrayBufferToBase64(encryptedPayloadBuffer),
      timestamp
    };
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CryptoHelper };
}
if (typeof window !== 'undefined') {
  window.CryptoHelper = CryptoHelper;
}
