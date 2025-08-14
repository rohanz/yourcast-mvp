# RSS Feed Categorization Improvements

## Overview

This document outlines the improvements made to the RSS feed discovery and clustering system to enhance categorization accuracy using feed-based categorization and AI-powered subcategorization.

## Changes Made

### 1. RSS Feed Configuration (`agent/rss_config.py`)

**NEW FILE**: Created a comprehensive RSS feed configuration system that organizes feeds by categories:

- **World News**: BBC World, Reuters World News, CNN World, etc.
- **Politics & Government**: Political feeds from Reuters, CNN, NPR, Politico, etc.  
- **Business**: Markets, corporate news, startups, economy feeds
- **Technology**: Tech feeds from TechCrunch, The Verge, Ars Technica, etc.
- **Science & Environment**: Science journals, NASA, National Geographic, etc.
- **Health**: Medical news from Reuters Health, CNN Health, WebMD, etc.
- **Sports**: Comprehensive sports coverage with 13 subcategories (NFL, NBA, Tennis, Golf, etc.)
- **Arts & Culture**: Entertainment, gaming, movies, music, books, art, fashion
- **Lifestyle**: Travel, food, home & garden, relationships, hobbies

**Features**:
- `get_all_feeds()`: Returns all feed URLs as a flat list
- `get_feed_category(feed_url)`: Maps feed URL to its category
- `get_category_subcategories(category)`: Returns available subcategories for a category
- `get_categories()`: Lists all available categories

### 2. Configuration Update (`agent/config.py`)

**MODIFIED**: Updated the settings to use the new categorized RSS feeds:
- Changed from hardcoded list of 4 feeds to dynamic property that uses `get_all_feeds()`
- Now includes ~50+ high-quality, categorized RSS feeds

### 3. RSS Discovery Service (`agent/services/rss_discovery_service.py`)

**ENHANCED**: Modified to pass feed category information to the clustering service:
- Added import for `get_feed_category`
- In `_process_feed()`: Added `feed_category = get_feed_category(feed_url)`
- Enhanced article data structure to include `feed_category` field

### 4. Clustering Service (`agent/services/clustering_service.py`)

**MAJOR IMPROVEMENTS**: Enhanced the AI judge to leverage known feed categories:

#### Enhanced AI Judge Logic:
- **Import**: Added imports for `get_feed_category` and `get_category_subcategories`
- **Category Assignment**: Uses feed category when available, falls back to keyword matching
- **Improved Prompt**: AI judge now receives:
  - Known feed category (e.g., "Technology")
  - List of available subcategories for that category
  - Instruction to focus on subcategorization rather than broad categorization

#### New AI Judge Prompt Structure:
```
NEW ARTICLE:
Title: [article title]
Summary: [article summary]  
Source: [source name]
Feed Category: Technology  <-- NEW

INSTRUCTIONS:
1. Determine if article belongs to same story as existing articles
2. Consider: same event, people/companies, timeframe, topic
3. Don't cluster articles just because they're in same category
4. Article is from Technology feed, assign subcategory from: AI & Machine Learning, Gadgets & Consumer Tech, Software & Apps, Cybersecurity, Hardware & Computing  <-- NEW

Respond with JSON:
{
  "action": "join_existing" or "create_new",
  "cluster_id": "cluster_id_to_join" or null,
  "reason": "brief explanation", 
  "category": "Technology",  <-- Pre-filled from feed
  "subcategory": "choose from: [available subcategories]",  <-- Guided selection
  "tags": ["tag1", "tag2", "tag3"]
}
```

## Benefits

### 1. **Improved Categorization Accuracy**
- **Before**: AI had to guess broad categories from title/summary alone
- **After**: Categories are pre-determined from curated feed sources, AI focuses on precise subcategorization

### 2. **Better Feed Coverage**
- **Before**: 4 generic news feeds
- **After**: 50+ specialized feeds covering 9 major categories with detailed subcategories

### 3. **Consistent Subcategorization**
- **Before**: AI could invent random subcategories
- **After**: AI chooses from predefined, consistent subcategory lists for each domain

### 4. **Reduced LLM Ambiguity**
- **Before**: "Categorize this article into Technology/Politics/Sports/etc."
- **After**: "This Technology article should be subcategorized as AI/Gadgets/Software/etc."

## Feed Categories & Subcategories

### Sports (Most Detailed)
- Football (NFL), Basketball (NBA), Baseball (MLB), Hockey (NHL)
- Soccer/Football, Tennis, Golf, Olympics
- Boxing, MMA, Motorsports, College Sports, Other Sports

### Technology
- AI & Machine Learning, Gadgets & Consumer Tech, Software & Apps
- Cybersecurity, Hardware & Computing

### Business  
- Markets & Finance, Corporate News, Startups & Entrepreneurship
- Economy & Policy, Cryptocurrency

### Science & Environment
- Space & Astronomy, Biology & Medicine, Physics & Chemistry
- Research & Innovation, Climate & Weather, Wildlife & Conservation

### World News
- North America, Europe, Asia, Africa, South America, Middle East, Oceania

### Politics & Government
- US Politics, International Politics, Elections, Policy & Legislation, Government Affairs

### Health
- Medical News, Public Health, Mental Health, Nutrition & Fitness, Healthcare Policy

### Arts & Culture
- Celebrity & Entertainment, Gaming, Movies & TV, Music, Books & Literature, Art & Design, Fashion

### Lifestyle
- Travel, Food & Dining, Home & Garden, Relationships & Family, Hobbies & Interests

## Implementation Status

✅ **Completed**:
- RSS feed configuration with categories and subcategories
- Updated config to use new feeds
- Enhanced RSS discovery to pass feed categories
- Updated AI clustering prompt to use feed categories and subcategories

🔄 **Ready for Testing**:
- The system is ready to run RSS discovery with improved categorization
- AI judge will now make more accurate categorization decisions
- Articles will be better organized by category and subcategory

## Next Steps

1. **Test the new system** by running RSS discovery
2. **Monitor categorization quality** in the database
3. **Fine-tune subcategories** based on real article distribution
4. **Add more specialized feeds** as needed
