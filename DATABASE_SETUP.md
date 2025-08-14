# PostgreSQL Database Setup

This guide helps you migrate from SQLite to PostgreSQL with pgvector support for the RSS clustering feature.

## Prerequisites

1. **Install PostgreSQL** (with pgvector extension)
   ```bash
   # macOS with Homebrew
   brew install postgresql pgvector
   
   # Start PostgreSQL service
   brew services start postgresql
   ```

2. **Create a PostgreSQL user**
   ```bash
   # Connect to PostgreSQL as superuser
   psql postgres
   
   # Create user and database
   CREATE USER yourcast_user WITH PASSWORD 'yourcast_password';
   ALTER USER yourcast_user CREATEDB;
   \q
   ```

## Setup Steps

1. **Update your environment variables**
   Create/update your `.env` file:
   ```bash
   # PostgreSQL Database with pgvector
   DATABASE_URL=postgresql://yourcast_user:yourcast_password@localhost:5432/yourcast_db
   
   # Google Cloud AI Configuration
   GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
   
   # Alternative: Gemini API Key only (limited functionality)
   # GEMINI_API_KEY=your_gemini_api_key
   
   # Redis for task queue
   REDIS_URL=redis://localhost:6379
   
   # Storage directory
   STORAGE_DIR=../../shared/storage
   ```

2. **Install new dependencies**
   ```bash
   # Sync API dependencies
   cd apps/api
   uv sync
   
   # Sync worker dependencies  
   cd ../../workers/agent
   uv sync
   ```

3. **Run the database setup script**
   ```bash
   # From project root
   python scripts/setup_postgres.py
   ```

   This will:
   - Create the `yourcast_db` database
   - Enable the `pgvector` extension
   - Create all tables with the new schema

## New Database Schema

### story_clusters
- `cluster_id` (PK): Unique story identifier
- `canonical_title`: Representative title for the story
- `created_at`: When the story was first identified

### articles  
- `article_id` (PK): Unique article identifier
- `cluster_id` (FK): Links to story_clusters
- `url`: Article URL (unique)
- `uniqueness_hash`: MD5 hash of URL for fast duplicate detection
- `source_name`, `title`, `summary`: Article metadata
- `publication_timestamp`: When article was published
- `category`, `subcategory`, `tags`: AI-generated classifications
- `embedding`: **768-dimension vector** for semantic similarity (Google text-embedding-004)
- `created_at`: When article was processed

## Migration from SQLite (Optional)

If you want to migrate existing episode data:

1. **Export from SQLite** (if needed)
2. **Import to PostgreSQL** (manual process - existing episodes/sources can be preserved)

## Verification

Check that everything is working:
```bash
# Test database connection
python -c "from app.database.connection import engine; print('✅ Database connected successfully')"

# Verify pgvector extension
psql yourcast_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## Troubleshooting

- **Connection refused**: Make sure PostgreSQL is running
- **pgvector not found**: Install pgvector extension for your PostgreSQL version
- **Permission denied**: Check user permissions and database ownership
