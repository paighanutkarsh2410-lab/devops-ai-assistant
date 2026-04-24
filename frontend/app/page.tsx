'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useBreakpoint } from '@/lib/useMediaQuery';

// ═══════════════════════════════════════════════════════════
// NEURAL NETWORK PARTICLE SYSTEM — Interactive connected nodes
// ═══════════════════════════════════════════════════════════
function NeuralCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let mouse = { x: -9999, y: -9999 };
    let time = 0;

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', (e) => { mouse = { x: e.clientX, y: e.clientY }; });

    interface Node {
      x: number; y: number; baseX: number; baseY: number;
      vx: number; vy: number; size: number; phase: number;
      color: string; pulseSpeed: number;
    }

    const colors = ['#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899', '#10b981', '#f59e0b'];
    const nodes: Node[] = [];

    for (let i = 0; i < 90; i++) {
      const x = Math.random() * canvas.width;
      const y = Math.random() * canvas.height;
      nodes.push({
        x, y, baseX: x, baseY: y,
        vx: (Math.random() - 0.5) * 0.15,
        vy: (Math.random() - 0.5) * 0.15,
        size: Math.random() * 2.5 + 0.8,
        phase: Math.random() * Math.PI * 2,
        color: colors[Math.floor(Math.random() * colors.length)],
        pulseSpeed: 0.005 + Math.random() * 0.01,
      });
    }

    const animate = () => {
      time++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      nodes.forEach((n, i) => {
        // Mouse interaction — attract gently, repel when close
        const dx = mouse.x - n.x;
        const dy = mouse.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200 && dist > 50) {
          n.x += dx * 0.003;
          n.y += dy * 0.003;
        } else if (dist <= 50) {
          n.x -= dx * 0.03;
          n.y -= dy * 0.03;
        }

        // Organic floating motion
        n.x += n.vx + Math.sin(time * 0.003 + n.phase) * 0.15;
        n.y += n.vy + Math.cos(time * 0.004 + n.phase) * 0.12;

        // Drift back to base
        n.x += (n.baseX - n.x) * 0.002;
        n.y += (n.baseY - n.y) * 0.002;

        // Breathing size
        const breathe = 1 + Math.sin(time * n.pulseSpeed + n.phase) * 0.4;
        const currentSize = n.size * breathe;

        // Glow
        const gradient = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, currentSize * 6);
        gradient.addColorStop(0, n.color + '40');
        gradient.addColorStop(0.5, n.color + '10');
        gradient.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(n.x, n.y, currentSize * 6, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // Core
        ctx.beginPath();
        ctx.arc(n.x, n.y, currentSize, 0, Math.PI * 2);
        ctx.fillStyle = n.color + 'cc';
        ctx.fill();

        // Neural connections
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const d = Math.sqrt((n.x - n2.x) ** 2 + (n.y - n2.y) ** 2);
          if (d < 140) {
            const alpha = (1 - d / 140) * 0.15;
            // Pulsing connection
            const pulse = 0.5 + Math.sin(time * 0.02 + i + j) * 0.5;
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = `rgba(59,130,246,${alpha * pulse})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();

            // Data flow dot traveling along connection
            if (d < 80 && Math.random() < 0.005) {
              const t = (time * 0.01 + i) % 1;
              const fx = n.x + (n2.x - n.x) * t;
              const fy = n.y + (n2.y - n.y) * t;
              ctx.beginPath();
              ctx.arc(fx, fy, 1.5, 0, Math.PI * 2);
              ctx.fillStyle = '#3b82f680';
              ctx.fill();
            }
          }
        }
      });

      animId = requestAnimationFrame(animate);
    };
    animate();

    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize); };
  }, []);

  return <canvas ref={canvasRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />;
}

// ═══════════════════════════════════════════════════════════
// 3D HOLOGRAPHIC SPHERE — CSS-only animated globe
// ═══════════════════════════════════════════════════════════
function HolographicSphere() {
  return (
    <div style={{
      width: 320, height: 320, position: 'relative',
      animation: 'float 8s ease-in-out infinite',
      perspective: 1000,
    }}>
      {/* Outer glow */}
      <div style={{
        position: 'absolute', inset: -40,
        background: 'radial-gradient(circle, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.06) 40%, transparent 65%)',
        animation: 'breathe 4s ease-in-out infinite',
        borderRadius: '50%', filter: 'blur(20px)',
      }} />
      {/* Main sphere */}
      <div style={{
        width: '100%', height: '100%', position: 'relative',
        transformStyle: 'preserve-3d',
        animation: 'spin-slow 25s linear infinite',
      }}>
        {/* Latitude rings */}
        {[0, 30, 60, 90, 120, 150].map((angle) => (
          <div key={`lat-${angle}`} style={{
            position: 'absolute', inset: 0,
            border: '1px solid rgba(59,130,246,0.12)',
            borderRadius: '50%',
            transform: `rotateX(${angle}deg)`,
          }} />
        ))}
        {/* Longitude rings */}
        {[0, 45, 90, 135].map((angle) => (
          <div key={`lon-${angle}`} style={{
            position: 'absolute', inset: 0,
            border: '1px solid rgba(139,92,246,0.1)',
            borderRadius: '50%',
            transform: `rotateY(${angle}deg)`,
          }} />
        ))}
        {/* Orbital ring 1 */}
        <div style={{
          position: 'absolute', inset: -20,
          border: '1.5px solid rgba(59,130,246,0.15)',
          borderRadius: '50%',
          transform: 'rotateX(70deg) rotateZ(20deg)',
          animation: 'spin-slow 15s linear infinite reverse',
        }}>
          <div style={{
            position: 'absolute', top: -4, left: '50%',
            width: 8, height: 8, borderRadius: '50%',
            background: '#3b82f6',
            boxShadow: '0 0 15px #3b82f6, 0 0 30px #3b82f660',
          }} />
        </div>
        {/* Orbital ring 2 */}
        <div style={{
          position: 'absolute', inset: -35,
          border: '1px solid rgba(236,72,153,0.1)',
          borderRadius: '50%',
          transform: 'rotateX(30deg) rotateY(60deg)',
          animation: 'spin-slow 20s linear infinite',
        }}>
          <div style={{
            position: 'absolute', bottom: -3, right: '30%',
            width: 6, height: 6, borderRadius: '50%',
            background: '#ec4899',
            boxShadow: '0 0 12px #ec4899, 0 0 24px #ec489960',
          }} />
        </div>
        {/* Core glow */}
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 80, height: 80, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.25) 0%, rgba(139,92,246,0.1) 50%, transparent 70%)',
          animation: 'breathe 3s ease-in-out infinite',
          filter: 'blur(10px)',
        }} />
        {/* Surface dots — precomputed positions to avoid hydration mismatch */}
        {[
          [-126,62,-1], [-96,-20,100], [-19,-109,83], [85,-83,73],
          [130,51,19], [73,119,-20], [-40,105,-82], [-130,11,-55],
          [-79,-95,-56], [31,-88,-103], [120,-18,-70], [90,95,37],
          [-8,137,21], [-108,60,60], [-76,-66,97], [56,-30,128],
          [121,51,-52], [28,132,-38], [-95,68,-78], [-68,-117,27],
        ].map((pos, i) => (
          <div key={`dot-${i}`} style={{
            position: 'absolute', left: '50%', top: '50%',
            width: 3, height: 3, borderRadius: '50%',
            background: i % 3 === 0 ? '#3b82f6' : i % 3 === 1 ? '#8b5cf6' : '#06b6d4',
            boxShadow: `0 0 6px ${i % 3 === 0 ? '#3b82f6' : i % 3 === 1 ? '#8b5cf6' : '#06b6d4'}`,
            transform: `translate3d(${pos[0]}px, ${pos[1]}px, ${pos[2]}px) translate(-50%, -50%)`,
            opacity: 0.7,
          }} />
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 3D TILT CARD with glare and glow
// ═══════════════════════════════════════════════════════════
function TiltCard({ children, gradient, delay, index }: { children: React.ReactNode; gradient: string; delay: number; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [style, setStyle] = useState({ transform: 'perspective(800px) rotateX(0) rotateY(0)', glareX: 50, glareY: 50, glareOp: 0 });

  const handleMove = useCallback((e: React.MouseEvent) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setStyle({
      transform: `perspective(800px) rotateX(${(0.5 - y) * 18}deg) rotateY(${(x - 0.5) * 18}deg) scale3d(1.05, 1.05, 1.05)`,
      glareX: x * 100, glareY: y * 100, glareOp: 0.12,
    });
  }, []);

  const handleLeave = useCallback(() => {
    setStyle({ transform: 'perspective(800px) rotateX(0) rotateY(0) scale3d(1,1,1)', glareX: 50, glareY: 50, glareOp: 0 });
  }, []);

  return (
    <div ref={ref} onMouseMove={handleMove} onMouseLeave={handleLeave}
      style={{
        transform: style.transform, transition: 'transform 0.15s ease-out',
        animation: `slide-up 0.7s ease-out ${delay}s both`,
        position: 'relative', borderRadius: 24, overflow: 'hidden',
        background: 'rgba(255,255,255,0.015)',
        border: '1px solid rgba(255,255,255,0.05)',
        padding: 36, cursor: 'default',
        boxShadow: style.glareOp > 0 ? '0 25px 60px rgba(0,0,0,0.4), 0 0 40px rgba(59,130,246,0.05)' : 'none',
      }}>
      {/* Top edge glow */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 1.5, background: gradient, opacity: 0.5 }} />
      {/* Glare */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `radial-gradient(circle at ${style.glareX}% ${style.glareY}%, rgba(255,255,255,${style.glareOp}), transparent 50%)`,
      }} />
      {/* Corner number */}
      <div style={{
        position: 'absolute', top: 16, right: 20,
        fontSize: 48, fontWeight: 900, color: 'rgba(255,255,255,0.02)',
        lineHeight: 1,
      }}>0{index + 1}</div>
      {children}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// ANIMATED COUNTER with scroll trigger
// ═══════════════════════════════════════════════════════════
function AnimCounter({ value, suffix = '', prefix = '' }: { value: string; suffix?: string; prefix?: string }) {
  const [display, setDisplay] = useState('0');
  const ref = useRef<HTMLSpanElement>(null);
  const triggered = useRef(false);

  useEffect(() => {
    const num = parseInt(value);
    if (isNaN(num)) { setDisplay(value); return; }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !triggered.current) {
        triggered.current = true;
        const duration = 2000;
        const start = Date.now();
        const tick = () => {
          const elapsed = Date.now() - start;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 4);
          setDisplay(Math.round(eased * num).toString());
          if (progress < 1) requestAnimationFrame(tick);
        };
        tick();
        observer.disconnect();
      }
    }, { threshold: 0.5 });

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [value]);

  return <span ref={ref}>{prefix}{display}{suffix}</span>;
}

// ═══════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════
export default function HomePage() {
  const router = useRouter();
  const [hoveredBtn, setHoveredBtn] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const { isMobile } = useBreakpoint();

  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    const h = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  const features = [
    { icon: '📡', title: 'Real-Time Monitoring', desc: 'Z-score anomaly detection across CPU, memory, response time with dynamic thresholds that adapt to your infrastructure patterns', gradient: 'linear-gradient(135deg, #3b82f6, #06b6d4)' },
    { icon: '🧬', title: 'AI Root Cause Analysis', desc: 'Multi-service correlation engine that traces cascading failures across your entire stack to find the true origin', gradient: 'linear-gradient(135deg, #8b5cf6, #a855f7)' },
    { icon: '⚡', title: 'Auto-Remediation', desc: 'Safe execution framework with pre-validation, approval gates, automatic rollback, and complete audit trail', gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)' },
    { icon: '🧠', title: 'Neural Learning', desc: 'Vector-based pattern recognition that builds a knowledge base from every resolved incident, getting smarter over time', gradient: 'linear-gradient(135deg, #10b981, #06b6d4)' },
    { icon: '🔮', title: 'Predictive Intelligence', desc: 'Forecast capacity breaches, cost anomalies, and potential failures before they impact your users', gradient: 'linear-gradient(135deg, #ec4899, #8b5cf6)' },
    { icon: '🔔', title: 'Smart Notifications', desc: 'Multi-channel alert routing with intelligent deduplication, escalation policies, and on-call schedule integration', gradient: 'linear-gradient(135deg, #06b6d4, #3b82f6)' },
    { icon: '📄', title: 'Log Analysis', desc: 'Intelligent log parsing with regex pattern matching, error clustering, and AI-powered root cause insights across all services', gradient: 'linear-gradient(135deg, #a855f7, #6366f1)' },
    { icon: '📐', title: 'Capacity Planning', desc: 'Resource trend analysis with linear regression, exhaustion prediction, and automated scaling recommendations before limits are hit', gradient: 'linear-gradient(135deg, #14b8a6, #06b6d4)' },
  ];

  const pipeline = [
    { step: 'Monitor', icon: '📡', color: '#3b82f6' },
    { step: 'Diagnose', icon: '🔬', color: '#8b5cf6' },
    { step: 'Logs', icon: '📄', color: '#a855f7' },
    { step: 'Remediate', icon: '⚡', color: '#f59e0b' },
    { step: 'Learn', icon: '🧠', color: '#10b981' },
    { step: 'Predict', icon: '🔮', color: '#ec4899' },
    { step: 'Capacity', icon: '📐', color: '#14b8a6' },
    { step: 'Notify', icon: '🔔', color: '#06b6d4' },
  ];

  return (
    <div style={{
      minHeight: '100vh', background: '#030308', color: '#fff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      overflowX: 'hidden', position: 'relative',
    }}>
      <NeuralCanvas />

      {/* ═══ AMBIENT LIGHTING ═══ */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0, overflow: 'hidden' }}>
        {/* Aurora bands */}
        <div style={{
          position: 'absolute', top: '-25%', left: '-15%', width: '130%', height: '50%',
          background: 'linear-gradient(180deg, transparent, rgba(59,130,246,0.03), rgba(139,92,246,0.02), transparent)',
          transform: `rotate(-6deg) translateY(${scrollY * 0.08}px)`,
          animation: 'aurora-drift 14s ease-in-out infinite', filter: 'blur(50px)',
        }} />
        <div style={{
          position: 'absolute', top: '20%', right: '-10%', width: '80%', height: '40%',
          background: 'linear-gradient(180deg, transparent, rgba(236,72,153,0.02), rgba(6,182,212,0.015), transparent)',
          transform: `rotate(4deg) translateY(${scrollY * -0.04}px)`,
          animation: 'aurora-drift 18s ease-in-out infinite reverse', filter: 'blur(70px)',
        }} />
        {/* Animated mesh grid */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          animation: 'grid-breathe 8s ease-in-out infinite',
          maskImage: 'radial-gradient(ellipse at 50% 30%, black 20%, transparent 70%)',
          WebkitMaskImage: 'radial-gradient(ellipse at 50% 30%, black 20%, transparent 70%)',
        }} />
      </div>

      {/* ═══ NAVIGATION ═══ */}
      <nav className={mounted ? 'slide-up' : ''} style={{
        display: isMobile ? 'none' : 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '16px 48px', position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: scrollY > 50 ? 'rgba(3,3,8,0.8)' : 'transparent',
        backdropFilter: scrollY > 50 ? 'blur(20px)' : 'none',
        borderBottom: scrollY > 50 ? '1px solid rgba(255,255,255,0.04)' : 'none',
        transition: 'all 0.4s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ position: 'relative' }}>
            <img
              src="/logo.svg"
              alt="SentryAI"
              style={{
                width: 44, height: 44,
                filter: 'drop-shadow(0 0 12px rgba(139,92,246,0.5))',
                animation: 'glow-pulse 4s ease-in-out infinite',
              }}
            />
            <div style={{
              position: 'absolute', inset: -5, borderRadius: 18,
              border: '1px solid rgba(59,130,246,0.25)',
              animation: 'ripple 3s ease-out infinite',
            }} />
          </div>
          <div>
            <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.5px', display: 'block', lineHeight: 1 }}>
              Sentry<span style={{
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899)',
                backgroundSize: '200% auto',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                animation: 'text-gradient 4s linear infinite',
              }}>AI</span>
            </span>
            <span style={{ fontSize: 9, color: '#3b82f680', fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase' }}>AUTONOMOUS OPS</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={() => router.push('/login')}
            onMouseEnter={() => setHoveredBtn('signin')} onMouseLeave={() => setHoveredBtn(null)}
            style={{
              padding: '10px 24px', borderRadius: 12, cursor: 'pointer', fontSize: 14, fontWeight: 500,
              border: '1px solid rgba(255,255,255,0.06)',
              background: hoveredBtn === 'signin' ? 'rgba(255,255,255,0.05)' : 'transparent',
              color: '#a1a1aa', transition: 'all 0.3s',
            }}>Sign In</button>
          <button onClick={() => router.push('/dashboard')}
            onMouseEnter={() => setHoveredBtn('demo')} onMouseLeave={() => setHoveredBtn(null)}
            style={{
              padding: '10px 24px', borderRadius: 12, border: 'none', cursor: 'pointer',
              fontSize: 14, fontWeight: 700, color: '#fff',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              boxShadow: hoveredBtn === 'demo'
                ? '0 0 30px rgba(59,130,246,0.6), 0 0 60px rgba(139,92,246,0.3)'
                : '0 4px 20px rgba(59,130,246,0.25)',
              transform: hoveredBtn === 'demo' ? 'translateY(-2px)' : 'none',
              transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
            }}>Live Demo</button>
        </div>
      </nav>

      {/* ═══ HERO SECTION WITH 3D SPHERE ═══ */}
      <section style={{
        display: 'flex', flexDirection: isMobile ? 'column' : 'row',
        alignItems: 'center', justifyContent: 'center',
        padding: isMobile ? '80px 20px 40px' : '160px 48px 60px',
        maxWidth: 1200, margin: '0 auto',
        position: 'relative', zIndex: 1, gap: isMobile ? 30 : 60,
        minHeight: isMobile ? 'auto' : '100vh',
      }}>
        {/* Left — Text content */}
        <div style={{ flex: 1, maxWidth: isMobile ? '100%' : 580 }}>
          {/* Live status badge */}
          <div className={mounted ? 'slide-up' : ''} style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            padding: '8px 20px', borderRadius: 50, marginBottom: 32,
            background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)',
          }}>
            <span style={{ position: 'relative', display: 'flex', width: 8, height: 8 }}>
              <span style={{
                position: 'absolute', inset: 0, borderRadius: '50%', background: '#22c55e',
                animation: 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite', opacity: 0.6,
              }} />
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }} />
            </span>
            <span style={{ fontSize: 12, color: '#4ade80', fontWeight: 600, letterSpacing: 0.5 }}>
              All Systems Operational
            </span>
          </div>

          <h1 className={mounted ? 'slide-up-d1' : ''} style={{
            fontSize: isMobile ? 38 : 72, fontWeight: 900, lineHeight: 1.0, marginBottom: 24, letterSpacing: isMobile ? '-1.5px' : '-3px',
          }}>
            <span style={{
              display: 'block',
              background: 'linear-gradient(135deg, #fff 0%, #e2e8f0 30%, #3b82f6 50%, #8b5cf6 65%, #ec4899 80%, #fff 100%)',
              backgroundSize: '300% auto',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              animation: 'text-gradient 8s linear infinite',
            }}>
              Self-Healing
            </span>
            <span style={{ color: '#e2e8f0' }}>Infrastructure</span>
          </h1>

          <p className={mounted ? 'slide-up-d2' : ''} style={{
            fontSize: isMobile ? 14 : 18, color: '#94a3b8', lineHeight: 1.8, marginBottom: isMobile ? 28 : 40,
          }}>
            8 autonomous AI agents that monitor, diagnose, and remediate
            your infrastructure in real-time.{' '}
            <span style={{ color: '#cbd5e1', fontWeight: 600 }}>Zero human intervention.</span>
          </p>

          <div className={mounted ? 'slide-up-d3' : ''} style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 16 }}>
            <button onClick={() => router.push('/login')}
              onMouseEnter={() => setHoveredBtn('hero-start')} onMouseLeave={() => setHoveredBtn(null)}
              style={{
                padding: '18px 40px', borderRadius: 16, border: 'none', cursor: 'pointer',
                fontSize: 16, fontWeight: 700, color: '#fff', position: 'relative', overflow: 'hidden',
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                boxShadow: hoveredBtn === 'hero-start'
                  ? '0 0 50px rgba(59,130,246,0.6), 0 0 100px rgba(139,92,246,0.3)'
                  : '0 8px 32px rgba(59,130,246,0.3)',
                transform: hoveredBtn === 'hero-start' ? 'translateY(-3px) scale(1.03)' : 'none',
                transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
              }}>
              {/* Shimmer */}
              <div style={{
                position: 'absolute', top: 0, left: '-100%', width: '200%', height: '100%',
                background: 'linear-gradient(90deg, transparent 40%, rgba(255,255,255,0.15) 50%, transparent 60%)',
                animation: 'shimmer 3s ease-in-out infinite',
              }} />
              <span style={{ position: 'relative' }}>
                Get Started <span style={{ marginLeft: 6, display: 'inline-block', transition: 'transform 0.3s', transform: hoveredBtn === 'hero-start' ? 'translateX(4px)' : 'none' }}>→</span>
              </span>
            </button>
            <button onClick={() => router.push('/dashboard')}
              onMouseEnter={() => setHoveredBtn('hero-dash')} onMouseLeave={() => setHoveredBtn(null)}
              style={{
                padding: '18px 40px', borderRadius: 16, cursor: 'pointer',
                fontSize: 16, fontWeight: 600, color: '#71717a',
                border: '1px solid rgba(255,255,255,0.06)',
                background: hoveredBtn === 'hero-dash' ? 'rgba(255,255,255,0.03)' : 'transparent',
                transform: hoveredBtn === 'hero-dash' ? 'translateY(-3px)' : 'none',
                transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
              }}>View Dashboard</button>
          </div>
        </div>

        {/* Right — 3D Holographic Sphere (hidden on mobile) */}
        {!isMobile && (
          <div className={mounted ? 'fade-in' : ''} style={{
            flex: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <HolographicSphere />
          </div>
        )}
      </section>

      {/* ═══ ANIMATED PIPELINE ═══ */}
      <section style={{
        padding: '0 24px 100px', maxWidth: 1200, margin: '0 auto',
        position: 'relative', zIndex: 1,
      }}>
        <div className={mounted ? 'slide-up-d4' : ''} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexWrap: 'wrap', gap: isMobile ? 8 : 4,
          padding: isMobile ? '20px 16px' : '20px 24px', borderRadius: 24,
          background: 'rgba(255,255,255,0.015)',
          border: '1px solid rgba(255,255,255,0.03)',
          backdropFilter: 'blur(10px)',
          position: 'relative', overflow: 'hidden',
        }}>
          {/* Scanning beam */}
          <div style={{
            position: 'absolute', top: 0, left: 0, width: '20%', height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.04), transparent)',
            animation: 'scan-line 5s linear infinite',
          }} />

          {pipeline.map((p, i) => (
            <div key={p.step} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: isMobile ? '10px 14px' : '10px 16px', borderRadius: 12,
                background: `${p.color}08`,
                border: `1px solid ${p.color}15`,
                animation: `pulse-subtle 4s ease-in-out ${i * 0.5}s infinite`,
                transition: 'all 0.3s',
                position: 'relative', overflow: 'hidden',
                whiteSpace: 'nowrap' as const,
              }}>
                {/* Inner glow */}
                <div style={{
                  position: 'absolute', top: '50%', left: '50%',
                  transform: 'translate(-50%, -50%)', width: 40, height: 40,
                  background: `radial-gradient(circle, ${p.color}10, transparent)`,
                  animation: 'breathe 3s ease-in-out infinite',
                  animationDelay: `${i * 0.3}s`,
                }} />
                <span style={{ fontSize: isMobile ? 16 : 18, position: 'relative' }}>{p.icon}</span>
                <span style={{ fontSize: isMobile ? 11 : 12, fontWeight: 700, color: p.color, position: 'relative' }}>{p.step}</span>
              </div>
              {i < pipeline.length - 1 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 2, padding: '0 1px' }}>
                  {[0, 1, 2].map(d => (
                    <div key={d} style={{
                      width: 3, height: 3, borderRadius: '50%', background: p.color,
                      animation: `flow-dot 1.5s ease-in-out ${i * 0.2 + d * 0.15}s infinite`,
                      boxShadow: `0 0 4px ${p.color}60`,
                    }} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ═══ STATS ═══ */}
      <section style={{
        display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: isMobile ? 12 : 16,
        padding: isMobile ? '0 16px 60px' : '0 24px 100px', maxWidth: 1100, margin: '0 auto',
        position: 'relative', zIndex: 1,
      }}>
        {[
          { value: '8', label: 'AI Agents', icon: '🤖', color: '#3b82f6', suffix: '' },
          { value: '30', label: 'Detection Time', icon: '⚡', color: '#f59e0b', suffix: 's', prefix: '<' },
          { value: '95', label: 'Auto-Resolution', icon: '✅', color: '#10b981', suffix: '%+' },
          { value: '24', label: 'Autonomous', icon: '🌐', color: '#8b5cf6', suffix: '/7' },
        ].map((stat, i) => (
          <div key={i} style={{
            textAlign: 'center', padding: isMobile ? '24px 16px' : '36px 24px', borderRadius: isMobile ? 18 : 24,
            background: 'rgba(255,255,255,0.015)',
            border: '1px solid rgba(255,255,255,0.04)',
            animation: `scale-in 0.6s ease-out ${0.5 + i * 0.1}s both`,
            position: 'relative', overflow: 'hidden',
          }}>
            {/* Top glow accent */}
            <div style={{
              position: 'absolute', top: -30, left: '50%', transform: 'translateX(-50%)',
              width: 100, height: 60,
              background: `radial-gradient(circle, ${stat.color}12, transparent)`,
              filter: 'blur(15px)', animation: 'breathe 4s ease-in-out infinite',
              animationDelay: `${i * 0.5}s`,
            }} />
            <div style={{ fontSize: 28, marginBottom: 14, position: 'relative' }}>{stat.icon}</div>
            <div style={{
              fontSize: isMobile ? 32 : 52, fontWeight: 900, letterSpacing: isMobile ? '-1px' : '-3px', position: 'relative',
              color: stat.color,
              textShadow: `0 0 40px ${stat.color}30`,
            }}>
              <AnimCounter value={stat.value} suffix={stat.suffix} prefix={stat.prefix || ''} />
            </div>
            <div style={{
              fontSize: 11, color: '#71717a', marginTop: 8, fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: 2, position: 'relative',
            }}>{stat.label}</div>
          </div>
        ))}
      </section>

      {/* ═══ FEATURES — 3D TILT CARDS ═══ */}
      <section style={{
        padding: '0 24px 100px', maxWidth: 1100, margin: '0 auto',
        position: 'relative', zIndex: 1,
      }}>
        <div className="slide-up" style={{ textAlign: 'center', marginBottom: 64 }}>
          <p style={{
            fontSize: 12, fontWeight: 800, letterSpacing: 4, textTransform: 'uppercase',
            marginBottom: 16,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>CAPABILITIES</p>
          <h2 style={{ fontSize: isMobile ? 30 : 52, fontWeight: 900, letterSpacing: isMobile ? '-1px' : '-2px', marginBottom: 16 }}>
            Eight Agents.{' '}
            <span style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899)',
              backgroundSize: '300% auto',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              animation: 'text-gradient 6s linear infinite',
            }}>One Brain.</span>
          </h2>
          <p style={{ fontSize: 16, color: '#94a3b8', maxWidth: 500, margin: '0 auto', lineHeight: 1.7 }}>
            A unified intelligence layer that orchestrates specialized agents into a self-healing system
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, 1fr)', gap: isMobile ? 16 : 20 }}>
          {features.map((f, i) => (
            <TiltCard key={i} gradient={f.gradient} delay={0.15 + i * 0.08} index={i}>
              <div style={{
                width: 60, height: 60, borderRadius: 18, marginBottom: 22,
                background: f.gradient, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, position: 'relative',
                boxShadow: `0 10px 40px ${f.gradient.includes('#3b82f6') ? 'rgba(59,130,246,0.25)' : f.gradient.includes('#8b5cf6') ? 'rgba(139,92,246,0.25)' : f.gradient.includes('#10b981') ? 'rgba(16,185,129,0.25)' : 'rgba(236,72,153,0.25)'}`,
              }}>
                {f.icon}
                {/* Icon pulse ring */}
                <div style={{
                  position: 'absolute', inset: -4, borderRadius: 22,
                  border: `1px solid ${f.gradient.includes('#3b82f6') ? 'rgba(59,130,246,0.2)' : 'rgba(139,92,246,0.2)'}`,
                  animation: 'ripple 4s ease-out infinite',
                  animationDelay: `${i * 0.3}s`,
                }} />
              </div>
              <h3 style={{ fontSize: 20, fontWeight: 800, marginBottom: 12, color: '#e2e8f0', letterSpacing: '-0.3px' }}>{f.title}</h3>
              <p style={{ fontSize: 14, color: '#94a3b8', lineHeight: 1.8 }}>{f.desc}</p>
            </TiltCard>
          ))}
        </div>
      </section>

      {/* ═══ LIVE CODE TERMINAL ═══ */}
      <section style={{
        padding: '0 24px 100px', maxWidth: 900, margin: '0 auto',
        position: 'relative', zIndex: 1,
      }}>
        <div className="slide-up" style={{
          borderRadius: 24, overflow: 'hidden', position: 'relative',
          background: 'rgba(255,255,255,0.015)',
          border: '1px solid rgba(255,255,255,0.04)',
          boxShadow: '0 30px 100px rgba(0,0,0,0.5), 0 0 60px rgba(59,130,246,0.04)',
        }}>
          {/* Scan effect */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: 'linear-gradient(180deg, transparent 0%, rgba(59,130,246,0.015) 50%, transparent 100%)',
            backgroundSize: '100% 200%',
            animation: 'scan-vertical 6s linear infinite',
          }} />

          {/* Terminal bar */}
          <div style={{
            padding: '14px 22px', display: 'flex', alignItems: 'center', gap: 8,
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            background: 'rgba(255,255,255,0.015)',
          }}>
            {['#ef4444', '#f59e0b', '#10b981'].map(c => (
              <div key={c} style={{ width: 12, height: 12, borderRadius: '50%', background: c, boxShadow: `0 0 8px ${c}50` }} />
            ))}
            <span style={{ marginLeft: 16, fontSize: 12, color: '#71717a', fontFamily: 'monospace' }}>orchestrator.py</span>
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{
                width: 6, height: 6, borderRadius: '50%', background: '#22c55e',
                animation: 'breathe 2s ease-in-out infinite',
                boxShadow: '0 0 8px rgba(34,197,94,0.5)',
              }} />
              <span style={{ fontSize: 10, color: '#22c55e', fontWeight: 700, letterSpacing: 1 }}>LIVE</span>
            </div>
          </div>
          {/* Code */}
          <div style={{
            padding: isMobile ? '16px 12px' : '28px 32px', fontFamily: '"Geist Mono", "Fira Code", monospace',
            fontSize: isMobile ? 11 : 13.5, lineHeight: 2.2, color: '#a1a1aa',
            overflowX: 'auto',
          }}>
            <div style={{ animation: 'slide-in-left 0.6s ease-out 0.2s both' }}>
              <span style={{ color: '#c084fc' }}>class</span>{' '}
              <span style={{ color: '#60a5fa', textShadow: '0 0 12px rgba(96,165,250,0.3)' }}>Orchestrator</span>
              <span style={{ color: '#71717a' }}>:</span>
            </div>
            <div style={{ paddingLeft: 24, animation: 'slide-in-left 0.6s ease-out 0.35s both' }}>
              <span style={{ color: '#c084fc' }}>async def</span>{' '}
              <span style={{ color: '#34d399', textShadow: '0 0 12px rgba(52,211,153,0.3)' }}>process_incident</span>
              <span style={{ color: '#71717a' }}>(self, incident):</span>
            </div>
            {[
              { comment: '# Stage 1: Detect anomaly', code: ['anomalies', ' = ', 'await', ' self.', 'monitor.detect', '(metrics)'] },
              { comment: '# Stage 2: Root cause analysis', code: ['diagnosis', ' = ', 'await', ' self.', 'diagnostic.analyze', '(anomalies)'] },
              { comment: '# Stage 3: Auto-remediate', code: ['result', ' = ', 'await', ' self.', 'remediation.execute', '(diagnosis)'] },
              { comment: '# Stage 4: Learn & improve', code: ['', '', 'await', ' self.', 'learning.store_pattern', '(incident, result)'] },
            ].map((line, i) => (
              <div key={i} style={{ paddingLeft: 48, animation: `slide-in-left 0.6s ease-out ${0.5 + i * 0.15}s both` }}>
                <div style={{ color: '#8b8b96' }}>{line.comment}</div>
                <div>
                  {line.code[0] && <span style={{ color: '#8b8b96' }}>{line.code[0]}</span>}
                  <span>{line.code[1]}</span>
                  <span style={{ color: '#c084fc' }}>{line.code[2]}</span>
                  <span style={{ color: '#8b8b96' }}>{line.code[3]}</span>
                  <span style={{ color: '#34d399' }}>{line.code[4]}</span>
                  <span style={{ color: '#8b8b96' }}>{line.code[5]}</span>
                </div>
              </div>
            ))}
            <div style={{ paddingLeft: 48, marginTop: 10 }}>
              <span style={{
                display: 'inline-block', width: 9, height: 20,
                background: '#3b82f6', borderRadius: 1,
                animation: 'blink 1.2s step-end infinite',
                boxShadow: '0 0 10px rgba(59,130,246,0.6)',
              }} />
            </div>
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="slide-up" style={{
        padding: '0 24px 120px', maxWidth: 800, margin: '0 auto',
        textAlign: 'center', position: 'relative', zIndex: 1,
      }}>
        <div style={{
          padding: isMobile ? '40px 24px' : '80px 60px', borderRadius: isMobile ? 20 : 32,
          position: 'relative', overflow: 'hidden',
          background: 'rgba(255,255,255,0.015)',
          border: '1px solid rgba(255,255,255,0.04)',
        }}>
          {/* Rotating conic gradient border */}
          <div style={{
            position: 'absolute', inset: -1, borderRadius: 32, padding: 1,
            background: 'conic-gradient(from var(--angle, 0deg), transparent 60%, #3b82f650, #8b5cf650, #ec489930, transparent 100%)',
            mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            maskComposite: 'exclude', WebkitMaskComposite: 'xor',
            animation: 'border-rotate 8s linear infinite', pointerEvents: 'none',
          }} />
          {/* Inner breathing glow */}
          <div style={{
            position: 'absolute', top: '-40%', left: '50%', transform: 'translateX(-50%)',
            width: 500, height: 500,
            background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 50%)',
            animation: 'breathe 5s ease-in-out infinite', pointerEvents: 'none',
          }} />

          <h2 style={{
            fontSize: isMobile ? 28 : 48, fontWeight: 900, marginBottom: 20, position: 'relative',
            letterSpacing: isMobile ? '-0.5px' : '-1.5px', lineHeight: 1.1,
          }}>
            Ready To Join A<br />
            <span style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899, #3b82f6)',
              backgroundSize: '300% auto',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              animation: 'text-gradient 5s linear infinite',
            }}>New Dimension?</span>
          </h2>
          <p style={{
            color: '#94a3b8', fontSize: 15, marginBottom: 40, position: 'relative',
            lineHeight: 1.8, maxWidth: 450, margin: '0 auto 40px',
          }}>
            Deploy autonomous AI agents that never sleep, never miss an alert,
            and get smarter with every incident.
          </p>
          <button onClick={() => router.push('/login')}
            onMouseEnter={() => setHoveredBtn('cta')} onMouseLeave={() => setHoveredBtn(null)}
            style={{
              padding: '20px 52px', borderRadius: 18, border: 'none', cursor: 'pointer',
              fontSize: 17, fontWeight: 800, color: '#fff', position: 'relative', overflow: 'hidden',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              boxShadow: hoveredBtn === 'cta'
                ? '0 0 60px rgba(59,130,246,0.6), 0 0 120px rgba(139,92,246,0.3)'
                : '0 8px 40px rgba(59,130,246,0.3)',
              transform: hoveredBtn === 'cta' ? 'scale(1.06) translateY(-3px)' : 'none',
              transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
            }}>
            <div style={{
              position: 'absolute', top: 0, left: '-100%', width: '200%', height: '100%',
              background: 'linear-gradient(90deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%)',
              animation: 'shimmer 3s ease-in-out infinite',
            }} />
            <span style={{ position: 'relative' }}>Get Started Now</span>
          </button>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer style={{
        textAlign: 'center', padding: '28px', position: 'relative', zIndex: 1,
        borderTop: '1px solid rgba(255,255,255,0.03)',
        color: '#52525b', fontSize: 13,
      }}>
        Built by Utkarsh &middot; MIT License &middot; 2026
      </footer>
    </div>
  );
}
