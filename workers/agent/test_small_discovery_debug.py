#!/usr/bin/env python3
"""
Small RSS Discovery Test with Debug - Test with just 5 feeds and show LLM responses
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agent.config import settings
from agent.services.rss_discovery_service import RSSDiscoveryService
from agent.rss_config import RSS_FEEDS_CONFIG, get_all_feeds

def test_small_discovery_debug():
    """Test RSS discovery with just 5 feeds and show LLM responses"""
    print("🚀 Starting Small RSS Discovery Test with Debug")
    
    all_feeds = get_all_feeds()
    print(f"📊 Total feeds available: {len(all_feeds)}")
    
    # Get first 5 feeds from different categories
    test_feeds = []
    
    for category, category_data in RSS_FEEDS_CONFIG.items():
        if test_feeds:
            # Add one feed from each category
            feeds_from_category = category_data['feeds']
            if feeds_from_category:
                test_feeds.append((feeds_from_category[0], category))
        else:
            # First category, add first feed
            feeds_from_category = category_data['feeds']
            if feeds_from_category:
                test_feeds.append((feeds_from_category[0], category))
        
        if len(test_feeds) >= 5:
            break
    
    print(f"🎯 Testing with {len(test_feeds)} feeds:")
    for i, (url, category) in enumerate(test_feeds, 1):
        print(f"  {i}. {url} ({category})")
    
    print(f"\n📡 Starting discovery with max 3 articles per feed...")
    print("🤖 Debug mode enabled - showing LLM responses!")
    print("=" * 80)
    
    # Temporarily modify RSS_FEEDS_CONFIG to only include our test feeds
    original_config = {}
    for category, data in RSS_FEEDS_CONFIG.items():
        original_config[category] = data.copy()
    
    # Clear all feeds and add only test feeds
    for category in RSS_FEEDS_CONFIG:
        RSS_FEEDS_CONFIG[category]['feeds'] = []
    
    for url, category in test_feeds:
        if category in RSS_FEEDS_CONFIG:
            RSS_FEEDS_CONFIG[category]['feeds'].append(url)
    
    try:
        # Create database session with debug enabled
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # Initialize RSS discovery service with debug enabled
            rss_service = RSSDiscoveryService(db, debug_llm_responses=True)
            
            # Run discovery
            results = rss_service.discover_and_process_articles(max_articles_per_feed=3)
            
            print("=" * 80)
            print(f"\n✅ Small RSS discovery test completed successfully!")
            print(f"📊 Results:")
            print(f"  - Feeds processed: {results['feeds_processed']}")
            print(f"  - Articles discovered: {results['articles_discovered']}")
            print(f"  - New articles: {results['new_articles']}")
            print(f"  - Duplicates skipped: {results['duplicates_skipped']}")
            print(f"  - Errors: {results['errors']}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original feeds
        RSS_FEEDS_CONFIG.clear()
        RSS_FEEDS_CONFIG.update(original_config)

if __name__ == "__main__":
    test_small_discovery_debug()
