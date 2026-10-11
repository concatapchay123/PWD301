"""Explicit, one-shot SQL Server release bootstrap; runtime containers never migrate."""

from __future__ import annotations

import os
import re
import subprocess

import sqlalchemy as sa
from sqlalchemy.engine import URL
from scripts.deployment_urls import validate_database_targets


def bootstrap() -> None:
    validate_database_targets(os.environ)
    database = os.environ.get("DB_NAME", "PWD301")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", database):
        raise ValueError("Invalid deployment database name.")
    password_names = ("DB_PASSWORD", "APP_DB_PASSWORD", "MIGRATION_DB_PASSWORD")
    if any(len(os.environ.get(name, "")) < 12 for name in password_names):
        raise ValueError(
            "Supply distinct strong database bootstrap, application and migrator secrets."
        )
    secrets = [os.environ[name] for name in password_names]
    if len(set(secrets)) != len(secrets):
        raise ValueError(
            "Database bootstrap, application and migrator credentials must be distinct."
        )
    master = URL.create(
        "mssql+pyodbc",
        username="sa",
        password=secrets[0],
        host="db",
        port=1433,
        database="master",
        query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
    )
    engine = sa.create_engine(master, isolation_level="AUTOCOMMIT", hide_parameters=True)
    try:
        with engine.connect() as connection:
            exists = connection.execute(sa.text("SELECT DB_ID(:name)"), {"name": database}).scalar()
            if exists is None:
                connection.exec_driver_sql(
                    f"CREATE DATABASE [{database}] COLLATE Vietnamese_100_CI_AS"
                )
            for login, password in (("pwd301_app", secrets[1]), ("pwd301_migrator", secrets[2])):
                if (
                    connection.execute(sa.text("SELECT SUSER_ID(:name)"), {"name": login}).scalar()
                    is None
                ):
                    escaped = password.replace("'", "''")
                    connection.exec_driver_sql(f"CREATE LOGIN [{login}] WITH PASSWORD=N'{escaped}'")
        with engine.connect() as connection:
            connection.exec_driver_sql(f"USE [{database}]")
            for login in ("pwd301_app", "pwd301_migrator"):
                connection.exec_driver_sql(
                    f"IF USER_ID(N'{login}') IS NULL CREATE USER [{login}] FOR LOGIN [{login}]"
                )
            connection.exec_driver_sql("ALTER ROLE db_owner ADD MEMBER [pwd301_migrator]")
            connection.exec_driver_sql("ALTER ROLE db_datareader ADD MEMBER [pwd301_app]")
            connection.exec_driver_sql("ALTER ROLE db_datawriter ADD MEMBER [pwd301_app]")
            connection.exec_driver_sql("GRANT EXECUTE TO [pwd301_app]")
            connection.exec_driver_sql("GRANT BACKUP DATABASE TO [pwd301_app]")
    except Exception:
        # Driver exceptions can contain password-bearing DDL. Never print the exception.
        raise RuntimeError(
            "Release database bootstrap failed; consult protected database diagnostics."
        ) from None
    finally:
        engine.dispose()
    subprocess.run(["flask", "db", "upgrade"], check=True)
    subprocess.run(["flask", "seed-baseline"], check=True)


if __name__ == "__main__":
    bootstrap()
