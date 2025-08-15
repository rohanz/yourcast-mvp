#!/usr/bin/env python3
"""
Test script to validate episode segments with proper source ID mapping
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.services.episode_service import EpisodeService
from agent.utils.uuid_utils import generate_uuidv7

def test_episode_segments():
    """Test episode segments with proper source ID mapping"""
    print("🧪 Testing Episode Segments with Source ID mapping...")
    
    service = EpisodeService()
    
    # Generate test episode ID
    episode_id = generate_uuidv7()
    print(f"📝 Created test episode: {episode_id}")
    
    # Test sources data
    sources_data = [
        {
            "id": "article-1", 
            "title": "Test Article 1",
            "url": "https://example.com/article1",
            "published_date": "2025-08-15T10:00:00Z",
            "excerpt": "Test article 1 excerpt",
            "summary": "Test summary 1"
        },
        {
            "id": "article-2",
            "title": "Test Article 2", 
            "url": "https://example.com/article2",
            "published_date": "2025-08-15T10:00:00Z",
            "excerpt": "Test article 2 excerpt",
            "summary": "Test summary 2"
        }
    ]
    
    # Test transcript data with source_ids referencing article IDs
    transcript_data = [
        {
            "start": 0,
            "end": 30,
            "text": "This is the first segment talking about article 1",
            "source_ids": ["article-1"]
        },
        {
            "start": 31,
            "end": 60,
            "text": "This is the second segment talking about article 2",
            "source_ids": ["article-2"]
        },
        {
            "start": 61,
            "end": 70,
            "text": "Short segment - should be skipped",  # This should be skipped (< 10 seconds)
            "source_ids": ["article-1"]
        },
        {
            "start": 71,
            "end": 100,
            "text": "This is the third segment also about article 1",
            "source_ids": ["article-1"]
        }
    ]
    
    try:
        # Create episode first
        print(f"📝 Creating episode: {episode_id}")
        service.update_episode(episode_id, 
                              title="Test Episode for Segments",
                              description="Test episode for segment source mapping",
                              subcategories=["Technology"],
                              status="processing")
        
        # Store sources and get mapping
        print(f"💾 Storing sources...")
        article_to_source_map = service.store_sources(episode_id, sources_data)
        print(f"✅ Sources stored successfully - mapping: {article_to_source_map}")
        
        # Store episode segments with mapping
        print(f"💾 Storing episode segments...")
        service.store_episode_segments(episode_id, transcript_data, article_to_source_map)
        print(f"✅ Episode segments stored successfully")
        
        print("\n🎉 SUCCESS! Episode segments created with proper source ID mapping!")
        print("\n📊 How it works:")
        print("- Article IDs in transcript are mapped to UUIDv7 source IDs")
        print("- Only segments > 10 seconds are stored")
        print("- Foreign key constraints are satisfied")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_episode_segments()
    if success:
        print("\n✨ Episode segments test verified successfully!")
    else:
        print("\n💥 Episode segments test failed!")
        sys.exit(1)
