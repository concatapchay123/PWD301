from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    def logout_user(page):
        try:
            if not page.url.startswith("about:"):
                page.evaluate("async () => { if (window.ApiClient && ApiClient.logout) await ApiClient.logout(); }")
                page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (_) {} }")
        except Exception:
            pass
        try:
            page.context.clear_cookies()
        except Exception:
            pass

    def login_user(page, email, password="Password123!"):
        logout_user(page)
        page.goto("http://127.0.0.1:5000/#/auth/login", wait_until="commit")
        page.wait_for_selector("#login-email", timeout=6000)
        page.fill("#login-email", email)
        page.fill("#login-password", password)
        page.click("#login-submit-btn")
        page.wait_for_function(f"() => window.app && window.app.currentUser && window.app.currentUser.email === '{email}'", timeout=8000)
        page.wait_for_timeout(250)

    # 1. Login student
    login_user(page, "student_wallet_t132@backend.local")
    print("User 1:", page.evaluate("() => window.app.currentUser.email"))

    # 2. Login admin
    login_user(page, "admin@backend.local")
    print("User 2:", page.evaluate("() => window.app.currentUser.email"))

    # 3. Call reassign
    res = page.evaluate("""async () => {
        try {
            return await ApiClient.reassignCourse('7fc3b4c0-a03a-4540-8075-47c02b0f312c', 10012, 'Điều chuyển');
        } catch (err) {
            return { error: err.message, status: err.status };
        }
    }""")
    print("Reassign res:", res.get("id") or res.get("public_id") or res)

    browser.close()
