"""Flask extension instances for PWD301.

Instantiates extensions with the unattached application factory pattern.
"""

from __future__ import annotations

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for PWD301 domain models."""


db: SQLAlchemy = SQLAlchemy(model_class=Base)
migrate: Migrate = Migrate()
csrf: CSRFProtect = CSRFProtect()
login_manager: LoginManager = LoginManager()

# Configure basic LoginManager defaults
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
