from pwd301.services import background_job_service as jobs


def test_worker_schedules_durable_maintenance_without_hot_loop(app, monkeypatch):
    scheduled = []
    monkeypatch.setattr(jobs, "enqueue_background_job", lambda **kwargs: scheduled.append(kwargs))
    monkeypatch.setattr(jobs, "run_worker_once", lambda: False)
    monkeypatch.setattr(jobs.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(jobs.time, "monotonic", lambda: 0.0)
    with app.app_context():
        jobs.run_worker_loop(max_iterations=3)
    assert len(scheduled) == 1
    assert scheduled[0]["job_type"] == "CLEANUP"
    assert scheduled[0]["run_async"] is False
