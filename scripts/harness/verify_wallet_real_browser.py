"""Real browser test with Playwright verifying Wallet VietQR and realtime auto-credit."""
import asyncio
import json
import os
import urllib.request
from playwright.async_api import async_playwright
from backend.services.payos_service import create_signature, PAYOS_CHECKSUM_KEY

SCREENSHOT_DIR = "qa-task130-evidence/payment_proofs"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def test_wallet_realtime_flow():
    print("=== Launching Playwright Chromium Real Browser Test ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Step 1: Login
        print("[Browser 1] Navigating to login page...")
        await page.goto("http://localhost:5000/#/auth/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "student1@backend.local")
        await page.fill('input[type="password"]', "StudentPass1234!")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)

        # Step 2: Navigate to Wallet
        print("[Browser 2] Navigating to Wallet page...")
        await page.goto("http://localhost:5000/#/student/wallet", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/01_wallet_initial_view.png", full_page=True)
        print("  -> Saved screenshot: 01_wallet_initial_view.png")

        # Step 3: Select 100.000 VND chip and generate QR
        print("[Browser 3] Selecting 100,000 VND chip and generating QR...")
        chip_100k = page.locator('.btn-deposit-chip[data-amount="100000"]')
        await chip_100k.click()
        await page.click('#btn-generate-qr')
        await page.wait_for_selector('#qr-display-card:not(.hidden)', timeout=10000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/02_qr_generated_view.png", full_page=True)
        print("  -> Saved screenshot: 02_qr_generated_view.png")

        # Extract transfer code from the page
        transfer_code = await page.inner_text('#qr-transfer-code')
        transfer_code = transfer_code.strip()
        print(f"[Browser 4] Detected on-screen transfer code: {transfer_code}")

        # Step 4: Simulate bank transfer arriving via PayOS Webhook
        print("[Browser 5] Simulating Bank Transfer & PayOS Webhook in background...")
        webhook_data = {
            "orderCode": int(asyncio.get_event_loop().time() * 1000) % 90000000,
            "amount": 100000,
            "description": f"MBVCB.998877.{transfer_code}.CHUYEN TIEN",
            "accountNumber": "0908667141",
            "reference": "FTBROWSERTEST",
            "transactionDateTime": "2026-10-24 10:45:00",
            "currency": "VND",
            "paymentLinkId": "pl-browser-test",
            "code": "00",
            "desc": "success",
            "counterAccountBankId": None,
            "counterAccountBankName": None,
            "counterAccountName": None,
            "counterAccountNumber": None,
            "virtualAccountName": None,
            "virtualAccountNumber": None,
        }
        sig = create_signature(webhook_data, PAYOS_CHECKSUM_KEY)
        payload = {
            "code": "00",
            "desc": "success",
            "data": webhook_data,
            "signature": sig
        }

        req = urllib.request.Request(
            "http://127.0.0.1:5000/api/payments/payos/webhook",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            wh_res = json.loads(resp.read().decode("utf-8"))
            print(f"  -> Webhook dispatched: HTTP {resp.status}, Msg: {wh_res.get('message')}")

        # Step 5: Wait for realtime polling on the page to detect the credit
        print("[Browser 6] Waiting for page to auto-update via polling (no refresh)...")
        # The success celebration card will replace the QR code
        await page.wait_for_selector('text=Nạp tiền thành công!', timeout=15000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_wallet_autocredited_success.png", full_page=True)
        print("  -> Saved screenshot: 03_wallet_autocredited_success.png")

        print("\n>>> PLAYWRIGHT REAL BROWSER TEST PASSED WITH PROOF SCREENSHOTS! <<<")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wallet_realtime_flow())
