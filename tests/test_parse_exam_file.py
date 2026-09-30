"""Tests for POST /instructor/exams/parse-file endpoint."""
import io
import pytest
from pwd301.extensions import db
from pwd301.services.user_service import register_user, assign_role_to_user
from tests.test_m3_challenger_stress import _make_sample_docx, _make_sample_pdf
from tests.conftest import login_web_user


def _setup_instructor(email="inst_parse@test.edu"):
    user = register_user(
        email,
        "ValidPassword123!",
        "Instructor Parser",
        session=db.session,
    )
    assign_role_to_user(
        user.id,
        "INSTRUCTOR",
        session=db.session,
    )
    db.session.commit()
    return user


def test_parse_exam_file_txt(client, app):
    with app.app_context():
        user = _setup_instructor("inst_parse_txt@test.edu")
        login_web_user(client, user)

    txt_content = (
        "Câu 1: Thủ đô của Việt Nam là gì?\n"
        "A. TP.HCM\n"
        "*B. Hà Nội\n"
        "C. Đà Nẵng\n"
        "D. Huế\n\n"
        "Câu 2: 1 + 1 bằng bao nhiêu?\n"
        "*A. 2\n"
        "B. 3\n"
        "C. 4\n"
        "D. 5\n"
    )
    res = client.post(
        "/instructor/exams/parse-file",
        data={
            "file": (io.BytesIO(txt_content.encode("utf-8")), "de_thi.txt", "text/plain")
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "Hà Nội" in data["raw_text"]
    assert data["filename"] == "de_thi.txt"


def test_parse_exam_file_docx(client, app):
    with app.app_context():
        user = _setup_instructor("inst_parse_docx@test.edu")
        login_web_user(client, user)

    docx_bytes = _make_sample_docx([
        "Câu 1: Kiến trúc RESTful dựa trên giao thức nào?",
        "A. FTP",
        "*B. HTTP",
        "C. SMTP",
        "D. SSH",
        "Lời giải: RESTful sử dụng HTTP làm giao thức truyền thông tải dữ liệu.",
    ])
    res = client.post(
        "/instructor/exams/parse-file",
        data={
            "file": (io.BytesIO(docx_bytes), "de_thi_rest.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "RESTful" in data["raw_text"]
    assert "HTTP" in data["raw_text"]
    assert data["filename"] == "de_thi_rest.docx"


def test_parse_exam_file_docx_with_underline_and_math(client, app):
    """Test that underlined choices are formatted as <u>...</u> and OMML fractions become LaTeX."""
    import zipfile
    with app.app_context():
        user = _setup_instructor("inst_parse_math@test.edu")
        login_web_user(client, user)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">\n'
            '  <w:body>\n'
            '    <w:p><w:r><w:t>Câu 1: Cho hàm số f(x) = </w:t></w:r>'
            '      <m:oMath><m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f></m:oMath>'
            '      <w:r><w:t>. Chọn đáp án đúng:</w:t></w:r></w:p>\n'
            '    <w:p><w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>A</w:t></w:r><w:r><w:t>. Bằng 0.5</w:t></w:r></w:p>\n'
            '    <w:p><w:r><w:t>B. Bằng 1</w:t></w:r></w:p>\n'
            '  </w:body>\n'
            '</w:document>'
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))

    res = client.post(
        "/instructor/exams/parse-file",
        data={
            "file": (io.BytesIO(buffer.getvalue()), "de_toan_omml.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    # Underlined choice A must be wrapped in <u>
    assert "<u>A</u>" in data["raw_text"]
    # Fraction 1/2 must be rendered with LaTeX \frac{1}{2}
    assert r"\frac{1}{2}" in data["raw_text"]
