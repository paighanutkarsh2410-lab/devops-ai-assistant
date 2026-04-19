'use client';

import { ReactNode, useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface NavItem { icon: string; label: string; path: string; }
interface NavGroup { title: string; items: NavItem[]; }

const navGroups: NavGroup[] = [
  {
    title: 'Overview',
    items: [
      { icon: '📊', label: 'Dashboard', path: '/dashboard' },
      { icon: '⚡', label: 'Live Metrics', path: '/live' },
      { icon: '💬', label: 'AI Chat', path: '/chat' },
    ],
  },
  {
    title: 'Monitoring',
    items: [
      { icon: '🫀', label: 'System Health', path: '/system-health' },
      { icon: '📈', label: 'Analytics', path: '/analytics' },
      { icon: '🏎️', label: 'Performance', path: '/performance' },
      { icon: '🔮', label: 'Predictions', path: '/predictions' },
    ],
  },
  {
    title: 'AI Agents',
    items: [
      { icon: '🤖', label: 'Agent Status', path: '/agents/status' },
      { icon: '🧠', label: 'Intelligence', path: '/agent-intelligence' },
      { icon: '🕸️', label: 'Decision Graph', path: '/decision-graph' },
      { icon: '▶️', label: 'Incident Flow', path: '/incident-flow' },
      { icon: '🏗️', label: 'Agent Builder', path: '/agents/builder' },
      { icon: '🛒', label: 'Marketplace', path: '/marketplace' },
      { icon: '📚', label: 'Learning', path: '/learning' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { icon: '🔄', label: 'Workflows', path: '/workflows' },
      { icon: '📋', label: 'Runbooks', path: '/runbooks' },
      { icon: '🔧', label: 'Maintenance', path: '/maintenance' },
      { icon: '💥', label: 'Chaos Testing', path: '/chaos' },
      { icon: '🔮', label: 'Scenarios', path: '/scenarios' },
    ],
  },
  {
    title: 'Security',
    items: [
      { icon: '🛡️', label: 'Security', path: '/security' },
      { icon: '✅', label: 'Compliance', path: '/compliance' },
      { icon: '📝', label: 'Audit Log', path: '/audit' },
      { icon: '🔥', label: 'Disaster Recovery', path: '/disaster-recovery' },
    ],
  },
  {
    title: 'Insights',
    items: [
      { icon: '📊', label: 'Reports', path: '/reports' },
      { icon: '💰', label: 'Cost Analysis', path: '/costs' },
      { icon: '📉', label: 'SLA Tracking', path: '/sla' },
      { icon: '👔', label: 'Executive View', path: '/executive' },
      { icon: '📉', label: 'Visualizations', path: '/visualizations' },
    ],
  },
];

const bottomNav: NavItem[] = [
  { icon: '🔔', label: 'Notifications', path: '/notifications' },
  { icon: '🔌', label: 'Integrations', path: '/integrations' },
  { icon: '⚙️', label: 'Settings', path: '/settings/notifications' },
];

// Mini particle background for dashboard area
function DashboardParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let animId: number;

    const resize = () => { canvas.width = canvas.parentElement?.clientWidth || window.innerWidth; canvas.height = canvas.parentElement?.clientHeight || window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);

    const particles = Array.from({ length: 35 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.12,
      vy: (Math.random() - 0.5) * 0.12,
      size: Math.random() * 1.2 + 0.4,
      phase: Math.random() * Math.PI * 2,
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const t = Date.now() * 0.001;
      particles.forEach((p, i) => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width; if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height; if (p.y > canvas.height) p.y = 0;
        const op = 0.12 + Math.sin(t + p.phase) * 0.08;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(59,130,246,${op})`;
        ctx.fill();
        // Connect nearby
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const d = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (d < 100) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(59,130,246,${0.03 * (1 - d / 100)})`;
            ctx.lineWidth = 0.4;
            ctx.stroke();
          }
        }
      });
      animId = requestAnimationFrame(animate);
    };
    animate();
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize); };
  }, []);
  return <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0 }} />;
}

