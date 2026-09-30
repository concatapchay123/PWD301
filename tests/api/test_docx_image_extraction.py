"""Tests for Word DOCX Image and Resource Extraction Engine."""

from __future__ import annotations

import io
from pathlib import Path
import tempfile
import zipfile
import pytest

from pwd301.services.import_service import (
    extract_docx_with_resources,
    extract_text_from_docx,
)


def create_sample_docx_with_images() -> bytes:
    """Create an in-memory DOCX archive with drawingML and VML image relationships."""
    buffer = io.BytesIO()
    
    # 1x1 valid PNG bytes
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"

    with zipfile.ZipFile(buffer, "w") as zf:
        # 1. document.xml.rels
        rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>\n'
            '  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.jpg"/>\n'
            '</Relationships>'
        )
        zf.writestr("word/_rels/document.xml.rels", rels_xml.encode("utf-8"))

        # 2. document.xml
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"\n'
            '            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"\n'
            '            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"\n'
            '            xmlns:v="urn:schemas-microsoft-com:vml">\n'
            '  <w:body>\n'
            '    <w:p>\n'
            '      <w:r><w:t>Câu 1: Cho hình vẽ bên dưới.</w:t></w:r>\n'
            '      <w:r>\n'
            '        <w:drawing>\n'
            '          <wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">\n'
            '            <a:graphic>\n'
            '              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">\n'
            '                <a:blip r:embed="rId1"/>\n'
            '              </a:graphicData>\n'
            '            </a:graphic>\n'
            '          </wp:inline>\n'
            '        </w:drawing>\n'
            '      </w:r>\n'
            '    </w:p>\n'
            '    <w:p><w:r><w:t>A. Đáp án 1</w:t></w:r></w:p>\n'
            '    <w:p><w:r><w:t>*B. Đáp án 2</w:t></w:r></w:p>\n'
            '    <w:p>\n'
            '      <w:r><w:t>Câu 2: Sơ đồ mạch điện VML</w:t></w:r>\n'
            '      <w:r>\n'
            '        <w:pict>\n'
            '          <v:shape id="shape1">\n'
            '            <v:imagedata r:id="rId2"/>\n'
            '          </v:shape>\n'
            '        </w:pict>\n'
            '      </w:r>\n'
            '    </w:p>\n'
            '  </w:body>\n'
            '</w:document>'
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))

        # 3. Media files
        zf.writestr("word/media/image1.png", png_bytes)
        zf.writestr("word/media/image2.jpg", jpeg_bytes)

    return buffer.getvalue()


def test_extract_docx_with_resources():
    """Verify that extract_docx_with_resources extracts images and places markers."""
    docx_bytes = create_sample_docx_with_images()
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(docx_bytes)

    try:
        lines, images = extract_docx_with_resources(tmp_path)
        assert len(lines) >= 4
        assert len(images) == 2

        # Verify image 1
        img1 = images[0]
        assert img1["mime_type"] == "image/png"
        assert img1["filename"].endswith(".png")
        assert len(img1["data"]) > 0
        assert "[[PWD301:EXTRACTED_IMAGE:0]]" in img1["token"]

        # Verify image 2
        img2 = images[1]
        assert img2["mime_type"] in ("image/jpeg", "image/jpg")
        assert len(img2["data"]) > 0
        assert "[[PWD301:EXTRACTED_IMAGE:1]]" in img2["token"]

        # Verify lines contain markers
        joined_text = "\n".join(lines)
        assert "Câu 1: Cho hình vẽ bên dưới." in joined_text
        assert "[[PWD301:EXTRACTED_IMAGE:0]]" in joined_text
        assert "Câu 2: Sơ đồ mạch điện VML" in joined_text
        assert "[[PWD301:EXTRACTED_IMAGE:1]]" in joined_text

        # Verify extract_text_from_docx backward compatibility
        compat_lines = extract_text_from_docx(tmp_path)
        assert len(compat_lines) >= 4
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
