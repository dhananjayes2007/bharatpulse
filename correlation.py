import sqlite3
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Fetching stock prices...")

stocks_map = {
    "RBI": ["SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS"],
    "Modi": ["RELIANCE.NS", "TCS.NS"],
    "Ambani": ["RELIANCE.NS"],
    "Adani": ["ADANIGREEN.NS", "ADANIENT.NS"]
}

all_stocks = list(set([s for stocks in stocks_map.values() for s in stocks]))
print(f"Tracking {len(all_stocks)} stocks: {all_stocks}")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

stock_data = {}
for stock in all_stocks:
    print(f"  Downloading {stock}...", end=" ")
    try:
        df = yf.download(stock, start=start_date, end=end_date, progress=False, auto_adjust=True)
        stock_data[stock] = df
        print(f"got {len(df)} days")
    except Exception as e:
        print(f"error: {e}")

print(f"Downloaded {len(stock_data)} stocks")

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
cursor.execute("SELECT a.headline, a.date, s.score FROM articles a LEFT JOIN sentiment s ON a.id = s.article_id WHERE s.score IS NOT NULL")
rows = cursor.fetchall()
conn.close()
print(f"Got {len(rows)} scored articles")

daily_sentiment = {}
for headline, date_str, score in rows:
    try:
        date = date_str.split("T")[0]
        if date not in daily_sentiment:
            daily_sentiment[date] = []
        daily_sentiment[date].append(score)
    except:
        pass

print(f"Sentiment across {len(daily_sentiment)} dates")
print("=" * 60)

for stock, df in stock_data.items():
    if df.empty:
        continue
    df["return"] = df["Close"].pct_change() * 100
    dates = [str(d.date()) for d in df.index]
    returns = list(df["return"])
    
    matched_sent = []
    matched_ret = []
    for d, r in zip(dates, returns):
        if d in daily_sentiment and not pd.isna(r):
            matched_sent.append(sum(daily_sentiment[d])/len(daily_sentiment[d]))
            matched_ret.append(r)
    
    if len(matched_sent) >= 2:
        corr = np.corrcoef(matched_sent, matched_ret)[0,1]
        print(f"{stock}: correlation={corr:.3f} ({len(matched_sent)} matching days)")
    else:
        print(f"{stock}: not enough matching data points")

print("=" * 60)
print("PHASE 3A COMPLETE")
