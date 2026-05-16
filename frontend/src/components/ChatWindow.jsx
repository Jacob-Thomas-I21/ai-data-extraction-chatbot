import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import SqlPreview from './SqlPreview'

const CAPABILITY_CARDS = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
    title: 'E-Commerce',
    desc: 'Orders, products, categories',
    color: 'blue',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
    title: 'Support',
    desc: 'Tickets, agents, interactions',
    color: 'green',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><path d="M16 12l-4-4-4 4" /><path d="M12 16V8" />
      </svg>
    ),
    title: 'Cross-Domain',
    desc: 'Combine both in one query',
    color: 'purple',
  },
]

export default function ChatWindow({ messages, isLoading, onSend, suggestedQueries }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Auto-resize textarea
  const autoResize = (el) => {
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    onSend(input.trim())
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    autoResize(e.target)
  }

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-state">
            {/* Animated orb */}
            <div className="welcome-orb">
              <div className="orb-ring orb-ring-1" />
              <div className="orb-ring orb-ring-2" />
              <div className="orb-core">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
            </div>

            <h2 className="welcome-title">
              What would you like to <span className="gradient-text">explore</span>?
            </h2>
            <p className="welcome-desc">
              Ask questions about customers, orders, tickets, and more — powered by AI
            </p>

            {/* Capability cards */}
            <div className="capability-cards">
              {CAPABILITY_CARDS.map((card, i) => (
                <div key={i} className={`capability-card card-${card.color}`}>
                  <div className="capability-icon">{card.icon}</div>
                  <div>
                    <div className="capability-title">{card.title}</div>
                    <div className="capability-desc">{card.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Suggestion grid */}
            {suggestedQueries.length > 0 && (
              <div className="suggestion-grid">
                {suggestedQueries.map((query, i) => (
                  <button
                    key={i}
                    className="suggestion-card"
                    onClick={() => onSend(query)}
                  >
                    <span className="suggestion-arrow">→</span>
                    <span>{query}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? (
                <span className="avatar-letter">Y</span>
              ) : (
                <div className="avatar-ai">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
              )}
            </div>
            <div className="message-body">
              {msg.role === 'user' && <div className="message-label">You</div>}
              {msg.role === 'assistant' && <div className="message-label">AI Assistant</div>}
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    {msg.sql && <SqlPreview sql={msg.sql} />}
                  </>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">
              <div className="avatar-ai pulsing">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
            </div>
            <div className="message-body">
              <div className="message-label">AI Assistant</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-text">Analyzing your query</div>
                  <div className="typing-dots">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="input-area">
        <form className="input-bar" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              ref={(el) => { inputRef.current = el; textareaRef.current = el }}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your data..."
              rows={1}
              disabled={isLoading}
              id="chat-input"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              id="send-button"
              title="Send message"
              className={input.trim() ? 'active' : ''}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </div>
          <div className="input-footer">
            <span>Press Enter to send · Shift+Enter for new line</span>
          </div>
        </form>
      </div>
    </div>
  )
}
