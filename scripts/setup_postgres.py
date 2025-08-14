#!/usr/bin/env python3
"""
Setup script for PostgreSQL with pgvector extension.
Run this script to create the database and enable the pgvector extension.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_database_and_extension():
    """Create database and enable pgvector extension"""
    
    # Database configuration
    DB_NAME = "yourcast_db"
    DB_USER = os.getenv("POSTGRES_USER", "yourcast_user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourcast_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    
    print(f"Setting up PostgreSQL database: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"  # Connect to default database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create database if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if not cur.fetchone():
            print(f"Creating database: {DB_NAME}")
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        else:
            print(f"Database {DB_NAME} already exists")
        
        cur.close()
        conn.close()
        
        # Connect to the new database and enable pgvector
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✅ pgvector extension enabled")
        
        cur.close()
        conn.close()
        
        # Print the database URL for configuration
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"\n✅ Database setup complete!")
        print(f"Add this to your .env file:")
        print(f"DATABASE_URL={db_url}")
        
    except psycopg2.Error as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)

def create_tables():
    """Create all tables using SQLAlchemy"""
    from app.database.connection import engine
    from app.models import Base
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--tables-only":
        create_tables()
    else:
        create_database_and_extension()
        create_tables()
