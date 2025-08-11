'use client'

import { useState } from 'react'
import { CreateEpisodeForm } from '@/components/CreateEpisodeForm'
import { EpisodePlayer } from '@/components/EpisodePlayer'

interface Episode {
  id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  topics: string[];
  status: string;
  audio_url?: string;
  transcript_url?: string;
  vtt_url?: string;
  created_at: string;
}

export default function Home() {
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null)

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Create Your Micro-Podcast
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Select 1-3 topics and we'll generate a 5-minute podcast from the latest news articles.
        </p>
      </div>
      
      <CreateEpisodeForm onEpisodeCreated={setCurrentEpisode} />
      
      {currentEpisode && (
        <div className="mt-8">
          <EpisodePlayer episode={currentEpisode} />
        </div>
      )}
    </div>
  )
}