"""Integration tests for baseline database seeding.

Verifies role initialization, root administrator setup, role assignments,
idempotency, and CLI commands.
"""

from __future__ import annotations

from werkzeug.security import check_password_hash

from pwd301.extensions import db
from pwd301.models.identity import Role, User, UserRole
from pwd301.seeds.baseline import seed_baseline


def test_seed_baseline_success(app):
    """Verify seed_baseline populates initial roles and root administrator."""
    with app.app_context():
        summary = seed_baseline(db.session)

        assert set(summary["roles_created"]) == {"STUDENT", "INSTRUCTOR", "ADMIN"}
        assert summary["roles_existing"] == []
        assert summary["admin_created"] is True
        assert set(summary["admin_roles_assigned"]) == {"STUDENT", "INSTRUCTOR", "ADMIN"}

        # Verify roles in database
        roles = db.session.query(Role).all()
        assert len(roles) == 3
        role_codes = {r.code for r in roles}
        assert role_codes == {"STUDENT", "INSTRUCTOR", "ADMIN"}

        # Verify root admin in database
        admin = db.session.query(User).filter(User.email == "admin@pwd301.local").one_or_none()
        assert admin is not None
        assert admin.status == "ACTIVE"
        assert admin.display_name == "System Administrator"
        assert check_password_hash(admin.password_hash, "Admin@123456")
        assert admin.email_verified_at is not None

        # Verify admin has all 3 roles assigned
        admin_roles = {r.code for r in admin.roles}
        assert admin_roles == {"STUDENT", "INSTRUCTOR", "ADMIN"}


def test_seed_baseline_idempotency(app):
    """Verify seed_baseline can be safely executed multiple times without duplicating data."""
    with app.app_context():
        # First execution
        res1 = seed_baseline(db.session)
        assert res1["admin_created"] is True

        # Second execution
        res2 = seed_baseline(db.session)
        assert res2["roles_created"] == []
        assert set(res2["roles_existing"]) == {"STUDENT", "INSTRUCTOR", "ADMIN"}
        assert res2["admin_created"] is False
        assert res2["admin_roles_assigned"] == []

        # Verify counts remain exact
        assert db.session.query(Role).count() == 3
        assert db.session.query(User).count() == 1
        assert db.session.query(UserRole).count() == 3


def test_seed_baseline_cli_commands(app, runner):
    """Verify Flask CLI seed commands execute cleanly."""
    with app.app_context():
        # Test 'flask seed-baseline'
        res1 = runner.invoke(args=["seed-baseline"])
        assert res1.exit_code == 0
        assert "Done!" in res1.output
        assert "Roles created:" in res1.output
        assert "Admin created: True" in res1.output

        # Test 'flask seed baseline' (group command, idempotent)
        res2 = runner.invoke(args=["seed", "baseline"])
        assert res2.exit_code == 0
        assert "Done!" in res2.output
        assert "Admin created: False" in res2.output
        assert "Roles created: []" in res2.output


def test_seed_baseline_custom_env_vars(app, monkeypatch):
    """Verify seed_baseline respects custom admin environment variables."""
    custom_email = "custom_admin@pwd301.local"
    custom_name = "Chief Security Officer"
    custom_pass = "CustomSecured@987654"

    monkeypatch.setenv("ADMIN_EMAIL", f"  {custom_email}  ")
    monkeypatch.setenv("ADMIN_DISPLAY_NAME", f"  {custom_name}  ")
    monkeypatch.setenv("ADMIN_PASSWORD", custom_pass)

    with app.app_context():
        summary = seed_baseline(db.session)
        assert summary["admin_created"] is True

        admin = (
            db.session.query(User)
            .filter(User.email_normalized == custom_email.lower())
            .one_or_none()
        )
        assert admin is not None
        assert admin.display_name == custom_name
        assert check_password_hash(admin.password_hash, custom_pass)
        assert admin.status == "ACTIVE"
        assert admin.email_verified_at is not None

        admin_roles = {r.code for r in admin.roles}
        assert admin_roles == {"STUDENT", "INSTRUCTOR", "ADMIN"}


def test_seed_baseline_partial_role_recovery(app):
    """Verify seed_baseline recovers when admin exists but lacks cumulative roles."""
    with app.app_context():
        # First execution to set up initial state
        seed_baseline(db.session)

        # Intentionally strip INSTRUCTOR and ADMIN roles from root admin
        admin = db.session.query(User).filter(User.email == "admin@pwd301.local").one()
        admin_id = admin.id

        instructor_role = db.session.query(Role).filter(Role.code == "INSTRUCTOR").one()
        admin_role = db.session.query(Role).filter(Role.code == "ADMIN").one()

        db.session.query(UserRole).filter(
            UserRole.user_id == admin_id,
            UserRole.role_id.in_([instructor_role.id, admin_role.id]),
        ).delete(synchronize_session=False)
        db.session.commit()

        # Verify only STUDENT role remains
        db.session.expire_all()
        assert {r.code for r in admin.roles} == {"STUDENT"}

        # Re-run seed_baseline: should heal missing roles without recreating admin
        heal_summary = seed_baseline(db.session)
        assert heal_summary["admin_created"] is False
        assert set(heal_summary["admin_roles_assigned"]) == {"INSTRUCTOR", "ADMIN"}

        # Verify all 3 cumulative roles are restored
        db.session.expire_all()
        assert {r.code for r in admin.roles} == {"STUDENT", "INSTRUCTOR", "ADMIN"}
        assert db.session.query(UserRole).filter(UserRole.user_id == admin_id).count() == 3
