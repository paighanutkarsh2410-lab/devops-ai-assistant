'use client';

import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';
import ChatInterface from '../../components/ChatInterface';

export default function ChatPage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 900, margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              DevOps AI Chat
            </h1>
            <span style={{
              fontSize: 12,
              background: colors.successBg,
              color: colors.success,
              padding: '2px 10px',
              borderRadius: 12,
              fontWeight: 500,
            }}>
              Online
            </span>
          </div>
          <nav style={{ display: 'flex', gap: 8 }}>
            {[
              { label: 'Dashboard', path: '/dashboard' },
              { label: 'Learning', path: '/learning' },
              { label: 'Predictions', path: '/predictions' },
            ].map(item => (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                style={btn}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Chat */}
        <div className="slide-up-d1" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <ChatInterface />
        </div>
      </div>
    </DashboardShell>
  );
}
