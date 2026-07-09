import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from '../hooks/useApi';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const DAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const CATEGORY_COLORS = ['#555', '#4488ff', '#ffaa00', '#ff0000'];
const CATEGORY_ICONS = ['📉', '📊', '🔥', '🚀'];

export default function MLPredictor() {
  const [form, setForm] = useState({
    hour: 14,
    titleLength: 50,
    day: 'Friday',
    hasEmoji: true,
    hasExclamation: false,
    hasQuestion: false,
    titleWordCount: 8,
    titleHasNumbers: false,
  });
  const [result, setResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE}/ml-metrics`)
      .then(res => setMetrics(res.data))
      .catch(console.error)
      .finally(() => setLoadingMetrics(false));
  }, []);

  const handlePredict = async () => {
    setLoadingPredict(true);
    try {
      const res = await axios.post(`${API_BASE}/ml-predict`, {
        hour: form.hour,
        day_of_week: DAY_ORDER.indexOf(form.day),
        month: new Date().getMonth() + 1,
        title_length: form.titleLength,
        has_emoji: form.hasEmoji ? 1 : 0,
        has_exclamation: form.hasExclamation ? 1 : 0,
        has_question: form.hasQuestion ? 1 : 0,
        title_word_count: form.titleWordCount,
        title_has_numbers: form.titleHasNumbers ? 1 : 0,
      });
      setResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPredict(false);
    }
  };

  const importanceData = metrics?.feature_importance
    ? Object.entries(metrics.feature_importance)
        .map(([feature, value]) => ({
          feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          value: parseFloat((value * 100).toFixed(1)),
        }))
        .sort((a, b) => b.value - a.value)
    : [];

  const distributionData = metrics?.distribution
    ? Object.entries(metrics.distribution).map(([cat, count], i) => ({
        category: cat,
        count,
        color: CATEGORY_COLORS[i],
      }))
    : [];

  return (
    <div>
      <div className="page-title">🤖 ML Performance Classifier</div>
      <div className="page-subtitle">
        GradientBoostingClassifier trained on {metrics?.trained_on || '...'} real videos — predicts performance category
      </div>

      {/* Model Metrics */}
      {loadingMetrics ? (
        <div className="loading"><div className="spinner" />Loading model metrics...</div>
      ) : metrics && (
        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 24 }}>
          {[
            { label: 'Accuracy', value: `${(metrics.accuracy * 100).toFixed(1)}%`, sub: '5-fold CV' },
            { label: 'Low (<10K)', value: metrics.distribution?.['Low (<10K)'], sub: 'videos' },
            { label: 'Medium / High', value: (metrics.distribution?.['Medium (10K-100K)'] || 0) + (metrics.distribution?.['High (100K-1M)'] || 0), sub: 'videos' },
            { label: 'Viral (1M+)', value: metrics.distribution?.['Viral (1M+)'], sub: 'videos' },
          ].map((kpi, i) => (
            <div className="kpi-card" key={i}>
              <div className="kpi-value" style={{ fontSize: '1.6rem', color: i === 0 ? '#ff0000' : '#fff' }}>{kpi.value}</div>
              <div className="kpi-label">{kpi.label}</div>
              <div style={{ color: '#555', fontSize: '0.72rem', marginTop: 4 }}>{kpi.sub}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2">
        {/* Form */}
        <div className="card">
          <div className="section-title">📋 Video Features</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            <div>
              <label style={{ color: '#aaa', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>
                Upload Hour (UTC): <span style={{ color: '#fff' }}>{form.hour}:00</span>
              </label>
              <input type="range" min={0} max={23} value={form.hour}
                onChange={e => setForm(f => ({ ...f, hour: +e.target.value }))}
                style={{ width: '100%', accentColor: '#ff0000' }} />
            </div>

            <div>
              <label style={{ color: '#aaa', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>
                Title Length: <span style={{ color: '#fff' }}>{form.titleLength} chars</span>
              </label>
              <input type="range" min={10} max={100} value={form.titleLength}
                onChange={e => setForm(f => ({ ...f, titleLength: +e.target.value }))}
                style={{ width: '100%', accentColor: '#ff0000' }} />
            </div>

            <div>
              <label style={{ color: '#aaa', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>
                Title Word Count: <span style={{ color: '#fff' }}>{form.titleWordCount} words</span>
              </label>
              <input type="range" min={1} max={20} value={form.titleWordCount}
                onChange={e => setForm(f => ({ ...f, titleWordCount: +e.target.value }))}
                style={{ width: '100%', accentColor: '#ff0000' }} />
            </div>

            <div>
              <label style={{ color: '#aaa', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>Day of Week</label>
              <select value={form.day}
                onChange={e => setForm(f => ({ ...f, day: e.target.value }))}
                className="input">
                {DAY_ORDER.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
              {[
                { key: 'hasEmoji', label: 'Has Emoji?' },
                { key: 'hasExclamation', label: "Has '!'?" },
                { key: 'hasQuestion', label: "Has '?'?" },
                { key: 'titleHasNumbers', label: 'Has Numbers?' },
              ].map(({ key, label }) => (
                <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#aaa', fontSize: '0.88rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={form[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))}
                    style={{ accentColor: '#ff0000', width: 16, height: 16 }} />
                  {label}
                </label>
              ))}
            </div>

            <button className="btn-primary" onClick={handlePredict} disabled={loadingPredict}>
              {loadingPredict
                ? <><div className="spinner" style={{ width: 16, height: 16 }} />Predicting...</>
                : '🔮 Predict Performance'}
            </button>
          </div>
        </div>

        {/* Result */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Prediction */}
          <div className="card">
            <div className="section-title">🔮 Prediction</div>
            {!result && !loadingPredict && (
              <div style={{ color: '#555', textAlign: 'center', padding: '20px 0' }}>
                Configure features and click Predict
              </div>
            )}
            {result && (
              <div>
                {/* Main prediction */}
                <div style={{
                  background: '#1a1a1a',
                  border: `2px solid ${CATEGORY_COLORS[result.predicted_class]}`,
                  borderRadius: 12,
                  padding: 24,
                  textAlign: 'center',
                  marginBottom: 16,
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: 8 }}>
                    {CATEGORY_ICONS[result.predicted_class]}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#aaa', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
                    Predicted Performance
                  </div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: CATEGORY_COLORS[result.predicted_class] }}>
                    {result.predicted_category}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#555', marginTop: 8 }}>
                    {result.model} · Trained on {result.trained_on} videos
                  </div>
                </div>

                {/* Probabilities */}
                <div style={{ marginBottom: 8, color: '#aaa', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Category Probabilities
                </div>
                {Object.entries(result.probabilities || {}).map(([cat, pct], i) => (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#aaa', fontSize: '0.82rem' }}>{CATEGORY_ICONS[i]} {cat}</span>
                      <span style={{ color: CATEGORY_COLORS[i], fontWeight: 600, fontSize: '0.82rem' }}>{pct}%</span>
                    </div>
                    <div style={{ background: '#272727', borderRadius: 4, height: 6 }}>
                      <div style={{
                        background: CATEGORY_COLORS[i],
                        width: `${pct}%`,
                        height: '100%',
                        borderRadius: 4,
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Feature Importance */}
          {importanceData.length > 0 && (
            <div className="card">
              <div className="section-title">🎯 Feature Importance</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={importanceData} layout="vertical">
                  <XAxis type="number" stroke="#555" tick={{ fill: '#aaa', fontSize: 11 }}
                    tickFormatter={v => `${v}%`} />
                  <YAxis type="category" dataKey="feature" width={140}
                    tick={{ fill: '#aaa', fontSize: 11 }} stroke="#555" />
                  <Tooltip
                    contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                    formatter={v => [`${v}%`, 'Importance']} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {importanceData.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? '#ff0000' : '#333'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Distribution */}
      {distributionData.length > 0 && (
        <div className="card">
          <div className="section-title">📊 Channel Video Distribution</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={distributionData}>
              <XAxis dataKey="category" stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} />
              <YAxis stroke="#555" tick={{ fill: '#aaa', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: '#1f1f1f', border: '1px solid #333', borderRadius: 8 }}
                formatter={v => [v, 'Videos']} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {distributionData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
