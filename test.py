# Run this standalone to see what Inc42 is actually publishing
import feedparser
feed = feedparser.parse("https://inc42.com/feed")
for entry in feed.entries[:10]:
    print(entry.get('title'))