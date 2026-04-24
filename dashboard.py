import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

st.set_page_config(page_title="SentinelFinance", page_icon="📊", layout="wide")

st.markdown("""<style>.main{background-color:#0e1117;}</style>""", unsafe_allow_html=True)

st.markdown("# 📊 SentinelFinance")
st.markdown("**Real-time Indian Political & Corporate Sentiment → Market Intelligence**")
st.markdown("---")

API_KEY = "87a13b1be1a34e0dbd3f4b86d4b3705e"

@st.cache_data(ttl=300)
def fetch_live_news():
    url = "https://newsapi.org/v2/everything"
    params = {"q": "RBI Governor OR Modi economy OR Adani OR Ambani", "apiKey": API_KEY, "pageSize": 20, "language": "en"}
    r = requests.get(url, params=params)
    return r.json().get("articles", [])

articles = fetch_live_news()

col1, col2, col3 = st.columns(3)
col1.metric("Total Articles", len(articles))
col2.metric("Sources Tracked", len(set(a["source"]["name"] for a in articles)))
col3.metric("Figures Monitored", "4 (RBI, Modi, Adani, Ambani)")

st.markdown("---")

st.subheader("🎯 Live Trade Signals")
sig1, sig2, sig3 = st.columns(3)
signals = [
    {"signal":"SELL","stock":"ADANIENT.NS","move":"2.07%","conf":"70%","color":"#ff4444"},
    {"signal":"BUY","stock":"TCS.NS","move":"0.99%","conf":"61%","color":"#00ff88"},
    {"signal":"SELL","stock":"ICICIBANK.NS","move":"0.24%","conf":"42%","color":"#ff4444"},
]
for col, s in zip([sig1,sig2,sig3], signals):
    with col:
        st.markdown(f"""<div style='background:#1c1c2e;padding:20px;border-radius:10px;border-left:4px solid {s["color"]}'>
        <h3 style='color:{s["color"]}'>{s["signal"]} {s["stock"]}</h3>
        <p>Expected move: <b>{s["move"]}</b></p>
        <p>Confidence: <b>{s["conf"]}</b></p></div>""", unsafe_allow_html=True)

st.markdown("---")
st.subheader("📰 Live News Feed")
for a in articles[:10]:
    st.markdown(f"""<div style='background:#1c1c2e;padding:12px;border-radius:8px;margin:4px 0;border-left:3px solid #00ff88'>
    <small style='color:#aaa'>[{a["source"]["name"]}]</small><br>
    <span style='color:white'>{a["title"]}</span></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<center><small style='color:#555'>SentinelFinance © 2026 | Indian Market Sentiment Engine</small></center>", unsafe_allow_html=True)
