"""Generate a beautiful, professional, Unicode-compliant PDF for a released student result."""

from __future__ import annotations

import io
import os
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Cache registered font names
_FONT_NORMAL = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONTS_REGISTERED = False


def _init_fonts() -> tuple[str, str]:
    """Register Unicode-compliant TrueType fonts (Windows Arial, Linux DejaVu/Liberation)."""
    global _FONT_NORMAL, _FONT_BOLD, _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return _FONT_NORMAL, _FONT_BOLD

    # Candidates for normal and bold fonts
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
    ]

    for norm_path, bold_path, norm_name, bold_name in candidates:
        if os.path.exists(norm_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(norm_name, norm_path))
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                _FONT_NORMAL = norm_name
                _FONT_BOLD = bold_name
                _FONTS_REGISTERED = True
                return _FONT_NORMAL, _FONT_BOLD
            except Exception:
                continue

    _FONTS_REGISTERED = True
    return _FONT_NORMAL, _FONT_BOLD


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def _format_datetime(val: Any) -> str:
    if not val:
        return "-"
    if isinstance(val, str):
        try:
            # Parse ISO string
            cleaned = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return val[:19].replace("T", " ")
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y %H:%M:%S")
    return str(val)


def build_attempt_result_pdf(result_data: dict[str, Any]) -> bytes:
    """Build a styled, vector PDF containing the student's authorized exam transcript."""
    font_norm, font_bold = _init_fonts()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="PWD301 LMS - Bang Diem Ket Qua Khao Thi",
        author="PWD301 LMS Examination Board",
    )

    # Custom typography styles
    style_header_org = ParagraphStyle(
        "HeaderOrg",
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        alignment=0,
    )
    style_doc_title = ParagraphStyle(
        "DocTitle",
        fontName=font_bold,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_doc_sub = ParagraphStyle(
        "DocSub",
        fontName=font_norm,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )
    style_info_label = ParagraphStyle(
        "InfoLabel",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    style_info_value = ParagraphStyle(
        "InfoValue",
        fontName=font_norm,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )
    style_th = ParagraphStyle(
        "TableHead",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )
    style_td = ParagraphStyle(
        "TableData",
        fontName=font_norm,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B"),
    )
    style_td_bold = ParagraphStyle(
        "TableDataBold",
        fontName=font_bold,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_td_correct = ParagraphStyle(
        "TableDataCorrect",
        fontName=font_bold,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#15803D"),
        alignment=1,
    )
    style_td_wrong = ParagraphStyle(
        "TableDataWrong",
        fontName=font_bold,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#B91C1C"),
        alignment=1,
    )

    story = []

    # 1. Top Organization & Document Header
    org_line = Paragraph("HỆ THỐNG QUẢN LÝ ĐÀO TẠO & KHẢO THÍ PWD301 LMS", style_header_org)
    story.append(org_line)
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2563EB"),
            spaceBefore=2,
            spaceAfter=8,
        )
    )

    title_text = Paragraph("BẢNG ĐIỂM KẾT QUẢ BÀI THI CHUẨN HÓA", style_doc_title)
    sub_text = Paragraph("OFFICIAL ACADEMIC EXAMINATION TRANSCRIPT", style_doc_sub)
    story.append(title_text)
    story.append(Spacer(1, 2))
    story.append(sub_text)
    story.append(Spacer(1, 10))

    # 2. Candidate & Exam Meta Table
    cand_name = str(result_data.get("candidate_name") or "Học viên").strip()
    cand_email = str(result_data.get("candidate_email") or "-").strip()
    asm_title = str(result_data.get("assessment_title") or "Bài kiểm tra").strip()
    asm_code = str(result_data.get("assessment_code") or "PWD301").strip()
    instructor_name = str(result_data.get("instructor_name") or "-").strip()
    submitted_at = _format_datetime(result_data.get("submitted_at"))
    started_at = _format_datetime(result_data.get("started_at"))
    duration = str(result_data.get("duration_minutes") or "45") + " phút"

    info_data = [
        [
            Paragraph("<b>Học viên:</b>", style_info_label),
            Paragraph(cand_name, style_info_value),
            Paragraph("<b>Bài kiểm tra:</b>", style_info_label),
            Paragraph(asm_title, style_info_value),
        ],
        [
            Paragraph("<b>Email:</b>", style_info_label),
            Paragraph(cand_email, style_info_value),
            Paragraph("<b>Học phần:</b>", style_info_label),
            Paragraph(asm_code, style_info_value),
        ],
        [
            Paragraph("<b>Thời gian bắt đầu:</b>", style_info_label),
            Paragraph(started_at, style_info_value),
            Paragraph("<b>Giảng viên:</b>", style_info_label),
            Paragraph(instructor_name, style_info_value),
        ],
        [
            Paragraph("<b>Thời gian nộp bài:</b>", style_info_label),
            Paragraph(submitted_at, style_info_value),
            Paragraph("<b>Thời lượng:</b>", style_info_label),
            Paragraph(duration, style_info_value),
        ],
    ]

    info_table = Table(info_data, colWidths=[1.1 * inch, 2.5 * inch, 1.2 * inch, 2.5 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 3. Overall Grade & Result Card
    raw_score = result_data.get("raw_score", result_data.get("total_score", 0))
    max_score = result_data.get("max_score", result_data.get("max_points", 0))
    percent_val = result_data.get("percent_score")
    if percent_val is not None:
        try:
            percent = float(percent_val)
        except (TypeError, ValueError):
            percent = 0.0
    else:
        try:
            raw_f = float(raw_score) if raw_score is not None else 0.0
            max_f = float(max_score) if max_score is not None else 0.0
            percent = (raw_f / max_f * 100) if max_f > 0 else 0.0
        except Exception:
            percent = 0.0

    is_passed = bool(result_data.get("is_passed", result_data.get("passed", percent >= 50.0)))
    badge_bg = colors.HexColor("#DCFCE7") if is_passed else colors.HexColor("#FEE2E2")
    badge_border = colors.HexColor("#86EFAC") if is_passed else colors.HexColor("#FCA5A5")
    badge_color = colors.HexColor("#15803D") if is_passed else colors.HexColor("#B91C1C")
    badge_label = "ĐẠT CHUẨN MÔN HỌC" if is_passed else "CHƯA ĐẠT YÊU CẦU"

    style_score_big = ParagraphStyle(
        "ScoreBig",
        fontName=font_bold,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_badge = ParagraphStyle(
        "ResultBadge",
        fontName=font_bold,
        fontSize=10.5,
        leading=14,
        textColor=badge_color,
        alignment=1,
    )

    score_card_data = [
        [
            Paragraph("<b>TỔNG ĐIỂM ĐẠT ĐƯỢC</b>", style_info_label),
            Paragraph("<b>TỶ LỆ HOÀN THÀNH</b>", style_info_label),
            Paragraph("<b>KẾT QUẢ ĐÁNH GIÁ</b>", style_info_label),
        ],
        [
            Paragraph(
                f"<b>{_format_score(raw_score)} / {_format_score(max_score)}</b>", style_score_big
            ),
            Paragraph(f"<b>{percent:.1f}%</b>", style_score_big),
            Paragraph(f"<b>{badge_label}</b>", style_badge),
        ],
    ]

    score_table = Table(score_card_data, colWidths=[2.4 * inch, 2.4 * inch, 2.5 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (0, 1), (1, 1), colors.HexColor("#FFFFFF")),
                ("BACKGROUND", (2, 1), (2, 1), badge_bg),
                ("BOX", (2, 1), (2, 1), 1, badge_border),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 12))

    # 4. Question Breakdown Section
    questions = result_data.get("questions") or []
    if questions:
        story.append(
            Paragraph(
                "<b>CHI TIẾT ĐÁNH GIÁ TỪNG CÂU HỎI (QUESTION BREAKDOWN)</b>", style_info_label
            )
        )
        story.append(Spacer(1, 4))

        breakdown_rows = [
            [
                Paragraph("<b>STT</b>", style_th),
                Paragraph("<b>Nội dung câu hỏi</b>", style_th),
                Paragraph("<b>Đáp án đã chọn</b>", style_th),
                Paragraph("<b>Kết quả</b>", style_th),
                Paragraph("<b>Điểm</b>", style_th),
            ]
        ]

        for idx, q in enumerate(questions, start=1):
            q_text = str(q.get("content") or f"Câu hỏi số {idx}").strip()
            # Trim long question text if needed
            if len(q_text) > 140:
                q_text = q_text[:137] + "..."

            # Extract selected answer text or keys
            selected = q.get("selected_choice_keys") or q.get("selected_choice_ids") or []
            selected_str = (
                ", ".join(str(s) for s in selected)
                if selected
                else str(q.get("student_answer_text") or "-")
            )
            if len(selected_str) > 40:
                selected_str = selected_str[:37] + "..."

            is_correct = bool(q.get("is_correct"))
            res_cell = (
                Paragraph("ĐÚNG", style_td_correct)
                if is_correct
                else Paragraph("SAI", style_td_wrong)
            )

            awarded = _format_score(q.get("awarded_points", 0))
            assigned = _format_score(q.get("points_assigned", 1))

            breakdown_rows.append(
                [
                    Paragraph(f"<b>#{idx}</b>", style_td_bold),
                    Paragraph(q_text, style_td),
                    Paragraph(selected_str, style_td),
                    res_cell,
                    Paragraph(f"{awarded} / {assigned}", style_td_bold),
                ]
            )

        breakdown_table = Table(
            breakdown_rows,
            colWidths=[0.5 * inch, 3.8 * inch, 1.4 * inch, 0.7 * inch, 0.9 * inch],
            repeatRows=1,
        )
        breakdown_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    *[
                        (
                            "BACKGROUND",
                            (0, r),
                            (-1, r),
                            colors.HexColor("#F8FAFC") if r % 2 == 0 else colors.white,
                        )
                        for r in range(1, len(breakdown_rows))
                    ],
                ]
            )
        )
        story.append(breakdown_table)
        story.append(Spacer(1, 10))

    # 5. Footer Notice
    now_str = datetime.now(UTC).strftime("%d/%m/%Y %H:%M:%S UTC")
    footer_text = Paragraph(
        f"<i>Bảng điểm điện tử được trích xuất tự động từ Cơ sở Dữ liệu Khảo thí PWD301 LMS vào lúc {now_str}. "
        "Mọi thắc mắc về điểm số vui lòng gửi yêu cầu phúc khảo qua cổng Học viên trước thời hạn quy định.</i>",
        style_doc_sub,
    )
    story.append(Spacer(1, 6))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#CBD5E1"),
            spaceBefore=2,
            spaceAfter=4,
        )
    )
    story.append(footer_text)

    doc.build(story)
    return buffer.getvalue()
