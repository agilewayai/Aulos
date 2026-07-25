import { useEffect, useRef, useState } from 'react'
import { sendChat, type ChatMessage } from './api'
import './App.css'

const THREAD_ID = 'web-default'

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Aulos is ready. Ask anything — replies route through the API gateway.',
    },
  ])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy) return

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
    }
    setMessages((prev) => [...prev, userMsg])
    setDraft('')
    setBusy(true)
    setError(null)

    try {
      const result = await sendChat(text, THREAD_ID)
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: result.reply,
        },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="shell">
      <div className="atmosphere" aria-hidden="true" />
      <header className="top">
        <p className="brand">Aulos</p>
        <p className="tagline">Operator console for the agent gateway</p>
      </header>

      <main className="stage">
        <section className="transcript" aria-live="polite">
          {messages.map((msg) => (
            <article
              key={msg.id}
              className={`bubble bubble-${msg.role}`}
              data-role={msg.role}
            >
              <span className="role">{msg.role === 'user' ? 'You' : 'Aulos'}</span>
              <p>{msg.content}</p>
            </article>
          ))}
          {busy ? <p className="thinking">Thinking…</p> : null}
          <div ref={endRef} />
        </section>

        <form className="composer" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="prompt">
            Message
          </label>
          <textarea
            id="prompt"
            rows={2}
            value={draft}
            placeholder="Message Aulos…"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void onSubmit(e)
              }
            }}
          />
          <button type="submit" disabled={busy || !draft.trim()}>
            Send
          </button>
        </form>
        {error ? <p className="error">{error}</p> : null}
      </main>
    </div>
  )
}

export default App
