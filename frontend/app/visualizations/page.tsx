'use client';

import { useState } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';
import HeatMap from '../../components/charts/HeatMap';
import SankeyDiagram from '../../components/charts/SankeyDiagram';
import NetworkGraph from '../../components/charts/NetworkGraph';
import TimelineViz from '../../components/charts/TimelineViz';
import TreeMap from '../../components/charts/TreeMap';
import BubbleChart from '../../components/charts/BubbleChart';
import RadarChart from '../../components/charts/RadarChart';
import GaugeChart from '../../components/charts/GaugeChart';

// ── Sample Data ────────────────────────────────────────────────────────

const heatMapData = (() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return days.flatMap((day) =>
    hours.map((hour) => ({
      row: day,
      col: hour,
      value: Math.round(Math.random() * 80 + (day === 'Mon' || day === 'Tue' ? 20 : 0) +
        (parseInt(hour) >= 9 && parseInt(hour) <= 17 ? 30 : 0)),
    }))
  );
})();

const sankeyNodes = [
  { id: 'alerts', label: 'Alerts', color: '#f59e0b' },
  { id: 'metrics', label: 'Metrics', color: '#3b82f6' },
  { id: 'logs', label: 'Logs', color: '#8b5cf6' },
  { id: 'monitor', label: 'Monitor Agent', color: '#06b6d4' },
  { id: 'diagnose', label: 'Diagnostic Agent', color: '#10b981' },
  { id: 'remediate', label: 'Remediation', color: '#ef4444' },
  { id: 'resolved', label: 'Resolved', color: '#22c55e' },
  { id: 'escalated', label: 'Escalated', color: '#f97316' },
];

const sankeyLinks = [
  { source: 'alerts', target: 'monitor', value: 45 },
  { source: 'metrics', target: 'monitor', value: 60 },
  { source: 'logs', target: 'monitor', value: 30 },
  { source: 'monitor', target: 'diagnose', value: 80 },
  { source: 'diagnose', target: 'remediate', value: 55 },
  { source: 'diagnose', target: 'escalated', value: 25 },
  { source: 'remediate', target: 'resolved', value: 45 },
  { source: 'remediate', target: 'escalated', value: 10 },
];

const networkNodes = [
  { id: 'api-gw', label: 'API Gateway', group: 'gateway', size: 14 },
  { id: 'auth', label: 'Auth Service', group: 'service', size: 10 },
  { id: 'users', label: 'User Service', group: 'service', size: 10 },
  { id: 'orders', label: 'Order Service', group: 'service', size: 12 },
  { id: 'payments', label: 'Payments', group: 'service', size: 11 },
  { id: 'pg-main', label: 'PostgreSQL', group: 'database', size: 13 },
  { id: 'redis', label: 'Redis Cache', group: 'cache', size: 10 },
  { id: 'rabbitmq', label: 'RabbitMQ', group: 'queue', size: 9 },
  { id: 'stripe', label: 'Stripe API', group: 'external', size: 8 },
];

const networkEdges = [
  { source: 'api-gw', target: 'auth', weight: 3, label: '200ms' },
  { source: 'api-gw', target: 'users', weight: 2 },
  { source: 'api-gw', target: 'orders', weight: 3, label: '150ms' },
  { source: 'auth', target: 'redis', weight: 2 },
  { source: 'users', target: 'pg-main', weight: 2 },
  { source: 'orders', target: 'pg-main', weight: 3 },
  { source: 'orders', target: 'rabbitmq', weight: 1 },
  { source: 'payments', target: 'stripe', weight: 2, label: '400ms' },
  { source: 'rabbitmq', target: 'payments', weight: 2 },
  { source: 'orders', target: 'redis', weight: 1 },
];

