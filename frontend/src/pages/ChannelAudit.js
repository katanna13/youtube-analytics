import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE } from '../hooks/useApi';

export default function ChannelAudit() {
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [weakAnalysis, setWeakAnalysis] = useState(null);
  const [loadingWeak, setLoadingWeak] = useState(false);
  const [weakVideos, setWeakVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const [auditRes, patternsRes] = await Promise.all([
        axios.get(`${API_BASE}/channel-audit`),
        axios.get(`${API_BASE}/patterns`),
      ]);
      setAudit(auditRes.data.audit);
      setWeakVideos(patternsRes.data.data?.weak_engagement?.weak_videos || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const analyzeVideo = async () => {
    if (!selectedVideo) return;
    setLoadingWeak(true);
    try {
      const video = weakVideos[selectedVideo];
      const res = await axios.post(`${API_BASE}/video/${video.video_id}/insights`, {
        video_id: video.video_id,
        title: video.title,
        retention: video.avg_retention,
        views: video.total_views,
      });
      setWeakAnalysis(res.data.analysis);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingWeak(false);
    }
  };

  return (
    <div>
      <div className="page-title">📈 Channel Audit</div>
      <div className="page-subtitle">Complete channel health check powered by Llama</div>

      {/* Full Audit */}
      <div className="card">
        <div className="section-title">🔍 Full Channel Audit</div>
        <button className="btn-primary" onClick={fetchAudit} disabled={loading} style={{ marginBottom: 20 }}>
          {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} />Running audit...</> : '🤖 Run Full Channel Audit'}
        </button>

        {audit && !audit.error && (
          <div>
            <div style={{ display: 'flex', gap: 20, marginBottom: 24, alignItems: 'flex-start' }}>
              {/* Score */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#aaa', textTransform: 'uppercase', marginBottom: 8 }}>Channel Score</div>
                <div className="score-badge">{audit.channel_score}/10</div>
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: '0.75rem', color: '#aaa', marginBottom: 4 }}>Traffic Diversity</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>{audit.traffic_diversity_score}/10</div>
                </div>
              </div>

              {/* Content mix */}
              <div className="ai-card" style={{ flex: 1 }}>
                <div className="ai-card-title">Content Mix Advice</div>
                <div className="ai-card-content">{audit.content_mix_advice}</div>
              </div>
            </div>

            <div className="grid-3">
              {/* Strengths */}
              <div>
                <div style={{ color: '#00cc66', fontWeight: 600, fontSize: '0.85rem', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  💪 Strengths
                </div>
                {(audit.strengths || []).map((s, i) => (
                  <div className="action-item" key={i} style={{ borderLeftColor: '#00cc66' }}>
                    <span>✅</span> {s}
                  </div>
                ))}
              </div>

              {/* Growth Gaps */}
              <div>
                <div style={{ color: '#ffaa00', fontWeight: 600, fontSize: '0.85rem', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  ⚠️ Growth Gaps
                </div>
                {(audit.growth_gaps || []).map((g, i) => (
                  <div className="action-item" key={i} style={{ borderLeftColor: '#ffaa00' }}>
                    <span>⚠️</span> {g}
                  </div>
                ))}
              </div>

              {/* Top Actions */}
              <div>
                <div style={{ color: '#ff0000', fontWeight: 600, fontSize: '0.85rem', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  🚀 Top 3 Actions
                </div>
                {(audit.top_3_actions || []).map((a, i) => (
                  <div className="action-item" key={i}>
                    <span style={{ color: '#ff0000', fontWeight: 700, minWidth: 20 }}>{i + 1}.</span> {a}
                  </div>
                ))}
              </div>
            </div>

            {audit.from_cache && <div className="cache-badge" style={{ marginTop: 12 }}>⚡ From cache</div>}
          </div>
        )}
      </div>

      {/* Weak Video Analysis */}
      {weakVideos.length > 0 && (
        <div className="card">
          <div className="section-title">⚠️ Weak Video Analysis</div>
          <div style={{ color: '#aaa', fontSize: '0.85rem', marginBottom: 16 }}>
            Select a video to analyze why it underperformed
          </div>

          <div className="grid-2">
            <div>
              <select
                className="input"
                value={selectedVideo || ''}
                onChange={e => setSelectedVideo(e.target.value)}
                style={{ marginBottom: 12 }}
              >
                <option value="">Select a video...</option>
                {weakVideos.map((v, i) => (
                  <option key={i} value={i}>
                    {v.title.slice(0, 50)}... ({v.avg_retention}% retention)
                  </option>
                ))}
              </select>

              {selectedVideo !== null && weakVideos[selectedVideo] && (
                <div className="ai-card" style={{ marginBottom: 12 }}>
                  <div className="ai-card-title">Video Stats</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                    {[
                      { label: 'Retention', value: `${weakVideos[selectedVideo].avg_retention}%`, color: '#ff6666' },
                      { label: 'Total Views', value: weakVideos[selectedVideo].total_views?.toLocaleString() },
                      { label: 'Below Avg By', value: `-${weakVideos[selectedVideo].below_avg_by}%`, color: '#ffaa00' },
                    ].map((item, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#aaa', fontSize: '0.85rem' }}>{item.label}</span>
                        <span style={{ color: item.color || '#fff', fontWeight: 600, fontSize: '0.85rem' }}>{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                className="btn-primary"
                onClick={analyzeVideo}
                disabled={loadingWeak || selectedVideo === null}
              >
                {loadingWeak ? <><div className="spinner" style={{ width: 16, height: 16 }} />Analyzing...</> : '🤖 Analyze This Video'}
              </button>
            </div>

            <div>
              {weakAnalysis && !weakAnalysis.error && (
                <div>
                  <div className="ai-card">
                    <div className="ai-card-title">Retention Diagnosis</div>
                    <div className="ai-card-content">{weakAnalysis.retention_diagnosis}</div>
                  </div>

                  <div style={{ marginTop: 12, marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase' }}>Likely Reasons</div>
                  {(weakAnalysis.likely_reasons || []).map((r, i) => (
                    <div className="action-item" key={i} style={{ borderLeftColor: '#ffaa00' }}>
                      <span>⚠️</span> {r}
                    </div>
                  ))}

                  <div style={{ marginTop: 12, marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase' }}>Specific Fixes</div>
                  {(weakAnalysis.specific_fixes || []).map((f, i) => (
                    <div className="action-item" key={i} style={{ borderLeftColor: '#00cc66' }}>
                      <span>✅</span> {f}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
