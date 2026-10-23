"""Script to update the downloaded certificate HTML and create the system template."""

from __future__ import annotations

import base64
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATERMARK_PATH = os.path.join(BASE_DIR, "frontend", "assets", "img", "pptq_logo_watermark.png")
DOWNLOAD_PATH = r"C:\Users\LENOVO\Downloads\ch_ng_ch_ho_n_th_nh_kh_a_h_c_pptq_lms.html"
SYSTEM_TEMPLATE_DIR = os.path.join(BASE_DIR, "src", "pwd301", "templates", "certificate")
SYSTEM_TEMPLATE_PATH = os.path.join(SYSTEM_TEMPLATE_DIR, "course_completion_certificate.html")

with open(WATERMARK_PATH, "rb") as f:
    b64_watermark = base64.b64encode(f.read()).decode("utf-8")

CSS_STYLES = """
        @page {
            size: A4 portrait;
            margin: 0;
        }
        *, *::before, *::after {
            box-sizing: border-box;
        }
        html, body {
            margin: 0;
            padding: 0;
        }
        html {
            background-color: #e2e8f0;
        }
        @media (prefers-color-scheme: dark) {
            html {
                background-color: #18181b;
            }
        }
        body {
            padding: 24px 0;
            margin: 0 auto;
            max-width: 900px !important;
            border: none !important;
            background: transparent !important;
            font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1a2a24;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: geometricPrecision;
            font-kerning: normal;
            font-variant-ligatures: common-ligatures;
        }

        /* A4 Portrait Certificate Canvas (210mm x 297mm) */
        .certificate-canvas {
            width: 210mm;
            min-height: 297mm;
            height: 297mm;
            margin: 0 auto;
            padding: 12mm;
            background-color: #fdfbf7;
            background-image: radial-gradient(circle at 50% 35%, #ffffff 0%, #faf6eb 70%, #f3ebd8 100%);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
        }

        @media print {
            html, body {
                background: #ffffff !important;
                padding: 0 !important;
            }
            .certificate-canvas {
                box-shadow: none !important;
                margin: 0 !important;
                width: 210mm !important;
                height: 297mm !important;
            }
        }

        /* Outer & Inner Sovereign Borders */
        .frame-outer {
            border: 3.5px solid #0F3D2E;
            padding: 4.5px;
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .frame-inner {
            border: 1.5px solid #C59B27;
            padding: 20px 30px 18px 30px;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            background-color: rgba(255, 255, 255, 0.45);
        }

        /* Top & Bottom Ornamental Framing Rules */
        .ornament-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            position: relative;
            z-index: 2;
        }
        .ornament-corner-box {
            width: 10px;
            height: 10px;
            background-color: #0F3D2E;
            border: 1.5px solid #C59B27;
            flex-shrink: 0;
        }
        .ornament-line {
            flex: 1;
            height: 1px;
            background-color: #d4b459;
            margin: 0 14px;
        }

        /* Watermark Overlay (Centered Base64 Logo) */
        .watermark-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 125mm;
            opacity: 0.08;
            pointer-events: none;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .watermark-logo {
            width: 100%;
            height: auto;
            display: block;
        }

        /* 1. Header / Academy Identity */
        .header-section {
            text-align: center;
            margin-top: 2px;
            position: relative;
            z-index: 2;
        }
        .emblem-wrapper {
            display: flex;
            justify-content: center;
            margin-bottom: 6px;
        }
        .academy-vi {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 2px;
            color: #0F3D2E;
            text-transform: uppercase;
            margin: 0;
            line-height: 1.35;
        }
        .academy-en {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 10.5px;
            font-weight: 600;
            letter-spacing: 2.5px;
            color: #B8860B;
            text-transform: uppercase;
            margin: 4px 0 0 0;
            line-height: 1.35;
        }

        /* 2. Title Block */
        .title-section {
            text-align: center;
            margin-top: 8px;
            position: relative;
            z-index: 2;
        }
        .cert-main-title {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 28px;
            font-weight: 800;
            color: #0F3D2E;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin: 0;
            line-height: 1.3;
        }
        .cert-sub-title {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 3.5px;
            color: #C59B27;
            text-transform: uppercase;
            margin: 5px 0 0 0;
        }
        .ornamental-divider {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 8px auto 0 auto;
            width: 62%;
        }
        .ornamental-divider .line {
            flex: 1;
            height: 1.5px;
            background-color: #C59B27;
        }
        .ornamental-divider .diamond {
            color: #0F3D2E;
            font-size: 10pt;
            padding: 0 12px;
            line-height: 1;
        }

        /* 3. Recipient Block */
        .recipient-section {
            text-align: center;
            margin-top: 8px;
            position: relative;
            z-index: 2;
        }
        .present-label-vi {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 13.5px;
            font-style: italic;
            font-weight: 500;
            color: #334155;
            letter-spacing: 0px;
            margin: 0;
        }
        .present-label-en {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 11px;
            font-weight: 400;
            color: #64748B;
            margin: 3px 0 8px 0;
            letter-spacing: 0.5px;
        }
        .recipient-name {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 36px;
            font-weight: 700;
            color: #0F3D2E;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin: 0 auto;
            padding-bottom: 6px;
            border-bottom: 2px solid #C59B27;
            display: inline-block;
            min-width: 68%;
        }

        /* 4. Citation & Course Block */
        .citation-section {
            text-align: center;
            margin-top: 10px;
            padding: 0 4px;
            position: relative;
            z-index: 2;
        }
        .citation-vi {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 13px;
            font-weight: 400;
            line-height: 1.6;
            letter-spacing: 0px;
            color: #1E293B;
            margin: 0 auto;
            max-width: 92%;
        }
        .citation-en {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 11.5px;
            font-weight: 400;
            font-style: italic;
            line-height: 1.5;
            letter-spacing: 0px;
            color: #64748B;
            margin: 5px auto 12px auto;
            max-width: 88%;
        }

        .course-banner {
            background-color: #f4efe1;
            border: 1px solid #d4b459;
            border-left: 5px solid #0F3D2E;
            border-right: 5px solid #0F3D2E;
            padding: 12px 16px;
            margin: 0 auto;
            max-width: 96%;
        }
        .course-title-main {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #0F3D2E;
            margin: 0;
            letter-spacing: 0px;
            line-height: 1.45;
            text-transform: uppercase;
        }
        .course-title-original {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 12.5px;
            font-weight: 400;
            color: #334155;
            letter-spacing: 0px;
            margin: 6px 0 0 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .course-title-original strong {
            font-weight: 700;
        }
        .course-code-badge {
            display: inline-block;
            background-color: #0F3D2E;
            color: #FFFFFF;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10.5px;
            font-weight: 700;
            padding: 3px 9px;
            letter-spacing: 1px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        /* 5. Governance & Seal Section */
        .governance-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
            padding: 0 4px;
            position: relative;
            z-index: 2;
        }
        .gov-col {
            width: 34%;
            text-align: center;
        }
        .seal-col {
            width: 32%;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .gov-role-vi {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 11.5px;
            font-weight: 700;
            color: #0F3D2E;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
        }
        .gov-role-en {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 9.5px;
            font-weight: 500;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 4px 0 8px 0;
            line-height: 1.35;
        }
        .sig-script {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 15.5px;
            font-style: italic;
            font-weight: 700;
            color: #0F3D2E;
            letter-spacing: 0px;
            margin: 6px 0;
            padding: 4px 0;
            line-height: 1.3;
        }
        .sig-divider {
            width: 85%;
            height: 1px;
            background-color: #94a3b8;
            margin: 6px auto;
        }
        .gov-sub-vi {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 11.5px;
            font-weight: 700;
            color: #1E293B;
            letter-spacing: 0px;
            margin: 5px 0 0 0;
        }
        .gov-sub-en {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 10px;
            font-weight: 400;
            color: #64748B;
            letter-spacing: 0px;
            margin: 3px 0 0 0;
        }

        /* 6. Metadata Registry Bar */
        .registry-ledger {
            margin-top: 12px;
            margin-bottom: 2px;
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-top: 2.5px solid #0F3D2E;
            padding: 10px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 2;
        }
        .registry-item {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 0 12px;
        }
        .registry-item + .registry-item {
            border-left: 1px solid #cbd5e1;
        }
        .reg-label {
            font-family: 'Be Vietnam Pro', sans-serif;
            font-size: 10.5px;
            font-weight: 600;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .reg-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12.5px;
            font-weight: 700;
            color: #0F3D2E;
            margin-top: 4px;
            letter-spacing: 0.5px;
        }
"""


