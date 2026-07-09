import React from 'react';
import { useBestTimes } from '../hooks/useApi';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

function fmt(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

const DAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

export default function BestTimes() {
  const { data, loading, error } = useBestTimes();

  if (loading) return <div className="loading"><div className="spinner" />Loading timing data...</div>;
  if (error) return <div style={{ color: '#ff6666' }}>Error: {error}</div>;

  const hourData = Object.entries(data?.hour_data || {})
    .map(([hour, views]) => ({ hour: `${hour}:00`, views, isMax: parseInt(hour) === data?.best_hour }))
    .sort((a, b) => parseInt(a.hour) - parseInt(b.hour));

  const dayData = DAY_ORDER.map(day => ({
    day: day.slice(0, 3),
    views: data?.day_data?.[day] || 0,
    isMax: day === data?.best_day,
  }));

  return (
    <div>
      <div className="page-title">⏰ Best Time to Post</div>
      <div className="page-subtitle">Based on real performance data from your channel</div>

      {/* Summary cards */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="ai-card">
          <div className="ai-card-title">Best Day</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ff0000', margin: '8px 0' }}>
            {data?.best_day}
          </div>
          <div className="ai-card-content">
            {fmt(data?.best_day_avg_views)} avg views per video
          </div>
        </div>
        <div className="ai-card">
          <div className="ai-card-title">Best Hour (UTC)</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ff0000', margin: '8px 0' }}>
            {data?.best_hour}:00
          </div>
          <div className="ai-card-content">
            {fmt(data?.best_hour_avg_views)} avg views per video
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Day chart */}
        <div className="card">
          <div className="section-title">📅 Avg Views by Day</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dayData}>
              <XAxis dataKey="day" stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} />
              <YAxis stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} tickFormatter={fmt} />
              <Tooltip
                contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                formatter={(val) => [fmt(val), 'Avg Views']}
              />
              <Bar dataKey="views" radius={[4, 4, 0, 0]}>
                {dayData.map((d, i) => (
                  <Cell key={i} fill={d.isMax ? '#ff0000' : '#333'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hour chart */}
        <div className="card">
          <div className="section-title">🕐 Avg Views by Hour (UTC)</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hourData}>
              <XAxis dataKey="hour" stroke="#555" tick={{ fill: '#aaa', fontSize: 10 }} interval={2} />
              <YAxis stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} tickFormatter={fmt} />
              <Tooltip
                contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                formatter={(val) => [fmt(val), 'Avg Views']}
              />
              <Bar dataKey="views" radius={[4, 4, 0, 0]}>
                {hourData.map((h, i) => (
                  <Cell key={i} fill={h.isMax ? '#ff0000' : '#333'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top 3 hours */}
      <div className="card">
        <div className="section-title">🏆 Top 3 Upload Hours</div>
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          {(data?.top_3_hours || []).map((hour, i) => (
            <div key={i} className="ai-card" style={{ flex: 1, textAlign: 'center' }}>
              <div className="ai-card-title">#{i + 1}</div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: i === 0 ? '#ff0000' : '#fff' }}>
                {hour}:00
              </div>
              <div style={{ color: '#aaa', fontSize: '0.8rem' }}>UTC</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
