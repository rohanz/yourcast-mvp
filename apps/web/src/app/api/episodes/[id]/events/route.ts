export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const episodeId = params.id

  try {
    // Proxy the SSE connection to the Python API
    const response = await fetch(`http://localhost:8000/episodes/${episodeId}/events`, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    // Return the stream directly with proper headers
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  } catch (error) {
    console.error('Failed to proxy SSE request:', error)
    
    // Return error event
    const errorEvent = `data: ${JSON.stringify({
      episode_id: episodeId,
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    })}\n\n`
    
    return new Response(errorEvent, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    })
  }
}
