import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE } from '../hooks/useApi';

export default function AIInsights() {
  const [topic, setTopic] = useState('');
  const [strategy, setStrategy] = useState(null);
  const [titles, setTitles] = useState(null);
  const [thumbnail, setThumbnail] = useState(null);
  const [nextIdeas, setNextIdeas] = useState(null);
  const [thumbFromTitle, setThumbFromTitle] = useState(null);
  const [customTitle, setCustomTitle] = useState('');

  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [loadingTitles, setLoadingTitles] = useState(false);
  const [loadingThumb, setLoadingThumb] = useState(false);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [loadingThumbTitle, setLoadingThumbTitle] = useState(false);

  const fetchStrategy = async () => {
    setLoadingStrategy(true);
    try {
      const res = await axios.get(`${API_BASE}/analyze-channel`);
      setStrategy(res.data.insights?.upload_strategy);
    } catch (e) { console.error(e); }
    finally { setLoadingStrategy(false); }
  };

  const fetchTitles = async () => {
    setLoadingTitles(true);
    try {
      const res = await axios.post(`${API_BASE}/generate-strategy`, { topic });
      setTitles(res.data.title_ideas);
    } catch (e) { console.error(e); }
    finally { setLoadingTitles(false); }
  };

  const fetchThumbnail = async () => {
    setLoadingThumb(true);
    try {
      const res = await axios.post(`${API_BASE}/generate-strategy`, { topic: '' });
      setThumbnail(res.data.thumbnail_recommendations);
    } catch (e) { console.error(e); }
    finally { setLoadingThumb(false); }
  };

  const fetchNextIdeas = async () => {
    setLoadingIdeas(true);
    try {
      const res = await axios.get(`${API_BASE}/next-video-ideas`);
      setNextIdeas(res.data);
    } catch (e) { console.error(e); }
    finally { setLoadingIdeas(false); }
  };

  const fetchThumbFromTitle = async () => {
    if (!customTitle.trim()) return;
    setLoadingThumbTitle(true);
    try {
      const res = await axios.post(`${API_BASE}/thumbnail-from-title`, { title: customTitle });
      setThumbFromTitle(res.data.thumbnail);
    } catch (e) { console.error(e); }
    finally { setLoadingThumbTitle(false); }
  };

  return (
    <div>
      <div className="page-title">💡 AI Insights</div>
      <div className="page-subtitle">Powered by Llama via Groq · Results cached for 24h</div>

      {/* ── Next Video Ideas ── */}
      <div className="card">
        <div className="section-title">🎬 Next Video Ideas</div>
        <div style={{ color: '#aaa', fontSize: '0.85rem', marginBottom: 16 }}>
          Based on your top performing videos — Llama analyzes your channel's niche and style
        </div>
        <button className="btn-primary" onClick={fetchNextIdeas} disabled={loadingIdeas} style={{ marginBottom: 16 }}>
          {loadingIdeas
            ? <><div className="spinner" style={{ width: 16, height: 16 }} />Analyzing channel...</>
            : '🤖 Generate Next Video Ideas'}
        </button>

        {nextIdeas && nextIdeas.ideas && !nextIdeas.ideas.error && (
          <div>
            <div className="grid-2" style={{ marginBottom: 16 }}>
              <div className="ai-card">
                <div className="ai-card-title">Channel Niche</div>
                <div className="ai-card-content" style={{ color: '#ff0000', fontWeight: 600 }}>
                  {nextIdeas.ideas.niche}
                </div>
              </div>
              <div className="ai-card">
                <div className="ai-card-title">Content Pattern</div>
                <div className="ai-card-content">{nextIdeas.ideas.content_pattern}</div>
              </div>
            </div>

            <div style={{ marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              5 Video Ideas
            </div>
            {(nextIdeas.ideas.video_ideas || []).map((idea, i) => (
              <div key={i} style={{
                background: '#1a1a1a',
                border: '1px solid #272727',
                borderRadius: 8,
                padding: 14,
                marginBottom: 10,
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <span style={{ color: '#ff0000', fontWeight: 700, fontSize: '1.1rem', minWidth: 24 }}>{i + 1}.</span>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 600, marginBottom: 4 }}>{idea.title}</div>
                    <div style={{ color: '#888', fontSize: '0.82rem' }}>{idea.why}</div>
                  </div>
                </div>
              </div>
            ))}
            {nextIdeas.ideas.from_cache && <div className="cache-badge">⚡ From cache</div>}
          </div>
        )}
      </div>

      {/* ── Thumbnail from Title ── */}
      <div className="card">
        <div className="section-title">🖼️ Thumbnail Generator from Title</div>
        <div style={{ color: '#aaa', fontSize: '0.85rem', marginBottom: 16 }}>
          Enter any title and get specific thumbnail recommendations based on your channel's style
        </div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <input
            className="input"
            placeholder="Enter your video title..."
            value={customTitle}
            onChange={e => setCustomTitle(e.target.value)}
            style={{ flex: 1 }}
            onKeyDown={e => e.key === 'Enter' && fetchThumbFromTitle()}
          />
          <button className="btn-primary" onClick={fetchThumbFromTitle} disabled={loadingThumbTitle || !customTitle.trim()}>
            {loadingThumbTitle
              ? <><div className="spinner" style={{ width: 16, height: 16 }} />Generating...</>
              : '🖼️ Generate Thumbnail'}
          </button>
        </div>

        {thumbFromTitle && !thumbFromTitle.error && (
          <div>
            <div className="grid-3" style={{ marginBottom: 12 }}>
              {[
                { title: 'Main Subject', content: thumbFromTitle.main_subject },
                { title: 'Expression / Reaction', content: thumbFromTitle.expression },
                { title: 'Text Overlay', content: thumbFromTitle.text_overlay, highlight: true },
                { title: 'Text Style', content: thumbFromTitle.text_style },
                { title: 'Background', content: thumbFromTitle.background },
                { title: 'Hook Element', content: thumbFromTitle.hook_element, highlight: true },
              ].map((item, i) => (
                <div className="ai-card" key={i} style={item.highlight ? { borderLeftColor: '#ffaa00' } : {}}>
                  <div className="ai-card-title" style={item.highlight ? { color: '#ffaa00' } : {}}>{item.title}</div>
                  <div className="ai-card-content">{item.content}</div>
                </div>
              ))}
            </div>
            <div className="ai-card" style={{ borderLeftColor: '#4488ff' }}>
              <div className="ai-card-title" style={{ color: '#4488ff' }}>Composition</div>
              <div className="ai-card-content">{thumbFromTitle.composition}</div>
            </div>
            <div className="ai-card">
              <div className="ai-card-title">Why This Works for Your Channel</div>
              <div className="ai-card-content">{thumbFromTitle.reasoning}</div>
            </div>
            {thumbFromTitle.from_cache && <div className="cache-badge">⚡ From cache</div>}
          </div>
        )}
      </div>

      {/* ── Upload Strategy ── */}
      <div className="card">
        <div className="section-title">⏰ Upload Strategy</div>
        <button className="btn-primary" onClick={fetchStrategy} disabled={loadingStrategy} style={{ marginBottom: 16 }}>
          {loadingStrategy
            ? <><div className="spinner" style={{ width: 16, height: 16 }} />Asking LLamma...</>
            : '🤖 Generate Upload Strategy'}
        </button>

        {strategy && !strategy.error && (
          <div className="grid-2">
            <div>
              <div className="ai-card">
                <div className="ai-card-title">Optimal Schedule</div>
                <div className="ai-card-content">{strategy.optimal_schedule}</div>
              </div>
              <div className="ai-card">
                <div className="ai-card-title">Why It Works</div>
                <div className="ai-card-content">{strategy.why_it_works}</div>
              </div>
              <div className="ai-card">
                <div className="ai-card-title">What to Avoid</div>
                <div className="ai-card-content">{strategy.avoid}</div>
              </div>
            </div>
            <div>
              <div style={{ marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Action Items</div>
              {(strategy.action_items || []).map((action, i) => (
                <div className="action-item" key={i}>
                  <span style={{ color: '#ff0000' }}>▶</span> {action}
                </div>
              ))}
              {strategy.from_cache && <div className="cache-badge">⚡ From cache</div>}
            </div>
          </div>
        )}
      </div>

      {/* ── Title Ideas ── */}
      <div className="card">
        <div className="section-title">📝 Title Ideas</div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <input
            className="input"
            placeholder="Topic (optional): e.g. fitness, gaming..."
            value={topic}
            onChange={e => setTopic(e.target.value)}
            style={{ flex: 1 }}
          />
          <button className="btn-primary" onClick={fetchTitles} disabled={loadingTitles}>
            {loadingTitles
              ? <><div className="spinner" style={{ width: 16, height: 16 }} />Generating...</>
              : '🤖 Generate Titles'}
          </button>
        </div>

        {titles && !titles.error && (
          <div className="grid-2">
            <div>
              <div style={{ marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase' }}>Title Ideas</div>
              {(titles.title_ideas || []).map((title, i) => (
                <div className="action-item" key={i}>
                  <span style={{ color: '#ff0000', fontWeight: 700, minWidth: 20 }}>{i + 1}.</span> {title}
                </div>
              ))}
            </div>
            <div>
              <div className="ai-card">
                <div className="ai-card-title">Winning Formula</div>
                <div className="ai-card-content">{titles.title_formula}</div>
              </div>
              <div className="ai-card">
                <div className="ai-card-title">Key Insight</div>
                <div className="ai-card-content">{titles.key_insight}</div>
              </div>
              {titles.from_cache && <div className="cache-badge">⚡ From cache</div>}
            </div>
          </div>
        )}
      </div>

      {/* ── General Thumbnail ── */}
      <div className="card">
        <div className="section-title">🎨 General Thumbnail Tips</div>
        <button className="btn-primary" onClick={fetchThumbnail} disabled={loadingThumb} style={{ marginBottom: 16 }}>
          {loadingThumb
            ? <><div className="spinner" style={{ width: 16, height: 16 }} />Analyzing...</>
            : '🤖 Generate General Tips'}
        </button>

        {thumbnail && !thumbnail.error && (
          <div className="grid-3">
            {[
              { title: 'Expression / Subject', content: thumbnail.expression },
              { title: 'Text Overlay', content: thumbnail.text_overlay },
              { title: 'Color Scheme', content: thumbnail.colors },
              { title: 'Composition', content: thumbnail.composition },
              { title: 'Why This Works', content: thumbnail.reasoning },
            ].map((item, i) => (
              <div className="ai-card" key={i}>
                <div className="ai-card-title">{item.title}</div>
                <div className="ai-card-content">{item.content}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
