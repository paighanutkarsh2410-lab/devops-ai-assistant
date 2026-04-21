'use client';

import { useState, useEffect } from 'react';
import { postmortemAPI, incidentsAPI } from '@/lib/api';
import {
  colors, pageContainer, pageContent, pageHeader, pageTitle, pageSubtitle,
  card, glassCard, btnPrimary, btn, badge, severityColor, flexBetween, flexGap,
} from '@/lib/theme';

interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  service_name: string | null;
  created_at?: string;
  resolved_at?: string | null;
}

interface PostmortemReport {
  incident_id: string;
  incident_title: string;
  incident_severity: string;
  service_name: string;
  generated_at: string;
  generated_by: string;
  report: {
    summary: string;
    timeline: { time: string; event: string }[];
    root_cause_analysis: string;
    contributing_factors: string[];
    impact: {
      duration_description: string;
      affected_services: string[];
      user_impact: string;
      severity_justification: string;
    };
    what_went_well: string[];
    what_went_wrong: string[];
    action_items: { action: string; priority: string; owner: string; due: string }[];
    lessons_learned: string[];
    prevention_measures: string[];
  };
}

export default function PostmortemPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<string>('');
  const [report, setReport] = useState<PostmortemReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingIncidents, setLoadingIncidents] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    incidentsAPI.getAll({ limit: 50 }).then(r => {
      setIncidents(r.data || []);
      setLoadingIncidents(false);
    }).catch(() => setLoadingIncidents(false));
  }, []);

  const generateReport = async () => {
    if (!selectedIncident) return;
    setLoading(true);
    setError('');
    setReport(null);
    try {
      const res = await postmortemAPI.generate(selectedIncident);
      setReport(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to generate post-mortem');
    } finally {
      setLoading(false);
    }
  };

  const sev = (s: string) => severityColor(s);

  return (
    <div style={pageContainer}>
      <div style={pageContent}>
        <div style={pageHeader}>
          <h1 style={pageTitle}>Post-Incident Review</h1>
          <p style={pageSubtitle}>Generate blameless post-mortem reports with AI-powered analysis</p>
        </div>

        {/* Incident Selector */}
        <div style={{ ...glassCard, marginBottom: 24 }}>
          <div style={{ ...flexBetween, flexWrap: 'wrap' as const, gap: 16 }}>
            <div style={{ flex: 1, minWidth: 280 }}>
              <label style={{ fontSize: 12, color: colors.textMuted, marginBottom: 6, display: 'block', textTransform: 'uppercase' as const, letterSpacing: 1 }}>
                Select Incident
              </label>
              <select
                value={selectedIncident}
                onChange={(e) => setSelectedIncident(e.target.value)}
                style={{
                  width: '100%', padding: '10px 14px', borderRadius: 8,
                  border: `1px solid ${colors.border}`, background: colors.bgInput,
                  color: colors.text, fontSize: 14, outline: 'none',
                }}
              >
                <option value="">Choose an incident...</option>
                {incidents.map(inc => (
                  <option key={inc.id} value={inc.id}>
                    [{inc.severity?.toUpperCase()}] {inc.title} ({inc.status})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={generateReport}
              disabled={!selectedIncident || loading}
              style={{
                ...btnPrimary,
                opacity: !selectedIncident || loading ? 0.5 : 1,
                marginTop: 18,
              }}
            >
              {loading ? 'Generating...' : 'Generate Post-Mortem'}
            </button>
          </div>
          {loadingIncidents && <p style={{ color: colors.textMuted, marginTop: 12, fontSize: 13 }}>Loading incidents...</p>}
          {error && <p style={{ color: colors.danger, marginTop: 12, fontSize: 13 }}>{error}</p>}
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ ...card, textAlign: 'center' as const, padding: 60 }}>
            <div style={{ fontSize: 40, marginBottom: 16, animation: 'pulse 2s infinite' }}>🔍</div>
            <p style={{ color: colors.textSecondary, fontSize: 15 }}>Analyzing incident data and generating report...</p>
            <p style={{ color: colors.textMuted, fontSize: 12, marginTop: 8 }}>This may take a few seconds</p>
          </div>
        )}

        {/* Report */}
        {report && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 20 }}>
            {/* Header */}
            <div style={{ ...glassCard, borderTop: `3px solid ${sev(report.incident_severity).color}` }}>
              <div style={flexBetween}>
                <div>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: colors.text, marginBottom: 4 }}>
                    {report.incident_title}
                  </h2>
                  <div style={{ ...flexGap(12), flexWrap: 'wrap' as const }}>
                    <span style={badge(sev(report.incident_severity).color, sev(report.incident_severity).bg)}>
                      {report.incident_severity?.toUpperCase()}
                    </span>
                    <span style={{ fontSize: 13, color: colors.textMuted }}>{report.service_name}</span>
                    <span style={{ fontSize: 12, color: colors.textDim }}>
                      Generated {new Date(report.generated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <span style={badge(
                  report.generated_by === 'claude_ai' ? '#8b5cf6' : colors.textMuted,
                  report.generated_by === 'claude_ai' ? 'rgba(139,92,246,0.1)' : colors.bgCard
                )}>
                  {report.generated_by === 'claude_ai' ? 'AI Generated' : 'Template'}
                </span>
              </div>
            </div>

            {/* Executive Summary */}
            <div style={card}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: '#60a5fa', marginBottom: 12 }}>Executive Summary</h3>
              <p style={{ color: colors.textSecondary, fontSize: 14, lineHeight: 1.7 }}>{report.report.summary}</p>
            </div>

            {/* Timeline + Root Cause side by side */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 20 }}>
              {/* Timeline */}
              <div style={card}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#60a5fa', marginBottom: 16 }}>Timeline</h3>
                <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 0 }}>
                  {report.report.timeline?.map((evt, i) => (
                    <div key={i} style={{ display: 'flex', gap: 12, padding: '10px 0', borderLeft: `2px solid ${colors.border}`, marginLeft: 8, paddingLeft: 16, position: 'relative' as const }}>
                      <div style={{
                        position: 'absolute' as const, left: -5, top: 14,
                        width: 8, height: 8, borderRadius: '50%',
                        background: i === 0 ? colors.danger : i === report.report.timeline.length - 1 ? colors.success : colors.accent,
                      }} />
                      <span style={{ fontSize: 12, color: colors.textMuted, minWidth: 120, fontFamily: 'monospace' }}>{evt.time}</span>
                      <span style={{ fontSize: 13, color: colors.textSecondary }}>{evt.event}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Root Cause Analysis */}
              <div style={card}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f59e0b', marginBottom: 12 }}>Root Cause Analysis</h3>
                <p style={{ color: colors.textSecondary, fontSize: 14, lineHeight: 1.7, marginBottom: 16 }}>
                  {report.report.root_cause_analysis}
                </p>
                {report.report.contributing_factors?.length > 0 && (
                  <>
                    <h4 style={{ fontSize: 13, fontWeight: 600, color: colors.textMuted, marginBottom: 8, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Contributing Factors</h4>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                      {report.report.contributing_factors.map((f, i) => (
                        <li key={i} style={{ padding: '6px 0', fontSize: 13, color: colors.textSecondary, display: 'flex', gap: 8 }}>
                          <span style={{ color: '#f59e0b' }}>&#9679;</span> {f}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </div>

            {/* Impact */}
            {report.report.impact && (
              <div style={card}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#ef4444', marginBottom: 16 }}>Impact Assessment</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                  <div style={{ padding: 16, background: colors.bgElevated, borderRadius: 12 }}>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Duration</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: colors.text }}>{report.report.impact.duration_description}</div>
                  </div>
                  <div style={{ padding: 16, background: colors.bgElevated, borderRadius: 12 }}>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Affected Services</div>
                    <div style={{ fontSize: 14, color: colors.text }}>{report.report.impact.affected_services?.join(', ')}</div>
                  </div>
                  <div style={{ padding: 16, background: colors.bgElevated, borderRadius: 12 }}>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4, textTransform: 'uppercase' as const, letterSpacing: 1 }}>User Impact</div>
                    <div style={{ fontSize: 14, color: colors.text }}>{report.report.impact.user_impact}</div>
                  </div>
                  <div style={{ padding: 16, background: colors.bgElevated, borderRadius: 12 }}>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Severity Justification</div>
                    <div style={{ fontSize: 14, color: colors.text }}>{report.report.impact.severity_justification}</div>
                  </div>
                </div>
              </div>
            )}

            {/* What went well / wrong */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 20 }}>
              <div style={{ ...card, borderTop: `2px solid ${colors.success}` }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.success, marginBottom: 12 }}>What Went Well</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {report.report.what_went_well?.map((item, i) => (
                    <li key={i} style={{ padding: '8px 0', fontSize: 13, color: colors.textSecondary, display: 'flex', gap: 8, borderBottom: `1px solid ${colors.borderLight}` }}>
                      <span style={{ color: colors.success, fontSize: 16 }}>+</span> {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div style={{ ...card, borderTop: `2px solid ${colors.danger}` }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.danger, marginBottom: 12 }}>What Went Wrong</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {report.report.what_went_wrong?.map((item, i) => (
                    <li key={i} style={{ padding: '8px 0', fontSize: 13, color: colors.textSecondary, display: 'flex', gap: 8, borderBottom: `1px solid ${colors.borderLight}` }}>
                      <span style={{ color: colors.danger, fontSize: 16 }}>-</span> {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Action Items */}
            {report.report.action_items?.length > 0 && (
              <div style={card}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#8b5cf6', marginBottom: 16 }}>Action Items</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
                  <thead>
                    <tr>
                      {['Action', 'Priority', 'Owner', 'Due'].map(h => (
                        <th key={h} style={{ textAlign: 'left' as const, padding: '10px 14px', fontSize: 11, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, borderBottom: `1px solid ${colors.border}` }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.report.action_items.map((item, i) => {
                      const prioColor = item.priority === 'P1' ? colors.danger : item.priority === 'P2' ? '#f97316' : colors.textMuted;
                      return (
                        <tr key={i}>
                          <td style={{ padding: '12px 14px', fontSize: 13, color: colors.textSecondary, borderBottom: `1px solid ${colors.borderLight}` }}>{item.action}</td>
                          <td style={{ padding: '12px 14px', borderBottom: `1px solid ${colors.borderLight}` }}>
                            <span style={badge(prioColor, `${prioColor}15`)}>{item.priority}</span>
                          </td>
                          <td style={{ padding: '12px 14px', fontSize: 13, color: colors.textMuted, borderBottom: `1px solid ${colors.borderLight}` }}>{item.owner}</td>
                          <td style={{ padding: '12px 14px', fontSize: 13, color: colors.textMuted, borderBottom: `1px solid ${colors.borderLight}` }}>{item.due}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Lessons Learned + Prevention */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 20 }}>
              {report.report.lessons_learned?.length > 0 && (
                <div style={card}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: '#06b6d4', marginBottom: 12 }}>Lessons Learned</h3>
                  {report.report.lessons_learned.map((l, i) => (
                    <div key={i} style={{ padding: '8px 0', fontSize: 13, color: colors.textSecondary, borderBottom: `1px solid ${colors.borderLight}`, display: 'flex', gap: 8 }}>
                      <span style={{ color: '#06b6d4' }}>{i + 1}.</span> {l}
                    </div>
                  ))}
                </div>
              )}
              {report.report.prevention_measures?.length > 0 && (
                <div style={card}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: '#10b981', marginBottom: 12 }}>Prevention Measures</h3>
                  {report.report.prevention_measures.map((m, i) => (
                    <div key={i} style={{ padding: '8px 0', fontSize: 13, color: colors.textSecondary, borderBottom: `1px solid ${colors.borderLight}`, display: 'flex', gap: 8 }}>
                      <span style={{ color: '#10b981' }}>&#10003;</span> {m}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!report && !loading && (
          <div style={{ ...card, textAlign: 'center' as const, padding: 60, marginTop: 20 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: colors.text, marginBottom: 8 }}>No Report Generated Yet</h3>
            <p style={{ color: colors.textMuted, fontSize: 14 }}>Select an incident above and click Generate to create a blameless post-incident review</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
