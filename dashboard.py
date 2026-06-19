import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(

    page_title="YouTube Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main { background: #0f0f0f; }

.kpi-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 6px;
}
.kpi-label {
    font-size: 0.8rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.kpi-delta {
    font-size: 0.85rem;
    color: #ff0000;
    margin-top: 4px;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #2a2a2a;
}

.stDataFrame { background: #1a1a1a !important; }

div[data-testid="stMetricValue"] { font-size: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ─────────────────────────────────────────────────────────────
DB_PATH = "db/youtube_analytics.db"

@st.cache_data(ttl=300)
def load_all():
    conn = sqlite3.connect(DB_PATH)
    videos = pd.read_sql("""
        SELECT video_id, title, published_at, duration_seconds, is_short
        FROM videos
    """, conn)
    daily = pd.read_sql("""
        SELECT d.*, v.title, v.is_short
        FROM daily_metrics d
        JOIN videos v ON d.video_id = v.video_id
    """, conn)
    traffic = pd.read_sql("""
        SELECT t.*, v.title
        FROM traffic_sources t
        JOIN videos v ON t.video_id = v.video_id
    """, conn)
    conn.close()

    daily["date"] = pd.to_datetime(daily["date"])
    videos["published_at"] = pd.to_datetime(videos["published_at"])
    daily["watch_hours"] = daily["estimated_minutes_watched"] / 60
    daily["avg_view_pct"] = daily["average_view_percentage"].round(1)

    return videos, daily, traffic

videos, daily, traffic = load_all()

# ── Sidebar Export ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📥 Export Data")
    conn_exp = sqlite3.connect(DB_PATH)
    csv_videos = pd.read_sql("SELECT * FROM videos", conn_exp).to_csv(index=False)
    csv_daily = pd.read_sql("SELECT * FROM daily_metrics", conn_exp).to_csv(index=False)
    csv_traffic = pd.read_sql("SELECT * FROM traffic_sources", conn_exp).to_csv(index=False)
    conn_exp.close()
    st.download_button("⬇️ Videos CSV", csv_videos, "videos.csv", "text/csv", use_container_width=True)
    st.download_button("⬇️ Daily Metrics CSV", csv_daily, "daily_metrics.csv", "text/csv", use_container_width=True)
    st.download_button("⬇️ Traffic Sources CSV", csv_traffic, "traffic_sources.csv", "text/csv", use_container_width=True)
# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("## 📊 YouTube Analytics")
st.markdown(f"<span style='color:#888;font-size:0.85rem'>Last updated: {daily['date'].max().strftime('%d %b %Y')} · {len(videos)} videos · {daily['date'].min().strftime('%b %Y')} – {daily['date'].max().strftime('%b %Y')}</span>", unsafe_allow_html=True)
st.markdown("---")

# ── Time Filter ──────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([3, 1])
with col_f2:
    period = st.selectbox("Period", ["Last 30 days", "Last 90 days", "Last 365 days", "All time"], index=1)

days_map = {"Last 30 days": 30, "Last 90 days": 90, "Last 365 days": 365, "All time": 99999}
cutoff = daily["date"].max() - timedelta(days=days_map[period])
daily_f = daily[daily["date"] >= cutoff]

# ── KPIs ─────────────────────────────────────────────────────────────────────
total_views = daily_f["views"].sum()
total_hours = daily_f["watch_hours"].sum()
total_subs = daily_f["subscribers_gained"].sum() - daily_f["subscribers_lost"].sum()
avg_retention = daily_f["avg_view_pct"].mean()

k1, k2, k3, k4, k5 = st.columns(5)

def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(int(n))

with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{fmt(total_views)}</div>
        <div class="kpi-label">Views</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{fmt(total_hours)}h</div>
        <div class="kpi-label">Watch Time</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{fmt(total_subs)}</div>
        <div class="kpi-label">Net Subscribers</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{avg_retention:.1f}%</div>
        <div class="kpi-label">Avg Retention</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{len(videos)}</div>
        <div class="kpi-label">Total Videos</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Daily Views + Traffic Sources ─────────────────────────────────────
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown('<p class="section-title">📈 Daily Views</p>', unsafe_allow_html=True)
    trend = daily_f.groupby("date").agg(views=("views", "sum")).reset_index()
    fig = px.area(trend, x="date", y="views",
                  color_discrete_sequence=["#ff0000"])
    fig.update_traces(fill="tozeroy", fillcolor="rgba(255,0,0,0.1)", line_width=2)
    fig.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555",
                   tickformat=".2s"),
        height=260, showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<p class="section-title">🚦 Traffic Sources</p>', unsafe_allow_html=True)
    src_agg = (traffic.groupby("traffic_source_type")["views"]
               .sum().reset_index()
               .sort_values("views", ascending=False)
               .head(6))
    src_agg["label"] = src_agg["traffic_source_type"].str.replace("_", " ").str.title()
    src_agg["pct"] = (src_agg["views"] / src_agg["views"].sum() * 100).round(1)
    
    fig2 = px.pie(src_agg, values="views", names="label",
                  color_discrete_sequence=["#ff0000","#cc0000","#990000","#666","#444","#333"])
    fig2.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        height=260, showlegend=True,
        legend=dict(font=dict(size=10), bgcolor="#1a1a1a")
    )
    fig2.update_traces(textinfo="percent", textfont_size=11)
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Top Videos ────────────────────────────────────────────────────────
st.markdown('<p class="section-title">🏆 Top Videos by Views</p>', unsafe_allow_html=True)

top = (daily_f.groupby(["video_id", "title", "is_short"])
       .agg(views=("views", "sum"),
            watch_hours=("watch_hours", "sum"),
            avg_retention=("avg_view_pct", "mean"))
       .reset_index()
       .sort_values("views", ascending=False)
       .head(10))

top["Type"] = top["is_short"].map({1: "🩳 Short", 0: "📹 Video"})
top["Views"] = top["views"].apply(fmt)
top["Watch Hours"] = top["watch_hours"].apply(lambda x: f"{x:,.0f}h")
top["Avg Retention"] = top["avg_retention"].apply(lambda x: f"{x:.1f}%")
top["Title"] = top["title"].str[:60] + "..."

display = top[["Title", "Type", "Views", "Watch Hours", "Avg Retention"]].reset_index(drop=True)
display.index += 1

st.dataframe(display, use_container_width=True, height=370)

# ── Row 3: Shorts vs Long-form + Retention Distribution ──────────────────────
c3, c4 = st.columns(2)

with c3:
    st.markdown('<p class="section-title">⚡ Shorts vs Long-form Views</p>', unsafe_allow_html=True)
    sv = (daily_f.groupby(["date", "is_short"])["views"]
          .sum().reset_index())
    sv["Type"] = sv["is_short"].map({1: "Shorts", 0: "Long-form"})
    fig3 = px.line(sv, x="date", y="views", color="Type",
                   color_discrete_map={"Shorts": "#ff0000", "Long-form": "#4488ff"})
    fig3.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555", tickformat=".2s"),
        height=260, legend=dict(bgcolor="#1a1a1a", font=dict(size=11))
    )
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.markdown('<p class="section-title">🎯 Retention Distribution</p>', unsafe_allow_html=True)
    ret = daily_f[daily_f["avg_view_pct"] > 0]["avg_view_pct"]
    fig4 = px.histogram(ret, nbins=30, color_discrete_sequence=["#ff0000"])
    fig4.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555", title="Retention %"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555", title="Videos"),
        height=260, showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<span style='color:#555;font-size:0.75rem'>YouTube Analytics Pipeline · SQLite · Streamlit · Built by Mihai Catana</span>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: Best Time to Post
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## ⏰ Best Time to Post")

