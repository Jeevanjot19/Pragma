#!/usr/bin/env python3
"""
Test categorize_news on actual Google News articles.
"""
import feedparser
from urllib.parse import quote
from discovery.company_monitor import categorize_news
from datetime import datetime, timedelta

NEWS_SOURCES = [
    "inc42.com", "yourstory.com", "entrackr.com",
    "downtoearth.org.in", "moneycontrol.com",
    "economictimes.indiatimes.com"
]

def build_company_news_url(company_name: str) -> str:
    site_queries = " OR ".join([f"site:{source}" for source in NEWS_SOURCES])
    query = f'"{company_name}" ({site_queries})'
    encoded_query = quote(query, safe='')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    return url

test_companies = ["Bachatt", "Kreditbee"]

print("=" * 70)
print("🔍 CATEGORIZE_NEWS TEST ON REAL ARTICLES")
print("=" * 70)

for company in test_companies:
    print(f"\n{company}:")
    url = build_company_news_url(company)
    feed = feedparser.parse(url)
    
    print(f"  Total articles: {len(feed.entries)}")
    
    categorized = 0
    skipped = 0
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    for entry in feed.entries[:10]:  # Test first 10
        title = entry.get('title', '')
        summary = entry.get('summary', '')
        published = entry.get('published_parsed')
        
        if published:
            article_date = datetime(*published[:6])
        else:
            article_date = datetime.now()
        
        if article_date < seven_days_ago:
            continue
            
        event_type, urgency = categorize_news(title, summary, company)
        
        if event_type:
            categorized += 1
            print(f"  ✓ {event_type:20} {title[:50]}")
        else:
            skipped += 1
            # Show why it was skipped
            content = (title + " " + summary).lower()
            company_lower = company.lower()
            
            if company_lower not in content:
                reason = "company name not found"
            else:
                reason = "no event keywords"
            
            print(f"  ✗ [{reason:25}] {title[:40]}")
    
    print(f"  Summary: {categorized} categorized, {skipped} skipped")

print("\n" + "=" * 70)
