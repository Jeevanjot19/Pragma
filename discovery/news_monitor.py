import feedparser
import time
import logging
from datetime import datetime
from database import (
    upsert_prospect, add_signal, is_article_processed,
    mark_article_processed, get_prospect_by_name
)
from intelligence.llm_extractor import (
    determine_recommended_product, batch_extract_companies
)
from config import EXISTING_PARTNERS, COMPETITORS, NON_PROSPECTS

# Setup logging for discovery pipeline
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DISCOVERY - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google News RSS with keyword search
# Format: https://news.google.com/rss/search?q=QUERY&hl=en-IN&gl=IN&ceid=IN:en
# This searches Google News for India-specific results

GOOGLE_NEWS_QUERIES = [
    # Funding signals — companies with money to spend on new products
    "Indian fintech startup raises funding",
    "India neobank series funding",
    "India payment app raises",
    "India wealthtech investment funding",
    "India savings app funding round",

    # Product launch signals — companies expanding into banking products
    "India fintech launches fixed deposit",
    "India app adds savings product",
    "India fintech banking product launch",
    "India investment platform new product",

    # Partnership signals — competitor integrations
    "fintech India banking infrastructure partnership",
    "India app Stable Money integration",
    "India platform GoldenPi",

    # Expansion signals — companies growing
    "India fintech product expansion 2026",
    "India broker adds investment product",
]

