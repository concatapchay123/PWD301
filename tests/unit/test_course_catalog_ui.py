"""Unit tests for redesigned modern minimalist course card UI rendering."""

from flask import render_template


def test_catalog_course_card_minimal_rendering(app):
    """Verify catalog.html renders courses using .course-card-minimal."""
    with app.test_request_context("/"):

        class MockInstructor:
            display_name = "ThS. Trần Thị B"

        class MockLesson:
            pass

        class MockCourse:
            def __init__(self, code, title, category, desc=""):
                self.public_id = f"pub-{code.lower()}"
                self.course_code = code
                self.title = title
                self.category = category
                self.description = desc
                self.owner_instructor = MockInstructor()
                self.lessons = [MockLesson(), MockLesson()]

        courses = [
            MockCourse(
                "CS301",
                "CS301: Trí tuệ Nhân tạo & Xử lý Ngôn ngữ Tự nhiên RAG",
                "Trí tuệ Nhân tạo",
                "Ứng dụng LLM và RAG",
            ),
            MockCourse(
                "WEB101",
                "WEB101: Phát triển Web Hiện đại",
                "Phát triển Web",
                "Khóa học Fullstack Web",
            ),
            MockCourse(
                "CS101",
                "CS101: Lập trình Python Cơ bản",
                "Khoa học Máy tính",
                "Nhập môn lập trình",
            ),
            MockCourse(
                "DATA201",
                "DATA201: Cơ sở Dữ liệu SQL Nâng cao",
                "Dữ liệu & SQL",
                "Quản trị cơ sở dữ liệu",
            ),
            MockCourse(
                "SEC301",
                "SEC301: An toàn thông tin",
                "Bảo mật",
                "Bảo mật hệ thống",
            ),
        ]

        rendered = render_template("public/catalog.html", courses=courses)

        # Check .course-card-minimal is used
        assert "course-card-minimal" in rendered
        assert "course-card-item" in rendered

        # Check tailored category mesh gradients
        assert "thumb-mesh-ai" in rendered
        assert "thumb-mesh-web" in rendered
        assert "thumb-mesh-cs" in rendered
        assert "thumb-mesh-data" in rendered
        assert "thumb-mesh-security" in rendered

        # Check essential modern UI elements
        assert "frosted-badge" in rendered
        assert "course-code-tag" in rendered
        assert "course-instructor-text" in rendered
        assert "course-card-desc" in rendered
        assert "course-status-pill" in rendered
        assert "Đang mở ghi danh" in rendered
        assert "course-card-cta" in rendered
        assert "cta-arrow" in rendered

        # Check harsh white grid SVG pattern is removed
        assert "grid-pat" not in rendered


def test_my_learning_course_card_minimal_rendering(app):
    """Verify student/my_learning.html renders enrolled courses with .course-card-minimal."""
    with app.test_request_context("/student/my-learning"):

        class MockEnrollment:
            def __init__(self, code, title, status, progress):
                self.course_id = f"c-{code.lower()}"
                self.course_code = code
                self.course_title = title
                self.instructor_name = "TS. Nguyễn Văn A"
                self.status = status
                self.progress_percent = progress

        overview = {
            "enrollments": [
                MockEnrollment("CS301", "Trí tuệ Nhân tạo RAG", "ACTIVE", 45),
                MockEnrollment("CS101", "Lập trình Python", "COMPLETED", 100),
            ]
        }

        rendered = render_template("student/my_learning.html", overview=overview)

        assert "course-card-minimal" in rendered
        assert "frosted-badge" in rendered
        assert "course-code-tag" in rendered
        assert "Tiến độ bài học" in rendered
        assert "45%" in rendered
        assert "100%" in rendered
        assert "grid-my" not in rendered