const timelineEvents = [
  { id: '1', label: 'Deploy v2.3.1', start: '2026-04-05T08:00:00Z', end: '2026-04-05T08:15:00Z', category: 'deployment', description: 'Rolling deployment to production' },
  { id: '2', label: 'CPU Spike Alert', start: '2026-04-05T09:30:00Z', end: '2026-04-05T09:45:00Z', category: 'alert', description: 'CPU > 90% on api-server-3' },
  { id: '3', label: 'Memory Leak Incident', start: '2026-04-05T10:00:00Z', end: '2026-04-05T11:30:00Z', category: 'incident', description: 'OOM kills on order-service' },
  { id: '4', label: 'Auto-remediation', start: '2026-04-05T10:15:00Z', end: '2026-04-05T10:20:00Z', category: 'resolution', description: 'Restarted order-service pods' },
  { id: '5', label: 'Maintenance Window', start: '2026-04-05T14:00:00Z', end: '2026-04-05T16:00:00Z', category: 'maintenance', description: 'DB migration for schema v4' },
  { id: '6', label: 'Deploy v2.3.2', start: '2026-04-05T12:00:00Z', end: '2026-04-05T12:10:00Z', category: 'deployment', description: 'Hotfix for memory leak' },
  { id: '7', label: 'Latency Spike', start: '2026-04-05T13:00:00Z', end: '2026-04-05T13:30:00Z', category: 'alert' },
];

const treeMapData = [
  { id: 'api', label: 'API Gateway', value: 42, group: 'frontend' },
  { id: 'auth', label: 'Auth Service', value: 18, group: 'security' },
  { id: 'order', label: 'Order Service', value: 35, group: 'core' },
  { id: 'payment', label: 'Payment', value: 28, group: 'core' },
  { id: 'user', label: 'User Service', value: 22, group: 'core' },
  { id: 'search', label: 'Search', value: 15, group: 'frontend' },
  { id: 'analytics', label: 'Analytics', value: 12, group: 'infra' },
  { id: 'monitoring', label: 'Monitoring', value: 20, group: 'infra' },
  { id: 'cache', label: 'Cache Layer', value: 10, group: 'infra' },
  { id: 'notif', label: 'Notifications', value: 8, group: 'core' },
];

const bubbleData = [
  { id: 'api', label: 'API', x: 12, y: 95, size: 42, group: 'critical' },
  { id: 'auth', label: 'Auth', x: 8, y: 88, size: 18, group: 'critical' },
  { id: 'order', label: 'Orders', x: 25, y: 72, size: 35, group: 'high' },
  { id: 'payment', label: 'Payments', x: 15, y: 65, size: 28, group: 'high' },
  { id: 'search', label: 'Search', x: 6, y: 55, size: 15, group: 'medium' },
  { id: 'analytics', label: 'Analytics', x: 3, y: 45, size: 12, group: 'low' },
  { id: 'cache', label: 'Cache', x: 20, y: 80, size: 10, group: 'medium' },
  { id: 'notif', label: 'Notif', x: 4, y: 60, size: 8, group: 'low' },
];

const radarLabels = ['Availability', 'Latency', 'Error Rate', 'Throughput', 'Recovery', 'Security'];
const radarDatasets = [
  { label: 'Current', values: [92, 78, 85, 70, 88, 76] },
  { label: 'Target', values: [99, 95, 95, 90, 95, 90], color: '#10b981' },
];

type TabKey = 'heatmap' | 'sankey' | 'network' | 'timeline' | 'treemap' | 'bubble' | 'radar' | 'gauge';

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'heatmap', label: 'Heat Map', icon: '🔥' },
  { key: 'sankey', label: 'Sankey Flow', icon: '🔀' },
  { key: 'network', label: 'Network Graph', icon: '🕸' },
  { key: 'timeline', label: 'Timeline', icon: '📅' },
  { key: 'treemap', label: 'Tree Map', icon: '🗺' },
  { key: 'bubble', label: 'Bubble Chart', icon: '⚪' },
  { key: 'radar', label: 'Radar', icon: '📡' },
  { key: 'gauge', label: 'Gauges', icon: '⏱' },
];

