"""
WHEN Layer - Component B: Signal Monitor
Continuously monitors existing prospects for changes and generates time-stamped events.
These monitoring_events feed into WHEN scoring with genuine temporal data.

Key insight: This runs on the universe of existing prospects (from WHO), not discovering new ones.
"""

import feedparser
import time
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from database import (
    get_db, record_monitoring_event, update_prospect_monitor_timestamp,
    get_all_prospects_for_monitoring
)

# Google News sources for company-specific monitoring
NEWS_SOURCES = [
    "inc42.com", "yourstory.com", "entrackr.com",
    "downtoearth.org.in", "moneycontrol.com",
    "economictimes.indiatimes.com"
]


def build_company_news_url(company_name: str) -> str:
    """
    Build a Google News RSS URL for company-specific search.
    Searches for recent articles specifically about a company.
    Properly URL-encodes the query to avoid control character errors.
    """
    # Build search query with site restrictions
    # Format: "Company Name" site:source1 OR site:source2 OR ...
    site_queries = " OR ".join([f"site:{source}" for source in NEWS_SOURCES])
    query = f'"{company_name}" ({site_queries})'
    
    # Properly encode the query
    encoded_query = quote(query, safe='')
    
    # Google News RSS with encoded query
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    return url


def monitor_company_news(prospect_name: str, prospect_id: int) -> int:
    """
    Search for recent news about a specific company.
    Generates monitoring events for substantial news in last 7 days.
    Deduplicates by source URL to prevent recording same article twice.
    Returns count of NEW events created (excludes deduplicated).
    
    NOTE: RSS feeds may have truncated summaries, so we trust that results
    from company-specific Google News search are relevant to the company.
    """
    new_events = 0
    
    try:
        url = build_company_news_url(prospect_name)
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  ❌ News error for {prospect_name}: {e}")
        return 0
    
    if not feed.entries:
        print(f"  ℹ️  {prospect_name}: No recent news")
        return 0
    
    print(f"  🔍 {prospect_name}: Checking {len(feed.entries)} articles...")
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    for entry in feed.entries[:20]:  # Check top 20 recent articles (was 10)
        try:
            title = entry.get('title', '')
            url = entry.get('link', '')
            summary = entry.get('summary', '')
            
            # Skip if we already have an event from this URL
            with get_db() as conn:
                existing = conn.execute(
                    "SELECT id FROM monitoring_events WHERE source_url = ?",
                    (url,)
                ).fetchone()
            if existing:
                continue
            
            # Parse article publish date
            published = entry.get('published_parsed')
            if published:
                article_date = datetime(*published[:6])
            else:
                article_date = datetime.now()
            
            # Only process articles from last 7 days
            if article_date < seven_days_ago:
                continue
            
            # Categorize the news
            # NOTE: Pass company_name but categorize_news no longer requires it in content
            event_type, urgency = categorize_news(title, summary, prospect_name)
            
            if event_type:
                event_date_str = article_date.strftime('%Y-%m-%d')
                
                # record_monitoring_event now returns bool (True if recorded, False if deduplicated)
                recorded = record_monitoring_event(
                    prospect_id=prospect_id,
                    event_type=event_type,
                    urgency=urgency,
                    title=f"{prospect_name}: {title[:80]}",
                    evidence=summary[:200],
                    source_url=url,
                    event_date=event_date_str
                )
                
                if recorded:
                    new_events += 1
                    print(f"    ✓ {event_type} ({urgency}): {title[:60]}")
                else:
                    print(f"    ⊘ {event_type} (already recorded): {title[:60]}")
            
            time.sleep(0.2)
            
        except Exception as e:
            print(f"    Error processing article: {e}")
            continue
    
    if new_events > 0:
        update_prospect_monitor_timestamp(prospect_id, 'news')
    
    return new_events


