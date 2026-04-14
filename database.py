import sqlite3
from contextlib import contextmanager

DB_PATH = "pragma.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.executescript("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            website TEXT,
            play_store_id TEXT,
            install_count TEXT,
            description TEXT,
            has_fd BOOLEAN DEFAULT 0,
            has_rd BOOLEAN DEFAULT 0,
            has_bonds BOOLEAN DEFAULT 0,
            has_upi_credit BOOLEAN DEFAULT 0,
            has_mutual_funds BOOLEAN DEFAULT 0,
            has_stocks BOOLEAN DEFAULT 0,
            has_insurance BOOLEAN DEFAULT 0,
            recommended_product TEXT,
            using_competitor TEXT,
            is_existing_partner BOOLEAN DEFAULT 0,
            who_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'WATCH',
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES prospects(id),
            signal_type TEXT NOT NULL,
            signal_strength TEXT NOT NULL,
            title TEXT NOT NULL,
            evidence TEXT,
            source_url TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS processed_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS regulatory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            relevant_products TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_prospect_by_name(name: str):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM prospects WHERE name = ?", (name,)
        ).fetchone()

def upsert_prospect(data: dict):
    """Insert or update a prospect. Name is normalised for deduplication."""
    # Normalise name — strip whitespace, title case for consistent matching
    name = data.get('name', '').strip()
    if not name:
        return
    data['name'] = name

    with get_db() as conn:
        # Case-insensitive lookup
        existing = conn.execute(
            "SELECT id FROM prospects WHERE LOWER(name) = LOWER(?)",
            (name,)
        ).fetchone()

        if existing:
            fields = [f"{k} = ?" for k in data.keys() if k != 'name']
            values = [v for k, v in data.items() if k != 'name']
            values.append(name)
            conn.execute(
                f"UPDATE prospects SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE LOWER(name) = LOWER(?)",
                values
            )
        else:
            placeholders = ', '.join(['?' for _ in data])
            conn.execute(
                f"INSERT INTO prospects ({', '.join(data.keys())}) VALUES ({placeholders})",
                list(data.values())
            )
        conn.commit()

def add_signal(prospect_id: int, signal_type: str, strength: str, 
               title: str, evidence: str = None, source_url: str = None):
    with get_db() as conn:
        # Check if we already have this signal type today for this prospect
        # Prevents duplicate signals from similar articles
        existing = conn.execute("""
            SELECT id FROM signals 
            WHERE prospect_id = ? 
            AND signal_type = ?
            AND date(detected_at) = date('now')
        """, (prospect_id, signal_type)).fetchone()
        
        if existing:
            return  # Don't add duplicate signal type for same day
        
        conn.execute("""
            INSERT INTO signals (prospect_id, signal_type, signal_strength, title, evidence, source_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (prospect_id, signal_type, strength, title, evidence, source_url))
        conn.commit()

def is_article_processed(url: str) -> bool:
    with get_db() as conn:
        result = conn.execute(
            "SELECT id FROM processed_articles WHERE url = ?", (url,)
        ).fetchone()
        return result is not None

def mark_article_processed(url: str, title: str):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_articles (url, title) VALUES (?, ?)",
            (url, title)
        )
        conn.commit()

def remove_non_prospects():
    """Remove entries that are clearly not fintech prospects."""
    NON_PROSPECTS = [
        'RBI', 'Reserve Bank of India', 'SEBI', 'NPCI', 'IRDAI',
        'SBI', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 'Kotak Bank',
        'Ministry of Finance', 'Government of India'
    ]
    with get_db() as conn:
        for name in NON_PROSPECTS:
            conn.execute(
                "DELETE FROM prospects WHERE name LIKE ?", (f"%{name}%",)
            )
        conn.commit()


def is_qualified_prospect(prospect: dict) -> tuple[bool, str]:
    """
    Returns (is_qualified, reason).
    A prospect must meet minimum criteria before staying in the pipeline.
    Checks install count and description for B2B-only products.
    """
    name = prospect.get('name', '')
    install_count = prospect.get('install_count', '')
    description = prospect.get('description', '')
    
    # Must have meaningful scale
    # Small apps with minimal users aren't worth a sales call
    LOW_SCALE_INDICATORS = ['50+', '100+', '500+', '1,000+', '5,000+', '10,000+']
    if install_count and any(ind == install_count for ind in LOW_SCALE_INDICATORS):
        return False, f"Too small: only {install_count} installs"
    
    # Must be consumer-facing, not purely B2B infrastructure
    B2B_ONLY_INDICATORS = [
        'for businesses', 'for merchants', 'b2b', 'enterprise only',
        'for banks', 'for lenders', 'api for', 'platform for banks'
    ]
    desc_lower = (description or '').lower()
    if description and any(ind in desc_lower for ind in B2B_ONLY_INDICATORS):
        # Check if they ALSO have consumer products
        has_consumer = any(ind in desc_lower for ind in [
            'for users', 'personal', 'individual', 'retail', 'consumer'
        ])
        if not has_consumer:
            return False, "B2B only product, no consumer users"
    
    return True, "Qualified"
    print("Cleaned up non-prospect entries")