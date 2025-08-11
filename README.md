# YourCast - Micro-Podcast Generator

An MVP web app that generates short, listenable "micro-podcasts" on demand from news articles.

## Architecture

- **Frontend**: Next.js app (Vercel) with audio player and transcript display
- **Backend API**: FastAPI (Fly.io) with episode endpoints and SSE
- **Workers**: Python job runner with Redis queue
- **Database**: Supabase Postgres
- **Storage**: Supabase Storage for audio/transcripts

## Structure

```
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── workers/
│   └── agent/        # Python podcast generation worker
└── packages/
    └── shared/       # Shared types and utilities
```

## Development

Each app has its own README with setup instructions.