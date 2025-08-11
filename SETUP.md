# YourCast - Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Redis server (or Docker for Redis)

## Required API Keys

You'll need to obtain these API keys:

1. **NewsAPI Key**: Get from [newsapi.org](https://newsapi.org/register)
2. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey) (free!)
3. **Google TTS API Key**: Get from [Google Cloud Console](https://console.cloud.google.com/) (see setup below)

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

### 2. Google Cloud TTS API Key Setup

**Simple API key setup:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable the Text-to-Speech API:
   - Go to APIs & Services → Library
   - Search for "Text-to-Speech API"
   - Click Enable
4. Create an API key:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → API Key
   - Copy your API key (starts with `AIzaSy...`)
   - (Optional) Restrict the key to Text-to-Speech API only

### 3. Database Setup

The app uses SQLite by default, so no database setup is required! The database file (`yourcast.db`) will be created automatically when you first run the API.

**Storage**: Audio files, transcripts, and VTT files are stored locally in a `./storage` directory.

### 4. Environment Variables

Copy the example files and fill in your values:

```bash
cp apps/api/.env.example apps/api/.env
cp workers/agent/.env.example workers/agent/.env
```

Edit the `.env` files with your actual API keys:
- `NEWS_API_KEY`: Your NewsAPI key
- `GEMINI_API_KEY`: Your Gemini API key (from Google AI Studio)
- `GOOGLE_TTS_API_KEY`: Your Google Cloud TTS API key

**Example:**
```bash
NEWS_API_KEY=1a2b3c4d5e6f7g8h9i0j
GEMINI_API_KEY=AIzaSyDhYmP4uM8cB9fG7kL3nQ2rS5tU6vW8xY1z
GOOGLE_TTS_API_KEY=AIzaSyBcDeFgHiJkLmNoPqRsTuVwXyZ123456789
```

The database and storage paths can be left as defaults for local development.

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