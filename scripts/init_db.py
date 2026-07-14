"""
Database Initialization Script

Runs `Base.metadata.create_all` (good enough for dev / tests). In production
prefer `alembic upgrade head`.
"""

import sys
import os

# Make `verxlite_api` importable when running from `scripts/`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from verxlite_api.db.base import Base
from verxlite_api.config import settings

# IMPORTANT: import every model BEFORE calling create_all so its table is
# registered on Base.metadata.
from verxlite_api.models.tenant import Tenant  # noqa: F401
from verxlite_api.models.user import User  # noqa: F401
from verxlite_api.models.connection import Connection  # noqa: F401
from verxlite_api.models.workflow import Workflow  # noqa: F401
from verxlite_api.models.workflow_run import WorkflowRun  # noqa: F401
from verxlite_api.models.workflow_step import WorkflowStep  # noqa: F401
from verxlite_api.models.artifact import Artifact  # noqa: F401


def init_database():
    """Initialize the database with all tables and seed data."""
    print("Initializing database...")

    engine = create_engine(settings.DATABASE_URL, echo=False)

    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Tables created successfully!")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if session.query(Tenant).count() == 0:
            print("Creating default tenant...")
            default_tenant = Tenant(
                name="Default Tenant",
                description="Default workspace for Verxlite",
                is_active=True,
            )
            session.add(default_tenant)
            session.commit()
            print(f"Default tenant created: {default_tenant.id}")

        if session.query(User).count() == 0:
            print("Creating default admin user (admin@verxlite.dev / admin12345)...")
            from verxlite_api.deps import hash_password
            default_tenant = session.query(Tenant).first()
            default_user = User(
                tenant_id=default_tenant.id,
                email="admin@verxlite.dev",
                first_name="Admin",
                last_name="User",
                role="admin",
                is_active=True,
                password_hash=hash_password("admin12345"),
            )
            session.add(default_user)
            session.commit()
            print(f"Default admin user created: {default_user.id}")
    finally:
        session.close()

    print("Database initialization complete!")


if __name__ == "__main__":
    init_database()
