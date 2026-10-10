from pwd301.extensions import db
from pwd301.services.background_job_service import enqueue_background_job


def test_terminal_job_does_not_block_future_deduplicated_job(app):
    with app.app_context():
        first = enqueue_background_job("EMAIL", dedupe_key="email-outbox-drain", run_async=False)
        first.status = "SUCCEEDED"
        db.session.commit()
        second = enqueue_background_job("EMAIL", dedupe_key="email-outbox-drain", run_async=False)
        db.session.commit()
        assert second.id != first.id
        assert first.status == "SUCCEEDED"
        assert first.dedupe_key is None
        assert second.dedupe_key == "email-outbox-drain"
