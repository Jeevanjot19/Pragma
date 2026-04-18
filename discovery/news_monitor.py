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


def _process_extracted_company(extracted: dict, url: str, title: str, article_date: str) -> dict:
    """Process a single extracted company and create signals. Returns dict with result details."""
    result = {'added': False, 'company': None, 'category': None, 'signals': 0}
    
    if not extracted or not extracted.get('is_relevant', False):
        return result
    
    company_name = extracted.get('company_name') or ''
    company_name = company_name.strip()
    
    if not company_name or len(company_name) < 2:
        return result

    # Skip garbage names
    if company_name in ['None', 'None mentioned', 'N/A', 'Unknown', '']:
        return result

    # Skip non-prospects (regulatory bodies, generic terms, etc.)
    if any(np.lower() == company_name.lower() for np in NON_PROSPECTS):
        logger.debug(f"Skipped non-prospect: {company_name}")
        return result

    # Skip existing Blostem partners
    if any(p.lower() in company_name.lower() or 
           company_name.lower() in p.lower() 
           for p in EXISTING_PARTNERS):
        logger.debug(f"Skipped existing partner: {company_name}")
        return result

    # Check for competitor
    competitor = None
    is_competitor = any(c.lower() in company_name.lower() or 
                        company_name.lower() in c.lower() 
                        for c in COMPETITORS)
    if is_competitor:
        logger.debug(f"Skipped competitor: {company_name}")
        return result

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
        return result
    prospect_id = prospect['id']

    # Add signals
    expansion = extracted.get('expansion_signals', [])
    signal_count = 0

    # Product gap
    add_signal(
        prospect_id=prospect_id,
        signal_type='PRODUCT_GAP',
        strength='HIGH',
        title=f"{company_name} needs {recommended}",
        evidence=extracted.get('signal_summary', ''),
        source_url=url
    )
    signal_count += 1

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
        signal_count += 1

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
        signal_count += 1

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
        signal_count += 1

    logger.info(f"✓ Added {company_name} ({category}) → {recommended} with {signal_count} signals")
    
    result['added'] = True
    result['company'] = company_name
    result['category'] = category
    result['signals'] = signal_count
    result['recommended_product'] = recommended
    result['source'] = url
    result['summary'] = extracted.get('signal_summary', '')
    return result


def process_query_batch(query: str, feed_url: str) -> dict:
    """Process one Google News query with batched LLM calls. Returns detailed results."""
    results = {
        'query': query,
        'new_prospects': 0,
        'companies': [],
        'error': None
    }

    logger.info(f"Processing query: {query}")

    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Error fetching '{query}': {e}")
        results['error'] = str(e)
        return results

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
        logger.debug(f"No unprocessed articles for query: {query}")
        return results

    logger.info(f"Found {len(unprocessed)} unprocessed articles for '{query}'")

    # BATCH in groups of 2 to AGGRESSIVELY reduce token usage
    BATCH_SIZE = 2  # Process 2 articles at a time to minimize token burn per request
    extracted_list = []
    
    for i in range(0, len(unprocessed), BATCH_SIZE):
        batch = unprocessed[i:i+BATCH_SIZE]
        logger.info(f"  Processing batch {i//BATCH_SIZE + 1} ({len(batch)} articles)...")
        batch_results = batch_extract_companies(batch)
        extracted_list.extend(batch_results)
        time.sleep(2)  # Wait 2 seconds between batches to throttle requests
    
    # Mark all as processed
    for article in unprocessed:
        mark_article_processed(article['url'], article['title'])

    # Process each extraction result
    for i, extracted in enumerate(extracted_list):
        if i >= len(unprocessed):
            break
        article = unprocessed[i]
        result = _process_extracted_company(
            extracted, 
            article['url'],
            article['title'],
            article.get('article_date')
        )
        
        if result['added']:
            results['new_prospects'] += 1
            results['companies'].append(result)
            
        time.sleep(0.2)

    logger.info(f"Query '{query}': {results['new_prospects']} new prospects")
    return results


def run_news_monitor() -> dict:
    """Run all Google News queries. Returns comprehensive results with prospect details."""
    start_time = datetime.now()
    logger.info("="*80)
    logger.info(f"🔍 STARTING NEWS DISCOVERY PIPELINE")
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Number of queries: {len(GOOGLE_NEWS_QUERIES)}")
    logger.info("="*80)
    
    total_new = 0
    all_companies = []
    failed_queries = []

    for query in GOOGLE_NEWS_QUERIES:
        url = build_google_news_url(query)
        result = process_query_batch(query, url)
        
        total_new += result['new_prospects']
        all_companies.extend(result['companies'])
        
        if result['error']:
            failed_queries.append({'query': query, 'error': result['error']})
        
        time.sleep(1)  # Pause between queries

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("="*80)
    logger.info(f"✅ NEWS DISCOVERY PIPELINE COMPLETE")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"New Prospects Found: {total_new}")
    if all_companies:
        logger.info("Companies discovered:")
        for c in all_companies:
            logger.info(f"  - {c['company']} ({c['category']}) → {c['recommended_product']} ({c['signals']} signals)")
    logger.info("="*80 + "\n")
    
    return {
        "status": "completed",
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_seconds": duration,
        "new_prospects": total_new,
        "companies": all_companies,
        "failed_queries": failed_queries,
        "total_queries": len(GOOGLE_NEWS_QUERIES),
        "message": f"✓ Discovery pipeline complete. Found {total_new} new prospect(s)."
    }