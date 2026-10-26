"""Wait for SQL Server database to become ready and initialize the target database if missing.

Supports SQL Server (via ODBC Driver 18) and handles retry backoff.
Safe for multi-container Docker startup loops.
"""

from __future__ import annotations

import os
import re
import sys
import time
from urllib.parse import parse_qs

import sqlalchemy as sa


def parse_db_params() -> dict[str, str]:
    """Parse database connection parameters from DATABASE_URL or individual env vars."""
    db_url = os.environ.get("DATABASE_URL", "")

    # Default fallback values
    params = {
        "user": os.environ.get("DB_USER", "sa"),
        "password": os.environ.get("DB_PASSWORD", "AdminStrongPassw0rd!"),
        "host": os.environ.get("DB_HOST", "db"),
        "port": os.environ.get("DB_PORT", "1433"),
        "database": os.environ.get("DB_NAME", "PWD301"),
        "driver": "ODBC Driver 18 for SQL Server",
    }

    if db_url.startswith("mssql"):
        # Parse connection URL
        match = re.search(
            r"mssql\+pyodbc://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([^?]+)(?:\?(.*))?",
            db_url,
        )
        if match:
            user, password, host, port, database, query = match.groups()
            params["user"] = user
            params["password"] = password
            params["host"] = host
            if port:
                params["port"] = port
            params["database"] = database.strip("/")
            if query:
                q_dict = parse_qs(query)
                if "driver" in q_dict:
                    params["driver"] = q_dict["driver"][0]
    return params


def wait_for_database(timeout_seconds: int = 90, interval_seconds: float = 2.0) -> bool:
    """Wait for database server to accept connections and ensure target database exists."""
    db_url = os.environ.get("DATABASE_URL", "")

    # If using SQLite, simply verify file path directory and return
    if db_url.startswith("sqlite"):
        print("[WAIT-FOR-DB] SQLite database detected. Ready.")
        return True

    params = parse_db_params()
    host = params["host"]
    port = params["port"]
    user = params["user"]
    password = params["password"]
    database = params["database"]
    driver = params["driver"].replace(" ", "+")

    # Connection URL to 'master' database for readiness probe and DB creation
    master_url = (
        f"mssql+pyodbc://{user}:{password}@{host}:{port}/master"
        f"?driver={driver}&TrustServerCertificate=yes"
    )

    target_url = (
        f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}"
        f"?driver={driver}&TrustServerCertificate=yes"
    )

    print(f"[WAIT-FOR-DB] Waiting for SQL Server at {host}:{port} (timeout: {timeout_seconds}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            # 1. Connect to master database
            engine_master = sa.create_engine(
                master_url,
                connect_args={"timeout": 5},
                isolation_level="AUTOCOMMIT",
            )
            with engine_master.connect() as conn:
                # Check if target database exists
                query = sa.text("SELECT database_id FROM sys.databases WHERE name = :dbname")
                result = conn.execute(query, {"dbname": database}).scalar()
                if not result:
                    print(f"[WAIT-FOR-DB] Database [{database}] does not exist. Creating...")
                    conn.execute(sa.text(f"CREATE DATABASE [{database}];"))
                    print(f"[WAIT-FOR-DB] Database [{database}] created successfully.")
                else:
                    print(f"[WAIT-FOR-DB] Database [{database}] already exists.")

            engine_master.dispose()

            # 2. Verify connection directly to target database
            engine_target = sa.create_engine(
                target_url,
                connect_args={"timeout": 5},
            )
            with engine_target.connect() as conn:
                conn.execute(sa.text("SELECT 1;"))
            engine_target.dispose()

            print(f"[WAIT-FOR-DB] Successfully connected to [{database}] on {host}:{port}!")
            return True

        except Exception as exc:
            elapsed = int(time.time() - start_time)
            print(
                f"[WAIT-FOR-DB] [{elapsed}s] Server not ready yet: {exc}. "
                f"Retrying in {interval_seconds}s..."
            )
            time.sleep(interval_seconds)

    print(f"[WAIT-FOR-DB] ERROR: Timeout after {timeout_seconds}s waiting for SQL Server.")
    return False


if __name__ == "__main__":
    timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "90"))
    if not wait_for_database(timeout_seconds=timeout):
        sys.exit(1)
    sys.exit(0)