videos_raw = pd.read_sql_query("SELECT video_id, published_at, is_short FROM videos", 
                                sqlite3.connect(DB_PATH))
daily_raw = pd.read_sql_query("SELECT video_id, SUM(views) as total_views FROM daily_metrics GROUP BY video_id",
                               sqlite3.connect(DB_PATH))

vt = videos_raw.merge(daily_raw, on="video_id")
vt["published_at"] = pd.to_datetime(vt["published_at"])
vt["hour"] = vt["published_at"].dt.hour
vt["day"] = vt["published_at"].dt.day_name()

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown('<p class="section-title">📅 Avg Views by Day of Week</p>', unsafe_allow_html=True)
    day_avg = (vt.groupby("day")["total_views"]
               .mean().reindex(DAY_ORDER).reset_index())
    day_avg.columns = ["day", "avg_views"]
    day_avg["color"] = day_avg["avg_views"].apply(
        lambda x: "#ff0000" if x == day_avg["avg_views"].max() else "#333"
    )
    fig_day = px.bar(day_avg, x="day", y="avg_views",
                     color="color", color_discrete_map="identity")
    fig_day.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555", tickformat=".2s"),
        height=280, showlegend=False
    )
    st.plotly_chart(fig_day, use_container_width=True)
    best_day = day_avg.loc[day_avg["avg_views"].idxmax(), "day"]
    st.markdown(f"<span style='color:#ff0000;font-weight:600'>Best day: {best_day}</span> — {fmt(int(day_avg['avg_views'].max()))} avg views", unsafe_allow_html=True)

