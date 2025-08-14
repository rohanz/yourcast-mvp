#!/usr/bin/env python3
"""
Simple RSS test - just test feed parsing without embeddings/clustering
"""

import sys
sys.path.append('.')

import feedparser
from agent.rss_config import get_all_feeds, get_feed_category, get_category_subcategories

def test_rss_parsing():
    """Test RSS feed parsing directly"""
    print("🔍 Testing RSS Feed Parsing (No Embeddings)...\n")
    
    # Test a few different feeds
    test_feeds = [
        "https://feeds.npr.org/1001/rss.xml",    # NPR (working)
        "https://techcrunch.com/feed/",          # TechCrunch (working)
        "http://feeds.bbci.co.uk/news/rss.xml",  # BBC (test redirect)
        "https://rss.cnn.com/rss/edition.rss",   # CNN
    ]
    
    successful_feeds = []
    
    for feed_url in test_feeds:
        print(f"📡 Testing: {feed_url}")
        
        # Get category from our config
        category = get_feed_category(feed_url)
        subcategories = get_category_subcategories(category)
        
        print(f"  📂 Category: {category}")
        print(f"  📋 Subcategories: {len(subcategories)} available")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if hasattr(feed, 'status'):
                print(f"  🌐 HTTP Status: {feed.status}")
            
            if hasattr(feed, 'entries') and feed.entries:
                print(f"  ✅ Found {len(feed.entries)} articles")
                
                # Show first article
                if feed.entries:
                    first_article = feed.entries[0]
                    print(f"     📰 Sample: {first_article.title[:60]}...")
                    
                    # Prepare article data like our RSS service would
                    article_data = {
                        'title': first_article.title,
                        'url': first_article.link,
                        'summary': getattr(first_article, 'summary', 'No summary')[:100] + '...',
                        'source_name': getattr(feed.feed, 'title', 'Unknown'),
                        'feed_category': category
                    }
                    
                    print(f"     🏷️  Would be categorized as: {category}")
                    if subcategories:
                        print(f"     📝 Subcategory options: {', '.join(subcategories[:3])}...")
                
                successful_feeds.append((feed_url, category, len(feed.entries)))
                
            else:
                print(f"  ⚠️  No articles found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()  # Empty line
    
    print(f"📊 Summary: {len(successful_feeds)}/{len(test_feeds)} feeds working")
    
    if successful_feeds:
        print("✅ Working feeds:")
        for feed_url, category, count in successful_feeds:
            print(f"  • {category}: {count} articles from {feed_url[:50]}...")
    
    return successful_feeds

def test_categorization():
    """Test our categorization system"""
    print("\n🎯 Testing Feed Categorization System...\n")
    
    # Test all categories
    from agent.rss_config import RSS_FEEDS_CONFIG
    
    for category, data in RSS_FEEDS_CONFIG.items():
        feeds = data['feeds']
        subcategories = data['subcategories']
        
        print(f"📂 {category}:")
        print(f"  📡 Feeds: {len(feeds)}")
        print(f"  📋 Subcategories: {len(subcategories)}")
        print(f"  🏷️  Examples: {', '.join(subcategories[:3])}")
        
        # Test first feed in category
        if feeds:
            first_feed = feeds[0]
            detected_category = get_feed_category(first_feed)
            print(f"  ✅ Test: {first_feed[:50]}... → {detected_category}")
        print()

def test_prompt_generation():
    """Test clustering prompt generation"""
    print("🎯 Testing Clustering Prompt Generation...\n")
    
    try:
        from agent.services.clustering_service import ClusteringService
        
        # Mock database session
        class MockDB:
            pass
        
        service = ClusteringService(MockDB())
        
        # Test article
        test_article = {
            'title': 'OpenAI Releases GPT-5 with Revolutionary Capabilities',
            'summary': 'OpenAI announced GPT-5, featuring advanced reasoning and multimodal understanding.',
            'source_name': 'TechCrunch',
            'feed_category': 'Technology'
        }
        
        # Test few-shot examples
        examples = service._get_few_shot_examples('Technology')
        print(f"📚 Technology examples: {len(examples)} chars")
        print(f"Sample: {examples[:200]}...")
        
        # Test prompt creation
        prompt = service._create_clustering_prompt(test_article, [])
        print(f"\n📝 Generated prompt: {len(prompt)} chars")
        
        # Show key sections
        lines = prompt.split('\n')
        
        print(f"🎯 Key sections:")
        for i, line in enumerate(lines):
            if 'NEW ARTICLE:' in line:
                print(f"  Line {i+1}: {line}")
            elif 'Feed Category:' in line:
                print(f"  Line {i+1}: {line}")
            elif 'INSTRUCTIONS:' in line:
                print(f"  Line {i+1}: {line}")
                break
        
        print(f"\n✅ Prompt generation working!")
        return True
        
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return False

def main():
    """Run all simple tests"""
    print("🚀 Simple RSS Discovery Test (No Embeddings)\n")
    
    # Test RSS parsing
    working_feeds = test_rss_parsing()
    
    # Test categorization system  
    test_categorization()
    
    # Test prompt generation
    prompt_success = test_prompt_generation()
    
    print(f"\n📊 Final Results:")
    print(f"  📡 Working RSS feeds: {len(working_feeds)}")
    print(f"  🎯 Prompt generation: {'✅ Pass' if prompt_success else '❌ Fail'}")
    
    if working_feeds:
        print(f"\n🎉 Core system is working!")
        print(f"📝 Next steps:")
        print(f"  1. Set up Google Cloud authentication for embeddings")
        print(f"  2. Run full discovery with: discover_rss_articles()")
        print(f"  3. Check database for categorized articles")
    else:
        print(f"\n⚠️  RSS feeds not working. Check internet connection.")

if __name__ == "__main__":
    main()
