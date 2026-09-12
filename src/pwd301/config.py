"""Application configuration management for PWD301.

Provides environment-aware configuration objects adhering to the PWD301
architecture specification and non-negotiable invariants.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Ensure local .env file variables are loaded when config module is loaded
load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    ENV: str = "base"
    DEBUG: bool = False
    TESTING: bool = False

    # Security secrets
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY", "dev-insecure-jwt-secret-change-in-production-min32bytes"
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

    # Reverse proxy configuration
    USE_PROXY_FIX: bool = os.environ.get("USE_PROXY_FIX", "true").lower() in ("true", "1", "yes")
    NUM_PROXIES: int = int(os.environ.get("NUM_PROXIES", "1"))

    # Large file streaming / Reverse proxy offload
    USE_X_ACCEL_REDIRECT: bool = os.environ.get("USE_X_ACCEL_REDIRECT", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    ACCEL_REDIRECT_PREFIX: str = os.environ.get("ACCEL_REDIRECT_PREFIX", "/internal-storage")

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
    MAX_CONTENT_LENGTH: int = int(
        os.environ.get("MAX_CONTENT_LENGTH", str(MAX_VIDEO_BYTES_EXCLUSIVE))
    )

    # Retention / lifecycle parameters (in days / seconds)
    ENROLLMENT_DETAIL_RETENTION_DAYS: int = int(
        os.environ.get("ENROLLMENT_DETAIL_RETENTION_DAYS", "30")
    )
    FILE_RECOVERY_DAYS: int = int(os.environ.get("FILE_RECOVERY_DAYS", "30"))
    BACKUP_RETENTION_DAYS: int = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
    AI_CHAT_INACTIVITY_SECONDS: int = int(os.environ.get("AI_CHAT_INACTIVITY_SECONDS", "300"))

    # Gemini & AI configuration
    GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
    GEMINI_TIMEOUT_SECONDS: int = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "8"))

    # Attempt lease and autosave configuration
    ATTEMPT_LEASE_SECONDS: int = int(os.environ.get("ATTEMPT_LEASE_SECONDS", "60"))
    ATTEMPT_HEARTBEAT_SECONDS: int = int(os.environ.get("ATTEMPT_HEARTBEAT_SECONDS", "10"))
    TEXT_AUTOSAVE_DEBOUNCE_MS: int = int(os.environ.get("TEXT_AUTOSAVE_DEBOUNCE_MS", "1500"))

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    def __init__(self) -> None:
        """Synchronize configuration instance with current environment variables."""
        if "SECRET_KEY" in os.environ:
            self.SECRET_KEY = os.environ["SECRET_KEY"]
        if "JWT_SECRET_KEY" in os.environ:
            self.JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
        if "DATABASE_URL" in os.environ:
            self.SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
        if "LOG_LEVEL" in os.environ:
            self.LOG_LEVEL = os.environ["LOG_LEVEL"]
        if "FILE_STORAGE_ROOT" in os.environ:
            self.FILE_STORAGE_ROOT = Path(os.environ["FILE_STORAGE_ROOT"])
        if "FILE_QUARANTINE_ROOT" in os.environ:
            self.FILE_QUARANTINE_ROOT = Path(os.environ["FILE_QUARANTINE_ROOT"])
        if "FILE_BACKUP_ROOT" in os.environ:
            self.FILE_BACKUP_ROOT = Path(os.environ["FILE_BACKUP_ROOT"])
        if "EXPORT_ROOT" in os.environ:
            self.EXPORT_ROOT = Path(os.environ["EXPORT_ROOT"])
        if "MAX_IMAGE_BYTES" in os.environ:
            self.MAX_IMAGE_BYTES = int(os.environ["MAX_IMAGE_BYTES"])
        if "MAX_PDF_BYTES" in os.environ:
            self.MAX_PDF_BYTES = int(os.environ["MAX_PDF_BYTES"])
        if "MAX_DOCX_BYTES" in os.environ:
            self.MAX_DOCX_BYTES = int(os.environ["MAX_DOCX_BYTES"])
        if "MAX_PPTX_BYTES" in os.environ:
            self.MAX_PPTX_BYTES = int(os.environ["MAX_PPTX_BYTES"])
        if "MAX_VIDEO_BYTES_EXCLUSIVE" in os.environ:
            self.MAX_VIDEO_BYTES_EXCLUSIVE = int(os.environ["MAX_VIDEO_BYTES_EXCLUSIVE"])
            self.MAX_CONTENT_LENGTH = self.MAX_VIDEO_BYTES_EXCLUSIVE
        if "MAX_CONTENT_LENGTH" in os.environ:
            self.MAX_CONTENT_LENGTH = int(os.environ["MAX_CONTENT_LENGTH"])
        if "ENROLLMENT_DETAIL_RETENTION_DAYS" in os.environ:
            self.ENROLLMENT_DETAIL_RETENTION_DAYS = int(
                os.environ["ENROLLMENT_DETAIL_RETENTION_DAYS"]
            )
        if "FILE_RECOVERY_DAYS" in os.environ:
            self.FILE_RECOVERY_DAYS = int(os.environ["FILE_RECOVERY_DAYS"])
        if "BACKUP_RETENTION_DAYS" in os.environ:
            self.BACKUP_RETENTION_DAYS = int(os.environ["BACKUP_RETENTION_DAYS"])
        if "AI_CHAT_INACTIVITY_SECONDS" in os.environ:
            self.AI_CHAT_INACTIVITY_SECONDS = int(os.environ["AI_CHAT_INACTIVITY_SECONDS"])
        if "GEMINI_API_KEY" in os.environ:
            self.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if "GEMINI_MODEL_NAME" in os.environ:
            self.GEMINI_MODEL_NAME = os.environ["GEMINI_MODEL_NAME"]
        if "GEMINI_TIMEOUT_SECONDS" in os.environ:
            self.GEMINI_TIMEOUT_SECONDS = int(os.environ["GEMINI_TIMEOUT_SECONDS"])
        if "ATTEMPT_LEASE_SECONDS" in os.environ:
            self.ATTEMPT_LEASE_SECONDS = int(os.environ["ATTEMPT_LEASE_SECONDS"])
        if "ATTEMPT_HEARTBEAT_SECONDS" in os.environ:
            self.ATTEMPT_HEARTBEAT_SECONDS = int(os.environ["ATTEMPT_HEARTBEAT_SECONDS"])
        if "TEXT_AUTOSAVE_DEBOUNCE_MS" in os.environ:
            self.TEXT_AUTOSAVE_DEBOUNCE_MS = int(os.environ["TEXT_AUTOSAVE_DEBOUNCE_MS"])


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    ENV: str = "development"
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    __test__: bool = False
    ENV: str = "testing"
    TESTING: bool = True
    DEBUG: bool = False
    WTF_CSRF_ENABLED: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    SECRET_KEY: str = "test-secret-key-pwd301"
    JWT_SECRET_KEY: str = "test-jwt-secret-key-pwd301-minimum-32-bytes!"
    SESSION_COOKIE_SECURE: bool = False
    USE_PROXY_FIX: bool = False

    def __init__(self) -> None:
        super().__init__()
        # In testing, isolate database to TEST_DATABASE_URL or in-memory SQLite
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
        self.SECRET_KEY = "test-secret-key-pwd301"
        self.JWT_SECRET_KEY = "test-jwt-secret-key-pwd301-minimum-32-bytes!"
        self.WTF_CSRF_ENABLED = False
        self.SESSION_COOKIE_SECURE = False
        self.USE_PROXY_FIX = False


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
        insecure_secrets = {
            "replace-me-with-a-long-random-secret",
            "dev-insecure-secret-key-change-in-production",
            "test-secret-key-pwd301",
        }
        if not secret or secret in insecure_secrets or len(secret) < 16:
            raise ValueError("In production, SECRET_KEY must be set to a secure, random value.")
        jwt_secret = os.environ.get("JWT_SECRET_KEY")
        insecure_jwt_defaults = {
            "dev-insecure-jwt-secret-change-in-production-min32bytes",
            "test-jwt-secret-key-pwd301-minimum-32-bytes!",
        }
        if not jwt_secret or jwt_secret in insecure_jwt_defaults or len(jwt_secret) < 32:
            raise ValueError("In production, JWT_SECRET_KEY must be set to a secure, random value.")
        self.SECRET_KEY = secret
        self.JWT_SECRET_KEY = jwt_secret
        if "SESSION_COOKIE_SECURE" in os.environ:
            self.SESSION_COOKIE_SECURE = os.environ.get(
                "SESSION_COOKIE_SECURE", "true"
            ).lower() in ("true", "1", "yes")
        if "REMEMBER_COOKIE_SECURE" in os.environ:
            self.REMEMBER_COOKIE_SECURE = os.environ.get(
                "REMEMBER_COOKIE_SECURE", "true"
            ).lower() in ("true", "1", "yes")


config_by_name: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
