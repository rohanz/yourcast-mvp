'use client'

import { useState, useRef, useEffect } from 'react'

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

interface CreateEpisodeRequest {
  topics: string[];
  duration_minutes: number;
}

interface CreateEpisodeFormProps {
  onEpisodeCreated: (episode: Episode) => void
}

const TOPIC_OPTIONS = [
  'Technology',
  'Science',
  'Politics',
  'Business',
  'Health',
  'Sports',
  'Entertainment',
  'World News',
]

export function CreateEpisodeForm({ onEpisodeCreated }: CreateEpisodeFormProps) {
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const toggleTopic = (topic: string) => {
    if (selectedTopics.includes(topic)) {
      setSelectedTopics(selectedTopics.filter(t => t !== topic))
    } else if (selectedTopics.length < 3) {
      setSelectedTopics([...selectedTopics, topic])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (selectedTopics.length === 0) {
      setError('Please select at least one topic')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      const request: CreateEpisodeRequest = {
        topics: selectedTopics,
        duration_minutes: 5
      }

      const response = await fetch('/api/episodes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error('Failed to create episode')
      }

      const { episode_id } = await response.json()
      
      // Poll for episode completion with proper cleanup
      let retryCount = 0
      const maxRetries = 150 // 5 minutes max (150 * 2 seconds)
      
      const pollForCompletion = async () => {
        try {
          if (retryCount >= maxRetries) {
            setError('Episode generation timed out. Please try again.')
            setIsGenerating(false)
            timeoutRef.current = null
            return
          }

          const episodeResponse = await fetch(`/api/episodes/${episode_id}`)
          
          if (!episodeResponse.ok) {
            throw new Error(`HTTP ${episodeResponse.status}: ${episodeResponse.statusText}`)
          }
          
          const episode: Episode = await episodeResponse.json()
          
          console.log(`Poll attempt ${retryCount + 1}/${maxRetries}: Episode status is "${episode.status}"`);
          
          if (episode.status === 'completed') {
            console.log('Episode generation completed successfully')
            onEpisodeCreated(episode)
            setIsGenerating(false)
            timeoutRef.current = null
          } else if (episode.status === 'failed') {
            console.log('Episode generation failed')
            setError('Failed to generate podcast. Please try again.')
            setIsGenerating(false)
            timeoutRef.current = null
          } else {
            // Episode is still pending or processing
            retryCount++
            
            // Add warning for episodes stuck too long in pending status
            if (episode.status === 'pending' && retryCount > 30) { // After 1 minute
              console.warn(`Episode has been pending for ${retryCount * 2} seconds. This may indicate a backend processing issue.`)
            }
            
            timeoutRef.current = setTimeout(pollForCompletion, 2000)
          }
        } catch (error) {
          console.error('Failed to check episode status:', error)
          setError(`Failed to check episode status: ${error instanceof Error ? error.message : 'Unknown error'}`)
          setIsGenerating(false)
          timeoutRef.current = null
        }
      }
      
      timeoutRef.current = setTimeout(pollForCompletion, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsGenerating(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Select Topics (1-3)
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {TOPIC_OPTIONS.map((topic) => (
              <button
                key={topic}
                type="button"
                onClick={() => toggleTopic(topic)}
                className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                  selectedTopics.includes(topic)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                } ${
                  !selectedTopics.includes(topic) && selectedTopics.length >= 3
                    ? 'opacity-50 cursor-not-allowed'
                    : 'cursor-pointer'
                }`}
                disabled={!selectedTopics.includes(topic) && selectedTopics.length >= 3}
              >
                {topic}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Selected: {selectedTopics.length}/3
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duration
          </label>
          <div className="p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">5 minutes (fixed for MVP)</span>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={selectedTopics.length === 0 || isGenerating}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? 'Generating Podcast...' : 'Generate Podcast'}
        </button>
      </form>
    </div>
  )
}