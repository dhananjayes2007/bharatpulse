import requests, sqlite3

API_KEY = "87a13b1be1a34e0dbd3f4b86d4b3705e"

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, headline TEXT, source TEXT, date TEXT)")
conn.commit()
conn.close()
print("Step 1: Database ready")

response = requests.get("https://newsapi.org/v2/everything", params={"q":"RBI Governor","apiKey":API_KEY,"pageSize":10})
articles = response.json().get("articles",[])
print(f"Step 2: Got {len(articles)} articles")

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
for a in articles:
    try:
        cursor.execute("INSERT INTO articles (headline,source,date) VALUES (?,?,?)",(a["title"],a["source"]["name"],a["publishedAt"]))
    except:
        pass
conn.commit()
conn.close()
print("Step 3: Saved")

conn = sqlite3.connect("news.db")
cursor = conn.cursor()
cursor.execute("SELECT headline,source FROM articles LIMIT 5")
for i,(h,s) in enumerate(cursor.fetchall(),1):
    print(f"{i}. [{s}] {h}")
conn.close()
print("DONE")