def categorize_news(title: str, summary: str, company_name: str) -> tuple:
    """
    Categorize news article by event type and urgency.
    SMARTER APPROACH: Trust Google News search results + look for event keywords.
    Company name is checked but NOT required (RSS summaries are often truncated).
    
    Strategy:
    1. Google News search is already company-specific (no generic articles)
    2. If we got this article from that search, it's about the company
    3. Just identify event type and urgency from keywords
    4. Company name in content is a confidence boost but not required
    
    Returns (event_type, urgency) or (None, None) if not a notable event.
    """
    content = (title + " " + summary).lower()
    name_lower = company_name.lower()
    company_in_content = name_lower in content

    # FUNDING — highest priority event (strong indicators)
    funding_rounds = ['series a', 'series b', 'series c', 'series d', 'series e',
                      'seed round', 'pre-series', 'seed funding', 'seed investment']
    funding_verbs = ['raises', 'raised', 'secures', 'secured', 'announces funding']
    
    # Also check for "funding" keyword explicitly in title or content
    has_funding_keyword = 'funding' in content or 'fundraising' in content
    
    has_round = any(term in content for term in funding_rounds)
    has_verb = any(term in content for term in funding_verbs)
    # Match amounts: $10 million, ₹100 crore, $80M, $80Mn, ₹50Cr, etc.
    has_amount = bool(re.search(r'[₹$£€]\s*\d+\s*(crore|cr|million|mn|m|billion|bn|b|lakh|lacs|k|thousand|t)', content))
    
    # Funding classification:
    # - If title/content says "Funding" → HIGH (company likely got funding)
    # - If verb + amount → HIGH
    # - If round terminology → HIGH
    if has_funding_keyword:
        return ("FUNDING", "HIGH")
    if (has_verb and has_amount) or has_round:
        return ("FUNDING", "HIGH")

    # PRODUCT_LAUNCH — new products, expansions
    launch_terms = ['launches', 'launched', 'introduces', 'introduces new',
                    'rolls out', 'unveils', 'announces new product',
                    'new feature', 'expands into', 'launches feature']
    fin_terms = ['fixed deposit', 'fd', 'savings', 'investment',
                 'credit', 'loan', 'banking', 'wealth', 'insurance', 'trading',
                 'mutual fund', 'stocks', 'payment', 'crypto', 'bitcoin']
    
    has_launch = any(t in content for t in launch_terms)
    has_fin = any(t in content for t in fin_terms)
    
    if has_launch and has_fin:
        return ("PRODUCT_LAUNCH", "HIGH")
    if has_launch and company_in_content:
        return ("PRODUCT_LAUNCH", "MEDIUM")

    # PARTNERSHIP — strategic alignments
    partnership_terms = ['partners with', 'partnership with',
                        'integrates with', 'ties up with', 'partners',
                        'integration', 'collaborates with', 'collaboration']
    has_partnership = any(t in content for t in partnership_terms)
    
    if has_partnership and company_in_content:
        return ("PARTNERSHIP", "MEDIUM")

    # LEADERSHIP_HIRE — team growth
    leadership_terms = ['appoints', 'appointed', 'names', 'hires',
                        'joins as', 'ceo', 'cto', 'cfo', 'chief',
                        'vp of', 'head of', 'director of']
    leadership_count = sum(1 for t in leadership_terms if t in content)
    
    if leadership_count >= 2 and company_in_content:
        return ("LEADERSHIP_HIRE", "MEDIUM")

    # Not enough signal
    return (None, None)



