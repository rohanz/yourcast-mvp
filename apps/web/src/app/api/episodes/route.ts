import { NextRequest, NextResponse } from 'next/server'

interface CreateEpisodeRequest {
  topics: string[];
  duration_minutes: number;
}

interface CreateEpisodeResponse {
  episode_id: string;
  status: string;
}

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body: CreateEpisodeRequest = await request.json()
    
    const response = await fetch(`${API_BASE_URL}/episodes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      throw new Error(`API responded with status ${response.status}`)
    }
    
    const data: CreateEpisodeResponse = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating episode:', error)
    return NextResponse.json(
      { error: 'Failed to create episode' },
      { status: 500 }
    )
  }
}