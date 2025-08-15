#!/usr/bin/env python3
"""
Migration script to add importance_score column to story_clusters table
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_importance_score_column():
    """Add importance_score column to story_clusters table"""
    
    # Database configuration  
    DB_NAME = "yourcast_db"
    DB_USER = os.getenv("POSTGRES_USER", "yourcast_user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourcast_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    
    print(f"Adding importance_score column to story_clusters table in {DB_NAME}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Add importance_score column
        print("Adding importance_score column...")
        cur.execute("""
            ALTER TABLE story_clusters 
            ADD COLUMN IF NOT EXISTS importance_score INTEGER DEFAULT 5;
        """)
        
        # Add comment to the column
        cur.execute("""
            COMMENT ON COLUMN story_clusters.importance_score IS 
            'AI-generated importance score from 1-10 based on newsworthiness, impact, and interest';
        """)
        
        # Create index on importance_score for efficient sorting
        cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_story_clusters_importance_score 
            ON story_clusters(importance_score DESC);
        """)
        
        print("✅ importance_score column added successfully")
        print("✅ Index created for importance_score")
        
        cur.close()
        conn.close()
        
        print("\n✅ Database migration complete!")
        print("The AI will now assign importance scores (1-10) to each story cluster.")
        
    except psycopg2.Error as e:
        print(f"❌ Error adding importance_score column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_importance_score_column()
