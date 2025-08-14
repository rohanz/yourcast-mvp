"""
RSS Feed Configuration with Categories and Subcategories

This module defines the RSS feeds organized by categories to improve
article classification and clustering accuracy.
"""

from typing import Dict, List

# RSS Feed Configuration organized by categories
RSS_FEEDS_CONFIG = {
    "World News": {
        "subcategories": ["Africa", "Asia", "Europe", "Middle East", "North America", "South America", "Oceania"],
        "feeds": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "http://rss.cnn.com/rss/cnn_topstories.rss",
            "http://rss.cnn.com/rss/cnn_world.rss",
            "https://www.yahoo.com/news/rss",
            "https://moxie.foxnews.com/google-publisher/latest.xml",
        ]
    },
    
    "Politics & Government": {
        "subcategories": ["US Politics", "International Politics", "Elections", "Policy & Legislation", "Government Affairs"],
        "feeds": [
            "http://rss.cnn.com/rss/cnn_allpolitics.rss",
            "https://moxie.foxnews.com/google-publisher/politics.xml",
            "https://feeds.npr.org/1014/rss.xml",
        ]
    },
    
    "Business": {
        "subcategories": ["Markets", "Corporations & earnings", "Startups & Entrepreneurship", "Economy and Policy"],
        "feeds": [
            "https://finance.yahoo.com/news/rssindex",
            "https://feeds.bbci.co.uk/news/business/rss.xml",
        ]
    },
    
    "Technology": {
        "subcategories": ["AI & Machine Learning", "Gadgets & Consumer Tech", "Software & Apps", "Cybersecurity", "Hardware & Infrastructure"],
        "feeds": [
            "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://feeds.foxnews.com/foxnews/tech",
            "http://rss.cnn.com/rss/cnn_tech.rss",
            "https://news.ycombinator.com/rss",
        ]
    },
    
    "Science & Environment": {
        "subcategories": ["Space & Astronomy", "Biology", "Physics & Chemistry", "Research & Academia", "Climate & Weather", "Sustainability", "Conservation & Wildlife"],
        "feeds": [
            "https://feeds.npr.org/1026/rss.xml",
            "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
            "https://feeds.npr.org/1167/rss.xml",
            "https://moxie.foxnews.com/google-publisher/science.xml",
        ]
    },
    
    "Health": {
        "subcategories": ["Public Health", "Medicine & Healthcare", "Fitness & Wellness", "Mental Health"],
        "feeds": [
            "https://feeds.bbci.co.uk/news/health/rss.xml",
            "https://news.yahoo.com/rss/health",
            "https://feeds.npr.org/1128/rss.xml",
        ]
    },
    
    "Sports": {
        "subcategories": [
            "Football (Soccer)", "American Football", "Basketball", "Baseball", "Cricket", 
            "Tennis", "F1", "Boxing", "MMA", "Golf", "Ice hockey", "Rugby", 
            "Volleyball", "Table Tennis (Ping Pong)", "Athletics"
        ],
        "feeds": [
            "https://sports.yahoo.com/soccer/news/rss/",
            "https://sports.yahoo.com/nfl/news/rss/",
            "https://sports.yahoo.com/nba/news/rss/",
            "https://sports.yahoo.com/mlb/news/rss/",
            "https://sports.yahoo.com/tennis/news/rss/",
            "https://sports.yahoo.com/boxing/news/rss/",
            "https://sports.yahoo.com/mma/news/rss/",
            "https://sports.yahoo.com/golf/news/rss/",
            "https://sports.yahoo.com/nhl/news/rss/",
            "https://feeds.bbci.co.uk/sport/rss.xml",
            "https://www.espn.com/espn/rss/news",
            "https://moxie.foxnews.com/google-publisher/sports.xml",
        ]
    },
    
    "Arts & Culture": {
        "subcategories": ["Celebrity News", "Gaming", "Film & TV", "Music", "Literature", "Art & Design", "Fashion"],
        "feeds": [
            "https://feeds.npr.org/1039/rss.xml",
            "https://feeds.npr.org/1045/rss.xml",
            "https://feeds.npr.org/1138/rss.xml",
            "https://feeds.npr.org/1128/rss.xml",
            "https://feeds.npr.org/1048/rss.xml",
            "https://feeds.npr.org/1008/rss.xml",
            "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
            "https://www.bbc.com/culture/feed.rss",
        ]
    },
    
    "Lifestyle": {
        "subcategories": ["Travel", "Food & Dining", "Home & Garden", "Relationships & Family", "Hobbies"],
        "feeds": [
            "https://feeds.npr.org/1053/rss.xml",
            "https://www.bbc.com/travel/feed.rss",
            "https://www.yahoo.com/lifestyle/rss",
            "https://moxie.foxnews.com/google-publisher/travel.xml",
        ]
    }
}

def get_all_feeds() -> List[str]:
    """Get all RSS feed URLs as a flat list"""
    all_feeds = []
    for category_data in RSS_FEEDS_CONFIG.values():
        all_feeds.extend(category_data["feeds"])
    return all_feeds

def get_feed_category(feed_url: str) -> str:
    """Get the category for a specific feed URL"""
    for category, category_data in RSS_FEEDS_CONFIG.items():
        if feed_url in category_data["feeds"]:
            return category
    return "General"

def get_category_subcategories(category: str) -> List[str]:
    """Get subcategories for a specific category"""
    if category in RSS_FEEDS_CONFIG:
        return RSS_FEEDS_CONFIG[category]["subcategories"]
    return []

def get_categories() -> List[str]:
    """Get all available categories"""
    return list(RSS_FEEDS_CONFIG.keys())
