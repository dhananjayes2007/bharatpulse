"""
BHARATPULSE PHASE 4: STREAMLIT DASHBOARD
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="BharatPulse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .title-text {
        font-size: 42px;
        font-weight: bold;
        color: #00ff88;
    }
    </style>
""", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("news.db")

def fetch_articles():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT 
            a.id,
            a.headline,
            a.source,
            a.date,
            s.score,
            s.label
        FROM articles a
        LEFT JOIN sentiment s ON a.id = s.article_id
        ORDER BY a.date DESC
    """, conn)
    conn.close()
    return df

def fetch_sentiment_summary():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT 
            s.label,
            COUNT(*) as total_articles,
            ROUND(AVG(s.score), 3) as avg_sentiment,
            COUNT(CASE WHEN s.score > 0.2 THEN 1 END) as bullish,
            COUNT(CASE WHEN s.score < -0.2 THEN 1 END) as bearish
        FROM articles a
        LEFT JOIN sentiment s ON a.id = s.article_id
        WHERE s.score IS NOT NULL
        GROUP BY s.label
    """, conn)
    conn.close()
    return df

# HEADER
st.markdown('<p class="title-text">📊 BharatPulse</p>', unsafe_allow_html=True)
st.markdown("**Real-time Indian Political & Corporate Sentiment → Market Intelligence**")
st.markdown("---")

# SIDEBAR
st.sidebar.title("🎛️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()

# FETCH DATA
df_articles = fetch_articles()
df_summary = fetch_sentiment_summary()

# SECTION 1: METRICS
st.subheader("📈 Sentiment Overview")
col1, col2, col3 = st.columns(3)
total = len(df_articles)
bullish = len(df_articles[df_articles['score'] > 0.2]) if 'score' in df_articles else 0
bearish = len(df_articles[df_articles['score'] < -0.2]) if 'score' in df_articles else 0

col1.metric("Total Articles", total)
col2.metric("📈 Bullish", bullish)
col3.metric("📉 Bearish", bearish)

st.markdown("---")

# SECTION 2: SENTIMENT CHART
st.subheader("📊 Sentiment Distribution")
if len(df_summary) > 0:
    fig_bar = px.bar(
        df_summary,
        x='label',
        y='avg_sentiment',
        color='avg_sentiment',
        color_continuous_scale=['#ff4444', '#ffaa00', '#00ff88'],
        title="Average Sentiment Score by Label",
        labels={'avg_sentiment': 'Sentiment Score', 'label': 'Label'}
    )
    fig_bar.update_layout(
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        font_color='white',
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# SECTION 3: TRADE SIGNALS
st.subheader("🎯 Live Trade Signals")
trade_signals = [
    {"signal": "SELL", "stock": "ADANIENT.NS", "figure": "Adani", "move": "2.07%", "lag": "1 day", "confidence": "70%"},
    {"signal": "BUY", "stock": "TCS.NS", "figure": "Modi", "move": "0.99%", "lag": "1 day", "confidence": "61%"},
    {"signal": "SELL", "stock": "ICICIBANK.NS", "figure": "RBI", "move": "0.24%", "lag": "1 day", "confidence": "42%"},
]
sig_col1, sig_col2, sig_col3 = st.columns(3)
sig_cols = [sig_col1, sig_col2, sig_col3]
for i, signal in enumerate(trade_signals):
    with sig_cols[i]:
        color = "#00ff88" if signal['signal'] == "BUY" else "#ff4444"
        st.markdown(f"""
        <div style='background-color:#1c1c2e; padding:20px; border-radius:10px; border-left: 4px solid {color}'>
            <h3 style='color:{color}'>{signal['signal']} {signal['stock']}</h3>
            <p>📌 Triggered by: <b>{signal['figure']}</b></p>
            <p>📊 Expected move: <b>{signal['move']}</b></p>
            <p>⏱️ Lag time: <b>{signal['lag']}</b></p>
            <p>🎯 Confidence: <b>{signal['confidence']}</b></p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# SECTION 4: NEWS FEED
st.subheader("📰 Latest News Feed")
for idx, row in df_articles.head(10).iterrows():
    score = row['score'] if row['score'] is not None else 0
    label = row['label'] if row['label'] is not None else "NEUTRAL"
    color = "#00ff88" if score > 0.2 else "#ff4444" if score < -0.2 else "#ffaa00"
    emoji = "📈" if score > 0.2 else "📉" if score < -0.2 else "➡️"
    col_news, col_score = st.columns([4, 1])
    with col_news:
        st.markdown(f"""
        <div style='background-color:#1c1c2e; padding:12px; border-radius:8px; margin:4px 0; border-left: 3px solid {color}'>
            <small style='color:#aaaaaa'>[{row['source']}] {row['date']}</small><br>
            <span style='color:white'>{row['headline']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_score:
        st.markdown(f"""
        <div style='background-color:#1c1c2e; padding:12px; border-radius:8px; margin:4px 0; text-align:center'>
            <span style='color:{color}; font-size:20px'>{emoji}</span><br>
            <span style='color:{color}; font-weight:bold'>{score:.2f}</span><br>
            <small style='color:#aaaaaa'>{label}</small>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# SECTION 5: TREND
st.subheader("📉 Sentiment Trend Over Time")
if len(df_articles) > 0 and 'score' in df_articles:
    df_articles['date'] = pd.to_datetime(df_articles['date'], errors='coerce')
    df_trend = df_articles.groupby('date')['score'].mean().reset_index()
    if len(df_trend) > 0:
        fig_line = px.line(
            df_trend,
            x='date',
            y='score',
            title="Sentiment Trend Over Time",
            labels={'score': 'Avg Sentiment', 'date': 'Date'}
        )
        fig_line.update_layout(
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font_color='white'
        )
        fig_line.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")
st.markdown(
    "<center><small style='color:#555'>BharatPulse © 2026 | Real-time Indian Market Sentiment Engine | Built for Seed Pitch</small></center>",
    unsafe_allow_html=True
)
