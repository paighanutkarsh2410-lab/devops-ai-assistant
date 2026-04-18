'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
// PDF export removed
import { useBreakpoint } from '@/lib/useMediaQuery';

interface Widget {
  type: string;
  title: string;
  size: 'half' | 'full';
  config?: Record<string, unknown>;
}

interface Template {
  id: string;
  name: string;
  description: string | null;
  report_type: string;
  widgets: Widget[];
  schedule: string | null;
  created_at: string;
  updated_at: string;
}

interface Preset {
  name: string;
  report_type: string;
  widgets: Widget[];
}

const WIDGET_TYPES = [
  { type: 'mttr', label: 'Mean Time To Resolve', icon: '⏱' },
  { type: 'mttd', label: 'Mean Time To Detect', icon: '🔍' },
  { type: 'frequency', label: 'Incident Frequency', icon: '📊' },
  { type: 'root_causes', label: 'Root Cause Distribution', icon: '🔬' },
  { type: 'reliability', label: 'Service Reliability', icon: '💚' },
  { type: 'effectiveness', label: 'Automation Effectiveness', icon: '🤖' },
  { type: 'cost_impact', label: 'Cost Savings', icon: '💰' },
];

export default function ReportsPage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showBuilder, setShowBuilder] = useState(false);
  const [builderName, setBuilderName] = useState('');
  const [builderDesc, setBuilderDesc] = useState('');
  const [builderWidgets, setBuilderWidgets] = useState<Widget[]>([]);
  const [generatedReport, setGeneratedReport] = useState<Record<string, unknown> | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadTemplates();
    loadPresets();
  }, []);

  const loadTemplates = async () => {
    try {
      const res = await api.get('/report-builder/templates');
      setTemplates(res.data);
    } catch { /* empty */ }
  };

  const loadPresets = async () => {
    try {
      const res = await api.get('/report-builder/presets');
      setPresets(res.data);
    } catch { /* empty */ }
  };

  const addWidget = (type: string) => {
    const wt = WIDGET_TYPES.find(w => w.type === type);
    if (!wt) return;
    setBuilderWidgets(prev => [...prev, { type, title: wt.label, size: 'half' }]);
  };

  const removeWidget = (idx: number) => {
    setBuilderWidgets(prev => prev.filter((_, i) => i !== idx));
  };

  const saveTemplate = async () => {
    if (!builderName.trim()) return;
    try {
      await api.post('/report-builder/templates', {
        name: builderName,
        description: builderDesc,
        report_type: 'custom',
        widgets: builderWidgets,
      });
      setShowBuilder(false);
      setBuilderName('');
      setBuilderDesc('');
      setBuilderWidgets([]);
      loadTemplates();
    } catch { /* empty */ }
  };

  const usePreset = async (preset: Preset) => {
    try {
      await api.post('/report-builder/templates', {
        name: preset.name,
        description: `Created from "${preset.name}" preset`,
        report_type: preset.report_type,
        widgets: preset.widgets,
      });
      loadTemplates();
    } catch { /* empty */ }
  };

  const generateReport = async (templateId: string) => {
    setGenerating(true);
    try {
      const res = await api.post(`/report-builder/templates/${templateId}/generate?days=30`);
      setGeneratedReport(res.data);
    } catch { /* empty */ }
    setGenerating(false);
  };

  const deleteTemplate = async (id: string) => {
    try {
      await api.delete(`/report-builder/templates/${id}`);
      loadTemplates();
    } catch { /* empty */ }
  };

  const glassCard: React.CSSProperties = {
    background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 16,
  };

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: 8, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 14, outline: 'none',
  };

  return (
    <DashboardShell>
      <div id="reports-content" style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Report Builder</h1>
            <p style={{ color: colors.textMuted, fontSize: 14 }}>Create custom reports with drag-and-drop widgets</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => setShowBuilder(!showBuilder)} style={{
              padding: '8px 16px', borderRadius: 8, background: colors.accentGradient, color: '#fff',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
            }}>
              + New Report
            </button>
            <button onClick={() => router.push('/dashboard')} style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`,
              background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 13,
            }}>
              Dashboard
            </button>
          </div>
        </div>

        {/* Builder */}
        {showBuilder && (
          <div className="slide-up-d1" style={{ ...glassCard, marginBottom: 24 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Build New Report</h2>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12, marginBottom: 16 }}>
              <input value={builderName} onChange={e => setBuilderName(e.target.value)}
                placeholder="Report name" style={inputStyle} />
              <input value={builderDesc} onChange={e => setBuilderDesc(e.target.value)}
                placeholder="Description (optional)" style={inputStyle} />
            </div>

            {/* Widget palette */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: colors.textMuted, display: 'block', marginBottom: 8 }}>
                Add Widgets
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {WIDGET_TYPES.map(wt => (
                  <button key={wt.type} onClick={() => addWidget(wt.type)} style={{
                    padding: '6px 12px', borderRadius: 16, border: `1px solid ${colors.border}`,
                    background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
                  }}>
                    {wt.icon} {wt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Selected widgets */}
            {builderWidgets.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: colors.textMuted, display: 'block', marginBottom: 8 }}>
                  Report Layout ({builderWidgets.length} widgets)
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {builderWidgets.map((w, i) => (
                    <div key={i} style={{
                      padding: 10, borderRadius: 8, border: `2px dashed ${colors.accent}`,
                      background: 'rgba(59,130,246,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      gridColumn: w.size === 'full' ? 'span 2' : undefined,
                    }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: colors.text }}>{w.title}</span>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button onClick={() => {
                          const updated = [...builderWidgets];
                          updated[i] = { ...w, size: w.size === 'full' ? 'half' : 'full' };
                          setBuilderWidgets(updated);
                        }} style={{
                          padding: '2px 8px', borderRadius: 4, border: `1px solid ${colors.border}`,
                          background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 11,
                        }}>
                          {w.size === 'full' ? '½' : '▬'}
                        </button>
                        <button onClick={() => removeWidget(i)} style={{
                          padding: '2px 8px', borderRadius: 4, border: `1px solid ${colors.dangerBorder}`,
                          background: colors.dangerBg, color: colors.danger, cursor: 'pointer', fontSize: 11,
                        }}>
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button onClick={saveTemplate} disabled={!builderName.trim() || builderWidgets.length === 0}
              style={{
                padding: '8px 20px', borderRadius: 8,
                background: builderName.trim() && builderWidgets.length > 0 ? colors.accentGradient : colors.bgElevated,
                color: builderName.trim() && builderWidgets.length > 0 ? '#fff' : colors.textMuted,
                border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
              }}>
              Save Template
            </button>
          </div>
        )}

        {/* Presets */}
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Report Presets</h2>
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
          {presets.map((p, i) => (
            <div key={i} style={{...glassCard, position: 'relative', overflow: 'hidden', borderTop: '2px solid #f59e0b'}}>
              <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(245,158,11,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
              <h3 style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: colors.text }}>{p.name}</h3>
              <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 8 }}>
                {p.widgets.length} widgets · {p.report_type}
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                {p.widgets.map((w, wi) => (
                  <span key={wi} style={{
                    padding: '2px 8px', borderRadius: 10, fontSize: 10,
                    background: colors.bgElevated, color: colors.textSecondary,
                  }}>
                    {w.title || w.type}
                  </span>
                ))}
              </div>
              <button onClick={() => usePreset(p)} style={{
                padding: '6px 14px', borderRadius: 6, border: `1px solid ${colors.accent}`,
                background: 'rgba(59,130,246,0.08)', color: colors.accent, cursor: 'pointer', fontSize: 12, fontWeight: 500,
              }}>
                Use Preset
              </button>
            </div>
          ))}
        </div>

        {/* Saved Templates */}
        <h2 className="slide-up-d2" style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>My Reports</h2>
        {templates.length === 0 ? (
          <div style={{ ...glassCard, textAlign: 'center', padding: 40, color: colors.textMuted }}>
            No custom reports yet. Create one above or use a preset.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12, marginBottom: 32 }}>
            {templates.map(t => (
              <div key={t.id} style={glassCard}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                  <div>
                    <h3 style={{ fontWeight: 600, fontSize: 14, color: colors.text }}>{t.name}</h3>
                    {t.description && <p style={{ color: colors.textMuted, fontSize: 12 }}>{t.description}</p>}
                  </div>
                  <span style={{
                    padding: '2px 8px', borderRadius: 10, fontSize: 10,
                    background: colors.successBg, color: colors.success, fontWeight: 600,
                  }}>
                    {t.report_type}
                  </span>
                </div>
                <p style={{ color: colors.textDim, fontSize: 11, marginBottom: 10 }}>
                  {t.widgets?.length || 0} widgets · Updated {new Date(t.updated_at).toLocaleDateString()}
                </p>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button onClick={() => generateReport(t.id)} disabled={generating} style={{
                    padding: '6px 14px', borderRadius: 6, background: colors.accentGradient, color: '#fff',
                    border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 500,
                  }}>
                    {generating ? 'Generating...' : 'Generate'}
                  </button>
                  <button onClick={() => deleteTemplate(t.id)} style={{
                    padding: '6px 14px', borderRadius: 6, border: `1px solid ${colors.dangerBorder}`,
                    background: colors.bgElevated, color: colors.danger, cursor: 'pointer', fontSize: 12,
                  }}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Generated Report */}
        {generatedReport && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>
                Generated: {(generatedReport as Record<string, string>).template_name}
              </h2>
              <button onClick={() => setGeneratedReport(null)} style={{
                padding: '4px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
              }}>
                Close
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
              {((generatedReport as Record<string, unknown[]>).widgets || []).map((w: unknown, i: number) => {
                const widget = w as { widget: Widget; data: Record<string, unknown> };
                return (
                  <div key={i} style={{
                    ...glassCard,
                    gridColumn: widget.widget.size === 'full' ? 'span 2' : undefined,
                  }}>
                    <h3 style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: colors.text }}>{widget.widget.title}</h3>
                    <pre style={{
                      background: colors.bgElevated, borderRadius: 6, padding: 10,
                      fontSize: 11, overflow: 'auto', maxHeight: 200, color: colors.textSecondary,
                    }}>
                      {JSON.stringify(widget.data, null, 2)}
                    </pre>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
