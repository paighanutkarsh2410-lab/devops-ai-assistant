'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

interface SearchFilters {
  query: string;
  status: string[];
  severity: string[];
  service: string;
  dateFrom: string;
  dateTo: string;
  autoResolved: boolean | null;
}

interface Props {
  onResults: (results: unknown[], total: number) => void;
}

const STATUSES = ['open', 'investigating', 'resolved', 'closed'];
const SEVERITIES = ['critical', 'high', 'medium', 'low'];

export default function AdvancedSearch({ onResults }: Props) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    status: [],
    severity: [],
    service: '',
    dateFrom: '',
    dateTo: '',
    autoResolved: null,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const doSearch = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filters.query) params.q = filters.query;
      if (filters.status.length) params.status = filters.status.join(',');
      if (filters.severity.length) params.severity = filters.severity.join(',');
      if (filters.service) params.service_name = filters.service;
      if (filters.dateFrom) params.date_from = filters.dateFrom;
      if (filters.dateTo) params.date_to = filters.dateTo;
      if (filters.autoResolved !== null) params.auto_resolved = String(filters.autoResolved);

      const res = await api.get('/incidents/search/results', { params });
      onResults(res.data.results, res.data.total);
    } catch {
      // silently fail
    }
  }, [filters, onResults]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(doSearch, 300);
    return () => clearTimeout(timer);
  }, [doSearch]);

  // Autocomplete suggestions
  useEffect(() => {
    if (filters.query.length < 2) { setSuggestions([]); return; }
    api.get('/incidents/search/suggestions', { params: { q: filters.query } })
      .then(res => setSuggestions(res.data.services || []))
      .catch(() => {});
  }, [filters.query]);

  const toggleFilter = (key: 'status' | 'severity', value: string) => {
    setFilters(prev => {
      const current = prev[key];
      return {
        ...prev,
        [key]: current.includes(value) ? current.filter(v => v !== value) : [...current, value],
      };
    });
  };

  const clearAll = () => {
    setFilters({ query: '', status: [], severity: [], service: '', dateFrom: '', dateTo: '', autoResolved: null });
  };

  const activeFilterCount = filters.status.length + filters.severity.length +
    (filters.service ? 1 : 0) + (filters.dateFrom ? 1 : 0) + (filters.autoResolved !== null ? 1 : 0);

  return (
    <div style={{ marginBottom: '16px' }}>
      {/* Search bar */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            value={filters.query}
            onChange={e => setFilters(prev => ({ ...prev, query: e.target.value }))}
            placeholder="Search incidents by title, description, root cause..."
            aria-label="Search incidents"
            style={{
              width: '100%', padding: '10px 14px', borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.03)', color: '#f0f0f0', fontSize: '14px',
            }}
          />
          {suggestions.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10,
              background: 'rgba(30,30,30,0.98)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px',
              marginTop: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            }}>
              {suggestions.map(s => (
                <div
                  key={s}
                  onClick={() => { setFilters(prev => ({ ...prev, service: s, query: '' })); setSuggestions([]); }}
                  style={{ padding: '8px 14px', cursor: 'pointer', fontSize: '13px', color: '#f0f0f0' }}
                >
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)',
            background: activeFilterCount > 0 ? 'rgba(37,99,235,0.15)' : 'rgba(255,255,255,0.03)', cursor: 'pointer', fontSize: '13px', color: '#a1a1aa',
          }}
        >
          Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
        </button>
        {activeFilterCount > 0 && (
          <button onClick={clearAll} style={{
            padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(220,38,38,0.3)',
            background: 'rgba(220,38,38,0.1)', color: '#f87171', cursor: 'pointer', fontSize: '13px',
          }}>
            Clear
          </button>
        )}
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div style={{
          marginTop: '12px', padding: '16px', background: 'rgba(255,255,255,0.03)',
          borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)',
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px',
        }}>
          {/* Status */}
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#a1a1aa', marginBottom: '6px', display: 'block' }}>Status</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {STATUSES.map(s => (
                <button key={s} onClick={() => toggleFilter('status', s)} style={{
                  padding: '4px 10px', borderRadius: '14px', fontSize: '12px', cursor: 'pointer',
                  border: '1px solid', textTransform: 'capitalize',
                  background: filters.status.includes(s) ? 'rgba(37,99,235,0.2)' : 'rgba(255,255,255,0.03)',
                  borderColor: filters.status.includes(s) ? '#3b82f6' : 'rgba(255,255,255,0.06)',
                  color: filters.status.includes(s) ? '#60a5fa' : '#a1a1aa',
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Severity */}
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#a1a1aa', marginBottom: '6px', display: 'block' }}>Severity</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {SEVERITIES.map(s => (
                <button key={s} onClick={() => toggleFilter('severity', s)} style={{
                  padding: '4px 10px', borderRadius: '14px', fontSize: '12px', cursor: 'pointer',
                  border: '1px solid', textTransform: 'capitalize',
                  background: filters.severity.includes(s) ? 'rgba(37,99,235,0.2)' : 'rgba(255,255,255,0.03)',
                  borderColor: filters.severity.includes(s) ? '#3b82f6' : 'rgba(255,255,255,0.06)',
                  color: filters.severity.includes(s) ? '#60a5fa' : '#a1a1aa',
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Date range */}
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#a1a1aa', marginBottom: '6px', display: 'block' }}>Date Range</label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <input type="date" value={filters.dateFrom}
                onChange={e => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                aria-label="From date"
                style={{ flex: 1, padding: '4px 8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.03)', color: '#f0f0f0', fontSize: '12px' }}
              />
              <input type="date" value={filters.dateTo}
                onChange={e => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                aria-label="To date"
                style={{ flex: 1, padding: '4px 8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.03)', color: '#f0f0f0', fontSize: '12px' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Active filter chips */}
      {activeFilterCount > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
          {filters.status.map(s => (
            <span key={`s-${s}`} onClick={() => toggleFilter('status', s)} style={{
              padding: '2px 10px', borderRadius: '12px', fontSize: '11px', cursor: 'pointer',
              background: 'rgba(37,99,235,0.2)', color: '#60a5fa',
            }}>
              {s} x
            </span>
          ))}
          {filters.severity.map(s => (
            <span key={`v-${s}`} onClick={() => toggleFilter('severity', s)} style={{
              padding: '2px 10px', borderRadius: '12px', fontSize: '11px', cursor: 'pointer',
              background: 'rgba(217,119,6,0.2)', color: '#fbbf24',
            }}>
              {s} x
            </span>
          ))}
          {filters.service && (
            <span onClick={() => setFilters(prev => ({ ...prev, service: '' }))} style={{
              padding: '2px 10px', borderRadius: '12px', fontSize: '11px', cursor: 'pointer',
              background: 'rgba(22,163,74,0.2)', color: '#4ade80',
            }}>
              {filters.service} x
            </span>
          )}
        </div>
      )}
    </div>
  );
}
