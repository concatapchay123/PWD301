import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

with open("frontend/assets/img/pptq_logo.png", "rb") as f:
    b64_logo = base64.b64encode(f.read()).decode("utf-8")

with open("frontend/assets/img/pptq_icon.png", "rb") as f:
    b64_icon = base64.b64encode(f.read()).decode("utf-8")

template_path = Path("src/pwd301/templates/certificate/course_completion_certificate.html")
html = template_path.read_text(encoding="utf-8")

# Option A: using pptq_logo.png (horizontal brand logo)
# Replace SVG in .emblem-wrapper
start_svg = html.find("<svg role=\"img\" aria-label=\"Biểu trưng")
end_svg = html.find("</svg>", start_svg) + len("</svg>")

img_logo_tag = f'<img src="data:image/png;base64,{b64_logo}" alt="Logo PPTQ LMS" style="height: 22mm; width: auto; object-fit: contain; display: block;" />'
html_opt_a = html[:start_svg] + img_logo_tag + html[end_svg:]
html_opt_a = html_opt_a.replace("HỌC VIỆN ĐÀO TẠO KỸ THUẬT PPTQ LMS", "HỆ THỐNG HỌC TẬP TRỰC TUYẾN PPTQ LMS")
html_opt_a = html_opt_a.replace("PPTQ LMS INSTITUTE OF TECHNICAL TRAINING &amp; EXCELLENCE", "PPTQ LMS ONLINE LEARNING &amp; TRAINING SYSTEM")

Path("scratch/opt_a_logo.html").write_text(html_opt_a, encoding="utf-8")

# Option B: using pptq_icon.png (shield icon)
img_icon_tag = f'<img src="data:image/png;base64,{b64_icon}" alt="Logo PPTQ LMS" style="height: 24mm; width: auto; object-fit: contain; display: block;" />'
html_opt_b = html[:start_svg] + img_icon_tag + html[end_svg:]
html_opt_b = html_opt_b.replace("HỌC VIỆN ĐÀO TẠO KỸ THUẬT PPTQ LMS", "HỆ THỐNG HỌC TẬP TRỰC TUYẾN PPTQ LMS")
html_opt_b = html_opt_b.replace("PPTQ LMS INSTITUTE OF TECHNICAL TRAINING &amp; EXCELLENCE", "PPTQ LMS ONLINE LEARNING &amp; TRAINING SYSTEM")

Path("scratch/opt_b_icon.html").write_text(html_opt_b, encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch()
    
    # Render A
    page_a = b.new_page(viewport={"width": 1200, "height": 1600})
    page_a.goto(f"file:///{Path('scratch/opt_a_logo.html').resolve().as_posix()}")
    page_a.wait_for_timeout(1000)
    page_a.locator(".certificate-canvas").screenshot(path="scratch/opt_a_logo_rendered.png")
    
    # Render B
    page_b = b.new_page(viewport={"width": 1200, "height": 1600})
    page_b.goto(f"file:///{Path('scratch/opt_b_icon.html').resolve().as_posix()}")
    page_b.wait_for_timeout(1000)
    page_b.locator(".certificate-canvas").screenshot(path="scratch/opt_b_icon_rendered.png")
    
    b.close()

print("Both options rendered!")