export default function DashboardShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const { isMobile } = useBreakpoint();

  useEffect(() => { setMounted(true); }, []);

  // Restore sidebar scroll position across navigations
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    const saved = sessionStorage.getItem('sidebar-scroll');
    if (saved) nav.scrollTop = Number(saved);
  }, []);

  // Save scroll position on every scroll
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    const handleScroll = () => sessionStorage.setItem('sidebar-scroll', String(nav.scrollTop));
    nav.addEventListener('scroll', handleScroll, { passive: true });
    return () => nav.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path: string) => pathname === path || pathname.startsWith(path + '/');
  const sidebarWidth = collapsed ? 68 : 248;

  const renderNavButton = (item: NavItem, showBorder = true) => {
    const active = isActive(item.path);
    const hovered = hoveredItem === item.path;
    return (
      <button
        key={item.path}
        onClick={() => router.push(item.path)}
        onMouseEnter={() => setHoveredItem(item.path)}
        onMouseLeave={() => setHoveredItem(null)}
        title={collapsed ? item.label : undefined}
        style={{
          width: '100%',
          display: 'flex', alignItems: 'center',
          gap: 10,
          padding: collapsed ? '9px 0' : '8px 12px',
          justifyContent: collapsed ? 'center' : 'flex-start',
          borderRadius: 10,
          border: 'none',
          background: active
            ? 'rgba(59,130,246,0.1)'
            : hovered
              ? 'rgba(255,255,255,0.03)'
              : 'transparent',
          color: active ? '#60a5fa' : hovered ? colors.text : colors.textSecondary,
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: active ? 600 : 400,
          transition: 'all 0.2s ease',
          textAlign: 'left',
          marginBottom: 2,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Active indicator */}
        {active && showBorder && (
          <div style={{
            position: 'absolute', left: 0, top: '20%', bottom: '20%', width: 3,
            background: 'linear-gradient(180deg, #3b82f6, #8b5cf6)',
            borderRadius: '0 3px 3px 0',
            boxShadow: '0 0 8px rgba(59,130,246,0.4)',
          }} />
        )}
        {/* Hover glow */}
        {(hovered || active) && (
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: active
              ? 'radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.08), transparent 70%)'
              : 'radial-gradient(ellipse at 50% 50%, rgba(255,255,255,0.02), transparent 70%)',
          }} />
        )}
        <span style={{
          fontSize: 16, flexShrink: 0, position: 'relative',
          filter: active ? 'drop-shadow(0 0 4px rgba(59,130,246,0.4))' : 'none',
        }}>{item.icon}</span>
        {!collapsed && <span style={{ whiteSpace: 'nowrap', position: 'relative' }}>{item.label}</span>}
      </button>
    );
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#04040c' }}>
      {/* ═══ SIDEBAR (hidden on mobile — MobileNav handles navigation) ═══ */}
      <aside style={{
        width: sidebarWidth,
        minHeight: '100vh',
        background: 'rgba(6,6,15,0.95)',
        backdropFilter: 'blur(20px)',
        display: isMobile ? 'none' : 'flex',
        borderRight: '1px solid rgba(255,255,255,0.04)',
        flexDirection: 'column',
        transition: 'width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
        position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 40,
        overflowY: 'auto', overflowX: 'hidden',
      }}>
        {/* Sidebar ambient glow */}
        <div style={{
          position: 'absolute', top: 0, right: 0, width: 1, height: '100%',
          background: 'linear-gradient(180deg, rgba(59,130,246,0.1) 0%, transparent 30%, transparent 70%, rgba(139,92,246,0.1) 100%)',
          pointerEvents: 'none',
        }} />

        {/* Logo */}
        <div
          onClick={() => router.push('/')}
          style={{
            padding: collapsed ? '18px 12px' : '18px 18px',
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            display: 'flex', alignItems: 'center', gap: 12,
            cursor: 'pointer', minHeight: 60,
          }}
        >
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18, flexShrink: 0,
            boxShadow: '0 0 15px rgba(59,130,246,0.3), 0 0 30px rgba(139,92,246,0.1)',
            animation: mounted ? 'glow-pulse 4s ease-in-out infinite' : 'none',
          }}>⚡</div>
          {!collapsed && (
            <div>
              <span style={{
                fontSize: 16, fontWeight: 800, display: 'block', lineHeight: 1,
                background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>DevOps AI</span>
              <span style={{
                fontSize: 9, fontWeight: 700, color: '#3b82f680',
                letterSpacing: 2, textTransform: 'uppercase' as const,
              }}>ASSISTANT</span>
            </div>
          )}
        </div>

        {/* Collapse toggle — morphing hamburger */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            width: collapsed ? 40 : 36, height: 36,
            margin: collapsed ? '10px auto 2px' : '10px 10px 2px auto',
            borderRadius: 10, border: '1px solid rgba(255,255,255,0.05)',
            background: 'rgba(255,255,255,0.02)',
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
            position: 'relative',
          }}
        >
          <div style={{ width: 18, height: 14, position: 'relative' }}>
            {/* Top bar */}
            <span style={{
              position: 'absolute', left: 0, height: 2, borderRadius: 2,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              transition: 'all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)',
              width: collapsed ? 18 : 12,
              top: collapsed ? 6 : 0,
              transform: collapsed ? 'rotate(45deg)' : 'rotate(0)',
              transformOrigin: 'center',
            }} />
            {/* Middle bar */}
            <span style={{
              position: 'absolute', left: 0, top: 6, height: 2, borderRadius: 2,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              transition: 'all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)',
              width: collapsed ? 0 : 18,
              opacity: collapsed ? 0 : 1,
            }} />
            {/* Bottom bar */}
            <span style={{
              position: 'absolute', left: 0, height: 2, borderRadius: 2,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              transition: 'all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)',
              width: collapsed ? 18 : 14,
              top: collapsed ? 6 : 12,
              transform: collapsed ? 'rotate(-45deg)' : 'rotate(0)',
              transformOrigin: 'center',
            }} />
          </div>
        </button>

        {/* Nav groups */}
        <nav ref={navRef} style={{ flex: 1, padding: '6px 8px', overflowY: 'auto' }}>
          {navGroups.map((group) => (
            <div key={group.title} style={{ marginBottom: 6 }}>
              {!collapsed && (
                <div style={{
                  padding: '10px 12px 4px',
                  fontSize: 10, fontWeight: 700,
                  color: '#3b82f650',
                  textTransform: 'uppercase' as const,
                  letterSpacing: 2,
                }}>
                  {group.title}
                </div>
              )}
              {collapsed && <div style={{ height: 1, background: 'rgba(255,255,255,0.03)', margin: '6px 8px' }} />}
              {group.items.map((item) => renderNavButton(item))}
            </div>
          ))}
        </nav>

        {/* Bottom nav */}
        <div style={{ padding: '8px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          {bottomNav.map((item) => renderNavButton(item, false))}
        </div>
      </aside>

      {/* ═══ MAIN CONTENT ═══ */}
      <main style={{
        flex: 1, marginLeft: isMobile ? 0 : sidebarWidth,
        transition: 'margin-left 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
        minHeight: '100vh', background: '#04040c',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Ambient background effects */}
        <DashboardParticles />
        {/* Top-right glow */}
        <div style={{
          position: 'fixed', top: -200, right: -200, width: 500, height: 500,
          background: 'radial-gradient(circle, rgba(59,130,246,0.04) 0%, transparent 60%)',
          pointerEvents: 'none', zIndex: 0,
          animation: mounted ? 'breathe 8s ease-in-out infinite' : 'none',
        }} />
        {/* Bottom-left glow */}
        <div style={{
          position: 'fixed', bottom: -200, left: sidebarWidth - 100, width: 400, height: 400,
          background: 'radial-gradient(circle, rgba(139,92,246,0.03) 0%, transparent 60%)',
          pointerEvents: 'none', zIndex: 0,
          animation: mounted ? 'breathe 10s ease-in-out 3s infinite' : 'none',
        }} />
        {/* Grid mesh — subtle */}
        <div style={{
          position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
          backgroundImage: `
            linear-gradient(rgba(59,130,246,0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59,130,246,0.015) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          maskImage: 'radial-gradient(ellipse at 70% 30%, rgba(0,0,0,0.4) 0%, transparent 60%)',
          WebkitMaskImage: 'radial-gradient(ellipse at 70% 30%, rgba(0,0,0,0.4) 0%, transparent 60%)',
        }} />

        {/* Content with relative z-index */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          {children}
        </div>
      </main>
    </div>
  );
}
