#!/bin/bash

# YourCast Deployment Script

set -e

echo "🚀 Deploying YourCast..."

# Check if required commands exist
command -v fly >/dev/null 2>&1 || { echo "❌ fly CLI is required but not installed. Install from https://fly.io/docs/getting-started/installing-flyctl/" >&2; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo "❌ vercel CLI is required but not installed. Run: npm i -g vercel" >&2; exit 1; }

echo "📦 Building shared packages..."
cd packages/shared
npm run build
cd ../..

echo "🌐 Deploying frontend to Vercel..."
cd apps/web
vercel --prod
cd ../..

echo "🔧 Deploying API to Fly.io..."
cd apps/api
fly deploy
cd ../..

echo "⚡ Deploying worker to Fly.io..."
cd workers/agent
fly deploy
cd ../..

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Set up your environment variables in Fly.io dashboard"
echo "2. Run the database schema in your Supabase dashboard"
echo "3. Create a 'podcasts' storage bucket in Supabase"
echo "4. Configure your API keys (NewsAPI, OpenAI, ElevenLabs)"
echo ""
echo "Your YourCast app should now be live! 🎉"