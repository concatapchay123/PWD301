"""Generate official Course Completion Certificates as elegant, Unicode-compliant Portrait A4 PDFs and HTML views."""

from __future__ import annotations

import base64
import io
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import date, datetime
from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

# PPTQ Branding assets
_BASE_REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_LOGO_LIGHT_PATH = os.path.join(_BASE_REPO_DIR, "frontend", "assets", "img", "pptq_logo_light.png")
_LOGO_WATERMARK_PATH = os.path.join(_BASE_REPO_DIR, "frontend", "assets", "img", "pptq_logo_watermark.png")
_TEMPLATE_PATH = os.path.join(
    _BASE_REPO_DIR,
    "src",
    "backend",
    "templates",
    "certificate",
    "course_completion_certificate.html",
)

# Font cache for ReportLab fallback
_FONT_NORMAL = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONTS_REGISTERED = False


def _get_watermark_base64() -> str:
    """Read the PPTQ watermark image and encode as base64."""
    if os.path.exists(_LOGO_WATERMARK_PATH):
        try:
            with open(_LOGO_WATERMARK_PATH, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass
    return ""


def _init_fonts() -> tuple[str, str]:
    """Register Unicode-compliant TrueType fonts for ReportLab fallback."""
    global _FONT_NORMAL, _FONT_BOLD, _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return _FONT_NORMAL, _FONT_BOLD

    candidates = [
        # Windows system fonts
        (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "SystemArial",
            "SystemArial-Bold",
        ),
        (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "SystemSegoe",
            "SystemSegoe-Bold",
        ),
        (
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "SystemCalibri",
            "SystemCalibri-Bold",
        ),
        # Linux standard paths
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "DejaVuSans",
            "DejaVuSans-Bold",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "LibSans",
            "LibSans-Bold",
        ),
        (
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "FreeSans",
            "FreeSans-Bold",
        ),
    ]

    for norm_path, bold_path, norm_name, bold_name in candidates:
        if os.path.exists(norm_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(norm_name, norm_path))
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                pdfmetrics.registerFontFamily(
                    norm_name,
                    normal=norm_name,
                    bold=bold_name,
                    italic=norm_name,
                    boldItalic=bold_name,
                )
                _FONT_NORMAL = norm_name
                _FONT_BOLD = bold_name
                _FONTS_REGISTERED = True
                return _FONT_NORMAL, _FONT_BOLD
            except Exception:
                continue

    _FONTS_REGISTERED = True
    return _FONT_NORMAL, _FONT_BOLD


def _find_system_chromium_binary() -> str | None:
    """Find an installed Chromium-compatible browser binary for headless PDF printing."""
    # 1. Environment variables
    for env_var in ["CHROME_PATH", "CHROMIUM_PATH", "CHROME_BIN", "EDGE_PATH"]:
        val = os.environ.get(env_var)
        if val and os.path.exists(val):
            return val

    # 2. Standard Linux / Docker paths
    linux_paths = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]
    for p in linux_paths:
        if os.path.exists(p):
            return p

    # 3. Standard Windows paths
    win_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p

    # 4. PATH lookups
    for name in ["chromium", "chromium-browser", "google-chrome", "chrome", "msedge"]:
        loc = shutil.which(name)
        if loc and os.path.exists(loc):
            return loc

    return None


