import base64
import http.cookiejar
import json
import os
import time
import urllib.request
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BASE_URL = "http://127.0.0.1:5000"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Fetch CSRF token & cookies
req1 = urllib.request.Request(f"{BASE_URL}/auth/login", headers={"Accept": "application/json"})
res1 = opener.open(req1, timeout=5)
data1 = json.loads(res1.read().decode())
csrf_token = data1.get("csrf_token")
print("[1] Fetched CSRF Token:", csrf_token[:30], "...")

# 2. Fetch RSA public key
req2 = urllib.request.Request(f"{BASE_URL}/auth/security-key", headers={"Accept": "application/json"})
res2 = opener.open(req2, timeout=5)
data2 = json.loads(res2.read().decode())
public_pem = data2["data"]["public_key"]
print("[2] Fetched RSA Public Key PEM (prefix:", data2["data"]["prefix"], ")")
rsa_pub_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))

# 3. Hybrid Encryption (Client-side simulation)
aes_key = os.urandom(32)
iv = os.urandom(12)
now_ms = int(time.time() * 1000)
payload = {
    "email": "admin@backend.local",
    "password": "Password123!",
    "timestamp": now_ms,
    "nonce": "test-client-nonce-999"
}
payload_bytes = json.dumps(payload).encode("utf-8")

cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
encryptor = cipher.encryptor()
ct = encryptor.update(payload_bytes) + encryptor.finalize()
tag = encryptor.tag

enc_aes_key = rsa_pub_key.encrypt(
    aes_key,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

envelope = {
    "prefix": "PPTQ LMS",
    "key": base64.b64encode(enc_aes_key).decode("utf-8"),
    "iv": base64.b64encode(iv).decode("utf-8"),
    "ciphertext": base64.b64encode(ct + tag).decode("utf-8"),
    "timestamp": now_ms
}

print("[3] Built Encrypted Envelope (Network Payload):")
print("    prefix:    ", envelope["prefix"])
print("    key:       ", envelope["key"][:40], "...")
print("    iv:        ", envelope["iv"])
print("    ciphertext:", envelope["ciphertext"][:40], "...")
print("    timestamp: ", envelope["timestamp"])

# 4. POST to /auth/login
req3 = urllib.request.Request(
    f"{BASE_URL}/auth/login",
    data=json.dumps({"encrypted_envelope": envelope, "remember": False}).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CSRFToken": csrf_token
    }
)

res3 = opener.open(req3, timeout=5)
data3 = json.loads(res3.read().decode())
import sys

print("\n[4] Login Server Response:")
print("    HTTP Status: ", res3.status)
print("    Success:     ", data3.get("success"))
sys.stdout.buffer.write(f"    Message:      {data3.get('message')}\n".encode("utf-8"))
sys.stdout.buffer.write(f"    User Email:   {data3.get('data', {}).get('user', {}).get('email')}\n".encode("utf-8"))
sys.stdout.buffer.write(f"    User Name:    {data3.get('data', {}).get('user', {}).get('display_name')}\n".encode("utf-8"))
sys.stdout.buffer.write(f"    Primary Role: {data3.get('data', {}).get('user', {}).get('primary_role')}\n".encode("utf-8"))

assert data3.get("success") is True
assert data3.get("data", {}).get("user", {}).get("email") == "admin@backend.local"
print("\n>>> LIVE HYBRID IN-TRANSIT ENCRYPTION VERIFIED WITH 100% SUCCESS! <<<")
