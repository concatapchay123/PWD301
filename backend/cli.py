"""Flask CLI command registration for PWD301."""

from __future__ import annotations

import click
from flask import Flask

from backend.extensions import db
from backend.seeds.baseline import seed_baseline
from backend.seeds.demo import seed_demo


def register_cli_commands(app: Flask) -> None:
    """Register custom CLI commands onto the Flask application."""

    @app.cli.command("seed-baseline")
    def seed_baseline_cmd() -> None:
        """Seed baseline roles and root administrator into the database."""
        click.echo("Seeding baseline data...")
        summary = seed_baseline(db.session)
        click.echo(
            f"Done! Roles created: {summary['roles_created']}, "
            f"existing: {summary['roles_existing']}, "
            f"Admin created: {summary['admin_created']}, "
            f"Admin roles assigned: {summary['admin_roles_assigned']}"
        )

    @app.cli.command("seed-demo")
    def seed_demo_cmd() -> None:
        """Seed complete realistic demonstration dataset for PWD301 platform."""
        click.echo("Seeding demonstration dataset...")
        summary = seed_demo(db.session)
        click.echo(
            f"Done! Users: {len(summary['users_created'])} created, "
            f"{len(summary['users_existing'])} existing; "
            f"Courses: {len(summary['courses_created'])} created, "
            f"{len(summary['courses_existing'])} existing; "
            f"Lessons: {len(summary['lessons_created'])}; "
            f"Questions: {len(summary['questions_created'])}; "
            f"Assessments: {len(summary['assessments_created'])}; "
            f"Enrollments: {len(summary['enrollments_created'])}; "
            f"Attempts: {len(summary['attempts_created'])}; "
            f"Notifications: {summary['notifications_created']}; "
            f"Audit events: {summary['audit_events_created']}."
        )

    @app.cli.group("seed")
    def seed_group() -> None:
        """Database seeding command group."""

    @seed_group.command("demo")
    def seed_group_demo() -> None:
        """Seed complete realistic demonstration dataset for PWD301 platform."""
        click.echo("Seeding demonstration dataset...")
        summary = seed_demo(db.session)
        click.echo(
            f"Done! Users: {len(summary['users_created'])} created, "
            f"{len(summary['users_existing'])} existing; "
            f"Courses: {len(summary['courses_created'])} created, "
            f"{len(summary['courses_existing'])} existing; "
            f"Lessons: {len(summary['lessons_created'])}; "
            f"Questions: {len(summary['questions_created'])}; "
            f"Assessments: {len(summary['assessments_created'])}; "
            f"Enrollments: {len(summary['enrollments_created'])}; "
            f"Attempts: {len(summary['attempts_created'])}; "
            f"Notifications: {summary['notifications_created']}; "
            f"Audit events: {summary['audit_events_created']}."
        )

    @seed_group.command("baseline")
    def seed_group_baseline() -> None:
        """Seed baseline roles and root administrator into the database."""
        click.echo("Seeding baseline data...")
        summary = seed_baseline(db.session)
        click.echo(
            f"Done! Roles created: {summary['roles_created']}, "
            f"existing: {summary['roles_existing']}, "
            f"Admin created: {summary['admin_created']}, "
            f"Admin roles assigned: {summary['admin_roles_assigned']}"
        )

    @app.cli.command("clean-db")
    @click.option(
        "--keep-baseline/--no-keep-baseline",
        default=True,
        show_default=True,
        help="Re-seed canonical roles and root administrator after cleaning.",
    )
    @click.option(
        "--clean-storage/--no-clean-storage",
        default=True,
        show_default=True,
        help="Clean physical storage blobs, quarantine files, exports, and dev caches.",
    )
    @click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
        help="Bypass interactive confirmation prompt.",
    )
    def clean_db_cmd(keep_baseline: bool, clean_storage: bool, yes: bool) -> None:
        """Hard delete all test and demonstration records from database and storage."""
        if not yes and not click.confirm(
            "WARNING: This will permanently delete all test records from the database. Continue?"
        ):
            click.echo("Database cleanup aborted.")
            return

        click.echo("Executing production database cleanup...")
        from backend.services.database_cleanup_service import clean_database

        report = clean_database(
            session=db.session,
            engine=db.engine,
            keep_baseline=keep_baseline,
            clean_storage=clean_storage,
        )
        click.echo(
            f"Done! Cleaned {report['tables_targeted']} tables, "
            f"deleted {report['total_records_deleted']} records, "
            f"reseeded {report['identities_reseeded']} identity sequences."
        )
        if report.get("baseline_summary"):
            b = report["baseline_summary"]
            click.echo(
                f"Baseline re-seeded: Roles: {b['roles_created']}, "
                f"Admin created: {b['admin_created']}."
            )
        if report.get("storage_summary"):
            s = report["storage_summary"]
            click.echo(
                f"Storage cleaned: {s['total_files_deleted']} files deleted "
                f"({s['bytes_freed']} bytes freed)."
            )

    @app.cli.command("reset-db")
    @click.option(
        "--seed-demo",
        is_flag=True,
        default=False,
        help="Seed full demonstration dataset after cleaning instead of baseline only.",
    )
    @click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
        help="Bypass interactive confirmation prompt.",
    )
    def reset_db_cmd(seed_demo: bool, yes: bool) -> None:
        """Reset database to a pristine baseline (or seed demo data if --seed-demo)."""
        if not yes and not click.confirm(
            "WARNING: This will reset the database. Continue?"
        ):
            click.echo("Database reset aborted.")
            return

        from backend.services.database_cleanup_service import clean_database

        report = clean_database(
            session=db.session,
            engine=db.engine,
            keep_baseline=not seed_demo,
            clean_storage=True,
        )
        click.echo(
            f"Wiped {report['tables_targeted']} tables ({report['total_records_deleted']} records deleted)."
        )
        if seed_demo:
            click.echo("Seeding demonstration dataset...")
            demo_summary = seed_demo(db.session)
            click.echo(
                f"Done! Courses created: {len(demo_summary['courses_created'])}, "
                f"Users: {len(demo_summary['users_created'])}."
            )
        else:
            click.echo("Pristine baseline established.")

