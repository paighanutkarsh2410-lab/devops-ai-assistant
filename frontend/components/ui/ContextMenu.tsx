'use client';

import { useState, useEffect, useRef, ReactNode } from 'react';

interface MenuItem {
  label: string;
  icon?: string;
  shortcut?: string;
  danger?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  divider?: boolean;
}

interface ContextMenuProps {
  items: MenuItem[];
  children: ReactNode;
}

export default function ContextMenu({ items, children }: ContextMenuProps) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const menuRef = useRef<HTMLDivElement>(null);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setPos({ x: e.clientX, y: e.clientY });
    setOpen(true);
  };

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener('click', close);
    window.addEventListener('contextmenu', close);
    window.addEventListener('scroll', close);
    return () => {
      window.removeEventListener('click', close);
      window.removeEventListener('contextmenu', close);
      window.removeEventListener('scroll', close);
    };
  }, [open]);

  // Adjust position to stay in viewport
  useEffect(() => {
    if (!open || !menuRef.current) return;
    const rect = menuRef.current.getBoundingClientRect();
    const newPos = { ...pos };
    if (rect.right > window.innerWidth) newPos.x = window.innerWidth - rect.width - 8;
    if (rect.bottom > window.innerHeight) newPos.y = window.innerHeight - rect.height - 8;
    if (newPos.x !== pos.x || newPos.y !== pos.y) setPos(newPos);
  }, [open, pos]);

  return (
    <div onContextMenu={handleContextMenu} style={{ display: 'contents' }}>
      {children}
      {open && (
        <div
          ref={menuRef}
          style={{
            position: 'fixed',
            left: pos.x,
            top: pos.y,
            zIndex: 9500,
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 10,
            boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
            padding: '4px 0',
            minWidth: 180,
            animation: 'fadeIn 0.15s ease-out',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {items.map((item, i) =>
            item.divider ? (
              <div key={i} style={{ height: 1, background: '#334155', margin: '4px 8px' }} />
            ) : (
              <button
                key={i}
                onClick={() => { if (!item.disabled) { item.onClick?.(); setOpen(false); } }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  padding: '7px 12px',
                  border: 'none',
                  background: 'transparent',
                  cursor: item.disabled ? 'not-allowed' : 'pointer',
                  color: item.disabled ? '#475569' : item.danger ? '#ef4444' : '#e2e8f0',
                  fontSize: 13,
                  textAlign: 'left',
                  transition: 'background 0.1s',
                  opacity: item.disabled ? 0.5 : 1,
                }}
                onMouseEnter={(e) => { if (!item.disabled) e.currentTarget.style.background = '#334155'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                {item.icon && <span style={{ width: 18, textAlign: 'center' }}>{item.icon}</span>}
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.shortcut && (
                  <kbd style={{ fontSize: 10, color: '#64748b', fontFamily: 'monospace' }}>{item.shortcut}</kbd>
                )}
              </button>
            )
          )}
        </div>
      )}
      <style>{`@keyframes fadeIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }`}</style>
    </div>
  );
}
