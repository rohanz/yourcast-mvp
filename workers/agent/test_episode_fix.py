#!/usr/bin/env python3
"""
Test script to verify the episode service fix with UUIDv7 and article_id handling
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.services.episode_service import EpisodeService
from agent.utils.uuid_utils import generate_uuidv7

def test_episode_service():
    """Test the fixed episode service"""
    print("🧪 Testing Episode Service with UUIDv7 and article_id fix...")
    
    service = EpisodeService()
    
    # Generate test episode ID
    episode_id = generate_uuidv7()
    print(f"📝 Created test episode: {episode_id}")
    
    # Test the same article in multiple "episodes" (simulate the error scenario)
    same_article_id = "test-article-123"  # This would be an article ID from RSS system
    
    # First episode sources
    sources_data_1 = [
        {
            "id": same_article_id,  # Same article ID
            "title": "Test Article - Same Article Different Episode",
            "url": "https://example.com/article",
            "published_date": "2025-08-15T10:00:00Z",
            "excerpt": "This is a test article excerpt",
            "summary": "Test summary"
        }
    ]
    
    # Second episode sources (same article)
    episode_id_2 = generate_uuidv7()
    sources_data_2 = [
        {
            "id": same_article_id,  # SAME article ID - this should work now!
            "title": "Test Article - Same Article Different Episode",
            "url": "https://example.com/article",
            "published_date": "2025-08-15T10:00:00Z",
            "excerpt": "This is a test article excerpt",
            "summary": "Test summary"
        }
    ]
    
    try:
        # Create episodes first (foreign key requirement)
        print(f"📝 Creating episode 1: {episode_id}")
        service.update_episode(episode_id, 
                              title="Test Episode 1",
                              description="Test episode for source fix",
                              subcategories=["Technology"],
                              status="processing")
        
        print(f"📝 Creating episode 2: {episode_id_2}")
        service.update_episode(episode_id_2,
                              title="Test Episode 2", 
                              description="Second test episode with same article",
                              subcategories=["Technology"],
                              status="processing")
        
        # Store sources for first episode
        print(f"💾 Storing sources for episode 1: {episode_id}")
        mapping_1 = service.store_sources(episode_id, sources_data_1)
        print(f"✅ Episode 1 sources stored successfully - mapping: {mapping_1}")
        
        # Store sources for second episode (same article)
        print(f"💾 Storing sources for episode 2: {episode_id_2}")
        mapping_2 = service.store_sources(episode_id_2, sources_data_2)
        print(f"✅ Episode 2 sources stored successfully - mapping: {mapping_2}")
        
        print("\n🎉 SUCCESS! Same article can now be used in multiple episodes!")
        print("\n📊 How it works:")
        print("- Each source gets a unique UUIDv7 ID")
        print("- article_id tracks the original RSS article")
        print("- Same article can appear in different episodes with different source IDs")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_episode_service()
    if success:
        print("\n✨ Episode service fix verified successfully!")
    else:
        print("\n💥 Episode service fix failed!")
        sys.exit(1)
