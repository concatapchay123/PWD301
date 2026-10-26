# -*- coding: utf-8 -*-
import pytest
from backend.services.course_service import extract_course_meta, clean_course_description

def test_extract_course_meta_with_contact_info():
    raw = (
        'Đây là khóa học của admin Phúc đẹp trai\n\n'
        '<!-- contact_info: {"email": "tqtphamnguyenhoangphuc@gmail.com", "phone": "0908123456", "group": "Zalo Group", "office_hours": "T2-T6"} -->'
    )
    clean, tr, ci = extract_course_meta(raw)
    assert clean == 'Đây là khóa học của admin Phúc đẹp trai'
    assert tr is None
    assert ci == {
        'email': 'tqtphamnguyenhoangphuc@gmail.com',
        'phone': '0908123456',
        'group': 'Zalo Group',
        'office_hours': 'T2-T6',
    }
    assert clean_course_description(raw) == 'Đây là khóa học của admin Phúc đẹp trai'

def test_extract_course_meta_with_trailer_url_and_contact():
    raw = (
        'Mô tả khóa học bảo mật web chuyên sâu\n\n'
        '<!-- trailer_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ -->\n'
        '<!-- contact_info: {"email": "instructor@pptq.vn", "phone": "", "group": "", "office_hours": ""} -->'
    )
    clean, tr, ci = extract_course_meta(raw)
    assert clean == 'Mô tả khóa học bảo mật web chuyên sâu'
    assert tr == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    assert ci['email'] == 'instructor@pptq.vn'
    assert clean_course_description(raw) == 'Mô tả khóa học bảo mật web chuyên sâu'

def test_clean_course_meta_empty():
    assert clean_course_description(None) == ''
    assert clean_course_description('') == ''
