'use client';

import { useState, useRef, useEffect } from 'react';
import { sendChatMessage, getChatSuggestions, ChatMessage, SuggestedQuery } from '../lib/chat-api';
import { colors, severityColor, statusColor } from '@/lib/theme';

/* ── Incident Card rendered inside chat ─────────────────────── */
function IncidentCard({ incident }: { incident: any }) {
  const sev = severityColor(incident.severity);
  const stat = statusColor(incident.status);
  return (
    <div style={{
      padding: 12, borderRadius: 10, marginTop: 6,
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${sev.border || colors.border}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{
          padding: '2px 8px', borderRadius: 5, fontSize: 10, fontWeight: 700,
          background: sev.bg, color: sev.color, textTransform: 'uppercase',
        }}>{incident.severity}</span>
        <span style={{
          padding: '2px 8px', borderRadius: 5, fontSize: 10, fontWeight: 600,
          background: stat.bg, color: stat.color, textTransform: 'uppercase',
        }}>{incident.status}</span>
        {incident.service && (
          <span style={{ fontSize: 11, color: colors.textDim }}>{incident.service}</span>
        )}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', lineHeight: 1.4 }}>
        {incident.title}
      </div>
      {incident.root_cause && (
        <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4, lineHeight: 1.5 }}>
          Root cause: {incident.root_cause}
        </div>
      )}
      {incident.detected_at && (
        <div style={{ fontSize: 10, color: colors.textDim, marginTop: 4 }}>
          {new Date(incident.detected_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}

function StructuredDataBlock({ data }: { data: Record<string, unknown> }) {
  const type = data.type as string;

  if (type === 'incidents' || type === 'diagnostic') {
    const items = (data.incidents || data.active_incidents || []) as any[];
    if (items.length === 0) return null;
    return (
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 11, color: colors.textDim, fontWeight: 600, marginBottom: 4 }}>
          {items.length} incident{items.length !== 1 ? 's' : ''} found
        </div>
        {items.slice(0, 5).map((inc: any, i: number) => (
          <IncidentCard key={inc.id || i} incident={inc} />
        ))}
        {items.length > 5 && (
          <div style={{ fontSize: 11, color: colors.accent, marginTop: 6 }}>
            +{items.length - 5} more incidents...
          </div>
        )}
      </div>
    );
  }

  if (type === 'service_status') {
    const incidents = (data.open_incidents || []) as any[];
    const metrics = (data.metrics || []) as any[];
    return (
      <div style={{ marginTop: 8 }}>
        {incidents.length > 0 && incidents.slice(0, 3).map((inc: any, i: number) => (
          <IncidentCard key={inc.id || i} incident={inc} />
        ))}
        {metrics.length > 0 && (
          <div style={{
            marginTop: 8, padding: 10, borderRadius: 8,
            background: 'rgba(255,255,255,0.03)', border: `1px solid ${colors.border}`,
          }}>
            <div style={{ fontSize: 11, color: colors.textDim, fontWeight: 600, marginBottom: 6 }}>
              Live Metrics
            </div>
            {metrics.slice(0, 5).map((m: any, i: number) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', padding: '3px 0',
                fontSize: 12, color: colors.textSecondary,
              }}>
                <span>{m.service}:{m.metric}</span>
                <span style={{ color: colors.text, fontWeight: 600, fontFamily: 'monospace' }}>
                  {m.value}{m.unit || ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return null;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestedQuery[]>([]);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getChatSuggestions().then(setSuggestions);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: msg, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(msg, sessionId);
      setMessages(prev => [...prev, response]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I couldn\'t process that request. Please try again.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '80vh' }}>
      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: '40px 0' }}>
            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>DevOps AI Assistant</h3>
            <p style={{ fontSize: '14px', marginBottom: '20px' }}>
              Ask me anything about your infrastructure — try natural language queries like &quot;show critical incidents&quot; or &quot;why is the API slow?&quot;
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(s.text)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '20px',
                    border: '1px solid rgba(255,255,255,0.06)',
                    background: 'rgba(255,255,255,0.05)',
                    cursor: 'pointer',
                    fontSize: '13px',
                    color: '#a1a1aa',
                  }}
                >
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div style={{
              maxWidth: msg.structured_data ? '85%' : '75%',
              padding: '10px 14px',
              borderRadius: '12px',
              background: msg.role === 'user' ? '#2563eb' : 'rgba(255,255,255,0.05)',
              color: msg.role === 'user' ? 'white' : '#f0f0f0',
              fontSize: '14px',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
              {msg.structured_data && (
                <StructuredDataBlock data={msg.structured_data} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              padding: '10px 14px',
              borderRadius: '12px',
              background: 'rgba(255,255,255,0.05)',
              color: '#71717a',
              fontSize: '14px',
            }}>
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        gap: '8px',
      }}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your infrastructure..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.06)',
            background: 'rgba(255,255,255,0.05)',
            color: '#f0f0f0',
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            background: loading || !input.trim() ? '#9ca3af' : '#2563eb',
            color: 'white',
            border: 'none',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
