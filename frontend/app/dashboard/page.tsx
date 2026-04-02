'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI, incidentsAPI } from '@/lib/api';
import LiveMetrics from '@/components/LiveMetrics';
import IncidentDetail from '@/components/IncidentDetail';
import ActionLog from '@/components/ActionLog';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  company: string | null;
  is_active: boolean;
  created_at: string;
}

interface Incident {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  service_name: string | null;
  root_cause: string | null;
  solution: string | null;
  detected_at: string;
  resolved_at: string | null;
  auto_resolved: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'metrics' | 'remediations'>('overview');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/login');
        return;
      }

      const userResponse = await authAPI.getCurrentUser();
      setUser(userResponse.data);

      const incidentsResponse = await incidentsAPI.getAll();
      setIncidents(incidentsResponse.data);
    } catch (error) {
      console.error('Error loading data:', error);
      localStorage.removeItem('token');
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold">DevOps AI Assistant</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">Welcome, {user?.full_name || user?.email}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500">Total Incidents</div>
            <div className="text-3xl font-bold">{incidents.length}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500">Open</div>
            <div className="text-3xl font-bold text-yellow-600">
              {incidents.filter(i => i.status === 'open').length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500">Resolved</div>
            <div className="text-3xl font-bold text-green-600">
              {incidents.filter(i => i.status === 'resolved').length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500">Auto-Resolved</div>
            <div className="text-3xl font-bold text-blue-600">
              {incidents.filter(i => i.auto_resolved).length}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'overview' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Incidents
          </button>
          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'metrics' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Live Metrics
          </button>
          <button
            onClick={() => setActiveTab('remediations')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'remediations' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Remediations
          </button>
          <button
            onClick={() => router.push('/audit')}
            className="px-4 py-2 rounded-lg font-medium bg-white text-gray-700 hover:bg-gray-100"
          >
            Audit Log
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'remediations' ? (
          <ActionLog />
        ) : activeTab === 'overview' ? (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-semibold">Recent Incidents</h2>
            </div>
            <div className="divide-y">
              {incidents.length === 0 ? (
                <div className="px-6 py-8 text-center text-gray-500">
                  No incidents yet. System is healthy!
                </div>
              ) : (
                incidents.slice(0, 10).map((incident) => (
                  <div key={incident.id} className="px-6 py-4 hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedIncident(incident)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{incident.title}</h3>
                        <p className="text-sm text-gray-500">{incident.service_name}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          incident.severity === 'critical' ? 'bg-red-100 text-red-800' :
                          incident.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                          incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {incident.severity}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          incident.status === 'resolved' ? 'bg-green-100 text-green-800' :
                          incident.status === 'investigating' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {incident.status}
                        </span>
                        <span className="text-xs text-blue-600">View Details</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          <LiveMetrics />
        )}
      </main>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <IncidentDetail
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
        />
      )}
    </div>
  );
}
