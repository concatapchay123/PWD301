"""Unit tests for wallet transaction 5-minute timeout and pagination."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import pytest
from werkzeug.security import generate_password_hash

from backend.extensions import db
from backend.models.identity import User
from backend.models.types import utc_now
from backend.models.wallet import UserBalance, WalletTransaction
from backend.services.wallet_service import (
    expire_stale_pending_transactions,
    get_or_create_balance,
    list_transactions_paginated,
)


def test_expire_stale_pending_transactions(app):
    """Verify pending transactions older than 300 seconds are auto-failed."""
    with app.app_context():
        now = utc_now()
        user = User(
            email="test_timeout_user@backend.local",
            display_name="Test Timeout User",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        # 1. Stale pending tx (310 seconds old)
        tx_stale = WalletTransaction(
            user_id=user.id,
            amount=50000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=800001,
            transfer_code_12="PPTQ001A8001",
            description="Stale deposit",
            created_at=now - timedelta(seconds=310),
        )
        # 2. Fresh pending tx (60 seconds old)
        tx_fresh = WalletTransaction(
            user_id=user.id,
            amount=100000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=800002,
            transfer_code_12="PPTQ001A8002",
            description="Fresh deposit",
            created_at=now - timedelta(seconds=60),
        )
        # 3. Completed tx older than 300s (should not be touched)
        tx_completed = WalletTransaction(
            user_id=user.id,
            amount=200000,
            balance_before=0,
            balance_after=200000,
            tx_type="DEPOSIT",
            status="COMPLETED",
            order_code=800003,
            transfer_code_12="PPTQ001A8003",
            description="Completed deposit",
            created_at=now - timedelta(seconds=400),
        )
        db.session.add_all([tx_stale, tx_fresh, tx_completed])
        db.session.commit()

        # Run sweep
        expired_count = expire_stale_pending_transactions(user_id=user.id, timeout_seconds=300, session=db.session)
        assert expired_count == 1

        # Reload
        db.session.refresh(tx_stale)
        db.session.refresh(tx_fresh)
        db.session.refresh(tx_completed)

        assert tx_stale.status == "FAILED"
        meta = json.loads(tx_stale.meta_data)
        assert meta.get("expire_reason") == "timeout_5m_expired"

        assert tx_fresh.status == "PENDING"
        assert tx_completed.status == "COMPLETED"


def test_list_transactions_paginated(app):
    """Verify transactions pagination handles limit, offset, and page counts accurately."""
    with app.app_context():
        now = utc_now()
        user = User(
            email="test_paginated_user@backend.local",
            display_name="Test Paginated User",
            password_hash=generate_password_hash("Secret123456!"),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        # Create 12 transactions
        for i in range(12):
            tx = WalletTransaction(
                user_id=user.id,
                amount=10000 * (i + 1),
                balance_before=0,
                balance_after=10000 * (i + 1),
                tx_type="DEPOSIT",
                status="COMPLETED",
                order_code=900000 + i,
                transfer_code_12=f"PPTQ{user.id:04d}{i:04d}",
                description=f"Tx {i + 1}",
                created_at=now - timedelta(minutes=15 - i),
            )
            db.session.add(tx)
        db.session.commit()

        # Page 1 (5 items)
        p1 = list_transactions_paginated(page=1, page_size=5, user_id=user.id, session=db.session)
        assert p1["total_count"] == 12
        assert p1["total_pages"] == 3
        assert p1["page"] == 1
        assert len(p1["items"]) == 5

        # Page 2 (5 items)
        p2 = list_transactions_paginated(page=2, page_size=5, user_id=user.id, session=db.session)
        assert p2["page"] == 2
        assert len(p2["items"]) == 5
        p1_ids = [item["id"] for item in p1["items"]]
        p2_ids = [item["id"] for item in p2["items"]]
        assert set(p1_ids).isdisjoint(set(p2_ids))

        # Page 3 (2 items)
        p3 = list_transactions_paginated(page=3, page_size=5, user_id=user.id, session=db.session)
        assert p3["page"] == 3
        assert len(p3["items"]) == 2


def test_get_my_wallet_route(app, client):
    """Verify GET /api/payments/wallet/me returns pagination envelope and sweeps stale txs."""
    email = "test_route_user@backend.local"
    password = "StudentPass1234!"

    with app.app_context():
        now = utc_now()
        user = User(
            email=email,
            display_name="Test Route User",
            password_hash=generate_password_hash(password),
            status="ACTIVE",
        )
        db.session.add(user)
        db.session.flush()

        from backend.models.identity import Role, UserRole
        role_student = db.session.query(Role).filter_by(code="STUDENT").first()
        if not role_student:
            role_student = Role(code="STUDENT", name="Student")
            db.session.add(role_student)
            db.session.flush()
        db.session.add(UserRole(user_id=user.id, role_id=role_student.id))
        db.session.flush()

        # Stale transaction
        tx_stale = WalletTransaction(
            user_id=user.id,
            amount=50000,
            balance_before=0,
            balance_after=0,
            tx_type="DEPOSIT",
            status="PENDING",
            order_code=950001,
            transfer_code_12="PPTQ001A9501",
            description="Stale deposit for route test",
            created_at=now - timedelta(seconds=350),
        )
        db.session.add(tx_stale)
        db.session.commit()

        from tests.conftest import login_web_user
        login_web_user(client, user)

    res = client.get("/api/payments/wallet/me?page=1&page_size=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 5
    assert data["pagination"]["total_count"] == 1
    assert len(data["recent_transactions"]) == 1
    assert data["recent_transactions"][0]["status"] == "FAILED"
