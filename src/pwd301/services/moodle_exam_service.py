"""Moodle XML & JSON Exam Import Service for PWD301.

Provides secure Moodle XML (using defusedxml) and JSON exam question parsing,
converting LMS format into PWD301 standardized question schema.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

import defusedxml.ElementTree as ET


def _clean_html_text(raw_html: str | None) -> str:
    """Strip HTML tags and unescape entities to return clean text."""
    if not raw_html:
        return ""
    text = html.unescape(str(raw_html))
    # Replace line breaks and paragraph tags with newlines
    text = re.sub(r"<(?:br|p|div)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespaces while preserving intentional newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    clean_lines = [l for l in lines if l]
    return "\n".join(clean_lines).strip()


def generate_moodle_sample_xml() -> str:
    """Generate a clean, standardized Moodle XML sample string containing various question types."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <!-- Question 1: Single Choice -->
  <question type="multichoice">
    <name>
      <text>Câu 1: Giao thức bảo mật HTTPS</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Đâu là giao thức mạng truyền tải siêu văn bản an toàn sử dụng chứng chỉ SSL/TLS?</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p>HTTPS bảo mật kết nối giữa trình duyệt và máy chủ qua mã hóa đối xứng và bất đối xứng.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1.0000000</defaultgrade>
    <single>true</single>
    <shuffleanswers>true</shuffleanswers>
    <answernumbering>abc</answernumbering>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>HTTP</p>]]></text>
      <feedback format="html"><text><![CDATA[<p>Chưa chính xác: HTTP truyền dữ liệu dạng văn bản rõ.</p>]]></text></feedback>
    </answer>
    <answer fraction="100" format="html">
      <text><![CDATA[<p>HTTPS</p>]]></text>
      <feedback format="html"><text><![CDATA[<p>Chính xác!</p>]]></text></feedback>
    </answer>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>FTP</p>]]></text>
    </answer>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>Telnet</p>]]></text>
    </answer>
  </question>

  <!-- Question 2: Multiple Choice -->
  <question type="multichoice">
    <name>
      <text>Câu 2: Các phương thức HTTP Idempotent</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Các phương thức HTTP nào sau đây có tính chất <strong>Idempotent</strong> (thao tác lặp lại nhiều lần sinh cùng kết quả trên máy chủ)?</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p>GET, PUT, DELETE được định nghĩa là Idempotent trong chuẩn HTTP/1.1 RFC 7231.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1.5000000</defaultgrade>
    <single>false</single>
    <shuffleanswers>true</shuffleanswers>
    <answernumbering>abc</answernumbering>
    <answer fraction="33.33333" format="html">
      <text><![CDATA[<p>GET</p>]]></text>
    </answer>
    <answer fraction="-50" format="html">
      <text><![CDATA[<p>POST</p>]]></text>
    </answer>
    <answer fraction="33.33333" format="html">
      <text><![CDATA[<p>PUT</p>]]></text>
    </answer>
    <answer fraction="33.33333" format="html">
      <text><![CDATA[<p>DELETE</p>]]></text>
    </answer>
  </question>

  <!-- Question 3: True / False -->
  <question type="truefalse">
    <name>
      <text>Câu 3: Khóa ngoại trong CSDL quan hệ</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Trong cơ sở dữ liệu quan hệ (RDBMS), Khóa ngoại (Foreign Key) bắt buộc phải luôn luôn có giá trị khác NULL.</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p>Sai. Cột khóa ngoại hoàn toàn có thể mang giá trị NULL nếu không khai báo ràng buộc NOT NULL.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1.0000000</defaultgrade>
    <answer fraction="0" format="html">
      <text>true</text>
    </answer>
    <answer fraction="100" format="html">
      <text>false</text>
    </answer>
  </question>

  <!-- Question 4: Short Answer / Fill in the blank -->
  <question type="shortanswer">
    <name>
      <text>Câu 4: Mã thông báo xác thực REST API</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Cơ chế xác thực không trạng thái (Stateless Authentication) chuẩn quốc tế dùng mã thông báo viết tắt là ___?</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p>JSON Web Token (JWT) là tiêu chuẩn mở RFC 7519 phổ biến nhất.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1.5000000</defaultgrade>
    <usecase>0</usecase>
    <answer fraction="100" format="plain_text">
      <text>JWT</text>
    </answer>
    <answer fraction="100" format="plain_text">
      <text>JSON Web Token</text>
    </answer>
  </question>