def build_google_news_url(query: str) -> str:
    """Build a Google News RSS URL for a specific query."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"


def is_worth_processing(title: str, summary: str) -> bool:
    """
    Quick pre-filter before calling LLM.
    Since we're already using targeted queries, 
    this is a light filter just to catch obvious irrelevant results.
    """
    # Skip if clearly not about Indian fintech
    skip_keywords = [
        'crypto', 'bitcoin', 'ethereum', 'nft', 'blockchain',
        'us stocks', 'wall street', 'federal reserve',
        'pakistan', 'bangladesh', 'china', 'usa fintech',
        'e-commerce', 'edtech', 'healthtech', 'agritech',
        'real estate', 'proptech', 'gaming', 'esports'
    ]
    text = (title + ' ' + summary).lower()
    if any(kw in text for kw in skip_keywords):
        return False
    return True


def detect_competitor_in_text(title: str, summary: str) -> str | None:
    """Check if article mentions a Blostem competitor."""
    text = (title + ' ' + summary).lower()
    for competitor in COMPETITORS:
        if competitor.lower() in text:
            if any(kw in text for kw in [
                'powered by', 'partnership', 'integration',
                'launched with', 'using', 'integrates'
            ]):
                return competitor
    return None


def _process_extracted_company(extracted: dict, url: str, title: str, article_date: str) -> int:
    """Process a single extracted company and create signals. Returns 1 if added, 0 otherwise."""
    if not extracted or not extracted.get('is_relevant', False):
        return 0
    
    company_name = extracted.get('company_name') or ''
    company_name = company_name.strip()
    
    if not company_name or len(company_name) < 2:
        return 0

    # Skip garbage names
    if company_name in ['None', 'None mentioned', 'N/A', 'Unknown', '']:
        return 0

    # Skip non-prospects (regulatory bodies, generic terms, etc.)
    if any(np.lower() == company_name.lower() for np in NON_PROSPECTS):
        print(f"  Skipped non-prospect: {company_name}")
        logger.debug(f"Skipped non-prospect: {company_name}")
        return 0

    # Skip existing Blostem partners
    if any(p.lower() in company_name.lower() or 
           company_name.lower() in p.lower() 
           for p in EXISTING_PARTNERS):
        print(f"  Skipped existing partner: {company_name}")
        logger.debug(f"Skipped existing partner: {company_name}")
        return 0

    # Check for competitor
    competitor = None
    is_competitor = any(c.lower() in company_name.lower() or 
                        company_name.lower() in c.lower() 
                        for c in COMPETITORS)
    if is_competitor:
        print(f"  Skipped competitor: {company_name}")
        logger.debug(f"Skipped competitor: {company_name}")
        return 0

    # Build prospect
    current_products = extracted.get('current_products', [])
    category = extracted.get('company_category', 'other')
    recommended = determine_recommended_product(category, current_products)

    prospect_data = {
        'name': company_name,
        'category': category,
        'has_fd': 'FD' in current_products,
        'has_rd': 'RD' in current_products,
        'has_bonds': 'bonds' in current_products,
        'has_upi_credit': 'UPI_credit' in current_products,
        'has_mutual_funds': 'mutual_funds' in current_products,
        'has_stocks': 'stocks' in current_products,
        'has_insurance': 'insurance' in current_products,
        'recommended_product': recommended,
        'using_competitor': competitor,
        'is_existing_partner': False,
        'source': 'google_news'
    }

    upsert_prospect(prospect_data)

    # Get ID for signals
    prospect = get_prospect_by_name(company_name)
    if not prospect:
        return 0
    prospect_id = prospect['id']

    # Add signals
    expansion = extracted.get('expansion_signals', [])

    # Product gap
    add_signal(
        prospect_id=prospect_id,
        signal_type='PRODUCT_GAP',
        strength='HIGH',
        title=f"{company_name} needs {recommended}",
        evidence=extracted.get('signal_summary', ''),
        source_url=url
    )

    # Funding + expansion
    if extracted.get('funding_detected') and expansion:
        add_signal(
            prospect_id=prospect_id,
            signal_type='FUNDING_EXPANSION',
            strength='HIGH',
            title=f"Raised {extracted.get('funding_amount', 'funding')}, plans to add {', '.join(expansion)}",
            evidence=title,
            source_url=url
        )

    # Leadership hire
    if extracted.get('leadership_hire') and extracted.get('leadership_role'):
        add_signal(
            prospect_id=prospect_id,
            signal_type='LEADERSHIP_HIRE',
            strength='MEDIUM',
            title=f"New {extracted.get('leadership_role')} hired at {company_name}",
            evidence=title,
            source_url=url
        )

    # Competitor displacement
    if extracted.get('competitor_mentioned'):
        add_signal(
            prospect_id=prospect_id,
            signal_type='DISPLACEMENT',
            strength='HIGH',
            title=f"Using {extracted.get('competitor_mentioned')} — displacement opportunity",
            evidence=title,
            source_url=url
        )

    print(f"  ✓ {company_name} ({category}) → {recommended}")
    logger.info(f"✓ Added {company_name} ({category}) → {recommended}")
    return 1


def process_query_batch(query: str, feed_url: str) -> int:
    """Process one Google News query with batched LLM calls."""
    new_count = 0
    logger.info(f"Processing query: {query}")

    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Error fetching '{query}': {e}")
        return 0

    # Collect unprocessed articles first
    unprocessed = []
    for entry in feed.entries[:10]:
        url = entry.get('link', '')
        title = entry.get('title', '')
        summary = entry.get('summary', entry.get('description', ''))
        
        if is_article_processed(url):
            continue
        if not is_worth_processing(title, summary):
            mark_article_processed(url, title)
            continue
            
        pub_date = entry.get('published_parsed')
        article_date_str = None
        if pub_date:
            try:
                import time as time_module
                article_date_str = time_module.strftime(
                    '%Y-%m-%d %H:%M:%S', pub_date
                )
            except Exception:
                pass
        
        unprocessed.append({
            'url': url,
            'title': title,
            'summary': summary,
            'article_date': article_date_str
        })

    if not unprocessed:
        return 0

    # ONE LLM call for all articles in this query
    extracted_list = batch_extract_companies(unprocessed)
    
    # Mark all as processed
    for article in unprocessed:
        mark_article_processed(article['url'], article['title'])

    # Process each extraction result
    for i, extracted in enumerate(extracted_list):
        if i >= len(unprocessed):
            break
        article = unprocessed[i]
        new_count += _process_extracted_company(
            extracted, 
            article['url'],
            article['title'],
            article.get('article_date')
        )
        time.sleep(0.2)

    return new_count


def run_news_monitor() -> dict:
    """Run all Google News queries. Returns comprehensive results."""
    start_time = datetime.now()
    logger.info("="*80)
    logger.info(f"🔍 STARTING NEWS DISCOVERY PIPELINE")
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Number of queries: {len(GOOGLE_NEWS_QUERIES)}")
    logger.info("="*80)
    
    total_new = 0
    total_signals = 0
    total_skipped = 0
    all_companies = []
    failed_queries = []

    for query in GOOGLE_NEWS_QUERIES:
        url = build_google_news_url(query)
        new = process_query_batch(query, url)
        total_new += new
        time.sleep(1)  # Pause between queries

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("="*80)
    logger.info(f"✅ NEWS DISCOVERY PIPELINE COMPLETE")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"New Prospects Found: {total_new}")
    logger.info("="*80 + "\n")
    
    return {
        "status": "completed",
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_seconds": duration,
        "new_prospects": total_new,
        "message": f"✓ Discovery pipeline complete. Found {total_new} new prospects."
    }