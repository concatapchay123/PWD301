"""Baseline database seeding script for PWD301.

Seeds canonical system roles (STUDENT, INSTRUCTOR, ADMIN) and an initial root
administrator account adhering strictly to project invariants:
- Email unique login identifier
- Role combination hierarchy: STUDENT + INSTRUCTOR + ADMIN for Administrator
- Full idempotency (safe to execute repeatedly without duplicating data or failing)
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import generate_password_hash

from pwd301.models.identity import Role, User, UserRole
from pwd301.models.types import utc_now

# Canonical baseline system roles
BASELINE_ROLES: list[dict[str, str]] = [
    {"code": "STUDENT", "name": "Student"},
    {"code": "INSTRUCTOR", "name": "Instructor"},
    {"code": "ADMIN", "name": "System Administrator"},
]

DEFAULT_ADMIN_EMAIL: str = "admin@pwd301.local"
DEFAULT_ADMIN_NAME: str = "System Administrator"
DEFAULT_ADMIN_PASSWORD: str = "Admin@123456"


def seed_baseline(session: Session | scoped_session[Any]) -> dict[str, Any]:
    """Seed baseline roles and root administrator into the database.

    Args:
        session: Active SQLAlchemy database session.

    Returns:
        Summary dictionary of created vs existing records.
    """
    summary: dict[str, Any] = {
        "roles_created": [],
        "roles_existing": [],
        "admin_created": False,
        "admin_roles_assigned": [],
    }

    # 1. Seed canonical roles
    role_map: dict[str, Role] = {}
    for role_data in BASELINE_ROLES:
        existing_role = session.query(Role).filter(Role.code == role_data["code"]).one_or_none()
        if existing_role is None:
            role = Role(code=role_data["code"], name=role_data["name"])
            session.add(role)
            session.flush()
            role_map[role.code] = role
            summary["roles_created"].append(role.code)
        else:
            role_map[existing_role.code] = existing_role
            summary["roles_existing"].append(existing_role.code)

    # 2. Seed root administrator
    admin_email = os.environ.get("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip()
    admin_name = os.environ.get("ADMIN_DISPLAY_NAME", DEFAULT_ADMIN_NAME).strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    admin_user = (
        session.query(User).filter(User.email_normalized == admin_email.lower()).one_or_none()
    )
    if admin_user is None:
        admin_user = User(
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            display_name=admin_name,
            status="ACTIVE",
            auth_version=1,
            email_verified_at=utc_now(),
        )
        session.add(admin_user)
        session.flush()
        summary["admin_created"] = True

    # 3. Assign role hierarchy (STUDENT + INSTRUCTOR + ADMIN)
    for code in ["STUDENT", "INSTRUCTOR", "ADMIN"]:
        target_role = role_map.get(code)
        if target_role is None:
            continue

        existing_link = (
            session.query(UserRole)
            .filter(
                UserRole.user_id == admin_user.id,
                UserRole.role_id == target_role.id,
            )
            .one_or_none()
        )
        if existing_link is None:
            link = UserRole(
                user_id=admin_user.id,
                role_id=target_role.id,
                assigned_by_user_id=admin_user.id,
                assignment_reason="Baseline root administrator initialization",
            )
            session.add(link)
            summary["admin_roles_assigned"].append(code)

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return summary
