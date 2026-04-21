'use client';

import { useState, useEffect } from 'react';
import { logAnalysisAPI, logsAPI } from '@/lib/api';
import {
  colors, pageContainer, pageContent, pageHeader, pageTitle, pageSubtitle,
  card, glassCard, btnPrimary, btn, badge, statCard, flexBetween, flexGap,
} from '@/lib/theme';

const CATEGORY_COLORS: Record<string, string> = {
  memory: '#ef4444',
  connectivity: '#f97316',
  timeout: '#f59e0b',
  disk: '#dc2626',
  database: '#a855f7',
  crash: '#ef4444',
  auth: '#06b6d4',
  ssl: '#8b5cf6',
  cpu: '#f97316',
  rate_limit: '#eab308',
  dns: '#3b82f6',
  server_error: '#dc2626',
  general: '#71717a',
  unknown: '#52525b',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#10b981',
  info: '#71717a',
};

interface LogStats {
  total_logs: number;
  hours: number;
  by_level: Record<string, number>;
  by_service: Record<string, number>;
  error_categories: Record<string, number>;
  smart_patterns_available: number;
}

interface AnalysisResult {
  total: number;
  errors: number;
  warnings: number;
  patterns: { category: string; severity: string; count: number; sample: string }[];
  recommendations: string[];
  top_categories: Record<string, number>;
}

