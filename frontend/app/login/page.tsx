'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';

// Mini particle system for login background
function LoginParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let animId: number;

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);

    const particles = Array.from({ length: 40 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      size: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.3 + 0.1,
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p, i) => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width; if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height; if (p.y > canvas.height) p.y = 0;
        p.opacity = 0.1 + Math.sin(Date.now() * 0.001 + i * 0.5) * 0.15;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(59,130,246,${p.opacity})`;
        ctx.fill();
      });
      animId = requestAnimationFrame(animate);
    };
    animate();
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize); };
  }, []);
  return <canvas ref={canvasRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />;
}

export default function LoginPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', full_name: '', company: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (isLogin) {
        const response = await authAPI.login({ email: formData.email, password: formData.password });
        localStorage.setItem('token', response.data.access_token);
        router.push('/dashboard');
      } else {
        await authAPI.signup({
          email: formData.email, password: formData.password,
          full_name: formData.full_name, company: formData.company,
        });
        const loginResponse = await authAPI.login({ email: formData.email, password: formData.password });
        localStorage.setItem('token', loginResponse.data.access_token);
        router.push('/dashboard');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'An error occurred');
    } finally { setLoading(false); }
  };

  const inputStyle = (name: string): React.CSSProperties => ({
    width: '100%', padding: '14px 16px', borderRadius: 14, fontSize: 14,
    outline: 'none', boxSizing: 'border-box' as const,
    color: '#f0f0f0', fontWeight: 400,
    background: focused === name ? 'rgba(59,130,246,0.05)' : 'rgba(255,255,255,0.03)',
    border: `1.5px solid ${focused === name ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.06)'}`,
    boxShadow: focused === name
      ? '0 0 0 4px rgba(59,130,246,0.08), 0 0 30px rgba(59,130,246,0.08), inset 0 0 20px rgba(59,130,246,0.03)'
      : 'none',
    transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
  });

  return (
    <div style={{
      minHeight: '100vh', background: '#04040c',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24, position: 'relative', overflow: 'hidden',
    }}>
      <LoginParticles />

      {/* Aurora blobs */}
      <div style={{
        position: 'fixed', top: '-30%', right: '-20%', width: 700, height: 700,
        background: 'radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 60%)',
        filter: 'blur(60px)', pointerEvents: 'none',
        animation: 'breathe 8s ease-in-out infinite',
      }} />
      <div style={{
        position: 'fixed', bottom: '-30%', left: '-20%', width: 700, height: 700,
        background: 'radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 60%)',
        filter: 'blur(80px)', pointerEvents: 'none',
        animation: 'breathe 10s ease-in-out 2s infinite',
      }} />
      {/* Center focus glow */}
      <div style={{
        position: 'fixed', top: '35%', left: '50%',
        width: 500, height: 500, transform: 'translate(-50%, -50%)',
        background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 50%)',
        animation: 'breathe 5s ease-in-out infinite', pointerEvents: 'none',
      }} />
      {/* Dot grid */}
      <div className="dot-grid" style={{ position: 'fixed', inset: 0, pointerEvents: 'none', opacity: 0.25 }} />

      <div className={mounted ? 'scale-in' : ''} style={{
        width: '100%', maxWidth: 460, position: 'relative', zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            width: 64, height: 64, borderRadius: 20,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 32, marginBottom: 24, position: 'relative',
            boxShadow: '0 0 40px rgba(59,130,246,0.3), 0 0 80px rgba(139,92,246,0.15)',
            animation: 'glow-pulse 3s ease-in-out infinite',
          }}>
            ⚡
            <div style={{
              position: 'absolute', inset: -6, borderRadius: 24,
              border: '1px solid rgba(59,130,246,0.2)',
              animation: 'ripple 3s ease-out infinite',
            }} />
            <div style={{
              position: 'absolute', inset: -12, borderRadius: 28,
              border: '1px solid rgba(59,130,246,0.1)',
              animation: 'ripple 3s ease-out 1s infinite',
            }} />
          </div>
          <h1 style={{
            fontSize: 36, fontWeight: 900, marginBottom: 10, letterSpacing: '-1px',
            background: 'linear-gradient(135deg, #ffffff, #94a3b8)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            {isLogin ? 'Welcome back' : 'Get started'}
          </h1>
          <p style={{ fontSize: 15, color: '#3f3f46' }}>
            {isLogin ? 'Sign in to your SentryAI dashboard' : 'Create your account to begin'}
          </p>
        </div>

        {/* Glass Card with animated border */}
        <div style={{
          padding: 40, borderRadius: 24, position: 'relative', overflow: 'hidden',
          background: 'rgba(255,255,255,0.02)',
          backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
          boxShadow: '0 25px 80px rgba(0,0,0,0.5), 0 0 40px rgba(59,130,246,0.03)',
          border: '1px solid rgba(255,255,255,0.05)',
        }}>
          {/* Rotating gradient border */}
          <div style={{
            position: 'absolute', inset: -1, borderRadius: 24, padding: 1,
            background: 'conic-gradient(from var(--angle, 0deg), transparent 70%, #3b82f640, #8b5cf640, transparent 100%)',
            mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            maskComposite: 'exclude', WebkitMaskComposite: 'xor',
            animation: 'border-rotate 8s linear infinite',
            pointerEvents: 'none',
          }} />
          {/* Top shine */}
          <div style={{
            position: 'absolute', top: 0, left: '10%', right: '10%', height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.3), rgba(139,92,246,0.3), transparent)',
          }} />

          {error && (
            <div style={{
              padding: '14px 18px', borderRadius: 14, marginBottom: 22,
              background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)',
              color: '#f87171', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ fontSize: 16 }}>⚠</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {[
              { name: 'email', label: 'Email', type: 'email', placeholder: 'you@company.com', icon: '✉', show: true },
              { name: 'password', label: 'Password', type: 'password', placeholder: 'Enter your password', icon: '🔒', show: true },
              { name: 'full_name', label: 'Full Name', type: 'text', placeholder: 'Your name', icon: '👤', show: !isLogin },
              { name: 'company', label: 'Company', type: 'text', placeholder: 'Acme Inc.', icon: '🏢', show: !isLogin },
            ].filter(f => f.show).map((field, i) => (
              <div key={field.name} style={{
                marginBottom: 20,
                animation: mounted ? `slide-up 0.5s ease-out ${0.05 * i}s both` : 'none',
              }}>
                <label style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  fontSize: 12, fontWeight: 600, marginBottom: 10,
                  color: focused === field.name ? '#60a5fa' : '#52525b',
                  textTransform: 'uppercase', letterSpacing: 1.2,
                  transition: 'color 0.3s',
                }}>
                  <span style={{ fontSize: 12 }}>{field.icon}</span>
                  {field.label}
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={field.name === 'password' ? (showPassword ? 'text' : 'password') : field.type}
                    required={field.name === 'email' || field.name === 'password'}
                    value={formData[field.name as keyof typeof formData]}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    onFocus={() => setFocused(field.name)}
                    onBlur={() => setFocused('')}
                    placeholder={field.placeholder}
                    style={{
                      ...inputStyle(field.name),
                      paddingRight: field.name === 'password' ? 48 : 16,
                    }}
                  />
                  {field.name === 'password' && (
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{
                        position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)',
                        background: 'none', border: 'none', cursor: 'pointer', padding: 4,
                        color: showPassword ? '#60a5fa' : '#52525b',
                        transition: 'color 0.3s',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}
                    >
                      {showPassword ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                          <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                          <line x1="1" y1="1" x2="23" y2="23" />
                          <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>
              </div>
            ))}

            <button type="submit" disabled={loading}
              style={{
                width: '100%', padding: '16px', borderRadius: 14, border: 'none',
                fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
                marginTop: 8, color: '#fff',
                background: loading ? 'rgba(255,255,255,0.04)' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                boxShadow: loading ? 'none' : '0 8px 32px rgba(59,130,246,0.3), 0 0 40px rgba(139,92,246,0.1)',
                transition: 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
                transform: !loading ? 'translateY(0)' : 'none',
                position: 'relative', overflow: 'hidden',
              }}>
              {/* Button shine */}
              {!loading && <div style={{
                position: 'absolute', top: 0, left: '-100%', width: '200%', height: '100%',
                background: 'linear-gradient(90deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%)',
                animation: 'shimmer 3s ease-in-out infinite',
              }} />}
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                  <span style={{
                    width: 18, height: 18,
                    border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff',
                    borderRadius: '50%', display: 'inline-block',
                    animation: 'spin-slow 0.6s linear infinite',
                  }} />
                  Authenticating...
                </span>
              ) : (
                <span style={{ position: 'relative' }}>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <span style={{ marginLeft: 8, display: 'inline-block' }}>→</span>
                </span>
              )}
            </button>
          </form>

          <div style={{
            textAlign: 'center', marginTop: 28, paddingTop: 28,
            borderTop: '1px solid rgba(255,255,255,0.04)',
          }}>
            <button onClick={() => { setIsLogin(!isLogin); setError(''); }}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', fontSize: 14,
                fontWeight: 500, transition: 'all 0.3s',
                color: '#3b82f6',
              }}>
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <span style={{ fontWeight: 700, textDecoration: 'underline', textUnderlineOffset: 3 }}>
                {isLogin ? 'Sign up' : 'Sign in'}
              </span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
