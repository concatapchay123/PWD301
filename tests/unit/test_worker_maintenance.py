from backend.services import background_job_service as jobs


def test_worker_schedules_durable_maintenance_without_hot_loop(app, monkeypatch):
    scheduled = []
    monkeypatch.setattr(jobs, "enqueue_background_job", lambda **kwargs: scheduled.append(kwargs))
    monkeypatch.setattr(jobs, "run_worker_once", lambda: False)
    monkeypatch.setattr(jobs.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(jobs.time, "monotonic", lambda: 0.0)
    with app.app_context():
        jobs.run_worker_loop(max_iterations=3)
    assert len(scheduled) == 2
    assert {job["dedupe_key"] for job in scheduled} == {
        "ai-message-retention",
        "storage-and-playback-receipt-maintenance",
    }
    assert {job["payload"]["scope"] for job in scheduled} == {
        "ai-message-retention",
        "storage-and-playback-receipts",
    }
    assert all(job["job_type"] == "CLEANUP" for job in scheduled)
    assert all(job["run_async"] is False for job in scheduled)
