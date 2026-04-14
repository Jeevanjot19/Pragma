from google_play_scraper import app as get_app_details, search
from database import upsert_prospect, get_prospect_by_name, get_db, is_qualified_prospect
from intelligence.llm_extractor import detect_products_smart
import time

FINANCE_SEARCH_TERMS = [
    "investment app India",
    "savings app India", 
    "mutual fund India",
    "stock trading India",
    "wealth management India"
]

BLOSTEM_PRODUCT_KEYWORDS = {
    'has_fd': ['fixed deposit', 'fd', 'term deposit'],
    'has_rd': ['recurring deposit', 'rd', 'monthly savings'],
    'has_bonds': ['bonds', 'debentures', 'fixed income'],
    'has_upi_credit': ['upi credit', 'credit line', 'overdraft'],
    'has_mutual_funds': ['mutual fund', 'sip', 'mf'],
    'has_stocks': ['stocks', 'equity', 'shares', 'trading', 'demat'],
    'has_insurance': ['insurance', 'life cover']
}

MINIMUM_INSTALLS_THRESHOLD = "1,000,000+"  # Only care about apps with 1M+ installs


def detect_products_from_description(description: str) -> dict:
    """Check which financial products an app already has."""
    desc_lower = description.lower()
    products = {}
    for product, keywords in BLOSTEM_PRODUCT_KEYWORDS.items():
        products[product] = any(kw in desc_lower for kw in keywords)
    return products


def enrich_prospect_from_play_store(prospect_name: str, app_id: str) -> bool:
    """
    Enrich an existing prospect with Play Store data.
    Uses smart keyword detection (zero LLM calls) to detect products.
    Only updates if prospect qualifies based on install count and description.
    Returns True if successful enrichment.
    """
    try:
        details = get_app_details(app_id, lang='en', country='in')
        
        install_count = details.get('installs', 'Unknown')
        description = details.get('description', '')
        
        # Check qualification before enriching
        qual_data = {
            'name': prospect_name,
            'install_count': install_count,
            'description': description
        }
        is_qualified, reason = is_qualified_prospect(qual_data)
        if not is_qualified:
            print(f"  Skipped {prospect_name}: {reason}")
            return False
        
        # Use smart keyword detection (zero API calls)
        product_flags = detect_products_smart(description)
        
        # Update prospect with enriched data
        update_data = {
            'name': prospect_name,
            'play_store_id': app_id,
            'install_count': install_count,
            'description': description[:500],  # Store first 500 chars
            'has_fd': product_flags.get('has_fd', False),
            'has_rd': product_flags.get('has_rd', False),
            'has_bonds': product_flags.get('has_bonds', False),
            'has_upi_credit': product_flags.get('has_upi_credit', False),
            'has_mutual_funds': product_flags.get('has_mutual_funds', False),
            'has_stocks': product_flags.get('has_stocks', False),
            'has_insurance': product_flags.get('has_insurance', False)
        }
        
        upsert_prospect(update_data)
        print(f"  Enriched {prospect_name}: {install_count} installs")
        return True
        
    except Exception as e:
        print(f"  Play Store error for {prospect_name}: {e}")
        return False


def discover_from_play_store() -> int:
    """
    Search Play Store for finance apps not yet in our database.
    Returns count of new prospects added.
    """
    print("\n📱 Running Play Store discovery...")
    new_count = 0
    seen_apps = set()
    
    with get_db() as conn:
        existing = conn.execute(
            "SELECT play_store_id FROM prospects WHERE play_store_id IS NOT NULL"
        ).fetchall()
        seen_apps = {r['play_store_id'] for r in existing}
    
    for term in FINANCE_SEARCH_TERMS:
        try:
            results = search(term, lang='en', country='in', n_hits=20)
            
            for app in results:
                app_id = app.get('appId', '')
                title = app.get('title', '')
                
                if app_id in seen_apps:
                    continue
                    
                # Only care about apps with significant user base
                # score as proxy for maturity
                score = app.get('score', 0)
                if score < 3.5:
                    continue
                
                # Check if this looks like a fintech app
                description = app.get('description', '')
                products = detect_products_from_description(description)
                
                # Only add if they have SOME financial products but gaps exist
                has_any_finance = any(products.values())
                has_fd = products.get('has_fd', False)
                
                if not has_any_finance:
                    continue
                    
                # Add to database
                upsert_prospect({
                    'name': title,
                    'play_store_id': app_id,
                    'description': description[:500],
                    'has_fd': has_fd,
                    **products,
                    'source': 'play_store'
                })
                
                seen_apps.add(app_id)
                new_count += 1
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  Search error for '{term}': {e}")
    
    print(f"✅ Play Store discovery complete. {new_count} new apps found.\n")
    return new_count


def enrich_all_prospects() -> int:
    """
    Enrich all non-enriched prospects from Play Store.
    Skips prospects that have already been enriched.
    Returns count of newly enriched prospects.
    """
    print("\n📱 Enriching prospects from Play Store...")
    enriched_count = 0
    
    with get_db() as conn:
        # Get prospects that haven't been enriched yet
        # (no play_store_id OR no install_count/description data)
        prospects = conn.execute("""
            SELECT id, name, play_store_id
            FROM prospects 
            WHERE (play_store_id IS NULL AND install_count IS NULL)
               OR (play_store_id IS NOT NULL AND description IS NULL)
            ORDER BY id DESC
        """).fetchall()
    
    if not prospects:
        print("  No unenriched prospects to process.")
        return 0
    
    print(f"  Found {len(prospects)} prospects to enrich...")
    
    for prospect in prospects:
        prospect_id = prospect['id']
        prospect_name = prospect['name']
        app_id = prospect['play_store_id']
        
        try:
            # Search for the app if we don't have app_id
            if not app_id:
                results = search(prospect_name, lang='en', country='in', n_hits=1)
                if not results:
                    print(f"  Could not find {prospect_name} on Play Store")
                    continue
                app_id = results[0].get('appId')
                if not app_id:
                    continue
            
            # Enrich with Play Store data
            if enrich_prospect_from_play_store(prospect_name, app_id):
                enriched_count += 1
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  Error enriching {prospect_name}: {e}")
            continue
    
    print(f"✅ Enrichment complete. {enriched_count} prospects enriched.\n")
    return enriched_count

def enrich_all_prospects():
    print("\n📱 Enriching prospects with Play Store data...")
    
    with get_db() as conn:
        prospects = conn.execute(
            """SELECT id, name FROM prospects 
               WHERE play_store_id IS NULL 
               AND is_existing_partner = 0
               AND name NOT IN ('None', 'None mentioned', 'India Fintech')"""
        ).fetchall()
    
    for prospect in prospects:
        name = prospect['name']
        try:
            results = search(name + " India fintech", lang='en', 
                           country='in', n_hits=3)
            
            if not results:
                continue
                
            best_match = results[0]
            app_id = best_match.get('appId', '')
            app_title = best_match.get('title', '')
            
            # STRICT matching — both names must share significant overlap
            name_lower = name.lower()
            title_lower = app_title.lower()
            
            # Only match if the prospect name appears directly in app title
            # or app title appears directly in prospect name
            strict_match = (
                name_lower in title_lower or
                title_lower in name_lower or
                # Allow first word match for short names
                (len(name.split()) == 1 and 
                 name_lower == title_lower.split()[0])
            )
            
            if strict_match:
                enrich_prospect_from_play_store(name, app_id)
            
            time.sleep(0.5)
        except Exception as e:
            print(f"  Could not enrich {name}: {e}")
    
    print("✅ Enrichment complete\n")