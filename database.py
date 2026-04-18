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
            last_description_checked TIMESTAMP,
            last_news_check TIMESTAMP,
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

        CREATE TABLE IF NOT EXISTS monitoring_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES prospects(id),
            event_type TEXT NOT NULL,
            urgency TEXT NOT NULL,
            title TEXT NOT NULL,
            evidence TEXT,
            source_url TEXT,
            event_date TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_processed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS prospect_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES prospects(id),
            interaction_type TEXT NOT NULL,
            email_persona TEXT,
            subject_line TEXT,
            sent_at TIMESTAMP,
            response_received INTEGER DEFAULT 0,
            response_type TEXT,
            response_date TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS compliance_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT NOT NULL,
            triggered_phrase TEXT,
            override_count INTEGER DEFAULT 1,
            last_override_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            first_override_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_status TEXT DEFAULT 'TRACKING'
        );

        CREATE TABLE IF NOT EXISTS partners_activated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES prospects(id) UNIQUE,
            signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activation_status TEXT DEFAULT 'INTEGRATION_PENDING',
            current_milestone TEXT,
            milestone_reached_at TIMESTAMP,
            days_in_current_milestone INTEGER DEFAULT 0,
            last_activity TIMESTAMP,
            activation_score INTEGER DEFAULT 0,
            is_at_risk INTEGER DEFAULT 0,
            next_milestone TEXT,
            estimated_milestone_completion TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS activation_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            milestone_type TEXT NOT NULL,
            milestone_name TEXT,
            expected_days INTEGER,
            reached_at TIMESTAMP,
            detection_method TEXT,
            evidence TEXT,
            status TEXT DEFAULT 'PENDING'
        );

        CREATE TABLE IF NOT EXISTS partner_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            activity_type TEXT NOT NULL,
            activity_date TIMESTAMP,
            metric_type TEXT,
            metric_value REAL,
            notes TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS partner_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            issue_type TEXT NOT NULL,
            issue_category TEXT,
            description TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolution_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS activation_reengage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            reengage_type TEXT NOT NULL,
            trigger_reason TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_subject TEXT,
            email_body TEXT,
            success_persona TEXT,
            sent_at TIMESTAMP,
            response_received INTEGER DEFAULT 0,
            response_type TEXT
        );

        -- INNOVATION 1: Buyer Committee Intelligence
        CREATE TABLE IF NOT EXISTS buyer_committee_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES prospects(id),
            partner_id INTEGER REFERENCES partners_activated(id),
            name TEXT NOT NULL,
            title TEXT,
            role TEXT NOT NULL,
            email TEXT,
            linkedin_profile TEXT,
            seniority_level TEXT,
            decision_authority TEXT,
            engagement_level TEXT DEFAULT 'UNKNOWN',
            sentiment TEXT DEFAULT 'NEUTRAL',
            is_champion INTEGER DEFAULT 0,
            is_blocker INTEGER DEFAULT 0,
            is_economic_buyer INTEGER DEFAULT 0,
            is_user INTEGER DEFAULT 0,
            first_contact_at TIMESTAMP,
            last_engagement_at TIMESTAMP,
            engagement_score REAL DEFAULT 0.0,
            opened_emails INTEGER DEFAULT 0,
            clicked_emails INTEGER DEFAULT 0,
            calls_attended INTEGER DEFAULT 0,
            demos_attended INTEGER DEFAULT 0,
            content_downloads INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stakeholder_engagement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER REFERENCES buyer_committee_members(id),
            engagement_type TEXT NOT NULL,
            detail TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_id TEXT,
            call_duration_seconds INTEGER,
            demo_duration_seconds INTEGER,
            sentiment_detected TEXT,
            confidence REAL,
            sentiment_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS stakeholder_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER REFERENCES buyer_committee_members(id),
            sentiment_status TEXT DEFAULT 'NEUTRAL',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            engagement_signals INTEGER,
            concern_area TEXT,
            influence_score REAL
        );

        CREATE TABLE IF NOT EXISTS buyer_committee_committee_consensus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            prospect_id INTEGER REFERENCES prospects(id),
            consensus_status TEXT DEFAULT 'FORMING',
            consensus_score REAL DEFAULT 0.0,
            champions_count INTEGER DEFAULT 0,
            blockers_count INTEGER DEFAULT 0,
            neutral_count INTEGER DEFAULT 0,
            deal_health TEXT DEFAULT 'HEALTHY',
            risk_factors TEXT,
            estimated_close_likelihood REAL DEFAULT 0.0,
            last_assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS buyer_committee_playbook_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER REFERENCES buyer_committee_members(id),
            role TEXT NOT NULL,
            intervention_sequence INTEGER,
            email_subject TEXT,
            email_body TEXT,
            resources_sent TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP,
            response_received INTEGER DEFAULT 0,
            response_type TEXT,
            response_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS activation_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            prospect_id INTEGER REFERENCES prospects(id),
            campaign_name TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            total_contacts INTEGER,
            target_completion_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            campaign_type TEXT DEFAULT 'MULTI_STAKEHOLDER'
        );

        CREATE TABLE IF NOT EXISTS activation_campaign_sends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER REFERENCES activation_campaigns(id),
            buyer_id INTEGER REFERENCES buyer_committee_members(id),
            contact_sequence INTEGER,
            role TEXT,
            scheduled_date TIMESTAMP,
            playbook_template TEXT,
            status TEXT DEFAULT 'SCHEDULED',
            email_subject TEXT,
            email_body TEXT,
            sent_at TIMESTAMP,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP,
            responded_at TIMESTAMP,
            response_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS partner_api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            environment TEXT NOT NULL DEFAULT 'sandbox',
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER,
            error_code TEXT,
            error_message TEXT,
            response_time_ms INTEGER,
            api_key_id TEXT,
            called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS partner_activation_stalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            stall_pattern TEXT NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            days_of_inactivity INTEGER,
            last_activity_date TIMESTAMP,
            intervention_email_sent INTEGER DEFAULT 0,
            intervention_sent_at TIMESTAMP,
            issue_resolved INTEGER DEFAULT 0,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS partner_political_risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            risk_type TEXT NOT NULL,
            detected_via TEXT NOT NULL,
            details TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            alert_sent INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS partner_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            name TEXT,
            email TEXT,
            persona TEXT NOT NULL,
            confidence TEXT DEFAULT 'manual',
            added_by TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified INTEGER DEFAULT 0,
            verified_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS intervention_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER REFERENCES partners_activated(id),
            stall_pattern TEXT NOT NULL,
            intervention_email_generated TIMESTAMP,
            intervention_email_sent TIMESTAMP,
            intervention_sent_to_email TEXT,
            outcome TEXT,
            outcome_recorded_at TIMESTAMP,
            notes TEXT
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
        # Check for exact duplicate signals (same type, same title)
        # This prevents adding the same signal multiple times across multiple runs
        existing = conn.execute("""
            SELECT id FROM signals 
            WHERE prospect_id = ? 
            AND signal_type = ?
            AND title = ?
        """, (prospect_id, signal_type, title)).fetchone()
        
        if existing:
            return  # Don't add exact duplicate
        
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


