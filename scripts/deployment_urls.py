"""Validate release targets before elevated database bootstrap touches a server."""

from __future__ import annotations

from sqlalchemy.engine import make_url


def validate_database_targets(settings) -> None:
    database = settings.get("DB_NAME", "PWD301")
    runtime = settings.get("RUNTIME_DATABASE_URL") or settings.get("DATABASE_URL", "")
    migration = settings.get("MIGRATION_DATABASE_URL", "")
    try:
        for raw, expected_user in ((runtime, "pwd301_app"), (migration, "pwd301_migrator")):
            url = make_url(raw)
            if (
                url.drivername != "mssql+pyodbc"
                or url.host != "db"
                or (url.port or 1433) != 1433
                or url.database != database
                or url.username != expected_user
            ):
                raise ValueError
    except Exception:
        raise ValueError(
            "Runtime and migration URLs must target declared DB_NAME at db:1433 with dedicated identities."
        ) from None