</quiz>
"""


def generate_sample_json() -> str:
    """Generate a clean, standardized JSON exam questions sample."""
    sample = {
        "title": "Đề thi mẫu PWD301 chuẩn hóa JSON",
        "description": "Cấu trúc danh sách câu hỏi học thuật trao đổi quốc tế",
        "questions": [
            {
                "number": 1,
                "question_type": "Trắc nghiệm 1 đáp án",
                "type": "SINGLE_CHOICE",
                "stem": "Đâu là giao thức mạng truyền tải siêu văn bản có mã hóa bảo mật SSL/TLS?",
                "points": 1.0,
                "bloom_level": "Nhận biết",
                "explanation": "HTTPS sử dụng SSL/TLS để mã hóa dữ liệu.",
                "choices": [
                    {"label": "A", "content": "HTTP", "is_correct": False},
                    {"label": "B", "content": "HTTPS", "is_correct": True},
                    {"label": "C", "content": "FTP", "is_correct": False},
                    {"label": "D", "content": "Telnet", "is_correct": False},
                ],
            },
            {
                "number": 2,
                "question_type": "TN nhiều đáp án",
                "type": "MULTIPLE_CHOICE",
                "stem": "Các phương thức HTTP nào sau đây được định nghĩa là Idempotent?",
                "points": 1.5,
                "bloom_level": "Thông hiểu",
                "explanation": "GET, PUT, DELETE là Idempotent theo RFC 7231.",
                "choices": [
                    {"label": "A", "content": "GET", "is_correct": True},
                    {"label": "B", "content": "POST", "is_correct": False},
                    {"label": "C", "content": "PUT", "is_correct": True},
                    {"label": "D", "content": "DELETE", "is_correct": True},
                ],
            },
            {
                "number": 3,
                "question_type": "Đúng / Sai",
                "type": "TRUE_FALSE",
                "stem": "Trong CSDL quan hệ, Khóa ngoại (Foreign Key) bắt buộc phải luôn khác NULL.",
                "points": 1.0,
                "bloom_level": "Thông hiểu",
                "explanation": "Khóa ngoại có thể mang giá trị NULL nếu không có ràng buộc NOT NULL.",
                "choices": [
                    {"label": "A", "content": "Đúng", "is_correct": False},
                    {"label": "B", "content": "Sai", "is_correct": True},
                ],
            },
            {
                "number": 4,
                "question_type": "Điền từ",
                "type": "SHORT_ANSWER",
                "stem": "Cơ chế xác thực không trạng thái phổ biến trong RESTful API sử dụng mã thông báo viết tắt là ___?",
                "points": 1.5,
                "bloom_level": "Vận dụng",
                "explanation": "JSON Web Token (JWT) theo chuẩn RFC 7519.",
                "accepted_answers": ["JWT", "JSON Web Token"],
                "choices": [],
            },
        ],
    }
    return json.dumps(sample, ensure_ascii=False, indent=2)


def parse_moodle_xml(xml_content: str) -> dict[str, Any]:
    """Parse Moodle XML into standardized PWD301 exam questions list."""
    if not xml_content or not xml_content.strip():
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": ["Nội dung Moodle XML trống."],
        }

    try:
        root = ET.fromstring(xml_content.strip())
    except Exception as err:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": [f"Lỗi cú pháp XML (Malformed XML): {err}"],
        }

    # Find question nodes: either directly under root or inside quiz
    question_nodes = root.findall(".//question")
    if not question_nodes and root.tag == "question":
        question_nodes = [root]

    parsed_questions: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    total_points = 0.0
    q_counter = 1

    for node in question_nodes:
        q_type_attr = (node.attrib.get("type") or "").strip().lower()
        if q_type_attr in ("category", "description", ""):
            # Skip Moodle section headers and category meta-nodes
            continue

        # Extract Question Text
        qt_node = node.find("./questiontext/text")
        raw_stem = qt_node.text if qt_node is not None and qt_node.text else ""
        if not raw_stem:
            # Fallback to name
            name_node = node.find("./name/text")
            raw_stem = name_node.text if name_node is not None and name_node.text else ""

        stem = _clean_html_text(raw_stem)
        if not stem:
            warnings.append(f"Bỏ qua câu hỏi #{q_counter} vì không tìm thấy nội dung câu hỏi.")
            continue

        # Extract Default Grade / Points
        grade_node = node.find("./defaultgrade")
        pts = 1.0
        if grade_node is not None and grade_node.text:
            try:
                pts = float(grade_node.text.strip())
                if pts <= 0:
                    pts = 1.0
            except ValueError:
                pts = 1.0

        # Extract General Feedback / Explanation
        fb_node = node.find("./generalfeedback/text")
        explanation = _clean_html_text(fb_node.text) if fb_node is not None and fb_node.text else ""

        # Map types and answers
        choices: list[dict[str, Any]] = []
        accepted_answers: list[str] = []
        mapped_type = "SINGLE_CHOICE"

        if q_type_attr == "multichoice":
            single_node = node.find("./single")
            is_single = True
            if single_node is not None and single_node.text:
                is_single = single_node.text.strip().lower() in ("true", "1", "yes")

            answer_nodes = node.findall("./answer")
            correct_count = 0
            for idx, ans_el in enumerate(answer_nodes, start=1):
                ans_text_el = ans_el.find("./text")
                ans_content = _clean_html_text(ans_text_el.text) if ans_text_el is not None and ans_text_el.text else ""
                if not ans_content:
                    continue

                fraction = float(ans_el.attrib.get("fraction", 0.0) or 0.0)
                is_corr = fraction > 0.0
                if is_corr:
                    correct_count += 1

                label = chr(64 + len(choices) + 1) if len(choices) < 26 else str(len(choices) + 1)
                choices.append({
                    "label": label,
                    "content": ans_content,
                    "is_correct": is_corr,
                    "position": len(choices) + 1,
                    "fraction": fraction,
                })

            if not is_single or correct_count > 1:
                mapped_type = "MULTIPLE_CHOICE"
            else:
                mapped_type = "SINGLE_CHOICE"

            if correct_count == 0 and choices:
                choices[0]["is_correct"] = True
                warnings.append(f"Câu {q_counter}: Không có đáp án đúng được đánh dấu, hệ thống tự động gán đáp án A.")

        elif q_type_attr == "truefalse":
            mapped_type = "TRUE_FALSE"
            answer_nodes = node.findall("./answer")
            is_true_correct = False
            for ans_el in answer_nodes:
                fraction = float(ans_el.attrib.get("fraction", 0.0) or 0.0)
                ans_text_el = ans_el.find("./text")
                txt = (ans_text_el.text or "").strip().lower() if ans_text_el is not None else ""
                if fraction >= 99.0 and txt in ("true", "đúng", "1"):
                    is_true_correct = True
                    break
                elif fraction >= 99.0 and txt in ("false", "sai", "0"):
                    is_true_correct = False
                    break

            choices = [
                {"label": "A", "content": "Đúng", "is_correct": is_true_correct, "position": 1},
                {"label": "B", "content": "Sai", "is_correct": not is_true_correct, "position": 2},
            ]

        elif q_type_attr in ("shortanswer", "numerical"):
            mapped_type = "SHORT_ANSWER"
            answer_nodes = node.findall("./answer")
            for ans_el in answer_nodes:
                fraction = float(ans_el.attrib.get("fraction", 0.0) or 0.0)
                if fraction > 0:
                    ans_text_el = ans_el.find("./text")
                    ans_txt = _clean_html_text(ans_text_el.text) if ans_text_el is not None and ans_text_el.text else ""
                    if ans_txt and ans_txt not in accepted_answers:
                        accepted_answers.append(ans_txt)

            if not accepted_answers:
                accepted_answers = ["Đáp án"]

        else:
            # Fallback for essay or custom types
            answer_nodes = node.findall("./answer")
            if answer_nodes:
                for idx, ans_el in enumerate(answer_nodes, start=1):
                    ans_text_el = ans_el.find("./text")
                    ans_content = _clean_html_text(ans_text_el.text) if ans_text_el is not None and ans_text_el.text else ""
                    if ans_content:
                        fraction = float(ans_el.attrib.get("fraction", 0.0) or 0.0)
                        choices.append({
                            "label": chr(64 + len(choices) + 1),
                            "content": ans_content,
                            "is_correct": fraction > 0,
                            "position": len(choices) + 1,
                        })
                mapped_type = "SINGLE_CHOICE"
            else:
                mapped_type = "SHORT_ANSWER"
                accepted_answers = ["Đáp án tự luận"]

        q_obj: dict[str, Any] = {
            "id": q_counter,
            "number": q_counter,
            "stem": stem,
            "question_text": stem,
            "type": mapped_type,
            "question_type": (
                "TN nhiều đáp án" if mapped_type == "MULTIPLE_CHOICE"
                else "Đúng / Sai" if mapped_type == "TRUE_FALSE"
                else "Điền từ" if mapped_type == "SHORT_ANSWER"
                else "Trắc nghiệm 1 đáp án"
            ),
            "points": pts,
            "bloom_level": "Thông hiểu",
            "explanation": explanation,
            "choices": choices,
        }

        if mapped_type == "SHORT_ANSWER":
            q_obj["accepted_answers"] = accepted_answers
            q_obj["options"] = [{"content": a, "is_correct": True} for a in accepted_answers]

        total_points += pts
        parsed_questions.append(q_obj)
        q_counter += 1

    if not parsed_questions:
        errors.append("Không tìm thấy câu hỏi hợp lệ trong tệp Moodle XML.")

    return {
        "success": len(errors) == 0 and len(parsed_questions) > 0,
        "questions": parsed_questions,
        "total_questions": len(parsed_questions),
        "total_points": round(total_points, 2),
        "warnings": warnings,
        "errors": errors,
    }


def parse_moodle_json(json_content: str) -> dict[str, Any]:
    """Parse JSON string into standardized PWD301 exam questions list."""
    if not json_content or not json_content.strip():
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": ["Nội dung JSON trống."],
        }

    try:
        data = json.loads(json_content.strip())
    except Exception as err:
        return {
            "success": False,
            "questions": [],
            "total_questions": 0,
            "total_points": 0.0,
            "warnings": [],
            "errors": [f"Lỗi cú pháp JSON không hợp lệ: {err}"],
        }

    raw_list: list[Any] = []
    if isinstance(data, list):
        raw_list = data
    elif isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            raw_list = data["questions"]
        elif "items" in data and isinstance(data["items"], list):
            raw_list = data["items"]
        else:
            raw_list = [data]

    parsed_questions: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    total_points = 0.0

    for idx, item in enumerate(raw_list, start=1):
        if not isinstance(item, dict):
            warnings.append(f"Mục #{idx} không phải là đối tượng JSON câu hỏi hợp lệ.")
            continue

        raw_stem = item.get("content") or item.get("stem") or item.get("question_text") or item.get("prompt") or ""
        stem = str(raw_stem).strip()
        if not stem:
            warnings.append(f"Mục #{idx}: Thiếu nội dung câu hỏi, bỏ qua.")
            continue

        raw_type = (item.get("question_type") or item.get("type") or "SINGLE_CHOICE").upper()
        if "NHIỀU" in raw_type or raw_type == "MULTIPLE_CHOICE":
            q_type = "MULTIPLE_CHOICE"
        elif "ĐÚNG" in raw_type or raw_type in ("TRUE_FALSE", "TRUEFALSE"):
            q_type = "TRUE_FALSE"
        elif "ĐIỀN" in raw_type or raw_type in ("SHORT_ANSWER", "SHORTANSWER"):
            q_type = "SHORT_ANSWER"
        else:
            q_type = "SINGLE_CHOICE"

        raw_pts = item.get("points") or item.get("default_points") or 1.0
        try:
            pts = float(raw_pts)
            if pts <= 0:
                pts = 1.0
        except (ValueError, TypeError):
            pts = 1.0

        raw_bloom = item.get("bloom_level") or item.get("difficulty") or "Thông hiểu"
        bloom = str(raw_bloom).strip()
        if bloom in ("REMEMBER", "Nhận biết"):
            bloom = "Nhận biết"
        elif bloom in ("APPLY", "Vận dụng"):
            bloom = "Vận dụng"
        else:
            bloom = "Thông hiểu"

        explanation = str(item.get("explanation") or "").strip()

        choices: list[dict[str, Any]] = []
        raw_choices = item.get("choices") or item.get("options") or []
        if isinstance(raw_choices, list) and q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE"):
            for c_idx, c in enumerate(raw_choices, start=1):
                if isinstance(c, dict):
                    c_txt = str(c.get("content") or c.get("text") or "").strip()
                    is_c = bool(c.get("is_correct", False))
                    lbl = str(c.get("label") or chr(64 + c_idx)).upper()
                else:
                    c_txt = str(c).strip()
                    is_c = False
                    lbl = chr(64 + c_idx)
                if c_txt:
                    choices.append({
                        "label": lbl,
                        "content": c_txt,
                        "is_correct": is_c,
                        "position": len(choices) + 1,
                    })

            # Check correctness
            corr_count = sum(1 for c in choices if c["is_correct"])
            if corr_count > 1:
                q_type = "MULTIPLE_CHOICE"
            elif corr_count == 0 and choices:
                choices[0]["is_correct"] = True
                warnings.append(f"Câu #{idx}: Chưa có đáp án đúng, hệ thống tự động gán đáp án {choices[0]['label']}.")

        elif q_type == "TRUE_FALSE":
            # Check if choices provided or synthesize
            is_t_corr = True
            if isinstance(raw_choices, list) and raw_choices:
                for c in raw_choices:
                    if isinstance(c, dict) and c.get("is_correct"):
                        is_t_corr = "đúng" in str(c.get("content") or "").lower() or str(c.get("label")).upper() == "A"
            choices = [
                {"label": "A", "content": "Đúng", "is_correct": is_t_corr, "position": 1},
                {"label": "B", "content": "Sai", "is_correct": not is_t_corr, "position": 2},
            ]

        accepted_answers: list[str] = []
        if q_type == "SHORT_ANSWER":
            raw_acc = item.get("accepted_answers") or item.get("answers") or raw_choices
            if isinstance(raw_acc, list):
                for a in raw_acc:
                    if isinstance(a, dict):
                        a_txt = str(a.get("content") or a.get("answer_text") or a.get("text") or "").strip()
                    else:
                        a_txt = str(a).strip()
                    if a_txt:
                        accepted_answers.append(a_txt)
            elif isinstance(raw_acc, str) and raw_acc.strip():
                accepted_answers.append(raw_acc.strip())

            if not accepted_answers:
                accepted_answers = ["Đáp án"]

        q_obj: dict[str, Any] = {
            "id": len(parsed_questions) + 1,
            "number": len(parsed_questions) + 1,
            "stem": stem,
            "question_text": stem,
            "type": q_type,
            "question_type": (
                "TN nhiều đáp án" if q_type == "MULTIPLE_CHOICE"
                else "Đúng / Sai" if q_type == "TRUE_FALSE"
                else "Điền từ" if q_type == "SHORT_ANSWER"
                else "Trắc nghiệm 1 đáp án"
            ),
            "points": pts,
            "bloom_level": bloom,
            "explanation": explanation,
            "choices": choices,
        }

        if q_type == "SHORT_ANSWER":
            q_obj["accepted_answers"] = accepted_answers
            q_obj["options"] = [{"content": a, "is_correct": True} for a in accepted_answers]

        total_points += pts
        parsed_questions.append(q_obj)

    if not parsed_questions:
        errors.append("Không tìm thấy câu hỏi hợp lệ nào trong tệp JSON.")

    return {
        "success": len(errors) == 0 and len(parsed_questions) > 0,
        "questions": parsed_questions,
        "total_questions": len(parsed_questions),
        "total_points": round(total_points, 2),
        "warnings": warnings,
        "errors": errors,
    }