export default function LogAnalysisPage() {
  const [stats, setStats] = useState<LogStats | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [hours, setHours] = useState(24);
  const [selectedLevel, setSelectedLevel] = useState('');

  useEffect(() => {
    loadData();
  }, [hours]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, logsRes] = await Promise.all([
        logAnalysisAPI.stats(hours).catch(() => ({ data: null })),
        logsAPI.getAll({ hours, level: selectedLevel || undefined, service_name: undefined }).catch(() => ({ data: [] })),
      ]);
      if (statsRes.data) setStats(statsRes.data);
      setRecentLogs(Array.isArray(logsRes.data) ? logsRes.data : []);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  const runAnalysis = async () => {
    if (recentLogs.length === 0) return;
    setAnalyzing(true);
    try {
      const logsToAnalyze = recentLogs.map(l => ({
        message: l.message,
        level: l.level,
        service: l.service_name,
        timestamp: l.timestamp,
      }));
      const res = await logAnalysisAPI.analyze(logsToAnalyze);
      setAnalysis(res.data);
    } catch {
      // ignore
    }
    setAnalyzing(false);
  };

  const levelColors: Record<string, string> = {
    ERROR: '#ef4444', CRITICAL: '#dc2626', FATAL: '#991b1b',
    WARNING: '#f59e0b', WARN: '#f59e0b',
    INFO: '#3b82f6', DEBUG: '#71717a',
  };

  return (
    <div style={pageContainer}>
      <div style={pageContent}>
        <div style={pageHeader}>
          <div style={flexBetween}>
            <div>
              <h1 style={pageTitle}>Log Analysis</h1>
              <p style={pageSubtitle}>AI-powered log pattern detection, error clustering, and root cause insights</p>
            </div>
            <div style={{ ...flexGap(8) }}>
              <select
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                style={{ padding: '8px 12px', borderRadius: 8, border: `1px solid ${colors.border}`, background: colors.bgInput, color: colors.text, fontSize: 13 }}
              >
                <option value={1}>Last 1 hour</option>
                <option value={6}>Last 6 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={72}>Last 3 days</option>
                <option value={168}>Last 7 days</option>
              </select>
              <button onClick={runAnalysis} disabled={analyzing || recentLogs.length === 0} style={{ ...btnPrimary, opacity: analyzing || recentLogs.length === 0 ? 0.5 : 1 }}>
                {analyzing ? 'Analyzing...' : 'Run Analysis'}
              </button>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
            <div style={statCard('#3b82f6')}>
              <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Total Logs</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.text }}>{stats.total_logs.toLocaleString()}</div>
              <div style={{ fontSize: 12, color: colors.textDim }}>Last {stats.hours}h</div>
            </div>
            <div style={statCard('#ef4444')}>
              <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Errors</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#ef4444' }}>{stats.by_level?.ERROR || 0}</div>
              <div style={{ fontSize: 12, color: colors.textDim }}>+ {stats.by_level?.CRITICAL || 0} critical</div>
            </div>
            <div style={statCard('#f59e0b')}>
              <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Warnings</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#f59e0b' }}>{stats.by_level?.WARNING || 0}</div>
            </div>
            <div style={statCard('#8b5cf6')}>
              <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Error Categories</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#8b5cf6' }}>{Object.keys(stats.error_categories || {}).length}</div>
              <div style={{ fontSize: 12, color: colors.textDim }}>{stats.smart_patterns_available} patterns active</div>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 20, marginBottom: 24 }}>
            {/* Error Patterns */}
            {analysis.patterns.length > 0 && (
              <div style={card}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#ef4444', marginBottom: 16 }}>Detected Error Patterns</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
                  {analysis.patterns.map((p, i) => (
                    <div key={i} style={{
                      padding: 16, borderRadius: 12, background: colors.bgElevated,
                      border: `1px solid ${colors.border}`, borderLeft: `3px solid ${CATEGORY_COLORS[p.category] || colors.textMuted}`,
                    }}>
                      <div style={flexBetween}>
                        <span style={{ fontSize: 14, fontWeight: 600, color: CATEGORY_COLORS[p.category] || colors.text }}>
                          {p.category.replace('_', ' ').toUpperCase()}
                        </span>
                        <div style={{ ...flexGap(6) }}>
                          <span style={badge(SEVERITY_COLORS[p.severity] || colors.textMuted, `${SEVERITY_COLORS[p.severity] || colors.textMuted}15`)}>
                            {p.severity}
                          </span>
                          <span style={{ fontSize: 13, fontWeight: 700, color: colors.text }}>{p.count}x</span>
                        </div>
                      </div>
                      <p style={{ fontSize: 12, color: colors.textMuted, marginTop: 8, lineHeight: 1.5, fontFamily: 'monospace' }}>
                        {p.sample}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {analysis.recommendations.length > 0 && (
              <div style={{ ...card, borderTop: `2px solid #10b981` }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#10b981', marginBottom: 16 }}>Recommendations</h3>
                {analysis.recommendations.map((rec, i) => (
                  <div key={i} style={{
                    padding: '12px 16px', marginBottom: 8, borderRadius: 10,
                    background: 'rgba(16,185,129,0.05)', border: `1px solid rgba(16,185,129,0.1)`,
                    fontSize: 13, color: colors.textSecondary, lineHeight: 1.6,
                  }}>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>Rec {i + 1}:</span> {rec}
                  </div>
                ))}
              </div>
            )}

            {/* Summary Bar */}
            <div style={{ ...glassCard, display: 'flex', gap: 24, flexWrap: 'wrap' as const }}>
              <div>
                <span style={{ fontSize: 11, color: colors.textMuted }}>Analyzed</span>
                <div style={{ fontSize: 18, fontWeight: 700, color: colors.text }}>{analysis.total}</div>
              </div>
              <div>
                <span style={{ fontSize: 11, color: colors.textMuted }}>Errors Found</span>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#ef4444' }}>{analysis.errors}</div>
              </div>
              <div>
                <span style={{ fontSize: 11, color: colors.textMuted }}>Warnings</span>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#f59e0b' }}>{analysis.warnings}</div>
              </div>
              <div>
                <span style={{ fontSize: 11, color: colors.textMuted }}>Categories</span>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#8b5cf6' }}>{Object.keys(analysis.top_categories).length}</div>
              </div>
            </div>
          </div>
        )}

        {/* Distribution Charts */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 20, marginBottom: 24 }}>
            {/* By Service */}
            <div style={card}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.text, marginBottom: 16 }}>Logs by Service</h3>
              {Object.entries(stats.by_service || {}).map(([svc, count]) => {
                const pct = stats.total_logs > 0 ? (count / stats.total_logs) * 100 : 0;
                return (
                  <div key={svc} style={{ marginBottom: 10 }}>
                    <div style={{ ...flexBetween, marginBottom: 4 }}>
                      <span style={{ fontSize: 13, color: colors.textSecondary }}>{svc}</span>
                      <span style={{ fontSize: 12, color: colors.textMuted }}>{count}</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, background: colors.bgElevated, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, borderRadius: 3, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', transition: 'width 0.5s ease' }} />
                    </div>
                  </div>
                );
              })}
              {Object.keys(stats.by_service || {}).length === 0 && (
                <p style={{ color: colors.textMuted, fontSize: 13 }}>No service data available</p>
              )}
            </div>

            {/* Error Categories */}
            <div style={card}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.text, marginBottom: 16 }}>Error Categories</h3>
              {Object.entries(stats.error_categories || {}).map(([cat, count]) => (
                <div key={cat} style={{ marginBottom: 10 }}>
                  <div style={{ ...flexBetween, marginBottom: 4 }}>
                    <span style={{ fontSize: 13, color: CATEGORY_COLORS[cat] || colors.textSecondary }}>
                      {cat.replace('_', ' ')}
                    </span>
                    <span style={{ fontSize: 12, color: colors.textMuted }}>{count}</span>
                  </div>
                  <div style={{ height: 6, borderRadius: 3, background: colors.bgElevated, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(count * 5, 100)}%`,
                      borderRadius: 3,
                      background: CATEGORY_COLORS[cat] || '#71717a',
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                </div>
              ))}
              {Object.keys(stats.error_categories || {}).length === 0 && (
                <p style={{ color: colors.textMuted, fontSize: 13 }}>No error patterns detected</p>
              )}
            </div>
          </div>
        )}

        {/* Recent Logs Table */}
        <div style={card}>
          <div style={{ ...flexBetween, marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>Recent Logs</h3>
            <span style={{ fontSize: 12, color: colors.textMuted }}>{recentLogs.length} entries</span>
          </div>
          <div style={{ maxHeight: 400, overflowY: 'auto' as const }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
              <thead>
                <tr>
                  {['Level', 'Service', 'Message', 'Time'].map(h => (
                    <th key={h} style={{ textAlign: 'left' as const, padding: '10px 12px', fontSize: 11, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, borderBottom: `1px solid ${colors.border}`, position: 'sticky' as const, top: 0, background: '#0a0a14' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentLogs.slice(0, 100).map((log, i) => (
                  <tr key={i}>
                    <td style={{ padding: '8px 12px', borderBottom: `1px solid ${colors.borderLight}` }}>
                      <span style={badge(levelColors[log.level] || colors.textMuted, `${levelColors[log.level] || colors.textMuted}15`)}>
                        {log.level}
                      </span>
                    </td>
                    <td style={{ padding: '8px 12px', fontSize: 13, color: colors.textSecondary, borderBottom: `1px solid ${colors.borderLight}` }}>{log.service_name}</td>
                    <td style={{ padding: '8px 12px', fontSize: 12, color: colors.textMuted, borderBottom: `1px solid ${colors.borderLight}`, maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const, fontFamily: 'monospace' }}>{log.message}</td>
                    <td style={{ padding: '8px 12px', fontSize: 12, color: colors.textDim, borderBottom: `1px solid ${colors.borderLight}`, whiteSpace: 'nowrap' as const }}>
                      {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {recentLogs.length === 0 && !loading && (
              <div style={{ textAlign: 'center' as const, padding: 40 }}>
                <div style={{ fontSize: 36, marginBottom: 8 }}>📄</div>
                <p style={{ color: colors.textMuted, fontSize: 13 }}>No logs found for the selected time range</p>
              </div>
            )}
          </div>
        </div>

        {loading && (
          <div style={{ textAlign: 'center' as const, padding: 60 }}>
            <div style={{ fontSize: 36, marginBottom: 12, animation: 'pulse 2s infinite' }}>📊</div>
            <p style={{ color: colors.textMuted }}>Loading log data...</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
