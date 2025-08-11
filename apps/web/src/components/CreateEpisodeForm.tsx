'use client'

import { useState, useRef, useEffect } from 'react'
import { flushSync } from 'react-dom'

// Interfaces and TOPIC_OPTIONS remain the same...
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
  'Technology', 'Science', 'Politics', 'Business', 'Health', 'Sports', 'Entertainment', 'World News',
]

function getStageMessage(stage: string): string {
  switch (stage) {
    case 'Starting...':
    case 'discovering_articles':
    case 'pending':
      return 'Leafing through the newspapers...'
    case 'extracting_content':
      return 'Picking your favourite articles...'
    case 'generating_script':
      return 'Writing the perfect script...'
    case 'generating_audio':
      return 'Recording the podcast in the studio...'
    case 'generating_timestamps':
    case 'uploading_files':
    case 'finalizing':
      return 'Sending it over to you...'
    case 'completed':
      return 'Ready to listen!'
    default:
      return 'Leafing through the newspapers...'
  }
}

export function CreateEpisodeForm({ onEpisodeCreated }: CreateEpisodeFormProps) {
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stageMessage, setStageMessage] = useState<string>('')
  
  const eventSourceRef = useRef<EventSource | null>(null)
  const completedRef = useRef(false)

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
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
    setStageMessage('Leafing through the newspapers...')
    completedRef.current = false

    try {
      const request: CreateEpisodeRequest = {
        topics: selectedTopics,
        duration_minutes: 5
      }

      const response = await fetch('/api/episodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error('Failed to create episode')
      }

      const { episode_id } = await response.json()
      
      const eventSource = new EventSource(`http://localhost:8000/episodes/${episode_id}/events`)
      eventSourceRef.current = eventSource
      
      console.log('🔌 SSE connection opened for episode:', episode_id)
      
      eventSource.onopen = () => {
        console.log('✅ SSE connection established')
      }
      
      eventSource.onmessage = (event) => {
        console.log('📨 SSE message received:', event.data)

        try {
          const statusData = JSON.parse(event.data)
          
          // ✨ FIX #2: Use flushSync to force immediate React updates
          // This bypasses React 18's automatic batching for SSE updates
          if (statusData.stage) {
            console.log('🔄 Updating stage to:', statusData.stage)
            const newMessage = getStageMessage(statusData.stage)
            console.log('📝 Setting stage message to:', newMessage)
            flushSync(() => {
              setStageMessage(newMessage)
            })
            console.log('✅ Stage message updated')
          }
          
          if (statusData.status === 'completed') {
            completedRef.current = true
            flushSync(() => {
              setStageMessage('Ready to listen!')
            })
            
            fetch(`/api/episodes/${episode_id}`)
              .then(res => res.json())
              .then((episode: Episode) => {
                onEpisodeCreated(episode)
                setIsGenerating(false)
                if (eventSourceRef.current) {
                  eventSourceRef.current.close()
                  eventSourceRef.current = null
                }
              })
              .catch((err) => {
                setError('Episode completed but failed to load details')
                setIsGenerating(false)
                if (eventSourceRef.current) {
                  eventSourceRef.current.close()
                  eventSourceRef.current = null
                }
              })

          } else if (statusData.status === 'failed') {
            flushSync(() => {
              setError(statusData.error || 'Failed to generate podcast. Please try again.')
              setIsGenerating(false)
            })
            if (eventSourceRef.current) {
              eventSourceRef.current.close()
              eventSourceRef.current = null
            }
          }

        } catch (err) {
          flushSync(() => {
            setError('Received invalid status update')
          })
        }
      }
      
      // Handle SSE connection errors (but only show error if not completed)
      eventSource.onerror = (error) => {
        // Don't log error if episode completed successfully (connection closed normally)
        if (!completedRef.current) {
          console.log('❌ SSE connection error:', error)
          setTimeout(() => {
            if (!completedRef.current) {
              setError('Lost connection to server. Please refresh and try again.')
              setIsGenerating(false)
            }
            if (eventSourceRef.current) {
              eventSourceRef.current.close()
              eventSourceRef.current = null
            }
          }, 100)
        } else {
          // Episode completed, connection closed normally
          if (eventSourceRef.current) {
            eventSourceRef.current.close()
            eventSourceRef.current = null
          }
        }
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsGenerating(false)
    }
  }
  
  // The JSX for the return statement remains identical to the previous answer.
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

        {isGenerating && (
          <div className="p-8 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-center">
            <div className="space-y-4">
              <div className="animate-pulse">
                <div className="w-8 h-8 bg-blue-600 rounded-full mx-auto mb-4 animate-bounce"></div>
                <h3 className="text-lg font-semibold text-blue-900 mb-2">Creating Your Podcast...</h3>
                <div key={stageMessage} className="transition-all duration-1000 ease-in-out animate-fade-in">
                  <p className="text-blue-700 text-base font-medium">
                    {stageMessage}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

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