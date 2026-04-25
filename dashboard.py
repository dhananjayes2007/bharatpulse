import streamlit as st
import feedparser
import pandas as pd
import plotly.graph_objects as go
import re
import zoneinfo
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Netunim | Indian Market Sentiment", page_icon="📡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: #0a0a0f; color: #e8e8f0; }
.stApp { background-color: #0a0a0f; }
.netunim-header { text-align: center; padding: 2rem 0 1rem 0; }
.netunim-title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 3.2rem; letter-spacing: -1px; background: linear-gradient(135deg, #00ff88 0%, #00ccff 50%, #ff6b6b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; }
.netunim-sub { font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #555577; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px; }
.signal-card { border-radius: 12px; padding: 1.5rem; margin: 0.5rem 0; font-family: 'Space Mono', monospace; font-size: 0.85rem; }
.signal-bullish { background: linear-gradient(135deg, #0d2b1a, #0a1f14); border: 1px solid #00ff8844; color: #00ff88; }
.signal-bearish { background: linear-gradient(135deg, #2b0d0d, #1f0a0a); border: 1px solid #ff6b6b44; color: #ff6b6b; }
.signal-neutral { background: linear-gradient(135deg, #1a1a2b, #14141f); border: 1px solid #8888ff44; color: #aaaaff; }
.signal-label { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
.metric-box { background: #13131e; border: 1px solid #222240; border-radius: 10px; padding: 1rem 1.2rem; text-align: center; }
.metric-val { font-family: 'Space Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #00ff88; }
.metric-label { font-size: 0.7rem; color: #555577; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }
.news-card { background: #13131e; border: 1px solid #1e1e35; border-left: 3px solid; border-radius: 8px; padding: 1rem 1.2rem; margin: 0.5rem 0; font-size: 0.85rem; }
.news-card-bullish { border-left-color: #00ff88; }
.news-card-bearish { border-left-color: #ff6b6b; }
.news-card-neutral { border-left-color: #6666aa; }
.news-headline { color: #dde; font-weight: 600; margin-bottom: 4px; line-height: 1.4; }
.news-meta { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: #445; }
.news-score { font-family: 'Space Mono', monospace; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-top: 6px; }
.score-bull { background: #00ff8822; color: #00ff88; }
.score-bear { background: #ff6b6b22; color: #ff6b6b; }
.score-neut { background: #6666aa22; color: #aaaaff; }
.ticker-wrap { background: #0d0d18; border-top: 1px solid #1e1e35; border-bottom: 1px solid #1e1e35; padding: 0.6rem 0; font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #556; letter-spacing: 1px; }
.section-divider { border: none; border-top: 1px solid #1e1e35; margin: 1.5rem 0; }
.section-title { font-size: 0.7rem; font-family: 'Space Mono', monospace; letter-spacing: 3px; color: #444466; text-transform: uppercase; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Business Standard Markets": "https://www.business-standard.com/rss/markets-106.rss",
    "Moneycontrol News": "https://www.moneycontrol.com/rss/latestnews.xml",
    "LiveMint Markets": "https://www.livemint.com/rss/markets",
    "NSE/BSE – Google News": "https://news.google.com/rss/search?q=NSE+BSE+India+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
    "RBI India – Google News": "https://news.google.com/rss/search?q=RBI+India+monetary+policy&hl=en-IN&gl=IN&ceid=IN:en",
    "India Budget Economy": "https://news.google.com/rss/search?q=India+economy+budget+GDP&hl=en-IN&gl=IN&ceid=IN:en",
}

KEYWORDS_BULLISH = ["surge","rally","gain","bull","growth","profit","record","rise","jump","boost","positive","strong","beat","upgrade","buy","outperform","high","revenue","expansion","recovery","green","up","advance","buoyant","momentum","inflow","FII buying","rate cut","stimulus"]
KEYWORDS_BEARISH = ["fall","drop","crash","bear","loss","sell","decline","plunge","weak","negative","miss","downgrade","underperform","low","recession","inflation","crisis","concern","risk","warning","outflow","FII selling","rate hike","slump","correction","volatility","tension","ban","fine","fraud"]
KEYWORDS_ENTITIES = ["Nifty","Sensex","NSE","BSE","RBI","SEBI","Modi","Ambani","Adani","TCS","Infosys","Reliance","HDFC","SBI","Wipro","Bajaj","Tata","budget","FII","DII","rupee","crude","gold"]


HF_TOKEN = st.secrets.get("HF_TOKEN", "")
HF_API_URL = "https://api-inference.huggingface.co/pipeline/text-classification/ProsusAI/finbert"

def finbert_sentiment(texts):
    try:
        import requests as req
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = req.post(HF_API_URL, headers=headers, json={"inputs": texts}, timeout=15)
        results = response.json()
        sentiments = []
        for r in results:
            if isinstance(r, list):
                top = max(r, key=lambda x: x["score"])
                label = top["label"].upper()
                score = top["score"]
                if label == "POSITIVE":
                    sentiments.append(("BULLISH", round(score, 3)))
                elif label == "NEGATIVE":
                    sentiments.append(("BEARISH", round(-score, 3)))
                else:
                    sentiments.append(("NEUTRAL", 0.0))
            else:
                sentiments.append(("NEUTRAL", 0.0))
        return sentiments
    except:
        return None

def score_sentiment(text):
    text_lower = text.lower()
    bull_hits = sum(1 for w in KEYWORDS_BULLISH if w in text_lower)
    bear_hits = sum(1 for w in KEYWORDS_BEARISH if w in text_lower)
    total = bull_hits + bear_hits
    if total == 0:
        return "NEUTRAL", 0.0
    raw = (bull_hits - bear_hits) / total
    if raw > 0.15:
        return "BULLISH", round(raw, 3)
    elif raw < -0.15:
        return "BEARISH", round(raw, 3)
    else:
        return "NEUTRAL", round(raw, 3)

def extract_entities(text):
    found = [e for e in KEYWORDS_ENTITIES if e.lower() in text.lower()]
    return ", ".join(found[:4]) if found else "General Market"

def parse_date(entry):
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*entry.published_parsed[:6]).strftime("%d %b %H:%M")
            except:
                return val[:16]
    return "—"

def fetch_market_prices():
    try:
        nifty = yf.Ticker("^NSEI")
        sensex = yf.Ticker("^BSESN")
        nifty_price = round(nifty.fast_info['lastPrice'], 2)
        sensex_price = round(sensex.fast_info['lastPrice'], 2)
        nifty_prev = round(nifty.fast_info['previousClose'], 2)
        sensex_prev = round(sensex.fast_info['previousClose'], 2)
        nifty_chg = round(((nifty_price - nifty_prev) / nifty_prev) * 100, 2)
        sensex_chg = round(((sensex_price - sensex_prev) / sensex_prev) * 100, 2)
        return nifty_price, nifty_chg, sensex_price, sensex_chg
    except:
        return None, None, None, None

@st.cache_data(ttl=180)
def fetch_all_news():
    articles = []
    raw_articles = []
    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                title = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "")
                full_text = f"{title} {summary}"
                clean = re.sub(r"<[^>]+>", " ", full_text)
                entities = extract_entities(clean)
                raw_articles.append({"headline": title[:140], "source": source, "date": parse_date(entry), "link": getattr(entry, "link", "#"), "entities": entities, "clean": clean})
        except:
            continue

    texts = [a["clean"][:512] for a in raw_articles]
    finbert_results = finbert_sentiment(texts)

    for i, art in enumerate(raw_articles):
        if finbert_results and i < len(finbert_results):
            sentiment, score = finbert_results[i]
        else:
            sentiment, score = score_sentiment(art["clean"])
        articles.append({"headline": art["headline"], "source": art["source"], "date": art["date"], "link": art["link"], "entities": art["entities"], "sentiment": sentiment, "score": score})

    return articles

def compute_signal(articles):
    if not articles:
        return "NEUTRAL", 0, 0, 0
    bull = sum(1 for a in articles if a["sentiment"] == "BULLISH")
    bear = sum(1 for a in articles if a["sentiment"] == "BEARISH")
    neut = sum(1 for a in articles if a["sentiment"] == "NEUTRAL")
    total = len(articles)
    avg_score = sum(a["score"] for a in articles) / total
    if avg_score > 0.12 and bull / total > 0.45:
        signal = "BULLISH"
    elif avg_score < -0.12 and bear / total > 0.45:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"
    return signal, bull, bear, neut

def make_gauge(avg_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(avg_score * 100, 1),
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Sentiment Index", "font": {"color": "#888899", "size": 13, "family": "Space Mono"}},
        number={"font": {"color": "#e8e8f0", "size": 28, "family": "Space Mono"}},
        gauge={"axis": {"range": [-100, 100]}, "bar": {"color": "#00ff88" if avg_score >= 0 else "#ff6b6b", "thickness": 0.3}, "bgcolor": "#13131e", "borderwidth": 0,
               "steps": [{"range": [-100, -30], "color": "#2b0d0d"}, {"range": [-30, 30], "color": "#13131e"}, {"range": [30, 100], "color": "#0d2b1a"}]}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=20, r=20, t=40, b=10))
    return fig

def make_donut(bull, bear, neut):
    fig = go.Figure(go.Pie(
        labels=["Bullish", "Bearish", "Neutral"], values=[bull, bear, neut], hole=0.65,
        marker=dict(colors=["#00ff88", "#ff6b6b", "#444466"]),
        textfont=dict(family="Space Mono", size=11, color="#e8e8f0"),
        hovertemplate="%{label}: %{value} articles<extra></extra>",
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True,
        legend=dict(font=dict(color="#888899", size=10, family="Space Mono"), bgcolor="rgba(0,0,0,0)"),
        height=220, margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f"<b>{bull+bear+neut}</b><br>articles", x=0.5, y=0.5, font_size=16, showarrow=False, font=dict(color="#e8e8f0", family="Space Mono"))])
    return fig

def make_timeline(articles):
    df = pd.DataFrame(articles)
    fig = go.Figure()
    for sentiment, color in [("BULLISH", "#00ff88"), ("BEARISH", "#ff6b6b"), ("NEUTRAL", "#6666aa")]:
        sub = df[df["sentiment"] == sentiment]
        fig.add_trace(go.Scatter(x=list(range(len(sub))), y=sub["score"].tolist(), mode="markers", name=sentiment,
            marker=dict(color=color, size=8, opacity=0.8),
            hovertemplate="<b>%{customdata}</b><br>Score: %{y:.3f}<extra></extra>",
            customdata=sub["headline"].str[:60].tolist()))
    fig.add_hline(y=0, line_dash="dot", line_color="#333355", line_width=1)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(gridcolor="#1e1e35", color="#444466", tickfont=dict(family="Space Mono", size=9)),
        legend=dict(font=dict(color="#888899", size=10, family="Space Mono"), bgcolor="rgba(0,0,0,0)"),
        height=180, margin=dict(l=40, r=20, t=10, b=10))
    return fig

def main():
    st.markdown("""
    <div class="netunim-header">
        <div class="netunim-title">NETUNIM</div>
        <div class="netunim-sub">Indian Market Sentiment Intelligence · Real-Time</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Scanning Indian market feeds..."):
        articles = fetch_all_news()

    if not articles:
        st.error("Could not load feeds. Check your internet connection.")
        return

    signal, bull, bear, neut = compute_signal(articles)
    avg_score = sum(a["score"] for a in articles) / len(articles)
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y · %H:%M IST")

    st.markdown(f"""
    <div class="ticker-wrap">
        &nbsp;&nbsp;🟢 LIVE &nbsp;·&nbsp; {now} &nbsp;·&nbsp; {len(articles)} articles scanned
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    nifty_price, nifty_chg, sensex_price, sensex_chg = fetch_market_prices()
    pc1, pc2 = st.columns(2)
    with pc1:
        if nifty_price:
            color = "#00ff88" if nifty_chg >= 0 else "#ff6b6b"
            arrow = "▲" if nifty_chg >= 0 else "▼"
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{color}">₹{nifty_price:,}</div><div class="metric-label">NIFTY 50 {arrow} {nifty_chg}%</div></div>', unsafe_allow_html=True)
    with pc2:
        if sensex_price:
            color2 = "#00ff88" if sensex_chg >= 0 else "#ff6b6b"
            arrow2 = "▲" if sensex_chg >= 0 else "▼"
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{color2}">₹{sensex_price:,}</div><div class="metric-label">SENSEX {arrow2} {sensex_chg}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_sig, col_gauge, col_donut = st.columns([1.2, 1, 1])
    with col_sig:
        signal_classes = {
            "BULLISH": ("signal-bullish", "📈 BULLISH", "Momentum favors buyers. Watch for breakout setups on Nifty/Sensex."),
            "BEARISH": ("signal-bearish", "📉 BEARISH", "Selling pressure elevated. Caution on fresh longs. Consider hedges."),
            "NEUTRAL": ("signal-neutral", "⏸ NEUTRAL", "Mixed signals. Wait for direction. Avoid overexposure."),
        }
        css_class, label, advice = signal_classes[signal]
        top_headlines = [a["headline"] for a in articles if a["sentiment"] == signal][:3]
        driven_by = " · ".join([h[:50] for h in top_headlines]) if top_headlines else "Mixed signals"
        st.markdown(f"""
        <div class="signal-card {css_class}">
            <div class="signal-label">{label}</div>
            <div style="font-size:0.8rem; margin-bottom:0.5rem; opacity:0.85;">{advice}</div>
            <div style="font-size:0.7rem; opacity:0.6; margin-bottom:0.5rem;">DRIVEN BY: {driven_by}</div>
            <div style="opacity:0.5; font-size:0.68rem;">TRADE SIGNAL · AUTO-GENERATED · NOT FINANCIAL ADVICE</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#00ff88">{bull}</div><div class="metric-label">Bullish</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#ff6b6b">{bear}</div><div class="metric-label">Bearish</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#aaaaff">{neut}</div><div class="metric-label">Neutral</div></div>', unsafe_allow_html=True)

    with col_gauge:
        st.plotly_chart(make_gauge(avg_score), use_container_width=True, config={"displayModeBar": False})
    with col_donut:
        st.plotly_chart(make_donut(bull, bear, neut), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<hr class="section-divider"><div class="section-title">Sentiment Scatter · All Articles</div>', unsafe_allow_html=True)
    st.plotly_chart(make_timeline(articles), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<hr class="section-divider"><div class="section-title">Live News Feed</div>', unsafe_allow_html=True)
    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        sentiment_filter = st.selectbox("Filter", ["ALL", "BULLISH", "BEARISH", "NEUTRAL"], label_visibility="collapsed")
    with filter_col2:
        source_filter = st.selectbox("Source", ["ALL SOURCES"] + list(FEEDS.keys()), label_visibility="collapsed")

    filtered = articles
    if sentiment_filter != "ALL":
        filtered = [a for a in filtered if a["sentiment"] == sentiment_filter]
    if source_filter != "ALL SOURCES":
        filtered = [a for a in filtered if a["source"] == source_filter]

    for art in filtered:
        s = art["sentiment"]
        css = {"BULLISH": "news-card-bullish", "BEARISH": "news-card-bearish", "NEUTRAL": "news-card-neutral"}[s]
        score_css = {"BULLISH": "score-bull", "BEARISH": "score-bear", "NEUTRAL": "score-neut"}[s]
        score_label = f"{'▲' if s == 'BULLISH' else '▼' if s == 'BEARISH' else '—'} {s}  {art['score']:+.3f}"
        st.markdown(f"""
        <div class="news-card {css}">
            <div class="news-headline"><a href="{art['link']}" target="_blank" style="color:inherit;text-decoration:none;">{art['headline']}</a></div>
            <div class="news-meta">{art['source']} · {art['date']} · 🏷 {art['entities']}</div>
            <span class="news-score {score_css}">{score_label}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <br><hr class="section-divider">
    <div style="text-align:center; font-family: 'Space Mono', monospace; font-size:0.65rem; color:#333355; padding-bottom:2rem;">
        NETUNIM · Sentiment Intelligence for Indian Markets · Not Financial Advice
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Feed"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()
