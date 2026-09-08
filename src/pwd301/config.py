"""Application configuration management for PWD301.

Provides environment-aware configuration objects adhering to the PWD301
architecture specification and non-negotiable invariants.
"""

from __future__ import annotations

import os
from pathlib import Path


class BaseConfig:
    """Base configuration shared across all environments."""

    ENV: str = "base"
    DEBUG: bool = False
    TESTING: bool = False

    # Security secrets
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY", "dev-insecure-jwt-secret-change-in-production"
    )

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        "sqlite:///instance/pwd301_dev.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # CSRF Protection
    WTF_CSRF_ENABLED: bool = True

    # Session & Cookie Security (Web UI session authentication)
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_HTTPONLY: bool = True
    REMEMBER_COOKIE_SAMESITE: str = "Lax"
    REMEMBER_COOKIE_SECURE: bool = False

    # Storage paths
    FILE_STORAGE_ROOT: Path = Path(os.environ.get("FILE_STORAGE_ROOT", "./storage"))
    FILE_QUARANTINE_ROOT: Path = Path(os.environ.get("FILE_QUARANTINE_ROOT", "./quarantine"))
    FILE_BACKUP_ROOT: Path = Path(os.environ.get("FILE_BACKUP_ROOT", "./backups"))
    EXPORT_ROOT: Path = Path(os.environ.get("EXPORT_ROOT", "./exports"))

    # File upload limits (Current business invariant: video strictly < 1 GB)
    MAX_IMAGE_BYTES: int = int(os.environ.get("MAX_IMAGE_BYTES", "10000000"))
    MAX_PDF_BYTES: int = int(os.environ.get("MAX_PDF_BYTES", "50000000"))
    MAX_DOCX_BYTES: int = int(os.environ.get("MAX_DOCX_BYTES", "50000000"))
    MAX_PPTX_BYTES: int = int(os.environ.get("MAX_PPTX_BYTES", "100000000"))
    MAX_VIDEO_BYTES_EXCLUSIVE: int = int(os.environ.get("MAX_VIDEO_BYTES_EXCLUSIVE", "1000000000"))

    # Retention / lifecycle parameters (in days / seconds)
    ENROLLMENT_DETAIL_RETENTION_DAYS: int = int(
        os.environ.get("ENROLLMENT_DETAIL_RETENTION_DAYS", "30")
    )
    FILE_RECOVERY_DAYS: int = int(os.environ.get("FILE_RECOVERY_DAYS", "30"))
    AI_CHAT_INACTIVITY_SECONDS: int = int(os.environ.get("AI_CHAT_INACTIVITY_SECONDS", "300"))

    # Attempt lease and autosave configuration
    ATTEMPT_LEASE_SECONDS: int = int(os.environ.get("ATTEMPT_LEASE_SECONDS", "30"))
    ATTEMPT_HEARTBEAT_SECONDS: int = int(os.environ.get("ATTEMPT_HEARTBEAT_SECONDS", "10"))
    TEXT_AUTOSAVE_DEBOUNCE_MS: int = int(os.environ.get("TEXT_AUTOSAVE_DEBOUNCE_MS", "1500"))

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    ENV: str = "development"
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    ENV: str = "testing"
    TESTING: bool = True
    DEBUG: bool = False
    WTF_CSRF_ENABLED: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    SECRET_KEY: str = "test-secret-key-pwd301"
    JWT_SECRET_KEY: str = "test-jwt-secret-key-pwd301"
    SESSION_COOKIE_SECURE: bool = False


class ProductionConfig(BaseConfig):
    """Production environment configuration with hardened security defaults."""

    ENV: str = "production"
    DEBUG: bool = False
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True

    def __init__(self) -> None:
        super().__init__()
        secret = os.environ.get("SECRET_KEY")
        if not secret or secret == "replace-me-with-a-long-random-secret":
            raise ValueError("In production, SECRET_KEY must be set to a secure, random value.")


config_by_name: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
