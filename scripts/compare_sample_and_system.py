import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # 1. Screenshot the user's sample file
        page1 = browser.new_page(viewport={"width": 1200, "height": 1600})
        sample_path = Path(r"C:\Users\LENOVO\Downloads\ch_ng_ch_ho_n_th_nh_kh_a_h_c_pptq_lms.html").resolve()
        page1.goto(f"file:///{sample_path.as_posix()}")
        page1.wait_for_timeout(1000)
        canvas1 = page1.query_selector(".certificate-canvas")
        if canvas1:
            canvas1.screenshot(path="scratch/user_sample_actual.png")
            print("Captured scratch/user_sample_actual.png (canvas)")
        else:
            page1.screenshot(path="scratch/user_sample_actual.png", full_page=True)
            print("Captured scratch/user_sample_actual.png (full page)")
            
        # 2. Screenshot the system template
        page2 = browser.new_page(viewport={"width": 1200, "height": 1600})
        template_path = Path(r"E:\PWD301\src\pwd301\templates\certificate\course_completion_certificate.html").resolve()
        page2.goto(f"file:///{template_path.as_posix()}")
        page2.wait_for_timeout(1000)
        canvas2 = page2.query_selector(".certificate-canvas")
        if canvas2:
            canvas2.screenshot(path="scratch/system_template_current.png")
            print("Captured scratch/system_template_current.png (canvas)")
        else:
            page2.screenshot(path="scratch/system_template_current.png", full_page=True)
            print("Captured scratch/system_template_current.png (full page)")

        browser.close()

if __name__ == "__main__":
    main()