def get_html_content(
    recipient_name: str = "HOÀNG PHÚC",
    course_title: str = "KỸ THUẬT & CHIẾN THUẬT KIỂM SOÁT ĐƯỜNG GIỮA",
    course_topic: str = "Cách đi lane Mid",
    course_code: str = "MID001",
    issue_date: str = "23/10/2026",
    cert_id: str = "CERT-MID001-3-1792740720",
    watermark_b64: str = b64_watermark,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Chứng Nhận Hoàn Thành Khóa Học - {recipient_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,600;1,700&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
    <style>{CSS_STYLES}
    </style>
</head>
<body>
    <div class="certificate-canvas">
        <div class="frame-outer">
            <div class="frame-inner">
                
                <!-- Watermark Logo PPTQ LMS Centered in Background -->
                <div class="watermark-container">
                    <img class="watermark-logo" src="data:image/png;base64,{watermark_b64}" alt="PPTQ LMS Watermark" />
                </div>

                <!-- Top Ornamental Rule -->
                <div class="ornament-bar">
                    <div class="ornament-corner-box"></div>
                    <div class="ornament-line"></div>
                    <div class="ornament-corner-box"></div>
                </div>

                <!-- 1. Academy Header & Crest SVG -->
                <div class="header-section">
                    <div class="emblem-wrapper">
                        <svg role="img" aria-label="Biểu trưng Học viện Đào tạo Kỹ thuật PPTQ LMS" style="height: 25mm; width: auto;" viewBox="0 0 180 115">
                            <title>Biểu trưng Học viện PPTQ LMS</title>
                            <!-- Outer Laurel Branches -->
                            <path d="M46,96 C20,82 14,52 24,24 C29,13 38,8 48,6" fill="none" stroke="#C59B27" stroke-width="2.2" stroke-linecap="round"/>
                            <path d="M134,96 C160,82 166,52 156,24 C151,13 142,8 132,6" fill="none" stroke="#C59B27" stroke-width="2.2" stroke-linecap="round"/>
                            
                            <!-- Left Laurel Leaves -->
                            <ellipse cx="20" cy="64" rx="5.5" ry="2.6" transform="rotate(-35 20 64)" fill="#C59B27"/>
                            <ellipse cx="18" cy="44" rx="5.5" ry="2.6" transform="rotate(-15 18 44)" fill="#C59B27"/>
                            <ellipse cx="24" cy="25" rx="5.5" ry="2.6" transform="rotate(15 24 25)" fill="#C59B27"/>
                            <ellipse cx="36" cy="11" rx="5" ry="2.4" transform="rotate(35 36 11)" fill="#C59B27"/>
                            
                            <!-- Right Laurel Leaves -->
                            <ellipse cx="160" cy="64" rx="5.5" ry="2.6" transform="rotate(35 160 64)" fill="#C59B27"/>
                            <ellipse cx="162" cy="44" rx="5.5" ry="2.6" transform="rotate(15 162 44)" fill="#C59B27"/>
                            <ellipse cx="156" cy="25" rx="5.5" ry="2.6" transform="rotate(-15 156 25)" fill="#C59B27"/>
                            <ellipse cx="144" cy="11" rx="5" ry="2.4" transform="rotate(-35 144 11)" fill="#C59B27"/>

                            <!-- Heraldic Shield -->
                            <path d="M44,10 L136,10 L136,52 C136,78 90,96 90,96 C90,96 44,78 44,52 Z" fill="#0F3D2E" stroke="#C59B27" stroke-width="2.6" stroke-linejoin="round"/>
                            <path d="M50,16 L130,16 L130,51 C130,72 90,88 90,88 C90,88 50,72 50,51 Z" fill="none" stroke="#e5c878" stroke-width="1.1" stroke-linejoin="round"/>

                            <!-- Top Gold Star Inside Shield -->
                            <polygon points="90,21 92.4,26.8 98.6,26.8 93.6,30.5 95.5,36.3 90,32.7 84.5,36.3 86.4,30.5 81.4,26.8 87.6,26.8" fill="#e5c878"/>

                            <!-- Cleanly Centered Shield Typography: Be Vietnam Pro 700 12px 1px #FDFBF7 -->
                            <text x="90" y="51" text-anchor="middle" fill="#FDFBF7" font-family="'Be Vietnam Pro', sans-serif" font-size="12" font-weight="700" letter-spacing="1">PPTQ</text>
                            <text x="90" y="67" text-anchor="middle" fill="#FDFBF7" font-family="'Be Vietnam Pro', sans-serif" font-size="12" font-weight="700" letter-spacing="1">LMS</text>

                            <!-- Base Ribbon Line -->
                            <path d="M58,105 L122,105" stroke="#C59B27" stroke-width="2.2" stroke-linecap="round"/>
                            <circle cx="90" cy="105" r="3" fill="#0F3D2E" stroke="#C59B27" stroke-width="1.5"/>
                        </svg>
                    </div>
                    <p class="academy-vi">HỌC VIỆN ĐÀO TẠO KỸ THUẬT PPTQ LMS</p>
                    <p class="academy-en">PPTQ LMS INSTITUTE OF TECHNICAL TRAINING &amp; EXCELLENCE</p>
                </div>

                <!-- 2. Certificate Main Title -->
                <div class="title-section">
                    <h1 class="cert-main-title">CHỨNG NHẬN HOÀN THÀNH KHÓA HỌC</h1>
                    <p class="cert-sub-title">CERTIFICATE OF COURSE COMPLETION</p>
                    <div class="ornamental-divider">
                        <span class="line"></span>
                        <span class="diamond">❖</span>
                        <span class="line"></span>
                    </div>
                </div>

                <!-- 3. Recipient Information -->
                <div class="recipient-section">
                    <p class="present-label-vi">Trân trọng trao tặng học viên</p>
                    <p class="present-label-en">This certificate is proudly conferred upon</p>
                    <h2 class="recipient-name">{recipient_name}</h2>
                </div>

                <!-- 4. Citation & Course Details -->
                <div class="citation-section">
                    <p class="citation-vi">
                        Đã hoàn thành xuất sắc chương trình đào tạo, đáp ứng đầy đủ các tiêu chuẩn học thuật, bài tập thực hành và vượt qua kỳ khảo thí năng lực của học phần:
                    </p>
                    <p class="citation-en">
                        For having successfully mastered the curriculum requirements, practical modules, and standardized competency assessments prescribed for the course:
                    </p>

                    <div class="course-banner">
                        <h3 class="course-title-main">{course_title}</h3>
                        <p class="course-title-original">
                            <span>Chuyên đề đào tạo: <strong>{course_topic}</strong></span>
                            <span class="course-code-badge">MÃ HỌC PHẦN: {course_code}</span>
                        </p>
                    </div>
                </div>

                <!-- 5. Signatures & Digital Seal -->
                <div class="governance-section">
                    <!-- Left Authority -->
                    <div class="gov-col">
                        <p class="gov-role-vi">HỘI ĐỒNG ĐÀO TẠO</p>
                        <p class="gov-role-en">ACADEMIC GOVERNANCE BOARD</p>
                        <div class="sig-script">PPTQ Academic Council</div>
                        <div class="sig-divider"></div>
                        <p class="gov-sub-vi">Chứng Thực Đào Tạo Điện Tử</p>
                        <p class="gov-sub-en">Verified Academic Record</p>
                    </div>

                    <!-- Center Official Digital Seal (180x180 SVG) -->
                    <div class="seal-col">
                        <svg role="img" aria-label="Con dấu xác nhận điện tử PPTQ LMS" style="height: 35mm; width: auto;" viewBox="0 0 180 180">
                            <title>Con dấu Xác nhận PPTQ LMS Digital Certified</title>
                            <!-- Concentric Seal Rings -->
                            <circle cx="90" cy="90" r="84" fill="#ffffff" stroke="#0F3D2E" stroke-width="4"/>
                            <circle cx="90" cy="90" r="77" fill="none" stroke="#C59B27" stroke-width="1.8"/>
                            <circle cx="90" cy="90" r="70" fill="#faf7f0" stroke="#0F3D2E" stroke-width="1.2" stroke-dasharray="3.5,2.5"/>

                            <!-- Upper Seal Header: Be Vietnam Pro 700 11px 0.5px #0F3D2E -->
                            <text x="90" y="47" text-anchor="middle" fill="#0F3D2E" font-family="'Be Vietnam Pro', sans-serif" font-size="11" font-weight="700" letter-spacing="0.5">PPTQ LMS</text>

                            <!-- Three Gold Stars -->
                            <polygon points="68,54 69.6,57.6 73.5,57.6 70.4,59.9 71.5,63.6 68,61.3 64.5,63.6 65.6,59.9 62.5,57.6 66.4,57.6" fill="#C59B27"/>
                            <polygon points="90,51 92,55.4 96.8,55.4 92.9,58.2 94.4,62.8 90,60 85.6,62.8 87.1,58.2 83.2,55.4 88,55.4" fill="#C59B27"/>
                            <polygon points="112,54 113.6,57.6 117.5,57.6 114.4,59.9 115.5,63.6 112,61.3 108.5,63.6 109.6,59.9 106.5,57.6 110.4,57.6" fill="#C59B27"/>

                            <!-- Center Stamp Pill: Be Vietnam Pro 700 9.5px 0.5px #FFFFFF on #0F3D2E -->
                            <rect x="33" y="74" width="114" height="26" rx="5" fill="#0F3D2E" stroke="#C59B27" stroke-width="1.2"/>
                            <text x="90" y="91" text-anchor="middle" fill="#FFFFFF" font-family="'Be Vietnam Pro', sans-serif" font-size="9.5" font-weight="700" letter-spacing="0.5">ĐÃ XÁC NHẬN</text>

                            <!-- Lower Seal Labels: Be Vietnam Pro 700 8.5px 0.5px #0F3D2E -->
                            <text x="90" y="116" text-anchor="middle" fill="#0F3D2E" font-family="'Be Vietnam Pro', sans-serif" font-size="8.5" font-weight="700" letter-spacing="0.5">DIGITAL CERTIFIED</text>
                            <text x="90" y="130" text-anchor="middle" fill="#B8860B" font-family="'Be Vietnam Pro', sans-serif" font-size="7.5" font-style="italic" font-weight="600">Authentic Credential</text>
                            
                            <!-- Bottom Small Diamond Accent -->
                            <polygon points="90,140 93,143 90,146 87,143" fill="#C59B27"/>
                        </svg>
                    </div>

                    <!-- Right Authority -->
                    <div class="gov-col">
                        <p class="gov-role-vi">BAN GIẢNG HUẤN &amp; QUẢN TRỊ</p>
                        <p class="gov-role-en">ACADEMIC DIRECTOR &amp; SYSTEM AUTHORITY</p>
                        <div class="sig-script">PPTQ Electronic Certification</div>
                        <div class="sig-divider"></div>
                        <p class="gov-sub-vi">Hệ Thống Quản Trị Học Tập PPTQ</p>
                        <p class="gov-sub-en">Official Digital Signature</p>
                    </div>
                </div>

                <!-- 6. Official Registry Bar -->
                <div class="registry-ledger">
                    <div class="registry-item">
                        <span class="reg-label">NGÀY CẤP / DATE OF ISSUE</span>
                        <span class="reg-value">{issue_date}</span>
                    </div>
                    <div class="registry-item">
                        <span class="reg-label">MÃ SỐ CHỨNG CHỈ / CREDENTIAL ID</span>
                        <span class="reg-value">{cert_id}</span>
                    </div>
                </div>

                <!-- Bottom Ornamental Rule -->
                <div class="ornament-bar">
                    <div class="ornament-corner-box"></div>
                    <div class="ornament-line"></div>
                    <div class="ornament-corner-box"></div>
                </div>

            </div>
        </div>
    </div>
</body>
</html>"""


def main() -> None:
    # 1. Update the downloaded file at C:\Users\LENOVO\Downloads\ch_ng_ch_ho_n_th_nh_kh_a_h_c_pptq_lms.html
    html_download = get_html_content()
    with open(DOWNLOAD_PATH, "w", encoding="utf-8") as f:
        f.write(html_download)
    print(f"[OK] Updated downloaded file at: {DOWNLOAD_PATH}")

    # 2. Write master system template in src/pwd301/templates/certificate/course_completion_certificate.html
    os.makedirs(SYSTEM_TEMPLATE_DIR, exist_ok=True)
    with open(SYSTEM_TEMPLATE_PATH, "w", encoding="utf-8") as f:
        f.write(html_download)
    print(f"[OK] Created system template at: {SYSTEM_TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
