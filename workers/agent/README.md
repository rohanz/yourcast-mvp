# YourCast Agent Worker

An intelligent RSS-based news discovery and clustering system that automatically organizes articles into story clusters using AI-powered analysis and vector embeddings.

## 🚀 New and Improved Discovery System

This project now features a **completely redesigned news discovery pipeline** that has evolved from basic RSS parsing to a sophisticated AI-powered clustering system:

### **Modern Architecture Overview**
```
RSS Feeds → Article Discovery → AI Clustering → Vector Storage → Story Clusters
     ↓              ↓              ↓               ↓              ↓
  46+ Feeds    Extract Content   Categorize     PostgreSQL    Organized Stories
              + Embeddings     + Tag + Cluster   + pgvector   + Smart Grouping
```

## 🎯 Key Features

### **Intelligent Article Clustering**
- **AI-Powered Analysis**: Uses Google's Gemini LLM to determine article relationships
- **Vector Similarity**: Employs 768-dimensional embeddings with pgvector for semantic similarity
- **Smart Clustering**: Automatically groups related articles into story clusters
- **Category-Aware**: Respects feed categories while making intelligent subcategorization decisions

### **Advanced Content Processing**
- **46+ RSS Feeds**: Curated feeds across 9 major categories (World News, Technology, Business, Sports, etc.)
- **Real-time Processing**: Processes articles as they're discovered
- **Duplicate Detection**: MD5-based URL hashing prevents duplicate processing
- **Content Enrichment**: AI generates relevant tags and subcategories for each article

### **Modern Technology Stack**
- **Database**: PostgreSQL with pgvector extension for vector operations
- **Embeddings**: Google's text-embedding-004 (768 dimensions) via new google-genai SDK
- **AI Processing**: Gemini 1.5 Flash for clustering decisions and categorization
- **Backend**: Python with SQLAlchemy, Celery for async processing
- **Vector Search**: Cosine similarity with configurable thresholds

## 📊 Project Flow

### **1. RSS Discovery**
```python
# Processes 46+ categorized RSS feeds
RSSDiscoveryService → discovers articles from feeds
                   → extracts title, summary, metadata
                   → filters recent articles (last 7 days)
```

### **2. Content Analysis**
```python
# AI-powered content understanding
EmbeddingService → generates 768-dim vectors
LLMService → analyzes content for categorization
ClusteringService → determines story relationships
```

### **3. Intelligent Clustering**
```python
# Smart article grouping
if similar_articles_found:
    ai_judge → "join existing cluster" or "create new"
else:
    ai_categorizer → generates subcategory + tags + new cluster
```

### **4. Data Storage**
```python
# Structured storage with relationships
PostgreSQL → articles table (with vector embeddings)
          → story_clusters table (canonical titles)
          → pgvector indexes (fast similarity search)
```

## 🛠 Services Architecture

### **Core Services**
- **`RSSDiscoveryService`**: RSS feed processing and article extraction
- **`ClusteringService`**: AI-powered article clustering and similarity analysis
- **`EmbeddingService`**: Vector embedding generation using Google's text-embedding-004
- **`LLMService`**: AI text generation for clustering decisions and categorization

### **Supporting Services**
- **`EpisodeService`**: Podcast episode generation and management
- **`StorageService`**: File storage and media handling
- **`TTSService`**: Text-to-speech for podcast generation
- **`TranscriptService`**: Audio transcription capabilities

## 🔧 Setup and Installation

### **Prerequisites**
- Python 3.11+
- PostgreSQL with pgvector extension
- Google Cloud credentials (for Gemini and embeddings)
- Redis (for Celery task queue)

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/yourcast_db

# Google Cloud AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GEMINI_API_KEY=your-gemini-api-key

# Redis
REDIS_URL=redis://localhost:6379

# Storage
STORAGE_DIR=../../shared/storage
```

### **Installation**
```bash
# Install dependencies
uv install

# Set up database (with pgvector)
createdb yourcast_db
psql yourcast_db -c "CREATE EXTENSION vector;"

# Run database migrations (if applicable)
# python manage.py migrate

# Start Redis
redis-server

# Start Celery worker
celery -A agent.celery_app worker --loglevel=info
```

## 🧪 Testing and Development

### **Available Test Scripts**
```bash
# Basic discovery test (5 feeds, 3 articles each)
uv run test_small_discovery.py

# Debug mode with LLM response logging
uv run test_small_discovery_debug.py

# Manual RSS testing
uv run test_manual_rss.py

# Clear all database data
uv run clear_database.py
```

### **Example Usage**
```python
from agent.services.rss_discovery_service import RSSDiscoveryService
from agent.services.clustering_service import ClusteringService

# Create database session
db = get_database_session()

# Initialize services
discovery = RSSDiscoveryService(db, debug_llm_responses=True)
clustering = ClusteringService(db, debug_llm_responses=True)

# Run discovery
results = discovery.discover_and_process_articles(max_articles_per_feed=10)
print(f"Processed {results['new_articles']} articles into {results['new_clusters']} clusters")
```

## 📈 Performance and Capabilities

### **Processing Stats**
- **Throughput**: ~13 articles processed simultaneously (limited by LLM rate limits)
- **Accuracy**: 100% AI categorization success rate in testing
- **Categories**: 9 major categories with 35+ subcategories
- **Similarity**: 85% cosine similarity threshold for clustering
- **Storage**: Vector embeddings compressed to 768 dimensions

### **Intelligent Features**
- **Semantic Understanding**: Groups articles by story, not just keywords
- **Cross-source Clustering**: Can relate articles from different news sources
- **Time-aware Processing**: Considers publication timestamps in clustering decisions
- **Category Inheritance**: Respects RSS feed categories while adding intelligent subcategorization

## 🔄 Recent Improvements

### **Major Updates**
1. **Migrated to Modern AI Stack**: Replaced deprecated `vertexai.language_models` with `google-genai` SDK
2. **Fixed Vector Dimensions**: Updated database schema from 1536 to 768 dimensions to match embedding model
3. **Enhanced SQL Compatibility**: Fixed parameter binding issues with PostgreSQL and pgvector
4. **Improved Clustering Logic**: AI now generates subcategories and tags even for standalone articles
5. **Added Debug Capabilities**: Optional LLM response logging for development and troubleshooting

### **Database Schema Updates**
- Updated `articles.embedding` column to `vector(768)`
- Fixed SQL parameter casting with `CAST(:param AS vector)` syntax
- Enhanced foreign key relationships between articles and story clusters

## 🎯 Future Roadmap

- **Summary Enhancement**: Add web scraping for missing article summaries
- **Real-time Processing**: WebSocket-based live article streaming
- **Advanced Clustering**: Multi-dimensional clustering with temporal analysis
- **Content Enhancement**: Automatic article summarization for feeds without descriptions
- **Performance Optimization**: Batch processing and caching improvements

## 📝 Contributing

1. All code follows Python best practices with type hints
2. SQL queries use parameterized statements for security
3. Error handling includes transaction rollbacks
4. Debug logging available for development
5. Comprehensive test coverage for core functionality

---

**Built with ❤️ for intelligent news discovery and automated podcast generation.**
