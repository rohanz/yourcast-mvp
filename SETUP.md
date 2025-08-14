# YourCast - Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Redis server (or Docker for Redis)

## Required API Keys

You'll need to obtain these API keys and credentials:

1. **Google Cloud Service Account**: For AI services (Gemini LLM + Text Embeddings) - **REQUIRED**
2. **Gemini API Key**: Alternative to service account for Gemini only - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **NewsAPI Key**: Optional legacy support - Get from [newsapi.org](https://newsapi.org/register)

**Note**: The system now uses RSS feeds as the primary news source with AI-powered clustering, making NewsAPI optional.

## Local Development Setup

### 1. Install Dependencies

```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd apps/web
npm install
cd ../..

# Install uv globally if not already installed
pip install uv

# Install Python dependencies for API
cd apps/api
uv sync
cd ../..

# Install Python dependencies for worker
cd workers/agent
uv sync
cd ../..
```

### 2. Google Cloud Service Account Setup

**For AI services (Gemini LLM + Text Embeddings):**

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Note your project ID

2. **Enable Required APIs**:
   - Go to APIs & Services → Library
   - Enable these APIs:
     - **Generative Language API** (for Gemini)
     - **Generative AI API** (for embeddings)
   
3. **Create a Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: `yourcast-ai-service`
   - Role: **Generative AI Administrator** (or Viewer for read-only)
   
4. **Download Service Account Key**:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key" → JSON
   - Download the JSON file to your project directory
   - **Important**: Keep this file secure and add to `.gitignore`

**Alternative - Gemini API Key Only** (simpler but limited):
- Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- This works for Gemini but not for text embeddings

### 3. Database Setup

**PostgreSQL with pgvector (Recommended for RSS clustering)**:

1. **Install PostgreSQL + pgvector**:
   ```bash
   # macOS with Homebrew
   brew install postgresql pgvector
   brew services start postgresql
   ```

2. **Create database and user**:
   ```bash
   # Connect as superuser
   psql postgres
   
   # Create user and database
   CREATE USER yourcast_user WITH PASSWORD 'yourcast_password';
   CREATE DATABASE yourcast_db OWNER yourcast_user;
   \c yourcast_db
   CREATE EXTENSION vector;
   \q
   ```

**SQLite (Fallback)**:
For basic functionality without RSS clustering, SQLite works automatically.

**Storage**: Audio files, transcripts, and VTT files are stored locally in `./storage` directory.

### 4. Environment Variables

Copy the example files and fill in your values:

```bash
cp apps/api/.env.example apps/api/.env
cp workers/agent/.env.example workers/agent/.env
```

**Required Variables:**

**For PostgreSQL + RSS Clustering:**
```bash
# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://yourcast_user:yourcast_password@localhost:5432/yourcast_db

# Google Cloud AI (Service Account)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service-account.json

# Alternative: Gemini API Key only (limited functionality)
# GEMINI_API_KEY=your_gemini_api_key

# Redis
REDIS_URL=redis://localhost:6379

# Storage
STORAGE_DIR=../../shared/storage

# Optional: Legacy News API
NEWS_API_KEY=your_news_api_key
```

**Important Notes:**
- Use **either** the service account JSON file **OR** the Gemini API key
- Service account provides full functionality (Gemini + embeddings)
- API key only works for Gemini, not embeddings
- RSS feeds are the primary news source, NewsAPI is optional

### 5. Start Development Services

You'll need 4 terminal windows/tabs:

**Terminal 1 - Frontend**
```bash
cd apps/web
npm run dev
```

**Terminal 2 - API**
```bash
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 3 - Redis** (or use Docker: `docker run -p 6379:6379 redis:alpine`)
```bash
redis-server
```

**Terminal 4 - Worker**
```bash
cd workers/agent
uv run python worker.py
```

### 6. Test the Application

1. Open http://localhost:3000
2. Select 1-3 topics (e.g., Technology, Science)
3. Click "Generate Podcast"
4. Wait for the podcast to be generated (may take 2-5 minutes)

## Production Deployment

### Prerequisites

- [Fly.io CLI](https://fly.io/docs/getting-started/installing-flyctl/)
- [Vercel CLI](https://vercel.com/cli)

### Deploy

```bash
./deploy.sh
```

This will:
1. Deploy the frontend to Vercel
2. Deploy the API to Fly.io
3. Deploy the worker to Fly.io

### Environment Variables for Production

Set these in your Fly.io dashboard and Vercel dashboard:

**API & Worker:**
- `DATABASE_URL`
- `REDIS_URL` 
- `NEWS_API_KEY`
- `OPENAI_API_KEY`
- `ELEVENLABS_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

**Frontend:**
- `API_BASE_URL` (your API's Fly.io URL)

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │     Worker      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Python)      │
│   Vercel        │    │   Fly.io        │    │   Fly.io        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         │              │   (Supabase)    │              │
         │              └─────────────────┘              │
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│   Supabase      │                            │     Redis       │
│   Storage       │                            │    (Queue)      │
│   (Audio/VTT)   │                            │   (Upstash)     │
└─────────────────┘                            └─────────────────┘
```

## Troubleshooting

### Common Issues

1. **Audio generation fails**: Check ElevenLabs API key and credits
2. **Database connection fails**: Verify DATABASE_URL format
3. **News articles not found**: Check NewsAPI key and quotas
4. **Worker not processing jobs**: Verify Redis connection

### Logs

**Local Development:**
- Check terminal outputs for error messages
- API logs show in the uvicorn terminal
- Worker logs show in the worker terminal

**Production:**
```bash
fly logs -a yourcast-api
fly logs -a yourcast-worker
```

## Performance Notes

- **Cold starts**: First request may take 10-15 seconds
- **Generation time**: 2-5 minutes per 5-minute podcast
- **Costs**: ~$0.10-0.20 per episode (TTS + LLM calls)
- **Limits**: NewsAPI has daily quotas (500/day free tier)