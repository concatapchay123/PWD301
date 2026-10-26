"""Wallet and Payment transaction models for PWD301.

Implements tables:
- user_balances: Digital wallet balances for registered users.
- wallet_transactions: Immutable financial ledger for deposits, course purchases,
  refunds, and admin revokes.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from backend.extensions import Base, db
from backend.models.types import (
    GUID,
    BigIntPK,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class UserBalance(Base):
    """User account balance model mapping to 'user_balances' table."""

    __tablename__ = "user_balances"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_user_balances_user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    balance = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    currency = db.Column(
        sa.String(10),
        nullable=False,
        default="VND",
        server_default=sa.text("'VND'"),
    )
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    user = relationship("User", backref=db.backref("balance_record", uselist=False))

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "balance": int(self.balance or 0),
            "currency": self.currency,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WalletTransaction(Base):
    """Financial ledger transactions mapping to 'wallet_transactions' table."""

    __tablename__ = "wallet_transactions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_wallet_transactions_user_id"),
        nullable=False,
        index=True,
    )
    amount = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
    )
    balance_before = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
    )
    balance_after = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
    )
    # tx_type: 'DEPOSIT', 'COURSE_PURCHASE', 'REVOKE', 'REFUND'
    tx_type = db.Column(
        sa.String(32),
        nullable=False,
        index=True,
    )
    # status: 'PENDING', 'COMPLETED', 'REVOKED', 'FAILED'
    status = db.Column(
        sa.String(32),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
        index=True,
    )
    payment_ref = db.Column(sa.Unicode(100), nullable=True)
    order_code = db.Column(sa.BigInteger, nullable=True, unique=True, index=True)
    # Required 12-char transfer code: PPTQ + [User 4 chars] + [Tx 4 chars]
    transfer_code_12 = db.Column(sa.String(20), nullable=True, index=True)
    target_course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_wallet_transactions_course_id"),
        nullable=True,
        index=True,
    )
    description = db.Column(sa.Unicode(255), nullable=True)
    meta_data = db.Column(NVarCharMax, nullable=True)
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
    created_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_wallet_transactions_created_by"),
        nullable=True,
    )

    user = relationship("User", foreign_keys=[user_id])
    target_course = relationship("Course", foreign_keys=[target_course_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    @property
    def transfer_code(self) -> str | None:
        return self.transfer_code_12

    def to_dict(self) -> dict[str, Any]:
        meta = None
        if self.meta_data:
            try:
                meta = json.loads(self.meta_data)
            except Exception:
                meta = self.meta_data

        return {
            "id": self.id,
            "public_id": str(self.public_id),
            "user_id": self.user_id,
            "user_name": self.user.display_name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "amount": int(self.amount or 0),
            "balance_before": int(self.balance_before or 0),
            "balance_after": int(self.balance_after or 0),
            "tx_type": self.tx_type,
            "status": self.status,
            "payment_ref": self.payment_ref,
            "order_code": self.order_code,
            "transfer_code_12": self.transfer_code_12,
            "transfer_code": self.transfer_code_12,
            "target_course_id": self.target_course_id,
            "target_course_title": self.target_course.title if self.target_course else None,
            "description": self.description,
            "metadata": meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_user_id": self.created_by_user_id,
            "created_by_name": self.created_by.display_name if self.created_by else None,
        }
