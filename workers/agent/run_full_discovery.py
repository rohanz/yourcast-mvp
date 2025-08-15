#!/usr/bin/env python3
"""
Full RSS Discovery Script - Populate database with all available articles
"""

import sys
import os
import time
from datetime import datetime

sys.path.append('.')

from agent.config import settings
from agent.rss_config import get_all_feeds
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def run_full_discovery():
    """Run full RSS discovery with no limits"""
    print("🚀 Starting Full RSS Discovery\n")
    
    # Show configuration
    feeds = get_all_feeds()
    print(f"📡 Configured feeds: {len(feeds)}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 AI responses will be shown for clustering decisions")
    print("="*60)
    
    try:
        # Database setup
        print("\n🗄️  Setting up database connection...")
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        print("✅ Database connected")
        
        # Initialize RSS Discovery Service
        print("\n📡 Initializing RSS Discovery Service...")
        from agent.services.rss_discovery_service import RSSDiscoveryService
        
        service = RSSDiscoveryService(db, debug_llm_responses=True)
        print("✅ RSS Discovery Service initialized")
        
        # Run discovery
        print("\n🔍 Processing all RSS feeds (this may take several minutes)...")
        start_time = time.time()
        
        results = service.discover_and_process_articles(
            max_articles_per_feed=1000  # High limit to get all available articles
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Show results
        print("\n" + "="*60)
        print("✅ DISCOVERY COMPLETED!")
        print(f"📊 Feeds processed: {results['feeds_processed']}")
        print(f"📊 Articles discovered: {results['articles_discovered']}")
        print(f"📊 New articles: {results['new_articles']}")
        print(f"📊 Duplicates skipped: {results['duplicates_skipped']}")
        print(f"📊 Errors: {results['errors']}")
        print(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        if results['new_articles'] > 0:
            print(f"📈 Average: {results['new_articles']/duration:.1f} articles/second")
        print("="*60)
        
        # Show final database stats
        try:
            from agent.services.smart_article_service import SmartArticleService
            smart_service = SmartArticleService()
            stats = smart_service.get_article_stats()
            
            if stats:
                print("\n📈 DATABASE STATISTICS:")
                print(f"   • Total articles: {stats.get('total_articles', 0)}")
                print(f"   • Unique stories: {stats.get('unique_stories', 0)}")
                print(f"   • Categories: {stats.get('categories_count', 0)}")
                print(f"   • Average importance: {stats.get('avg_importance_score', 5.0):.1f}")
                
                if 'importance_distribution' in stats:
                    print("\n📊 Importance Score Distribution:")
                    for score, count in sorted(stats['importance_distribution'].items()):
                        print(f"      Score {score}: {count} stories")
        except Exception as e:
            print(f"⚠️  Could not fetch final stats: {e}")
        
        print("\n🎉 Ready for podcast generation!")
        
        db.close()
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Discovery interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Discovery failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = run_full_discovery()
    
    if success:
        print("\n✅ Full discovery completed successfully!")
    else:
        print("\n❌ Full discovery failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
