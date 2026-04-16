'use client';

import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Evidence {
  description: string;
  weight: number;
  source: string;
  data_point?: string;
}

interface Alternative {
  hypothesis: string;
  probability: number;
  reason_rejected: string;
}

interface Explanation {
  incident_id: string;
  type: string;
  summary: string;
  confidence: number;
  evidence: Evidence[];
  alternatives: Alternative[];
  decision_path: string[];
  feature_importance: Record<string, number>;
}

const SOURCE_COLORS: Record<string, string> = {
  metric: '#3b82f6',
  pattern: '#8b5cf6',
  history: '#10b981',
  correlation: '#f59e0b',
  diagnostic_agent: '#06b6d4',
  remediation_agent: '#ef4444',
  monitoring: '#64748b',
  learning_agent: '#ec4899',
  safety: '#f97316',
  diagnosis: '#06b6d4',
  performance: '#22d3ee',
  safety_rules: '#f97316',
};

export default function ExplanationPanel({ incidentId }: { incidentId: string }) {
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [remExplanation, setRemExplanation] = useState<Explanation | null>(null);
  const [activeTab, setActiveTab] = useState<'diagnosis' | 'remediation'>('diagnosis');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!incidentId) return;
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};

    Promise.all([
      fetch(`${API}/explanations/incidents/${incidentId}/explanation`, { headers }).then(r => r.json()),
      fetch(`${API}/explanations/incidents/${incidentId}/remediation-explanation`, { headers }).then(r => r.json()),
    ]).then(([diag, rem]) => {
      if (!diag.error) setExplanation(diag);
      if (!rem.error) setRemExplanation(rem);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [incidentId]);

  if (loading) return <div style={{ color: '#94a3b8', padding: 16 }}>Loading explanation...</div>;

  const current = activeTab === 'diagnosis' ? explanation : remExplanation;
  if (!current) return <div style={{ color: '#64748b', padding: 16 }}>No explanation available</div>;

  return (
    <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid #1e293b', overflow: 'hidden' }}>
      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1e293b' }}>
        {(['diagnosis', 'remediation'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1, padding: '12px 16px', border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, textTransform: 'capitalize',
              background: activeTab === tab ? '#1e293b' : 'transparent',
              color: activeTab === tab ? '#e2e8f0' : '#64748b',
              borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
            }}
          >
            {tab} Explanation
          </button>
        ))}
      </div>

      <div style={{ padding: 20 }}>
        {/* Summary */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', marginBottom: 4 }}>{current.summary}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>Confidence:</div>
            <div style={{ flex: 1, maxWidth: 200, height: 8, borderRadius: 4, background: '#1e293b', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 4,
                width: `${current.confidence}%`,
                background: current.confidence > 80 ? '#10b981' : current.confidence > 60 ? '#f59e0b' : '#ef4444',
              }} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, color: current.confidence > 80 ? '#10b981' : '#f59e0b' }}>
              {current.confidence}%
            </span>
          </div>
        </div>

        {/* Evidence */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#cbd5e1', marginBottom: 10 }}>Evidence (ranked by importance)</div>
          {current.evidence.map((e, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 0', borderBottom: i < current.evidence.length - 1 ? '1px solid #1e293b40' : 'none',
            }}>
              <div style={{ width: 4, height: 32, borderRadius: 2, background: SOURCE_COLORS[e.source] || '#64748b' }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: '#e2e8f0' }}>{e.description}</div>
                <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>Source: {e.source}</div>
              </div>
              <div style={{
                minWidth: 50, padding: '3px 8px', borderRadius: 6,
                background: '#1e293b', textAlign: 'center',
                fontSize: 12, fontWeight: 600, color: '#94a3b8',
              }}>
                {(e.weight * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>

        {/* Decision Path */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#cbd5e1', marginBottom: 10 }}>Decision Path</div>
          <div style={{ paddingLeft: 12 }}>
            {current.decision_path.map((step, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 6 }}>
                <div style={{
                  width: 8, height: 8, borderRadius: '50%', marginTop: 5,
                  background: i === current.decision_path.length - 1 ? '#3b82f6' : '#334155',
                  boxShadow: i === current.decision_path.length - 1 ? '0 0 6px #3b82f6' : 'none',
                }} />
                <span style={{ fontSize: 12, color: i === current.decision_path.length - 1 ? '#e2e8f0' : '#94a3b8' }}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Feature Importance */}
        {current.feature_importance && Object.keys(current.feature_importance).length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#cbd5e1', marginBottom: 10 }}>Feature Importance</div>
            {Object.entries(current.feature_importance).map(([feature, importance]) => (
              <div key={feature} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: '#94a3b8', width: 90, textTransform: 'capitalize' }}>{feature}</span>
                <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#1e293b', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 3,
                    width: `${(importance as number) * 100}%`,
                    background: SOURCE_COLORS[feature] || '#3b82f6',
                  }} />
                </div>
                <span style={{ fontSize: 11, color: '#64748b', width: 36, textAlign: 'right' }}>
                  {((importance as number) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Alternatives */}
        {current.alternatives && current.alternatives.length > 0 && (
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#cbd5e1', marginBottom: 10 }}>Alternatives Considered</div>
            {current.alternatives.map((alt, i) => (
              <div key={i} style={{
                padding: '8px 12px', borderRadius: 8, background: '#1e293b',
                marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <span style={{ fontSize: 13, color: '#e2e8f0' }}>{alt.hypothesis}</span>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{alt.reason_rejected}</div>
                </div>
                <span style={{ fontSize: 12, color: '#64748b', fontWeight: 600, whiteSpace: 'nowrap', marginLeft: 12 }}>
                  {alt.probability}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
