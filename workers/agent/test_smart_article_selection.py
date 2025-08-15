#!/usr/bin/env python3
"""
Test script for smart article selection with importance scoring.

This script tests the new importance scoring system and smart article distribution.
"""

import sys
import os
import json
from datetime import datetime

# Add the agent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from agent.services.smart_article_service import SmartArticleService

def test_article_stats():
    """Test getting article statistics"""
    print("🔍 Testing Article Statistics...")
    print("=" * 60)
    
    service = SmartArticleService()
    stats = service.get_article_stats()
    
    if stats:
        print(f"📊 Database Statistics:")
        print(f"   Total articles: {stats['total_articles']}")
        print(f"   Unique stories: {stats['unique_stories']}")
        print(f"   Categories: {stats['categories_count']}")
        print(f"   Average importance score: {stats['avg_importance_score']}")
        print(f"   Recent articles (24h): {stats['recent_articles_24h']}")
        
        if 'importance_distribution' in stats:
            print(f"\n📈 Importance Score Distribution:")
            for score in sorted(stats['importance_distribution'].keys()):
                count = stats['importance_distribution'][score]
                print(f"   Score {score}: {count} stories")
        
        print(f"\n📅 Date range:")
        print(f"   Oldest: {stats['oldest_article']}")
        print(f"   Newest: {stats['newest_article']}")
    else:
        print("❌ Failed to get article statistics")
    
    print()

def test_available_categories():
    """Test getting available categories with importance stats"""
    print("📂 Testing Available Categories...")
    print("=" * 60)
    
    service = SmartArticleService()
    categories = service.get_available_categories()
    
    if categories:
        print(f"Found {len(categories)} categories:\n")
        
        for cat in categories:
            print(f"📁 {cat['category']}")
            print(f"   Articles: {cat['total_articles']}")
            print(f"   Avg importance: {cat['avg_importance']}")
            print(f"   Max importance: {cat['max_importance']}")
            print(f"   Subcategories: {len(cat['subcategories'])}")
            
            # Show top subcategories
            top_subs = sorted(cat['subcategories'], 
                            key=lambda x: x['avg_importance'], reverse=True)[:3]
            for sub in top_subs:
                print(f"      • {sub['subcategory']}: {sub['article_count']} articles, "
                      f"avg importance {sub['avg_importance']}")
            print()
    else:
        print("❌ Failed to get available categories")
    
    print()

def test_top_stories():
    """Test getting top stories by importance"""
    print("⭐ Testing Top Stories by Importance...")
    print("=" * 60)
    
    service = SmartArticleService()
    top_stories = service.get_top_stories_by_importance(
        limit=5, 
        min_importance=6, 
        hours_back=48
    )
    
    if top_stories:
        print(f"Found {len(top_stories)} top stories:\n")
        
        for i, article in enumerate(top_stories, 1):
            print(f"{i}. 📰 {article['title'][:80]}...")
            print(f"   Category: {article['category']} → {article['subcategory']}")
            print(f"   Importance: {article['importance_score']}/10")
            print(f"   Source: {article['source_name']}")
            print(f"   Published: {article['publication_timestamp']}")
            print()
    else:
        print("❌ No top stories found")
    
    print()

def test_smart_article_selection():
    """Test smart article selection for different category combinations"""
    print("🎯 Testing Smart Article Selection...")
    print("=" * 60)
    
    service = SmartArticleService()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Single Category (Technology)",
            "categories": ["Technology"],
            "total_articles": 10
        },
        {
            "name": "Two Categories (Tech + Business)", 
            "categories": ["Technology", "Business"],
            "total_articles": 12
        },
        {
            "name": "Multiple Categories",
            "categories": ["Technology", "Business", "Sports", "Politics & Government"],
            "total_articles": 20
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Test Case: {test_case['name']}")
        print("-" * 40)
        
        articles = service.get_articles_for_podcast(
            selected_categories=test_case['categories'],
            total_articles=test_case['total_articles'],
            min_importance_score=4,
            hours_back=168  # 7 days
        )
        
        if articles:
            print(f"✅ Selected {len(articles)} articles")
            
            # Show distribution by category
            category_counts = {}
            importance_scores = []
            
            for article in articles:
                cat = article['category']
                category_counts[cat] = category_counts.get(cat, 0) + 1
                importance_scores.append(article['importance_score'])
            
            print(f"📊 Distribution by category:")
            for cat, count in category_counts.items():
                print(f"   {cat}: {count} articles")
            
            print(f"📈 Importance scores:")
            print(f"   Range: {min(importance_scores)}-{max(importance_scores)}")
            print(f"   Average: {sum(importance_scores)/len(importance_scores):.1f}")
            
            print(f"\n📋 Sample Articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      {article['category']} | Score: {article['importance_score']}/10")
            
        else:
            print("❌ No articles found for this selection")
        
        print()

def test_category_balance():
    """Test that article distribution is balanced across categories"""
    print("⚖️  Testing Category Balance...")
    print("=" * 60)
    
    service = SmartArticleService()
    
    # Test with many categories to see distribution
    categories = ["Technology", "Business", "Sports", "Politics & Government", "Health"]
    total_articles = 25
    
    articles = service.get_articles_for_podcast(
        selected_categories=categories,
        total_articles=total_articles,
        min_importance_score=3,
        hours_back=168
    )
    
    if articles:
        print(f"✅ Retrieved {len(articles)} articles across {len(categories)} categories")
        
        # Detailed distribution analysis
        category_distribution = {}
        for article in articles:
            cat = article['category']
            if cat not in category_distribution:
                category_distribution[cat] = []
            category_distribution[cat].append(article)
        
        expected_per_category = total_articles // len(categories)
        remainder = total_articles % len(categories)
        
        print(f"📊 Expected distribution: {expected_per_category} per category (+{remainder} remainder)")
        print(f"📈 Actual distribution:")
        
        for cat in categories:
            count = len(category_distribution.get(cat, []))
            articles_in_cat = category_distribution.get(cat, [])
            avg_importance = sum(a['importance_score'] for a in articles_in_cat) / len(articles_in_cat) if articles_in_cat else 0
            print(f"   {cat}: {count} articles (avg importance: {avg_importance:.1f})")
        
        # Check balance
        counts = [len(category_distribution.get(cat, [])) for cat in categories]
        max_diff = max(counts) - min(counts)
        print(f"\n⚖️  Balance check: max difference = {max_diff} articles")
        if max_diff <= 1:
            print("   ✅ Well balanced distribution")
        else:
            print("   ⚠️  Distribution could be more balanced")
    else:
        print("❌ No articles found")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Smart Article Selection Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        test_article_stats()
        test_available_categories()
        test_top_stories()
        test_smart_article_selection()
        test_category_balance()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
