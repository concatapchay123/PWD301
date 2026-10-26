from scripts.test_topbar_local import start_server, PORT
from playwright.sync_api import sync_playwright

server = start_server()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1024, "height": 800})
    page.goto(f"http://127.0.0.1:{PORT}/frontend/index.html")
    page.wait_for_selector("#app-topbar", state="attached")
    page.evaluate("""
        const tb = document.getElementById("app-topbar");
        if (tb) { tb.classList.remove("hidden"); tb.style.display = "flex"; }
    """)
    for role in ["INSTRUCTOR", "STUDENT"]:
        page.evaluate(f"""
            window.app.currentUser = {{
                id: 'test',
                primary_role: '{role}',
                active_role: '{role}',
                display_name: 'Test',
                email: 'test@pptq.vn',
                roles: ['{role}'],
                role_codes: ['{role}']
            }};
            window.app.currentRole = '{role}';
            window.app.renderDynamicTopbar();
        """)
        page.wait_for_timeout(300)
        logo = page.locator('#app-topbar a[href="#/"]').bounding_box()
        nav = page.locator('#topbar-navigation-items').bounding_box()
        right = page.locator('#app-topbar > div:last-child').bounding_box()
        print(f"{role} at 1024px:")
        print(f"  Nav: left={nav['x']:.1f}, right={nav['x']+nav['width']:.1f}, width={nav['width']:.1f}")
        print(f"  Logo right: {logo['x']+logo['width']:.1f}, Right controls left: {right['x']:.1f}")
    browser.close()
server.shutdown()
