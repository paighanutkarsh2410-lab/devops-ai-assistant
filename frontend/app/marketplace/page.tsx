'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

const TYPE_COLORS: Record<string, string> = {
  agent: '#8b5cf6', plugin: colors.accent, integration: '#06b6d4',
  workflow: colors.success, dashboard: colors.warning, report: '#f97316',
};

export default function MarketplacePage() {
  const [items, setItems] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('downloads');
  const [installing, setInstalling] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchItems = async () => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    params.set('sort_by', sortBy);
    const res = await fetch(`${API}/marketplace/items?${params}`, { headers: authHeaders() });
    const data = await res.json();
    setItems(data.items || []);
    setCategories(data.categories || []);
    setLoading(false);
  };

  useEffect(() => { fetchItems(); }, [category, sortBy]);

  const handleSearch = () => fetchItems();

  const install = async (id: string) => {
    setInstalling(id);
    await fetch(`${API}/marketplace/items/${id}/install`, { method: 'POST', headers: authHeaders() });
    await fetchItems();
    setInstalling(null);
  };

  const stars = (rating: number) => {
    const full = Math.floor(rating);
    return '\u2605'.repeat(full) + '\u2606'.repeat(5 - full);
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Agent Marketplace</h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>
            Discover and install agents, plugins, workflows, and dashboards
          </p>
        </div>

        {/* Search + Filters */}
        <div className="slide-up-d1" style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200, display: 'flex', gap: 8 }}>
            <input value={search} onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Search marketplace..."
              style={{
                flex: 1, padding: '8px 14px', borderRadius: 6, border: `1px solid ${colors.border}`,
                background: colors.bgInput, color: colors.text, fontSize: 13, outline: 'none',
              }}
            />
            <button onClick={handleSearch} style={{
              padding: '8px 16px', borderRadius: 6, border: 'none', background: colors.accentGradient,
              color: '#fff', fontSize: 13, cursor: 'pointer', fontWeight: 600,
            }}>Search</button>
          </div>

          <select value={category} onChange={e => setCategory(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bgInput, color: colors.text, fontSize: 13 }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bgInput, color: colors.text, fontSize: 13 }}>
            <option value="downloads">Most Popular</option>
            <option value="rating">Highest Rated</option>
            <option value="name">Name A-Z</option>
          </select>
        </div>

        {loading ? (
          <div style={{ color: colors.textMuted, padding: 32 }}>Loading marketplace...</div>
        ) : (
          <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
            {items.map((item: any) => (
              <div key={item.id} style={{
                background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
                padding: 20, display: 'flex', flexDirection: 'column',
              }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 15, fontWeight: 600, color: colors.text }}>{item.name}</span>
                      {item.verified && <span style={{ fontSize: 10, color: colors.success }}>{'\u2713'}</span>}
                    </div>
                    <div style={{ fontSize: 11, color: colors.textDim, marginTop: 2 }}>by {item.author} &middot; v{item.version}</div>
                  </div>
                  <span style={{
                    padding: '3px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: (TYPE_COLORS[item.type] || colors.accent) + '20',
                    color: TYPE_COLORS[item.type] || colors.accent,
                  }}>{item.type}</span>
                </div>

                {/* Description */}
                <p style={{ fontSize: 12, color: colors.textSecondary, lineHeight: 1.5, flex: 1, margin: '0 0 12px' }}>
                  {item.description}
                </p>

                {/* Tags */}
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
                  {(item.tags || []).slice(0, 4).map((tag: string) => (
                    <span key={tag} style={{
                      padding: '2px 6px', borderRadius: 4, fontSize: 10,
                      background: colors.bgElevated, color: colors.textDim,
                    }}>{tag}</span>
                  ))}
                </div>

                {/* Stats + Install */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: 12 }}>
                    <span style={{ color: colors.warning }}>{stars(item.rating)}</span>
                    <span style={{ color: colors.textDim, marginLeft: 6 }}>{item.rating}</span>
                    <span style={{ color: colors.border, margin: '0 6px' }}>|</span>
                    <span style={{ color: colors.textDim }}>{item.downloads.toLocaleString()} installs</span>
                  </div>
                  <button onClick={() => install(item.id)} disabled={installing === item.id}
                    style={{
                      padding: '6px 16px', borderRadius: 6, border: 'none',
                      background: colors.accentGradient, color: '#fff', fontSize: 12, fontWeight: 600,
                      cursor: 'pointer', opacity: installing === item.id ? 0.5 : 1,
                    }}>
                    {installing === item.id ? 'Installing...' : 'Install'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
