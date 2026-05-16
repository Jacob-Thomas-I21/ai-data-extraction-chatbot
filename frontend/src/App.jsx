import { useState, useEffect } from 'react'
import ChatWindow from './components/ChatWindow'

const SUGGESTED_QUERIES = [
  "Show me all orders from Alice Chen",
  "List all open support tickets",
  "What are the top 5 most expensive products?",
]

// ─── localStorage helpers ────────────────────────────────────────────────────

const STORAGE_KEY = 'chatbot_conversations'

function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveConversations(convos) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convos))
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [conversations, setConversations] = useState(() => loadConversations())
  const [activeConvId, setActiveConvId] = useState(null)
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Persist conversations to localStorage whenever they change
  useEffect(() => {
    saveConversations(conversations)
  }, [conversations])

  // Get title from first user message
  const getTitle = (msgs) => {
    const first = msgs.find(m => m.role === 'user')
    if (!first) return 'New conversation'
    return first.content.length > 50
      ? first.content.slice(0, 50) + '...'
      : first.content
  }

  // Save current chat to conversations list
  const saveCurrentChat = (msgs, convId) => {
    if (msgs.length === 0) return

    setConversations(prev => {
      const existing = prev.findIndex(c => c.id === convId)
      const entry = {
        id: convId,
        title: getTitle(msgs),
        messages: msgs,
        updatedAt: new Date().toISOString(),
      }
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = entry
        return updated
      }
      return [entry, ...prev]
    })
  }

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return

    const userMsg = { role: 'user', content: text }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)

      const data = await res.json()
      setConversationId(data.conversation_id)

      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        sql: data.sql_used,
        data: data.data,
      }
      const updatedMessages = [...newMessages, assistantMsg]
      setMessages(updatedMessages)
      saveCurrentChat(updatedMessages, data.conversation_id)
      setActiveConvId(data.conversation_id)
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Sorry, something went wrong: ${err.message}. Please try again.`,
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setConversationId(null)
    setActiveConvId(null)
    setSidebarOpen(false)
  }

  const handleLoadConversation = (convo) => {
    setMessages(convo.messages)
    setConversationId(convo.id)
    setActiveConvId(convo.id)
    setSidebarOpen(false)
  }

  const handleDeleteConversation = (e, convoId) => {
    e.stopPropagation()
    setConversations(prev => prev.filter(c => c.id !== convoId))
    if (activeConvId === convoId) {
      handleNewChat()
    }
  }

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>History</h2>
          <button className="sidebar-close" onClick={() => setSidebarOpen(false)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <button className="sidebar-new-chat" onClick={handleNewChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>

        <div className="sidebar-list">
          {conversations.length === 0 && (
            <p className="sidebar-empty">No conversations yet</p>
          )}
          {conversations.map(convo => (
            <div
              key={convo.id}
              className={`sidebar-item ${convo.id === activeConvId ? 'active' : ''}`}
              onClick={() => handleLoadConversation(convo)}
            >
              <span className="sidebar-item-title">{convo.title}</span>
              <button
                className="sidebar-item-delete"
                onClick={(e) => handleDeleteConversation(e, convo.id)}
                title="Delete conversation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Main content */}
      <div className="main-content">
        <header className="app-header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)} title="Toggle history">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="logo">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div>
              <h1>Data Extraction Chatbot</h1>
              <p className="subtitle">Query e-commerce & support data with natural language</p>
            </div>
          </div>
          <button className="new-chat-btn" onClick={handleNewChat} title="Start new conversation">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Chat
          </button>
        </header>

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          suggestedQueries={messages.length === 0 ? SUGGESTED_QUERIES : []}
        />
      </div>
    </div>
  )
}