def check_play_store_changes(prospect_id: int, play_store_id: str, 
                             prospect_name: str, stored_description: str) -> int:
    """
    Check for changes in Play Store app description.
    Stores current description and flags changes as APP_UPDATE events.
    Returns count of new events created.
    """
    if not play_store_id:
        return 0
    
    try:
        from google_play_scraper import app as get_app_details
        details = get_app_details(play_store_id, lang='en', country='in')
        current_description = details.get('description', '')
    except Exception as e:
        print(f"  ⚠️  Play Store error for {prospect_name}: {e}")
        return 0
    
    if not current_description:
        return 0
    
    # If no stored description, this is first check
    if not stored_description:
        print(f"  ℹ️  {prospect_name}: First description stored")
        update_prospect_monitor_timestamp(prospect_id, 'description')
        return 0
    
    # Check if description changed
    if current_description == stored_description:
        print(f"  ℹ️  {prospect_name}: No description changes")
        return 0
    
    print(f"  📝 {prospect_name}: Description updated!")
    
    # Check if new products mentioned
    new_products = detect_new_products(
        stored_description,
        current_description
    )
    
    urgency = "HIGH" if new_products else "MEDIUM"
    
    product_mention = f"Added: {', '.join(new_products)}" if new_products else "Description changed"
    
    record_monitoring_event(
        prospect_id=prospect_id,
        event_type="APP_UPDATE",
        urgency=urgency,
        title=f"{prospect_name}: Play Store description updated",
        evidence=product_mention,
        source_url=f"https://play.google.com/store/apps/details?id={play_store_id}",
        event_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    # Update stored description
    from database import get_db
    with get_db() as conn:
        conn.execute(
            "UPDATE prospects SET description = ? WHERE id = ?",
            (current_description, prospect_id)
        )
        conn.commit()
    
    update_prospect_monitor_timestamp(prospect_id, 'description')
    return 1


def detect_new_products(old_desc: str, new_desc: str) -> list:
    """
    Detect new product keywords that appeared in updated description.
    """
    PRODUCT_KEYWORDS = {
        'FD': ['fixed deposit', 'fd', 'term deposit'],
        'RD': ['recurring deposit', 'rd', 'systematic savings'],
        'Bonds': ['bonds', 'fixed income', 'debentures'],
        'Stocks': ['stocks', 'equity', 'shares', 'trading'],
        'Mutual Funds': ['mutual fund', 'mf', 'sip'],
        'Insurance': ['insurance', 'protection', 'life cover'],
    }
    
    old_lower = (old_desc or '').lower()
    new_lower = (new_desc or '').lower()
    
    new_products = []
    
    for product, keywords in PRODUCT_KEYWORDS.items():
        old_has = any(kw in old_lower for kw in keywords)
        new_has = any(kw in new_lower for kw in keywords)
        
        # Product mentioned in new but not in old = new product
        if new_has and not old_has:
            new_products.append(product)
    
    return new_products


def run_full_monitoring() -> dict:
    """
    Run complete monitoring cycle on all in-universe prospects.
    Returns summary of monitoring events created.
    """
    print("\n📡 Starting prospect monitoring cycle...")
    
    prospects = get_all_prospects_for_monitoring()
    
    if not prospects:
        print("  No prospects to monitor")
        return {"news_events": 0, "description_events": 0, "total_prospects": 0}
    
    news_events = 0
    description_events = 0
    
    print(f"  Monitoring {len(prospects)} prospects...\n")
    
    for prospect in prospects:
        prospect_id = prospect['id']
        prospect_name = prospect['name']
        play_store_id = prospect['play_store_id']
        description = prospect['description']
        
        print(f"• {prospect_name}:")
        
        # Check for recent news
        news_count = monitor_company_news(prospect_name, prospect_id)
        news_events += news_count
        
        # Check for Play Store changes
        if play_store_id:
            desc_count = check_play_store_changes(
                prospect_id, play_store_id, prospect_name, description
            )
            description_events += desc_count
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Monitoring complete!")
    print(f"  News events: {news_events}")
    print(f"  Description changes: {description_events}")
    print(f"  Total events: {news_events + description_events}\n")
    
    return {
        "news_events": news_events,
        "description_events": description_events,
        "total_prospects": len(prospects)
    }


if __name__ == "__main__":
    result = run_full_monitoring()
    print(result)