def event_already_recorded(prospect_id: int, source_url: str) -> bool:
    """Check if monitoring event was already recorded for this prospect from this URL."""
    if not source_url:
        return False
    with get_db() as conn:
        existing = conn.execute("""
            SELECT id FROM monitoring_events 
            WHERE prospect_id = ? AND source_url = ?
        """, (prospect_id, source_url)).fetchone()
        return existing is not None


def record_monitoring_event(prospect_id: int, event_type: str, urgency: str,
                            title: str, evidence: str = None, 
                            source_url: str = None, event_date: str = None):
    """Record a monitoring event for a prospect. Deduplicates by (prospect_id, source_url)."""
    # Skip if already recorded from this source
    if event_already_recorded(prospect_id, source_url):
        return False
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO monitoring_events 
            (prospect_id, event_type, urgency, title, evidence, source_url, event_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (prospect_id, event_type, urgency, title, evidence, source_url, event_date))
        conn.commit()
    
    return True


def get_monitoring_events(prospect_id: int, days: int = 7):
    """Get recent monitoring events for a prospect."""
    with get_db() as conn:
        return conn.execute("""
            SELECT * FROM monitoring_events 
            WHERE prospect_id = ? 
            AND datetime(detected_at) >= datetime('now', '-' || ? || ' days')
            ORDER BY detected_at DESC
        """, (prospect_id, days)).fetchall()


