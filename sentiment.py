import sqlite3
from transformers import pipeline

print("Loading AI model...")
analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model loaded")

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
cursor.execute("SELECT id, headline FROM articles LIMIT 10")
articles = cursor.fetchall()
print(f"Got {len(articles)} articles")

cursor.execute("CREATE TABLE IF NOT EXISTS sentiment (id INTEGER PRIMARY KEY, article_id INTEGER, score REAL, label TEXT)")

scores = []
print("=" * 80)
for article_id, headline in articles:
    result = analyzer(headline[:512])[0]
    label = result["label"]
    confidence = result["score"]
    score = confidence if label == "POSITIVE" else -confidence
    scores.append((article_id, score, label))
    emoji = "up" if score > 0 else "down"
    print(f"{emoji} {score:.2f} ({label}) | {headline[:70]}")

print("=" * 80)

for article_id, score, label in scores:
    cursor.execute("INSERT OR REPLACE INTO sentiment (article_id, score, label) VALUES (?,?,?)", (article_id, score, label))
conn.commit()

cursor.execute("SELECT COUNT(CASE WHEN score > 0.2 THEN 1 END), COUNT(CASE WHEN score < -0.2 THEN 1 END), ROUND(AVG(score),2) FROM sentiment")
bullish, bearish, avg = cursor.fetchone()
conn.close()

print(f"Bullish: {bullish} | Bearish: {bearish} | Avg: {avg}")
print("PHASE 2 COMPLETE")
