"""Integration checks for multi-image assessment authoring and student delivery."""

import io

from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.identity import User
from pwd301.services.file_service import store_file_stream

pytest_plugins = ("tests.api.test_attempt_api",)


def test_batch_created_question_delivers_all_clean_images(
    client: FlaskClient,
    published_assessment: Assessment,
    instructor_user: User,
    instructor_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    images = []
    for filename, image_bytes in (
        ("triangle.png", b"\x89PNG\r\n\x1a\ntriangle"),
        ("angle.png", b"\x89PNG\r\n\x1a\nangle"),
    ):
        image = store_file_stream(
            actor=instructor_user,
            course_id=published_assessment.course_id,
            file_stream=io.BytesIO(image_bytes),
            filename=filename,
            content_type="image/png",
            asset_type="RESOURCE",
            session=db.session,
        )
        image.status = "ACTIVE"
        images.append(image)
    db.session.commit()

    created = client.post(
        f"/instructor/assessments/{published_assessment.public_id}/questions/batch",
        headers=instructor_headers,
        json={
            "questions": [
                {
                    "question_type": "SINGLE_CHOICE",
                    "content": "Which diagram shows the right angle?",
                    "points": 1,
                    "choices": [
                        {"content": "Diagram one", "is_correct": True},
                        {"content": "Diagram two", "is_correct": False},
                    ],
                    "image_asset_ids": [str(image.public_id) for image in images],
                }
            ]
        },
    )
    assert created.status_code == 201

    started = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert started.status_code == 201
    delivered = client.get(
        f"/api/attempts/{started.get_json()['attempt_id']}",
        headers=student_headers,
    )

    assert delivered.status_code == 200
    question = next(
        item
        for item in delivered.get_json()["questions"]
        if item["content"] == "Which diagram shows the right angle?"
    )
    delivered_asset_ids = [
        resource["url"].split("?", 1)[0].rstrip("/").rsplit("/", 2)[-2]
        for resource in question["resources"]
    ]
    assert delivered_asset_ids == [str(image.public_id) for image in images]
    assert all(
        resource["url"].endswith("?disposition=inline")
        for resource in question["resources"]
    )


def test_batch_created_question_hides_unscanned_image_from_student(
    client: FlaskClient,
    published_assessment: Assessment,
    instructor_user: User,
    instructor_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    image = store_file_stream(
        actor=instructor_user,
        course_id=published_assessment.course_id,
        file_stream=io.BytesIO(b"\x89PNG\r\n\x1a\nwaiting-for-scan"),
        filename="pending-diagram.png",
        content_type="image/png",
        asset_type="RESOURCE",
        session=db.session,
    )
    image.status = "PENDING"
    db.session.commit()

    created = client.post(
        f"/instructor/assessments/{published_assessment.public_id}/questions/batch",
        headers=instructor_headers,
        json={
            "questions": [
                {
                    "question_type": "SINGLE_CHOICE",
                    "content": "Pending diagram stays private.",
                    "points": 1,
                    "choices": [
                        {"content": "A", "is_correct": True},
                        {"content": "B", "is_correct": False},
                    ],
                    "image_asset_id": str(image.public_id),
                }
            ]
        },
    )
    assert created.status_code == 201

    started = client.post(
        f"/api/assessments/{published_assessment.public_id}/attempts",
        headers=student_headers,
    )
    assert started.status_code == 201
    delivered = client.get(
        f"/api/attempts/{started.get_json()['attempt_id']}",
        headers=student_headers,
    )

    assert delivered.status_code == 200
    question = next(
        item
        for item in delivered.get_json()["questions"]
        if item["content"] == "Pending diagram stays private."
    )
    assert question["resources"] == []