export default function VisualizationsPage() {
  const { isMobile } = useBreakpoint();
  const [activeTab, setActiveTab] = useState<TabKey>('heatmap');

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Advanced Visualizations
          </h1>
          <p style={{ color: colors.textMuted, fontSize: 13, margin: '4px 0 0' }}>
            Interactive data visualizations for infrastructure monitoring and incident analysis
          </p>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            gap: 4,
            background: colors.bgCard,
            borderRadius: 12,
            padding: 4,
            marginBottom: 24,
            overflowX: 'auto',
            border: `1px solid ${colors.border}`,
          }}
        >
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '10px 16px',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
                whiteSpace: 'nowrap' as const,
                background: activeTab === tab.key ? colors.bgElevated : 'transparent',
                color: activeTab === tab.key ? colors.text : colors.textDim,
                transition: 'all 0.2s',
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Chart panels */}
        <div
          style={{
            background: colors.bgCard,
            backdropFilter: 'blur(12px)',
            borderRadius: 14,
            border: `1px solid ${colors.border}`,
            padding: 24,
            minHeight: 450,
          }}
        >
          {activeTab === 'heatmap' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Incident Frequency Heatmap
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Incidents by day of week and hour. Click a cell to drill down.
              </p>
              <HeatMap
                data={heatMapData}
                rows={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
                width={900}
                height={320}
                onCellClick={(cell) => console.log('Cell clicked:', cell)}
              />
            </div>
          )}

          {activeTab === 'sankey' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Incident Flow Diagram
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                How data flows through the AI agent pipeline from detection to resolution.
              </p>
              <SankeyDiagram
                nodes={sankeyNodes}
                links={sankeyLinks}
                width={850}
                height={380}
                onNodeClick={(node) => console.log('Node clicked:', node)}
              />
            </div>
          )}

          {activeTab === 'network' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Service Dependency Graph
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Drag nodes to rearrange. Arrows show request direction, labels show latency.
              </p>
              <NetworkGraph
                nodes={networkNodes}
                edges={networkEdges}
                width={850}
                height={420}
                onNodeClick={(node) => console.log('Node clicked:', node)}
              />
            </div>
          )}

          {activeTab === 'timeline' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Incident Timeline
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Chronological view of deployments, incidents, alerts, and maintenance.
              </p>
              <TimelineViz
                events={timelineEvents}
                width={850}
                height={300}
                onEventClick={(event) => console.log('Event clicked:', event)}
              />
              <div style={{ display: 'flex', gap: 16, marginTop: 12 }}>
                {[
                  { label: 'Deployment', color: '#3b82f6' },
                  { label: 'Alert', color: '#f97316' },
                  { label: 'Incident', color: '#ef4444' },
                  { label: 'Resolution', color: '#10b981' },
                  { label: 'Maintenance', color: '#f59e0b' },
                ].map((l) => (
                  <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: l.color }} />
                    <span style={{ color: colors.textMuted, fontSize: 11 }}>{l.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'treemap' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Incident Distribution by Service
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Size represents incident count. Click to see service details.
              </p>
              <TreeMap
                data={treeMapData}
                width={850}
                height={380}
                onItemClick={(item) => console.log('Item clicked:', item)}
              />
            </div>
          )}

          {activeTab === 'bubble' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Service Risk Analysis
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                X: incident frequency, Y: uptime %, bubble size: impact score.
              </p>
              <BubbleChart
                data={bubbleData}
                xLabel="Incidents / Month"
                yLabel="Uptime %"
                width={850}
                height={380}
                onBubbleClick={(b) => console.log('Bubble clicked:', b)}
              />
            </div>
          )}

          {activeTab === 'radar' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                Service Health Radar
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Current performance vs. targets across key reliability dimensions.
              </p>
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <RadarChart
                  labels={radarLabels}
                  datasets={radarDatasets}
                  maxValue={100}
                  width={500}
                  height={420}
                />
              </div>
            </div>
          )}

          {activeTab === 'gauge' && (
            <div>
              <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, marginTop: 0, marginBottom: 4 }}>
                System Health Gauges
              </h2>
              <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 16 }}>
                Real-time system health metrics with animated thresholds.
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 24, justifyContent: 'center' }}>
                <GaugeChart value={87} label="CPU Usage" unit="%" />
                <GaugeChart value={62} label="Memory" unit="%" />
                <GaugeChart
                  value={99.7}
                  min={95}
                  max={100}
                  label="Uptime"
                  unit="%"
                  thresholds={[
                    { value: 99, color: '#ef4444', label: 'Critical' },
                    { value: 99.9, color: '#f59e0b', label: 'Warning' },
                    { value: 100, color: '#10b981', label: 'Healthy' },
                  ]}
                />
                <GaugeChart value={23} label="Error Rate" unit="%" />
                <GaugeChart
                  value={145}
                  min={0}
                  max={200}
                  label="Latency"
                  unit="ms"
                  thresholds={[
                    { value: 100, color: '#10b981', label: 'Fast' },
                    { value: 150, color: '#f59e0b', label: 'Moderate' },
                    { value: 200, color: '#ef4444', label: 'Slow' },
                  ]}
                />
                <GaugeChart value={78} label="Throughput" unit="%" />
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
