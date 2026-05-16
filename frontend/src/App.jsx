import { useState, useEffect } from 'react'
import ChatWindow from './components/ChatWindow'

const SUGGESTED_QUERIES = [
  "Show me all orders from Alice Chen",
  "List all open support tickets",
  "What are the top 5 most expensive products?",
]

const STORAGE_KEY = 'chatbot_conversations'
const THEME_KEY = 'chatbot_theme'

function loadConversations() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
  } catch { return [] }
}

function saveConversations(convos) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convos))
}

export default function App() {
  const [conversations, setConversations] = useState(() => loadConversations())
  const [activeConvId, setActiveConvId] = useState(null)
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark')

  useEffect(() => { saveConversations(conversations) }, [conversations])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  const getTitle = (msgs) => {
    const first = msgs.find(m => m.role === 'user')
    if (!first) return 'New conversation'
    return first.content.length > 45 ? first.content.slice(0, 45) + '…' : first.content
  }

  const saveCurrentChat = (msgs, convId) => {
    if (!msgs.length) return
    setConversations(prev => {
      const idx = prev.findIndex(c => c.id === convId)
      const entry = { id: convId, title: getTitle(msgs), messages: msgs, updatedAt: new Date().toISOString() }
      if (idx >= 0) { const u = [...prev]; u[idx] = entry; return u }
      return [entry, ...prev]
    })
  }

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return
    const userMsg = { role: 'user', content: text }
    const newMsgs = [...messages, userMsg]
    setMessages(newMsgs)
    setIsLoading(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setConversationId(data.conversation_id)
      const aMsg = { role: 'assistant', content: data.answer, sql: data.sql_used, data: data.data }
      const updated = [...newMsgs, aMsg]
      setMessages(updated)
      saveCurrentChat(updated, data.conversation_id)
      setActiveConvId(data.conversation_id)
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }])
    } finally { setIsLoading(false) }
  }

  const handleNewChat = () => { setMessages([]); setConversationId(null); setActiveConvId(null); setSidebarOpen(false) }
  const handleLoad = (c) => { setMessages(c.messages); setConversationId(c.id); setActiveConvId(c.id); setSidebarOpen(false) }
  const handleDelete = (e, id) => { e.stopPropagation(); setConversations(p => p.filter(c => c.id !== id)); if (activeConvId === id) handleNewChat() }

  return (
    <div className="app">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-logo">⚡</span>
          <h2>Conversations</h2>
          <button className="sidebar-close" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>
        <button className="sidebar-new-chat" onClick={handleNewChat}>+ New Chat</button>
        <div className="sidebar-list">
          {conversations.length === 0 && <p className="sidebar-empty">No history yet</p>}
          {conversations.map(c => (
            <div key={c.id} className={`sidebar-item ${c.id === activeConvId ? 'active' : ''}`} onClick={() => handleLoad(c)}>
              <span className="sidebar-item-title">{c.title}</span>
              <button className="sidebar-item-delete" onClick={e => handleDelete(e, c.id)}>×</button>
            </div>
          ))}
        </div>
      </aside>

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      <div className="main-content">
        <header className="app-header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)} title="History">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
            <div className="header-brand">
              <h1>DataLens</h1>
              <span className="header-tag">AI</span>
            </div>
          </div>
          <div className="header-right">
            <button className="theme-toggle" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} title="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button className="new-chat-btn" onClick={handleNewChat}>+ New</button>
          </div>
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
