"""Identity domain models for PWD301.

Implements canonical schema tables from sql/001_identity.sql:
- users
- roles
- user_roles
- auth_sessions
- jwt_token_grants
- user_security_tokens
- instructor_applications
- security_events
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import sqlalchemy as sa
from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy.orm import relationship

from pwd301.extensions import Base, db
from pwd301.models.types import (
    GUID,
    BigIntPK,
    Binary32,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class User(Base, UserMixin):
    """User account model mapping to canonical 'users' table."""

    __tablename__ = "users"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    email = db.Column(sa.Unicode(320), nullable=False)
    email_normalized = db.Column(
        sa.Unicode(320),
        sa.Computed("LOWER(LTRIM(RTRIM(email)))", persisted=True),
        unique=True,
    )
    password_hash = db.Column(sa.Unicode(255), nullable=False)
    display_name = db.Column(sa.Unicode(150), nullable=False)
    avatar_file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "file_assets.id",
            name="fk_users_avatar_file_asset_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    status = db.Column(
        sa.String(24),
        nullable=False,
        default="ACTIVE",
        server_default=sa.text("'ACTIVE'"),
    )
    auth_version = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    email_verified_at = db.Column(UTCDateTime, nullable=True)
    suspended_at = db.Column(UTCDateTime, nullable=True)
    suspension_reason = db.Column(sa.Unicode(500), nullable=True)
    anonymized_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('ACTIVE','SUSPENDED','DEACTIVATED','ANONYMIZED')",
            name="ck_users_1",
        ),
        sa.CheckConstraint("auth_version >= 1", name="ck_users_2"),
        sa.Index("ix_users_status", "status", "id"),
    )

    # Relationships
    roles = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.id == foreign(UserRole.user_id)",
        secondaryjoin="Role.id == foreign(UserRole.role_id)",
        back_populates="users",
        overlaps="user_role_links,role_user_links,user,role",
    )
    courses = relationship(
        "Course",
        back_populates="owner_instructor",
        foreign_keys="Course.owner_instructor_id",
    )
    enrollments = relationship(
        "Enrollment",
        back_populates="student",
        foreign_keys="Enrollment.student_user_id",
    )

    @property
    def is_active(self) -> bool:
        """Return True if user account is active and not suspended."""
        return self.status == "ACTIVE" and self.suspended_at is None

    def get_id(self) -> str:
        """Return user primary key as string for Flask-Login session management."""
        return str(self.id)

    @property
    def role_codes(self) -> set[str]:
        """Return the set of role code strings assigned to this user."""
        return {r.code for r in self.roles}

    @property
    def is_admin(self) -> bool:
        """Return True if user has the ADMIN role."""
        return "ADMIN" in self.role_codes

    @property
    def is_instructor(self) -> bool:
        """Return True if user has INSTRUCTOR or ADMIN role (cumulative capability)."""
        return bool(self.role_codes & {"INSTRUCTOR", "ADMIN"})

    @property
    def is_student(self) -> bool:
        """Return True if user has STUDENT, INSTRUCTOR, or ADMIN role."""
        return bool(self.role_codes & {"STUDENT", "INSTRUCTOR", "ADMIN"})

    @property
    def primary_role(self) -> str:
        """Return the highest canonical role of the user (ADMIN > INSTRUCTOR > STUDENT)."""
        codes = self.role_codes
        if "ADMIN" in codes:
            return "ADMIN"
        if "INSTRUCTOR" in codes:
            return "INSTRUCTOR"
        if "STUDENT" in codes:
            return "STUDENT"
        return "STUDENT"

    def has_role(self, role_code: str) -> bool:
        """Check if user has a specific role, respecting cumulative hierarchy.

        Per AUTH-002:
        - ADMIN inherits INSTRUCTOR and STUDENT capabilities.
        - INSTRUCTOR inherits STUDENT capability.
        """
        norm_code = role_code.strip().upper()
        codes = self.role_codes
        if norm_code == "STUDENT":
            return bool(codes & {"STUDENT", "INSTRUCTOR", "ADMIN"})
        if norm_code == "INSTRUCTOR":
            return bool(codes & {"INSTRUCTOR", "ADMIN"})
        if norm_code == "ADMIN":
            return "ADMIN" in codes
        return norm_code in codes

    def has_any_role(self, *role_codes: str) -> bool:
        """Check if user has at least one of the specified roles."""
        return any(self.has_role(code) for code in role_codes)

    def has_all_roles(self, *role_codes: str) -> bool:
        """Check if user has all of the specified roles."""
        return all(self.has_role(code) for code in role_codes)

    def verify_password(self, password: str) -> bool:
        """Verify raw password against stored password hash."""
        if not password or not self.password_hash:
            return False
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)


class AnonymousUser(AnonymousUserMixin):
    """Anonymous user representation for unauthenticated guests.

    Implements safe authorization check methods that consistently return False,
    preventing AttributeError in templates or decorators.
    """

    @property
    def role_codes(self) -> set[str]:
        return set()

    @property
    def is_admin(self) -> bool:
        return False

    @property
    def is_instructor(self) -> bool:
        return False

    @property
    def is_student(self) -> bool:
        return False

    @property
    def primary_role(self) -> str:
        return ""

    def has_role(self, role_code: str) -> bool:
        return False

    def has_any_role(self, *role_codes: str) -> bool:
        return False

    def has_all_roles(self, *role_codes: str) -> bool:
        return False


class Role(Base):
    """System role model mapping to canonical 'roles' table."""

    __tablename__ = "roles"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    code = db.Column(sa.String(32), nullable=False, unique=True)
    name = db.Column(sa.Unicode(100), nullable=False)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint("code IN ('STUDENT','INSTRUCTOR','ADMIN')", name="ck_roles_1"),
    )

    users = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == foreign(UserRole.role_id)",
        secondaryjoin="User.id == foreign(UserRole.user_id)",
        back_populates="roles",
        overlaps="user_role_links,role_user_links,user,role",
    )


class UserRole(Base):
    """Junction model mapping to canonical 'user_roles' table."""

    __tablename__ = "user_roles"

    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_user_roles_user_id"),
        primary_key=True,
    )
    role_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("roles.id", name="fk_user_roles_role_id"),
        primary_key=True,
    )
    assigned_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    assigned_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_user_roles_assigned_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    assignment_reason = db.Column(sa.Unicode(500), nullable=True)

    __table_args__ = (sa.Index("ix_user_roles_role", "role_id", "user_id"),)

    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref=sa.orm.backref(
            "user_role_links", cascade="all, delete-orphan", overlaps="roles,users"
        ),
        overlaps="roles,users",
    )
    role = relationship(
        "Role",
        foreign_keys=[role_id],
        backref=sa.orm.backref(
            "role_user_links", cascade="all, delete-orphan", overlaps="roles,users"
        ),
        overlaps="roles,users",
    )
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])


class AuthSession(Base):
    """Server-side web authentication session mapping to canonical 'auth_sessions' table."""

    __tablename__ = "auth_sessions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    session_key_hash = db.Column(Binary32, nullable=False, unique=True)
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_auth_sessions_user_id"),
        nullable=False,
    )
    auth_version = db.Column(sa.Integer, nullable=False)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    last_seen_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    expires_at = db.Column(UTCDateTime, nullable=False)
    revoked_at = db.Column(UTCDateTime, nullable=True)
    reauthenticated_at = db.Column(UTCDateTime, nullable=True)
    ip_address = db.Column(sa.String(45), nullable=True)
    user_agent_hash = db.Column(Binary32, nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("expires_at > created_at", name="ck_auth_sessions_1"),
        sa.Index(
            "ix_auth_sessions_user_active",
            "user_id",
            "expires_at",
            mssql_where=sa.text("revoked_at IS NULL"),
            sqlite_where=sa.text("revoked_at IS NULL"),
        ),
    )

    user = relationship("User", foreign_keys=[user_id], backref="auth_sessions")


class JwtTokenGrant(Base):
    """REST API JWT token grant mapping to canonical 'jwt_token_grants' table."""

    __tablename__ = "jwt_token_grants"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    jti = db.Column(GUID, nullable=False, unique=True, default=uuid.uuid4)
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_jwt_token_grants_user_id"),
        nullable=False,
    )
    session_family_id = db.Column(
        GUID,
        nullable=False,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    auth_version = db.Column(sa.Integer, nullable=False)
    token_type = db.Column(sa.String(16), nullable=False)
    issued_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    expires_at = db.Column(UTCDateTime, nullable=False)
    revoked_at = db.Column(UTCDateTime, nullable=True)
    replaced_by_jti = db.Column(GUID, nullable=True)
    token_hash = db.Column(Binary32, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("token_type IN ('ACCESS','REFRESH')", name="ck_jwt_token_grants_1"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_jwt_token_grants_2"),
        sa.Index(
            "ix_jwt_user_active",
            "user_id",
            "expires_at",
            mssql_where=sa.text("revoked_at IS NULL"),
            sqlite_where=sa.text("revoked_at IS NULL"),
        ),
        sa.Index("ix_jwt_family", "session_family_id", "issued_at"),
    )

    user = relationship("User", foreign_keys=[user_id], backref="jwt_token_grants")


class UserSecurityToken(Base):
    """Single-use verification token mapping to canonical 'user_security_tokens' table."""

    __tablename__ = "user_security_tokens"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_user_security_tokens_user_id"),
        nullable=False,
    )
    purpose = db.Column(sa.String(32), nullable=False)
    token_hash = db.Column(Binary32, nullable=False, unique=True)
    pending_email = db.Column(sa.Unicode(320), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    expires_at = db.Column(UTCDateTime, nullable=False)
    consumed_at = db.Column(UTCDateTime, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "purpose IN ('EMAIL_VERIFY','EMAIL_CHANGE','PASSWORD_RESET')",
            name="ck_user_security_tokens_1",
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_user_security_tokens_2"),
        sa.Index("ix_security_tokens_user_purpose", "user_id", "purpose", "expires_at"),
    )

    user = relationship("User", foreign_keys=[user_id], backref="security_tokens")


class InstructorApplication(Base):
    """Instructor application workflow model mapping to 'instructor_applications' table."""

    __tablename__ = "instructor_applications"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    applicant_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_instructor_applications_applicant_user_id"),
        nullable=False,
    )
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    application_note = db.Column(sa.Unicode(2000), nullable=True)
    reviewed_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_instructor_applications_reviewed_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    review_reason = db.Column(sa.Unicode(1000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    reviewed_at = db.Column(UTCDateTime, nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('PENDING','APPROVED','REJECTED','CANCELLED')",
            name="ck_instructor_applications_1",
        ),
        sa.Index("ix_instructor_app_status", "status", "created_at"),
    )

    applicant = relationship(
        "User",
        foreign_keys=[applicant_user_id],
        backref="instructor_applications",
    )
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])

    @property
    def parsed_details(self) -> dict[str, Any]:
        """Parse structured application information from JSON note, fallback to raw dict."""
        if not self.application_note:
            return {}
        try:
            val = json.loads(self.application_note)
            if isinstance(val, dict):
                return val
        except (json.JSONDecodeError, TypeError):
            pass
        return {"raw_note": self.application_note}

    @property
    def status_label_vi(self) -> str:
        """Return Vietnamese user-friendly status label."""
        labels = {
            "PENDING": "Chờ duyệt",
            "APPROVED": "Đã duyệt",
            "REJECTED": "Đã từ chối",
            "CANCELLED": "Đã hủy",
        }
        return labels.get(self.status, self.status)

    @property
    def status_badge_class(self) -> str:
        """Return CSS class for badge styling."""
        classes = {
            "PENDING": "badge-warning bg-amber-subtle text-amber-800",
            "APPROVED": "badge-success bg-emerald-subtle text-emerald-800",
            "REJECTED": "badge-danger bg-rose-subtle text-rose-800",
            "CANCELLED": "badge-secondary bg-slate-subtle text-slate-700",
        }
        return classes.get(self.status, "badge-secondary")


class SecurityEvent(Base):
    """Security audit and rate-limiting event model mapping to 'security_events' table."""

    __tablename__ = "security_events"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_security_events_user_id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type = db.Column(sa.String(64), nullable=False)
    severity = db.Column(sa.String(16), nullable=False)
    action_taken = db.Column(sa.String(64), nullable=False)
    risk_score = db.Column(sa.Numeric(5, 2), nullable=True)
    input_hash = db.Column(Binary32, nullable=True)
    ip_address = db.Column(sa.String(45), nullable=True)
    correlation_id = db.Column(
        GUID,
        nullable=False,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    metadata_json = db.Column(NVarCharMax, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "severity IN ('INFO','WARN','HIGH','CRITICAL')",
            name="ck_security_events_1",
        ),
        sa.CheckConstraint(
            "action_taken IN ('ALLOW','BLOCK','REVOKE','QUARANTINE','ALERT')",
            name="ck_security_events_2",
        ),
        sa.CheckConstraint(
            "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)",
            name="ck_security_events_3",
        ),
        sa.CheckConstraint(
            "metadata_json IS NULL OR ISJSON(metadata_json)=1",
            name="ck_security_events_4",
        ),
        sa.Index("ix_security_events_type_time", "event_type", "created_at"),
        sa.Index("ix_security_events_user_time", "user_id", "created_at"),
    )

    user = relationship("User", foreign_keys=[user_id], backref="security_events")
