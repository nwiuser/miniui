#!/usr/bin/env python3
"""Initialize the ApexOS database.

Runs the same startup routine the container uses: apply every Alembic migration
(stamping legacy ``create_all`` schemas first) and, when the ``BOOTSTRAP_ADMIN_*``
variables are set, create the first administrator.

Usage:
    python scripts/init_db.py

Optional environment variables for seeding the first admin:
    BOOTSTRAP_ADMIN_USERNAME
    BOOTSTRAP_ADMIN_PASSWORD
    BOOTSTRAP_ADMIN_EMAIL
"""

import sys
from pathlib import Path


def _find_backend_dir() -> Path:
    """Locate the backend package for both the repo and the container layout.

    In the repository the script is at ``<root>/scripts`` and the app at
    ``<root>/backend``; in the backend container it is mounted at
    ``/app/scripts`` next to the app.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent / "backend", here.parent.parent):
        if (candidate / "bootstrap.py").exists():
            return candidate
    raise SystemExit("Could not locate the backend directory.")


sys.path.insert(0, str(_find_backend_dir()))

import bootstrap  # noqa: E402


def main() -> None:
    print("Initializing ApexOS database...")
    bootstrap.main()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
