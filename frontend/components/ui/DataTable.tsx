'use client';

import { useState, useMemo } from 'react';

interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (value: unknown, row: T) => React.ReactNode;
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  pageSize?: number;
  searchable?: boolean;
  searchKeys?: string[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

type SortDirection = 'asc' | 'desc' | null;

export default function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  pageSize = 10,
  searchable = true,
  searchKeys,
  onRowClick,
  emptyMessage = 'No data available',
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>(null);
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (!search) return data;
    const keys = searchKeys || columns.map((c) => c.key);
    const q = search.toLowerCase();
    return data.filter((row) =>
      keys.some((k) => String(row[k] || '').toLowerCase().includes(q))
    );
  }, [data, search, searchKeys, columns]);

  const sorted = useMemo(() => {
    if (!sortKey || !sortDir) return filtered;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = typeof av === 'number' && typeof bv === 'number'
        ? av - bv
        : String(av).localeCompare(String(bv));
      return sortDir === 'desc' ? -cmp : cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : sortDir === 'desc' ? null : 'asc');
      if (sortDir === 'desc') setSortKey(null);
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  return (
    <div>
      {searchable && (
        <div style={{ marginBottom: 12 }}>
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            style={{
              width: 260,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: 13,
              outline: 'none',
            }}
          />
        </div>
      )}

      <div style={{ overflowX: 'auto', borderRadius: 10, border: '1px solid #1e293b' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={col.sortable !== false ? () => handleSort(col.key) : undefined}
                  style={{
                    padding: '10px 14px',
                    textAlign: 'left',
                    color: '#94a3b8',
                    fontWeight: 600,
                    fontSize: 11,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                    borderBottom: '1px solid #1e293b',
                    cursor: col.sortable !== false ? 'pointer' : 'default',
                    userSelect: 'none',
                    width: col.width,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col.label}
                  {col.sortable !== false && sortKey === col.key && (
                    <span style={{ marginLeft: 4 }}>
                      {sortDir === 'asc' ? '\u25B2' : '\u25BC'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, i) => (
              <tr
                key={i}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                style={{
                  background: i % 2 === 0 ? '#1e293b' : '#1a2536',
                  cursor: onRowClick ? 'pointer' : 'default',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#334155')}
                onMouseLeave={(e) => (e.currentTarget.style.background = i % 2 === 0 ? '#1e293b' : '#1a2536')}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    style={{
                      padding: '10px 14px',
                      color: '#cbd5e1',
                      borderBottom: '1px solid #1e293b20',
                    }}
                  >
                    {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
            {paged.length === 0 && (
              <tr>
                <td colSpan={columns.length} style={{ padding: 32, textAlign: 'center', color: '#64748b' }}>
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
          <span style={{ color: '#64748b', fontSize: 12 }}>
            Showing {page * pageSize + 1}\u2013{Math.min((page + 1) * pageSize, sorted.length)} of {sorted.length}
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: '1px solid #334155',
                background: '#1e293b',
                color: page === 0 ? '#475569' : '#e2e8f0',
                cursor: page === 0 ? 'not-allowed' : 'pointer',
                fontSize: 12,
              }}
            >
              Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const p = page < 3 ? i : page > totalPages - 3 ? totalPages - 5 + i : page - 2 + i;
              if (p < 0 || p >= totalPages) return null;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  style={{
                    padding: '6px 10px',
                    borderRadius: 6,
                    border: p === page ? '1px solid #3b82f6' : '1px solid #334155',
                    background: p === page ? '#3b82f6' : '#1e293b',
                    color: '#e2e8f0',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: p === page ? 600 : 400,
                  }}
                >
                  {p + 1}
                </button>
              );
            })}
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: '1px solid #334155',
                background: '#1e293b',
                color: page >= totalPages - 1 ? '#475569' : '#e2e8f0',
                cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer',
                fontSize: 12,
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
