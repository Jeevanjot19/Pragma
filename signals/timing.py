"""
WHEN Layer — Component C: Temporal Scoring
Scores prospects based on monitoring_events (temporal signals) combined with WHO scale/maturity.
Generates actionable weekly priorities: "CALL THIS WEEK", "EMAIL THIS WEEK", etc.
"""

from datetime import datetime, timedelta
from database import get_db

SCALE_SCORES = {
    '1,000,000,000+': 40, '500,000,000+': 38,
    '100,000,000+': 35,   '50,000,000+': 30,
    '10,000,000+': 25,    '5,000,000+': 20,
    '1,000,000+': 15,     '500,000+': 12,
    '100,000+': 8,        '50,000+': 5,
    '10,000+': 3,         '1,000+': 1,
}

PRODUCT_MATURITY_SCORES = {0: 5, 1: 10, 2: 15, 3: 20, 4: 25}

EVENT_TYPE_BOOSTS = {
    'FUNDING': 30,
    'DISPLACEMENT': 30,
    'LEADERSHIP_HIRE': 25,
    'COMPETITOR_MOVE': 20,
    'PRODUCT_LAUNCH': 20,
    'APP_UPDATE': 15,
    'PARTNERSHIP': 10,
    'REGULATORY_IMPACT': 10,
    'NEWS': 0,  # Generic news gives no boost
}

URGENCY_MULTIPLIERS = {'HIGH': 1.0, 'MEDIUM': 0.7, 'LOW': 0.3}


def get_product_maturity_score(prospect: dict) -> int:
    """Score based on number of financial products offered."""
    fields = ['has_mutual_funds', 'has_stocks', 'has_bonds',
              'has_insurance', 'has_lending', 'has_payments']
    count = min(sum(1 for f in fields if prospect.get(f, 0) == 1), 4)
    return PRODUCT_MATURITY_SCORES.get(count, 5)


def get_monitoring_event_score(prospect_id: int) -> tuple[int, int, dict | None]:
    """
    Score based on monitoring_events table with exponential decay.
    Returns (event_boost, recency_bonus, best_event).
    Only counts events from last 30 days.
    Applies exponential decay: e^(-days_since_event / 14).
    At 14 days: 37% of original boost. At 30 days: 11% of original boost.
    """
    import math
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )

    with get_db() as conn:
        events = conn.execute("""
            SELECT * FROM monitoring_events
            WHERE prospect_id = ?
            AND detected_at >= ?
            ORDER BY detected_at DESC
        """, (prospect_id, thirty_days_ago)).fetchall()

    if not events:
        return 0, 0, None

    events = [dict(e) for e in events]

    # Find best event (highest boost × urgency × decay)
    best_event = None
    best_score = 0

    for event in events:
        etype = event.get('event_type', '')
        urgency = event.get('urgency', 'LOW')
        base_boost = EVENT_TYPE_BOOSTS.get(etype, 0)
        multiplier = URGENCY_MULTIPLIERS.get(urgency, 0.3)
        
        # Calculate decay from event date
        event_date_str = (event.get('event_date') or
                         str(event.get('detected_at', ''))[:10])
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            days_since = (datetime.now() - event_date).days
        except Exception:
            days_since = 0
        
        decay_factor = math.exp(-days_since / 14)
        score = int(base_boost * multiplier * decay_factor)
        
        if score > best_score:
            best_score = score
            best_event = event

    event_boost = best_score

    # Recency bonus — how fresh is the best event?
    recency_bonus = 0
    if best_event:
        event_date_str = (best_event.get('event_date') or
                         str(best_event.get('detected_at', ''))[:10])
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            days_ago = (datetime.now() - event_date).days
            if days_ago <= 3:
                recency_bonus = 15
            elif days_ago <= 7:
                recency_bonus = 10
            elif days_ago <= 14:
                recency_bonus = 5
        except Exception:
            pass

    return event_boost, recency_bonus, best_event