def _generate_cli_browser_pdf(html_markup: str) -> bytes | None:
    """Render HTML directly to PDF using an installed Chromium-based browser via CLI headless mode.

    Ensures 100% pixel-perfect equivalence to the HTML browser view.
    """
    browser_bin = _find_system_chromium_binary()
    if not browser_bin or not os.path.exists(browser_bin):
        return None

    temp_html = None
    temp_pdf = None
    temp_user_data_dir = None
    try:
        temp_user_data_dir = tempfile.mkdtemp(prefix="pptq_pdf_shm_")
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f_html:
            f_html.write(html_markup)
            temp_html = f_html.name

        temp_pdf = temp_html.rsplit(".", 1)[0] + ".pdf"
        cmd = [
            browser_bin,
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--user-data-dir={temp_user_data_dir}",
            f"--print-to-pdf={temp_pdf}",
            temp_html,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=25)
        if res.returncode == 0 and os.path.exists(temp_pdf) and os.path.getsize(temp_pdf) > 100:
            with open(temp_pdf, "rb") as f_pdf:
                pdf_data = f_pdf.read()
            if pdf_data.startswith(b"%PDF-"):
                return pdf_data
    except Exception as ex:
        import logging
        logging.getLogger(__name__).warning(f"CLI browser PDF generation failed with {browser_bin}: {ex}")
    finally:
        if temp_html and os.path.exists(temp_html):
            try:
                os.remove(temp_html)
            except Exception:
                pass
        if temp_pdf and os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except Exception:
                pass
        if temp_user_data_dir and os.path.exists(temp_user_data_dir):
            try:
                import shutil
                shutil.rmtree(temp_user_data_dir, ignore_errors=True)
            except Exception:
                pass
    return None


