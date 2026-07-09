import React from 'react';
import './Sidebar.css';

const NAV_ITEMS = [
  { id: 'overview', icon: '📊', label: 'Overview' },
  { id: 'bestTimes', icon: '⏰', label: 'Best Times' },
  { id: 'mlPredictor', icon: '🤖', label: 'ML Predictor' },
  { id: 'aiInsights', icon: '💡', label: 'AI Insights' },
  { id: 'channelAudit', icon: '📈', label: 'Channel Audit' },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <span className="logo-icon">▶</span>
        <div>
          <div className="logo-title">Growth <span>Copilot</span></div>
          <div className="logo-sub">Powered by Gemma 4</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="footer-badge">AMD Hackathon 2026</div>
        <div className="footer-sub">Track 3 · Unicorn</div>
      </div>
    </aside>
  );
}
