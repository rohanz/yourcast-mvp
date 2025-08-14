#!/usr/bin/env python3
"""
Manual test for RSS discovery - tests actual RSS feeds
"""

import sys
sys.path.append('.')

from agent.config import settings
from agent.rss_config import get_all_feeds, get_feed_category
from agent.services.rss_discovery_service import RSSDiscoveryService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_working_rss_feeds():
    """Test several RSS feeds to find working ones"""
    print("🔍 Testing RSS Feeds...")
    
    # Test different feeds to find working ones
    test_feeds = [
        "http://feeds.bbci.co.uk/news/rss.xml",  # BBC main feed
        "https://rss.cnn.com/rss/edition.rss",   # CNN main feed  
        "https://feeds.npr.org/1001/rss.xml",    # NPR top stories
        "https://techcrunch.com/feed/",          # TechCrunch
    ]
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    rss_service = RSSDiscoveryService(db)
    
    working_feeds = []
    
    for feed_url in test_feeds:
        print(f"\n📡 Testing: {feed_url}")
        
        try:
            # Get category
            category = get_feed_category(feed_url)
            print(f"  📂 Category: {category}")
            
            # Test feed processing
            result = rss_service._process_feed(feed_url, max_articles=3)
            
            if result['status'] == 'success' and result['articles_discovered'] > 0:
                print(f"  ✅ Success: {result['articles_discovered']} articles found")
                working_feeds.append((feed_url, category, result))
            else:
                print(f"  ⚠️  Issues: {result['status']}, {result['articles_discovered']} articles")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    db.close()
    
    print(f"\n📊 Working feeds: {len(working_feeds)}/{len(test_feeds)}")
    return working_feeds

def test_article_with_clustering():
    """Test an article going through the full clustering pipeline"""
    print("\n🎯 Testing Full Article Processing...")
    
    # Create a mock article that would come from RSS
    test_article = {
        'title': 'Apple Unveils iPhone 15 Pro with Titanium Design',
        'url': 'https://techcrunch.com/apple-iphone-15-pro-test-123',
        'summary': 'Apple announced the iPhone 15 Pro featuring a new titanium design, improved cameras, and the A17 Pro chip.',
        'published_date': None,
        'source_name': 'TechCrunch',
        'feed_category': 'Technology'  # This comes from our RSS categorization
    }
    
    print(f"📱 Test article: {test_article['title']}")
    print(f"📂 Category: {test_article['feed_category']}")
    
    try:
        from agent.services.clustering_service import ClusteringService
        
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        clustering_service = ClusteringService(db)
        
        # Test the AI judge clustering logic (without actually calling the LLM)
        similar_articles = []  # Simulating no similar articles found
        
        decision = clustering_service._ai_judge_clustering(test_article, similar_articles)
        print(f"✅ AI Judge decision: {decision}")
        
        # Test prompt generation
        prompt = clustering_service._create_clustering_prompt(test_article, similar_articles)
        print(f"✅ Generated prompt: {len(prompt)} chars")
        
        # Show the prompt structure
        lines = prompt.split('\n')
        print(f"📝 Prompt structure:")
        for i, line in enumerate(lines[:10]):  # First 10 lines
            print(f"   {i+1:2}: {line[:80]}...")
        print(f"   ... (total {len(lines)} lines)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Clustering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run manual tests"""
    print("🚀 Manual RSS Discovery Test\n")
    
    # Test RSS feeds
    working_feeds = test_working_rss_feeds()
    
    # Test clustering
    clustering_success = test_article_with_clustering()
    
    print(f"\n📊 Results:")
    print(f"  📡 Working RSS feeds: {len(working_feeds)}")
    print(f"  🎯 Clustering test: {'✅ Pass' if clustering_success else '❌ Fail'}")
    
    if working_feeds and clustering_success:
        print(f"\n🎉 System is working! Ready to run full discovery.")
        print(f"💡 Next step: Run the full RSS discovery task:")
        print(f"   uv run python -c \"from agent.tasks.rss_tasks import discover_rss_articles; discover_rss_articles(max_articles_per_feed=3)\"")
    else:
        print(f"\n⚠️  Some issues found. Check configuration.")

if __name__ == "__main__":
    main()
