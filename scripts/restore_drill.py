"""Physical recovery proof on disposable Express only; never replace an existing database."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, UTC
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.engine import URL

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.services.operations_service import create_database_backup, verify_backup_integrity


def validate_drill_targets(source: str, target: str) -> None:
    if (
        os.environ.get("PWD301_TEST_DB_DISPOSABLE") != "1"
        or source == target
        or any(
            not re.fullmatch(r"pwd301_test_[A-Za-z0-9_]{1,90}", name) for name in (source, target)
        )
    ):
        raise ValueError(
            "Restore drill requires different disposable pwd301_test_* targets and explicit confirmation."
        )


def run() -> None:
    source = os.environ.get("DB_NAME", "")
    target = os.environ.get("RESTORE_DRILL_DB_NAME", "")
    validate_drill_targets(source, target)
    master = URL.create(
        "mssql+pyodbc",
        username="sa",
        password=os.environ["DB_PASSWORD"],
        host="db",
        port=1433,
        database="master",
        query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
    )
    engine = sa.create_engine(master, isolation_level="AUTOCOMMIT", hide_parameters=True)
    with engine.connect() as connection:
        if (
            connection.execute(sa.text("SELECT DB_ID(:name)"), {"name": target}).scalar()
            is not None
        ):
            raise ValueError("Restore target already exists; nothing was overwritten.")
        edition = str(connection.exec_driver_sql("SELECT SERVERPROPERTY('Edition')").scalar())
        if "Express" not in edition:
            raise ValueError("This release proof requires real SQL Server Express.")
    app = create_app("production")
    with app.app_context():
        actor = (
            db.session.query(User)
            .filter_by(email_normalized=os.environ["ADMIN_EMAIL"].lower())
            .one()
        )
        sample_tables = ("courses", "users", "lessons", "enrollments")
        counts = {
            table: db.session.execute(sa.text(f"SELECT COUNT(*) FROM [{table}]")).scalar()
            for table in sample_tables
        }
        backup = create_database_backup(actor, backup_type="RESTORE_DRILL")
        verified = verify_backup_integrity(actor, str(backup.public_id))
        artifact = Path(backup.storage_location)
        path = str(app.config["SQLSERVER_BACKUP_ROOT"]).rstrip("/") + "/" + artifact.name
        literal = path.replace("'", "''")
        with engine.connect() as connection:
            cursor = connection.connection.driver_connection.cursor()
            cursor.execute(f"RESTORE VERIFYONLY FROM DISK=N'{literal}' WITH CHECKSUM")
            while cursor.nextset():
                pass
            cursor.execute(f"RESTORE FILELISTONLY FROM DISK=N'{literal}'")
            rows = cursor.fetchall()
            moves = []
            for index, row in enumerate(rows):
                logical = str(row[0]).replace("'", "''")
                extension = "ldf" if str(row[2]) == "L" else "mdf"
                moves.append(
                    f"MOVE N'{logical}' TO N'/var/opt/mssql/data/{target}_{index}.{extension}'"
                )
            while cursor.nextset():
                pass
            cursor.execute(
                f"RESTORE DATABASE [{target}] FROM DISK=N'{literal}' WITH CHECKSUM, RECOVERY, "
                + ", ".join(moves)
            )
            while cursor.nextset():
                pass
            cursor.execute(f"DBCC CHECKDB([{target}]) WITH NO_INFOMSGS, ALL_ERRORMSGS")
            errors = []
            while True:
                if cursor.description:
                    errors.extend(cursor.fetchall())
                if not cursor.nextset():
                    break
            if errors:
                raise ValueError("Restored database failed integrity check.")
            cursor.close()
            restored = {
                table: connection.exec_driver_sql(
                    f"SELECT COUNT(*) FROM [{target}].dbo.[{table}]"
                ).scalar()
                for table in sample_tables
            }
        if restored != counts:
            raise ValueError("Restore sample counts do not match source snapshot.")
        report = {
            "time_utc": datetime.now(UTC).isoformat(),
            "edition": edition,
            "source": source,
            "target": target,
            "backup_id": str(backup.public_id),
            "checksum_manifest": verified,
            "restore_verifyonly": "PASS",
            "restore_drill": "PASS",
            "dbcc_checkdb": "PASS",
            "sample_counts": restored,
        }
        destination = artifact.parent / (artifact.name + ".drill.json")
        destination.write_text(json.dumps(report, default=str, indent=2), encoding="utf-8")
        print(json.dumps(report, default=str))
    engine.dispose()


if __name__ == "__main__":
    run()