with col_t2:
    st.markdown('<p class="section-title">🕐 Avg Views by Hour (UTC)</p>', unsafe_allow_html=True)
    hour_avg = (vt.groupby("hour")["total_views"]
                .mean().reset_index())
    hour_avg.columns = ["hour", "avg_views"]
    hour_avg["color"] = hour_avg["avg_views"].apply(
        lambda x: "#ff0000" if x == hour_avg["avg_views"].max() else "#333"
    )
    fig_hr = px.bar(hour_avg, x="hour", y="avg_views",
                    color="color", color_discrete_map="identity")
    fig_hr.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555", dtick=2),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555", tickformat=".2s"),
        height=280, showlegend=False
    )
    st.plotly_chart(fig_hr, use_container_width=True)
    best_hr = hour_avg.loc[hour_avg["avg_views"].idxmax(), "hour"]
    st.markdown(f"<span style='color:#ff0000;font-weight:600'>Best hour: {best_hr}:00 UTC</span> — {fmt(int(hour_avg['avg_views'].max()))} avg views", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: Correlation Analysis
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🔗 Correlation Analysis")

vt["title_length"] = vt["video_id"].map(
    dict(zip(videos["video_id"], videos["title"].str.len()))
)
vt["duration_sec"] = vt["video_id"].map(
    dict(zip(videos["video_id"], videos["duration_seconds"]))
)

col_c1, col_c2 = st.columns(2)

with col_c1:
    st.markdown('<p class="section-title">⏱️ Duration vs Views</p>', unsafe_allow_html=True)
    vt_dur = vt[vt["duration_sec"].notna() & (vt["duration_sec"] > 0)].copy()
    # Cap outliers la percentila 95 pentru vizibilitate
    y_cap = vt_dur["total_views"].quantile(0.95)
    vt_dur["views_capped"] = vt_dur["total_views"].clip(upper=y_cap)
    vt_dur["Type"] = vt_dur["is_short"].map({1: "Short", 0: "Long-form"})
    fig_dur = px.scatter(vt_dur, x="duration_sec", y="views_capped",
                         color="Type",
                         trendline="ols",
                         color_discrete_map={"Short": "#ff0000", "Long-form": "#4488ff"},
                         hover_data={"duration_sec": True, "total_views": True, "views_capped": False})
    fig_dur.update_traces(marker=dict(size=5, opacity=0.6))
    fig_dur.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555", title="Duration (seconds)"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555",
                   tickformat=".2s", title="Views (capped at p95)"),
        height=280, legend=dict(bgcolor="#1a1a1a", font=dict(size=10))
    )
    st.plotly_chart(fig_dur, use_container_width=True)

