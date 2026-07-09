import React from 'react';
import { usePatterns } from '../hooks/useApi';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

function fmt(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

const COLORS = ['#ff0000', '#cc0000', '#990000', '#666', '#444', '#333'];

export default function Overview() {
  const { data, loading, error } = usePatterns();

  if (loading) return (
    <div className="loading">
      <div className="spinner" />
      Loading channel data...
    </div>
  );

  if (error) return <div style={{ color: '#ff6666' }}>Error: {error}</div>;

  const traffic = data?.traffic?.sources || {};
  const trafficData = Object.entries(traffic)
    .map(([name, vals]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: vals.total_views,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);

  const vl = data?.video_length || {};
  const tp = data?.title_patterns || {};
  const we = data?.weak_engagement || {};

  return (
    <div>
      <div className="page-title">📊 Channel Overview</div>
      <div className="page-subtitle">Real data from your YouTube channel</div>

      {/* KPIs */}
      <div className="kpi-grid">
        {[
          { label: 'Total Shorts', value: fmt(vl.total_shorts) },
          { label: 'Total Long-form', value: fmt(vl.total_longform) },
          { label: 'Better Format', value: vl.better_format || '—' },
          { label: 'Avg Retention', value: `${we.channel_avg_retention || 0}%` },
          { label: 'Weak Videos', value: fmt(we.total_weak_count) },
        ].map((kpi, i) => (
          <div className="kpi-card" key={i}>
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Traffic Sources */}
        <div className="card">
          <div className="section-title">🚦 Traffic Sources</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={trafficData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {trafficData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                labelStyle={{ color: '#fff' }}
                formatter={(val) => fmt(val)}
              />
              <Legend
                wrapperStyle={{ color: '#aaa', fontSize: '0.8rem' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 12 }}>
            <div className="ai-card-title">Top Source</div>
            <div className="ai-card-content">
              <span style={{ color: '#ff0000', fontWeight: 700 }}>
                {data?.traffic?.top_source?.replace(/_/g, ' ')}
              </span>
              {' '}— {data?.traffic?.top_source_percentage?.toFixed(1)}% of views
            </div>
          </div>
        </div>

        {/* Format Performance */}
        <div className="card">
          <div className="section-title">⚡ Format Performance</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={[
              { name: 'Shorts', views: vl.avg_views_shorts || 0 },
              { name: 'Long-form', views: vl.avg_views_longform || 0 },
            ]}>
              <XAxis dataKey="name" stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} />
              <YAxis stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} tickFormatter={fmt} />
              <Tooltip
                contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                formatter={(val) => [fmt(val), 'Avg Views']}
              />
              <Bar dataKey="views" radius={[6, 6, 0, 0]}>
                <Cell fill="#ff0000" />
                <Cell fill="#4488ff" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
            <div className="ai-card" style={{ flex: 1 }}>
              <div className="ai-card-title">Better Format</div>
              <div className="ai-card-content" style={{ color: '#ff0000', fontWeight: 700, fontSize: '1.2rem' }}>
                {vl.better_format}
              </div>
            </div>
            <div className="ai-card" style={{ flex: 1 }}>
              <div className="ai-card-title">Performance Multiplier</div>
              <div className="ai-card-content" style={{ color: '#fff', fontWeight: 700, fontSize: '1.2rem' }}>
                {vl.multiplier}x better
              </div>
            </div>
          </div>

          {/* Title patterns */}
          <div style={{ marginTop: 16 }}>
            <div className="section-title">📝 Title Patterns</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              <span className="tag" style={{ background: tp.emoji_helps ? 'rgba(255,0,0,0.15)' : '#272727', color: tp.emoji_helps ? '#ff6666' : '#aaa' }}>
                {tp.emoji_helps ? '✅' : '❌'} Emoji helps
              </span>
              <span className="tag" style={{ background: tp.exclamation_helps ? 'rgba(255,0,0,0.15)' : '#272727', color: tp.exclamation_helps ? '#ff6666' : '#aaa' }}>
                {tp.exclamation_helps ? '✅' : '❌'} ! helps
              </span>
              <span className="tag">
                Best length: {tp.best_title_length_bucket}
              </span>
              <span className="tag">
                Avg: {tp.avg_title_length} chars
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Weak Videos */}
      <div className="card">
        <div className="section-title">⚠️ Videos with Weak Engagement</div>
        <div style={{ color: '#aaa', fontSize: '0.8rem', marginBottom: 16 }}>
          Channel avg retention: <span style={{ color: '#ff0000', fontWeight: 600 }}>{we.channel_avg_retention}%</span>
          {' '}· {we.total_weak_count} videos below average
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Retention</th>
              <th>Views</th>
              <th>Below Avg By</th>
            </tr>
          </thead>
          <tbody>
            {(we.weak_videos || []).map((v, i) => (
              <tr key={i}>
                <td>{v.title}</td>
                <td style={{ color: '#ff6666' }}>{v.avg_retention}%</td>
                <td>{fmt(v.total_views)}</td>
                <td style={{ color: '#ffaa00' }}>-{v.below_avg_by}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
