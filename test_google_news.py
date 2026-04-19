#!/usr/bin/env python3
"""
Test if Google News RSS is working and returning articles for sample companies.
"""
import feedparser
from urllib.parse import quote
from datetime import datetime, timedelta

NEWS_SOURCES = [
    "inc42.com", "yourstory.com", "entrackr.com",
    "downtoearth.org.in", "moneycontrol.com",
    "economictimes.indiatimes.com"
]

def build_company_news_url(company_name: str) -> str:
    """Build Google News RSS URL."""
    site_queries = " OR ".join([f"site:{source}" for source in NEWS_SOURCES])
    query = f'"{company_name}" ({site_queries})'
    encoded_query = quote(query, safe='')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    return url

test_companies = ["Kreditbee", "Bachatt", "StockGro", "PhonePe"]

print("=" * 70)
print("🔍 GOOGLE NEWS RSS FEED TEST")
print("=" * 70)

for company in test_companies:
    print(f"\nTesting: {company}")
    url = build_company_news_url(company)
    print(f"  URL: {url[:80]}...")
    
    try:
        feed = feedparser.parse(url)
        print(f"  ✓ Feed parsed successfully")
        print(f"  📰 Articles found: {len(feed.entries)}")
        
        if feed.entries:
            print(f"  Recent articles (last 3):")
            for entry in feed.entries[:3]:
                title = entry.get('title', 'N/A')
                published = entry.get('published', 'N/A')
                print(f"    • {title[:60]}")
                print(f"      Published: {published}")
        else:
            print(f"  ⚠️  No articles returned by feed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)
