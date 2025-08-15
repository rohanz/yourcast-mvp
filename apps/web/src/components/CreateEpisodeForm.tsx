'use client'

import { useState, useRef, useEffect } from 'react'
import { flushSync } from 'react-dom'

interface Episode {
  id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  categories: string[];
  status: string;
  audio_url?: string;
  transcript_url?: string;
  vtt_url?: string;
  created_at: string;
}

interface CreateEpisodeRequest {
  subcategories: string[];
  duration_minutes: number;
}

interface CreateEpisodeFormProps {
  onEpisodeCreated: (episode: Episode) => void
}

interface Category {
  category: string;
  subcategories: Subcategory[];
  total_articles: number;
  avg_importance: number;
  max_importance: number;
}

interface Subcategory {
  subcategory: string;
  article_count: number;
  avg_importance: number;
  max_importance: number;
  latest_article: string | null;
}

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
  const [selectedSubcategories, setSelectedSubcategories] = useState<string[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoadingCategories, setIsLoadingCategories] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stageMessage, setStageMessage] = useState<string>('')
  
  const eventSourceRef = useRef<EventSource | null>(null)
  const completedRef = useRef(false)

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('/api/categories')
        if (!response.ok) {
          throw new Error('Failed to fetch categories')
        }
        const data = await response.json()
        setCategories(data.categories || [])
      } catch (err) {
        setError('Failed to load categories. Please refresh the page.')
      } finally {
        setIsLoadingCategories(false)
      }
    }
    fetchCategories()
  }, [])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  // Helper function to get subcategories for a category
  const getSubcategoriesForCategory = (categoryName: string): string[] => {
    const category = categories.find(cat => cat.category === categoryName)
    return category ? category.subcategories.map(sub => sub.subcategory) : []
  }

  // Check if all subcategories of a category are selected
  const isCategoryFullySelected = (categoryName: string): boolean => {
    const subcats = getSubcategoriesForCategory(categoryName)
    return subcats.length > 0 && subcats.every(sub => selectedSubcategories.includes(sub))
  }

  // Get total selection count for limit checking
  const getTotalSelectionCount = () => {
    return selectedSubcategories.length
  }

  const toggleCategory = (categoryName: string) => {
    const subcats = getSubcategoriesForCategory(categoryName)
    const isFullySelected = isCategoryFullySelected(categoryName)
    
    if (isFullySelected) {
      // Deselect all subcategories of this category
      setSelectedSubcategories(selectedSubcategories.filter(sub => !subcats.includes(sub)))
    } else {
      // Select all subcategories of this category (if we have room)
      const newSelections = subcats.filter(sub => !selectedSubcategories.includes(sub))
      const wouldExceedLimit = selectedSubcategories.length + newSelections.length > 10
      
      if (!wouldExceedLimit) {
        setSelectedSubcategories([...selectedSubcategories, ...newSelections])
      }
    }
  }

  const toggleSubcategory = (subcategoryName: string) => {
    if (selectedSubcategories.includes(subcategoryName)) {
      // Deselect the subcategory
      setSelectedSubcategories(selectedSubcategories.filter(sub => sub !== subcategoryName))
    } else {
      if (selectedSubcategories.length < 10) { // Allow up to 10 subcategories
        // Select the subcategory
        setSelectedSubcategories([...selectedSubcategories, subcategoryName])
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (selectedSubcategories.length === 0) {
      setError('Please select at least one subcategory')
      return
    }

    setIsGenerating(true)
    setError(null)
    setStageMessage('Leafing through the newspapers...')
    completedRef.current = false

    try {
      const request: CreateEpisodeRequest = {
        subcategories: selectedSubcategories,
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
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Select Categories or Subcategories (up to 10)
          </label>
          <p className="text-xs text-gray-600 mb-4">
            Click category headers to select all subcategories, or choose individual subcategories.
          </p>
          
          {isLoadingCategories ? (
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="border rounded-lg p-4 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded mb-3 w-1/3"></div>
                  <div className="grid grid-cols-2 gap-2">
                    {[...Array(4)].map((_, j) => (
                      <div key={j} className="h-8 bg-gray-200 rounded"></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : categories.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-2">No categories available</p>
              <p className="text-sm text-gray-400">Try running RSS discovery to populate articles</p>
            </div>
          ) : (
            <div className="space-y-6">
              {categories.map((category) => {
                const categoryFullySelected = isCategoryFullySelected(category.category)
                const hasSelectedSubcats = category.subcategories.some(sub => 
                  selectedSubcategories.includes(sub.subcategory)
                )
                
                return (
                  <div key={category.category} className="border rounded-lg p-4">
                    {/* Category Header Button */}
                    <button
                      type="button"
                      onClick={() => toggleCategory(category.category)}
                      className={`w-full p-3 rounded-lg border text-sm font-medium transition-colors text-left mb-3 ${
                        categoryFullySelected
                          ? 'bg-blue-600 text-white border-blue-600'
                          : hasSelectedSubcats
                          ? 'bg-orange-100 text-orange-800 border-orange-300'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold mb-1">📁 {category.category}</div>
                          <div className={`text-xs ${
                            categoryFullySelected ? 'text-blue-200' 
                            : hasSelectedSubcats ? 'text-orange-600' 
                            : 'text-gray-500'
                          }`}>
                            {category.total_articles} articles • ⭐ {category.avg_importance.toFixed(1)}
                          </div>
                        </div>
                        {categoryFullySelected && (
                          <div className="text-blue-200 text-xs">✓ All Selected</div>
                        )}
                        {hasSelectedSubcats && !categoryFullySelected && (
                          <div className="text-orange-600 text-xs">Some Selected</div>
                        )}
                      </div>
                    </button>
                    
                    {/* Subcategories Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {category.subcategories.map((subcategory) => {
                        const subcatSelected = selectedSubcategories.includes(subcategory.subcategory)
                        
                        return (
                          <button
                            key={subcategory.subcategory}
                            type="button"
                            onClick={() => toggleSubcategory(subcategory.subcategory)}
                            className={`p-2 rounded border text-xs font-medium transition-colors text-left ${
                              subcatSelected
                                ? 'bg-green-500 text-white border-green-500'
                                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            } ${
                              !subcatSelected && getTotalSelectionCount() >= 10
                                ? 'opacity-50 cursor-not-allowed'
                                : 'cursor-pointer'
                            }`}
                            disabled={!subcatSelected && getTotalSelectionCount() >= 10}
                          >
                            <div className="font-medium">{subcategory.subcategory}</div>
                            <div className={`text-xs mt-1 ${
                              subcatSelected ? 'text-green-200' : 'text-gray-500'
                            }`}>
                              {subcategory.article_count} • ⭐{subcategory.avg_importance.toFixed(1)}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">
                Selected: {getTotalSelectionCount()}/10 subcategories
              </span>
              <span className="text-gray-600">
                {getTotalSelectionCount() === 0 ? 'None selected' : 'Ready to generate podcast'}
              </span>
            </div>
            {selectedSubcategories.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {selectedSubcategories.map(sub => (
                  <span key={sub} className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                    {sub}
                  </span>
                ))}
              </div>
            )}
          </div>
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
          disabled={selectedSubcategories.length === 0 || isGenerating}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? 'Generating Podcast...' : 'Generate Podcast'}
        </button>
      </form>
    </div>
  )
}