def calculate_when_score(prospect_id: int) -> dict:
    """
    Calculate WHEN score (temporal priority score) for a prospect.
    NEW FORMULA (Issue 3 & 1 Fix):
    - Removed scale to avoid double-counting (WHO already scores it)
    - Added days_since_last_contact to prevent duplicate outreach (Issue 1)
    - Applies exponential decay to event urgency (Issue 5)
    
    Final Score: (product_maturity + event_boost + recency_bonus) × contact_factor
    contact_factor diminishes re-engagement frequency based on days_since_last_contact
    """
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?",
            (prospect_id,)
        ).fetchone()

    if not prospect:
        return {'when_score': 0, 'action': 'SKIP'}

    prospect = dict(prospect)

    maturity = get_product_maturity_score(prospect)
    event_boost, recency_bonus, best_event = \
        get_monitoring_event_score(prospect_id)
    
    # Get days since last contact (Issue 1: Feedback loop)
    with get_db() as conn:
        last_interaction = conn.execute("""
            SELECT MAX(sent_at) as last_sent 
            FROM prospect_interactions 
            WHERE prospect_id = ?
        """, (prospect_id,)).fetchone()
    
    contact_factor = 1.0
    days_since_contact = -1
    
    if last_interaction and last_interaction['last_sent']:
        try:
            last_sent = datetime.fromisoformat(last_interaction['last_sent'])
            days_since_contact = (datetime.now() - last_sent).days
            
            # Contact factor: Full weight if no contact, decays if recently contacted
            # 0 days: 0.5x (just contacted today, low re-engagement)
            # 3 days: 0.7x
            # 7 days: 0.9x
            # 14+ days: 1.0x (ready for re-engagement)
            if days_since_contact <= 1:
                contact_factor = 0.5
            elif days_since_contact <= 3:
                contact_factor = 0.7
            elif days_since_contact <= 7:
                contact_factor = 0.9
            else:
                contact_factor = 1.0
        except Exception:
            pass

    # Final calculation: NO SCALE (removed for Issue 3)
    when_score = int((maturity + event_boost + recency_bonus) * contact_factor)
    when_score = min(when_score, 100)

    has_event = event_boost > 0

    if when_score >= 65 and has_event:
        action = 'CALL THIS WEEK'
    elif when_score >= 50 and has_event:
        action = 'EMAIL THIS WEEK'
    elif when_score >= 50:
        action = 'SEND INTRO EMAIL'
    elif when_score >= 30:
        action = 'NURTURE'
    else:
        action = 'MONITOR'

    best_event_summary = None
    if best_event:
        best_event_summary = {
            'type': best_event.get('event_type'),
            'title': best_event.get('title'),
            'date': best_event.get('event_date'),
            'urgency': best_event.get('urgency')
        }

    return {
        'prospect_id': prospect_id,
        'prospect_name': prospect['name'],
        'category': prospect.get('category'),
        'recommended_product': prospect.get('recommended_product'),
        'install_count': prospect.get('install_count'),
        'who_score': prospect.get('who_score', 0),
        'when_score': when_score,
        'action': action,
        'has_event_signal': has_event,
        'best_recent_event': best_event_summary,
        'days_since_last_contact': days_since_contact,
        'contact_factor': contact_factor,
        'score_breakdown': {
            'product_maturity': maturity,
            'event_boost': event_boost,
            'recency_bonus': recency_bonus,
            'contact_factor': f"{contact_factor:.1%}"
        }
    }


def get_all_when_scores() -> list:
    """Get WHEN scores for all qualified prospects. Returns sorted by when_score DESC."""
    with get_db() as conn:
        prospects = conn.execute("""
            SELECT id FROM prospects
            WHERE is_existing_partner = 0
            AND status IN ('HOT', 'WARM')
            ORDER BY who_score DESC
        """).fetchall()

    results = []
    for p in prospects:
        score_data = calculate_when_score(p['id'])
        results.append(score_data)

    results.sort(key=lambda x: x['when_score'], reverse=True)
    return results


def get_weekly_priorities() -> dict:
    """Returns categorized priority list — the Monday morning view of what to do this week."""
    all_scores = get_all_when_scores()

    return {
        'generated_at': datetime.now().isoformat(),
        'call_this_week': [
            s for s in all_scores if s['action'] == 'CALL THIS WEEK'
        ],
        'email_this_week': [
            s for s in all_scores if s['action'] == 'EMAIL THIS WEEK'
        ],
        'send_intro': [
            s for s in all_scores if s['action'] == 'SEND INTRO EMAIL'
        ],
        'nurture': [s for s in all_scores if s['action'] == 'NURTURE'],
        'monitor': [s for s in all_scores if s['action'] == 'MONITOR'],
    }