def generate_course_certificate_html(
    student: Any,
    course: Any,
    completion_date: str | date | datetime | None = None,
    cert_id: str | uuid.UUID | None = None,
) -> str:
    """Generate the official HTML markup for the Course Completion Certificate in Portrait A4 format.

    Uses the canonical typography, SVG heraldic crest, central digital seal, and embedded Base64 watermark.
    """
    # Extract student display name
    if isinstance(student, dict):
        student_name = student.get("display_name") or student.get("full_name") or student.get("email") or "Học viên"
    else:
        student_name = getattr(student, "display_name", None) or getattr(student, "email", "Học viên")
    student_name = str(student_name).strip()

    # Extract course details
    if isinstance(course, dict):
        course_title = course.get("title") or "Khóa học"
        course_code = course.get("course_code") or "PPTQ"
        course_topic = course.get("category") or course.get("description") or "Chuyên môn tiêu chuẩn"
    else:
        course_title = getattr(course, "title", "Khóa học")
        course_code = getattr(course, "course_code", "PPTQ")
        course_topic = getattr(course, "category", None) or getattr(course, "description", None) or "Chuyên môn tiêu chuẩn"

    course_title = str(course_title).strip()
    course_code = str(course_code).strip()
    course_topic = str(course_topic).strip()
    if len(course_topic) > 60:
        course_topic = course_topic[:57] + "..."

    # Normalize completion date
    if completion_date is None:
        fmt_date = datetime.now().strftime("%d/%m/%Y")
    elif isinstance(completion_date, (datetime, date)):
        fmt_date = completion_date.strftime("%d/%m/%Y")
    else:
        fmt_date = str(completion_date).strip()

    # Normalize certificate ID
    if cert_id is None:
        fmt_cert_id = f"CERT-{course_code}-{uuid.uuid4().hex[:12].upper()}"
    else:
        fmt_cert_id = str(cert_id).strip()

    # Load canonical template from disk
    template_content = ""
    if os.path.exists(_TEMPLATE_PATH):
        try:
            with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception:
            pass

    if not template_content:
        alt_paths = [
            os.path.join(_BASE_REPO_DIR, "scratch", "original_sample_certificate.html"),
            r"C:\Users\LENOVO\Downloads\ch_ng_ch_ho_n_th_nh_kh_a_h_c_pptq_lms.html",
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                try:
                    with open(alt, "r", encoding="utf-8") as f:
                        template_content = f.read()
                    break
                except Exception:
                    pass

    # Perform precise token replacements
    html = template_content
    html = html.replace("<title>Chứng Nhận Hoàn Thành Khóa Học - HOÀNG PHÚC</title>", f"<title>Chứng Nhận Hoàn Thành Khóa Học - {escape(student_name)}</title>")
    html = html.replace('<h2 class="recipient-name">HOÀNG PHÚC</h2>', f'<h2 class="recipient-name">{escape(student_name.upper())}</h2>')
    html = html.replace('<h3 class="course-title-main">KỸ THUẬT &amp; CHIẾN THUẬT KIỂM SOÁT ĐƯỜNG GIỮA</h3>', f'<h3 class="course-title-main">{escape(course_title.upper())}</h3>')
    html = html.replace('<span>Chuyên đề đào tạo: <strong>Cách đi lane Mid</strong></span>', f'<span>Chuyên đề đào tạo: <strong>{escape(course_topic)}</strong></span>')
    html = html.replace('<span class="course-code-badge">MÃ HỌC PHẦN: MID001</span>', f'<span class="course-code-badge">MÃ HỌC PHẦN: {escape(course_code)}</span>')
    html = html.replace('<span class="reg-value">23/10/2026</span>', f'<span class="reg-value">{escape(fmt_date)}</span>')
    html = html.replace('<span class="reg-value">CERT-MID001-3-1792740720</span>', f'<span class="reg-value">{escape(fmt_cert_id)}</span>')

    return html


def _generate_reportlab_portrait_fallback(
    student_name: str,
    course_title: str,
    course_code: str,
    completion_date: str,
    cert_id: str,
    course_topic: str | None = None,
) -> bytes:
    """Fallback generator using ReportLab A4 Portrait when Headless Chromium is unavailable.

    Upgraded with official PPTQ logo, standard citation text, emerald course box with course code badge,
    and elevated footer coordinates preventing any clipping or page overflow.
    """
    font_normal, font_bold = _init_fonts()

    buf = io.BytesIO()
    pagesize = A4  # Portrait (595.27 x 841.89 pt)
    w, h = pagesize
    cx = w / 2

    c = canvas.Canvas(buf, pagesize=pagesize)
    c.setTitle(f"Chung_chi_{course_code or 'PPTQ'}.pdf")
    c.setAuthor("PPTQ LMS Academy")
    c.setSubject(f"Certificate of Completion - {course_title}")

    # 1. Warm ivory background
    c.setFillColor(colors.HexColor("#FAFDFB"))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # 2. PPTQ watermark in background center
    if os.path.exists(_LOGO_WATERMARK_PATH):
        try:
            wm_w = 340
            wm_h = wm_w * (260 / 743)
            c.saveState()
            c.drawImage(
                _LOGO_WATERMARK_PATH,
                (w - wm_w) / 2,
                (h - wm_h) / 2,
                width=wm_w,
                height=wm_h,
                mask="auto",
            )
            c.restoreState()
        except Exception:
            pass

    # Brand Colors
    emerald_color = colors.HexColor("#0F3D2E")
    gold_color = colors.HexColor("#C59B27")
    slate_dark = colors.HexColor("#1E293B")
    slate_sub = colors.HexColor("#334155")
    slate_muted = colors.HexColor("#64748B")

    # 3. Outer border: Emerald Green (#0F3D2E)
    c.setStrokeColor(emerald_color)
    c.setLineWidth(3.5)
    c.rect(20, 20, w - 40, h - 40, fill=0, stroke=1)

    # 4. Inner border: Imperial Gold (#C59B27)
    c.setStrokeColor(gold_color)
    c.setLineWidth(1.5)
    c.rect(26, 26, w - 52, h - 52, fill=0, stroke=1)

    # 5. Top Official PPTQ Logo
    if os.path.exists(_LOGO_LIGHT_PATH):
        try:
            logo_w = 92
            logo_h = logo_w * (260 / 743)
            c.drawImage(_LOGO_LIGHT_PATH, cx - (logo_w / 2), 766, width=logo_w, height=logo_h, mask="auto")
        except Exception:
            pass

    # 6. Academy Header Title
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 11)
    c.drawCentredString(cx, 750, "HỆ THỐNG HỌC TẬP TRỰC TUYẾN PPTQ LMS")
    c.setFillColor(colors.HexColor("#B8860B"))
    c.setFont(font_bold, 7.5)
    c.drawCentredString(cx, 737, "PPTQ LMS ONLINE LEARNING & TRAINING SYSTEM")

    # 7. Main Certificate Titles
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 18)
    c.drawCentredString(cx, 705, "CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC")
    c.setFillColor(gold_color)
    c.setFont(font_bold, 8.5)
    c.drawCentredString(cx, 690, "CERTIFICATE OF COURSE COMPLETION")

    # Ornamental divider line with diamond
    c.setStrokeColor(gold_color)
    c.setLineWidth(1)
    c.line(cx - 120, 680, cx - 12, 680)
    c.line(cx + 12, 680, cx + 120, 680)
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 9)
    c.drawCentredString(cx, 677, "❖")

    # 8. Recipient Block
    c.setFillColor(slate_sub)
    c.setFont(font_normal, 9.5)
    c.drawCentredString(cx, 654, "Trân trọng trao tặng học viên")
    c.setFillColor(slate_muted)
    c.setFont(font_normal, 7.5)
    c.drawCentredString(cx, 642, "This certificate is proudly conferred upon")

    style_student = ParagraphStyle(
        "CertStudentName",
        fontName=font_bold,
        fontSize=22,
        leading=26,
        textColor=emerald_color,
        alignment=1,
    )
    p_student = Paragraph(f"<b>{escape(student_name.upper())}</b>", style_student)
    sw, sh = p_student.wrap(w - 120, 36)
    p_student.drawOn(c, cx - (sw / 2), 606)

    c.setStrokeColor(gold_color)
    c.setLineWidth(1.5)
    c.line(cx - 140, 598, cx + 140, 598)

    # 9. Citation Block (Standardized official recognition text)
    style_cit_vi = ParagraphStyle(
        "CertCitationVi",
        fontName=font_normal,
        fontSize=9,
        leading=13,
        textColor=slate_dark,
        alignment=1,
    )
    p_cit_vi = Paragraph(
        "Đã hoàn thành xuất sắc chương trình đào tạo, đáp ứng đầy đủ các tiêu chuẩn học thuật, bài tập thực hành và vượt qua kỳ khảo thí năng lực của học phần:",
        style_cit_vi,
    )
    cw_vi, ch_vi = p_cit_vi.wrap(470, 34)
    p_cit_vi.drawOn(c, cx - (cw_vi / 2), 562)

    style_cit_en = ParagraphStyle(
        "CertCitationEn",
        fontName=font_normal,
        fontSize=7.5,
        leading=11,
        textColor=slate_muted,
        alignment=1,
    )
    p_cit_en = Paragraph(
        "For having successfully mastered the curriculum requirements, practical modules, and standardized competency assessments prescribed for the course:",
        style_cit_en,
    )
    cw_en, ch_en = p_cit_en.wrap(470, 26)
    p_cit_en.drawOn(c, cx - (cw_en / 2), 534)

    # 10. Course Banner Box (Emerald accents, topic, and course code badge)
    box_w = 470
    box_h = 58
    box_x = cx - (box_w / 2)
    box_y = 455
    c.setFillColor(colors.HexColor("#F4EFE1"))
    c.setStrokeColor(gold_color)
    c.setLineWidth(1)
    c.roundRect(box_x, box_y, box_w, box_h, 3, fill=1, stroke=1)

    # Accent bars left and right (Emerald #0F3D2E)
    c.setFillColor(emerald_color)
    c.rect(box_x, box_y, 4, box_h, fill=1, stroke=0)
    c.rect(box_x + box_w - 4, box_y, 4, box_h, fill=1, stroke=0)

    style_course = ParagraphStyle(
        "CertCourseTitle",
        fontName=font_bold,
        fontSize=11.5,
        leading=14,
        textColor=emerald_color,
        alignment=1,
    )
    p_course = Paragraph(f"<b>{escape(course_title.upper())}</b>", style_course)
    cw, ch = p_course.wrap(box_w - 30, 28)
    p_course.drawOn(c, cx - (cw / 2), box_y + box_h - ch - 8)

    # Topic & Course Code Badge inside banner
    actual_topic = course_topic or "Chuyên môn tiêu chuẩn"
    c.setFillColor(slate_sub)
    c.setFont(font_normal, 8)
    c.drawCentredString(cx - 50, box_y + 12, f"Chuyên đề đào tạo: {actual_topic}")

    # Badge: MÃ HỌC PHẦN
    badge_w = 110
    badge_h = 15
    badge_x = cx + 55
    badge_y = box_y + 7
    c.setFillColor(emerald_color)
    c.roundRect(badge_x, badge_y, badge_w, badge_h, 2.5, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font_bold, 7)
    c.drawCentredString(badge_x + (badge_w / 2), badge_y + 4, f"MÃ HỌC PHẦN: {escape(course_code)}")

    # 11. Authorities & Governance Signatures (Elevated coordinates)
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 8.5)
    c.drawCentredString(130, 310, "HỘI ĐỒNG ĐÀO TẠO")
    c.drawCentredString(w - 130, 310, "BAN GIẢNG HUẤN & QUẢN TRỊ")
    c.setFillColor(slate_muted)
    c.setFont(font_normal, 7)
    c.drawCentredString(130, 298, "ACADEMIC GOVERNANCE BOARD")
    c.drawCentredString(w - 130, 298, "ACADEMIC DIRECTOR & SYSTEM AUTHORITY")

    c.setFillColor(colors.HexColor("#165640"))
    c.setFont(font_bold, 10)
    c.drawCentredString(130, 262, "PPTQ Academic Council")
    c.drawCentredString(w - 130, 262, "PPTQ Electronic Certification")

    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(0.8)
    c.line(60, 252, 200, 252)
    c.line(w - 200, 252, w - 60, 252)

    c.setFillColor(slate_dark)
    c.setFont(font_bold, 8)
    c.drawCentredString(130, 238, "Chứng Thực Đào Tạo Điện Tử")
    c.drawCentredString(w - 130, 238, "Hệ Thống Quản Trị Học Tập PPTQ")

    c.setFillColor(slate_muted)
    c.setFont(font_normal, 6.8)
    c.drawCentredString(130, 226, "Verified Academic Record")
    c.drawCentredString(w - 130, 226, "Official Digital Signature")

    # 12. Center Official Digital Seal
    seal_y = 265
    c.setFillColor(colors.white)
    c.setStrokeColor(emerald_color)
    c.setLineWidth(2.5)
    c.circle(cx, seal_y, 38, fill=1, stroke=1)
    c.setStrokeColor(gold_color)
    c.setLineWidth(1.2)
    c.circle(cx, seal_y, 34, fill=0, stroke=1)

    c.setFillColor(emerald_color)
    c.setFont(font_bold, 8)
    c.drawCentredString(cx, seal_y + 17, "PPTQ LMS")

    # Seal stamp pill
    pill_w = 56
    pill_h = 13
    c.setFillColor(emerald_color)
    c.setStrokeColor(gold_color)
    c.setLineWidth(0.8)
    c.roundRect(cx - (pill_w / 2), seal_y - 6, pill_w, pill_h, 2.5, fill=1, stroke=1)
    c.setFillColor(colors.white)
    c.setFont(font_bold, 6.5)
    c.drawCentredString(cx, seal_y - 2.5, "ĐÃ XÁC NHẬN")

    c.setFillColor(emerald_color)
    c.setFont(font_bold, 6)
    c.drawCentredString(cx, seal_y - 16, "DIGITAL CERTIFIED")
    c.setFillColor(colors.HexColor("#9A781C"))
    c.setFont(font_normal, 5.5)
    c.drawCentredString(cx, seal_y - 24, "Authentic Credential")

    # 13. Bottom Registry Ledger Bar
    reg_y = 80
    reg_h = 44
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(1)
    c.rect(40, reg_y, w - 80, reg_h, fill=1, stroke=1)

    # Top emerald border accent
    c.setStrokeColor(emerald_color)
    c.setLineWidth(2.5)
    c.line(40, reg_y + reg_h, w - 40, reg_y + reg_h)

    c.setFillColor(slate_muted)
    c.setFont(font_bold, 7.5)
    c.drawCentredString(160, reg_y + 26, "NGÀY CẤP / DATE OF ISSUE")
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 9.5)
    c.drawCentredString(160, reg_y + 11, completion_date)

    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(1)
    c.line(cx, reg_y, cx, reg_y + reg_h)

    c.setFillColor(slate_muted)
    c.setFont(font_bold, 7.5)
    c.drawCentredString(w - 160, reg_y + 26, "MÃ SỐ CHỨNG CHỈ / CREDENTIAL ID")
    c.setFillColor(emerald_color)
    c.setFont(font_bold, 9.5)
    c.drawCentredString(w - 160, reg_y + 11, cert_id)

    # 14. Bottom ornamental bar
    c.setFillColor(emerald_color)
    c.setStrokeColor(gold_color)
    c.setLineWidth(1)
    c.rect(45, 52, 8, 8, fill=1, stroke=1)
    c.rect(w - 53, 52, 8, 8, fill=1, stroke=1)
    c.setStrokeColor(colors.HexColor("#D4B459"))
    c.line(59, 56, w - 59, 56)

    c.showPage()
    c.save()
    return buf.getvalue()


