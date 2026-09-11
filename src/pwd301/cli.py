"""Flask CLI command registration for PWD301."""

from __future__ import annotations

import click
from flask import Flask

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline
from pwd301.seeds.demo import seed_demo


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
