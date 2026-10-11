"""Generate a beautiful, professional, Unicode-compliant PDF for a released student result."""

from __future__ import annotations

import io
import math
import os
from datetime import UTC, datetime
from html import escape
from typing import Any
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

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

    raise RuntimeError("A Unicode TrueType font is required to export Vietnamese result PDFs.")


def _format_score(value: Any) -> str:
    try:
        val = float(value)
        if not math.isfinite(val):
            return "-"
        if val.is_integer():
            return f"{int(val)}"
        formatted = f"{val:.2f}".rstrip("0").rstrip(".")
        return formatted
    except (TypeError, ValueError):
        return "-"


def _plain(value: Any) -> str:
    """Treat snapshot/user strings as text, never ReportLab markup."""
    return escape(str(value)).replace("\n", "<br/>")


def _display_title(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        UUID(text)
    except ValueError:
        return text
    return fallback


def _draw_icon(canvas: Any, kind: str, x: float, y: float, size: float, color: Any) -> None:
    """Small vector marks avoid platform-dependent emoji and missing glyphs."""
    canvas.saveState()
    canvas.translate(x, y)
    canvas.scale(size / 24, size / 24)
    canvas.setFillColor(color)
    canvas.setStrokeColor(color)
    canvas.setLineWidth(1.6)
    if kind == "cap":
        path = canvas.beginPath()
        path.moveTo(1, 15)
        for px, py in [(12, 20), (23, 15), (12, 10)]:
            path.lineTo(px, py)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.rect(6, 5, 12, 5, fill=1, stroke=0)
        canvas.line(22, 14, 22, 5)
    elif kind == "person":
        canvas.circle(12, 17, 4, fill=1, stroke=0)
        path = canvas.beginPath()
        path.moveTo(4, 2)
        path.curveTo(3, 13, 21, 13, 20, 2)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
    elif kind == "bars":
        for bx, bh in [(4, 7), (10, 13), (16, 19)]:
            canvas.roundRect(bx, 2, 4, bh, 1, fill=1, stroke=0)
    elif kind == "check":
        canvas.circle(12, 12, 10, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#F8FAFC"))
        canvas.line(7, 12, 11, 8)
        canvas.line(11, 8, 17, 16)
    elif kind == "alert":
        path = canvas.beginPath()
        path.moveTo(12, 22)
        path.lineTo(1, 2)
        path.lineTo(23, 2)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#F8FAFC"))
        canvas.line(12, 15, 12, 9)
        canvas.setFillColor(colors.HexColor("#F8FAFC"))
        canvas.circle(12, 5, 1, fill=1, stroke=0)
    elif kind == "trophy":
        canvas.roundRect(7, 10, 10, 11, 3, fill=1, stroke=0)
        canvas.line(12, 10, 12, 3)
        canvas.rect(7, 1, 10, 2, fill=1, stroke=0)
        for x in (3, 17):
            canvas.roundRect(x, 13, 4, 6, 2, fill=0, stroke=1)
    elif kind == "pie":
        canvas.wedge(2, 2, 21, 21, 90, 270, fill=1, stroke=0)
        canvas.wedge(5, 5, 23, 23, 0, 90, fill=1, stroke=0)
    elif kind == "book":
        for direction in (-1, 1):
            path = canvas.beginPath()
            path.moveTo(12, 3)
            path.lineTo(12, 20)
            path.curveTo(12 + direction * 4, 23, 12 + direction * 9, 22, 12 + direction * 10, 20)
            path.lineTo(12 + direction * 10, 3)
            path.curveTo(12 + direction * 7, 5, 12 + direction * 3, 5, 12, 3)
            canvas.drawPath(path, fill=0, stroke=1)
    else:
        canvas.roundRect(5, 2, 14, 20, 2, fill=0, stroke=1)
        for ly in (7, 12, 17):
            canvas.line(8, ly, 16, ly)
    canvas.restoreState()


class _AcademicMark(Flowable):
    """Book and laurel crest, drawn as scalable PDF paths."""

    def __init__(self, width: float, height: float = 64):
        super().__init__()
        self.width, self.height = width, height

    def draw(self) -> None:
        c = self.canv
        cx, cy = self.width / 2, self.height / 2
        blue = colors.HexColor("#174783")
        _draw_icon(c, "book", cx - 19, cy - 18, 38, blue)
        c.saveState()
        c.setFillColor(blue)
        c.setStrokeColor(blue)
        c.setLineWidth(0.8)
        for side in (-1, 1):
            for angle in range(25, 155, 18):
                radians = math.radians(angle)
                lx = cx + side * 30 * math.sin(radians)
                ly = cy + 29 * math.cos(radians)
                c.saveState()
                c.translate(lx, ly)
                c.rotate(side * (angle - 45))
                c.ellipse(-2, -5, 2, 5, fill=1, stroke=0)
                c.restoreState()
            c.line(cx + side * 8, cy - 30, cx + side * 21, cy - 24)
        c.circle(cx, cy + 27, 2, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor("#9FC3E8"))
        c.line(80, cy, cx - 48, cy)
        c.line(cx + 48, cy, self.width - 80, cy)
        c.restoreState()


class _SectionBand(Flowable):
    def __init__(self, title: str, width: float, icon: str = "document", dark: bool = False):
        super().__init__()
        self.title, self.width, self.height = title, width, 32
        self.icon, self.dark = icon, dark
        self.keepWithNext = True

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        c.setFillColor(colors.HexColor("#EAF2FC"))
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        if self.dark:
            for i in range(100):
                c.setFillColor(colors.Color(0.08 + i * 0.0014, 0.23 + i * 0.0016, 0.46 + i * 0.002))
                c.rect(
                    i * self.width / 100, 0, self.width / 100 + 0.2, self.height, fill=1, stroke=0
                )
        ink = colors.HexColor("#F8FAFC" if self.dark else "#153A73")
        _draw_icon(c, self.icon, 12, 7, 19, ink)
        c.setFillColor(ink)
        # Fit headings to their band without clipping Vietnamese text.
        font_size = min(11, (self.width - 52) / pdfmetrics.stringWidth(self.title, _FONT_BOLD, 1))
        c.setFont(_FONT_BOLD, font_size)
        c.drawString(43, 11, self.title)
        c.restoreState()


def _metric_cards(rows: list[list[Any]], width: float, fills: list[str], icons: list[str]) -> Table:
    """Separate rounded metric cards, with predictable gutters and flexible text."""
    count = len(rows[0])
    gutter = 8
    card_width = (width - gutter * (count - 1)) / count
    label_height = max(cell.wrap(card_width - 16, 1000)[1] for cell in rows[0]) + 14
    value_height = max(cell.wrap(card_width - 16, 1000)[1] for cell in rows[1]) + 14
    cells: list[Any] = []
    widths: list[float] = []
    for index in range(count):
        card = Table(
            [
                [
                    _MetricIcon(
                        icons[index],
                        {
                            "#EAF8F9": "#167A85",
                            "#FFF7E7": "#B57817",
                            "#F2EDFC": "#743DB8",
                            "#ECF8F0": "#168148",
                            "#FFF0F1": "#CA263E",
                        }.get(fills[index], "#21518D"),
                    )
                ],
                [rows[0][index]],
                [rows[1][index]],
            ],
            colWidths=[card_width],
            cornerRadii=[6] * 4,
            rowHeights=[38 if count == 3 else 30, max(30, label_height), max(32, value_height)],
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fills[index])),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5E4F5")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        if cells:
            cells.append("")
            widths.append(gutter)
        cells.append(card)
        widths.append(card_width)
    table = Table([cells], colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


class _MetricIcon(Flowable):
    def __init__(self, kind: str, color: str = "#21518D"):
        super().__init__()
        self.kind, self.width, self.height = kind, 24, 24
        self.color = color

    def draw(self) -> None:
        _draw_icon(self.canv, self.kind, 0, 0, 24, colors.HexColor(self.color))


def _page_number(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setFillColor(colors.HexColor("#FDFEFE"))
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    for color, rise in [("#D9EAFB", 35), ("#77A9D6", 23), ("#174783", 14)]:
        canvas.setFillColor(colors.HexColor(color))
        path = canvas.beginPath()
        path.moveTo(0, 0)
        path.lineTo(0, rise)
        path.curveTo(w * 0.35, rise - 18, w * 0.65, rise - 18, w, rise)
        path.lineTo(w, 0)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
    canvas.setFont(_FONT_NORMAL, 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(w - doc.rightMargin, 39, f"Trang {doc.page}")
    canvas.drawString(doc.leftMargin, 39, "PWD301 LMS  /  KHẢO THÍ & ĐÀO TẠO")
    if doc.page > 1:
        canvas.setFont(_FONT_BOLD, 8)
        canvas.drawString(doc.leftMargin, h - 26, "PWD301 LMS  |  KẾT QUẢ KHẢO THÍ")
    canvas.restoreState()


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
        bottomMargin=60,
        title="PWD301 LMS - Bang Diem Ket Qua Khao Thi",
        author="PWD301 LMS Examination Board",
    )
    # Platypus frames inset content by six points on both sides.
    doc.width -= 12

    # Custom typography styles
    style_header_org = ParagraphStyle(
        "HeaderOrg",
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        alignment=1,
    )
    style_doc_title = ParagraphStyle(
        "DocTitle",
        fontName=font_bold,
        fontSize=20,
        leading=25,
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
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#475569"),
        alignment=0,
    )
    style_info_value = ParagraphStyle(
        "InfoValue",
        fontName=font_norm,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )
    style_th = ParagraphStyle(
        "TableHead",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#F8FAFC"),
        alignment=1,
    )
    style_td = ParagraphStyle(
        "TableData",
        fontName=font_norm,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
    )
    style_td_bold = ParagraphStyle(
        "TableDataBold",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_td_correct = ParagraphStyle(
        "TableDataCorrect",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#15803D"),
        alignment=1,
    )
    style_td_wrong = ParagraphStyle(
        "TableDataWrong",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#B91C1C"),
        alignment=1,
    )

    story = []

    # 1. Top Organization & Document Header
    org_line = Paragraph("HỆ THỐNG QUẢN LÝ ĐÀO TẠO & KHẢO THÍ PWD301 LMS", style_header_org)
    brand = Table([[_MetricIcon("cap"), org_line]], colWidths=[34, doc.width - 34])
    brand.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(brand)
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
    story.append(Spacer(1, 12))

    # 2. Candidate & Exam Meta Table
    cand_name = str(result_data.get("candidate_name") or "Học viên").strip()
    cand_email = str(result_data.get("candidate_email") or "-").strip()
    asm_title = _display_title(result_data.get("assessment_title"), "Bài kiểm tra")
    asm_code = _display_title(
        result_data.get("course_title") or result_data.get("assessment_code"), "Khóa học"
    )
    instructor_name = str(result_data.get("instructor_name") or "-").strip()
    submitted_at = _format_datetime(result_data.get("submitted_at"))
    started_at = _format_datetime(result_data.get("started_at"))
    duration = _format_score(result_data.get("duration_minutes")) + " phút"

    info_data = [
        [
            Paragraph("<b>Học viên:</b>", style_info_label),
            Paragraph(_plain(cand_name), style_info_value),
            Paragraph("<b>Bài kiểm tra:</b>", style_info_label),
            Paragraph(_plain(asm_title), style_info_value),
        ],
        [
            Paragraph("<b>Email:</b>", style_info_label),
            Paragraph(_plain(cand_email), style_info_value),
            Paragraph("<b>Học phần:</b>", style_info_label),
            Paragraph(_plain(asm_code), style_info_value),
        ],
        [
            Paragraph("<b>Thời gian bắt đầu:</b>", style_info_label),
            Paragraph(_plain(started_at), style_info_value),
            Paragraph("<b>Giảng viên:</b>", style_info_label),
            Paragraph(_plain(instructor_name), style_info_value),
        ],
        [
            Paragraph("<b>Thời gian nộp bài:</b>", style_info_label),
            Paragraph(_plain(submitted_at), style_info_value),
            Paragraph("<b>Thời lượng:</b>", style_info_label),
            Paragraph(duration, style_info_value),
        ],
        [
            Paragraph("<b>Tiêu chuẩn khảo thí:</b>", style_info_label),
            Paragraph("Có giám sát nâng cao", style_info_value),
            Paragraph("<b>Địa điểm kết xuất:</b>", style_info_label),
            Paragraph("Thành phố Hồ Chí Minh", style_info_value),
        ],
    ]

    story.append(_SectionBand("THÔNG TIN HỌC VIÊN & BÀI KIỂM TRA", doc.width, "person"))
    info_table = Table(
        info_data,
        colWidths=[doc.width * x for x in (0.20, 0.29, 0.19, 0.32)],
        cornerRadii=[0, 0, 6, 6],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
                ("LINEAFTER", (1, 0), (1, -1), 0.5, colors.HexColor("#D5E4F5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 12))

    # 3. Overall Grade & Result Card
    raw_score = result_data.get("raw_score", result_data.get("total_score"))
    max_score = result_data.get("max_score", result_data.get("max_points"))
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
    badge_fill = "#ECF8F0" if is_passed else "#FFF0F1"
    badge_color = colors.HexColor("#15803D") if is_passed else colors.HexColor("#B91C1C")
    badge_label = "ĐẠT CHUẨN MÔN HỌC" if is_passed else "CHƯA ĐẠT YÊU CẦU"
    if result_data.get("is_passed", result_data.get("passed")) is None:
        badge_label = "CHƯA CÓ KẾT LUẬN"
        badge_fill = "#F1F5F9"
        badge_color = colors.HexColor("#475569")

    percent_display = _format_score(percent)
    if percent_val is None and (_format_score(raw_score) == "-" or _format_score(max_score) == "-"):
        percent_display = "-"

    style_score_big = ParagraphStyle(
        "ScoreBig",
        fontName=font_bold,
        fontSize=25,
        leading=30,
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
            Paragraph(f"<b>{percent_display}%</b>", style_score_big),
            Paragraph(f"<b>{badge_label}</b>", style_badge),
        ],
    ]
    for label in score_card_data[0]:
        label.style = ParagraphStyle("MetricLabel", parent=style_info_label, alignment=1)

    story.append(_SectionBand("TỔNG QUAN KẾT QUẢ", doc.width, "bars"))
    score_table = _metric_cards(
        score_card_data,
        doc.width,
        ["#EAF3FE", "#EAF8F9", badge_fill],
        ["trophy", "pie", "check" if is_passed else "alert"],
    )
    story.append(score_table)
    story.append(Spacer(1, 18))

    # 4. Question Breakdown Section
    questions = result_data.get("questions") or []
    if questions:
        story.append(_SectionBand("CHI TIẾT ĐÁNH GIÁ TỪNG CÂU HỎI (QUESTION BREAKDOWN)", doc.width))
        story.append(Spacer(1, 6))

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

            # Extract selected answer text (decode from choices instead of raw UUID keys)
            choices = q.get("choices") or []
            raw_keys = q.get("selected_choice_keys") or q.get("selected_choice_ids") or []
            selected_keys = {str(k).strip() for k in raw_keys if k}

            selected_texts: list[str] = []
            for c in choices:
                c_key = str(c.get("choice_key") or c.get("choice_id") or "").strip()
                is_sel = bool(c.get("is_selected")) or (bool(c_key) and c_key in selected_keys)
                if is_sel:
                    content = str(c.get("content") or "").strip()
                    if content:
                        selected_texts.append(content)

            if selected_texts:
                selected_str = "; ".join(selected_texts)
            elif q.get("student_answer_text"):
                selected_str = str(q.get("student_answer_text")).strip()
            else:
                if selected_keys:
                    first_key = next(iter(selected_keys))
                    if len(first_key) == 36 and first_key.count("-") == 4:
                        selected_str = "(Đã chọn đáp án)"
                    else:
                        selected_str = ", ".join(sorted(selected_keys))
                else:
                    selected_str = "(Chưa trả lời)"

            is_correct = bool(q.get("is_correct"))
            res_cell = (
                Paragraph("ĐÚNG", style_td_correct)
                if is_correct
                else Paragraph("SAI", style_td_wrong)
            )
            if q.get("is_correct") is None:
                res_cell = Paragraph("-", style_td_bold)

            awarded = _format_score(q.get("awarded_points"))
            assigned = _format_score(q.get("points_assigned"))

            breakdown_rows.append(
                [
                    Paragraph(f"<b>#{idx}</b>", style_td_bold),
                    Paragraph(_plain(q_text), style_td),
                    Paragraph(_plain(selected_str), style_td),
                    res_cell,
                    Paragraph(f"{awarded} / {assigned}", style_td_bold),
                ]
            )

        breakdown_table = Table(
            breakdown_rows,
            colWidths=[doc.width * x for x in (0.07, 0.40, 0.23, 0.12, 0.18)],
            repeatRows=1,
            splitInRow=1,
        )
        breakdown_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    *[
                        (
                            "BACKGROUND",
                            (0, r),
                            (-1, r),
                            colors.HexColor("#F8FAFC")
                            if r % 2 == 0
                            else colors.HexColor("#F8FAFC"),
                        )
                        for r in range(1, len(breakdown_rows))
                    ],
                ]
            )
        )
        story.append(breakdown_table)
        story.append(Spacer(1, 12))

    # 5. Footer Notice
    now_str = datetime.now(UTC).strftime("%d/%m/%Y %H:%M:%S UTC")
    footer_text = Paragraph(
        f"<i>Bảng điểm điện tử được trích xuất tự động từ Cơ sở Dữ liệu Khảo thí PWD301 LMS vào lúc {now_str}. "
        "Mọi thắc mắc về điểm số vui lòng gửi yêu cầu phúc khảo qua cổng Học viên trước thời hạn quy định.</i>",
        style_doc_sub,
    )
    notice = Table([[footer_text]], colWidths=[doc.width], cornerRadii=[6] * 4)
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F6FC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7DDF4")),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ]
        )
    )
    story.append(notice)

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()


def build_assessment_gradebook_pdf(gradebook_data: dict[str, Any]) -> bytes:
    """Generate a formal, academic class gradebook and assessment audit PDF.

    Features:
    - Official academic header (Ministry / Academy).
    - Course and examination metadata table.
    - Executive statistics summary (Total, submitted, average, min/max, pass rate).
    - Full candidate roster table with violation counts and pass/fail indicators.
    - Official examination committee signature block.
    """
    font_norm, font_bold = _init_fonts()
    buffer = io.BytesIO()

    # Page setup: A4 with 28pt (approx 0.39 inch) margins for maximum printable area
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=30,
        bottomMargin=60,
    )
    doc.width -= 12

    # Styles
    style_header_org = ParagraphStyle(
        "GbHeaderOrg",
        fontName=font_bold,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
    )
    style_doc_title = ParagraphStyle(
        "GbDocTitle",
        fontName=font_bold,
        fontSize=14,
        leading=19,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_doc_sub = ParagraphStyle(
        "GbDocSub",
        fontName=font_norm,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )
    style_info_label = ParagraphStyle(
        "GbInfoLabel",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )
    style_info_value = ParagraphStyle(
        "GbInfoValue",
        fontName=font_norm,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )
    style_th = ParagraphStyle(
        "GbTableHead",
        fontName=font_bold,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#153A73"),
        alignment=1,
    )
    style_td = ParagraphStyle(
        "GbTableData",
        fontName=font_norm,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )
    style_td_center = ParagraphStyle(
        "GbTableDataCenter",
        fontName=font_norm,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        alignment=1,
    )
    style_td_bold_center = ParagraphStyle(
        "GbTableDataBoldCenter",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    style_td_pass = ParagraphStyle(
        "GbTableDataPass",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#15803D"),
        alignment=1,
    )
    style_td_fail = ParagraphStyle(
        "GbTableDataFail",
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#B91C1C"),
        alignment=1,
    )
    style_sig_title = ParagraphStyle(
        "GbSigTitle",
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        alignment=1,
    )
    style_sig_sub = ParagraphStyle(
        "GbSigSub",
        fontName=font_norm,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )

    story = [_AcademicMark(doc.width, 48), Spacer(1, 6)]

    # 1. Organization Header
    org_title = Paragraph(
        "BỘ GIÁO DỤC VÀ ĐÀO TẠO &bull; HỆ THỐNG ĐÀO TẠO TRỰC TUYẾN PWD301 LMS",
        style_header_org,
    )
    story.append(org_title)
    story.append(Spacer(1, 3))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2563EB"),
            spaceBefore=2,
            spaceAfter=6,
        )
    )

    # 2. Document Title
    story.append(
        Paragraph("BẢNG ĐIỂM TỔNG HỢP &amp; KẾT QUẢ KHẢO THÍ TRẮC NGHIỆM", style_doc_title)
    )
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "OFFICIAL CLASS ASSESSMENT GRADEBOOK &amp; PROCTORING AUDIT REPORT",
            style_doc_sub,
        )
    )
    story.append(Spacer(1, 10))

    # 3. Assessment & Course Meta
    raw_asm_title = _display_title(
        gradebook_data.get("assessment_title") or gradebook_data.get("title"),
        "Khảo thí trắc nghiệm",
    )
    asm_type_raw = str(gradebook_data.get("assessment_type") or "").strip().upper()
    type_map = {
        "QUIZ": "Bài trắc nghiệm",
        "MIDTERM": "Kiểm tra Giữa kỳ",
        "FINAL": "Thi Cuối kỳ",
        "PRACTICE": "Bài luyện tập",
        "ASSIGNMENT": "Bài tập lớn",
    }
    type_label = type_map.get(asm_type_raw, "")
    if (
        type_label
        and not raw_asm_title.lower().startswith(type_label.lower())
        and ":" not in raw_asm_title
    ):
        asm_display = f"{type_label}: {raw_asm_title}"
    else:
        asm_display = raw_asm_title

    course_title = _display_title(gradebook_data.get("course_title"), "Khóa học")
    instructor_name = str(gradebook_data.get("instructor_name") or "-").strip()
    duration_min = _format_score(gradebook_data.get("duration_minutes")) + " phút"
    now_str = datetime.now(UTC).strftime("%d/%m/%Y %H:%M:%S UTC")

    meta_rows = [
        [
            Paragraph("<b>Khóa học:</b>", style_info_label),
            Paragraph(_plain(course_title), style_info_value),
            Paragraph("<b>Bài kiểm tra:</b>", style_info_label),
            Paragraph(_plain(asm_display), style_info_value),
        ],
        [
            Paragraph("<b>Giảng viên phụ trách:</b>", style_info_label),
            Paragraph(_plain(instructor_name), style_info_value),
            Paragraph("<b>Thời lượng làm bài:</b>", style_info_label),
            Paragraph(duration_min, style_info_value),
        ],
        [
            Paragraph("<b>Thời điểm kết xuất:</b>", style_info_label),
            Paragraph(now_str, style_info_value),
            Paragraph("<b>Tiêu chuẩn khảo thí:</b>", style_info_label),
            Paragraph("Có giám sát nâng cao", style_info_value),
        ],
    ]
    panel_width = (doc.width - 10) / 2
    meta_row_heights = [
        max(
            cell.wrap(panel_width * (0.36 if index % 2 == 0 else 0.64) - 18, 1000)[1]
            for index, cell in enumerate(row)
        )
        + 14
        for row in meta_rows
    ]
    panels = []
    for offset, heading, icon in [
        (0, "THÔNG TIN KHÓA HỌC", "book"),
        (2, "THÔNG TIN BÀI KIỂM TRA", "document"),
    ]:
        body = Table(
            [row[offset : offset + 2] for row in meta_rows],
            colWidths=[panel_width * 0.36, panel_width * 0.64],
            rowHeights=meta_row_heights,
            cornerRadii=[0, 0, 6, 6],
        )
        body.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F6FC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5E4F5")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ]
            )
        )
        panels.append([_SectionBand(heading, panel_width, icon, dark=True), body])
    meta_table = Table([[panels[0], "", panels[1]]], colWidths=[panel_width, 10, panel_width])
    meta_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 4. Executive Statistics Summary
    total_candidates = int(gradebook_data.get("total_candidates") or 0)
    submitted_count = int(gradebook_data.get("submitted_count") or 0)
    passed_count = int(gradebook_data.get("passed_count") or 0)
    pass_rate_value = gradebook_data.get("pass_rate_pct")
    pass_rate = (
        float(pass_rate_value)
        if pass_rate_value is not None
        else (round((passed_count / submitted_count) * 100, 1) if submitted_count > 0 else 0.0)
    )
    avg_score = gradebook_data.get("average_score")
    avg_score_str = _format_score(avg_score) if avg_score is not None else "—"
    highest_score = gradebook_data.get("highest_score")
    lowest_score = gradebook_data.get("lowest_score")
    high_low_str = (
        f"{_format_score(highest_score)} / {_format_score(lowest_score)}"
        if highest_score is not None and lowest_score is not None
        else "—"
    )

    stat_style_title = ParagraphStyle(
        "StatTitle",
        fontName=font_bold,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )
    stat_style_val = ParagraphStyle(
        "StatVal",
        fontName=font_bold,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    stat_style_pass = ParagraphStyle(
        "StatPass",
        fontName=font_bold,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#15803D"),
        alignment=1,
    )

    stats_cells = [
        [
            Paragraph("TỔNG THÍ SINH", stat_style_title),
            Paragraph("ĐÃ NỘP BÀI", stat_style_title),
            Paragraph("ĐIỂM TRUNG BÌNH", stat_style_title),
            Paragraph("CAO NHẤT / THẤP NHẤT", stat_style_title),
            Paragraph("TỶ LỆ ĐẠT (PASS)", stat_style_title),
        ],
        [
            Paragraph(str(total_candidates), stat_style_val),
            Paragraph(f"{submitted_count} bài", stat_style_val),
            Paragraph(f"{avg_score_str} / 100", stat_style_val),
            Paragraph(high_low_str, stat_style_val),
            Paragraph(
                f"{_format_score(pass_rate)}% ({passed_count}/{submitted_count})", stat_style_pass
            ),
        ],
    ]
    story.append(_SectionBand("TỔNG HỢP KẾT QUẢ KHẢO THÍ", doc.width, "bars", dark=True))
    stats_table = _metric_cards(
        stats_cells,
        doc.width,
        ["#EAF3FE", "#EAF3FE", "#FFF7E7", "#F2EDFC", "#ECF8F0"],
        ["person", "document", "bars", "trophy", "check"],
    )
    story.append(stats_table)
    story.append(Spacer(1, 10))
    story.append(
        _SectionBand("DANH SÁCH CHI TIẾT KẾT QUẢ BÀI THI CỦA THÍ SINH", doc.width, dark=True)
    )
    story.append(Spacer(1, 8))

    attempts_data = gradebook_data.get("attempts") or []
    roster_rows = [
        [
            Paragraph("<b>STT</b>", style_th),
            Paragraph("<b>Mã SV</b>", style_th),
            Paragraph("<b>Họ và tên thí sinh</b>", style_th),
            Paragraph("<b>Thời gian nộp</b>", style_th),
            Paragraph("<b>Vi phạm</b>", style_th),
            Paragraph("<b>Điểm số</b>", style_th),
            Paragraph("<b>Kết quả</b>", style_th),
        ]
    ]

    for idx, att in enumerate(attempts_data, start=1):
        raw_code = str(att.get("student_code") or att.get("student_id") or "-").strip()
        if len(raw_code) == 36 and raw_code.count("-") == 4:
            s_code = f"SV-{raw_code[:8].upper()}"
        else:
            s_code = raw_code

        s_name = str(att.get("student_name") or att.get("student_email") or "Thí sinh").strip()
        sub_time = _format_datetime(att.get("submitted_at") or att.get("created_at"))
        violation_count = int(att.get("violation_count") or 0)
        v_str = f"<b>{violation_count}</b>" if violation_count > 0 else "0"
        score_val = att.get("percentage")
        if score_val is None:
            score_val = att.get("percent_score")
        if score_val is None:
            score_val = att.get("score")
        score_str = _format_score(score_val)

        is_passed = bool(att.get("is_passed") or att.get("passed"))
        if is_passed:
            status_cell = Paragraph("ĐẠT", style_td_pass)
        else:
            status_cell = Paragraph("HỎNG", style_td_fail)
        if att.get("score_status") not in (None, "RELEASED"):
            score_str = "-"
            status_cell = Paragraph("CHƯA CÔNG BỐ", style_td_center)
        elif att.get("is_passed", att.get("passed")) is None:
            status_cell = Paragraph("-", style_td_center)

        roster_rows.append(
            [
                Paragraph(f"#{idx}", style_td_center),
                Paragraph(_plain(s_code), style_td_bold_center),
                Paragraph(_plain(s_name), style_td),
                Paragraph(_plain(sub_time), style_td_center),
                Paragraph(v_str, style_td_center),
                Paragraph(f"<b>{score_str}</b>", style_td_bold_center),
                status_cell,
            ]
        )

    if len(roster_rows) == 1:
        # Empty placeholder row
        roster_rows.append(
            [
                Paragraph("-", style_td_center),
                Paragraph("-", style_td_center),
                Paragraph("<i>Chưa có thí sinh nộp bài</i>", style_td),
                Paragraph("-", style_td_center),
                Paragraph("0", style_td_center),
                Paragraph("—", style_td_center),
                Paragraph("—", style_td_center),
            ]
        )

    roster_table = Table(
        roster_rows,
        colWidths=[doc.width * x for x in (0.06, 0.14, 0.27, 0.18, 0.09, 0.11, 0.15)],
        repeatRows=1,
        splitInRow=1,
    )
    roster_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2F0FF")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                *[
                    (
                        "BACKGROUND",
                        (0, r),
                        (-1, r),
                        colors.HexColor("#F8FAFC") if r % 2 == 0 else colors.HexColor("#F8FAFC"),
                    )
                    for r in range(1, len(roster_rows))
                ],
            ]
        )
    )
    story.append(roster_table)
    story.append(Spacer(1, 10))

    # 6. Official Signatures Block
    sig_date_str = datetime.now(UTC).strftime("Thành phố Hồ Chí Minh, ngày %d tháng %m năm %Y")
    sig_rows = [
        [
            Paragraph("<b>CÁN BỘ CHẤM THI / GIẢNG VIÊN</b>", style_sig_title),
            Paragraph(
                f"<i>{sig_date_str}</i><br/><b>TRƯỞNG BAN KHẢO THÍ &amp; ĐÀO TẠO</b>",
                style_sig_title,
            ),
        ],
        [
            Paragraph("<i>(Ký và ghi rõ họ tên)</i>", style_sig_sub),
            Paragraph("<i>(Ký, đóng dấu xác nhận)</i>", style_sig_sub),
        ],
        [
            Spacer(1, 28),
            Spacer(1, 28),
        ],
        [
            Paragraph(f"<b>{_plain(instructor_name)}</b>", style_sig_title),
            Paragraph("<b>BAN KHẢO THÍ HỆ THỐNG PWD301</b>", style_sig_title),
        ],
    ]
    sig_table = Table(sig_rows, colWidths=[doc.width / 2] * 2)
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FC")),
                ("LINEABOVE", (0, 3), (-1, 3), 0.5, colors.HexColor("#9CB5D5")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    story.append(KeepTogether([sig_table]))
    story.append(Spacer(1, 6))

    # 7. Security & Verification Footer
    footer_text = Paragraph(
        f"<i>Bảng điểm học vụ điện tử được sinh tự động bởi Hệ thống PWD301 LMS lúc {now_str}. "
        "Dữ liệu có tính pháp lý nội bộ dùng cho công tác quản trị học vụ và lưu trữ khảo thí.</i>",
        style_doc_sub,
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#CBD5E1"),
            spaceBefore=2,
            spaceAfter=4,
        )
    )
    notice = Table([[footer_text]], colWidths=[doc.width], cornerRadii=[6] * 4)
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F6FC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7DDF4")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ]
        )
    )
    story.append(notice)

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()
