"""
Database Initialization Script
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verxlite_api.db.base import Base
from verxlite_api.config import settings


def init_database():
    """
    Initialize the database with all tables.
    """
    print("Initializing database...")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    
    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("Tables created successfully!")
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if we need to create a default tenant
    from verxlite_api.models.tenant import Tenant
    from verxlite_api.models.user import User
    
    tenant_count = session.query(Tenant).count()
    if tenant_count == 0:
        print("Creating default tenant...")
        default_tenant = Tenant(
            name="Default Tenant",
            description="Default workspace for Verxlite",
            is_active=True,
        )
        session.add(default_tenant)
        session.commit()
        print(f"Default tenant created: {default_tenant.id}")
    
    user_count = session.query(User).count()
    if user_count == 0:
        print("Creating default admin user...")
        default_user = User(
            tenant_id=session.query(Tenant).first().id,
            email="admin@verxlite.dev",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
        )
        session.add(default_user)
        session.commit()
        print(f"Default admin user created: {default_user.id}")
    
    session.close()
    print("Database initialization complete!")


if __name__ == "__main__":
    init_database()
