"""Public cover bytes follow the same owned, scanned image contract as authoring."""

import io

import pytest

from backend.extensions import db
from backend.models.file_import import FileScanResult
from backend.services.course_service import change_course_status, create_course, update_course
from backend.services.file_service import store_file_stream

pytest_plugins = ["tests.api.test_course_api"]


def _published_cover(owner, admin, asset_type="RESOURCE"):
    course = create_course(owner, {"course_code": "COVER-MEDIA", "title": "Cover Media Contract"})
    image = store_file_stream(
        owner,
        course.id,
        io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"a" * 64),
        "cover.png",
        "image/png",
        asset_type=asset_type,
        session=db.session,
    )
    update_course(owner, course.id, {"thumbnail_file_asset_id": str(image.public_id)})
    change_course_status(owner, course.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course.id, "APPROVED")
    change_course_status(owner, course.id, "PUBLISHED")
    return course, image


@pytest.mark.parametrize("asset_type", ["RESOURCE", "COURSE_IMAGE"])
def test_public_cover_accepts_every_supported_owned_scanned_image_type(
    app, client, instructor_user, admin_user, asset_type
):
    course, image = _published_cover(instructor_user, admin_user, asset_type)
    response = client.get(f"/api/courses/{course.public_id}/thumbnail")
    assert response.status_code == 200, response.json if response.is_json else response.status
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    response.close()
    assert image.course_id == course.id


@pytest.mark.parametrize("verdict", ["QUARANTINED", "FAIL", "ERROR"])
def test_public_resource_cover_remains_fail_closed_after_unsafe_scan(
    app, client, instructor_user, admin_user, verdict
):
    course, image = _published_cover(instructor_user, admin_user)
    if verdict == "QUARANTINED":
        image.current_revision.is_current = False
        image.current_revision.status = "QUARANTINED"
    else:
        db.session.add(
            FileScanResult(
                file_revision_id=image.current_revision.id,
                scan_type="MALWARE",
                engine="additional-cover-scanner",
                status=verdict,
            )
        )
    db.session.commit()
    assert client.get(f"/api/courses/{course.public_id}/thumbnail").status_code == 404


def test_public_cover_never_serves_another_courses_asset(app, client, instructor_user, admin_user):
    course, _ = _published_cover(instructor_user, admin_user)
    other = create_course(instructor_user, {"course_code": "OTHER-COVER", "title": "Other course"})
    foreign = store_file_stream(
        instructor_user,
        other.id,
        io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"b" * 64),
        "foreign.png",
        "image/png",
        asset_type="RESOURCE",
        session=db.session,
    )
    course.thumbnail_file_asset_id = foreign.id
    db.session.commit()
    assert client.get(f"/api/courses/{course.public_id}/thumbnail").status_code == 404