def update_prospect_monitor_timestamp(prospect_id: int, check_type: str):
    """Update last check timestamp for a prospect."""
    column = 'last_news_check' if check_type == 'news' else 'last_description_checked'
    with get_db() as conn:
        conn.execute(
            f"UPDATE prospects SET {column} = CURRENT_TIMESTAMP WHERE id = ?",
            (prospect_id,)
        )
        conn.commit()


def get_all_prospects_for_monitoring():
    """Get all HOT and WARM prospects for monitoring. Excludes WATCH and garbage companies."""
    with get_db() as conn:
        return conn.execute("""
            SELECT id, name, play_store_id, description
            FROM prospects
            WHERE is_existing_partner = 0
            AND status IN ('HOT', 'WARM')
            ORDER BY who_score DESC
        """).fetchall()


# ============================================================================
# DATA VALIDATION LAYER — Prevent bad data at the source
# ============================================================================

def validate_prospect_data(prospect_dict: dict) -> tuple[bool, str]:
    """Validate prospect data before upsert. Returns (is_valid, error_message)"""
    
    name = prospect_dict.get('name', '').strip()
    category = prospect_dict.get('category', '').strip() if prospect_dict.get('category') else None
    
    # Validate company name
    if not name or len(name) < 2:
        return False, f"Company name too short: '{name}'"
    
    if len(name) > 80:
        return False, f"Company name too long (>80 chars): '{name}'"
    
    # Reject test data
    if 'test' in name.lower() and 'partner' in name.lower():
        return False, f"Test data rejected: {name}"
    
    # Reject suspicious/garbage names
    garbage_patterns = ['none', 'n/a', 'unknown', 'undefined', '###', 'null']
    if any(pattern in name.lower() for pattern in garbage_patterns):
        return False, f"Garbage company name rejected: {name}"
    
    # Validate category (required, must be in whitelist)
    valid_categories = [
        'neobank', 'wealth', 'payment', 'savings',
        'lending', 'broker', 'fintech', 'banking',
        'ai', 'cross-border'
    ]
    
    if not category:
        return False, f"Category is required for {name}"
    
    if category not in valid_categories:
        return False, f"Invalid category '{category}' for {name}. Valid: {', '.join(valid_categories)}"
    
    return True, "Valid"


def validate_signal(prospect_id: int, signal_type: str, strength: str) -> tuple[bool, str]:
    """Validate signal before insert. Returns (is_valid, error_message)"""
    
    valid_types = [
        'PRODUCT_GAP', 'FUNDING_EXPANSION', 'LEADERSHIP_HIRE',
        'COMPETITOR_MOVE', 'DISPLACEMENT', 'COMPLIANCE_RISK',
        'PRODUCTION_READY', 'API_INTEGRATION'
    ]
    
    valid_strengths = ['HIGH', 'MEDIUM', 'LOW']
    
    if signal_type not in valid_types:
        return False, f"Invalid signal type: {signal_type}. Valid: {', '.join(valid_types)}"
    
    if strength not in valid_strengths:
        return False, f"Invalid signal strength: {strength}. Valid: {', '.join(valid_strengths)}"
    
    if prospect_id <= 0:
        return False, f"Invalid prospect_id: {prospect_id}"
    
    return True, "Valid"


def validate_who_score(score) -> bool:
    """Validate WHO score is in valid range (0-100)."""
    try:
        score_int = int(score) if score is not None else 0
        return 0 <= score_int <= 100
    except (ValueError, TypeError):
        return False