import { useState } from 'react'

export default function SqlPreview({ sql }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!sql) return null

  return (
    <div className="sql-preview">
      <button
        className="sql-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
        SQL Query
      </button>
      {isOpen && (
        <pre className="sql-code">
          <code>{sql}</code>
        </pre>
      )}
    </div>
  )
}