def generate_course_certificate_pdf(
    student: Any,
    course: Any,
    completion_date: str | date | datetime | None = None,
    cert_id: str | uuid.UUID | None = None,
) -> bytes:
    """Generate an official, high-fidelity Portrait A4 Course Completion Certificate PDF.

    Multi-tier rendering pipeline:
    - Tier 1: Playwright Chromium Headless (if installed and functioning).
    - Tier 2: Operating System CLI Headless Browser (msedge, chrome, chromium) via
              --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer --print-to-pdf.
              Ensures 100% pixel-perfect equivalence to the HTML browser view.
    - Tier 3: Upgraded ReportLab Portrait A4 fallback (guaranteed Unicode support, PPTQ logo,
              clean layout with no clipping or page overflow).
    """
    html_markup = generate_course_certificate_html(
        student=student,
        course=course,
        completion_date=completion_date,
        cert_id=cert_id,
    )

    # 1. Primary: Playwright Chromium Headless PDF rendering
    try:
        if os.path.exists("/ms-playwright"):
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/ms-playwright")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            launch_args = [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
            ]
            browser = None
            try:
                browser = p.chromium.launch(args=launch_args)
            except Exception:
                for channel in ["chrome", "msedge"]:
                    try:
                        browser = p.chromium.launch(channel=channel, args=launch_args)
                        break
                    except Exception:
                        continue

            if browser is not None:
                page = browser.new_page()
                page.set_content(html_markup, wait_until="networkidle")
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
                    prefer_css_page_size=True,
                )
                browser.close()
                if pdf_bytes and pdf_bytes.startswith(b"%PDF-"):
                    return pdf_bytes
    except Exception as ex:
        import logging
        logging.getLogger(__name__).warning(f"Playwright PDF generation skipped: {ex}")

    # 2. Secondary: Operating System CLI Headless Browser (Chrome / Edge / Chromium)
    cli_pdf = _generate_cli_browser_pdf(html_markup)
    if cli_pdf and cli_pdf.startswith(b"%PDF-"):
        return cli_pdf

    # 3. Fallback: ReportLab Portrait A4
    if isinstance(student, dict):
        s_name = student.get("display_name") or student.get("email") or "Học viên"
    else:
        s_name = getattr(student, "display_name", None) or getattr(student, "email", "Học viên")

    if isinstance(course, dict):
        c_title = course.get("title") or "Khóa học"
        c_code = course.get("course_code") or "PPTQ"
        c_topic = course.get("category") or course.get("description") or "Chuyên môn tiêu chuẩn"
    else:
        c_title = getattr(course, "title", "Khóa học")
        c_code = getattr(course, "course_code", "PPTQ")
        c_topic = getattr(course, "category", None) or getattr(course, "description", None) or "Chuyên môn tiêu chuẩn"

    fmt_d = (
        completion_date.strftime("%d/%m/%Y")
        if isinstance(completion_date, (datetime, date))
        else (str(completion_date) if completion_date else datetime.now().strftime("%d/%m/%Y"))
    )
    fmt_c_id = str(cert_id) if cert_id else f"CERT-{c_code}-{uuid.uuid4().hex[:12].upper()}"

    return _generate_reportlab_portrait_fallback(
        student_name=str(s_name),
        course_title=str(c_title),
        course_code=str(c_code),
        completion_date=fmt_d,
        cert_id=fmt_c_id,
        course_topic=str(c_topic),
    )
