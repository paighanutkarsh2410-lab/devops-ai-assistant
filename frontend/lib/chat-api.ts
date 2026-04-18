const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  intent?: Record<string, unknown>;
  structured_data?: Record<string, unknown> | null;
}

export interface SuggestedQuery {
  text: string;
  category: string;
}

export async function sendChatMessage(
  message: string,
  sessionId: string = 'default'
): Promise<ChatMessage> {
  const res = await fetch(`${API_BASE}/chat/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const data = await res.json();
  return {
    role: 'assistant',
    content: data.answer,
    timestamp: data.timestamp,
    intent: data.intent,
    structured_data: data.structured_data || null,
  };
}

export async function getChatSuggestions(): Promise<SuggestedQuery[]> {
  try {
    const res = await fetch(`${API_BASE}/chat/suggestions`);
    if (!res.ok) return defaultSuggestions();
    return await res.json();
  } catch {
    return defaultSuggestions();
  }
}

function defaultSuggestions(): SuggestedQuery[] {
  return [
    { text: 'System status?', category: 'status' },
    { text: 'Show recent incidents', category: 'incidents' },
    { text: 'Any predictions?', category: 'predictions' },
    { text: 'Cost forecast', category: 'predictions' },
  ];
}
