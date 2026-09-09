"""Unit tests for configuration loading and environment validation."""

from __future__ import annotations

import pytest

from pwd301.config import (
    BaseConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config_by_name,
)


def test_config_by_name_contains_standard_environments() -> None:
    """Verify that expected environments are registered in config_by_name."""
    assert "development" in config_by_name
    assert "testing" in config_by_name
    assert "production" in config_by_name
    assert config_by_name["development"] is DevelopmentConfig
    assert config_by_name["testing"] is TestingConfig
    assert config_by_name["production"] is ProductionConfig


def test_development_config() -> None:
    """Verify development configuration flags."""
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.TESTING is False
    assert DevelopmentConfig.ENV == "development"
    assert DevelopmentConfig.SESSION_COOKIE_SECURE is False
    assert DevelopmentConfig.WTF_CSRF_ENABLED is True


def test_testing_config() -> None:
    """Verify testing configuration flags."""
    assert TestingConfig.TESTING is True
    assert TestingConfig.DEBUG is False
    assert TestingConfig.ENV == "testing"
    assert TestingConfig.WTF_CSRF_ENABLED is False
    assert TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert TestingConfig.SESSION_COOKIE_SECURE is False


def test_production_config_security_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that ProductionConfig requires valid, secure SECRET_KEY and JWT_SECRET_KEY."""
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.TESTING is False
    assert ProductionConfig.ENV == "production"
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.REMEMBER_COOKIE_SECURE is True

    valid_secret = "super-secret-random-production-token-12345"
    valid_jwt_secret = "super-jwt-secret-random-prod-key-32bytes-long"

    # When SECRET_KEY is default or missing, instantiation must fail
    monkeypatch.setenv("SECRET_KEY", "replace-me-with-a-long-random-secret")
    monkeypatch.setenv("JWT_SECRET_KEY", valid_jwt_secret)
    with pytest.raises(ValueError, match="SECRET_KEY must be set to a secure, random value"):
        ProductionConfig()

    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY must be set to a secure, random value"):
        ProductionConfig()

    # When JWT_SECRET_KEY is default or missing, instantiation must fail
    monkeypatch.setenv("SECRET_KEY", valid_secret)
    monkeypatch.setenv("JWT_SECRET_KEY", "dev-insecure-jwt-secret-change-in-production-min32bytes")
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a secure, random value"):
        ProductionConfig()

    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a secure, random value"):
        ProductionConfig()

    # When proper secrets are supplied, instantiation succeeds
    monkeypatch.setenv("SECRET_KEY", valid_secret)
    monkeypatch.setenv("JWT_SECRET_KEY", valid_jwt_secret)
    prod = ProductionConfig()
    assert prod.ENV == "production"


def test_non_negotiable_invariants_in_config() -> None:
    """Ensure non-negotiable configuration invariants are upheld."""
    # Video limit strictly < 1 GB (1,000,000,000 bytes)
    assert BaseConfig.MAX_VIDEO_BYTES_EXCLUSIVE == 1_000_000_000

    # AI chat inactivity purge timeout is 300 seconds (5 minutes)
    assert BaseConfig.AI_CHAT_INACTIVITY_SECONDS == 300

    # Session cookie must be HTTPOnly and SameSite=Lax for web protection
    assert BaseConfig.SESSION_COOKIE_HTTPONLY is True
    assert BaseConfig.SESSION_COOKIE_SAMESITE == "Lax"

    # Enrollment detail retention is 30 days
    assert BaseConfig.ENROLLMENT_DETAIL_RETENTION_DAYS == 30
