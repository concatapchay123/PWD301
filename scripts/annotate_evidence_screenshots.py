import os
from PIL import Image, ImageDraw, ImageFont

orig_dir = r"e:\PWD301\artifacts\lms-remediation-2026-10-17\02-rounds\round-01\screenshots-original"
annot_dir = r"e:\PWD301\artifacts\lms-remediation-2026-10-17\02-rounds\round-01\screenshots-annotated"
os.makedirs(annot_dir, exist_ok=True)

annotations = [
    {
        "file": "01_preflight_checklist_granular_subitems.png",
        "title": "BUG 01: Preflight Checklist chia nho thanh 2 sub-items ro rang (Mo ta & Chuan dau ra)",
        "boxes": [
            {"rect": [320, 360, 960, 500], "color": (239, 68, 68), "label": "Sub-items tach biet: Mo ta (CHUA DAT) vs SLO (CHUA DAT) kem nut 'Sua mo ta' & 'Sua SLO'"}
        ]
    },
    {
        "file": "02_slo_editor_weight_validation.png",
        "title": "BUG 01: Trinh bien tap SLO kiem soat ty trong thoi gian thuc (Canh bao khi nhap 500%)",
        "boxes": [
            {"rect": [250, 160, 1020, 240], "color": (239, 68, 68), "label": "Thanh trang thai: Canh bao ty trong khong hop le & tu dong chuan hoa"},
            {"rect": [700, 340, 850, 400], "color": (239, 68, 68), "label": "Vien do & bao loi khi ty trong vuot 100% (500%)"}
        ]
    },
    {
        "file": "03_preflight_checklist_criterion_passed.png",
        "title": "BUG 01: Tieu chuan 3 DAT khi da cap nhat day du Mo ta hop le & SLOs chuan hoa 100%",
        "boxes": [
            {"rect": [320, 330, 960, 520], "color": (16, 185, 129), "label": "Tieu chuan 3: DAT TIEU CHUAN (Day du mo ta >= 20 ky tu & SLOs 100%)"}
        ]
    },
    {
        "file": "04_youtube_trailer_preview.png",
        "title": "BUG 02: YouTube Trailer Embed su dung youtube-nocookie voi modestbranding & sach se",
        "boxes": [
            {"rect": [200, 200, 1080, 680], "color": (16, 185, 129), "label": "youtube-nocookie.com embed: modestbranding=1, rel=0, playsinline=1, enablejsapi=1"}
        ]
    },
    {
        "file": "05_youtube_clean_preview_modal.png",
        "title": "BUG 02: Modal xem truoc video YouTube Unlisted sach se, chuan phong cach PWD301 LMS",
        "boxes": [
            {"rect": [150, 60, 1130, 720], "color": (16, 185, 129), "label": "Modal phong chieu chuan: Huy hieu YOUTUBE UNLISTED, nen toi chong loa, khong nut thua"}
        ]
    },
    {
        "file": "06_course_changeset_submitted.png",
        "title": "BUG 03: Dot cap nhat giao trinh #120006 hien thi trong Hang doi phe duyet Admin",
        "boxes": [
            {"rect": [100, 280, 1180, 420], "color": (59, 130, 246), "label": "Dot cap nhat #120006 (2 moi, 0 sua, 0 xoa) - Peppa Pig (Cho duyet)"}
        ]
    },
    {
        "file": "07_admin_course_approval_success.png",
        "title": "BUG 03: Phe duyet thanh cong 100% - Khong con loi SQL Server 2601 trung vi tri",
        "boxes": [
            {"rect": [100, 240, 1180, 550], "color": (16, 185, 129), "label": "Admin Phe duyet thanh cong dot cap nhat giao trinh - Audit log PERSISTED"}
        ]
    },
    {
        "file": "08_course_approved_published_status.png",
        "title": "BUG 03: Cac bai hoc moi da xuat ban chinh thuc (Pos 1, Pos 2) - Bai xoa luu TRASH an toan",
        "boxes": [
            {"rect": [50, 180, 380, 650], "color": (16, 185, 129), "label": "Curriculum Studio: Bai 1 (Pos 1) & Bai123 (Pos 2) da xuat ban (PUBLISHED)"}
        ]
    }
]

try:
    font = ImageFont.truetype("arial.ttf", 16)
    font_bold = ImageFont.truetype("arialbd.ttf", 18)
except Exception:
    font = ImageFont.load_default()
    font_bold = font

for item in annotations:
    src_path = os.path.join(orig_dir, item["file"])
    dst_path = os.path.join(annot_dir, item["file"])
    if not os.path.exists(src_path):
        print(f"Skipping {src_path}, not found")
        continue

    img = Image.open(src_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top banner
    draw.rectangle([(0, 0), (img.width, 42)], fill=(24, 24, 27, 230))
    draw.text((16, 10), item["title"], fill=(255, 255, 255, 255), font=font_bold)

    # Draw boxes
    for b in item["boxes"]:
        rect = b["rect"]
        color = b["color"]
        # Scale if image size is different from standard 1280x800
        w_scale = img.width / 1280.0
        h_scale = img.height / 800.0
        scaled_rect = [
            int(rect[0] * w_scale),
            int(rect[1] * h_scale),
            int(rect[2] * w_scale),
            int(rect[3] * h_scale)
        ]
        # Bounding box
        draw.rectangle(scaled_rect, outline=color + (255,), width=4)
        
        # Label pill
        label = b["label"]
        lx = scaled_rect[0]
        ly = max(scaled_rect[1] - 32, 45)
        text_bbox = draw.textbbox((lx + 10, ly + 6), label, font=font)
        pill_rect = [lx, ly, text_bbox[2] + 10, text_bbox[3] + 6]
        draw.rectangle(pill_rect, fill=color + (230,))
        draw.text((lx + 10, ly + 6), label, fill=(255, 255, 255, 255), font=font)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(dst_path, "PNG")
    print(f"Saved annotated screenshot: {dst_path}")
