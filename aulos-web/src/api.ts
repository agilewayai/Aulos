export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export type ChatResponse = {
  reply: string
  thread_id: string
  source: string
}

const apiBase = import.meta.env.VITE_AULOS_API_BASE ?? ''

export async function sendChat(
  message: string,
  threadId: string,
): Promise<ChatResponse> {
  const response = await fetch(`${apiBase}/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  })
  if (!response.ok) {
    throw new Error(`Chat failed (${response.status})`)
  }
  return response.json() as Promise<ChatResponse>
}
