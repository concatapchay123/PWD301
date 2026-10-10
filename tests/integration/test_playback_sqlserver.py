"""Live, explicitly disposable SQL Server concurrency gate; never SQLite proof."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import LessonProgress
from pwd301.models.identity import User
from pwd301.models.playback import PlaybackReceipt
from pwd301.services.playback_service import record_playback_heartbeat, start_playback_session
from tests.unit.test_playback_sessions import playback_setup  # noqa: F401


@pytest.mark.integration
@pytest.mark.concurrency
def test_same_sequence_concurrent_workers_credit_once(playback_setup):  # noqa: F811
    if db.engine.dialect.name != "mssql":
        pytest.skip("Requires disposable SQL Server; SQLite cannot verify UPDLOCK/HOLDLOCK.")
    actor, lesson, t = playback_setup
    actor_id, lesson_id, engine = actor.id, lesson.public_id, db.engine
    start = start_playback_session(actor, lesson_id, "youtube:abcdefghijk", now=t)
    payload = {
        "playback_session_id": start["session_id"],
        "sequence": 1,
        "media_id": "youtube:abcdefghijk",
        "position_seconds": 0,
        "playback_rate": 1,
        "state": "playing",
    }
    record_playback_heartbeat(actor, lesson_id, payload, now=t)
    barrier = Barrier(2)

    def worker():
        with Session(engine) as session, session.begin():
            user = session.get(User, actor_id)
            barrier.wait(timeout=15)
            return record_playback_heartbeat(
                user,
                lesson_id,
                {**payload, "sequence": 2, "position_seconds": 10},
                session=session,
                now=t + timedelta(seconds=10),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(worker)
        second = pool.submit(worker)
        left, right = first.result(timeout=30), second.result(timeout=30)
    assert left == right
    db.session.expire_all()
    assert db.session.query(LessonProgress).one().seconds_spent == 10
    assert db.session.query(PlaybackReceipt).count() == 2
