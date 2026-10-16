"""Prevent active guidance from restoring the retired approval workflow."""

from pathlib import Path

import pytest

from scripts import repo_check


def test_repository_workflow_authority_and_superseded_plans_are_consistent():
    repo_check.check_workflow_authority()


def test_missing_agent_authority_pointer_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(repo_check, "ROOT", tmp_path)
    (tmp_path / "AGENTS.md").write_text("Use the previous lesson approval process.")
    with pytest.raises(SystemExit):
        repo_check.check_workflow_authority()


def test_retired_plan_has_no_actionable_implementation_steps():
    root = Path(__file__).resolve().parents[2]
    for name in repo_check.SUPERSEDED_WORKFLOW_PLANS:
        text = (root / "docs" / "superpowers" / "plans" / name).read_text(encoding="utf-8")
        assert "SUPERSEDED" in text
        assert "WORKFLOW_SUPERSESSION.md" in text
        assert "### Task" not in text
        assert "Step 1:" not in text


def test_retired_execution_reports_cannot_reinstate_email_gate_or_opt_in_staging():
    root = Path(__file__).resolve().parents[2]
    for path in (root / "execution-reports").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "SUPERSEDED" in text, path.name
        assert "WORKFLOW_SUPERSESSION.md" in text, path.name
        assert "EMAIL_NOT_VERIFIED" not in text, path.name
        assert "is_email_verified == False" not in text, path.name
        assert "| **PASS** |" not in text, path.name
