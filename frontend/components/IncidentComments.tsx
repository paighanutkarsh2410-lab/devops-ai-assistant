'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Comment {
  id: string;
  user_id: string;
  comment_text: string;
  created_at: string;
  edited_at: string | null;
}

interface Props {
  incidentId: string;
}

export default function IncidentComments({ incidentId }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadComments();
  }, [incidentId]);

  const loadComments = async () => {
    try {
      const res = await api.get(`/incidents/${incidentId}/comments`);
      setComments(res.data);
    } catch {
      // silently fail
    }
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/incidents/${incidentId}/comments`, { comment_text: newComment });
      setNewComment('');
      loadComments();
    } catch {
      // handle error
    } finally {
      setSubmitting(false);
    }
  };

  const deleteComment = async (id: string) => {
    try {
      await api.delete(`/comments/${id}`);
      setComments(prev => prev.filter(c => c.id !== id));
    } catch {
      // handle error
    }
  };

  return (
    <div style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#f0f0f0' }}>
        Comments ({comments.length})
      </h3>

      {/* Comment list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {comments.map(c => (
          <div key={c.id} style={{
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                {new Date(c.created_at).toLocaleString()}
                {c.edited_at && ' (edited)'}
              </span>
              <button
                onClick={() => deleteComment(c.id)}
                aria-label="Delete comment"
                style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '12px' }}
              >
                Delete
              </button>
            </div>
            <p style={{ fontSize: '14px', margin: 0, whiteSpace: 'pre-wrap', color: '#f0f0f0' }}>{c.comment_text}</p>
          </div>
        ))}
        {comments.length === 0 && (
          <p style={{ color: '#9ca3af', fontSize: '13px', textAlign: 'center', padding: '16px' }}>
            No comments yet. Be the first to add one.
          </p>
        )}
      </div>

      {/* Add comment */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <textarea
          value={newComment}
          onChange={e => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          aria-label="Comment text"
          onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) submitComment(); }}
          style={{
            flex: 1,
            padding: '10px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.06)',
            background: 'rgba(255,255,255,0.05)',
            color: '#f0f0f0',
            fontSize: '14px',
            resize: 'vertical',
            minHeight: '60px',
          }}
        />
        <button
          onClick={submitComment}
          disabled={submitting || !newComment.trim()}
          style={{
            padding: '10px 20px',
            background: submitting ? '#93c5fd' : '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: submitting ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            alignSelf: 'flex-end',
          }}
        >
          {submitting ? 'Sending...' : 'Send'}
        </button>
      </div>
      <p style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>Ctrl+Enter to send</p>
    </div>
  );
}
