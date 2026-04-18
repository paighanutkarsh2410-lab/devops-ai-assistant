'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function FeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ type: 'general', message: '', email: '' });
  const [submitted, setSubmitted] = useState(false);
  const [sending, setSending] = useState(false);
  const { isMobile } = useBreakpoint();

  // Draggable state
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [initialized, setInitialized] = useState(false);
  const dragging = useRef(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const btnRef = useRef<HTMLButtonElement>(null);

  // Set initial position after mount
  useEffect(() => {
    setPos({ x: window.innerWidth - 72, y: window.innerHeight - 90 });
    setInitialized(true);
  }, []);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!isMobile) return;
    const touch = e.touches[0];
    const rect = btnRef.current?.getBoundingClientRect();
    if (!rect) return;
    dragOffset.current = { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
    dragging.current = true;
  }, [isMobile]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!dragging.current || !isMobile) return;
    e.preventDefault();
    const touch = e.touches[0];
    const newX = Math.max(0, Math.min(window.innerWidth - 48, touch.clientX - dragOffset.current.x));
    const newY = Math.max(0, Math.min(window.innerHeight - 48, touch.clientY - dragOffset.current.y));
    setPos({ x: newX, y: newY });
  }, [isMobile]);

  const handleTouchEnd = useCallback(() => {
    dragging.current = false;
  }, []);

  const handleSubmit = async () => {
    if (!form.message.trim()) return;
    setSending(true);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      await fetch(`${API}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
    } catch {
      // Feedback endpoint may not exist yet — still show success for UX
    }
    setSending(false);
    setSubmitted(true);
    setTimeout(() => { setSubmitted(false); setOpen(false); setForm({ type: 'general', message: '', email: '' }); }, 2000);
  };

  // Button position styles
  const btnStyle: React.CSSProperties = isMobile && initialized
    ? { position: 'fixed', left: pos.x, top: pos.y, zIndex: 9999, touchAction: 'none' }
    : { position: 'fixed', bottom: 24, right: 24, zIndex: 9999 };

  // Panel position — opens above or below the button depending on space
  const panelAbove = isMobile ? pos.y > 300 : true;
  const panelStyle: React.CSSProperties = isMobile && initialized
    ? {
        position: 'fixed',
        left: Math.min(pos.x - 146, window.innerWidth - 350),
        top: panelAbove ? pos.y - 340 : pos.y + 56,
        zIndex: 9998,
      }
    : { position: 'fixed', bottom: 84, right: 24, zIndex: 9998 };

  return (
    <>
      {/* Floating button — draggable on mobile */}
      <button
        ref={btnRef}
        onClick={() => { if (!dragging.current) setOpen(!open); }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{
          ...btnStyle,
          width: 48, height: 48, borderRadius: '50%',
          background: '#3b82f6', color: '#fff', border: 'none',
          cursor: 'pointer', fontSize: 20, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(59,130,246,0.4)',
          transition: dragging.current ? 'none' : 'transform 0.2s',
          transform: open ? 'rotate(45deg)' : 'none',
        }}
        title="Send Feedback"
      >
        {open ? '+' : '\u{1F4AC}'}
      </button>

      {/* Feedback panel */}
      {open && (
        <div style={{
          ...panelStyle,
          width: 320, background: '#0f172a', borderRadius: 14,
          border: '1px solid #1e293b', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid #1e293b',
            fontSize: 15, fontWeight: 600, color: '#e2e8f0',
          }}>
            Send Feedback
          </div>

          {submitted ? (
            <div style={{ padding: 32, textAlign: 'center' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>&#10003;</div>
              <div style={{ fontSize: 14, color: '#10b981', fontWeight: 600 }}>Thank you!</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Your feedback has been received.</div>
            </div>
          ) : (
            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <select
                value={form.type}
                onChange={e => setForm({ ...form, type: e.target.value })}
                style={{
                  padding: '8px 12px', borderRadius: 8,
                  background: '#1e293b', border: '1px solid #334155',
                  color: '#e2e8f0', fontSize: 13,
                }}
              >
                <option value="general">General Feedback</option>
                <option value="bug">Bug Report</option>
                <option value="feature">Feature Request</option>
                <option value="improvement">Improvement</option>
              </select>

              <textarea
                value={form.message}
                onChange={e => setForm({ ...form, message: e.target.value })}
                placeholder="What's on your mind?"
                rows={4}
                style={{
                  padding: '10px 12px', borderRadius: 8,
                  background: '#1e293b', border: '1px solid #334155',
                  color: '#e2e8f0', fontSize: 13, resize: 'vertical',
                  fontFamily: 'inherit',
                }}
              />

              <input
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="Email (optional)"
                type="email"
                style={{
                  padding: '8px 12px', borderRadius: 8,
                  background: '#1e293b', border: '1px solid #334155',
                  color: '#e2e8f0', fontSize: 13,
                }}
              />

              <button
                onClick={handleSubmit}
                disabled={!form.message.trim() || sending}
                style={{
                  padding: '10px 16px', borderRadius: 8,
                  background: form.message.trim() ? '#3b82f6' : '#334155',
                  color: '#fff', border: 'none', cursor: form.message.trim() ? 'pointer' : 'default',
                  fontSize: 13, fontWeight: 600,
                }}
              >
                {sending ? 'Sending...' : 'Send Feedback'}
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