with col_c2:
    st.markdown('<p class="section-title">📝 Title Length vs Views</p>', unsafe_allow_html=True)
    vt_tl = vt[vt["title_length"].notna()].copy()
    fig_tl = px.scatter(vt_tl, x="title_length", y="total_views",
                        trendline="ols",
                        color_discrete_sequence=["#4488ff"],
                        hover_data={"title_length": True, "total_views": True})
    fig_tl.update_traces(marker=dict(size=5, opacity=0.6))
    fig_tl.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False, color="#555", title="Title Length (chars)"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555",
                   tickformat=".2s", title="Total Views"),
        height=280
    )
    st.plotly_chart(fig_tl, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: ML Prediction
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🤖 ML Performance Predictor")
st.markdown("<span style='color:#888;font-size:0.85rem'>Predicts expected views in first 7 days based on video features</span>", unsafe_allow_html=True)

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

@st.cache_data
def train_model():
    conn = sqlite3.connect(DB_PATH)
    
    # Views in first 7 days per video
    first7 = pd.read_sql("""
        SELECT d.video_id,
               SUM(CASE WHEN julianday(d.date) - julianday(v.published_at) <= 7 
                        THEN d.views ELSE 0 END) as views_7d,
               SUM(d.views) as total_views
        FROM daily_metrics d
        JOIN videos v ON d.video_id = v.video_id
        GROUP BY d.video_id
        HAVING total_views > 0
    """, conn)
    
    vids = pd.read_sql("SELECT video_id, title, published_at, duration_seconds, is_short FROM videos", conn)
    conn.close()
    
    df = vids.merge(first7, on="video_id")
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["hour"] = df["published_at"].dt.hour
    df["day_of_week"] = df["published_at"].dt.dayofweek
    df["month"] = df["published_at"].dt.month
    df["title_length"] = df["title"].str.len()
    df["has_emoji"] = df["title"].str.contains(r'[^\x00-\x7F]', regex=True).astype(int)
    df["has_exclamation"] = df["title"].str.contains("!").astype(int)
    df["has_question"] = df["title"].str.contains(r'\?').astype(int)
    
    features = ["duration_seconds", "is_short", "hour", "day_of_week", 
                "month", "title_length", "has_emoji", "has_exclamation", "has_question"]
    
    df = df.dropna(subset=features + ["views_7d"])
    X = df[features]
    y = np.log1p(df["views_7d"])
    
    model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    model.fit(X, y)
    
    importance = pd.DataFrame({
        "feature": features,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=True)
    
    return model, features, scores.mean(), importance

with st.spinner("Training model on your channel data..."):
    model, features, r2, importance = train_model()

col_m1, col_m2 = st.columns([1, 1])

with col_m1:
    st.markdown('<p class="section-title">🎯 Feature Importance</p>', unsafe_allow_html=True)
    importance["feature_label"] = importance["feature"].str.replace("_", " ").str.title()
    fig_imp = px.bar(importance, x="importance", y="feature_label",
                     orientation="h", color_discrete_sequence=["#ff0000"])
    fig_imp.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#ccc", margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a", color="#555"),
        yaxis=dict(showgrid=False, color="#555"),
        height=300, showlegend=False
    )
    st.plotly_chart(fig_imp, use_container_width=True)
    st.markdown(f"<span style='color:#888;font-size:0.8rem'>Model R² score: <b style='color:#fff'>{r2:.3f}</b> (5-fold CV)</span>", unsafe_allow_html=True)

with col_m2:
    st.markdown('<p class="section-title">🔮 Predict Your Next Video</p>', unsafe_allow_html=True)
    
    p1, p2 = st.columns(2)
    with p1:
        pred_dur = st.slider("Duration (sec)", 15, 1200, 60)
        pred_hour = st.slider("Upload hour (UTC)", 0, 23, 14)
        pred_title_len = st.slider("Title length", 10, 100, 50)
    with p2:
        pred_day = st.selectbox("Day of week", DAY_ORDER)
        pred_short = st.checkbox("Is a Short?", value=True)
        pred_emoji = st.checkbox("Has emoji?", value=True)
        pred_excl = st.checkbox("Has '!'?", value=True)
    
    day_num = DAY_ORDER.index(pred_day)
    X_pred = pd.DataFrame([{
        "duration_seconds": pred_dur,
        "is_short": int(pred_short),
        "hour": pred_hour,
        "day_of_week": day_num,
        "month": datetime.now().month,
        "title_length": pred_title_len,
        "has_emoji": int(pred_emoji),
        "has_exclamation": int(pred_excl),
        "has_question": 0
    }])
    
    pred_views = int(np.expm1(model.predict(X_pred)[0]))
    
    st.markdown(f"""
    <div style='background:#1a1a1a;border:1px solid #ff0000;border-radius:12px;
                padding:24px;text-align:center;margin-top:16px'>
        <div style='font-size:0.8rem;color:#888;text-transform:uppercase;
                    letter-spacing:0.1em;margin-bottom:8px'>Predicted Views (7 days)</div>
        <div style='font-size:3rem;font-weight:700;color:#ff0000'>{fmt(pred_views)}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: Data Quality
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🔍 Data Quality")

@st.cache_data
def run_quality_checks():
    conn = sqlite3.connect(DB_PATH)
    
    # Duplicate check
    dup_metrics = pd.read_sql("""
        SELECT COUNT(*) - COUNT(DISTINCT video_id || date) as dups 
        FROM daily_metrics
    """, conn).iloc[0,0]
    
    dup_traffic = pd.read_sql("""
        SELECT COUNT(*) - COUNT(DISTINCT video_id || traffic_source_type) as dups 
        FROM traffic_sources
    """, conn).iloc[0,0]
    
    # Missing video IDs
    missing_vids = pd.read_sql("""
        SELECT COUNT(*) as cnt FROM daily_metrics 
        WHERE video_id NOT IN (SELECT video_id FROM videos)
    """, conn).iloc[0,0]
    
    # Missing dates
    missing_dates = pd.read_sql("""
        SELECT COUNT(*) as cnt FROM daily_metrics WHERE date IS NULL OR date = ''
    """, conn).iloc[0,0]
    
    # Latest ingestion
    latest = pd.read_sql("SELECT MAX(fetched_at) as last FROM daily_metrics", conn).iloc[0,0]
    
    # Total rows
    total_videos = pd.read_sql("SELECT COUNT(*) FROM videos", conn).iloc[0,0]
    total_metrics = pd.read_sql("SELECT COUNT(*) FROM daily_metrics", conn).iloc[0,0]
    total_traffic = pd.read_sql("SELECT COUNT(*) FROM traffic_sources", conn).iloc[0,0]
    
    conn.close()
    return {
        "dup_metrics": dup_metrics,
        "dup_traffic": dup_traffic,
        "missing_vids": missing_vids,
        "missing_dates": missing_dates,
        "latest": latest,
        "total_videos": total_videos,
        "total_metrics": total_metrics,
        "total_traffic": total_traffic
    }

qc = run_quality_checks()

dq1, dq2 = st.columns(2)

with dq1:
    st.markdown('<p class="section-title">✅ Checks</p>', unsafe_allow_html=True)
    
    checks = [
        (qc["dup_metrics"] == 0, f"No duplicate daily metric records ({qc['total_metrics']:,} rows)"),
        (qc["dup_traffic"] == 0, f"No duplicate traffic source records ({qc['total_traffic']:,} rows)"),
        (qc["missing_vids"] == 0, "No orphaned metric records (all video IDs valid)"),
        (qc["missing_dates"] == 0, "No missing dates in daily metrics"),
        (qc["latest"] is not None, f"Latest ingestion: {qc['latest'][:16] if qc['latest'] else 'N/A'}"),
    ]
    
    for passed, msg in checks:
        icon = "✅" if passed else "❌"
        color = "#4caf50" if passed else "#f44336"
        st.markdown(f"<span style='color:{color}'>{icon}</span> {msg}", unsafe_allow_html=True)

with dq2:
    st.markdown('<p class="section-title">📦 Database Stats</p>', unsafe_allow_html=True)
    stats = [
        ("Videos", f"{qc['total_videos']:,}"),
        ("Daily metric rows", f"{qc['total_metrics']:,}"),
        ("Traffic source rows", f"{qc['total_traffic']:,}"),
        ("DB size", f"~{qc['total_metrics'] * 0.0002:.1f} MB (estimated)"),
    ]
    for label, val in stats:
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
            f"border-bottom:1px solid #2a2a2a'>"
            f"<span style='color:#888'>{label}</span>"
            f"<span style='color:#fff;font-weight:600'>{val}</span></div>",
            unsafe_allow_html=True
        )

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: Auto Insights
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 💡 Automated Insights")

@st.cache_data
def generate_insights():
    conn = sqlite3.connect(DB_PATH)
    
    vids = pd.read_sql("SELECT video_id, title, published_at, duration_seconds, is_short FROM videos", conn)
    daily_all = pd.read_sql("""
        SELECT d.*, v.is_short FROM daily_metrics d 
        JOIN videos v ON d.video_id = v.video_id
    """, conn)
    traffic_all = pd.read_sql("SELECT * FROM traffic_sources", conn)
    conn.close()
    
    insights = []
    
    # Shorts vs Long-form views
    shorts_views = daily_all[daily_all["is_short"]==1]["views"].sum()
    total_v = daily_all["views"].sum()
    shorts_pct = shorts_views / total_v * 100
    insights.append(("📱", f"Shorts generated **{shorts_pct:.0f}%** of total channel views ({fmt(int(shorts_views))} out of {fmt(int(total_v))})"))
    
    # Best day
    vids["published_at"] = pd.to_datetime(vids["published_at"])
    vids["day"] = vids["published_at"].dt.day_name()
    total_per_video = daily_all.groupby("video_id")["views"].sum().reset_index()
    vids_m = vids.merge(total_per_video, on="video_id")
    best_day = vids_m.groupby("day")["views"].mean().idxmax()
    best_day_val = vids_m.groupby("day")["views"].mean().max()
    insights.append(("📅", f"**{best_day}** is the best publishing day — {fmt(int(best_day_val))} avg views per video"))
    
    # Best traffic source
    best_src = traffic_all.groupby("traffic_source_type")["views"].sum().idxmax()
    best_src_pct = (traffic_all.groupby("traffic_source_type")["views"].sum().max() / 
                    traffic_all["views"].sum() * 100)
    insights.append(("🚦", f"**{best_src.replace('_',' ').title()}** is the top traffic source — {best_src_pct:.0f}% of views"))
    
    # Avg retention
    avg_ret = daily_all[daily_all["average_view_percentage"] > 0]["average_view_percentage"].mean()
    insights.append(("🎯", f"Average retention across all videos: **{avg_ret:.1f}%** — {'above' if avg_ret > 50 else 'below'} the 50% benchmark"))
    
    # Most productive month
    daily_all["date"] = pd.to_datetime(daily_all["date"])
    daily_all["month"] = daily_all["date"].dt.strftime("%B %Y")
    best_month = daily_all.groupby("month")["views"].sum().idxmax()
    best_month_views = daily_all.groupby("month")["views"].sum().max()
    insights.append(("🗓️", f"**{best_month}** was the best month — {fmt(int(best_month_views))} views"))
    
    # Shorts count
    n_shorts = vids["is_short"].sum()
    n_long = len(vids) - n_shorts
    insights.append(("📊", f"Channel mix: **{n_shorts} Shorts** ({n_shorts/len(vids)*100:.0f}%) and **{n_long} long-form** videos ({n_long/len(vids)*100:.0f}%)"))
    
    return insights

insights = generate_insights()

ins1, ins2 = st.columns(2)
for i, (icon, text) in enumerate(insights):
    col = ins1 if i % 2 == 0 else ins2
    with col:
        st.markdown(
            f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
            f"padding:14px 16px;margin-bottom:10px'>"
            f"<span style='font-size:1.2rem'>{icon}</span> "
            f"<span style='color:#ccc;font-size:0.9rem'>{text}</span></div>",
            unsafe_allow_html=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: ML Metrics (improved)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📈 Model Performance")

@st.cache_data
def get_model_metrics():
    conn = sqlite3.connect(DB_PATH)
    first7 = pd.read_sql("""
        SELECT d.video_id,
               SUM(CASE WHEN julianday(d.date) - julianday(v.published_at) <= 7 
                        THEN d.views ELSE 0 END) as views_7d
        FROM daily_metrics d
        JOIN videos v ON d.video_id = v.video_id
        GROUP BY d.video_id
        HAVING SUM(d.views) > 0
    """, conn)
    vids2 = pd.read_sql("SELECT video_id, published_at, duration_seconds, is_short, title FROM videos", conn)
    conn.close()
    
    df = vids2.merge(first7, on="video_id").dropna()
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["hour"] = df["published_at"].dt.hour
    df["day_of_week"] = df["published_at"].dt.dayofweek
    df["month"] = df["published_at"].dt.month
    df["title_length"] = df["title"].str.len()
    df["has_emoji"] = df["title"].str.contains(r'[^\x00-\x7F]', regex=True).astype(int)
    df["has_exclamation"] = df["title"].str.contains("!").astype(int)
    df["has_question"] = df["title"].str.contains(r'\?').astype(int)
    
    feats = ["duration_seconds","is_short","hour","day_of_week","month",
             "title_length","has_emoji","has_exclamation","has_question"]
    df = df.dropna(subset=feats + ["views_7d"])
    X = df[feats]
    y = df["views_7d"]
    y_log = np.log1p(y)
    
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    
    model2 = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    y_pred_log = cross_val_predict(model2, X, y_log, cv=5)
    y_pred = np.expm1(y_pred_log)
    
    # Baseline = median
    baseline_pred = np.full_like(y, y.median())
    
    rmse_model = np.sqrt(mean_squared_error(y, y_pred))
    rmse_baseline = np.sqrt(mean_squared_error(y, baseline_pred))
    mae_model = mean_absolute_error(y, y_pred)
    
    r2_scores = cross_val_score(model2, X, y_log, cv=5, scoring="r2")
    
    improvement = (rmse_baseline - rmse_model) / rmse_baseline * 100
    
    return {
        "rmse_model": rmse_model,
        "rmse_baseline": rmse_baseline,
        "mae": mae_model,
        "r2": r2_scores.mean(),
        "improvement": improvement
    }

with st.spinner("Computing model metrics..."):
    mm = get_model_metrics()

m1, m2, m3, m4 = st.columns(4)
metrics_data = [
    (m1, "R² Score", f"{mm['r2']:.3f}", "5-fold CV"),
    (m2, "Model RMSE", fmt(int(mm['rmse_model'])), "views"),
    (m3, "Baseline RMSE", fmt(int(mm['rmse_baseline'])), "median baseline"),
    (m4, "Improvement", f"{mm['improvement']:.0f}%", "vs baseline"),
]
for col, label, val, sub in metrics_data:
    with col:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value" style="font-size:1.6rem">{val}</div>
            <div class="kpi-label">{label}</div>
            <div style="color:#666;font-size:0.75rem;margin-top:4px">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<span style='color:#555;font-size:0.75rem'>YouTube Analytics Pipeline · SQLite · Streamlit · ML · Built by Mihai Catana</span>", unsafe_allow_html=True)