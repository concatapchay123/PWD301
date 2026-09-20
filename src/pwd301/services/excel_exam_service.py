"""Excel Exam Import & Template Service for PWD301.

Provides standardized Excel (.xlsx) template generation and robust parsing
with flexible header recognition and strict data validation for exam questions.
"""

from __future__ import annotations

import io
import re
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def generate_excel_exam_template() -> bytes:
    """Generate a beautifully formatted standardized Excel (.xlsx) exam question template.

    Returns the Excel file content as bytes.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Đề thi - Câu hỏi"

    # Header styling
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side,
    )

    headers = [
        "STT",
        "Loại câu hỏi",
        "Nội dung câu hỏi",
        "Phương án A",
        "Phương án B",
        "Phương án C",
        "Phương án D",
        "Đáp án đúng",
        "Điểm số",
        "Mức độ Bloom",
        "Giải thích / Lời giải",
    ]

    ws.row_dimensions[1].height = 32
    for col_idx, header_text in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header_text)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = border

    # Sample rows demonstrating different question types
    sample_rows = [
        [
            1,
            "Trắc nghiệm 1 đáp án",
            "Đâu là giao thức mạng truyền tải siêu văn bản có mã hóa bảo mật SSL/TLS?",
            "HTTP",
            "HTTPS",
            "FTP",
            "Telnet",
            "B",
            1.0,
            "Nhận biết",
            "HTTPS (HyperText Transfer Protocol Secure) sử dụng chứng chỉ SSL/TLS để mã hóa dữ liệu.",
        ],
        [
            2,
            "TN nhiều đáp án",
            "Các phương thức HTTP nào sau đây được coi là Idempotent (thao tác lặp lại cho cùng kết quả)?",
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "A, C, D",
            1.5,
            "Thông hiểu",
            "Theo RFC 7231, các phương thức GET, PUT, DELETE, HEAD, OPTIONS có tính chất Idempotent.",
        ],
        [
            3,
            "Đúng / Sai",
            "Trong cơ sở dữ liệu quan hệ, Khóa ngoại (Foreign Key) bắt buộc phải luôn luôn có giá trị khác NULL.",
            "Đúng",
            "Sai",
            "",
            "",
            "Sai",
            1.0,
            "Thông hiểu",
            "Khóa ngoại hoàn toàn có thể nhận giá trị NULL nếu cột đó không được định nghĩa ràng buộc NOT NULL.",
        ],
        [
            4,
            "Điền từ",
            "Cơ chế xác thực không trạng thái (Stateless) phổ biến trong RESTful API là sử dụng mã thông báo định dạng ___ (viết tắt 3 chữ cái).",
            "",
            "",
            "",
            "",
            "JWT",
            1.5,
            "Vận dụng",
            "JSON Web Token (JWT) được dùng để truyền tải thông tin xác thực an toàn giữa các bên dưới dạng đối tượng JSON.",
        ],
    ]

    data_font = Font(name="Arial", size=10)
    for row_idx, row_data in enumerate(sample_rows, start=2):
        ws.row_dimensions[row_idx].height = 28
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.border = border
            if col_idx in (1, 8, 9, 10):
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # Auto-adjust column widths with generous padding
    col_widths = {
        1: 8,    # STT
        2: 24,   # Loại câu
        3: 45,   # Nội dung
        4: 20,   # A
        5: 20,   # B
        6: 20,   # C
        7: 20,   # D
        8: 15,   # Đáp án đúng
        9: 10,   # Điểm
        10: 16,  # Bloom
        11: 35,  # Giải thích
    }
    for col_idx, width in col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

    # Add Guide Sheet
    guide_ws = wb.create_sheet(title="Hướng dẫn định dạng")
    guide_ws.views.sheetView[0].showGridLines = True
    guide_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    guide_title = guide_ws.cell(row=1, column=1, value="HƯỚNG DẪN ĐỊNH DẠNG TỆP CÂU HỎI EXCEL CHO GIẢNG VIÊN")
    guide_title.font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
    guide_title.fill = guide_fill
    guide_ws.merge_cells("A1:C1")
    guide_ws.row_dimensions[1].height = 30

    guide_lines = [
        ("Cột", "Quy định bắt buộc", "Ví dụ / Gợi ý"),
        ("STT", "Số thứ tự câu hỏi tăng dần (1, 2, 3...)", "1, 2, 3"),
        ("Loại câu hỏi", "Hỗ trợ: 'Trắc nghiệm 1 đáp án', 'TN nhiều đáp án', 'Đúng / Sai', 'Điền từ'", "Trắc nghiệm 1 đáp án"),
        ("Nội dung câu hỏi", "Nội dung câu hỏi, có thể chèn công thức $...$ hoặc khoảng trống ___", "Đâu là giao thức...?"),
        ("Phương án A, B, C, D", "Các đáp án lựa chọn cho câu trắc nghiệm. Bỏ trống nếu là câu Điền từ", "HTTPS, HTTP, ..."),
        ("Đáp án đúng", "Chữ cái đáp án đúng (A, B, C, D) hoặc danh sách đáp án nhiều lựa chọn ('A, B' hoặc 'A;C') hoặc 'Đúng'/'Sai' hoặc từ khóa điền.", "B hoặc A, C hoặc JWT"),
        ("Điểm số", "Điểm phân bổ cho câu hỏi (số dương, ví dụ: 1.0, 1.5, 2.0)", "1.0"),
        ("Mức độ Bloom", "Các mức độ: 'Nhận biết', 'Thông hiểu', 'Vận dụng'", "Thông hiểu"),
        ("Giải thích / Lời giải", "Lời giải thích củng cố kiến thức cho sinh viên sau khi nộp bài", "Giải thích chi tiết..."),
    ]

    for r_idx, (c1, c2, c3) in enumerate(guide_lines, start=3):
        guide_ws.row_dimensions[r_idx].height = 24
        is_hd = (r_idx == 3)
        for c_idx, val in enumerate([c1, c2, c3], start=1):
            c = guide_ws.cell(row=r_idx, column=c_idx, value=val)
            c.border = border
            if is_hd:
                c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
                c.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
            else:
                c.font = Font(name="Arial", size=10)
    guide_ws.column_dimensions["A"].width = 25
    guide_ws.column_dimensions["B"].width = 50
    guide_ws.column_dimensions["C"].width = 35

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def _normalize_header(header: str) -> str:
    """Normalize header string for fuzzy matching."""
    if not header:
        return ""
    h = str(header).strip().lower()
    h = re.sub(r"\s+", " ", h)
    return h


def parse_excel_exam(file_stream: io.BytesIO | bytes) -> dict[str, Any]:
    """Parse an uploaded Excel workbook into validated exam questions.

    Supports both standardized 8-11 column format and flexible fuzzy header matching.
    Returns:
    {
        "success": bool,
        "questions": list[dict],
        "total_questions": int,
        "total_points": float,
        "warnings": list[str],
        "errors": list[str]
    }
    """
    if isinstance(file_stream, bytes):
        stream = io.BytesIO(file_stream)
    else:
        stream = file_stream

    try:
        wb = openpyxl.load_workbook(stream, data_only=True)
    except Exception as err:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": [f"Không thể đọc tệp Excel. Vui lòng đảm bảo tệp định dạng .xlsx hợp lệ: {err}"],
        }

    ws = wb.active
    if ws is None:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": ["Bảng tính Excel không có trang dữ liệu hợp lệ."],
        }

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": ["Tệp Excel trống."],
        }

    # Find header row
    header_row_idx = -1
    col_mapping: dict[str, int] = {}
    choice_cols: list[tuple[str, int]] = []  # [(label, col_idx), ...]

    for r_idx, row in enumerate(rows[:10]):
        row_strs = [str(c).strip().lower() for c in row if c is not None]
        if any("nội dung" in c or "câu hỏi" in c or "stem" in c or "question" in c for c in row_strs):
            header_row_idx = r_idx
            break

    if header_row_idx == -1:
        header_row_idx = 0

    header_row = rows[header_row_idx]
    for col_idx, cell_val in enumerate(header_row):
        if cell_val is None:
            continue
        h = _normalize_header(str(cell_val))

        is_known_col = False
        if any(kw in h for kw in ("stt", "thứ tự", "order", "no")):
            col_mapping.setdefault("stt", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("loại câu", "dạng câu", "question type", "type")):
            col_mapping.setdefault("type", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("nội dung", "câu hỏi", "stem", "question", "content", "đề bài")):
            col_mapping.setdefault("content", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("đáp án đúng", "key", "correct", "đáp án chính xác", "đ/a")):
            col_mapping.setdefault("correct_answer", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("điểm", "points", "score", "thang điểm")):
            col_mapping.setdefault("points", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("mức độ", "bloom", "độ khó", "difficulty")):
            col_mapping.setdefault("bloom", col_idx)
            is_known_col = True
        elif any(kw in h for kw in ("giải thích", "lời giải", "explanation", "hướng dẫn giải")):
            col_mapping.setdefault("explanation", col_idx)
            is_known_col = True

        if not is_known_col:
            # Detect choice options: Phương án A, Đáp án A, Option A, hoặc cột mang tên A, B, C, D...
            opt_match = re.search(r"^(?:phương án|đáp án|lựa chọn|option|choice)\s*([a-f])(?:\b|$|\.|\:)|^([a-f])(?:\b|$|\.|\:)", h)
            if opt_match:
                opt_label = (opt_match.group(1) or opt_match.group(2)).upper()
                choice_cols.append((opt_label, col_idx))

    choice_cols.sort(key=lambda x: x[1])

    if "content" not in col_mapping:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": ["Không tìm thấy cột 'Nội dung câu hỏi' trong tệp Excel."],
        }

    parsed_questions: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    total_points = 0.0

    data_rows = rows[header_row_idx + 1:]
    question_counter = 1

    for row_idx, row in enumerate(data_rows, start=header_row_idx + 2):
        if not row:
            continue
        if all(c is None or str(c).strip() == "" for c in row):
            continue

        raw_content = row[col_mapping["content"]] if col_mapping.get("content") is not None and col_mapping["content"] < len(row) else None
        if not raw_content or str(raw_content).strip() == "":
            continue

        content = str(raw_content).strip()

        # Question Type
        raw_type = row[col_mapping["type"]] if col_mapping.get("type") is not None and col_mapping["type"] < len(row) else ""
        type_str = str(raw_type or "").strip().lower()
        q_type = "SINGLE_CHOICE"
        if any(kw in type_str for kw in ("nhiều", "multiple", "đa đáp án")):
            q_type = "MULTIPLE_CHOICE"
        elif any(kw in type_str for kw in ("đúng/sai", "đúng / sai", "true/false", "true_false", "đúng sai")):
            q_type = "TRUE_FALSE"
        elif any(kw in type_str for kw in ("điền", "fill", "short", "trả lời ngắn")):
            q_type = "SHORT_ANSWER"

        # Correct Answer
        raw_correct = row[col_mapping["correct_answer"]] if col_mapping.get("correct_answer") is not None and col_mapping["correct_answer"] < len(row) else ""
        correct_str = str(raw_correct or "").strip()

        # Points
        raw_pts = row[col_mapping["points"]] if col_mapping.get("points") is not None and col_mapping["points"] < len(row) else 1.0
        try:
            pts = float(raw_pts) if raw_pts is not None and str(raw_pts).strip() != "" else 1.0
            if pts <= 0:
                pts = 1.0
        except (ValueError, TypeError):
            pts = 1.0
            warnings.append(f"Dòng {row_idx}: Điểm không hợp lệ, đặt mặc định 1.0đ")

        # Bloom
        raw_bloom = row[col_mapping["bloom"]] if col_mapping.get("bloom") is not None and col_mapping["bloom"] < len(row) else ""
        bloom_str = str(raw_bloom or "").strip()
        bloom_level = "Thông hiểu"
        if any(kw in bloom_str.lower() for kw in ("nhận biết", "remember", "dễ")):
            bloom_level = "Nhận biết"
        elif any(kw in bloom_str.lower() for kw in ("vận dụng", "apply", "khó", "cao")):
            bloom_level = "Vận dụng"

        # Explanation
        raw_exp = row[col_mapping["explanation"]] if col_mapping.get("explanation") is not None and col_mapping["explanation"] < len(row) else ""
        explanation = str(raw_exp or "").strip()

        # Process choices
        choices: list[dict[str, Any]] = []
        if q_type == "TRUE_FALSE":
            is_true_correct = "đúng" in correct_str.lower() or correct_str.upper() in ("A", "TRUE", "T", "1")
            choices = [
                {"label": "A", "content": "Đúng", "is_correct": is_true_correct, "position": 1},
                {"label": "B", "content": "Sai", "is_correct": not is_true_correct, "position": 2},
            ]
        elif q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE"):
            correct_keys = [k.strip().upper() for k in re.split(r"[,;/|\s]+", correct_str) if k.strip()]
            for label, c_col in choice_cols:
                if c_col < len(row) and row[c_col] is not None:
                    c_val = str(row[c_col]).strip()
                    if c_val:
                        is_corr = label in correct_keys or (len(correct_keys) == 1 and correct_keys[0] == c_val.upper())
                        choices.append({
                            "label": label,
                            "content": c_val,
                            "is_correct": is_corr,
                            "position": len(choices) + 1,
                        })

            corr_count = sum(1 for c in choices if c["is_correct"])
            if corr_count > 1:
                q_type = "MULTIPLE_CHOICE"
            elif corr_count == 0 and choices:
                choices[0]["is_correct"] = True
                warnings.append(f"Dòng {row_idx} (Câu {question_counter}): Chưa đánh dấu đáp án đúng, hệ thống tạm gán phương án {choices[0]['label']}.")

        elif q_type == "SHORT_ANSWER":
            accepted_answers = [a.strip() for a in re.split(r"[,;/|]+", correct_str) if a.strip()]
            if not accepted_answers:
                accepted_answers = ["Đáp án"]

        q_obj: dict[str, Any] = {
            "id": question_counter,
            "number": question_counter,
            "row_index": row_idx,
            "stem": content,
            "question_text": content,
            "question_type": (
                "TN nhiều đáp án" if q_type == "MULTIPLE_CHOICE"
                else "Đúng / Sai" if q_type == "TRUE_FALSE"
                else "Điền từ" if q_type == "SHORT_ANSWER"
                else "Trắc nghiệm 1 đáp án"
            ),
            "type": q_type,
            "points": pts,
            "bloom_level": bloom_level,
            "explanation": explanation,
            "choices": choices,
        }

        if q_type == "SHORT_ANSWER":
            q_obj["accepted_answers"] = accepted_answers
            q_obj["options"] = [{"content": a, "is_correct": True} for a in accepted_answers]

        total_points += pts
        parsed_questions.append(q_obj)
        question_counter += 1

    if not parsed_questions:
        errors.append("Không bóc tách được câu hỏi nào từ tệp Excel. Vui lòng kiểm tra lại cấu trúc bảng tính.")

    return {
        "success": len(errors) == 0 and len(parsed_questions) > 0,
        "questions": parsed_questions,
        "total_questions": len(parsed_questions),
        "total_points": round(total_points, 2),
        "warnings": warnings,
        "errors": errors,
    }
