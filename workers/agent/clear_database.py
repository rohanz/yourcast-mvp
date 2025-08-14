#!/usr/bin/env python3
"""
Clear Database Script - Remove all articles and clusters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from agent.config import settings

def clear_database():
    """Clear all articles and story clusters from the database"""
    print("🗑️  Starting database cleanup...")
    
    try:
        # Create database connection
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Get counts before deletion
                articles_count = conn.execute(text("SELECT COUNT(*) FROM articles")).scalar()
                clusters_count = conn.execute(text("SELECT COUNT(*) FROM story_clusters")).scalar()
                
                print(f"📊 Found {articles_count} articles and {clusters_count} clusters")
                
                # Delete all articles first (due to foreign key constraint)
                print("🔄 Deleting all articles...")
                result = conn.execute(text("DELETE FROM articles"))
                print(f"✅ Deleted {result.rowcount} articles")
                
                # Delete all story clusters
                print("🔄 Deleting all story clusters...")
                result = conn.execute(text("DELETE FROM story_clusters"))
                print(f"✅ Deleted {result.rowcount} story clusters")
                
                # Commit the transaction
                trans.commit()
                
                # Verify cleanup
                articles_remaining = conn.execute(text("SELECT COUNT(*) FROM articles")).scalar()
                clusters_remaining = conn.execute(text("SELECT COUNT(*) FROM story_clusters")).scalar()
                
                print(f"📊 After cleanup: {articles_remaining} articles, {clusters_remaining} clusters")
                
                if articles_remaining == 0 and clusters_remaining == 0:
                    print("🎉 Database successfully cleared!")
                else:
                    print("⚠️  Warning: Some records may not have been deleted")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during cleanup: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Ask for confirmation
    response = input("Are you sure you want to clear ALL articles and clusters? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        clear_database()
    else:
        print("❌ Operation cancelled")
