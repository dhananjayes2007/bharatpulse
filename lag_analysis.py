import sqlite3
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("PHASE 3B: LAG TIME ANALYSIS")

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
cursor.execute("SELECT a.date, s.score FROM articles a LEFT JOIN sentiment s ON a.id = s.article_id WHERE s.score IS NOT NULL")
rows = cursor.fetchall()
conn.close()
print("Got " + str(len(rows)) + " sentiment events")

events_by_date = {}
for date_str, score in rows:
    date = date_str.split("T")[0]
    if date not in events_by_date:
        events_by_date[date] = []
    events_by_date[date].append(score)

end_date = datetime.now()
start_date = end_date - timedelta(days=40)
all_stocks = ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","RELIANCE.NS","TCS.NS","ADANIENT.NS"]
stock_prices = {}
for stock in all_stocks:
    print("  Downloading " + stock)
    try:
        df = yf.download(stock, start=start_date, end=end_date, progress=False, auto_adjust=True)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        stock_prices[stock] = df
    except Exception as e:
        print("  Error: " + str(e))

print("=" * 60)
lag_results = []
for stock, df in stock_prices.items():
    if df.empty:
        continue
    closes = df["Close"].squeeze()
    rets = closes.pct_change() * 100
    for lag in [0, 1]:
        sv, rv = [], []
        for i, idx in enumerate(df.index):
            sd = str((idx - timedelta(days=lag)).date())
            ret_val = float(rets.iloc[i])
            if sd in events_by_date and not np.isnan(ret_val):
                sv.append(sum(events_by_date[sd])/len(events_by_date[sd]))
                rv.append(ret_val)
        if len(sv) >= 2:
            corr = np.corrcoef(sv, rv)[0,1]
            avg_ret = np.mean(rv)
            if not np.isnan(corr):
                lag_results.append({"stock":stock,"lag":lag,"corr":corr,"avg_ret":avg_ret,"n":len(sv)})
                print(stock + " lag=" + str(lag) + "d corr=" + str(round(corr,3)) + " avg_move=" + str(round(avg_ret,2)) + "% n=" + str(len(sv)))

print("=" * 60)
if lag_results:
    best = sorted(lag_results, key=lambda x: abs(x["corr"]), reverse=True)[:3]
    print("TOP SIGNALS:")
    for r in best:
        signal = "BUY" if r["corr"] > 0 else "SELL"
        print("  " + signal + " " + r["stock"] + ": moves " + str(round(r["avg_ret"],2)) + "% at lag " + str(r["lag"]) + "d (corr=" + str(round(r["corr"],3)) + " n=" + str(r["n"]) + ")")
print("PHASE 3B COMPLETE")
