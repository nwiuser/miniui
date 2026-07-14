#!/usr/bin/env python3
"""
Database initialization script for ApexOS.
Creates initial data and sets up the database.
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine, Base
from app import models

def init_db() -> None:
    """Initialize the database with tables and initial data."""
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    # Create initial data
    print("Creating initial data...")
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(models.Application).first() is not None:
            print("Database already contains data. Skipping initial data creation.")
            return

        # Create a sample application
        # app = models.Application(
        #     name="Sample Application",
        #     alias="SAMPLE",
        #     description="A sample application to get started"
        # )
        # db.add(app)
        # db.commit()
        # print("Created sample application")

        print("Initial data creation skipped (implement as needed)")
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing ApexOS database...")
    init_db()
    print("Database initialization complete!")