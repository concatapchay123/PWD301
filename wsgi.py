"""WSGI application entrypoint for PWD301 production deployment."""

from __future__ import annotations

from pwd301 import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
