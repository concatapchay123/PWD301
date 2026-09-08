"""Flask CLI command registration for PWD301."""

from __future__ import annotations

import click
from flask import Flask

from pwd301.extensions import db
from pwd301.seeds.baseline import seed_baseline


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

    @app.cli.group("seed")
    def seed_group() -> None:
        """Database seeding command group."""

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
