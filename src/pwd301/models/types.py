"""SQLAlchemy custom column types and dialect compatibility helpers for PWD301.

Provides SQL Server-first data types with clean SQLite in-memory fallback
for unit testing and local development without altering canonical DDL semantics.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# ---------------------------------------------------------------------------
# Dialect-aware type helpers
# ---------------------------------------------------------------------------

# BIGINT identity primary key (falls back to INTEGER rowid on SQLite for autoincrement)
BigIntPK = sa.BigInteger().with_variant(sa.Integer, "sqlite")

# Public UUID mapped to UNIQUEIDENTIFIER on MSSQL, CHAR(32) on SQLite
GUID = sa.Uuid(as_uuid=True).with_variant(mssql.UNIQUEIDENTIFIER, "mssql")

# UTC timestamp mapped to DATETIME2(3) on MSSQL, DATETIME on SQLite
UTCDateTime = sa.DateTime().with_variant(mssql.DATETIME2(3), "mssql")

# Concurrency row version mapped to ROWVERSION on MSSQL, BLOB(8) on SQLite
RowVersion = sa.LargeBinary(8).with_variant(mssql.ROWVERSION, "mssql")

# Large text mapped to NVARCHAR(MAX) on MSSQL, TEXT on SQLite
NVarCharMax = sa.UnicodeText().with_variant(mssql.NVARCHAR(None), "mssql")

# SHA-256 / hash binary mapped to BINARY(32) on MSSQL, BLOB on SQLite
Binary32 = sa.LargeBinary(32).with_variant(mssql.BINARY(32), "mssql")


def utc_now() -> datetime.datetime:
    """Return the current UTC timestamp."""
    return datetime.datetime.now(datetime.UTC)


# ---------------------------------------------------------------------------
# SQLite engine listener to emulate SQL Server native functions in tests
# ---------------------------------------------------------------------------


def _sqlite_isjson(val: Any) -> int:
    """SQLite user-defined function emulating T-SQL ISJSON()."""
    if val is None:
        return 1
    if not isinstance(val, str):
        return 0
    stripped = val.strip()
    if not (
        (stripped.startswith("{") and stripped.endswith("}"))
        or (stripped.startswith("[") and stripped.endswith("]"))
    ):
        return 0
    try:
        json.loads(stripped)
        return 1
    except Exception:
        return 0


def _sqlite_sysutcdatetime() -> str:
    """SQLite user-defined function emulating T-SQL SYSUTCDATETIME()."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _sqlite_newid() -> str:
    """SQLite user-defined function emulating T-SQL NEWID() / NEWSEQUENTIALID()."""
    return str(uuid.uuid4())


def register_sqlite_functions(engine: sa.engine.Engine) -> None:
    """Register SQL Server emulator functions on SQLite connections."""

    @sa.event.listens_for(engine, "connect")
    def _on_sqlite_connect(dbapi_connection: Any, connection_record: Any) -> None:
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.create_function("ISJSON", 1, _sqlite_isjson)
            dbapi_connection.create_function("SYSUTCDATETIME", 0, _sqlite_sysutcdatetime)
            dbapi_connection.create_function("NEWSEQUENTIALID", 0, _sqlite_newid)
            dbapi_connection.create_function("NEWID", 0, _sqlite_newid)


# Register globally for any Engine connect
@sa.event.listens_for(sa.engine.Engine, "connect")
def _global_engine_connect(dbapi_connection: Any, connection_record: Any) -> None:
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("ISJSON", 1, _sqlite_isjson)
        dbapi_connection.create_function("SYSUTCDATETIME", 0, _sqlite_sysutcdatetime)
        dbapi_connection.create_function("NEWSEQUENTIALID", 0, _sqlite_newid)
        dbapi_connection.create_function("NEWID", 0, _sqlite_newid)
