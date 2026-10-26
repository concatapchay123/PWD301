import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:5000/#/auth")
    
    csrf_before = page.evaluate("() => ApiClient.getCsrfToken()")
    print("CSRF before login:", csrf_before)
    
    page.locator("#login-email").fill("student1@backend.local")
    page.locator("#login-password").fill("Password123!")
    page.locator("#login-submit-btn").click()
    page.wait_for_url("**/#/student/dashboard")
    
    # Test UI Logout button
    page.locator("#topbar-avatar-btn").click()
    time.sleep(0.5)
    page.locator("#topbar-logout-btn").click()
    page.wait_for_url("**/#/auth")
    time.sleep(1)
    
    print("URL after UI logout:", page.url)
    user_after_logout = page.evaluate("() => window.app?.currentUser")
    print("CurrentUser in app after logout:", user_after_logout)
    
    # Try direct goto #/student/dashboard
    page.goto("http://localhost:5000/#/student/dashboard")
    page.wait_for_url("**/#/auth", timeout=5000)
    print("URL after direct goto and wait_for_url:", page.url)
    user_after_goto = page.evaluate("() => window.app?.currentUser")
    print("CurrentUser in app after direct goto:", user_after_goto)
    h1 = page.locator("h1, h2").first.inner_text() if page.locator("h1, h2").count() > 0 else "NO H1/H2"
    print("Heading on page:", h1)
    browser.close()
