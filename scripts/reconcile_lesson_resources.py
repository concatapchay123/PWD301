"""Reconcile and backfill missing LessonResource links for active/published lessons.

Ensures that any published lesson whose predecessor (historical revision) or
prior change requests had attached resources (videos, documents) retains them.
"""

import sys
from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.course import Lesson
from pwd301.models.file_import import LessonResource
from pwd301.services.lesson_service import _copy_lesson_resources


def reconcile() -> int:
    app = create_app()
    with app.app_context():
        print("=== BẮT ĐẦU ĐỒNG BỘ & KHẮC PHỤC DỮ LIỆU TÀI NGUYÊN BÀI HỌC ===")
        active_lessons = (
            db.session.query(Lesson)
            .filter(Lesson.status.in_(["PUBLISHED", "ACTIVE"]))
            .all()
        )
        reconciled_count = 0

        for les in active_lessons:
            initial_res_count = (
                db.session.query(LessonResource)
                .filter(LessonResource.lesson_id == les.id)
                .count()
            )

            # 1. Backfill from predecessor chain (previous_lesson_id)
            curr = les
            visited = set()
            while curr and curr.previous_lesson_id and curr.previous_lesson_id not in visited:
                visited.add(curr.previous_lesson_id)
                _copy_lesson_resources(curr.previous_lesson_id, les.id, session=db.session)
                curr = db.session.query(Lesson).get(curr.previous_lesson_id)

            new_res_count = (
                db.session.query(LessonResource)
                .filter(LessonResource.lesson_id == les.id)
                .count()
            )

            diff = new_res_count - initial_res_count
            if diff > 0:
                reconciled_count += diff
                print(
                    f"[RECONCILED] Bài học id={les.id} ('{les.title}', position={les.position}, "
                    f"revision_no={les.revision_no}) đã được khôi phục thêm {diff} tài nguyên "
                    f"(trước: {initial_res_count}, sau: {new_res_count})."
                )
            else:
                print(
                    f"[OK] Bài học id={les.id} ('{les.title}', position={les.position}): "
                    f"{new_res_count} tài nguyên hiện hữu."
                )

        db.session.commit()
        print(f"=== HOÀN TẤT ĐỒNG BỘ: Đã bổ sung tổng cộng {reconciled_count} tài nguyên bị thiếu ===")
        return 0


if __name__ == "__main__":
    sys.exit(reconcile())
