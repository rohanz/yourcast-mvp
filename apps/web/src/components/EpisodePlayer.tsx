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

interface EpisodeSegment {
  id: string;
  episode_id: string;
  start_time: number;
  end_time: number;
  text: string;
  source_id?: string;
  order_index: number;
}

interface Source {
  id: string;
  episode_id: string;
  title: string;
  url: string;
  published_date: string;
  excerpt?: string;
  summary?: string;
}

interface TranscriptEntry {
  start: number;
  end: number;
  text: string;
  source_id?: string;
}

interface EpisodePlayerProps {
  episode: Episode
}

export function EpisodePlayer({ episode }: EpisodePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [segments, setSegments] = useState<EpisodeSegment[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    // Fetch episode segments and sources
    const fetchEpisodeData = async () => {
      try {
        const [segmentsRes, sourcesRes, transcriptRes] = await Promise.all([
          fetch(`/api/episodes/${episode.id}/segments`),
          fetch(`/api/episodes/${episode.id}/sources`),
          episode.transcript_url ? fetch(episode.transcript_url) : Promise.resolve(null)
        ])

        if (segmentsRes.ok) {
          const segmentsData = await segmentsRes.json()
          setSegments(segmentsData)
        }

        if (sourcesRes.ok) {
          const sourcesData = await sourcesRes.json()
          setSources(sourcesData)
        }

        if (transcriptRes && transcriptRes.ok) {
          const transcriptData = await transcriptRes.json()
          setTranscript(transcriptData)
        }
      } catch (error) {
        console.error('Failed to fetch episode data:', error)
      }
    }

    fetchEpisodeData()
  }, [episode.id, episode.transcript_url])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime)
    const handleDurationChange = () => setDuration(audio.duration)
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('durationchange', handleDurationChange)
    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('durationchange', handleDurationChange)
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
    }
  }, [])

  const togglePlayPause = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
  }

  const seekTo = (time: number) => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = time
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const getCurrentSegment = () => {
    return segments.find(
      segment => currentTime >= segment.start_time && currentTime <= segment.end_time
    )
  }

  const currentSegment = getCurrentSegment()

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">{episode.title}</h3>
        <p className="text-gray-600 mb-4">{episode.description}</p>
        
        {episode.audio_url && (
          <div className="space-y-4">
            <audio ref={audioRef} src={episode.audio_url} preload="metadata" />
            
            {/* Player Controls */}
            <div className="flex items-center space-x-4">
              <button
                onClick={togglePlayPause}
                className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full transition-colors"
              >
                {isPlaying ? (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                )}
              </button>
              
              <div className="flex-1">
                <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
                <div
                  className="w-full bg-gray-200 rounded-full h-2 cursor-pointer"
                  onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect()
                    const x = e.clientX - rect.left
                    const percentage = x / rect.width
                    seekTo(percentage * duration)
                  }}
                >
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Chapter Navigation */}
            {segments.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Chapters</h4>
                <div className="space-y-1">
                  {segments.map((segment) => (
                    <button
                      key={segment.id}
                      onClick={() => seekTo(segment.start_time)}
                      className={`w-full text-left p-2 rounded text-sm hover:bg-gray-50 transition-colors ${
                        currentSegment?.id === segment.id ? 'bg-blue-50 text-blue-700' : 'text-gray-600'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <span className="flex-1">{segment.text.slice(0, 100)}...</span>
                        <span className="text-xs ml-2">{formatTime(segment.start_time)}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="border-t bg-gray-50 p-6">
          <h4 className="font-medium text-gray-900 mb-3">Sources</h4>
          <div className="space-y-3">
            {sources.map((source) => (
              <div key={source.id} className="bg-white rounded p-3 border">
                <h5 className="font-medium text-sm text-gray-900 mb-1">
                  <a 
                    href={source.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="hover:text-blue-600 transition-colors"
                  >
                    {source.title}
                  </a>
                </h5>
                <p className="text-xs text-gray-600 mb-2">{source.excerpt}</p>
                <p className="text-xs text-gray-500">
                  {new Date(source.published_date).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}