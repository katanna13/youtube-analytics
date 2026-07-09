"""
dashboard.py — YouTube Growth Copilot
Streamlit dashboard cu tabs separate si AI insights via Gemma 4
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
import os

warnings.filterwarnings("ignore")

# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Growth Copilot",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS YouTube Theme ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
    background-color: #0f0f0f;
    color: #f1f1f1;
}

.main { background: #0f0f0f; }

/* Header */
.yt-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 0 8px 0;
    border-bottom: 1px solid #272727;
    margin-bottom: 20px;
}
.yt-logo {
    font-size: 1.8rem;
    font-weight: 700;
    color: #fff;
}
.yt-logo span { color: #ff0000; }
.yt-subtitle {
    font-size: 0.85rem;
    color: #aaa;
    margin-top: 2px;
}

/* KPI Cards */
.kpi-card {
    background: #1f1f1f;
    border: 1px solid #272727;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: #ff0000; }
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 6px;
}
.kpi-label {
    font-size: 0.75rem;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Section titles */
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f1f1;
    margin: 0 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #ff0000;
    display: inline-block;
}

/* AI Insight Cards */
.ai-card {
    background: #1f1f1f;
    border: 1px solid #272727;
    border-left: 3px solid #ff0000;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.ai-card-title {
    font-size: 0.75rem;
    color: #ff0000;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    font-weight: 600;
}
.ai-card-content {
    font-size: 0.9rem;
    color: #e0e0e0;
    line-height: 1.6;
}

/* Action items */
.action-item {
    background: #272727;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: #f1f1f1;
    border-left: 3px solid #ff0000;
}

/* Score badge */
.score-badge {
    display: inline-block;
    background: #ff0000;
    color: #fff;
    font-size: 2rem;
    font-weight: 700;
    padding: 12px 24px;
    border-radius: 12px;
    text-align: center;
}

/* Tags */
.tag {
    display: inline-block;
    background: #272727;
    color: #aaa;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 3px;
}
.tag-red {
    background: rgba(255,0,0,0.15);
    color: #ff6666;
}

/* Subscribe button style */
.subscribe-btn {
    background: #ff0000;
    color: #fff;
    border: none;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
}

/* Weak video card */
.weak-card {
    background: #1f1f1f;
    border: 1px solid #272727;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}
.weak-card-title {
    font-size: 0.9rem;
    color: #f1f1f1;
    font-weight: 500;
    margin-bottom: 6px;
}
.weak-metric {
    font-size: 0.8rem;
    color: #aaa;
}
.weak-metric span { color: #ff6666; font-weight: 600; }

div[data-testid="stMetricValue"] { font-size: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── DB Config ─────────────────────────────────────────────────────────────────
DB_PATH = "db/youtube_analytics.db"
DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(int(n))

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    conn = sqlite3.connect(DB_PATH)
    videos = pd.read_sql("SELECT * FROM videos", conn)
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

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="yt-header">
    <div>
        <div class="yt-logo">▶ YouTube <span>Growth</span> Copilot</div>
        <div class="yt-subtitle">AI-powered channel analysis · Powered by Gemma 4 via Fireworks AI</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar Export ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ▶ YouTube Growth Copilot")
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    conn_exp = sqlite3.connect(DB_PATH)
    csv_videos = pd.read_sql("SELECT * FROM videos", conn_exp).to_csv(index=False)
    csv_daily = pd.read_sql("SELECT * FROM daily_metrics", conn_exp).to_csv(index=False)
    conn_exp.close()
    st.download_button("⬇️ Videos CSV", csv_videos, "videos.csv", "text/csv", use_container_width=True)
    st.download_button("⬇️ Daily Metrics CSV", csv_daily, "daily_metrics.csv", "text/csv", use_container_width=True)
    st.markdown("---")
    st.markdown(f"<span style='color:#aaa;font-size:0.8rem'>{len(videos)} videos · {daily['date'].max().strftime('%d %b %Y')}</span>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview",
    "⏰ Best Times",
    "🔗 Correlations",
    "🤖 ML Predictor",
    "💡 AI Insights",
    "📈 Channel Audit",
    "🔍 Data Quality",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    # Time filter
    col_f1, col_f2 = st.columns([4, 1])
    with col_f2:
        period = st.selectbox("Period", ["Last 30 days", "Last 90 days", "Last 365 days", "All time"], index=1)

    days_map = {"Last 30 days": 30, "Last 90 days": 90, "Last 365 days": 365, "All time": 99999}
    cutoff = daily["date"].max() - timedelta(days=days_map[period])
    daily_f = daily[daily["date"] >= cutoff]

    # KPIs
    total_views = daily_f["views"].sum()
    total_hours = daily_f["watch_hours"].sum()
    total_subs = daily_f["subscribers_gained"].sum() - daily_f["subscribers_lost"].sum()
    avg_retention = daily_f["avg_view_pct"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, fmt(total_views), "Views"),
        (k2, f"{fmt(total_hours)}h", "Watch Time"),
        (k3, fmt(total_subs), "Net Subscribers"),
        (k4, f"{avg_retention:.1f}%", "Avg Retention"),
        (k5, str(len(videos)), "Total Videos"),
    ]
    for col, val, label in kpis:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-value">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<p class="section-title">📈 Daily Views</p>', unsafe_allow_html=True)
        trend = daily_f.groupby("date").agg(views=("views", "sum")).reset_index()
        fig = px.area(trend, x="date", y="views", color_discrete_sequence=["#ff0000"])
        fig.update_traces(fill="tozeroy", fillcolor="rgba(255,0,0,0.1)", line_width=2)
        fig.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=260, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<p class="section-title">🚦 Traffic Sources</p>', unsafe_allow_html=True)
        src_agg = (traffic.groupby("traffic_source_type")["views"]
                   .sum().reset_index().sort_values("views", ascending=False).head(6))
        src_agg["label"] = src_agg["traffic_source_type"].str.replace("_", " ").str.title()
        fig2 = px.pie(src_agg, values="views", names="label",
                      color_discrete_sequence=["#ff0000","#cc0000","#990000","#666","#444","#333"])
        fig2.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            height=260, showlegend=True,
            legend=dict(font=dict(size=10), bgcolor="#1f1f1f")
        )
        fig2.update_traces(textinfo="percent", textfont_size=11)
        st.plotly_chart(fig2, use_container_width=True)

    # Top Videos
    st.markdown('<p class="section-title">🏆 Top Videos by Views</p>', unsafe_allow_html=True)
    top = (daily_f.groupby(["video_id","title","is_short"])
           .agg(views=("views","sum"), watch_hours=("watch_hours","sum"), avg_retention=("avg_view_pct","mean"))
           .reset_index().sort_values("views", ascending=False).head(10))
    top["Type"] = top["is_short"].map({1: "🩳 Short", 0: "▶ Video"})
    top["Views"] = top["views"].apply(fmt)
    top["Watch Hours"] = top["watch_hours"].apply(lambda x: f"{x:,.0f}h")
    top["Avg Retention"] = top["avg_retention"].apply(lambda x: f"{x:.1f}%")
    top["Title"] = top["title"].str[:55] + "..."
    display = top[["Title","Type","Views","Watch Hours","Avg Retention"]].reset_index(drop=True)
    display.index += 1
    st.dataframe(display, use_container_width=True, height=370)

    # Shorts vs Long
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<p class="section-title">⚡ Shorts vs Long-form</p>', unsafe_allow_html=True)
        sv = daily_f.groupby(["date","is_short"])["views"].sum().reset_index()
        sv["Type"] = sv["is_short"].map({1: "Shorts", 0: "Long-form"})
        fig3 = px.line(sv, x="date", y="views", color="Type",
                       color_discrete_map={"Shorts":"#ff0000","Long-form":"#4488ff"})
        fig3.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=260, legend=dict(bgcolor="#1f1f1f", font=dict(size=11))
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<p class="section-title">🎯 Retention Distribution</p>', unsafe_allow_html=True)
        ret = daily_f[daily_f["avg_view_pct"] > 0]["avg_view_pct"]
        fig4 = px.histogram(ret, nbins=30, color_discrete_sequence=["#ff0000"])
        fig4.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555", title="Retention %"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", title="Videos"),
            height=260, showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: BEST TIMES
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ⏰ Best Time to Post")
    st.markdown("<span style='color:#aaa;font-size:0.85rem'>Based on real performance data from your channel</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    conn2 = sqlite3.connect(DB_PATH)
    vt = pd.read_sql("SELECT video_id, published_at, is_short FROM videos", conn2)
    dv = pd.read_sql("SELECT video_id, SUM(views) as total_views FROM daily_metrics GROUP BY video_id", conn2)
    conn2.close()

    vt = vt.merge(dv, on="video_id")
    vt["published_at"] = pd.to_datetime(vt["published_at"])
    vt["hour"] = vt["published_at"].dt.hour
    vt["day"] = vt["published_at"].dt.day_name()

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown('<p class="section-title">📅 Avg Views by Day of Week</p>', unsafe_allow_html=True)
        day_avg = vt.groupby("day")["total_views"].mean().reindex(DAY_ORDER).reset_index()
        day_avg.columns = ["day","avg_views"]
        day_avg["color"] = day_avg["avg_views"].apply(
            lambda x: "#ff0000" if x == day_avg["avg_views"].max() else "#333"
        )
        fig_day = px.bar(day_avg, x="day", y="avg_views", color="color", color_discrete_map="identity")
        fig_day.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=300, showlegend=False
        )
        st.plotly_chart(fig_day, use_container_width=True)
        best_day = day_avg.loc[day_avg["avg_views"].idxmax(), "day"]
        st.markdown(f"""<div class="ai-card">
            <div class="ai-card-title">Best Day</div>
            <div class="ai-card-content">Post on <b style='color:#ff0000'>{best_day}</b> — {fmt(int(day_avg['avg_views'].max()))} avg views per video</div>
        </div>""", unsafe_allow_html=True)

    with col_t2:
        st.markdown('<p class="section-title">🕐 Avg Views by Hour (UTC)</p>', unsafe_allow_html=True)
        hour_avg = vt.groupby("hour")["total_views"].mean().reset_index()
        hour_avg.columns = ["hour","avg_views"]
        hour_avg["color"] = hour_avg["avg_views"].apply(
            lambda x: "#ff0000" if x == hour_avg["avg_views"].max() else "#333"
        )
        fig_hr = px.bar(hour_avg, x="hour", y="avg_views", color="color", color_discrete_map="identity")
        fig_hr.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555", dtick=2),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=300, showlegend=False
        )
        st.plotly_chart(fig_hr, use_container_width=True)
        best_hr = hour_avg.loc[hour_avg["avg_views"].idxmax(), "hour"]
        st.markdown(f"""<div class="ai-card">
            <div class="ai-card-title">Best Hour</div>
            <div class="ai-card-content">Post at <b style='color:#ff0000'>{best_hr}:00 UTC</b> — {fmt(int(hour_avg['avg_views'].max()))} avg views per video</div>
        </div>""", unsafe_allow_html=True)

    # Heatmap day x hour
    st.markdown('<p class="section-title">🔥 Views Heatmap: Day × Hour</p>', unsafe_allow_html=True)
    heat = vt.groupby(["day","hour"])["total_views"].mean().reset_index()
    heat_pivot = heat.pivot(index="day", columns="hour", values="total_views").reindex(DAY_ORDER)
    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale=[[0,"#1f1f1f"],[0.5,"#990000"],[1,"#ff0000"]],
        aspect="auto",
        labels=dict(x="Hour (UTC)", y="Day", color="Avg Views")
    )
    fig_heat.update_layout(
        paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
        font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
        height=300
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: CORRELATIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🔗 Correlation Analysis")
    st.markdown("<span style='color:#aaa;font-size:0.85rem'>How video features affect performance</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    conn3 = sqlite3.connect(DB_PATH)
    vt3 = pd.read_sql("SELECT video_id, published_at, duration_seconds, is_short, title FROM videos", conn3)
    dv3 = pd.read_sql("SELECT video_id, SUM(views) as total_views FROM daily_metrics GROUP BY video_id", conn3)
    conn3.close()

    vt3 = vt3.merge(dv3, on="video_id")
    vt3["title_length"] = vt3["title"].str.len()

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown('<p class="section-title">⏱️ Duration vs Views</p>', unsafe_allow_html=True)
        vt_dur = vt3[vt3["duration_seconds"].notna() & (vt3["duration_seconds"] > 0)].copy()
        y_cap = vt_dur["total_views"].quantile(0.95)
        vt_dur["views_capped"] = vt_dur["total_views"].clip(upper=y_cap)
        vt_dur["Type"] = vt_dur["is_short"].map({1: "Short", 0: "Long-form"})
        fig_dur = px.scatter(vt_dur, x="duration_seconds", y="views_capped", color="Type",
                             trendline="ols",
                             color_discrete_map={"Short":"#ff0000","Long-form":"#4488ff"})
        fig_dur.update_traces(marker=dict(size=5, opacity=0.6))
        fig_dur.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555", title="Duration (seconds)"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=300, legend=dict(bgcolor="#1f1f1f")
        )
        st.plotly_chart(fig_dur, use_container_width=True)

    with col_c2:
        st.markdown('<p class="section-title">📝 Title Length vs Views</p>', unsafe_allow_html=True)
        fig_tl = px.scatter(vt3, x="title_length", y="total_views",
                            trendline="ols", color_discrete_sequence=["#4488ff"])
        fig_tl.update_traces(marker=dict(size=5, opacity=0.6))
        fig_tl.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, color="#555", title="Title Length (chars)"),
            yaxis=dict(showgrid=True, gridcolor="#272727", color="#555", tickformat=".2s"),
            height=300
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    # Shorts vs Long summary
    st.markdown('<p class="section-title">⚡ Format Performance Summary</p>', unsafe_allow_html=True)
    shorts_data = vt3[vt3["is_short"]==1]["total_views"]
    longs_data = vt3[vt3["is_short"]==0]["total_views"]
    shorts_avg = int(shorts_data.mean()) if len(shorts_data) > 0 else 0
    longs_avg = int(longs_data.mean()) if len(longs_data) > 0 else 0
    multiplier = round(shorts_avg / longs_avg, 2) if longs_avg > 0 else 1.0
    better = "Shorts" if shorts_avg > longs_avg else "Long-form"

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#ff0000">{fmt(shorts_avg)}</div>
            <div class="kpi-label">Avg Views — Shorts</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#4488ff">{fmt(longs_avg)}</div>
            <div class="kpi-label">Avg Views — Long-form</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#ffaa00">{multiplier}x</div>
            <div class="kpi-label">{better} perform better</div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: ML PREDICTOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🤖 ML Performance Predictor")
    st.markdown("<span style='color:#aaa;font-size:0.85rem'>Predicts expected views in first 7 days based on video features</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    @st.cache_data
    def train_model():
        conn = sqlite3.connect(DB_PATH)
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

        features = ["duration_seconds","is_short","hour","day_of_week","month",
                    "title_length","has_emoji","has_exclamation","has_question"]
        df = df.dropna(subset=features + ["views_7d"])
        X = df[features]
        y = np.log1p(df["views_7d"])

        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        scores = cross_val_score(model, X, y, cv=5, scoring="r2")

        y_pred_log = cross_val_predict(model, X, y, cv=5)
        y_pred = np.expm1(y_pred_log)
        y_actual = np.expm1(y)
        baseline = np.full_like(y_actual, np.expm1(y).median())

        rmse_model = np.sqrt(mean_squared_error(y_actual, y_pred))
        rmse_baseline = np.sqrt(mean_squared_error(y_actual, baseline))
        improvement = (rmse_baseline - rmse_model) / rmse_baseline * 100

        model.fit(X, y)
        importance = pd.DataFrame({"feature": features, "importance": model.feature_importances_}).sort_values("importance", ascending=True)

        return model, features, scores.mean(), importance, rmse_model, rmse_baseline, improvement

    with st.spinner("Training model on your channel data..."):
        model, features, r2, importance, rmse_m, rmse_b, improvement = train_model()

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    for col, label, val, sub in [
        (m1, "R² Score", f"{r2:.3f}", "5-fold CV"),
        (m2, "Model RMSE", fmt(int(rmse_m)), "views"),
        (m3, "Baseline RMSE", fmt(int(rmse_b)), "median baseline"),
        (m4, "Improvement", f"{improvement:.0f}%", "vs baseline"),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-value" style="font-size:1.6rem">{val}</div>
                <div class="kpi-label">{label}</div>
                <div style="color:#666;font-size:0.75rem;margin-top:4px">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown('<p class="section-title">🎯 Feature Importance</p>', unsafe_allow_html=True)
        importance["feature_label"] = importance["feature"].str.replace("_"," ").str.title()
        fig_imp = px.bar(importance, x="importance", y="feature_label",
                         orientation="h", color_discrete_sequence=["#ff0000"])
        fig_imp.update_layout(
            paper_bgcolor="#1f1f1f", plot_bgcolor="#1f1f1f",
            font_color="#aaa", margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=True, gridcolor="#272727", color="#555"),
            yaxis=dict(showgrid=False, color="#555"),
            height=320, showlegend=False
        )
        st.plotly_chart(fig_imp, use_container_width=True)

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

        X_pred = pd.DataFrame([{
            "duration_seconds": pred_dur,
            "is_short": int(pred_short),
            "hour": pred_hour,
            "day_of_week": DAY_ORDER.index(pred_day),
            "month": datetime.now().month,
            "title_length": pred_title_len,
            "has_emoji": int(pred_emoji),
            "has_exclamation": int(pred_excl),
            "has_question": 0
        }])

        pred_views = int(np.expm1(model.predict(X_pred)[0]))
        st.markdown(f"""
        <div style='background:#1f1f1f;border:2px solid #ff0000;border-radius:12px;
                    padding:24px;text-align:center;margin-top:16px'>
            <div style='font-size:0.75rem;color:#aaa;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:8px'>Predicted Views (7 days)</div>
            <div style='font-size:3rem;font-weight:700;color:#ff0000'>{fmt(pred_views)}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: AI INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 💡 AI Insights")
    st.markdown("<span style='color:#aaa;font-size:0.85rem'>Powered by Gemma 4 via Fireworks AI · Results are cached for 24h</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        from features import get_all_patterns
        from insights_engine import get_upload_strategy, get_title_ideas, get_thumbnail_recommendations

        with st.spinner("Calculating patterns from your data..."):
            patterns = get_all_patterns()

        # Upload Strategy
        st.markdown('<p class="section-title">⏰ Upload Strategy</p>', unsafe_allow_html=True)
        if st.button("🤖 Generate Upload Strategy", key="btn_upload"):
            with st.spinner("Asking Gemma 4..."):
                strategy = get_upload_strategy(patterns)

            if "error" not in strategy:
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Optimal Schedule</div>
                        <div class="ai-card-content">{strategy.get('optimal_schedule','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Why It Works</div>
                        <div class="ai-card-content">{strategy.get('why_it_works','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">What to Avoid</div>
                        <div class="ai-card-content">{strategy.get('avoid','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                with col_s2:
                    st.markdown('<p class="section-title">Action Items</p>', unsafe_allow_html=True)
                    for action in strategy.get("action_items", []):
                        st.markdown(f'<div class="action-item">▶ {action}</div>', unsafe_allow_html=True)
                    if strategy.get("from_cache"):
                        st.markdown("<span style='color:#555;font-size:0.75rem'>⚡ From cache</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Title Ideas
        st.markdown('<p class="section-title">📝 Title Ideas</p>', unsafe_allow_html=True)
        topic_input = st.text_input("Topic (optional)", placeholder="e.g. fitness, gaming, cooking...")
        if st.button("🤖 Generate Title Ideas", key="btn_titles"):
            with st.spinner("Asking Gemma 4..."):
                titles = get_title_ideas(patterns, topic=topic_input)

            if "error" not in titles:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown('<p class="section-title">💡 Title Ideas</p>', unsafe_allow_html=True)
                    for i, title in enumerate(titles.get("title_ideas", []), 1):
                        st.markdown(f"""<div class="action-item">
                            <span style='color:#ff0000;font-weight:700'>{i}.</span> {title}
                        </div>""", unsafe_allow_html=True)
                with col_t2:
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Winning Formula</div>
                        <div class="ai-card-content">{titles.get('title_formula','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Key Insight</div>
                        <div class="ai-card-content">{titles.get('key_insight','N/A')}</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # Thumbnail Recommendations
        st.markdown('<p class="section-title">🖼️ Thumbnail Recommendations</p>', unsafe_allow_html=True)
        if st.button("🤖 Generate Thumbnail Tips", key="btn_thumb"):
            with st.spinner("Asking Gemma 4..."):
                thumb = get_thumbnail_recommendations(patterns)

            if "error" not in thumb:
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Expression / Subject</div>
                        <div class="ai-card-content">{thumb.get('expression','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Text Overlay</div>
                        <div class="ai-card-content">{thumb.get('text_overlay','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                with t2:
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Color Scheme</div>
                        <div class="ai-card-content">{thumb.get('colors','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Composition</div>
                        <div class="ai-card-content">{thumb.get('composition','N/A')}</div>
                    </div>""", unsafe_allow_html=True)
                with t3:
                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Why This Works</div>
                        <div class="ai-card-content">{thumb.get('reasoning','N/A')}</div>
                    </div>""", unsafe_allow_html=True)

        # Weak Video Analysis
        st.markdown("---")
        st.markdown('<p class="section-title">⚠️ Weak Video Analysis</p>', unsafe_allow_html=True)
        st.markdown("<span style='color:#aaa;font-size:0.85rem'>Select a video to analyze why it underperformed</span>", unsafe_allow_html=True)

        weak_data = patterns["weak_engagement"]["weak_videos"]
        if weak_data:
            weak_titles = [f"{v['title'][:50]}... ({v['avg_retention']}% retention)" for v in weak_data]
            selected_idx = st.selectbox("Select video", range(len(weak_titles)), format_func=lambda i: weak_titles[i])
            selected_video = weak_data[selected_idx]

            col_w1, col_w2 = st.columns([1, 2])
            with col_w1:
                st.markdown(f"""<div class="weak-card">
                    <div class="weak-card-title">{selected_video['title']}</div>
                    <div class="weak-metric">Retention: <span>{selected_video['avg_retention']}%</span></div>
                    <div class="weak-metric">Views: <span>{fmt(selected_video['total_views'])}</span></div>
                    <div class="weak-metric">Below avg by: <span>{selected_video['below_avg_by']}%</span></div>
                </div>""", unsafe_allow_html=True)

            with col_w2:
                if st.button("🤖 Analyze This Video", key="btn_weak"):
                    from insights_engine import analyze_weak_video
                    with st.spinner("Asking Gemma 4..."):
                        analysis = analyze_weak_video(
                            patterns=patterns,
                            video_title=selected_video["title"],
                            retention=selected_video["avg_retention"],
                            views=selected_video["total_views"],
                        )
                    if "error" not in analysis:
                        st.markdown(f"""<div class="ai-card">
                            <div class="ai-card-title">Retention Diagnosis</div>
                            <div class="ai-card-content">{analysis.get('retention_diagnosis','N/A')}</div>
                        </div>""", unsafe_allow_html=True)
                        st.markdown('<p class="section-title">Likely Reasons</p>', unsafe_allow_html=True)
                        for reason in analysis.get("likely_reasons", []):
                            st.markdown(f'<div class="action-item">⚠️ {reason}</div>', unsafe_allow_html=True)
                        st.markdown('<p class="section-title">Specific Fixes</p>', unsafe_allow_html=True)
                        for fix in analysis.get("specific_fixes", []):
                            st.markdown(f'<div class="action-item">✅ {fix}</div>', unsafe_allow_html=True)

    except ImportError:
        st.warning("⚠️ Set FIREWORKS_API_KEY in .env to enable AI insights")
    except Exception as e:
        st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: CHANNEL AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### 📈 Channel Audit & Growth Gaps")
    st.markdown("<span style='color:#aaa;font-size:0.85rem'>Complete channel health check powered by Gemma 4</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        from features import get_all_patterns
        from insights_engine import get_channel_audit

        if st.button("🤖 Run Full Channel Audit", key="btn_audit"):
            with st.spinner("Calculating patterns and asking Gemma 4..."):
                patterns = get_all_patterns()
                audit = get_channel_audit(patterns)

            if "error" not in audit:
                col_a1, col_a2 = st.columns([1, 2])

                with col_a1:
                    score = audit.get("channel_score", 0)
                    st.markdown(f"""
                    <div style='text-align:center;margin-bottom:20px'>
                        <div style='font-size:0.8rem;color:#aaa;margin-bottom:8px'>CHANNEL SCORE</div>
                        <div class="score-badge">{score}/10</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Traffic Diversity</div>
                        <div class="ai-card-content">{audit.get('traffic_diversity_score','N/A')}/10</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""<div class="ai-card">
                        <div class="ai-card-title">Content Mix Advice</div>
                        <div class="ai-card-content">{audit.get('content_mix_advice','N/A')}</div>
                    </div>""", unsafe_allow_html=True)

                with col_a2:
                    st.markdown('<p class="section-title">💪 Strengths</p>', unsafe_allow_html=True)
                    for s in audit.get("strengths", []):
                        st.markdown(f'<div class="action-item" style="border-left-color:#00aa00">✅ {s}</div>', unsafe_allow_html=True)

                    st.markdown('<p class="section-title">⚠️ Growth Gaps</p>', unsafe_allow_html=True)
                    for g in audit.get("growth_gaps", []):
                        st.markdown(f'<div class="action-item" style="border-left-color:#ffaa00">⚠️ {g}</div>', unsafe_allow_html=True)

                    st.markdown('<p class="section-title">🚀 Top 3 Actions</p>', unsafe_allow_html=True)
                    for i, action in enumerate(audit.get("top_3_actions", []), 1):
                        st.markdown(f'<div class="action-item">▶ <b style="color:#ff0000">{i}.</b> {action}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7: DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("### 🔍 Data Quality")
    st.markdown("<br>", unsafe_allow_html=True)

    @st.cache_data
    def run_quality_checks():
        conn = sqlite3.connect(DB_PATH)
        dup_metrics = pd.read_sql("SELECT COUNT(*) - COUNT(DISTINCT video_id || date) as dups FROM daily_metrics", conn).iloc[0,0]
        dup_traffic = pd.read_sql("SELECT COUNT(*) - COUNT(DISTINCT video_id || traffic_source_type) as dups FROM traffic_sources", conn).iloc[0,0]
        missing_vids = pd.read_sql("SELECT COUNT(*) as cnt FROM daily_metrics WHERE video_id NOT IN (SELECT video_id FROM videos)", conn).iloc[0,0]
        missing_dates = pd.read_sql("SELECT COUNT(*) as cnt FROM daily_metrics WHERE date IS NULL OR date = ''", conn).iloc[0,0]
        latest = pd.read_sql("SELECT MAX(fetched_at) as last FROM daily_metrics", conn).iloc[0,0]
        total_videos = pd.read_sql("SELECT COUNT(*) FROM videos", conn).iloc[0,0]
        total_metrics = pd.read_sql("SELECT COUNT(*) FROM daily_metrics", conn).iloc[0,0]
        total_traffic = pd.read_sql("SELECT COUNT(*) FROM traffic_sources", conn).iloc[0,0]
        conn.close()
        return dict(dup_metrics=dup_metrics, dup_traffic=dup_traffic, missing_vids=missing_vids,
                    missing_dates=missing_dates, latest=latest, total_videos=total_videos,
                    total_metrics=total_metrics, total_traffic=total_traffic)

    qc = run_quality_checks()

    dq1, dq2 = st.columns(2)
    with dq1:
        st.markdown('<p class="section-title">✅ Quality Checks</p>', unsafe_allow_html=True)
        checks = [
            (qc["dup_metrics"] == 0, f"No duplicate daily metric records ({qc['total_metrics']:,} rows)"),
            (qc["dup_traffic"] == 0, f"No duplicate traffic source records ({qc['total_traffic']:,} rows)"),
            (qc["missing_vids"] == 0, "No orphaned metric records"),
            (qc["missing_dates"] == 0, "No missing dates in daily metrics"),
            (qc["latest"] is not None, f"Latest ingestion: {qc['latest'][:16] if qc['latest'] else 'N/A'}"),
        ]
        for passed, msg in checks:
            icon = "✅" if passed else "❌"
            color = "#00aa00" if passed else "#ff4444"
            st.markdown(f"<span style='color:{color}'>{icon}</span> {msg}", unsafe_allow_html=True)

    with dq2:
        st.markdown('<p class="section-title">📦 Database Stats</p>', unsafe_allow_html=True)
        for label, val in [
            ("Videos", f"{qc['total_videos']:,}"),
            ("Daily metric rows", f"{qc['total_metrics']:,}"),
            ("Traffic source rows", f"{qc['total_traffic']:,}"),
            ("Estimated DB size", f"~{qc['total_metrics'] * 0.0002:.1f} MB"),
        ]:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:8px 0;"
                f"border-bottom:1px solid #272727'>"
                f"<span style='color:#aaa'>{label}</span>"
                f"<span style='color:#fff;font-weight:600'>{val}</span></div>",
                unsafe_allow_html=True
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<span style='color:#555;font-size:0.75rem'>"
    "▶ YouTube Growth Copilot · SQLite · Streamlit · Gemma 4 · AMD Developer Hackathon · Built by Mihai Catana"
    "</span>",
    unsafe_allow_html=True
)



