'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Pattern {
  id: string;
  name: string;
  description: string | null;
  pattern_type: string;
  frequency: number;
  confidence: number;
  trending: string;
  affected_services: Record<string, unknown> | null;
  best_actions: Record<string, unknown> | null;
  last_seen: string | null;
}

interface OutcomeStat {
  action_name: string;
  total: number;
  successes: number;
  success_rate: number;
  avg_duration: number;
  avg_impact: number;
}

export default function PatternInsights() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [outcomeStats, setOutcomeStats] = useState<OutcomeStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [patternsRes, statsRes] = await Promise.all([
        api.get('/learning/patterns', { params: { limit: 20 } }),
        api.get('/learning/outcomes/stats'),
      ]);
      setPatterns(patternsRes.data);
      setOutcomeStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load pattern data:', error);
    } finally {
      setLoading(false);
    }
  };

  const trendingIcon = (trending: string) => {
    if (trending === 'increasing') return '↑';
    if (trending === 'decreasing') return '↓';
    return '→';
  };

  const trendingColor = (trending: string) => {
    if (trending === 'increasing') return 'text-red-600';
    if (trending === 'decreasing') return 'text-green-600';
    return 'text-gray-500';
  };

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading pattern data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Pattern Clusters */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">Discovered Patterns</h3>
          <p className="text-sm text-gray-500">Recurring incident patterns identified by the Learning Agent</p>
        </div>
        <div className="divide-y">
          {patterns.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No patterns discovered yet. The system learns from resolved incidents.
            </div>
          ) : (
            patterns.map((pattern) => (
              <div key={pattern.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{pattern.name}</h4>
                    <p className="text-sm text-gray-500">{pattern.description}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{pattern.frequency}</div>
                      <div className="text-xs text-gray-500">occurrences</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold">{pattern.confidence.toFixed(0)}%</div>
                      <div className="text-xs text-gray-500">confidence</div>
                    </div>
                    <span className={`text-lg font-bold ${trendingColor(pattern.trending)}`}>
                      {trendingIcon(pattern.trending)}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      pattern.trending === 'increasing'
                        ? 'bg-red-100 text-red-700'
                        : pattern.trending === 'decreasing'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {pattern.trending}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Action Effectiveness */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">Action Effectiveness</h3>
          <p className="text-sm text-gray-500">Success rates for each remediation action</p>
        </div>
        <div className="overflow-x-auto">
          {outcomeStats.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No action outcomes tracked yet.
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b">
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Total Uses</th>
                  <th className="px-6 py-3">Successes</th>
                  <th className="px-6 py-3">Success Rate</th>
                  <th className="px-6 py-3">Avg Duration</th>
                  <th className="px-6 py-3">Avg Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {outcomeStats.map((stat) => (
                  <tr key={stat.action_name} className="hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium">{stat.action_name}</td>
                    <td className="px-6 py-3">{stat.total}</td>
                    <td className="px-6 py-3">{stat.successes}</td>
                    <td className="px-6 py-3">
                      <span className={`font-medium ${
                        stat.success_rate >= 80 ? 'text-green-600' :
                        stat.success_rate >= 50 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {stat.success_rate}%
                      </span>
                    </td>
                    <td className="px-6 py-3">{stat.avg_duration.toFixed(1)}s</td>
                    <td className="px-6 py-3">
                      <span className={stat.avg_impact >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {stat.avg_impact > 0 ? '+' : ''}{stat.avg_impact.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
