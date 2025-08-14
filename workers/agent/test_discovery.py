#!/usr/bin/env python3
"""
Test script for RSS discovery and clustering functionality
"""

import sys
import os
sys.path.append('.')

from agent.config import settings
from agent.rss_config import get_all_feeds, get_feed_category, get_category_subcategories
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_rss_config():
    """Test RSS configuration"""
    print("🔧 Testing RSS Configuration...")
    
    feeds = get_all_feeds()
    print(f"✅ Total feeds: {len(feeds)}")
    
    # Test categories
    categories = {}
    for feed in feeds[:10]:  # Test first 10 feeds
        category = get_feed_category(feed)
        if category not in categories:
            categories[category] = []
        categories[category].append(feed)
    
    print(f"✅ Categories found: {list(categories.keys())}")
    
    # Test subcategories
    for category in categories.keys():
        subcats = get_category_subcategories(category)
        print(f"  📂 {category}: {len(subcats)} subcategories")
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing Database Connection...")
    
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Test connection
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        print("✅ Database connection successful")
        
        # Check if tables exist
        tables_check = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('articles', 'story_clusters')
        """)).fetchall()
        
        existing_tables = [row[0] for row in tables_check]
        print(f"✅ Found tables: {existing_tables}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_rss_discovery_service():
    """Test RSS discovery service"""
    print("\n📡 Testing RSS Discovery Service...")
    
    try:
        from agent.services.rss_discovery_service import RSSDiscoveryService
        
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        rss_service = RSSDiscoveryService(db)
        print("✅ RSS Discovery Service initialized")
        
        # Test processing a single feed (limit to 2 articles for quick test)
        test_feed = "https://feeds.reuters.com/Reuters/worldNews"
        print(f"🔍 Testing single feed: {test_feed}")
        
        # Get feed category
        feed_category = get_feed_category(test_feed)
        print(f"✅ Feed category: {feed_category}")
        
        result = rss_service._process_feed(test_feed, max_articles=2)
        print(f"✅ Feed processing result: {result}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ RSS Discovery Service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_clustering_service():
    """Test clustering service examples"""
    print("\n🎯 Testing Clustering Service...")
    
    try:
        from agent.services.clustering_service import ClusteringService
        
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        clustering_service = ClusteringService(db)
        print("✅ Clustering Service initialized")
        
        # Test few-shot examples
        tech_examples = clustering_service._get_few_shot_examples("Technology")
        print(f"✅ Technology examples: {len(tech_examples)} characters")
        
        sports_examples = clustering_service._get_few_shot_examples("Sports")
        print(f"✅ Sports examples: {len(sports_examples)} characters")
        
        # Test categorization
        test_article = {
            'title': 'Apple Announces New iPhone 15 Pro',
            'summary': 'Apple unveiled the latest iPhone with titanium design and advanced camera system',
            'source_name': 'TechCrunch',
            'feed_category': 'Technology'
        }
        
        # Test the prompt creation (without actually calling LLM)
        prompt = clustering_service._create_clustering_prompt(test_article, [])
        print(f"✅ Clustering prompt created: {len(prompt)} characters")
        print(f"📝 Prompt preview: {prompt[:200]}...")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Clustering Service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RSS Discovery and Clustering Tests\n")
    
    tests = [
        test_rss_config,
        test_database_connection, 
        test_rss_discovery_service,
        test_clustering_service
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! The system is ready to use.")
        print("\n💡 To run full RSS discovery:")
        print("   python -c \"from agent.tasks.rss_tasks import discover_rss_articles; discover_rss_articles(max_articles_per_feed=5)\"")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
